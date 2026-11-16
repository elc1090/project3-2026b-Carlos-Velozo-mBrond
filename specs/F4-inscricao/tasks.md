# F4 · Inscrição e etapas — tasks

**Estado:** aprovado · **Data:** 2026-11-04
**Spec:** [`spec.md`](spec.md) (aprovada) · **Plano:** [`plan.md`](plan.md) (aprovado)

Cada tarefa cabe num PR e vira uma issue no GitHub. O título da issue é o título da tarefa; o corpo é o bloco da tarefa. Toda tarefa termina com `python manage.py test` e `python manage.py makemigrations --check --dry-run` sem erros.

**Tamanho:** P (algumas horas) · M (1 a 2 dias).

| Tarefa | Issue | Entrada na `main` |
|---|---|---|
| T1 · Restringir a inscrição | #22 | PR #23 (em revisão) |

---

## Ordem e dependências

```text
T1 ─▶ T2 ─▶ T3 ─┬─▶ T4
                ├─▶ T5
                └─▶ T6 ─▶ T7 (S)
```

- **T1 → T2 → T3** é sequencial: T3 usa o status e os campos de T2.
- **T4, T5 e T6** podem andar em paralelo depois de T3. Mexem em `trilhas/regras.py`, `trilhas/views.py` e `trilhas/urls.py`, então combinem quem mergeia primeiro.
- **T7** é prioridade S e fica por último (decisão 7.5 da spec).
- **T4** toca `criar_usuario_view`, que a F1 também altera. Quem vier depois atualiza a branch.

---

## T1 · Permitir inscrição somente em trilhas personalizadas publicadas

**Branch:** `fix/f4-inscricao-trilhas-publicadas` · **Tamanho:** P · **Depende de:** F3 (concluída)

**Objetivo:** a IS só escolhe trilhas personalizadas publicadas (INS-01). Está na issue #22 e no PR #23.

**Fazer:**
- [ ] `InscricaoForm` lista só trilhas personalizadas publicadas e recusa as outras no servidor.
- [ ] Manter a seleção só de empreendimentos ativos e o acesso só da IS.

**Testes novos:**
- [ ] `test_a02_formulario_exibe_somente_trilhas_personalizadas_publicadas`
- [ ] `test_a02_inscricao_forjada_em_trilha_invalida_e_recusada`, com a trilha de etapa publicada no teste (`plan.md` seção 9)
- [ ] `test_a04_so_is_pode_inscrever`

**Pronto quando:**
- [ ] O PR #23 estiver mergeado, com os ajustes da revisão.

---

## T2 · Status Concluída e nova restrição de inscrição

**Branch:** `feat/f4-t2-concluida` · **Tamanho:** M · **Depende de:** T1

**Objetivo:** a inscrição passa a ter o status Concluída, e um empreendimento pode ser inscrito de novo depois de concluir (INS-06, INS-07).

**Fazer** ([`plan.md`](plan.md) seções 2 e 3):
- [ ] `Inscricao`: status `CONCLUIDA`, campos `reativado_em` e `concluido_em`.
- [ ] Restrição `inscricao_unica_em_andamento` no lugar de `inscricao_unica_nao_cancelada`.
- [ ] Migração `0009_inscricao_concluida`, com a reversa da seção 3.

**Testes novos:**
- [ ] `test_a03_aceita_nova_apos_concluida_ou_cancelada`, no nível do banco
- [ ] `test_migracao_reversa_converte_concluidas_em_canceladas`

**Pronto quando:**
- [ ] A migração foi rodada para frente e para trás numa cópia do `db.sqlite3`, com duas inscrições concluídas no mesmo par. Resultado descrito no PR.

---

## T3 · Regras de inscrição e status

**Branch:** `feat/f4-t3-regras` · **Tamanho:** M · **Depende de:** T2

**Objetivo:** concentrar a inscrição e as transições em `trilhas/regras.py` (Art. 7.5) e acrescentar a conclusão à mão (INS-05, INS-06).

**Fazer** ([`plan.md`](plan.md) seções 4 a 6):
- [ ] `trilhas_inscriviveis`, `inscricao_de_etapa`, `etapa_atual`, `incubacao_concluida`, `proxima_etapa`.
- [ ] `inscrever` e o auxiliar privado único de criação de inscrição.
- [ ] Mover `TRANSICOES_INSCRICAO` para `regras.py`, com `concluir`, e criar `alterar_status`.
- [ ] `InscricaoForm` usa `trilhas_inscriviveis` e recusa duplicidade só contra `STATUS_EM_ANDAMENTO`. Sem `clean_trilha`.
- [ ] `inscricoes_view` usa `regras.inscrever`; `alterar_inscricao_view` usa `regras.alterar_status`; a rota ganha `concluir`.
- [ ] `inscricoes.html`: selo de Concluída, ações só em ativa e pausada, botão Concluir só em ativa de trilha personalizada.
- [ ] `AGENTS.md`: atualizar a referência a `TRANSICOES_INSCRICAO`.

**Testes novos:**
- [ ] `test_a01_inscrito_ve_a_trilha_e_outro_nao`
- [ ] `test_a03_recusa_duplicada_ativa_ou_pausada`
- [ ] `test_a13_formulario_nao_aceita_trilha_de_etapa_publicada`
- [ ] `test_a13c_is_conclui_personalizada_e_pode_reinscrever`, `test_a13c_concluir_trilha_de_etapa_e_recusado`
- [ ] `test_a14_pausar_reativar_cancelar_gravam_status_data_e_motivo`
- [ ] `test_a15_concluida_ou_cancelada_nao_volta`
- [ ] `test_a16_sem_inscricao_de_etapa_e_sem_etapa`

