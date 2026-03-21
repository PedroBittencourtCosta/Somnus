from django.urls import path
from .views import exportar_respostas_excel, responder_questionario, lista_questionarios, dashboard_respostas


urlpatterns = [
    path('responder/<int:pk>/', responder_questionario, name='responder_questionario'),
    path('avaliacoes/', lista_questionarios, name='lista_questionarios'),
    path('dashboard/', dashboard_respostas, name='dashboard_respostas'),
    path('exportar-excel/<int:pk>/', exportar_respostas_excel, name='exportar_respostas_excel'),
]