from django.urls import path
from . import views

urlpatterns = [
    path('', views.listarCestas, name='cestas'),
    path('nova/', views.novaCesta, name='nova_cesta'),
    path('editar/<int:id_cesta>/', views.editarCesta, name='editar_cesta'),
    path('confirmar-exclusao/<int:id_cesta>/', views.confirmarExclusao, name='confirmar_exclusao_cesta'),
    path('excluir/<int:id_cesta>/', views.excluirCesta, name='excluir_cesta'),
    path('buscar-produtos/', views.buscarProdutos, name='buscar_produtos'),
    path('visualizar/<int:id_cesta>/', views.visualizarCesta, name='visualizar_cesta'),
]