from django.urls import path
from .views import login_view, logout_view, cadastro_view, perfil_view, alterar_senha_view, cadastrar_assistente, gestao_assistentes, alternar_status_assistente
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    path('cadastro/', cadastro_view, name='cadastro'),
    path('perfil/', perfil_view, name='perfil'),
    path('perfil/alterar-senha/', alterar_senha_view, name='alterar_senha'),
    path('password_reset/', auth_views.PasswordResetView.as_view(
        template_name='password/password_reset_form.html',
        email_template_name='password/password_reset_email.html',
        subject_template_name='password/password_reset_subject.txt'
    ), name='password_reset'),
    
    path('password_reset/done/', auth_views.PasswordResetDoneView.as_view(
        template_name='password/password_reset_done.html'
    ), name='password_reset_done'),
    
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(
        template_name='password/password_reset_confirm.html'
    ), name='password_reset_confirm'),
    
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(
        template_name='password/password_reset_complete.html'
    ), name='password_reset_complete'),
    path('equipe/cadastrar/', cadastrar_assistente, name='cadastrar_assistente'),
    path('equipe/gestao/', gestao_assistentes, name='gestao_assistentes'),
    path('equipe/<int:usuario_id>/alternar-status/', alternar_status_assistente, name='alternar_status_assistente'),
]