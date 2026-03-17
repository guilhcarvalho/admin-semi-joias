from django.urls import path
from . import views

app_name = 'clients'

urlpatterns = [
    path('clientes/', views.exibir_clientes, name='lista'),
    path('criar_cliente/', views.cadastrar_cliente, name='criar'),
    path('atualizar_cliente/<int:id>/', views.atualizar_cliente, name='atualizar'),
    path('deletar_cliente/<int:id>/', views.deletar_cliente, name='deletar'),
]