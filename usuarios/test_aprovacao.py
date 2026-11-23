"""IS aprova o cadastro feito pelo Google, criando o empreendimento da pessoa."""
from django.test import TestCase, override_settings
from django.urls import reverse

from trilhas.models import Inscricao
from usuarios.models import Usuario
from usuarios.test_federado import GOOGLE_DE_TESTE, LoginGoogleTests

EMPREENDIMENTO = {'nome': 'Ateliê Novo', 'tipo': 'Artesanato', 'descricao': ''}


@override_settings(SOCIALACCOUNT_PROVIDERS=GOOGLE_DE_TESTE)
class AprovacaoTests(TestCase):
    entrar_com_google = LoginGoogleTests.entrar_com_google

    def setUp(self):
        self.is_ = Usuario.objects.create_user('is-a@x.com', 'IS', 'senha12345', papel=Usuario.Papel.IS)
        self.entrar_com_google('nova@x.com', nome='Nova Pessoa')
        self.pendente = Usuario.objects.get(email='nova@x.com')
        self.client.force_login(self.is_)

    def test_pendente_aparece_com_selo_e_no_filtro(self):
        Usuario.objects.create_user('off@x.com', 'Desligada', 'senha12345',
                                    papel=Usuario.Papel.EMPREENDEDOR, is_active=False)
        pagina = self.client.get(reverse('contas')).content.decode()
        self.assertIn('Aguardando aprovação</span>', pagina)
        self.assertIn(reverse('aprovar_cadastro', args=[self.pendente.pk]), pagina)

        filtrada = self.client.get(reverse('contas'), {'status': 'pendente'})
        self.assertEqual([c.email for c in filtrada.context['contas']], ['nova@x.com'])

    def test_aprovar_cria_empreendimento_reativa_e_inscreve(self):
        resposta = self.client.post(reverse('aprovar_cadastro', args=[self.pendente.pk]), EMPREENDIMENTO)
        self.assertRedirects(resposta, reverse('contas'), fetch_redirect_response=False)
        self.pendente.refresh_from_db()
        self.assertTrue(self.pendente.is_active)
        empreendimento = self.pendente.empreendimentos.get()
        self.assertEqual(empreendimento.nome, 'Ateliê Novo')
        self.assertTrue(Inscricao.objects.filter(empreendimento=empreendimento).exists())

        # Saiu da fila e a pessoa entra pelo Google
        self.assertFalse(self.client.get(reverse('contas'), {'status': 'pendente'}).context['contas'])
        self.client.logout()
        self.entrar_com_google('nova@x.com', nome='Nova Pessoa')
        self.assertEqual(int(self.client.session['_auth_user_id']), self.pendente.pk)

    def test_formulario_invalido_nao_aprova(self):
        resposta = self.client.post(reverse('aprovar_cadastro', args=[self.pendente.pk]), {'nome': ''})
        self.assertEqual(resposta.status_code, 200)
        self.assertTrue(resposta.context['form'].has_error('nome'))
        self.pendente.refresh_from_db()
        self.assertFalse(self.pendente.is_active)

    def test_conta_desativada_de_proposito_nao_e_aprovada(self):
        conta = Usuario.objects.create_user('off@x.com', 'Desligada', 'senha12345',
                                            papel=Usuario.Papel.EMPREENDEDOR, is_active=False)
        resposta = self.client.post(reverse('aprovar_cadastro', args=[conta.pk]), EMPREENDIMENTO)
        self.assertRedirects(resposta, reverse('contas'), fetch_redirect_response=False)
        conta.refresh_from_db()
        self.assertFalse(conta.is_active)
        self.assertFalse(conta.empreendimentos.exists())

    def test_aprovacao_negada_a_professor_e_empreendedor(self):
        for papel in (Usuario.Papel.PROFESSOR, Usuario.Papel.EMPREENDEDOR):
            with self.subTest(papel=papel):
                outro = Usuario.objects.create_user(f'{papel}-n@x.com', papel, 'senha12345', papel=papel)
                self.client.force_login(outro)
                url = reverse('aprovar_cadastro', args=[self.pendente.pk])
                self.assertEqual(self.client.get(url).status_code, 403)
                self.assertEqual(self.client.post(url, EMPREENDIMENTO).status_code, 403)
        self.pendente.refresh_from_db()
        self.assertFalse(self.pendente.is_active)
