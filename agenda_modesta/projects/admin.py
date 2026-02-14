from django.contrib import admin

from .models import Projeto


@admin.register(Projeto)
class ProjetoAdmin(admin.ModelAdmin):
    list_display = ["nome", "cliente", "status", "data_inicio", "ativo", "data_criacao"]
    list_filter = ["status", "ativo"]
    search_fields = ["nome", "cliente__nome"]
    readonly_fields = ["id", "data_criacao", "data_atualizacao"]
