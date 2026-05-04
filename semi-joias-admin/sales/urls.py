from django.urls import path
from .views.maleta_view import exibir_maletas, cadastrar_maleta, atualizar_maleta, deletar_maleta, info_maleta
from .views.vendas_view import (
    vendas_por_cliente, exibir_vendas, info_vendas,
    nova_venda_itens, nova_venda_verificar, nova_venda_dados,
    atualizar_venda, cancelar_venda, toggle_parcela,
    registrar_devolucao, registrar_garantia, atualizar_garantia,
)
from .views.produtos_view import exibir_produtos, cadastrar_produto, atualizar_produto, deletar_produto

app_name = 'sales'

urlpatterns = [
    path('maletas/', exibir_maletas, name='maletas_lista'),
    path('vendas/clientes/<int:id>/', vendas_por_cliente, name='vendas_por_cliente'),
    path('info_maleta/<int:id>/', info_maleta, name='info_maleta'),
    path('cadastrar_maleta/', cadastrar_maleta, name='cadastro_maleta'),
    path('atualizar_maleta/<int:id>/', atualizar_maleta, name='atualizar_maleta'),
    path('deletar_maleta/<int:id>/', deletar_maleta, name='deletar_maleta'),
    path('info_maleta/produtos/<int:id>/', exibir_produtos, name='maleta_produtos'),
    path('info_maleta/produtos/atualizar/<int:id>/', atualizar_produto, name='maleta_produto_att'),
    path('info_maleta/produtos/deletar/<int:id>/', deletar_produto, name='maleta_produto_del'),
    path('info_maleta/produtos/cadastrar/<int:id>/', cadastrar_produto, name='maleta_produto_cadastro'),
    path('vendas/', exibir_vendas, name='vendas'),
    path('vendas/info/<int:id>/', info_vendas, name='info_vendas'),
    path('vendas/registrar_venda/<int:id>/', nova_venda_itens, name='registrar_venda'),
    path('vendas/nova/<int:id>/verificar/', nova_venda_verificar, name='nova_venda_verificar'),
    path('vendas/nova/<int:id>/dados/', nova_venda_dados, name='nova_venda_dados'),
    path('vendas/atualizar_venda/<int:id>/', atualizar_venda, name='atualizar_venda'),
    path('vendas/cancelar_venda/<int:id>/', cancelar_venda, name='cancelar_venda'),
    path('vendas/parcela/toggle/<int:id>/', toggle_parcela, name='toggle_parcela'),
    path('vendas/<int:id>/devolucao/', registrar_devolucao, name='registrar_devolucao'),
    path('vendas/<int:id>/garantia/', registrar_garantia, name='registrar_garantia'),
    path('vendas/garantia/<int:id>/atualizar/', atualizar_garantia, name='atualizar_garantia'),
]
