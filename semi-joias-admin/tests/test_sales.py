import datetime
from decimal import Decimal

import pytest
from django.core.exceptions import ValidationError
from django.urls import reverse

from clients.models import Cliente
from sales.models import Devolucao, Garantia, ItemDevolucao, ItensVenda, Maleta, Parcela, Produtos, Vendas
from sales.choices import PAYMENT_METHODS, PAYMENT_SITUATION, MONTH_SELECTION

pytestmark = pytest.mark.django_db

PIX          = PAYMENT_METHODS.PIX
CREDITO      = PAYMENT_METHODS.CREDITO
ADIMPLENTE   = PAYMENT_SITUATION.ADIMPLENTE
INADIMPLENTE = PAYMENT_SITUATION.INADIMPLENTE
JANEIRO      = MONTH_SELECTION.JANEIRO


# ─── helpers ──────────────────────────────────────────────────────────────────

def make_cliente(**kwargs):
    defaults = {'first_name': 'Maria', 'last_name': 'Silva', 'phone_number': '11999998888'}
    defaults.update(kwargs)
    return Cliente.objects.create(**defaults)


def make_maleta(order_number=741, **kwargs):
    defaults = {
        'month': JANEIRO,
        'start_sale_period': datetime.date(2025, 1, 1),
        'end_sale_period': datetime.date(2025, 1, 31),
        'order_number': order_number,
        'order_value': Decimal('1000.00'),
    }
    defaults.update(kwargs)
    return Maleta.objects.create(**defaults)


def make_produto(maleta, product_code=9001, **kwargs):
    defaults = {
        'product_name': 'Anel',
        'product_code': product_code,
        'product_value': Decimal('100.00'),
        'product_quantity': 10,
    }
    defaults.update(kwargs)
    return Produtos.objects.create(product_briefcase=maleta, **defaults)


def make_venda(maleta, cliente, **kwargs):
    defaults = {'payment_method': PIX, 'in_good_standing': ADIMPLENTE}
    defaults.update(kwargs)
    return Vendas.objects.create(client=cliente, briefcase=maleta, **defaults)


def make_item(venda, produto, quantity=1, **kwargs):
    defaults = {'discount_percent': Decimal('0.00'), 'integer_discount': Decimal('0.00')}
    defaults.update(kwargs)
    item = ItensVenda(sale=venda, product=produto, quantity=quantity, **defaults)
    item.save()
    return item


# ─── Maleta model ─────────────────────────────────────────────────────────────

class TestMaletaModel:

    def test_str(self):
        m = make_maleta()
        assert str(m) == 'Maleta 741'

    def test_clean_rejects_end_before_start(self):
        m = Maleta(
            month=JANEIRO,
            start_sale_period=datetime.date(2025, 1, 31),
            end_sale_period=datetime.date(2025, 1, 1),
            order_number=741,
            order_value=Decimal('1000.00'),
        )
        with pytest.raises(ValidationError):
            m.full_clean()

    def test_clean_rejects_value_sold_exceeding_order_value(self):
        m = Maleta(
            month=JANEIRO,
            start_sale_period=datetime.date(2025, 1, 1),
            end_sale_period=datetime.date(2025, 1, 31),
            order_number=741,
            order_value=Decimal('100.00'),
            value_sold=Decimal('200.00'),
        )
        with pytest.raises(ValidationError):
            m.full_clean()

    def test_clean_accepts_equal_start_end_date(self):
        m = Maleta(
            month=JANEIRO,
            start_sale_period=datetime.date(2025, 1, 1),
            end_sale_period=datetime.date(2025, 1, 1),
            order_number=741,
            order_value=Decimal('1000.00'),
        )
        m.full_clean()

    def test_sales_quantity_counts_only_own_vendas(self):
        m1 = make_maleta(order_number=741)
        m2 = make_maleta(order_number=852)
        c = make_cliente()
        make_venda(m1, c)
        make_venda(m1, c, payment_method=PAYMENT_METHODS.DEBITO)
        make_venda(m2, c)
        assert m1.sales_quantity == 2
        assert m2.sales_quantity == 1

    def test_value_sold_calc_sums_end_values_across_vendas(self):
        m = make_maleta()
        c = make_cliente()
        p1 = make_produto(m, product_code=9001, product_value=Decimal('100.00'))
        p2 = make_produto(m, product_code=9002, product_value=Decimal('50.00'))
        v = make_venda(m, c)
        make_item(v, p1, quantity=2)
        make_item(v, p2, quantity=1)
        m.refresh_from_db()
        assert m.value_sold_calc == Decimal('250.00')

    def test_value_sold_calc_excludes_cancelled_vendas(self):
        m = make_maleta()
        c = make_cliente()
        p = make_produto(m, product_value=Decimal('100.00'))
        v = make_venda(m, c)
        make_item(v, p, quantity=2)
        v.cancelar()
        m.refresh_from_db()
        assert m.value_sold_calc == Decimal('0.00')

    def test_value_sold_updated_on_briefcase_save_after_item_add(self):
        m = make_maleta()
        c = make_cliente()
        p = make_produto(m, product_value=Decimal('80.00'))
        v = make_venda(m, c)
        make_item(v, p, quantity=3)
        m.refresh_from_db()
        assert m.value_sold == Decimal('240.00')

    def test_order_number_unique_constraint(self):
        make_maleta(order_number=741)
        with pytest.raises(Exception):
            make_maleta(order_number=741)

    def test_order_value_negative_rejected(self):
        m = Maleta(
            month=JANEIRO,
            start_sale_period=datetime.date(2025, 1, 1),
            end_sale_period=datetime.date(2025, 1, 31),
            order_number=741,
            order_value=Decimal('-1.00'),
        )
        with pytest.raises(ValidationError):
            m.full_clean()


# ─── Maleta queryset ──────────────────────────────────────────────────────────

class TestMaletaQuerySet:

    @pytest.fixture(autouse=True)
    def setup(self):
        self.m1 = make_maleta(order_number=741, month=MONTH_SELECTION.JANEIRO)
        self.m2 = make_maleta(order_number=852, month=MONTH_SELECTION.FEVEREIRO)
        self.m3 = make_maleta(order_number=963, month='Março')

    def test_no_params_returns_all(self):
        assert Maleta.objects.param_filter().count() == 3

    def test_filter_by_month(self):
        qs = Maleta.objects.param_filter(month=MONTH_SELECTION.JANEIRO)
        assert self.m1 in qs
        assert self.m2 not in qs

    def test_filter_by_month_case_insensitive_partial(self):
        qs = Maleta.objects.param_filter(month='ver')
        assert self.m2 in qs
        assert self.m1 not in qs

    def test_filter_by_order_number(self):
        qs = Maleta.objects.param_filter(order_number='852')
        assert self.m2 in qs
        assert self.m1 not in qs

    def test_filter_combined_month_and_order(self):
        qs = Maleta.objects.param_filter(month=MONTH_SELECTION.JANEIRO, order_number='741')
        assert self.m1 in qs
        assert self.m2 not in qs

    def test_filter_no_match(self):
        qs = Maleta.objects.param_filter(month='inexistente')
        assert qs.count() == 0


# ─── Produtos model ───────────────────────────────────────────────────────────

class TestProdutosModel:

    @pytest.fixture(autouse=True)
    def setup(self):
        self.maleta = make_maleta()

    def test_str(self):
        p = make_produto(self.maleta, product_code=9001)
        assert str(p) == 'Anel 9001'

    def test_remaining_quantity(self):
        p = make_produto(self.maleta, product_quantity=10)
        p.quantity_sold = 3
        assert p.remaining_quantity == 7

    def test_remaining_quantity_zero_when_all_sold(self):
        p = make_produto(self.maleta, product_quantity=5)
        p.quantity_sold = 5
        assert p.remaining_quantity == 0

    def test_clean_rejects_quantity_sold_exceeding_quantity(self):
        p = Produtos(
            product_briefcase=self.maleta,
            product_name='Anel',
            product_code=9001,
            product_value=Decimal('100.00'),
            product_quantity=5,
            quantity_sold=6,
        )
        with pytest.raises(ValidationError):
            p.full_clean()

    def test_product_code_unique_constraint(self):
        make_produto(self.maleta, product_code=9001)
        with pytest.raises(Exception):
            make_produto(self.maleta, product_code=9001)

    def test_product_value_negative_rejected(self):
        p = Produtos(
            product_briefcase=self.maleta,
            product_name='Anel',
            product_code=9001,
            product_value=Decimal('-1.00'),
            product_quantity=5,
        )
        with pytest.raises(ValidationError):
            p.full_clean()


