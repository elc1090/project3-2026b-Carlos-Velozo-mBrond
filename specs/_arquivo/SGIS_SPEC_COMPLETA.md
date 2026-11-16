> ⚠️ **Documento arquivado — não usar para implementar.** Substituído por [`SGIS_SPEC_MVP_v0.4.md`](../SGIS_SPEC_MVP_v0.4.md). Mantido apenas como registro histórico. Ver [`README.md`](README.md).

# SGIS — Especificação Funcional Completa

**Sistema de Gestão da Incubadora Social (UFSM)**
**Versão:** 0.1 (rascunho para validação)

---

## 0. Como ler e usar este documento


**Convenções**

| Marca | Significado |
|---|---|
| `RF-XXX-NN` | Requisito funcional (módulo + número) |
| `RN-NN` | Regra de negócio |
| `RNF-NN` | Requisito não funcional |
| `Q-NN` | Questão em aberto (seção 11) |
| `[ASSUMIDO]` | Inferido do protótipo, **precisa ser confirmado** pela equipe da IS |
| Prioridade | **M**ust · **S**hould · **C**ould · **W**on't (nesta versão), no estilo MoSCoW |
| Coluna MVP | **Sim** (entra integral) · **Parcial** (versão simplificada, ver `SGIS_SPEC_MVP.md`) · **Não** |

---

## 1. Visão e contexto

### 1.1 Problema
A Incubadora Social (IS) acompanha empreendimentos (MEIs, associações, coletivos) durante um ciclo de 4 semestres. Hoje, o diagnóstico, as demandas, as ofertas de projetos/disciplinas de extensão e o acompanhamento individual não estão conectados em um único lugar.

### 1.2 Objetivos
1. Organizar o ciclo de incubação (Acolhimento → Diagnóstico → Trilha → Desenvolvimento → Reavaliação).
2. Medir o desenvolvimento dos empreendimentos em 5 eixos e 3 níveis de maturidade.
3. Transformar o diagnóstico em demandas rastreáveis.
4. Conectar demandas às ofertas de projetos e disciplinas extensionistas (**Nexus**).
5. Dar ao empreendimento uma trilha clara do que fazer, com conteúdos, atividades, encontros e entregas.
6. Dar à IS e aos professores visibilidade do andamento e da evolução.

### 1.3 Não-objetivos (v1)
- Ser um Learning Management System completo (hospedagem de vídeo, fóruns, notas, questionários).
- Gestão financeira do empreendimento. A jornada *orienta* finanças, mas o sistema não é um ERP.
- Aplicativo nativo. A v1 é web responsiva.
- Marketplace, pagamentos ou chat em tempo real.

---

## 3. Atores e permissões

### 3.1 Perfis

| Perfil | Descrição | Área no protótipo |
|---|---|---|
| **Empreendimento** | Representante(s) do negócio. Percorre a trilha e executa atividades. | `screenEmp` |
| **Professor / Projeto** | Docente ou equipe de projeto/disciplina que oferta jornadas e acompanha os empreendimentos atendidos. | `screenProf`, `moodleProfessor` |
| **Incubadora Social** | Equipe gestora: configura ciclo e metodologia, aplica diagnósticos, gerencia demandas, pactua e acompanha. | `screenIS`, `isAdminPanel`, `isEnterprisesPanel` |
| **Admin** | Gestão de contas de todos os papéis e da plataforma. | — |

### 3.2 Matriz de permissões (resumo)

| Recurso | Empreendimento | Professor/Projeto | IS | Admin |
|---|---|---|---|---|
| Dados do próprio empreendimento | Ler/editar parcial | Ler (apenas vinculados) | Ler/editar tudo | — |
| Diagnóstico | Ler resultado (próprio) | Ler resultado (vinculados) | Aplicar/editar/finalizar | — |
| Demandas | Ler (próprias) | Ler (vinculadas às suas ofertas) | CRUD | — |
| Metodologia e ciclo | — | — | CRUD | — |
| Jornadas (catálogo e editor) | Ler as suas | CRUD nas suas ofertas | CRUD em todas | — |
| Execução de itens | Executar os próprios | Validar nos vinculados | Validar/lançar ações | — |
| Indicadores | Ver próprio progresso | Ver das suas ofertas | Ver todos | — |
| Trilha base | Ver (se inscrito) | Ver | Criar, editar, publicar | — |
| Trilhas personalizadas | Ver (se inscrito) | Criar e editar as suas; ver as demais [Q-24] | Ver todas | — |
| Inscrição em trilhas | — | Ver (dos supervisionados) | Criar, pausar, cancelar | — |
| Marcar atividade como concluída | ✔ (as próprias) | — | — | — |
| Validar ou devolver atividade | — | ✔ (regra: RF-VAL-06) | ✔ (exceção registrada) [Q-22] | — |
| Nível por eixo | Ver o próprio | Ver (supervisionados) | Definir | — |
| Prontuário | Só registros liberados [Q-25] | Ler e escrever (supervisionados) | Ler e escrever | — |
| Contas de usuário | — | — | Convidar professor e empreendimento | Todas, inclusive IS e admin |
| Usuários e perfis | — | — | Convidar | CRUD |

---

## 4. Modelo conceitual

Entidades principais e relacionamentos. **O modelo de dados detalhado e atualizado com as decisões da reunião está em `MODELAGEM_BANCO.md`**, que prevalece sobre o esboço abaixo (a "Jornada" do esboço corresponde à "Trilha"; a "Demanda" passa a ser registro do prontuário).

```
Ciclo 1──n Semestre
Ciclo 1──n Matrícula n──1 Empreendimento
Empreendimento 1──n Usuário(representante)
Eixo 1──n Competência 1──n Pergunta (nível N1|N2|N3)
Empreendimento 1──n Diagnóstico 1──n RespostaDiagnóstico n──1 Pergunta
Diagnóstico 1──n ResultadoCompetência (nível, prioridade, evidência, pontos fortes/atenção)
Empreendimento 1──n Demanda n──1 Competência
Origem(Projeto|Disciplina|IS) 1──n Jornada(oferta) 1──n Etapa 1──n Item
Demanda 1──n Pactuação n──1 Jornada(oferta)
Pactuação 1──1 InstânciaJornada n──1 Empreendimento
InstânciaJornada 1──n ProgressoItem n──1 Item
ProgressoItem 1──n Evidência
Empreendimento 1──n Ação (lançada pela IS/Professor)
Encontro n──n Participante
```

