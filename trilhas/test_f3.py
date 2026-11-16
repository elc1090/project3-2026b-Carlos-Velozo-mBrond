"""Testes da F3 · Trilhas (specs/F3-trilhas/spec.md). Cada teste cita o critério que cobre."""

from django.core.exceptions import PermissionDenied
from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.test import TestCase, TransactionTestCase
from django.urls import reverse

from empreendimentos.models import Empreendimento
from usuarios.models import Usuario

from . import regras
from .models import AtividadeTrilha, Inscricao, Trilha
from .regras import RegraViolada

ANTES_DA_F3 = [('trilhas', '0005_criar_trilha_pre_incubacao')]
DEPOIS_DA_F3 = [('trilhas', '0008_remover_tipo_pre_incubacao')]
# Estado dos outros apps no momento do teste (já com o campo `representante`).
OUTROS_APPS = [
    ('usuarios', '0003_papel_empreendedor'),
    ('empreendimentos', '0003_renomeia_representante'),
]


class TrilhasDeEtapaTests(TestCase):
    def test_a02_existem_tres_trilhas_de_etapa(self):
        """A-02 (TRL-01, TRL-03): o sistema instalado tem uma trilha para cada etapa."""
        etapas = list(Trilha.objects.exclude(etapa='').values_list('etapa', flat=True))
        self.assertCountEqual(etapas, Trilha.Etapa.values)


class MigracaoF3Tests(TransactionTestCase):
    """Spec F3, seção 6: conversão de tipo/pre_incubacao para etapa/status (plan.md, seção 3)."""

    # Restaura no fim os dados criados pelas migrações (usuário IS, trilhas de etapa),
    # dos quais os outros testes dependem.
    serialized_rollback = True

    def setUp(self):
        executor = MigrationExecutor(connection)
        # Também exercita a reversa de 0006 a 0008. Os outros apps voltam ao estado do teste,
        # senão migrações posteriores (como usuarios/0004) deixam colunas que o estado antigo não conhece.
        executor.migrate(ANTES_DA_F3 + OUTROS_APPS)
        apps = executor.loader.project_state(ANTES_DA_F3 + OUTROS_APPS).apps

        Usuario = apps.get_model('usuarios', 'Usuario')
        Trilha = apps.get_model('trilhas', 'Trilha')
        Empreendimento = apps.get_model('empreendimentos', 'Empreendimento')
        Inscricao = apps.get_model('trilhas', 'Inscricao')

        empreendedor = Usuario.objects.create(email='e@ufsm.br', nome='Emp', papel='empreendedor')
        professor = Usuario.objects.create(email='p@ufsm.br', nome='Prof', papel='professor')
        empreendimento = Empreendimento.objects.create(
            nome='Padaria', tipo='alimentos', representante=empreendedor,
        )
        self.pre_pk = Trilha.objects.get(pre_incubacao=True).pk
        self.inscricao_pk = Inscricao.objects.create(
            empreendimento=empreendimento, trilha_id=self.pre_pk, status='ativa',
        ).pk
        self.personalizada_pk = Trilha.objects.create(
            titulo='Precificação', tipo='custom', usuario_criador=professor,
        ).pk
        self.professor_pk = professor.pk

        executor = MigrationExecutor(connection)
        executor.migrate(DEPOIS_DA_F3)
        self.apps = executor.loader.project_state(DEPOIS_DA_F3 + OUTROS_APPS).apps

    def tearDown(self):
        executor = MigrationExecutor(connection)
        executor.migrate(executor.loader.graph.leaf_nodes())

    def test_migracao_pre_incubacao_vira_etapa_publicada_sem_perder_inscricoes(self):
        Trilha = self.apps.get_model('trilhas', 'Trilha')
        Inscricao = self.apps.get_model('trilhas', 'Inscricao')

        pre = Trilha.objects.get(pk=self.pre_pk)
        self.assertEqual(pre.etapa, 'pre_incubacao')
        self.assertEqual(pre.status, 'publicada')
        self.assertIsNone(pre.usuario_criador_id)
        self.assertEqual(Inscricao.objects.get(pk=self.inscricao_pk).trilha_id, self.pre_pk)

        personalizada = Trilha.objects.get(pk=self.personalizada_pk)
        self.assertEqual(personalizada.etapa, '')
        self.assertEqual(personalizada.status, 'publicada')
        self.assertEqual(personalizada.usuario_criador_id, self.professor_pk)

        for etapa in ('incubacao', 'desincubacao'):
            with self.subTest(etapa=etapa):
                trilha = Trilha.objects.get(etapa=etapa)
                self.assertEqual(trilha.status, 'rascunho')
                self.assertIsNone(trilha.usuario_criador_id)


def criar_usuario(email, papel):
    return Usuario.objects.create_user(email, email.split('@')[0], 'x', papel=papel)


class RegrasBaseTests(TestCase):
    """Cenário comum: IS, professores X, Y e Z, um empreendedor com empreendimento e o admin."""

    def setUp(self):
        self.is_user = criar_usuario('is@ufsm.br', Usuario.Papel.IS)
        self.prof_x = criar_usuario('x@ufsm.br', Usuario.Papel.PROFESSOR)
        self.prof_y = criar_usuario('y@ufsm.br', Usuario.Papel.PROFESSOR)
        self.prof_z = criar_usuario('z@ufsm.br', Usuario.Papel.PROFESSOR)
        self.empreendedor = criar_usuario('e@ufsm.br', Usuario.Papel.EMPREENDEDOR)
        self.admin = criar_usuario('admin@ufsm.br', Usuario.Papel.ADMIN)
        self.empreendimento = Empreendimento.objects.create(
            nome='Padaria', tipo='alimentos', representante=self.empreendedor,
        )
        self.etapa = Trilha.objects.get(etapa=Trilha.Etapa.PRE_INCUBACAO)  # criada pela migração
        self.trilha_x = Trilha.objects.create(titulo='Do X', usuario_criador=self.prof_x)

    def dono_de(self, trilha):
        return self.is_user if trilha.e_de_etapa else trilha.usuario_criador

    def atividade(self, trilha, titulo='Ler o guia', **extra):
        dados = {'titulo': titulo, 'tipo': AtividadeTrilha.Tipo.LEITURA, **extra}
        return regras.acrescentar_atividade(trilha, self.dono_de(trilha), dados)

    def publicada(self, trilha):
        self.atividade(trilha)
        regras.publicar(trilha, self.dono_de(trilha))
        trilha.refresh_from_db()
        return trilha

    def inscrever(self, trilha, status=Inscricao.Status.ATIVA):
        return Inscricao.objects.create(
            empreendimento=self.empreendimento, trilha=trilha, status=status,
        )


