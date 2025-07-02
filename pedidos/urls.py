from django.urls import path
from . import views

urlpatterns = [
    path('', views.listarPedidos, name='pedidos'),
    path('novo/', views.novoPedido, name='novo_pedido'),
    path('editar/<int:id_venda>/', views.editarPedido, name='editar_pedido'),
    path('confirmar-exclusao/<int:id_venda>/', views.confirmarExclusaoPedido, name='confirmar_exclusao_pedido'),
    path('excluir/<int:id_venda>/', views.excluirPedido, name='excluir_pedido'),
    path('visualizar/<int:id_venda>/', views.visualizarPedido, name='visualizar_pedido'),
    path('buscar-clientes/', views.buscarClientes, name='buscar_clientes'),
    path('novo-cliente-rapido/', views.novoClienteRapido, name='novo_cliente_rapido'),
]