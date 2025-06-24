from django.urls import path
from . import views

urlpatterns = [
    path('', views.listarProdutos, name='produtos'),
    path('novo/', views.novoProduto, name='novo_produto'),
    path('editar/<int:id_produto>/', views.editarProduto, name='editar_produto'),
    path('confirmar-exclusao/<int:id_produto>/', views.confirmarExclusao, name='confirmar_exclusao_produto'),
    path('excluir/<int:id_produto>/', views.excluirProduto, name='excluir_produto'),
]
