from django.urls import path
from .views import responder_questionario, lista_questionarios, dashboard_respostas, exportar_respostas_csv


urlpatterns = [
    path('responder/<int:pk>/', responder_questionario, name='responder_questionario'),
    path('avaliacoes/', lista_questionarios, name='lista_questionarios'),
    path('dashboard/', dashboard_respostas, name='dashboard_respostas'),
    path('export_csv/', exportar_respostas_csv, name='exportar_respostas_csv'),
]