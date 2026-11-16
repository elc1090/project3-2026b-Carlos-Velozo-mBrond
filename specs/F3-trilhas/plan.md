# F3 · Trilhas — plan

**Estado:** aprovado · **Data:** 2026-10-23
**Spec:** [`spec.md`](spec.md) (aprovada) · **Constituição:** [`../00-constituicao.md`](../00-constituicao.md) · **Situação atual:** [`../levantamento-codigo-v0.4.md`](../levantamento-codigo-v0.4.md)

Como implementar a F3 no código atual. Nenhuma regra nova: onde este plano precisa de uma decisão técnica, ela está marcada como **Decisão de plano**.

---

## 1. Visão geral

| Camada | Arquivo | O que muda |
|---|---|---|
| Models | `trilhas/models.py` | `Trilha` troca `tipo` e `pre_incubacao` por `etapa` e `status`; novo model `AtividadeTrilha` |
| Migrações | `trilhas/migrations/0006` a `0008` | Esquema novo, conversão dos dados e remoção dos campos antigos |
| Regras | `trilhas/regras.py` (**novo**) | Todas as regras de permissão, estado e edição da F3, num lugar só (Constituição, Art. 7.5) |
| Forms | `trilhas/forms.py` | `TrilhaForm` com confirmação; novos `AtividadeForm` e `AtividadeTextoForm` |
| Views e URLs | `trilhas/views.py`, `trilhas/urls.py` | Detalhe, edição, publicar, arquivar e atividades; listas por papel |
| Templates | `trilhas/templates/trilhas/` | Detalhe da trilha, formulário de atividade, aviso de confirmação |
| Signal | `trilhas/signals.py` | Procura a pré-incubação por `etapa` |
| Admin | `trilhas/admin.py` | Colunas novas |
| Dados de teste | `usuarios/management/commands/popular_banco.py` | Sem `tipo`; preenche as trilhas de etapa com atividades |
| Testes | `trilhas/test_f3.py` (**novo**) e `trilhas/tests.py` | Critérios A-01 a A-23; ajuste dos testes antigos |

Nenhuma dependência nova.

---

## 2. Models

### 2.1 `Trilha`

```python
class Trilha(models.Model):
    class Etapa(models.TextChoices):
        PRE_INCUBACAO = 'pre_incubacao', 'Pré-incubação'
        INCUBACAO = 'incubacao', 'Incubação'
        DESINCUBACAO = 'desincubacao', 'Desincubação'

    class Status(models.TextChoices):
        RASCUNHO = 'rascunho', 'Rascunho'
        PUBLICADA = 'publicada', 'Publicada'
        ARQUIVADA = 'arquivada', 'Arquivada'

    titulo = models.CharField('título', max_length=200)
    descricao = models.TextField('descrição', blank=True)
    etapa = models.CharField('etapa', max_length=20, choices=Etapa.choices, blank=True, default='')
    status = models.CharField('status', max_length=10, choices=Status.choices, default=Status.RASCUNHO)
    usuario_criador = models.ForeignKey(            # dono; vazio nas trilhas de etapa
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        null=True, blank=True,
        related_name='trilhas_criadas', verbose_name='dono',
    )
    publicada_em = models.DateTimeField('publicada em', null=True, blank=True)
    arquivada_em = models.DateTimeField('arquivada em', null=True, blank=True)

    class Meta:
        constraints = [
            # RN-08: no máximo uma trilha por etapa.
            models.UniqueConstraint(fields=['etapa'], condition=~models.Q(etapa=''),
                                    name='trilha_etapa_unica'),
            # Trilha de etapa não tem usuário dono (a dona é "a IS"); personalizada sempre tem.
            models.CheckConstraint(
                condition=(models.Q(etapa='') & models.Q(usuario_criador__isnull=False))
                | (~models.Q(etapa='') & models.Q(usuario_criador__isnull=True)),
                name='trilha_dono_conforme_tipo',
            ),
        ]

    @property
    def e_de_etapa(self):
        return self.etapa != ''
```

**Decisão de plano · dono das trilhas de etapa = vazio.** A spec diz que a dona das trilhas de etapa é "a IS", não um usuário (3.2.3). Deixar `usuario_criador` vazio nelas representa isso diretamente e tira a dependência de existir um usuário IS na hora da migração (no Render, sem `IS_SENHA_INICIAL`, ele não existe). A permissão nas trilhas de etapa é checada pelo papel IS, nunca pelo campo.

