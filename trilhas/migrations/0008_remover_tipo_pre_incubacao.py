from django.db import migrations, models


class Migration(migrations.Migration):
    """F3 · T1: tira `tipo` e `pre_incubacao` e passa a garantir as regras de etapa e dono."""

    dependencies = [
        ('trilhas', '0007_converter_trilhas'),
    ]

    operations = [
        migrations.RemoveConstraint(
            model_name='trilha',
            name='trilha_pre_incubacao_unica',
        ),
        # Com default, a reversa consegue recriar a coluna em tabelas com dados.
        migrations.AlterField(
            model_name='trilha',
            name='tipo',
            field=models.CharField(
                choices=[('padrao', 'Padrão'), ('custom', 'Personalizada')],
                default='custom',
                max_length=10,
                verbose_name='tipo',
            ),
        ),
        migrations.RemoveField(
            model_name='trilha',
            name='tipo',
        ),
        migrations.RemoveField(
            model_name='trilha',
            name='pre_incubacao',
        ),
        migrations.AddConstraint(
            model_name='trilha',
            constraint=models.UniqueConstraint(
                condition=models.Q(('etapa', ''), _negated=True),
                fields=('etapa',),
                name='trilha_etapa_unica',
            ),
        ),
        migrations.AddConstraint(
            model_name='trilha',
            constraint=models.CheckConstraint(
                condition=models.Q(
                    models.Q(('etapa', ''), ('usuario_criador__isnull', False)),
                    models.Q(models.Q(('etapa', ''), _negated=True), ('usuario_criador__isnull', True)),
                    _connector='OR',
                ),
                name='trilha_dono_conforme_tipo',
            ),
        ),
    ]