class EstadosDaTrilhaTests(RegrasBaseTests):
    def test_a03_trilha_de_etapa_nao_pode_ser_arquivada(self):
        """A-03 (RN-08): nem a IS arquiva uma trilha de etapa."""
        self.assertEqual(self.etapa.status, Trilha.Status.PUBLICADA)
        with self.assertRaises(RegraViolada):
            regras.arquivar(self.etapa, self.is_user)
        self.etapa.refresh_from_db()
        self.assertEqual(self.etapa.status, Trilha.Status.PUBLICADA)

    def test_a09_publicar_exige_atividade_ativa(self):
        """A-09 (TRL-05): sem atividade ativa não publica; com uma, publica."""
        with self.assertRaises(RegraViolada):
            regras.publicar(self.trilha_x, self.prof_x)

        arquivada = self.atividade(self.trilha_x)
        regras.arquivar_atividade(arquivada, self.prof_x)
        with self.assertRaises(RegraViolada):
            regras.publicar(self.trilha_x, self.prof_x)

        self.atividade(self.trilha_x, 'Outra')
        regras.publicar(self.trilha_x, self.prof_x)
        self.trilha_x.refresh_from_db()
        self.assertEqual(self.trilha_x.status, Trilha.Status.PUBLICADA)
        self.assertIsNotNone(self.trilha_x.publicada_em)

    def test_a10_publicada_nao_volta_a_rascunho(self):
        """A-10 (TRL-05): não há transição de volta; publicar de novo é recusado."""
        trilha = self.publicada(self.trilha_x)
        with self.assertRaises(RegraViolada):
            regras.publicar(trilha, self.prof_x)
        trilha.refresh_from_db()
        self.assertEqual(trilha.status, Trilha.Status.PUBLICADA)

    def test_a14_trilha_arquivada_nao_e_editavel(self):
        """A-14 (TRL-05): nenhuma alteração em trilha arquivada."""
        trilha = self.publicada(self.trilha_x)
        atividade = trilha.atividades.get()
        regras.arquivar(trilha, self.prof_x)
        trilha.refresh_from_db()
        atividade.refresh_from_db()

        self.assertEqual(regras.campos_editaveis(trilha), ())
        acoes = {
            'publicar': lambda: regras.publicar(trilha, self.prof_x),
            'arquivar': lambda: regras.arquivar(trilha, self.prof_x),
            'acrescentar': lambda: regras.acrescentar_atividade(
                trilha, self.prof_x, {'titulo': 'X', 'tipo': AtividadeTrilha.Tipo.TAREFA},
            ),
            'apagar atividade': lambda: regras.apagar_atividade(atividade, self.prof_x),
            'arquivar atividade': lambda: regras.arquivar_atividade(atividade, self.prof_x),
            'mover atividade': lambda: regras.mover_atividade(atividade, self.prof_x, 'cima'),
            'IS publicar': lambda: regras.publicar(trilha, self.is_user),
        }
        for nome, acao in acoes.items():
            with self.subTest(acao=nome), self.assertRaises(RegraViolada):
                acao()

    def test_a15_nao_arquiva_trilha_com_inscricao_ativa_ou_pausada(self):
        """A-15 (TRL-05, decisão 7.3): só arquiva depois de concluir ou cancelar as inscrições."""
        trilha = self.publicada(self.trilha_x)
        inscricao = self.inscrever(trilha)
        for status in (Inscricao.Status.ATIVA, Inscricao.Status.PAUSADA):
            with self.subTest(status=status):
                Inscricao.objects.filter(pk=inscricao.pk).update(status=status)
                with self.assertRaises(RegraViolada):
                    regras.arquivar(trilha, self.prof_x)

        Inscricao.objects.filter(pk=inscricao.pk).update(status=Inscricao.Status.CANCELADA)
        regras.arquivar(trilha, self.prof_x)
        trilha.refresh_from_db()
        self.assertEqual(trilha.status, Trilha.Status.ARQUIVADA)
        self.assertIsNotNone(trilha.arquivada_em)


class AtividadesTests(RegrasBaseTests):
    def test_a08_atividade_nova_entra_no_fim(self):
        """A-08 (TRL-04): cada atividade nova fica por último."""
        primeira = self.atividade(self.trilha_x, 'Primeira')
        segunda = self.atividade(self.trilha_x, 'Segunda')
        self.assertLess(primeira.ordem, segunda.ordem)
        self.assertEqual(list(self.trilha_x.atividades.all()), [primeira, segunda])

    def test_a11_campos_editaveis_por_estado(self):
        """A-11 (TRL-06): depois de publicada, só os textos da atividade mudam."""
        self.assertIn('prazo_fixo', regras.campos_editaveis(self.trilha_x))
        trilha = self.publicada(self.trilha_x)
        self.assertEqual(set(regras.campos_editaveis(trilha)), {'titulo', 'descricao', 'endereco'})

    def test_a13_atividade_de_publicada_nao_e_apagada_so_arquivada(self):
        """A-13 (RN-10): em rascunho apaga; publicada, só arquiva."""
        rascunho = self.atividade(self.trilha_x, 'Some')
        regras.apagar_atividade(rascunho, self.prof_x)
        self.assertFalse(AtividadeTrilha.objects.filter(pk=rascunho.pk).exists())

        trilha = self.publicada(self.trilha_x)
        atividade = trilha.atividades.get()
        with self.assertRaises(RegraViolada):
            regras.apagar_atividade(atividade, self.prof_x)
        regras.arquivar_atividade(atividade, self.prof_x)
        atividade.refresh_from_db()
        self.assertIsNotNone(atividade.arquivada_em)

    def test_a23_mover_so_em_rascunho(self):
        """A-23 (TRL-08): troca de lugar com a vizinha; em publicada é recusado."""
        primeira = self.atividade(self.trilha_x, 'Primeira')
        segunda = self.atividade(self.trilha_x, 'Segunda')
        regras.mover_atividade(segunda, self.prof_x, 'cima')
        self.assertEqual(list(self.trilha_x.atividades.all()), [segunda, primeira])

        regras.publicar(self.trilha_x, self.prof_x)
        segunda.refresh_from_db()
        with self.assertRaises(RegraViolada):
            regras.mover_atividade(segunda, self.prof_x, 'baixo')


