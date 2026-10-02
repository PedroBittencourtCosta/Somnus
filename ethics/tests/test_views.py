import pytest
from django.urls import reverse

pytestmark = pytest.mark.django_db


# ── aceitar_tcle ─────────────────────────────────────────────────────────────

class TestAceitarTcle:
    def test_anonimo_redireciona_para_login(self, client, tcle_ativo):
        url = reverse('aceitar_tcle', args=[tcle_ativo.id])
        response = client.get(url)
        assert response.status_code == 302
        assert '/login/' in response['Location']

    def test_get_autenticado_redireciona_para_home(self, client_pesquisador, tcle_ativo):
        url = reverse('aceitar_tcle', args=[tcle_ativo.id])
        response = client_pesquisador.get(url)
        assert response.status_code == 302
        assert response['Location'] == reverse('home')

    def test_post_marca_sessao_tcle_aceito(self, client_pesquisador, tcle_ativo):
        url = reverse('aceitar_tcle', args=[tcle_ativo.id])
        client_pesquisador.post(url)
        assert client_pesquisador.session.get('tcle_aceito') is True

    def test_post_sem_referer_redireciona_para_home(self, client_pesquisador, tcle_ativo):
        url = reverse('aceitar_tcle', args=[tcle_ativo.id])
        response = client_pesquisador.post(url)
        assert response.status_code == 302
        assert response['Location'] == reverse('home')

    def test_post_com_referer_redireciona_para_referer(self, client_pesquisador, tcle_ativo):
        url = reverse('aceitar_tcle', args=[tcle_ativo.id])
        response = client_pesquisador.post(url, HTTP_REFERER='/pagina-origem/')
        assert response.status_code == 302
        assert response['Location'] == '/pagina-origem/'


# ── lista_tcle ───────────────────────────────────────────────────────────────

class TestListaTcle:
    def test_anonimo_redireciona_para_login(self, client):
        response = client.get(reverse('lista_tcle'))
        assert response.status_code == 302
        assert '/login/' in response['Location']

    def test_assistente_sem_permissao_redireciona(self, client_assistente):
        response = client_assistente.get(reverse('lista_tcle'))
        assert response.status_code == 302
        assert response['Location'] == reverse('home')

    def test_pesquisador_retorna_200(self, client_pesquisador):
        response = client_pesquisador.get(reverse('lista_tcle'))
        assert response.status_code == 200

    def test_lista_ordenada_do_mais_recente(self, client_pesquisador, tcle_ativo):
        from ethics.models import TCLE
        from django.utils import timezone
        import datetime

        tcle2 = TCLE.objects.create(conteudo='Versão mais recente', versao=2.0)
        # Garante timestamp mais antigo para tcle_ativo (criados rapidamente podem ter igual)
        TCLE.objects.filter(id=tcle_ativo.id).update(
            data_criacao=timezone.now() - datetime.timedelta(seconds=10)
        )

        response = client_pesquisador.get(reverse('lista_tcle'))
        tcles = list(response.context['tcles'])
        assert tcles[0] == tcle2


# ── nova_versao_tcle ─────────────────────────────────────────────────────────

class TestNovaVersaoTcle:
    def test_anonimo_redireciona(self, client):
        response = client.get(reverse('nova_versao_tcle'))
        assert response.status_code == 302

    def test_assistente_sem_permissao_redireciona(self, client_assistente):
        response = client_assistente.get(reverse('nova_versao_tcle'))
        assert response.status_code == 302
        assert response['Location'] == reverse('home')

    def test_pesquisador_get_retorna_200(self, client_pesquisador):
        response = client_pesquisador.get(reverse('nova_versao_tcle'))
        assert response.status_code == 200

    def test_get_sem_tcle_sugere_versao_1(self, client_pesquisador):
        response = client_pesquisador.get(reverse('nova_versao_tcle'))
        assert response.context['versao'] == 1.0

    def test_get_com_tcle_sugere_proxima_versao(self, client_pesquisador, tcle_ativo):
        # tcle_ativo has versao=1.0 → next should be 2.0
        response = client_pesquisador.get(reverse('nova_versao_tcle'))
        assert response.context['versao'] == 2.0

    def test_post_conteudo_vazio_nao_cria_tcle(self, client_pesquisador):
        from ethics.models import TCLE
        count_antes = TCLE.objects.count()
        client_pesquisador.post(reverse('nova_versao_tcle'), {
            'conteudo': '',
            'versao': '1.0',
        })
        assert TCLE.objects.count() == count_antes

    def test_post_versao_invalida_nao_cria_tcle(self, client_pesquisador):
        from ethics.models import TCLE
        count_antes = TCLE.objects.count()
        client_pesquisador.post(reverse('nova_versao_tcle'), {
            'conteudo': 'Conteúdo válido',
            'versao': 'abc',
        })
        assert TCLE.objects.count() == count_antes

    def test_post_versao_duplicada_nao_cria_tcle(self, client_pesquisador, tcle_ativo):
        from ethics.models import TCLE
        count_antes = TCLE.objects.count()
        client_pesquisador.post(reverse('nova_versao_tcle'), {
            'conteudo': 'Conteúdo novo',
            'versao': '1.0',   # tcle_ativo já tem versao=1.0
        })
        assert TCLE.objects.count() == count_antes

    def test_post_valido_cria_tcle(self, client_pesquisador):
        from ethics.models import TCLE
        client_pesquisador.post(reverse('nova_versao_tcle'), {
            'conteudo': 'Novo conteúdo TCLE',
            'versao': '3.5',
        })
        assert TCLE.objects.filter(versao=3.5).exists()

    def test_post_valido_redireciona_para_lista_tcle(self, client_pesquisador):
        response = client_pesquisador.post(reverse('nova_versao_tcle'), {
            'conteudo': 'Conteúdo',
            'versao': '4.0',
        })
        assert response.status_code == 302
        assert response['Location'] == reverse('lista_tcle')


