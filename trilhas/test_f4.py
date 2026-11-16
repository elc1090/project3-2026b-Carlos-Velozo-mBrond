"""Testes da F4 · Inscrição e etapas (specs/F4-inscricao/)."""
from datetime import timedelta
from unittest import mock

from django.core.exceptions import PermissionDenied
from django.db import IntegrityError, connection, transaction
from django.db.migrations.executor import MigrationExecutor
from django.test import TestCase, TransactionTestCase
from django.urls import reverse
from django.utils import timezone

from empreendimentos.models import Empreendimento
from sgis.excecoes import RegraViolada
from usuarios.models import Usuario

from . import regras
from .models import Inscricao, Trilha

ANTES_DA_0009 = ('trilhas', '0008_remover_tipo_pre_incubacao')


def criar_par():
    """Um empreendimento e uma trilha personalizada, prontos para inscrever."""
    professor = Usuario.objects.create_user('prof@escola.com', 'Prof', 'senha-forte-123',
                                            papel=Usuario.Papel.PROFESSOR)
    empreendedor = Usuario.objects.create_user('joao@atelie.com', 'João', 'senha-forte-123',
                                               papel=Usuario.Papel.EMPREENDEDOR)
    empreendimento = Empreendimento.objects.create(nome='Ateliê', tipo='Artesanato',
                                                   representante=empreendedor)
    trilha = Trilha.objects.create(titulo='Precificação', usuario_criador=professor,
                                   status=Trilha.Status.PUBLICADA)
    return empreendimento, trilha


class RestricaoDeInscricaoTests(TestCase):
    """INS-07 e A-03, no nível do banco: só uma inscrição ativa ou pausada por par."""

    def setUp(self):
        self.empreendimento, self.trilha = criar_par()

    def inscrever(self, status=Inscricao.Status.ATIVA):
        return Inscricao.objects.create(empreendimento=self.empreendimento, trilha=self.trilha,
                                        status=status)

    def test_a03_banco_recusa_duplicada_ativa_ou_pausada(self):
        for em_andamento in (Inscricao.Status.ATIVA, Inscricao.Status.PAUSADA):
            for nova in (Inscricao.Status.ATIVA, Inscricao.Status.PAUSADA):
                with self.subTest(existente=em_andamento, nova=nova):
                    primeira = self.inscrever(em_andamento)
                    with self.assertRaises(IntegrityError), transaction.atomic():
                        self.inscrever(nova)
                    primeira.status = Inscricao.Status.CANCELADA
                    primeira.save()

    def test_a03_aceita_nova_apos_concluida_ou_cancelada(self):
        for encerrada in (Inscricao.Status.CONCLUIDA, Inscricao.Status.CANCELADA):
            with self.subTest(status=encerrada):
                inscricao = self.inscrever()
                inscricao.status = encerrada
                inscricao.save()
                self.inscrever().delete()  # a nova é aceita; sai para o próximo caso

        # Várias encerradas no mesmo par convivem com uma em andamento.
        self.inscrever(Inscricao.Status.CONCLUIDA)
        self.inscrever(Inscricao.Status.CONCLUIDA)
        self.inscrever()
        self.assertEqual(Inscricao.objects.filter(empreendimento=self.empreendimento,
                                                  trilha=self.trilha).count(), 5)


