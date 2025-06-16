from django.urls import path
from . import views

urlpatterns = [
    path('', views.listarCategorias, name='categorias'),
    path('nova/', views.novaCategoria, name='nova_categoria'),
    path('editar/<int:id_categoria>/', views.editarCategoria, name='editar_categoria'),
    path('confirmar-exclusao/<int:id_categoria>/', views.confirmarExclusao, name='confirmar_exclusao'),
    path('excluir/<int:id_categoria>/', views.excluirCategoria, name='excluir_categoria'),
]