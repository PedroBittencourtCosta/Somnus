import pytest
from django.contrib.auth.models import Group


# ── Usuários ────────────────────────────────────────────────────────────────

@pytest.fixture
def grupo_pesquisador(db):
    return Group.objects.get_or_create(name='Pesquisador')[0]


@pytest.fixture
def grupo_assistente(db):
    return Group.objects.get_or_create(name='Assistente de Pesquisa')[0]


def _criar_usuario(email, password='senha123', **kwargs):
    """Cria e salva um Usuario sem depender do manager padrão (que exige username)."""
    from accounts.models import Usuario
    user = Usuario(email=email, **kwargs)
    user.set_password(password)
    user.save()
    return user


@pytest.fixture
def usuario_pesquisador(db, grupo_pesquisador):
    user = _criar_usuario('pesquisador@test.com', first_name='Ana', last_name='Pesquisadora')
    user.groups.add(grupo_pesquisador)
    return user


@pytest.fixture
def usuario_assistente(db, grupo_assistente):
    user = _criar_usuario('assistente@test.com', first_name='Carlos', last_name='Assistente')
    user.groups.add(grupo_assistente)
    return user


@pytest.fixture
def usuario_comum(db):
    return _criar_usuario('comum@test.com', first_name='Maria', last_name='Comum')


# ── Questionário completo ───────────────────────────────────────────────────

@pytest.fixture
def questionario_simples(db):
    from core.models import Questionario
    return Questionario.objects.create(
        titulo='Questionário de Teste',
        descricao='Questionário usado nos testes automatizados.',
    )


@pytest.fixture
def questionario_completo(db):
    from core.models import Questionario, Secao, Pergunta, Alternativa

    q = Questionario.objects.create(
        titulo='Questionário de Sono e Saúde Mental',
        descricao='Questionário completo para testes.',
    )

    secao1 = Secao.objects.create(
        questionario=q,
        titulo='Dados Demográficos',
        ordem=1,
        layout='LISTA',
    )
    secao2 = Secao.objects.create(
        questionario=q,
        titulo='Escala K10',
        ordem=2,
        layout='TABELA',
    )

    p_idade = Pergunta.objects.create(
        secao=secao1,
        conteudo='Qual é a sua idade?',
        tipo='TX',
        ordem=1,
        identificador='idade',
    )

    p_k10a = Pergunta.objects.create(
        secao=secao2,
        conteudo='Com que frequência se sentiu cansado sem motivo?',
        tipo='MC',
        ordem=1,
        identificador='k10a',
    )
    for valor, texto in enumerate(['Nunca', 'Raramente', 'Às vezes', 'Frequentemente', 'Sempre']):
        Alternativa.objects.create(pergunta=p_k10a, conteudo=texto, valor=valor + 1)

    return q


@pytest.fixture
def resposta_completa(db, questionario_completo, usuario_pesquisador):
    from core.models import RespostaQuestionario, RespostaPergunta, Pergunta, Alternativa

    resposta = RespostaQuestionario.objects.create(
        pesquisadora=usuario_pesquisador,
        questionario=questionario_completo,
        paciente_nome='Paciente Teste',
    )

    pergunta_k10a = Pergunta.objects.get(identificador='k10a')
    alt = Alternativa.objects.filter(pergunta=pergunta_k10a).first()
    RespostaPergunta.objects.create(
        resposta_questionario=resposta,
        pergunta=pergunta_k10a,
        alternativa=alt,
    )

    return resposta


# ── Escalas ─────────────────────────────────────────────────────────────────

@pytest.fixture
def escala_psqi(db, questionario_completo):
    from core.models import EscalaConfig
    escala = EscalaConfig.objects.create(nome='PSQI', strategy_class='PSQI')
    escala.questionarios.add(questionario_completo)
    return escala


@pytest.fixture
def escala_dass21(db, questionario_completo):
    from core.models import EscalaConfig
    escala = EscalaConfig.objects.create(nome='DASS-21', strategy_class='DASS21')
    escala.questionarios.add(questionario_completo)
    return escala


@pytest.fixture
def escala_k10(db, questionario_completo):
    from core.models import EscalaConfig
    escala = EscalaConfig.objects.create(nome='K10', strategy_class='K10')
    escala.questionarios.add(questionario_completo)
    return escala


@pytest.fixture
def escala_srq20(db, questionario_completo):
    from core.models import EscalaConfig
    escala = EscalaConfig.objects.create(nome='SRQ-20', strategy_class='SRQ20')
    escala.questionarios.add(questionario_completo)
    return escala


@pytest.fixture
def escala_ese(db, questionario_completo):
    from core.models import EscalaConfig
    escala = EscalaConfig.objects.create(nome='ESE', strategy_class='ESE')
    escala.questionarios.add(questionario_completo)
    return escala


@pytest.fixture
def escala_audit(db, questionario_completo):
    from core.models import EscalaConfig
    escala = EscalaConfig.objects.create(nome='AUDIT', strategy_class='AUDIT')
    escala.questionarios.add(questionario_completo)
    return escala


@pytest.fixture
def escala_emssp(db, questionario_completo):
    from core.models import EscalaConfig
    escala = EscalaConfig.objects.create(nome='EMSSP', strategy_class='EMSSP')
    escala.questionarios.add(questionario_completo)
    return escala


@pytest.fixture
def escala_imc(db, questionario_completo):
    from core.models import EscalaConfig
    escala = EscalaConfig.objects.create(nome='IMC', strategy_class='IMC')
    escala.questionarios.add(questionario_completo)
    return escala


@pytest.fixture
def escala_dynamic(db, questionario_completo):
    from core.models import EscalaConfig
    escala = EscalaConfig.objects.create(
        nome='Escala Dinâmica',
        strategy_class='DYNAMIC',
        config_dinamica={
            'operacao': 'SUM',
            'variaveis': ['q1', 'q2', 'q3'],
            'limiares': [
                {'max': 5, 'status': 'Baixo'},
                {'max': 10, 'status': 'Médio'},
                {'max': 999, 'status': 'Alto'},
            ],
        },
    )
    escala.questionarios.add(questionario_completo)
    return escala


# ── TCLE ────────────────────────────────────────────────────────────────────

@pytest.fixture
def tcle_ativo(db):
    from ethics.models import TCLE
    return TCLE.objects.create(
        conteudo='Este é o Termo de Consentimento Livre e Esclarecido para fins de teste.',
        versao=1.0,
    )


# ── Cliente autenticado ──────────────────────────────────────────────────────

@pytest.fixture
def client_pesquisador(client, usuario_pesquisador):
    client.force_login(usuario_pesquisador)
    return client


@pytest.fixture
def client_assistente(client, usuario_assistente):
    client.force_login(usuario_assistente)
    return client
