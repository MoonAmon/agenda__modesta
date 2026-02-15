"""
Management command para sincronizar Google Calendar ↔ App.

Uso:
  python manage.py sync_google_calendar                # sync incremental
  python manage.py sync_google_calendar --full         # sync completo
  python manage.py sync_google_calendar --register     # registrar webhook
  python manage.py sync_google_calendar --unregister   # cancelar webhooks
"""

from django.core.management.base import BaseCommand

from agenda_modesta.agenda.google_calendar import (
    cancelar_webhook,
    registrar_webhook,
    sincronizar_eventos_google,
)
from agenda_modesta.agenda.models import GoogleCalendarChannel
from agenda_modesta.subscriptions.models import Subscritor


class Command(BaseCommand):
    help = "Sincroniza eventos entre Google Calendar e a aplicação."

    def add_arguments(self, parser):
        parser.add_argument(
            "--full",
            action="store_true",
            help="Ignora sync_token e faz sincronização completa.",
        )
        parser.add_argument(
            "--register",
            action="store_true",
            help="Registra webhook push notification no Google.",
        )
        parser.add_argument(
            "--unregister",
            action="store_true",
            help="Cancela todos os webhooks registrados.",
        )
        parser.add_argument(
            "--subscritor",
            type=str,
            default="",
            help="UUID do subscritor. Se omitido, processa todos.",
        )

    def handle(self, *args, **options):
        subscritores = self._get_subscritores(options["subscritor"])

        if options["unregister"]:
            self._unregister(subscritores)
            return

        if options["register"]:
            self._register(subscritores)

        self._sync(subscritores, full=options["full"])

    def _get_subscritores(self, subscritor_id: str):
        if subscritor_id:
            try:
                return [Subscritor.objects.get(pk=subscritor_id)]
            except Subscritor.DoesNotExist:
                self.stderr.write(f"Subscritor {subscritor_id} não encontrado.")
                return []
        return list(Subscritor.objects.filter(ativo=True))

    def _register(self, subscritores):
        for sub in subscritores:
            try:
                result = registrar_webhook(sub)
                self.stdout.write(
                    self.style.SUCCESS(
                        f"Webhook registrado para {sub}: "
                        f"channel={result['channel_id']} expira={result['expiration']}"
                    )
                )
            except Exception as exc:
                self.stderr.write(
                    self.style.ERROR(f"Erro ao registrar webhook para {sub}: {exc}")
                )

    def _unregister(self, subscritores):
        channels = GoogleCalendarChannel.objects.filter(
            subscritor__in=subscritores,
        )
        for ch in channels:
            cancelar_webhook(ch)
            self.stdout.write(
                self.style.SUCCESS(f"Webhook {ch.channel_id} cancelado.")
            )

    def _sync(self, subscritores, full: bool):
        for sub in subscritores:
            usuario = sub.usuario  # owner do subscritor

            channel = GoogleCalendarChannel.objects.filter(
                subscritor=sub,
            ).order_by("-criado_em").first()

            sync_token = "" if full else (channel.sync_token if channel else "")

            self.stdout.write(f"Sincronizando {sub} (full={full})…")
            try:
                new_token = sincronizar_eventos_google(
                    subscritor=sub,
                    usuario=usuario,
                    sync_token=sync_token,
                )
                if channel:
                    channel.sync_token = new_token
                    channel.save(update_fields=["sync_token"])
                self.stdout.write(
                    self.style.SUCCESS(f"Sincronização concluída para {sub}.")
                )
            except Exception as exc:
                self.stderr.write(
                    self.style.ERROR(f"Erro na sincronização de {sub}: {exc}")
                )
