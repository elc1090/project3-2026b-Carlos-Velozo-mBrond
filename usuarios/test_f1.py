"""Testes da F1 · Acesso e contas (specs/F1-acesso/)."""
import importlib
import os
from io import StringIO
from unittest import mock

from django.core.management import call_command
from django.db import IntegrityError, connection
from django.db.migrations.executor import MigrationExecutor
from django.test import Client, TestCase, TransactionTestCase
from django.urls import reverse

from empreendimentos.models import Empreendimento
from sgis.excecoes import RegraViolada
from trilhas.models import Inscricao, Trilha

from . import regras
from .models import Usuario

ANTES = ('usuarios', '0003_papel_empreendedor')
DEPOIS = ('usuarios', '0004_troca_de_senha_e_criado_em')


def entrar(client, email, senha):
    return client.post(reverse('login'), {'email': email, 'senha': senha})


def dados_conta(**extra):
    """POST válido para criar um professor; `extra` sobrescreve campos."""
    return {
        'nome': 'Maria das Trilhas',
        'email': 'maria@escola.com',
        'papel': Usuario.Papel.PROFESSOR,
        'senha': 'senha-inicial-123',
        **extra,
    }


def dados_empreendedor(**extra):
    """POST válido para criar um empreendedor com o empreendimento."""
    return dados_conta(**{
        'nome': 'João do Ateliê',
        'email': 'joao@atelie.com',
        'papel': Usuario.Papel.EMPREENDEDOR,
        'empreendimento-nome': 'Ateliê da Praça',
        'empreendimento-tipo': 'Artesanato',
        'empreendimento-descricao': 'Peças feitas à mão.',
        **extra,
    })


class CriacaoDeContasTests(TestCase):
    """ACE-04, ACE-05, RN-01: a IS cria professores e empreendedores (F1, 3.3)."""

    def setUp(self):
        self.is_ = Usuario.objects.create_user('is-teste@sgis.com', 'Incubadora',
                                               'senha-forte-123', papel=Usuario.Papel.IS)
        self.client.force_login(self.is_)

    def test_a05_is_cria_professor_com_troca_obrigatoria(self):
        resposta = self.client.post(reverse('criar_usuario'), dados_conta())

        self.assertRedirects(resposta, reverse('criar_usuario'))
        conta = Usuario.objects.get(email='maria@escola.com')
        self.assertEqual(conta.papel, Usuario.Papel.PROFESSOR)
        self.assertTrue(conta.deve_trocar_senha)
        self.assertFalse(Empreendimento.objects.filter(representante=conta).exists())

    def test_a05_is_nao_cria_is_nem_admin(self):
        for papel in (Usuario.Papel.IS, Usuario.Papel.ADMIN):
            with self.subTest(papel=papel):
                resposta = self.client.post(reverse('criar_usuario'), dados_conta(papel=papel))
                self.assertTrue(resposta.context['form'].has_error('papel'))
                self.assertFalse(Usuario.objects.filter(email='maria@escola.com').exists())

    def test_a07_email_repetido_com_maiusculas_e_recusado(self):
        Usuario.objects.create_user('maria@x.com', 'Maria', 'senha-forte-123',
                                    papel=Usuario.Papel.PROFESSOR)

        resposta = self.client.post(reverse('criar_usuario'), dados_conta(email='MARIA@x.com'))

        self.assertTrue(resposta.context['form'].has_error('email'))
        self.assertEqual(Usuario.objects.filter(email='maria@x.com').count(), 1)

    def test_a08_empreendedor_e_empreendimento_criados_juntos(self):
        resposta = self.client.post(reverse('criar_usuario'), dados_empreendedor())

        self.assertRedirects(resposta, reverse('criar_usuario'))
        conta = Usuario.objects.get(email='joao@atelie.com')
        self.assertEqual(conta.papel, Usuario.Papel.EMPREENDEDOR)
        self.assertTrue(conta.deve_trocar_senha)
        empreendimento = Empreendimento.objects.get(representante=conta)
        self.assertEqual(empreendimento.nome, 'Ateliê da Praça')
        self.assertTrue(Inscricao.objects.filter(
            empreendimento=empreendimento, trilha__etapa=Trilha.Etapa.PRE_INCUBACAO,
        ).exists())

    def test_a08_empreendimento_invalido_nao_cria_nada(self):
        resposta = self.client.post(reverse('criar_usuario'),
                                    dados_empreendedor(**{'empreendimento-nome': ''}))

        self.assertTrue(resposta.context['form_empreendimento'].has_error('nome'))
        self.assertFalse(Usuario.objects.filter(email='joao@atelie.com').exists())
        self.assertFalse(Empreendimento.objects.filter(nome='Ateliê da Praça').exists())

    def test_a08_erro_ao_salvar_o_empreendimento_nao_deixa_conta(self):
        """Pronto quando da T4: um erro no empreendimento não deixa conta criada."""
        with mock.patch('usuarios.regras.vincular_empreendimento', side_effect=IntegrityError):
            with self.assertRaises(IntegrityError):
                self.client.post(reverse('criar_usuario'), dados_empreendedor())

        self.assertFalse(Usuario.objects.filter(email='joao@atelie.com').exists())

    def test_a08_dados_do_empreendimento_sao_ignorados_para_professor(self):
        resposta = self.client.post(reverse('criar_usuario'), dados_conta(**{
            'empreendimento-nome': 'Não deveria existir', 'empreendimento-tipo': 'Teste',
        }))

        self.assertRedirects(resposta, reverse('criar_usuario'))
        self.assertFalse(Empreendimento.objects.filter(nome='Não deveria existir').exists())

    def test_j1_contas_de_ponta_a_ponta(self):
        """J-1: a IS cria o empreendedor, e o empreendimento entra na pré-incubação.

        A parte de "precisa trocar a senha antes de usar o sistema" é a F1 · T3 (#31):
        aqui só se confere que a conta nasce marcada.
        """
        self.client.post(reverse('criar_usuario'), dados_empreendedor())
        conta = Usuario.objects.get(email='joao@atelie.com')
        empreendimento = conta.empreendimentos.get()
        self.assertTrue(conta.deve_trocar_senha)
        self.assertEqual(
            list(empreendimento.inscricoes.values_list('trilha__etapa', flat=True)),
            [Trilha.Etapa.PRE_INCUBACAO],
        )

        resposta = self.client.post(reverse('criar_usuario'),
                                    dados_conta(email='outra.is@sgis.com', papel=Usuario.Papel.IS))
        self.assertTrue(resposta.context['form'].has_error('papel'))

        self.client.logout()
        resposta = entrar(self.client, 'joao@atelie.com', 'senha-inicial-123')
        self.assertRedirects(resposta, reverse('home'), fetch_redirect_response=False)


