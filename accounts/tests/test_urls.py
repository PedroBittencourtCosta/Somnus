from django.urls import reverse, resolve
from accounts import views


class TestAccountsUrls:
    def test_login(self):
        url = reverse('login')
        assert url == '/accounts/login/'
        assert resolve(url).view_name == 'login'

    def test_logout(self):
        url = reverse('logout')
        assert url == '/accounts/logout/'
        assert resolve(url).view_name == 'logout'

    def test_cadastro(self):
        url = reverse('cadastro')
        assert url == '/accounts/cadastro/'
        assert resolve(url).view_name == 'cadastro'

    def test_perfil(self):
        url = reverse('perfil')
        assert url == '/accounts/perfil/'
        assert resolve(url).view_name == 'perfil'

    def test_alterar_senha(self):
        url = reverse('alterar_senha')
        assert url == '/accounts/perfil/alterar-senha/'
        assert resolve(url).view_name == 'alterar_senha'

    def test_password_reset(self):
        url = reverse('password_reset')
        assert url == '/accounts/password_reset/'
        assert resolve(url).view_name == 'password_reset'

    def test_password_reset_done(self):
        url = reverse('password_reset_done')
        assert url == '/accounts/password_reset/done/'
        assert resolve(url).view_name == 'password_reset_done'

    def test_password_reset_complete(self):
        url = reverse('password_reset_complete')
        assert url == '/accounts/reset/done/'
        assert resolve(url).view_name == 'password_reset_complete'

    def test_cadastrar_assistente(self):
        url = reverse('cadastrar_assistente')
        assert url == '/accounts/equipe/cadastrar/'
        assert resolve(url).view_name == 'cadastrar_assistente'

    def test_gestao_assistentes(self):
        url = reverse('gestao_assistentes')
        assert url == '/accounts/equipe/gestao/'
        assert resolve(url).view_name == 'gestao_assistentes'

    def test_alternar_status_assistente(self):
        url = reverse('alternar_status_assistente', args=[99])
        assert url == '/accounts/equipe/99/alternar-status/'
        assert resolve(url).view_name == 'alternar_status_assistente'
