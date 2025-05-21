from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta


class Event(models.Model):
    """Модель для хранения информации о мероприятиях."""
    
    title = models.CharField(max_length=200, verbose_name="Название")
    date = models.DateTimeField(verbose_name="Дата и время", db_index=True)
    description = models.TextField(verbose_name="Описание")

    class Meta:
        verbose_name = "Мероприятие"
        verbose_name_plural = "Мероприятия"
        ordering = ["-date"]
        indexes = [models.Index(fields=["date"])]

    @property
    def is_active(self):
        """Проверяет, активно ли мероприятие."""
        return self.date.date() >= timezone.now().date()

    def save(self, *args, **kwargs):
        """Сохраняет мероприятие и отправляет уведомления."""
        is_new = self.pk is None
        super().save(*args, **kwargs)

        from .services import notify_upcoming_event, notify_event_change

        if is_new:
            notify_upcoming_event(self)
        else:
            notify_event_change(self, "Обновлена информация о мероприятии")

    def __str__(self):
        return f"{self.title} ({self.date})"


class Talk(models.Model):
    """Модель для хранения информации о докладах."""
    
    event = models.ForeignKey(
        Event,
        on_delete=models.CASCADE,
        related_name="talks",
        verbose_name="Мероприятие",
    )
    speaker = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="speaker_talks",
        verbose_name="Докладчик",
    )
    title = models.CharField(max_length=200, verbose_name="Название")
    description = models.TextField(verbose_name="Описание")
    start_time = models.TimeField(verbose_name="Время начала")
    end_time = models.TimeField(verbose_name="Время окончания")

    class Meta:
        verbose_name = "Доклад"
        verbose_name_plural = "Доклады"
        ordering = ["event", "start_time"]
        indexes = [models.Index(fields=["event", "start_time"])]

    def save(self, *args, **kwargs):
        """Сохраняет доклад и отправляет уведомления."""
        is_new = self.pk is None
        super().save(*args, **kwargs)

        if is_new:
            from .services import notify_speaker
            notify_speaker(self)

    @property
    def is_active(self):
        """Проверяет, активен ли доклад."""
        now = timezone.now()
        talk_start = timezone.make_aware(
            timezone.datetime.combine(self.event.date.date(), self.start_time)
        )
        talk_end = timezone.make_aware(
            timezone.datetime.combine(self.event.date.date(), self.end_time)
        )
        talk_end += timedelta(minutes=30)
        return talk_start <= now <= talk_end and self.event.is_active

    def __str__(self):
        return f"{self.title} by {self.speaker.username}"


class Question(models.Model):
    """Модель для хранения вопросов к докладам."""
    
    talk = models.ForeignKey(
        Talk,
        on_delete=models.CASCADE,
        related_name="questions",
        verbose_name="Доклад",
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="asked_questions",
        verbose_name="Пользователь",
    )
    text = models.TextField(verbose_name="Текст вопроса")
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Дата создания",
        db_index=True,
    )

    class Meta:
        verbose_name = "Вопрос"
        verbose_name_plural = "Вопросы"
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["created_at"])]

    def __str__(self):
        return f"Question for {self.talk.title}"


class UserProfile(models.Model):
    """Модель для хранения дополнительной информации о пользователях."""
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, verbose_name="Пользователь")
    telegram_id = models.CharField(max_length=100, unique=True, verbose_name="Telegram ID")
    is_speaker = models.BooleanField(default=False, verbose_name="Является докладчиком")
    subscribed_to_notifications = models.BooleanField(
        default=True,
        verbose_name="Подписан на уведомления",
    )

    class Meta:
        verbose_name = "Профиль пользователя"
        verbose_name_plural = "Профили пользователей"

    def __str__(self):
        return self.user.username
