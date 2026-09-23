import pytest
from django.http import HttpResponse
from django.test import RequestFactory
from core.decorators import medico_ou_admin_required

pytestmark = pytest.mark.django_db

_factory = RequestFactory()


def _dummy_view(request):
    return HttpResponse('ok', status=200)


_protected = medico_ou_admin_required(_dummy_view)


class TestMedicoOuAdminRequired:
    def test_staff_acessa(self, usuario_pesquisador):
        usuario_pesquisador.is_staff = True
        usuario_pesquisador.save()

        request = _factory.get('/')
        request.user = usuario_pesquisador
        response = _protected(request)
        assert response.status_code == 200

    def test_grupo_medicos_acessa(self, db):
        from django.contrib.auth.models import Group
        from accounts.models import Usuario

        grupo, _ = Group.objects.get_or_create(name='Medicos')
        user = Usuario(email='medico@test.com')
        user.set_password('x')
        user.save()
        user.groups.add(grupo)

        request = _factory.get('/')
        request.user = user
        response = _protected(request)
        assert response.status_code == 200

    def test_usuario_comum_redireciona(self, usuario_comum):
        request = _factory.get('/')
        request.user = usuario_comum
        response = _protected(request)
        assert response.status_code == 302

    def test_usuario_comum_redireciona_para_home(self, usuario_comum):
        from django.urls import reverse
        request = _factory.get('/')
        request.user = usuario_comum
        response = _protected(request)
        # user_passes_test anexa ?next=<path> à URL de redirecionamento
        assert response['Location'].startswith(reverse('home'))

    def test_anonimo_redireciona(self):
        from django.contrib.auth.models import AnonymousUser
        request = _factory.get('/')
        request.user = AnonymousUser()
        response = _protected(request)
        assert response.status_code == 302

    def test_assistente_redireciona(self, usuario_assistente):
        request = _factory.get('/')
        request.user = usuario_assistente
        response = _protected(request)
        assert response.status_code == 302

    def test_pesquisador_sem_staff_redireciona(self, usuario_pesquisador):
        # Pesquisador está no grupo Pesquisador, não em Medicos → sem acesso
        request = _factory.get('/')
        request.user = usuario_pesquisador
        response = _protected(request)
        assert response.status_code == 302
