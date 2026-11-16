# F4 · Inscrição e etapas — plan

**Estado:** aprovado · **Data:** 2026-11-04
**Spec:** [`spec.md`](spec.md) (aprovada) · **Constituição:** [`../00-constituicao.md`](../00-constituicao.md) · **Situação atual:** [`../levantamento-codigo-v0.4.md`](../levantamento-codigo-v0.4.md)

Como implementar a F4 no código atual. Nenhuma regra nova: onde este plano precisa de uma decisão técnica, ela está marcada como **Decisão de plano**.

---

## 1. Visão geral

| Camada | Arquivo | O que muda |
|---|---|---|
| Models | `trilhas/models.py` | `Inscricao` ganha o status Concluída e os campos `concluido_em` e `reativado_em`; a restrição de unicidade passa a valer só para ativas e pausadas |
| Migração | `trilhas/migrations/0009` | Esquema novo, com reversa |
| Regras | `trilhas/regras.py` | Regras da F4, inclusive as transições que hoje estão em `trilhas/views.py` (Constituição, Art. 7.5) |
| Forms | `trilhas/forms.py` | `InscricaoForm` usa a regra de `regras.py`; novos `DefinirEtapaForm` e `InscricaoLoteForm` |
| Views e URLs | `trilhas/views.py`, `trilhas/urls.py` | Tela de etapa do empreendimento, avançar, definir etapa, concluir e lote |
| Signal | `trilhas/signals.py` | Inscreve só se a Pré-incubação estiver publicada |
| Conta | `usuarios/views.py` | Aviso à IS quando a Pré-incubação não está publicada (A-06) |
| Templates | `trilhas/templates/trilhas/` | Tela nova de etapa, tela de lote, ajustes em inscrições, detalhe e "Minhas trilhas" |
| Documentação | `AGENTS.md` | `TRANSICOES_INSCRICAO` deixa de estar em `trilhas/views.py` |
| Testes | `trilhas/test_f4.py` (**novo**) e `trilhas/tests.py` | Critérios A-01 a A-19, com A-12b, A-13b e A-13c, e jornadas J-3 e J-4 |

Nenhuma dependência nova.

**O que já está feito:** o PR #23 restringe o `InscricaoForm` a trilhas personalizadas publicadas (INS-01, A-02). Este plano parte dele. A regra muda de lugar na seção 5, sem mudar de comportamento.

---

## 2. Model `Inscricao`

```python
class Inscricao(models.Model):
    class Status(models.TextChoices):
        ATIVA = 'ativa', 'Ativa'
        PAUSADA = 'pausada', 'Pausada'
        CONCLUIDA = 'concluida', 'Concluída'
        CANCELADA = 'cancelada', 'Cancelada'

    # Campos existentes sem mudança.
    reativado_em = models.DateTimeField('reativado em', null=True, blank=True)
    concluido_em = models.DateTimeField('concluído em', null=True, blank=True)

    class Meta:
        constraints = [
            # INS-07: só uma inscrição ativa ou pausada por empreendimento e trilha.
            models.UniqueConstraint(
                fields=['empreendimento', 'trilha'],
                condition=models.Q(status__in=['ativa', 'pausada']),
                name='inscricao_unica_em_andamento',
            ),
        ]
```

**Decisão de plano · etapa única garantida por regra, não pelo banco.** O banco não consegue exigir INS-04 com uma restrição simples, porque a etapa está na trilha, e a condição de uma `UniqueConstraint` não atravessa `ForeignKey`. Guardar a etapa na inscrição para contornar isso contraria o Art. 4.3. A garantia fica nas funções de `regras.py`, que travam a linha do empreendimento (seção 4). A-09 cobre a regra com teste.

---

## 3. Migração

`0009_inscricao_concluida`, nesta ordem:

1. `AddField` de `reativado_em` e `concluido_em`.
2. `AlterField` de `status`, com a nova opção.
3. `RemoveConstraint` de `inscricao_unica_nao_cancelada`.
4. `RunPython(noop, concluidas_viram_canceladas)`.
5. `AddConstraint` de `inscricao_unica_em_andamento`.

**Para frente**, nenhum dado muda: a restrição nova é mais permissiva que a antiga.

