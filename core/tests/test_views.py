import json
import pytest
from django.urls import reverse

pytestmark = pytest.mark.django_db


# ── index_view ───────────────────────────────────────────────────────────────

class TestIndexView:
    def test_get_retorna_200(self, client):
        response = client.get(reverse('home'))
        assert response.status_code == 200

    def test_usa_template_home(self, client):
        response = client.get(reverse('home'))
        assert 'home.html' in [t.name for t in response.templates]


# ── lista_questionarios ──────────────────────────────────────────────────────

class TestListaQuestionarios:
    def test_get_retorna_200(self, client):
        response = client.get(reverse('lista_questionarios'))
        assert response.status_code == 200

    def test_exibe_apenas_ativos(self, client):
        from core.models import Questionario
        Questionario.objects.create(titulo='Ativo', ativo=True)
        Questionario.objects.create(titulo='Inativo', ativo=False)

        response = client.get(reverse('lista_questionarios'))
        questionarios = list(response.context['questionarios'])
        titulos = [q.titulo for q in questionarios]

        assert 'Ativo' in titulos
        assert 'Inativo' not in titulos

    def test_nao_exige_login(self, client):
        response = client.get(reverse('lista_questionarios'))
        assert response.status_code != 302


# ── gerenciar_questionarios ──────────────────────────────────────────────────

class TestGerenciarQuestionarios:
    def test_anonimo_redireciona_para_login(self, client):
        response = client.get(reverse('gerenciar_questionarios'))
        assert response.status_code == 302
        assert '/login/' in response['Location']

    def test_autenticado_retorna_200(self, client_pesquisador):
        response = client_pesquisador.get(reverse('gerenciar_questionarios'))
        assert response.status_code == 200

    def test_exibe_ativos_e_inativos(self, client_pesquisador):
        from core.models import Questionario
        Questionario.objects.create(titulo='Ativo', ativo=True)
        Questionario.objects.create(titulo='Inativo', ativo=False)

        response = client_pesquisador.get(reverse('gerenciar_questionarios'))
        titulos = [q.titulo for q in response.context['questionarios']]
        assert 'Ativo' in titulos
        assert 'Inativo' in titulos


# ── responder_questionario ───────────────────────────────────────────────────

class TestResponderQuestionario:
    def test_anonimo_redireciona_para_login(self, client, questionario_completo):
        url = reverse('responder_questionario', args=[questionario_completo.id])
        response = client.get(url)
        assert response.status_code == 302
        assert '/login/' in response['Location']

    def test_get_sem_tcle_no_bd_exibe_questionario(self, client_pesquisador, questionario_completo):
        # Sem TCLE no BD → vai direto para o questionário
        url = reverse('responder_questionario', args=[questionario_completo.id])
        response = client_pesquisador.get(url)
        assert response.status_code == 200
        assert not response.context.get('exibir_tcle', False)

    def test_get_com_tcle_nao_aceito_exibe_tcle(self, client_pesquisador, questionario_completo, tcle_ativo):
        url = reverse('responder_questionario', args=[questionario_completo.id])
        response = client_pesquisador.get(url)
        assert response.status_code == 200
        assert response.context.get('exibir_tcle') is True

    def test_post_aceitar_tcle_marca_sessao(self, client_pesquisador, questionario_completo, tcle_ativo):
        # O aceite do TCLE é tratado por ethics.aceitar_tcle; responder_questionario
        # apenas exibe o termo enquanto a sessão não tiver o aceite.
        url = reverse('aceitar_tcle', args=[tcle_ativo.id])
        response = client_pesquisador.post(url)
        assert response.status_code == 302
        assert client_pesquisador.session.get('tcle_aceito') is True

    def test_protecao_de_pagina_redireciona_ao_maximo_respondido(self, client_pesquisador, questionario_completo):
        url = reverse('responder_questionario', args=[questionario_completo.id])
        session = client_pesquisador.session
        session['tcle_aceito'] = True
        session['max_pagina_respondida'] = 1
        session.save()

        # questionario_completo tem 2 seções → página 2 existe, mas max é 1
        response = client_pesquisador.get(url + '?page=2')
        assert response.status_code == 302
        assert 'page=1' in response['Location']

    def test_post_finalizar_cria_resposta_questionario(self, client_pesquisador, questionario_completo):
        from core.models import Pergunta, Alternativa, RespostaQuestionario

        pergunta = Pergunta.objects.get(identificador='k10a')
        alt = Alternativa.objects.filter(pergunta=pergunta).first()

        session = client_pesquisador.session
        session['tcle_aceito'] = True
        session['max_pagina_respondida'] = 99
        session['respostas_temp'] = {
            str(pergunta.id): {
                'alternativa': str(alt.id),
                'texto': None,
                'identificador': 'k10a',
            }
        }
        session.save()

        url = reverse('responder_questionario', args=[questionario_completo.id])
        response = client_pesquisador.post(url, {'acao': 'finalizar'})

        assert response.status_code == 302
        resposta = RespostaQuestionario.objects.get(questionario=questionario_completo)
        assert response['Location'] == reverse('comprovante_coleta', args=[resposta.codigo_paciente])


