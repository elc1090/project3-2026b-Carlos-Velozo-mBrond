from django.test import TestCase
from django.urls import reverse

from django.utils import timezone

from empreendimentos.models import Empreendimento
from usuarios.models import Usuario

from .models import Inscricao, Trilha


class CriarTrilhaTests(TestCase):
    def setUp(self):
        self.professor = Usuario.objects.create_user(
            'prof@ufsm.br', 'Professor', 'senha123', papel=Usuario.Papel.PROFESSOR,
        )
        self.url = reverse('trilhas:criar')

    def test_exige_login(self):
        resposta = self.client.get(self.url)
        self.assertRedirects(resposta, f"{reverse('login')}?next={self.url}")

    def test_outros_papeis_recebem_403(self):
        # A IS também cria trilhas (TRL-02); os demais papéis, não.
        for papel in (Usuario.Papel.EMPREENDEDOR, Usuario.Papel.ADMIN):
            usuario = Usuario.objects.create_user(f'{papel}@ufsm.br', papel, 'x', papel=papel)
            self.client.force_login(usuario)
            self.assertEqual(self.client.get(self.url).status_code, 403)
            self.assertEqual(self.client.post(self.url, {'titulo': 'X'}).status_code, 403)
        self.assertFalse(Trilha.objects.filter(etapa='').exists())

    def test_professor_cria_trilha_personalizada(self):
        self.client.force_login(self.professor)
        resposta = self.client.post(self.url, {
            'titulo': '  Gestão financeira  ',
            'descricao': 'Noções básicas',
            # Campos forjados devem ser ignorados.
            'etapa': Trilha.Etapa.INCUBACAO,
            'status': Trilha.Status.PUBLICADA,
        })
        trilha = Trilha.objects.get(usuario_criador=self.professor)
        self.assertRedirects(resposta, reverse('trilhas:detalhe', args=[trilha.pk]))
        self.assertEqual(trilha.titulo, 'Gestão financeira')
        self.assertEqual(trilha.etapa, '')
        self.assertEqual(trilha.status, Trilha.Status.RASCUNHO)
        self.assertEqual(trilha.usuario_criador, self.professor)

    def test_titulo_obrigatorio(self):
        self.client.force_login(self.professor)
        resposta = self.client.post(self.url, {'titulo': '   ', 'descricao': ''})
        self.assertEqual(resposta.status_code, 200)
        self.assertFalse(Trilha.objects.filter(etapa='').exists())


class MinhasTrilhasTests(TestCase):
    def test_lista_apenas_trilhas_do_professor(self):
        prof = Usuario.objects.create_user('a@ufsm.br', 'A', 'x', papel=Usuario.Papel.PROFESSOR)
        outro = Usuario.objects.create_user('b@ufsm.br', 'B', 'x', papel=Usuario.Papel.PROFESSOR)
        Trilha.objects.create(titulo='Minha', usuario_criador=prof)
        Trilha.objects.create(titulo='Alheia', usuario_criador=outro)

        self.client.force_login(prof)
        resposta = self.client.get(reverse('trilhas:minhas'))
        self.assertContains(resposta, 'Minha')
        self.assertNotContains(resposta, 'Alheia')


