import django.utils.timezone
from django.db import migrations, models


def marcar_contas_is(apps, schema_editor):
    """F1, decisão 7.7 e A-20: as contas da IS trocam a senha no próximo acesso."""
    Usuario = apps.get_model('usuarios', 'Usuario')
    Usuario.objects.filter(papel='is').update(deve_trocar_senha=True)


def normalizar_emails(apps, schema_editor):
    """ACE-01: e-mails existentes passam a ficar em minúsculas.

    Se dois e-mails ficarem iguais, para sem alterar nada: a IS decide qual conta fica.
    """
    Usuario = apps.get_model('usuarios', 'Usuario')
    vistos = {}
    for pk, email in Usuario.objects.values_list('pk', 'email'):
        normalizado = email.strip().lower()
        if normalizado in vistos:
            raise RuntimeError(
                f'As contas {vistos[normalizado]} e {pk} ficariam com o mesmo e-mail. '
                'Decida qual conta fica antes de migrar.'
            )
        vistos[normalizado] = pk

    for pk, email in Usuario.objects.values_list('pk', 'email'):
        if email != email.strip().lower():
            Usuario.objects.filter(pk=pk).update(email=email.strip().lower())


class Migration(migrations.Migration):

    dependencies = [
        ('usuarios', '0003_papel_empreendedor'),
    ]

    operations = [
        migrations.AddField(
            model_name='usuario',
            name='deve_trocar_senha',
            field=models.BooleanField(default=False, verbose_name='deve trocar a senha'),
        ),
        # Contas antigas não têm a data original: recebem a data da migração (plano, seção 3).
        migrations.AddField(
            model_name='usuario',
            name='criado_em',
            field=models.DateTimeField(
                auto_now_add=True, default=django.utils.timezone.now, verbose_name='criado em',
            ),
            preserve_default=False,
        ),
        # As reversas não fazem nada: o campo sai com o AddField, e a grafia original não é guardada.
        migrations.RunPython(marcar_contas_is, migrations.RunPython.noop),
        migrations.RunPython(normalizar_emails, migrations.RunPython.noop),
    ]
