# F1 · Acesso e contas — tasks

**Estado:** aprovado · **Data:** 2026-11-04
**Spec:** [`spec.md`](spec.md) (aprovada) · **Plano:** [`plan.md`](plan.md) (aprovado)

Cada tarefa cabe num PR e vira uma issue no GitHub. O título da issue é o título da tarefa; o corpo é o bloco da tarefa. Toda tarefa termina com `python manage.py test` e `python manage.py makemigrations --check --dry-run` sem erros.

**Tamanho:** P (algumas horas) · M (1 a 2 dias).

---

## Ordem e dependências

```text
F0 ─▶ T1 ─┬─▶ T2
          ├─▶ T3
          └─▶ T4 ─▶ T5 ─▶ T6
```

- **T1** vem primeiro: as outras usam os campos novos e a regra da senha.
- **T2, T3 e T4** podem andar em paralelo. Mexem em `usuarios/views.py` e `sgis/settings.py`, então combinem quem mergeia primeiro.
- **T6** vem por último, porque usa as regras de T4 e T5.

---

## T1 · Model de usuário e senha de 10 caracteres

**Branch:** `feat/f1-t1-usuario` · **Tamanho:** M · **Depende de:** F0

**Objetivo:** preparar a conta para as regras da F1 e fazer o `createsuperuser` funcionar (ACE-01, ACE-12, ACE-13).

**Fazer** ([`plan.md`](plan.md) seções 2, 3 e 5):
- [ ] `normalizar_email` em `usuarios/models.py`; `save()` em minúsculas.
- [ ] `deve_trocar_senha` e `criado_em`.
- [ ] Renomear o parâmetro `senha` do manager para `password`.
- [ ] Migração `0004_troca_de_senha_e_criado_em`.
- [ ] `MinimumLengthValidator` com 10 e texto de ajuda atualizado.
- [ ] Ajustar as senhas curtas de `usuarios/tests.py`.

**Testes novos** (em `usuarios/test_f1.py`):
- [ ] `test_a01_entra_com_email_em_maiusculas`
- [ ] `test_a09_senha_fraca_recusada_na_criacao_redefinicao_e_troca`, nos caminhos que já existem
- [ ] `test_a20_conta_inicial_da_is_em_minusculas_com_troca_obrigatoria`
- [ ] `test_createsuperuser_cria_conta_que_entra`
- [ ] `test_migracao_marca_contas_is_e_normaliza_emails`

**Pronto quando:**
- [ ] A migração foi rodada para frente e para trás numa cópia do `db.sqlite3`. Resultado descrito no PR.

---

## T2 · Login e página inicial por papel

**Branch:** `feat/f1-t2-login` · **Tamanho:** P · **Depende de:** T1

**Objetivo:** mensagem única de erro, orientação de "esqueci a senha", sessão de 2 horas e página inicial de cada papel (ACE-01, ACE-02, ACE-03, ACE-08).

**Fazer** ([`plan.md`](plan.md) seção 5):
- [ ] `LoginForm` com uma só mensagem.
- [ ] Orientação na tela de login.
- [ ] `SESSION_COOKIE_AGE` e `SESSION_SAVE_EVERY_REQUEST`.
- [ ] `home_view` redireciona por papel.
- [ ] Ajustar `test_menu_do_empreendedor_aponta_para_trilhas_inscritas`.

**Testes novos:**
- [ ] `test_a02_mensagem_unica_para_toda_falha_de_login`
- [ ] `test_a03_cada_papel_vai_para_sua_pagina_inicial`
- [ ] `test_a04_sessao_expira_por_inatividade`
- [ ] `test_a12_login_mostra_orientacao_de_esqueci_a_senha`

**Pronto quando:**
- [ ] Cada papel cai na sua página depois de entrar.

---

## T3 · Troca de senha obrigatória

**Branch:** `feat/f1-t3-troca-obrigatoria` · **Tamanho:** P · **Depende de:** T1

**Objetivo:** conta marcada só usa a troca de senha e o "Sair" (ACE-06).

**Fazer** ([`plan.md`](plan.md) seção 5):
- [ ] `usuarios/middleware.py` e entrada em `MIDDLEWARE`.
- [ ] `trocar_senha_view` limpa a marcação.

**Testes novos:**
- [ ] `test_a10_troca_de_senha_mantem_a_sessao`, `test_a10_senha_atual_errada_nao_muda_nada`
- [ ] `test_a11_troca_obrigatoria_bloqueia_tudo_menos_sair`

