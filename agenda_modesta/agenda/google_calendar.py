"""
Integração com Google Calendar via Service Account.

Requer UMA das opções:
  GOOGLE_CALENDAR_CREDENTIALS_FILE – caminho para o arquivo JSON da service account
  GOOGLE_CALENDAR_CREDENTIALS_JSON – JSON da chave da service account (string)

E obrigatoriamente:
  GOOGLE_CALENDAR_ID – ID do calendário compartilhado
"""

import json
import logging

from django.conf import settings
from google.oauth2 import service_account
from googleapiclient.discovery import build

logger = logging.getLogger(__name__)


def get_calendar_service():
    """Retorna um Resource do Google Calendar v3 autenticado."""
    creds_file = getattr(settings, "GOOGLE_CALENDAR_CREDENTIALS_FILE", "")
    creds_json = getattr(settings, "GOOGLE_CALENDAR_CREDENTIALS_JSON", "")

    if creds_file:
        credentials = service_account.Credentials.from_service_account_file(
            creds_file,
            scopes=settings.GOOGLE_CALENDAR_SCOPES,
        )
    elif creds_json:
        info = json.loads(creds_json)
        credentials = service_account.Credentials.from_service_account_info(
            info,
            scopes=settings.GOOGLE_CALENDAR_SCOPES,
        )
    else:
        raise RuntimeError(
            "Configure GOOGLE_CALENDAR_CREDENTIALS_FILE ou "
            "GOOGLE_CALENDAR_CREDENTIALS_JSON nas settings."
        )
    return build("calendar", "v3", credentials=credentials)


def criar_evento(agenda):
    """Cria um evento no Google Calendar e retorna o event_id."""
    service = get_calendar_service()
    event_body = {
        "summary": agenda.titulo,
        "description": agenda.descricao,
        "start": {
            "dateTime": agenda.data_inicio.isoformat(),
            "timeZone": "America/Sao_Paulo",
        },
        "end": {
            "dateTime": agenda.data_fim.isoformat(),
            "timeZone": "America/Sao_Paulo",
        },
        "location": agenda.local or "",
    }
    event = (
        service.events()
        .insert(
            calendarId=settings.GOOGLE_CALENDAR_ID,
            body=event_body,
        )
        .execute()
    )
    logger.info("Evento Google criado: %s", event["id"])
    return event["id"]


def atualizar_evento(agenda):
    """Atualiza um evento existente ou cria um novo se não houver ID."""
    if not agenda.google_event_id:
        return criar_evento(agenda)
    service = get_calendar_service()
    event_body = {
        "summary": agenda.titulo,
        "description": agenda.descricao,
        "start": {
            "dateTime": agenda.data_inicio.isoformat(),
            "timeZone": "America/Sao_Paulo",
        },
        "end": {
            "dateTime": agenda.data_fim.isoformat(),
            "timeZone": "America/Sao_Paulo",
        },
        "location": agenda.local or "",
    }
    event = (
        service.events()
        .update(
            calendarId=settings.GOOGLE_CALENDAR_ID,
            eventId=agenda.google_event_id,
            body=event_body,
        )
        .execute()
    )
    logger.info("Evento Google atualizado: %s", event["id"])
    return event["id"]


def deletar_evento(agenda):
    """Remove o evento do Google Calendar."""
    if not agenda.google_event_id:
        return
    service = get_calendar_service()
    service.events().delete(
        calendarId=settings.GOOGLE_CALENDAR_ID,
        eventId=agenda.google_event_id,
    ).execute()
    logger.info("Evento Google deletado: %s", agenda.google_event_id)


def listar_eventos(max_results=10, days_ahead=30):
    """
    Lista os próximos eventos do calendário compartilhado do Google.

    Args:
        max_results: número máximo de eventos a retornar.
        days_ahead: quantos dias no futuro buscar.

    Returns:
        Lista de dicts com id, summary, start, end, location, description e htmlLink.
        Retorna lista vazia em caso de erro.
    """
    from datetime import datetime, timedelta

    try:
        service = get_calendar_service()
    except Exception:
        logger.exception("Falha ao conectar ao Google Calendar")
        return []

    now = datetime.utcnow()
    time_min = now.isoformat() + "Z"
    time_max = (now + timedelta(days=days_ahead)).isoformat() + "Z"

    try:
        result = (
            service.events()
            .list(
                calendarId=settings.GOOGLE_CALENDAR_ID,
                timeMin=time_min,
                timeMax=time_max,
                maxResults=max_results,
                singleEvents=True,
                orderBy="startTime",
            )
            .execute()
        )
    except Exception:
        logger.exception("Erro ao listar eventos do Google Calendar")
        return []

    eventos = []
    for item in result.get("items", []):
        start = item.get("start", {})
        end = item.get("end", {})
        eventos.append(
            {
                "id": item.get("id"),
                "summary": item.get("summary", "(Sem título)"),
                "start": start.get("dateTime") or start.get("date", ""),
                "end": end.get("dateTime") or end.get("date", ""),
                "location": item.get("location", ""),
                "description": item.get("description", ""),
                "htmlLink": item.get("htmlLink", ""),
            }
        )
    return eventos
