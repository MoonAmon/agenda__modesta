from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods, require_POST
from django.utils import timezone

from .models import Agenda, GoogleCalendarChannel
from .forms import AgendaForm, StepProjetoForm, StepDetalhesForm
from agenda_modesta.projects.models import Projeto
from agenda_modesta.core.utils import get_user_subscritor


@login_required
def agenda_list(request):
    subscritor = get_user_subscritor(request.user)
    agendamentos = Agenda.objects.filter(
        subscritor=subscritor
    ).select_related('projeto', 'projeto__cliente').order_by('data_inicio')

    # Filters
    q = request.GET.get('q', '')
    if q:
        agendamentos = agendamentos.filter(titulo__icontains=q) | agendamentos.filter(projeto__cliente__nome__icontains=q)

    data_inicio = request.GET.get('data_inicio', '')
    if data_inicio:
        agendamentos = agendamentos.filter(data_inicio__date__gte=data_inicio)

    data_fim = request.GET.get('data_fim', '')
    if data_fim:
        agendamentos = agendamentos.filter(data_inicio__date__lte=data_fim)

    confirmado = request.GET.get('confirmado', '')
    if confirmado == 'true':
        agendamentos = agendamentos.filter(confirmado=True)
    elif confirmado == 'false':
        agendamentos = agendamentos.filter(confirmado=False)

    # Default: show future appointments
    if not data_inicio and not data_fim:
        agendamentos = agendamentos.filter(data_inicio__gte=timezone.now())

    context = {'agendamentos': agendamentos}

    if request.htmx:
        return render(request, 'agenda/partials/agenda_list.html', context)

    return render(request, 'agenda/agenda_list.html', context)


@login_required
def agenda_create(request):
    subscritor = get_user_subscritor(request.user)
    projetos = Projeto.objects.filter(subscritor=subscritor, ativo=True)

    if request.method == 'POST':
        form = AgendaForm(request.POST)
        form.fields['projeto'].queryset = projetos
        if form.is_valid():
            agenda = form.save(commit=False)
            agenda.usuario = request.user
            agenda.subscritor = subscritor
            agenda.save()
            messages.success(request, 'Agendamento criado com sucesso!')
            return redirect('agenda:list')
    else:
        form = AgendaForm()
        form.fields['projeto'].queryset = projetos

    return render(request, 'agenda/agenda_form.html', {
        'form': form,
        'projetos': projetos,
    })


@login_required
def agenda_edit(request, pk):
    subscritor = get_user_subscritor(request.user)
    agenda = get_object_or_404(Agenda, pk=pk, subscritor=subscritor)
    projetos = Projeto.objects.filter(subscritor=subscritor, ativo=True)

    if request.method == 'POST':
        form = AgendaForm(request.POST, instance=agenda)
        form.fields['projeto'].queryset = projetos
        if form.is_valid():
            form.save()
            messages.success(request, 'Agendamento atualizado com sucesso!')
            return redirect('agenda:list')
    else:
        form = AgendaForm(instance=agenda)
        form.fields['projeto'].queryset = projetos

    return render(request, 'agenda/agenda_form.html', {
        'form': form,
        'agenda': agenda,
        'projetos': projetos,
    })


@login_required
@require_http_methods(["DELETE"])
def agenda_delete(request, pk):
    subscritor = get_user_subscritor(request.user)
    agenda = get_object_or_404(Agenda, pk=pk, subscritor=subscritor)
    agenda.delete()
    messages.success(request, 'Agendamento excluído com sucesso!')
    return HttpResponse("")


@login_required
@require_http_methods(["POST"])
def toggle_confirmado(request, pk):
    subscritor = get_user_subscritor(request.user)
    agenda = get_object_or_404(Agenda, pk=pk, subscritor=subscritor)
    agenda.confirmado = not agenda.confirmado
    agenda.save()

    # Return the updated row
    return render(request, 'agenda/partials/agenda_item.html', {'agenda': agenda})


# ============ HTMX – Novo Agendamento em Passos ============

@login_required
def novo_agendamento(request):
    """Retorna o partial do passo 1 (escolher projeto) dentro do modal."""
    subscritor = get_user_subscritor(request.user)
    projetos = Projeto.objects.filter(subscritor=subscritor, ativo=True)
    form = StepProjetoForm()
    form.fields["projeto"].queryset = projetos
    return render(request, "agenda/partials/step1_projeto.html", {"form": form})


