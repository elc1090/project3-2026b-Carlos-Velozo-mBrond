> ⚠️ **Documento arquivado — não usar para implementar.** Substituído por [`SGIS_SPEC_MVP_v0.4.md`](../SGIS_SPEC_MVP_v0.4.md). Mantido apenas como registro histórico. Ver [`README.md`](README.md).

# SGIS — Especificação do MVP

**Versão:** 0.3 (rascunho para validação) 

**Convenções:** `MVP-XXX-NN` = requisito do MVP · `Prior.`: **M** obrigatório, **S** desejável, **C** só se sobrar tempo, **Opc** opcional do MVP (entra apenas se o cronograma permitir) · `[ASSUMIDO]` = inferido, precisa de confirmação · `Spec` = requisito equivalente na spec completa.

---

## 1. Objetivo e hipótese

**Objetivo:** colocar em produção, em 8 semanas, um sistema fechado em que a Incubadora Social (IS) organiza o ciclo e define as trilhas, os professores criam trilhas personalizadas e validam o que os empreendedores concluem, e os empreendimentos percorrem as trilhas em que foram inscritos.

**Hipótese a validar:** *se a IS, os professores e os empreendimentos conduzirem o dia a dia das trilhas dentro de um único sistema, abandonam mensagens e planilhas soltas, e isso justifica construir as camadas seguintes (agendamento, prontuário completo, diagnóstico, evidências).*

**Papéis (reunião, R-01):**

| Papel | No MVP |
|---|---|
| **Empreendimento** | Vê as trilhas em que a IS o inscreveu, marca atividades como concluídas, vê devoluções do professor e os acompanhamentos da IS. |
| **Professor** | Cria trilhas personalizadas, valida ou devolve atividades, vê os empreendimentos que supervisiona, as trilhas em que estão inscritos e o status em cada. |
| **IS** | Define o ciclo e a trilha base, decide em quais trilhas cada empreendimento entra, cadastra empreendimentos e supervisões, convida professores e empreendimentos, registra acompanhamentos e níveis por eixo, vê estatísticas gerais. |
| **Admin** | Gerencia contas de todos os papéis, inclusive IS e admin. Não acessa dados de negócio. [ASSUMIDO, Q-28] |

---

## 2. Regra transversal: nada disponível sem login (R-02)

Vale para **todas** as features e tem prioridade sobre qualquer outro requisito.

| ID | Requisito | Prior. |
|---|---|---|
| MVP-ACE-00 | Todo endereço do sistema exige usuário autenticado. Anônimos são redirecionados ao login, **inclusive** ao tentar endereços que não existem (o sistema não revela o que existe). | M |
| MVP-ACE-00a | **Lista fechada de exceções públicas:** (1) tela de login; (2) solicitação e redefinição de senha; (3) aceite de convite; (4) verificação de saúde do serviço, que responde só "ok", sem dados; (5) `robots.txt` bloqueando indexação; (6) arquivos visuais estritamente necessários às telas anteriores. | M |
| MVP-ACE-00b | Não existe cadastro público, página institucional, listagem pública, API pública nem documentação de API acessível a anônimos. | M |
| MVP-ACE-00c | Páginas autenticadas não são indexáveis por buscadores. | M |
| MVP-ACE-00d | Toda rota nova nasce protegida. Torná-la pública exige marcação explícita, revisada em code review. | M |

> **Por que existem exceções:** convite e redefinição de senha são abertos por quem ainda não tem senha, e a hospedagem precisa saber se o serviço está vivo. Nenhum deles exibe dado do sistema.

**Aceite MVP-ACE-00:** *Dado* um visitante sem sessão, *quando* abre qualquer endereço fora da lista de exceções (existente ou não), *então* vai ao login e nenhum dado, nome de tela ou mensagem de "não encontrado" é exibido.
**Aceite MVP-ACE-00a:** *Dado* um teste que percorre todas as rotas registradas sem sessão, *então* só as 6 exceções respondem sem redirecionar ao login.

---

## 3. Escopo

### 3.1 Dentro do MVP

| Feature | Conteúdo | Prioridade |
|---|---|---|
| **F1 · Acesso** | Login, 4 papéis, convites, recuperação de senha, gestão de contas, isolamento de dados | M |
| **F2 · Empreendimentos e ciclo** | Cadastro pela IS, representantes, supervisão, ciclo definido pela IS | M |
| **F3 · Trilhas** | Trilha base (IS) e trilhas personalizadas (professor), com atividades | M |
| **F4 · Inscrição** | A IS decide em quais trilhas cada empreendimento entra | M |
| **F5 · Execução e validação** | Empreendedor marca, professor valida ou devolve | M |
| **F6 · Visão do professor e acompanhamentos** | Empreendimentos × trilhas × status; acompanhamentos da IS | M |
| **F7 · Estatísticas** | Painel geral da IS | M |
| **F8 · Opcionais** | Nível por eixo (IS) e prontuário mínimo | Opc |
| **F9 · Endurecimento e piloto** | Segurança, acessibilidade, LGPD, backups, dados reais | M |

