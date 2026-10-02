from django.urls import reverse, resolve
from core import views


class TestCoreUrls:
    def test_lista_questionarios(self):
        url = reverse('lista_questionarios')
        assert url == '/questionario/avaliacoes/'
        assert resolve(url).view_name == 'lista_questionarios'

    def test_gerenciar_questionarios(self):
        url = reverse('gerenciar_questionarios')
        assert url == '/questionario/avaliacoes/gerenciar/'
        assert resolve(url).view_name == 'gerenciar_questionarios'

    def test_nova_avaliacao(self):
        url = reverse('nova_avaliacao')
        assert url == '/questionario/avaliacoes/nova/'
        assert resolve(url).view_name == 'nova_avaliacao'

    def test_editar_avaliacao(self):
        url = reverse('editar_avaliacao', args=[42])
        assert url == '/questionario/avaliacoes/42/editar/'
        assert resolve(url).view_name == 'editar_avaliacao'

    def test_configurar_escala(self):
        url = reverse('configurar_escala', args=[1])
        assert url == '/questionario/avaliacoes/1/escala/'
        assert resolve(url).view_name == 'configurar_escala'

    def test_desativar_questionario(self):
        url = reverse('desativar_questionario', args=[5])
        assert url == '/questionario/avaliacoes/5/desativar/'
        assert resolve(url).view_name == 'desativar_questionario'

    def test_responder_questionario(self):
        url = reverse('responder_questionario', args=[7])
        assert url == '/questionario/responder/7/'
        assert resolve(url).view_name == 'responder_questionario'

    def test_salvar_avaliacao_api(self):
        url = reverse('salvar_avaliacao_api')
        assert url == '/questionario/api/avaliacoes/salvar/'
        assert resolve(url).view_name == 'salvar_avaliacao_api'

    def test_dashboard_respostas(self):
        url = reverse('dashboard_respostas')
        assert url == '/questionario/dashboard/'
        assert resolve(url).view_name == 'dashboard_respostas'

    def test_recalcular_escalas(self):
        url = reverse('recalcular_escalas')
        assert url == '/questionario/dashboard/recalcular/'
        assert resolve(url).view_name == 'recalcular_escalas'

    def test_relatorios_medicos(self):
        url = reverse('relatorios_medicos')
        assert url == '/questionario/relatorios/'
        assert resolve(url).view_name == 'relatorios_medicos'

    def test_exportar_respostas_excel(self):
        url = reverse('exportar_respostas_excel', args=[3])
        assert url == '/questionario/exportar-excel/3/'
        assert resolve(url).view_name == 'exportar_respostas_excel'

    def test_exportar_resultados_massa_excel(self):
        url = reverse('exportar_resultados_massa_excel')
        assert url == '/questionario/exportar-resultados-massa/'
        assert resolve(url).view_name == 'exportar_resultados_massa_excel'