**Reversa:** o esquema antigo não conhece Concluída, e duas inscrições concluídas no mesmo par quebrariam a restrição antiga. A função reversa transforma as concluídas em canceladas, com `cancelado_em = concluido_em`. Assim, as inscrições continuam no banco, mas a reversa perde a diferença entre os dois status e as datas de reativação. A posição no passo 4 faz a função rodar, na volta, depois de a restrição nova sair, antes de a antiga voltar e com `concluido_em` ainda existente.

**A testar à mão antes do PR** (Art. 7.4): rodar a migração para frente e para trás numa cópia do `db.sqlite3` local, com pelo menos duas inscrições concluídas no mesmo par.

---

## 4. Regras (`trilhas/regras.py`)

As views só chamam estas funções. Cada função cita o ID que implementa. Vale o padrão da F3: falta de permissão levanta `PermissionDenied`, e condição de estado não atendida levanta `RegraViolada`, sem mudar nada.

```python
ETAPAS_EM_ORDEM = (Trilha.Etapa.PRE_INCUBACAO, Trilha.Etapa.INCUBACAO, Trilha.Etapa.DESINCUBACAO)
STATUS_EM_ANDAMENTO = (Inscricao.Status.ATIVA, Inscricao.Status.PAUSADA)

# Consultas (nada é gravado: INS-05, Art. 4.3)
def trilhas_inscriviveis(): ...                 # personalizadas publicadas (3.1.2)
def inscricao_de_etapa(empreendimento): ...     # a ativa ou pausada em trilha de etapa, ou None
def etapa_atual(empreendimento): ...            # etapa dessa inscrição, ou None = "sem etapa" (A-16)
def incubacao_concluida(empreendimento): ...    # sem etapa, e a inscrição de etapa mais recente é a da Desincubação, concluída (3.4.6)
def proxima_etapa(etapa): ...                   # a seguinte em ETAPAS_EM_ORDEM, ou None na Desincubação

# Inscrever
def inscrever(empreendimento, trilha, usuario): ...                # 3.1
def inscrever_em_lote(trilha, empreendimentos, usuario): ...       # 3.8; devolve (inscritos, ignorados)
def inscrever_na_pre_incubacao(empreendimento): ...                # 3.3.1; sem autor; só se publicada
def inscrever_pendentes_na_pre_incubacao(): ...                    # 3.3.2
def aviso_pre_incubacao(): ...                                     # 3.3.2; texto do aviso, ou None

# Etapas
def avancar_etapa(empreendimento, usuario, etapa_esperada): ...    # 3.4; atômico
def definir_etapa(empreendimento, etapa, usuario): ...             # 3.5a; atômico

# Status
TRANSICOES_INSCRICAO = {...}                                       # 3.5; movido de views.py
def alterar_status(inscricao, usuario, acao, motivo=''): ...       # 3.5
def inscricao_pausada_do_empreendedor(usuario, trilha): ...        # 3.6, A-18
```

**`inscrever`:** ponto único de criação das inscrições feitas por uma pessoa. A EXE-01 da F5 vai criar as execuções ao criar uma inscrição. Por isso, `inscrever_na_pre_incubacao`, `avancar_etapa`, `definir_etapa` e o lote usam um mesmo auxiliar privado de criação.

**`avancar_etapa`** (dentro de `transaction.atomic`):

1. Exige papel IS e trava o empreendimento com `select_for_update`.
2. Recusa se o empreendimento estiver desativado (3.4.7). Depois, busca `inscricao_de_etapa`. Sem ela, levanta `RegraViolada`.
3. Recusa se a etapa atual for diferente de `etapa_esperada`.
4. Recusa se a inscrição estiver pausada (3.4.5).
5. Se houver próxima etapa, recusa quando a trilha dela não está publicada, com o nome da trilha na mensagem (3.4.4). Essa checagem vem antes de qualquer escrita.
6. Marca a inscrição como Concluída, com `concluido_em`.
7. Se houver próxima etapa, cria a inscrição Ativa com `inscrito_por=usuario`. Na Desincubação, não cria nada (3.4.6).

