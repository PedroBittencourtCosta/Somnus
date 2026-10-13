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

    def _pergunta(self, conteudo, temp_id, alternativas=(), **extra):
        return {
            'temp_id': temp_id,
            'conteudo': conteudo,
            'tipo': 'MC' if alternativas else 'TX',
            'identificador': temp_id,
            'alternativas': list(alternativas),
            **extra,
        }

    def test_resolve_dependencias_por_ids_temporarios(self, client_pesquisador):
        """O frontend ainda não conhece os IDs reais: as dependências chegam com temp_id."""
        from core.models import Pergunta
        payload = self._payload('Q Dependências', secoes=[{
            'titulo': 'Triagem',
            'perguntas': [
                self._pergunta('Fuma?', 'fuma', alternativas=[
                    {'temp_id': 'alt_sim', 'conteudo': 'Sim', 'valor': '1'},
                    {'temp_id': 'alt_nao', 'conteudo': 'Não', 'valor': '0'},
                ]),
                self._pergunta('Quantos cigarros por dia?', 'cigarros', depende_de_alternativa_ids=['alt_sim']),
                self._pergunta('Qual marca?', 'marca', depende_de_texto_de_id='cigarros'),
            ],
        }])

        response = self._post(client_pesquisador, payload)
        assert response.json()['status'] == 'success'

        fuma = Pergunta.objects.get(identificador='fuma')
        cigarros = Pergunta.objects.get(identificador='cigarros')
        marca = Pergunta.objects.get(identificador='marca')
        alt_sim = fuma.alternativas.get(conteudo='Sim')
        assert list(cigarros.depende_de_alternativa.all()) == [alt_sim]
        assert marca.depende_de_texto_de == cigarros
        assert fuma.depende_de_texto_de is None

    def test_valor_de_alternativa_nao_numerico_vira_zero(self, client_pesquisador):
        from core.models import Alternativa
        payload = self._payload('Q Valores', secoes=[{
            'titulo': 'S',
            'perguntas': [self._pergunta('P', 'p', alternativas=[{'conteudo': 'Talvez', 'valor': 'abc'}])],
        }])
        self._post(client_pesquisador, payload)
        assert Alternativa.objects.get(conteudo='Talvez').valor == 0

    def test_dependencia_de_texto_inexistente_e_descartada(self, client_pesquisador):
        from core.models import Pergunta
        payload = self._payload('Q Dep Órfã', secoes=[{
            'titulo': 'S',
            'perguntas': [self._pergunta('P', 'p', depende_de_texto_de_id='temp_removida')],
        }])
        self._post(client_pesquisador, payload)
        assert Pergunta.objects.get(identificador='p').depende_de_texto_de is None

    def test_atualiza_registros_existentes_sem_duplicar(self, client_pesquisador, questionario_completo):
        from core.models import Secao, Pergunta, Alternativa
        secao = Secao.objects.get(questionario=questionario_completo, ordem=2)
        pergunta = Pergunta.objects.get(identificador='k10a')
        alternativa = pergunta.alternativas.get(valor=1)
        outra_alternativa = pergunta.alternativas.get(valor=2)

        payload = {
            'id': questionario_completo.id,
            'titulo': questionario_completo.titulo,
            'secoes': [{
                'id': secao.id,
                'titulo': 'K10 revisada',
                'layout': 'TABELA',
                'perguntas': [{
                    'id': pergunta.id,
                    'conteudo': 'Texto revisado',
                    'tipo': 'MC',
                    'identificador': 'k10a',
                    'alternativas': [
                        {'id': alternativa.id, 'conteudo': 'Nunca (revisado)', 'valor': 1},
                        {'id': outra_alternativa.id, 'conteudo': 'Raramente', 'valor': 2},
                    ],
                    'depende_de_alternativa_ids': [],
                }],
            }],
        }
        response = self._post(client_pesquisador, payload)
        assert response.json()['status'] == 'success'

        secao.refresh_from_db()
        pergunta.refresh_from_db()
        alternativa.refresh_from_db()
        assert secao.titulo == 'K10 revisada'
        assert secao.ordem == 1   # passou a ser a primeira seção do payload
        assert pergunta.conteudo == 'Texto revisado'
        assert alternativa.conteudo == 'Nunca (revisado)'
        # Itens fora do payload foram removidos: seção 'Dados Demográficos' e 3 alternativas
        assert Secao.objects.filter(questionario=questionario_completo).count() == 1
        assert Alternativa.objects.filter(pergunta=pergunta).count() == 2

    def test_erro_no_meio_do_salvamento_desfaz_tudo(self, client_pesquisador, questionario_simples, questionario_completo):
        """Seção de outro questionário no payload → erro e rollback da transação."""
        from core.models import Secao
        secao_alheia = Secao.objects.filter(questionario=questionario_completo).first()
        payload = {
            'id': questionario_simples.id,
            'titulo': 'Não deveria salvar',
            'secoes': [{'id': secao_alheia.id, 'titulo': 'Invasão', 'perguntas': []}],
        }

        response = self._post(client_pesquisador, payload)

        assert response.status_code == 400
        questionario_simples.refresh_from_db()
        secao_alheia.refresh_from_db()
        assert questionario_simples.titulo == 'Questionário de Teste'
        assert secao_alheia.titulo != 'Invasão'

    def test_json_invalido_retorna_400_sem_detalhes_internos(self, client_pesquisador):
        response = client_pesquisador.post(
            reverse('salvar_avaliacao_api'), data='{quebrado', content_type='application/json',
        )
        assert response.status_code == 400
        data = response.json()
        assert data['status'] == 'error'
        assert 'trace' not in data
        assert 'Traceback' not in response.content.decode()


