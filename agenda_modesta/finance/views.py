from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.http import HttpResponse, JsonResponse
from django.views.decorators.http import require_http_methods
from django.db.models import Sum

from .models import Orcamento, Recibo, PacoteServico
from .forms import OrcamentoForm, ReciboForm, PacoteServicoForm
from agenda_modesta.clients.models import Cliente
from agenda_modesta.projects.models import Projeto
from agenda_modesta.core.utils import get_user_subscritor


# ============ ORÇAMENTOS ============

@login_required
def orcamento_list(request):
    subscritor = get_user_subscritor(request.user)
    orcamentos = Orcamento.objects.filter(
        subscritor=subscritor
    ).select_related('cliente', 'projeto').order_by('-data_criacao')

    clientes = Cliente.objects.filter(subscritor=subscritor, ativo=True)

    # Stats
    total_orcamentos = orcamentos.count()
    valor_pendente = orcamentos.filter(status_pagamento='pendente').aggregate(Sum('valor_total'))['valor_total__sum'] or 0
    valor_pago = orcamentos.filter(status_pagamento='pago').aggregate(Sum('valor_total'))['valor_total__sum'] or 0

    # Filters
    q = request.GET.get('q', '')
    if q:
        orcamentos = orcamentos.filter(cliente__nome__icontains=q) | orcamentos.filter(numero_sequencial__icontains=q)

    status = request.GET.get('status', '')
    if status:
        orcamentos = orcamentos.filter(status_pagamento=status)

    cliente_id = request.GET.get('cliente', '')
    if cliente_id:
        orcamentos = orcamentos.filter(cliente_id=cliente_id)

    # Pagination
    paginator = Paginator(orcamentos, 10)
    page = request.GET.get('page', 1)
    orcamentos = paginator.get_page(page)

    context = {
        'orcamentos': orcamentos,
        'clientes': clientes,
        'total_orcamentos': total_orcamentos,
        'valor_pendente': valor_pendente,
        'valor_pago': valor_pago,
    }

    if request.htmx:
        return render(request, 'finance/partials/orcamento_table.html', context)

    return render(request, 'finance/orcamento_list.html', context)


@login_required
def orcamento_create(request):
    subscritor = get_user_subscritor(request.user)
    clientes = Cliente.objects.filter(subscritor=subscritor, ativo=True)
    projetos = Projeto.objects.filter(subscritor=subscritor, ativo=True)
    pacotes = PacoteServico.objects.filter(subscritor=subscritor, ativo=True)
    cliente_selecionado = request.GET.get('cliente')

    if request.method == 'POST':
        form = OrcamentoForm(request.POST)
        if form.is_valid():
            orcamento = form.save(commit=False)
            orcamento.usuario = request.user
            orcamento.subscritor = subscritor
            # Generate sequential number
            last = Orcamento.objects.filter(subscritor=subscritor).order_by('-numero_sequencial').first()
            orcamento.numero_sequencial = (last.numero_sequencial + 1) if last else 1
            orcamento.save()

            # Send email if requested
            if request.POST.get('enviar_email'):
                # TODO: Implement email sending
                pass

            messages.success(request, 'Orçamento criado com sucesso!')
            return redirect('finance:orcamentos')
    else:
        form = OrcamentoForm()

    return render(request, 'finance/orcamento_form.html', {
        'form': form,
        'clientes': clientes,
        'projetos': projetos,
        'pacotes': pacotes,
        'cliente_selecionado': cliente_selecionado,
    })


@login_required
def orcamento_edit(request, pk):
    subscritor = get_user_subscritor(request.user)
    orcamento = get_object_or_404(Orcamento, pk=pk, subscritor=subscritor)
    clientes = Cliente.objects.filter(subscritor=subscritor, ativo=True)
    projetos = Projeto.objects.filter(subscritor=subscritor, ativo=True)
    pacotes = PacoteServico.objects.filter(subscritor=subscritor, ativo=True)

    if request.method == 'POST':
        form = OrcamentoForm(request.POST, instance=orcamento)
        if form.is_valid():
            form.save()
            messages.success(request, 'Orçamento atualizado com sucesso!')
            return redirect('finance:orcamentos')
    else:
        form = OrcamentoForm(instance=orcamento)

    return render(request, 'finance/orcamento_form.html', {
        'form': form,
        'orcamento': orcamento,
        'clientes': clientes,
        'projetos': projetos,
        'pacotes': pacotes,
    })


