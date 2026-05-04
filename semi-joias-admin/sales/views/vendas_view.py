from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render

from clients.models import Cliente
from ..forms import AtualizarGarantiaForm, VendasCreateForm, VendasForm
from ..models import Devolucao, Garantia, ItemDevolucao, ItensVenda, Maleta, Parcela, Produtos, Vendas


def _session_key(maleta_id):
    return f'nova_venda_maleta_{maleta_id}'


def _enriquecer_itens(itens_raw):
    resultado = []
    for item in itens_raw:
        try:
            produto = Produtos.objects.get(id=item['product_id'])
        except Produtos.DoesNotExist:
            continue
        unit_price = produto.product_value
        dp = Decimal(item['discount_percent'])
        id_d = Decimal(item['integer_discount'])
        pdc = unit_price * (dp / 100)
        end_value = unit_price - pdc - id_d
        qty = item['quantity']
        resultado.append({
            **item,
            'produto': produto,
            'unit_price': unit_price,
            'discount_percent': dp,
            'integer_discount': id_d,
            'end_value': end_value,
            'subtotal': end_value * qty,
        })
    return resultado


def _action_add(maleta, itens, post):

    product_id = post.get('product')
    try:
        quantity = int(post.get('quantity', 0))
        discount_percent = Decimal(post.get('discount_percent', '0'))
        integer_discount = Decimal(post.get('integer_discount', '0'))
        produto = Produtos.objects.get(id=product_id, product_briefcase=maleta)
    except Exception:
        return itens, 'Dados inválidos.'

    unit_price = produto.product_value
    total_discount = unit_price * (discount_percent / 100) + integer_discount

    if quantity <= 0:
        return itens, 'Quantidade deve ser maior que zero.'
    if quantity > produto.remaining_quantity:
        return itens, f'Estoque insuficiente. Disponível: {produto.remaining_quantity}.'
    if not (0 <= discount_percent <= 100):
        return itens, 'Desconto em % deve ser entre 0 e 100.'
    if integer_discount < 0:
        return itens, 'Desconto em R$ não pode ser negativo.'
    if total_discount > unit_price:
        return itens, 'O desconto total não pode exceder o preço do produto.'
    if any(i['product_id'] == int(product_id) for i in itens):
        return itens, 'Este produto já foi adicionado.'

    return itens + [{
        'product_id': int(product_id),
        'quantity': quantity,
        'discount_percent': str(discount_percent),
        'integer_discount': str(integer_discount),
    }], None


def _action_remove(itens, post):
    try:
        product_id = int(post.get('product_id', 0))
    except (ValueError, TypeError):
        return itens
    return [i for i in itens if i['product_id'] != product_id]


def _calcular_totais(itens):
    gross = sum(i['unit_price'] * i['quantity'] for i in itens)
    discount = sum(
        (i['unit_price'] * (i['discount_percent'] / 100) + i['integer_discount']) * i['quantity']
        for i in itens
    )
    end = sum(i['subtotal'] for i in itens)
    return gross, discount, end


def _parse_quantidades_devolucao(itens, post_data):

    resultado = []
    for item in itens:
        try:
            qty = int(post_data.get(f'quantidade_{item.id}', '0'))
        except (ValueError, TypeError):
            qty = 0
        if qty > 0:
            resultado.append((item, qty))
    return resultado


def _salvar_devolucao(venda, itens_qtds, motivo):

    with transaction.atomic():
        product_ids = [item.product_id for item, _ in itens_qtds]
        produtos = {p.id: p for p in Produtos.objects.select_for_update().filter(id__in=product_ids)}

        devolucao = Devolucao.objects.create(venda=venda, motivo=motivo)
        for item, qty in itens_qtds:
            already_returned = sum(
                id_obj.quantidade for id_obj in item.devolucoes.all()
            )
            disponivel = item.quantity - already_returned
            if qty > disponivel:
                raise ValidationError(
                    f'Quantidade inválida para {item.product.product_name}. '
                    f'Máximo disponível: {disponivel}.'
                )
            ItemDevolucao.objects.create(
                devolucao=devolucao,
                item_venda=item,
                quantidade=qty,
                valor_estornado=item.end_value * qty,
            )
            produto = produtos[item.product_id]
            produto.quantity_sold -= qty
            produto.save()

        Vendas.objects.filter(pk=venda.pk).update(status='devolvida_parcial')
        venda.briefcase.save()


