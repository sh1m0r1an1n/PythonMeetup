from django.conf import settings
from django.utils import timezone
import telebot
from telebot.apihelper import ApiTelegramException as TelegramError

from .models import Event, Talk, UserProfile


def get_telegram_bot():
    token = getattr(settings, "TELEGRAM_BOT_TOKEN", None)
    return telebot.TeleBot(token) if token else None


def send_telegram_message(telegram_id, message):
    """Отправляет сообщение пользователю в Telegram."""
    bot = get_telegram_bot()
    if not bot:
        return False

    try:
        bot.send_message(
            chat_id=telegram_id,
            text=message,
            parse_mode="HTML"
        )
        return True
    except TelegramError:
        return False


def notify_upcoming_event(event):
    """Отправляет уведомления о новом мероприятии."""
    message = (
        f"🎉 <b>Новое мероприятие!</b>\n\n"
        f"<b>{event.title}</b>\n"
        f"📅 {event.date.strftime('%d.%m.%Y %H:%M')}\n\n"
        f"{event.description}"
    )

    profiles = UserProfile.objects.filter(
        subscribed_to_notifications=True,
        telegram_id__isnull=False
    ).select_related("user")

    for profile in profiles:
        send_telegram_message(profile.telegram_id, message)


def notify_event_change(event, message):
    """Отправляет уведомления об изменении мероприятия."""
    full_message = (
        f"📢 <b>Обновление мероприятия</b>\n\n"
        f"<b>{event.title}</b>\n"
        f"📅 {event.date.strftime('%d.%m.%Y %H:%M')}\n\n"
        f"{message}"
    )

    profiles = UserProfile.objects.filter(
        subscribed_to_notifications=True,
        telegram_id__isnull=False
    ).select_related("user")

    for profile in profiles:
        send_telegram_message(profile.telegram_id, full_message)


def notify_speaker(talk):
    """Отправляет уведомление докладчику о новом докладе."""
    try:
        profile = talk.speaker.userprofile
        if not profile.telegram_id:
            return

        message = (
            f"🎤 <b>У вас новый доклад</b>\n\n"
            f"<b>{talk.title}</b>\n"
            f"📅 {talk.event.date.strftime('%d.%m.%Y')}\n"
            f"⏰ {talk.start_time.strftime('%H:%M')} - {talk.end_time.strftime('%H:%M')}\n\n"
            f"{talk.description}"
        )

        send_telegram_message(profile.telegram_id, message)
    except UserProfile.DoesNotExist:
        pass 


def notify_program_change(talk):
    """Уведомляет всех пользователей об изменении программы (докладов)."""
    try:
        event = talk.event
        message = (
            f"📌 <b>Изменения в программе мероприятия</b>\n\n"
            f"<b>{event.title}</b>\n"
            f"📅 {event.date.strftime('%d.%m.%Y')}\n\n"
            f"Обновлён доклад:\n"
            f"<b>{talk.title}</b>\n"
            f"⏰ {talk.start_time.strftime('%H:%M')} - {talk.end_time.strftime('%H:%M')}\n"
            f"🎤 {talk.speaker.get_full_name() or talk.speaker.username}\n\n"
            f"{talk.description}"
        )

        profiles = UserProfile.objects.filter(
            subscribed_to_notifications=True,
            telegram_id__isnull=False
        ).select_related("user")

        for profile in profiles:
            send_telegram_message(profile.telegram_id, message)

    except Exception as e:
        pass