class InscricaoPersonalizadaTests(TestCase):
    """INS-01, INS-07 e 3.2.1: inscrição à mão pela IS (T3)."""

    def setUp(self):
        self.empreendimento, self.trilha = criar_par()
        self.is_user = Usuario.objects.create_user('is@ufsm.br', 'IS', 'senha-forte-123',
                                                   papel=Usuario.Papel.IS)
        self.url = reverse('trilhas:inscricoes')

    def inscricoes(self, trilha=None):
        return Inscricao.objects.filter(empreendimento=self.empreendimento,
                                        trilha=trilha or self.trilha)

    def postar(self, trilha=None):
        self.client.force_login(self.is_user)
        return self.client.post(self.url, {'empreendimento': self.empreendimento.pk,
                                           'trilha': (trilha or self.trilha).pk})

    def test_a01_inscrito_ve_a_trilha_e_outro_nao(self):
        outro = Usuario.objects.create_user('maria@horta.com', 'Maria', 'senha-forte-123',
                                            papel=Usuario.Papel.EMPREENDEDOR)
        Empreendimento.objects.create(nome='Horta', tipo='Agricultura', representante=outro)

        self.assertRedirects(self.postar(), self.url)
        inscricao = self.inscricoes().get()
        self.assertEqual(inscricao.inscrito_por, self.is_user)  # 3.1.4
        self.assertIsNotNone(inscricao.inscrito_em)

        detalhe = reverse('trilhas:detalhe', args=[self.trilha.pk])
        self.client.force_login(self.empreendimento.representante)
        self.assertContains(self.client.get(reverse('trilhas:inscritas')), 'Precificação')
        self.assertEqual(self.client.get(detalhe).status_code, 200)

        self.client.force_login(outro)
        self.assertNotContains(self.client.get(reverse('trilhas:inscritas')), 'Precificação')
        self.assertEqual(self.client.get(detalhe).status_code, 403)

    def test_a03_recusa_duplicada_ativa_ou_pausada(self):
        inscricao = regras.inscrever(self.empreendimento, self.trilha, self.is_user)
        for status in (Inscricao.Status.ATIVA, Inscricao.Status.PAUSADA):
            with self.subTest(status=status):
                inscricao.status = status
                inscricao.save()

                with self.assertRaises(RegraViolada):
                    regras.inscrever(self.empreendimento, self.trilha, self.is_user)

                resposta = self.postar()
                self.assertEqual(resposta.status_code, 200)
                self.assertTrue(resposta.context['form'].has_error('__all__'))
                self.assertEqual(self.inscricoes().count(), 1)

    def test_a13_formulario_nao_aceita_trilha_de_etapa_publicada(self):
        # Publicada no teste: sem isso a recusa viria do rascunho (plano, seção 9).
        Trilha.objects.exclude(etapa='').update(status=Trilha.Status.PUBLICADA)

        self.client.force_login(self.is_user)
        opcoes = self.client.get(self.url).context['form'].fields['trilha'].queryset
        self.assertFalse(opcoes.exclude(etapa='').exists())

        for etapa in (Trilha.Etapa.INCUBACAO, Trilha.Etapa.DESINCUBACAO):
            with self.subTest(etapa=etapa):
                trilha = Trilha.objects.get(etapa=etapa)
                resposta = self.postar(trilha)
                self.assertTrue(resposta.context['form'].has_error('trilha', 'invalid_choice'))
                with self.assertRaises(RegraViolada):
                    regras.inscrever(self.empreendimento, trilha, self.is_user)
                self.assertFalse(self.inscricoes(trilha).exists())

    def test_inscrever_nega_outros_papeis(self):
        """INS-01 e A-04, na regra: a view já é coberta por `test_apenas_is_acessa`."""
        for papel in (Usuario.Papel.PROFESSOR, Usuario.Papel.EMPREENDEDOR, Usuario.Papel.ADMIN):
            with self.subTest(papel=papel):
                usuario = Usuario.objects.create_user(f'{papel}@ufsm.br', papel, 'senha-forte-123',
                                                      papel=papel)
                with self.assertRaises(PermissionDenied):
                    regras.inscrever(self.empreendimento, self.trilha, usuario)
        self.assertFalse(self.inscricoes().exists())


