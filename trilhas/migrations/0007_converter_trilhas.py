from django.db import migrations
from django.utils import timezone

# Títulos das trilhas de etapa criadas pelo sistema (spec F3, seção 3.2).
TITULOS_ETAPA = {
    'pre_incubacao': 'Pré-incubação',
    'incubacao': 'Incubação',
    'desincubacao': 'Desincubação',
}


def converter(apps, schema_editor):
    """Spec F3, seção 6: a pré-incubação vira trilha de etapa publicada; o resto, personalizada publicada."""
    Trilha = apps.get_model('trilhas', 'Trilha')
    agora = timezone.now()

    Trilha.objects.filter(pre_incubacao=True).update(
        etapa='pre_incubacao', status='publicada', publicada_em=agora, usuario_criador=None,
    )
    Trilha.objects.filter(pre_incubacao=False).update(
        etapa='', status='publicada', publicada_em=agora,
    )

    for etapa, titulo in TITULOS_ETAPA.items():
        if not Trilha.objects.filter(etapa=etapa).exists():
            Trilha.objects.create(titulo=titulo, etapa=etapa, status='rascunho')


def desfazer(apps, schema_editor):
    Usuario = apps.get_model('usuarios', 'Usuario')
    Trilha = apps.get_model('trilhas', 'Trilha')
    AtividadeTrilha = apps.get_model('trilhas', 'AtividadeTrilha')

    dono = (
        Usuario.objects.filter(papel='is').order_by('id').first()
        or Usuario.objects.filter(is_superuser=True).order_by('id').first()
    )

    # Trilhas de etapa criadas aqui e nunca usadas voltam a não existir.
    novas = (
        Trilha.objects
        .filter(etapa__in=['incubacao', 'desincubacao'], inscricoes__isnull=True)
    )
    AtividadeTrilha.objects.filter(trilha__in=novas).delete()
    novas.delete()

    if Trilha.objects.exclude(etapa='').exists() and dono is None:
        raise RuntimeError(
            'Não há usuário IS nem superusuário para ser dono das trilhas de etapa '
            'ao desfazer a migração.'
        )

    Trilha.objects.filter(etapa='pre_incubacao').update(
        pre_incubacao=True, tipo='padrao', usuario_criador=dono,
    )
    # Trilhas de etapa que tinham inscrições não podem sumir: voltam como padrão.
    Trilha.objects.exclude(etapa__in=['', 'pre_incubacao']).update(
        tipo='padrao', usuario_criador=dono,
    )
    Trilha.objects.filter(etapa='').update(tipo='custom')


class Migration(migrations.Migration):

    dependencies = [
        ('trilhas', '0006_etapa_status_atividades'),
        ('usuarios', '0003_papel_empreendedor'),
    ]

    operations = [
        migrations.RunPython(converter, desfazer),
    ]
