from django.shortcuts import render, redirect, get_object_or_404
from ..models import Produtos, Maleta

def exibir_produtos(request, id):
    maleta = get_object_or_404(Maleta, id=id)
        
    product_briefcase = request.GET.get('product_briefcase', '').strip()
    product_name = request.GET.get('product_name', '').strip()
    product_code = request.GET.get('product_code', '').strip()

    produtos = Produtos.objects.filter(product_briefcase=maleta).param_filter(
        product_briefcase=product_briefcase,
        product_name=product_name,
        product_code=product_code
    )
    
    return render(request, 'sales/produtos.html',{
        'maleta': maleta,
        'produtos': produtos,
        'active': 'produtos',
        'briefcase_filter': product_briefcase,
        'product_name_filter': product_name,
    })
    
def cadastrar_produto(request, id):
    
    maleta = get_object_or_404(Maleta, id=id)
    
    if request.method == "GET":
        return render(request, 'sales/registrar_produto.html', {'maleta': maleta})
    
    elif request.method == "POST":
        product_briefcase = maleta
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
        return redirect('sales:maleta_produtos', id=id)


def atualizar_produto(request, id):
    produto = get_object_or_404(Produtos, id=id)
    
    maleta = produto.product_briefcase
    
    if request.method == "GET":
        contexto = {
            'produto': produto,
            'maleta': maleta
        }
        
        return render(request, 'sales/atualizar_produto.html', contexto)
    
    elif request.method == "POST":
        produto.product_name = request.POST.get('product_name')
        produto.product_code = request.POST.get('product_code')
        produto.product_value = request.POST.get('product_value')
        produto.product_quantity = request.POST.get('product_quantity')
        
        produto.save()
        return redirect('sales:maleta_produtos', id=id)

def deletar_produto(request, id):
    produto = get_object_or_404(Produtos, id=id)
    if request.method == "POST":
        maleta_id = produto.product_briefcase.id
        produto.delete()
        return redirect('sales:maleta_produtos', id=maleta_id)