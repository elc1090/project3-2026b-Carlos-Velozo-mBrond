# SGIS — Especificação do MVP

**Versão:** 0.4.5 (revisão após reunião com a IS)

**Substitui:** `_arquivo/SGIS_SPEC_MVP.md` (v0.3) e, para o MVP, o `_arquivo/MODELAGEM_BANCO.md`. A `_arquivo/SGIS_SPEC_COMPLETA.md` continua como registro da visão inicial, mas vários módulos dela foram descartados (ver seção 12).

**Convenções:** `ID` = requisito · `Prior.`: **M** obrigatório, **S** desejável, **C** só se sobrar tempo · `[Confirmar]` = decisão ainda pendente com a IS · `[ASSUMIDO]` = proposta da equipe, ainda não validada.

---

## 1. Objetivo

Um sistema fechado em que a Incubadora Social (IS) organiza as etapas da incubação, os professores oferecem trilhas personalizadas, e os empreendimentos percorrem as trilhas em que foram inscritos, marcando atividades que o dono da trilha valida.

**Hub e IS são a mesma coisa.** O sistema atende uma única incubadora.

---

## 2. Vocabulário

| Termo | Significado |
|---|---|
| **Empreendimento** | O negócio incubado (MEI, associação, coletivo…). |
| **Empreendedor** | A pessoa que faz login em nome do empreendimento. É o **representante** dele. |
| **Etapa** | Fase da incubação: **Pré-incubação → Incubação → Desincubação**. [Confirmar o nome da última etapa] |
| **Trilha de etapa** | Trilha criada pela IS, comum a todos os empreendimentos daquela etapa. Existe uma por etapa. |
| **Trilha personalizada** | Trilha criada por um professor ou pela IS, sem etapa, em que só alguns empreendimentos são inscritos. |
| **Dono da trilha** | Quem a criou. É quem edita e quem valida as atividades. |
| **Inscrição** | Decisão da IS de colocar um empreendimento numa trilha. |
| **Execução** | O andamento de uma atividade para um empreendimento inscrito. |
| **Professor que atende** | Professor dono de alguma trilha em que o empreendimento está ou esteve inscrito. |
| **Prontuário** | Notas no perfil do empreendimento, para registrar o que já foi trabalhado. |
| **Nível por eixo** | Nível atual (N1, N2, N3) do empreendimento em cada um dos 5 eixos, definido pela IS. |

---

## 3. Papéis

| Papel | No MVP |
|---|---|
| **Empreendedor** | Vê o perfil do próprio empreendimento, as trilhas em que ele está inscrito, marca atividades como concluídas, vê devoluções, o prontuário e os níveis por eixo. |
| **Professor** | Cria trilhas personalizadas, valida ou devolve atividades delas, vê os empreendimentos que atende, com as trilhas e o status em cada uma, e escreve no prontuário deles. |
| **IS** | Cria contas de professores e empreendedores, mantém as trilhas de etapa, cria trilhas personalizadas, inscreve empreendimentos, avança etapas, valida as trilhas de etapa e as suas personalizadas, define níveis por eixo, escreve no prontuário e vê as estatísticas. |
| **Admin** | Gerencia contas de todos os papéis, inclusive IS e admin. Não acessa dados de negócio. |

Cada usuário tem um único papel.

---

## 4. Regra transversal: nada disponível sem login

| ID | Requisito | Prior. |
|---|---|---|
| ACE-00 | Todo endereço exige usuário autenticado. Anônimos são redirecionados ao login, **inclusive** em endereços que não existem. | M |
| ACE-00a | **Exceções públicas (lista fechada):** tela de login; verificação de saúde do serviço (responde só "ok"); `robots.txt` bloqueando indexação; arquivos estáticos, que não têm dados. | M |
| ACE-00b | Toda rota nova nasce protegida. Torná-la pública exige marcação explícita, revisada em code review. | M |

**Aceite ACE-00:** *Dado* um visitante sem sessão, *quando* abre qualquer endereço fora da lista de exceções (existente ou não), *então* vai ao login e nenhum dado ou mensagem de "não encontrado" é exibido.

