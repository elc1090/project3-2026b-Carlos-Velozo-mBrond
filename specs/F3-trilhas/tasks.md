# F3 · Trilhas — tasks

**Estado:** aprovado · **Data:** 2026-10-23
**Spec:** [`spec.md`](spec.md) (aprovada) · **Plano:** [`plan.md`](plan.md) (aprovado)

**Situação: concluída em 2026-10-28.**

| Tarefa | Issue | Entrada na `main` |
|---|---|---|
| T1 · Models e migrações | #11 | PR #18 (`b9ab46e`) |
| T2 · Módulo de regras | #12 | merge direto (`021478c`) |
| T3 · Criar, editar, publicar e arquivar | #13 | commit direto (`0804cb6`) |
| T4 · Atividades | (fechada manualmente) | merge direto (`a1f1a78`) |
| T5 · Listas por papel | — | PR #19 (`b56b708`) |
| T6 · Confirmação da IS | — | PR #20 (`6edb7d6`) |
| T7 · Reordenar | — | PR #21 (`1dea3a8`) |

Cada tarefa cabe num PR e vira uma issue no GitHub. O título da issue é o título da tarefa; o corpo é o bloco da tarefa. Toda tarefa termina com `python manage.py test` e `python manage.py makemigrations --check --dry-run` sem erros.

**Tamanho:** P (algumas horas) · M (1 a 2 dias).

---

## Ordem e dependências

```text
T1 ─▶ T2 ─▶ T3 ─▶ T4 ─▶ T6
              │      └──▶ T7 (S)
              └──▶ T5
```

- **T1 → T2 → T3** é sequencial: cada uma usa o que a anterior criou.
- **T5** pode andar em paralelo com **T3/T4** depois da T2, mas as três mexem em `trilhas/views.py` e `trilhas/urls.py`. Se forem pessoas diferentes, combinem quem mergeia primeiro e quem atualiza a branch.
- **T6** vem por último entre as obrigatórias, porque aplica a confirmação em todas as views de alteração criadas em T3 e T4.

---

## T1 · Models e migrações de trilhas e atividades

**Branch:** `feat/f3-t1-models` · **Tamanho:** M · **Depende de:** —

**Objetivo:** trocar `tipo`/`pre_incubacao` por `etapa`/`status`, criar a `AtividadeTrilha` e converter os dados sem perder inscrições, mantendo o sistema funcionando como hoje.

**Fazer** ([`plan.md`](plan.md) seções 2, 3 e 8):
- [ ] `Trilha`: `Etapa`, `Status`, `etapa`, `status`, `publicada_em`, `arquivada_em`; `usuario_criador` aceitando vazio, com `verbose_name='dono'`; restrições `trilha_etapa_unica` e `trilha_dono_conforme_tipo`; propriedade `e_de_etapa`.
- [ ] Model `AtividadeTrilha` com as três `CheckConstraint`. Não registrar no admin.
- [ ] Migrações `0006_etapa_status_atividades`, `0007_converter_trilhas` (com função reversa) e `0008_remover_tipo_pre_incubacao`.
- [ ] `trilhas/signals.py`: procurar a pré-incubação por `etapa`.
- [ ] `trilhas/admin.py`: colunas e filtros com `etapa` e `status`.
- [ ] Trocar `Trilha.Tipo` e `pre_incubacao` por `etapa` em `trilhas/views.py` (criar trilha e filtro de "todas"), nos templates (`todas_trilhas.html`) e no `InscricaoForm`.
- [ ] `popular_banco`: sem `tipo`; atividades nas trilhas de etapa e na do professor; publicar essas trilhas.
- [ ] Ajustar os testes de `trilhas/tests.py` que usam `Trilha.Tipo` ou `pre_incubacao`.

**Testes novos** (em `trilhas/test_f3.py`):
- [ ] `test_a02_existem_tres_trilhas_de_etapa`
- [ ] `test_migracao_pre_incubacao_vira_etapa_publicada_sem_perder_inscricoes`

**Pronto quando:**
- [ ] Os 41 testes atuais (ajustados) e os novos passam.
- [ ] As três migrações foram rodadas para frente e para trás numa cópia do `db.sqlite3` local, e as inscrições na pré-incubação continuam ligadas à mesma trilha. Resultado descrito no PR.
- [ ] `popular_banco` roda sem erro num banco novo.

---

## T2 · Módulo de regras das trilhas

**Branch:** `feat/f3-t2-regras` · **Tamanho:** M · **Depende de:** T1

**Objetivo:** concentrar em `trilhas/regras.py` todas as decisões de "quem pode" e "quando pode" da F3, testadas sem passar por views.

