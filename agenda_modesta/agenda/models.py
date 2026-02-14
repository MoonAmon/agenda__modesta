import uuid
from django.db import models
from django.conf import settings

from agenda_modesta.subscriptions.models import Subscritor
from agenda_modesta.projects.models import Projeto

class Agenda(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="agendas",
    )
    subscritor = models.ForeignKey(
        Subscritor,
        on_delete=models.CASCADE,
        related_name="agendas",
    )

    titulo = models.CharField(max_length=150)
    descricao = models.TextField(blank=True)

    data_inicio = models.DateTimeField()
    data_fim = models.DateTimeField()

    confirmado = models.BooleanField(default=False)
    notificar_email = models.BooleanField(default=True)
    notificado = models.BooleanField(default=False)

    projeto = models.ForeignKey(
        Projeto,
        on_delete=models.CASCADE,
        related_name="agendamentos",
    )

    origem = models.CharField(
        max_length=20,
        choices=[("local", "Local"), ("google", "Google")],
        default="local",
    )
    local = models.CharField(max_length=150, blank=True)
    google_calendar_id = models.CharField(max_length=255, blank=True)
    google_event_id = models.CharField(max_length=255, blank=True, db_index=True)

    data_criacao = models.DateTimeField(auto_now_add=True)
    data_atualizacao = models.DateTimeField(auto_now=True)

    ultima_sicronizacao = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return self.titulo
