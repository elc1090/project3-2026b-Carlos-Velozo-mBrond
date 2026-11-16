"""Regras das trilhas e das inscrições: quem pode e quando pode.

F3 · Trilhas (specs/F3-trilhas/spec.md, seção 3) e F4 · Inscrição e etapas
(specs/F4-inscricao/spec.md, seção 3). As views só chamam estas funções. Falta de permissão (quem) levanta `PermissionDenied`,
que vira 403; condição de estado não atendida (quando) levanta `RegraViolada`, cuja
mensagem é mostrada ao usuário.
"""

from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.db.models import Max, Q
from django.utils import timezone

from empreendimentos.models import Empreendimento
from sgis.excecoes import RegraViolada
from usuarios.models import Usuario

from .models import AtividadeTrilha, Inscricao, Trilha

# Campos de atividade que podem mudar em cada estado da trilha (spec 3.5).
CAMPOS_ATIVIDADE = (
    'titulo', 'descricao', 'tipo', 'endereco', 'obrigatoria',
    'exige_validacao', 'prazo_fixo', 'dias_apos_inscricao',
)
CAMPOS_TEXTO_ATIVIDADE = ('titulo', 'descricao', 'endereco')


# Quem é quem

def e_is(usuario):
    return usuario.is_authenticated and usuario.papel == Usuario.Papel.IS


def e_dono(usuario, trilha):
    """TRL-01: a dona da trilha de etapa é a IS (papel); a da personalizada, quem a criou."""
    if trilha.e_de_etapa:
        return e_is(usuario)
    return usuario.is_authenticated and trilha.usuario_criador_id == usuario.pk


def empreendimentos_atendidos(professor):
    """Vocabulário da spec mãe: inscritos, em qualquer status, em trilhas do professor."""
    return Empreendimento.objects.filter(
        inscricoes__trilha__usuario_criador=professor,
    ).distinct()


# Ver

def trilhas_visiveis(usuario):
    """TRL-10 (spec 3.6): as trilhas que cada papel pode ver."""
    if not usuario.is_authenticated:
        return Trilha.objects.none()

    if usuario.papel == Usuario.Papel.IS:
        return Trilha.objects.all()

    if usuario.papel == Usuario.Papel.PROFESSOR:
        de_outros = (
            Q(etapa='')
            & Q(status__in=[Trilha.Status.PUBLICADA, Trilha.Status.ARQUIVADA])
            & Q(inscricoes__empreendimento__in=empreendimentos_atendidos(usuario))
        )
        return Trilha.objects.filter(
            Q(usuario_criador=usuario) | ~Q(etapa='') | de_outros,
        ).distinct()

    if usuario.papel == Usuario.Papel.EMPREENDEDOR:
        return (
            Trilha.objects
            .filter(inscricoes__empreendimento__representante=usuario)
            .exclude(status=Trilha.Status.RASCUNHO)
            .distinct()
        )

    return Trilha.objects.none()  # admin: RN-16


def pode_ver(usuario, trilha):
    """TRL-10."""
    return trilhas_visiveis(usuario).filter(pk=trilha.pk).exists()


# Editar

def pode_editar(usuario, trilha):
    """TRL-07 (spec 3.3): o dono e a IS. Nunca outro professor, empreendedor ou admin."""
    return e_dono(usuario, trilha) or e_is(usuario)


def exige_confirmacao(usuario, trilha):
    """TRL-07 (spec 3.3.5, decisão 7.7): a IS confirma antes de alterar trilha de professor."""
    return (
        e_is(usuario)
        and not trilha.e_de_etapa
        and trilha.usuario_criador.papel == Usuario.Papel.PROFESSOR
    )


def exigir_edicao(usuario, trilha):
    """TRL-07 e A-14: quem não pode editar recebe 403; trilha arquivada não muda."""
    if not pode_editar(usuario, trilha):
        raise PermissionDenied
    if trilha.status == Trilha.Status.ARQUIVADA:
        raise RegraViolada('Trilha arquivada não pode ser alterada.')  # A-14


# Estados

def publicar(trilha, usuario):
    """TRL-05: rascunho → publicada, com pelo menos uma atividade ativa (A-09, A-10)."""
    exigir_edicao(usuario, trilha)
    if trilha.status != Trilha.Status.RASCUNHO:
        raise RegraViolada('Só uma trilha em rascunho pode ser publicada.')
    if not trilha.atividades.filter(arquivada_em__isnull=True).exists():
        raise RegraViolada('Acrescente pelo menos uma atividade antes de publicar.')
    trilha.status = Trilha.Status.PUBLICADA
    trilha.publicada_em = timezone.now()
    trilha.save(update_fields=['status', 'publicada_em'])


