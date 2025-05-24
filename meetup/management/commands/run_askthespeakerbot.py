import os
import threading
from datetime import datetime, timedelta

import django
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
import telebot
from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "project.settings")
django.setup()

from meetup.models import Event, Talk, Question, UserProfile
from meetup.signals import PENDING_ANSWER

LOGO_PATH = os.path.join(settings.BASE_DIR, "logo2.png")
PENDING_QUESTION = {}
UPDATERS = {}


def stop_updater(chat_id: int) -> None:
    ev = UPDATERS.pop(chat_id, None)
    if ev:
        ev.set()


def format_timedelta(td: timedelta) -> str:
    total = int(td.total_seconds())
    if total <= 0:
        return "уже идёт"
    days, rem = divmod(total, 86400)
    hours, rem = divmod(rem, 3600)
    minutes, _ = divmod(rem, 60)
    parts = []
    if days:
        parts.append(f"{days} дн")
    if hours:
        parts.append(f"{hours} ч")
    if minutes:
        parts.append(f"{minutes} мин")
    return " ".join(parts)


def build_program_text(event: Event) -> str:
    delta = timezone.localtime(event.date) - timezone.localtime()
    local_event = timezone.localtime(event.date)
    return (
        f"Митап: {event.title}\n"
        f"Время проведения: {local_event.strftime('%d.%m.%Y %H:%M')}\n"
        f"До начала: {format_timedelta(delta)}\n\n"
        f"{event.description}\n\n"
        "Программа:"
    )


def build_progress_bar(talk: Talk, length: int = 10) -> str:
    now = timezone.localtime()
    start = timezone.make_aware(datetime.combine(talk.event.date.date(), talk.start_time))
    end = timezone.make_aware(datetime.combine(talk.event.date.date(), talk.end_time))
    if end <= start:
        end += timedelta(days=1)
    start, end = map(timezone.localtime, (start, end))
    total   = max((end - start).total_seconds(), 1)
    elapsed = (now - start).total_seconds()
    ratio   = max(0.0, min(elapsed / total, 1.0))
    filled = int(round(ratio * length))
    empty  = length - filled
    bar = "█" * filled + " " * empty
    percent = int(round(ratio * 100))
    return f"[{bar}] {percent}%"


def build_talk_text(talk: Talk) -> str:
    date_str = timezone.localtime(talk.event.date).strftime("%d.%m.%Y")
    time_range = f"{talk.start_time.strftime('%H:%M')}–{talk.end_time.strftime('%H:%M')}"
    progress = build_progress_bar(talk)
    return (
        f"{talk.title}\n"
        f"Докладчик: {talk.speaker.get_full_name() or talk.speaker.username}\n"
        f"{date_str}  {time_range}\n\n"
        f"{talk.description}\n\n"
        f"{progress}"
    )


def program_markup(event: Event) -> InlineKeyboardMarkup:
    now = timezone.localtime()
    buttons = []
    for talk in event.talks.order_by("start_time"):
        start = timezone.make_aware(datetime.combine(event.date.date(), talk.start_time))
        end = timezone.make_aware(datetime.combine(event.date.date(), talk.end_time))
        start, end = map(timezone.localtime, (start, end))
        is_current = start <= now <= end
        indicator = "🟢 " if is_current else ""
        time_str = talk.start_time.strftime("%H:%M")
        speaker = talk.speaker.get_full_name() or talk.speaker.username
        title = talk.title
        text = f"{indicator}{time_str} {speaker} — {title}"
        buttons.append([InlineKeyboardButton(text=text, callback_data=f"talk_{talk.id}")])
    return InlineKeyboardMarkup(buttons)


def talk_markup(talk_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Задать вопрос", callback_data=f"ask_{talk_id}")],
        [InlineKeyboardButton("Вернуться к программе", callback_data="back_program")],
    ])


def schedule_program_timer(bot, chat_id, message_id, event):
    stop_updater(chat_id)
    stop_event = threading.Event()
    UPDATERS[chat_id] = stop_event
    def worker():
        while not stop_event.is_set():
            try:
                bot.edit_message_text(
                    chat_id=chat_id,
                    message_id=message_id,
                    text=build_program_text(event),
                    reply_markup=program_markup(event),
                )
            except Exception:
                pass
            if timezone.localtime() >= timezone.localtime(event.date):
                break
            stop_event.wait(60)
    threading.Thread(target=worker, daemon=True).start()


