from django.conf import settings
from django.contrib.auth.middleware import LoginRequiredMiddleware
from django.contrib.auth.views import redirect_to_login


class ProtecaoLoginMiddleware(LoginRequiredMiddleware):
    """ACE-00, ACE-00b: toda rota exige login, e anônimo sempre vai ao login do sistema."""

    def get_login_url(self, view_func):
        return str(settings.LOGIN_URL)  # ignora o login próprio do /admin/ (F0, decisão 7.1)

    def process_response(self, request, response):
        if response.status_code == 404 and not request.user.is_authenticated:
            return redirect_to_login(request.get_full_path(), self.get_login_url(None))  # F0, 3.1.1
        return response
