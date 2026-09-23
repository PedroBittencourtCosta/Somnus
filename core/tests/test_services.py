import pytest
from django.db import IntegrityError

from core.services import (
    _extrair_score_e_classif,
    _montar_answers_map,
    calcular_e_salvar_resultados,
)


# ── _extrair_score_e_classif ─────────────────────────────────────────────────
# Testes puros: não precisam de banco de dados.

class TestExtrarirScoreEClassif:
    def test_psqi(self):
        score, classif = _extrair_score_e_classif(
            {'psqi_global': 7, 'psqi_status': 'Qualidade Ruim'}, 'PSQI'
        )
        assert score == 7.0
        assert classif == 'Qualidade Ruim'

    def test_dass21_sem_classificacao(self):
        resultado = {'dass_depressao': 10, 'dass_ansiedade': 8, 'dass_estresse': 12}
        score, classif = _extrair_score_e_classif(resultado, 'DASS21')
        assert score == 10.0   # usa 'dass_depressao' como score principal
        assert classif == ''   # DASS21 não tem classificação única no mapa

    def test_k10(self):
        score, classif = _extrair_score_e_classif(
            {'k10_total': 25, 'k10_classificacao': 'Provável transtorno'}, 'K10'
        )
        assert score == 25.0
        assert classif == 'Provável transtorno'

    def test_srq20(self):
        score, classif = _extrair_score_e_classif(
            {'srq_total': 8, 'srq_status': 'Suspeita de TMC'}, 'SRQ20'
        )
        assert score == 8.0
        assert classif == 'Suspeita de TMC'

    def test_ese(self):
        score, classif = _extrair_score_e_classif(
            {'ese_total': 12, 'ese_status': 'Sonolência Diurna Excessiva'}, 'ESE'
        )
        assert score == 12.0
        assert classif == 'Sonolência Diurna Excessiva'

    def test_audit(self):
        score, classif = _extrair_score_e_classif(
            {'audit_total': 5, 'audit_status': 'Baixo Risco'}, 'AUDIT'
        )
        assert score == 5.0
        assert classif == 'Baixo Risco'

    def test_emssp_sem_classificacao(self):
        score, classif = _extrair_score_e_classif(
            {'suporte_total': 60, 'suporte_familia': 20}, 'EMSSP'
        )
        assert score == 60.0
        assert classif == ''   # EMSSP não tem classificação no mapa

    def test_imc(self):
        score, classif = _extrair_score_e_classif(
            {'imc_valor': 22.5, 'imc_status': 'Peso normal'}, 'IMC'
        )
        assert score == 22.5
        assert classif == 'Peso normal'

    def test_dynamic_com_total(self):
        score, classif = _extrair_score_e_classif(
            {'total': 15.0, 'status': 'Alto'}, 'DYNAMIC'
        )
        assert score == 15.0
        assert classif == 'Alto'

    def test_dynamic_fallback_para_media(self):
        score, classif = _extrair_score_e_classif({'media': 3.5}, 'DYNAMIC')
        assert score == 3.5
        assert classif == ''

    def test_strategy_desconhecida_retorna_none(self):
        score, classif = _extrair_score_e_classif({'x': 1}, 'INEXISTENTE')
        assert score is None
        assert classif == ''

    def test_chave_score_ausente_retorna_none(self):
        # Mapa existe para K10, mas o resultado não tem 'k10_total'
        score, classif = _extrair_score_e_classif({}, 'K10')
        assert score is None


# ── _montar_answers_map ──────────────────────────────────────────────────────