class QuemEditaTests(RegrasBaseTests):
    def test_a16_professor_nao_altera_trilha_de_outro(self):
        """A-16 (TRL-07): o professor Y não edita, publica nem arquiva a trilha do X."""
        self.assertFalse(regras.pode_editar(self.prof_y, self.trilha_x))
        self.atividade(self.trilha_x)
        with self.assertRaises(PermissionDenied):
            regras.publicar(self.trilha_x, self.prof_y)
        regras.publicar(self.trilha_x, self.prof_x)
        with self.assertRaises(PermissionDenied):
            regras.arquivar(self.trilha_x, self.prof_y)

    def test_a17_professor_nao_edita_trilha_de_etapa_nem_da_is(self):
        """A-17 (TRL-07)."""
        da_is = Trilha.objects.create(titulo='Da IS', usuario_criador=self.is_user)
        for trilha in (self.etapa, da_is):
            with self.subTest(trilha=trilha.titulo):
                self.assertFalse(regras.pode_editar(self.prof_x, trilha))
                with self.assertRaises(PermissionDenied):
                    regras.acrescentar_atividade(
                        trilha, self.prof_x, {'titulo': 'X', 'tipo': AtividadeTrilha.Tipo.TAREFA},
                    )

    def test_a19_empreendedor_e_admin_nao_editam(self):
        """A-19 (TRL-07)."""
        for usuario in (self.empreendedor, self.admin):
            for trilha in (self.etapa, self.trilha_x):
                with self.subTest(usuario=usuario.papel, trilha=trilha.titulo):
                    self.assertFalse(regras.pode_editar(usuario, trilha))

    def test_dono_e_is_editam(self):
        """TRL-07 (spec 3.3.5): o dono edita a sua; a IS edita qualquer uma."""
        self.assertTrue(regras.pode_editar(self.prof_x, self.trilha_x))
        self.assertTrue(regras.pode_editar(self.is_user, self.trilha_x))
        self.assertTrue(regras.pode_editar(self.is_user, self.etapa))

    def test_a18_confirmacao_so_quando_is_altera_trilha_de_professor(self):
        """A-18 (decisão 7.7): só a IS, e só em trilha de professor, precisa confirmar."""
        da_is = Trilha.objects.create(titulo='Da IS', usuario_criador=self.is_user)
        self.assertTrue(regras.exige_confirmacao(self.is_user, self.trilha_x))
        self.assertFalse(regras.exige_confirmacao(self.is_user, self.etapa))
        self.assertFalse(regras.exige_confirmacao(self.is_user, da_is))
        self.assertFalse(regras.exige_confirmacao(self.prof_x, self.trilha_x))

    def test_a18b_is_altera_mas_professor_continua_dono(self):
        """A-18b (RN-04): a IS publica a trilha do professor; o dono não muda."""
        self.atividade(self.trilha_x)
        regras.publicar(self.trilha_x, self.is_user)
        self.trilha_x.refresh_from_db()
        self.assertEqual(self.trilha_x.usuario_criador, self.prof_x)
        self.assertTrue(regras.e_dono(self.prof_x, self.trilha_x))
        self.assertFalse(regras.e_dono(self.is_user, self.trilha_x))


class QuemVeTests(RegrasBaseTests):
    def test_a20_rascunho_visivel_so_para_dono_e_is(self):
        """A-20 (TRL-10)."""
        self.assertTrue(regras.pode_ver(self.prof_x, self.trilha_x))
        self.assertTrue(regras.pode_ver(self.is_user, self.trilha_x))
        for usuario in (self.prof_y, self.empreendedor, self.admin):
            with self.subTest(usuario=usuario.email):
                self.assertFalse(regras.pode_ver(usuario, self.trilha_x))

    def test_a21_professor_ve_trilha_de_outro_so_se_atende_o_empreendimento(self):
        """A-21 (TRL-10): X atende o empreendimento (inscrito na trilha dele) e vê a do Y; Z não."""
        trilha_y = self.publicada(Trilha.objects.create(titulo='Do Y', usuario_criador=self.prof_y))
        self.inscrever(self.publicada(self.trilha_x))
        self.inscrever(trilha_y)

        self.assertTrue(regras.pode_ver(self.prof_x, trilha_y))
        self.assertFalse(regras.pode_ver(self.prof_z, trilha_y))

        # Continua vendo depois que a inscrição na trilha dele termina (PRO-03).
        Inscricao.objects.filter(trilha=self.trilha_x).update(status=Inscricao.Status.CANCELADA)
        self.assertTrue(regras.pode_ver(self.prof_x, trilha_y))

    def test_professor_ve_trilhas_de_etapa(self):
        """TRL-10: o professor vê as trilhas de etapa, em leitura."""
        rascunho = Trilha.objects.get(etapa=Trilha.Etapa.INCUBACAO)
        self.assertTrue(regras.pode_ver(self.prof_z, self.etapa))
        self.assertTrue(regras.pode_ver(self.prof_z, rascunho))

    def test_a22_empreendedor_nao_ve_trilha_sem_inscricao(self):
        """A-22 (TRL-10): vê só as trilhas em que o empreendimento está ou esteve inscrito."""
        trilha = self.publicada(self.trilha_x)
        self.assertTrue(regras.pode_ver(self.empreendedor, self.etapa))  # inscrição automática
        self.assertFalse(regras.pode_ver(self.empreendedor, trilha))

        inscricao = self.inscrever(trilha)
        self.assertTrue(regras.pode_ver(self.empreendedor, trilha))
        Inscricao.objects.filter(pk=inscricao.pk).update(status=Inscricao.Status.CANCELADA)
        self.assertTrue(regras.pode_ver(self.empreendedor, trilha))

    def test_admin_nao_ve_trilhas(self):
        """RN-16: o admin não acessa dados de negócio."""
        self.assertFalse(regras.trilhas_visiveis(self.admin).exists())