**Tipos de item de jornada:** Material de leitura · Vídeo · Link externo · Questionário · Atividade prática · Entrega de arquivo/evidência · Encontro/agendamento · Checklist · Formulário · Evento.

**Tipos de ação lançada pela IS:** Ação · Material · Questionário · Atividade · Encontro/agendamento · Entrega/evidência · Formulário · Registro/nota.

---

## 5. Ciclos de vida (máquinas de estado)

### 5.1 Empreendimento no ciclo
`Pré-incubação → Incubação (semestres 2 e 3) → Desincubação → Encerrado`
Saídas alternativas: `Desligado` (qualquer estado, com motivo). [ASSUMIDO] [Q-06]

### 5.2 Demanda
`Identificada → Em planejamento → Em pactuação → Em atendimento → Concluída`
Laterais: `Monitoramento` (prioridade "Acompanhar") e `Cancelada` (com motivo).
Status vistos no protótipo: *Identificada, Em planejamento, Em pactuação, Em atendimento, Monitoramento*.

### 5.3 Instância de jornada
`Planejada → Em andamento → Concluída` · lateral: `Pausada`, `Cancelada`.

### 5.4 Item de jornada (por empreendimento)
`Não iniciado → Em andamento → (Aguardando validação) → Concluído` · laterais: `Agendado` (encontros), `Atrasado` (derivado do prazo), `Devolvido` (evidência recusada).

### 5.5 Diagnóstico
`Rascunho → Finalizado` (imutável). Correção cria nova versão vinculada. (RN-03)

### 5.6 Jornada (oferta)
`Rascunho → Publicada → Arquivada`. Edição de publicada gera nova versão (RN-10).

---

## 6. Requisitos funcionais por módulo

> Os critérios de aceite usam o formato **Dado / Quando / Então**, de forma resumida. Eles serão a base dos testes.

### M01 · Acesso e perfis

| ID | Requisito | Prior. | MVP |
|---|---|---|---|
| RF-ACE-01 | O usuário se autentica com credenciais válidas. [Q-01 define e-mail/senha ou login institucional] | M | Sim |
| RF-ACE-02 | Após o login, o usuário é direcionado à área do seu perfil (Empreendimento, Professor/Projeto ou IS). | M | Sim |
| RF-ACE-03 | Um usuário pode ter mais de um perfil e alternar entre eles. [ASSUMIDO: o protótipo tem seletor de perfil apenas para demonstração] [Q-08] | C | Não |
| RF-ACE-04 | Recuperação de senha por e-mail. | M | Sim |
| RF-ACE-05 | A IS convida usuários por e-mail, definindo perfil e vínculo (empreendimento ou projeto). | M | Sim |
| RF-ACE-06 | Isolamento de dados: cada perfil só acessa o que a matriz 3.2 permite. | M | Sim |
| RF-ACE-07 | Registro de auditoria das ações sensíveis (quem, quando, o quê). | S | Parcial |

**Aceite RF-ACE-06:** *Dado* um usuário do empreendimento A, *quando* ele tenta abrir (por URL ou API) dados do empreendimento B, *então* recebe acesso negado e nada é exibido.

### M02 · Empreendimentos

| ID | Requisito | Prior. | MVP |
|---|---|---|---|
| RF-EMP-01 | A IS cadastra empreendimento: nome, tipo (MEI, Associação, Coletivo, Empreendimento, outro), descrição/segmento, contatos. | M | Sim |
| RF-EMP-02 | A IS vincula um ou mais representantes (usuários) ao empreendimento. | M | Sim |
| RF-EMP-03 | O empreendimento é matriculado em um ciclo e possui um semestre atual (1 a 4). | M | Sim |
| RF-EMP-04 | A IS avança o semestre do empreendimento, mantendo histórico com data e autor. | M | Sim |
| RF-EMP-05 | A IS lista empreendimentos com filtros: Todos, Ativos, Desincubação. | M | Sim |
| RF-EMP-06 | A IS registra desincubação ou desligamento com motivo. [Q-06] | S | Não |
| RF-EMP-07 | O representante edita dados de contato do próprio empreendimento. | S | Parcial |

**Aceite RF-EMP-04:** *Dado* um empreendimento no semestre 2, *quando* a IS avança o semestre, *então* ele passa ao semestre 3, o histórico registra a mudança e o semestre anterior permanece consultável.

### M03 · Ciclo e Metodologia (configuração da IS)

| ID | Requisito | Prior. | MVP |
|---|---|---|---|
| RF-CIC-01 | A IS cria/edita um ciclo: nome, período, 4 semestres com datas. | M | Parcial (1 ciclo semeado) |
| RF-CIC-02 | A IS define, por semestre, as **atividades do ciclo**, comuns a todos os empreendimentos (ex.: acolhimento, diagnóstico inicial, pactuação da trilha, formações, reavaliação). | M | Parcial |
| RF-CIC-03 | Cada atividade do ciclo tem tipo (material, questionário, atividade, encontro, formulário, evento), obrigatoriedade e prazo. | M | Parcial |
| RF-MET-01 | A IS gerencia eixos (5 padrão: Empreendedor, Tecnológico, Mercado, Gestão, Capital) com descrição. | M | Parcial (seed + edição) |
| RF-MET-02 | A IS gerencia competências por eixo (no protótipo, 9 por eixo). | M | Parcial |
| RF-MET-03 | Biblioteca de ferramentas: recursos reutilizáveis (guias, planilhas, modelos) associáveis a competências. | C | Não |
| RF-MET-04 | Alterações na metodologia não alteram diagnósticos já finalizados. | M | Sim |

### M04 · Diagnóstico

