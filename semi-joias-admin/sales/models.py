from django.db import models
from clients.models import Cliente
from django.core.validators import MinValueValidator
from .choices import PAYMENT_METHODS, PAYMENT_SITUATION, MONTH_SELECTION
from django.core.exceptions import ValidationError
from decimal import Decimal


class Maleta(models.Model):
    month = models.CharField(max_length=20, choices=MONTH_SELECTION.choices, verbose_name="mês")
    start_sale_period = models.DateField(verbose_name="inicio do periodo de venda")
    end_sale_period = models.DateField(verbose_name="fim do periodo de venda")
    order_number = models.PositiveIntegerField(unique=True, verbose_name="numero da ordem")
    order_value = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal("0.00"))], verbose_name="valor da ordem")
    value_sold = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal("0.00"))], verbose_name="valor vendido")
    
    def __str__(self):
        return f"Maleta {self.order_number}"
    
    class Meta:
        verbose_name = "maleta"
        verbose_name_plural = 'maletas'
    
    def clean(self):
        if self.end_sale_period < self.start_sale_period:
            raise ValidationError("A data final não pode ser menor que a inicial.")
        
        if self.value_sold > self.order_value:
            raise ValidationError("O valor vendido não pode ser maior que o valor da ordem.")


class Produtos(models.Model):
    product_briefcase = models.ForeignKey(Maleta, on_delete=models.CASCADE, verbose_name="maleta")
    product_name = models.CharField(max_length=30, verbose_name="nome do produto")
    product_code = models.PositiveIntegerField(unique=True, verbose_name="código do produto")
    product_value = models.DecimalField(max_digits=10, validators=[MinValueValidator(Decimal("0.00"))], decimal_places=2, verbose_name="valor do produto")
    product_quantity = models.PositiveIntegerField(verbose_name="quantidade")
    quantity_sold = models.PositiveIntegerField(verbose_name="quantidade vendida")
    
    def __str__(self):
        return f"{self.product_name} {self.product_code}"

    class Meta:
        verbose_name = "produto"
        verbose_name_plural = 'produtos'
        
    @property
    def remaining_quantity(self):
        return self.product_quantity - self.quantity_sold
    
    def clean(self):
        if self.quantity_sold > self.product_quantity:
            raise ValidationError("A quantidade vendida não pode ser maior que a quantidade do produto.")


class Vendas(models.Model):
    client = models.ForeignKey(Cliente, on_delete=models.CASCADE, verbose_name="cliente")
    briefcase = models.ForeignKey(Maleta, on_delete=models.CASCADE, verbose_name="maleta")
    sale_value = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal("0.00"))], default=Decimal("0.00"), verbose_name="valor integro da venda")
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS.choices, verbose_name="método de pagamento")
    installments = models.PositiveIntegerField(validators=[MinValueValidator(0)], blank=True, null=True, verbose_name="quantidade de parcelas")
    discount = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal("0.00"))], default=Decimal("0.00"), verbose_name="desconto")
    end_value = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal("0.00"))], default=Decimal("0.00"), verbose_name="valor final da venda")
    in_good_standing = models.CharField(max_length=20,choices=PAYMENT_SITUATION.choices, verbose_name="situação de pagamento")
    #remaining_installments = models.PositiveIntegerField(validators=[MinValueValidator(0)], blank=True, null=True, verbose_name="Parcelas restantes")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="data da venda")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="atualização")
    
    def __str__(self):
        return f"{self.briefcase} / Cliente: {self.client}"
    
    class Meta:
        verbose_name = "venda"
        verbose_name_plural = 'vendas'
    
    #@property
    #def installiments_calc(self):
    #    remaining = 
    
    @property
    def end_value_calc(self):
        return self.sale_value - self.discount
    
    @property
    def sale_value_calc(self):
        return sum(
            item.quantity * item.end_value
            for item in self.itens.all()
        ) or Decimal("0.00")
        
    @property
    def discount_calc(self):
        return sum(
            item.percent_discount_calculator + item.integer_discount_calculator
            for item in self.itens.all()
        ) or Decimal("0.00")

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.sale_value = self.sale_value_calc
        self.discount = self.discount_calc
        self.end_value = self.end_value_calc
        Vendas.objects.filter(pk=self.pk).update(
            sale_value=self.sale_value,
            discount=self.discount,
            end_value=self.end_value,
        )
    
    def clean(self):
        if self.payment_method == 'credito' and not self.installments:
            raise ValidationError({
                'installments': 'Defina quantidade de parcelas para vendas no crédito.'
            })


class ItensVenda(models.Model):
    sale = models.ForeignKey(Vendas, on_delete=models.CASCADE, related_name="itens", verbose_name="venda")
    product = models.ForeignKey(Produtos, on_delete=models.CASCADE, verbose_name="produto")
    quantity = models.PositiveIntegerField(validators=[MinValueValidator(1)], verbose_name="quantidade")
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal("0.00"))], verbose_name="preço unitario")
    discount_percent = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal("0.00"))], default=0, verbose_name='Desconto em Porcentagem.')
    integer_discount = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal("0.00"))], default=0, verbose_name='Desconto em Dinheiro.')
    
    def __str__(self):
        return f"{self.product}"
    
    class Meta:
        verbose_name = "itens venda"
        verbose_name_plural = 'itens vendas'
    
    @property
    def percent_discount_calculator(self):
        percent_calc = self.unit_price * (self.discount_percent / 100)
        return percent_calc
    
    @property
    def integer_discount_calculator(self):
        return self.integer_discount
         
    @property
    def end_value(self):
        return self.unit_price - self.percent_discount_calculator - self.integer_discount_calculator
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.sale.save()
        