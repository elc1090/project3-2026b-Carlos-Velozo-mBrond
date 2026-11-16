# Levantamento: código atual × spec v0.4

**Base:** `main` em `1dea3a8` (2026-10-28) · 110 testes passando · Documento informativo, não precisa de aprovação.

**Histórico:** primeira versão em 2026-10-23 (`cbe3135`, 41 testes). Atualizado em 2026-10-28 depois da F3 (trilhas) e da troca de senha (ACE-07).

Para cada requisito da [`SGIS_SPEC_MVP_v0.4.md`](SGIS_SPEC_MVP_v0.4.md), o que o código faz hoje. Serve de entrada para o `spec.md` e o `plan.md` de cada feature: o que está **diferente** vira tarefa de ajuste, o que está **faltando** vira tarefa nova.

**Legenda:** ✅ feito · 🟡 parcial · 🔀 feito diferente da spec · ❌ faltando

---

## Resumo

| Feature | ✅ | 🟡 | 🔀 | ❌ | Observação |
|---|---|---|---|---|---|
| Seção 4 · Nada sem login | 0 | 0 | 1 | 2 | Hoje a proteção é view por view |
| F1 · Acesso e contas | 2 | 5 | 1 | 6 | Login, logout, criação de contas pela IS e troca da própria senha |
| F2 · Empreendimentos | 0 | 2 | 1 | 3 | Sem nenhuma tela; só pelo admin |
| F3 · Trilhas | 9 | 0 | 0 | 1 | **Concluída.** Só falta duplicar trilha (prioridade C) |
| F4 · Inscrição e etapas | 1 | 3 | 1 | 6 | Inscrição pela IS existe; etapas não. A F3 criou os estados da trilha, mas a inscrição ainda não os respeita |
| F5 · Execução e validação | 0 | 0 | 0 | 11 | Não existe |
| F6 · Visão do professor | 0 | 0 | 0 | 3 | Não existe |
| F7 · Prontuário | 0 | 0 | 0 | 4 | Não existe |
| F8 · Níveis por eixo | 0 | 0 | 0 | 5 | Não existe |
| F9 · Estatísticas | 0 | 0 | 0 | 3 | Não existe |

---

## Seção 4 · Nada sem login

| ID | Situação | Hoje |
|---|---|---|
| ACE-00 | 🔀 | Cada view tem `@login_required` ou `@papel_requerido`. Endereço inexistente responde **404** para anônimo, em vez de redirecionar ao login. |
| ACE-00a | ❌ | Não há verificação de saúde nem `robots.txt`. O `base.html` tem `<meta name="robots" content="noindex">`, o que ajuda, mas não substitui. |
| ACE-00b | ❌ | Não há proteção por padrão (`LoginRequiredMiddleware`) nem o teste que percorre todas as rotas. |

## F1 · Acesso e contas

| ID | Situação | Hoje |
|---|---|---|
| ACE-01 | 🟡 | Login por e-mail e senha, com o e-mail normalizado para minúsculas no form. Contas criadas pelo admin ou pelo `createsuperuser` podem ter maiúsculas e aí não entram. A mensagem "Esta conta está desativada" não é genérica (na prática é inalcançável, porque o `authenticate` já recusa contas inativas). |
| ACE-02 | 🟡 | Todos caem na mesma `home`, que mostra links conforme o papel. Não há área própria por papel. |
| ACE-03 | 🟡 | Logout existe. Não há expiração por inatividade (a sessão dura o padrão do Django, 2 semanas). |
| ACE-04 | ✅ | `/usuarios/novo/`: a IS cria professor e empreendedor com senha inicial e não consegue criar IS nem admin. O admin cria qualquer papel pelo `/admin/`. |
| ACE-05 | ❌ | Criar um empreendedor não cria o empreendimento. O empreendedor fica sem empreendimento e sem pré-incubação. |
| ACE-06 | ❌ | Não há `deve_trocar_senha`. |
| ACE-07 | ✅ | `/conta/senha/` ("Minha conta"): exige a senha atual, confirma a nova, aplica os validadores do Django e mantém a sessão (`update_session_auth_hash`). Veio do repositório de entrega (`26fd31f` → `9833adf`), sem spec da F1 (exceção ao Art. 1.1). |
| ACE-08 | ❌ | Não há orientação na tela de login nem redefinição de senha pela IS. |
| ACE-09 | ❌ | O link "Usuários" abre só o formulário de criação. Não há lista, edição, desativação nem reativação. |
| ACE-10 | 🟡 | Conta inativa não entra, e a sessão aberta deixa de valer na próxima requisição (o Django checa `is_active`). Mas só dá para desativar pelo `/admin/`. |
| ACE-11 | ❌ | Nada impede desativar a si mesmo ou o último admin. |
| ACE-12 | 🔀 | Validadores do Django ativos, mas com o mínimo padrão de **8** caracteres. A spec pede 10. |
| ACE-13 | 🟡 | O admin é criado com `createsuperuser` (padrão do Django). A IS inicial vem de `IS_EMAIL` e `IS_SENHA_INICIAL` (migração `usuarios/0002`). |
| ACE-14 | ❌ | Sem bloqueio por tentativas (S). |