---

## 5. Requisitos funcionais

### F1 · Acesso e contas

| ID | Requisito | Prior. |
|---|---|---|
| ACE-01 | Login com e-mail e senha. O e-mail não diferencia maiúsculas. Erro genérico: "e-mail ou senha incorretos". | M |
| ACE-02 | Após o login, o usuário vai para a área do seu papel. | M |
| ACE-03 | Logout e expiração da sessão por inatividade. | M |
| ACE-04 | A **IS cria contas** de professor e de empreendedor, definindo uma senha inicial. O **admin** cria contas de qualquer papel. A IS não cria contas IS nem admin. | M |
| ACE-05 | Ao criar um empreendedor, a IS informa também os dados do empreendimento (F2). Usuário e empreendimento são criados juntos: se um falhar, nenhum é salvo. | M |
| ACE-06 | Toda conta criada por outra pessoa nasce com **troca de senha obrigatória**: no primeiro acesso, o usuário só consegue usar o sistema depois de trocar a senha. | M |
| ACE-07 | O usuário altera a própria senha estando logado (exige a senha atual). | M |
| ACE-08 | **Esqueci a senha:** sem fluxo por e-mail no MVP. A tela de login orienta: "entre em contato com a Incubadora Social". A IS redefine a senha de professores e empreendedores, e a conta volta a exigir troca no próximo acesso. | M |
| ACE-09 | **Gestão de contas:** lista com nome, e-mail, papel, status e data de criação, com filtro por papel. A IS edita, desativa e reativa contas de professor e empreendedor; o admin, de todos os papéis. Nada é apagado. | M |
| ACE-10 | Conta desativada não entra e perde as sessões abertas. | M |
| ACE-11 | Ninguém desativa a si mesmo nem a última conta ativa de admin. | M |
| ACE-12 | A senha passa pelos validadores do Django, com **mínimo de 10 caracteres**. | M |
| ACE-13 | A primeira conta de admin é criada na implantação, por comando. A conta inicial da IS vem de variáveis de ambiente. | M |
| ACE-14 | Bloqueio temporário após tentativas de login malsucedidas repetidas. | S |

### F2 · Empreendimentos

| ID | Requisito | Prior. |
|---|---|---|
| EMP-01 | A IS cadastra e edita o empreendimento: nome, tipo (MEI, Associação, Coletivo, Outro), descrição, e-mail e telefone de contato. | M |
| EMP-02 | Cada empreendimento tem **um único representante** (empreendedor). | M |
| EMP-03 | A IS lista os empreendimentos com filtros: ativos, desativados e por etapa atual. | M |
| EMP-04 | **Perfil do empreendimento:** dados, etapa atual, níveis por eixo, trilhas em que está inscrito (com status) e prontuário. | M |
| EMP-05 | Quem vê o perfil: a IS (todos), os professores que o atendem e o próprio representante. | M |
| EMP-06 | A IS desativa um empreendimento sem apagar histórico. O representante perde o acesso enquanto o empreendimento estiver desativado. | S |

### F3 · Trilhas