class EmailEmMinusculasTests(TestCase):
    """ACE-01: o e-mail vale com ou sem maiúsculas e é guardado em minúsculas."""

    def test_a01_entra_com_email_em_maiusculas(self):
        Usuario.objects.create_user('maria@x.com', 'Maria', 'senha-forte-123',
                                    papel=Usuario.Papel.PROFESSOR)

        resposta = entrar(self.client, 'Maria@X.com', 'senha-forte-123')
        self.assertRedirects(resposta, reverse('home'), fetch_redirect_response=False)

    def test_a01_conta_criada_com_maiusculas_fica_em_minusculas(self):
        conta = Usuario.objects.create_user('Joao@X.com', 'João', 'senha-forte-123',
                                            papel=Usuario.Papel.PROFESSOR)
        conta.refresh_from_db()
        self.assertEqual(conta.email, 'joao@x.com')


class SenhaFracaTests(TestCase):
    """ACE-12: senha com os validadores do Django e mínimo de 10 caracteres."""

    SENHAS_FRACAS = [
        ('9 caracteres', 'Trilha#12'),
        ('comum', 'qwertyuiop'),
        ('só números', '83920571946'),
        ('parecida com o e-mail', 'mariadastrilhas'),
    ]

    def setUp(self):
        self.is_ = Usuario.objects.create_user('is-teste@sgis.com', 'Incubadora',
                                               'senha-forte-123', papel=Usuario.Papel.IS)

    def test_a09_senha_fraca_recusada_na_criacao_redefinicao_e_troca(self):
        # A redefinição pela IS chega na F1 · T5; aqui, os caminhos que já existem.
        self.client.force_login(self.is_)
        for motivo, senha in self.SENHAS_FRACAS:
            with self.subTest(caminho='criação', motivo=motivo):
                resposta = self.client.post(reverse('criar_usuario'), {
                    'nome': 'Maria das Trilhas', 'email': 'mariadastrilhas@escola.com',
                    'papel': Usuario.Papel.PROFESSOR, 'senha': senha,
                })
                self.assertTrue(resposta.context['form'].has_error('senha'))
                self.assertFalse(
                    Usuario.objects.filter(email='mariadastrilhas@escola.com').exists())

        conta = Usuario.objects.create_user('mariadastrilhas@escola.com', 'Maria das Trilhas',
                                            'senha-antiga-123', papel=Usuario.Papel.PROFESSOR)
        self.client.force_login(conta)
        for motivo, senha in self.SENHAS_FRACAS:
            with self.subTest(caminho='troca', motivo=motivo):
                resposta = self.client.post(reverse('trocar_senha'), {
                    'senha_atual': 'senha-antiga-123',
                    'nova_senha': senha, 'confirmar_nova_senha': senha,
                })
                self.assertTrue(resposta.context['form'].has_error('nova_senha'))
                conta.refresh_from_db()
                self.assertTrue(conta.check_password('senha-antiga-123'))