**Decisão de plano · manter o nome `usuario_criador`.** O campo representa o "dono" da spec. Renomear mexeria em views, templates e testes sem ganho de comportamento; o `verbose_name` passa a ser "dono". Se quiser o nome `dono` no código, vira uma tarefa de `refactor` separada.

### 2.2 `AtividadeTrilha` (novo)

```python
class AtividadeTrilha(models.Model):
    class Tipo(models.TextChoices):
        LEITURA = 'leitura', 'Leitura'
        LINK = 'link', 'Link'
        TAREFA = 'tarefa', 'Tarefa'

    trilha = models.ForeignKey(Trilha, on_delete=models.PROTECT, related_name='atividades')
    titulo = models.CharField('título', max_length=200)
    descricao = models.TextField('descrição', blank=True)
    tipo = models.CharField('tipo', max_length=10, choices=Tipo.choices)
    endereco = models.URLField('endereço', blank=True)
    ordem = models.PositiveIntegerField('ordem')
    obrigatoria = models.BooleanField('obrigatória', default=True)
    exige_validacao = models.BooleanField('exige validação', default=True)
    prazo_fixo = models.DateField('prazo fixo', null=True, blank=True)
    dias_apos_inscricao = models.PositiveIntegerField('dias após a inscrição', null=True, blank=True)
    criada_em = models.DateTimeField('criada em', auto_now_add=True)
    arquivada_em = models.DateTimeField('arquivada em', null=True, blank=True)  # vazio = ativa

    class Meta:
        ordering = ['ordem', 'id']
        constraints = [
            models.CheckConstraint(   # 3.4.3: nunca os dois prazos
                condition=models.Q(prazo_fixo__isnull=True) | models.Q(dias_apos_inscricao__isnull=True),
                name='atividade_um_prazo'),
            models.CheckConstraint(   # 3.4.3: dias > 0
                condition=models.Q(dias_apos_inscricao__isnull=True) | models.Q(dias_apos_inscricao__gt=0),
                name='atividade_dias_positivo'),
            models.CheckConstraint(   # 3.4.2: Link exige endereço
                condition=~models.Q(tipo='link') | ~models.Q(endereco=''),
                name='atividade_link_com_endereco'),
        ]
```

As restrições do banco são a última barreira. As mensagens amigáveis vêm da validação dos forms (seção 5).

A `AtividadeTrilha` **não** é registrada no `/admin/` (RN-16).

---

## 3. Migrações

| Migração | Tipo | Conteúdo | Reversa |
|---|---|---|---|
| `0006_etapa_status_atividades` | Esquema | `AddField` de `etapa`, `status`, `publicada_em`, `arquivada_em`; `AlterField` de `usuario_criador` para aceitar vazio; `CreateModel` de `AtividadeTrilha` | Automática |
| `0007_converter_trilhas` | Dados | Ver abaixo | Função reversa |
| `0008_remover_tipo_pre_incubacao` | Esquema | Remove a restrição `trilha_pre_incubacao_unica`; `AlterField` de `tipo` com `default='custom'` (para a reversa conseguir recriar a coluna); `RemoveField` de `tipo` e `pre_incubacao`; `AddConstraint` de `trilha_etapa_unica` e `trilha_dono_conforme_tipo` | Automática |

**`0007_converter_trilhas`** (spec, seção 6, e decisões 7.2 e 7.4):
1. A trilha com `pre_incubacao=True` → `etapa='pre_incubacao'`, `status='publicada'`, `publicada_em=agora`, `usuario_criador=None`. Inscrições existentes não são tocadas.
2. Todas as outras trilhas → `etapa=''`, `status='publicada'`, `publicada_em=agora` (continuam personalizadas, com o dono atual).
3. Para cada etapa que ainda não tem trilha (Incubação, Desincubação e, se a `0005` não tiver criado, Pré-incubação), cria a trilha de etapa em **rascunho**, sem dono e sem atividades. Títulos: "Pré-incubação", "Incubação", "Desincubação".

**Reversa da `0007`:** a trilha de etapa Pré-incubação volta a `pre_incubacao=True`, `tipo='padrao'`, com dono = primeiro usuário IS (ou o primeiro superusuário, se não houver IS); as trilhas de Incubação e Desincubação criadas aqui são apagadas (junto com suas atividades, que senão bloqueariam pelo `PROTECT`) se não tiverem inscrições; as personalizadas voltam a `tipo='custom'`. Se não houver nenhum usuário IS nem superusuário, a reversa falha com uma mensagem clara, em vez de deixar a trilha sem dono.

