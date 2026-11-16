from django.conf import settings
from django.db import models


class Trilha(models.Model):
    """Trilha de atividades: de etapa (da IS) ou personalizada (professor ou IS)."""

    class Etapa(models.TextChoices):
        PRE_INCUBACAO = 'pre_incubacao', 'Pré-incubação'
        INCUBACAO = 'incubacao', 'Incubação'
        DESINCUBACAO = 'desincubacao', 'Desincubação'

    class Status(models.TextChoices):
        RASCUNHO = 'rascunho', 'Rascunho'
        PUBLICADA = 'publicada', 'Publicada'
        ARQUIVADA = 'arquivada', 'Arquivada'

    titulo = models.CharField('título', max_length=200)
    descricao = models.TextField('descrição', blank=True)
    etapa = models.CharField(
        'etapa',
        max_length=20,
        choices=Etapa.choices,
        blank=True,
        default='',
        help_text='Vazio = trilha personalizada.',
    )
    status = models.CharField(
        'status', max_length=10, choices=Status.choices, default=Status.RASCUNHO,
    )
    usuario_criador = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='trilhas_criadas',
        verbose_name='dono',
        help_text='Vazio nas trilhas de etapa: a dona é a IS, não um usuário.',
    )
    publicada_em = models.DateTimeField('publicada em', null=True, blank=True)
    arquivada_em = models.DateTimeField('arquivada em', null=True, blank=True)

    class Meta:
        verbose_name = 'trilha'
        verbose_name_plural = 'trilhas'
        constraints = [
            # RN-08: no máximo uma trilha por etapa.
            models.UniqueConstraint(
                fields=['etapa'],
                condition=~models.Q(etapa=''),
                name='trilha_etapa_unica',
            ),
            # Trilha de etapa não tem usuário dono; personalizada sempre tem.
            models.CheckConstraint(
                condition=(
                    (models.Q(etapa='') & models.Q(usuario_criador__isnull=False))
                    | (~models.Q(etapa='') & models.Q(usuario_criador__isnull=True))
                ),
                name='trilha_dono_conforme_tipo',
            ),
        ]

    def __str__(self):
        return self.titulo

    @property
    def e_de_etapa(self):
        return self.etapa != ''


class AtividadeTrilha(models.Model):
    """Atividade de uma trilha (TRL-04)."""

    class Tipo(models.TextChoices):
        LEITURA = 'leitura', 'Leitura'
        LINK = 'link', 'Link'
        TAREFA = 'tarefa', 'Tarefa'

    trilha = models.ForeignKey(
        Trilha,
        on_delete=models.PROTECT,
        related_name='atividades',
        verbose_name='trilha',
    )
    titulo = models.CharField('título', max_length=200)
    descricao = models.TextField('descrição', blank=True)
    tipo = models.CharField('tipo', max_length=10, choices=Tipo.choices)
    endereco = models.URLField('endereço', blank=True)
    ordem = models.PositiveIntegerField('ordem')
    obrigatoria = models.BooleanField('obrigatória', default=True)
    exige_validacao = models.BooleanField('exige validação', default=True)
    prazo_fixo = models.DateField('prazo fixo', null=True, blank=True)
    dias_apos_inscricao = models.PositiveIntegerField(
        'dias após a inscrição', null=True, blank=True,
    )
    criada_em = models.DateTimeField('criada em', auto_now_add=True)
    arquivada_em = models.DateTimeField(
        'arquivada em', null=True, blank=True, help_text='Vazio = ativa.',
    )

    class Meta:
        verbose_name = 'atividade da trilha'
        verbose_name_plural = 'atividades da trilha'
        ordering = ['ordem', 'id']
        constraints = [
            # Nunca os dois prazos ao mesmo tempo.
            models.CheckConstraint(
                condition=(
                    models.Q(prazo_fixo__isnull=True)
                    | models.Q(dias_apos_inscricao__isnull=True)
                ),
                name='atividade_um_prazo',
            ),
            models.CheckConstraint(
                condition=(
                    models.Q(dias_apos_inscricao__isnull=True)
                    | models.Q(dias_apos_inscricao__gt=0)
                ),
                name='atividade_dias_positivo',
            ),
            # Atividade do tipo Link precisa de endereço.
            models.CheckConstraint(
                condition=~models.Q(tipo='link') | ~models.Q(endereco=''),
                name='atividade_link_com_endereco',
            ),
        ]

    def __str__(self):
        return self.titulo


class Inscricao(models.Model):
    """Inscrição de um empreendimento em uma trilha, feita pela IS."""

    class Status(models.TextChoices):
        ATIVA = 'ativa', 'Ativa'
        PAUSADA = 'pausada', 'Pausada'
        CONCLUIDA = 'concluida', 'Concluída'
        CANCELADA = 'cancelada', 'Cancelada'

    empreendimento = models.ForeignKey(
        'empreendimentos.Empreendimento',
        on_delete=models.PROTECT,
        related_name='inscricoes',
        verbose_name='empreendimento',
    )
    trilha = models.ForeignKey(
        Trilha,
        on_delete=models.PROTECT,
        related_name='inscricoes',
        verbose_name='trilha',
    )
    status = models.CharField(
        'status', max_length=10, choices=Status.choices, default=Status.ATIVA,
    )
    inscrito_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='inscricoes_realizadas',
        verbose_name='inscrito por',
        help_text='Vazio = inscrição automática feita pelo sistema.',
    )
    inscrito_em = models.DateTimeField('inscrito em', auto_now_add=True)
    pausado_em = models.DateTimeField('pausado em', null=True, blank=True)
    cancelado_em = models.DateTimeField('cancelado em', null=True, blank=True)
    reativado_em = models.DateTimeField('reativado em', null=True, blank=True)
    concluido_em = models.DateTimeField('concluído em', null=True, blank=True)
    motivo = models.TextField('motivo', blank=True)

    class Meta:
        verbose_name = 'inscrição'
        verbose_name_plural = 'inscrições'
        constraints = [
            # INS-07: só uma inscrição ativa ou pausada por empreendimento e trilha.
            models.UniqueConstraint(
                fields=['empreendimento', 'trilha'],
                condition=models.Q(status__in=['ativa', 'pausada']),
                name='inscricao_unica_em_andamento',
            ),
        ]

    def __str__(self):
        return f'{self.empreendimento} → {self.trilha}'
