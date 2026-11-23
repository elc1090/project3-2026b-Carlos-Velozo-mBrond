from django.contrib.auth.signals import user_logged_in
from django.dispatch import receiver


METODO_POR_BACKEND = {
    'django.contrib.auth.backends.ModelBackend': 'senha',
    'allauth.account.auth_backends.AuthenticationBackend': 'google'
}


@receiver(user_logged_in)
def registrar_metodo_de_login(sender, request, user, **kwargs):
    """
    Guarda no request o método de login usado, para depois gravar no cookie
    """
    metodo = METODO_POR_BACKEND.get(getattr(user, 'backend', ''))
    if metodo:
        request.metodo_login = metodo