from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.http import HttpResponse
from django.views.decorators.http import require_http_methods

from .models import Cliente
from .forms import ClienteForm
from agenda_modesta.core.utils import get_user_subscritor


UFS = [
    'AC', 'AL', 'AP', 'AM', 'BA', 'CE', 'DF', 'ES', 'GO', 'MA',
    'MT', 'MS', 'MG', 'PA', 'PB', 'PR', 'PE', 'PI', 'RJ', 'RN',
    'RS', 'RO', 'RR', 'SC', 'SP', 'SE', 'TO'
]


@login_required
def client_list(request):
    subscritor = get_user_subscritor(request.user)
    clientes = Cliente.objects.filter(
        subscritor=subscritor
    ).order_by('-data_criacao')

    # Filters
    q = request.GET.get('q', '')
    if q:
        clientes = clientes.filter(nome__icontains=q) | clientes.filter(email__icontains=q) | clientes.filter(telefone__icontains=q)

    ativo = request.GET.get('ativo', '')
    if ativo == 'true':
        clientes = clientes.filter(ativo=True)
    elif ativo == 'false':
        clientes = clientes.filter(ativo=False)

    # Pagination
    paginator = Paginator(clientes, 10)
    page = request.GET.get('page', 1)
    clientes = paginator.get_page(page)

    context = {'clientes': clientes}

    if request.htmx:
        return render(request, 'clients/partials/client_table.html', context)

    return render(request, 'clients/client_list.html', context)


@login_required
def client_create(request):
    if request.method == 'POST':
        form = ClienteForm(request.POST)
        if form.is_valid():
            cliente = form.save(commit=False)
            cliente.usuario = request.user
            cliente.subscritor = get_user_subscritor(request.user)
            cliente.save()
            messages.success(request, 'Cliente criado com sucesso!')
            return redirect('clients:list')
    else:
        form = ClienteForm()

    return render(request, 'clients/client_form.html', {
        'form': form,
        'ufs': UFS,
    })


@login_required
def client_edit(request, pk):
    subscritor = get_user_subscritor(request.user)
    cliente = get_object_or_404(Cliente, pk=pk, subscritor=subscritor)

    if request.method == 'POST':
        form = ClienteForm(request.POST, instance=cliente)
        if form.is_valid():
            form.save()
            messages.success(request, 'Cliente atualizado com sucesso!')
            return redirect('clients:list')
    else:
        form = ClienteForm(instance=cliente)

    return render(request, 'clients/client_form.html', {
        'form': form,
        'cliente': cliente,
        'ufs': UFS,
    })


@login_required
def client_detail(request, pk):
    subscritor = get_user_subscritor(request.user)
    cliente = get_object_or_404(Cliente, pk=pk, subscritor=subscritor)
    return render(request, 'clients/client_detail.html', {'cliente': cliente})


@login_required
@require_http_methods(["DELETE"])
def client_delete(request, pk):
    subscritor = get_user_subscritor(request.user)
    cliente = get_object_or_404(Cliente, pk=pk, subscritor=subscritor)
    cliente.delete()
    messages.success(request, 'Cliente excluído com sucesso!')
    return HttpResponse("")
