# SGIS — Constituição

**Estado:** Aprovado · **Versão:** 1.1 · **Data:** 2026-10-23

Princípios que valem para **todo** o projeto. Nenhuma spec, plano, tarefa ou PR pode contrariá-los. Quando uma regra daqui conflitar com qualquer outro documento, vale esta.

As regras de negócio ficam na spec mãe (`SGIS_SPEC_MVP_v0.4.md`). Aqui ficam apenas as regras de **como** o sistema é construído.

---

## Artigo 1 · Spec antes do código

1. Nenhuma funcionalidade é implementada sem `spec.md` e `plan.md` **aprovados** na pasta da feature (Artigo 9).
2. Regra nova ou alterada vai **primeiro para a spec**, por PR, e só depois para o código. Se surgir uma dúvida durante a implementação, a implementação para naquele ponto até a spec responder.
3. O código implementa o que a spec diz, nem mais nem menos. Funcionalidade "a mais" é tratada como regra nova (item 2).
4. Correção de bug que **não muda regra** não precisa de spec, mas o PR cita o requisito afetado.

## Artigo 2 · Nada sem login

1. Toda rota exige usuário autenticado, salvo a lista fechada de exceções da spec mãe (seção 4).
2. Rota nova nasce protegida. Torná-la pública exige marcação explícita no código e menção no PR.
3. Um teste automatizado percorre todas as rotas registradas sem sessão e falha se alguma responder fora da lista de exceções.

## Artigo 3 · Permissão no servidor

1. Toda permissão é verificada **no servidor**, na view ou na camada de regras. Esconder um botão ou link nunca é controle de acesso.
2. As permissões seguem a tabela única da spec mãe (seção 6). Mudar quem pode o quê é mudar a spec.
3. Acesso negado responde 403 e não exibe nenhum dado. Dados de outro escopo não aparecem por lista, busca nem endereço direto.
4. Campos que o servidor define (dono, autor, status, papel) nunca são lidos do formulário enviado pelo usuário.

## Artigo 4 · Nada se apaga

1. Registros de negócio (inscrições, execuções, histórico, notas do prontuário, contas, empreendimentos, trilhas e atividades com progresso) **não são apagados**: são desativados, cancelados ou arquivados.
2. Chaves estrangeiras entre registros de negócio usam `PROTECT`.
3. Estados derivados (atrasada, progresso, etapa atual, situação) são **calculados**, nunca gravados.

## Artigo 5 · Segurança e segredos

1. Segredos (chave do Django, senhas, URLs de banco) ficam **só em variáveis de ambiente**. Nenhum segredo de produção entra no repositório. O `.env.example` documenta as variáveis, com valores fictícios.
2. Em produção: `DEBUG` desligado, HTTPS obrigatório e cookies seguros.
3. Senhas: só com hash, pelos validadores do Django (mínimo de 10 caracteres). Senha nunca aparece em log, mensagem ou URL.
4. Dados fictícios (comando `popular_banco`) nunca rodam em produção.
5. Coleta mínima de dados pessoais: só o que a spec pede.

## Artigo 6 · Testes

1. Todo requisito **M** e toda regra de negócio têm pelo menos um teste automatizado. Toda jornada (J-1 a J-8) tem um teste de ponta a ponta.
2. O nome ou a docstring do teste cita o ID que ele cobre: `test_exe06_devolver_sem_comentario_e_recusado`.
3. Todo controle de acesso tem teste do caso **negado**, não só do permitido.
4. A `main` só recebe código com todos os testes passando.
5. Os testes não dependem de textos traduzidos do Django: verificam o campo do erro ou o código, não a mensagem.

## Artigo 7 · Simplicidade técnica

1. **Stack:** Python 3.12+, Django, páginas renderizadas no servidor com templates do Django, Tailwind por CDN, SQLite em desenvolvimento e PostgreSQL em produção, hospedagem gratuita no Render.
2. Não há API pública, SPA nem framework de frontend. JavaScript só para pequenos ajustes de interface.
3. Dependência nova exige justificativa no `plan.md`.
4. Migrações são **aditivas e reversíveis**. Renomear campo usa `RenameField`; mudança de dado vem com migração de dados que tem função reversa.
5. Regras de negócio ficam num lugar só (por exemplo, uma função de transição por recurso), não espalhadas entre views e templates.
6. Prefira o recurso pronto do Django ao código próprio (validadores de senha, autenticação, mensagens, admin).

