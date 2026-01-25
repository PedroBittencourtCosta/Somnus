from django.urls import path
from . import views

urlpatterns = [
    path('aceitar/<int:tcle_id>/', views.aceitar_tcle, name='aceitar_tcle'),
]