# ── revogar_consentimento ───────────────────────────────────────────────────

class TestRevogarConsentimento:
    def test_anonimo_redireciona_para_login(self, client):
        response = client.get(reverse('revogar_consentimento'))
        assert response.status_code == 302
        assert '/login/' in response['Location']

    def test_assistente_sem_acesso(self, client_assistente):
        response = client_assistente.get(reverse('revogar_consentimento'))
        assert response.status_code == 302
        assert response['Location'] == reverse('home')

    def test_assistente_nao_consegue_excluir(self, client_assistente, resposta_completa):
        from core.models import RespostaQuestionario
        client_assistente.post(reverse('revogar_consentimento'), {'codigo': resposta_completa.codigo_paciente})
        assert RespostaQuestionario.objects.filter(pk=resposta_completa.pk).exists()

    def test_get_sem_codigo_renderiza(self, client_pesquisador):
        response = client_pesquisador.get(reverse('revogar_consentimento'))
        assert response.status_code == 200
        assert response.context['resposta'] is None

    def test_busca_encontra_coleta(self, client_pesquisador, resposta_completa):
        response = client_pesquisador.get(
            reverse('revogar_consentimento'), {'codigo': resposta_completa.codigo_paciente.lower()}
        )
        assert response.context['resposta'] == resposta_completa
        assert response.context['total_respostas'] == 1

    def test_busca_codigo_inexistente(self, client_pesquisador):
        response = client_pesquisador.get(reverse('revogar_consentimento'), {'codigo': 'NAOEXISTE'})
        assert response.status_code == 200
        assert response.context['resposta'] is None
        assert 'Nenhuma coleta encontrada' in response.content.decode()

    def test_resumo_nao_exibe_nome_do_participante(self, client_pesquisador, resposta_completa):
        response = client_pesquisador.get(
            reverse('revogar_consentimento'), {'codigo': resposta_completa.codigo_paciente}
        )
        assert 'Paciente Teste' not in response.content.decode()

    def test_post_exclui_coleta_e_dependentes(self, client_pesquisador, resposta_completa, tcle_ativo):
        from core.models import RespostaQuestionario, RespostaPergunta
        from ethics.models import AceiteTCLE
        AceiteTCLE.objects.create(resposta_questionario=resposta_completa, tcle=tcle_ativo)

        client_pesquisador.post(reverse('revogar_consentimento'), {'codigo': resposta_completa.codigo_paciente})

        assert not RespostaQuestionario.objects.filter(pk=resposta_completa.pk).exists()
        assert not RespostaPergunta.objects.filter(resposta_questionario_id=resposta_completa.pk).exists()
        assert not AceiteTCLE.objects.filter(resposta_questionario_id=resposta_completa.pk).exists()

    def test_post_registra_revogacao(self, client_pesquisador, usuario_pesquisador, resposta_completa, tcle_ativo):
        from ethics.models import AceiteTCLE, RevogacaoConsentimento
        AceiteTCLE.objects.create(resposta_questionario=resposta_completa, tcle=tcle_ativo)
        codigo = resposta_completa.codigo_paciente

        client_pesquisador.post(reverse('revogar_consentimento'), {'codigo': codigo})

        revogacao = RevogacaoConsentimento.objects.get(codigo_paciente=codigo)
        assert revogacao.revogado_por == usuario_pesquisador
        assert revogacao.tcle_versao == 1.0
        assert revogacao.questionario_titulo == resposta_completa.questionario.titulo

    def test_post_redireciona_para_tela(self, client_pesquisador, resposta_completa):
        response = client_pesquisador.post(
            reverse('revogar_consentimento'), {'codigo': resposta_completa.codigo_paciente}
        )
        assert response.status_code == 302
        assert response['Location'] == reverse('revogar_consentimento')

    def test_post_codigo_inexistente_nao_registra(self, client_pesquisador):
        from ethics.models import RevogacaoConsentimento
        client_pesquisador.post(reverse('revogar_consentimento'), {'codigo': 'NAOEXISTE'})
        assert not RevogacaoConsentimento.objects.exists()

    def test_historico_lista_revogacoes(self, client_pesquisador, resposta_completa):
        codigo = resposta_completa.codigo_paciente
        client_pesquisador.post(reverse('revogar_consentimento'), {'codigo': codigo})
        response = client_pesquisador.get(reverse('revogar_consentimento'))
        assert codigo in response.content.decode()
