from django.urls import path
from . import views

urlpatterns = [
    path('', views.listarProdutos, name='cestas'),
    path('nova/', views.novoProduto, name='nova_Cesta'),
    path('editar/<int:id_produto>/', views.editarProduto, name='editar_cesta'),
    path('confirmar-exclusao/<int:id_produto>/', views.confirmarExclusao, name='confirmar_exclusao_cesta'),
    path('excluir/<int:id_produto>/', views.excluirProduto, name='excluir_cesta'),
]
