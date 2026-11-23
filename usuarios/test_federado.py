"""Login federado com Google: o retorno do Google é simulado, sem rede."""
from unittest import mock
from urllib.parse import parse_qs, urlparse

from django.test import TestCase, override_settings

from usuarios.models import Usuario

GOOGLE_DE_TESTE = {
    'google': {
        'APPS': [{'client_id': 'id-de-teste', 'secret': 'segredo-de-teste'}],
        'SCOPE': ['openid', 'profile', 'email'],
    },
}


@override_settings(SOCIALACCOUNT_PROVIDERS=GOOGLE_DE_TESTE)
class LoginGoogleTests(TestCase):

    def entrar_com_google(self, email, sub='google-123', nome='Pessoa do Google', proximo=None):
        """Faz o caminho completo: botão, ida ao Google e volta pelo callback."""
        url = '/accounts/google/login/' + (f'?next={proximo}' if proximo else '')
        ida = self.client.post(url)
        state = parse_qs(urlparse(ida.url).query)['state'][0]
        dados = {'sub': sub, 'email': email, 'email_verified': True, 'name': nome}
        with mock.patch('allauth.socialaccount.providers.oauth2.client.OAuth2Client.get_access_token',
                        return_value={'access_token': 'token', 'id_token': 'jwt'}), \
             mock.patch('allauth.socialaccount.providers.google.views.GoogleOAuth2Adapter._decode_id_token',
                        return_value=dados):
            return self.client.get('/accounts/google/login/callback/', {'code': 'c', 'state': state})

    def test_conta_existente_entra_e_mantem_a_senha(self):
        conta = Usuario.objects.create_user('ana@x.com', 'Ana', 'senha12345',
                                            papel=Usuario.Papel.EMPREENDEDOR)
        resposta = self.entrar_com_google('ana@x.com')
        self.assertEqual(resposta.status_code, 302)
        self.assertEqual(int(self.client.session['_auth_user_id']), conta.pk)
        conta.refresh_from_db()
        self.assertTrue(conta.check_password('senha12345'))

    def test_email_novo_vira_cadastro_desativado(self):
        resposta = self.entrar_com_google('nova@x.com', nome='Nova Pessoa')
        conta = Usuario.objects.get(email='nova@x.com')
        self.assertEqual(conta.papel, Usuario.Papel.EMPREENDEDOR)
        self.assertEqual(conta.nome, 'Nova Pessoa')
        self.assertFalse(conta.is_active)
        self.assertFalse(conta.has_usable_password())
        self.assertNotIn('_auth_user_id', self.client.session)
        self.assertEqual(resposta.url, '/login/')

    def test_cadastro_pendente_nao_duplica_nem_entra(self):
        self.entrar_com_google('nova@x.com')
        self.entrar_com_google('nova@x.com')
        self.assertEqual(Usuario.objects.filter(email='nova@x.com').count(), 1)
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_conta_desativada_nao_entra(self):
        Usuario.objects.create_user('inativo@x.com', 'Inativo', 'senha12345',
                                    papel=Usuario.Papel.EMPREENDEDOR, is_active=False)
        self.entrar_com_google('inativo@x.com')
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_is_e_professor_nao_entram_pelo_google(self):
        for papel in (Usuario.Papel.IS, Usuario.Papel.PROFESSOR, Usuario.Papel.ADMIN):
            with self.subTest(papel=papel):
                self.client.logout()
                Usuario.objects.create_user(f'{papel}@x.com', papel, 'senha12345', papel=papel)
                self.entrar_com_google(f'{papel}@x.com', sub=f'sub-{papel}')
                self.assertNotIn('_auth_user_id', self.client.session)

    def test_next_e_respeitado(self):
        Usuario.objects.create_user('bia@x.com', 'Bia', 'senha12345', papel=Usuario.Papel.EMPREENDEDOR)
        resposta = self.entrar_com_google('bia@x.com', proximo='/trilhas/')
        self.assertEqual(resposta.url, '/trilhas/')

    def test_cookie_de_ultimo_metodo(self):
        Usuario.objects.create_user('cris@x.com', 'Cris', 'senha12345', papel=Usuario.Papel.EMPREENDEDOR)
        resposta = self.entrar_com_google('cris@x.com')
        self.assertEqual(resposta.cookies['sgis_ultimo_login'].value, 'google')


class RotasDoAllauthTests(TestCase):

    def setUp(self):
        self.conta = Usuario.objects.create_user('ana@x.com', 'Ana', 'senha12345',
                                                 papel=Usuario.Papel.EMPREENDEDOR)

    def test_rotas_desligadas_nao_respondem(self):
        self.client.force_login(self.conta)
        for url in ('/accounts/password/reset/', '/accounts/password/change/',
                    '/accounts/password/set/', '/accounts/email/', '/accounts/3rdparty/'):
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url).status_code, 404)

    def test_reset_de_senha_anonimo_vai_ao_login(self):
        resposta = self.client.get('/accounts/password/reset/')
        self.assertEqual(resposta.status_code, 302)
        self.assertTrue(resposta.url.startswith('/login/'))

    @override_settings(SOCIALACCOUNT_PROVIDERS={'google': {'APPS': []}})
    def test_google_sem_credenciais_da_404_e_nao_500(self):
        self.assertEqual(self.client.get('/accounts/google/login/').status_code, 302)  # anônimo → login
        self.client.force_login(self.conta)
        self.assertEqual(self.client.get('/accounts/google/login/').status_code, 404)
        self.assertEqual(self.client.post('/accounts/google/login/').status_code, 404)