class TelasDaTrilhaTests(RegrasBaseTests):
    """T3: criar, ver, editar, publicar e arquivar pela interface."""

    def url(self, nome, trilha, *args):
        return reverse(f'trilhas:{nome}', args=[trilha.pk, *args])

    def test_a01_trilha_criada_e_personalizada_do_criador_em_rascunho(self):
        """A-01 (TRL-01, TRL-02): professor ou IS cria; quem criou é o dono; nasce em rascunho."""
        for usuario in (self.prof_x, self.is_user):
            with self.subTest(usuario=usuario.papel):
                self.client.force_login(usuario)
                titulo = f'Nova de {usuario.papel}'
                resposta = self.client.post(reverse('trilhas:criar'), {'titulo': titulo})
                trilha = Trilha.objects.get(titulo=titulo)
                self.assertRedirects(resposta, self.url('detalhe', trilha))
                self.assertEqual(trilha.usuario_criador, usuario)
                self.assertEqual(trilha.etapa, '')
                self.assertEqual(trilha.status, Trilha.Status.RASCUNHO)

    def test_a03_is_cria_trilha_personalizada_nao_de_etapa(self):
        """A-03 (TRL-02, RN-08): a trilha da IS é personalizada; continuam três de etapa."""
        self.client.force_login(self.is_user)
        self.client.post(reverse('trilhas:criar'), {'titulo': 'Formação extra'})
        self.assertEqual(Trilha.objects.get(titulo='Formação extra').etapa, '')
        self.assertEqual(Trilha.objects.exclude(etapa='').count(), 3)

        resposta = self.client.post(self.url('acao', self.etapa, 'arquivar'))
        self.assertRedirects(resposta, self.url('detalhe', self.etapa))
        self.etapa.refresh_from_db()
        self.assertEqual(self.etapa.status, Trilha.Status.PUBLICADA)

    def test_a04_etapa_dono_e_status_forjados_sao_ignorados(self):
        """A-04 (TRL-01, Constituição Art. 3.4)."""
        self.client.force_login(self.prof_x)
        self.client.post(reverse('trilhas:criar'), {
            'titulo': 'Forjada',
            'etapa': Trilha.Etapa.INCUBACAO,
            'status': Trilha.Status.PUBLICADA,
            'usuario_criador': self.is_user.pk,
        })
        trilha = Trilha.objects.get(titulo='Forjada')
        self.assertEqual(trilha.etapa, '')
        self.assertEqual(trilha.status, Trilha.Status.RASCUNHO)
        self.assertEqual(trilha.usuario_criador, self.prof_x)

    def test_dono_edita_titulo_e_descricao(self):
        """TRL-06: o dono altera os textos da trilha."""
        self.client.force_login(self.prof_x)
        resposta = self.client.post(
            self.url('editar', self.trilha_x), {'titulo': 'Novo título', 'descricao': 'Nova'},
        )
        self.assertRedirects(resposta, self.url('detalhe', self.trilha_x))
        self.trilha_x.refresh_from_db()
        self.assertEqual(self.trilha_x.titulo, 'Novo título')

    def test_a09_publicar_pela_tela_exige_atividade(self):
        """A-09 (TRL-05)."""
        self.client.force_login(self.prof_x)
        self.client.post(self.url('acao', self.trilha_x, 'publicar'))
        self.trilha_x.refresh_from_db()
        self.assertEqual(self.trilha_x.status, Trilha.Status.RASCUNHO)

        self.atividade(self.trilha_x)
        self.client.post(self.url('acao', self.trilha_x, 'publicar'))
        self.trilha_x.refresh_from_db()
        self.assertEqual(self.trilha_x.status, Trilha.Status.PUBLICADA)

    def test_a10_publicada_continua_publicada(self):
        """A-10 (TRL-05)."""
        trilha = self.publicada(self.trilha_x)
        self.client.force_login(self.prof_x)
        self.client.post(self.url('acao', trilha, 'publicar'))
        trilha.refresh_from_db()
        self.assertEqual(trilha.status, Trilha.Status.PUBLICADA)

    def test_a14_trilha_arquivada_nao_e_editavel_pela_tela(self):
        """A-14 (TRL-05)."""
        trilha = self.publicada(self.trilha_x)
        regras.arquivar(trilha, self.prof_x)
        self.client.force_login(self.prof_x)

        self.assertRedirects(self.client.get(self.url('editar', trilha)), self.url('detalhe', trilha))
        self.client.post(self.url('editar', trilha), {'titulo': 'Mudou'})
        trilha.refresh_from_db()
        self.assertEqual(trilha.titulo, 'Do X')

    def test_a15_nao_arquiva_pela_tela_com_inscricao_ativa(self):
        """A-15 (TRL-05)."""
        trilha = self.publicada(self.trilha_x)
        self.inscrever(trilha)
        self.client.force_login(self.prof_x)
        self.client.post(self.url('acao', trilha, 'arquivar'))
        trilha.refresh_from_db()
        self.assertEqual(trilha.status, Trilha.Status.PUBLICADA)

    def test_a16_professor_nao_altera_trilha_de_outro_pela_tela(self):
        """A-16 (TRL-07): editar, publicar e arquivar dão 403 e nada muda."""
        self.atividade(self.trilha_x)
        self.client.force_login(self.prof_y)
        self.assertEqual(self.client.get(self.url('editar', self.trilha_x)).status_code, 403)
        resposta = self.client.post(self.url('editar', self.trilha_x), {'titulo': 'Invadida'})
        self.assertEqual(resposta.status_code, 403)
        for acao in ('publicar', 'arquivar'):
            with self.subTest(acao=acao):
                resposta = self.client.post(self.url('acao', self.trilha_x, acao))
                self.assertEqual(resposta.status_code, 403)
        self.trilha_x.refresh_from_db()
        self.assertEqual(self.trilha_x.titulo, 'Do X')
        self.assertEqual(self.trilha_x.status, Trilha.Status.RASCUNHO)

    def test_a17_professor_nao_edita_trilha_de_etapa_nem_da_is_pela_tela(self):
        """A-17 (TRL-07)."""
        da_is = Trilha.objects.create(titulo='Da IS', usuario_criador=self.is_user)
        self.client.force_login(self.prof_x)
        for trilha in (self.etapa, da_is):
            with self.subTest(trilha=trilha.titulo):
                self.assertEqual(self.client.get(self.url('editar', trilha)).status_code, 403)
                resposta = self.client.post(self.url('acao', trilha, 'publicar'))
                self.assertEqual(resposta.status_code, 403)

    def test_a19_empreendedor_e_admin_nao_abrem_edicao(self):
        """A-19 (TRL-07): nem criar, nem editar, nem publicar."""
        for usuario in (self.empreendedor, self.admin):
            self.client.force_login(usuario)
            with self.subTest(usuario=usuario.papel):
                self.assertEqual(self.client.get(reverse('trilhas:criar')).status_code, 403)
                for trilha in (self.etapa, self.trilha_x):
                    self.assertEqual(self.client.get(self.url('editar', trilha)).status_code, 403)
                    resposta = self.client.post(self.url('acao', trilha, 'publicar'))
                    self.assertEqual(resposta.status_code, 403)

    def test_detalhe_so_para_quem_pode_ver(self):
        """TRL-10: o detalhe responde 200 para quem vê a trilha e 403 para os demais."""
        self.client.force_login(self.prof_x)
        self.assertEqual(self.client.get(self.url('detalhe', self.trilha_x)).status_code, 200)
        self.client.force_login(self.prof_y)
        self.assertEqual(self.client.get(self.url('detalhe', self.trilha_x)).status_code, 403)

    def test_acoes_exigem_post(self):
        """Ações que mudam estado não aceitam GET."""
        self.client.force_login(self.prof_x)
        resposta = self.client.get(self.url('acao', self.trilha_x, 'publicar'))
        self.assertEqual(resposta.status_code, 405)


