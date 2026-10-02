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
        # O aceite do TCLE vai para ethics.aceitar_tcle, não para responder_questionario.
        # A view responder_questionario intercepta toda requisição (GET e POST) com render
        # quando o TCLE não foi aceito ainda, tornando seu handler interno de aceite inacessível.
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