| ID | Requisito | Prior. | MVP |
|---|---|---|---|
| RF-DIA-01 | **Construtor:** a IS define perguntas por competência e nível (N1, N2, N3). Cada pergunta tem um tipo (estruturação, consolidação, autonomia). | M | Parcial (importação/seed + edição simples) |
| RF-DIA-02 | Opções de resposta padrão: *Sim, Parcialmente, Não, Não se aplica*. | M | Sim |
| RF-DIA-03 | A IS aplica o diagnóstico em reunião conjunta: navega por eixo/competência, registra respostas, salva rascunho e retoma depois. | M | Sim |
| RF-DIA-04 | O sistema apresenta as perguntas do nível corrente da competência (no primeiro diagnóstico, N1). [ASSUMIDO] [Q-02] | M | Sim |
| RF-DIA-05 | Por competência, o resultado registra: **nível**, **prioridade** (Alta, Média, Acompanhar), **evidência** (texto), **pontos fortes**, **pontos de atenção**. O sistema sugere; a IS confirma ou ajusta. [Q-02] | M | Sim |
| RF-DIA-06 | Ao finalizar, o diagnóstico fica imutável. Correções criam nova versão. | M | Sim |
| RF-DIA-07 | **Devolutiva:** o empreendimento vê o resultado por eixo e competência (níveis e prioridades). | M | Sim |
| RF-DIA-08 | Reavaliação semestral: nova aplicação com a mesma estrutura, comparável às anteriores. | M | Parcial |
| RF-DIA-09 | Anexar evidências (arquivos) às respostas. | C | Não |
| RF-DIA-10 | Resultado agregado por eixo (ex.: "Capital: N1") a partir das competências. [Q-03] | S | Parcial |

**Aceite RF-DIA-06:** *Dado* um diagnóstico finalizado, *quando* qualquer usuário tenta alterar uma resposta, *então* o sistema bloqueia e oferece "criar nova versão".

### M05 · Demandas

| ID | Requisito | Prior. | MVP |
|---|---|---|---|
| RF-DEM-01 | A IS cria demandas a partir de resultados do diagnóstico (competência, eixo e prioridade herdados, editáveis). | M | Sim |
| RF-DEM-02 | A IS ou o professor cria demanda manual a partir do acompanhamento. | M | Sim |
| RF-DEM-03 | Demanda tem: título, competência, eixo, prioridade, status, origem (diagnóstico/acompanhamento), empreendimento, descrição. | M | Sim |
| RF-DEM-04 | Status conforme 5.2, com histórico de transições. | M | Sim |
| RF-DEM-05 | Priorização conjunta: a IS registra, com o empreendimento, quais demandas são prioritárias (ex.: "3 definidas"). | M | Sim |
| RF-DEM-06 | Listagem e filtros por empreendimento, eixo, prioridade e status. | M | Sim |
| RF-DEM-07 | O empreendimento visualiza suas demandas e o andamento de cada uma. | M | Sim |

### M06 · Jornadas (catálogo e editor)

| ID | Requisito | Prior. | MVP |
|---|---|---|---|
| RF-JOR-01 | O professor/projeto (ou a IS) cadastra uma oferta de jornada: nome, origem (Projeto, Disciplina ou IS), eixo/competências atendidas, descrição. | M | Sim |
| RF-JOR-02 | **Editor:** o professor organiza a jornada em etapas ordenadas (ex.: Conhecer, Diagnosticar, Aplicar, Encontro, Consolidar) e, em cada etapa, itens ordenados. Pode adicionar etapa e reordenar. | M | Sim |
| RF-JOR-03 | Tipos de item: ver seção 4. | M | Parcial (ver MVP) |
| RF-JOR-04 | Por item: título, descrição/orientação, obrigatório (sim/não), **regra de conclusão** (empreendimento marca / professor valida / concluído após envio de evidência), prazo. | M | Sim |
| RF-JOR-05 | Ciclo de vida: rascunho → publicada → arquivada. | M | Sim |
| RF-JOR-06 | Editar jornada publicada cria nova versão; instâncias em andamento mantêm a versão original, salvo migração explícita. | S | Não |
| RF-JOR-07 | Uma jornada publicada gera **instâncias** por empreendimento (ex.: "3 instâncias ativas"), cada uma com progresso próprio. | M | Sim |
| RF-JOR-08 | Personalizar a instância (prazos, itens extras ou ocultos) para um empreendimento. | S | Não |
| RF-JOR-09 | **Jornada de Incubação**: jornada-base do ciclo, gerida pela IS, presente em toda trilha. | M | Parcial |
| RF-JOR-10 | Duplicar jornada. | C | Não |
| RF-JOR-11 | Cada etapa pode definir uma **entrega esperada** (ex.: "planilha de controle financeiro"). | M | Sim |

### M07 · Trilha e execução (área do empreendimento)

| ID | Requisito | Prior. | MVP |
|---|---|---|---|
| RF-TRI-01 | **Minha Incubação** (início): saudação, semestre atual, etapa do ciclo (Acolhimento → Diagnóstico → Trilha → Desenvolvimento → Reavaliação), contadores de demandas e jornadas ativas, próximos passos, níveis por eixo. | M | Sim |
| RF-TRI-02 | **Minha Trilha:** lista a Jornada de Incubação e as jornadas complementares, com progresso. | M | Sim |
| RF-TRI-03 | **Próximas atividades:** atividade, jornada, responsável, prazo, status. | M | Sim |
| RF-TRI-04 | **Continue sua jornada:** destaca o próximo item pendente (até 3 sugestões). | M | Sim |
| RF-TRI-05 | Abrir uma jornada mostra etapas com status (concluída, em andamento, não iniciada), entrega de cada etapa, próxima atividade e progresso. | M | Sim |
| RF-TRI-06 | Abrir um item: ler o conteúdo, enviar evidência, marcar como concluído conforme a regra de conclusão. | M | Sim |
| RF-TRI-07 | Upload de evidência com validação de tipo e tamanho (RN-11). | M | Sim |
| RF-TRI-08 | Responder questionário/formulário dentro do sistema. [Q-14] | S | Não |
| RF-TRI-09 | Solicitar/agendar encontro com o projeto ou a IS. | M | Parcial (registro manual) |
| RF-TRI-10 | Registrar dificuldades ou comentários em um item. | S | Não |
| RF-TRI-11 | Ver demandas (RF-DEM-07), diagnóstico (RF-DIA-07) e evolução (RF-EVO-01). | M | Sim |