### 3.2 Fora do MVP

**Agendamento** (R-09, a refinar) · etapas dentro da trilha · upload de evidências · diagnóstico por questionário · Nexus como fluxo de pactuação · agenda e encontros · notificações de prazo · gráficos avançados · exportação de relatórios · SSO · múltiplos perfis por usuário · autocadastro · aplicativo nativo.

**Substituto provisório do agendamento:** atividade do tipo **Tarefa** com instrução textual ("combine o horário com o professor pelo canal X"). O tipo `scheduling` fica reservado no modelo de dados.

---

## 4. Permissões (estado inicial)

Vão mudar durante o desenvolvimento. Ficam em um único lugar do código (`plan.md`, seção 5).

| Recurso | Ação | Empreendimento | Professor | IS | Admin |
|---|---|---|---|---|---|
| Contas | listar, convidar, desativar, reativar | — | — | professor e empreendimento | todas |
| Minha conta | alterar a própria senha | ✔ | ✔ | ✔ | ✔ |
| Ciclo | criar, editar, avançar semestre | — | — | ✔ | — |
| Empreendimentos | ver | o próprio | supervisionados | todos | — |
| Empreendimentos | criar, editar, desativar, definir supervisão | — | — | ✔ | — |
| Trilha base | criar, editar, publicar | — | — | ✔ | — |
| Trilhas personalizadas | criar, editar, publicar | — | as suas | ver todas | — |
| Trilhas | ver | as inscritas | as suas + demais [Q-24] | todas | — |
| Inscrição | criar, pausar, cancelar | — | — | ✔ | — |
| Inscrição | ver | as próprias | dos supervisionados | todas | — |
| Atividade | marcar como concluída / desfazer | ✔ (as próprias) | — | — | — |
| Atividade | validar, devolver, reabrir | — | ✔ (regra MVP-VAL-01) | ✔ (exceção registrada) | — |
| Acompanhamentos | criar, editar, excluir | — | — | ✔ | — |
| Acompanhamentos | ver | os próprios | — | todos | — |
| Nível por eixo | definir | — | — | ✔ | — |
| Nível por eixo | ver | o próprio | supervisionados | todos | — |
| Prontuário (Opc) | ler e escrever | só liberados [Q-25] | supervisionados | todos | — |
| Estatísticas gerais | ver | — | — | ✔ | — |

---

## 5. Requisitos funcionais

### F1 · Acesso (semanas 1–2)

| ID | Requisito | Prior. | Spec |
|---|---|---|---|
| MVP-ACE-01 | Login com e-mail e senha. Erro genérico ("e-mail ou senha incorretos"). | M | RF-ACE-01 |
| MVP-ACE-02 | Após o login, o usuário vai para a área do seu papel. | M | RF-ACE-02 |
| MVP-ACE-03 | Logout e expiração de sessão por inatividade. | M | — |
| MVP-ACE-04 | Recuperação de senha por e-mail, com resposta idêntica exista ou não a conta. | M | RF-ACE-04 |
| MVP-ACE-05 | Usuários só entram por **convite**. A IS convida professores e usuários de empreendimento; o admin convida qualquer papel. Quem recebe define nome e senha pelo link. [Confirmar convite × autocadastro com aprovação] | M | RF-ACE-05, RF-ACE-10 |
| MVP-ACE-06 | **Gestão de contas:** lista com nome, e-mail, papel, vínculo, status (convite pendente, convite expirado, ativo, desativado), criação e último acesso; filtros; convidar, reenviar, revogar, desativar, reativar. | M | RF-ACE-09 |
| MVP-ACE-07 | **Monitorar novos usuários:** destaque para criados nos últimos 7 dias, convites pendentes e expirados. | M | — |
| MVP-ACE-08 | Bloqueio temporário após tentativas de login malsucedidas repetidas. | M | RNF-02 |
| MVP-ACE-09 | Isolamento: cada papel só acessa o que a seção 4 permite; dados de outro escopo não aparecem por lista, busca ou endereço direto. | M | RF-ACE-06 |
| MVP-ACE-10 | O usuário altera a própria senha estando logado. | S | — |
| MVP-ACE-11 | Desativar uma conta encerra suas sessões imediatamente. | M | — |
| MVP-ACE-12 | Ninguém desativa a si mesmo, nem a última conta ativa de admin. | M | — |
| MVP-ACE-13 | A primeira conta de admin é criada na implantação por comando, com troca de senha obrigatória no primeiro acesso. | M | — |

