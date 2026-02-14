from django.apps import AppConfig


class SubscriptionsConfig(AppConfig):
    name = 'agenda_modesta.subscriptions'
    verbose_name = 'Subscriptions'

    def ready(self):
        import agenda_modesta.subscriptions.signals  # noqa: F401