**Aceite RF-TRI-06:** *Dado* um item com regra "concluído após envio de evidência", *quando* o empreendimento envia um arquivo válido, *então* o item passa a Concluído e o progresso da instância é recalculado.
**Aceite (variante):** *Dado* um item com regra "professor valida", *quando* o empreendimento envia a evidência, *então* o item fica *Aguardando validação* e só conclui após aprovação.

### M08 · Nexus (demanda × oferta)

| ID | Requisito | Prior. | MVP |
|---|---|---|---|
| RF-NEX-01 | **Mapa demanda × oferta:** por tipo de demanda/competência, mostra nº de empreendimentos com essa demanda e as ofertas compatíveis. | M | Sim |
| RF-NEX-02 | Contadores: demandas sem oferta, ofertas cadastradas, jornadas em execução. | M | Sim |
| RF-NEX-03 | Fluxo **Demanda → Oferta → Planejamento → Pactuação → Jornada específica**, com registro de cada passo. | M | Parcial |
| RF-NEX-04 | **Pactuação:** registra data, participantes (IS, projeto/disciplina, empreendimento), acordos e, ao confirmar, cria a instância da jornada. | M | Sim |
| RF-NEX-05 | Sugestão automática de ofertas compatíveis por eixo/competência. | S | Não |
| RF-NEX-06 | Atendimento coletivo: agrupar demandas semelhantes de vários empreendimentos em uma turma. | C | Não |
| RF-NEX-07 | Ofertas com janela de atendimento (semestre) e capacidade de vagas. | S | Não |

### M09 · Acompanhamento (IS e Professor)

| ID | Requisito | Prior. | MVP |
|---|---|---|---|
| RF-ACO-01 | **Painel da IS:** contadores (empreendimentos, demandas abertas, jornadas ativas, ações Nexus), fluxo de gestão, demandas para acompanhamento, agenda. | M | Parcial |
| RF-ACO-02 | **Meus empreendimentos (IS):** cards com progresso da trilha, nº de jornadas, demandas, pendências. | M | Sim |
| RF-ACO-03 | **Detalhe do empreendimento:** ações e atividades, jornadas e demandas, resumo (progresso, jornadas, demandas, pendências), último diagnóstico, próximos compromissos. | M | Sim |
| RF-ACO-04 | **Lançar ação:** título, descrição, tipo (seção 4), responsável, data/prazo. Fica no histórico do empreendimento. | M | Parcial (subconjunto de tipos) |
| RF-ACO-05 | Linha do tempo única por empreendimento (ações, encontros, entregas, transições de status). | M | Sim |
| RF-ACO-06 | **Painel do professor ("Minhas ações"):** jornadas ofertadas, empreendimentos atendidos, atividades do mês, pendências. | M | Sim |
| RF-ACO-07 | O professor acompanha cada empreendimento atendido: etapa atual, próxima ação, registro de atividades, encontros, entregas, evidências, dificuldades e próximos passos. | M | Sim |
| RF-ACO-08 | Validar entrega: aprovar ou devolver com comentário. | M | Sim |
| RF-ACO-09 | **Pendência** = item atrasado, entrega aguardando validação ou reavaliação em aberto. | M | Sim |

### M10 · Evolução e reavaliação

| ID | Requisito | Prior. | MVP |
|---|---|---|---|
| RF-EVO-01 | Tabela histórica por competência: nível no 1º diagnóstico e em cada reavaliação, com **situação** (Prioridade, Em evolução, Consolidada). | M | Sim |
| RF-EVO-02 | Linha do tempo do ciclo (4 semestres) com o semestre atual destacado. | S | Sim |
| RF-EVO-03 | Regras para definir a "situação" da competência. [Q-02] | M | Parcial |
| RF-EVO-04 | Gráficos de evolução (radar por eixo, linha por competência). | C | Não |
| RF-EVO-05 | A interface sempre explicita que N1/N2/N3 medem desenvolvimento e não etapas da incubação. | S | Sim |

### M11 · Agenda e encontros

| ID | Requisito | Prior. | MVP |
|---|---|---|---|
| RF-AGE-01 | Agenda da IS: lista cronológica de encontros, pactuações e reavaliações. | M | Parcial (lista simples) |
| RF-AGE-02 | Encontro: título, participantes, data/hora, duração, modalidade (online/presencial), link/local, registro pós-encontro. | M | Parcial |
| RF-AGE-03 | Exportar/sincronizar com calendário (arquivo ICS, Google, Outlook). | C | Não |
| RF-AGE-04 | Professor publica disponibilidade e o empreendimento escolhe um horário. | C | Não |

### M12 · Indicadores e relatórios

| ID | Requisito | Prior. | MVP |
|---|---|---|---|
| RF-IND-01 | Indicadores da IS: distribuição de níveis por eixo, demandas por status, jornadas por projeto, taxa de conclusão, empreendimentos por semestre. [Q-18] | S | Não |
| RF-IND-02 | Exportação de dados (CSV) e relatório institucional (PDF). | S | Não |
| RF-IND-03 | Relatório individual do empreendimento (portfólio do ciclo). | C | Não |

### M13 · Notificações

| ID | Requisito | Prior. | MVP |
|---|---|---|---|
| RF-NOT-01 | Notificações no sistema para eventos relevantes (nova atividade, prazo próximo, entrega validada/devolvida, encontro agendado). | S | Não |
| RF-NOT-02 | E-mails transacionais: convite, recuperação de senha (obrigatórios); demais eventos opcionais por preferência. | M/S | Parcial (convite e senha) |

### M14 · Administração da plataforma

