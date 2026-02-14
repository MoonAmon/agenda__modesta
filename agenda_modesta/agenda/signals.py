"""
Signals da app agenda – sincroniza com Google Calendar, Django Scheduler
e dispara notificações por e-mail via Celery.
"""

import logging

from django.conf import settings
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from .models import Agenda

logger = logging.getLogger(__name__)


def _google_calendar_enabled() -> bool:
    return bool(
        getattr(settings, "GOOGLE_CALENDAR_ID", "")
        and (
            getattr(settings, "GOOGLE_CALENDAR_CREDENTIALS_FILE", "")
            or getattr(settings, "GOOGLE_CALENDAR_CREDENTIALS_JSON", "")
        ),
    )


# ---------------------------------------------------------------------------
# Django Scheduler – sync
# ---------------------------------------------------------------------------

def _get_or_create_scheduler_calendar(subscritor):
    """Retorna (ou cria) o Calendar do django-scheduler para o subscritor."""
    from schedule.models import Calendar as ScheduleCalendar

    slug = f"subscritor-{subscritor.pk}"
    cal, _created = ScheduleCalendar.objects.get_or_create(
        slug=slug,
        defaults={"name": f"Agenda – {subscritor}"},
    )
    return cal


@receiver(post_save, sender=Agenda)
def sync_agenda_to_scheduler(sender, instance, created, **kwargs):
    """Cria ou atualiza um Event do django-scheduler ao salvar Agenda."""
    from schedule.models import Event as ScheduleEvent

    cal = _get_or_create_scheduler_calendar(instance.subscritor)

    # Cores por status
    color = "#10b981" if instance.confirmado else "#f59e0b"  # green / amber

    # Título com nome do cliente (via projeto)
    title = instance.titulo
    if instance.projeto and instance.projeto.cliente:
        title = f"{instance.titulo} – {instance.projeto.cliente.nome}"

    # Tentar encontrar evento existente vinculado via EventRelation ou por campo extra
    existing = ScheduleEvent.objects.filter(
        calendar=cal,
        description__contains=f"agenda_id:{instance.pk}",
    ).first()

    if existing:
        existing.title = title
        existing.start = instance.data_inicio
        existing.end = instance.data_fim
        existing.color_event = color
        existing.description = f"agenda_id:{instance.pk}\n{instance.descricao}"
        existing.save()
    else:
        ScheduleEvent.objects.create(
            calendar=cal,
            title=title,
            start=instance.data_inicio,
            end=instance.data_fim,
            color_event=color,
            creator=instance.usuario,
            description=f"agenda_id:{instance.pk}\n{instance.descricao}",
        )


@receiver(post_delete, sender=Agenda)
def delete_agenda_from_scheduler(sender, instance, **kwargs):
    """Remove o Event do django-scheduler ao deletar Agenda."""
    from schedule.models import Event as ScheduleEvent

    cal = _get_or_create_scheduler_calendar(instance.subscritor)
    ScheduleEvent.objects.filter(
        calendar=cal,
        description__contains=f"agenda_id:{instance.pk}",
    ).delete()


# ---------------------------------------------------------------------------
# Google Calendar – sync
# ---------------------------------------------------------------------------


@receiver(post_save, sender=Agenda)
def sync_agenda_google(sender, instance, created, **kwargs):
    """Cria ou atualiza evento no Google Calendar ao salvar Agenda."""
    if not _google_calendar_enabled():
        return

    from .google_calendar import atualizar_evento, criar_evento  # noqa: E402

    try:
        if created or not instance.google_event_id:
            event_id = criar_evento(instance)
        else:
            event_id = atualizar_evento(instance)

        if event_id and instance.google_event_id != event_id:
            Agenda.objects.filter(pk=instance.pk).update(google_event_id=event_id)
    except Exception:
        logger.exception("Erro ao sincronizar agenda %s com Google Calendar", instance.pk)


@receiver(post_delete, sender=Agenda)
def delete_agenda_google(sender, instance, **kwargs):
    """Remove evento do Google Calendar ao deletar Agenda."""
    if not _google_calendar_enabled():
        return

    from .google_calendar import deletar_evento  # noqa: E402

    try:
        deletar_evento(instance)
    except Exception:
        logger.exception("Erro ao deletar evento Google para agenda %s", instance.pk)


@receiver(post_save, sender=Agenda)
def enviar_notificacao_agenda(sender, instance, created, **kwargs):
    """Dispara e-mail de confirmação via Celery ao criar um agendamento."""
    if not created:
        return
    if not instance.notificar_email:
        return

    try:
        from agenda_modesta.notifications.tasks import enviar_email_confirmacao_agenda

        enviar_email_confirmacao_agenda.delay(str(instance.pk))
    except Exception:
        logger.exception("Erro ao enfileirar notificação para agenda %s", instance.pk)