# ── cancelar_preenchimento ───────────────────────────────────────────────────

class TestCancelarPreenchimento:
    def _sessao_em_andamento(self, client):
        session = client.session
        session['tcle_aceito'] = True
        session['max_pagina_respondida'] = 2
        session['respostas_temp'] = {'1': {'alternativa': '1', 'texto': None, 'identificador': 'x'}}
        session.save()

    def test_anonimo_redireciona_para_login(self, client, questionario_completo):
        url = reverse('cancelar_preenchimento', args=[questionario_completo.id])
        response = client.post(url)
        assert response.status_code == 302
        assert '/login/' in response['Location']

    def test_get_nao_permitido(self, client_assistente, questionario_completo):
        url = reverse('cancelar_preenchimento', args=[questionario_completo.id])
        assert client_assistente.get(url).status_code == 405

    def test_limpa_sessao_e_exige_novo_tcle(self, client_assistente, questionario_completo):
        self._sessao_em_andamento(client_assistente)
        url = reverse('cancelar_preenchimento', args=[questionario_completo.id])
        response = client_assistente.post(url)

        assert response.status_code == 302
        assert response['Location'] == reverse('lista_questionarios')
        session = client_assistente.session
        assert 'respostas_temp' not in session
        assert session['tcle_aceito'] is False
        assert session['max_pagina_respondida'] == 1

    def test_nao_grava_resposta(self, client_assistente, questionario_completo):
        from core.models import RespostaQuestionario
        self._sessao_em_andamento(client_assistente)
        client_assistente.post(reverse('cancelar_preenchimento', args=[questionario_completo.id]))
        assert not RespostaQuestionario.objects.exists()


# ── comprovante_coleta ───────────────────────────────────────────────────────

@pytest.fixture
def resposta_da_assistente(questionario_completo, usuario_assistente, tcle_ativo):
    from core.models import RespostaQuestionario
    from ethics.models import AceiteTCLE
    resposta = RespostaQuestionario.objects.create(
        pesquisadora=usuario_assistente,
        questionario=questionario_completo,
        paciente_nome='Paciente Sigiloso',
    )
    AceiteTCLE.objects.create(resposta_questionario=resposta, tcle=tcle_ativo)
    return resposta


class TestComprovanteColeta:
    def test_anonimo_redireciona_para_login(self, client, resposta_da_assistente):
        url = reverse('comprovante_coleta', args=[resposta_da_assistente.codigo_paciente])
        response = client.get(url)
        assert response.status_code == 302
        assert '/login/' in response['Location']

    def test_autora_da_coleta_acessa(self, client_assistente, resposta_da_assistente):
        url = reverse('comprovante_coleta', args=[resposta_da_assistente.codigo_paciente])
        response = client_assistente.get(url)
        assert response.status_code == 200
        assert resposta_da_assistente.codigo_paciente in response.content.decode()

    def test_nao_exibe_nome_do_paciente(self, client_assistente, resposta_da_assistente):
        url = reverse('comprovante_coleta', args=[resposta_da_assistente.codigo_paciente])
        response = client_assistente.get(url)
        assert 'Paciente Sigiloso' not in response.content.decode()

    def test_pesquisador_acessa_coleta_de_outro(self, client_pesquisador, resposta_da_assistente):
        url = reverse('comprovante_coleta', args=[resposta_da_assistente.codigo_paciente])
        assert client_pesquisador.get(url).status_code == 200

    def test_outra_assistente_recebe_403(self, client, resposta_da_assistente, grupo_assistente):
        from accounts.models import Usuario
        outra = Usuario(email='outra@test.com')
        outra.set_password('senha123')
        outra.save()
        outra.groups.add(grupo_assistente)
        client.force_login(outra)

        url = reverse('comprovante_coleta', args=[resposta_da_assistente.codigo_paciente])
        assert client.get(url).status_code == 403

    def test_codigo_inexistente_retorna_404(self, client_assistente):
        url = reverse('comprovante_coleta', args=['NAOEXISTE0'])
        assert client_assistente.get(url).status_code == 404


class TestRegistrarEntregaComprovante:
    def test_registra_impresso(self, client_assistente, resposta_da_assistente):
        url = reverse('registrar_entrega_comprovante', args=[resposta_da_assistente.codigo_paciente])
        response = client_assistente.post(url, {'modo': 'IMPRESSO'})
        assert response.status_code == 200
        resposta_da_assistente.aceite.refresh_from_db()
        assert resposta_da_assistente.aceite.comprovante_entregue_por == 'IMPRESSO'

    def test_modo_invalido_retorna_400(self, client_assistente, resposta_da_assistente):
        url = reverse('registrar_entrega_comprovante', args=[resposta_da_assistente.codigo_paciente])
        response = client_assistente.post(url, {'modo': 'EMAIL'})
        assert response.status_code == 400


