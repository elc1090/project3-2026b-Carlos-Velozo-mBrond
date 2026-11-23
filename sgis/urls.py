from django.contrib import admin
from django.urls import include, path, re_path
from django.contrib.auth.decorators import login_not_required
from django.views.generic import RedirectView


from usuarios import views

from .views import admin_login_view, robots_view, saude_view, rota_desativada_view, login_cancelado_view

_para_login = login_not_required(RedirectView.as_view(pattern_name='login'))



urlpatterns = [
    path('admin/login/', admin_login_view, name='admin_login'),  # antes do admin (decisão 7.1)
    path('admin/', admin.site.urls),
    path('saude/', saude_view, name='saude'),
    path('robots.txt', robots_view, name='robots'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('usuarios/', views.contas_view, name='contas'),
    path('usuarios/novo/', views.criar_usuario_view, name='criar_usuario'),
    path('usuarios/<int:pk>/editar/', views.editar_conta_view, name='editar_conta'),
    path('usuarios/<int:pk>/senha/', views.redefinir_senha_view, name='redefinir_senha'),
    path('usuarios/<int:pk>/aprovar/', views.aprovar_cadastro_view, name='aprovar_cadastro'),
    re_path(r'^usuarios/(?P<pk>\d+)/(?P<acao>desativar|reativar)/$', views.alterar_conta_view,
            name='alterar_conta'),
    path('conta/senha/', views.trocar_senha_view, name='trocar_senha'),
    path('trilhas/', include('trilhas.urls')),
    path('', views.home_view, name='home'),
    path('accounts/login/', _para_login, name="para_login"),
    path('accounts/signup/', _para_login, name="para_login"),
    re_path(r'^accounts/(password|email|confirm-email)/', rota_desativada_view),
    path('accounts/3rdparty/', rota_desativada_view),
    path('accounts/3rdparty/login/cancelled/', login_cancelado_view),
    path('accounts/', include('allauth.urls')),

]
