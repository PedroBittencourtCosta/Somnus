from django.urls import path
from .views import responder_questionario, lista_questionarios


urlpatterns = [
    path('responder/<int:pk>/', responder_questionario, name='responder_questionario'),
    path('avaliacoes/', lista_questionarios, name='lista_questionarios'),
]