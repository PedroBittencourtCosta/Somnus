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
        assert RespostaQuestionario.objects.filter(questionario=questionario_completo).exists()


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