@pytest.mark.django_db
class TestMontarAnswersMap:
    def _setup(self):
        from accounts.models import Usuario
        from core.models import Questionario, Secao, Pergunta, Alternativa, RespostaQuestionario

        q = Questionario.objects.create(titulo='Q Teste')
        secao = Secao.objects.create(questionario=q, titulo='S1', ordem=1)

        p_com_id = Pergunta.objects.create(secao=secao, conteudo='P1', ordem=1, tipo='MC', identificador='p1')
        alt = Alternativa.objects.create(pergunta=p_com_id, conteudo='Sim', valor=1)

        p_sem_id = Pergunta.objects.create(secao=secao, conteudo='P2', ordem=2, tipo='TX', identificador=None)

        user = Usuario(email='svc@test.com')
        user.set_password('senha123')
        user.save()

        resposta = RespostaQuestionario.objects.create(
            pesquisadora=user, questionario=q, paciente_nome='Teste'
        )
        return resposta, p_com_id, alt, p_sem_id

    def test_mapeamento_por_identificador_com_alternativa(self):
        from core.models import RespostaPergunta
        resposta, p_com_id, alt, _ = self._setup()

        RespostaPergunta.objects.create(
            resposta_questionario=resposta, pergunta=p_com_id, alternativa=alt
        )

        resultado = _montar_answers_map(resposta)
        assert resultado == {'p1': 1}

    def test_mapeamento_por_identificador_com_texto(self):
        from core.models import RespostaPergunta

        from accounts.models import Usuario
        from core.models import Questionario, Secao, Pergunta, RespostaQuestionario

        q = Questionario.objects.create(titulo='Q Texto')
        secao = Secao.objects.create(questionario=q, titulo='S', ordem=1)
        pergunta = Pergunta.objects.create(secao=secao, conteudo='Quantos anos?', ordem=1, tipo='TX', identificador='idade')

        user = Usuario(email='svc2@test.com')
        user.set_password('x')
        user.save()

        resposta = RespostaQuestionario.objects.create(
            pesquisadora=user, questionario=q, paciente_nome='P'
        )
        RespostaPergunta.objects.create(
            resposta_questionario=resposta, pergunta=pergunta, resposta_texto='25'
        )

        resultado = _montar_answers_map(resposta)
        assert resultado == {'idade': '25'}

    def test_pergunta_sem_identificador_e_ignorada(self):
        from core.models import RespostaPergunta
        resposta, p_com_id, alt, p_sem_id = self._setup()

        RespostaPergunta.objects.create(
            resposta_questionario=resposta, pergunta=p_sem_id, resposta_texto='texto livre'
        )

        resultado = _montar_answers_map(resposta)
        assert resultado == {}   # sem identificador → não entra no mapa

    def test_sem_respostas_retorna_dict_vazio(self):
        resposta, *_ = self._setup()
        assert _montar_answers_map(resposta) == {}


# ── calcular_e_salvar_resultados ─────────────────────────────────────────────

@pytest.mark.django_db
class TestCalcularESalvarResultados:
    def _setup_k10(self):
        """Cria questionário com escala K10, usuário e respostas k10a-k10j=2."""
        from accounts.models import Usuario
        from core.models import (
            Questionario, Secao, Pergunta, Alternativa,
            EscalaConfig, RespostaQuestionario, RespostaPergunta,
        )
        from core.Scaleprocessor import K10Calculator

        q = Questionario.objects.create(titulo='Q K10')
        secao = Secao.objects.create(questionario=q, titulo='K10', ordem=1)

        escala = EscalaConfig.objects.create(nome='K10', strategy_class='K10')
        escala.questionarios.add(q)

        user = Usuario(email='k10svc@test.com')
        user.set_password('x')
        user.save()

        resposta = RespostaQuestionario.objects.create(
            pesquisadora=user, questionario=q, paciente_nome='P'
        )

        for i, vid in enumerate(K10Calculator.K10_IDS):
            p = Pergunta.objects.create(secao=secao, conteudo=f'K10 {vid}', ordem=i + 1, tipo='MC', identificador=vid)
            alt = Alternativa.objects.create(pergunta=p, conteudo='2', valor=2)
            RespostaPergunta.objects.create(resposta_questionario=resposta, pergunta=p, alternativa=alt)

        return resposta, escala

    def test_cria_resultado_escala(self):
        from core.models import ResultadoEscala
        resposta, escala = self._setup_k10()

        resultados = calcular_e_salvar_resultados(resposta)

        assert len(resultados) == 1
        assert ResultadoEscala.objects.filter(
            resposta_questionario=resposta, escala_config=escala
        ).exists()

    def test_score_e_classificacao_corretos(self):
        resposta, _ = self._setup_k10()
        resultados = calcular_e_salvar_resultados(resposta)

        r = resultados[0]
        assert r.score_principal == 20.0          # 10 itens × 2
        assert r.classificacao == 'Provável transtorno'

    def test_idempotente_update_or_create(self):
        from core.models import ResultadoEscala
        resposta, _ = self._setup_k10()

        calcular_e_salvar_resultados(resposta)
        calcular_e_salvar_resultados(resposta)   # segunda chamada

        # Deve existir exatamente 1 registro (update, não duplicata)
        assert ResultadoEscala.objects.filter(resposta_questionario=resposta).count() == 1

    def test_escala_com_erro_nao_e_salva(self):
        from accounts.models import Usuario
        from core.models import Questionario, EscalaConfig, RespostaQuestionario, ResultadoEscala

        q = Questionario.objects.create(titulo='Q Erro')
        escala_ruim = EscalaConfig.objects.create(
            nome='Ruim', strategy_class='DYNAMIC', config_dinamica=None
        )
        escala_ruim.questionarios.add(q)

        user = Usuario(email='errosvc@test.com')
        user.set_password('x')
        user.save()

        resposta = RespostaQuestionario.objects.create(
            pesquisadora=user, questionario=q, paciente_nome='P'
        )

        resultados = calcular_e_salvar_resultados(resposta)

        assert resultados == []
        assert ResultadoEscala.objects.filter(resposta_questionario=resposta).count() == 0
