import uuid
from django.db import models
from django.conf import settings
from djmoney.models.fields import MoneyField

from agenda_modesta.subscriptions.models import Subscritor
from agenda_modesta.clients.models import Cliente
from agenda_modesta.projects.models import Projeto

class PacoteServico(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    subscritor = models.ForeignKey(
        Subscritor,
        on_delete=models.CASCADE,
        related_name="pacotes",
    )
    usuario = models.ForeignKey(  # quem criou/gerencia o pacote
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="pacotes_criados",
    )

    nome = models.CharField(max_length=150)  # ex.: "Hora avulsa", "Pacote 10h + Otimização"
    descricao = models.TextField(blank=True)

    # Horas totais incluídas no pacote (None/0 para hora avulsa)
    horas_inclusas = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        null=True,
        blank=True,
    )

    # Se o pacote for baseado em hora, quanto custa cada hora nesse pacote
    valor_hora_pacote = MoneyField(
        max_digits=10,
        decimal_places=2,
        default_currency="BRL",
    )

    # Valor de referência "cheio" por hora (ex.: 390/h) para exibir desconto
    valor_hora_referencia = MoneyField(
        max_digits=10,
        decimal_places=2,
        default_currency="BRL",
        null=True,
        blank=True,
    )

    # Indica se inclui otimização naquele pacote
    inclui_otimizacao = models.BooleanField(default=False)

    # Benefícios extras (direção de arte, vinheta, desconto vitalício, etc.)
    beneficios = models.TextField(
        blank=True,
        help_text="Descreva bônus como direção de arte, vinheta, desconto vitalício, etc.",
    )

    ativo = models.BooleanField(default=True)
    data_criacao = models.DateTimeField(auto_now_add=True)
    data_atualizacao = models.DateTimeField(auto_now=True)

    def __str__(self):
        if self.horas_inclusas:
            return f"{self.nome} - {self.horas_inclusas}h a {self.valor_hora_pacote}/h"
        return f"{self.nome} - {self.valor_hora_pacote}/h"

class FormaPagamento(models.TextChoices):
    PIX = "pix", "Pix"
    DINHEIRO = "dinheiro", "Dinheiro"
    CARTAO = "cartao", "Cartão"
    TRANSFERENCIA = "transferencia", "Transferência"


class StatusPagamento(models.TextChoices):
    PENDENTE = "pendente", "Pendente"
    PAGO = "pago", "Pago"


class Orcamento(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="orcamentos",
    )
    subscritor = models.ForeignKey(
        Subscritor,
        on_delete=models.CASCADE,
        related_name="orcamentos",
    )
    cliente = models.ForeignKey(
        Cliente,
        on_delete=models.CASCADE,
        related_name="orcamentos",
    )
    projeto = models.ForeignKey(
        Projeto,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="orcamentos",
    )

    numero_sequencial = models.IntegerField()
    descricao = models.TextField(blank=True)

    horas_trabalhadas = models.DecimalField(max_digits=8, decimal_places=2)
    valor_hora = models.DecimalField(max_digits=8, decimal_places=2)
    valor_total = models.DecimalField(max_digits=10, decimal_places=2)

    forma_pagamento = models.CharField(
        max_length=20,
        choices=FormaPagamento.choices,
        default=FormaPagamento.PIX,
    )
    status_pagamento = models.CharField(
        max_length=20,
        choices=StatusPagamento.choices,
        default=StatusPagamento.PENDENTE,
    )

    data_emissao = models.DateField(auto_now_add=True)
    data_validade = models.DateField(null=True, blank=True)

    pdf_gerado = models.FileField(upload_to="orcamentos/", null=True, blank=True)

    data_criacao = models.DateTimeField(auto_now_add=True)
    data_atualizacao = models.DateTimeField(auto_now=True)

    pacote = models.ForeignKey(
        PacoteServico,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="orcamentos",
    )

    def calcular_valor_total(self):
        # Se tiver pacote, calcula pela regar do pacote
        if self.pacote:
            if self.pacote.horas_inclusas:
                # Pacote fechado (10h, 20h, 40h)
                return self.pacote.valor_hora_pacote * self.pacote.horas_inclusas
            return self.pacote.valor_hora_pacote * self.horas_trabalhadas

        # Se não tiver pacote, calcula normalmente
        return self.valor_hora * self.horas_trabalhadas

    def __str__(self):
        return f"Orçamento #{self.numero_sequencial}"


class Recibo(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="recibos",
    )
    subscritor = models.ForeignKey(
        Subscritor,
        on_delete=models.CASCADE,
        related_name="recibos",
    )
    cliente = models.ForeignKey(
        Cliente,
        on_delete=models.CASCADE,
        related_name="recibos",
    )
    projeto = models.ForeignKey(
        Projeto,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="recibos",
    )

    numero_sequencial = models.IntegerField()
    descricao = models.TextField(blank=True)

    horas_trabalhadas = models.DecimalField(max_digits=8, decimal_places=2)
    valor_hora = models.DecimalField(max_digits=8, decimal_places=2)
    valor_total = models.DecimalField(max_digits=10, decimal_places=2)

    forma_pagamento = models.CharField(
        max_length=20,
        choices=FormaPagamento.choices,
        default=FormaPagamento.PIX,
    )

    data_emissao = models.DateField(auto_now_add=True)
    pdf_gerado = models.FileField(upload_to="recibos/", null=True, blank=True)

    data_criacao = models.DateTimeField(auto_now_add=True)
    data_atualizacao = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Recibo #{self.numero_sequencial}"


