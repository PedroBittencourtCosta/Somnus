import pytest
from django.db import IntegrityError

pytestmark = pytest.mark.django_db


# ── Questionario ─────────────────────────────────────────────────────────────

class TestQuestionarioModel:
    def test_str(self):
        from core.models import Questionario
        q = Questionario(titulo='Questionário de Sono')
        assert str(q) == 'Questionário de Sono'

    def test_titulo_curto_dentro_do_limite_7_palavras(self):
        from core.models import Questionario
        q = Questionario(titulo='Um dois três quatro cinco seis sete')
        assert q.titulo_curto == 'Um dois três quatro cinco seis sete'

    def test_titulo_curto_trunca_acima_de_7_palavras(self):
        from core.models import Questionario
        q = Questionario(titulo='Um dois três quatro cinco seis sete oito nove')
        assert q.titulo_curto == 'Um dois três quatro cinco seis sete...'

    def test_ativo_default_true(self):
        from core.models import Questionario
        q = Questionario.objects.create(titulo='Q Ativo')
        assert q.ativo is True


# ── Secao ────────────────────────────────────────────────────────────────────

class TestSecaoModel:
    def test_str(self, questionario_simples):
        from core.models import Secao
        s = Secao.objects.create(questionario=questionario_simples, titulo='Dados Demográficos', ordem=1)
        assert str(s) == 'Dados Demográficos - Questionário de Teste'

    def test_ordering_por_ordem(self, questionario_simples):
        from core.models import Secao
        Secao.objects.create(questionario=questionario_simples, titulo='B', ordem=2)
        Secao.objects.create(questionario=questionario_simples, titulo='A', ordem=1)
        secoes = list(Secao.objects.filter(questionario=questionario_simples))
        assert secoes[0].titulo == 'A'
        assert secoes[1].titulo == 'B'


# ── Pergunta ─────────────────────────────────────────────────────────────────

class TestPerguntaModel:
    def test_str_sem_identificador(self):
        from core.models import Pergunta
        p = Pergunta(conteudo='Qual é a sua idade?', identificador=None)
        assert str(p) == 'Qual é a sua idade?'

    def test_str_com_identificador_sempre_adiciona_reticencias(self):
        from core.models import Pergunta
        p = Pergunta(identificador='k10a', conteudo='Pergunta curta')
        assert str(p) == '[k10a] Pergunta curta...'

    def test_str_com_identificador_trunca_conteudo_em_50_chars(self):
        from core.models import Pergunta
        conteudo_longo = 'A' * 60
        p = Pergunta(identificador='p1', conteudo=conteudo_longo)
        esperado = f'[p1] {"A" * 50}...'
        assert str(p) == esperado

    def test_ordering_por_ordem(self, questionario_simples):
        from core.models import Secao, Pergunta
        secao = Secao.objects.create(questionario=questionario_simples, titulo='S', ordem=1)
        Pergunta.objects.create(secao=secao, conteudo='Segunda', ordem=2, tipo='TX')
        Pergunta.objects.create(secao=secao, conteudo='Primeira', ordem=1, tipo='TX')
        perguntas = list(Pergunta.objects.filter(secao=secao))
        assert perguntas[0].conteudo == 'Primeira'
        assert perguntas[1].conteudo == 'Segunda'


# ── Alternativa ──────────────────────────────────────────────────────────────

class TestAlternativaModel:
    def test_str(self, questionario_simples):
        from core.models import Secao, Pergunta, Alternativa
        secao = Secao.objects.create(questionario=questionario_simples, titulo='S', ordem=1)
        pergunta = Pergunta.objects.create(secao=secao, conteudo='P', ordem=1, tipo='MC')
        alt = Alternativa.objects.create(pergunta=pergunta, conteudo='Nunca', valor=0)
        assert str(alt) == 'Nunca'


# ── RespostaQuestionario ─────────────────────────────────────────────────────

