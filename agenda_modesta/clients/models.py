import uuid
from django.db import models
from django.conf import settings
from simple_history.models import HistoricalRecords

from agenda_modesta.subscriptions.models import Subscritor

class Cliente(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='clientes'
    )
    subscritor = models.ForeignKey(
        Subscritor,
        on_delete=models.CASCADE,
        related_name='clientes'
    )

    nome = models.CharField(max_length=255)
    email = models.EmailField()
    telefone = models.CharField(max_length=20)
    cpf_cnpj = models.CharField(max_length=20)
    cidade = models.CharField(max_length=255)
    estado = models.CharField(max_length=2)
    endereco = models.CharField(max_length=255)

    ativo = models.BooleanField(default=True)
    data_criacao = models.DateTimeField(auto_now_add=True)
    data_atualizacao = models.DateTimeField(auto_now=True)

    history = HistoricalRecords()

    def __str__(self):
        return self.nome