class TestEnviarComprovanteEmail:
    def _url(self, resposta):
        return reverse('enviar_comprovante_email', args=[resposta.codigo_paciente])

    def test_envia_email_com_codigo_e_sem_nome(self, client_assistente, resposta_da_assistente, mailoutbox):
        response = client_assistente.post(self._url(resposta_da_assistente), {'email': 'paciente@exemplo.com'})

        assert response.status_code == 302
        assert len(mailoutbox) == 1
        msg = mailoutbox[0]
        assert msg.to == ['paciente@exemplo.com']
        assert resposta_da_assistente.codigo_paciente in msg.body
        assert 'Paciente Sigiloso' not in msg.body
        assert 'Paciente Sigiloso' not in msg.alternatives[0][0]

    def test_registra_entrega_por_email(self, client_assistente, resposta_da_assistente, mailoutbox):
        client_assistente.post(self._url(resposta_da_assistente), {'email': 'paciente@exemplo.com'})
        resposta_da_assistente.aceite.refresh_from_db()
        assert resposta_da_assistente.aceite.comprovante_entregue_por == 'EMAIL'

    def test_email_invalido_nao_envia(self, client_assistente, resposta_da_assistente, mailoutbox):
        response = client_assistente.post(self._url(resposta_da_assistente), {'email': 'invalido'})
        assert response.status_code == 302
        assert len(mailoutbox) == 0

    def test_falha_no_envio_nao_registra_entrega(self, client_assistente, resposta_da_assistente, monkeypatch):
        def _falha(*args, **kwargs):
            raise ConnectionError('provedor fora do ar')
        monkeypatch.setattr('core.views.send_mail', _falha)

        response = client_assistente.post(self._url(resposta_da_assistente), {'email': 'paciente@exemplo.com'})
        assert response.status_code == 302
        resposta_da_assistente.aceite.refresh_from_db()
        assert resposta_da_assistente.aceite.comprovante_entregue_por == ''


# ── desativar_questionario ───────────────────────────────────────────────────

class TestDesativarQuestionario:
    def test_post_alterna_ativo(self, client_pesquisador, questionario_simples):
        url = reverse('desativar_questionario', args=[questionario_simples.id])
        response = client_pesquisador.post(url)
        assert response.status_code == 200
        data = response.json()
        assert data['status'] == 'success'

        questionario_simples.refresh_from_db()
        assert questionario_simples.ativo is False   # era True → virou False

    def test_segundo_post_reativa(self, client_pesquisador, questionario_simples):
        url = reverse('desativar_questionario', args=[questionario_simples.id])
        client_pesquisador.post(url)   # desativa
        client_pesquisador.post(url)   # reativa
        questionario_simples.refresh_from_db()
        assert questionario_simples.ativo is True

    def test_get_retorna_405(self, client_pesquisador, questionario_simples):
        url = reverse('desativar_questionario', args=[questionario_simples.id])
        response = client_pesquisador.get(url)
        assert response.status_code == 405

    def test_anonimo_redireciona_para_login(self, client, questionario_simples):
        url = reverse('desativar_questionario', args=[questionario_simples.id])
        response = client.post(url)
        assert response.status_code == 302


# ── dashboard_respostas ──────────────────────────────────────────────────────

class TestDashboardRespostas:
    def test_anonimo_redireciona_para_login(self, client):
        response = client.get(reverse('dashboard_respostas'))
        assert response.status_code == 302

    def test_autenticado_retorna_200(self, client_pesquisador):
        response = client_pesquisador.get(reverse('dashboard_respostas'))
        assert response.status_code == 200

    def test_filtro_por_questionario(self, client_pesquisador, questionario_simples):
        url = reverse('dashboard_respostas') + f'?questionario={questionario_simples.id}'
        response = client_pesquisador.get(url)
        assert response.status_code == 200
        assert response.context['filtro_questionario'] == str(questionario_simples.id)

    def test_total_avaliacoes_no_contexto(self, client_pesquisador, resposta_completa):
        response = client_pesquisador.get(reverse('dashboard_respostas'))
        assert 'total_avaliacoes' in response.context
        assert response.context['total_avaliacoes'] >= 1


# ── exportar_respostas_excel ─────────────────────────────────────────────────

class TestExportarRespostasExcel:
    def test_anonimo_redireciona(self, client, resposta_completa):
        url = reverse('exportar_respostas_excel', args=[resposta_completa.id])
        response = client.get(url)
        assert response.status_code == 302

    def test_retorna_xlsx(self, client_pesquisador, resposta_completa):
        url = reverse('exportar_respostas_excel', args=[resposta_completa.id])
        response = client_pesquisador.get(url)
        assert response.status_code == 200
        assert 'spreadsheetml' in response['Content-Type']


