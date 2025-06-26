from django.urls import path
from . import views

urlpatterns = [
    path('', views.listarCestas, name='cestas'),
    path('nova/', views.novaCesta, name='nova_Cesta'),
    path('editar/<int:id_produto>/', views.editarCesta, name='editar_cesta'),
    path('confirmar-exclusao/<int:id_produto>/', views.confirmarExclusao, name='confirmar_exclusao_cesta'),
    path('excluir/<int:id_produto>/', views.excluirCesta, name='excluir_cesta'),
]