class CreateSuperuserTests(TestCase):
    """ACE-13: o primeiro admin é criado por comando e consegue entrar."""

    def test_createsuperuser_cria_conta_que_entra(self):
        with mock.patch.dict(os.environ, {'DJANGO_SUPERUSER_PASSWORD': 'senha-do-admin-123'}):
            call_command('createsuperuser', interactive=False, email='Admin@SGIS.com',
                         nome='Administrador', stdout=StringIO())

        conta = Usuario.objects.get(email='admin@sgis.com')
        self.assertEqual(conta.papel, Usuario.Papel.ADMIN)
        resposta = entrar(self.client, 'admin@sgis.com', 'senha-do-admin-123')
        self.assertRedirects(resposta, reverse('home'), fetch_redirect_response=False)


class MigracaoTests(TransactionTestCase):
    """Migração 0004 (plano da F1, seção 3), rodada de verdade a partir da 0003."""

    serialized_rollback = True

    def setUp(self):
        self.addCleanup(self.voltar_ao_estado_atual)  # roda mesmo se o setUp falhar
        self.executor = MigrationExecutor(connection)
        self.executor.migrate([ANTES])
        self.apps_antes = self.executor.loader.project_state(ANTES).apps

    def voltar_ao_estado_atual(self):
        executor = MigrationExecutor(connection)
        executor.migrate(executor.loader.graph.leaf_nodes())

    def migrar_para_a_0004(self):
        executor = MigrationExecutor(connection)
        executor.migrate([DEPOIS])

    def test_migracao_marca_contas_is_e_normaliza_emails(self):
        Antigo = self.apps_antes.get_model('usuarios', 'Usuario')
        Antigo.objects.create(email='Outra.IS@SGIS.com', nome='IS', papel='is', password='!')
        Antigo.objects.create(email='Prof@Escola.com', nome='Prof', papel='professor',
                              password='!')

        self.migrar_para_a_0004()

        self.assertTrue(Usuario.objects.get(email='outra.is@sgis.com').deve_trocar_senha)
        professor = Usuario.objects.get(email='prof@escola.com')
        self.assertFalse(professor.deve_trocar_senha)
        self.assertIsNotNone(professor.criado_em)

    def test_a20_conta_inicial_da_is_em_minusculas_com_troca_obrigatoria(self):
        Antigo = self.apps_antes.get_model('usuarios', 'Usuario')
        Antigo.objects.filter(papel='is').delete()
        conta_inicial = importlib.import_module(
            'usuarios.migrations.0002_criar_usuario_is_padrao')
        ambiente = {'IS_EMAIL': 'Nova.IS@SGIS.com', 'IS_SENHA_INICIAL': 'senha-inicial-123'}
        with mock.patch.dict(os.environ, ambiente):
            conta_inicial.criar_usuario_is_padrao(self.apps_antes, None)

        self.migrar_para_a_0004()

        conta = Usuario.objects.get(papel=Usuario.Papel.IS)
        self.assertEqual(conta.email, 'nova.is@sgis.com')
        self.assertTrue(conta.deve_trocar_senha)
        self.assertTrue(conta.check_password('senha-inicial-123'))

    def test_migracao_para_com_emails_que_ficariam_iguais(self):
        Antigo = self.apps_antes.get_model('usuarios', 'Usuario')
        Antigo.objects.create(email='Ana@X.com', nome='Ana', papel='professor', password='!')
        Antigo.objects.create(email='ana@x.com', nome='Ana 2', papel='professor', password='!')

        with self.assertRaises(RuntimeError):
            self.migrar_para_a_0004()

        emails = set(Antigo.objects.values_list('email', flat=True))
        self.assertTrue({'Ana@X.com', 'ana@x.com'} <= emails)  # nada foi alterado
        Antigo.objects.filter(email='Ana@X.com').delete()