class TelasDeAtividadeTests(RegrasBaseTests):
    """T4: criar, editar, apagar e arquivar atividades pela interface."""

    def setUp(self):
        super().setUp()
        self.client.force_login(self.prof_x)

    def criar(self, trilha=None, **dados):
        trilha = trilha or self.trilha_x
        dados = {'titulo': 'Atividade', 'tipo': AtividadeTrilha.Tipo.TAREFA, **dados}
        return self.client.post(reverse('trilhas:atividade_criar', args=[trilha.pk]), dados)

    def test_a05_link_sem_endereco_ou_invalido_e_recusado(self):
        """A-05 (TRL-04)."""
        for endereco in ('', 'nao-e-um-endereco'):
            with self.subTest(endereco=endereco):
                resposta = self.criar(tipo=AtividadeTrilha.Tipo.LINK, endereco=endereco)
                self.assertEqual(resposta.status_code, 200)
                self.assertTrue(resposta.context['form'].has_error('endereco'))
        self.assertFalse(self.trilha_x.atividades.exists())

        self.criar(tipo=AtividadeTrilha.Tipo.LINK, endereco='https://www.ufsm.br/')
        self.assertEqual(self.trilha_x.atividades.get().endereco, 'https://www.ufsm.br/')

    def test_a06_dois_prazos_sao_recusados(self):
        """A-06 (TRL-04)."""
        resposta = self.criar(prazo_fixo='2026-12-01', dias_apos_inscricao=10)
        self.assertEqual(resposta.status_code, 200)
        self.assertTrue(resposta.context['form'].has_error('dias_apos_inscricao'))
        self.assertFalse(self.trilha_x.atividades.exists())

    def test_dias_apos_inscricao_maior_que_zero(self):
        """TRL-04 (spec 3.4.3)."""
        resposta = self.criar(dias_apos_inscricao=0)
        self.assertTrue(resposta.context['form'].has_error('dias_apos_inscricao'))

    def test_a07_padrao_obrigatoria_e_exige_validacao(self):
        """A-07 (TRL-04): sem informar, a atividade é obrigatória e exige validação."""
        formulario = self.client.get(reverse('trilhas:atividade_criar', args=[self.trilha_x.pk]))
        self.assertEqual(formulario.context['form']['obrigatoria'].value(), 'sim')
        self.assertEqual(formulario.context['form']['exige_validacao'].value(), 'sim')

        self.criar()
        atividade = self.trilha_x.atividades.get()
        self.assertTrue(atividade.obrigatoria)
        self.assertTrue(atividade.exige_validacao)

        self.criar(titulo='Opcional', obrigatoria='nao', exige_validacao='nao')
        opcional = self.trilha_x.atividades.get(titulo='Opcional')
        self.assertFalse(opcional.obrigatoria)
        self.assertFalse(opcional.exige_validacao)

    def test_a11_publicada_aceita_texto_e_ignora_tipo_prazo_e_validacao(self):
        """A-11 (TRL-06): com a trilha publicada, só os textos da atividade mudam."""
        trilha = self.publicada(self.trilha_x)
        atividade = trilha.atividades.get()
        resposta = self.client.post(reverse('trilhas:atividade_editar', args=[atividade.pk]), {
            'titulo': 'Título novo',
            'descricao': 'Nova descrição',
            'tipo': AtividadeTrilha.Tipo.TAREFA,
            'obrigatoria': 'nao',
            'exige_validacao': 'nao',
            'dias_apos_inscricao': 5,
        })
        self.assertRedirects(resposta, reverse('trilhas:detalhe', args=[trilha.pk]))
        atividade.refresh_from_db()
        self.assertEqual(atividade.titulo, 'Título novo')
        self.assertEqual(atividade.tipo, AtividadeTrilha.Tipo.LEITURA)
        self.assertTrue(atividade.obrigatoria)
        self.assertTrue(atividade.exige_validacao)
        self.assertIsNone(atividade.dias_apos_inscricao)

    def test_rascunho_permite_mudar_tudo(self):
        """TRL-06 (spec 3.5.2): em rascunho, todos os campos da atividade podem mudar."""
        atividade = self.atividade(self.trilha_x)
        self.client.post(reverse('trilhas:atividade_editar', args=[atividade.pk]), {
            'titulo': 'Agora é tarefa',
            'tipo': AtividadeTrilha.Tipo.TAREFA,
            'obrigatoria': 'nao',
            'dias_apos_inscricao': 5,
        })
        atividade.refresh_from_db()
        self.assertEqual(atividade.tipo, AtividadeTrilha.Tipo.TAREFA)
        self.assertFalse(atividade.obrigatoria)
        self.assertEqual(atividade.dias_apos_inscricao, 5)

    def test_a12_atividade_acrescentada_em_publicada_entra_no_fim(self):
        """A-12 (TRL-06)."""
        trilha = self.publicada(self.trilha_x)
        self.criar(trilha, titulo='Depois da publicação')
        self.assertEqual(trilha.atividades.last().titulo, 'Depois da publicação')

    def test_a13_pela_tela_publicada_nao_apaga_so_arquiva(self):
        """A-13 (RN-10)."""
        rascunho = self.atividade(self.trilha_x, 'Some')
        self.client.post(reverse('trilhas:atividade_apagar', args=[rascunho.pk]))
        self.assertFalse(AtividadeTrilha.objects.filter(pk=rascunho.pk).exists())

        trilha = self.publicada(self.trilha_x)
        atividade = trilha.atividades.get()
        self.client.post(reverse('trilhas:atividade_apagar', args=[atividade.pk]))
        self.assertTrue(AtividadeTrilha.objects.filter(pk=atividade.pk).exists())

        self.client.post(reverse('trilhas:atividade_arquivar', args=[atividade.pk]))
        atividade.refresh_from_db()
        self.assertIsNotNone(atividade.arquivada_em)

    def test_outro_professor_nao_mexe_nas_atividades(self):
        """A-16 (TRL-07): criar, editar, apagar e arquivar atividade alheia dão 403."""
        atividade = self.atividade(self.trilha_x)
        self.client.force_login(self.prof_y)
        rotas = [
            ('get', reverse('trilhas:atividade_criar', args=[self.trilha_x.pk])),
            ('post', reverse('trilhas:atividade_criar', args=[self.trilha_x.pk])),
            ('get', reverse('trilhas:atividade_editar', args=[atividade.pk])),
            ('post', reverse('trilhas:atividade_apagar', args=[atividade.pk])),
            ('post', reverse('trilhas:atividade_arquivar', args=[atividade.pk])),
        ]
        for metodo, url in rotas:
            with self.subTest(url=url, metodo=metodo):
                self.assertEqual(getattr(self.client, metodo)(url).status_code, 403)
        self.assertTrue(AtividadeTrilha.objects.filter(pk=atividade.pk, arquivada_em__isnull=True).exists())

    def test_trilha_montada_e_publicada_pela_interface(self):
        """T4, 'pronto quando': trilha montada do zero, com os três tipos, e publicada."""
        self.criar(titulo='Ler', tipo=AtividadeTrilha.Tipo.LEITURA)
        self.criar(titulo='Acessar', tipo=AtividadeTrilha.Tipo.LINK, endereco='https://www.ufsm.br/')
        self.criar(titulo='Fazer', tipo=AtividadeTrilha.Tipo.TAREFA, dias_apos_inscricao=7)
        self.client.post(reverse('trilhas:acao', args=[self.trilha_x.pk, 'publicar']))
        self.trilha_x.refresh_from_db()
        self.assertEqual(self.trilha_x.status, Trilha.Status.PUBLICADA)
        self.assertEqual([a.titulo for a in self.trilha_x.atividades.all()], ['Ler', 'Acessar', 'Fazer'])