| ID | Requisito | Prior. |
|---|---|---|
| TRL-01 | Há dois tipos de trilha: **de etapa** (da IS, exatamente uma por etapa, criadas pelo sistema) e **personalizada** (criada por um professor ou pela IS). | M |
| TRL-02 | O professor e a IS criam trilhas personalizadas: título, descrição e atividades. Uma trilha personalizada da IS não é trilha de etapa. | M |
| TRL-03 | A IS cria e mantém a trilha de cada etapa: título, descrição e atividades. | M |
| TRL-04 | **Atividade:** título, descrição, tipo (**Leitura, Link, Tarefa**), endereço (obrigatório para Link), obrigatória (sim/não), exige validação (padrão **sim**), prazo fixo **ou** em dias após a inscrição, e ordem. | M |
| TRL-05 | **Estados da trilha:** rascunho → publicada → arquivada. Publicar exige pelo menos uma atividade ativa. Rascunho não aparece para empreendimentos. | M |
| TRL-06 | Editar trilha publicada: ajustar textos e acrescentar atividades ao final. Atividade com progresso só pode ser arquivada. Trilha com progresso nunca é apagada. | M |
| TRL-07 | O dono edita a trilha. A IS também tem plenos poderes de edição sobre as trilhas personalizadas de professores (editar, publicar, arquivar), com uma confirmação antes de cada alteração. O dono continua sendo o professor. | M |
| TRL-08 | Reordenar atividades. | S |
| TRL-09 | Duplicar trilha. | C |
| TRL-10 | **Quem vê trilhas:** a IS vê todas; o professor vê as suas, as trilhas de etapa e, em leitura, as outras trilhas personalizadas em que os empreendimentos que ele atende estão inscritos; o empreendedor vê só as trilhas em que está inscrito. | M |

### F4 · Inscrição e etapas

| ID | Requisito | Prior. |
|---|---|---|
| INS-01 | A IS inscreve um empreendimento numa trilha personalizada **publicada**. | M |
| INS-02 | Todo empreendimento novo é inscrito automaticamente na trilha de **pré-incubação**. Se ela não estiver publicada, o cadastro avisa a IS e a inscrição é feita quando ela for publicada. [ASSUMIDO] | M |
| INS-03 | **Avançar etapa:** tela própria em que a IS move o empreendimento para a etapa seguinte. A inscrição na trilha da etapa atual vira **Concluída** e é criada a inscrição na trilha da próxima etapa. | M |
| INS-04 | O empreendimento está em **uma única etapa por vez**: no máximo uma inscrição ativa ou pausada em trilha de etapa. | M |
| INS-05 | A **etapa atual** é a trilha de etapa com inscrição ativa ou pausada. Não é guardada em campo próprio. | M |
| INS-06 | Status da inscrição: **Ativa, Pausada, Concluída, Cancelada**. A IS pausa, reativa ou cancela, com motivo opcional. O histórico é preservado. | M |
| INS-07 | Não pode haver duas inscrições ativas ou pausadas do mesmo empreendimento na mesma trilha. | M |
| INS-08 | Com a inscrição pausada, o empreendedor vê a trilha, mas não marca atividades. Os prazos continuam correndo. | M |
| INS-09 | O empreendedor vê só as inscrições do próprio empreendimento. | M |
| INS-10 | Inscrição de vários empreendimentos de uma vez. | S |
| INS-11 | Avançar a partir da Desincubação **encerra a incubação**: a inscrição fica Concluída e o empreendimento fica sem etapa ativa ("incubação concluída"). | M |

### F5 · Execução e validação

| ID | Requisito | Prior. |
|---|---|---|
| EXE-01 | Ao criar uma inscrição, o sistema cria uma **execução** para cada atividade ativa da trilha. Ao acrescentar uma atividade a uma trilha publicada, cria execuções para as inscrições ativas e pausadas. | M |
| EXE-02 | **Prazo da execução:** o prazo fixo da atividade, ou os dias após a **data mais recente** entre a inscrição e a criação da atividade. | M |
| EXE-03 | Status da execução: **Pendente, Aguardando validação, Devolvida, Concluída**. **Atrasada** é calculada (não concluída e prazo vencido), nunca gravada. | M |
| EXE-04 | O empreendedor **marca como concluída**, com confirmação. Se a atividade exige validação, vai para *Aguardando validação*; senão, para *Concluída*. | M |
| EXE-05 | O empreendedor desfaz a marcação enquanto ela aguarda validação. | S |
| EXE-06 | **O dono da trilha valida ou devolve.** A devolução exige comentário, que o empreendedor vê; ele pode marcar de novo. | M |
| EXE-07 | O dono reabre uma atividade concluída, informando o motivo. Ela volta a *Pendente*. | S |
| EXE-08 | **Histórico** de cada execução (marcada, desfeita, validada, devolvida, reaberta), com autor, data e comentário. Nunca é apagado. | M |
| EXE-09 | **Progresso** da inscrição = atividades obrigatórias concluídas ÷ obrigatórias. *Aguardando validação* ainda não conta. Atividades arquivadas saem do cálculo e continuam no histórico. | M |
| EXE-10 | **Minhas atividades** (empreendedor): lista de todas as execuções, com filtros Pendentes, Devolvidas, Concluídas e Atrasadas, ordenada por prazo. | M |
| EXE-11 | **Fila de validação** do dono (professor ou IS): execuções aguardando validação nas suas trilhas, da mais antiga para a mais nova. | M |