# ─── Vendas model ─────────────────────────────────────────────────────────────

class TestVendasModel:

    @pytest.fixture(autouse=True)
    def setup(self):
        self.maleta = make_maleta()
        self.cliente = make_cliente()

    def test_str(self):
        v = make_venda(self.maleta, self.cliente)
        assert 'Maleta 741' in str(v)
        assert 'Maria' in str(v)

    def test_clean_any_method_without_installments_passes(self):
        for method in [PIX, CREDITO, PAYMENT_METHODS.DEBITO, PAYMENT_METHODS.DINHEIRO]:
            v = Vendas(
                client=self.cliente,
                briefcase=self.maleta,
                payment_method=method,
                in_good_standing=ADIMPLENTE,
            )
            v.full_clean()

    def test_gerar_parcelas_creates_correct_count(self):
        p = make_produto(self.maleta, product_value=Decimal('90.00'))
        v = make_venda(self.maleta, self.cliente, installments=3)
        make_item(v, p, quantity=1)
        v.refresh_from_db()
        v.gerar_parcelas()
        assert Parcela.objects.filter(venda=v).count() == 3

    def test_gerar_parcelas_total_equals_end_value(self):
        p = make_produto(self.maleta, product_value=Decimal('100.00'))
        v = make_venda(self.maleta, self.cliente, installments=3)
        make_item(v, p, quantity=1)
        v.refresh_from_db()
        v.gerar_parcelas()
        total = sum(p.valor for p in Parcela.objects.filter(venda=v))
        assert total == v.end_value

    def test_gerar_parcelas_no_installments_creates_none(self):
        v = make_venda(self.maleta, self.cliente)
        v.gerar_parcelas()
        assert Parcela.objects.filter(venda=v).count() == 0

    def test_gerar_parcelas_situacao_default_pendente(self):
        p = make_produto(self.maleta, product_value=Decimal('50.00'))
        v = make_venda(self.maleta, self.cliente, installments=2)
        make_item(v, p, quantity=1)
        v.refresh_from_db()
        v.gerar_parcelas()
        assert all(parc.situacao == 'pendente' for parc in Parcela.objects.filter(venda=v))

    def test_save_recalculates_sale_and_end_value_from_items(self):
        p = make_produto(self.maleta, product_value=Decimal('100.00'))
        v = make_venda(self.maleta, self.cliente)
        make_item(v, p, quantity=2)
        v.refresh_from_db()
        assert v.sale_value == Decimal('200.00')
        assert v.end_value == Decimal('200.00')

    def test_gross_value_calc_uses_unit_price(self):
        p = make_produto(self.maleta, product_value=Decimal('50.00'))
        v = make_venda(self.maleta, self.cliente)
        make_item(v, p, quantity=4)
        assert v.gross_value_calc == Decimal('200.00')

    def test_end_value_calc_applies_integer_discount_per_unit(self):
        p = make_produto(self.maleta, product_value=Decimal('100.00'))
        v = make_venda(self.maleta, self.cliente)
        make_item(v, p, quantity=2, integer_discount=Decimal('10.00'))
        assert v.end_value_calc == Decimal('180.00')

    def test_discount_calc_applies_percent_discount_per_quantity(self):
        p = make_produto(self.maleta, product_value=Decimal('100.00'))
        v = make_venda(self.maleta, self.cliente)
        make_item(v, p, quantity=2, discount_percent=Decimal('10.00'))
        assert v.gross_value_calc == Decimal('200.00')
        assert v.end_value_calc == Decimal('180.00')
        assert v.discount_calc == Decimal('20.00')
        assert v.discount_calc == v.gross_value_calc - v.end_value_calc

    def test_discount_calc_integer_discount_correctly_multiplied(self):
        p = make_produto(self.maleta, product_value=Decimal('100.00'))
        v = make_venda(self.maleta, self.cliente)
        make_item(v, p, quantity=2, integer_discount=Decimal('5.00'))
        assert v.discount_calc == Decimal('10.00')

    def test_delete_cascade_decrements_quantity_sold(self):
        p = make_produto(self.maleta, product_quantity=10)
        v = make_venda(self.maleta, self.cliente)
        make_item(v, p, quantity=3)
        p.refresh_from_db()
        assert p.quantity_sold == 3
        v.delete()
        p.refresh_from_db()
        assert p.quantity_sold == 0

    def test_delete_updates_briefcase_value_sold(self):
        p = make_produto(self.maleta, product_value=Decimal('100.00'), product_quantity=10)
        v = make_venda(self.maleta, self.cliente)
        make_item(v, p, quantity=2)
        self.maleta.refresh_from_db()
        assert self.maleta.value_sold == Decimal('200.00')
        v.delete()
        self.maleta.refresh_from_db()
        assert self.maleta.value_sold == Decimal('0.00')

    def test_delete_multiple_items_cascade_all(self):
        p1 = make_produto(self.maleta, product_code=9001, product_quantity=10)
        p2 = make_produto(self.maleta, product_code=9002, product_quantity=10)
        v = make_venda(self.maleta, self.cliente)
        make_item(v, p1, quantity=2)
        make_item(v, p2, quantity=3)
        v.delete()
        p1.refresh_from_db()
        p2.refresh_from_db()
        assert p1.quantity_sold == 0
        assert p2.quantity_sold == 0
        assert ItensVenda.objects.count() == 0


# ─── Vendas cancelar ──────────────────────────────────────────────────────────

class TestVendasCancelar:

    @pytest.fixture(autouse=True)
    def setup(self):
        self.maleta = make_maleta()
        self.cliente = make_cliente()
        self.produto = make_produto(self.maleta, product_quantity=10, product_value=Decimal('100.00'))
        self.venda = make_venda(self.maleta, self.cliente, installments=2)
        make_item(self.venda, self.produto, quantity=3)
        self.venda.refresh_from_db()
        self.venda.gerar_parcelas()

    def test_cancelar_sets_status_cancelada(self):
        self.venda.cancelar()
        self.venda.refresh_from_db()
        assert self.venda.status == 'cancelada'

    def test_cancelar_restores_quantity_sold(self):
        self.venda.cancelar()
        self.produto.refresh_from_db()
        assert self.produto.quantity_sold == 0

    def test_cancelar_marks_parcelas_canceladas(self):
        self.venda.cancelar()
        assert all(p.situacao == 'cancelada' for p in Parcela.objects.filter(venda=self.venda))

    def test_cancelar_updates_briefcase_value_sold(self):
        self.maleta.refresh_from_db()
        assert self.maleta.value_sold == Decimal('300.00')
        self.venda.cancelar()
        self.maleta.refresh_from_db()
        assert self.maleta.value_sold == Decimal('0.00')


# ─── Vendas queryset ──────────────────────────────────────────────────────────

