from io import StringIO

import pytest
from django.core.management import call_command

pytestmark = pytest.mark.django_db


def _backfill(*args):
    out, err = StringIO(), StringIO()
    call_command('backfill_resultados', *args, stdout=out, stderr=err)
    return out.getvalue(), err.getvalue()


# ── backfill_resultados ──────────────────────────────────────────────────────

class TestBackfillResultados:
    def test_sem_respostas_informa_que_nao_ha_pendencias(self):
        out, _ = _backfill()
        assert 'Nenhuma resposta pendente' in out

    def test_calcula_resultados_das_respostas_sem_cache(self, resposta_completa, escala_k10):
        from core.models import ResultadoEscala

        out, _ = _backfill()

        resultado = ResultadoEscala.objects.get(resposta_questionario=resposta_completa, escala_config=escala_k10)
        assert resultado.score_principal == 1
        assert resultado.classificacao == 'Baixo risco'
        assert '1 sucesso(s), 0 falha(s)' in out

    def test_nao_reprocessa_respostas_que_ja_tem_cache(self, resposta_completa, escala_k10):
        _backfill()
        out, _ = _backfill()
        assert 'Nenhuma resposta pendente' in out

    def test_recalcular_forca_reprocessamento(self, resposta_completa, escala_k10):
        from core.models import ResultadoEscala
        _backfill()
        ResultadoEscala.objects.update(score_principal=999)

        out, _ = _backfill('--recalcular')

        assert ResultadoEscala.objects.get().score_principal == 1
        assert '1 sucesso(s)' in out

    def test_filtra_por_questionario(self, resposta_completa, escala_k10, questionario_simples, usuario_pesquisador):
        from core.models import RespostaQuestionario, ResultadoEscala
        RespostaQuestionario.objects.create(
            pesquisadora=usuario_pesquisador, questionario=questionario_simples, paciente_nome='Outro',
        )

        out, _ = _backfill('--questionario', str(questionario_simples.id))

        assert f'questionário ID={questionario_simples.id}' in out
        assert not ResultadoEscala.objects.filter(resposta_questionario=resposta_completa).exists()

    def test_falha_em_uma_resposta_nao_interrompe_as_demais(self, resposta_completa, escala_k10, usuario_pesquisador, monkeypatch):
        from core.models import RespostaQuestionario
        RespostaQuestionario.objects.create(
            pesquisadora=usuario_pesquisador, questionario=resposta_completa.questionario, paciente_nome='Outro',
        )

        def _calcular(resposta):
            if resposta.pk == resposta_completa.pk:
                raise ValueError('dado corrompido')
            return []
        monkeypatch.setattr('core.management.commands.backfill_resultados.calcular_e_salvar_resultados', _calcular)

        out, err = _backfill()

        assert f'[{resposta_completa.codigo_paciente}] Erro: dado corrompido' in err
        assert '1 sucesso(s), 1 falha(s)' in out
