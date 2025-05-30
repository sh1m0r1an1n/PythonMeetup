from django.apps import AppConfig


class MeetupConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "meetup"
    verbose_name = "Мероприятия"

    def ready(self):
        import meetup.signals
