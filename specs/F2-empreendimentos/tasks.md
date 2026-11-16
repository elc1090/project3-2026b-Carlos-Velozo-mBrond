# F2 · Empreendimentos — tasks

**Estado:** aprovado · **Data:** 2026-11-04
**Spec:** [`spec.md`](spec.md) (aprovada) · **Plano:** [`plan.md`](plan.md) (aprovado)

Cada tarefa cabe num PR e vira uma issue no GitHub. O título da issue é o título da tarefa; o corpo é o bloco da tarefa. Toda tarefa termina com `python manage.py test` e `python manage.py makemigrations --check --dry-run` sem erros.

**Tamanho:** P (algumas horas) · M (1 a 2 dias).

---

## Ordem e dependências

```text
F1 e F4 ─▶ T1 ─┬─▶ T2 ─▶ T3 ─▶ T4
               └─▶ T5
                          T3 ─▶ T6 (S)
```

- **T1** vem primeiro: as outras usam o model novo.
- **T2 → T3 → T4** é sequencial: a lista leva ao perfil, e o perfil leva à edição.
- **T5** pode andar em paralelo depois de T1.
- **T6** é prioridade S e fica por último.

---

## T1 · Model e migrações do empreendimento

**Branch:** `feat/f2-t1-models` · **Tamanho:** M · **Depende de:** F1, F4

**Objetivo:** lista de tipos, contatos, representante único e fim do supervisor (EMP-01, EMP-02, RN-01, RN-02, RN-03).

**Fazer** ([`plan.md`](plan.md) seções 2, 3 e 8):
- [ ] `Empreendimento.Tipo`, `email_contato`, `telefone_contato`.
- [ ] `representante` como `OneToOneField`; `clean` valida o papel.
- [ ] Remover `usuario_professor_supervisor`.
- [ ] Migrações `0004_contatos`, `0005_converter_tipo` (com função reversa) e `0006_tipo_representante_unico`.
- [ ] `popular_banco`: sem supervisor, com tipos da lista e contatos.

**Testes novos** (em `empreendimentos/tests.py`):
- [ ] `test_a04_empreendedor_nao_representa_dois`, `test_a04_so_empreendedor_e_representante`
- [ ] `test_migracao_converte_tipo_e_reversa_restaura`

**Pronto quando:**
- [ ] A produção foi consultada, e os casos da seção 10 do plano foram corrigidos.
- [ ] As três migrações foram rodadas para frente e para trás numa cópia do `db.sqlite3`. Resultado descrito no PR.
- [ ] `popular_banco` roda sem erro num banco novo.

---

## T2 · Lista de empreendimentos

**Branch:** `feat/f2-t2-lista` · **Tamanho:** M · **Depende de:** T1

**Objetivo:** a IS vê os empreendimentos, com filtros por situação e etapa atual (EMP-03).

**Fazer** ([`plan.md`](plan.md) seções 4, 6 e 8):
- [ ] `trilhas.regras.anotar_etapa_atual`.
- [ ] `empreendimentos/urls.py`, rota `lista` e `lista.html`.
- [ ] Link "Empreendimentos" no cabeçalho e link para a tela de etapa em cada linha.

**Testes novos:**
- [ ] `test_a06_filtros_se_combinam`
- [ ] `test_a07_lista_mostra_etapa_calculada`

**Pronto quando:**
- [ ] A lista não faz uma consulta por linha para calcular a etapa.

---

## T3 · Perfil do empreendimento

**Branch:** `feat/f2-t3-perfil` · **Tamanho:** M · **Depende de:** T2

**Objetivo:** cada pessoa envolvida vê o perfil do empreendimento (EMP-04, EMP-05).

**Fazer** ([`plan.md`](plan.md) seções 4, 6 e 8):
- [ ] `empreendimentos_visiveis` e `pode_ver`.
- [ ] Rota `perfil` e `perfil.html`.
- [ ] Link "Meu empreendimento" no cabeçalho.

**Testes novos:**
- [ ] `test_a08_perfil_mostra_dados_etapa_e_inscricoes`
- [ ] `test_a09_professor_ve_quem_atendeu_e_outro_recebe_403`
- [ ] `test_a10_representante_ve_o_proprio_e_admin_recebe_403`

**Pronto quando:**
- [ ] Quem não pode ver recebe 403, inclusive pelo endereço direto.

---

## T4 · Edição do empreendimento

**Branch:** `feat/f2-t4-editar` · **Tamanho:** P · **Depende de:** T3

**Objetivo:** a IS edita os dados, sem trocar o representante (EMP-01, 3.2.4).

**Fazer** ([`plan.md`](plan.md) seções 4 a 6):
- [ ] `EmpreendimentoForm`, `exigir_edicao`, rota `editar` e `editar.html`.

**Testes novos:**
- [ ] `test_a03_is_edita`, `test_a03_professor_e_representante_nao_editam`
- [ ] `test_a05_representante_forjado_e_ignorado`

**Pronto quando:**
- [ ] O representante não muda, nem forjando o formulário.

---

## T5 · Campos novos na criação do empreendedor

**Branch:** `feat/f2-t5-criacao` · **Tamanho:** P · **Depende de:** T1

**Objetivo:** o formulário da F1 pede todos os dados do empreendimento (EMP-01).

**Fazer** ([`plan.md`](plan.md) seção 5):
- [ ] `EmpreendimentoCadastroForm`: `tipo` em lista, `email_contato` e `telefone_contato`.
- [ ] Campos novos em `criar_usuario.html` e no formulário de criação do `/admin/`.

**Testes novos:**
- [ ] `test_a01_criar_empreendedor_salva_todos_os_campos`
- [ ] `test_a02_tipo_ou_email_invalido_nao_cria_nada`

**Pronto quando:**
- [ ] Um dado inválido não deixa conta nem empreendimento criados.

---

## T6 · Desativar e reativar empreendimento (S)

**Branch:** `feat/f2-t6-desativar` · **Tamanho:** P · **Depende de:** T3

**Objetivo:** a IS desativa sem apagar, e o representante perde o acesso enquanto isso durar (EMP-06).

**Fazer** ([`plan.md`](plan.md) seções 4, 6 e 7):
- [ ] `desativar`, `reativar` e a rota `situacao`.
- [ ] `usuarios/backends.py` e `AUTHENTICATION_BACKENDS`.
- [ ] Botões no perfil.

**Testes novos:**
- [ ] `test_a11_desativado_fica_no_filtro_e_fora_da_inscricao`
- [ ] `test_a12_representante_nao_entra_ate_reativar`

**Pronto quando:**
- [ ] Reativar devolve o acesso sem mexer na conta nem nas inscrições.
