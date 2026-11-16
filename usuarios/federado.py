from allauth.account.adapter import DefaultAccountAdapter
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter

from .models import Usuario

class ContaAdapter(DefaultAccountAdapter):
    def is_open_for_signup(self, request):
        return False

class ContaFederadaAdapter(DefaultSocialAccountAdapter):
    def is_open_for_signup(self, request, sociallogin):
        return True
    
    def populate_user(self, request, sociallogin, data):
        user = super().populate_user(request, sociallogin, data)
        extra = sociallogin.account.extra_data
        user.nome = extra.get('name') or user.email.split('@')[0]
        user.papel = Usuario.Papel.EMPREENDEDOR
        return user