class TelasDeListaTests(RegrasBaseTests):
    """T5: cada papel vê exatamente as trilhas da spec 3.6, na lista e pelo endereço direto."""

    def lista_do_professor(self, professor):
        self.client.force_login(professor)
        contexto = self.client.get(reverse('trilhas:minhas')).context
        return {secao: list(contexto[secao]) for secao in ('minhas', 'de_etapa', 'de_outros')}

    def todas(self, **filtros):
        self.client.force_login(self.is_user)
        return list(self.client.get(reverse('trilhas:todas'), filtros).context['trilhas'])

    def status_do_detalhe(self, usuario, trilha):
        self.client.force_login(usuario)
        return self.client.get(reverse('trilhas:detalhe', args=[trilha.pk])).status_code

    def test_a20_rascunho_visivel_so_para_dono_e_is(self):
        """A-20 (TRL-10): rascunho aparece para o dono e para a IS; os demais não veem nem pelo endereço."""
        self.assertIn(self.trilha_x, self.lista_do_professor(self.prof_x)['minhas'])
        self.assertIn(self.trilha_x, self.todas())

        listas_do_y = self.lista_do_professor(self.prof_y)
        self.assertNotIn(self.trilha_x, listas_do_y['minhas'] + listas_do_y['de_outros'])
        for usuario in (self.prof_y, self.empreendedor, self.admin):
            with self.subTest(usuario=usuario.email):
                self.assertEqual(self.status_do_detalhe(usuario, self.trilha_x), 403)

    def test_a21_professor_ve_trilha_de_outro_so_se_atende_o_empreendimento(self):
        """A-21 (TRL-10): X atende o empreendimento e vê a trilha do Y em 'de outros'; Z não vê."""
        trilha_y = self.publicada(Trilha.objects.create(titulo='Do Y', usuario_criador=self.prof_y))
        self.inscrever(self.publicada(self.trilha_x))
        self.inscrever(trilha_y)

        self.assertIn(trilha_y, self.lista_do_professor(self.prof_x)['de_outros'])
        self.assertEqual(self.status_do_detalhe(self.prof_x, trilha_y), 200)

        listas_do_z = self.lista_do_professor(self.prof_z)
        self.assertNotIn(trilha_y, listas_do_z['minhas'] + listas_do_z['de_outros'])
        self.assertEqual(self.status_do_detalhe(self.prof_z, trilha_y), 403)

    def test_a22_empreendedor_nao_ve_trilha_sem_inscricao(self):
        """A-22 (TRL-10): o empreendedor vê só as trilhas em que o empreendimento está inscrito."""
        sem_inscricao = self.publicada(self.trilha_x)
        trilha_y = self.publicada(Trilha.objects.create(titulo='Do Y', usuario_criador=self.prof_y))
        self.inscrever(trilha_y)

        self.client.force_login(self.empreendedor)
        inscricoes = self.client.get(reverse('trilhas:inscritas')).context['inscricoes']
        trilhas = [inscricao.trilha for inscricao in inscricoes]
        self.assertIn(trilha_y, trilhas)
        self.assertIn(self.etapa, trilhas)  # inscrição automática na pré-incubação
        self.assertNotIn(sem_inscricao, trilhas)

        self.assertEqual(self.status_do_detalhe(self.empreendedor, trilha_y), 200)
        self.assertEqual(self.status_do_detalhe(self.empreendedor, sem_inscricao), 403)

    def test_professor_ve_as_tres_trilhas_de_etapa(self):
        """TRL-10: a seção de etapa do professor tem as três trilhas, em leitura."""
        self.assertCountEqual(
            [trilha.etapa for trilha in self.lista_do_professor(self.prof_z)['de_etapa']],
            Trilha.Etapa.values,
        )

    def test_is_filtra_por_tipo_e_estado(self):
        """TRL-10: filtros da lista da IS por tipo e por estado, combináveis."""
        publicada = self.publicada(Trilha.objects.create(titulo='Publicada', usuario_criador=self.prof_y))

        rascunhos = self.todas(estado=Trilha.Status.RASCUNHO)
        self.assertIn(self.trilha_x, rascunhos)
        self.assertNotIn(publicada, rascunhos)

        personalizadas_publicadas = self.todas(tipo='personalizada', estado=Trilha.Status.PUBLICADA)
        self.assertEqual(personalizadas_publicadas, [publicada])

        self.assertEqual(len(self.todas(estado='xyz')), Trilha.objects.count())  # filtro inválido é ignorado


