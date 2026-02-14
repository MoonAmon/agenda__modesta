import uuid
from django.db import models
from django.conf import settings

class Subscritor(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    usuario = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='subscritor',
    )

    nome_empresa = models.CharField(max_length=255, blank=True)
    logo = models.ImageField(upload_to='subscriptions/logos', null=True, blank=True)

    ativo = models.BooleanField(default=True)
    data_criacao = models.DateTimeField(auto_now_add=True)
    data_atualizacao = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.nome_empresa or self.usuario.get_full_name()
