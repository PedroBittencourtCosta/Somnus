import json
import pytest
from django.urls import reverse

pytestmark = pytest.mark.django_db


# ── salvar_questionario_api ──────────────────────────────────────────────────

class TestSalvarQuestionarioApi:
    def _payload(self, titulo='Q API', secoes=None):
        return {
            'titulo': titulo,
            'descricao': 'Descrição',
            'secoes': secoes or [],
        }

    def _post(self, client, data):
        return client.post(
            reverse('salvar_avaliacao_api'),
            data=json.dumps(data),
            content_type='application/json',
        )

    def test_anonimo_redireciona(self, client):
        response = self._post(client, self._payload())
        assert response.status_code == 302

    def test_cria_questionario_novo(self, client_pesquisador):
        from core.models import Questionario
        response = self._post(client_pesquisador, self._payload('Novo Q'))
        assert response.status_code == 200
        data = response.json()
        assert data['status'] == 'success'
        assert Questionario.objects.filter(titulo='Novo Q').exists()

    def test_retorna_id_do_questionario(self, client_pesquisador):
        response = self._post(client_pesquisador, self._payload('Q com ID'))
        data = response.json()
        assert 'questionario_id' in data
        assert isinstance(data['questionario_id'], int)

    def test_edita_questionario_existente(self, client_pesquisador, questionario_simples):
        payload = {
            'id': questionario_simples.id,
            'titulo': 'Título Atualizado',
            'descricao': 'Nova descrição',
            'secoes': [],
        }
        response = self._post(client_pesquisador, payload)
        assert response.status_code == 200
        questionario_simples.refresh_from_db()
        assert questionario_simples.titulo == 'Título Atualizado'

    def test_cria_questionario_com_secao_e_pergunta(self, client_pesquisador):
        from core.models import Secao, Pergunta
        payload = self._payload(
            'Q Completo',
            secoes=[{
                'titulo': 'Seção 1',
                'instrucao': '',
                'layout': 'LISTA',
                'perguntas': [{
                    'conteudo': 'Qual é a sua idade?',
                    'tipo': 'TX',
                    'mascara': 'NENHUMA',
                    'config_mista': 'QUALQUER',
                    'obrigatoria': True,
                    'identificador': 'idade',
                    'alternativas': [],
                    'depende_de_alternativa_ids': [],
                    'depende_de_texto_de_id': None,
                }],
            }],
        )
        response = self._post(client_pesquisador, payload)
        data = response.json()
        assert data['status'] == 'success'
        assert Secao.objects.filter(titulo='Seção 1').exists()
        assert Pergunta.objects.filter(identificador='idade').exists()

    def test_remove_secoes_deletadas_do_payload(self, client_pesquisador, questionario_completo):
        """Salvar sem seções → limpa as seções anteriores do questionário."""
        from core.models import Secao
        payload = {
            'id': questionario_completo.id,
            'titulo': questionario_completo.titulo,
            'descricao': questionario_completo.descricao,
            'secoes': [],
        }
        self._post(client_pesquisador, payload)
        assert Secao.objects.filter(questionario=questionario_completo).count() == 0

    def test_get_retorna_405(self, client_pesquisador):
        response = client_pesquisador.get(reverse('salvar_avaliacao_api'))
        assert response.status_code == 405


# ── configurar_escala_view ───────────────────────────────────────────────────

class TestConfigurarEscalaView:
    def _url(self, questionario_id):
        return reverse('configurar_escala', args=[questionario_id])

    def _post(self, client, questionario_id, data):
        return client.post(
            self._url(questionario_id),
            data=json.dumps(data),
            content_type='application/json',
        )

    def test_anonimo_redireciona(self, client, questionario_simples):
        response = client.get(self._url(questionario_simples.id))
        assert response.status_code == 302

    def test_get_retorna_200(self, client_pesquisador, questionario_simples):
        response = client_pesquisador.get(self._url(questionario_simples.id))
        assert response.status_code == 200

    def test_vincular_escala(self, client_pesquisador, questionario_simples):
        from core.models import EscalaConfig
        escala = EscalaConfig.objects.create(nome='K10 Vinc', strategy_class='K10')

        response = self._post(client_pesquisador, questionario_simples.id, {
            'acao': 'vincular', 'escala_id': escala.id,
        })
        assert response.status_code == 200
        assert response.json()['status'] == 'success'
        assert escala.questionarios.filter(id=questionario_simples.id).exists()

    def test_desvincular_escala(self, client_pesquisador, questionario_simples, escala_k10):
        response = self._post(client_pesquisador, questionario_simples.id, {
            'acao': 'desvincular', 'escala_id': escala_k10.id,
        })
        assert response.status_code == 200
        assert not escala_k10.questionarios.filter(id=questionario_simples.id).exists()

    def test_desativar_escala(self, client_pesquisador, questionario_simples, escala_k10):
        response = self._post(client_pesquisador, questionario_simples.id, {
            'acao': 'desativar', 'escala_id': escala_k10.id,
        })
        assert response.status_code == 200
        escala_k10.refresh_from_db()
        assert escala_k10.ativo is False

    def test_criar_escala_dynamic(self, client_pesquisador, questionario_simples):
        from core.models import EscalaConfig
        response = self._post(client_pesquisador, questionario_simples.id, {
            'nome': 'Escala Criada',
            'strategy_class': 'DYNAMIC',
            'config_dinamica': {'operacao': 'SUM', 'variaveis': ['q1'], 'limiares': []},
        })
        assert response.status_code == 200
        assert EscalaConfig.objects.filter(nome='Escala Criada').exists()

    def test_criar_escala_nativa(self, client_pesquisador, questionario_simples):
        from core.models import EscalaConfig
        response = self._post(client_pesquisador, questionario_simples.id, {
            'nome': 'K10 Nativa',
            'strategy_class': 'K10',
        })
        assert response.status_code == 200
        nova = EscalaConfig.objects.get(nome='K10 Nativa')
        assert nova.strategy_class == 'K10'
        assert nova.config_dinamica is None