class ConfirmacaoDaISTests(RegrasBaseTests):
    """T6: a IS altera trilha de professor só depois de confirmar (spec 3.3.5, decisão 7.7)."""

    def setUp(self):
        super().setUp()
        self.client.force_login(self.is_user)
        self.atividade_x = self.atividade(self.trilha_x, 'Primeira')

    def post(self, nome, objeto, dados=None, confirmar=False, *args):
        dados = dict(dados or {})
        if confirmar:
            dados['confirmar'] = '1'
        return self.client.post(reverse(f'trilhas:{nome}', args=[objeto.pk, *args]), dados)

    def verificar(self, enviar, mudou):
        """Sem confirmar, nada muda (formulário ou página de confirmação); confirmando, muda."""
        resposta = enviar(False)
        self.assertEqual(resposta.status_code, 200)
        self.assertFalse(mudou(), 'mudou sem confirmação')
        enviar(True)
        self.assertTrue(mudou(), 'não mudou com confirmação')

    def test_a18_is_altera_trilha_de_professor_so_com_confirmacao(self):
        """A-18 (TRL-07): editar, publicar, arquivar e todas as ações de atividade pedem confirmação."""
        atividade = self.atividade_x
        tarefa = {'titulo': 'Nova', 'tipo': AtividadeTrilha.Tipo.TAREFA}

        with self.subTest(acao='editar trilha'):
            self.verificar(
                lambda c: self.post('editar', self.trilha_x, {'titulo': 'Pela IS'}, c),
                lambda: Trilha.objects.get(pk=self.trilha_x.pk).titulo == 'Pela IS',
            )
        with self.subTest(acao='criar atividade'):
            self.verificar(
                lambda c: self.post('atividade_criar', self.trilha_x, tarefa, c),
                lambda: self.trilha_x.atividades.filter(titulo='Nova').exists(),
            )
        with self.subTest(acao='editar atividade'):
            self.verificar(
                lambda c: self.post('atividade_editar', atividade, {**tarefa, 'titulo': 'Editada'}, c),
                lambda: AtividadeTrilha.objects.get(pk=atividade.pk).titulo == 'Editada',
            )
        with self.subTest(acao='apagar atividade'):
            self.verificar(
                lambda c: self.post('atividade_apagar', self.trilha_x.atividades.get(titulo='Nova'), None, c),
                lambda: not self.trilha_x.atividades.filter(titulo='Nova').exists(),
            )
        with self.subTest(acao='publicar'):
            self.verificar(
                lambda c: self.post('acao', self.trilha_x, None, c, 'publicar'),
                lambda: Trilha.objects.get(pk=self.trilha_x.pk).status == Trilha.Status.PUBLICADA,
            )
        with self.subTest(acao='arquivar atividade'):
            self.verificar(
                lambda c: self.post('atividade_arquivar', atividade, None, c),
                lambda: AtividadeTrilha.objects.get(pk=atividade.pk).arquivada_em is not None,
            )
        with self.subTest(acao='arquivar trilha'):
            self.verificar(
                lambda c: self.post('acao', self.trilha_x, None, c, 'arquivar'),
                lambda: Trilha.objects.get(pk=self.trilha_x.pk).status == Trilha.Status.ARQUIVADA,
            )

    def test_a18_formulario_e_pagina_mostram_o_dono(self):
        """A-18: antes de confirmar, a IS vê de qual professor é a trilha."""
        formulario = self.client.get(reverse('trilhas:editar', args=[self.trilha_x.pk]))
        self.assertContains(formulario, 'name="confirmar"')
        self.assertContains(formulario, self.prof_x.nome)

        pagina = self.post('acao', self.trilha_x, None, False, 'publicar')
        self.assertTemplateUsed(pagina, 'trilhas/confirmar_acao.html')
        self.assertContains(pagina, self.prof_x.nome)

    def test_a18b_edicao_pela_is_mantem_o_professor_como_dono(self):
        """A-18b (RN-04): depois de a IS editar e publicar, o dono continua sendo o professor."""
        self.post('editar', self.trilha_x, {'titulo': 'Pela IS'}, True)
        self.post('acao', self.trilha_x, None, True, 'publicar')
        self.trilha_x.refresh_from_db()
        self.assertEqual(self.trilha_x.status, Trilha.Status.PUBLICADA)
        self.assertEqual(self.trilha_x.usuario_criador, self.prof_x)

    def test_is_nao_confirma_na_trilha_de_etapa_nem_na_propria(self):
        """Spec 3.3.5: a confirmação é só para trilha de professor."""
        da_is = Trilha.objects.create(titulo='Da IS', usuario_criador=self.is_user)
        for trilha in (Trilha.objects.get(etapa=Trilha.Etapa.INCUBACAO), da_is):
            with self.subTest(trilha=trilha.titulo):
                formulario = self.client.get(reverse('trilhas:editar', args=[trilha.pk]))
                self.assertNotContains(formulario, 'name="confirmar"')
                resposta = self.post('editar', trilha, {'titulo': f'{trilha.titulo} editada'})
                self.assertRedirects(resposta, reverse('trilhas:detalhe', args=[trilha.pk]))
                trilha.refresh_from_db()
                self.assertTrue(trilha.titulo.endswith('editada'))

    def test_professor_dono_nao_confirma(self):
        """Spec 3.3.5: o próprio professor altera a sua trilha sem confirmação."""
        self.client.force_login(self.prof_x)
        resposta = self.post('editar', self.trilha_x, {'titulo': 'Pelo dono'})
        self.assertRedirects(resposta, reverse('trilhas:detalhe', args=[self.trilha_x.pk]))


