# F0 · Fundação — plan

**Estado:** aprovado · **Data:** 2026-11-04
**Spec:** [`spec.md`](spec.md) (aprovada) · **Constituição:** [`../00-constituicao.md`](../00-constituicao.md) · **Situação atual:** [`../levantamento-codigo-v0.4.md`](../levantamento-codigo-v0.4.md)

Como implementar a F0 no código atual. Nenhuma regra nova: onde este plano precisa de uma decisão técnica, ela está marcada como **Decisão de plano**.

---

## 1. Visão geral

| Camada | Arquivo | O que muda |
|---|---|---|
| Middleware | `sgis/middleware.py` (**novo**) | Proteção por padrão, inclusive em endereço inexistente |
| Views | `sgis/views.py` (**novo**) | `/saude/`, `robots.txt` e entrada do `/admin/` |
| URLs | `sgis/urls.py` | Rotas novas; `/admin/login/` sobreposto |
| Login | `usuarios/views.py` | `next` validado; view marcada como pública |
| Admin | `empreendimentos/admin.py`, `trilhas/admin.py`, `usuarios/admin.py` | Só contas |
| Templates | `sgis/templates/403.html`, `404.html` (**novos**) | Páginas de erro do SGIS |
| Configuração | `sgis/settings.py`, `render.yaml` | Middleware, exceção do HTTPS em `/saude/`, *health check* |
| CI | `.github/workflows/testes.yml` (**novo**) | Testes e migrações a cada envio |
| Testes | `sgis/tests.py` (**novo**) | A-01 a A-13 |

Nenhuma dependência nova. Nenhuma migração.

---

## 2. Proteção por padrão

```python
class ProtecaoLoginMiddleware(LoginRequiredMiddleware):
    """ACE-00, ACE-00b: toda rota exige login, e anônimo sempre vai ao login do sistema."""

    def get_login_url(self, view_func):
        return str(settings.LOGIN_URL)      # ignora o login próprio do /admin/ (decisão 7.1)

    def process_response(self, request, response):
        if response.status_code == 404 and not request.user.is_authenticated:
            return redirect_to_login(request.get_full_path())     # 3.1.1
        return response
```

Em `MIDDLEWARE`, entra logo depois de `AuthenticationMiddleware`.

**Decisão de plano · subclasse em vez do middleware pronto.** O `LoginRequiredMiddleware` do Django cobre a proteção por padrão (Art. 7.6), mas sozinho não atende a spec em dois pontos:

- só age em rotas que existem, e 3.1.1 exige que endereço inexistente também vá ao login;
- as rotas do `/admin/` levam ao login próprio do admin, e a decisão 7.1 pede o login do sistema.

**Exceções públicas (3.2).** Só `login_view`, `saude_view` e `robots_view` recebem `@login_not_required`. Os arquivos estáticos são servidos pelo WhiteNoise antes da sessão, então não passam pelo middleware; todos são públicos (decisão 7.6).

| Rota | Nome | Resposta |
|---|---|---|
| `saude/` | `saude` | `ok`, em texto simples (decisão 7.3) |
| `robots.txt` | `robots` | `User-agent: *` e `Disallow: /` |

`SECURE_REDIRECT_EXEMPT = [r'^saude/$']`, e `healthCheckPath: /saude/` no `render.yaml`.

Os decorators `@login_required` e `@papel_requerido` continuam nas views: o primeiro fica redundante, mas não atrapalha, e o segundo segue checando o papel.

---

## 3. Admin

- Remover `admin.site.register` de `Empreendimento`, `Trilha` e `Inscricao`. Sem o registro, os endereços diretos respondem 404 (A-08). `empreendimentos/admin.py` e `trilhas/admin.py` ficam vazios.
- Tirar também `Group` do admin (`admin.site.unregister(Group)`), porque 3.3.1 limita o `/admin/` a contas e papéis.

**Decisão de plano · `/admin/login/`.** A view de login do Django já é pública, o que abriria uma exceção fora da lista fechada. Uma rota em `sgis/urls.py`, antes de `admin.site.urls`, sobrepõe esse endereço com `admin_login_view`:

