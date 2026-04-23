from django.shortcuts import render, get_object_or_404, redirect
from clients.models import Cliente
from ..models import Vendas, Maleta, ItensVenda
from ..forms import VendasForm


def vendas_por_cliente(request, id):
    cliente = get_object_or_404(Cliente, id=id)
    vendas = Vendas.objects.filter(client=cliente)
    
    return render(request, 'sales/vendas_cliente.html', {
        'cliente': cliente,
        'vendas': vendas,
        'active': 'vendas',  
    })

def exibir_vendas(request):
    client = request.GET.get('client', '').strip()
    briefcase = request.GET.get('briefcase', '').strip()

    vendas = Vendas.objects.param_filter(
        client=client,
        briefcase=briefcase,
    )
    
    return render(request, 'sales/vendas.html', {
        'vendas': vendas,
        'client': client,
        'venda': briefcase,
        'active': 'vendas'
        })
    
def info_vendas(request, id):
    venda = get_object_or_404(Vendas, id=id)
    venda_itens = ItensVenda.objects.filter(sale=venda)
    briefcase = venda.briefcase
    
    return render(request, 'sales/info_vendas.html', {
        'venda': venda,
        'venda_itens': venda_itens,
        'maleta': briefcase,
        })

def registrar_venda(request, id):
    briefcase = get_object_or_404(Maleta, id=id)

    if request.method == 'POST':
        form = VendasForm(request.POST)
        client_id = request.POST.get('client')
        
        if form.is_valid() and client_id:
            venda = form.save(commit=False)
            venda.briefcase = briefcase
            venda.client = get_object_or_404(Cliente, id=client_id)
            venda.save()
            return redirect('sales:info_maleta', id=venda.briefcase.id)
    else:
        form = VendasForm()
    
    return render(request, 'sales/registrar_venda.html', {
        'maleta': briefcase,
        'form': form,
        })
    
def atualizar_venda(request, id):
    venda = get_object_or_404(Vendas, id=id)
    briefcase = venda.briefcase
    
    if request.method == "POST":
        form = VendasForm(request.POST, instance=venda)
        if form.is_valid():
            form.save()
            return redirect('sales:info_maleta', id=venda.briefcase.id)
    else:
        form = VendasForm(instance=venda)
    return render(request, 'sales/atualizar_venda.html', {
        'maleta': briefcase,
        'venda': venda,
        'form': form,
        'clientes': Cliente.objects.all()
        })

def deletar_venda(request, id):
    venda = get_object_or_404(Vendas, id=id)
    if request.method == "POST":
        venda.delete()
        return redirect('sales:info_maleta', id=venda.briefcase.id)