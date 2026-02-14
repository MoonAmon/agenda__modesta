import uuid
from django.db import models
from django.conf import settings

from agenda_modesta.subscriptions.models import Subscritor
from agenda_modesta.clients.models import Cliente

class Projeto(models.Model):
    class StatusProjeto(models.TextChoices):
        PLANEJAMENTO = 'PLANEJAMENTO', 'Planejamento'
        EM_ANDAMENTO = 'EM_ANDAMENTO', 'Em andamento'
        CONCLUIDO = 'CONCLUIDO', 'Concluido'
        CANCELADO = 'CANCELADO', 'Cancelado'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='projetos'
    )
    subscritor = models.ForeignKey(
        Subscritor,
        on_delete=models.CASCADE,
        related_name='projetos'
    )
    cliente = models.ForeignKey(
        Cliente,
        on_delete=models.CASCADE,
        related_name='projetos'
    )

    nome = models.CharField(max_length=255)
    descricao = models.TextField(blank=True, null=True)
    status = models.CharField(
        max_length=20,
        choices=StatusProjeto.choices,
        default=StatusProjeto.PLANEJAMENTO
    )

    data_inicio = models.DateField(blank=True, null=True)
    data_prevista_conclusao = models.DateField(blank=True, null=True)
    data_conclusao = models.DateField(blank=True, null=True)

    ativo = models.BooleanField(default=True)
    data_criacao = models.DateTimeField(auto_now_add=True)
    data_atualizacao = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.nome
