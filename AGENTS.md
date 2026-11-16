# AGENTS.md — SGIS

Instruções para agentes de IA (Claude Code, OpenCode e outros) que trabalham neste repositório.

**SGIS** é o Sistema de Gestão da Incubadora Social da UFSM: a IS organiza as etapas da incubação, professores criam trilhas, e empreendimentos percorrem as trilhas em que foram inscritos.

## Leia antes de qualquer tarefa

1. [`specs/00-constituicao.md`](specs/00-constituicao.md): as regras de **como** construir. Prevalece sobre tudo.
2. [`specs/SGIS_SPEC_MVP_v0.4.md`](specs/SGIS_SPEC_MVP_v0.4.md): a spec mãe, com **o que** o sistema faz. Vocabulário na seção 2, permissões na seção 6, regras de negócio na seção 7, modelo de dados na seção 8.
3. `specs/F#-nome/spec.md` e `plan.md` da feature em que você vai trabalhar.

**Não use** nada em `specs/_arquivo/`: são documentos substituídos.

## Este projeto segue Spec Driven Development

- **Não implemente nada** que não tenha `spec.md` **e** `plan.md` com `Estado: aprovado` na pasta da feature. Se não houver, pare e avise.
- Implemente **o que a spec diz, nem mais nem menos**. Trabalhe **uma tarefa do `tasks.md` por vez**.
- Encontrou lacuna, ambiguidade ou contradição na spec? **Pergunte.** Não decida regra de negócio por conta própria, nem preencha a lacuna com uma suposição.
- Regra nova ou alterada vai primeiro para a spec, nunca direto para o código.
- Cite os IDs da spec (por exemplo `EXE-04`, `RN-04`) em planos, commits, PRs e nomes de testes.
- Só o responsável pelo projeto aprova documentos. Não marque nada como `aprovado`.

## Stack

- Python 3.12+ e Django 6.1. Páginas renderizadas no servidor (templates do Django), Tailwind por CDN.
- SQLite em desenvolvimento; PostgreSQL em produção via `DATABASE_URL` (`dj-database-url`).
- Deploy no Render (`render.yaml`), com gunicorn e WhiteNoise.
- **Sem** API pública, SPA ou framework de frontend. Dependência nova só com justificativa no `plan.md`.

## Estrutura

| Caminho | Conteúdo |
|---|---|
| `sgis/` | `settings.py` (configuração por variáveis de ambiente), `urls.py`, templates base em `sgis/templates/` (`base.html`, `partials/header.html`) |
| `usuarios/` | Model `Usuario` (login por e-mail, campo `papel`), login/logout, cadastro pela IS, decorator `papel_requerido`, comando `popular_banco` |
| `empreendimentos/` | Model `Empreendimento` (campo `representante` → empreendedor) |
| `trilhas/` | Models `Trilha` e `Inscricao`, signal de inscrição automática na pré-incubação, views de trilhas e inscrições |

## Comandos

```bash
python manage.py test                              # toda a suíte
python manage.py makemigrations --check --dry-run  # nenhuma migração pendente
python manage.py migrate
python manage.py runserver
python manage.py popular_banco                     # dados fictícios, só em desenvolvimento
```

Antes de dizer que uma tarefa está pronta: rode os testes e o `makemigrations --check`, e informe o resultado real.

## Convenções de código

- **Português** em nomes de domínio, interface, mensagens e commits. Siga o vocabulário da spec: **empreendimento** é o negócio, **empreendedor** é a pessoa (papel `empreendedor`), **representante** é o vínculo.
- **Permissão no servidor:** use `@papel_requerido(Usuario.Papel.X)` (de `usuarios/decorators.py`) nas views restritas a um papel. Nunca confie em esconder um link.
- **Campos definidos pelo servidor** (dono, autor, status, papel) nunca vêm do formulário: defina-os na view, depois de `form.save(commit=False)`.
- **Nada se apaga:** use `on_delete=models.PROTECT` entre registros de negócio; desative, cancele ou arquive em vez de apagar.
- **Estados derivados** (atrasada, progresso, etapa atual) são calculados, nunca gravados.
- **Regras de transição de estado** ficam num lugar só, no padrão do `TRANSICOES_INSCRICAO` em `trilhas/regras.py`.
- **Migrações** aditivas e reversíveis: `RenameField` para renomear; migração de dados sempre com função reversa. Nunca edite migrações já aplicadas.
- Siga o estilo do código ao redor: densidade de comentários, nomes e padrões já usados.

## Testes

- Todo requisito **M** e toda regra de negócio têm teste. Todo controle de acesso tem teste do caso **negado**.
- O nome ou a docstring do teste cita o ID: `test_exe06_devolver_sem_comentario_e_recusado`.
- Não compare mensagens traduzidas do Django: use `form.has_error('campo')` ou o código do erro.
- A migração `trilhas/0005` cria a trilha de pré-incubação também no banco de testes. Considere isso ao contar registros.

## Segurança

- Segredos só em variáveis de ambiente (ver `.env.example`). Nunca escreva chave, senha ou URL de banco no código.
- Nunca rode `popular_banco` contra produção.
- Não exponha dados pessoais em logs, mensagens ou URLs.

## Git e PRs

- Branches `docs/…`, `feat/…`, `fix/…`, `refactor/…`. Commits no formato `tipo: descrição`, em português.
- Um PR por tarefa; documentação e código em PRs separados. Use o modelo em `.github/pull_request_template.md`.
- Não faça push, merge nem force-push sem pedido explícito.
