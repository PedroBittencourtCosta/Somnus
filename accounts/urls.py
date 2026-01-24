from django.urls import path
from .views import login_view, logout_view, cadastro_view, perfil_view


urlpatterns = [
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    path('cadastro/', cadastro_view, name='cadastro'),
    path('perfil/', perfil_view, name='perfil'),
]