**A testar à mão antes do PR** (Constituição, Art. 7.4): rodar as três migrações para frente e para trás numa cópia do `db.sqlite3` local e conferir que as inscrições na pré-incubação continuam ligadas à mesma trilha.

---

## 4. Regras (`trilhas/regras.py`)

Todas as decisões de "pode ou não pode" da F3 ficam aqui. As views só chamam estas funções. Cada função cita o ID que implementa.

```python
class RegraViolada(Exception):
    """Ação não permitida pelo estado da trilha. A mensagem é mostrada ao usuário."""

# Quem é quem
def e_is(usuario): ...                                  # papel IS
def e_dono(usuario, trilha): ...                       # personalizada: usuario_criador; etapa: papel IS
def empreendimentos_atendidos(professor): ...          # inscrição (qualquer status) em trilha do professor

# Ver (TRL-10, spec 3.6)
def trilhas_visiveis(usuario): ...                     # queryset por papel
def pode_ver(usuario, trilha): ...

# Editar (TRL-07, spec 3.3)
def pode_editar(usuario, trilha): ...                  # dono ou IS; nunca outro professor, empreendedor ou admin
def exige_confirmacao(usuario, trilha): ...            # IS alterando trilha personalizada de professor (7.7)

# Estados (TRL-05, spec 3.5)
def publicar(trilha, usuario): ...                     # rascunho → publicada; ≥ 1 atividade ativa (A-09)
def arquivar(trilha, usuario): ...                     # só personalizada; sem inscrição ativa ou pausada (A-15, 7.3)

# Atividades (TRL-04, TRL-06, TRL-08)
def acrescentar_atividade(trilha, dados): ...          # ordem = última + 1 (A-08, A-12)
def campos_editaveis(trilha): ...                      # rascunho: todos; publicada: título, descrição, endereço (A-11)
def apagar_atividade(atividade): ...                   # só em rascunho (A-13)
def arquivar_atividade(atividade): ...                 # preenche arquivada_em
def mover_atividade(atividade, direcao): ...           # só em rascunho (A-23)
```

- Falta de **permissão** (quem) → `PermissionDenied` → 403 (Constituição, Art. 3.3).
- Falta de **condição de estado** (quando) → `RegraViolada` → a view mostra a mensagem e não muda nada.
- Trilha arquivada: qualquer função de alteração levanta `RegraViolada` (A-14).

**`trilhas_visiveis(usuario)`** (spec 3.6):

| Papel | Queryset |
|---|---|
| IS | `Trilha.objects.all()` |
| Professor | as suas **∪** as de etapa **∪** personalizadas publicadas ou arquivadas com inscrição de algum empreendimento de `empreendimentos_atendidos(professor)` |
| Empreendedor | trilhas com inscrição do seu empreendimento, exceto rascunho |
| Admin | nenhuma |

---

## 5. Forms (`trilhas/forms.py`)

| Form | Campos | Usado em |
|---|---|---|
| `TrilhaForm` (existente) | `titulo`, `descricao` (+ `confirmar`, ver abaixo) | Criar e editar trilha |
| `AtividadeForm` (novo) | `titulo`, `descricao`, `tipo`, `endereco`, `obrigatoria`, `exige_validacao`, `prazo_fixo`, `dias_apos_inscricao` (+ `confirmar`) | Criar atividade; editar em rascunho |
| `AtividadeTextoForm` (novo) | `titulo`, `descricao`, `endereco` (+ `confirmar`) | Editar atividade de trilha publicada (A-11) |

- `AtividadeForm.clean()`: Link sem endereço → erro em `endereco` (A-05); dois prazos → erro geral (A-06); dias ≤ 0 → erro em `dias_apos_inscricao`.
- `AtividadeTextoForm.clean()`: se a atividade é do tipo Link, o endereço continua obrigatório.
- Como o `AtividadeTextoForm` **não tem** os campos de tipo, obrigatoriedade, validação e prazo, valores forjados nesses campos são ignorados (A-11, Art. 3.4). O mesmo vale para `etapa`, `status` e dono no `TrilhaForm` (A-04).
- **Campo `confirmar`** (7.7, A-18): um checkbox "Confirmo que quero alterar a trilha de *Nome do professor*". Só é adicionado ao form quando `exige_confirmacao(usuario, trilha)`; nesse caso é obrigatório. Os botões de ação sem formulário (publicar, arquivar, apagar, mover) também enviam `confirmar=1`, e a view recusa sem ele. **A confirmação é checada no servidor**, não só com JavaScript.

