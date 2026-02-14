from django.contrib import admin

from .models import Cliente


@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ["nome", "email", "telefone", "cidade", "ativo", "data_criacao"]
    list_filter = ["ativo", "cidade"]
    search_fields = ["nome", "email", "cpf_cnpj"]
    readonly_fields = ["id", "data_criacao", "data_atualizacao"]
