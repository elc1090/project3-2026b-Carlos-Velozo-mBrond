from allauth.account.adapter import DefaultAccountAdapter
from allauth.account.models import EmailAddress
from allauth.core.exceptions import ImmediateHttpResponse
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from allauth.socialaccount.models import SocialApp
from django.contrib import messages
from django.http import Http404
from django.shortcuts import redirect

from .models import Usuario


class ContaAdapter(DefaultAccountAdapter):
    def is_open_for_signup(self, request):
        return False

    def add_message(self, *args, **kwargs):
        """Silencia os avisos do allauth ("Conectado como..."); o SGIS dá os próprios."""


class ContaFederadaAdapter(DefaultSocialAccountAdapter):
    """Login pelo Google só para empreendedores que a IS já cadastrou."""

    def is_open_for_signup(self, request, sociallogin):
        return True

    def get_app(self, request, provider, client_id=None):
        """Sem credenciais configuradas, a rota do provedor responde 404, e não 500."""
        try:
            return super().get_app(request, provider, client_id)
        except SocialApp.DoesNotExist:
            raise Http404 from None

    def pre_social_login(self, request, sociallogin):
        usuario = sociallogin.user
        if usuario.pk is None:
            return
        if usuario.papel != Usuario.Papel.EMPREENDEDOR:
            self._recusar(request, 'O login com Google é só para empreendedores. Entre com e-mail e senha.')

        if not usuario.is_active:
            self._recusar(request, "Aguardando liberação pela Incubadora Social.")

        EmailAddress.objects.update_or_create(
            user=usuario, email=usuario.email, defaults={'verified': True, 'primary': True},
        )


    def populate_user(self, request, sociallogin, data):
        usuario = super().populate_user(request, sociallogin, data)

        usuario.nome = sociallogin.account.extra_data.get('name') or usuario.email.split('@')[0]
        usuario.papel = Usuario.Papel.EMPREENDEDOR
        return usuario

    def save_user(self, request, sociallogin, form=None):
        usuario = super().save_user(request, sociallogin, form)
        usuario.is_active = False
        usuario.save(update_fields=['is_active'])
        messages.success(request, 'Cadastro recebido. Aguarde a Incubadora Social liberar o seu acesso.')
        raise ImmediateHttpResponse(redirect('login'))



    def _recusar(self, request, mensagem):
        messages.error(request, mensagem)
        raise ImmediateHttpResponse(redirect('login'))