from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from .models import Question, Event, Talk
from django.conf import settings
from telebot import TeleBot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

bot = TeleBot(settings.TELEGRAM_BOT_TOKEN, parse_mode="HTML")

PENDING_ANSWER = {}

_talk_pre_save_instances = {}


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


@receiver(post_save, sender=Event)
def handle_event_notifications(sender, instance, created, **kwargs):
    """Обрабатывает уведомления при создании или изменении мероприятия."""
    from .services import notify_upcoming_event, notify_event_change
    
    if created:
        notify_upcoming_event(instance)
    else:
        notify_event_change(instance, "Обновлена информация о мероприятии")


@receiver(pre_save, sender=Talk)
def store_talk_pre_save_instance(sender, instance, **kwargs):
    """Сохраняет состояние Talk перед изменением для отслеживания изменений."""
    if instance.pk:
        try:
            _talk_pre_save_instances[instance.pk] = Talk.objects.get(pk=instance.pk)
        except Talk.DoesNotExist:
            _talk_pre_save_instances[instance.pk] = None
    else:
        _talk_pre_save_instances[instance.pk] = None


@receiver(post_save, sender=Talk)
def handle_talk_notifications(sender, instance, created, **kwargs):
    """Обрабатывает уведомления при создании или изменении доклада."""
    from .services import notify_speaker, notify_program_change
    
    if created:
        notify_speaker(instance)
        notify_program_change(instance)
    else:
        old_instance = _talk_pre_save_instances.get(instance.pk)
        
        fields_changed = (
            not old_instance or
            old_instance.title != instance.title or
            old_instance.description != instance.description or
            old_instance.start_time != instance.start_time or
            old_instance.end_time != instance.end_time or
            old_instance.speaker_id != instance.speaker_id
        )
        
        if fields_changed:
            notify_program_change(instance)
    
    if instance.pk in _talk_pre_save_instances:
        del _talk_pre_save_instances[instance.pk]