# ── exportar_resultados_massa_excel ──────────────────────────────────────────

class TestExportarResultadosMassaExcel:
    def test_anonimo_redireciona(self, client):
        response = client.get(reverse('exportar_resultados_massa_excel'))
        assert response.status_code == 302

    def test_retorna_xlsx(self, client_pesquisador):
        response = client_pesquisador.get(reverse('exportar_resultados_massa_excel'))
        assert response.status_code == 200
        assert 'spreadsheetml' in response['Content-Type']


# ── recalcular_escalas ───────────────────────────────────────────────────────

class TestRecalcularEscalas:
    def test_anonimo_redireciona(self, client):
        response = client.post(reverse('recalcular_escalas'))
        assert response.status_code == 302

    def test_get_retorna_405(self, client_pesquisador):
        response = client_pesquisador.get(reverse('recalcular_escalas'))
        assert response.status_code == 405

    def test_post_retorna_json(self, client_pesquisador):
        response = client_pesquisador.post(reverse('recalcular_escalas'))
        assert response.status_code == 200
        data = response.json()
        assert 'sucesso' in data
        assert 'falhas' in data
        assert 'total' in data

    def test_recalcula_respostas_existentes(self, client_pesquisador, resposta_completa, escala_k10):
        response = client_pesquisador.post(reverse('recalcular_escalas'))
        data = response.json()
        assert data['total'] >= 1


# ── helpers ──────────────────────────────────────────────────────────────────

def _ler_planilha(response):
    """Abre o .xlsx retornado pela view e devolve as linhas como listas de valores."""
    import io
    import openpyxl
    wb = openpyxl.load_workbook(io.BytesIO(response.content))
    return [list(linha) for linha in wb.active.iter_rows(values_only=True)]


def _criar_resposta(questionario, pesquisadora, nome='Paciente'):
    from core.models import RespostaQuestionario
    return RespostaQuestionario.objects.create(
        pesquisadora=pesquisadora,
        questionario=questionario,
        paciente_nome=nome,
    )


def _criar_resultado(resposta, escala, score=None, classificacao='', resultado_json=None):
    from core.models import ResultadoEscala
    return ResultadoEscala.objects.create(
        resposta_questionario=resposta,
        escala_config=escala,
        score_principal=score,
        classificacao=classificacao,
        resultado_json=resultado_json or {},
    )


@pytest.fixture
def sessao_coleta(client_pesquisador):
    """Sessão com TCLE aceito, pronta para navegar entre as páginas do questionário."""
    def _configurar(max_pagina=1, respostas=None):
        session = client_pesquisador.session
        session['tcle_aceito'] = True
        session['max_pagina_respondida'] = max_pagina
        session['respostas_temp'] = respostas or {}
        session.save()
        return client_pesquisador
    return _configurar


# ── responder_questionario: navegação e finalização ─────────────────────────

