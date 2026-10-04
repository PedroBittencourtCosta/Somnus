import pytest
from django.urls import reverse

pytestmark = pytest.mark.django_db


def _criar_usuario(email, password='senha123', **kwargs):
    from accounts.models import Usuario
    user = Usuario(email=email, **kwargs)
    user.set_password(password)
    user.save()
    return user


# ── login_view ───────────────────────────────────────────────────────────────

class TestLoginView:
    def test_get_redireciona_para_home(self, client):
        response = client.get(reverse('login'))
        assert response.status_code == 302
        assert response['Location'] == reverse('home')

    def test_get_usuario_ja_logado_redireciona_para_home(self, client_pesquisador):
        response = client_pesquisador.get(reverse('login'))
        assert response.status_code == 302
        assert response['Location'] == reverse('home')

    def test_post_credenciais_corretas_autentica(self, client, usuario_pesquisador):
        response = client.post(reverse('login'), {
            'email': 'pesquisador@test.com',
            'password': 'senha123',
        })
        assert response.status_code == 302
        assert '_auth_user_id' in client.session

    def test_post_credenciais_incorretas_nao_autentica(self, client, usuario_pesquisador):
        response = client.post(reverse('login'), {
            'email': 'pesquisador@test.com',
            'password': 'senhaErrada',
        })
        assert response.status_code == 302
        assert '_auth_user_id' not in client.session

    def test_post_conta_desativada_nao_autentica(self, client):
        user = _criar_usuario('desativado@test.com', password='senha123')
        user.is_active = False
        user.save()

        response = client.post(reverse('login'), {
            'email': 'desativado@test.com',
            'password': 'senha123',
        })
        assert '_auth_user_id' not in client.session


# ── logout_view ──────────────────────────────────────────────────────────────

class TestLogoutView:
    def test_redireciona_para_home(self, client_pesquisador):
        response = client_pesquisador.get(reverse('logout'))
        assert response.status_code == 302
        assert response['Location'] == reverse('home')

    def test_sessao_encerrada_apos_logout(self, client_pesquisador):
        client_pesquisador.get(reverse('logout'))
        assert '_auth_user_id' not in client_pesquisador.session


# ── perfil_view ──────────────────────────────────────────────────────────────

class TestPerfilView:
    def test_anonimo_redireciona_para_login(self, client):
        response = client.get(reverse('perfil'))
        assert response.status_code == 302
        assert '/login/' in response['Location']

    def test_get_retorna_200(self, client_pesquisador):
        response = client_pesquisador.get(reverse('perfil'))
        assert response.status_code == 200

    def test_post_valido_atualiza_dados(self, client_pesquisador, usuario_pesquisador):
        response = client_pesquisador.post(reverse('perfil'), {
            'first_name': 'Ana Editada',
            'last_name': 'Pesquisadora',
            'email': 'pesquisador@test.com',
        })
        assert response.status_code == 302
        usuario_pesquisador.refresh_from_db()
        assert usuario_pesquisador.first_name == 'Ana Editada'


# ── alterar_senha_view ───────────────────────────────────────────────────────

class TestAlterarSenhaView:
    def test_anonimo_redireciona(self, client):
        response = client.get(reverse('alterar_senha'))
        assert response.status_code == 302

    def test_get_retorna_200(self, client_pesquisador):
        response = client_pesquisador.get(reverse('alterar_senha'))
        assert response.status_code == 200

    def test_post_senha_correta_atualiza(self, client_pesquisador, usuario_pesquisador):
        response = client_pesquisador.post(reverse('alterar_senha'), {
            'old_password': 'senha123',
            'new_password1': 'novaSenhaForte456',
            'new_password2': 'novaSenhaForte456',
        })
        assert response.status_code == 302
        usuario_pesquisador.refresh_from_db()
        assert usuario_pesquisador.check_password('novaSenhaForte456')

    def test_post_senha_errada_nao_atualiza(self, client_pesquisador, usuario_pesquisador):
        client_pesquisador.post(reverse('alterar_senha'), {
            'old_password': 'senhaErrada',
            'new_password1': 'novaSenha456',
            'new_password2': 'novaSenha456',
        })
        usuario_pesquisador.refresh_from_db()
        assert usuario_pesquisador.check_password('senha123')  # não mudou