def _parse_dados_garantia(itens_qs, post_data):

    item_id = post_data.get('item_venda')
    motivo = post_data.get('motivo', '').strip()
    try:
        item = itens_qs.get(id=item_id)
        quantidade = int(post_data.get('quantidade', '0'))
    except (ItensVenda.DoesNotExist, ValueError, TypeError):
        return None, None, None, 'Dados inválidos.'

    if quantidade <= 0 or quantidade > item.quantity:
        return None, None, None, f'Quantidade inválida. Máximo: {item.quantity}.'
    if not motivo:
        return None, None, None, 'Informe o motivo da garantia.'

    return item, quantidade, motivo, None


@login_required
def vendas_por_cliente(request, id):
    cliente = get_object_or_404(Cliente, id=id)
    vendas = Vendas.objects.filter(client=cliente).select_related('briefcase')
    return render(request, 'sales/vendas_cliente.html', {
        'cliente': cliente,
        'vendas': vendas,
        'active': 'vendas',
    })


@login_required
def exibir_vendas(request):
    client = request.GET.get('client', '').strip()
    briefcase = request.GET.get('briefcase', '').strip()
    vendas = Vendas.objects.param_filter(client=client, briefcase=briefcase).select_related('client', 'briefcase')
    return render(request, 'sales/vendas.html', {
        'vendas': vendas,
        'client': client,
        'venda': briefcase,
        'active': 'vendas',
    })


@login_required
def info_vendas(request, id):
    venda = get_object_or_404(Vendas, id=id)
    itens = ItensVenda.objects.filter(sale=venda).select_related('product')
    items_data = [
        {'item': item, 'subtotal': item.quantity * item.end_value}
        for item in itens
    ]
    devolucoes = venda.devolucoes.prefetch_related('itens__item_venda__product').all()
    garantias = Garantia.objects.filter(item_venda__sale=venda).select_related('item_venda__product')

    return render(request, 'sales/info_vendas.html', {
        'venda': venda,
        'items_data': items_data,
        'maleta': venda.briefcase,
        'devolucoes': devolucoes,
        'garantias': garantias,
    })


@login_required
def nova_venda_itens(request, id):
    maleta = get_object_or_404(Maleta, id=id)
    key = _session_key(id)
    itens = request.session.get(key, [])

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'add':
            itens, erro = _action_add(maleta, itens, request.POST)
            if erro:
                messages.error(request, erro)
            request.session[key] = itens

        elif action == 'remove':
            itens = _action_remove(itens, request.POST)
            request.session[key] = itens

        elif action == 'cancelar':
            request.session.pop(key, None)
            return redirect('sales:info_maleta', id=id)

        elif action == 'next':
            if not itens:
                messages.error(request, 'Adicione pelo menos um item antes de prosseguir.')
            else:
                return redirect('sales:nova_venda_verificar', id=id)

        return redirect('sales:registrar_venda', id=id)

    produtos = Produtos.objects.filter(product_briefcase=maleta)
    return render(request, 'sales/venda_nova_itens.html', {
        'maleta': maleta,
        'produtos': produtos,
        'itens': _enriquecer_itens(itens),
    })


@login_required
def nova_venda_verificar(request, id):
    maleta = get_object_or_404(Maleta, id=id)
    key = _session_key(id)
    itens_raw = request.session.get(key, [])

    if not itens_raw:
        return redirect('sales:registrar_venda', id=id)

    if request.method == 'POST':
        return redirect('sales:nova_venda_dados', id=id)

    itens = _enriquecer_itens(itens_raw)
    gross_total, discount_total, end_total = _calcular_totais(itens)

    return render(request, 'sales/venda_nova_verificar.html', {
        'maleta': maleta,
        'itens': itens,
        'gross_total': gross_total,
        'discount_total': discount_total,
        'end_total': end_total,
    })


