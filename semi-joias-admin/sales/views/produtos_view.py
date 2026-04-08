from django.shortcuts import render, redirect, get_object_or_404
from ..models import Produtos, Maleta

def exibir_produtos(request, id):
    maleta = get_object_or_404(Maleta, id=id)
    
    produtos = Produtos.objects.filter(product_briefcase=maleta)
        
    product_briefcase = request.GET.get('product_briefcase', '').strip()
    product_name = request.GET.get('product_name', '').strip()
    product_code = request.GET.get('product_code', '').strip()

    if product_briefcase:
        produtos = produtos.filter(product_briefcase__icontains=product_briefcase)
        
    if product_name:
        produtos = produtos.filter(product_name__icontains=product_name)
        
    if product_code:
        produtos = produtos.filter(product_code__icontains=product_code)
    
    return render(request, 'sales/produtos.html',{
        'maleta': maleta,
        'produtos': produtos,
        'active': 'produtos',
        'briefcase_filter': product_briefcase,
        'product_name_filter': product_name,
    })
    
def cadastrar_produto(request):
    if request.method == "GET":
        return render(request, 'sales/registrar_produto.html')
    
    elif request.method == "POST":
        product_briefcase = request.POST.get('product_briefcase')
        product_name = request.POST.get('product_name')
        product_code = request.POST.get('product_code')
        product_value = request.POST.get('product_value')
        product_quantity = request.POST.get('product_quantity')
        
        produto = Produtos(
            product_briefcase=product_briefcase,
            product_name=product_name,
            product_code=product_code,
            product_value=product_value,
            product_quantity=product_quantity,
        )
        produto.save()
        return redirect('sales:info_maleta')


def atualizar_produto(request, id):
    produto = get_object_or_404(Produtos, id=id)
    
    if request.method == "GET":
        return render(request, 'sales/atualizar_produto.html', {'produto': produto})
    
    elif request.method == "POST":
        produto.product_briefcase = request.POST.get('product_briefcase')
        produto.product_name = request.POST.get('product_name')
        produto.product_code = request.POST.get('product_code')
        produto.product_value = request.POST.get('product_value')
        produto.product_quantity = request.POST.get('product_quantity')
        
        produto.save()
        return redirect('sales:info_maleta')

def deletar_produto(request, id):
    produto = get_object_or_404(Produtos, id=id)
    produto.delete()
    return redirect('sales:info_maleta')