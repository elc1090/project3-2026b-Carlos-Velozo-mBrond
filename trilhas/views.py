from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from usuarios.decorators import papel_requerido
from usuarios.models import Usuario

from . import regras
from .forms import AtividadeForm, AtividadeTextoForm, InscricaoForm, TrilhaForm
from .models import AtividadeTrilha, Inscricao, Trilha
from .regras import RegraViolada


@papel_requerido(Usuario.Papel.PROFESSOR)
def minhas_trilhas_view(request):
    """TRL-10 (spec 3.6): as trilhas do professor, as de etapa e as de outros nos empreendimentos que atende."""
    visiveis = regras.trilhas_visiveis(request.user).select_related('usuario_criador')
    return render(request, 'trilhas/minhas_trilhas.html', {
        'minhas': visiveis.filter(usuario_criador=request.user).order_by('-id'),
        'de_etapa': visiveis.exclude(etapa='').order_by('id'),
        'de_outros': (
            visiveis.filter(etapa='').exclude(usuario_criador=request.user).order_by('titulo')
        ),
    })


@papel_requerido(Usuario.Papel.PROFESSOR, Usuario.Papel.IS)
def criar_trilha_view(request):
    """A-01, A-03, A-04: professor ou IS cria trilha personalizada; etapa, status e dono vêm do servidor."""
    form = TrilhaForm(request.POST or None)

    if request.method == 'POST' and form.is_valid():
        trilha = form.save(commit=False)
        trilha.usuario_criador = request.user
        trilha.save()
        messages.success(request, f'Trilha "{trilha.titulo}" criada em rascunho.')
        return redirect('trilhas:detalhe', pk=trilha.pk)

    return render(request, 'trilhas/criar_trilha.html', {'form': form})


@login_required
def detalhe_trilha_view(request, pk):
    """TRL-10: dados, estado e atividades da trilha, para quem pode vê-la (senão, 403)."""
    trilha = get_object_or_404(Trilha.objects.select_related('usuario_criador'), pk=pk)
    if not regras.pode_ver(request.user, trilha):
        raise PermissionDenied

    atividades = list(trilha.atividades.all())
    pode_editar = (
        regras.pode_editar(request.user, trilha)
        and trilha.status != Trilha.Status.ARQUIVADA
    )
    return render(request, 'trilhas/detalhe.html', {
        'trilha': trilha,
        'ativas': [a for a in atividades if a.arquivada_em is None],
        'arquivadas': [a for a in atividades if a.arquivada_em is not None],
        'pode_editar': pode_editar,
        'exige_confirmacao': regras.exige_confirmacao(request.user, trilha),
        'pode_publicar': pode_editar and trilha.status == Trilha.Status.RASCUNHO,
        'pode_arquivar': (
            pode_editar and not trilha.e_de_etapa
            and trilha.status == Trilha.Status.PUBLICADA
        ),
    })


def _falta_confirmacao(request, trilha):
    """A-18 (spec 3.3.5, decisão 7.7): a IS só altera trilha de professor depois de confirmar."""
    return (
        request.method == 'POST'
        and regras.exige_confirmacao(request.user, trilha)
        and request.POST.get('confirmar') != '1'
    )


def _pedir_confirmacao(request, trilha, descricao):
    """Página intermediária em que a IS confirma uma ação sobre a trilha de um professor."""
    return render(request, 'trilhas/confirmar_acao.html', {
        'trilha': trilha,
        'descricao': descricao,
        'acao_url': request.path,
    })


@login_required
def editar_trilha_view(request, pk):
    """TRL-06, TRL-07: título e descrição, pelo dono ou pela IS (A-14, A-16, A-17, A-19)."""
    trilha = get_object_or_404(Trilha, pk=pk)
    try:
        regras.exigir_edicao(request.user, trilha)
    except RegraViolada as erro:
        messages.error(request, str(erro))
        return redirect('trilhas:detalhe', pk=trilha.pk)

    form = TrilhaForm(request.POST or None, instance=trilha)
    falta_confirmacao = _falta_confirmacao(request, trilha)
    if request.method == 'POST' and form.is_valid() and not falta_confirmacao:
        form.save()
        messages.success(request, 'Trilha atualizada.')
        return redirect('trilhas:detalhe', pk=trilha.pk)

    return render(request, 'trilhas/criar_trilha.html', {
        'form': form,
        'trilha': trilha,
        'exige_confirmacao': regras.exige_confirmacao(request.user, trilha),
        'confirmacao_faltando': falta_confirmacao,
    })