### F2 · Empreendimentos e ciclo (semana 3)

| ID | Requisito | Prior. | Spec |
|---|---|---|---|
| MVP-EMP-01 | A IS cadastra e edita empreendimento: nome, tipo (MEI, Associação, Coletivo, outro), descrição, contato. | M | RF-EMP-01 |
| MVP-EMP-02 | A IS convida representantes vinculados ao empreendimento. | M | RF-EMP-02 |
| MVP-EMP-03 | A IS vincula e desvincula professores (supervisão). Um empreendimento pode ter mais de um professor. [Confirmar] | M | — |
| MVP-EMP-04 | A IS lista empreendimentos com filtros (ativos, sem professor). | M | RF-EMP-05 |
| MVP-EMP-05 | O professor lista **apenas** os empreendimentos que supervisiona. | M | — |
| MVP-EMP-06 | O representante vê os dados do próprio empreendimento (leitura). | M | — |
| MVP-EMP-07 | A IS desativa um empreendimento sem apagar histórico; representantes não conseguem entrar. [Confirmar] | S | — |
| MVP-CIC-01 | A IS define o **ciclo** (nome, datas, 4 semestres). No MVP existe um ciclo ativo. | M | RF-TRL-02 |
| MVP-CIC-02 | A IS inclui empreendimentos no ciclo e avança o semestre de cada um, com registro de data e autor. | M | RF-EMP-03, RF-EMP-04 |

### F3 · Trilhas (semana 4)

| ID | Requisito | Prior. | Spec |
|---|---|---|---|
| MVP-TRL-01 | A IS cria a **trilha base** do ciclo: título, descrição e atividades. Uma trilha base publicada por ciclo. | M | RF-TRL-01 |
| MVP-TRL-02 | O professor cria **trilhas personalizadas**: título, descrição e atividades. | M | RF-TRL-03 |
| MVP-TRL-03 | Atividade: título, descrição, tipo (**Leitura, Link, Tarefa**), obrigatória (sim/não), exige validação (padrão **sim**), prazo fixo ou em dias a partir da inscrição. | M | RF-TRL-04 |
| MVP-TRL-04 | Estados: rascunho, publicada, arquivada. Publicar exige ao menos uma atividade. Rascunho é invisível para empreendimentos. | M | RF-TRL-05 |
| MVP-TRL-05 | Editar trilha publicada: ajustar textos e acrescentar atividades ao final. Atividade com progresso só pode ser arquivada. Trilha com progresso nunca é apagada. | M | RF-TRL-06 |
| MVP-TRL-06 | Reordenar atividades. | S | RF-TRL-08 |
| MVP-TRL-07 | Duplicar trilha. | C | RF-TRL-08 |
| MVP-TRL-08 | A IS vê todas as trilhas; o professor vê e edita as suas e lê a trilha base. | M | — |

### F4 · Inscrição (semana 5)

| ID | Requisito | Prior. | Spec |
|---|---|---|---|
| MVP-INS-01 | A **IS decide** em quais trilhas cada empreendimento entra, inscrevendo-o em uma trilha publicada. | M | RF-INS-01 |
| MVP-INS-02 | Todo empreendimento incluído no ciclo é inscrito automaticamente na trilha base. [ASSUMIDO] | M | RF-INS-03 |
| MVP-INS-03 | O empreendimento vê apenas as trilhas em que está inscrito. | M | RF-INS-05 |
| MVP-INS-04 | A IS pausa ou cancela uma inscrição; o histórico fica preservado. | S | RF-INS-04 |
| MVP-INS-05 | Inscrição de vários empreendimentos de uma vez. | S | RF-INS-02 |

### F5 · Execução e validação (semanas 5–6)

