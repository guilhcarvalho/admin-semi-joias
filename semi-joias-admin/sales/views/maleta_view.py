from django.shortcuts import render, redirect, get_object_or_404
from ..models import Maleta

def info_maleta(request, id):
    maleta = get_object_or_404(Maleta, id=id)
    vendas = maleta.vendas.all()

    return render(request, 'sales/info_maleta.html', {
        'maleta': maleta,
        'vendas': vendas,
        'active': 'maletas',
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
    
def cadastrar_maleta(request):
    if request.method == "GET":
        return render(request, 'sales/criar_maleta.html')
    
    elif request.method == "POST":
        month = request.POST.get('month')
        start_sale_period = request.POST.get('start_sale_period')
        end_sale_period = request.POST.get('end_sale_period')
        order_number = request.POST.get('order_number')
        order_value = request.POST.get('order_value')
        
        briefcase = Maleta(
            month=month,
            start_sale_period=start_sale_period,
            end_sale_period=end_sale_period,
            order_number=order_number,
            order_value=order_value,
        )
        briefcase.save()
        return redirect('sales:maletas_lista')
    
def atualizar_maleta(request, id):
    maleta = get_object_or_404(Maleta, id=id)
    
    if request.method == "GET":
        return render(request, 'sales/criar_maleta.html', {'maleta': maleta})
    
    elif request.method == "POST":
        maleta.month = request.POST.get('month')
        maleta.start_sale_period = request.POST.get('start_sale_period')
        maleta.end_sale_period = request.POST.get('end_sale_period')
        maleta.order_number = request.POST.get('order_number')
        maleta.order_value = request.POST.get('order_value')
        
        maleta.save()
        return redirect('sales:maletas_lista')

def deletar_maleta(request, id):
    maleta = get_object_or_404(Maleta, id=id)
    maleta.delete()
    return redirect('sales:maletas_lista')