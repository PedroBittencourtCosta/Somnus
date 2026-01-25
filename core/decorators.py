# core/decorators.py
from django.contrib.auth.decorators import user_passes_test

def medico_ou_admin_required(view_func):
    """
    Permite acesso apenas a superusuários ou usuários no grupo 'Medicos'.
    """
    return user_passes_test(
        lambda u: u.is_authenticated and (u.is_staff or u.groups.filter(name='Medicos').exists()),
        login_url='home'
    )(view_func)