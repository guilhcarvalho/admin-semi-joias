from django.db import models
from clients.models import Clientes
from django.core.validators import MinValueValidator


class Maleta(models.Model):
    month = models.CharField(max_length=20, verbose_name="mês")
    start_sale_period = models.DateField(verbose_name="inicio do periodo de venda")
    end_sale_period = models.DateField(verbose_name="fim do periodo de venda")
    order_number = models.IntegerField(verbose_name="numero da ordem")
    order_value = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="valor da ordem")
    value_sold = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="valor vendido")
    
    def __str__(self):
        return f"Maleta {self.order_number}"


class Produtos(models.Model):
    product_briefcase = models.ForeignKey(Maleta, on_delete=models.CASCADE, verbose_name="maleta")
    product_name = models.CharField(max_length=30, verbose_name="nome do produto")
    product_code = models.IntegerField(verbose_name="código do produto")
    product_value = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="valor do produto")
    product_quantity = models.IntegerField(verbose_name="quantidade")
    quantity_sold = models.IntegerField(verbose_name="quantidade vendida")
    
    def __str__(self):
        return f"{self.product_name} {self.product_code}"


class Vendas(models.Model):
    client = models.ForeignKey(Clientes, on_delete=models.CASCADE, verbose_name="cliente")
    briefcase = models.ForeignKey(Maleta, on_delete=models.CASCADE, verbose_name="maleta")
    sale_value = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="valor da venda")
    payment_method = models.CharField(max_length=20, verbose_name="método de pagamento")   #Alterar para choices
    installments = models.IntegerField(validators=[MinValueValidator(1)], verbose_name="quantidade de parcelas")
    in_good_standing = models.BooleanField(default=True, verbose_name="situação de pagamento") #Alterar para choices
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="data da venda")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="atualização")
    
    
class ItensVenda(models.Model):
    sale = models.ForeignKey(Vendas, on_delete=models.CASCADE, related_name="itens", verbose_name="venda")
    product = models.ForeignKey(Produtos, on_delete=models.CASCADE, verbose_name="produto")
    quantity = models.IntegerField(validators=[MinValueValidator(1)], verbose_name="quantidade")
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="preço unitario")
