"""Regras da F1 · Acesso e contas (specs/F1-acesso/spec.md, seção 3).

As views e o /admin/ só chamam estas funções, para que as regras fiquem num lugar só (Art. 7.5).
"""

from django.core.exceptions import PermissionDenied
from django.db import transaction

from empreendimentos.models import Empreendimento
from sgis.excecoes import RegraViolada

from .models import Usuario

# 3.6.1: as contas que a IS gerencia.
PAPEIS_DA_IS = (Usuario.Papel.PROFESSOR, Usuario.Papel.EMPREENDEDOR)


# Quem gerencia quem

def contas_geridas(usuario):
    """3.6.1 e 3.6.3: a IS gerencia professores e empreendedores; o admin, todas as contas."""
    if usuario.papel == Usuario.Papel.ADMIN:
        return Usuario.objects.all()
    if usuario.papel == Usuario.Papel.IS:
        return Usuario.objects.filter(papel__in=PAPEIS_DA_IS)
    return Usuario.objects.none()


def exigir_gestao(usuario, conta):
    """A-13 e A-19: conta fora do escopo de quem pede responde 403."""
    if not contas_geridas(usuario).filter(pk=conta.pk).exists():
        raise PermissionDenied


# Criação


def criar_conta(dados_conta, senha):
    """3.3: cria a conta com troca de senha obrigatória (3.3.5)."""
    conta = Usuario(**dados_conta, deve_trocar_senha=True)
    conta.set_password(senha)
    conta.save()
    return conta


@transaction.atomic
def criar_empreendedor(dados_conta, senha, dados_empreendimento):
    """3.3.4 e RN-01: o empreendedor e o empreendimento são criados juntos, ou nenhum."""
    conta = criar_conta({**dados_conta, 'papel': Usuario.Papel.EMPREENDEDOR}, senha)
    vincular_empreendimento(conta, dados_empreendimento)
    return conta


def vincular_empreendimento(conta, dados_empreendimento):
    """3.3.4: o empreendimento novo entra na pré-incubação pelo signal da F4."""
    return Empreendimento.objects.create(representante=conta, **dados_empreendimento)


# Senha e situação da conta. Nada apaga conta (3.6.4).

def redefinir_senha(conta, usuario, nova_senha):
    """3.5.4: a senha nova vale na hora, e o próximo acesso exige troca.

    Mudar a senha muda o hash da sessão, então as sessões abertas da conta terminam (A-13).
    """
    exigir_gestao(usuario, conta)
    conta.set_password(nova_senha)
    conta.deve_trocar_senha = True
    conta.save(update_fields=['password', 'deve_trocar_senha'])


def desativar(conta, usuario):
    """3.6.5 e 3.6.6: a conta desativada não entra e perde as sessões na próxima ação."""
    exigir_gestao(usuario, conta)
    if conta.pk == usuario.pk:
        raise RegraViolada('Você não pode desativar a sua própria conta.')
    if not conta.is_active:
        raise RegraViolada('Esta conta já está desativada.')
    if conta.papel == Usuario.Papel.ADMIN and not Usuario.objects.filter(
        papel=Usuario.Papel.ADMIN, is_active=True,
    ).exclude(pk=conta.pk).exists():
        raise RegraViolada('A última conta ativa de admin não pode ser desativada.')
    conta.is_active = False
    conta.save(update_fields=['is_active'])


def reativar(conta, usuario):
    """3.6.2: a conta reativada volta a entrar."""
    exigir_gestao(usuario, conta)
    if conta.is_active:
        raise RegraViolada('Esta conta já está ativa.')
    conta.is_active = True
    conta.save(update_fields=['is_active'])