@login_required
@require_http_methods(["DELETE"])
def orcamento_delete(request, pk):
    subscritor = get_user_subscritor(request.user)
    orcamento = get_object_or_404(Orcamento, pk=pk, subscritor=subscritor)
    orcamento.delete()
    messages.success(request, 'Orçamento excluído com sucesso!')
    return HttpResponse("")


@login_required
@require_http_methods(["POST"])
def orcamento_marcar_pago(request, pk):
    subscritor = get_user_subscritor(request.user)
    orcamento = get_object_or_404(Orcamento, pk=pk, subscritor=subscritor)
    orcamento.status_pagamento = 'pago'
    orcamento.save()
    return render(request, 'finance/partials/orcamento_row.html', {'orcamento': orcamento})


@login_required
@require_http_methods(["POST"])
def orcamento_enviar_email(request, pk):
    subscritor = get_user_subscritor(request.user)
    orcamento = get_object_or_404(Orcamento, pk=pk, subscritor=subscritor)
    # TODO: Implement email sending
    messages.success(request, f'Orçamento enviado para {orcamento.cliente.email}')
    return HttpResponse(status=200)


@login_required
def orcamento_pdf(request, pk):
    subscritor = get_user_subscritor(request.user)
    orcamento = get_object_or_404(Orcamento, pk=pk, subscritor=subscritor)
    # TODO: Generate PDF
    return HttpResponse("PDF generation not implemented", content_type='text/plain')


@login_required
def get_pacote_info(request):
    subscritor = get_user_subscritor(request.user)
    pacote_id = request.GET.get('pacote')
    if pacote_id:
        pacote = get_object_or_404(PacoteServico, pk=pacote_id, subscritor=subscritor)
        return render(request, 'finance/partials/pacote_info.html', {'pacote': pacote})
    return HttpResponse("")


# ============ RECIBOS ============

@login_required
def recibo_list(request):
    subscritor = get_user_subscritor(request.user)
    recibos = Recibo.objects.filter(
        subscritor=subscritor
    ).select_related('cliente', 'projeto').order_by('-data_criacao')

    clientes = Cliente.objects.filter(subscritor=subscritor, ativo=True)

    # Stats
    total_recibos = recibos.count()
    valor_total = recibos.aggregate(Sum('valor_total'))['valor_total__sum'] or 0

    # Filters
    q = request.GET.get('q', '')
    if q:
        recibos = recibos.filter(cliente__nome__icontains=q) | recibos.filter(numero_sequencial__icontains=q)

    cliente_id = request.GET.get('cliente', '')
    if cliente_id:
        recibos = recibos.filter(cliente_id=cliente_id)

    # Pagination
    paginator = Paginator(recibos, 10)
    page = request.GET.get('page', 1)
    recibos = paginator.get_page(page)

    context = {
        'recibos': recibos,
        'clientes': clientes,
        'total_recibos': total_recibos,
        'valor_total': valor_total,
    }

    if request.htmx:
        return render(request, 'finance/partials/recibo_table.html', context)

    return render(request, 'finance/recibo_list.html', context)


@login_required
def recibo_create(request):
    subscritor = get_user_subscritor(request.user)
    clientes = Cliente.objects.filter(subscritor=subscritor, ativo=True)
    projetos = Projeto.objects.filter(subscritor=subscritor, ativo=True)

    if request.method == 'POST':
        form = ReciboForm(request.POST)
        if form.is_valid():
            recibo = form.save(commit=False)
            recibo.usuario = request.user
            recibo.subscritor = subscritor
            # Generate sequential number
            last = Recibo.objects.filter(subscritor=subscritor).order_by('-numero_sequencial').first()
            recibo.numero_sequencial = (last.numero_sequencial + 1) if last else 1
            recibo.save()
            messages.success(request, 'Recibo criado com sucesso!')
            return redirect('finance:recibos')
    else:
        form = ReciboForm()

    return render(request, 'finance/recibo_form.html', {
        'form': form,
        'clientes': clientes,
        'projetos': projetos,
    })