**Transições:**

| Ação | Quem | De | Para | Condição |
|---|---|---|---|---|
| Marcar | Empreendedor | Pendente, Devolvida | Aguardando validação (ou Concluída) | Inscrição ativa |
| Desfazer | Empreendedor | Aguardando validação | Pendente | — |
| Validar | Dono da trilha | Aguardando validação | Concluída | — |
| Devolver | Dono da trilha | Aguardando validação | Devolvida | Comentário obrigatório |
| Reabrir | Dono da trilha | Concluída | Pendente | Motivo obrigatório |

### F6 · Visão do professor

| ID | Requisito | Prior. |
|---|---|---|
| PRO-01 | **Painel do professor:** os empreendimentos que ele atende e, para cada um, as trilhas em que está inscrito, com status (progresso, aguardando validação, atrasadas). | M |
| PRO-02 | **Situação do empreendimento**, derivada das atividades: *Sem atividades*, *Em dia*, *Atenção* (atividade atrasada ou devolvida há mais de 7 dias) e *Concluído*. Painel ordenado com *Atenção* primeiro. [ASSUMIDO o prazo de 7 dias] | M |
| PRO-03 | O professor continua vendo o empreendimento depois que a inscrição na trilha dele é concluída ou cancelada (somente leitura). | M |

### F7 · Prontuário

| ID | Requisito | Prior. |
|---|---|---|
| PRN-01 | Cada empreendimento tem um prontuário: uma lista de **notas** (texto, autor, data), da mais recente para a mais antiga. | M |
| PRN-02 | Escrevem: a IS e os professores que atendem o empreendimento. | M |
| PRN-03 | Veem: a IS, os professores que atendem o empreendimento e o próprio empreendedor. | M |
| PRN-04 | Notas não são editadas nem apagadas; só acrescentadas. [ASSUMIDO] | M |

### F8 · Níveis por eixo

| ID | Requisito | Prior. |
|---|---|---|
| EIX-01 | Os 5 eixos são fixos: Empreendedor, Tecnológico, Mercado, Gestão e Capital. | M |
| EIX-02 | Cada empreendimento tem um **nível atual** (N1, N2 ou N3) em cada eixo, como um "status de RPG". Sem histórico no MVP. | M |
| EIX-03 | Só a IS define e altera os níveis, manualmente. | M |
| EIX-04 | O empreendedor e os professores que atendem o empreendimento veem os níveis (somente leitura). | M |
| EIX-05 | Nível de um empreendimento novo: vazio ("não avaliado") até a IS definir. [ASSUMIDO] | M |

### F9 · Estatísticas da IS

| ID | Requisito | Prior. |
|---|---|---|
| EST-01 | Painel da IS com: **contas** por papel e status; **empreendimentos** ativos e por etapa; **inscrições** por trilha; **atividades** por status, atrasadas e taxa geral de conclusão; **fila de validação** (quantidade e idade da mais antiga). | M |
| EST-02 | Quadro por professor: trilhas, empreendimentos atendidos, atividades aguardando validação. | S |
| EST-03 | Gráficos. | C |

---

## 6. Permissões