@login_required
@require_http_methods(["POST"])
def step1_projeto(request):
    """Recebe o projeto escolhido (opcional) e retorna o passo 2 (detalhes)."""
    subscritor = get_user_subscritor(request.user)
    form = StepProjetoForm(request.POST)
    projetos = Projeto.objects.filter(subscritor=subscritor, ativo=True)
    form.fields["projeto"].queryset = projetos

    if not form.is_valid():
        return render(request, "agenda/partials/step1_projeto.html", {"form": form})

    projeto = form.cleaned_data.get("projeto")  # pode ser None
    detalhes_form = StepDetalhesForm()
    return render(request, "agenda/partials/step2_detalhes.html", {
        "form": detalhes_form,
        "projeto": projeto,
    })


@login_required
@require_http_methods(["POST"])
def step2_detalhes(request):
    """Recebe os detalhes e retorna o passo 3 (confirmação)."""
    subscritor = get_user_subscritor(request.user)
    projeto_id = request.POST.get("projeto_id")
    projeto = None
    if projeto_id:
        projeto = get_object_or_404(Projeto, pk=projeto_id, subscritor=subscritor)

    form = StepDetalhesForm(request.POST)
    if not form.is_valid():
        return render(request, "agenda/partials/step2_detalhes.html", {
            "form": form,
            "projeto": projeto,
        })

    return render(request, "agenda/partials/step3_confirmacao.html", {
        "projeto": projeto,
        "titulo": form.cleaned_data["titulo"],
        "descricao": form.cleaned_data["descricao"],
        "data_inicio": form.cleaned_data["data_inicio"],
        "data_fim": form.cleaned_data["data_fim"],
        "local": form.cleaned_data["local"],
    })


@login_required
@require_http_methods(["POST"])
def step3_confirmar(request):
    """Salva o agendamento definitivamente."""
    subscritor = get_user_subscritor(request.user)
    projeto_id = request.POST.get("projeto_id")
    projeto = None
    if projeto_id:
        projeto = get_object_or_404(Projeto, pk=projeto_id, subscritor=subscritor)

    form = StepDetalhesForm(request.POST)
    if not form.is_valid():
        return render(request, "agenda/partials/step2_detalhes.html", {
            "form": form,
            "projeto": projeto,
        })

    agenda = Agenda(
        usuario=request.user,
        subscritor=subscritor,
        projeto=projeto,
        titulo=form.cleaned_data["titulo"],
        descricao=form.cleaned_data["descricao"],
        data_inicio=form.cleaned_data["data_inicio"],
        data_fim=form.cleaned_data["data_fim"],
        local=form.cleaned_data["local"],
        confirmado=True,
        notificar_email=True,
    )
    agenda.save()
    messages.success(request, "Agendamento criado com sucesso!")

    # Retorna resposta que fecha o modal e recarrega a lista
    response = HttpResponse(status=204)
    response["HX-Trigger"] = "agendamentoCriado"
    return response


@login_required
def projetos_por_cliente(request):
    """API HTMX – retorna <option> de projetos filtrados por cliente."""
    subscritor = get_user_subscritor(request.user)
    cliente_id = request.GET.get("cliente")
    if not cliente_id:
        return HttpResponse('<option value="">—</option>')
    projetos = Projeto.objects.filter(
        subscritor=subscritor, cliente_id=cliente_id, ativo=True,
    )
    html = '<option value="">Selecione...</option>'
    for p in projetos:
        html += f'<option value="{p.pk}">{p.nome}</option>'
    return HttpResponse(html)