---

## 6. Rotas e views

| Rota | Nome | Método | Quem | O que faz | Critérios |
|---|---|---|---|---|---|
| `trilhas/` | `minhas` | GET | Professor | As suas, as de etapa e as de outros nos empreendimentos que atende, em três seções | A-21 |
| `trilhas/todas/` | `todas` | GET | IS | Todas, com filtro por tipo (etapa / personalizada) e por estado | A-02 |
| `trilhas/inscritas/` | `inscritas` | GET | Empreendedor | Sem mudança | A-22 |
| `trilhas/nova/` | `criar` | GET/POST | Professor, IS | Cria trilha personalizada em rascunho e redireciona para o detalhe | A-01, A-03, A-04 |
| `trilhas/<pk>/` | `detalhe` | GET | `pode_ver` | Dados, estado, atividades e os botões que `regras` permite | A-20 a A-22 |
| `trilhas/<pk>/editar/` | `editar` | GET/POST | `pode_editar` | Título e descrição | A-14, A-16 a A-19 |
| `trilhas/<pk>/publicar/` | `publicar` | POST | `pode_editar` | `regras.publicar` | A-09, A-10 |
| `trilhas/<pk>/arquivar/` | `arquivar` | POST | `pode_editar` | `regras.arquivar` | A-03, A-15 |
| `trilhas/<pk>/atividades/nova/` | `atividade_criar` | GET/POST | `pode_editar` | `AtividadeForm` + `regras.acrescentar_atividade` | A-05 a A-08, A-12 |
| `trilhas/atividades/<pk>/editar/` | `atividade_editar` | GET/POST | `pode_editar` | `AtividadeForm` em rascunho; `AtividadeTextoForm` em publicada | A-11 |
| `trilhas/atividades/<pk>/apagar/` | `atividade_apagar` | POST | `pode_editar` | Só em rascunho | A-13 |
| `trilhas/atividades/<pk>/arquivar/` | `atividade_arquivar` | POST | `pode_editar` | Preenche `arquivada_em` | A-13 |
| `trilhas/atividades/<pk>/mover/<cima\|baixo>/` | `atividade_mover` | POST | `pode_editar` | Só em rascunho (S) | A-23 |

- Rotas de lista usam `@papel_requerido`; rotas de uma trilha usam `@login_required` e chamam `regras.pode_ver` / `regras.pode_editar`, que levantam `PermissionDenied`.
- Ações que mudam estado aceitam **só POST** (`@require_POST`), como as de inscrição.
- `inscricoes/` e as transições de inscrição **não mudam** nesta feature (a regra "só trilha publicada" é da F4), exceto que o filtro da tela de inscrições deixa de usar `Trilha.Tipo`.

---

## 7. Templates

| Template | Situação |
|---|---|
| `trilhas/detalhe.html` | **Novo.** Cabeçalho com tipo, etapa, estado e dono; lista de atividades em ordem (arquivadas separadas); botões conforme `regras` |
| `trilhas/atividade_form.html` | **Novo.** Criar e editar atividade; mostra o endereço só quando o tipo é Link (JavaScript simples, opcional: o servidor valida de qualquer forma) |
| `partials/confirmacao_is.html` | **Novo.** Aviso "Esta trilha é de *Nome do professor*" + checkbox `confirmar`, incluído nos forms quando necessário |
| `trilhas/criar_trilha.html` | Reaproveitado para editar (título muda conforme o caso) |
| `trilhas/minhas_trilhas.html` | Três seções (minhas, de etapa, de outros professores) e o estado de cada trilha |
| `trilhas/todas_trilhas.html` | Troca `tipo`/`pre_incubacao` por etapa e estado; filtros novos |
| `partials/header.html` e `usuarios/home.html` | Link "Nova trilha" também para a IS |

Estados aparecem com texto, não só com cor (RNF-05).

---

## 8. Outros ajustes