| ID | Requisito | Prior. | MVP |
|---|---|---|---|
| RF-ADM-01 | Gerir usuários, perfis e vínculos. | M | Sim |
| RF-ADM-02 | Gerir entidades de origem de oferta (Projetos, Disciplinas) e seus professores. | M | Sim |
| RF-ADM-03 | Consultar trilha de auditoria. | S | Não |

---

### Módulos acrescentados pela reunião

> Estes módulos complementam M01 a M14. Onde houver conflito com requisitos anteriores (ex.: RF-JOR, RF-NEX, RF-DEM, RF-DIA), valem os desta seção.

### M01-A · Sem área pública e contas (R-01, R-02)

| ID | Requisito | Prior. | MVP |
|---|---|---|---|
| RF-ACE-08 | **Nenhuma funcionalidade ou dado é acessível sem login.** As únicas rotas abertas a anônimos são as necessárias para entrar: login, recuperação de senha, aceite de convite, verificação de saúde do serviço (sem dados), `robots.txt` e os arquivos visuais dessas telas. Lista fechada e critérios em `SGIS_SPEC_MVP.md`, seção 2. | M | Sim |
| RF-ACE-09 | O **admin** gerencia as contas de todos os papéis (inclusive IS e admin): convidar, desativar, reativar. Alcance sobre dados de negócio: Q-28. | M | Sim |
| RF-ACE-10 | A **IS** convida professores e usuários de empreendimento. Apenas o admin convida IS e admin. [ASSUMIDO] | M | Sim |

### M06-A · Trilhas, inscrição e visão do professor (R-03 a R-06, R-10)

| ID | Requisito | Prior. | MVP |
|---|---|---|---|
| RF-TRL-01 | A IS define a **trilha base** do ciclo: título, descrição e atividades. Existe uma trilha base publicada por ciclo. | M | Sim |
| RF-TRL-02 | O ciclo principal da incubadora (semestres e datas) é definido pela IS. Revisa RF-CIC-01. | M | Parcial |
| RF-TRL-03 | O professor cria **trilhas personalizadas**: título, descrição e atividades. | M | Sim |
| RF-TRL-04 | Atividade de trilha: título, descrição, tipo (leitura, link, tarefa, agendamento), obrigatória (sim/não), exige validação (padrão sim), prazo fixo ou relativo à inscrição. | M | Parcial (sem agendamento) |
| RF-TRL-05 | Estados: rascunho, publicada, arquivada. Publicar exige ao menos uma atividade. Trilha com progresso é arquivada, nunca apagada. | M | Sim |
| RF-TRL-06 | Editar trilha publicada: ajustar textos e acrescentar atividades ao final. Atividade com progresso só pode ser arquivada. | M | Sim |
| RF-TRL-07 | Etapas dentro da trilha, com entrega esperada (substitui RF-JOR-02 e RF-JOR-11). | S | Não (Depois) |
| RF-TRL-08 | Reordenar atividades; duplicar trilha. | S/C | Parcial |
| RF-INS-01 | A **IS decide** em quais trilhas cada empreendimento pode entrar, inscrevendo-o. Sem inscrição, o empreendimento não vê a trilha. | M | Sim |
| RF-INS-02 | Inscrição em lote de vários empreendimentos. | S | Parcial |
| RF-INS-03 | Todo empreendimento do ciclo é inscrito automaticamente na trilha base. [ASSUMIDO] | M | Sim |
| RF-INS-04 | A IS pausa ou cancela uma inscrição; o histórico é preservado. | S | Sim |
| RF-INS-05 | O empreendimento vê apenas as trilhas em que está inscrito. | M | Sim |
| RF-INS-06 | O professor sugere à IS a inscrição de um empreendimento. | C | Não |
| RF-ACO-10 | O **professor visualiza**, por empreendimento supervisionado, **em quais trilhas ele está inscrito e o status em cada** (progresso, aguardando validação, atrasadas). | M | Sim |
| RF-ACO-11 | O professor vê também as trilhas de outros donos em que o empreendimento está inscrito (somente leitura). [Q-24] | S | Sim |

**Aceite RF-INS-01:** *Dado* uma trilha publicada, *quando* a IS inscreve o empreendimento A, *então* a trilha aparece para A com todas as atividades pendentes e **não** aparece para o empreendimento B.

### M07-A · Conclusão e validação (R-07)

| ID | Requisito | Prior. | MVP |
|---|---|---|---|
| RF-VAL-01 | O empreendedor **marca** a atividade como concluída. Se ela exige validação, passa a *Aguardando validação*. | M | Sim |
| RF-VAL-02 | O professor **valida** (aprova) ou **devolve** a atividade; a devolução exige comentário. | M | Sim |
| RF-VAL-03 | Atividade devolvida: o empreendedor vê o comentário e pode marcar novamente. | M | Sim |
| RF-VAL-04 | O empreendedor desfaz a marcação enquanto ela aguarda validação. | S | Sim |
| RF-VAL-05 | O validador reabre uma atividade concluída, informando o motivo. | S | Parcial |
| RF-VAL-06 | **Quem valida:** na trilha personalizada, o professor dono da trilha; na trilha base, professor supervisor do empreendimento ou a IS. [Q-22] | M | Sim |
| RF-VAL-07 | **Fila de validação** do professor, da mais antiga para a mais nova. | M | Sim |
| RF-VAL-08 | Histórico de cada atividade (marcações, validações, devoluções) com autor, data e comentário. | M | Sim |
| RF-VAL-09 | Atividade sem validação (configuração da atividade) conclui ao ser marcada. | S | Sim |

**Aceite RF-VAL-02:** *Dado* uma atividade *Aguardando validação*, *quando* o professor devolve sem comentário, *então* o sistema recusa. *Quando* devolve com comentário, *então* o status passa a *Devolvida*, o empreendedor recebe o comentário e o evento fica no histórico.

### M11-A · Atividade de agendamento (R-09 — a refinar)

> A ideia ainda será refinada. Opções e perguntas em `MODELAGEM_BANCO.md`, seção 10. Os requisitos abaixo são provisórios.

