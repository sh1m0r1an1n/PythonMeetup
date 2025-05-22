from django.contrib import admin
from django.utils.html import format_html

from .models import Event, Talk, Question, UserProfile


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ("title", "date", "is_active", "talks_count")
    list_filter = ("date",)
    search_fields = ("title", "description")
    date_hierarchy = "date"
    ordering = ("-date",)
    list_display_links = ("title",)

    def talks_count(self, obj):
        return obj.talks.count()
    talks_count.short_description = "Количество докладов"


@admin.register(Talk)
class TalkAdmin(admin.ModelAdmin):
    list_display = ("title", "event", "speaker", "start_time", "end_time", "is_active", "questions_count")
    list_filter = ("event", "speaker")
    search_fields = ("title", "description", "speaker__username", "event__title")
    raw_id_fields = ("speaker", "event")
    list_select_related = ("event", "speaker")
    list_display_links = ("title",)
    date_hierarchy = "event__date"

    def questions_count(self, obj):
        return obj.questions.count()
    questions_count.short_description = "Количество вопросов"


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ("text_preview", "talk", "user", "created_at", "talk_event")
    list_filter = ("created_at", "talk", "talk__event")
    search_fields = ("text", "user__username", "talk__title", "talk__event__title")
    raw_id_fields = ("user", "talk")
    list_select_related = ("user", "talk", "talk__event")
    date_hierarchy = "created_at"
    list_display_links = ("text_preview",)

    def text_preview(self, obj):
        return format_html(
            '<span title="{}">{}</span>',
            obj.text,
            obj.text[:50] + "..." if len(obj.text) > 50 else obj.text
        )
    text_preview.short_description = "Текст вопроса"

    def talk_event(self, obj):
        return obj.talk.event
    talk_event.short_description = "Мероприятие"
    talk_event.admin_order_field = "talk__event__title"


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "telegram_id", "is_speaker", "is_organizer", "subscribed_to_notifications", "talks_count", "questions_count")
    list_filter = ("is_speaker", "is_organizer", "subscribed_to_notifications")
    search_fields = ("user__username", "user__email", "telegram_id")
    raw_id_fields = ("user",)
    list_display_links = ("user",)
    list_editable = ("is_speaker", "is_organizer", "subscribed_to_notifications")

    def talks_count(self, obj):
        return obj.user.speaker_talks.count()
    talks_count.short_description = "Количество докладов"

    def questions_count(self, obj):
        return obj.user.asked_questions.count()
    questions_count.short_description = "Количество вопросов"
