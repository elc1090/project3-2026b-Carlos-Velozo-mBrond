import logging

from django.db.models.signals import post_save
from django.dispatch import receiver

from empreendimentos.models import Empreendimento

from .models import Inscricao, Trilha

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Empreendimento)
def inscrever_na_pre_incubacao(sender, instance, created, raw=False, **kwargs):
    """Todo empreendimento novo entra automaticamente na trilha de pré-incubação."""
    if not created or raw:
        return

    trilha = Trilha.objects.filter(etapa=Trilha.Etapa.PRE_INCUBACAO).first()
    if trilha is None:
        logger.warning(
            'Nenhuma trilha de pré-incubação definida; %s não foi inscrito.', instance,
        )
        return

    Inscricao.objects.get_or_create(
        empreendimento=instance,
        trilha=trilha,
        defaults={'status': Inscricao.Status.ATIVA},
    )