**Pronto quando:**
- [ ] Depois da troca, a conta usa o sistema normalmente.

---

## T4 · Criar empreendedor com empreendimento

**Branch:** `feat/f1-t4-criar-conta` · **Tamanho:** M · **Depende de:** T1

**Objetivo:** a IS cria o empreendedor e o empreendimento juntos, e toda conta nasce com troca obrigatória (ACE-04, ACE-05, RN-01).

**Fazer** ([`plan.md`](plan.md) seções 4 e 6):
- [ ] `sgis/excecoes.py` com `RegraViolada`; `trilhas/regras.py` importa de lá.
- [ ] `usuarios/regras.py` com `criar_conta`, `criar_empreendedor` e `vincular_empreendimento`.
- [ ] `empreendimentos/forms.py` com `EmpreendimentoCadastroForm`.
- [ ] `criar_usuario_view` valida os dois formulários.
- [ ] Campos do empreendimento em `criar_usuario.html`, com o script de mostrar e esconder.

**Testes novos:**
- [ ] `test_a05_is_cria_professor_com_troca_obrigatoria`, `test_a05_is_nao_cria_is_nem_admin`
- [ ] `test_a07_email_repetido_com_maiusculas_e_recusado`
- [ ] `test_a08_empreendedor_e_empreendimento_criados_juntos`, `test_a08_empreendimento_invalido_nao_cria_nada`
- [ ] `test_j1_contas_de_ponta_a_ponta`

**Pronto quando:**
- [ ] Um erro no empreendimento não deixa conta criada.

---

## T5 · Gestão de contas pela IS

**Branch:** `feat/f1-t5-gestao` · **Tamanho:** M · **Depende de:** T4

**Objetivo:** a IS lista, edita, redefine a senha, desativa e reativa contas (ACE-08, ACE-09, ACE-10, ACE-11).

**Fazer** ([`plan.md`](plan.md) seções 4, 6 e 7):
- [ ] `contas_geridas`, `exigir_gestao`, `redefinir_senha`, `desativar`, `reativar`.
- [ ] `UsuarioEdicaoForm` e `RedefinirSenhaForm`.
- [ ] Rotas `contas`, `editar_conta`, `redefinir_senha`, `alterar_conta` e templates.
- [ ] Link "Usuários" do cabeçalho aponta para `contas`.

**Testes novos:**
- [ ] `test_a13_redefinicao_encerra_sessoes_e_exige_troca`, `test_a13_is_nao_redefine_is_nem_admin`
- [ ] `test_a14_lista_de_contas_da_is_com_filtros`
- [ ] `test_a15_edita_nome_e_email_e_papel_forjado_e_ignorado`
- [ ] `test_a16_desativar_encerra_sessao_e_reativar_devolve_acesso`
- [ ] `test_a17_ninguem_desativa_a_si_mesmo`
- [ ] `test_a19_professor_e_empreendedor_nao_abrem_gestao_de_contas`

**Pronto quando:**
- [ ] A IS gerencia professores e empreendedores sem usar o `/admin/`.

---

## T6 · Contas pelo `/admin/`

**Branch:** `feat/f1-t6-admin` · **Tamanho:** P · **Depende de:** T5 e F0

**Objetivo:** o admin gerencia todas as contas com as mesmas regras (ACE-04, ACE-09, ACE-11).

**Fazer** ([`plan.md`](plan.md) seção 8):
- [ ] `papel` e `is_active` somente leitura depois de criar.
- [ ] Ações Desativar e Reativar pelas regras; sem apagar.
- [ ] Troca obrigatória ao criar e ao redefinir.
- [ ] Campos do empreendimento no formulário de criação; `regras.vincular_empreendimento` em `save_model`.
- [ ] `is_staff` e `is_superuser` definidos pelo papel.

**Testes novos:**
- [ ] `test_a06_admin_cria_conta_com_troca_obrigatoria`, `test_a06_admin_cria_empreendedor_com_empreendimento`, `test_a06_admin_sem_dados_do_empreendimento_nao_cria_nada`
- [ ] `test_a17_ultimo_admin_nao_e_desativado`
- [ ] `test_a18_nenhuma_tela_apaga_conta`
- [ ] `test_j8_gestao_de_contas_de_ponta_a_ponta`

**Pronto quando:**
- [ ] Nenhum caminho do `/admin/` contorna as regras da seção 4 do plano, e o empreendimento criado não aparece ali.
