from django.db import models, transaction
from sales.services.models_filter import MaletaQuerySet, ProdutosQuerySet, VendasQuerySet
from clients.models import Cliente
from django.core.validators import MinValueValidator, MaxValueValidator
from .choices import PAYMENT_METHODS, PAYMENT_SITUATION, MONTH_SELECTION, SALE_STATUS, GARANTIA_STATUS, PARCELA_SITUACAO
from django.core.exceptions import ValidationError
from decimal import Decimal, ROUND_DOWN
from django.db.models import Sum


class Maleta(models.Model):
    month = models.CharField(max_length=20, choices=MONTH_SELECTION.choices, verbose_name="mês")
    start_sale_period = models.DateField(verbose_name="inicio do periodo de venda")
    end_sale_period = models.DateField(verbose_name="fim do periodo de venda")
    order_number = models.PositiveIntegerField(unique=True, verbose_name="numero da ordem")
    order_value = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal("0.00"))], verbose_name="valor da ordem")
    value_sold = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"), validators=[MinValueValidator(Decimal("0.00"))], verbose_name="valor vendido")
    objects = MaletaQuerySet.as_manager()

    def __str__(self):
        return f"Maleta {self.order_number}"

    class Meta:
        verbose_name = "maleta"
        verbose_name_plural = 'maletas'

    @property
    def sales_quantity(self):
        return self.vendas.count()

    @property
    def value_sold_calc(self):
        result = self.vendas.exclude(status='cancelada').aggregate(total=Sum('end_value'))
        return result['total'] or Decimal('0.00')

    def clean(self):
        if self.end_sale_period < self.start_sale_period:
            raise ValidationError("A data final não pode ser menor que a inicial.")
        if self.value_sold > self.order_value:
            raise ValidationError("O valor vendido não pode ser maior que o valor da ordem.")

    def save(self, *args, **kwargs):
        if self.pk:
            self.value_sold = self.value_sold_calc
        super().save(*args, **kwargs)


class Produtos(models.Model):
    product_briefcase = models.ForeignKey(Maleta, on_delete=models.CASCADE, verbose_name="maleta")
    product_name = models.CharField(max_length=30, verbose_name="nome do produto")
    product_code = models.PositiveIntegerField(verbose_name="código do produto")
    product_value = models.DecimalField(max_digits=10, validators=[MinValueValidator(Decimal("0.00"))], decimal_places=2, verbose_name="valor do produto")
    product_quantity = models.PositiveIntegerField(verbose_name="quantidade")
    quantity_sold = models.PositiveIntegerField(default=0, verbose_name="quantidade vendida")
    objects = ProdutosQuerySet.as_manager()

    def __str__(self):
        return f"{self.product_name} {self.product_code}"

    class Meta:
        verbose_name = "produto"
        verbose_name_plural = 'produtos'
        unique_together = [('product_briefcase', 'product_code')]

    @property
    def remaining_quantity(self):
        return self.product_quantity - self.quantity_sold

    def clean(self):
        if self.quantity_sold > self.product_quantity:
            raise ValidationError("A quantidade vendida não pode ser maior que a quantidade do produto.")