# Ações de estado da trilha: nome da rota -> (função de regras.py, mensagem de sucesso, descrição).
ACOES_TRILHA = {
    'publicar': (regras.publicar, 'Trilha publicada.', 'publicar esta trilha'),
    'arquivar': (regras.arquivar, 'Trilha arquivada.', 'arquivar esta trilha'),
}


@require_POST
@login_required
def acao_trilha_view(request, pk, acao):
    """TRL-05: publicar (A-09, A-10) ou arquivar (A-03, A-15) a trilha."""
    trilha = get_object_or_404(Trilha.objects.select_related('usuario_criador'), pk=pk)
    funcao, sucesso, descricao = ACOES_TRILHA[acao]
    if _falta_confirmacao(request, trilha):
        return _pedir_confirmacao(request, trilha, descricao)
    try:
        funcao(trilha, request.user)
    except RegraViolada as erro:
        messages.error(request, str(erro))
    else:
        messages.success(request, sucesso)
    return redirect('trilhas:detalhe', pk=trilha.pk)


@login_required
def criar_atividade_view(request, pk):
    """TRL-04, TRL-06: nova atividade no fim da trilha, em rascunho ou publicada (A-05 a A-08, A-12)."""
    trilha = get_object_or_404(Trilha, pk=pk)
    try:
        regras.exigir_edicao(request.user, trilha)
    except RegraViolada as erro:
        messages.error(request, str(erro))
        return redirect('trilhas:detalhe', pk=trilha.pk)

    form = AtividadeForm(request.POST or None)
    falta_confirmacao = _falta_confirmacao(request, trilha)
    if request.method == 'POST' and form.is_valid() and not falta_confirmacao:
        try:
            regras.acrescentar_atividade(trilha, request.user, form.cleaned_data)
        except RegraViolada as erro:
            messages.error(request, str(erro))
        else:
            messages.success(request, 'Atividade acrescentada.')
        return redirect('trilhas:detalhe', pk=trilha.pk)

    return render(request, 'trilhas/atividade_form.html', {
        'form': form,
        'trilha': trilha,
        'exige_confirmacao': regras.exige_confirmacao(request.user, trilha),
        'confirmacao_faltando': falta_confirmacao,
    })


@login_required
def editar_atividade_view(request, pk):
    """TRL-06: em rascunho, tudo; com a trilha publicada, só os textos (A-11)."""
    atividade = get_object_or_404(AtividadeTrilha.objects.select_related('trilha'), pk=pk)
    trilha = atividade.trilha
    try:
        regras.exigir_edicao(request.user, trilha)
    except RegraViolada as erro:
        messages.error(request, str(erro))
        return redirect('trilhas:detalhe', pk=trilha.pk)

    classe = AtividadeForm if trilha.status == Trilha.Status.RASCUNHO else AtividadeTextoForm
    form = classe(request.POST or None, instance=atividade)
    falta_confirmacao = _falta_confirmacao(request, trilha)
    if request.method == 'POST' and form.is_valid() and not falta_confirmacao:
        form.save()
        messages.success(request, 'Atividade atualizada.')
        return redirect('trilhas:detalhe', pk=trilha.pk)

    return render(request, 'trilhas/atividade_form.html', {
        'form': form,
        'trilha': trilha,
        'atividade': atividade,
        'exige_confirmacao': regras.exige_confirmacao(request.user, trilha),
        'confirmacao_faltando': falta_confirmacao,
    })


# Ações sobre uma atividade: nome -> (função de regras.py, mensagem de sucesso, descrição).
ACOES_ATIVIDADE = {
    'apagar': (regras.apagar_atividade, 'Atividade apagada.', 'apagar a atividade'),
    'arquivar': (regras.arquivar_atividade, 'Atividade arquivada.', 'arquivar a atividade'),
}


@require_POST
@login_required
def acao_atividade_view(request, pk, acao):
    """RN-10: apagar só em rascunho; depois disso, arquivar (A-13)."""
    atividade = get_object_or_404(AtividadeTrilha.objects.select_related('trilha'), pk=pk)
    trilha = atividade.trilha
    funcao, sucesso, descricao = ACOES_ATIVIDADE[acao]
    if _falta_confirmacao(request, trilha):
        return _pedir_confirmacao(request, trilha, f'{descricao} "{atividade.titulo}"')
    try:
        funcao(atividade, request.user)
    except RegraViolada as erro:
        messages.error(request, str(erro))
    else:
        messages.success(request, sucesso)
    return redirect('trilhas:detalhe', pk=trilha.pk)


