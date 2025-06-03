from django.urls import path
from . import views

urlpatterns = [
    path('', views.visualizarDashboard, name='dashboard'),
    path('logout/', views.logout, name='logout'),
]