def schedule_talk_timer(bot, chat_id, message_id, talk):
    stop_updater(chat_id)
    stop_event = threading.Event()
    UPDATERS[chat_id] = stop_event
    def worker():
        while not stop_event.is_set():
            try:
                bot.edit_message_text(
                    chat_id=chat_id,
                    message_id=message_id,
                    text=build_talk_text(talk),
                    reply_markup=talk_markup(talk.id),
                )
            except Exception:
                pass
            end = timezone.make_aware(datetime.combine(talk.event.date.date(), talk.end_time))
            if timezone.localtime() >= timezone.localtime(end):
                break
            stop_event.wait(60)
    threading.Thread(target=worker, daemon=True).start()


class Command(BaseCommand):
    help = "Запускает AskTheSpeakerBot"

    def handle(self, *args, **options):
        token = getattr(settings, "TELEGRAM_BOT_TOKEN", None)
        if not token:
            raise CommandError("TELEGRAM_BOT_TOKEN не задан в settings.py")
        bot = telebot.TeleBot(token, parse_mode="HTML")

        def show_program(chat_id, *, via_edit=None):
            now = timezone.now()
            upcoming_events = Event.objects.filter(date__gte=now - timedelta(days=1)).order_by("date")
            active_event = next((e for e in upcoming_events if e.is_active), None)
            if not active_event:
                text = "Митапов не запланировано."
                if via_edit:
                    try:
                        bot.edit_message_text(chat_id=chat_id, message_id=via_edit.id, text=text)
                    except Exception:
                        bot.send_message(chat_id, text)
                else:
                    bot.send_message(chat_id, text)
                stop_updater(chat_id)
                return
            text = build_program_text(active_event)
            markup = program_markup(active_event)
            if via_edit:
                try:
                    bot.edit_message_text(
                        chat_id=chat_id,
                        message_id=via_edit.id,
                        text=text,
                        reply_markup=markup,
                    )
                    msg_id = via_edit.id
                except Exception:
                    msg = bot.send_message(chat_id, text, reply_markup=markup)
                    msg_id = msg.message_id
            else:
                msg = bot.send_message(chat_id, text, reply_markup=markup)
                msg_id = msg.message_id
            schedule_program_timer(bot, chat_id, msg_id, active_event)

        @bot.message_handler(commands=["start"])
        def start_handler(msg):
            chat_id = msg.chat.id
            tg_user = msg.from_user
            if UserProfile.objects.filter(telegram_id=str(tg_user.id)).exists():
                show_program(chat_id)
                return
            caption = "Если хотите принять участие, нажмите \"Продолжить\"."
            markup = InlineKeyboardMarkup([[InlineKeyboardButton("Продолжить", callback_data="register")]])
            if os.path.isfile(LOGO_PATH):
                with open(LOGO_PATH, "rb") as p:
                    bot.send_photo(chat_id, p, caption=caption, reply_markup=markup)
            else:
                bot.send_message(chat_id, caption, reply_markup=markup)

        @bot.callback_query_handler(func=lambda c: c.data == "register")
        def cb_register(call):
            chat_id = call.message.chat.id
            tg_user = call.from_user
            if not UserProfile.objects.filter(telegram_id=str(tg_user.id)).exists():
                from django.contrib.auth.models import User
                username = tg_user.username or f"tg_{tg_user.id}"
                user, _ = User.objects.get_or_create(username=username)
                UserProfile.objects.create(user=user, telegram_id=str(tg_user.id))
            bot.answer_callback_query(call.id, text="Регистрация завершена")
            show_program(chat_id, via_edit=call.message)

        @bot.callback_query_handler(func=lambda c: c.data.startswith("talk_"))
        def cb_talk(call):
            chat_id = call.message.chat.id
            talk_id = int(call.data.split("_")[1])
            talk = Talk.objects.select_related("event", "speaker").get(id=talk_id)
            bot.edit_message_text(chat_id=chat_id, message_id=call.message.id,
                                  text=build_talk_text(talk), reply_markup=talk_markup(talk.id))
            bot.answer_callback_query(call.id)
            schedule_talk_timer(bot, chat_id, call.message.id, talk)

        @bot.callback_query_handler(func=lambda c: c.data == "back_program")
        def cb_back(call):
            bot.answer_callback_query(call.id)
            show_program(call.message.chat.id, via_edit=call.message)

        @bot.callback_query_handler(func=lambda c: c.data.startswith("ask_"))
        def cb_ask(call):
            talk_id = int(call.data.split("_")[1])
            PENDING_QUESTION[call.from_user.id] = talk_id
            bot.answer_callback_query(call.id)
            bot.send_message(call.message.chat.id, "Напишите свой вопрос:")

        @bot.callback_query_handler(func=lambda c: c.data.startswith("reply_"))
        def cb_reply_to_question(call):
            question_id = int(call.data.split("_")[1])
            PENDING_ANSWER[call.from_user.id] = question_id
            bot.answer_callback_query(call.id)
            bot.send_message(call.message.chat.id, "Напишите ваш ответ:")

        @bot.message_handler(func=lambda m: m.from_user.id in PENDING_QUESTION)
        def handle_question(msg):
            user_id = msg.from_user.id
            talk_id = PENDING_QUESTION.pop(user_id)
            talk = Talk.objects.select_related("speaker", "speaker__userprofile").get(id=talk_id)
            user_obj = None
            try:
                profile = UserProfile.objects.get(telegram_id=str(msg.from_user.id))
                user_obj = profile.user
            except UserProfile.DoesNotExist:
                pass
            Question.objects.create(talk=talk, user=user_obj, text=msg.text.strip())
            bot.reply_to(msg, "Вопрос отправлен докладчику.")
            try:
                profile = talk.speaker.userprofile
            except UserProfile.DoesNotExist:
                pass
        
        @bot.message_handler(func=lambda m: m.from_user.id in PENDING_ANSWER)
        def handle_answer(msg):
            speaker_id = msg.from_user.id
            question_id = PENDING_ANSWER.pop(speaker_id)
            try:
                question = Question.objects.select_related("user", "talk").get(id=question_id)
                question.answer = msg.text.strip()
                question.save()
                bot.reply_to(msg, "Ответ сохранён и отправлен слушателю.")
            except Question.DoesNotExist:
                bot.reply_to(msg, "Вопрос не найден.")

        @bot.message_handler(func=lambda m: UserProfile.objects.filter(telegram_id=str(m.from_user.id), is_speaker=True).exists())
        def handle_speaker_answer(message):
            import re
            from django.contrib.auth.models import User
            RE_ANSWER = re.compile(r"^ответ\s+на\s+вопрос\s*#(?P<qid>\d+):\s*(?P<answer>.+)", re.IGNORECASE | re.DOTALL)
            match = RE_ANSWER.match(message.text.strip())
            if not match:
                return
            qid = match.group("qid")
            answer = match.group("answer").strip()
            try:
                question = Question.objects.select_related("talk", "user").get(id=qid)
            except Question.DoesNotExist:
                bot.send_message(message.chat.id, f"Вопрос с ID #{qid} не найден.")
                return
            speaker_profile = UserProfile.objects.get(telegram_id=str(message.from_user.id))
            if speaker_profile.user != question.talk.speaker:
                bot.send_message(message.chat.id, "Вы не являетесь спикером этого доклада.")
                return
            question.answer = answer
            question.save()
            bot.send_message(message.chat.id, "Ответ сохранён.")
            if question.user:
                try:
                    listener_profile = question.user.userprofile
                    if listener_profile.telegram_id:
                        bot.send_message(
                            listener_profile.telegram_id,
                            f"Ответ на ваш вопрос к докладу «{question.talk.title}»:\n\n{answer}"
                        )
                except UserProfile.DoesNotExist:
                    pass

        self.stdout.write(self.style.SUCCESS("AskTheSpeakerBot запущен."))
        bot.infinity_polling(skip_pending=True)
