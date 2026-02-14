from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.db.models import Sum

from agenda_modesta.clients.models import Cliente
from agenda_modesta.projects.models import Projeto
from agenda_modesta.agenda.models import Agenda
from agenda_modesta.finance.models import Orcamento
from agenda_modesta.core.utils import get_user_subscritor


def _get_calendar_slug(subscritor):
    """Retorna o slug do Calendar do django-scheduler para o subscritor."""
    from schedule.models import Calendar as ScheduleCalendar

    slug = f"subscritor-{subscritor.pk}"
    cal, _ = ScheduleCalendar.objects.get_or_create(
        slug=slug,
        defaults={"name": f"Agenda – {subscritor}"},
    )
    return cal.slug


@login_required
def dashboard(request):
    # Get or create subscritor for the user
    subscritor = get_user_subscritor(request.user)

    # Calendar slug for FullCalendar
    calendar_slug = _get_calendar_slug(subscritor)

    # Stats
    total_clientes = Cliente.objects.filter(subscritor=subscritor, ativo=True).count()
    projetos_andamento = Projeto.objects.filter(
        subscritor=subscritor,
        status='EM_ANDAMENTO'
    ).count()

    # Today's appointments
    today = timezone.now().date()
    agendamentos_hoje = Agenda.objects.filter(
        subscritor=subscritor,
        data_inicio__date=today
    ).count()

    # Pending orcamentos value
    orcamentos_pendentes = Orcamento.objects.filter(
        subscritor=subscritor,
        status_pagamento='pendente'
    )
    orcamentos_pendentes_valor = orcamentos_pendentes.aggregate(
        Sum('valor_total')
    )['valor_total__sum'] or 0

    # Upcoming appointments
    proximos_agendamentos = Agenda.objects.filter(
        subscritor=subscritor,
        data_inicio__gte=timezone.now()
    ).select_related('projeto', 'projeto__cliente').order_by('data_inicio')[:5]

    # Recent orcamentos
    orcamentos_recentes = Orcamento.objects.filter(
        subscritor=subscritor
    ).select_related('cliente').order_by('-data_criacao')[:5]

    context = {
        'total_clientes': total_clientes,
        'projetos_andamento': projetos_andamento,
        'agendamentos_hoje': agendamentos_hoje,
        'orcamentos_pendentes_valor': orcamentos_pendentes_valor,
        'proximos_agendamentos': proximos_agendamentos,
        'orcamentos_recentes': orcamentos_recentes,
        'calendar_slug': calendar_slug,
    }

    return render(request, 'pages/home.html', context)