| ID | Requisito | Prior. | Spec |
|---|---|---|---|
| MVP-EXE-01 | O empreendimento vê suas trilhas com progresso e, em cada uma, as atividades com status (Pendente, Aguardando validação, Devolvida, Concluída) e prazo. | M | RF-TRI-02, RF-TRI-05 |
| MVP-EXE-02 | **Minhas atividades:** lista consolidada com filtros Pendentes, Devolvidas, Concluídas e Atrasadas, por prazo. | M | RF-TRI-03 |
| MVP-EXE-03 | O empreendedor **marca como concluída**, com confirmação. Se exige validação, passa a *Aguardando validação*; senão, conclui. | M | RF-VAL-01, RF-VAL-09 |
| MVP-EXE-04 | O empreendedor desfaz a marcação enquanto aguarda validação. | S | RF-VAL-04 |
| MVP-EXE-05 | Atividade devolvida mostra o comentário do professor e pode ser marcada de novo. | M | RF-VAL-03 |
| MVP-EXE-06 | Progresso da inscrição = atividades obrigatórias **concluídas** ÷ obrigatórias. Aguardando validação ainda não conta. | M | RN-19 |
| MVP-VAL-01 | **Quem valida:** na trilha personalizada, o professor dono; na trilha base, qualquer professor com supervisão ativa sobre o empreendimento. A IS valida como exceção, com registro. [Q-22] | M | RF-VAL-06 |
| MVP-VAL-02 | O professor **valida** ou **devolve**; a devolução exige comentário. | M | RF-VAL-02 |
| MVP-VAL-03 | **Fila de validação** do professor, da mais antiga para a mais nova. | M | RF-VAL-07 |
| MVP-VAL-04 | Histórico de cada atividade (marcações, validações, devoluções) com autor, data e comentário. | M | RF-VAL-08 |
| MVP-VAL-05 | O validador reabre uma atividade concluída, com motivo. | S | RF-VAL-05 |

### F6 · Visão do professor e acompanhamentos (semana 6)

| ID | Requisito | Prior. | Spec |
|---|---|---|---|
| MVP-PRO-01 | **Painel do professor:** empreendimentos que supervisiona e, para cada um, **as trilhas em que está inscrito e o status em cada** (progresso, aguardando validação, atrasadas). | M | RF-ACO-10 |
| MVP-PRO-02 | **Situação do empreendimento**, derivada das atividades: *Sem atividades*, *Em dia*, *Atenção* (há atividade atrasada ou devolvida há mais de 7 dias [ASSUMIDO]), *Concluído*. Painel ordenado com *Atenção* primeiro. | M | RN-07 |
| MVP-PRO-03 | O professor vê também as trilhas de outros donos do empreendimento, somente leitura. [Q-24] | S | RF-ACO-11 |
| MVP-ACP-01 | A IS cria **acompanhamento** para um empreendimento: título, descrição, data da reunião. | M | RF-ACO-04 |
| MVP-ACP-02 | A IS edita e exclui acompanhamentos (exclusão lógica). | M | — |
| MVP-ACP-03 | O empreendimento vê seus acompanhamentos, mais recentes primeiro (leitura). | M | — |
| MVP-ACP-04 | A IS vê os acompanhamentos de cada empreendimento em ordem cronológica. | M | RF-ACO-05 |

### F7 · Estatísticas (semana 6–7)

| ID | Requisito | Prior. | Spec |
|---|---|---|---|
| MVP-EST-01 | Painel da IS: **contas** por papel e status, novos nos últimos 30 dias, convites pendentes e expirados; **empreendimentos** ativos e sem professor; **inscrições** por trilha; **atividades** por status, atrasadas e taxa geral de conclusão; **fila de validação** (quantidade e idade da mais antiga). | M | RF-IND-01 |
| MVP-EST-02 | Quadro por professor: empreendimentos, trilhas criadas, atividades aguardando validação e tempo médio de resposta. | S | — |
| MVP-EST-03 | Gráficos. | C | RF-IND-01 |

### F8 · Opcionais (só se o cronograma permitir)

| ID | Requisito | Prior. | Spec |
|---|---|---|---|
| MVP-EIX-01 | A IS registra o **nível por eixo** (5 eixos) de cada empreendimento, com data, observação e acompanhamento de origem. Histórico preservado; nível atual = último. | Opc | RF-EIX-02, 03 |
| MVP-EIX-02 | O empreendimento e o professor supervisor veem nível atual e evolução (leitura). | Opc | RF-EIX-04 |
| MVP-PRN-01 | **Prontuário mínimo:** por empreendimento, registros de texto (tipo: demanda, problema, observação, encaminhamento; status: aberto, resolvido), escritos por professores supervisores e pela IS, visíveis a todos os supervisores e à IS. O histórico fica com o empreendimento quando o professor muda. | Opc | RF-PRN-01 a 05 |
| MVP-PRN-02 | Registros não visíveis ao empreendimento por padrão. [Q-25] | Opc | RF-PRN-08 |

### F9 · Endurecimento e piloto (semanas 7–8)

Ver seções 9, 11 e 12.

---

## 6. Regras de negócio

