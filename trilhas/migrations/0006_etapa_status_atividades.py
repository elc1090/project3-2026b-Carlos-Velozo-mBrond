import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    """F3 · T1: etapa e status da trilha, dono opcional e atividades (plan.md, seção 3)."""

    dependencies = [
        ('trilhas', '0005_criar_trilha_pre_incubacao'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='trilha',
            name='etapa',
            field=models.CharField(
                blank=True,
                choices=[
                    ('pre_incubacao', 'Pré-incubação'),
                    ('incubacao', 'Incubação'),
                    ('desincubacao', 'Desincubação'),
                ],
                default='',
                help_text='Vazio = trilha personalizada.',
                max_length=20,
                verbose_name='etapa',
            ),
        ),
        migrations.AddField(
            model_name='trilha',
            name='status',
            field=models.CharField(
                choices=[
                    ('rascunho', 'Rascunho'),
                    ('publicada', 'Publicada'),
                    ('arquivada', 'Arquivada'),
                ],
                default='rascunho',
                max_length=10,
                verbose_name='status',
            ),
        ),
        migrations.AddField(
            model_name='trilha',
            name='publicada_em',
            field=models.DateTimeField(blank=True, null=True, verbose_name='publicada em'),
        ),
        migrations.AddField(
            model_name='trilha',
            name='arquivada_em',
            field=models.DateTimeField(blank=True, null=True, verbose_name='arquivada em'),
        ),
        migrations.AlterField(
            model_name='trilha',
            name='usuario_criador',
            field=models.ForeignKey(
                blank=True,
                help_text='Vazio nas trilhas de etapa: a dona é a IS, não um usuário.',
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name='trilhas_criadas',
                to=settings.AUTH_USER_MODEL,
                verbose_name='dono',
            ),
        ),
        migrations.CreateModel(
            name='AtividadeTrilha',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('titulo', models.CharField(max_length=200, verbose_name='título')),
                ('descricao', models.TextField(blank=True, verbose_name='descrição')),
                ('tipo', models.CharField(
                    choices=[('leitura', 'Leitura'), ('link', 'Link'), ('tarefa', 'Tarefa')],
                    max_length=10,
                    verbose_name='tipo',
                )),
                ('endereco', models.URLField(blank=True, verbose_name='endereço')),
                ('ordem', models.PositiveIntegerField(verbose_name='ordem')),
                ('obrigatoria', models.BooleanField(default=True, verbose_name='obrigatória')),
                ('exige_validacao', models.BooleanField(default=True, verbose_name='exige validação')),
                ('prazo_fixo', models.DateField(blank=True, null=True, verbose_name='prazo fixo')),
                ('dias_apos_inscricao', models.PositiveIntegerField(
                    blank=True, null=True, verbose_name='dias após a inscrição',
                )),
                ('criada_em', models.DateTimeField(auto_now_add=True, verbose_name='criada em')),
                ('arquivada_em', models.DateTimeField(
                    blank=True, help_text='Vazio = ativa.', null=True, verbose_name='arquivada em',
                )),
                ('trilha', models.ForeignKey(
                    on_delete=django.db.models.deletion.PROTECT,
                    related_name='atividades',
                    to='trilhas.trilha',
                    verbose_name='trilha',
                )),
            ],
            options={
                'verbose_name': 'atividade da trilha',
                'verbose_name_plural': 'atividades da trilha',
                'ordering': ['ordem', 'id'],
                'constraints': [
                    models.CheckConstraint(
                        condition=models.Q(('prazo_fixo__isnull', True), ('dias_apos_inscricao__isnull', True), _connector='OR'),
                        name='atividade_um_prazo',
                    ),
                    models.CheckConstraint(
                        condition=models.Q(('dias_apos_inscricao__isnull', True), ('dias_apos_inscricao__gt', 0), _connector='OR'),
                        name='atividade_dias_positivo',
                    ),
                    models.CheckConstraint(
                        condition=models.Q(models.Q(('tipo', 'link'), _negated=True), models.Q(('endereco', ''), _negated=True), _connector='OR'),
                        name='atividade_link_com_endereco',
                    ),
                ],
            },
        ),
    ]