def arquivar(trilha, usuario):
    """TRL-05: publicada → arquivada; só personalizada e sem inscrição ativa ou pausada (A-03, A-15)."""
    exigir_edicao(usuario, trilha)
    if trilha.e_de_etapa:
        raise RegraViolada('Trilhas de etapa não podem ser arquivadas.')
    if trilha.status != Trilha.Status.PUBLICADA:
        raise RegraViolada('Só uma trilha publicada pode ser arquivada.')
    if trilha.inscricoes.filter(
        status__in=[Inscricao.Status.ATIVA, Inscricao.Status.PAUSADA],
    ).exists():
        raise RegraViolada(
            'A trilha tem inscrições ativas ou pausadas. '
            'Peça à IS para concluí-las ou cancelá-las antes de arquivar.'
        )
    trilha.status = Trilha.Status.ARQUIVADA
    trilha.arquivada_em = timezone.now()
    trilha.save(update_fields=['status', 'arquivada_em'])


# Atividades

def campos_editaveis(trilha):
    """TRL-06 (spec 3.5): em rascunho, todos; publicada, só os textos; arquivada, nenhum (A-11)."""
    if trilha.status == Trilha.Status.RASCUNHO:
        return CAMPOS_ATIVIDADE
    if trilha.status == Trilha.Status.PUBLICADA:
        return CAMPOS_TEXTO_ATIVIDADE
    return ()


@transaction.atomic
def acrescentar_atividade(trilha, usuario, dados):
    """TRL-04, TRL-06: atividade nova entra no fim, em rascunho ou publicada (A-08, A-12)."""
    exigir_edicao(usuario, trilha)
    ultima = trilha.atividades.aggregate(maior=Max('ordem'))['maior'] or 0
    campos = {campo: valor for campo, valor in dados.items() if campo in CAMPOS_ATIVIDADE}
    return AtividadeTrilha.objects.create(trilha=trilha, ordem=ultima + 1, **campos)


def apagar_atividade(atividade, usuario):
    """RN-10: só se apaga atividade de trilha em rascunho; depois disso, só arquivar (A-13)."""
    exigir_edicao(usuario, atividade.trilha)
    if atividade.trilha.status != Trilha.Status.RASCUNHO:
        raise RegraViolada('Atividade de trilha publicada não pode ser apagada; arquive-a.')
    atividade.delete()


def arquivar_atividade(atividade, usuario):
    """RN-10: atividade arquivada sai da trilha, mas continua no histórico de quem a fez."""
    exigir_edicao(usuario, atividade.trilha)
    if atividade.arquivada_em is not None:
        raise RegraViolada('Esta atividade já está arquivada.')
    atividade.arquivada_em = timezone.now()
    atividade.save(update_fields=['arquivada_em'])


@transaction.atomic
def mover_atividade(atividade, usuario, direcao):
    """TRL-08: troca a atividade de lugar com a vizinha, só em rascunho (A-23)."""
    trilha = atividade.trilha
    exigir_edicao(usuario, trilha)
    if trilha.status != Trilha.Status.RASCUNHO:
        raise RegraViolada('A ordem só pode ser mudada enquanto a trilha está em rascunho.')

    ativas = trilha.atividades.filter(arquivada_em__isnull=True)
    if direcao == 'cima':
        vizinha = ativas.filter(ordem__lt=atividade.ordem).order_by('-ordem').first()
    elif direcao == 'baixo':
        vizinha = ativas.filter(ordem__gt=atividade.ordem).order_by('ordem').first()
    else:
        raise ValueError(f'Direção inválida: {direcao}')

    if vizinha is None:
        return  # já é a primeira (ou a última)
    atividade.ordem, vizinha.ordem = vizinha.ordem, atividade.ordem
    atividade.save(update_fields=['ordem'])
    vizinha.save(update_fields=['ordem'])


# F4 · Inscrição e etapas

ETAPAS_EM_ORDEM = (Trilha.Etapa.PRE_INCUBACAO, Trilha.Etapa.INCUBACAO, Trilha.Etapa.DESINCUBACAO)
STATUS_EM_ANDAMENTO = (Inscricao.Status.ATIVA, Inscricao.Status.PAUSADA)


# Consultas: a etapa é sempre calculada, nunca gravada (INS-05)

def trilhas_inscriviveis():
    """INS-01 (spec 3.1.2): só trilhas personalizadas publicadas recebem inscrição à mão."""
    return Trilha.objects.filter(etapa='', status=Trilha.Status.PUBLICADA)