| ID | Regra |
|---|---|
| RN-MVP-01 | Um usuário tem **um único papel**. Empreendimento exige vínculo com um empreendimento; os demais papéis não têm vínculo de empreendimento. |
| RN-MVP-02 | Professor só enxerga e gerencia dados de empreendimentos que supervisiona **no momento**. Encerrar a supervisão remove o acesso; o histórico permanece. |
| RN-MVP-03 | Empreendimento só enxerga dados do próprio empreendimento e das trilhas em que está inscrito. |
| RN-MVP-04 | Atividade **atrasada** = não concluída com prazo vencido (calculado, sem gravar status). |
| RN-MVP-05 | Convite vale 7 dias, é de uso único e pode ser reenviado (o anterior é revogado). |
| RN-MVP-06 | Conta desativada não entra e perde as sessões ativas. |
| RN-MVP-07 | Nenhuma exclusão apaga histórico de forma irrecuperável (exclusão lógica, com autor e data). |
| RN-MVP-08 | Toda criação e alteração de trilha, atividade, inscrição, supervisão, acompanhamento e conta registra autor e data. |
| RN-MVP-09 | Toda rota exige login, salvo a lista fechada (MVP-ACE-00a). |
| RN-MVP-10 | Os dados fictícios do protótipo nunca vão para produção. |
| RN-MVP-11 | Há **uma trilha base publicada por ciclo**, de autoria da IS. Trilha personalizada é de autoria de professor. |
| RN-MVP-12 | A atividade só é concluída pelo empreendedor (marcação) e, quando exige validação, pelo professor (validação). Nenhum outro papel marca por ele. |
| RN-MVP-13 | Atividade com progresso e trilha com progresso são arquivadas, nunca apagadas. |
| RN-MVP-14 | O nível por eixo só é alterado pela IS; cada mudança é um novo registro (histórico imutável). |
| RN-MVP-15 | O admin não acessa dados de negócio. [ASSUMIDO, Q-28] |

---

## 7. Jornadas de usuário e critérios de aceite

Cada jornada é um **teste de ponta a ponta**.

**J-1 · Contas e convites**
1. O admin inicial entra e troca a senha.
2. Convida uma pessoa da IS. Ela convida um professor e um representante de empreendimento.
3. Cada convidado define a senha e entra na sua área.

> *Dado* um convite válido, *quando* o convidado define a senha, *então* entra na área do seu papel e o convite não pode ser reutilizado. *Dado* a IS, *quando* tenta convidar outra IS ou um admin, *então* o sistema recusa.

**J-2 · Nada sem login**
> *Dado* um visitante sem sessão, *quando* tenta abrir qualquer endereço fora das 6 exceções, *então* vai ao login e nada é exibido. *Dado* um usuário de um papel, *quando* tenta abrir a área de outro, *então* o acesso é negado.

**J-3 · A IS organiza o ciclo**
1. Define o ciclo, cadastra o empreendimento, convida o representante, vincula o professor.
2. Cria e publica a trilha base.

> *Dado* um professor sem vínculo, *quando* abre sua lista, *então* ela está vazia. *Quando* a IS o vincula, *então* só aquele empreendimento aparece. *Dado* a trilha base publicada, *quando* o empreendimento é incluído no ciclo, *então* é inscrito nela automaticamente.

**J-4 · Trilha personalizada e inscrição**
1. O professor cria uma trilha com 3 atividades e a publica.
2. A IS inscreve o empreendimento A.

> *Dado* uma trilha publicada, *quando* a IS inscreve A, *então* ela aparece para A com todas as atividades pendentes e **não** aparece para B. *Dado* uma trilha em rascunho, *então* nenhum empreendimento a vê.

**J-5 · Execução e validação**
1. O empreendedor marca uma atividade.
2. O professor a devolve com comentário.
3. O empreendedor marca de novo; o professor valida.

> *Dado* uma atividade que exige validação, *quando* o empreendedor a marca, *então* ela fica *Aguardando validação* e o progresso **não** muda. *Quando* o professor a devolve sem comentário, *então* o sistema recusa; com comentário, o empreendedor o vê. *Quando* o professor a valida, *então* ela vira *Concluída*, o progresso é recalculado e o histórico mostra as três ações.
> *Dado* um professor que não é dono da trilha personalizada, *quando* tenta validar uma atividade dela, *então* o acesso é negado.

**J-6 · O professor acompanha**
> *Dado* um professor que supervisiona dois empreendimentos inscritos em trilhas, *quando* abre seu painel, *então* vê cada empreendimento com suas trilhas e status; o que tem atividade atrasada aparece primeiro como *Atenção*.