## F2 · Empreendimentos

| ID | Situação | Hoje |
|---|---|---|
| EMP-01 | 🔀 | Model tem nome, tipo e descrição. **Tipo é texto livre**, não a lista (MEI, Associação, Coletivo, Outro). **Faltam e-mail e telefone de contato.** Sem tela para a IS: só pelo `/admin/`. |
| EMP-02 | 🟡 | FK `representante` garante um representante por empreendimento. Mas um mesmo usuário pode representar **vários** empreendimentos (a RN-01 pede exatamente um), e nada impede que o representante não tenha o papel empreendedor. |
| EMP-03 | ❌ | Sem lista. |
| EMP-04 | ❌ | Sem perfil do empreendimento. |
| EMP-05 | ❌ | Depende do EMP-04. |
| EMP-06 | 🟡 | Campo `desativado_em` existe e o empreendimento desativado não pode ser inscrito. O representante continua entrando normalmente. Sem tela. |
| — | 🔀 | **Sobra:** campo `usuario_professor_supervisor`, que a v0.4 descartou (RN-03, sem supervisão). Também aparece no admin e no `popular_banco`. |

## F3 · Trilhas

**Concluída em 2026-10-28** (tarefas T1 a T7). Detalhes na seção 6 da [`F3-trilhas/spec.md`](F3-trilhas/spec.md).

| ID | Situação | Hoje |
|---|---|---|
| TRL-01 | ✅ | Trilha com `etapa` (vazia nas personalizadas) e as três trilhas de etapa, sem usuário dono. |
| TRL-02 | ✅ | Professor e IS criam trilhas personalizadas, com atividades. |
| TRL-03 | ✅ | A IS edita e publica as trilhas de etapa pela interface. |
| TRL-04 | ✅ | `AtividadeTrilha` com tipo, endereço, obrigatoriedade, validação, prazo e ordem. |
| TRL-05 | ✅ | Rascunho → publicada → arquivada, com as regras em `trilhas/regras.py`. |
| TRL-06 | ✅ | Publicada: só textos mudam e atividades entram no fim; atividade de trilha publicada só é arquivada. |
| TRL-07 | ✅ | Dono e IS editam; a IS confirma antes de alterar trilha de professor. |
| TRL-08 | ✅ | Subir e descer atividades, só em rascunho. |
| TRL-09 | ❌ | Duplicar trilha (C). |
| TRL-10 | ✅ | Listas por papel e detalhe com 403 para quem não pode ver. |

## F4 · Inscrição e etapas

| ID | Situação | Hoje |
|---|---|---|
| INS-01 | 🟡 | A IS inscreve em `/trilhas/inscricoes/`. Mas o formulário oferece **qualquer** trilha: em rascunho, arquivada ou de etapa. Os estados já existem (F3); falta a inscrição respeitá-los. |
| INS-02 | 🟡 | Um signal inscreve todo empreendimento novo na trilha de etapa Pré-incubação, mesmo que ela esteja em rascunho. Se ela não existir, só grava um aviso no log; a IS não é avisada. |
| INS-03 | ❌ | Sem "avançar etapa". |
| INS-04 | ❌ | Nada impede duas etapas ao mesmo tempo. |
| INS-05 | ❌ | Etapa atual não é calculada em lugar nenhum. |
| INS-06 | 🟡 | Ativa, Pausada e Cancelada, com motivo e transições (`TRANSICOES_INSCRICAO`). **Falta Concluída** (e `concluido_em`). |
| INS-07 | 🔀 | A restrição no banco considera "não cancelada". Com o status Concluída, precisa passar a considerar só **ativa ou pausada**, senão um empreendimento que concluiu uma trilha não pode ser reinscrito. |
| INS-08 | ❌ | Depende da F5. |
| INS-09 | ✅ | O empreendedor só vê as inscrições do próprio empreendimento (canceladas ficam ocultas). |
| INS-10 | ❌ | (S). |
| INS-11 | ❌ | Pendente de confirmação na spec. |

