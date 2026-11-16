# F2 · Empreendimentos — plan

**Estado:** aprovado · **Data:** 2026-11-04
**Spec:** [`spec.md`](spec.md) (aprovada) · **Constituição:** [`../00-constituicao.md`](../00-constituicao.md) · **Situação atual:** [`../levantamento-codigo-v0.4.md`](../levantamento-codigo-v0.4.md) · **Depende de:** [`F1-acesso/plan.md`](../F1-acesso/plan.md) e [`F4-inscricao/plan.md`](../F4-inscricao/plan.md)

Como implementar a F2 no código atual. Nenhuma regra nova: onde este plano precisa de uma decisão técnica, ela está marcada como **Decisão de plano**.

**Ordem:** a F2 vem depois da F1, que cria o formulário de empreendedor, e da F4 (decisão 7.9 da F4), que traz a etapa atual.

---

## 1. Visão geral

| Camada | Arquivo | O que muda |
|---|---|---|
| Models | `empreendimentos/models.py` | Tipo em lista, contatos, representante único, sem supervisor |
| Migrações | `empreendimentos/migrations/0004` a `0006` | Esquema novo e conversão do tipo |
| Regras | `empreendimentos/regras.py` (**novo**) | Quem vê, quem edita, desativar e reativar |
| Etapa na lista | `trilhas/regras.py` | `anotar_etapa_atual`, para calcular a etapa numa consulta só |
| Forms | `empreendimentos/forms.py` | Campos novos e `EmpreendimentoForm` para editar |
| Views e URLs | `empreendimentos/views.py`, `empreendimentos/urls.py` (**novo**) | Lista, perfil, edição, desativação |
| Login | `usuarios/backends.py` (**novo**), `sgis/settings.py` | Representante de empreendimento desativado não entra |
| Templates | `empreendimentos/templates/empreendimentos/` (**novo**) | Lista, perfil, edição |
| Outros | `popular_banco`, cabeçalho, `trilhas/etapa.html` | Sem supervisor; links novos |
| Testes | `empreendimentos/tests.py` | A-01 a A-12 |

Nenhuma dependência nova.

---

## 2. Model `Empreendimento`

```python
class Empreendimento(models.Model):
    class Tipo(models.TextChoices):
        MEI = 'mei', 'MEI'
        ASSOCIACAO = 'associacao', 'Associação'
        COLETIVO = 'coletivo', 'Coletivo'
        OUTRO = 'outro', 'Outro'

    nome = models.CharField('nome', max_length=200)
    tipo = models.CharField('tipo', max_length=20, choices=Tipo.choices)
    descricao = models.TextField('descrição', blank=True)
    email_contato = models.EmailField('e-mail de contato', blank=True)
    telefone_contato = models.CharField('telefone de contato', max_length=30, blank=True)
    desativado_em = models.DateTimeField(...)                     # sem mudança
    representante = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        related_name='empreendimento', verbose_name='representante',
    )

    def clean(self):
        # RN-01: só uma conta de empreendedor pode ser representante (A-04).
        ...
```

- `usuario_professor_supervisor` sai (RN-03).
- `OneToOneField` garante no banco que um empreendedor representa só um empreendimento (RN-01, A-04).
- O papel do representante não cabe numa restrição do banco, porque está em outra tabela. Quem garante é `Empreendimento.clean` e `usuarios.regras.vincular_empreendimento`, único caminho de criação, pela tela da IS e pelo `/admin/` (3.2.1).
- Nenhum código usa o `related_name` antigo `empreendimentos`; as consultas filtram por `representante`.

---

## 3. Migrações