**J-7 · Acompanhamento e estatísticas**
> *Dado* um empreendimento, *quando* a IS cria um acompanhamento, *então* o representante o vê e nenhum outro empreendimento o vê. *Dado* dados cadastrados, *quando* a IS abre as estatísticas, *então* os números conferem com as listagens.

**J-8 · Gestão de contas**
> *Dado* um usuário com sessão aberta, *quando* a IS (ou o admin) o desativa, *então* a sessão é encerrada e ele não entra mais. Ninguém desativa a última conta ativa de admin.

---

## 8. Telas do MVP

| Área | Telas |
|---|---|
| **Todos** | Login · Esqueci a senha · Redefinir senha · Aceitar convite · Minha conta · Erros 403 e 404 |
| **Empreendimento** | Início (próximas atividades, devoluções, últimos acompanhamentos) · Minhas trilhas · Detalhe da trilha · Minhas atividades · Acompanhamentos · Meu empreendimento |
| **Professor** | Painel (empreendimentos × trilhas × status) · Fila de validação · Detalhe do empreendimento · Minhas trilhas · Editor de trilha |
| **IS** | Painel de estatísticas · Contas · Empreendimentos (lista, cadastro, supervisão) · Ciclo · Trilha base (editor) · Trilhas (lista e inscrição) · Detalhe do empreendimento (inscrições, atividades, acompanhamentos) · Novo acompanhamento |
| **Admin** | Contas (todas) |
| **Opc** | Nível por eixo (IS) · Prontuário do empreendimento |

Aproveitar do protótipo: identidade visual (lateral verde-escura, cartões brancos), menu lateral por papel e linguagem simples. A tela de escolha de perfil **não** existe em produção.

---

## 9. Requisitos não funcionais

| ID | Requisito | Prior. |
|---|---|---|
| RNF-MVP-01 | **Segurança:** HTTPS, senhas com hash forte (mínimo 10 caracteres), OWASP Top 10, cookies seguros, bloqueio de tentativas, isolamento testado automaticamente. | M |
| RNF-MVP-02 | **LGPD:** coleta mínima (nome, e-mail, papel), termo de privacidade no primeiro acesso, definição de quem acessa o quê e de retenção. Avaliar hospedagem fora do Brasil antes do piloto. | M |
| RNF-MVP-03 | **Mobile:** telas do empreendimento utilizáveis em celular. | M |
| RNF-MVP-04 | **Acessibilidade:** contraste, teclado, status que não dependem só de cor (Atrasada tem texto e ícone). | M |
| RNF-MVP-05 | **Desempenho:** telas principais em até 3 s; listas paginadas. | M |
| RNF-MVP-06 | **Backup** automático do banco com restauração testada antes do piloto. | M |
| RNF-MVP-07 | **Testes:** toda regra RN-MVP e todo critério J-1 a J-8 com teste automatizado; teste "toda rota exige login" na CI. | M |
| RNF-MVP-08 | **Observabilidade:** logs de erro e de acessos negados. | S |
| RNF-MVP-09 | **Idioma:** pt-BR, textos externalizados. | M |
| RNF-MVP-10 | **Modelo de dados** conforme `MODELAGEM_BANCO.md`, com migrações aditivas por feature. | M |

---

## 10. Dados iniciais

1. Conta de admin inicial, criada na implantação por comando.
2. Os 5 eixos (carga fixa).
3. Para o piloto, **fornecidos pela IS**: ciclo e semestres, trilha base (atividades), lista de empreendimentos, representantes e professores (nome, e-mail, papel, vínculo).
4. Dados fictícios só em desenvolvimento e demonstração (RN-MVP-10).

---

## 11. Cronograma (8 semanas) e viabilidade

### 11.1 Premissas
- **Capacidade [ASSUMIDO]:** 1 pessoa desenvolvendo, com apoio de assistente de código, em dedicação parcial consistente. As estimativas são minhas e **não foram validadas**.
- Cada feature segue o fluxo SDD: **spec → plan → tasks → implementação**.
- Cada feature **nasce implantada** na Render.
- Feature freeze no fim da semana 6, com uma exceção: as estatísticas básicas (MVP-EST-01) fecham na primeira metade da semana 7.

### 11.2 Revisão de viabilidade (importante)
O escopo da v0.2 tinha atividades soltas atribuídas pelo professor. A reunião trocou isso por **trilhas com inscrição, execução e validação**, e voltou o papel admin. Pelas minhas estimativas, isso adiciona de **1,5 a 2 semanas** ao plano anterior, e as semanas 4 a 6 ficam densas.