class TestResponderQuestionarioNavegacao:
    def _url(self, questionario, page=None):
        url = reverse('responder_questionario', args=[questionario.id])
        return f'{url}?page={page}' if page else url

    def test_get_exibe_secao_e_progresso(self, sessao_coleta, questionario_completo):
        client = sessao_coleta()
        response = client.get(self._url(questionario_completo))
        assert response.context['secao'].titulo == 'Dados Demográficos'
        assert response.context['progresso'] == 50   # página 1 de 2

    def test_proximo_salva_respostas_e_libera_proxima_pagina(self, sessao_coleta, questionario_completo):
        from core.models import Pergunta
        idade = Pergunta.objects.get(identificador='idade')
        client = sessao_coleta()

        response = client.post(self._url(questionario_completo), {
            'acao': 'proximo',
            f'pergunta_{idade.id}_texto': '34',
        })

        assert response.status_code == 302
        assert response['Location'].endswith('?page=2')
        session = client.session
        assert session['respostas_temp'][str(idade.id)]['texto'] == '34'
        assert session['max_pagina_respondida'] == 2

    def test_proximo_em_pagina_ja_liberada_nao_reduz_maximo(self, sessao_coleta, questionario_completo):
        client = sessao_coleta(max_pagina=2)
        # Volta à página 1 e avança de novo: o máximo continua 2
        client.post(self._url(questionario_completo, page=1), {'acao': 'proximo'})
        assert client.session['max_pagina_respondida'] == 2

    def test_anterior_volta_uma_pagina(self, sessao_coleta, questionario_completo):
        client = sessao_coleta(max_pagina=2)
        response = client.post(self._url(questionario_completo, page=2), {'acao': 'anterior'})
        assert response.status_code == 302
        assert response['Location'].endswith('?page=1')

    def test_ir_pagina_nao_ultrapassa_maximo_respondido(self, sessao_coleta, questionario_completo):
        # Não é possível pular para uma página ainda não respondida
        client = sessao_coleta(max_pagina=1)
        response = client.post(self._url(questionario_completo), {'acao': 'ir_pagina_2'})
        assert response['Location'].endswith('?page=1')

    def test_ir_pagina_permite_voltar_a_pagina_liberada(self, sessao_coleta, questionario_completo):
        client = sessao_coleta(max_pagina=2)
        response = client.post(self._url(questionario_completo), {'acao': 'ir_pagina_2'})
        assert response['Location'].endswith('?page=2')

    def test_ir_pagina_com_numero_invalido_vai_para_primeira(self, sessao_coleta, questionario_completo):
        client = sessao_coleta(max_pagina=2)
        response = client.post(self._url(questionario_completo, page=2), {'acao': 'ir_pagina_abc'})
        assert response['Location'].endswith('?page=1')

    def test_finalizar_grava_coleta_completa(self, sessao_coleta, questionario_completo, tcle_ativo, escala_k10):
        from core.models import Pergunta, Alternativa, RespostaQuestionario, RespostaPergunta, ResultadoEscala, Secao
        from ethics.models import AceiteTCLE

        secao = Secao.objects.get(questionario=questionario_completo, ordem=1)
        nome = Pergunta.objects.create(secao=secao, conteudo='Nome', tipo='TX', ordem=2, identificador='nome')
        k10a = Pergunta.objects.get(identificador='k10a')
        alt = Alternativa.objects.get(pergunta=k10a, valor=3)

        # Página 1 já respondida (na sessão); a resposta da página 2 chega no próprio POST de finalização
        client = sessao_coleta(max_pagina=2, respostas={
            str(nome.id): {'alternativa': None, 'texto': 'João da Silva', 'identificador': 'nome'},
        })
        client.post(self._url(questionario_completo, page=2), {
            'acao': 'finalizar',
            f'pergunta_{k10a.id}': str(alt.id),
        })

        resposta = RespostaQuestionario.objects.get(questionario=questionario_completo)
        # Nome do paciente vem da pergunta com identificador 'nome'
        assert resposta.paciente_nome == 'João da Silva'
        # Vínculo com a versão do TCLE aceita
        assert AceiteTCLE.objects.get(resposta_questionario=resposta).tcle == tcle_ativo
        assert RespostaPergunta.objects.get(resposta_questionario=resposta, pergunta=k10a).alternativa == alt
        # Escalas calculadas e cacheadas na submissão
        resultado = ResultadoEscala.objects.get(resposta_questionario=resposta, escala_config=escala_k10)
        assert resultado.score_principal == 3
        # Sessão limpa: próximo atendimento exige novo aceite
        session = client.session
        assert session['tcle_aceito'] is False
        assert 'respostas_temp' not in session

    def test_finalizar_sem_pergunta_de_nome_registra_nao_informado(self, sessao_coleta, questionario_completo):
        from core.models import RespostaQuestionario
        client = sessao_coleta(max_pagina=2)
        client.post(self._url(questionario_completo, page=2), {'acao': 'finalizar'})
        assert RespostaQuestionario.objects.get().paciente_nome == 'Não informado'

    @pytest.mark.parametrize('alternativa_invalida', ['999999', 'abc'])
    def test_finalizar_ignora_alternativa_invalida(self, sessao_coleta, questionario_completo, alternativa_invalida):
        from core.models import Pergunta, RespostaPergunta
        k10a = Pergunta.objects.get(identificador='k10a')
        client = sessao_coleta(max_pagina=2)

        response = client.post(self._url(questionario_completo, page=2), {
            'acao': 'finalizar',
            f'pergunta_{k10a.id}': alternativa_invalida,
        })

        assert response.status_code == 302
        assert RespostaPergunta.objects.get(pergunta=k10a).alternativa is None


# ── controle de acesso por grupo ─────────────────────────────────────────────

ROTAS_PESQUISADOR = [
    ('get', 'gerenciar_questionarios', False),
    ('get', 'nova_avaliacao', False),
    ('get', 'editar_avaliacao', True),
    ('get', 'configurar_escala', True),
    ('post', 'desativar_questionario', True),
    ('post', 'salvar_avaliacao_api', False),
]

ROTAS_EQUIPE = [
    ('get', 'dashboard_respostas', False),
    ('get', 'relatorios_medicos', False),
    ('post', 'recalcular_escalas', False),
    ('get', 'exportar_resultados_massa_excel', False),
]


def _requisitar(client, metodo, nome_url, usa_pk, pk):
    url = reverse(nome_url, args=[pk]) if usa_pk else reverse(nome_url)
    return getattr(client, metodo)(url)