@login_required
def nova_venda_dados(request, id):
    maleta = get_object_or_404(Maleta, id=id)
    key = _session_key(id)
    itens_raw = request.session.get(key, [])

    if not itens_raw:
        return redirect('sales:registrar_venda', id=id)

    if request.method == 'POST':
        form = VendasCreateForm(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    venda = form.save(commit=False)
                    venda.briefcase = maleta
                    venda.save()

                    for item_data in itens_raw:
                        produto = get_object_or_404(Produtos, id=item_data['product_id'], product_briefcase=maleta)
                        ItensVenda(
                            sale=venda,
                            product=produto,
                            quantity=item_data['quantity'],
                            discount_percent=Decimal(item_data['discount_percent']),
                            integer_discount=Decimal(item_data['integer_discount']),
                        ).save()

                    venda.refresh_from_db()
                    venda.gerar_parcelas()

                request.session.pop(key, None)
                return redirect('sales:info_vendas', id=venda.id)
            except ValidationError as e:
                msgs = e.messages if hasattr(e, 'messages') else [str(e)]
                for msg in msgs:
                    form.add_error(None, msg)
    else:
        form = VendasCreateForm()

    return render(request, 'sales/venda_nova_dados.html', {
        'maleta': maleta,
        'form': form,
    })


@login_required
def toggle_parcela(request, id):
    parcela = get_object_or_404(Parcela, id=id)
    if request.method == 'POST' and parcela.situacao != 'cancelada':
        parcela.situacao = 'pago' if parcela.situacao == 'pendente' else 'pendente'
        parcela.save()
    return redirect('sales:info_vendas', id=parcela.venda_id)


@login_required
def atualizar_venda(request, id):
    venda = get_object_or_404(Vendas, id=id)

    if request.method == 'POST':
        form = VendasForm(request.POST, instance=venda)
        if form.is_valid():
            form.save()
            return redirect('sales:info_vendas', id=venda.id)
    else:
        form = VendasForm(instance=venda)

    return render(request, 'sales/atualizar_venda.html', {
        'maleta': venda.briefcase,
        'venda': venda,
        'form': form,
    })


@login_required
def cancelar_venda(request, id):
    venda = get_object_or_404(Vendas, id=id)
    if venda.status != 'ativa':
        messages.error(request, 'Apenas vendas ativas podem ser canceladas.')
        return redirect('sales:info_vendas', id=id)
    if request.method == 'POST':
        venda.cancelar()
        messages.success(request, 'Venda cancelada com sucesso.')
        return redirect('sales:info_vendas', id=id)
    return render(request, 'sales/cancelar_venda.html', {'venda': venda})


@login_required
def registrar_devolucao(request, id):
    venda = get_object_or_404(Vendas, id=id)
    if venda.status == 'cancelada':
        messages.error(request, 'Não é possível registrar devolução em venda cancelada.')
        return redirect('sales:info_vendas', id=id)

    itens = list(
        ItensVenda.objects.filter(sale=venda)
        .select_related('product')
        .prefetch_related('devolucoes')
    )
    for item in itens:
        item.disponivel = item.quantity - sum(d.quantidade for d in item.devolucoes.all())

    if request.method == 'POST':
        motivo = request.POST.get('motivo', '').strip()
        itens_qtds = _parse_quantidades_devolucao(itens, request.POST)

        if not itens_qtds:
            messages.error(request, 'Selecione ao menos um item para devolver.')
        else:
            try:
                _salvar_devolucao(venda, itens_qtds, motivo)
                messages.success(request, 'Devolução registrada com sucesso.')
                return redirect('sales:info_vendas', id=id)
            except ValidationError as e:
                for msg in e.messages:
                    messages.error(request, msg)

    return render(request, 'sales/registrar_devolucao.html', {'venda': venda, 'itens': itens})


@login_required
def registrar_garantia(request, id):
    venda = get_object_or_404(Vendas, id=id)
    if venda.status == 'cancelada':
        messages.error(request, 'Não é possível registrar garantia em venda cancelada.')
        return redirect('sales:info_vendas', id=id)

    itens = ItensVenda.objects.filter(sale=venda).select_related('product')

    if request.method == 'POST':
        item, quantidade, motivo, erro = _parse_dados_garantia(itens, request.POST)
        if erro:
            messages.error(request, erro)
        else:
            Garantia.objects.create(item_venda=item, quantidade=quantidade, motivo=motivo)
            messages.success(request, 'Garantia registrada com sucesso.')
            return redirect('sales:info_vendas', id=id)

    return render(request, 'sales/registrar_garantia.html', {'venda': venda, 'itens': itens})


@login_required
def atualizar_garantia(request, id):
    garantia = get_object_or_404(Garantia, id=id)
    venda = garantia.item_venda.sale

    if request.method == 'POST':
        form = AtualizarGarantiaForm(request.POST, instance=garantia)
        if form.is_valid():
            form.save()
            messages.success(request, 'Status da garantia atualizado.')
            return redirect('sales:info_vendas', id=venda.id)
    else:
        form = AtualizarGarantiaForm(instance=garantia)

    return render(request, 'sales/atualizar_garantia.html', {
        'garantia': garantia,
        'venda': venda,
        'form': form,
    })