def inscricao_de_etapa(empreendimento):
    """3.2.2: a inscrição ativa ou pausada em trilha de etapa, ou None."""
    return (
        empreendimento.inscricoes
        .exclude(trilha__etapa='')
        .filter(status__in=STATUS_EM_ANDAMENTO)
        .select_related('trilha')
        .first()
    )


def etapa_atual(empreendimento):
    """INS-05 e A-16: a etapa dessa inscrição; None é "sem etapa". Pausada conta como etapa."""
    inscricao = inscricao_de_etapa(empreendimento)
    return inscricao.trilha.etapa if inscricao else None


def incubacao_concluida(empreendimento):
    """INS-11 (3.4.6): sem etapa, e a inscrição de etapa mais recente é a Desincubação concluída."""
    if inscricao_de_etapa(empreendimento) is not None:
        return False
    ultima = (
        empreendimento.inscricoes
        .exclude(trilha__etapa='')
        .select_related('trilha')
        .order_by('-inscrito_em', '-pk')
        .first()
    )
    return (
        ultima is not None
        and ultima.trilha.etapa == Trilha.Etapa.DESINCUBACAO
        and ultima.status == Inscricao.Status.CONCLUIDA
    )


def proxima_etapa(etapa):
    """3.4.2: a etapa seguinte, ou None a partir da Desincubação."""
    posicao = ETAPAS_EM_ORDEM.index(etapa)
    return ETAPAS_EM_ORDEM[posicao + 1] if posicao + 1 < len(ETAPAS_EM_ORDEM) else None


# Inscrever

def _criar_inscricao(empreendimento, trilha, inscrito_por):
    """Único ponto em que uma inscrição nasce (plano da F4, seção 4).

    A F5 vai criar aqui as execuções das atividades (EXE-01). `inscrito_por` vazio é a
    inscrição automática (3.3.3).
    """
    return Inscricao.objects.create(
        empreendimento=empreendimento, trilha=trilha, inscrito_por=inscrito_por,
    )


def inscrever(empreendimento, trilha, usuario):
    """INS-01, INS-07 (spec 3.1): a IS inscreve um empreendimento ativo numa trilha
    personalizada publicada, sem duplicar uma inscrição ativa ou pausada (A-02, A-03, A-13)."""
    if not e_is(usuario):
        raise PermissionDenied
    if empreendimento.desativado_em is not None:
        raise RegraViolada('Empreendimento desativado não pode ser inscrito.')
    if not trilhas_inscriviveis().filter(pk=trilha.pk).exists():
        raise RegraViolada('Escolha uma trilha personalizada publicada.')
    if empreendimento.inscricoes.filter(trilha=trilha, status__in=STATUS_EM_ANDAMENTO).exists():
        raise RegraViolada('Este empreendimento já está inscrito nesta trilha.')
    return _criar_inscricao(empreendimento, trilha, usuario)


# Status

# Transições permitidas (spec 3.5): ação -> (status de origem, status de destino, campo da data).
TRANSICOES_INSCRICAO = {
    'pausar': ({Inscricao.Status.ATIVA}, Inscricao.Status.PAUSADA, 'pausado_em'),
    'reativar': ({Inscricao.Status.PAUSADA}, Inscricao.Status.ATIVA, 'reativado_em'),
    'cancelar': (
        {Inscricao.Status.ATIVA, Inscricao.Status.PAUSADA},
        Inscricao.Status.CANCELADA,
        'cancelado_em',
    ),
    'concluir': ({Inscricao.Status.ATIVA}, Inscricao.Status.CONCLUIDA, 'concluido_em'),
}
ACOES_COM_MOTIVO = ('pausar', 'cancelar')  # tabela de 3.5


def alterar_status(inscricao, usuario, acao, motivo=''):
    """INS-06 (spec 3.5): só a IS muda o status; concluída e cancelada não voltam (A-14, A-15).

    Concluir à mão só vale em trilha personalizada; na de etapa, a conclusão vem do
    avanço (A-13c). Cada inscrição guarda a data mais recente de cada mudança e um único
    motivo (3.5.4).
    """
    if not e_is(usuario):
        raise PermissionDenied
    origens, destino, campo_data = TRANSICOES_INSCRICAO[acao]
    if inscricao.status not in origens:
        raise RegraViolada('Esta ação não é permitida para o status atual.')
    if acao == 'concluir' and inscricao.trilha.e_de_etapa:
        raise RegraViolada(
            'A inscrição numa trilha de etapa só é concluída ao avançar a etapa.'
        )

    inscricao.status = destino
    setattr(inscricao, campo_data, timezone.now())
    campos = ['status', campo_data]
    motivo = motivo.strip()
    if acao in ACOES_COM_MOTIVO and motivo:
        inscricao.motivo = motivo
        campos.append('motivo')
    inscricao.save(update_fields=campos)