class TestVendasQuerySet:

    @pytest.fixture(autouse=True)
    def setup(self):
        self.maleta1 = make_maleta(order_number=741)
        self.maleta2 = make_maleta(order_number=852)
        self.c1 = make_cliente(first_name='Ana', last_name='Silva', phone_number='11999998888')
        self.c2 = make_cliente(first_name='Bruno', last_name='Costa', phone_number='21988887777')
        self.v1 = make_venda(self.maleta1, self.c1)
        self.v2 = make_venda(self.maleta2, self.c2)

    def test_no_params_returns_all(self):
        assert Vendas.objects.param_filter().count() == 2

    def test_filter_by_client_first_name(self):
        qs = Vendas.objects.param_filter(client='Ana')
        assert self.v1 in qs
        assert self.v2 not in qs

    def test_filter_by_client_last_name(self):
        qs = Vendas.objects.param_filter(client='Costa')
        assert self.v2 in qs
        assert self.v1 not in qs

    def test_filter_by_client_case_insensitive(self):
        qs = Vendas.objects.param_filter(client='ana')
        assert self.v1 in qs

    def test_filter_by_briefcase_order_number(self):
        qs = Vendas.objects.param_filter(briefcase='741')
        assert self.v1 in qs
        assert self.v2 not in qs

    def test_filter_combined_client_and_briefcase(self):
        qs = Vendas.objects.param_filter(client='Ana', briefcase='741')
        assert self.v1 in qs
        assert self.v2 not in qs

    def test_filter_no_match(self):
        qs = Vendas.objects.param_filter(client='Inexistente')
        assert qs.count() == 0


# ─── ItensVenda save — new item ───────────────────────────────────────────────

class TestItensVendaSaveNew:

    @pytest.fixture(autouse=True)
    def setup(self):
        self.maleta = make_maleta()
        self.cliente = make_cliente()
        self.venda = make_venda(self.maleta, self.cliente)
        self.produto = make_produto(self.maleta, product_quantity=10, product_value=Decimal('100.00'))

    def test_new_item_increments_quantity_sold(self):
        make_item(self.venda, self.produto, quantity=3)
        self.produto.refresh_from_db()
        assert self.produto.quantity_sold == 3

    def test_new_item_sets_unit_price_from_product(self):
        item = make_item(self.venda, self.produto, quantity=1)
        assert item.unit_price == Decimal('100.00')

    def test_new_item_triggers_sale_recalculation(self):
        make_item(self.venda, self.produto, quantity=2)
        self.venda.refresh_from_db()
        assert self.venda.end_value == Decimal('200.00')

    def test_new_item_triggers_briefcase_value_update(self):
        make_item(self.venda, self.produto, quantity=2)
        self.maleta.refresh_from_db()
        assert self.maleta.value_sold == Decimal('200.00')

    def test_new_item_quantity_exceeds_remaining_raises(self):
        p = make_produto(self.maleta, product_code=9002, product_quantity=2)
        with pytest.raises(ValidationError):
            make_item(self.venda, p, quantity=3)

    def test_new_item_exactly_remaining_quantity_succeeds(self):
        p = make_produto(self.maleta, product_code=9002, product_quantity=5)
        make_item(self.venda, p, quantity=5)
        p.refresh_from_db()
        assert p.quantity_sold == 5
        assert p.remaining_quantity == 0

    def test_new_item_no_quantity_sold_when_validation_fails(self):
        p = make_produto(self.maleta, product_code=9002, product_quantity=2)
        try:
            make_item(self.venda, p, quantity=5)
        except ValidationError:
            pass
        p.refresh_from_db()
        assert p.quantity_sold == 0

    def test_end_value_applies_percent_discount(self):
        item = make_item(self.venda, self.produto, quantity=1, discount_percent=Decimal('10.00'))
        assert item.end_value == Decimal('90.00')

    def test_end_value_applies_integer_discount(self):
        item = make_item(self.venda, self.produto, quantity=1, integer_discount=Decimal('15.00'))
        assert item.end_value == Decimal('85.00')

    def test_end_value_applies_both_discounts(self):
        item = make_item(
            self.venda, self.produto, quantity=1,
            discount_percent=Decimal('10.00'),
            integer_discount=Decimal('5.00'),
        )
        assert item.end_value == Decimal('85.00')

    def test_subtotal_property(self):
        item = make_item(self.venda, self.produto, quantity=3)
        assert item.subtotal == Decimal('300.00')

    def test_duplicate_product_in_same_sale_raises(self):
        make_item(self.venda, self.produto, quantity=1)
        with pytest.raises(ValidationError):
            make_item(self.venda, self.produto, quantity=2)

    def test_same_product_different_sales_is_allowed(self):
        v2 = make_venda(self.maleta, self.cliente, payment_method=PAYMENT_METHODS.DEBITO)
        make_item(self.venda, self.produto, quantity=1)
        make_item(v2, self.produto, quantity=1)
        self.produto.refresh_from_db()
        assert self.produto.quantity_sold == 2


# ─── ItensVenda save — update ─────────────────────────────────────────────────

class TestItensVendaSaveUpdate:

    @pytest.fixture(autouse=True)
    def setup(self):
        self.maleta = make_maleta()
        self.cliente = make_cliente()
        self.venda = make_venda(self.maleta, self.cliente)
        self.produto = make_produto(self.maleta, product_code=9001, product_quantity=10, product_value=Decimal('100.00'))
        self.item = make_item(self.venda, self.produto, quantity=3)

    def test_update_same_product_increase_quantity(self):
        self.item.quantity = 5
        self.item.save()
        self.produto.refresh_from_db()
        assert self.produto.quantity_sold == 5

    def test_update_same_product_decrease_quantity(self):
        self.item.quantity = 1
        self.item.save()
        self.produto.refresh_from_db()
        assert self.produto.quantity_sold == 1

    def test_update_same_product_quantity_exceeds_available_raises(self):
        self.item.quantity = 11
        with pytest.raises(ValidationError):
            self.item.save()

    def test_update_same_product_quantity_exactly_at_limit(self):
        self.item.quantity = 10
        self.item.save()
        self.produto.refresh_from_db()
        assert self.produto.quantity_sold == 10

    def test_update_same_product_does_not_change_quantity_sold_on_failure(self):
        self.produto.refresh_from_db()
        old_sold = self.produto.quantity_sold
        self.item.quantity = 100
        try:
            self.item.save()
        except ValidationError:
            pass
        self.produto.refresh_from_db()
        assert self.produto.quantity_sold == old_sold

    def test_update_different_product_decrements_old_increments_new(self):
        p2 = make_produto(self.maleta, product_code=9002, product_quantity=10)
        self.item.product = p2
        self.item.quantity = 4
        self.item.save()
        self.produto.refresh_from_db()
        p2.refresh_from_db()
        assert self.produto.quantity_sold == 0
        assert p2.quantity_sold == 4

    def test_update_different_product_insufficient_new_raises(self):
        p2 = make_produto(self.maleta, product_code=9002, product_quantity=2)
        self.item.product = p2
        self.item.quantity = 3
        with pytest.raises(ValidationError):
            self.item.save()

    def test_update_triggers_sale_recalculation(self):
        self.item.quantity = 5
        self.item.save()
        self.venda.refresh_from_db()
        assert self.venda.end_value == Decimal('500.00')

    def test_update_triggers_briefcase_recalculation(self):
        self.item.quantity = 5
        self.item.save()
        self.maleta.refresh_from_db()
        assert self.maleta.value_sold == Decimal('500.00')


# ─── ItensVenda delete ────────────────────────────────────────────────────────

class TestItensVendaDelete:

    @pytest.fixture(autouse=True)
    def setup(self):
        self.maleta = make_maleta()
        self.cliente = make_cliente()
        self.venda = make_venda(self.maleta, self.cliente)
        self.produto = make_produto(self.maleta, product_quantity=10, product_value=Decimal('100.00'))
        self.item = make_item(self.venda, self.produto, quantity=4)

    def test_delete_decrements_quantity_sold(self):
        self.item.delete()
        self.produto.refresh_from_db()
        assert self.produto.quantity_sold == 0

    def test_delete_updates_sale_end_value(self):
        self.item.delete()
        self.venda.refresh_from_db()
        assert self.venda.end_value == Decimal('0.00')

    def test_delete_updates_briefcase_value_sold(self):
        self.item.delete()
        self.maleta.refresh_from_db()
        assert self.maleta.value_sold == Decimal('0.00')

    def test_delete_inconsistent_quantity_sold_raises(self):
        Produtos.objects.filter(pk=self.produto.pk).update(quantity_sold=0)
        with pytest.raises(ValidationError):
            self.item.delete()

    def test_delete_partial_leaves_other_items_intact(self):
        p2 = make_produto(self.maleta, product_code=9002, product_quantity=10, product_value=Decimal('50.00'))
        item2 = make_item(self.venda, p2, quantity=2)
        self.item.delete()
        assert ItensVenda.objects.filter(pk=item2.pk).exists()
        p2.refresh_from_db()
        assert p2.quantity_sold == 2


