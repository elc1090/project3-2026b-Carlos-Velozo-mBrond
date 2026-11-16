# F1 · Acesso e contas — plan

**Estado:** aprovado · **Data:** 2026-11-04
**Spec:** [`spec.md`](spec.md) (aprovada) · **Constituição:** [`../00-constituicao.md`](../00-constituicao.md) · **Situação atual:** [`../levantamento-codigo-v0.4.md`](../levantamento-codigo-v0.4.md) · **Depende de:** [`F0-fundacao/plan.md`](../F0-fundacao/plan.md)

Como implementar a F1 no código atual. Nenhuma regra nova: onde este plano precisa de uma decisão técnica, ela está marcada como **Decisão de plano**.

---

## 1. Visão geral

| Camada | Arquivo | O que muda |
|---|---|---|
| Models | `usuarios/models.py` | `deve_trocar_senha`, `criado_em`, e-mail sempre em minúsculas, correção do `create_user` |
| Migração | `usuarios/migrations/0004` | Campos novos, contas IS marcadas, e-mails em minúsculas |
| Regras | `usuarios/regras.py` (**novo**), `sgis/excecoes.py` (**novo**) | Quem gerencia quem, criar, redefinir, desativar, reativar |
| Middleware | `usuarios/middleware.py` (**novo**) | Troca de senha obrigatória |
| Forms | `usuarios/forms.py`, `empreendimentos/forms.py` (**novo**) | Login genérico, edição, redefinição e dados do empreendimento |
| Views e URLs | `usuarios/views.py`, `sgis/urls.py` | Página por papel, lista, edição, redefinição, desativação |
| Admin | `usuarios/admin.py` | Mesmas regras no `/admin/` |
| Configuração | `sgis/settings.py` | Senha com 10 caracteres, sessão de 2 horas |
| Templates | `usuarios/templates/usuarios/` | Login, criação, lista e formulários novos |
| Testes | `usuarios/test_f1.py` (**novo**) e `usuarios/tests.py` | A-01 a A-20 e jornadas J-1 e J-8 |

Nenhuma dependência nova.

---

## 2. Model `Usuario`

```python
def normalizar_email(email):            # movida de usuarios/forms.py
    return (email or '').strip().lower()


class UsuarioManager(BaseUserManager):
    def create_user(self, email, nome, password=None, **extra_fields): ...
    def create_superuser(self, email, nome, password=None, **extra_fields): ...


class Usuario(AbstractBaseUser, PermissionsMixin):
    # Campos existentes sem mudança.
    deve_trocar_senha = models.BooleanField('deve trocar a senha', default=False)
    criado_em = models.DateTimeField('criado em', auto_now_add=True)

    def save(self, *args, **kwargs):
        self.email = normalizar_email(self.email)     # 3.1.1: venha de onde vier
        super().save(*args, **kwargs)
```

**Correção necessária · `createsuperuser` não funciona hoje.** O parâmetro do manager se chama `senha`, mas o comando do Django envia `password`. Testado em 2026-11-04: `createsuperuser` conclui sem erro, mas a conta fica sem senha utilizável e com o domínio como único trecho em minúsculas. Nenhum admin criado assim consegue entrar, o que quebra 3.7.1. Renomear o parâmetro para `password` resolve, e as chamadas atuais são posicionais.

**Decisão de plano · minúsculas no `save()`.** É o único ponto por onde passam a tela da IS, o `/admin/` e os comandos. `update()` em queryset não passa por ali, mas nenhum código altera e-mail assim.

`último acesso` (seção 8 da spec mãe) já existe como `last_login`.

---

## 3. Migração

`0004_troca_de_senha_e_criado_em`:

| Passo | Conteúdo | Reversa |
|---|---|---|
| 1 | `AddField` de `deve_trocar_senha` | Automática |
| 2 | `AddField` de `criado_em`, com a data da migração nas contas existentes | Automática |
| 3 | `RunPython`: marca as contas IS para trocar a senha (decisão 7.7, A-20) | Sem efeito; o campo sai no passo 1 |
| 4 | `RunPython`: converte os e-mails existentes para minúsculas | Sem efeito; a grafia original não é guardada |

Se dois e-mails ficarem iguais ao converter, a migração para com uma mensagem clara, sem alterar nada. Nesse caso, a IS decide qual conta fica.

**Decisão de plano · `criado_em` das contas antigas.** A data original não existe, então essas contas recebem a data da migração.

---

## 4. Regras (`usuarios/regras.py`)

`RegraViolada` sai de `trilhas/regras.py` e vai para `sgis/excecoes.py`, para os dois apps usarem a mesma exceção. `trilhas/regras.py` passa a importá-la de lá, sem mudar quem a usa.

