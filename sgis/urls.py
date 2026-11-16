from django.contrib import admin
from django.urls import include, path, re_path

from usuarios import views

from .views import admin_login_view, robots_view, saude_view

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
    re_path(r'^usuarios/(?P<pk>\d+)/(?P<acao>desativar|reativar)/$', views.alterar_conta_view,
            name='alterar_conta'),
    path('conta/senha/', views.trocar_senha_view, name='trocar_senha'),
    path('trilhas/', include('trilhas.urls')),
    path('', views.home_view, name='home'),
]
