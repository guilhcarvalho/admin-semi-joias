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
from .models import Vendas, Maleta

def vendas_por_cliente(request, id):
    cliente = get_object_or_404(Cliente, id=id)
    vendas = Vendas.objects.filter(client=cliente)
    
    return render(request, 'sales/vendas_cliente.html', {
        'cliente': cliente,
        'vendas': vendas,
        'active': 'vendas',  
    })
    
def exibir_maletas(request):
    maletas = Maleta.objects.all()
    
    month = request.GET.get('month', '').strip()
    order_number = request.GET.get('order', '').strip()
    
    if month:
        maletas = maletas.filter(month__icontains=month)
        
    if order_number:
        maletas = maletas.filter(order_number__icontains=order_number)
    
    return render(request, 'sales/maletas.html',{
        'maletas': maletas,
        'active': 'maletas',
        'month_filter': month,
        'order_number_filter': order_number,
    })
    