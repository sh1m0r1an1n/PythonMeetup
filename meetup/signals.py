from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Question
from django.conf import settings
from telebot import TeleBot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

bot = TeleBot(settings.TELEGRAM_BOT_TOKEN, parse_mode="HTML")

PENDING_ANSWER = {}


@receiver(post_save, sender=Question)
def notify_user_on_answer(sender, instance, created, **kwargs):
    if created:
        if hasattr(instance.talk.speaker, "userprofile"):
            tg_id = instance.talk.speaker.userprofile.telegram_id
            if tg_id:
                text = (
                    f"Вопрос к докладу «{instance.talk.title}»\n"
                    f"От: @{instance.user.username if instance.user else 'аноним'}\n\n"
                    f"{instance.text}"
                )
                markup = InlineKeyboardMarkup([
                    [InlineKeyboardButton("Ответить на вопрос", callback_data=f"reply_{instance.id}")]
                ])
                bot.send_message(tg_id, text, reply_markup=markup)
    else:
        if instance.answer and instance.user and hasattr(instance.user, "userprofile"):
            tg_id = instance.user.userprofile.telegram_id
            if tg_id:
                bot.send_message(
                    tg_id,
                    f"Ответ от спикера на ваш вопрос к докладу «{instance.talk.title}»:\n\n{instance.answer}"
                )