class TestControleDeAcesso:
    """Valida as regras de permissão por grupo descritas na especificação."""

    @pytest.mark.parametrize('metodo,nome_url,usa_pk', ROTAS_PESQUISADOR)
    def test_assistente_nao_gerencia_questionarios(self, client_assistente, questionario_simples, metodo, nome_url, usa_pk):
        response = _requisitar(client_assistente, metodo, nome_url, usa_pk, questionario_simples.id)
        assert response.status_code == 403

    @pytest.mark.parametrize('metodo,nome_url,usa_pk', ROTAS_PESQUISADOR + ROTAS_EQUIPE)
    def test_usuario_sem_grupo_recebe_403(self, client, usuario_comum, questionario_simples, metodo, nome_url, usa_pk):
        client.force_login(usuario_comum)
        response = _requisitar(client, metodo, nome_url, usa_pk, questionario_simples.id)
        assert response.status_code == 403

    @pytest.mark.parametrize('metodo,nome_url,usa_pk', ROTAS_EQUIPE)
    def test_assistente_acessa_dashboard_e_relatorios(self, client_assistente, metodo, nome_url, usa_pk):
        response = _requisitar(client_assistente, metodo, nome_url, usa_pk, None)
        assert response.status_code == 200

    def test_staff_sem_grupo_gerencia_questionarios(self, client, usuario_comum):
        usuario_comum.is_staff = True
        usuario_comum.save()
        client.force_login(usuario_comum)
        assert client.get(reverse('gerenciar_questionarios')).status_code == 200

    def test_assistente_nao_consegue_desativar_questionario(self, client_assistente, questionario_simples):
        client_assistente.post(reverse('desativar_questionario', args=[questionario_simples.id]))
        questionario_simples.refresh_from_db()
        assert questionario_simples.ativo is True

    def test_assistente_exporta_resposta_individual(self, client_assistente, resposta_completa):
        url = reverse('exportar_respostas_excel', args=[resposta_completa.id])
        assert client_assistente.get(url).status_code == 200


# ── relatorios_medicos ───────────────────────────────────────────────────────

class TestRelatoriosMedicos:
    def _codigos(self, response):
        return [r.codigo_paciente for r in response.context['todas_respostas']]

    def _antiga_e_recente(self, questionario, pesquisadora):
        from datetime import timedelta
        from django.utils import timezone
        from core.models import RespostaQuestionario
        antiga = _criar_resposta(questionario, pesquisadora)
        recente = _criar_resposta(questionario, pesquisadora)
        RespostaQuestionario.objects.filter(pk=antiga.pk).update(data_submissao=timezone.now() - timedelta(days=1))
        return antiga, recente

    def test_anonimo_redireciona_para_login(self, client):
        response = client.get(reverse('relatorios_medicos'))
        assert response.status_code == 302
        assert '/login/' in response['Location']

    def test_padrao_ordena_da_mais_recente_para_a_mais_antiga(self, client_pesquisador, questionario_simples, usuario_pesquisador):
        antiga, recente = self._antiga_e_recente(questionario_simples, usuario_pesquisador)
        response = client_pesquisador.get(reverse('relatorios_medicos'))
        assert self._codigos(response) == [recente.codigo_paciente, antiga.codigo_paciente]

    def test_ordena_por_codigo_do_paciente(self, client_pesquisador, questionario_simples, usuario_pesquisador):
        for _ in range(3):
            _criar_resposta(questionario_simples, usuario_pesquisador)

        response = client_pesquisador.get(reverse('relatorios_medicos') + '?sort=codigo_paciente')
        codigos = self._codigos(response)
        assert codigos == sorted(codigos)
        assert response.context['current_sort'] == 'codigo_paciente'

    def test_ordenacao_fora_da_lista_permitida_usa_padrao(self, client_pesquisador, questionario_simples, usuario_pesquisador):
        antiga, recente = self._antiga_e_recente(questionario_simples, usuario_pesquisador)
        # Campo fora da lista branca (ex.: dado criptografado) não pode ir para o order_by
        response = client_pesquisador.get(reverse('relatorios_medicos') + '?sort=paciente_nome')
        assert response.status_code == 200
        assert self._codigos(response) == [recente.codigo_paciente, antiga.codigo_paciente]

    def test_filtra_por_questionario(self, client_pesquisador, questionario_simples, questionario_completo, usuario_pesquisador):
        alvo = _criar_resposta(questionario_simples, usuario_pesquisador)
        _criar_resposta(questionario_completo, usuario_pesquisador)

        response = client_pesquisador.get(reverse('relatorios_medicos') + f'?questionario={questionario_simples.id}')
        assert self._codigos(response) == [alvo.codigo_paciente]

    def test_pagina_de_10_em_10(self, client_pesquisador, questionario_simples, usuario_pesquisador):
        for _ in range(12):
            _criar_resposta(questionario_simples, usuario_pesquisador)

        pagina1 = client_pesquisador.get(reverse('relatorios_medicos'))
        pagina2 = client_pesquisador.get(reverse('relatorios_medicos') + '?page=2')
        assert len(self._codigos(pagina1)) == 10
        assert len(self._codigos(pagina2)) == 2


