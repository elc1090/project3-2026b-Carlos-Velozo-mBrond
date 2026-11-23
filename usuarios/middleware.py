from django.conf import settings

COOKIE_METODO_LOGIN = 'sgis_ultimo_login'

class UltimoMetodoLoginMiddleware:

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        metodo = getattr(request, 'metodo_login', None)
        if metodo:
            response.set_cookie(
                COOKIE_METODO_LOGIN, metodo,
                max_age= 60 * 60 * 24 * 31,
                httponly=True,
                samesite='Lax',
                secure=not settings.DEBUG,
            )
        return response