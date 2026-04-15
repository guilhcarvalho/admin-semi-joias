from django import forms
from .models import Maleta, Produtos

class MaletaForm(forms.ModelForm):
    class Meta:
        model = Maleta

        fields = [
            'month', 
            'start_sale_period', 
            'end_sale_period', 
            'order_number', 
            'order_value'
        ]
        exclude = ['value_sold']
        
class ProdutosForm(forms.ModelForm):
    class Meta:
        model = Produtos
        
        fields = [
            'product_name',
            'product_code',
            'product_value',
            'product_quantity',
        ]