| Opção | O que fazer | Risco |
|---|---|---|
| **A · Manter 8 semanas** (recomendada) | Todos os itens **M** e **S** entram; os **Opc** (nível por eixo e prontuário) ficam para depois do piloto se não couberem; corte pela ordem de 11.4 | Médio. Revisar na semana 2 com a velocidade real |
| **B · Estender para 10 semanas** | Entram também os Opc | Baixo para o escopo, mas o prazo muda |
| **C · Manter 8 semanas e todos os itens** | — | **Alto.** Não recomendado |

### 11.3 Plano semanal (opção A)

| Semana | Foco | Entregas | Critério de saída |
|---|---|---|---|
| **1** | Fundação e login | Constituição e spec da F1; esqueleto Django; CI; deploy; modelo de usuário (4 papéis); login obrigatório por padrão; páginas iniciais por papel; comando do primeiro admin | Login em **produção**; teste "toda rota exige login" verde |
| **2** | Contas e convites | Convite, aceite, recuperação de senha, e-mail por API, bloqueio de tentativas, gestão de contas (IS e admin), troca de senha | **Marco M1:** F1 completa (J-1, J-2, J-8) |
| **3** | Empreendimentos e ciclo | Empreendimentos, representantes, supervisão, ciclo e semestres, listas por papel | J-3 (primeira parte) |
| **4** | Trilhas | Editor de trilha base (IS) e personalizadas (professor); atividades; publicar e arquivar; regras de edição | Trilhas publicadas |
| **5** | Inscrição e execução | Inscrição pela IS e automática na trilha base; geração do progresso por atividade; telas do empreendimento; marcar como concluída | J-4 completa |
| **6** | Validação, painel e acompanhamentos | Fila e validação/devolução; histórico; painel do professor; situação; acompanhamentos da IS | **Marco M2:** J-5 e J-6 completas (laço professor ↔ empreendimento); **feature freeze** |
| **7** | Estatísticas e endurecimento | Estatísticas básicas; revisão de segurança (OWASP ASVS); acessibilidade; mobile; termo de privacidade; backup e restauração testados; plano pago na Render; carga dos dados reais; testes de ponta a ponta | **Marco M3:** J-1 a J-8 verdes em produção; piloto interno com a IS |
| **8** | Piloto e estabilização | Piloto assistido; correção de bugs; guia de 1 página por papel; manual de operação; retrospectiva; priorização do próximo ciclo | **Marco M4:** MVP em produção com usuários reais |

> Exemplo de calendário: começando na semana de 12/10/2026, o marco M4 cairia em 4/12/2026.

### 11.4 Ordem de corte
Cortar nesta ordem, sem tocar no obrigatório:
1. **Opc:** prontuário mínimo (MVP-PRN-*), depois nível por eixo (MVP-EIX-*)
2. MVP-INS-05 (inscrição em lote) e MVP-TRL-07 (duplicar trilha)
3. MVP-EST-02 e MVP-EST-03
4. MVP-EXE-04 e MVP-VAL-05 (desfazer e reabrir)
5. MVP-PRO-03 (ver trilhas de outros donos)
6. MVP-EMP-07 (desativar empreendimento; manter o campo "ativo" no banco)

**Não cortar:** seção 2 (nada sem login), F1 (exceto MVP-ACE-10), isolamento, trilhas (TRL-01 a 05), inscrição (INS-01 a 03), execução e validação (EXE-01 a 03, 05, 06 e VAL-01 a 04), MVP-PRO-01 e 02, MVP-ACP-01 a 03, MVP-EST-01 e os RNF-MVP-01, 02, 06, 07.

### 11.5 Prazos de decisão

| Decisão | Necessária até | Se não houver resposta |
|---|---|---|
| Q-20 · O que é o "hub" (muda o modelo de topo) | Semana 1 | Considerar uma única incubadora |
| Q-21 · Vocabulário (Trilha como nome único) | Semana 1 | Adotar a proposta |
| Q-28 · Alcance do admin | Semana 1 | Só contas |
| Convite × autocadastro com aprovação | Semana 1 | Convite |
| Framework de CSS | Semana 1 | Bootstrap 5 |
| Provedor de e-mail transacional | Início da semana 2 | O de menor custo com API HTTPS |
| Q-22 · Quem valida na trilha base | Semana 4 | Professor supervisor, com IS como exceção |
| Q-24 · Professor vê todas as trilhas ou só as suas | Semana 4 | Todas, em leitura |
| Orçamento da Render (plano pago) | Semana 6 | Piloto sem o banco gratuito |
| Avaliação LGPD da hospedagem | Semana 6 | Piloto sem dados pessoais reais |
| Lista real de usuários do piloto | Semana 6 | Piloto com poucos usuários |