**Decisão de plano · `etapa_esperada`.** A tela envia a etapa que estava mostrando. Sem isso, um clique duplo avançaria duas etapas, e os dois envios seriam válidos, um depois do outro. É uma proteção técnica de 3.4.2, sem regra nova.

**Decisão de plano · trava no empreendimento.** A trava impede que dois envios simultâneos criem duas inscrições de etapa (INS-04). Vale no PostgreSQL; no SQLite o Django ignora o `select_for_update`, o que não importa em desenvolvimento.

**`definir_etapa`:** com a mesma trava, recusa se o empreendimento estiver desativado (3.5a.3), se `inscricao_de_etapa` existir (A-13b) ou se a trilha da etapa escolhida não estiver publicada (3.5a.1). Cria a inscrição Ativa com `inscrito_por=usuario`. Inscrição pausada conta como etapa, conforme 3.2.3 e A-16.

**`inscrever_pendentes_na_pre_incubacao`:** chamada por `publicar`, dentro da mesma transação, quando a trilha publicada é a Pré-incubação. Alcança os empreendimentos ativos sem nenhuma inscrição em trilha de etapa, em qualquer status:

```python
Empreendimento.objects.filter(desativado_em__isnull=True).exclude(
    pk__in=Inscricao.objects.exclude(trilha__etapa='').values('empreendimento'),
)
```

Assim, quem já concluiu a incubação não é reinscrito (A-07). `publicar` passa a usar `@transaction.atomic`.

**`TRANSICOES_INSCRICAO`:** acrescenta `'concluir': ({ATIVA}, CONCLUIDA)`. A função `alterar_status` preenche `pausado_em`, `reativado_em`, `cancelado_em` ou `concluido_em`, substituindo a data anterior do mesmo tipo (3.5.4), e recusa `concluir` em trilha de etapa, em que a conclusão vem só do avanço (3.5). `motivo` continua aceito em pausar e cancelar, e um motivo novo substitui o anterior (3.5.4); concluir não recebe motivo (tabela de 3.5).

Mover as transições cumpre a seção 6 da spec. O `AGENTS.md` precisa acompanhar, porque cita `TRANSICOES_INSCRICAO` em `trilhas/views.py`.

O docstring de `regras.py` passa a citar a F4.

---

## 5. Forms (`trilhas/forms.py`)

| Form | Campos | Usado em |
|---|---|---|
| `InscricaoForm` (existente) | `empreendimento`, `trilha` | Inscrição individual |
| `DefinirEtapaForm` (novo) | `etapa` (opções de `Trilha.Etapa`) | Definir etapa |
| `InscricaoLoteForm` (novo) | `trilha`, `empreendimentos` (`ModelMultipleChoiceField`) | Lote |

- **`InscricaoForm`:** o queryset de `trilha` vem de `regras.trilhas_inscriviveis()`, e `clean()` passa a recusar duplicidade só contra `STATUS_EM_ANDAMENTO` (A-03).
- **Trilha forjada:** quem recusa é o próprio `ModelChoiceField`, porque o queryset já está filtrado. Não é preciso um `clean_trilha`. Se o texto próprio da recusa for mantido, ele fica em `error_messages['invalid_choice']`.
- **`InscricaoLoteForm.trilha`:** usa o mesmo queryset.

**Decisão de plano · desativado no lote.** A tela lista só empreendimentos ativos, como pede a F2 (A-11 da F2). O campo `empreendimentos`, porém, aceita todos, para que um desativado enviado pelo POST, ou desativado depois de a tela abrir, seja ignorado e contado (3.8.2, A-19), em vez de invalidar o lote inteiro.

---

## 6. Rotas e views