# ─── Maleta views ─────────────────────────────────────────────────────────────

class TestExibirMaletas:

    @pytest.fixture(autouse=True)
    def setup(self, auth_client):
        self.http = auth_client
        self.m1 = make_maleta(order_number=741, month=MONTH_SELECTION.JANEIRO)
        self.m2 = make_maleta(order_number=852, month=MONTH_SELECTION.FEVEREIRO)

    def test_get_lists_all_maletas(self):
        response = self.http.get(reverse('sales:maletas_lista'))
        assert response.status_code == 200
        assert '741' in response.content.decode()
        assert '852' in response.content.decode()

    def test_get_with_month_filter(self):
        response = self.http.get(reverse('sales:maletas_lista'), {'month': 'Janeiro'})
        assert '741' in response.content.decode()
        assert '852' not in response.content.decode()

    def test_get_with_order_number_filter(self):
        response = self.http.get(reverse('sales:maletas_lista'), {'order': '852'})
        assert '852' in response.content.decode()
        assert '741' not in response.content.decode()


class TestInfoMaleta:

    @pytest.fixture(autouse=True)
    def setup(self, auth_client):
        self.http = auth_client
        self.maleta = make_maleta()

    def test_get_returns_200(self):
        response = self.http.get(reverse('sales:info_maleta', args=[self.maleta.id]))
        assert response.status_code == 200

    def test_context_has_maleta_and_vendas(self):
        response = self.http.get(reverse('sales:info_maleta', args=[self.maleta.id]))
        assert 'maleta' in response.context
        assert 'vendas' in response.context

    def test_404_for_nonexistent_maleta(self):
        response = self.http.get(reverse('sales:info_maleta', args=[9999]))
        assert response.status_code == 404


class TestCadastrarMaleta:

    @pytest.fixture(autouse=True)
    def setup(self, auth_client):
        self.http = auth_client
        self.url = reverse('sales:cadastro_maleta')

    def test_get_renders_form(self):
        response = self.http.get(self.url)
        assert response.status_code == 200

    def test_post_valid_creates_and_redirects(self):
        response = self.http.post(self.url, {
            'month': str(MONTH_SELECTION.JANEIRO),
            'start_sale_period': '2025-01-01',
            'end_sale_period': '2025-01-31',
            'order_number': 741,
            'order_value': '1000.00',
        })
        assert response.status_code == 302
        assert response.url == reverse('sales:maletas_lista')
        assert Maleta.objects.filter(order_number=741).exists()

    def test_post_end_before_start_does_not_create(self):
        self.http.post(self.url, {
            'month': str(MONTH_SELECTION.JANEIRO),
            'start_sale_period': '2025-01-31',
            'end_sale_period': '2025-01-01',
            'order_number': 741,
            'order_value': '1000.00',
        })
        assert Maleta.objects.count() == 0

    def test_post_duplicate_order_number_does_not_create(self):
        make_maleta(order_number=741)
        self.http.post(self.url, {
            'month': str(MONTH_SELECTION.FEVEREIRO),
            'start_sale_period': '2025-02-01',
            'end_sale_period': '2025-02-28',
            'order_number': 741,
            'order_value': '500.00',
        })
        assert Maleta.objects.count() == 1

    def test_post_invalid_re_renders_with_errors(self):
        response = self.http.post(self.url, {
            'month': str(MONTH_SELECTION.JANEIRO),
            'start_sale_period': '2025-01-31',
            'end_sale_period': '2025-01-01',
            'order_number': 741,
            'order_value': '1000.00',
        })
        assert response.status_code == 200
        assert response.context['form'].errors


class TestAtualizarMaleta:

    @pytest.fixture(autouse=True)
    def setup(self, auth_client):
        self.http = auth_client
        self.maleta = make_maleta(order_number=741)
        self.url = reverse('sales:atualizar_maleta', args=[self.maleta.id])

    def test_get_renders_form(self):
        response = self.http.get(self.url)
        assert response.status_code == 200

    def test_post_valid_updates_and_redirects(self):
        response = self.http.post(self.url, {
            'month': str(MONTH_SELECTION.FEVEREIRO),
            'start_sale_period': '2025-02-01',
            'end_sale_period': '2025-02-28',
            'order_number': 741,
            'order_value': '2000.00',
        })
        assert response.status_code == 302
        assert response.url == reverse('sales:maletas_lista')
        self.maleta.refresh_from_db()
        assert self.maleta.order_value == Decimal('2000.00')

    def test_post_invalid_does_not_update(self):
        self.http.post(self.url, {
            'month': str(MONTH_SELECTION.FEVEREIRO),
            'start_sale_period': '2025-01-31',
            'end_sale_period': '2025-01-01',
            'order_number': 741,
            'order_value': '2000.00',
        })
        self.maleta.refresh_from_db()
        assert self.maleta.order_value == Decimal('1000.00')

    def test_post_invalid_re_renders_with_errors(self):
        response = self.http.post(self.url, {
            'month': str(MONTH_SELECTION.FEVEREIRO),
            'start_sale_period': '2025-01-31',
            'end_sale_period': '2025-01-01',
            'order_number': 741,
            'order_value': '2000.00',
        })
        assert response.status_code == 200
        assert response.context['form'].errors

    def test_404_for_nonexistent_maleta(self):
        response = self.http.get(reverse('sales:atualizar_maleta', args=[9999]))
        assert response.status_code == 404


class TestDeletarMaleta:

    @pytest.fixture(autouse=True)
    def setup(self, auth_client):
        self.http = auth_client
        self.maleta = make_maleta()

    def test_post_deletes_and_redirects(self):
        response = self.http.post(reverse('sales:deletar_maleta', args=[self.maleta.id]))
        assert response.status_code == 302
        assert response.url == reverse('sales:maletas_lista')
        assert not Maleta.objects.filter(id=self.maleta.id).exists()

    def test_get_does_not_delete(self):
        self.http.get(reverse('sales:deletar_maleta', args=[self.maleta.id]))
        assert Maleta.objects.filter(id=self.maleta.id).exists()

    def test_get_redirects_to_lista(self):
        response = self.http.get(reverse('sales:deletar_maleta', args=[self.maleta.id]))
        assert response.status_code == 302
        assert response.url == reverse('sales:maletas_lista')

    def test_404_for_nonexistent_maleta(self):
        response = self.http.post(reverse('sales:deletar_maleta', args=[9999]))
        assert response.status_code == 404


# ─── Vendas views ─────────────────────────────────────────────────────────────

