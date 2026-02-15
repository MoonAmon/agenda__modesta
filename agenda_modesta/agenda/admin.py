from django.contrib import admin

from .models import Agenda, GoogleCalendarChannel


@admin.register(Agenda)
class AgendaAdmin(admin.ModelAdmin):
    list_display = [
        "titulo", "usuario", "projeto", "data_inicio", "data_fim",
        "confirmado", "origem", "google_event_id",
    ]
    list_filter = ["confirmado", "origem"]
    search_fields = ["titulo", "projeto__nome", "projeto__cliente__nome", "usuario__username"]
    readonly_fields = [
        "id", "data_criacao", "data_atualizacao",
        "google_event_id", "google_calendar_id", "ultima_sincronizacao",
    ]


@admin.register(GoogleCalendarChannel)
class GoogleCalendarChannelAdmin(admin.ModelAdmin):
    list_display = ["channel_id", "subscritor", "expiration", "criado_em"]
    readonly_fields = ["id", "channel_id", "resource_id", "criado_em"]
    list_filter = ["subscritor"]