## Artigo 8 · Linguagem

1. Interface, documentação, mensagens de commit e nomes de domínio no código em **português**, seguindo o vocabulário da spec mãe (seção 2).
2. Uma palavra, um significado. **Empreendimento** é o negócio; **empreendedor** é a pessoa; **representante** é o vínculo entre eles. Termo novo entra primeiro no vocabulário da spec.
3. Termos técnicos do Django e do Python ficam como são (`models`, `views`, `ForeignKey`).

## Artigo 9 · Fluxo de trabalho

### 9.1 Documentos

```text
specs/
├── 00-constituicao.md          ← este arquivo
├── SGIS_SPEC_MVP_v0.4.md       ← spec mãe
└── F#-nome/                    ← uma pasta por feature da spec mãe
    ├── spec.md                 ← o quê e por quê
    ├── plan.md                 ← como
    └── tasks.md                ← passos
```

| Documento | Conteúdo | Não contém |
|---|---|---|
| `spec.md` | Requisitos da spec mãe que a feature cobre, critérios de aceite em *Dado / Quando / Então*, fora de escopo e dúvidas abertas | Tecnologia, nomes de classe, telas detalhadas |
| `plan.md` | Models e migrações, rotas e views, permissões, templates e o teste que cobre cada critério de aceite | Regras novas (essas vão para o `spec.md`) |
| `tasks.md` | Tarefas pequenas, cada uma cabendo num PR, com as dependências entre elas | — |

### 9.2 Estados de um documento

`rascunho` → `aprovado`. O estado fica na primeira linha do documento. Quem aprova é o **responsável pelo projeto** (Miguel Brondani): a aprovação dele, no PR ou registrada na conversa de trabalho, vale como aprovação.

### 9.3 Definição de pronto

- **Uma feature está pronta para o plano** quando o `spec.md` está aprovado e não tem dúvida bloqueante (`[Confirmar]`) para ela.
- **Uma tarefa está pronta para começar** quando o `plan.md` está aprovado e a tarefa virou issue.
- **Uma tarefa está concluída** quando a mudança foi aprovada pelo responsável e está na `main`, os testes do Artigo 6 passam e a spec continua dizendo a verdade sobre o código.

### 9.4 Pull requests

1. Código entra na `main` por PR aprovado pelo responsável. Documentos (specs, planos, tarefas) vão direto na `main` ou por branch e PR, conforme o responsável decidir em cada caso.
2. Um PR resolve uma tarefa. PR de documentação e PR de código são separados.
3. A descrição do PR cita os IDs implementados e a issue (`Closes #N`).
4. Branches: `docs/…`, `feat/…`, `fix/…`, `refactor/…`. Commits no formato `tipo: descrição` em português.

## Artigo 10 · Uso de IA

1. Ferramentas de IA podem propor planos, tarefas, código, testes e revisões. **Não decidem regras de negócio**: decisões são das pessoas da equipe e da IS, registradas na spec.
2. Toda saída de IA é revisada como código de qualquer outra pessoa: passa pelo PR e pelos testes.
3. A IA recebe como contexto a constituição, o `spec.md` e o `plan.md` da feature, e trabalha **uma tarefa por vez**.
4. Se a IA encontrar uma lacuna ou contradição na spec, ela pergunta; não preenche por conta própria.

## Artigo 11 · Alterações nesta constituição

Esta constituição só muda com a aprovação do responsável pelo projeto, com a versão e a data atualizadas no topo e uma linha no histórico abaixo.

---

## Histórico

| Versão | Data | Mudança |
|---|---|---|
| 1.0 | 2026-10-23 | Primeira versão. |
| 1.1 | 2026-10-23 | Aprovação pelo responsável pelo projeto (9.2, 9.3, 9.4 e 11); documentos podem ir direto na `main`. |