```python
PAPEIS_DA_IS = (Usuario.Papel.PROFESSOR, Usuario.Papel.EMPREENDEDOR)

def contas_geridas(usuario): ...                # 3.6.1, 3.6.3; IS: professores e empreendedores; admin: todas
def exigir_gestao(usuario, conta): ...          # A-13, A-19: fora do escopo → PermissionDenied

def criar_conta(dados_conta, senha): ...                                  # 3.3; troca obrigatória
def criar_empreendedor(dados_conta, senha, dados_empreendimento): ...     # 3.3.4; atômico
def vincular_empreendimento(conta, dados_empreendimento): ...             # 3.3.4; usado também pelo /admin/

def redefinir_senha(conta, usuario, nova_senha): ...    # 3.5.4
def desativar(conta, usuario): ...                      # 3.6.5, 3.6.6
def reativar(conta, usuario): ...
```

- **`criar_empreendedor`:** roda em `transaction.atomic`. Cria a conta e o empreendimento; o signal da F4 faz a inscrição na Pré-incubação (A-08).
- **`redefinir_senha`:** chama `set_password` e marca `deve_trocar_senha`. Mudar a senha muda o hash da sessão, então as sessões abertas caem sozinhas (A-13).
- **`desativar`:** recusa a própria conta e a última conta ativa de admin (A-17). Com `is_active=False`, o Django já invalida a sessão na próxima página (A-16).

Nada apaga conta (3.6.4).

---

## 5. Login, sessão e troca obrigatória

- **`LoginForm`:** remove o ramo "Esta conta está desativada", que nunca é alcançado. Fica só uma mensagem para todas as falhas (A-02), no texto de 3.1.2.
- **Tela de login:** acrescenta "Esqueceu a senha? Entre em contato com a Incubadora Social." (A-12).
- **Sessão:** `SESSION_COOKIE_AGE = 7200` e `SESSION_SAVE_EVERY_REQUEST = True`, para contar por inatividade (decisão 7.3).
- **Senha:** `MinimumLengthValidator` com `min_length=10`. O texto de ajuda do `TrocarSenhaForm` passa a dizer 10.
- **Página por papel (3.2):** `home_view` redireciona o professor para `trilhas:minhas`, o empreendedor para `trilhas:inscritas` e o admin para `admin:usuarios_usuario_changelist`. A IS continua na página atual.

```python
class TrocaSenhaObrigatoriaMiddleware:
    """ACE-06: enquanto a conta estiver marcada, só a troca de senha e o Sair funcionam."""
    # Em process_view: usuário logado, deve_trocar_senha e rota fora de ('trocar_senha', 'logout')
    # → redirect('trocar_senha').
```

Entra em `MIDDLEWARE` depois do `ProtecaoLoginMiddleware`. `trocar_senha_view` limpa a marcação e salva com `update_fields=['password', 'deve_trocar_senha']`.

---

## 6. Forms

| Form | Campos | Usado em |
|---|---|---|
| `UsuarioCadastroForm` (existente) | `nome`, `email`, `papel`, `senha` | Criar conta |
| `EmpreendimentoCadastroForm` (**novo**, em `empreendimentos/forms.py`) | `nome`, `tipo`, `descricao` (decisão 7.1), com `prefix='empreendimento'` | Criar empreendedor |
| `UsuarioEdicaoForm` (**novo**) | `nome`, `email` | Editar conta. `papel` fica fora, então um valor forjado é ignorado (A-15) |
| `RedefinirSenhaForm` (**novo**) | `nova_senha` | Redefinir pela IS. Valida com `validate_password(user=conta)` |

**Criar empreendedor:** a view valida os dois formulários e só chama `regras.criar_empreendedor` se ambos passarem (A-08). Para outros papéis, o segundo formulário é ignorado. Um script pequeno mostra os campos do empreendimento quando o papel é empreendedor; o servidor valida de qualquer forma (Art. 7.2).

---

## 7. Rotas e views

| Rota | Nome | Método | Quem | O que faz | Critérios |
|---|---|---|---|---|---|
| `usuarios/` | `contas` | GET | IS | Lista com filtros por papel e status | A-14, A-19 |
| `usuarios/novo/` | `criar_usuario` | GET/POST | IS | Passa a usar `regras`; cria empreendimento junto | A-05, A-07, A-08 |
| `usuarios/<pk>/editar/` | `editar_conta` | GET/POST | IS | Nome e e-mail | A-15 |
| `usuarios/<pk>/senha/` | `redefinir_senha` | GET/POST | IS | `regras.redefinir_senha` | A-09, A-13 |
| `usuarios/<pk>/<desativar\|reativar>/` | `alterar_conta` | POST | IS | `regras.desativar` ou `regras.reativar` | A-16, A-17 |
| `conta/senha/` | `trocar_senha` | GET/POST | Todos | Limpa a marcação | A-10, A-11 |

- Todas as rotas de `usuarios/` usam `@papel_requerido(Usuario.Papel.IS)` e `regras.exigir_gestao` quando recebem uma conta.
- O link "Usuários" do cabeçalho aponta para `contas`.
- Filtros inválidos são ignorados, como em `todas_trilhas_view`.

---

## 8. Admin (`usuarios/admin.py`)

O admin gerencia todas as contas pelo `/admin/` (3.6.3), com as mesmas regras:

