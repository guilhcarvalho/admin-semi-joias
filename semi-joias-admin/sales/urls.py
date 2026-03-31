from django.urls import path
from .views.maleta_view import exibir_maletas, cadastrar_maleta, atualizar_maleta, deletar_maleta, info_maleta
from .views.vendas_view import vendas_por_cliente

app_name = 'sales'

urlpatterns = [
    path('maletas/', exibir_maletas, name='maletas_lista'),
    path('vendas/clientes/<int:id>/', vendas_por_cliente, name='vendas_por_cliente'),
    path('info_maleta/<int:id>/', info_maleta, name='info_maleta'),
    path('cadastrar_maleta/', cadastrar_maleta, name='cadastro_maleta'),
    path('atualizar_maleta/<int:id>/', atualizar_maleta, name='atualizar_maleta'),
    path('deletar_maleta/<int:id>/', deletar_maleta, name='deletar_maleta'),
]