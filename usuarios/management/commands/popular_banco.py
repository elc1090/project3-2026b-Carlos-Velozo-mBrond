from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from empreendimentos.models import Empreendimento
from trilhas.models import AtividadeTrilha, Trilha
from usuarios.models import Usuario


class Command(BaseCommand):
    help = 'Popula o banco de dados com dados de teste/mock (usuários, empreendimentos e trilhas).'

    @transaction.atomic
    def handle(self, *args, **options):
        if not settings.DEBUG:
            raise CommandError('Dados de mock nunca vão para produção (RN-MVP-10).')
        self.stdout.write(self.style.NOTICE('Iniciando carga de dados de mock...'))

        # 1. Usuários de teste para cada papel
        usuarios_data = [
            {
                'email': 'admin@sgis.com',
                'nome': 'Administrador Geral',
                'papel': Usuario.Papel.ADMIN,
                'senha': 'admin123',
                'is_staff': True,
                'is_superuser': True,
            },
            {
                'email': 'is@sgis.com',
                'nome': 'Coordenação Incubadora Social',
                'papel': Usuario.Papel.IS,
                'senha': 'is123456',
                'is_staff': False,
                'is_superuser': False,
            },
            {
                'email': 'professor.carlos@sgis.com',
                'nome': 'Prof. Carlos Eduardo',
                'papel': Usuario.Papel.PROFESSOR,
                'senha': 'prof123456',
                'is_staff': False,
                'is_superuser': False,
            },
            {
                'email': 'professora.marina@sgis.com',
                'nome': 'Profa. Marina Silva',
                'papel': Usuario.Papel.PROFESSOR,
                'senha': 'prof123456',
                'is_staff': False,
                'is_superuser': False,
            },
            {
                'email': 'ana.costura@sgis.com',
                'nome': 'Ana Souza (Costura Criativa)',
                'papel': Usuario.Papel.EMPREENDEDOR,
                'senha': 'emp123456',
                'is_staff': False,
                'is_superuser': False,
            },
            {
                'email': 'joao.horta@sgis.com',
                'nome': 'João Pereira (Horta Comunitária)',
                'papel': Usuario.Papel.EMPREENDEDOR,
                'senha': 'emp123456',
                'is_staff': False,
                'is_superuser': False,
            },
        ]

        usuarios = {}
        for item in usuarios_data:
            usuario, created = Usuario.objects.get_or_create(
                email=item['email'],
                defaults={
                    'nome': item['nome'],
                    'papel': item['papel'],
                    'is_staff': item['is_staff'],
                    'is_superuser': item['is_superuser'],
                    'is_active': True,
                },
            )
            # Garante que a senha está devidamente configurada
            usuario.nome = item['nome']
            usuario.papel = item['papel']
            usuario.is_staff = item['is_staff']
            usuario.is_superuser = item['is_superuser']
            usuario.set_password(item['senha'])
            usuario.save()

            status = 'criado' if created else 'atualizado'
            self.stdout.write(f'  [OK] Usuario [{usuario.papel.upper()}] {usuario.email} ({status})')
            usuarios[item['email']] = usuario

        # 2. Empreendimentos de mock
        empreendimentos_data = [
            {
                'nome': 'Atelie Costura Solidaria',
                'tipo': 'Artesanato / Textil',
                'descricao': 'Producao artesanal sustentavel e geracao de renda para costureiras locais.',
                'representante': usuarios['ana.costura@sgis.com'],
                'usuario_professor_supervisor': usuarios['professor.carlos@sgis.com'],
            },
            {
                'nome': 'Horta Urbana Verde Vivo',
                'tipo': 'Agroecologia / Alimentos',
                'descricao': 'Cultivo comunitario de hortalicas organicas com venda direta ao consumidor.',
                'representante': usuarios['joao.horta@sgis.com'],
                'usuario_professor_supervisor': usuarios['professora.marina@sgis.com'],
            },
        ]

        for emp_info in empreendimentos_data:
            emp, created = Empreendimento.objects.get_or_create(
                nome=emp_info['nome'],
                defaults=emp_info,
            )
            status = 'criado' if created else 'ja existente'
            self.stdout.write(f'  [OK] Empreendimento: {emp.nome} ({status})')

        # 3. Trilhas de mock: as de etapa já existem (migração trilhas/0007);
        #    aqui ganham atividades e são publicadas, junto com uma trilha de professor.
        L, T, R = AtividadeTrilha.Tipo.LINK, AtividadeTrilha.Tipo.TAREFA, AtividadeTrilha.Tipo.LEITURA
        atividades_por_etapa = {
            Trilha.Etapa.PRE_INCUBACAO: [
                (R, 'Conhecer a Incubadora Social', '', 7),
                (T, 'Descrever o empreendimento', '', 14),
            ],
            Trilha.Etapa.INCUBACAO: [
                (T, 'Organizar entradas e saidas', '', 30),
                (L, 'Guia de fluxo de caixa', 'https://www.sebrae.com.br/', None),
            ],
            Trilha.Etapa.DESINCUBACAO: [
                (T, 'Plano de continuidade', '', 30),
            ],
        }
        for etapa, atividades in atividades_por_etapa.items():
            trilha = Trilha.objects.get(etapa=etapa)
            self._preencher_e_publicar(trilha, atividades)
            self.stdout.write(f'  [OK] Trilha de etapa: {trilha.titulo} ({trilha.get_status_display()})')

        trilha_prof, _ = Trilha.objects.get_or_create(
            titulo='Mentoria de Precificacao e Custos',
            defaults={
                'descricao': 'Trilha personalizada focada em definicao de precos, margem e fluxo de caixa.',
                'usuario_criador': usuarios['professor.carlos@sgis.com'],
            },
        )
        self._preencher_e_publicar(trilha_prof, [
            (R, 'Conceitos de custo fixo e variavel', '', 7),
            (T, 'Calcular o preco de um produto', '', 14),
        ])
        self.stdout.write(f'  [OK] Trilha personalizada: {trilha_prof.titulo} ({trilha_prof.get_status_display()})')

        self.stdout.write(self.style.SUCCESS('\nDados de mock populados com sucesso!'))

    def _preencher_e_publicar(self, trilha, atividades):
        """Cria as atividades que faltam e publica a trilha, se ainda for rascunho."""
        for ordem, (tipo, titulo, endereco, dias) in enumerate(atividades, start=1):
            AtividadeTrilha.objects.get_or_create(
                trilha=trilha,
                titulo=titulo,
                defaults={
                    'tipo': tipo,
                    'endereco': endereco,
                    'ordem': ordem,
                    'dias_apos_inscricao': dias,
                },
            )
        if trilha.status == Trilha.Status.RASCUNHO:
            trilha.status = Trilha.Status.PUBLICADA
            trilha.publicada_em = timezone.now()
            trilha.save(update_fields=['status', 'publicada_em'])