- `papel` e `is_active` ficam somente leitura depois de criar a conta (A-15, A-17).
- Ações **Desativar** e **Reativar** chamam `regras.desativar` e `regras.reativar`, e mostram a recusa como mensagem.
- `has_delete_permission` devolve `False`, e a ação de apagar sai da lista (A-18).
- Em `save_model`, conta nova nasce com `deve_trocar_senha=True` (A-06).
- **Empreendedor pelo `/admin/` (decisão 7.8):** o `add_form` ganha os campos do empreendimento, obrigatórios quando o papel é empreendedor. `save_model` chama `regras.vincular_empreendimento`, dentro da transação que o admin já abre ao salvar. Conta e empreendimento são criados juntos, e o model continua fora do admin (F0, 3.3.2).
- `change_password_form` usa uma subclasse de `AdminPasswordChangeForm` que marca a troca obrigatória (3.5.4).

**Decisão de plano · acesso do papel admin ao `/admin/`.** `is_staff` e `is_superuser` deixam de aparecer no formulário. Ao criar uma conta com papel admin, `save_model` liga os dois; nos outros papéis, ficam desligados. Assim, papel e acesso não divergem. Depois da F0, o `/admin/` só tem contas, então `is_superuser` não dá acesso a mais nada.

---

## 9. Testes

Arquivo novo `usuarios/test_f1.py`, com o ID no nome (Art. 6.2). Todo controle de acesso testa o caso negado (Art. 6.3).

| Critério | Teste |
|---|---|
| A-01 | `test_a01_entra_com_email_em_maiusculas` |
| A-02 | `test_a02_mensagem_unica_para_toda_falha_de_login` |
| A-03 | `test_a03_cada_papel_vai_para_sua_pagina_inicial` |
| A-04 | `test_a04_sessao_expira_por_inatividade` |
| A-05 | `test_a05_is_cria_professor_com_troca_obrigatoria`, `test_a05_is_nao_cria_is_nem_admin` |
| A-06 | `test_a06_admin_cria_conta_com_troca_obrigatoria`, `test_a06_admin_cria_empreendedor_com_empreendimento`, `test_a06_admin_sem_dados_do_empreendimento_nao_cria_nada` |
| A-07 | `test_a07_email_repetido_com_maiusculas_e_recusado` |
| A-08 | `test_a08_empreendedor_e_empreendimento_criados_juntos`, `test_a08_empreendimento_invalido_nao_cria_nada` |
| A-09 | `test_a09_senha_fraca_recusada_na_criacao_redefinicao_e_troca` |
| A-10 | `test_a10_troca_de_senha_mantem_a_sessao`, `test_a10_senha_atual_errada_nao_muda_nada` |
| A-11 | `test_a11_troca_obrigatoria_bloqueia_tudo_menos_sair` |
| A-12 | `test_a12_login_mostra_orientacao_de_esqueci_a_senha` |
| A-13 | `test_a13_redefinicao_encerra_sessoes_e_exige_troca`, `test_a13_is_nao_redefine_is_nem_admin` |
| A-14 | `test_a14_lista_de_contas_da_is_com_filtros` |
| A-15 | `test_a15_edita_nome_e_email_e_papel_forjado_e_ignorado` |
| A-16 | `test_a16_desativar_encerra_sessao_e_reativar_devolve_acesso` |
| A-17 | `test_a17_ninguem_desativa_a_si_mesmo`, `test_a17_ultimo_admin_nao_e_desativado` |
| A-18 | `test_a18_nenhuma_tela_apaga_conta` |
| A-19 | `test_a19_professor_e_empreendedor_nao_abrem_gestao_de_contas` |
| A-20 | `test_a20_conta_inicial_da_is_em_minusculas_com_troca_obrigatoria` |
| ACE-13 | `test_createsuperuser_cria_conta_que_entra` |
| Migração | `test_migracao_marca_contas_is_e_normaliza_emails` |
| J-1 | `test_j1_contas_de_ponta_a_ponta` |
| J-8 | `test_j8_gestao_de_contas_de_ponta_a_ponta` |

**Testes existentes:**

- Senhas de 8 ou 9 caracteres em `usuarios/tests.py` passam a ter pelo menos 10.
- `test_menu_do_empreendedor_aponta_para_trilhas_inscritas`, em `trilhas/tests.py`, abre a `home`, que passa a redirecionar o empreendedor. O teste precisa seguir o redirecionamento.

**Verificação final:** `python manage.py test` e `python manage.py makemigrations --check --dry-run` sem erros.

---

## 10. Riscos

| Risco | Mitigação |
|---|---|
| Contas IS de produção cairem na troca obrigatória sem aviso | Combinar com a IS o momento do deploy (decisão 7.7) |
| Empreendedores já criados sem empreendimento | Tratado na F2 (seção 10 daquele plano) |
| Conflito em `criar_usuario_view` com a F4, que mostra o aviso da Pré-incubação | A tarefa que vier depois atualiza a branch |
| Admin perder o acesso por um erro na migração ou no `save_model` | Testar `createsuperuser` e o `/admin/` numa cópia do banco antes do deploy |
