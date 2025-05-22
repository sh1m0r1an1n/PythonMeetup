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

    def talks_count(self, obj):
        return obj.talks.count()
    talks_count.short_description = "Количество докладов"


@admin.register(Talk)
class TalkAdmin(admin.ModelAdmin):
    list_display = ("title", "event", "speaker", "start_time", "end_time", "is_active")
    list_filter = ("event", "speaker")
    search_fields = ("title", "description", "speaker__username")
    raw_id_fields = ("speaker",)
    list_select_related = ("event", "speaker")


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ("text_preview", "talk", "user", "created_at")
    list_filter = ("created_at", "talk")
    search_fields = ("text", "user__username", "talk__title")
    raw_id_fields = ("user", "talk")
    list_select_related = ("user", "talk")
    date_hierarchy = "created_at"

    def text_preview(self, obj):
        return format_html(
            '<span title="{}">{}</span>',
            obj.text,
            obj.text[:50] + "..." if len(obj.text) > 50 else obj.text
        )
    text_preview.short_description = "Текст вопроса"


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "telegram_id", "is_speaker", "is_organizer", "subscribed_to_notifications")
    list_filter = ("is_speaker", "is_organizer", "subscribed_to_notifications")
    search_fields = ("user__username", "telegram_id")
    raw_id_fields = ("user",)
    list_per_page = 20
    list_display_links = ("user",)