**Pronto quando:**
- [ ] `trilhas/views.py` não tem mais regra de transição.

---

## T4 · Entrada automática na Pré-incubação

**Branch:** `feat/f4-t4-pre-incubacao` · **Tamanho:** P · **Depende de:** T3

**Objetivo:** só inscrever com a Pré-incubação publicada e alcançar os pendentes quando ela for publicada (INS-02).

**Fazer** ([`plan.md`](plan.md) seções 4, 6 e 8):
- [ ] `inscrever_na_pre_incubacao`, `inscrever_pendentes_na_pre_incubacao`, `aviso_pre_incubacao`.
- [ ] `trilhas/signals.py` chama a regra.
- [ ] `publicar` fica atômico e inscreve os pendentes ao publicar a Pré-incubação.
- [ ] `criar_usuario_view` mostra o aviso ao criar um empreendedor.

**Testes novos:**
- [ ] `test_a05_empreendimento_novo_entra_na_pre_incubacao_sem_autor`
- [ ] `test_a06_pre_em_rascunho_fica_sem_etapa_e_avisa_is`, `test_a06_publicar_pre_inscreve_pendentes`
- [ ] `test_a07_quem_concluiu_nao_e_reinscrito`

**Pronto quando:**
- [ ] Um empreendimento criado com a Pré-incubação em rascunho fica sem etapa e entra nela quando ela é publicada.

---

## T5 · Tela de etapa: avançar e definir

**Branch:** `feat/f4-t5-etapas` · **Tamanho:** M · **Depende de:** T3

**Objetivo:** a IS conduz o empreendimento pelas etapas (INS-03, INS-04, INS-11, RN-09).

**Fazer** ([`plan.md`](plan.md) seções 4 a 7):
- [ ] `avancar_etapa` e `definir_etapa`, com trava e `etapa_esperada`, recusando empreendimento desativado.
- [ ] `DefinirEtapaForm`.
- [ ] Rotas `etapa`, `etapa_avancar` e `etapa_definir`, só da IS.
- [ ] `trilhas/etapa.html` e link em cada cartão de `inscricoes.html`.

**Testes novos:**
- [ ] `test_a08_avancar_conclui_e_inscreve_na_proxima`
- [ ] `test_a09_sequencia_de_acoes_nunca_gera_duas_etapas`
- [ ] `test_a10_proxima_etapa_em_rascunho_recusa_e_nada_muda`
- [ ] `test_a11_inscricao_pausada_nao_avanca`
- [ ] `test_a12_avancar_da_desincubacao_encerra_a_incubacao`
- [ ] `test_a12b_empreendimento_desativado_nao_avanca_nem_define_etapa`
- [ ] `test_a13b_define_etapa_sem_etapa_ativa`, `test_a13b_definir_forjado_com_etapa_ativa_e_recusado`
- [ ] `test_avancar_com_etapa_esperada_antiga_e_recusado`
- [ ] `test_rotas_de_etapa_e_lote_negam_outros_papeis`, para as rotas de etapa
- [ ] `test_j3_etapas_de_ponta_a_ponta`

**Pronto quando:**
- [ ] Antes do deploy, a produção foi consultada por empreendimentos com mais de uma inscrição de etapa ativa ou pausada, e o resultado foi levado à IS (`plan.md` seção 10).

---

## T6 · O que o empreendedor vê

**Branch:** `feat/f4-t6-empreendedor` · **Tamanho:** P · **Depende de:** T3

**Objetivo:** "Minhas trilhas" mostra o histórico de concluídas, e a inscrição pausada tem aviso (INS-08, INS-09).

**Fazer** ([`plan.md`](plan.md) seções 6 e 7):
- [ ] `inscricao_pausada_do_empreendedor`.
- [ ] `trilhas_inscritas.html`: selo de Concluída e seção de histórico.
- [ ] `detalhe.html`: aviso de inscrição pausada.

**Testes novos:**
- [ ] `test_a17_empreendedor_ve_as_proprias_e_nao_as_de_outro`
- [ ] `test_a18_inscricao_pausada_mostra_aviso`
- [ ] `test_j4_inscricao_em_trilha_personalizada`

**Pronto quando:**
- [ ] Canceladas não aparecem na lista, e a trilha continua acessível pelo detalhe.

---

## T7 · Inscrição em lote (S)

**Branch:** `feat/f4-t7-lote` · **Tamanho:** P · **Depende de:** T3

**Objetivo:** a IS inscreve vários empreendimentos de uma vez (INS-10).

**Fazer** ([`plan.md`](plan.md) seções 4 a 7):
- [ ] `inscrever_em_lote` e `InscricaoLoteForm`.
- [ ] Rota `inscricoes_lote` e `trilhas/inscricoes_lote.html`.
- [ ] Link na tela de inscrições.

**Testes novos:**
- [ ] `test_a19_lote_inscreve_um_e_ignora_dois`
- [ ] `test_rotas_de_etapa_e_lote_negam_outros_papeis`, para a rota de lote

**Pronto quando:**
- [ ] A IS vê quantos foram inscritos e quantos foram ignorados.
