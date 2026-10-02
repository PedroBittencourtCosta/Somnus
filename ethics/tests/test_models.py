import pytest

pytestmark = pytest.mark.django_db


class TestTCLEModel:
    def test_str_retorna_versao(self, tcle_ativo):
        assert str(tcle_ativo) == 'Versão 1.0'

    def test_criacao_com_versao_customizada(self):
        from ethics.models import TCLE
        tcle = TCLE.objects.create(conteudo='Conteúdo v2', versao=2.5)
        assert str(tcle) == 'Versão 2.5'

    def test_versao_default_e_1(self):
        from ethics.models import TCLE
        tcle = TCLE.objects.create(conteudo='Conteúdo padrão')
        assert tcle.versao == 1.0


class TestAceiteTCLEModel:
    def test_str(self, resposta_completa, tcle_ativo):
        from ethics.models import AceiteTCLE
        aceite = AceiteTCLE.objects.create(
            resposta_questionario=resposta_completa,
            tcle=tcle_ativo,
        )
        s = str(aceite)
        assert resposta_completa.codigo_paciente in s
        assert '1.0' in s

    def test_relacao_onetoone_com_resposta(self, resposta_completa, tcle_ativo):
        from django.db import IntegrityError
        from ethics.models import AceiteTCLE

        AceiteTCLE.objects.create(resposta_questionario=resposta_completa, tcle=tcle_ativo)

        with pytest.raises(IntegrityError):
            AceiteTCLE.objects.create(resposta_questionario=resposta_completa, tcle=tcle_ativo)

    def test_aceite_acessivel_pela_resposta(self, resposta_completa, tcle_ativo):
        from ethics.models import AceiteTCLE
        aceite = AceiteTCLE.objects.create(
            resposta_questionario=resposta_completa,
            tcle=tcle_ativo,
        )
        assert resposta_completa.aceite == aceite
