from django.urls import path, re_path

from . import views

app_name = 'trilhas'

urlpatterns = [
    path('', views.minhas_trilhas_view, name='minhas'),
    path('todas/', views.todas_trilhas_view, name='todas'),
    path('inscritas/', views.trilhas_inscritas_view, name='inscritas'),
    path('nova/', views.criar_trilha_view, name='criar'),
    path('<int:pk>/', views.detalhe_trilha_view, name='detalhe'),
    path('<int:pk>/editar/', views.editar_trilha_view, name='editar'),
    re_path(
        r'^(?P<pk>\d+)/(?P<acao>publicar|arquivar)/$',
        views.acao_trilha_view,
        name='acao',
    ),
    path('<int:pk>/atividades/nova/', views.criar_atividade_view, name='atividade_criar'),
    path('atividades/<int:pk>/editar/', views.editar_atividade_view, name='atividade_editar'),
    path('atividades/<int:pk>/apagar/', views.acao_atividade_view, {'acao': 'apagar'}, name='atividade_apagar'),
    path('atividades/<int:pk>/arquivar/', views.acao_atividade_view, {'acao': 'arquivar'}, name='atividade_arquivar'),
    re_path(
        r'^atividades/(?P<pk>\d+)/mover/(?P<direcao>cima|baixo)/$',
        views.mover_atividade_view,
        name='atividade_mover',
    ),
    path('inscricoes/', views.inscricoes_view, name='inscricoes'),
    re_path(
        r'^inscricoes/(?P<pk>\d+)/(?P<acao>pausar|reativar|cancelar|concluir)/$',
        views.alterar_inscricao_view,
        name='alterar_inscricao',
    ),
]