| ID | Requisito | Prior. | MVP |
|---|---|---|---|
| RF-AGD-01 | Tipo de atividade **Agendamento**: o empreendedor escolhe data e horário. | S | Não |
| RF-AGD-02 | Origem dos horários: responsável publica janelas livres (opção A), empreendedor propõe e responsável confirma (B) ou disponibilidade recorrente (C). [Q-27] | S | Não |
| RF-AGD-03 | Um horário só pode ser reservado por um empreendimento. | S | Não |
| RF-AGD-04 | Cancelamento e remarcação com regras de antecedência. | S | Não |
| RF-AGD-05 | A atividade conclui após o encontro realizado, registrado pelo responsável. [ASSUMIDO] | S | Não |
| RF-AGD-06 | Lembretes e arquivo de calendário. | C | Não |

### M15 · Prontuário do empreendimento (R-11 — a pensar)

> Objetivo: **evitar retrabalho** com demandas e problemas do empreendimento. Princípios em `MODELAGEM_BANCO.md`, seção 11.

| ID | Requisito | Prior. | MVP |
|---|---|---|---|
| RF-PRN-01 | Cada empreendimento tem **um prontuário** que permanece quando o professor muda. | S | Parcial (MVP-opc) |
| RF-PRN-02 | Professores supervisores e a IS criam registros: demanda, problema, observação, encaminhamento e resolução, com eixo, prioridade e status (aberto, em andamento, resolvido, descartado). | S | Parcial (MVP-opc) |
| RF-PRN-03 | Resumo atual do empreendimento, editável. | S | Parcial (MVP-opc) |
| RF-PRN-04 | Edições guardam a versão anterior; nada é apagado. | S | Parcial (MVP-opc) |
| RF-PRN-05 | Ao abrir um empreendimento, o professor vê primeiro as pendências abertas do prontuário. | S | Parcial (MVP-opc) |
| RF-PRN-06 | Ao criar um registro, o sistema mostra registros abertos semelhantes (mesmo eixo) para evitar duplicidade. | C | Não |
| RF-PRN-07 | Uma demanda aponta para a inscrição que a atende (demanda → trilha → resolução). | S | Não |
| RF-PRN-08 | Cada registro tem a opção de ser visível ao empreendimento (padrão: não). [Q-25] | S | Parcial (MVP-opc) |
| RF-PRN-09 | A **demanda** (M05) passa a ser um tipo de registro do prontuário. RF-DEM-* será reescrito sobre este módulo. | — | — |

### M16 · Desenvolvimento por eixo (R-08)

| ID | Requisito | Prior. | MVP |
|---|---|---|---|
| RF-EIX-01 | Os 5 eixos (Empreendedor, Tecnológico, Mercado, Gestão, Capital) são mantidos pela IS. | M | Sim (carga fixa) |
| RF-EIX-02 | A IS registra o **nível de cada eixo** de cada empreendimento conforme as reuniões, com data, observação e o acompanhamento de origem. | M | Parcial (MVP-opc) |
| RF-EIX-03 | O histórico é preservado; o nível atual de um eixo é o registro mais recente. | M | Parcial (MVP-opc) |
| RF-EIX-04 | O empreendimento e o professor supervisor veem o nível atual e a evolução (somente leitura). | M | Parcial (MVP-opc) |
| RF-EIX-05 | Só a IS altera o nível por eixo. | M | Sim |
| RF-EIX-06 | Relação com o diagnóstico por questionário (M04): o questionário vira instrumento de apoio ou é retirado. [Q-30] | — | — |

---

## 7. Regras de negócio

| ID | Regra |
|---|---|
| RN-01 | Um empreendimento está em **um único** semestre do ciclo por vez. |
| RN-02 | N1, N2 e N3 medem desenvolvimento da **competência**, independentemente do semestre. Um empreendimento pode estar em N2 em Gestão e N1 em Capital no mesmo semestre. |
| RN-03 | Diagnóstico finalizado é imutável. Correção = nova versão, com justificativa. |
| RN-04 | Toda demanda pertence a um empreendimento e a uma competência. |
| RN-05 | Uma instância de jornada nasce de uma pactuação e se vincula a uma demanda. [ASSUMIDO] [Q-05] |
| RN-06 | Não existe instância de jornada complementar sem pactuação confirmada. A Jornada de Incubação é criada automaticamente na matrícula. |
| RN-07 | **Progresso** da instância = itens obrigatórios concluídos ÷ total de itens obrigatórios. Itens opcionais não entram no cálculo. [ASSUMIDO] |
| RN-08 | Visibilidade: empreendimento vê apenas os próprios dados; professor vê apenas empreendimentos com instância de suas ofertas; IS vê tudo. |
| RN-09 | Regras de conclusão de item: (a) *empreendimento marca*: conclui no ato; (b) *professor valida*: conclui após aprovação; (c) *após envio de evidência*: conclui ao receber arquivo válido. |
| RN-10 | Editar jornada publicada não altera instâncias em andamento (versionamento). |
| RN-11 | Evidências: tipos permitidos e tamanho máximo definidos em configuração. [Q-10] Valores iniciais sugeridos: PDF, imagens, planilhas e documentos; até 20 MB. |
| RN-12 | Prioridade de demanda: **Alta**, **Média** ou **Acompanhar** (vai para status *Monitoramento*). |
| RN-13 | A reavaliação ocorre ao final de cada semestre de incubação (semestres 2 e 3), no mínimo. [ASSUMIDO] |
| RN-14 | Dados do protótipo (Delícias da Ana, ASSFOR etc.) são **fictícios** e não devem ser usados como carga real. |
| RN-15 | Item atrasado = prazo vencido e status diferente de Concluído (cálculo automático). |
| RN-16 | **Sem login, nada é acessível**, exceto a lista fechada de RF-ACE-08. Rota nova nasce protegida. |
| RN-17 | Há uma única trilha base publicada por ciclo, de autoria da IS. Trilha personalizada é de autoria de professor. |
| RN-18 | O empreendimento só percorre trilhas em que a IS o inscreveu. A inscrição na trilha base é automática. |
| RN-19 | Atividade que exige validação só conta como concluída (e no progresso) depois de validada pelo professor. Padrão: exige. |
| RN-20 | Atividade com progresso não pode ser apagada, apenas arquivada. Trilha com progresso, idem. |
| RN-21 | O nível por eixo só é alterado pela IS e o histórico é imutável. |
| RN-22 | O prontuário pertence ao empreendimento; trocar o professor supervisor não perde histórico. Registros não são apagados. |
| RN-23 | O admin gerencia contas e plataforma e **não** acessa dados de negócio. [ASSUMIDO] [Q-28] |