| Recurso | Ação | Empreendedor | Professor | IS | Admin |
|---|---|---|---|---|---|
| Contas | criar, editar, desativar, redefinir senha | — | — | professor e empreendedor | todas |
| Minha conta | alterar a própria senha | ✔ | ✔ | ✔ | ✔ |
| Empreendimentos | ver perfil | o próprio | os que atende | todos | — |
| Empreendimentos | criar, junto com o empreendedor | — | — | ✔ | ✔ |
| Empreendimentos | editar, desativar | — | — | ✔ | — |
| Trilhas de etapa | criar, editar, publicar, arquivar | — | — | ✔ | — |
| Trilhas de etapa | ver | as inscritas (atual e anteriores) | ✔ | ✔ | — |
| Trilhas personalizadas | criar, editar, publicar, arquivar | — | as suas | as suas | — |
| Trilhas personalizadas de professores | editar, publicar, arquivar | — | — | ✔ (com confirmação) | — |
| Trilhas personalizadas | ver | as inscritas | as suas + as outras nos empreendimentos que atende | todas | — |
| Inscrição | criar, pausar, reativar, cancelar, avançar etapa | — | — | ✔ | — |
| Inscrição | ver | as próprias | dos empreendimentos que atende | todas | — |
| Atividade | marcar, desfazer | ✔ (as próprias) | — | — | — |
| Atividade | validar, devolver, reabrir | — | nas suas trilhas | nas trilhas de etapa e nas suas personalizadas | — |
| Prontuário | escrever | — | dos que atende | ✔ | — |
| Prontuário | ler | o próprio | dos que atende | todos | — |
| Nível por eixo | definir | — | — | ✔ | — |
| Nível por eixo | ver | o próprio | dos que atende | todos | — |
| Estatísticas | ver | — | — | ✔ | — |

Qualquer acesso fora desta tabela, por lista, busca ou endereço direto, é negado (403) e nenhum dado é exibido.

---

## 7. Regras de negócio

| ID | Regra |
|---|---|
| RN-01 | Um usuário tem um único papel. O empreendedor é representante de exatamente um empreendimento; os demais papéis não têm vínculo com empreendimento. |
| RN-02 | Um empreendimento tem um único representante. |
| RN-03 | O professor se relaciona com um empreendimento **apenas por meio das trilhas dele**: atende quem está ou esteve inscrito nelas. Não há supervisão nem orientador fixo. |
| RN-04 | Quem valida é sempre o **dono da trilha**: a IS nas trilhas de etapa e nas personalizadas que criou, o professor nas dele. |
| RN-05 | A atividade só é marcada pelo empreendedor. Nenhum outro papel marca por ele. |
| RN-06 | Atividade que exige validação só conta como concluída depois de validada. |
| RN-07 | Atividade atrasada = não concluída com prazo vencido (calculado, nunca gravado). |
| RN-08 | Há exatamente uma trilha de etapa para cada etapa. |
| RN-09 | O empreendimento está em uma única etapa por vez. |
| RN-10 | Atividade com progresso e trilha com progresso são arquivadas, nunca apagadas. |
| RN-11 | Inscrições, execuções, histórico e prontuário nunca são apagados. |
| RN-12 | O nível por eixo só é alterado pela IS. |
| RN-13 | Conta desativada não entra e perde as sessões ativas. |
| RN-14 | Toda rota exige login, salvo a lista fechada da seção 4. |
| RN-15 | Dados fictícios nunca vão para produção. |
| RN-16 | O admin não acessa dados de negócio, exceto para informar os dados do empreendimento ao criar um empreendedor. |

---

## 8. Modelo de dados (MVP)

Substitui o `MODELAGEM_BANCO.md` para o escopo do MVP. Campos de auditoria (`criado_por`, `atualizado_por` etc.) ficam fora por enquanto.