# ── dashboard_respostas: indicadores ─────────────────────────────────────────

class TestDashboardIndicadores:
    def test_prevalencia_k10_considera_apenas_classificacao_de_risco(self, client_pesquisador, questionario_completo, usuario_pesquisador, escala_k10):
        _criar_resultado(_criar_resposta(questionario_completo, usuario_pesquisador), escala_k10, 25, 'Provável transtorno')
        _criar_resultado(_criar_resposta(questionario_completo, usuario_pesquisador), escala_k10, 12, 'Baixo risco')

        ctx = client_pesquisador.get(reverse('dashboard_respostas')).context
        assert ctx['n_k10_risco'] == 1
        assert ctx['pct_k10_risco'] == 50.0
        assert json.loads(ctx['dist_k10_json']) == {'Provável transtorno': 1, 'Baixo risco': 1}

    def test_sem_resultados_indicadores_ficam_zerados(self, client_pesquisador):
        ctx = client_pesquisador.get(reverse('dashboard_respostas')).context
        assert ctx['pct_psqi_ruim'] == 0
        assert ctx['n_psqi_ruim'] == 0

    def test_filtro_por_questionario_restringe_indicadores(self, client_pesquisador, questionario_completo, questionario_simples, usuario_pesquisador, escala_k10):
        _criar_resultado(_criar_resposta(questionario_completo, usuario_pesquisador), escala_k10, 25, 'Provável transtorno')
        _criar_resultado(_criar_resposta(questionario_simples, usuario_pesquisador), escala_k10, 12, 'Baixo risco')

        url = reverse('dashboard_respostas') + f'?questionario={questionario_simples.id}'
        ctx = client_pesquisador.get(url).context
        assert ctx['total_avaliacoes'] == 1
        assert ctx['n_k10_risco'] == 0
        assert ctx['pct_k10_risco'] == 0.0

    def test_dispersao_psqi_x_depressao_dass(self, client_pesquisador, questionario_completo, usuario_pesquisador, escala_psqi, escala_dass21):
        com_dass = _criar_resposta(questionario_completo, usuario_pesquisador)
        _criar_resultado(com_dass, escala_psqi, 8, 'Qualidade Ruim')
        _criar_resultado(com_dass, escala_dass21, resultado_json={'dass_depressao_total': 14})

        # Sem DASS-21 ou com PSQI sem score: ficam fora do gráfico
        sem_dass = _criar_resposta(questionario_completo, usuario_pesquisador)
        _criar_resultado(sem_dass, escala_psqi, 5, 'Qualidade Boa')
        sem_score = _criar_resposta(questionario_completo, usuario_pesquisador)
        _criar_resultado(sem_score, escala_psqi, None)

        url = reverse('dashboard_respostas') + f'?questionario={questionario_completo.id}'
        ctx = client_pesquisador.get(url).context
        assert json.loads(ctx['scatter_psqi_dass_json']) == [{'x': 8.0, 'y': 14}]
        assert ctx['n_psqi_ruim'] == 1


# ── recalcular_escalas: falhas e filtro ──────────────────────────────────────

class TestRecalcularEscalasFalhas:
    def test_contabiliza_falha_sem_interromper_lote(self, client_pesquisador, questionario_completo, usuario_pesquisador, monkeypatch):
        _criar_resposta(questionario_completo, usuario_pesquisador)
        com_erro = _criar_resposta(questionario_completo, usuario_pesquisador)

        def _calcular(resposta):
            if resposta.pk == com_erro.pk:
                raise ValueError('dado corrompido')
            return []
        monkeypatch.setattr('core.views.calcular_e_salvar_resultados', _calcular)

        data = client_pesquisador.post(reverse('recalcular_escalas')).json()
        assert data['total'] == 2
        assert data['sucesso'] == 1
        assert data['falhas'] == 1
        assert data['erros'] == [f'[{com_erro.codigo_paciente}] dado corrompido']

    def test_filtra_por_questionario(self, client_pesquisador, questionario_completo, questionario_simples, usuario_pesquisador):
        _criar_resposta(questionario_completo, usuario_pesquisador)
        _criar_resposta(questionario_simples, usuario_pesquisador)

        data = client_pesquisador.post(reverse('recalcular_escalas'), {'questionario': questionario_simples.id}).json()
        assert data['total'] == 1


# ── exportar_respostas_excel: conteúdo ───────────────────────────────────────

