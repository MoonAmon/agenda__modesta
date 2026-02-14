from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.http import HttpResponse
from django.views.decorators.http import require_http_methods

from .models import Projeto
from .forms import ProjetoForm
from agenda_modesta.clients.models import Cliente
from agenda_modesta.core.utils import get_user_subscritor


@login_required
def project_list(request):
    subscritor = get_user_subscritor(request.user)
    projetos = Projeto.objects.filter(
        subscritor=subscritor
    ).select_related('cliente').order_by('-data_criacao')

    clientes = Cliente.objects.filter(subscritor=subscritor, ativo=True)

    # Filters
    q = request.GET.get('q', '')
    if q:
        projetos = projetos.filter(nome__icontains=q) | projetos.filter(cliente__nome__icontains=q)

    status = request.GET.get('status', '')
    if status:
        projetos = projetos.filter(status=status)

    cliente_id = request.GET.get('cliente', '')
    if cliente_id:
        projetos = projetos.filter(cliente_id=cliente_id)

    # Pagination
    paginator = Paginator(projetos, 9)
    page = request.GET.get('page', 1)
    projetos = paginator.get_page(page)

    context = {
        'projetos': projetos,
        'clientes': clientes,
    }

    if request.htmx:
        return render(request, 'projects/partials/project_grid.html', context)

    return render(request, 'projects/project_list.html', context)


@login_required
def project_create(request):
    subscritor = get_user_subscritor(request.user)
    clientes = Cliente.objects.filter(subscritor=subscritor, ativo=True)
    cliente_selecionado = request.GET.get('cliente')

    if request.method == 'POST':
        form = ProjetoForm(request.POST)
        if form.is_valid():
            projeto = form.save(commit=False)
            projeto.usuario = request.user
            projeto.subscritor = subscritor
            projeto.save()
            messages.success(request, 'Projeto criado com sucesso!')
            return redirect('projects:list')
    else:
        form = ProjetoForm()

    return render(request, 'projects/project_form.html', {
        'form': form,
        'clientes': clientes,
        'cliente_selecionado': cliente_selecionado,
    })


@login_required
def project_edit(request, pk):
    subscritor = get_user_subscritor(request.user)
    projeto = get_object_or_404(Projeto, pk=pk, subscritor=subscritor)
    clientes = Cliente.objects.filter(subscritor=subscritor, ativo=True)

    if request.method == 'POST':
        form = ProjetoForm(request.POST, instance=projeto)
        if form.is_valid():
            form.save()
            messages.success(request, 'Projeto atualizado com sucesso!')
            return redirect('projects:list')
    else:
        form = ProjetoForm(instance=projeto)

    return render(request, 'projects/project_form.html', {
        'form': form,
        'projeto': projeto,
        'clientes': clientes,
    })


@login_required
def project_detail(request, pk):
    subscritor = get_user_subscritor(request.user)
    projeto = get_object_or_404(Projeto, pk=pk, subscritor=subscritor)
    return render(request, 'projects/project_detail.html', {'projeto': projeto})


@login_required
@require_http_methods(["DELETE"])
def project_delete(request, pk):
    subscritor = get_user_subscritor(request.user)
    projeto = get_object_or_404(Projeto, pk=pk, subscritor=subscritor)
    projeto.delete()
    messages.success(request, 'Projeto excluído com sucesso!')
    return HttpResponse("")