> **Banco gratuito da Render:** um Postgres gratuito criado na semana 1 expira 30 dias depois, antes do fim do prazo, e não tem backups. Use Postgres local no desenvolvimento e crie o da Render já em plano pago.

---

## 12. Critérios de aceite do MVP e do piloto

**O MVP está pronto quando:**
1. J-1 a J-8 passam em produção.
2. O teste automatizado confirma que só as 6 exceções da seção 2 respondem sem login.
3. Os testes de isolamento passam: empreendimento A não vê B; professor só vê supervisionados; só o validador autorizado valida.
4. Backup automático ativo e restauração testada.
5. Termo de privacidade exibido no primeiro acesso.
6. Nenhum defeito bloqueante ou de segurança aberto.

**Sucesso do piloto:**

| Critério | Meta |
|---|---|
| Escala | 1 IS, 2–3 professores, 5–9 empreendimentos |
| Adoção | 100% dos convidados ativos; ≥ 70% dos empreendimentos acessam a cada 2 semanas |
| Laço completo | Pelo menos 1 atividade de cada empreendimento percorre marcar → validar |
| Tempo de resposta | Fila de validação com atividade mais antiga abaixo de 7 dias [ASSUMIDO] |
| Substituição | A IS acompanha trilhas e acompanhamentos pelo sistema, sem planilha paralela |
| Segurança | Nenhum acesso indevido entre empreendimentos |

---

## 13. Riscos

| Risco | Prob. | Impacto | Mitigação |
|---|---|---|---|
| Escopo da reunião não cabe em 8 semanas | **Alta** | Alto | Opção A (11.2), ordem de corte, revisão na semana 2 |
| Vocabulário e regras de validação ainda ambíguos (Q-20, 21, 22) | Alta | Alto | Resolver até a semana 1; o modelo de dados depende deles |
| Permissões mudam no meio do caminho | Alta | Médio | Tabela única de permissões e testes gerados dela |
| Fila de validação trava e o empreendedor fica sem retorno | Média | Alto | Painel de validação com idade; estatística de fila na IS |
| E-mail de convite não chega | Média | Alto | Provedor por API com SPF/DKIM; reenvio |
| Banco gratuito da Render expira | Alta (se usado) | Alto | Local no desenvolvimento; pago na Render |
| Dados pessoais hospedados fora do Brasil | Média | Alto | Avaliar LGPD até a semana 6 |
| Escopo cresce | Alta | Médio | Todo pedido novo vai primeiro para a spec |

---

## 14. Decisões pendentes (resumo)

| # | Pergunta | Proposta |
|---|---|---|
| 1 | Q-20 · O que é o hub? | Uma incubadora só |
| 2 | Q-21 · Trilha como nome único? | Sim |
| 3 | Q-22 · Quem valida na trilha base? | Professor supervisor; IS como exceção |
| 4 | Q-28 · Alcance do admin | Só contas |
| 5 | Convite ou autocadastro com aprovação | Convite |
| 6 | Um empreendimento com mais de um professor | Sim |
| 7 | Q-24 · Professor vê todas as trilhas do empreendimento | Sim, em leitura |
| 8 | O empreendedor pode desfazer; o validador pode reabrir | Ambos |
| 9 | Capacidade real (pessoas e horas por semana) e data de início | Base do cronograma |
| 10 | Escolher a Opção A ou B da seção 11.2 | A |

---

## 15. Backlog pós-MVP

1. **Agendamento** (R-09): atividade em que o empreendedor escolhe data e horário (`MODELAGEM_BANCO.md`, seção 10).
2. **Prontuário completo** (R-11): resumo, busca de duplicidades, ligação com trilhas, visibilidade ao empreendimento.
3. **Nível por eixo** completo, com gráficos de evolução (se não couber no MVP).
4. **Etapas** dentro da trilha e **upload de evidências**.
5. Diagnóstico por questionário (se Q-30 mantiver).
6. Indicadores institucionais e exportação.
7. Notificações de prazo e por e-mail.
8. SSO institucional, múltiplos perfis, auditoria completa.

---

## 16. Histórico

| Versão | Data | Mudança |
|---|---|---|
| 0.1 | 2026-09-30 | MVP amplo: diagnóstico, demandas, Nexus, jornadas. |
| 0.2 | 2026-10-07 | MVP-0: 3 papéis, atividades, acompanhamentos, estatísticas; "nada sem login"; 8 semanas. |
| 0.3 | 2026-10-10 | Decisões da reunião: 4 papéis (admin), trilha base e personalizadas, inscrição pela IS, validação pelo professor, nível por eixo e prontuário (opcionais), agendamento adiado; revisão de viabilidade. |