class TestNovaVendaItens:

    @pytest.fixture(autouse=True)
    def setup(self, auth_client):
        self.http = auth_client
        self.maleta = make_maleta()
        self.produto = make_produto(self.maleta, product_quantity=10)
        self.url = reverse('sales:registrar_venda', args=[self.maleta.id])
        self.session_key = f'nova_venda_maleta_{self.maleta.id}'

    def _post_add(self, product_id=None, quantity=1, discount_percent='0', integer_discount='0'):
        return self.http.post(self.url, {
            'action': 'add',
            'product': product_id or self.produto.id,
            'quantity': quantity,
            'discount_percent': discount_percent,
            'integer_discount': integer_discount,
        })

    def test_get_renders_form(self):
        response = self.http.get(self.url)
        assert response.status_code == 200

    def test_get_404_for_nonexistent_maleta(self):
        response = self.http.get(reverse('sales:registrar_venda', args=[9999]))
        assert response.status_code == 404

    def test_post_add_saves_item_to_session(self):
        self._post_add(quantity=2)
        session = self.http.session
        assert len(session[self.session_key]) == 1
        assert session[self.session_key][0]['product_id'] == self.produto.id
        assert session[self.session_key][0]['quantity'] == 2

    def test_post_add_duplicate_product_rejected(self):
        self._post_add(quantity=1)
        self._post_add(quantity=1)
        session = self.http.session
        assert len(session.get(self.session_key, [])) == 1

    def test_post_add_invalid_quantity_zero_rejected(self):
        self._post_add(quantity=0)
        session = self.http.session
        assert len(session.get(self.session_key, [])) == 0

    def test_post_add_exceeding_stock_rejected(self):
        p = make_produto(self.maleta, product_code=9002, product_quantity=2)
        self.http.post(self.url, {'action': 'add', 'product': p.id, 'quantity': 5, 'discount_percent': '0', 'integer_discount': '0'})
        session = self.http.session
        assert len(session.get(self.session_key, [])) == 0

    def test_post_add_excess_discount_rejected(self):
        self._post_add(integer_discount='999')
        session = self.http.session
        assert len(session.get(self.session_key, [])) == 0

    def test_post_remove_removes_item_from_session(self):
        self._post_add(quantity=1)
        self.http.post(self.url, {'action': 'remove', 'product_id': self.produto.id})
        session = self.http.session
        assert len(session.get(self.session_key, [])) == 0

    def test_post_cancelar_clears_session_and_redirects(self):
        self._post_add(quantity=1)
        response = self.http.post(self.url, {'action': 'cancelar'})
        assert response.status_code == 302
        assert response.url == reverse('sales:info_maleta', args=[self.maleta.id])
        assert self.session_key not in self.http.session

    def test_post_next_with_empty_session_stays_on_page(self):
        response = self.http.post(self.url, {'action': 'next'})
        assert response.status_code == 302
        assert response.url == self.url

    def test_post_next_with_items_redirects_to_verificar(self):
        self._post_add(quantity=1)
        response = self.http.post(self.url, {'action': 'next'})
        assert response.status_code == 302
        assert response.url == reverse('sales:nova_venda_verificar', args=[self.maleta.id])


class TestNovaVendaVerificar:

    @pytest.fixture(autouse=True)
    def setup(self, auth_client):
        self.http = auth_client
        self.maleta = make_maleta()
        self.produto = make_produto(self.maleta, product_value=Decimal('100.00'), product_quantity=10)
        self.url = reverse('sales:nova_venda_verificar', args=[self.maleta.id])
        self.session_key = f'nova_venda_maleta_{self.maleta.id}'

    def _set_session(self, itens):
        session = self.http.session
        session[self.session_key] = itens
        session.save()

    def test_get_with_empty_session_redirects_to_step1(self):
        response = self.http.get(self.url)
        assert response.status_code == 302
        assert response.url == reverse('sales:registrar_venda', args=[self.maleta.id])

    def test_get_with_items_returns_200(self):
        self._set_session([{'product_id': self.produto.id, 'quantity': 2, 'discount_percent': '0', 'integer_discount': '0'}])
        response = self.http.get(self.url)
        assert response.status_code == 200

    def test_get_context_has_totals(self):
        self._set_session([{'product_id': self.produto.id, 'quantity': 2, 'discount_percent': '0', 'integer_discount': '0'}])
        response = self.http.get(self.url)
        assert response.context['end_total'] == Decimal('200.00')

    def test_post_redirects_to_step3(self):
        self._set_session([{'product_id': self.produto.id, 'quantity': 1, 'discount_percent': '0', 'integer_discount': '0'}])
        response = self.http.post(self.url)
        assert response.status_code == 302
        assert response.url == reverse('sales:nova_venda_dados', args=[self.maleta.id])


class TestNovaVendaDados:

    @pytest.fixture(autouse=True)
    def setup(self, auth_client):
        self.http = auth_client
        self.maleta = make_maleta()
        self.cliente = make_cliente()
        self.produto = make_produto(self.maleta, product_value=Decimal('100.00'), product_quantity=10)
        self.url = reverse('sales:nova_venda_dados', args=[self.maleta.id])
        self.session_key = f'nova_venda_maleta_{self.maleta.id}'
        session = auth_client.session
        session[self.session_key] = [{'product_id': self.produto.id, 'quantity': 2, 'discount_percent': '0', 'integer_discount': '0'}]
        session.save()

    def _valid_post(self):
        return {'client': self.cliente.id, 'payment_method': str(PIX), 'in_good_standing': str(ADIMPLENTE)}

    def test_get_with_empty_session_redirects_to_step1(self):
        session = self.http.session
        del session[self.session_key]
        session.save()
        response = self.http.get(self.url)
        assert response.status_code == 302
        assert response.url == reverse('sales:registrar_venda', args=[self.maleta.id])

    def test_get_renders_form(self):
        response = self.http.get(self.url)
        assert response.status_code == 200

    def test_post_valid_creates_venda_and_redirects(self):
        response = self.http.post(self.url, self._valid_post())
        assert Vendas.objects.count() == 1
        venda = Vendas.objects.first()
        assert response.status_code == 302
        assert response.url == reverse('sales:info_vendas', args=[venda.id])

    def test_post_valid_creates_itens(self):
        self.http.post(self.url, self._valid_post())
        assert ItensVenda.objects.count() == 1

    def test_post_valid_venda_linked_to_maleta(self):
        self.http.post(self.url, self._valid_post())
        venda = Vendas.objects.first()
        assert venda.briefcase == self.maleta

    def test_post_valid_clears_session(self):
        self.http.post(self.url, self._valid_post())
        assert self.session_key not in self.http.session

    def test_post_with_installments_creates_parcelas(self):
        data = self._valid_post()
        data['installments'] = 2
        self.http.post(self.url, data)
        venda = Vendas.objects.first()
        assert Parcela.objects.filter(venda=venda).count() == 2

    def test_post_without_installments_creates_no_parcelas(self):
        self.http.post(self.url, self._valid_post())
        assert Parcela.objects.count() == 0

    def test_post_no_client_does_not_create(self):
        data = self._valid_post()
        del data['client']
        self.http.post(self.url, data)
        assert Vendas.objects.count() == 0

    def test_post_credit_without_installments_creates(self):
        data = self._valid_post()
        data['payment_method'] = str(CREDITO)
        self.http.post(self.url, data)
        assert Vendas.objects.count() == 1

    def test_post_venda_created_with_status_ativa(self):
        self.http.post(self.url, self._valid_post())
        venda = Vendas.objects.first()
        assert venda.status == 'ativa'


class TestToggleParcela:

    @pytest.fixture(autouse=True)
    def setup(self, auth_client):
        self.http = auth_client
        self.maleta = make_maleta()
        self.cliente = make_cliente()
        self.produto = make_produto(self.maleta, product_value=Decimal('100.00'), product_quantity=10)
        self.venda = make_venda(self.maleta, self.cliente, installments=2)
        make_item(self.venda, self.produto, quantity=1)
        self.venda.refresh_from_db()
        self.venda.gerar_parcelas()
        self.parcela = Parcela.objects.filter(venda=self.venda).first()

    def test_post_pendente_to_pago(self):
        assert self.parcela.situacao == 'pendente'
        self.http.post(reverse('sales:toggle_parcela', args=[self.parcela.id]))
        self.parcela.refresh_from_db()
        assert self.parcela.situacao == 'pago'

    def test_post_pago_to_pendente(self):
        self.parcela.situacao = 'pago'
        self.parcela.save()
        self.http.post(reverse('sales:toggle_parcela', args=[self.parcela.id]))
        self.parcela.refresh_from_db()
        assert self.parcela.situacao == 'pendente'

    def test_post_cancelled_parcela_not_toggled(self):
        self.parcela.situacao = 'cancelada'
        self.parcela.save()
        self.http.post(reverse('sales:toggle_parcela', args=[self.parcela.id]))
        self.parcela.refresh_from_db()
        assert self.parcela.situacao == 'cancelada'

    def test_post_redirects_to_info_vendas(self):
        response = self.http.post(reverse('sales:toggle_parcela', args=[self.parcela.id]))
        assert response.status_code == 302
        assert response.url == reverse('sales:info_vendas', args=[self.venda.id])

    def test_get_does_not_toggle(self):
        self.http.get(reverse('sales:toggle_parcela', args=[self.parcela.id]))
        self.parcela.refresh_from_db()
        assert self.parcela.situacao == 'pendente'

    def test_404_for_nonexistent_parcela(self):
        response = self.http.post(reverse('sales:toggle_parcela', args=[9999]))
        assert response.status_code == 404


