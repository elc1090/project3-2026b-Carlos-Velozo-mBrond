from django.db import migrations, models


def concluidas_viram_canceladas(apps, schema_editor):
    """Reversa (plano da F4, seção 3): o esquema antigo não conhece Concluída.

    Duas inscrições concluídas no mesmo par quebrariam a restrição antiga, então as
    concluídas viram canceladas, com `cancelado_em = concluido_em`. Nada é apagado, mas
    a reversa perde a diferença entre os dois status e as datas de reativação.
    """
    Inscricao = apps.get_model('trilhas', 'Inscricao')
    for inscricao in Inscricao.objects.filter(status='concluida'):
        inscricao.status = 'cancelada'
        inscricao.cancelado_em = inscricao.concluido_em
        inscricao.save(update_fields=['status', 'cancelado_em'])


class Migration(migrations.Migration):
    """INS-06 e INS-07: status Concluída e reinscrição depois de concluir ou cancelar."""

    dependencies = [
        ('trilhas', '0008_remover_tipo_pre_incubacao'),
    ]

    operations = [
        # 1. Campos novos.
        migrations.AddField(
            model_name='inscricao',
            name='reativado_em',
            field=models.DateTimeField(blank=True, null=True, verbose_name='reativado em'),
        ),
        migrations.AddField(
            model_name='inscricao',
            name='concluido_em',
            field=models.DateTimeField(blank=True, null=True, verbose_name='concluído em'),
        ),
        # 2. Nova opção de status.
        migrations.AlterField(
            model_name='inscricao',
            name='status',
            field=models.CharField(
                choices=[
                    ('ativa', 'Ativa'),
                    ('pausada', 'Pausada'),
                    ('concluida', 'Concluída'),
                    ('cancelada', 'Cancelada'),
                ],
                default='ativa',
                max_length=10,
                verbose_name='status',
            ),
        ),
        # 3. Sai a restrição antiga.
        migrations.RemoveConstraint(
            model_name='inscricao',
            name='inscricao_unica_nao_cancelada',
        ),
        # 4. Para frente nada muda. Na volta, roda depois de a restrição nova sair,
        # antes de a antiga voltar e com `concluido_em` ainda existente.
        migrations.RunPython(migrations.RunPython.noop, concluidas_viram_canceladas),
        # 5. Entra a restrição nova, mais permissiva que a antiga.
        migrations.AddConstraint(
            model_name='inscricao',
            constraint=models.UniqueConstraint(
                condition=models.Q(status__in=['ativa', 'pausada']),
                fields=('empreendimento', 'trilha'),
                name='inscricao_unica_em_andamento',
            ),
        ),
    ]
