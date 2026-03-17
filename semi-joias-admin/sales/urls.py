from django.urls import path
from . import views

app_name = 'sales'

urlpatterns = [
    path('vendas/clientes/<int:id>/', views.vendas_por_cliente, name='vendas_por_cliente'),
]