| Migração | Tipo | Conteúdo | Reversa |
|---|---|---|---|
| `0004_contatos` | Esquema | `AddField` de `email_contato` e `telefone_contato` | Automática |
| `0005_converter_tipo` | Dados | Todo tipo em texto livre vira `outro`, com o texto antigo no fim da descrição, em uma linha `Tipo anterior: <texto>` (decisão 7.1) | Devolve o texto ao tipo e remove essa linha |
| `0006_tipo_representante_unico` | Esquema | `AlterField` de `tipo` com a lista; `AlterField` de `representante` para `OneToOneField`; `RemoveField` de `usuario_professor_supervisor` | Automática; os supervisores removidos não voltam |

A `0006` falha se um usuário representar dois empreendimentos (seção 10).

**A testar à mão antes do PR** (Art. 7.4): rodar as três migrações para frente e para trás numa cópia do `db.sqlite3` local e conferir o tipo e a descrição dos empreendimentos do `popular_banco`.

---

## 4. Regras (`empreendimentos/regras.py`)

```python
def empreendimentos_visiveis(usuario): ...     # EMP-05: IS, todos; professor, os que atende; representante, o próprio; admin, nenhum
def pode_ver(usuario, empreendimento): ...     # EMP-05
def exigir_edicao(usuario): ...                # 3.3.1: só a IS
def desativar(empreendimento, usuario): ...    # 3.6
def reativar(empreendimento, usuario): ...     # 3.6
```

- O professor usa `trilhas.regras.empreendimentos_atendidos`, já com inscrição em qualquer status (A-09).
- Desativar e reativar só preenchem ou limpam `desativado_em`. Inscrições e conta não mudam (decisão 7.3, 3.6.3).
- Quem não pode ver recebe `PermissionDenied`, o que vira 403 (3.5.4).

**`trilhas.regras.anotar_etapa_atual(queryset)`:** acrescenta a etapa por `Subquery`, sobre as inscrições ativas ou pausadas em trilha de etapa. Calcula a etapa na consulta, sem gravar nada e sem uma consulta por linha (Art. 4.3, A-07). O filtro usa essa anotação; "sem etapa" é `etapa_atual` nula.

---

## 5. Forms

| Form | Campos | Usado em |
|---|---|---|
| `EmpreendimentoCadastroForm` (F1) | Passa a ter `email_contato` e `telefone_contato`; `tipo` vira lista. O formulário de criação do `/admin/` recebe os mesmos campos | Criar empreendedor (A-01, A-02) |
| `EmpreendimentoForm` (**novo**) | `nome`, `tipo`, `descricao`, `email_contato`, `telefone_contato` | Editar. `representante` fica fora, então um valor forjado é ignorado (A-05) |

---

## 6. Rotas e views

Em `sgis/urls.py`, `path('empreendimentos/', include('empreendimentos.urls'))`.

| Rota | Nome | Método | Quem | O que faz | Critérios |
|---|---|---|---|---|---|
| `empreendimentos/` | `lista` | GET | IS | Lista com filtros `situacao` e `etapa`, combináveis | A-06, A-07, A-11 |
| `empreendimentos/<pk>/` | `perfil` | GET | `pode_ver` | Dados, representante, etapa atual e inscrições | A-08 a A-10 |
| `empreendimentos/<pk>/editar/` | `editar` | GET/POST | IS | `EmpreendimentoForm` | A-03, A-05 |
| `empreendimentos/<pk>/<desativar\|reativar>/` | `situacao` | POST | IS | `regras.desativar` ou `regras.reativar` | A-11, A-12 |

Filtros inválidos são ignorados, como em `todas_trilhas_view`. O nome da trilha no perfil só vira link quando `trilhas.regras.pode_ver` permite.

---

## 7. Desativação e login (S)

```python
class SgisBackend(ModelBackend):
    """EMP-06: representante de empreendimento desativado não entra."""

    def user_can_authenticate(self, user):
        if not super().user_can_authenticate(user):
            return False
        return not Empreendimento.objects.filter(
            representante=user, desativado_em__isnull=False,
        ).exists()
```

`AUTHENTICATION_BACKENDS = ['usuarios.backends.SgisBackend']`.