class TodasTrilhasTests(TestCase):
    def setUp(self):
        self.is_user = Usuario.objects.create_user('is@ufsm.br', 'IS', 'x', papel=Usuario.Papel.IS)
        prof = Usuario.objects.create_user('p@ufsm.br', 'Prof', 'x', papel=Usuario.Papel.PROFESSOR)
        self.etapa = Trilha.objects.get(etapa=Trilha.Etapa.INCUBACAO)  # criada pela migração
        self.do_prof = Trilha.objects.create(titulo='Trilha do prof', usuario_criador=prof)
        self.url = reverse('trilhas:todas')

    def test_exige_login(self):
        resposta = self.client.get(self.url)
        self.assertRedirects(resposta, f"{reverse('login')}?next={self.url}")

    def test_outros_papeis_recebem_403(self):
        for papel in (Usuario.Papel.PROFESSOR, Usuario.Papel.EMPREENDEDOR, Usuario.Papel.ADMIN):
            usuario = Usuario.objects.create_user(f'{papel}2@ufsm.br', papel, 'x', papel=papel)
            self.client.force_login(usuario)
            self.assertEqual(self.client.get(self.url).status_code, 403)

    def test_is_ve_todas_as_trilhas(self):
        self.client.force_login(self.is_user)
        resposta = self.client.get(self.url)
        self.assertIn(self.etapa, resposta.context['trilhas'])
        self.assertIn(self.do_prof, resposta.context['trilhas'])

    def test_filtro_por_tipo(self):
        self.client.force_login(self.is_user)
        resposta = self.client.get(self.url, {'tipo': 'personalizada'})
        self.assertIn(self.do_prof, resposta.context['trilhas'])
        self.assertNotIn(self.etapa, resposta.context['trilhas'])

        resposta = self.client.get(self.url, {'tipo': 'etapa'})
        self.assertIn(self.etapa, resposta.context['trilhas'])
        self.assertNotIn(self.do_prof, resposta.context['trilhas'])

    def test_filtro_invalido_mostra_todas(self):
        self.client.force_login(self.is_user)
        resposta = self.client.get(self.url, {'tipo': 'xyz'})
        self.assertEqual(len(resposta.context['trilhas']), Trilha.objects.count())


