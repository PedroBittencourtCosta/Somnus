# core/decorators.py
from functools import wraps

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied

GRUPO_PESQUISADOR = 'Pesquisador'
GRUPO_ASSISTENTE = 'Assistente de Pesquisa'


def eh_pesquisador(user):
    return user.is_staff or user.groups.filter(name=GRUPO_PESQUISADOR).exists()


def eh_equipe_pesquisa(user):
    return user.is_staff or user.groups.filter(name__in=[GRUPO_PESQUISADOR, GRUPO_ASSISTENTE]).exists()


def _restrito_a(teste):
    """Anônimo vai para o login; autenticado sem permissão recebe 403."""
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def _wrapped(request, *args, **kwargs):
            if not teste(request.user):
                raise PermissionDenied
            return view_func(request, *args, **kwargs)
        return _wrapped
    return decorator


# Gestão de questionários e escalas: somente Pesquisador ou staff.
pesquisador_required = _restrito_a(eh_pesquisador)

# Dashboard, relatórios e exportações: Pesquisador, Assistente de Pesquisa ou staff.
equipe_pesquisa_required = _restrito_a(eh_equipe_pesquisa)