class Vendas(models.Model):
    client = models.ForeignKey(Cliente, on_delete=models.CASCADE, verbose_name="cliente")
    briefcase = models.ForeignKey(Maleta, on_delete=models.CASCADE, related_name='vendas', verbose_name="maleta")
    sale_value = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal("0.00"))], default=Decimal("0.00"), blank=True, verbose_name="valor integro da venda")
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS.choices, verbose_name="método de pagamento")
    installments = models.PositiveIntegerField(validators=[MinValueValidator(0)], blank=True, null=True, verbose_name="quantidade de parcelas")
    discount = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal("0.00"))], default=Decimal("0.00"), blank=True, verbose_name="desconto")
    end_value = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal("0.00"))], default=Decimal("0.00"), blank=True, verbose_name="valor final da venda")
    in_good_standing = models.CharField(max_length=20, choices=PAYMENT_SITUATION.choices, verbose_name="situação de pagamento")
    status = models.CharField(max_length=20, choices=SALE_STATUS.choices, default=SALE_STATUS.ATIVA, verbose_name="status")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="data da venda")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="atualização")
    objects = VendasQuerySet.as_manager()

    def __str__(self):
        return f"{self.briefcase} / Cliente: {self.client}"

    class Meta:
        verbose_name = "venda"
        verbose_name_plural = 'vendas'

    @property
    def end_value_calc(self):
        return self.sale_value_calc

    @property
    def sale_value_calc(self):
        return sum(
            item.quantity * item.end_value
            for item in self.itens.all()
        ) or Decimal("0.00")

    @property
    def gross_value_calc(self):
        return sum(
            item.quantity * item.unit_price
            for item in self.itens.all()
        ) or Decimal('0.00')

    @property
    def discount_calc(self):
        return sum(
            (item.percent_discount_calculator + item.integer_discount_calculator) * item.quantity
            for item in self.itens.all()
        ) or Decimal("0.00")

    def save(self, *args, **kwargs):
        if self.pk:
            self.sale_value = self.gross_value_calc
            self.discount = self.discount_calc
            self.end_value = self.end_value_calc
        super().save(*args, **kwargs)
        self.briefcase.save()

    def gerar_parcelas(self):
        if not self.installments or self.parcelas.exists():
            return
        n = self.installments
        valor_base = (self.end_value / n).quantize(Decimal('0.01'), rounding=ROUND_DOWN)
        resto = self.end_value - valor_base * n
        for i in range(1, n + 1):
            valor = valor_base + (resto if i == n else Decimal('0.00'))
            Parcela.objects.create(venda=self, numero=i, valor=valor)

    def cancelar(self):
        with transaction.atomic():
            product_ids = list(self.itens.values_list('product_id', flat=True))
            produtos = {p.id: p for p in Produtos.objects.select_for_update().filter(id__in=product_ids)}
            for item in self.itens.all():
                produto = produtos[item.product_id]
                produto.quantity_sold -= item.quantity
                produto.save()
            self.parcelas.all().update(situacao='cancelada')
            Vendas.objects.filter(pk=self.pk).update(status='cancelada')
            self.status = 'cancelada'
            self.briefcase.save()

    def delete(self, *args, **kwargs):
        briefcase = self.briefcase
        for item in self.itens.all():
            item.delete()
        super().delete(*args, **kwargs)
        briefcase.save()


class ItensVenda(models.Model):
    sale = models.ForeignKey(Vendas, on_delete=models.CASCADE, related_name="itens", verbose_name="venda")
    product = models.ForeignKey(Produtos, on_delete=models.CASCADE, verbose_name="produto")
    quantity = models.PositiveIntegerField(validators=[MinValueValidator(1)], verbose_name="quantidade")
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, validators=[MinValueValidator(Decimal("0.00"))], verbose_name="preço unitario")
    discount_percent = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal("0.00")), MaxValueValidator(Decimal("100.00"))], default=0, verbose_name='Desconto em Porcentagem.')
    integer_discount = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal("0.00"))], default=0, verbose_name='Desconto em Dinheiro.')

    def __str__(self):
        return f"{self.product}"

    class Meta:
        verbose_name = "itens venda"
        verbose_name_plural = 'itens vendas'
        unique_together = [('sale', 'product')]

    def clean(self):
        unit_price = self.product.product_value if self.product_id else Decimal("0.00")
        total_discount = unit_price * (self.discount_percent / 100) + self.integer_discount
        if total_discount > unit_price:
            raise ValidationError("O desconto total não pode exceder o preço unitário do produto.")

    @property
    def percent_discount_calculator(self):
        return self.unit_price * (self.discount_percent / 100)

    @property
    def integer_discount_calculator(self):
        return self.integer_discount

    @property
    def end_value(self):
        return self.unit_price - self.percent_discount_calculator - self.integer_discount_calculator

    @property
    def subtotal(self):
        return self.quantity * self.end_value

    def save(self, *args, **kwargs):
        with transaction.atomic():
            self.unit_price = self.product.product_value
            if self.pk:
                old = ItensVenda.objects.select_related('product').get(pk=self.pk)
                if old.product_id != self.product_id:
                    produto_novo = Produtos.objects.select_for_update().get(pk=self.product_id)
                    produto_old = Produtos.objects.select_for_update().get(pk=old.product_id)
                    if self.quantity > produto_novo.remaining_quantity:
                        raise ValidationError(f"Quantidade insuficiente. Disponível: {produto_novo.remaining_quantity}.")
                    if produto_old.quantity_sold < old.quantity:
                        raise ValidationError(f"Inconsistência: quantity_sold ({produto_old.quantity_sold}) é menor que a quantidade do item ({old.quantity}).")
                    produto_old.quantity_sold -= old.quantity
                    produto_old.save()
                    produto_novo.quantity_sold += self.quantity
                    produto_novo.save()
                else:
                    produto = Produtos.objects.select_for_update().get(pk=self.product_id)
                    available = produto.remaining_quantity + old.quantity
                    if self.quantity > available:
                        raise ValidationError(f"Quantidade insuficiente. Disponível: {available}.")
                    produto.quantity_sold += self.quantity - old.quantity
                    produto.save()
            else:
                produto = Produtos.objects.select_for_update().get(pk=self.product_id)
                if self.quantity > produto.remaining_quantity:
                    raise ValidationError(f"Quantidade insuficiente. Disponível: {produto.remaining_quantity}.")
                if ItensVenda.objects.filter(sale=self.sale, product=self.product).exists():
                    raise ValidationError("Este produto já foi adicionado a esta venda.")
                produto.quantity_sold += self.quantity
                produto.save()
            super().save(*args, **kwargs)
            self.sale.save()

    def delete(self, *args, **kwargs):
        with transaction.atomic():
            product = Produtos.objects.select_for_update().get(pk=self.product_id)
            sale = self.sale
            if product.quantity_sold < self.quantity:
                raise ValidationError(f"Inconsistência: quantity_sold ({product.quantity_sold}) é menor que a quantidade do item ({self.quantity}).")
            product.quantity_sold -= self.quantity
            super().delete(*args, **kwargs)
            product.save()
            sale.save()


