from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.views.decorators.http import require_http_methods
from django.utils import timezone

from .models import Agenda
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
    """Recebe o projeto escolhido e retorna o passo 2 (detalhes)."""
    subscritor = get_user_subscritor(request.user)
    form = StepProjetoForm(request.POST)
    projetos = Projeto.objects.filter(subscritor=subscritor, ativo=True)
    form.fields["projeto"].queryset = projetos

    if not form.is_valid():
        return render(request, "agenda/partials/step1_projeto.html", {"form": form})

    projeto = form.cleaned_data["projeto"]
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
        })

    return JsonResponse({
        "week_start": week_start.isoformat(),
        "week_end": week_end.isoformat(),
        "events": events,
    })