class TelaDeReordenarTests(RegrasBaseTests):
    """T7: subir e descer atividades pela interface (TRL-08)."""

    def setUp(self):
        super().setUp()
        self.primeira = self.atividade(self.trilha_x, 'Primeira')
        self.segunda = self.atividade(self.trilha_x, 'Segunda')

    def mover(self, atividade, direcao, **dados):
        return self.client.post(
            reverse('trilhas:atividade_mover', args=[atividade.pk, direcao]), dados,
        )

    def ordem(self):
        return [atividade.titulo for atividade in self.trilha_x.atividades.all()]

    def test_a23_reordenar_so_em_rascunho(self):
        """A-23 (TRL-08): em rascunho a ordem muda e é a exibida no detalhe; publicada, não muda."""
        self.client.force_login(self.prof_x)
        resposta = self.mover(self.segunda, 'cima')
        self.assertRedirects(resposta, reverse('trilhas:detalhe', args=[self.trilha_x.pk]))
        self.assertEqual(self.ordem(), ['Segunda', 'Primeira'])

        detalhe = self.client.get(reverse('trilhas:detalhe', args=[self.trilha_x.pk]))
        self.assertEqual([a.titulo for a in detalhe.context['ativas']], ['Segunda', 'Primeira'])

        regras.publicar(self.trilha_x, self.prof_x)
        self.mover(self.segunda, 'baixo')
        self.assertEqual(self.ordem(), ['Segunda', 'Primeira'])

    def test_botoes_so_em_rascunho_e_sem_mover_alem_das_pontas(self):
        """TRL-08: a primeira não sobe, a última não desce; publicada não mostra os botões."""
        self.client.force_login(self.prof_x)
        url_detalhe = reverse('trilhas:detalhe', args=[self.trilha_x.pk])
        subir = lambda a: reverse('trilhas:atividade_mover', args=[a.pk, 'cima'])
        descer = lambda a: reverse('trilhas:atividade_mover', args=[a.pk, 'baixo'])

        detalhe = self.client.get(url_detalhe)
        self.assertNotContains(detalhe, subir(self.primeira))
        self.assertContains(detalhe, descer(self.primeira))
        self.assertContains(detalhe, subir(self.segunda))
        self.assertNotContains(detalhe, descer(self.segunda))

        regras.publicar(self.trilha_x, self.prof_x)
        self.assertNotContains(self.client.get(url_detalhe), descer(self.primeira))

    def test_outro_professor_nao_reordena(self):
        """A-16 (TRL-07): professor que não é dono recebe 403 e a ordem não muda."""
        self.client.force_login(self.prof_y)
        self.assertEqual(self.mover(self.segunda, 'cima').status_code, 403)
        self.assertEqual(self.ordem(), ['Primeira', 'Segunda'])

    def test_is_reordena_trilha_de_professor_so_com_confirmacao(self):
        """A-18 (T6 aplicada à T7): sem confirmar, nada muda; confirmando, muda."""
        self.client.force_login(self.is_user)
        resposta = self.mover(self.segunda, 'cima')
        self.assertTemplateUsed(resposta, 'trilhas/confirmar_acao.html')
        self.assertEqual(self.ordem(), ['Primeira', 'Segunda'])

        self.mover(self.segunda, 'cima', confirmar='1')
        self.assertEqual(self.ordem(), ['Segunda', 'Primeira'])

    def test_mover_exige_post(self):
        """Ações que mudam estado não aceitam GET."""
        self.client.force_login(self.prof_x)
        url = reverse('trilhas:atividade_mover', args=[self.segunda.pk, 'cima'])
        self.assertEqual(self.client.get(url).status_code, 405)