| Entidade | Campos principais | Observações |
|---|---|---|
| **Usuário** | nome, e-mail (único, minúsculas), senha (hash), papel, ativo, deve_trocar_senha, último acesso, criado_em | Papéis: `admin`, `is`, `professor`, `empreendedor` |
| **Empreendimento** | nome, tipo, descrição, e-mail e telefone de contato, representante → Usuário, desativado_em | Nulo em `desativado_em` = ativo |
| **Trilha** | título, descrição, etapa (vazio, `pre_incubacao`, `incubacao`, `desincubacao`), dono → Usuário, status, publicada_em, arquivada_em | Etapa vazia = trilha personalizada. No máximo uma trilha não arquivada por etapa |
| **Atividade da trilha** | trilha, título, descrição, tipo, endereço, ordem, obrigatória, exige_validacao, prazo_fixo, dias_apos_inscricao, criada_em, arquivada_em | Um dos dois prazos, ou nenhum |
| **Inscrição** | empreendimento, trilha, status, inscrito_por (vazio = automática), inscrito_em, pausado_em, reativado_em, cancelado_em, concluido_em, motivo | Única por par entre as ativas e pausadas |
| **Execução da atividade** | inscrição, atividade, status, prazo, concluida_em, atualizada_em | Única por par inscrição–atividade |
| **Histórico da atividade** | execução, ação, autor, comentário, criado_em | Só inserção |
| **Nota do prontuário** | empreendimento, autor, texto, criado_em | Só inserção |
| **Nível por eixo** | empreendimento, eixo, nível | Único por par empreendimento–eixo. Eixo é uma lista fixa |

**Relacionamentos:**
```text
USUARIO 1 ─── 0..1 EMPREENDIMENTO            (representante)
USUARIO 1 ─── N TRILHA                       (dono)
TRILHA 1 ─── N ATIVIDADE_TRILHA
EMPREENDIMENTO 1 ─── N INSCRICAO N ─── 1 TRILHA
INSCRICAO 1 ─── N EXECUCAO_ATIVIDADE N ─── 1 ATIVIDADE_TRILHA
EXECUCAO_ATIVIDADE 1 ─── N HISTORICO_ATIVIDADE
EMPREENDIMENTO 1 ─── N NOTA_PRONTUARIO
EMPREENDIMENTO 1 ─── 5 NIVEL_EIXO
```

---

## 9. Jornadas e critérios de aceite

Cada jornada é um teste de ponta a ponta.

**J-1 · Contas**
> *Dado* a IS, *quando* cria um empreendedor com os dados do empreendimento, *então* os dois são criados e o empreendimento entra na trilha de pré-incubação. *Quando* o empreendedor entra pela primeira vez, *então* precisa trocar a senha antes de usar o sistema. *Dado* a IS, *quando* tenta criar uma conta IS ou admin, *então* o sistema recusa.

**J-2 · Nada sem login**
> *Dado* um visitante sem sessão, *quando* abre qualquer endereço fora das exceções, *então* vai ao login e nada é exibido. *Dado* um usuário de um papel, *quando* tenta abrir a área de outro, *então* o acesso é negado.

**J-3 · Etapas**
> *Dado* um empreendimento na pré-incubação, *quando* a IS avança a etapa, *então* a inscrição na pré-incubação fica *Concluída*, ele é inscrito na trilha de incubação, e não fica em duas etapas ao mesmo tempo.

**J-4 · Trilha personalizada e inscrição**
> *Dado* uma trilha personalizada publicada, *quando* a IS inscreve o empreendimento A, *então* ela aparece para A com todas as atividades pendentes e **não** aparece para B. *Dado* uma trilha em rascunho, *então* nenhum empreendimento a vê e a IS não consegue inscrever ninguém nela.

**J-5 · Execução e validação**
> *Dado* uma atividade que exige validação, *quando* o empreendedor a marca, *então* ela fica *Aguardando validação* e o progresso não muda. *Quando* o dono a devolve sem comentário, *então* o sistema recusa; com comentário, o empreendedor o vê. *Quando* o dono a valida, *então* ela vira *Concluída*, o progresso é recalculado e o histórico mostra as três ações. *Dado* um professor que não é dono da trilha, *quando* tenta validar uma atividade dela, *então* o acesso é negado.

**J-6 · O professor acompanha**
> *Dado* um professor com dois empreendimentos inscritos nas suas trilhas, *quando* abre o painel, *então* vê cada um com suas trilhas e status, e o que tem atividade atrasada aparece primeiro como *Atenção*. *Quando* a inscrição de um deles é concluída, *então* ele continua aparecendo, em leitura.

