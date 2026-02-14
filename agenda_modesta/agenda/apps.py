from django.apps import AppConfig


class AgendaConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'agenda_modesta.agenda'
    verbose_name = 'Agenda'

    def ready(self):
        import agenda_modesta.agenda.signals  # noqa: F401