| Rota | Nome | Método | Quem | O que faz | Critérios |
|---|---|---|---|---|---|
| `trilhas/inscricoes/` | `inscricoes` | GET/POST | IS | Passa a salvar por `regras.inscrever` | A-01 a A-04, A-13 |
| `trilhas/inscricoes/<pk>/<pausar\|reativar\|cancelar\|concluir>/` | `alterar_inscricao` | POST | IS | `regras.alterar_status` | A-13c, A-14, A-15 |
| `trilhas/inscricoes/lote/` | `inscricoes_lote` | GET/POST | IS | `regras.inscrever_em_lote`; mostra quantos entraram e quantos foram ignorados | A-19 |
| `trilhas/empreendimentos/<pk>/etapa/` | `etapa` | GET | IS | Etapa atual, inscrição, próxima etapa e as ações disponíveis | A-08, A-13b |
| `trilhas/empreendimentos/<pk>/etapa/avancar/` | `etapa_avancar` | POST | IS | `regras.avancar_etapa` | A-08 a A-12, A-12b |
| `trilhas/empreendimentos/<pk>/etapa/definir/` | `etapa_definir` | POST | IS | `regras.definir_etapa` | A-12b, A-13b |
| `trilhas/inscritas/` | `inscritas` | GET | Empreendedor | Sem mudança na consulta | A-17 |
| `trilhas/<pk>/` | `detalhe` | GET | `pode_ver` | Recebe `inscricao_pausada` para o aviso | A-18 |

- Todas as rotas novas usam `@papel_requerido(Usuario.Papel.IS)`. As de ação usam também `@require_POST`.
- `RegraViolada` vira mensagem de erro e redireciona, como na F3.
- `alterar_inscricao_view` fica só com o tratamento do pedido. A rota `re_path` ganha a ação `concluir`.
- Em `inscricoes_lote`, o caminho fixo `inscricoes/lote/` não conflita com a rota de ações, que começa por número.

**Entrada para a tela de etapa (3.4.1, decisão 7.9 da spec).** Perfil e lista de empreendimentos são telas da F2 e ainda não existem. Enquanto isso, cada cartão de `inscricoes.html` terá um link para a tela de etapa do empreendimento. A F2 acrescenta os dois links quando as telas existirem.

**Aviso de A-06.** Em `criar_usuario_view`, depois de criar um empreendedor, a view mostra `messages.warning` com `regras.aviso_pre_incubacao()`, quando houver aviso. O texto diz que o empreendimento ficará sem etapa até a trilha ser publicada. A criação do empreendimento junto com o representante é da F1 (ACE-05).

---

## 7. Templates

| Template | Situação |
|---|---|
| `trilhas/etapa.html` | **Novo.** Etapa atual, ou "sem etapa", ou "incubação concluída"; botão de avançar com `etapa_esperada` oculto; `DefinirEtapaForm` só quando não há etapa ativa ou pausada |
| `trilhas/inscricoes_lote.html` | **Novo.** Trilha e caixas de seleção dos empreendimentos ativos |
| `trilhas/inscricoes.html` | Selo próprio para Concluída; ações só em ativa e pausada (hoje aparecem para tudo que não é cancelada); botão Concluir só em ativa de trilha personalizada; link para a tela de etapa e para o lote; texto "Inscrito automaticamente" mantido (3.3.3) |
| `trilhas/trilhas_inscritas.html` | Selo próprio para Concluída, com as concluídas numa seção de histórico (3.7.2) |
| `trilhas/detalhe.html` | Aviso de inscrição pausada para o empreendedor (A-18) |

Status aparecem com texto, não só com cor (RNF-05).

---

## 8. Outros ajustes

- **`trilhas/signals.py`:** chama `regras.inscrever_na_pre_incubacao`. Mantém o log de quando a trilha não existe. Se ela estiver em rascunho, não inscreve (3.3.2).
- **`/admin/`:** nada muda aqui. `InscricaoAdmin` ainda permite criar inscrição sem passar por estas regras, o que a RN-16 proíbe. A retirada dos models de negócio do admin é da F0 (spec, 3.3).
- **`popular_banco`:** sem mudança. As trilhas de etapa e a do professor já ficam publicadas.

---

## 9. Testes

Arquivo novo `trilhas/test_f4.py`, com o ID no nome (Art. 6.2). Todo controle de acesso testa o caso negado (Art. 6.3).

As migrações deixam Incubação e Desincubação em **rascunho**. Os testes que dependem delas precisam publicá-las com `Trilha.objects.filter(...).update(status=Trilha.Status.PUBLICADA)`. Sem isso, um teste de "trilha de etapa recusada" passa pelo motivo errado, porque a trilha já seria recusada por estar em rascunho.