class TestRespostaQuestionarioModel:
    def test_codigo_paciente_gerado_automaticamente(self, usuario_pesquisador, questionario_simples):
        from core.models import RespostaQuestionario
        r = RespostaQuestionario.objects.create(
            pesquisadora=usuario_pesquisador,
            questionario=questionario_simples,
            paciente_nome='Maria Silva',
        )
        assert r.codigo_paciente is not None

    def test_codigo_paciente_tem_10_caracteres(self, usuario_pesquisador, questionario_simples):
        from core.models import RespostaQuestionario
        r = RespostaQuestionario.objects.create(
            pesquisadora=usuario_pesquisador,
            questionario=questionario_simples,
            paciente_nome='P',
        )
        assert len(r.codigo_paciente) == 10

    def test_codigo_paciente_e_uppercase(self, usuario_pesquisador, questionario_simples):
        from core.models import RespostaQuestionario
        r = RespostaQuestionario.objects.create(
            pesquisadora=usuario_pesquisador,
            questionario=questionario_simples,
            paciente_nome='P',
        )
        assert r.codigo_paciente == r.codigo_paciente.upper()

    def test_codigo_paciente_e_unico(self, usuario_pesquisador, questionario_simples):
        from core.models import RespostaQuestionario
        r1 = RespostaQuestionario.objects.create(
            pesquisadora=usuario_pesquisador, questionario=questionario_simples, paciente_nome='A'
        )
        r2 = RespostaQuestionario.objects.create(
            pesquisadora=usuario_pesquisador, questionario=questionario_simples, paciente_nome='B'
        )
        assert r1.codigo_paciente != r2.codigo_paciente

    def test_str(self, usuario_pesquisador, questionario_simples):
        from core.models import RespostaQuestionario
        r = RespostaQuestionario.objects.create(
            pesquisadora=usuario_pesquisador,
            questionario=questionario_simples,
            paciente_nome='Ana Costa',
        )
        resultado = str(r)
        assert r.codigo_paciente in resultado
        assert 'pesquisador@test.com' in resultado


# ── EscalaConfig ─────────────────────────────────────────────────────────────

class TestEscalaConfigModel:
    def test_str(self):
        from core.models import EscalaConfig
        e = EscalaConfig(nome='K10', strategy_class='K10')
        assert 'K10' in str(e)
        assert 'Kessler' in str(e)   # texto do display choice

    def test_strategy_class_choices_contem_todas_escalas(self):
        from core.models import EscalaConfig
        choices = dict(EscalaConfig.ESTRATEGIA_CHOICES)
        for estrategia in ['DYNAMIC', 'PSQI', 'IMC', 'DASS21', 'K10', 'SRQ20', 'ESE', 'AUDIT', 'EMSSP']:
            assert estrategia in choices

    def test_ativo_default_true(self):
        from core.models import EscalaConfig
        e = EscalaConfig.objects.create(nome='Teste', strategy_class='K10')
        assert e.ativo is True


# ── ResultadoEscala ──────────────────────────────────────────────────────────

class TestResultadoEscalaModel:
    def test_str(self, resposta_completa, escala_k10):
        from core.models import ResultadoEscala
        r = ResultadoEscala.objects.create(
            resposta_questionario=resposta_completa,
            escala_config=escala_k10,
            resultado_json={'k10_total': 20},
            score_principal=20.0,
            classificacao='Provável transtorno',
        )
        s = str(r)
        assert resposta_completa.codigo_paciente in s
        assert 'K10' in s
        assert '20.0' in s

    def test_unique_together_impede_duplicata(self, resposta_completa, escala_k10):
        from core.models import ResultadoEscala
        ResultadoEscala.objects.create(
            resposta_questionario=resposta_completa,
            escala_config=escala_k10,
            resultado_json={},
        )
        with pytest.raises(IntegrityError):
            ResultadoEscala.objects.create(
                resposta_questionario=resposta_completa,
                escala_config=escala_k10,
                resultado_json={},
            )