# ── editar_questionario_view ─────────────────────────────────────────────────

class TestEditarQuestionarioView:
    def test_novo_questionario_comeca_vazio(self, client_pesquisador):
        response = client_pesquisador.get(reverse('nova_avaliacao'))
        assert response.status_code == 200
        assert response.context['questionario'] is None
        assert response.context['questionario_json'] == '{}'

    def test_edicao_carrega_estrutura_completa(self, client_pesquisador, questionario_completo):
        from core.models import Pergunta, Secao
        k10a = Pergunta.objects.get(identificador='k10a')
        dependente = Pergunta.objects.create(
            secao=Secao.objects.get(questionario=questionario_completo, ordem=2),
            conteudo='Desde quando?', tipo='TX', ordem=2, identificador='desde',
            depende_de_texto_de=Pergunta.objects.get(identificador='idade'),
        )
        dependente.depende_de_alternativa.add(k10a.alternativas.get(valor=5))

        response = client_pesquisador.get(reverse('editar_avaliacao', args=[questionario_completo.id]))
        dados = json.loads(response.context['questionario_json'])

        assert dados['titulo'] == questionario_completo.titulo
        assert [s['titulo'] for s in dados['secoes']] == ['Dados Demográficos', 'Escala K10']
        perguntas_k10 = dados['secoes'][1]['perguntas']
        assert [p['identificador'] for p in perguntas_k10] == ['k10a', 'desde']
        assert [a['valor'] for a in perguntas_k10[0]['alternativas']] == [1, 2, 3, 4, 5]
        assert perguntas_k10[1]['depende_de_alternativa_ids'] == [k10a.alternativas.get(valor=5).id]
        assert perguntas_k10[1]['depende_de_texto_de_id'] == Pergunta.objects.get(identificador='idade').id

    def test_questionario_inexistente_retorna_404(self, client_pesquisador):
        assert client_pesquisador.get(reverse('editar_avaliacao', args=[99999])).status_code == 404


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

    def test_edita_escala_existente(self, client_pesquisador, questionario_simples, escala_k10):
        response = self._post(client_pesquisador, questionario_simples.id, {
            'escala_id': escala_k10.id,
            'nome': 'K10 Renomeada',
            'strategy_class': 'K10',
        })
        assert response.status_code == 200
        escala_k10.refresh_from_db()
        assert escala_k10.nome == 'K10 Renomeada'

    def test_vincular_escala_inexistente_retorna_404(self, client_pesquisador, questionario_simples):
        response = self._post(client_pesquisador, questionario_simples.id, {
            'acao': 'vincular', 'escala_id': 99999,
        })
        assert response.status_code == 404

    def test_corpo_invalido_retorna_400_sem_detalhes_internos(self, client_pesquisador, questionario_simples):
        response = client_pesquisador.post(
            self._url(questionario_simples.id), data='nao-e-json', content_type='application/json',
        )
        assert response.status_code == 400
        assert 'trace' not in response.json()

    def test_get_lista_variaveis_e_escalas_ativas(self, client_pesquisador, questionario_completo, escala_k10):
        from core.models import EscalaConfig
        EscalaConfig.objects.create(nome='Outra', strategy_class='ESE')
        EscalaConfig.objects.create(nome='Desativada', strategy_class='AUDIT', ativo=False)

        response = client_pesquisador.get(self._url(questionario_completo.id))

        variaveis = {p['identificador'] for p in json.loads(response.context['perguntas_json'])}
        assert variaveis == {'idade', 'k10a'}
        escalas = {e['nome']: e for e in json.loads(response.context['escalas_templates_json'])}
        assert set(escalas) == {'K10', 'Outra'}
        assert escalas['K10']['is_linked'] is True
        assert escalas['Outra']['is_linked'] is False
