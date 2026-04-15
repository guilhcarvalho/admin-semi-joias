from django.shortcuts import render, redirect, get_object_or_404
from ..models import Maleta
from ..forms import MaletaForm

def info_maleta(request, id):
    maleta = get_object_or_404(Maleta, id=id)
    vendas = maleta.vendas.all()

    return render(request, 'sales/info_maleta.html', {
        'maleta': maleta,
        'vendas': vendas,
        'active': 'maletas',
    })

def exibir_maletas(request):
    month = request.GET.get('month', '').strip()
    order_number = request.GET.get('order', '').strip()
    
    maletas = Maleta.objects.param_filter(
        month=month, 
        order_number=order_number
    )

    return render(request, 'sales/maletas.html',{
        'maletas': maletas,
        'active': 'maletas',
        'month_filter': month,
        'order_number_filter': order_number,
    })
    
def cadastrar_maleta(request):
    if request.method == "POST":
        form = MaletaForm(request.POST)
        
        if form.is_valid():
            form.save()
            return redirect('sales:maletas_lista')
    else:
        form = MaletaForm()
    
    return render(request, 'sales/criar_maleta.html', {'form': form})

def atualizar_maleta(request, id):
    maleta = get_object_or_404(Maleta, id=id)
    
    if request.method == "POST":
        form = MaletaForm(request.POST, instance=maleta)
        if form.is_valid():
            form.save()
            return redirect('sales:maletas_lista')
        
    else:
        form = MaletaForm(instance=maleta)

    return render(request, 'sales/atualizar_maleta.html', {'form': form, 'maleta': maleta})

def deletar_maleta(request, id):
    maleta = get_object_or_404(Maleta, id=id)
    maleta.delete()
    return redirect('sales:maletas_lista')