- **`trilhas/signals.py`:** `Trilha.objects.filter(etapa=Trilha.Etapa.PRE_INCUBACAO).first()`, no lugar de `pre_incubacao=True`. O comportamento continua o mesmo; a regra "só se estiver publicada" é da F4 (INS-02).
- **`trilhas/admin.py`:** `list_display` e `list_filter` com `etapa` e `status`, no lugar de `tipo` e `pre_incubacao`. Tirar os models de negócio do admin (RN-16) fica para a F1.
- **`popular_banco`:** remove `tipo` das trilhas; acrescenta 2 ou 3 atividades a cada trilha de etapa e à trilha do professor, e publica as trilhas de etapa e a do professor. A trilha "Trilha Base da Incubadora" deixa de existir no mock (o papel dela agora é da trilha de etapa Pré-incubação).
- **`InscricaoForm`:** continua aceitando qualquer trilha (a restrição é da F4), mas sem referência a `Tipo`.

---

## 9. Testes

Arquivo novo `trilhas/test_f3.py`, um teste por critério, com o ID no nome (Constituição, Art. 6.2). Todo controle de acesso testa o caso negado (Art. 6.3).

| Critério | Teste |
|---|---|
| A-01 | `test_a01_trilha_criada_e_personalizada_do_criador_em_rascunho` (professor e IS) |
| A-02 | `test_a02_existem_tres_trilhas_de_etapa` |
| A-03 | `test_a03_is_cria_trilha_personalizada_nao_de_etapa`, `test_a03_trilha_de_etapa_nao_pode_ser_arquivada` |
| A-04 | `test_a04_etapa_dono_e_status_forjados_sao_ignorados` |
| A-05 | `test_a05_link_sem_endereco_ou_invalido_e_recusado` |
| A-06 | `test_a06_dois_prazos_sao_recusados` |
| A-07 | `test_a07_padrao_obrigatoria_e_exige_validacao` |
| A-08, A-12 | `test_a08_atividade_nova_entra_no_fim`, `test_a12_atividade_acrescentada_em_publicada_entra_no_fim` |
| A-09 | `test_a09_publicar_exige_atividade_ativa` |
| A-10 | `test_a10_publicada_nao_volta_a_rascunho` |
| A-11 | `test_a11_publicada_aceita_texto_e_ignora_tipo_prazo_e_validacao` |
| A-13 | `test_a13_atividade_de_publicada_nao_e_apagada_so_arquivada` |
| A-14 | `test_a14_trilha_arquivada_nao_e_editavel` |
| A-15 | `test_a15_nao_arquiva_trilha_com_inscricao_ativa_ou_pausada` |
| A-16 | `test_a16_professor_nao_altera_trilha_de_outro` (editar, publicar, arquivar) |
| A-17 | `test_a17_professor_nao_edita_trilha_de_etapa_nem_da_is` |
| A-18 | `test_a18_is_altera_trilha_de_professor_so_com_confirmacao` (sem `confirmar` → nada muda; com → muda; vale para editar, publicar e arquivar) |
| A-18b | `test_a18b_edicao_pela_is_mantem_o_professor_como_dono` |
| A-19 | `test_a19_empreendedor_e_admin_nao_abrem_edicao` |
| A-20 | `test_a20_rascunho_visivel_so_para_dono_e_is` |
| A-21 | `test_a21_professor_ve_trilha_de_outro_so_se_atende_o_empreendimento` |
| A-22 | `test_a22_empreendedor_nao_ve_trilha_sem_inscricao` |
| A-23 | `test_a23_reordenar_so_em_rascunho` |
| Migração | `test_migracao_pre_incubacao_vira_etapa_publicada_sem_perder_inscricoes` |

**Testes existentes em `trilhas/tests.py`** (23 linhas usam `Trilha.Tipo` ou `pre_incubacao`): trocar por `etapa` e `status`. A intenção de cada teste não muda; os que já cobrem a mesma coisa que um critério novo podem ser removidos em favor do teste novo.

**Verificação final:** `python manage.py test` e `python manage.py makemigrations --check --dry-run` sem erros.

---

## 10. Riscos

| Risco | Mitigação |
|---|---|
| A conversão perder o vínculo das inscrições na pré-incubação | A `0007` só altera campos da trilha, nunca recria; teste de migração + teste manual numa cópia do banco |
| `CheckConstraint` com `condition=` (sintaxe do Django 5.1+) | O projeto usa Django 6.1; confirmar com `makemigrations` |
| Banco de produção (Postgres) com dados diferentes do local | A conversão não depende de existir usuário IS (dono vazio nas trilhas de etapa) |
| Esquecer uma checagem de permissão numa view nova | Toda view de trilha passa por `regras.pode_ver` ou `regras.pode_editar`; um teste de negado por rota |