**Decisão de plano · backend em vez de checar no login.** O Django usa esse método ao entrar e ao recuperar a sessão. Assim, uma sessão aberta também cai ao desativar, e a mensagem continua a mesma de login inválido (A-12). A conta segue ativa e volta a entrar quando o empreendimento for reativado.

---

## 8. Templates e outros ajustes

| Template | Situação |
|---|---|
| `empreendimentos/lista.html` | **Novo.** Tabela com nome, tipo, representante, etapa atual e situação; filtros |
| `empreendimentos/perfil.html` | **Novo.** Com espaço para F7 e F8. Link para a tela de etapa, só para a IS |
| `empreendimentos/editar.html` | **Novo.** |
| `partials/header.html` | Link "Empreendimentos" para a IS; "Meu empreendimento" para o empreendedor |
| `trilhas/inscricoes.html` | O link provisório da F4 pode virar link para o perfil |

- A lista também ganha link para a tela de etapa, cumprindo 3.4.1 da F4 (decisão 7.9).
- **`popular_banco`:** sem `usuario_professor_supervisor`; `tipo` com valores da lista e contatos fictícios.
- **`empreendimentos/admin.py`:** nada a fazer; a F0 tirou o model do admin.
- Situação aparece com texto, não só com cor (RNF-05).

---

## 9. Testes

Em `empreendimentos/tests.py`, com o ID no nome (Art. 6.2). Todo controle de acesso testa o caso negado (Art. 6.3).

| Critério | Teste |
|---|---|
| A-01 | `test_a01_criar_empreendedor_salva_todos_os_campos` |
| A-02 | `test_a02_tipo_ou_email_invalido_nao_cria_nada` |
| A-03 | `test_a03_is_edita`, `test_a03_professor_e_representante_nao_editam` |
| A-04 | `test_a04_empreendedor_nao_representa_dois`, `test_a04_so_empreendedor_e_representante` |
| A-05 | `test_a05_representante_forjado_e_ignorado` |
| A-06 | `test_a06_filtros_se_combinam` |
| A-07 | `test_a07_lista_mostra_etapa_calculada` |
| A-08 | `test_a08_perfil_mostra_dados_etapa_e_inscricoes` |
| A-09 | `test_a09_professor_ve_quem_atendeu_e_outro_recebe_403` |
| A-10 | `test_a10_representante_ve_o_proprio_e_admin_recebe_403` |
| A-11 | `test_a11_desativado_fica_no_filtro_e_fora_da_inscricao` |
| A-12 | `test_a12_representante_nao_entra_ate_reativar` |
| Migração | `test_migracao_converte_tipo_e_reversa_restaura` |

**Testes existentes:** os testes de `trilhas` usam `tipo='alimentos'`, o que o banco continua aceitando em `objects.create`. Nenhum cria dois empreendimentos com o mesmo representante.

**Verificação final:** `python manage.py test` e `python manage.py makemigrations --check --dry-run` sem erros.

---

## 10. Dados de produção

Decisão 7.5 da spec. Antes da `0006`, consultar a produção por empreendedores sem empreendimento ou com mais de um. Cada empreendedor deve ficar com **exatamente um**.

Se houver casos, a IS diz qual é o certo, e a correção vira um comando revisado, executado antes do deploy da `0006`.

---

## 11. Riscos

| Risco | Mitigação |
|---|---|
| `0006` falhar no deploy, com o `migrate` rodando no build do Render | Fazer a consulta da seção 10 antes do merge |
| Lista lenta com a etapa calculada | `anotar_etapa_atual` usa uma única consulta |
| Perfil mostrar a um professor dados de trilha que ele não pode ver | Link só com `trilhas.regras.pode_ver`; A-09 e A-10 |
| A linha `Tipo anterior` ser editada e a reversa não encontrá-la | A reversa só age quando encontra a linha; os demais ficam em `outro` |