| Critério | Teste |
|---|---|
| A-01 | `test_a01_inscrito_ve_a_trilha_e_outro_nao` |
| A-02 | `test_a02_formulario_exibe_somente_trilhas_personalizadas_publicadas`, `test_a02_inscricao_forjada_em_trilha_invalida_e_recusada` (PR #23, em `trilhas/tests.py`) |
| A-03 | `test_a03_recusa_duplicada_ativa_ou_pausada`, `test_a03_aceita_nova_apos_concluida_ou_cancelada` |
| A-04 | `test_a04_so_is_pode_inscrever` |
| A-05 | `test_a05_empreendimento_novo_entra_na_pre_incubacao_sem_autor` |
| A-06 | `test_a06_pre_em_rascunho_fica_sem_etapa_e_avisa_is`, `test_a06_publicar_pre_inscreve_pendentes` |
| A-07 | `test_a07_quem_concluiu_nao_e_reinscrito` (inclui atividade nova na trilha) |
| A-08 | `test_a08_avancar_conclui_e_inscreve_na_proxima` |
| A-09 | `test_a09_sequencia_de_acoes_nunca_gera_duas_etapas` |
| A-10 | `test_a10_proxima_etapa_em_rascunho_recusa_e_nada_muda` |
| A-11 | `test_a11_inscricao_pausada_nao_avanca` |
| A-12 | `test_a12_avancar_da_desincubacao_encerra_a_incubacao` |
| A-12b | `test_a12b_empreendimento_desativado_nao_avanca_nem_define_etapa` |
| A-13 | `test_a13_formulario_nao_aceita_trilha_de_etapa_publicada` |
| A-13b | `test_a13b_define_etapa_sem_etapa_ativa`, `test_a13b_definir_forjado_com_etapa_ativa_e_recusado` |
| A-13c | `test_a13c_is_conclui_personalizada_e_pode_reinscrever`, `test_a13c_concluir_trilha_de_etapa_e_recusado` |
| A-14 | `test_a14_pausar_reativar_cancelar_gravam_status_data_e_motivo` (confere `reativado_em`) |
| A-15 | `test_a15_concluida_ou_cancelada_nao_volta` |
| A-16 | `test_a16_sem_inscricao_de_etapa_e_sem_etapa` |
| A-17 | `test_a17_empreendedor_ve_as_proprias_e_nao_as_de_outro` |
| A-18 | `test_a18_inscricao_pausada_mostra_aviso` |
| A-19 | `test_a19_lote_inscreve_um_e_ignora_dois` |
| Permissão | `test_rotas_de_etapa_e_lote_negam_outros_papeis`, para professor, empreendedor e admin |
| Clique duplo | `test_avancar_com_etapa_esperada_antiga_e_recusado` |
| Migração | `test_migracao_reversa_converte_concluidas_em_canceladas` |
| J-3 | `test_j3_etapas_de_ponta_a_ponta` |
| J-4 | `test_j4_inscricao_em_trilha_personalizada` (as atividades pendentes entram na F5) |

**Testes existentes em `trilhas/tests.py`:** continuam valendo, inclusive os de transição e o do signal sem trilha.

**Verificação final:** `python manage.py test` e `python manage.py makemigrations --check --dry-run` sem erros.

---

## 10. Riscos

| Risco | Mitigação |
|---|---|
| Dados antigos com inscrição em trilha de rascunho, arquivada ou de etapa, porque o formulário aceitava qualquer trilha até o PR #23 | Antes do deploy, consultar a produção por empreendimentos com mais de uma inscrição de etapa ativa ou pausada e levar o resultado à IS. A migração não altera esses dados |
| Avançar deixar a inscrição concluída sem criar a próxima | `transaction.atomic`, e todas as recusas antes da primeira escrita; A-10 confere que nada muda |
| A F5 precisar criar execuções em vários lugares | Um único auxiliar de criação de inscrição (seção 4) |
| Reversa da migração perder a diferença entre concluída e cancelada | Registrada na seção 3; aceitável, porque só se usa em caso de rollback |
| Inscrição criada pelo `/admin/` sem as regras | RN-16 e F0 (seção 8) |