**Fazer** ([`plan.md`](plan.md) seção 4):
- [ ] `RegraViolada`.
- [ ] Quem é quem: `e_is`, `e_dono`, `empreendimentos_atendidos`.
- [ ] Ver: `trilhas_visiveis`, `pode_ver`.
- [ ] Editar: `pode_editar`, `exige_confirmacao`.
- [ ] Estados: `publicar`, `arquivar`.
- [ ] Atividades: `acrescentar_atividade`, `campos_editaveis`, `apagar_atividade`, `arquivar_atividade`, `mover_atividade`.
- [ ] Cada função com docstring citando o ID que implementa.

**Testes novos** (nível de regra, em `trilhas/test_f3.py`):
- [ ] `test_a03_trilha_de_etapa_nao_pode_ser_arquivada`
- [ ] `test_a08_atividade_nova_entra_no_fim`
- [ ] `test_a09_publicar_exige_atividade_ativa`
- [ ] `test_a10_publicada_nao_volta_a_rascunho`
- [ ] `test_a13_atividade_de_publicada_nao_e_apagada_so_arquivada`
- [ ] `test_a14_trilha_arquivada_nao_e_editavel`
- [ ] `test_a15_nao_arquiva_trilha_com_inscricao_ativa_ou_pausada`
- [ ] Regras de `pode_editar` para A-16, A-17 e A-19, e de `trilhas_visiveis` para A-20 a A-22 (os testes completos, pela tela, ficam em T3 e T5).

**Pronto quando:**
- [ ] Nenhuma view usa ainda o módulo (isso é T3 a T7), mas todas as regras da seção 4 do plano existem e têm teste.

---

## T3 · Criar, editar, publicar e arquivar trilha

**Branch:** `feat/f3-t3-trilha` · **Tamanho:** M · **Depende de:** T2

**Objetivo:** telas e ações da trilha, para o dono e para a IS.

**Fazer** ([`plan.md`](plan.md) seções 5, 6 e 7):
- [ ] `trilhas/nova/` para professor **e** IS, criando trilha personalizada em rascunho e indo para o detalhe.
- [ ] `trilhas/<pk>/` (detalhe): dados, tipo, etapa, estado, dono, atividades em ordem, arquivadas separadas, botões conforme `regras`.
- [ ] `trilhas/<pk>/editar/`, `publicar/` (POST) e `arquivar/` (POST).
- [ ] Templates `detalhe.html` e reaproveitamento de `criar_trilha.html` para editar.
- [ ] Link "Nova trilha" para a IS no cabeçalho e na `home`.
- [ ] `RegraViolada` vira mensagem de erro na tela; `PermissionDenied` vira 403.

**Testes novos:**
- [ ] `test_a01_trilha_criada_e_personalizada_do_criador_em_rascunho` (professor e IS)
- [ ] `test_a03_is_cria_trilha_personalizada_nao_de_etapa`
- [ ] `test_a04_etapa_dono_e_status_forjados_sao_ignorados`
- [ ] `test_a16_professor_nao_altera_trilha_de_outro` (editar, publicar, arquivar)
- [ ] `test_a17_professor_nao_edita_trilha_de_etapa_nem_da_is`
- [ ] `test_a19_empreendedor_e_admin_nao_abrem_edicao`
- [ ] Os testes de A-09, A-10, A-14 e A-15 da T2 também pela tela (POST nas rotas).

**Pronto quando:**
- [ ] Um professor cria, edita e publica uma trilha pela interface; a IS faz o mesmo com uma trilha de etapa.

---

## T4 · Atividades da trilha

**Branch:** `feat/f3-t4-atividades` · **Tamanho:** M · **Depende de:** T3

**Objetivo:** criar, editar, apagar e arquivar atividades, respeitando o que pode mudar depois da publicação.

**Fazer** ([`plan.md`](plan.md) seções 5, 6 e 7):
- [ ] `AtividadeForm` e `AtividadeTextoForm`, com as validações de endereço, prazos e dias.
- [ ] Rotas `atividade_criar`, `atividade_editar`, `atividade_apagar` (POST) e `atividade_arquivar` (POST).
- [ ] Template `atividade_form.html`; mostrar o campo de endereço só para Link é opcional (o servidor valida de qualquer jeito).
- [ ] Botões de atividade no `detalhe.html`.

**Testes novos:**
- [ ] `test_a05_link_sem_endereco_ou_invalido_e_recusado`
- [ ] `test_a06_dois_prazos_sao_recusados`
- [ ] `test_a07_padrao_obrigatoria_e_exige_validacao`
- [ ] `test_a11_publicada_aceita_texto_e_ignora_tipo_prazo_e_validacao`
- [ ] `test_a12_atividade_acrescentada_em_publicada_entra_no_fim`
- [ ] A-13 pela tela: em publicada, apagar é recusado e arquivar funciona.

