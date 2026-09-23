import pytest

pytestmark = pytest.mark.django_db


class TestUsuarioModel:
    def _criar(self, email, password='senha123', **kwargs):
        from accounts.models import Usuario
        user = Usuario(email=email, **kwargs)
        user.set_password(password)
        user.save()
        return user

    def test_username_sincronizado_com_email_no_save(self):
        user = self._criar('sync@test.com')
        assert user.username == 'sync@test.com'

    def test_username_atualizado_ao_alterar_email(self):
        user = self._criar('original@test.com')
        user.email = 'novo@test.com'
        user.save()
        assert user.username == 'novo@test.com'

    def test_str_retorna_nome_completo_quando_disponivel(self):
        user = self._criar('nome@test.com', first_name='João', last_name='Silva')
        assert str(user) == 'João Silva'

    def test_str_retorna_email_quando_sem_nome(self):
        user = self._criar('semnome@test.com')
        assert str(user) == 'semnome@test.com'

    def test_username_field_e_email(self):
        from accounts.models import Usuario
        assert Usuario.USERNAME_FIELD == 'email'

    def test_email_e_unico(self):
        from django.db import IntegrityError
        self._criar('unico@test.com')
        with pytest.raises(IntegrityError):
            self._criar('unico@test.com')
