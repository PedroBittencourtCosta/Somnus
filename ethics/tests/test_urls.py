from django.urls import reverse, resolve
from ethics import views


class TestEthicsUrls:
    def test_aceitar_tcle(self):
        url = reverse('aceitar_tcle', args=[1])
        assert url == '/tcle/aceitar/1/'
        assert resolve(url).view_name == 'aceitar_tcle'

    def test_lista_tcle(self):
        url = reverse('lista_tcle')
        assert url == '/tcle/gerenciar/'
        assert resolve(url).view_name == 'lista_tcle'

    def test_nova_versao_tcle(self):
        url = reverse('nova_versao_tcle')
        assert url == '/tcle/gerenciar/nova-versao/'
        assert resolve(url).view_name == 'nova_versao_tcle'

    def test_revogar_consentimento(self):
        url = reverse('revogar_consentimento')
        assert url == '/tcle/revogacao/'
        assert resolve(url).view_name == 'revogar_consentimento'
