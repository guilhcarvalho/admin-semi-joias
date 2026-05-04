from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from ..models import Produtos, Maleta, ItensVenda
from ..forms import ProdutosForm
from django.db import transaction


@login_required
def exibir_produtos(request, id):
    maleta = get_object_or_404(Maleta, id=id)
    
    product_briefcase = request.GET.get('product_briefcase', '').strip()
    product_name = request.GET.get('product_name', '').strip()
    product_code = request.GET.get('product_code', '').strip()

    produtos = Produtos.objects.filter(product_briefcase=maleta).param_filter(
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
    
@login_required
def cadastrar_produto(request, id):
    
    maleta = get_object_or_404(Maleta, id=id)
    
    if request.method == "POST":
        form = ProdutosForm(request.POST)
        
        if form.is_valid():
            produto = form.save(commit=False)
            produto.product_briefcase = maleta
            if Produtos.objects.filter(product_briefcase=maleta, product_code=produto.product_code).exists():
                form.add_error('product_code', 'Já existe um produto com este código nesta maleta.')
            else:
                produto.save()
                return redirect('sales:maleta_produtos', id=id)
    else:
        form = ProdutosForm()
        
    return render(request, 'sales/registrar_produto.html', {'maleta': maleta, 'form': form})

@login_required
def atualizar_produto(request, id):
    produto = get_object_or_404(Produtos, id=id)
    
    maleta = produto.product_briefcase
        
    if request.method == "POST":
        form = ProdutosForm(request.POST, instance=produto)
        if form.is_valid():
            novo_code = form.cleaned_data['product_code']
            nova_quantity = form.cleaned_data['product_quantity']
            if Produtos.objects.filter(product_briefcase=maleta, product_code=novo_code).exclude(pk=produto.pk).exists():
                form.add_error('product_code', 'Já existe um produto com este código nesta maleta.')
            elif nova_quantity < produto.quantity_sold:
                form.add_error('product_quantity', f'Quantidade não pode ser menor que {produto.quantity_sold} (já vendida).')
            else:
                form.save()
                return redirect('sales:maleta_produtos', id=maleta.id)
        
    else:
        form = ProdutosForm(instance=produto)
    return render(request, 'sales/atualizar_produto.html', {'produto': produto, 'maleta': maleta, 'form': form})
    
@login_required
def deletar_produto(request, id):
    produto = get_object_or_404(Produtos, id=id)
    maleta_id = produto.product_briefcase.id
    if request.method == "POST":
        if ItensVenda.objects.filter(product=produto).exists():
            messages.error(request, 'Não é possível excluir um produto com vendas registradas.')
            return redirect('sales:maleta_produtos', id=maleta_id)
        produto.delete()
        return redirect('sales:maleta_produtos', id=maleta_id)
    return redirect('sales:maleta_produtos', id=maleta_id)