class TestAtualizarVenda:

    @pytest.fixture(autouse=True)
    def setup(self, auth_client):
        self.http = auth_client
        self.maleta = make_maleta()
        self.cliente = make_cliente()
        self.venda = make_venda(self.maleta, self.cliente)
        self.url = reverse('sales:atualizar_venda', args=[self.venda.id])

    def test_get_renders_form(self):
        response = self.http.get(self.url)
        assert response.status_code == 200

    def test_post_valid_updates_in_good_standing_and_redirects(self):
        response = self.http.post(self.url, {'in_good_standing': str(INADIMPLENTE)})
        assert response.status_code == 302
        assert response.url == reverse('sales:info_vendas', args=[self.venda.id])
        self.venda.refresh_from_db()
        assert self.venda.in_good_standing == str(INADIMPLENTE)

    def test_post_does_not_change_payment_method(self):
        self.http.post(self.url, {'in_good_standing': str(INADIMPLENTE)})
        self.venda.refresh_from_db()
        assert self.venda.payment_method == str(PIX)

    def test_post_client_not_changed_by_edit(self):
        original_client = self.venda.client
        self.http.post(self.url, {'in_good_standing': str(INADIMPLENTE)})
        self.venda.refresh_from_db()
        assert self.venda.client == original_client

    def test_404_for_nonexistent_venda(self):
        response = self.http.get(reverse('sales:atualizar_venda', args=[9999]))
        assert response.status_code == 404


class TestInfoVendas:

    @pytest.fixture(autouse=True)
    def setup(self, auth_client):
        self.http = auth_client
        self.maleta = make_maleta()
        self.cliente = make_cliente()
        self.venda = make_venda(self.maleta, self.cliente)

    def test_get_returns_200(self):
        response = self.http.get(reverse('sales:info_vendas', args=[self.venda.id]))
        assert response.status_code == 200

    def test_context_has_required_keys(self):
        response = self.http.get(reverse('sales:info_vendas', args=[self.venda.id]))
        assert 'items_data' in response.context
        assert 'devolucoes' in response.context
        assert 'garantias' in response.context

    def test_items_data_contains_subtotal(self):
        p = make_produto(self.maleta, product_value=Decimal('50.00'))
        make_item(self.venda, p, quantity=3)
        response = self.http.get(reverse('sales:info_vendas', args=[self.venda.id]))
        items_data = response.context['items_data']
        assert len(items_data) == 1
        assert items_data[0]['subtotal'] == Decimal('150.00')

    def test_404_for_nonexistent_venda(self):
        response = self.http.get(reverse('sales:info_vendas', args=[9999]))
        assert response.status_code == 404


class TestCancelarVenda:

    @pytest.fixture(autouse=True)
    def setup(self, auth_client):
        self.http = auth_client
        self.maleta = make_maleta()
        self.cliente = make_cliente()
        self.produto = make_produto(self.maleta, product_quantity=10, product_value=Decimal('100.00'))
        self.venda = make_venda(self.maleta, self.cliente)
        make_item(self.venda, self.produto, quantity=3)
        self.url = reverse('sales:cancelar_venda', args=[self.venda.id])

    def test_get_returns_200_for_ativa_venda(self):
        response = self.http.get(self.url)
        assert response.status_code == 200

    def test_get_already_cancelled_redirects(self):
        Vendas.objects.filter(pk=self.venda.pk).update(status='cancelada')
        response = self.http.get(self.url)
        assert response.status_code == 302

    def test_post_sets_status_cancelada(self):
        self.http.post(self.url)
        self.venda.refresh_from_db()
        assert self.venda.status == 'cancelada'

    def test_post_restores_inventory(self):
        self.http.post(self.url)
        self.produto.refresh_from_db()
        assert self.produto.quantity_sold == 0

    def test_post_redirects_to_info_vendas(self):
        response = self.http.post(self.url)
        assert response.status_code == 302
        assert response.url == reverse('sales:info_vendas', args=[self.venda.id])

    def test_post_on_already_cancelled_redirects(self):
        Vendas.objects.filter(pk=self.venda.pk).update(status='cancelada')
        response = self.http.post(self.url)
        assert response.status_code == 302

    def test_post_updates_briefcase_value(self):
        self.maleta.refresh_from_db()
        assert self.maleta.value_sold == Decimal('300.00')
        self.http.post(self.url)
        self.maleta.refresh_from_db()
        assert self.maleta.value_sold == Decimal('0.00')

    def test_404_for_nonexistent_venda(self):
        response = self.http.post(reverse('sales:cancelar_venda', args=[9999]))
        assert response.status_code == 404


# ─── Devolução views ──────────────────────────────────────────────────────────

class TestRegistrarDevolucao:

    @pytest.fixture(autouse=True)
    def setup(self, auth_client):
        self.http = auth_client
        self.maleta = make_maleta()
        self.cliente = make_cliente()
        self.produto = make_produto(self.maleta, product_quantity=10, product_value=Decimal('100.00'))
        self.venda = make_venda(self.maleta, self.cliente)
        self.item = make_item(self.venda, self.produto, quantity=4)
        self.url = reverse('sales:registrar_devolucao', args=[self.venda.id])

    def test_get_returns_200(self):
        response = self.http.get(self.url)
        assert response.status_code == 200

    def test_post_creates_devolucao(self):
        self.http.post(self.url, {f'quantidade_{self.item.id}': 2, 'motivo': 'defeito'})
        assert Devolucao.objects.count() == 1

    def test_post_creates_item_devolucao(self):
        self.http.post(self.url, {f'quantidade_{self.item.id}': 2, 'motivo': 'defeito'})
        assert ItemDevolucao.objects.count() == 1

    def test_post_restores_inventory(self):
        self.http.post(self.url, {f'quantidade_{self.item.id}': 2, 'motivo': 'defeito'})
        self.produto.refresh_from_db()
        assert self.produto.quantity_sold == 2

    def test_post_sets_status_devolvida_parcial(self):
        self.http.post(self.url, {f'quantidade_{self.item.id}': 1, 'motivo': ''})
        self.venda.refresh_from_db()
        assert self.venda.status == 'devolvida_parcial'

    def test_post_zero_quantities_does_not_create(self):
        self.http.post(self.url, {f'quantidade_{self.item.id}': 0, 'motivo': ''})
        assert Devolucao.objects.count() == 0

    def test_post_excessive_quantity_does_not_create(self):
        self.http.post(self.url, {f'quantidade_{self.item.id}': 99, 'motivo': ''})
        assert Devolucao.objects.count() == 0

    def test_cancelled_venda_redirects(self):
        Vendas.objects.filter(pk=self.venda.pk).update(status='cancelada')
        response = self.http.get(self.url)
        assert response.status_code == 302

    def test_valor_estornado_calculated_correctly(self):
        self.http.post(self.url, {f'quantidade_{self.item.id}': 2, 'motivo': ''})
        item_dev = ItemDevolucao.objects.first()
        assert item_dev.valor_estornado == Decimal('200.00')

    def test_redirect_to_info_vendas_on_success(self):
        response = self.http.post(self.url, {f'quantidade_{self.item.id}': 1, 'motivo': ''})
        assert response.status_code == 302
        assert response.url == reverse('sales:info_vendas', args=[self.venda.id])


# ─── Garantia views ───────────────────────────────────────────────────────────

