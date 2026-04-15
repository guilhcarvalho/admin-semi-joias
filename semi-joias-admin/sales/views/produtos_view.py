from django.shortcuts import render, redirect, get_object_or_404
from ..models import Produtos, Maleta
from ..forms import ProdutosForm
from django.db import transaction


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
    
    if request.method == "POST":
        form = ProdutosForm(request.POST)
        
        if form.is_valid():
            produto = form.save(commit=False)
            produto.product_briefcase = maleta
            produto.save()
            return redirect('sales:maleta_produtos', id=id)
    else:
        form = ProdutosForm()
        
    return render(request, 'sales/registrar_produto.html', {'maleta': maleta, 'form': form})

def atualizar_produto(request, id):
    produto = get_object_or_404(Produtos, id=id)
    
    maleta = produto.product_briefcase
        
    if request.method == "POST":
        form = ProdutosForm(request.POST, instance=produto)
        if form.is_valid():
            form.save()
            return redirect('sales:maleta_produtos', id=maleta.id)
        
    else:
        form = ProdutosForm(instance=produto)
    return render(request, 'sales/atualizar_produto.html', {'produto': produto, 'maleta': maleta, 'form': form})
    
def deletar_produto(request, id):
    produto = get_object_or_404(Produtos, id=id)
    if request.method == "POST":
        maleta_id = produto.product_briefcase.id
        produto.delete()
        return redirect('sales:maleta_produtos', id=maleta_id)