class StatusDaInscricaoTests(TestCase):
    """INS-06 (spec 3.5): pausar, reativar, cancelar e concluir (T3)."""

    def setUp(self):
        self.empreendimento, self.trilha = criar_par()
        self.is_user = Usuario.objects.create_user('is@ufsm.br', 'IS', 'senha-forte-123',
                                                   papel=Usuario.Papel.IS)
        self.inscricao = regras.inscrever(self.empreendimento, self.trilha, self.is_user)
        self.client.force_login(self.is_user)

    def acao(self, acao, inscricao=None, **dados):
        inscricao = inscricao or self.inscricao
        resposta = self.client.post(
            reverse('trilhas:alterar_inscricao', args=[inscricao.pk, acao]), dados,
        )
        inscricao.refresh_from_db()
        return resposta

    def test_a13c_is_conclui_personalizada_e_pode_reinscrever(self):
        self.assertRedirects(self.acao('concluir'), reverse('trilhas:inscricoes'))
        self.assertEqual(self.inscricao.status, Inscricao.Status.CONCLUIDA)
        self.assertIsNotNone(self.inscricao.concluido_em)

        # Selo com texto (RNF-05) e nenhuma ação na inscrição concluída.
        pagina = self.client.get(reverse('trilhas:inscricoes'))
        self.assertContains(pagina, 'Concluída')
        self.assertNotContains(
            pagina, reverse('trilhas:alterar_inscricao', args=[self.inscricao.pk, 'cancelar']),
        )

        nova =regras.inscrever(self.empreendimento, self.trilha, self.is_user)
        self.assertEqual(nova.status, Inscricao.Status.ATIVA)
        self.assertEqual(Inscricao.objects.filter(trilha=self.trilha).count(), 2)

    def test_a13c_concluir_trilha_de_etapa_e_recusado(self):
        pre = self.empreendimento.inscricoes.get(trilha__etapa=Trilha.Etapa.PRE_INCUBACAO)
        self.assertEqual(pre.status, Inscricao.Status.ATIVA)

        self.acao('concluir', pre)
        self.assertEqual(pre.status, Inscricao.Status.ATIVA)
        self.assertIsNone(pre.concluido_em)
        with self.assertRaises(RegraViolada):
            regras.alterar_status(pre, self.is_user, 'concluir')

    def test_a14_pausar_reativar_cancelar_gravam_status_data_e_motivo(self):
        horarios = [timezone.now() + timedelta(hours=hora) for hora in range(4)]
        # Troca só o `timezone` visto por regras.py; o do Django segue para sessões e afins.
        with mock.patch('trilhas.regras.timezone') as relogio:
            relogio.now.side_effect = horarios
            self.acao('pausar', motivo='  Férias coletivas  ')
            self.assertEqual(self.inscricao.status, Inscricao.Status.PAUSADA)
            self.assertEqual(self.inscricao.pausado_em, horarios[0])
            self.assertEqual(self.inscricao.motivo, 'Férias coletivas')

            self.acao('reativar', motivo='não é guardado')
            self.assertEqual(self.inscricao.status, Inscricao.Status.ATIVA)
            self.assertEqual(self.inscricao.reativado_em, horarios[1])
            self.assertEqual(self.inscricao.motivo, 'Férias coletivas')

            # 3.5.4: pausar de novo substitui a data, e o motivo novo substitui o anterior.
            self.acao('pausar', motivo='Obra no ateliê')
            self.assertEqual(self.inscricao.pausado_em, horarios[2])
            self.assertEqual(self.inscricao.motivo, 'Obra no ateliê')

            self.acao('cancelar')
            self.assertEqual(self.inscricao.status, Inscricao.Status.CANCELADA)
            self.assertEqual(self.inscricao.cancelado_em, horarios[3])
            self.assertEqual(self.inscricao.motivo, 'Obra no ateliê')  # sem motivo, fica o anterior
        self.assertTrue(Inscricao.objects.filter(pk=self.inscricao.pk).exists())  # 3.5.2

    def test_a15_concluida_ou_cancelada_nao_volta(self):
        for encerrar in ('concluir', 'cancelar'):
            inscricao = (self.inscricao if encerrar == 'concluir'
                         else regras.inscrever(self.empreendimento, self.trilha, self.is_user))
            regras.alterar_status(inscricao, self.is_user, encerrar)
            encerrada = inscricao.status
            for acao in regras.TRANSICOES_INSCRICAO:
                with self.subTest(status=encerrada, acao=acao):
                    self.acao(acao, inscricao)
                    self.assertEqual(inscricao.status, encerrada)
                    with self.assertRaises(RegraViolada):
                        regras.alterar_status(inscricao, self.is_user, acao)
            if encerrar == 'concluir':
                self.assertIsNone(inscricao.reativado_em)

    def test_concluir_nega_outros_papeis(self):
        """INS-06: só a IS muda o status, na view e na regra."""
        for papel in (Usuario.Papel.PROFESSOR, Usuario.Papel.EMPREENDEDOR, Usuario.Papel.ADMIN):
            with self.subTest(papel=papel):
                usuario = Usuario.objects.create_user(f'{papel}@ufsm.br', papel, 'senha-forte-123',
                                                      papel=papel)
                self.client.force_login(usuario)
                self.assertEqual(self.acao('concluir').status_code, 403)
                with self.assertRaises(PermissionDenied):
                    regras.alterar_status(self.inscricao, usuario, 'concluir')
                self.assertEqual(self.inscricao.status, Inscricao.Status.ATIVA)