class Parcela(models.Model):
    venda = models.ForeignKey(Vendas, on_delete=models.CASCADE, related_name='parcelas', verbose_name='venda')
    numero = models.PositiveIntegerField(verbose_name='número')
    valor = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='valor')
    situacao = models.CharField(
        max_length=10,
        choices=PARCELA_SITUACAO.choices,
        default=PARCELA_SITUACAO.PENDENTE,
        verbose_name='situação',
    )

    class Meta:
        verbose_name = 'parcela'
        verbose_name_plural = 'parcelas'
        unique_together = [('venda', 'numero')]
        ordering = ['numero']

    def __str__(self):
        return f'Parcela {self.numero}/{self.venda.installments} — Venda #{self.venda_id}'


class Devolucao(models.Model):
    venda = models.ForeignKey(Vendas, on_delete=models.CASCADE, related_name='devolucoes', verbose_name='venda')
    motivo = models.TextField(blank=True, verbose_name='motivo')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='data')

    class Meta:
        verbose_name = 'devolução'
        verbose_name_plural = 'devoluções'
        ordering = ['-created_at']

    def __str__(self):
        return f'Devolução — Venda #{self.venda_id}'

    @property
    def valor_total(self):
        return sum(i.valor_estornado for i in self.itens.all()) or Decimal('0.00')


class ItemDevolucao(models.Model):
    devolucao = models.ForeignKey(Devolucao, on_delete=models.CASCADE, related_name='itens', verbose_name='devolução')
    item_venda = models.ForeignKey(ItensVenda, on_delete=models.CASCADE, related_name='devolucoes', verbose_name='item da venda')
    quantidade = models.PositiveIntegerField(verbose_name='quantidade')
    valor_estornado = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='valor estornado')

    class Meta:
        verbose_name = 'item da devolução'
        verbose_name_plural = 'itens da devolução'

    def __str__(self):
        return f'{self.item_venda.product.product_name} × {self.quantidade}'


class Garantia(models.Model):
    item_venda = models.ForeignKey(ItensVenda, on_delete=models.CASCADE, related_name='garantias', verbose_name='item da venda')
    quantidade = models.PositiveIntegerField(verbose_name='quantidade')
    motivo = models.TextField(verbose_name='motivo')
    status = models.CharField(
        max_length=10,
        choices=GARANTIA_STATUS.choices,
        default=GARANTIA_STATUS.ENVIADO,
        verbose_name='status',
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='data de envio')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='atualização')

    class Meta:
        verbose_name = 'garantia'
        verbose_name_plural = 'garantias'
        ordering = ['-created_at']

    def clean(self):
        if self.item_venda_id:
            if self.quantidade <= 0:
                raise ValidationError('A quantidade deve ser maior que zero.')
            if self.quantidade > self.item_venda.quantity:
                raise ValidationError(
                    f'A quantidade não pode exceder {self.item_venda.quantity} (quantidade do item na venda).'
                )

    def __str__(self):
        return f'Garantia — {self.item_venda.product.product_name}'
