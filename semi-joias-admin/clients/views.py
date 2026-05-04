from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Cliente
from .forms import ClienteForm


@login_required
def exibir_clientes(request):
    nome = request.GET.get('nome', '').strip()
    celular = request.GET.get('celular', '').strip()

    clientes = Cliente.objects.param_filter(
        nome=nome,
        celular=celular
    )

    return render(request, 'clients/clientes.html', {
        'clientes': clientes,
        'active': 'clientes',
        'name_filter': nome,
        'phone_filter': celular,
    })


@login_required
def cadastrar_cliente(request):
    if request.method == 'POST':
        form = ClienteForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('clients:lista')
    else:
        form = ClienteForm()

    return render(request, 'clients/criar_cliente.html', {'form': form})


@login_required
def atualizar_cliente(request, id):
    client = get_object_or_404(Cliente, id=id)

    if request.method == 'POST':
        form = ClienteForm(request.POST, instance=client)
        if form.is_valid():
            form.save()
            return redirect('clients:lista')
    else:
        form = ClienteForm(instance=client)

    return render(request, 'clients/atualizar_cliente.html', {
        'cliente': client,
        'form': form,
    })


@login_required
def deletar_cliente(request, id):
    client = get_object_or_404(Cliente, id=id)
    if request.method == 'POST':
        client.delete()
    return redirect('clients:lista')