## F5 a F9

Nada implementado:
- **F5 · Execução e validação** (EXE-01 a 11): não há models de execução nem de histórico.
- **F6 · Visão do professor** (PRO-01 a 03): não há painel.
- **F7 · Prontuário** (PRN-01 a 04): não há model de nota.
- **F8 · Níveis por eixo** (EIX-01 a 05): não há model de nível.
- **F9 · Estatísticas** (EST-01 a 03): não há painel.

---

## Regras transversais (constituição e seções 6, 7 e 11 da spec)

| Regra | Situação | Hoje |
|---|---|---|
| RN-16 · Admin não acessa dados de negócio | 🔀 | O `/admin/` registra `Trilha`, `Inscricao` e `Empreendimento` (a `AtividadeTrilha` ficou de fora). O admin vê e edita dados de negócio. Nas telas do sistema, o admin já não vê trilhas. |
| RN-11 · Nada se apaga | 🟡 | FKs de negócio usam `PROTECT` ✅. Mas o `/admin/` permite apagar trilhas e empreendimentos sem inscrição. |
| RNF-01 · Segurança | 🟡 | Produção com `DEBUG` desligado, HTTPS, cookies seguros e segredos no ambiente ✅. **Problema:** o login redireciona para o parâmetro `next` sem validar o destino (`redirect(request.GET.get('next'))`), o que permite *open redirect* para um site externo. |
| RNF-03 · Testes / Constituição Art. 6 | 🟡 | 110 testes. Os da F3 (`trilhas/test_f3.py`) citam o ID do critério; os mais antigos (`trilhas/tests.py`, `usuarios/tests.py`) não. Não há CI nem o teste "toda rota exige login". `empreendimentos` não tem testes. |
| Constituição Art. 7.5 · Regras num lugar só | 🟡 | As regras de trilha estão em `trilhas/regras.py` ✅. As transições de inscrição continuam em `trilhas/views.py`, junto das views. |
| Limpeza | — | `CLASSES_INPUT` duplicado em `usuarios/forms.py` e `trilhas/forms.py`. |

---

## O que muda no código que já existe

Ajustes que as features vão precisar fazer em código existente (não são features novas):

| Onde | Mudança | Feature |
|---|---|---|
| `Inscricao.Status` e restrição única | Acrescentar Concluída e `concluido_em`; restrição única passa a ser só entre ativa e pausada | F4 |
| `InscricaoForm` | Só trilhas personalizadas publicadas | F4 |
| Signal da pré-incubação | Só inscrever se a trilha de etapa Pré-incubação estiver publicada (INS-02) | F4 |
| `Empreendimento.usuario_professor_supervisor` | Remover (migração), e tirar do admin e do `popular_banco` | F2 |
| `Empreendimento.tipo` | Lista fixa + e-mail e telefone de contato | F2 |
| `Usuario` | `deve_trocar_senha`; senha mínima 10 | F1 |
| Login | Validar o `next` (`url_has_allowed_host_and_scheme`) | F1 |
| `sgis/settings.py` | `LoginRequiredMiddleware`, expiração por inatividade, `MinimumLengthValidator` com 10 | F1 / Seção 4 |
| `/admin/` | Tirar os models de negócio do admin, ou restringi-los ao superusuário técnico | F1 |
| Transições de inscrição em `trilhas/views.py` | Mover para um módulo de regras, como o `trilhas/regras.py` (Art. 7.5) | F4 |
| `popular_banco` | Tirar o `usuario_professor_supervisor` quando ele sair do model | F2 |
