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
