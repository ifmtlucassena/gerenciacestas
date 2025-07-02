from django.urls import path
from . import views

urlpatterns = [
    path('', views.listarClientes, name='clientes'),
    path('novo/', views.novoCliente, name='novo_cliente'),
    path('editar/<int:id_cliente>/', views.editarCliente, name='editar_cliente'),
    path('visualizar/<int:id_cliente>/', views.visualizarCliente, name='visualizar_cliente'),
    path('confirmar-exclusao/<int:id_cliente>/', views.confirmarExclusaoCliente, name='confirmar_exclusao_cliente'),
    path('excluir/<int:id_cliente>/', views.excluirCliente, name='excluir_cliente'),
]