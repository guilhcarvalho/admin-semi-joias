# View: Login / Autenticação

# View: Paginal inicial / Seleção de infos

# View: Exibir Vendas 
    #/ Filtrar vendas por data
    #/ Filtrar vendas por cliente
    #/ Filtrar vendas por pendencia
    #/ Filtrar vendas por produto
    #/ Filtrar vendas por maleta
    #/ Filtrar vendas por valor

# View: Registrar Cliente / Maleta / Produto


from django.shortcuts import render, get_object_or_404
from clients.models import Cliente
from .models import Vendas

def vendas_por_cliente(request, id):
    cliente = get_object_or_404(Cliente, id=id)
    vendas = Vendas.objects.filter(client=cliente)
    
    return render(request, 'sales/vendas_cliente.html', {
        'cliente': cliente,
        'vendas': vendas,
        'active': 'vendas',  
    })