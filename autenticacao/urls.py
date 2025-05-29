from django.urls import path
from autenticacao import views

urlpatterns = [
    path ('', views.visualizarTelaLogin, name='login'),
    path('cadastro/', views.visualizarTelaCadastro, name='cadastro')
]