---

## 8. Requisitos não funcionais

| ID | Requisito |
|---|---|
| RNF-01 | **LGPD:** base legal definida, minimização de dados pessoais, consentimento quando aplicável, direito de exclusão/anonimização, política de retenção de evidências. [Q-10] |
| RNF-02 | **Segurança:** HTTPS, senhas com hash forte, controle de acesso por perfil (RBAC) em todas as rotas, proteção contra OWASP Top 10, upload com verificação de tipo e varredura de malware. |
| RNF-03 | **Responsivo / mobile-first para o perfil Empreendimento** (provável uso em celular). |
| RNF-04 | **Acessibilidade:** WCAG 2.1 AA (contraste, teclado, leitores de tela). Não depender só de cor para status/prioridade. |
| RNF-05 | **Desempenho:** telas principais carregam em até 3 s em conexão 4G comum; listas paginadas. |
| RNF-06 | **Disponibilidade:** meta de 99% em horário letivo, com backup diário e restauração testada. [Q-12] |
| RNF-07 | **Auditoria:** alterações em diagnóstico, demanda, pactuação e validação guardam autor e data. |
| RNF-08 | **Usabilidade:** linguagem simples, sem jargão metodológico na área do empreendimento. |
| RNF-09 | **Manutenibilidade:** cobertura de testes automatizados para regras de negócio (RN-*) e critérios de aceite. |
| RNF-10 | **Observabilidade:** logs estruturados e monitoramento de erros. |
| RNF-11 | **Portabilidade de dados:** exportação completa dos dados do ciclo em formato aberto. |
| RNF-12 | **Internacionalização:** apenas pt-BR na v1, com textos externalizados. |

---

## 9. Mapa do protótipo para as specs

| Tela / componente do protótipo | Módulo | Observações |
|---|---|---|
| `sgLanding` (escolha de perfil) | M01 | Em produção será tela de login. A escolha de perfil sai. |
| `home` (Minha Incubação) | M07 | |
| `diagnostico` | M04 | No protótipo aparece na área do empreendimento; na prática a aplicação é conduzida pela IS. [Q-04] |
| `trilha`, `journeyModal`, `activityModal` | M07 | |
| `demandas` | M05 | |
| `jornadas` (ofertas) | M06 | |
| `nexus` | M08 | |
| `evolucao` | M10 | |
| `screenEmp` | M07 | Resumo em cards da área do empreendimento. |
| `screenProf`, `moodleProfessor`, `editorResource` | M06, M09 | O nome `moodleProfessor` sugere inspiração no Moodle. [Q-14] |
| `screenIS` | M09 | |
| `isAdminPanel` (`isCycle`, `isDiag`, `isMethod`, `isActivities`) | M03, M04 | |
| `isEnterprisesPanel`, `enterpriseDetail`, `edAddModal` | M09 | "Demandas", "Jornadas" e "Indicadores" aparecem no menu, mas sem tela prototipada. |

---

## 10. Inconsistências encontradas no protótipo

Devem ser resolvidas antes de virarem requisito definitivo.

| # | Inconsistência | Onde | Impacto |
|---|---|---|---|
| I-1 | "Delícias da Ana" está no **1º semestre (Pré-incubação)** na área do empreendimento e no **3º semestre (Incubação)** no painel da IS. O ciclo mostra "Incubação 1" como atual. | home × IS | Define a regra de semestre (RN-01). |
| I-2 | Jornada "Gestão Financeira" tem **5 etapas** (lista e trilha: "3 de 5") e **6 etapas** no modal. | jornadas × journeyModal | Modelo de etapas/itens. |
| I-3 | Dois sentidos de "etapa": fases do editor (Conhecer → Consolidar) e etapas sequenciais com entrega (Diagnóstico financeiro → Planejamento). | moodleProfessor × journeyModal | Precisa decidir entre **etapa** e **fase/seção**. |
| I-4 | Jornadas ativas de "Delícias da Ana": 2 (home), 2 (trilha) e 3 (detalhe da IS). | vários | Regra de contagem. |
| I-5 | Níveis por eixo divergem: home mostra Empreendedor N2, Tecnológico N2, Mercado N1, Gestão N1, Capital N1; o detalhe da IS mostra Gestão N2. Mercado é "prioridade média" no diagnóstico e "Alta" em demandas. | home × IS × demandas | Fonte única de verdade dos níveis (Q-03). |
| I-6 | "45 perguntas" = 5 eixos × 9 competências, mas cada competência tem perguntas N1, N2 e N3 (potencialmente 135). | isDiag | Definir o tamanho do instrumento. |
| I-7 | Jornadas em execução: **18** no Nexus e **11** no painel da IS. | nexus × IS | Definição única do indicador. |
| I-8 | Filtros do IS: "Todos · 9 / Ativos · 8 / Desincubação · 1", mas só 6 cards. | isEnterprisesPanel | Apenas dado de exemplo. |
| I-9 | "Nexus" é nome do módulo **e** de um projeto ("Projeto Nexus"). | vários | Confusão de linguagem. [Q-13] |
| I-10 | A aplicação do diagnóstico aparece na área do empreendimento, mas o texto diz que é reunião conjunta conduzida pela IS. | diagnostico | Define quem responde. [Q-04] |

---

## 11. Questões em aberto

As marcadas com ⛔ **bloqueiam o MVP**.

