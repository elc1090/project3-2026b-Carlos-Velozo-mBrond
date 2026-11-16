from django.contrib import messages
from django.contrib.auth import login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_not_required, login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from empreendimentos.forms import EmpreendimentoCadastroForm
from sgis.excecoes import RegraViolada

from . import regras
from .decorators import papel_requerido
from .forms import (
    LoginForm,
    RedefinirSenhaForm,
    TrocarSenhaForm,
    UsuarioCadastroForm,
    UsuarioEdicaoForm,
)
from .models import Usuario


def proximo_seguro(request):
    """Devolve o `next` pedido, se ele for do próprio SGIS (RNF-01)."""
    proximo = request.POST.get('next') or request.GET.get('next')
    if proximo and url_has_allowed_host_and_scheme(
        proximo, allowed_hosts={request.get_host()}, require_https=request.is_secure(),
    ):
        return proximo
    return None


@login_not_required
def login_view(request):
    """Tela de login. Redireciona se já autenticado."""
    if request.user.is_authenticated:
        return redirect('home')

    form = LoginForm(data=request.POST or None, request=request)

    if request.method == 'POST' and form.is_valid():
        login(request, form.get_user())
        return redirect(proximo_seguro(request) or 'home')

    return render(request, 'usuarios/login.html', {'form': form})


def logout_view(request):
    """Encerra a sessão e volta ao login."""
    logout(request)
    return redirect('login')


@login_required
def home_view(request):
    """Página inicial após o login."""
    return render(request, 'usuarios/home.html')


@papel_requerido(Usuario.Papel.IS)
def criar_usuario_view(request):
    """IS cria um professor ou um empreendedor; o empreendedor vem com o empreendimento (ACE-05)."""
    form = UsuarioCadastroForm(request.POST or None)
    form_empreendimento = EmpreendimentoCadastroForm(request.POST or None, prefix='empreendimento')

    if request.method == 'POST' and form.is_valid():
        dados_conta = {campo: form.cleaned_data[campo] for campo in ('nome', 'email', 'papel')}
        senha = form.cleaned_data['senha']

        if dados_conta['papel'] != Usuario.Papel.EMPREENDEDOR:
            # Para os outros papéis, os dados do empreendimento são ignorados.
            conta = regras.criar_conta(dados_conta, senha)
            messages.success(request, f'Usuário "{conta.nome}" criado com sucesso.')
            return redirect('criar_usuario')

        if form_empreendimento.is_valid():
            conta = regras.criar_empreendedor(dados_conta, senha, form_empreendimento.cleaned_data)
            messages.success(
                request,
                f'Usuário "{conta.nome}" e empreendimento '
                f'"{form_empreendimento.cleaned_data["nome"]}" criados com sucesso.',
            )
            return redirect('criar_usuario')
    elif request.method == 'POST' and request.POST.get('papel') == Usuario.Papel.EMPREENDEDOR:
        form_empreendimento.is_valid()  # mostra os erros dos dois formulários de uma vez

    return render(request, 'usuarios/criar_usuario.html', {
        'form': form, 'form_empreendimento': form_empreendimento,
    })


# Gestão de contas pela IS (F1, 3.6). Toda conta recebida passa por regras.exigir_gestao.

FILTROS_STATUS = {'ativa': True, 'desativada': False}


@papel_requerido(Usuario.Papel.IS)
def contas_view(request):
    """ACE-09 e A-14: professores e empreendedores, com filtros por papel e por status."""
    contas = regras.contas_geridas(request.user).order_by('nome')

    papel = request.GET.get('papel', '')
    if papel in regras.PAPEIS_DA_IS:
        contas = contas.filter(papel=papel)
    else:
        papel = ''

    status = request.GET.get('status', '')
    if status in FILTROS_STATUS:
        contas = contas.filter(is_active=FILTROS_STATUS[status])
    else:
        status = ''

    return render(request, 'usuarios/contas.html', {
        'contas': contas,
        'papeis': [(valor, Usuario.Papel(valor).label) for valor in regras.PAPEIS_DA_IS],
        'papel_atual': papel,
        'status': [('ativa', 'Ativas'), ('desativada', 'Desativadas')],
        'status_atual': status,
    })


@papel_requerido(Usuario.Papel.IS)
def editar_conta_view(request, pk):
    """ACE-09 e A-15: nome e e-mail. O papel não muda (decisão 7.2)."""
    conta = get_object_or_404(Usuario, pk=pk)
    regras.exigir_gestao(request.user, conta)
    form = UsuarioEdicaoForm(request.POST or None, instance=conta)

    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, f'Conta de "{conta.nome}" atualizada.')
        return redirect('contas')

    return render(request, 'usuarios/editar_conta.html', {'form': form, 'conta': conta})


@papel_requerido(Usuario.Papel.IS)
def redefinir_senha_view(request, pk):
    """ACE-08 e A-13: senha nova, sessões encerradas e troca no próximo acesso."""
    conta = get_object_or_404(Usuario, pk=pk)
    regras.exigir_gestao(request.user, conta)
    form = RedefinirSenhaForm(request.POST or None, conta=conta)

    if request.method == 'POST' and form.is_valid():
        regras.redefinir_senha(conta, request.user, form.cleaned_data['nova_senha'])
        messages.success(request, f'Senha de "{conta.nome}" redefinida.')  # 3.4.2: sem a senha
        return redirect('contas')

    return render(request, 'usuarios/redefinir_senha.html', {'form': form, 'conta': conta})


@require_POST
@papel_requerido(Usuario.Papel.IS)
def alterar_conta_view(request, pk, acao):
    """ACE-10, ACE-11, A-16 e A-17: desativa ou reativa, sem apagar."""
    conta = get_object_or_404(Usuario, pk=pk)
    try:
        if acao == 'desativar':
            regras.desativar(conta, request.user)
            messages.success(request, f'Conta de "{conta.nome}" desativada.')
        else:
            regras.reativar(conta, request.user)
            messages.success(request, f'Conta de "{conta.nome}" reativada.')
    except RegraViolada as erro:
        messages.error(request, str(erro))
    return redirect('contas')


@login_required
def trocar_senha_view(request):
    """Usuário logado troca a própria senha (qualquer papel)."""
    form = TrocarSenhaForm(request.POST or None, user=request.user)

    if request.method == 'POST' and form.is_valid():
        request.user.set_password(form.cleaned_data['nova_senha'])
        request.user.save(update_fields=['password'])
        # O hash do usuário mudou: sem isto a sessão atual seria encerrada.
        update_session_auth_hash(request, request.user)
        messages.success(request, 'Senha alterada com sucesso.')
        return redirect('trocar_senha')

    return render(request, 'usuarios/trocar_senha.html', {'form': form})
