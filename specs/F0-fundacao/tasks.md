# F0 · Fundação — tasks

**Estado:** aprovado · **Data:** 2026-11-04
**Spec:** [`spec.md`](spec.md) (aprovada) · **Plano:** [`plan.md`](plan.md) (aprovado)

Cada tarefa cabe num PR e vira uma issue no GitHub. O título da issue é o título da tarefa; o corpo é o bloco da tarefa. Toda tarefa termina com `python manage.py test` e `python manage.py makemigrations --check --dry-run` sem erros.

**Tamanho:** P (algumas horas) · M (1 a 2 dias).

---

## Ordem e dependências

```text
T1 (CI) ─▶ T2 ─┬─▶ T3
               ├─▶ T4
               └─▶ T5
```

- **T1** vem primeiro: a partir dela, os PRs seguintes já mostram o resultado da CI.
- **T3, T4 e T5** podem andar em paralelo depois de T2. T3 e T4 mexem em `usuarios/views.py` e `sgis/urls.py`, então combinem quem mergeia primeiro.

---

## T1 · Testes automáticos a cada mudança

**Branch:** `feat/f0-t1-ci` · **Tamanho:** P · **Depende de:** —

**Objetivo:** a suíte e a checagem de migrações rodam sozinhas a cada envio (RNF-03).

**Fazer** ([`plan.md`](plan.md) seção 6):
- [ ] `.github/workflows/testes.yml`.
- [ ] Depois do merge, o responsável liga a proteção da `main` no GitHub.

**Pronto quando:**
- [ ] O resultado aparece no GitHub, junto do PR (A-13).

---

## T2 · Toda rota protegida por padrão

**Branch:** `feat/f0-t2-protecao` · **Tamanho:** M · **Depende de:** T1

**Objetivo:** uma rota nova nasce protegida, e anônimo vai ao login até em endereço inexistente (ACE-00, ACE-00a, ACE-00b, RN-14).

**Fazer** ([`plan.md`](plan.md) seção 2):
- [ ] `sgis/middleware.py` com `ProtecaoLoginMiddleware`, e entrada em `MIDDLEWARE`.
- [ ] `sgis/views.py` com `saude_view` e `robots_view`; rotas em `sgis/urls.py`.
- [ ] `@login_not_required` em `login_view`.
- [ ] `SECURE_REDIRECT_EXEMPT` e `healthCheckPath` no `render.yaml`.

**Testes novos** (em `sgis/tests.py`):
- [ ] `test_a01_anonimo_vai_ao_login_e_volta_para_a_pagina`
- [ ] `test_a02_anonimo_em_endereco_inexistente_vai_ao_login`
- [ ] `test_a04_excecoes_respondem_sem_login`, `test_a04_estaticos_vem_antes_da_protecao`
- [ ] `test_a05_saude_responde_so_ok`
- [ ] `test_a06_robots_pede_para_nao_indexar`
- [ ] `test_a07_toda_rota_exige_login_salvo_a_lista_de_excecoes`, `test_a07_rota_nova_sem_marcacao_e_protegida`

**Pronto quando:**
- [ ] Depois do deploy, o *health check* do Render responde `ok`.

---

## T3 · Admin só com contas

**Branch:** `feat/f0-t3-admin` · **Tamanho:** P · **Depende de:** T2

**Objetivo:** o `/admin/` não mostra dados de negócio, e sua entrada é o login do sistema (RN-16).

**Fazer** ([`plan.md`](plan.md) seção 3):
- [ ] Tirar `Empreendimento`, `Trilha`, `Inscricao` e `Group` do admin.
- [ ] `admin_login_view` e a rota que sobrepõe `/admin/login/`.

**Testes novos:**
- [ ] `test_a08_admin_so_gerencia_contas`
- [ ] `test_a09_admin_anonimo_vai_ao_login_do_sistema`, `test_a09_login_do_admin_nao_e_publico`

**Pronto quando:**
- [ ] O admin não encontra dados de negócio, nem pelo endereço direto.

---

## T4 · Login sem redirecionamento para fora

**Branch:** `fix/f0-t4-next` · **Tamanho:** P · **Depende de:** T2

**Objetivo:** fechar o *open redirect* do login (RNF-01).

**Fazer** ([`plan.md`](plan.md) seção 4):
- [ ] Validar `next` em `login_view` com `url_has_allowed_host_and_scheme`.

**Testes novos:**
- [ ] `test_a10_next_externo_vai_para_a_pagina_inicial`
- [ ] `test_a11_next_interno_e_respeitado`

**Pronto quando:**
- [ ] Um `next` para outro site leva à página inicial.

---

## T5 · Páginas de erro

**Branch:** `feat/f0-t5-erros` · **Tamanho:** P · **Depende de:** T2

**Objetivo:** 403 e 404 com o visual do SGIS, sem detalhes técnicos.

**Fazer** ([`plan.md`](plan.md) seção 5):
- [ ] `sgis/templates/403.html` e `404.html`.

**Testes novos:**
- [ ] `test_a03_logado_em_endereco_inexistente_ve_404_do_sgis`
- [ ] `test_a12_403_do_sgis_sem_detalhes_tecnicos`

**Pronto quando:**
- [ ] As duas páginas aparecem com o cabeçalho e o link para o início.
