"""
Tasks Celery para envio de notificações por e-mail.
"""

import logging

from celery import shared_task
from django.core.mail import send_mail

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def enviar_email_confirmacao_agenda(self, agenda_id: str):
    """Envia e-mail de confirmação de agendamento."""
    from agenda_modesta.agenda.models import Agenda  # import local p/ evitar circularidade

    try:
        agenda = Agenda.objects.select_related("usuario", "projeto", "projeto__cliente").get(pk=agenda_id)
    except Agenda.DoesNotExist:
        logger.warning("Agenda %s não encontrada para notificação.", agenda_id)
        return

    cliente_nome = agenda.projeto.cliente.nome if agenda.projeto and agenda.projeto.cliente else "N/A"
    assunto = f"Confirmação de agendamento – {agenda.titulo}"
    mensagem = (
        f"Olá {agenda.usuario.nome_completo or agenda.usuario.name},\n\n"
        f"Seu agendamento está confirmado:\n"
        f"  Título : {agenda.titulo}\n"
        f"  Início : {agenda.data_inicio:%d/%m/%Y %H:%M}\n"
        f"  Fim    : {agenda.data_fim:%d/%m/%Y %H:%M}\n"
        f"  Cliente: {cliente_nome}\n"
        f"  Local  : {agenda.local or '—'}\n\n"
        "Atenciosamente,\nEstúdio Modesto"
    )

    try:
        send_mail(
            subject=assunto,
            message=mensagem,
            from_email=None,  # usa DEFAULT_FROM_EMAIL
            recipient_list=[agenda.usuario.email],
            fail_silently=False,
        )
        logger.info("E-mail de confirmação enviado para %s (agenda %s)", agenda.usuario.email, agenda_id)
    except Exception as exc:
        logger.exception("Falha ao enviar e-mail para agenda %s", agenda_id)
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def enviar_lembrete_agendamento(self, agenda_id: str):
    """Envia lembrete de agendamento (ex.: 24h antes)."""
    from agenda_modesta.agenda.models import Agenda

    try:
        agenda = Agenda.objects.select_related("usuario", "projeto", "projeto__cliente").get(pk=agenda_id)
    except Agenda.DoesNotExist:
        logger.warning("Agenda %s não encontrada para lembrete.", agenda_id)
        return

    cliente_nome = agenda.projeto.cliente.nome if agenda.projeto and agenda.projeto.cliente else "N/A"
    assunto = f"Lembrete de agendamento – {agenda.titulo}"
    mensagem = (
        f"Olá {agenda.usuario.nome_completo or agenda.usuario.name},\n\n"
        f"Lembrete: você tem um agendamento amanhã.\n"
        f"  Título : {agenda.titulo}\n"
        f"  Início : {agenda.data_inicio:%d/%m/%Y %H:%M}\n"
        f"  Fim    : {agenda.data_fim:%d/%m/%Y %H:%M}\n"
        f"  Cliente: {cliente_nome}\n"
        f"  Local  : {agenda.local or '—'}\n\n"
        "Atenciosamente,\nEstúdio Modesto"
    )

    try:
        send_mail(
            subject=assunto,
            message=mensagem,
            from_email=None,
            recipient_list=[agenda.usuario.email],
            fail_silently=False,
        )
        logger.info("Lembrete enviado para %s (agenda %s)", agenda.usuario.email, agenda_id)
    except Exception as exc:
        logger.exception("Falha ao enviar lembrete para agenda %s", agenda_id)
        raise self.retry(exc=exc)


@shared_task
def verificar_lembretes():
    """
    Periodic task (Celery Beat) – busca agendamentos nas próximas 24h
    que ainda não foram notificados e dispara lembretes.
    """
    from datetime import timedelta

    from django.utils import timezone

    from agenda_modesta.agenda.models import Agenda

    agora = timezone.now()
    limite = agora + timedelta(hours=24)

    agendamentos = Agenda.objects.filter(
        data_inicio__gte=agora,
        data_inicio__lte=limite,
        notificar_email=True,
        notificado=False,
    )

    enviados = 0
    for agenda in agendamentos:
        enviar_lembrete_agendamento.delay(str(agenda.pk))
        Agenda.objects.filter(pk=agenda.pk).update(notificado=True)
        enviados += 1

    logger.info("Lembretes enfileirados: %d", enviados)
    return enviados


# ---------------------------------------------------------------------------
# Google Calendar – sincronização bilateral
# ---------------------------------------------------------------------------


@shared_task(bind=True, max_retries=3, default_retry_delay=30)
def sincronizar_google_calendar(self, subscritor_id: str, sync_token: str = ""):
    """
    Task Celery disparada pelo webhook do Google Calendar.
    Faz sync incremental Google → App.
    """
    from agenda_modesta.agenda.google_calendar import sincronizar_eventos_google
    from agenda_modesta.agenda.models import GoogleCalendarChannel
    from agenda_modesta.subscriptions.models import Subscritor

    try:
        subscritor = Subscritor.objects.select_related("usuario").get(pk=subscritor_id)
    except Subscritor.DoesNotExist:
        logger.warning("Subscritor %s não encontrado para sync Google.", subscritor_id)
        return

    try:
        new_token = sincronizar_eventos_google(
            subscritor=subscritor,
            usuario=subscritor.usuario,
            sync_token=sync_token,
        )

        # Atualizar sync_token no canal mais recente
        channel = GoogleCalendarChannel.objects.filter(
            subscritor=subscritor,
        ).order_by("-criado_em").first()
        if channel and new_token:
            channel.sync_token = new_token
            channel.save(update_fields=["sync_token"])

        logger.info("Sync Google finalizado para subscritor %s", subscritor_id)
    except Exception as exc:
        logger.exception("Erro no sync Google para subscritor %s", subscritor_id)
        raise self.retry(exc=exc)


@shared_task
def renovar_webhooks_google():
    """
    Periodic task (Celery Beat) – renova webhooks que expiram em < 2 dias.
    Configurar no Django Admin do django-celery-beat para rodar diariamente.
    """
    from datetime import timedelta

    from django.utils import timezone

    from agenda_modesta.agenda.google_calendar import cancelar_webhook, registrar_webhook
    from agenda_modesta.agenda.models import GoogleCalendarChannel

    limite = timezone.now() + timedelta(days=2)
    channels = GoogleCalendarChannel.objects.filter(expiration__lte=limite)

    renovados = 0
    for ch in channels:
        old_token = ch.sync_token
        subscritor = ch.subscritor
        try:
            cancelar_webhook(ch)
            result = registrar_webhook(subscritor)

            # Preservar o sync_token do canal antigo
            GoogleCalendarChannel.objects.filter(
                channel_id=result["channel_id"],
            ).update(sync_token=old_token)

            renovados += 1
            logger.info("Webhook renovado para %s", subscritor)
        except Exception:
            logger.exception("Erro ao renovar webhook para %s", subscritor)

    logger.info("Webhooks renovados: %d", renovados)
    return renovados
