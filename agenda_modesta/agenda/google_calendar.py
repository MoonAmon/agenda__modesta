"""
Integração bilateral com Google Calendar via Service Account.

Requer UMA das opções:
  GOOGLE_CALENDAR_CREDENTIALS_FILE – caminho para o arquivo JSON da service account
  GOOGLE_CALENDAR_CREDENTIALS_JSON – JSON da chave da service account (string)

E obrigatoriamente:
  GOOGLE_CALENDAR_ID – ID do calendário compartilhado

Para receber push notifications (webhook):
  GOOGLE_CALENDAR_WEBHOOK_URL – URL pública https que o Google chamará
                                 ex.: https://meudominio.com/agenda/google/webhook/
"""

import json
import logging
import uuid
from datetime import datetime, timedelta, timezone as dt_tz

from django.conf import settings
from django.utils import timezone
from google.oauth2 import service_account
from googleapiclient.discovery import build

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Autenticação
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# App → Google (push de eventos)
# ---------------------------------------------------------------------------

def criar_evento(agenda):
    """Cria um evento no Google Calendar e retorna o event_id."""
    service = get_calendar_service()
    event_body = _agenda_to_event_body(agenda)
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
    event_body = _agenda_to_event_body(agenda)
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


def _agenda_to_event_body(agenda):
    """Converte uma instância Agenda em dict compatível com a API do Google."""
    tz = getattr(settings, "GOOGLE_CALENDAR_TIMEZONE", "America/Sao_Paulo")
    body = {
        "summary": agenda.titulo,
        "description": agenda.descricao,
        "start": {"dateTime": agenda.data_inicio.isoformat(), "timeZone": tz},
        "end": {"dateTime": agenda.data_fim.isoformat(), "timeZone": tz},
        "location": agenda.local or "",
        "extendedProperties": {
            "private": {"agenda_modesta_id": str(agenda.pk)},
        },
    }
    return body


# ---------------------------------------------------------------------------
# Google → App (pull de eventos)
# ---------------------------------------------------------------------------

def listar_eventos(max_results=10, days_ahead=30):
    """
    Lista os próximos eventos do calendário compartilhado do Google.
    """
    try:
        service = get_calendar_service()
    except Exception:
        logger.exception("Falha ao conectar ao Google Calendar")
        return []

    now = datetime.now(dt_tz.utc)
    time_min = now.isoformat().replace("+00:00", "Z")
    time_max = (now + timedelta(days=days_ahead)).isoformat().replace("+00:00", "Z")

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


def buscar_evento(event_id: str) -> dict | None:
    """Busca um único evento pelo ID."""
    service = get_calendar_service()
    try:
        return (
            service.events()
            .get(calendarId=settings.GOOGLE_CALENDAR_ID, eventId=event_id)
            .execute()
        )
    except Exception:
        logger.exception("Erro ao buscar evento %s", event_id)
        return None


def listar_eventos_alterados(sync_token: str = "") -> tuple[list[dict], str]:
    """
    Faz sync incremental via syncToken.
    Retorna (lista_de_eventos, next_sync_token).
    Na primeira chamada (sem token), traz todos os eventos futuros.
    """
    service = get_calendar_service()
    kwargs = {
        "calendarId": settings.GOOGLE_CALENDAR_ID,
        "singleEvents": True,
    }
    if sync_token:
        kwargs["syncToken"] = sync_token
    else:
        # Primeira sincronização: eventos dos últimos 30 dias + futuros
        now = datetime.now(dt_tz.utc)
        kwargs["timeMin"] = (now - timedelta(days=30)).isoformat().replace("+00:00", "Z")

    all_items = []
    page_token = None

    while True:
        if page_token:
            kwargs["pageToken"] = page_token

        try:
            result = service.events().list(**kwargs).execute()
        except Exception as exc:
            # 410 GONE → syncToken expirou, precisa full sync
            if hasattr(exc, "resp") and exc.resp.status == 410:
                logger.warning("syncToken expirado, fazendo full sync")
                return listar_eventos_alterados(sync_token="")
            raise

        all_items.extend(result.get("items", []))
        page_token = result.get("nextPageToken")
        if not page_token:
            break

    next_sync_token = result.get("nextSyncToken", "")
    return all_items, next_sync_token


# ---------------------------------------------------------------------------
# Webhook / Push Notifications
# ---------------------------------------------------------------------------