class InscricaoTests(TestCase):
    def setUp(self):
        self.is_user = Usuario.objects.create_user('is@ufsm.br', 'IS', 'x', papel=Usuario.Papel.IS)
        dono = Usuario.objects.create_user('e@ufsm.br', 'Emp', 'x', papel=Usuario.Papel.EMPREENDEDOR)
        self.emp = Empreendimento.objects.create(nome='Padaria', tipo='alimentos', representante=dono)
        self.trilha = Trilha.objects.create(
            titulo='Finanças',
            usuario_criador=self.is_user,
            status=Trilha.Status.PUBLICADA,
            publicada_em=timezone.now(),
        )
        self.url = reverse('trilhas:inscricoes')

    def inscricoes(self):
        return Inscricao.objects.filter(trilha=self.trilha)

    def inscrever(self, **extra):
        dados = {'empreendimento': self.emp.pk, 'trilha': self.trilha.pk, **extra}
        return self.client.post(self.url, dados)

    def url_acao(self, inscricao, acao):
        return reverse('trilhas:alterar_inscricao', args=[inscricao.pk, acao])

    def test_apenas_is_acessa(self):
        for papel in (Usuario.Papel.PROFESSOR, Usuario.Papel.EMPREENDEDOR, Usuario.Papel.ADMIN):
            usuario = Usuario.objects.create_user(f'{papel}3@ufsm.br', papel, 'x', papel=papel)
            self.client.force_login(usuario)
            self.assertEqual(self.client.get(self.url).status_code, 403)
            self.assertEqual(self.inscrever().status_code, 403)
        self.assertFalse(self.inscricoes().exists())

    def test_is_inscreve_empreendimento(self):
        self.client.force_login(self.is_user)
        resposta = self.inscrever(status=Inscricao.Status.CANCELADA)  # campo forjado é ignorado
        self.assertRedirects(resposta, self.url)
        inscricao = self.inscricoes().get()
        self.assertEqual(inscricao.empreendimento, self.emp)
        self.assertEqual(inscricao.trilha, self.trilha)
        self.assertEqual(inscricao.status, Inscricao.Status.ATIVA)
        self.assertEqual(inscricao.inscrito_por, self.is_user)

    def test_a02_formulario_exibe_somente_trilhas_personalizadas_publicadas(self):
        rascunho = Trilha.objects.create(titulo='Rascunho', usuario_criador=self.is_user)
        arquivada = Trilha.objects.create(
            titulo='Arquivada',
            usuario_criador=self.is_user,
            status=Trilha.Status.ARQUIVADA,
        )
        etapa = Trilha.objects.get(etapa=Trilha.Etapa.INCUBACAO)

        self.client.force_login(self.is_user)
        resposta = self.client.get(self.url)
        trilhas = resposta.context['form'].fields['trilha'].queryset

        self.assertIn(self.trilha, trilhas)
        self.assertNotIn(rascunho, trilhas)
        self.assertNotIn(arquivada, trilhas)
        self.assertNotIn(etapa, trilhas)

    def test_a02_inscricao_forjada_em_trilha_invalida_e_recusada(self):
        trilhas_invalidas = [
            Trilha.objects.create(titulo='Rascunho', usuario_criador=self.is_user),
            Trilha.objects.create(
                titulo='Arquivada',
                usuario_criador=self.is_user,
                status=Trilha.Status.ARQUIVADA,
            ),
            Trilha.objects.get(etapa=Trilha.Etapa.INCUBACAO),
        ]

        self.client.force_login(self.is_user)
        for trilha in trilhas_invalidas:
            with self.subTest(trilha=trilha.titulo):
                resposta = self.inscrever(trilha=trilha.pk)
                self.assertEqual(resposta.status_code, 200)
                self.assertFalse(
                    Inscricao.objects.filter(empreendimento=self.emp, trilha=trilha).exists()
                )

    def test_nao_permite_inscricao_duplicada(self):
        self.client.force_login(self.is_user)
        self.inscrever()
        resposta = self.inscrever()
        self.assertContains(resposta, 'já está inscrito')
        self.assertEqual(self.inscricoes().count(), 1)

    def test_pode_reinscrever_apos_cancelamento(self):
        self.client.force_login(self.is_user)
        self.inscrever()
        self.client.post(self.url_acao(self.inscricoes().get(), 'cancelar'))
        self.inscrever()
        self.assertEqual(self.inscricoes().count(), 2)

    def test_empreendimento_desativado_nao_pode_ser_inscrito(self):
        self.emp.desativado_em = timezone.now()
        self.emp.save()
        self.client.force_login(self.is_user)
        self.assertEqual(self.inscrever().status_code, 200)
        self.assertFalse(self.inscricoes().exists())

    def test_pausar_reativar_cancelar(self):
        self.client.force_login(self.is_user)
        self.inscrever()
        inscricao = self.inscricoes().get()

        self.client.post(self.url_acao(inscricao, 'pausar'), {'motivo': 'Férias'})
        inscricao.refresh_from_db()
        self.assertEqual(inscricao.status, Inscricao.Status.PAUSADA)
        self.assertIsNotNone(inscricao.pausado_em)
        self.assertEqual(inscricao.motivo, 'Férias')

        self.client.post(self.url_acao(inscricao, 'reativar'))
        inscricao.refresh_from_db()
        self.assertEqual(inscricao.status, Inscricao.Status.ATIVA)

        self.client.post(self.url_acao(inscricao, 'cancelar'))
        inscricao.refresh_from_db()
        self.assertEqual(inscricao.status, Inscricao.Status.CANCELADA)
        self.assertIsNotNone(inscricao.cancelado_em)

    def test_transicao_invalida_nao_altera(self):
        self.client.force_login(self.is_user)
        self.inscrever()
        inscricao = self.inscricoes().get()
        self.client.post(self.url_acao(inscricao, 'cancelar'))
        self.client.post(self.url_acao(inscricao, 'reativar'))
        inscricao.refresh_from_db()
        self.assertEqual(inscricao.status, Inscricao.Status.CANCELADA)

    def test_acao_exige_post(self):
        self.client.force_login(self.is_user)
        self.inscrever()
        resposta = self.client.get(self.url_acao(self.inscricoes().get(), 'cancelar'))
        self.assertEqual(resposta.status_code, 405)


