from django.contrib import admin

from .models import Agenda


@admin.register(Agenda)
class AgendaAdmin(admin.ModelAdmin):
    list_display = ["titulo", "usuario", "projeto", "data_inicio", "data_fim", "confirmado"]
    list_filter = ["confirmado", "origem"]
    search_fields = ["titulo", "projeto__nome", "projeto__cliente__nome", "usuario__username"]
    readonly_fields = ["id", "data_criacao", "data_atualizacao", "google_event_id"]
