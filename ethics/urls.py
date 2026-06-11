from django.urls import path
from . import views

urlpatterns = [
    path('aceitar/<int:tcle_id>/', views.aceitar_tcle, name='aceitar_tcle'),
    path('gerenciar/', views.lista_tcle, name='lista_tcle'),
    path('gerenciar/nova-versao/', views.nova_versao_tcle, name='nova_versao_tcle'),
]