| Quem | Resposta |
|---|---|
| Anônimo | Vai ao login do sistema, pelo middleware |
| Logado com `is_staff` | Volta ao `next`, se for do próprio SGIS, ou ao `/admin/` |
| Logado sem `is_staff` | 403, como em A-12 |

---

## 4. Login seguro

Em `login_view`, antes de redirecionar:

```python
proximo = request.POST.get('next') or request.GET.get('next')
if proximo and url_has_allowed_host_and_scheme(
    proximo, allowed_hosts={request.get_host()}, require_https=request.is_secure(),
):
    return redirect(proximo)
return redirect('home')
```

A mesma validação é usada em `admin_login_view`, por uma função auxiliar.

---

## 5. Páginas de erro

| Template | Conteúdo |
|---|---|
| `403.html` | Estende `base.html`, inclui o cabeçalho, diz que o usuário não tem permissão, com link para o início |
| `404.html` | Igual, com a mensagem de não encontrado. Anônimos nunca chegam aqui (seção 2) |

Os handlers padrão do Django já renderizam esses templates com o contexto do usuário. `DEBUG` desligado em produção cobre 3.5.3.

---

## 6. CI

`.github/workflows/testes.yml`, disparado em `push` e `pull_request`, com Python 3.12:

1. `pip install -r requirements.txt`
2. `python manage.py test`
3. `python manage.py makemigrations --check --dry-run`

**Fora do repositório:** a proteção da `main` (decisão 7.5) é uma configuração do GitHub, feita pelo responsável. Exige a CI em merges por PR e permite merge direto ao responsável.

---

## 7. Testes

Arquivo novo `sgis/tests.py`, com o ID no nome (Art. 6.2).

| Critério | Teste |
|---|---|
| A-01 | `test_a01_anonimo_vai_ao_login_e_volta_para_a_pagina` |
| A-02 | `test_a02_anonimo_em_endereco_inexistente_vai_ao_login` |
| A-03 | `test_a03_logado_em_endereco_inexistente_ve_404_do_sgis` |
| A-04 | `test_a04_excecoes_respondem_sem_login`, `test_a04_estaticos_vem_antes_da_protecao` |
| A-05 | `test_a05_saude_responde_so_ok` |
| A-06 | `test_a06_robots_pede_para_nao_indexar` |
| A-07 | `test_a07_toda_rota_exige_login_salvo_a_lista_de_excecoes`, `test_a07_rota_nova_sem_marcacao_e_protegida` |
| A-08 | `test_a08_admin_so_gerencia_contas` (lista do admin e endereços diretos) |
| A-09 | `test_a09_admin_anonimo_vai_ao_login_do_sistema`, `test_a09_login_do_admin_nao_e_publico` |
| A-10 | `test_a10_next_externo_vai_para_a_pagina_inicial` |
| A-11 | `test_a11_next_interno_e_respeitado` |
| A-12 | `test_a12_403_do_sgis_sem_detalhes_tecnicos` |
| A-13 | Verificação manual: o resultado da CI aparece no primeiro PR depois da tarefa |

**Teste de rotas (A-07):** percorre `get_resolver().url_patterns` recursivamente, monta cada caminho com valores fictícios e confere que o anônimo vai ao login. As únicas exceções ficam na constante `ROTAS_PUBLICAS`, no próprio teste.

**Testes existentes:** os de `test_exige_login` continuam válidos, porque o redirecionamento mantém `?next=`.

---

## 8. Riscos

| Risco | Mitigação |
|---|---|
| O *health check* do Render não usar um domínio de `ALLOWED_HOSTS` e receber 400 | Depois do deploy, conferir no painel do Render. Se falhar, ajustar `ALLOWED_HOSTS` antes de ligar o *health check* |
| Uma atualização do Django mudar `LoginRequiredMiddleware` | A-07 e A-09 falham na CI |
| A proteção por padrão bloquear uma rota usada por algum serviço | A lista de exceções é fechada; qualquer acréscimo muda a spec |
