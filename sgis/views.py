from django.contrib.auth.decorators import login_not_required
from django.core.exceptions import PermissionDenied
from django.http import HttpResponse
from django.shortcuts import redirect

from usuarios.views import proximo_seguro


@login_not_required
def saude_view(request):
    """Verificação de saúde do Render: responde só `ok` (ACE-00a)."""
    return HttpResponse('ok', content_type='text/plain')


@login_not_required
def robots_view(request):
    """Pede a todos os buscadores que não indexem o site (ACE-00a)."""
    return HttpResponse('User-agent: *\nDisallow: /\n', content_type='text/plain')


def admin_login_view(request):
    """Sobrepõe o login próprio do /admin/: a entrada é o login do sistema (RN-16, decisão 7.1)."""
    if not request.user.is_staff:
        raise PermissionDenied
    return redirect(proximo_seguro(request) or 'admin:index')