# ── cadastrar_assistente ─────────────────────────────────────────────────────

class TestCadastrarAssistente:
    def test_anonimo_redireciona(self, client):
        response = client.get(reverse('cadastrar_assistente'))
        assert response.status_code == 302

    def test_assistente_sem_permissao_redireciona(self, client_assistente):
        response = client_assistente.get(reverse('cadastrar_assistente'))
        assert response.status_code == 302

    def test_pesquisador_get_retorna_200(self, client_pesquisador):
        response = client_pesquisador.get(reverse('cadastrar_assistente'))
        assert response.status_code == 200

    def test_pesquisador_post_cria_usuario_no_grupo(self, client_pesquisador):
        from accounts.models import Usuario
        from django.contrib.auth.models import Group

        response = client_pesquisador.post(reverse('cadastrar_assistente'), {
            'first_name': 'Novo',
            'last_name': 'Assistente',
            'email': 'novoass@test.com',
            'papel': 'Assistente de Pesquisa',
            'senha': 'senhaForte123',
            'confirmar_senha': 'senhaForte123',
        })
        assert response.status_code == 302
        novo = Usuario.objects.get(email='novoass@test.com')
        assert novo.groups.filter(name='Assistente de Pesquisa').exists()


# ── gestao_assistentes ───────────────────────────────────────────────────────

class TestGestaoAssistentes:
    def test_anonimo_redireciona(self, client):
        response = client.get(reverse('gestao_assistentes'))
        assert response.status_code == 302

    def test_assistente_sem_permissao_redireciona(self, client_assistente):
        response = client_assistente.get(reverse('gestao_assistentes'))
        assert response.status_code == 302

    def test_pesquisador_get_retorna_200(self, client_pesquisador):
        response = client_pesquisador.get(reverse('gestao_assistentes'))
        assert response.status_code == 200

    def test_lista_exclui_o_proprio_usuario(self, client_pesquisador, usuario_pesquisador):
        response = client_pesquisador.get(reverse('gestao_assistentes'))
        ids = [u.id for u in response.context['usuarios']]
        assert usuario_pesquisador.id not in ids

    def test_lista_exclui_superusuarios(self, client_pesquisador):
        from accounts.models import Usuario
        superuser = Usuario(email='super@test.com', is_superuser=True)
        superuser.set_password('x')
        superuser.save()

        response = client_pesquisador.get(reverse('gestao_assistentes'))
        ids = [u.id for u in response.context['usuarios']]
        assert superuser.id not in ids


# ── alternar_status_assistente ───────────────────────────────────────────────

class TestAlternarStatusAssistente:
    def test_anonimo_redireciona(self, client, usuario_assistente):
        url = reverse('alternar_status_assistente', args=[usuario_assistente.id])
        response = client.post(url, HTTP_ACCEPT='application/json')
        assert response.status_code == 302

    def test_pesquisador_alterna_status_via_json(self, client_pesquisador, usuario_assistente):
        url = reverse('alternar_status_assistente', args=[usuario_assistente.id])
        response = client_pesquisador.post(url, HTTP_ACCEPT='application/json')
        assert response.status_code == 200
        data = response.json()
        assert data['status'] == 'success'

        usuario_assistente.refresh_from_db()
        assert usuario_assistente.is_active is False   # era True → virou False

    def test_nao_pode_alterar_o_proprio_status(self, client_pesquisador, usuario_pesquisador):
        url = reverse('alternar_status_assistente', args=[usuario_pesquisador.id])
        response = client_pesquisador.post(url, HTTP_ACCEPT='application/json')

        # Deve retornar erro (403) ou redirecionar sem alterar is_active
        usuario_pesquisador.refresh_from_db()
        assert usuario_pesquisador.is_active is True   # não foi alterado