**Pronto quando:**
- [ ] Uma trilha pode ser montada do zero pela interface, com atividades dos três tipos, e publicada.

---

## T5 · Listas de trilhas por papel

**Branch:** `feat/f3-t5-listas` · **Tamanho:** P · **Depende de:** T2 *(pode andar junto com T3/T4; ver "Ordem e dependências")*

**Objetivo:** cada papel vê exatamente as trilhas da spec 3.6.

**Fazer** ([`plan.md`](plan.md) seções 4, 6 e 7):
- [ ] `trilhas/` (professor): três seções (minhas, de etapa, de outros professores nos empreendimentos que atende), usando `regras.trilhas_visiveis`.
- [ ] `trilhas/todas/` (IS): filtros por tipo (etapa / personalizada) e por estado.
- [ ] Estado de cada trilha com texto, não só cor.
- [ ] Cada trilha das listas leva ao detalhe (se a T3 já estiver mergeada; senão, o link entra na T3).

**Testes novos:**
- [ ] `test_a20_rascunho_visivel_so_para_dono_e_is`
- [ ] `test_a21_professor_ve_trilha_de_outro_so_se_atende_o_empreendimento`
- [ ] `test_a22_empreendedor_nao_ve_trilha_sem_inscricao`

**Pronto quando:**
- [ ] Nenhuma lista mostra trilha que o papel não deveria ver, e o acesso direto pelo endereço também é negado.

---

## T6 · Confirmação da IS ao alterar trilha de professor

**Branch:** `feat/f3-t6-confirmacao-is` · **Tamanho:** P · **Depende de:** T3, T4

**Objetivo:** a IS altera trilhas de professores com plenos poderes, mas só depois de confirmar (spec 3.3.5 e 7.7).

**Fazer** ([`plan.md`](plan.md) seções 5 e 7):
- [ ] Campo `confirmar` nos forms quando `regras.exige_confirmacao(usuario, trilha)`.
- [ ] `confirmar=1` exigido no servidor em **todas** as alterações de trilha de professor feitas pela IS: editar trilha, publicar, arquivar, criar/editar/apagar/arquivar atividade (e mover, se a T7 já existir).
- [ ] Template `partials/confirmacao_is.html` com o nome do professor dono.

**Testes novos:**
- [ ] `test_a18_is_altera_trilha_de_professor_so_com_confirmacao` (sem `confirmar` nada muda; com, muda; para cada ação)
- [ ] `test_a18b_edicao_pela_is_mantem_o_professor_como_dono`
- [ ] A IS alterando trilha de etapa ou a própria trilha personalizada **não** pede confirmação.

**Pronto quando:**
- [ ] Nenhuma rota de alteração aceita a ação da IS numa trilha de professor sem a confirmação.

---

## T7 · Reordenar atividades *(prioridade S)*

**Branch:** `feat/f3-t7-reordenar` · **Tamanho:** P · **Depende de:** T4

**Objetivo:** mudar a ordem das atividades enquanto a trilha está em rascunho (TRL-08).

**Fazer:**
- [ ] Rota `atividade_mover` (POST, `cima` ou `baixo`) usando `regras.mover_atividade`.
- [ ] Botões ↑ ↓ no `detalhe.html`, só em rascunho.
- [ ] Se a T6 já estiver mergeada, incluir a confirmação da IS nesta rota.

**Testes novos:**
- [ ] `test_a23_reordenar_so_em_rascunho`

**Pronto quando:**
- [ ] A ordem mudada é a ordem exibida no detalhe.

---

## Cobertura dos critérios

| Critério | Tarefa |
|---|---|
| A-01 | T3 |
| A-02 | T1 |
| A-03 | T2 (arquivar etapa), T3 (IS cria personalizada) |
| A-04 | T3 |
| A-05, A-06, A-07 | T4 |
| A-08 | T2 |
| A-09, A-10 | T2 (regra), T3 (tela) |
| A-11, A-12 | T4 |
| A-13 | T2 (regra), T4 (tela) |
| A-14, A-15 | T2 (regra), T3 (tela) |
| A-16, A-17, A-19 | T2 (regra), T3 (tela) |
| A-18, A-18b | T6 |
| A-20, A-21, A-22 | T2 (regra), T5 (tela) |
| A-23 | T7 |

**F3 concluída quando:** T1 a T6 mergeadas (T7 é desejável), todos os critérios acima com teste passando, e a seção 6 da spec ("Situação atual") e o [`levantamento-codigo-v0.4.md`](../levantamento-codigo-v0.4.md) atualizados para refletir o código novo.