class TestRegistrarGarantia:

    @pytest.fixture(autouse=True)
    def setup(self, auth_client):
        self.http = auth_client
        self.maleta = make_maleta()
        self.cliente = make_cliente()
        self.produto = make_produto(self.maleta, product_quantity=10, product_value=Decimal('100.00'))
        self.venda = make_venda(self.maleta, self.cliente)
        self.item = make_item(self.venda, self.produto, quantity=3)
        self.url = reverse('sales:registrar_garantia', args=[self.venda.id])

    def test_get_returns_200(self):
        response = self.http.get(self.url)
        assert response.status_code == 200

    def test_post_creates_garantia(self):
        self.http.post(self.url, {'item_venda': self.item.id, 'quantidade': 1, 'motivo': 'arranhado'})
        assert Garantia.objects.count() == 1

    def test_post_redirects_to_info_vendas(self):
        response = self.http.post(self.url, {'item_venda': self.item.id, 'quantidade': 1, 'motivo': 'arranhado'})
        assert response.status_code == 302
        assert response.url == reverse('sales:info_vendas', args=[self.venda.id])

    def test_post_zero_quantity_does_not_create(self):
        self.http.post(self.url, {'item_venda': self.item.id, 'quantidade': 0, 'motivo': 'arranhado'})
        assert Garantia.objects.count() == 0

    def test_post_missing_motivo_does_not_create(self):
        self.http.post(self.url, {'item_venda': self.item.id, 'quantidade': 1, 'motivo': ''})
        assert Garantia.objects.count() == 0

    def test_post_quantity_exceeds_item_quantity_does_not_create(self):
        self.http.post(self.url, {'item_venda': self.item.id, 'quantidade': 99, 'motivo': 'arranhado'})
        assert Garantia.objects.count() == 0

    def test_cancelled_venda_redirects(self):
        Vendas.objects.filter(pk=self.venda.pk).update(status='cancelada')
        response = self.http.get(self.url)
        assert response.status_code == 302

    def test_garantia_default_status_enviado(self):
        self.http.post(self.url, {'item_venda': self.item.id, 'quantidade': 1, 'motivo': 'arranhado'})
        g = Garantia.objects.first()
        assert g.status == 'enviado'


class TestAtualizarGarantia:

    @pytest.fixture(autouse=True)
    def setup(self, auth_client):
        self.http = auth_client
        self.maleta = make_maleta()
        self.cliente = make_cliente()
        self.produto = make_produto(self.maleta, product_quantity=10)
        self.venda = make_venda(self.maleta, self.cliente)
        self.item = make_item(self.venda, self.produto, quantity=1)
        self.garantia = Garantia.objects.create(item_venda=self.item, quantidade=1, motivo='teste')
        self.url = reverse('sales:atualizar_garantia', args=[self.garantia.id])

    def test_get_returns_200(self):
        response = self.http.get(self.url)
        assert response.status_code == 200

    def test_post_updates_status(self):
        self.http.post(self.url, {'status': 'em_analise'})
        self.garantia.refresh_from_db()
        assert self.garantia.status == 'em_analise'

    def test_post_redirects_to_info_vendas(self):
        response = self.http.post(self.url, {'status': 'resolvido'})
        assert response.status_code == 302
        assert response.url == reverse('sales:info_vendas', args=[self.venda.id])

    def test_post_invalid_status_does_not_update(self):
        self.http.post(self.url, {'status': 'invalido'})
        self.garantia.refresh_from_db()
        assert self.garantia.status == 'enviado'

    def test_404_for_nonexistent_garantia(self):
        response = self.http.get(reverse('sales:atualizar_garantia', args=[9999]))
        assert response.status_code == 404


# ─── Produtos queryset ────────────────────────────────────────────────────────

class TestProdutosQuerySet:

    @pytest.fixture(autouse=True)
    def setup(self):
        self.maleta = make_maleta()
        self.p1 = make_produto(self.maleta, product_code=9001, product_name='Anel')
        self.p2 = make_produto(self.maleta, product_code=9002, product_name='Brinco')
        self.p3 = make_produto(self.maleta, product_code=9003, product_name='Colar')

    def test_no_params_returns_all(self):
        qs = Produtos.objects.filter(product_briefcase=self.maleta).param_filter()
        assert qs.count() == 3

    def test_filter_by_product_name(self):
        qs = Produtos.objects.filter(product_briefcase=self.maleta).param_filter(product_name='Anel')
        assert self.p1 in qs
        assert self.p2 not in qs

    def test_filter_by_product_name_case_insensitive(self):
        qs = Produtos.objects.filter(product_briefcase=self.maleta).param_filter(product_name='anel')
        assert self.p1 in qs

    def test_filter_by_product_name_partial(self):
        qs = Produtos.objects.filter(product_briefcase=self.maleta).param_filter(product_name='rin')
        assert self.p2 in qs
        assert self.p1 not in qs

    def test_filter_by_product_code(self):
        qs = Produtos.objects.filter(product_briefcase=self.maleta).param_filter(product_code='9002')
        assert self.p2 in qs
        assert self.p1 not in qs

    def test_filter_combined_name_and_code(self):
        qs = Produtos.objects.filter(product_briefcase=self.maleta).param_filter(product_name='Anel', product_code='9001')
        assert self.p1 in qs
        assert self.p2 not in qs

    def test_filter_no_match(self):
        qs = Produtos.objects.filter(product_briefcase=self.maleta).param_filter(product_name='Inexistente')
        assert qs.count() == 0

    def test_empty_string_params_returns_all(self):
        qs = Produtos.objects.filter(product_briefcase=self.maleta).param_filter(product_name='', product_code='')
        assert qs.count() == 3


# ─── ItensVenda clean ─────────────────────────────────────────────────────────

class TestItensVendaClean:

    @pytest.fixture(autouse=True)
    def setup(self):
        self.maleta = make_maleta()
        self.cliente = make_cliente()
        self.venda = make_venda(self.maleta, self.cliente)
        self.produto = make_produto(self.maleta, product_quantity=10, product_value=Decimal('100.00'))

    def test_total_discount_exceeds_unit_price_raises(self):
        item = ItensVenda(
            sale=self.venda, product=self.produto, quantity=1,
            discount_percent=Decimal('50.00'), integer_discount=Decimal('60.00'),
        )
        with pytest.raises(ValidationError):
            item.full_clean()

    def test_integer_discount_equals_unit_price_is_valid(self):
        item = ItensVenda(
            sale=self.venda, product=self.produto, quantity=1,
            discount_percent=Decimal('0.00'), integer_discount=Decimal('100.00'),
        )
        item.full_clean()

    def test_percent_discount_100_is_valid(self):
        item = ItensVenda(
            sale=self.venda, product=self.produto, quantity=1,
            discount_percent=Decimal('100.00'), integer_discount=Decimal('0.00'),
        )
        item.full_clean()

    def test_combined_discounts_equal_unit_price_is_valid(self):
        item = ItensVenda(
            sale=self.venda, product=self.produto, quantity=1,
            discount_percent=Decimal('50.00'), integer_discount=Decimal('50.00'),
        )
        item.full_clean()

    def test_percent_discount_over_100_raises(self):
        item = ItensVenda(
            sale=self.venda, product=self.produto, quantity=1,
            discount_percent=Decimal('101.00'), integer_discount=Decimal('0.00'),
        )
        with pytest.raises(ValidationError):
            item.full_clean()


# ─── Vendas por cliente view ──────────────────────────────────────────────────

class TestVendasPorCliente:

    @pytest.fixture(autouse=True)
    def setup(self, auth_client):
        self.http = auth_client
        self.maleta = make_maleta()
        self.cliente = make_cliente()

    def test_get_returns_200(self):
        response = self.http.get(reverse('sales:vendas_por_cliente', args=[self.cliente.id]))
        assert response.status_code == 200

    def test_context_has_cliente_and_vendas(self):
        response = self.http.get(reverse('sales:vendas_por_cliente', args=[self.cliente.id]))
        assert 'cliente' in response.context
        assert 'vendas' in response.context

    def test_shows_only_vendas_for_client(self):
        c2 = make_cliente(first_name='Bruno', last_name='Costa', phone_number='21988887777')
        v1 = make_venda(self.maleta, self.cliente)
        v2 = make_venda(self.maleta, c2, payment_method=PAYMENT_METHODS.DEBITO)
        response = self.http.get(reverse('sales:vendas_por_cliente', args=[self.cliente.id]))
        vendas = response.context['vendas']
        assert v1 in vendas
        assert v2 not in vendas

    def test_404_for_nonexistent_cliente(self):
        response = self.http.get(reverse('sales:vendas_por_cliente', args=[9999]))
        assert response.status_code == 404