class GestaoDeContasTests(TestCase):
    """ACE-08 a ACE-11: a IS gerencia professores e empreendedores (F1, 3.5.4 e 3.6)."""

    def setUp(self):
        self.is_ = Usuario.objects.create_user('is-teste@sgis.com', 'Incubadora',
                                               'senha-forte-123', papel=Usuario.Papel.IS)
        self.outra_is = Usuario.objects.create_user('outra-is@sgis.com', 'Outra IS',
                                                    'senha-forte-123', papel=Usuario.Papel.IS)
        self.admin = Usuario.objects.create_superuser('admin@sgis.com', 'Admin', 'senha-forte-123')
        self.professor = Usuario.objects.create_user('prof@escola.com', 'Professora Ana',
                                                     'senha-forte-123',
                                                     papel=Usuario.Papel.PROFESSOR)
        self.empreendedor = Usuario.objects.create_user('joao@atelie.com', 'João do Ateliê',
                                                        'senha-antiga-123',
                                                        papel=Usuario.Papel.EMPREENDEDOR)
        self.client.force_login(self.is_)

    def alterar(self, conta, acao):
        return self.client.post(reverse('alterar_conta', args=[conta.pk, acao]))

    def assertVaiAoLogin(self, sessao):
        resposta = sessao.get(reverse('trocar_senha'))
        self.assertRedirects(resposta, f"{reverse('login')}?next={reverse('trocar_senha')}",
                             fetch_redirect_response=False)

    def test_a13_redefinicao_encerra_sessoes_e_exige_troca(self):
        sessao_do_empreendedor = Client()
        sessao_do_empreendedor.force_login(self.empreendedor)
        self.assertEqual(sessao_do_empreendedor.get(reverse('trocar_senha')).status_code, 200)

        resposta = self.client.post(reverse('redefinir_senha', args=[self.empreendedor.pk]),
                                    {'nova_senha': 'senha-nova-456'}, follow=True)

        self.assertRedirects(resposta, reverse('contas'))
        self.assertNotContains(resposta, 'senha-nova-456')  # 3.4.2: a senha não aparece
        self.empreendedor.refresh_from_db()
        self.assertTrue(self.empreendedor.deve_trocar_senha)
        self.assertFalse(self.empreendedor.check_password('senha-antiga-123'))
        self.assertVaiAoLogin(sessao_do_empreendedor)
        resposta = entrar(Client(), 'joao@atelie.com', 'senha-nova-456')
        self.assertRedirects(resposta, reverse('home'), fetch_redirect_response=False)

    def test_a13_is_nao_redefine_is_nem_admin(self):
        for conta in (self.outra_is, self.admin, self.is_):
            with self.subTest(conta=conta.email):
                resposta = self.client.post(reverse('redefinir_senha', args=[conta.pk]),
                                            {'nova_senha': 'senha-nova-456'})
                self.assertEqual(resposta.status_code, 403)
                conta.refresh_from_db()
                self.assertTrue(conta.check_password('senha-forte-123'))

    def test_a09_senha_fraca_recusada_na_redefinicao(self):
        url = reverse('redefinir_senha', args=[self.professor.pk])
        senhas_fracas = [
            ('9 caracteres', 'Trilha#12'),
            ('comum', 'qwertyuiop'),
            ('só números', '83920571946'),
            ('parecida com o e-mail', 'profescola'),
            ('parecida com o nome', 'professoraana'),  # 3.4.1: o nome também conta
        ]
        for motivo, senha in senhas_fracas:
            with self.subTest(motivo=motivo):
                resposta = self.client.post(url, {'nova_senha': senha})
                self.assertEqual(resposta.status_code, 200)
                self.assertTrue(resposta.context['form'].has_error('nova_senha'))
                self.professor.refresh_from_db()
                self.assertTrue(self.professor.check_password('senha-forte-123'))

    def test_a14_lista_de_contas_da_is_com_filtros(self):
        self.empreendedor.is_active = False
        self.empreendedor.save()

        contas = set(self.client.get(reverse('contas')).context['contas'])
        self.assertEqual(contas, {self.professor, self.empreendedor})

        casos = [
            ({'papel': 'professor'}, {self.professor}),
            ({'status': 'desativada'}, {self.empreendedor}),
            ({'papel': 'professor', 'status': 'desativada'}, set()),
            ({'papel': 'admin', 'status': 'qualquer'}, {self.professor, self.empreendedor}),
        ]
        for filtros, esperado in casos:
            with self.subTest(filtros=filtros):
                resposta = self.client.get(reverse('contas'), filtros)
                self.assertEqual(set(resposta.context['contas']), esperado)

    def test_a15_edita_nome_e_email_e_papel_forjado_e_ignorado(self):
        resposta = self.client.post(reverse('editar_conta', args=[self.professor.pk]), {
            'nome': 'Professora Ana Lima', 'email': 'Ana.Lima@Escola.com', 'papel': 'admin',
        })

        self.assertRedirects(resposta, reverse('contas'))
        self.professor.refresh_from_db()
        self.assertEqual(self.professor.nome, 'Professora Ana Lima')
        self.assertEqual(self.professor.email, 'ana.lima@escola.com')
        self.assertEqual(self.professor.papel, Usuario.Papel.PROFESSOR)

    def test_a15_email_de_outra_conta_e_recusado_na_edicao(self):
        resposta = self.client.post(reverse('editar_conta', args=[self.professor.pk]), {
            'nome': 'Professora Ana', 'email': 'JOAO@atelie.com',
        })
        self.assertTrue(resposta.context['form'].has_error('email'))

    def test_a16_desativar_encerra_sessao_e_reativar_devolve_acesso(self):
        sessao_do_empreendedor = Client()
        sessao_do_empreendedor.force_login(self.empreendedor)

        self.assertRedirects(self.alterar(self.empreendedor, 'desativar'), reverse('contas'))
        self.empreendedor.refresh_from_db()
        self.assertFalse(self.empreendedor.is_active)
        self.assertVaiAoLogin(sessao_do_empreendedor)
        resposta = entrar(Client(), 'joao@atelie.com', 'senha-antiga-123')
        self.assertEqual(resposta.status_code, 200)  # o login é recusado

        self.assertRedirects(self.alterar(self.empreendedor, 'reativar'), reverse('contas'))
        resposta = entrar(Client(), 'joao@atelie.com', 'senha-antiga-123')
        self.assertRedirects(resposta, reverse('home'), fetch_redirect_response=False)

    def test_a17_ninguem_desativa_a_si_mesmo(self):
        # A IS não gerencia contas IS, então a própria conta já responde 403.
        self.assertEqual(self.alterar(self.is_, 'desativar').status_code, 403)
        self.is_.refresh_from_db()
        self.assertTrue(self.is_.is_active)

        # Para o admin, que gerencia todas as contas, a regra recusa a própria.
        with self.assertRaises(RegraViolada):
            regras.desativar(self.admin, self.admin)
        self.admin.refresh_from_db()
        self.assertTrue(self.admin.is_active)

    def test_a18_lista_de_contas_nao_tem_acao_de_apagar(self):
        conteudo = self.client.get(reverse('contas')).content.decode().lower()
        for termo in ('apagar', 'excluir', 'remover'):
            with self.subTest(termo=termo):
                self.assertNotIn(termo, conteudo)

    def test_a19_professor_e_empreendedor_nao_abrem_gestao_de_contas(self):
        for conta, alvo in ((self.professor, self.empreendedor), (self.empreendedor, self.professor)):
            sessao = Client()
            sessao.force_login(conta)
            pedidos = [
                ('get', reverse('contas')),
                ('get', reverse('editar_conta', args=[alvo.pk])),
                ('post', reverse('editar_conta', args=[alvo.pk])),
                ('get', reverse('redefinir_senha', args=[alvo.pk])),
                ('post', reverse('redefinir_senha', args=[alvo.pk])),
                ('post', reverse('alterar_conta', args=[alvo.pk, 'desativar'])),
            ]
            for metodo, url in pedidos:
                with self.subTest(papel=conta.papel, metodo=metodo, url=url):
                    self.assertEqual(getattr(sessao, metodo)(url).status_code, 403)
            alvo.refresh_from_db()
            self.assertTrue(alvo.is_active)
