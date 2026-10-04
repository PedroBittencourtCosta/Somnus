import pytest

pytestmark = pytest.mark.django_db


def _criar_usuario(email, password='senha123', **kwargs):
    from accounts.models import Usuario
    user = Usuario(email=email, **kwargs)
    user.set_password(password)
    user.save()
    return user


# ── CadastroAssistenteForm ───────────────────────────────────────────────────

class TestCadastroAssistenteForm:
    _dados_base = {
        'first_name': 'João',
        'last_name': 'Silva',
        'email': 'assistente@form.com',
        'papel': 'Assistente de Pesquisa',
        'senha': 'senhaForte123',
        'confirmar_senha': 'senhaForte123',
    }

    def test_senhas_iguais_formulario_valido(self):
        from accounts.forms import CadastroAssistenteForm
        form = CadastroAssistenteForm(data=self._dados_base)
        assert form.is_valid(), form.errors

    def test_senhas_diferentes_formulario_invalido(self):
        from accounts.forms import CadastroAssistenteForm
        dados = {**self._dados_base, 'confirmar_senha': 'outrasenha456'}
        form = CadastroAssistenteForm(data=dados)
        assert not form.is_valid()
        assert 'As senhas não conferem.' in str(form.errors)

    def test_senha_curta_formulario_invalido(self):
        from accounts.forms import CadastroAssistenteForm
        dados = {**self._dados_base, 'senha': 'ab12', 'confirmar_senha': 'ab12'}
        form = CadastroAssistenteForm(data=dados)
        assert not form.is_valid()
        assert 'senha' in form.errors

    def test_senha_somente_numerica_formulario_invalido(self):
        from accounts.forms import CadastroAssistenteForm
        dados = {**self._dados_base, 'senha': '83749261', 'confirmar_senha': '83749261'}
        form = CadastroAssistenteForm(data=dados)
        assert not form.is_valid()
        assert 'senha' in form.errors

    def test_senha_comum_formulario_invalido(self):
        from accounts.forms import CadastroAssistenteForm
        dados = {**self._dados_base, 'senha': 'password', 'confirmar_senha': 'password'}
        form = CadastroAssistenteForm(data=dados)
        assert not form.is_valid()
        assert 'senha' in form.errors

    def test_email_obrigatorio(self):
        from accounts.forms import CadastroAssistenteForm
        dados = {**self._dados_base, 'email': ''}
        form = CadastroAssistenteForm(data=dados)
        assert not form.is_valid()
        assert 'email' in form.errors

    def test_first_name_opcional(self):
        # AbstractUser.first_name tem blank=True, então o form aceita vazio
        from accounts.forms import CadastroAssistenteForm
        dados = {**self._dados_base, 'first_name': ''}
        form = CadastroAssistenteForm(data=dados)
        assert form.is_valid()

    def test_email_duplicado_invalido(self):
        from accounts.forms import CadastroAssistenteForm
        _criar_usuario('assistente@form.com')
        form = CadastroAssistenteForm(data=self._dados_base)
        assert not form.is_valid()
        assert 'email' in form.errors


# ── PerfilForm ───────────────────────────────────────────────────────────────

class TestPerfilForm:
    def test_dados_validos_formulario_valido(self):
        from accounts.forms import PerfilForm
        user = _criar_usuario('perfil@test.com', first_name='Maria', last_name='Souza')
        dados = {'first_name': 'Maria Atualizada', 'last_name': 'Souza', 'email': 'perfil@test.com'}
        form = PerfilForm(data=dados, instance=user)
        assert form.is_valid(), form.errors

    def test_email_de_outro_usuario_invalido(self):
        from accounts.forms import PerfilForm
        _criar_usuario('ocupado@test.com')
        user = _criar_usuario('editavel@test.com')
        dados = {'first_name': 'X', 'last_name': 'Y', 'email': 'ocupado@test.com'}
        form = PerfilForm(data=dados, instance=user)
        assert not form.is_valid()
        assert 'email' in form.errors


# ── AlterarSenhaForm ─────────────────────────────────────────────────────────

class TestAlterarSenhaForm:
    def test_senha_atual_correta_formulario_valido(self):
        from accounts.forms import AlterarSenhaForm
        user = _criar_usuario('alterar@test.com', password='senhaAtual123')
        dados = {
            'old_password': 'senhaAtual123',
            'new_password1': 'novaSenhaForte456',
            'new_password2': 'novaSenhaForte456',
        }
        form = AlterarSenhaForm(user=user, data=dados)
        assert form.is_valid(), form.errors

    def test_senha_atual_incorreta_formulario_invalido(self):
        from accounts.forms import AlterarSenhaForm
        user = _criar_usuario('alterarfail@test.com', password='senhaAtual123')
        dados = {
            'old_password': 'senhaErrada999',
            'new_password1': 'novaSenhaForte456',
            'new_password2': 'novaSenhaForte456',
        }
        form = AlterarSenhaForm(user=user, data=dados)
        assert not form.is_valid()
        assert 'old_password' in form.errors

    def test_novas_senhas_diferentes_invalido(self):
        from accounts.forms import AlterarSenhaForm
        user = _criar_usuario('alterardiff@test.com', password='senhaAtual123')
        dados = {
            'old_password': 'senhaAtual123',
            'new_password1': 'novaSenhaA456',
            'new_password2': 'novaSenhaB789',
        }
        form = AlterarSenhaForm(user=user, data=dados)
        assert not form.is_valid()


# ── UsuarioCreationForm ──────────────────────────────────────────────────────

class TestUsuarioCreationForm:
    def test_email_valido_formulario_valido(self):
        from accounts.forms import UsuarioCreationForm
        dados = {
            'email': 'novo@creation.com',
            'first_name': 'Novo',
            'last_name': 'Usuário',
            'password1': 'senhaForte123',
            'password2': 'senhaForte123',
        }
        form = UsuarioCreationForm(data=dados)
        assert form.is_valid(), form.errors

    def test_email_duplicado_formulario_invalido(self):
        from accounts.forms import UsuarioCreationForm
        _criar_usuario('duplicado@creation.com')
        dados = {
            'email': 'duplicado@creation.com',
            'first_name': 'X',
            'last_name': 'Y',
            'password1': 'senhaForte123',
            'password2': 'senhaForte123',
        }
        form = UsuarioCreationForm(data=dados)
        assert not form.is_valid()
        assert 'email' in form.errors