def registrar_webhook(subscritor) -> dict:
    """
    Registra um canal de push notification no Google Calendar.
    Retorna dict com channel_id, resource_id, expiration.
    """
    from .models import GoogleCalendarChannel

    service = get_calendar_service()
    webhook_url = getattr(settings, "GOOGLE_CALENDAR_WEBHOOK_URL", "")
    if not webhook_url:
        raise RuntimeError("GOOGLE_CALENDAR_WEBHOOK_URL não configurada.")

    channel_id = str(uuid.uuid4())
    # Google permite até ~30 dias de TTL
    expiration_ms = int((datetime.now(dt_tz.utc) + timedelta(days=14)).timestamp() * 1000)

    body = {
        "id": channel_id,
        "type": "web_hook",
        "address": webhook_url,
        "expiration": expiration_ms,
    }

    result = (
        service.events()
        .watch(calendarId=settings.GOOGLE_CALENDAR_ID, body=body)
        .execute()
    )

    expiration_dt = datetime.fromtimestamp(
        int(result["expiration"]) / 1000,
        tz=dt_tz.utc,
    )

    channel = GoogleCalendarChannel.objects.create(
        subscritor=subscritor,
        channel_id=result["id"],
        resource_id=result["resourceId"],
        google_calendar_id=settings.GOOGLE_CALENDAR_ID,
        expiration=expiration_dt,
    )

    logger.info(
        "Webhook registrado: channel=%s resource=%s expira=%s",
        channel.channel_id,
        channel.resource_id,
        channel.expiration,
    )
    return {
        "channel_id": channel.channel_id,
        "resource_id": channel.resource_id,
        "expiration": channel.expiration,
    }


def cancelar_webhook(channel):
    """Cancela um canal de push notification."""
    service = get_calendar_service()
    try:
        service.channels().stop(
            body={
                "id": channel.channel_id,
                "resourceId": channel.resource_id,
            }
        ).execute()
        logger.info("Webhook cancelado: %s", channel.channel_id)
    except Exception:
        logger.exception("Erro ao cancelar webhook %s", channel.channel_id)
    finally:
        channel.delete()


# ---------------------------------------------------------------------------
# Sincronização Google → App
# ---------------------------------------------------------------------------

def _parse_google_datetime(dt_dict: dict) -> datetime:
    """Converte start/end do Google para datetime aware."""
    from django.utils.dateparse import parse_datetime as dj_parse

    raw = dt_dict.get("dateTime") or dt_dict.get("date", "")
    if not raw:
        return timezone.now()
    dt = dj_parse(raw)
    if dt is None:
        # date-only (all day event)
        from datetime import date as _date
        d = _date.fromisoformat(raw)
        dt = datetime(d.year, d.month, d.day, tzinfo=dt_tz.utc)
    if timezone.is_naive(dt):
        dt = timezone.make_aware(dt)
    return dt


def sincronizar_eventos_google(subscritor, usuario, sync_token: str = ""):
    """
    Puxa eventos do Google Calendar e cria/atualiza/remove Agendas locais.
    Retorna o novo sync_token para futuras chamadas incrementais.
    """
    from .models import Agenda

    items, next_sync_token = listar_eventos_alterados(sync_token)
    criados = atualizados = removidos = 0

    for item in items:
        google_event_id = item.get("id", "")
        status = item.get("status", "")

        # Evento cancelado → remover localmente
        if status == "cancelled":
            deleted_count, _ = Agenda.objects.filter(
                google_event_id=google_event_id,
                subscritor=subscritor,
            ).delete()
            removidos += deleted_count
            continue

        # Verificar se é um evento que já veio da app (evita duplicar)
        ext_props = item.get("extendedProperties", {}).get("private", {})
        app_id = ext_props.get("agenda_modesta_id", "")

        # Se tem app_id, veio da app — atualizar somente campos que o Google pode mudar
        if app_id:
            try:
                agenda = Agenda.objects.get(pk=app_id, subscritor=subscritor)
            except Agenda.DoesNotExist:
                continue  # evento órfão, ignorar

            agenda.titulo = item.get("summary", agenda.titulo)
            agenda.descricao = item.get("description", agenda.descricao)
            agenda.local = item.get("location", agenda.local)
            agenda.data_inicio = _parse_google_datetime(item.get("start", {}))
            agenda.data_fim = _parse_google_datetime(item.get("end", {}))
            agenda.ultima_sincronizacao = timezone.now()
            agenda._skip_google_sync = True
            agenda.save()
            atualizados += 1
            continue

        # Evento criado diretamente no Google → criar Agenda local
        existing = Agenda.objects.filter(
            google_event_id=google_event_id,
            subscritor=subscritor,
        ).first()

        data_inicio = _parse_google_datetime(item.get("start", {}))
        data_fim = _parse_google_datetime(item.get("end", {}))

        if existing:
            existing.titulo = item.get("summary", "(Sem título)")
            existing.descricao = item.get("description", "")
            existing.local = item.get("location", "")
            existing.data_inicio = data_inicio
            existing.data_fim = data_fim
            existing.ultima_sincronizacao = timezone.now()
            existing._skip_google_sync = True
            existing.save()
            atualizados += 1
        else:
            agenda = Agenda(
                usuario=usuario,
                subscritor=subscritor,
                titulo=item.get("summary", "(Sem título)"),
                descricao=item.get("description", ""),
                data_inicio=data_inicio,
                data_fim=data_fim,
                local=item.get("location", ""),
                origem="google",
                google_event_id=google_event_id,
                google_calendar_id=settings.GOOGLE_CALENDAR_ID,
                confirmado=True,
                notificar_email=False,
                ultima_sincronizacao=timezone.now(),
            )
            agenda._skip_google_sync = True
            agenda.save()
            criados += 1

    logger.info(
        "Sincronização Google→App finalizada: criados=%d atualizados=%d removidos=%d",
        criados,
        atualizados,
        removidos,
    )
    return next_sync_token