class InscricaoPreIncubacaoTests(TestCase):
    def setUp(self):
        self.dono = Usuario.objects.create_user('e@ufsm.br', 'Emp', 'x', papel=Usuario.Papel.EMPREENDEDOR)
        self.pre = Trilha.objects.get(etapa=Trilha.Etapa.PRE_INCUBACAO)  # criada pela migração

    def criar_empreendimento(self, nome='Padaria'):
        return Empreendimento.objects.create(nome=nome, tipo='alimentos', representante=self.dono)

    def test_migracao_cria_trilha_pre_incubacao(self):
        self.assertEqual(self.pre.titulo, 'Pré-incubação')
        self.assertEqual(self.pre.status, Trilha.Status.PUBLICADA)
        self.assertIsNone(self.pre.usuario_criador)

    def test_novo_empreendimento_inscrito_automaticamente(self):
        emp = self.criar_empreendimento()
        inscricao = Inscricao.objects.get(empreendimento=emp)
        self.assertEqual(inscricao.trilha, self.pre)
        self.assertEqual(inscricao.status, Inscricao.Status.ATIVA)
        self.assertIsNone(inscricao.inscrito_por)

    def test_editar_empreendimento_nao_reinscreve(self):
        emp = self.criar_empreendimento()
        Inscricao.objects.filter(empreendimento=emp).update(status=Inscricao.Status.CANCELADA)
        emp.descricao = 'Nova descrição'
        emp.save()
        self.assertEqual(Inscricao.objects.filter(empreendimento=emp).count(), 1)

    def test_sem_trilha_pre_incubacao_nao_inscreve(self):
        Trilha.objects.filter(pk=self.pre.pk).update(etapa='', usuario_criador=self.dono)
        with self.assertLogs('trilhas.signals', level='WARNING'):
            emp = self.criar_empreendimento()
        self.assertFalse(Inscricao.objects.filter(empreendimento=emp).exists())

    def test_apenas_uma_trilha_pre_incubacao(self):
        from django.db import IntegrityError, transaction
        with self.assertRaises(IntegrityError), transaction.atomic():
            Trilha.objects.create(titulo='Outra', etapa=Trilha.Etapa.PRE_INCUBACAO)


class TrilhasInscritasTests(TestCase):
    def setUp(self):
        is_user = Usuario.objects.create_user('is@ufsm.br', 'IS', 'x', papel=Usuario.Papel.IS)
        self.dono = Usuario.objects.create_user('e@ufsm.br', 'Emp', 'x', papel=Usuario.Papel.EMPREENDEDOR)
        outro_dono = Usuario.objects.create_user('o@ufsm.br', 'Outro', 'x', papel=Usuario.Papel.EMPREENDEDOR)
        self.emp = Empreendimento.objects.create(nome='Padaria', tipo='alimentos', representante=self.dono)
        outro_emp = Empreendimento.objects.create(nome='Horta', tipo='alimentos', representante=outro_dono)

        def trilha(titulo):
            return Trilha.objects.create(titulo=titulo, usuario_criador=is_user)

        Inscricao.objects.create(empreendimento=self.emp, trilha=trilha('Ativa'), inscrito_por=is_user)
        Inscricao.objects.create(
            empreendimento=self.emp, trilha=trilha('Pausada'), inscrito_por=is_user,
            status=Inscricao.Status.PAUSADA,
        )
        Inscricao.objects.create(
            empreendimento=self.emp, trilha=trilha('Cancelada'), inscrito_por=is_user,
            status=Inscricao.Status.CANCELADA,
        )
        Inscricao.objects.create(empreendimento=outro_emp, trilha=trilha('De outro'), inscrito_por=is_user)
        trilha('Sem inscrição')
        self.url = reverse('trilhas:inscritas')

    def test_menu_do_empreendedor_aponta_para_trilhas_inscritas(self):
        """Garante que os templates comparam com o papel certo ('empreendedor')."""
        self.client.force_login(self.dono)
        for pagina in (reverse('home'), self.url):
            with self.subTest(pagina=pagina):
                self.assertContains(self.client.get(pagina), f'href="{self.url}"')

    def test_apenas_empreendedor_acessa(self):
        for papel in (Usuario.Papel.IS, Usuario.Papel.PROFESSOR, Usuario.Papel.ADMIN):
            usuario = Usuario.objects.create_user(f'{papel}4@ufsm.br', papel, 'x', papel=papel)
            self.client.force_login(usuario)
            self.assertEqual(self.client.get(self.url).status_code, 403)

    def test_ve_apenas_suas_trilhas_nao_canceladas(self):
        self.client.force_login(self.dono)
        resposta = self.client.get(self.url)
        for titulo in ('Ativa', 'Pausada', 'Pré-incubação'):
            self.assertContains(resposta, titulo)
        for titulo in ('Cancelada', 'De outro', 'Sem inscrição'):
            self.assertNotContains(resposta, titulo)

    def test_empreendimento_desativado_nao_mostra_trilhas(self):
        self.emp.desativado_em = timezone.now()
        self.emp.save()
        self.client.force_login(self.dono)
        resposta = self.client.get(self.url)
        self.assertEqual(len(resposta.context['inscricoes']), 0)
