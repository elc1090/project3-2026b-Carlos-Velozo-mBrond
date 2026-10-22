from django.test import TestCase
from django.urls import reverse

from .models import Usuario

URL = reverse('criar_usuario')


def criar_is():
    return Usuario.objects.create_user(
        'is-teste@sgis.com', 'Incubadora', 'senha12345', papel=Usuario.Papel.IS,
    )


def dados(**extra):
    """POST válido para criar um professor; `extra` sobrescreve campos."""
    return {
        'nome': 'Maria das Trilhas',
        'email': 'maria@escola.com',
        'papel': Usuario.Papel.PROFESSOR,
        'senha': 'senha-super-segura',
        **extra,
    }


class CriarUsuarioPermissaoTests(TestCase):
    """Só a IS cria usuários."""

    def test_anonimo_e_redirecionado_para_login(self):
        resposta = self.client.get(URL)
        self.assertRedirects(resposta, f"{reverse('login')}?next={URL}")

    def test_papel_diferente_de_is_recebe_403(self):
        for papel in (Usuario.Papel.PROFESSOR, Usuario.Papel.EMPREENDEDOR, Usuario.Papel.ADMIN):
            with self.subTest(papel=papel):
                usuario = Usuario.objects.create_user(
                    f'{papel}@sgis.com', 'Teste', 'senha12345', papel=papel,
                )
                self.client.force_login(usuario)
                self.assertEqual(self.client.get(URL).status_code, 403)
                self.assertEqual(self.client.post(URL, dados()).status_code, 403)
                self.client.logout()
        self.assertFalse(Usuario.objects.filter(email='maria@escola.com').exists())


class CriarUsuarioTests(TestCase):
    def setUp(self):
        self.client.force_login(criar_is())

    def test_is_cria_professor_e_ele_consegue_logar(self):
        resposta = self.client.post(URL, dados())

        self.assertRedirects(resposta, URL)
        usuario = Usuario.objects.get(email='maria@escola.com')
        self.assertEqual(usuario.nome, 'Maria das Trilhas')
        self.assertEqual(usuario.papel, Usuario.Papel.PROFESSOR)
        self.assertTrue(usuario.check_password('senha-super-segura'))
        self.assertNotEqual(usuario.password, 'senha-super-segura')  # salva com hash

        self.client.logout()
        self.assertTrue(self.client.login(email='maria@escola.com', password='senha-super-segura'))

    def test_is_cria_empreendedor(self):
        resposta = self.client.post(URL, dados(
            nome='Ateliê da Praça', email='contato@atelie.com', papel=Usuario.Papel.EMPREENDEDOR,
        ))

        self.assertRedirects(resposta, URL)
        usuario = Usuario.objects.get(email='contato@atelie.com')
        self.assertEqual(usuario.papel, Usuario.Papel.EMPREENDEDOR)

    def test_is_nao_consegue_criar_is_ou_admin(self):
        """Mesmo enviando o papel direto no POST, a validação bloqueia."""
        for papel in (Usuario.Papel.IS, Usuario.Papel.ADMIN):
            with self.subTest(papel=papel):
                email = f'forjado-{papel}@sgis.com'
                resposta = self.client.post(URL, dados(email=email, papel=papel))
                self.assertEqual(resposta.status_code, 200)  # re-renderiza o form
                self.assertTrue(resposta.context['form'].has_error('papel', 'invalid_choice'))
                self.assertFalse(Usuario.objects.filter(email=email).exists())


class CriarUsuarioEmailTests(TestCase):
    def setUp(self):
        self.client.force_login(criar_is())

    def criar_maria(self):
        Usuario.objects.create_user(
            'maria@escola.com', 'Maria', 'senha12345', papel=Usuario.Papel.PROFESSOR,
        )

    def test_email_duplicado_e_recusado(self):
        self.criar_maria()
        resposta = self.client.post(URL, dados(nome='Outra Maria'))

        self.assertEqual(resposta.status_code, 200)
        self.assertTrue(resposta.context['form'].has_error('email'))
        self.assertEqual(Usuario.objects.filter(email__iexact='maria@escola.com').count(), 1)

    def test_email_duplicado_com_maiusculas_e_recusado(self):
        self.criar_maria()
        resposta = self.client.post(URL, dados(email='Maria@ESCOLA.com'))

        self.assertTrue(resposta.context['form'].has_error('email'))
        self.assertEqual(Usuario.objects.filter(email__iexact='maria@escola.com').count(), 1)

    def test_email_salvo_em_minusculas(self):
        self.client.post(URL, dados(email='  Maria@Escola.com '))
        self.assertTrue(Usuario.objects.filter(email='maria@escola.com').exists())

    def test_login_aceita_email_com_maiusculas(self):
        self.client.post(URL, dados())
        self.client.logout()

        resposta = self.client.post(reverse('login'), {
            'email': 'Maria@Escola.com', 'senha': 'senha-super-segura',
        })
        self.assertRedirects(resposta, reverse('home'))