@login_required
def agenda_week_json(request):
    """Retorna os agendamentos da semana em JSON para o calendário semanal."""
    from datetime import datetime, timedelta
    import json as _json

    subscritor = get_user_subscritor(request.user)

    # Determinar a semana: aceita ?week_start=YYYY-MM-DD, senão usa a semana atual
    week_start_str = request.GET.get("week_start", "")
    if week_start_str:
        try:
            week_start = datetime.strptime(week_start_str, "%Y-%m-%d").date()
            # Ajustar para segunda-feira
            week_start = week_start - timedelta(days=week_start.weekday())
        except ValueError:
            week_start = timezone.now().date() - timedelta(days=timezone.now().date().weekday())
    else:
        today = timezone.now().date()
        week_start = today - timedelta(days=today.weekday())  # segunda-feira

    week_end = week_start + timedelta(days=6)  # domingo

    agendamentos = Agenda.objects.filter(
        subscritor=subscritor,
        data_inicio__date__gte=week_start,
        data_inicio__date__lte=week_end,
    ).select_related("projeto", "projeto__cliente").order_by("data_inicio")

    events = []
    for a in agendamentos:
        events.append({
            "id": str(a.id),
            "title": a.titulo,
            "start": a.data_inicio.isoformat(),
            "end": a.data_fim.isoformat(),
            "confirmed": a.confirmado,
            "client": a.projeto.cliente.nome if a.projeto and a.projeto.cliente else "",
            "location": a.local or "",
            "day": a.data_inicio.weekday(),  # 0=Mon, 6=Sun
            "origem": a.origem,
        })

    return JsonResponse({
        "week_start": week_start.isoformat(),
        "week_end": week_end.isoformat(),
        "events": events,
    })


# ============ Google Calendar – Webhook & Sync ============

import logging

_gc_logger = logging.getLogger(__name__)


@csrf_exempt
@require_POST
def google_calendar_webhook(request):
    """
    Endpoint que o Google Calendar chama via push notification quando
    há alterações no calendário.
    Headers relevantes:
      X-Goog-Channel-ID   – ID do canal (nosso channel_id)
      X-Goog-Resource-ID  – ID do recurso
      X-Goog-Resource-State – "sync" (handshake) ou "exists" (mudança)
    """
    channel_id = request.headers.get("X-Goog-Channel-ID", "")
    resource_state = request.headers.get("X-Goog-Resource-State", "")

    _gc_logger.info(
        "Webhook recebido: channel=%s state=%s",
        channel_id,
        resource_state,
    )

    # Handshake inicial do Google → apenas responder 200
    if resource_state == "sync":
        return HttpResponse(status=200)

    # Buscar o canal registrado
    try:
        channel = GoogleCalendarChannel.objects.select_related("subscritor").get(
            channel_id=channel_id,
        )
    except GoogleCalendarChannel.DoesNotExist:
        _gc_logger.warning("Webhook de canal desconhecido: %s", channel_id)
        return HttpResponse(status=200)  # responder 200 para não reenviar

    # Disparar sincronização via Celery (não bloquear a resposta)
    from agenda_modesta.notifications.tasks import sincronizar_google_calendar

    sincronizar_google_calendar.delay(
        str(channel.subscritor.pk),
        channel.sync_token,
    )

    return HttpResponse(status=200)


@login_required
@require_POST
def registrar_google_sync(request):
    """
    Ação do admin/UI para registrar o webhook do Google Calendar
    e fazer a primeira sincronização completa.
    """
    from .google_calendar import registrar_webhook, sincronizar_eventos_google

    subscritor = get_user_subscritor(request.user)

    try:
        result = registrar_webhook(subscritor)

        # Primeira sincronização completa (sem sync_token)
        new_token = sincronizar_eventos_google(
            subscritor=subscritor,
            usuario=request.user,
            sync_token="",
        )

        # Salvar o sync_token no canal
        GoogleCalendarChannel.objects.filter(
            channel_id=result["channel_id"],
        ).update(sync_token=new_token)

        messages.success(
            request,
            f"Sincronização com Google Calendar ativada! "
            f"Expira em {result['expiration']:%d/%m/%Y %H:%M}.",
        )
    except Exception as exc:
        _gc_logger.exception("Erro ao registrar webhook Google")
        messages.error(request, f"Erro ao ativar sincronização: {exc}")

    return redirect("agenda:list")


@login_required
@require_POST
def sincronizar_google_agora(request):
    """Força uma sincronização imediata Google → App."""
    from .google_calendar import sincronizar_eventos_google

    subscritor = get_user_subscritor(request.user)

    channel = GoogleCalendarChannel.objects.filter(
        subscritor=subscritor,
    ).order_by("-criado_em").first()

    sync_token = channel.sync_token if channel else ""

    try:
        new_token = sincronizar_eventos_google(
            subscritor=subscritor,
            usuario=request.user,
            sync_token=sync_token,
        )
        if channel:
            channel.sync_token = new_token
            channel.save(update_fields=["sync_token"])
        messages.success(request, "Sincronização concluída com sucesso!")
    except Exception as exc:
        _gc_logger.exception("Erro na sincronização manual")
        messages.error(request, f"Erro na sincronização: {exc}")

    return redirect("agenda:list")