class EtapaAtualTests(TestCase):
    """INS-05 e INS-11: a etapa é calculada a partir das inscrições (T3)."""

    def setUp(self):
        self.empreendimento, _ = criar_par()
        self.is_user = Usuario.objects.create_user('is@ufsm.br', 'IS', 'senha-forte-123',
                                                   papel=Usuario.Papel.IS)
        self.pre = self.empreendimento.inscricoes.get(trilha__etapa=Trilha.Etapa.PRE_INCUBACAO)

    def test_a16_sem_inscricao_de_etapa_e_sem_etapa(self):
        self.assertEqual(regras.etapa_atual(self.empreendimento), Trilha.Etapa.PRE_INCUBACAO)

        regras.alterar_status(self.pre, self.is_user, 'pausar')  # pausada conta como etapa
        self.assertEqual(regras.etapa_atual(self.empreendimento), Trilha.Etapa.PRE_INCUBACAO)

        regras.alterar_status(self.pre, self.is_user, 'cancelar')  # 3.5.3
        self.assertIsNone(regras.inscricao_de_etapa(self.empreendimento))
        self.assertIsNone(regras.etapa_atual(self.empreendimento))
        self.assertFalse(regras.incubacao_concluida(self.empreendimento))

        # Nenhuma tabela guarda a etapa do empreendimento.
        for modelo in (Empreendimento, Inscricao):
            with self.subTest(modelo=modelo.__name__):
                campos = {campo.name for campo in modelo._meta.get_fields()}
                self.assertFalse(campos & {'etapa', 'etapa_atual'})

    def test_incubacao_concluida_so_depois_da_desincubacao(self):
        """INS-11 (3.4.6). O avançar é da T5; aqui a conclusão é gravada direto."""
        desincubacao = Trilha.objects.get(etapa=Trilha.Etapa.DESINCUBACAO)
        self.pre.status = Inscricao.Status.CONCLUIDA
        self.pre.save()
        self.assertFalse(regras.incubacao_concluida(self.empreendimento))

        ultima = Inscricao.objects.create(empreendimento=self.empreendimento, trilha=desincubacao)
        self.assertEqual(regras.etapa_atual(self.empreendimento), Trilha.Etapa.DESINCUBACAO)
        self.assertFalse(regras.incubacao_concluida(self.empreendimento))

        ultima.status = Inscricao.Status.CONCLUIDA
        ultima.save()
        self.assertIsNone(regras.etapa_atual(self.empreendimento))
        self.assertTrue(regras.incubacao_concluida(self.empreendimento))

    def test_proxima_etapa_segue_a_ordem(self):
        """3.4.2: Pré-incubação → Incubação → Desincubação."""
        self.assertEqual(regras.proxima_etapa(Trilha.Etapa.PRE_INCUBACAO), Trilha.Etapa.INCUBACAO)
        self.assertEqual(regras.proxima_etapa(Trilha.Etapa.INCUBACAO), Trilha.Etapa.DESINCUBACAO)
        self.assertIsNone(regras.proxima_etapa(Trilha.Etapa.DESINCUBACAO))


class MigracaoF4Tests(TransactionTestCase):
    """Migração 0009 (plano da F4, seção 3), rodada de verdade para trás."""

    serialized_rollback = True

    def setUp(self):
        self.addCleanup(self.voltar_ao_estado_atual)  # roda mesmo se o teste falhar

    def voltar_ao_estado_atual(self):
        executor = MigrationExecutor(connection)
        executor.migrate(executor.loader.graph.leaf_nodes())

    def test_migracao_reversa_converte_concluidas_em_canceladas(self):
        empreendimento, trilha = criar_par()
        concluida_em = timezone.now() - timedelta(days=3)
        concluidas = [
            Inscricao.objects.create(empreendimento=empreendimento, trilha=trilha,
                                     status=Inscricao.Status.CONCLUIDA,
                                     concluido_em=concluida_em - timedelta(days=dias))
            for dias in (0, 10)
        ]
        ativa = Inscricao.objects.create(empreendimento=empreendimento, trilha=trilha)

        MigrationExecutor(connection).migrate([ANTES_DA_0009])

        Antiga = MigrationExecutor(connection).loader.project_state(ANTES_DA_0009).apps \
            .get_model('trilhas', 'Inscricao')
        for original in concluidas:
            convertida = Antiga.objects.get(pk=original.pk)
            self.assertEqual(convertida.status, 'cancelada')
            self.assertEqual(convertida.cancelado_em, original.concluido_em)
        self.assertEqual(Antiga.objects.get(pk=ativa.pk).status, 'ativa')
        self.assertEqual(Antiga.objects.filter(empreendimento_id=empreendimento.pk,
                                               trilha_id=trilha.pk).count(), 3)