@require_POST
@login_required
def mover_atividade_view(request, pk, direcao):
    """TRL-08: sobe ou desce a atividade na trilha, só em rascunho (A-23)."""
    atividade = get_object_or_404(AtividadeTrilha.objects.select_related('trilha'), pk=pk)
    trilha = atividade.trilha
    if _falta_confirmacao(request, trilha):
        sentido = 'para cima' if direcao == 'cima' else 'para baixo'
        return _pedir_confirmacao(request, trilha, f'mover a atividade "{atividade.titulo}" {sentido}')
    try:
        regras.mover_atividade(atividade, request.user, direcao)
    except RegraViolada as erro:
        messages.error(request, str(erro))
    return redirect('trilhas:detalhe', pk=trilha.pk)


# Filtro por tipo na lista de todas as trilhas: valor do parâmetro -> (rótulo, filtro).
FILTROS_TIPO = {
    'etapa': ('De etapa', ~Q(etapa='')),
    'personalizada': ('Personalizadas', Q(etapa='')),
}


@papel_requerido(Usuario.Papel.IS)
def todas_trilhas_view(request):
    """TRL-10: IS vê todas as trilhas, com filtros por tipo e por estado."""
    trilhas = Trilha.objects.select_related('usuario_criador').order_by('-id')

    tipo = request.GET.get('tipo', '')
    if tipo in FILTROS_TIPO:
        trilhas = trilhas.filter(FILTROS_TIPO[tipo][1])
    else:
        tipo = ''

    estado = request.GET.get('estado', '')
    if estado in Trilha.Status.values:
        trilhas = trilhas.filter(status=estado)
    else:
        estado = ''

    return render(request, 'trilhas/todas_trilhas.html', {
        'trilhas': trilhas,
        'tipos': [(valor, rotulo) for valor, (rotulo, _) in FILTROS_TIPO.items()],
        'tipo_atual': tipo,
        'estados': Trilha.Status.choices,
        'estado_atual': estado,
    })


@papel_requerido(Usuario.Papel.IS)
def inscricoes_view(request):
    """INS-01: IS lista as inscrições e inscreve empreendimentos em trilhas personalizadas."""
    form = InscricaoForm(request.POST or None)

    if request.method == 'POST' and form.is_valid():
        try:
            inscricao = regras.inscrever(
                form.cleaned_data['empreendimento'], form.cleaned_data['trilha'], request.user,
            )
        except RegraViolada as erro:
            messages.error(request, str(erro))
        else:
            messages.success(
                request,
                f'{inscricao.empreendimento} inscrito na trilha "{inscricao.trilha}".',
            )
        return redirect('trilhas:inscricoes')

    inscricoes = (
        Inscricao.objects
        .select_related('empreendimento', 'trilha', 'inscrito_por')
        .order_by('-inscrito_em')
    )
    return render(request, 'trilhas/inscricoes.html', {
        'form': form,
        'inscricoes': inscricoes,
    })


@require_POST
@papel_requerido(Usuario.Papel.IS)
def alterar_inscricao_view(request, pk, acao):
    """INS-06: IS pausa, reativa, cancela ou conclui uma inscrição. O registro nunca é apagado."""
    inscricao = get_object_or_404(Inscricao.objects.select_related('trilha'), pk=pk)
    try:
        regras.alterar_status(inscricao, request.user, acao, request.POST.get('motivo', ''))
    except RegraViolada as erro:
        messages.error(request, str(erro))
    else:
        messages.success(
            request, f'Inscrição {inscricao} atualizada: {inscricao.get_status_display()}.',
        )
    return redirect('trilhas:inscricoes')


@papel_requerido(Usuario.Papel.EMPREENDEDOR)
def trilhas_inscritas_view(request):
    """Empreendedor vê as trilhas em que seu empreendimento está inscrito (canceladas ficam ocultas)."""
    inscricoes = (
        Inscricao.objects
        .filter(
            empreendimento__representante=request.user,
            empreendimento__desativado_em__isnull=True,
        )
        .exclude(status=Inscricao.Status.CANCELADA)
        .select_related('empreendimento', 'trilha')
        .order_by('empreendimento__nome', '-inscrito_em')
    )
    return render(request, 'trilhas/trilhas_inscritas.html', {'inscricoes': inscricoes})