| ID | Questão | Quem decide |
|---|---|---|
| ⛔ Q-01 | Login: e-mail/senha próprio ou login institucional da UFSM? | IS + TI |
| ⛔ Q-02 | Como o nível (N1/N2/N3) e a prioridade são calculados a partir de Sim/Parcialmente/Não/Não se aplica? Qual o limiar para passar de nível? O que define "Consolidada"? | IS (metodologia) |
| Q-03 | O nível é por **competência** e/ou por **eixo**? Como agregar? | IS |
| ⛔ Q-04 | Quem responde o diagnóstico: só a IS em reunião conjunta, ou o empreendimento também pode preencher sozinho? | IS |
| Q-05 | Uma instância de jornada atende uma demanda ou várias? | IS + professores |
| Q-06 | Critérios e fluxo de desincubação e desligamento. O que o empreendimento vê depois? | IS |
| Q-07 | Haverá vários ciclos/coortes simultâneos (empreendimentos entrando em momentos diferentes)? | IS |
| Q-08 | Um professor pode atuar em vários projetos/disciplinas? Uma disciplina muda a cada semestre letivo? | IS + professores |
| Q-09 | Agendamento precisa integrar calendário externo já na v1? | IS |
| Q-10 | Política de armazenamento de evidências: tipos, tamanho, retenção, base legal LGPD. | IS + jurídico |
| Q-11 | Volume esperado (empreendimentos, usuários, arquivos) e picos de uso. | IS |
| Q-12 | Onde será hospedado? Há exigência institucional de infraestrutura ou stack? | IS + TI |
| Q-13 | Renomear o módulo ("Nexus") ou o projeto para evitar ambiguidade? | IS |
| Q-14 | Questionários/formulários: construir motor próprio, usar ferramenta externa (links) ou integrar com Moodle? | IS |
| Q-15 | Dados pessoais dos membros do empreendimento: quais coletar e com qual finalidade? | IS + jurídico |
| Q-16 | Quem pode validar uma entrega quando a jornada é da IS? | IS |
| Q-17 | Canais de notificação (e-mail, WhatsApp, in-app)? | IS |
| Q-18 | Quais indicadores institucionais são exigidos (relatórios de extensão, editais, financiadores)? | IS |
| Q-19 | Existem dados históricos (planilhas, diagnósticos anteriores) a migrar? | IS |
| ⛔ Q-20 | O que é o **hub**? Outro nome da IS ou uma entidade que a contém (mais de uma incubadora)? Define se o sistema é multi-instituição. | IS |
| ⛔ Q-21 | Confirmar o vocabulário: **Trilha** como nome único; "Jornada" = trilha personalizada; "Jornada de Incubação" = trilha base. | IS |
| ⛔ Q-22 | Quem valida atividades da trilha base: professor supervisor, IS ou ambos? A IS pode validar qualquer atividade? | IS |
| Q-23 | A escala de nível por eixo continua N1–N3? O nível é só por eixo ou também por competência? | IS |
| Q-24 | O professor vê **todas** as trilhas dos empreendimentos que supervisiona ou só as suas? | IS |
| Q-25 | O empreendimento enxerga o prontuário (nada, parte ou tudo)? | IS + jurídico |
| Q-26 | Nome do "prontuário" (lembra saúde): "Ficha do empreendimento", "Histórico"? | IS |
| Q-27 | Modelo do agendamento: horários publicados, proposta livre ou disponibilidade recorrente? Com quem se agenda? A atividade conclui ao agendar ou ao realizar? | IS |
| ⛔ Q-28 | O que o admin faz além de gerir contas? Vê dados de negócio? Quem cria o primeiro admin? | IS + TI |
| Q-29 | Um empreendimento pode participar de mais de um ciclo ao mesmo tempo? | IS |
| Q-30 | O questionário de diagnóstico por competência (M04) continua existindo ou o nível por eixo definido pela IS o substitui? | IS |

---

## 12. Fora de escopo (v1)

Aplicativo nativo · hospedagem própria de vídeos · chat · fórum · pagamentos · integração financeira/contábil · certificação automática · IA generativa para diagnóstico · multi-instituição (multi-tenant). Podem entrar em versões futuras após validação.

---

## 13. Roadmap de specs derivadas

Esta spec é a "mãe". Para o desenvolvimento, ela deve ser fatiada em specs menores, uma por módulo, cada uma com o próprio plano e tarefas.

```
specs/
├── 00-constituicao.md          # princípios inegociáveis (segurança, LGPD, acessibilidade, testes)
├── 01-visao-e-glossario.md     # seções 1 e 2 deste documento
├── 02-atores-e-permissoes.md   # seção 3
├── 03-dominio-e-dados.md       # seções 4, 5 e 7
├── 10-acesso-e-perfis/         # M01
├── 20-empreendimentos/         # M02
├── 30-ciclo-e-metodologia/     # M03
├── 40-diagnostico/             # M04 e M10
├── 50-demandas/                # M05
├── 60-jornadas/                # M06
├── 70-trilha-e-execucao/       # M07
├── 80-nexus/                   # M08
├── 90-acompanhamento/          # M09 e M11
├── 95-indicadores-e-notificacoes/  # M12 e M13
└── NN-modulo/
    ├── spec.md      # o quê / por quê + critérios de aceite
    ├── plan.md      # como (stack, arquitetura, modelo de dados)
    └── tasks.md     # tarefas pequenas e verificáveis
```

**Ordem sugerida para escrever as próximas specs:** `00-constituicao` → `40-diagnostico` (maior risco metodológico, Q-02) → `60-jornadas` → `80-nexus` → `70-trilha-e-execucao`.

---

## 14. Histórico

| Versão | Data | Mudança |
|---|---|---|
| 0.1 | 2026-09-30 | Primeira versão, derivada do protótipo. Pendente de validação com a IS. |
| 0.2 | 2026-10-10 | Incorpora as decisões da reunião (R-01 a R-11): 4 papéis, sem área pública, trilha base e personalizadas, inscrição pela IS, validação pelo professor, nível por eixo, agendamento (a refinar), prontuário (a pensar). Novos módulos M01-A, M06-A, M07-A, M11-A, M15, M16; RN-16 a RN-23; Q-20 a Q-30. |
