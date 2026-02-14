from django.contrib import admin

from .models import Orcamento, Recibo, PacoteServico


@admin.register(PacoteServico)
class PacoteServicoAdmin(admin.ModelAdmin):
    list_display = ["nome", "horas_inclusas", "valor_hora_pacote", "ativo"]
    list_filter = ["ativo"]
    search_fields = ["nome"]


@admin.register(Orcamento)
class OrcamentoAdmin(admin.ModelAdmin):
    list_display = ["numero_sequencial", "cliente", "valor_total", "status_pagamento", "data_emissao"]
    list_filter = ["status_pagamento", "forma_pagamento"]
    search_fields = ["cliente__nome", "numero_sequencial"]
    readonly_fields = ["id", "data_criacao", "data_atualizacao"]


@admin.register(Recibo)
class ReciboAdmin(admin.ModelAdmin):
    list_display = ["numero_sequencial", "cliente", "valor_total", "forma_pagamento", "data_emissao"]
    list_filter = ["forma_pagamento"]
    search_fields = ["cliente__nome", "numero_sequencial"]
    readonly_fields = ["id", "data_criacao", "data_atualizacao"]
