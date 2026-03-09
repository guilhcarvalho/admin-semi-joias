from django.contrib import admin

from .models import Vendas, ItensVenda, Maleta, Produtos

admin.site.register(Vendas)
admin.site.register(ItensVenda)
admin.site.register(Maleta)
admin.site.register(Produtos)