class TestExportarRespostasExcelConteudo:
    def _exportar(self, client, resposta):
        return _ler_planilha(client.get(reverse('exportar_respostas_excel', args=[resposta.id])))

    def _vincular(self, questionario, nome, config):
        from core.models import EscalaConfig
        escala = EscalaConfig.objects.create(nome=nome, strategy_class='DYNAMIC', config_dinamica=config)
        escala.questionarios.add(questionario)
        return escala

    def test_cabecalho_identifica_paciente_e_pesquisadora(self, client_pesquisador, resposta_completa):
        linhas = self._exportar(client_pesquisador, resposta_completa)
        assert linhas[0][0] == 'SOMNUS - RELATÓRIO TÉCNICO'
        assert ['Paciente:', 'Paciente Teste', None] in linhas
        assert ['Pesquisadora:', 'pesquisador@test.com', None] in linhas

    def test_inclui_score_e_classificacao_da_escala_vinculada(self, client_pesquisador, resposta_completa, escala_k10):
        # resposta_completa marcou k10a = 1 → total 1, abaixo do corte de 20
        linhas = self._exportar(client_pesquisador, resposta_completa)
        assert ['K10 - K10 Total', 1, 'Baixo risco'] in linhas

    def test_escala_dinamica_associa_status_ao_total(self, client_pesquisador, resposta_completa, escala_dynamic):
        linhas = self._exportar(client_pesquisador, resposta_completa)
        assert ['Escala Dinâmica - Total', 0, 'Baixo'] in linhas

    def test_subescalas_associam_status_ao_respectivo_total(self, client_pesquisador, resposta_completa):
        self._vincular(resposta_completa.questionario, 'Subescalas', {
            'operacao': 'SUM_BY_SUBSCALE',
            'subescalas': {'fisico': ['k10a'], 'emocional': []},
            'limiares': {'fisico': [{'max': 5, 'status': 'Leve'}]},
        })

        linhas = self._exportar(client_pesquisador, resposta_completa)
        assert ['Subescalas - Fisico Total', 1, 'Leve'] in linhas
        # Subescala sem limiares não recebe classificação
        assert ['Subescalas - Emocional Total', 0, '-'] in linhas

    def test_escala_com_erro_nao_aparece_no_relatorio(self, client_pesquisador, resposta_completa):
        self._vincular(resposta_completa.questionario, 'Sem Config', {})

        linhas = self._exportar(client_pesquisador, resposta_completa)
        assert not any(str(linha[0]).startswith('Sem Config') for linha in linhas)

    def test_calcula_imc_a_partir_de_texto_livre(self, client_pesquisador, resposta_completa):
        from core.models import Pergunta, RespostaPergunta, Secao
        secao = Secao.objects.get(questionario=resposta_completa.questionario, ordem=1)
        for ordem, (ident, texto) in enumerate([('peso', '70 kg'), ('altura', '1,75 m')], start=10):
            pergunta = Pergunta.objects.create(secao=secao, conteudo=ident, tipo='TX', ordem=ordem, identificador=ident)
            RespostaPergunta.objects.create(resposta_questionario=resposta_completa, pergunta=pergunta, resposta_texto=texto)

        linhas = self._exportar(client_pesquisador, resposta_completa)
        assert ['IMC Calculado Automaticamente', 22.86, 'kg/m²'] in linhas

    def test_detalha_respostas_por_identificador(self, client_pesquisador, resposta_completa):
        linhas = self._exportar(client_pesquisador, resposta_completa)
        assert ['k10a', 'Com que frequência se sentiu cansado sem motivo?', 1] in linhas


# ── exportar_resultados_massa_excel: conteúdo ────────────────────────────────

class TestExportarResultadosMassaConteudo:
    def test_uma_linha_por_paciente_com_escalas_e_respostas(self, client_pesquisador, resposta_completa, escala_k10):
        from core.services import calcular_e_salvar_resultados
        calcular_e_salvar_resultados(resposta_completa)

        linhas = _ler_planilha(client_pesquisador.get(reverse('exportar_resultados_massa_excel')))
        cabecalho, dados = linhas[0], linhas[1:]
        assert cabecalho[:5] == ['ID', 'Código Paciente', 'Nome Paciente', 'Data', 'Questionário']
        assert 'E: K10 (Score)' in cabecalho
        assert 'P: k10a' in cabecalho

        assert len(dados) == 1
        linha = dict(zip(cabecalho, dados[0]))
        assert linha['Código Paciente'] == resposta_completa.codigo_paciente
        assert linha['E: K10 (Score)'] == 1
        assert linha['E: K10 (Classificação)'] == 'Baixo risco'
        assert linha['P: k10a'] == 1

    def test_filtra_por_questionario(self, client_pesquisador, resposta_completa, questionario_simples, usuario_pesquisador):
        outra = _criar_resposta(questionario_simples, usuario_pesquisador)

        url = reverse('exportar_resultados_massa_excel') + f'?questionario={questionario_simples.id}'
        dados = _ler_planilha(client_pesquisador.get(url))[1:]
        assert [linha[1] for linha in dados] == [outra.codigo_paciente]