**J-7 · Prontuário e níveis**
> *Dado* um empreendimento, *quando* um professor que o atende escreve uma nota, *então* a IS, o empreendedor e os outros professores que o atendem a veem, e um professor que não o atende não vê. *Quando* a IS altera um nível por eixo, *então* o empreendedor vê o novo nível; nenhum outro papel consegue alterá-lo.

**J-8 · Gestão de contas**
> *Dado* um usuário com sessão aberta, *quando* a IS (ou o admin) o desativa, *então* a sessão é encerrada e ele não entra mais. Ninguém desativa a última conta ativa de admin.

---

## 10. Telas

| Área | Telas |
|---|---|
| **Todos** | Login (com a orientação de "esqueci a senha") · Troca de senha obrigatória · Minha conta · Erros 403 e 404 |
| **Empreendedor** | Início (próximas atividades e devoluções) · Meu empreendimento (perfil) · Minhas trilhas · Detalhe da trilha · Minhas atividades |
| **Professor** | Painel (empreendimentos × trilhas × status) · Fila de validação · Perfil do empreendimento · Minhas trilhas · Editor de trilha |
| **IS** | Estatísticas · Contas · Empreendimentos (lista e cadastro) · Perfil do empreendimento (inscrições, níveis, prontuário) · Avançar etapa · Trilhas de etapa (editor) · Todas as trilhas e inscrição · Fila de validação |
| **Admin** | Contas (todas) |

---

## 11. Requisitos não funcionais

| ID | Requisito | Prior. |
|---|---|---|
| RNF-01 | **Segurança:** HTTPS, senhas com hash forte, cookies seguros, proteção CSRF, `DEBUG` desligado em produção, segredos só em variáveis de ambiente. | M |
| RNF-02 | **Isolamento testado automaticamente:** empreendimento A não vê B; professor só vê quem atende; só o dono valida. | M |
| RNF-03 | **Testes:** toda regra RN e toda jornada J com teste automatizado; teste "toda rota exige login" na CI. | M |
| RNF-04 | **Mobile:** telas do empreendedor utilizáveis em celular. | M |
| RNF-05 | **Acessibilidade:** contraste, navegação por teclado, status que não dependem só de cor. | M |
| RNF-06 | **Desempenho:** telas principais em até 3 s; listas paginadas. | M |
| RNF-07 | **Idioma:** pt-BR. | M |
| RNF-08 | **Hospedagem:** serviços gratuitos (Render: web e Postgres free) enquanto o projeto não tiver piloto com dados reais. | M |

**Antes de um piloto com dados reais** (fora do MVP acadêmico): banco com backup e restauração testada (o Postgres gratuito do Render expira em 30 dias e não tem backup), termo de privacidade e avaliação de LGPD da hospedagem, e o bloqueio de tentativas de login (ACE-14).

---

## 12. Fora do MVP

### Adiado (pode voltar)
- **Acompanhamentos da IS:** registro de reuniões e ações com o empreendimento. Quando voltar, **não deve depender de trilha**.
- **Agendamento:** o empreendedor escolhe data e horário de um encontro.
- **Upload de evidências** nas atividades. [Confirmar com a IS se o MVP pode sair sem]
- **Auditoria** completa (quem alterou o quê, campos `*_por`).
- **Recuperação de senha por e-mail** e **convites** por e-mail.
- **Histórico dos níveis por eixo.**
- **Mais de um representante** por empreendimento.
- Etapas dentro da trilha; notificações; exportação de relatórios.

### Descartado (decisão da reunião ou da equipe)
- **Diagnóstico por questionário** (eixos × competências × perguntas): os níveis por eixo são definidos manualmente pela IS.
- **Demandas** e **Nexus** (demanda × oferta, pactuação).
- **Professor como projeto ou disciplina** (origem da oferta).
- **Ciclo, semestres e participação no ciclo:** a etapa atual vem da inscrição na trilha de etapa.
- **Supervisão** (professor fixo por empreendimento): o professor atua só pelas trilhas.
- **Hub** como entidade: é a própria IS.
- **Incubação 1 e 2** como etapas separadas: é uma só etapa de incubação.

