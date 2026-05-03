from django.urls import path
from .views import exportar_respostas_excel, responder_questionario, lista_questionarios, dashboard_respostas, editar_questionario_view, salvar_questionario_api, configurar_escala_view


urlpatterns = [
    path('responder/<int:pk>/', responder_questionario, name='responder_questionario'),
    path('avaliacoes/', lista_questionarios, name='lista_questionarios'),
    path('avaliacoes/nova/', editar_questionario_view, name='nova_avaliacao'),
    path('avaliacoes/<int:pk>/editar/', editar_questionario_view, name='editar_avaliacao'),
    path('avaliacoes/<int:pk>/escala/', configurar_escala_view, name='configurar_escala'),
    path('api/avaliacoes/salvar/', salvar_questionario_api, name='salvar_avaliacao_api'),
    path('dashboard/', dashboard_respostas, name='dashboard_respostas'),
    path('exportar-excel/<int:pk>/', exportar_respostas_excel, name='exportar_respostas_excel'),
]