# ─── Exibir vendas view ───────────────────────────────────────────────────────

class TestExibirVendas:

    @pytest.fixture(autouse=True)
    def setup(self, auth_client):
        self.http = auth_client
        self.maleta1 = make_maleta(order_number=741)
        self.maleta2 = make_maleta(order_number=852)
        self.c1 = make_cliente(first_name='Ana', last_name='Silva', phone_number='11999998888')
        self.c2 = make_cliente(first_name='Bruno', last_name='Costa', phone_number='21988887777')
        self.v1 = make_venda(self.maleta1, self.c1)
        self.v2 = make_venda(self.maleta2, self.c2)

    def test_get_lists_all_vendas(self):
        response = self.http.get(reverse('sales:vendas'))
        assert response.status_code == 200
        assert 'Ana' in response.content.decode()
        assert 'Bruno' in response.content.decode()

    def test_get_with_client_filter(self):
        response = self.http.get(reverse('sales:vendas'), {'client': 'Ana'})
        assert 'Ana' in response.content.decode()
        assert 'Bruno' not in response.content.decode()

    def test_get_with_briefcase_filter(self):
        response = self.http.get(reverse('sales:vendas'), {'briefcase': '852'})
        assert 'Bruno' in response.content.decode()
        assert 'Ana' not in response.content.decode()


# ─── Produtos views ───────────────────────────────────────────────────────────

class TestExibirProdutos:

    @pytest.fixture(autouse=True)
    def setup(self, auth_client):
        self.http = auth_client
        self.maleta = make_maleta()
        self.p1 = make_produto(self.maleta, product_code=9001, product_name='Anel')
        self.p2 = make_produto(self.maleta, product_code=9002, product_name='Brinco')

    def test_get_lists_products_for_maleta(self):
        response = self.http.get(reverse('sales:maleta_produtos', args=[self.maleta.id]))
        assert response.status_code == 200
        assert 'Anel' in response.content.decode()
        assert 'Brinco' in response.content.decode()

    def test_get_with_product_name_filter(self):
        response = self.http.get(
            reverse('sales:maleta_produtos', args=[self.maleta.id]),
            {'product_name': 'Anel'},
        )
        assert 'Anel' in response.content.decode()
        assert 'Brinco' not in response.content.decode()

    def test_get_with_product_code_filter(self):
        response = self.http.get(
            reverse('sales:maleta_produtos', args=[self.maleta.id]),
            {'product_code': '9002'},
        )
        assert 'Brinco' in response.content.decode()
        assert 'Anel' not in response.content.decode()

    def test_get_does_not_show_products_from_other_maleta(self):
        other_maleta = make_maleta(order_number=852)
        make_produto(other_maleta, product_code=9003, product_name='Colar')
        response = self.http.get(reverse('sales:maleta_produtos', args=[self.maleta.id]))
        assert 'Colar' not in response.content.decode()

    def test_404_for_nonexistent_maleta(self):
        response = self.http.get(reverse('sales:maleta_produtos', args=[9999]))
        assert response.status_code == 404


class TestCadastrarProduto:

    @pytest.fixture(autouse=True)
    def setup(self, auth_client):
        self.http = auth_client
        self.maleta = make_maleta()
        self.url = reverse('sales:maleta_produto_cadastro', args=[self.maleta.id])

    def test_get_renders_form(self):
        response = self.http.get(self.url)
        assert response.status_code == 200

    def test_post_valid_creates_and_redirects(self):
        response = self.http.post(self.url, {
            'product_name': 'Anel',
            'product_code': 9001,
            'product_value': '100.00',
            'product_quantity': 10,
        })
        assert response.status_code == 302
        assert response.url == reverse('sales:maleta_produtos', args=[self.maleta.id])
        assert Produtos.objects.filter(product_code=9001).exists()

    def test_post_product_linked_to_correct_maleta(self):
        self.http.post(self.url, {
            'product_name': 'Anel',
            'product_code': 9001,
            'product_value': '100.00',
            'product_quantity': 10,
        })
        produto = Produtos.objects.get(product_code=9001)
        assert produto.product_briefcase == self.maleta

    def test_post_duplicate_code_does_not_create(self):
        make_produto(self.maleta, product_code=9001)
        self.http.post(self.url, {
            'product_name': 'Anel',
            'product_code': 9001,
            'product_value': '100.00',
            'product_quantity': 10,
        })
        assert Produtos.objects.count() == 1

    def test_post_invalid_re_renders_with_errors(self):
        response = self.http.post(self.url, {
            'product_name': '',
            'product_code': 9001,
            'product_value': '100.00',
            'product_quantity': 10,
        })
        assert response.status_code == 200
        assert response.context['form'].errors

    def test_404_for_nonexistent_maleta(self):
        response = self.http.get(reverse('sales:maleta_produto_cadastro', args=[9999]))
        assert response.status_code == 404


class TestAtualizarProduto:

    @pytest.fixture(autouse=True)
    def setup(self, auth_client):
        self.http = auth_client
        self.maleta = make_maleta()
        self.produto = make_produto(self.maleta, product_code=9001)
        self.url = reverse('sales:maleta_produto_att', args=[self.produto.id])

    def test_get_renders_form(self):
        response = self.http.get(self.url)
        assert response.status_code == 200

    def test_post_valid_updates_and_redirects(self):
        response = self.http.post(self.url, {
            'product_name': 'Pulseira',
            'product_code': 9001,
            'product_value': '150.00',
            'product_quantity': 5,
        })
        assert response.status_code == 302
        assert response.url == reverse('sales:maleta_produtos', args=[self.maleta.id])
        self.produto.refresh_from_db()
        assert self.produto.product_name == 'Pulseira'
        assert self.produto.product_value == Decimal('150.00')

    def test_post_invalid_does_not_update(self):
        self.http.post(self.url, {
            'product_name': '',
            'product_code': 9001,
            'product_value': '150.00',
            'product_quantity': 5,
        })
        self.produto.refresh_from_db()
        assert self.produto.product_name == 'Anel'

    def test_post_invalid_re_renders_with_errors(self):
        response = self.http.post(self.url, {
            'product_name': '',
            'product_code': 9001,
            'product_value': '150.00',
            'product_quantity': 5,
        })
        assert response.status_code == 200
        assert response.context['form'].errors

    def test_404_for_nonexistent_product(self):
        response = self.http.get(reverse('sales:maleta_produto_att', args=[9999]))
        assert response.status_code == 404


class TestDeletarProduto:

    @pytest.fixture(autouse=True)
    def setup(self, auth_client):
        self.http = auth_client
        self.maleta = make_maleta()
        self.produto = make_produto(self.maleta)

    def test_post_deletes_and_redirects(self):
        response = self.http.post(reverse('sales:maleta_produto_del', args=[self.produto.id]))
        assert response.status_code == 302
        assert response.url == reverse('sales:maleta_produtos', args=[self.maleta.id])
        assert not Produtos.objects.filter(id=self.produto.id).exists()

    def test_get_does_not_delete(self):
        self.http.get(reverse('sales:maleta_produto_del', args=[self.produto.id]))
        assert Produtos.objects.filter(id=self.produto.id).exists()

    def test_get_redirects_to_produtos(self):
        response = self.http.get(reverse('sales:maleta_produto_del', args=[self.produto.id]))
        assert response.status_code == 302
        assert response.url == reverse('sales:maleta_produtos', args=[self.maleta.id])

    def test_404_for_nonexistent_product(self):
        response = self.http.post(reverse('sales:maleta_produto_del', args=[9999]))
        assert response.status_code == 404