---

## 13. Pendências a confirmar

| # | Pergunta | Proposta |
|---|---|---|
| 1 | Nome da última etapa | "Desincubação" (nome usado no protótipo da IS) |
| 2 | O que acontece ao avançar a partir da Desincubação | **Decidido** (F4, 7.1): encerra a incubação; a inscrição fica *Concluída* e o empreendimento fica sem etapa ativa |
| 3 | O MVP pode sair sem upload de evidências? | Sim; entregas são descritas na atividade e conferidas pelo dono |
| 4 | Notas do prontuário podem ser editadas ou apagadas? | Não; só acrescentadas |
| 5 | Nível inicial de um empreendimento novo | Vazio ("não avaliado") |
| 6 | Prazo para a situação *Atenção* | Atividade devolvida há mais de 7 dias |
| 7 | Desativar empreendimento tira o acesso do representante? | **Decidido** (F2, 7.4): sim, enquanto estiver desativado; a conta do representante continua ativa |

---

## 14. Mudanças em relação à v0.3

- **Validação:** sempre pelo dono da trilha (antes: professor supervisor na trilha base, com a IS como exceção).
- **Trilha base por ciclo → trilha por etapa**, três etapas, sem tabela de ciclo; a etapa atual vem da inscrição; nova tela "avançar etapa".
- **Inscrição** ganha o status *Concluída*.
- **Sem convites:** a IS cria as contas com senha inicial e troca obrigatória no primeiro acesso; "esqueci a senha" é resolvido pela IS.
- **Sem supervisão:** a relação professor–empreendimento vem das trilhas.
- **Prontuário** simplificado para notas, visíveis também ao empreendedor, e entra no MVP (antes: opcional).
- **Níveis por eixo** entram no MVP, só com o nível atual (antes: opcional, com histórico).
- **Acompanhamentos** saem do MVP.
- **Papel "empreendimento" renomeado para "empreendedor"**, e o vínculo para "representante".
- Atividade ganha o campo **endereço** (para o tipo Link); senha mínima de **10 caracteres** passa a valer no código.
- Cronograma e capacidade da v0.3 foram retirados: serão definidos pela equipe a partir das issues.

---

## 15. Histórico

| Versão | Data | Mudança |
|---|---|---|
| 0.1 | 2026-09-30 | MVP amplo: diagnóstico, demandas, Nexus, jornadas. |
| 0.2 | 2026-10-07 | MVP-0: 3 papéis, atividades, acompanhamentos, estatísticas; "nada sem login"; 8 semanas. |
| 0.3 | 2026-10-10 | Decisões da reunião: 4 papéis, trilha base e personalizadas, inscrição pela IS, validação pelo professor. |
| 0.4 | 2026-10-23 | Revisão da equipe após a reunião com a IS (ver seção 14). |
| 0.4.1 | 2026-10-23 | A IS também cria trilhas personalizadas e pode editar as dos professores; "trilha de professor" passa a se chamar "trilha personalizada" (decisões da `F3-trilhas/spec.md`). |
| 0.4.2 | 2026-10-28 | Decisões das specs F2 e F4: INS-11 (avançar a partir da Desincubação encerra a incubação) e EMP-06 (representante perde o acesso enquanto o empreendimento estiver desativado); pendências 2 e 7 da seção 13 fechadas. |
| 0.4.3 | 2026-11-04 | Decisão da spec F4 (7.7): a inscrição guarda a data de reativação (`reativado_em`, seção 8). |
| 0.4.4 | 2026-11-04 | Decisão da spec F0 (7.6): todos os arquivos estáticos são públicos (ACE-00a). |
| 0.4.5 | 2026-11-04 | Decisão da spec F1 (7.8): o admin informa os dados do empreendimento ao criar um empreendedor (RN-16 e tabela de permissões). |