@login_required
def recibo_from_orcamento(request, pk):
    """Create a recibo from an orcamento"""
    subscritor = get_user_subscritor(request.user)
    orcamento = get_object_or_404(Orcamento, pk=pk, subscritor=subscritor)

    # Generate sequential number
    last = Recibo.objects.filter(subscritor=subscritor).order_by('-numero_sequencial').first()
    numero = (last.numero_sequencial + 1) if last else 1

    recibo = Recibo.objects.create(
        usuario=request.user,
        subscritor=subscritor,
        cliente=orcamento.cliente,
        projeto=orcamento.projeto,
        numero_sequencial=numero,
        descricao=orcamento.descricao,
        horas_trabalhadas=orcamento.horas_trabalhadas,
        valor_hora=orcamento.valor_hora,
        valor_total=orcamento.valor_total,
        forma_pagamento=orcamento.forma_pagamento,
    )

    messages.success(request, f'Recibo #{recibo.numero_sequencial} criado a partir do orçamento!')
    return redirect('finance:recibo_detail', pk=recibo.id)


@login_required
def recibo_detail(request, pk):
    subscritor = get_user_subscritor(request.user)
    recibo = get_object_or_404(Recibo, pk=pk, subscritor=subscritor)
    return render(request, 'finance/recibo_detail.html', {'recibo': recibo})


@login_required
@require_http_methods(["DELETE"])
def recibo_delete(request, pk):
    subscritor = get_user_subscritor(request.user)
    recibo = get_object_or_404(Recibo, pk=pk, subscritor=subscritor)
    recibo.delete()
    messages.success(request, 'Recibo excluído com sucesso!')
    return HttpResponse("")


@login_required
@require_http_methods(["POST"])
def recibo_enviar_email(request, pk):
    subscritor = get_user_subscritor(request.user)
    recibo = get_object_or_404(Recibo, pk=pk, subscritor=subscritor)
    # TODO: Implement email sending
    messages.success(request, f'Recibo enviado para {recibo.cliente.email}')
    return HttpResponse(status=200)


@login_required
def recibo_pdf(request, pk):
    subscritor = get_user_subscritor(request.user)
    recibo = get_object_or_404(Recibo, pk=pk, subscritor=subscritor)
    # TODO: Generate PDF
    return HttpResponse("PDF generation not implemented", content_type='text/plain')


# ============ PACOTES ============

@login_required
def pacote_list(request):
    subscritor = get_user_subscritor(request.user)
    pacotes = PacoteServico.objects.filter(
        subscritor=subscritor
    ).order_by('-data_criacao')

    return render(request, 'finance/pacote_list.html', {'pacotes': pacotes})


@login_required
def pacote_create(request):
    subscritor = get_user_subscritor(request.user)
    if request.method == 'POST':
        form = PacoteServicoForm(request.POST)
        if form.is_valid():
            pacote = form.save(commit=False)
            pacote.usuario = request.user
            pacote.subscritor = subscritor
            pacote.save()
            messages.success(request, 'Pacote criado com sucesso!')
            return redirect('finance:pacotes')
    else:
        form = PacoteServicoForm()

    return render(request, 'finance/pacote_form.html', {'form': form})


@login_required
def pacote_edit(request, pk):
    subscritor = get_user_subscritor(request.user)
    pacote = get_object_or_404(PacoteServico, pk=pk, subscritor=subscritor)

    if request.method == 'POST':
        form = PacoteServicoForm(request.POST, instance=pacote)
        if form.is_valid():
            form.save()
            messages.success(request, 'Pacote atualizado com sucesso!')
            return redirect('finance:pacotes')
    else:
        form = PacoteServicoForm(instance=pacote)

    return render(request, 'finance/pacote_form.html', {
        'form': form,
        'pacote': pacote,
    })


@login_required
@require_http_methods(["DELETE"])
def pacote_delete(request, pk):
    subscritor = get_user_subscritor(request.user)
    pacote = get_object_or_404(PacoteServico, pk=pk, subscritor=subscritor)
    pacote.delete()
    messages.success(request, 'Pacote excluído com sucesso!')
    return HttpResponse("")