class CriarUsuarioSenhaTests(TestCase):
    """A senha passa pelos AUTH_PASSWORD_VALIDATORS do settings."""

    def setUp(self):
        self.client.force_login(criar_is())

    def assert_senha_recusada(self, senha, **extra):
        resposta = self.client.post(URL, dados(senha=senha, **extra))
        self.assertEqual(resposta.status_code, 200)
        self.assertTrue(resposta.context['form'].has_error('senha'))
        self.assertFalse(Usuario.objects.filter(email=dados(**extra)['email']).exists())

    def test_senha_curta_e_recusada(self):
        self.assert_senha_recusada('Ab1!x')

    def test_senha_comum_e_recusada(self):
        for senha in ('password', 'qwertyuiop'):
            with self.subTest(senha=senha):
                self.assert_senha_recusada(senha)

    def test_senha_so_numerica_e_recusada(self):
        self.assert_senha_recusada('83920571946')

    def test_senha_parecida_com_o_email_e_recusada(self):
        self.assert_senha_recusada('mariadastrilhas', email='mariadastrilhas@escola.com')

    def test_senha_em_branco_e_recusada(self):
        self.assert_senha_recusada('        ')


URL_TROCAR_SENHA = reverse('trocar_senha')


class TrocarSenhaTests(TestCase):
    """Usuário logado troca a própria senha (MVP-ACE-10)."""

    def setUp(self):
        self.usuario = Usuario.objects.create_user(
            'maria@escola.com', 'Maria das Trilhas', 'senha-antiga-123',
            papel=Usuario.Papel.PROFESSOR,
        )
        self.client.force_login(self.usuario)

    def dados(self, **extra):
        """POST válido para trocar a senha; `extra` sobrescreve campos."""
        return {
            'senha_atual': 'senha-antiga-123',
            'nova_senha': 'nova-senha-forte-456',
            'confirmar_nova_senha': 'nova-senha-forte-456',
            **extra,
        }

    def test_exige_login(self):
        self.client.logout()
        resposta = self.client.get(URL_TROCAR_SENHA)
        self.assertRedirects(resposta, f"{reverse('login')}?next={URL_TROCAR_SENHA}")

    def test_todos_os_papeis_acessam_a_pagina(self):
        for papel in (Usuario.Papel.ADMIN, Usuario.Papel.IS,
                      Usuario.Papel.PROFESSOR, Usuario.Papel.EMPREENDEDOR):
            with self.subTest(papel=papel):
                usuario = Usuario.objects.create_user(
                    f'{papel}-conta@sgis.com', 'Teste', 'senha-antiga-123', papel=papel,
                )
                self.client.force_login(usuario)
                self.assertEqual(self.client.get(URL_TROCAR_SENHA).status_code, 200)
                self.client.logout()

    def test_senha_atual_incorreta_e_recusada(self):
        resposta = self.client.post(URL_TROCAR_SENHA, self.dados(senha_atual='errada-123'))

        self.assertEqual(resposta.status_code, 200)
        self.assertTrue(resposta.context['form'].has_error('senha_atual'))
        self.usuario.refresh_from_db()
        self.assertTrue(self.usuario.check_password('senha-antiga-123'))

    def test_confirmacao_divergente_e_recusada(self):
        resposta = self.client.post(URL_TROCAR_SENHA, self.dados(
            confirmar_nova_senha='outra-senha-789',
        ))

        self.assertEqual(resposta.status_code, 200)
        self.assertTrue(resposta.context['form'].has_error('confirmar_nova_senha'))
        self.usuario.refresh_from_db()
        self.assertTrue(self.usuario.check_password('senha-antiga-123'))

    def test_nova_senha_igual_a_atual_e_recusada(self):
        resposta = self.client.post(URL_TROCAR_SENHA, self.dados(
            nova_senha='senha-antiga-123', confirmar_nova_senha='senha-antiga-123',
        ))

        self.assertEqual(resposta.status_code, 200)
        self.assertTrue(resposta.context['form'].has_error('nova_senha'))

    def test_nova_senha_fraca_e_recusada(self):
        for senha in ('password', '1234', 'mariadas'):
            with self.subTest(senha=senha):
                resposta = self.client.post(URL_TROCAR_SENHA, self.dados(
                    nova_senha=senha, confirmar_nova_senha=senha,
                ))

                self.assertEqual(resposta.status_code, 200)
                self.assertTrue(resposta.context['form'].has_error('nova_senha'))
                self.usuario.refresh_from_db()
                self.assertTrue(self.usuario.check_password('senha-antiga-123'))

    def test_senha_alterada_e_salva_com_hash(self):
        resposta = self.client.post(URL_TROCAR_SENHA, self.dados())

        self.assertRedirects(resposta, URL_TROCAR_SENHA)
        self.usuario.refresh_from_db()
        self.assertTrue(self.usuario.check_password('nova-senha-forte-456'))
        self.assertNotEqual(self.usuario.password, 'nova-senha-forte-456')

    def test_sessao_permanece_ativa_apos_a_troca(self):
        self.client.post(URL_TROCAR_SENHA, self.dados())

        resposta = self.client.get(URL_TROCAR_SENHA)
        self.assertEqual(resposta.status_code, 200)
        self.assertTrue(resposta.context['user'].is_authenticated)

    def test_login_so_funciona_com_a_senha_nova(self):
        self.client.post(URL_TROCAR_SENHA, self.dados())
        self.client.logout()

        self.assertFalse(self.client.login(email='maria@escola.com', password='senha-antiga-123'))
        self.assertTrue(self.client.login(email='maria@escola.com', password='nova-senha-forte-456'))
