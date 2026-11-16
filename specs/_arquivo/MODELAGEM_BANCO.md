> ⚠️ **Documento arquivado — não usar para implementar.** Substituído por [`SGIS_SPEC_MVP_v0.4.md`](../SGIS_SPEC_MVP_v0.4.md). Mantido apenas como registro histórico. Ver [`README.md`](README.md).

# Modelagem textual do banco de dados — SGIS

## 1. Objetivo

Este documento descreve uma proposta conceitual para o banco de dados do Sistema Gerenciador da Incubadora Social (SGIS).

Ele foi elaborado com base nas especificações atuais do projeto, no protótipo e nas anotações das reuniões. O documento deve servir como base para a criação do esquema visual do banco e, posteriormente, para a implementação dos modelos no Django.

## 2. Premissas principais

- O sistema não possui área pública.
- Todo usuário precisa estar autenticado para acessar as funcionalidades do sistema.
- Existem quatro papéis: `empreendimento`, `professor`, `IS` e `admin`.
- O papel `empreendimento` representa os usuários vinculados a um empreendimento.
- A IS controla ciclos, trilhas base, inscrições, eixos e acompanhamentos.
- O professor cria trilhas personalizadas e valida atividades.
- O admin gerencia contas, mas não acessa dados de negócio.
- Nenhum histórico importante deve ser apagado fisicamente.
- Alterações relevantes devem registrar autor e data.
- Os status calculados, como atividade atrasada, devem ser derivados do prazo e do estado atual sempre que possível.

## 3. Usuários e controle de acesso

### 3.1 Usuário

Representa qualquer pessoa que acessa o sistema.

Campos principais:

- `id`
- `nome`
- `email`
- `senha_hash`
- `papel`: empreendimento, professor, IS ou admin
- `status`: convite pendente, ativo ou desativado
- `ultimo_acesso`
- `criado_em`
- `atualizado_em`

Regras:

- Cada usuário possui apenas um papel.
- O e-mail deve ser único.
- Usuários desativados não podem acessar o sistema.
- O admin não visualiza dados de empreendimentos, trilhas ou prontuários.

### 3.2 Convite

Controla o acesso inicial de novos usuários.

Campos principais:

- `id`
- `email`
- `papel`
- `token`
- `expira_em`
- `aceito_em`
- `revogado_em`
- `criado_por`

Regras:

- O convite possui prazo de validade.
- O convite só pode ser utilizado uma vez.
- O reenvio deve revogar o convite anterior.

### 3.3 Vínculo usuário–empreendimento

Relaciona representantes ou usuários do empreendimento ao respectivo empreendimento.

Campos principais:

- `id`
- `usuario_id`
- `empreendimento_id`
- `tipo_vinculo`
- `principal`
- `ativo`
- `inicio_em`
- `fim_em`

Um empreendimento pode possuir vários representantes.

## 4. Empreendimentos

### 4.1 Empreendimento

Representa o negócio, coletivo, associação ou grupo acompanhado pela IS.

Campos principais:

- `id`
- `nome`
- `tipo`: MEI, associação, coletivo ou outro
- `descricao`
- `email_contato`
- `telefone_contato`
- `ativo`
- `criado_por`
- `criado_em`
- `atualizado_em`
- `desativado_em`

Relacionamentos:

- Possui vários representantes.
- Pode possuir vários professores supervisores.
- Pode participar de vários ciclos.
- Possui um prontuário.
- Possui inscrições em várias trilhas.
- Possui acompanhamentos e avaliações por eixo.

### 4.2 Supervisão

Representa o vínculo entre um professor e um empreendimento.

Campos principais:

- `id`
- `professor_id`
- `empreendimento_id`
- `inicio_em`
- `fim_em`
- `ativo`
- `criado_por`
- `observacao`

Um empreendimento pode ter vários professores. O histórico da supervisão deve ser preservado.

## 5. Ciclos e desenvolvimento

### 5.1 Ciclo

Representa o ciclo principal da incubadora, definido pela IS.

Campos principais:

- `id`
- `nome`
- `descricao`
- `data_inicio`
- `data_fim`
- `status`: planejamento, ativo ou encerrado
- `criado_por`
- `criado_em`

### 5.2 Semestre ou etapa do ciclo

Representa os quatro períodos do ciclo.

Campos principais:

- `id`
- `ciclo_id`
- `numero`
- `nome`
- `data_inicio`
- `data_fim`
- `descricao`

Exemplo:

- Pré-incubação
- Incubação 1
- Incubação 2
- Desincubação

### 5.3 Participação do empreendimento no ciclo

Relaciona um empreendimento a um ciclo.

Campos principais:

- `id`
- `empreendimento_id`
- `ciclo_id`
- `semestre_atual_id`
- `status`
- `inicio_em`
- `fim_em`
- `criado_por`

Regras:

- O empreendimento deve estar em apenas um semestre do ciclo por vez.
- A mudança de semestre deve registrar data e autor.
- O histórico de mudanças deve ser armazenado em uma tabela de movimentação.

### 5.4 Movimentação no ciclo

Registra a evolução do empreendimento entre os semestres.

Campos principais:

- `id`
- `participacao_ciclo_id`
- `semestre_anterior_id`
- `novo_semestre_id`
- `alterado_por`
- `alterado_em`
- `observacao`

## 6. Trilhas e atividades

### 6.1 Trilha

Representa uma trilha de desenvolvimento.

Campos principais:

- `id`
- `titulo`
- `descricao`
- `tipo`: base ou personalizada
- `ciclo_id`
- `criado_por`
- `professor_responsavel_id`
- `status`: rascunho, publicada ou arquivada
- `publicada_em`
- `arquivada_em`
- `criado_em`
- `atualizado_em`

Regras:

- A trilha base pertence à IS e está vinculada a um ciclo.
- Deve existir apenas uma trilha base publicada por ciclo.
- A trilha personalizada pertence a um professor.
- Uma trilha em rascunho não aparece para empreendimentos.
- Uma trilha com progresso não deve ser apagada; deve ser arquivada.
- A publicação exige ao menos uma atividade ativa.

### 6.2 Atividade da trilha

Representa uma atividade que faz parte de uma trilha.

Campos principais:

- `id`
- `trilha_id`
- `titulo`
- `descricao`
- `ordem`
- `tipo`: leitura, link, tarefa ou agendamento
- `obrigatoria`
- `exige_validacao`
- `tipo_prazo`: fixo ou relativo à inscrição
- `prazo_fixo`
- `dias_apos_inscricao`
- `ativa`
- `criado_por`
- `arquivada_em`

A atividade é um modelo. O seu andamento para cada empreendimento será controlado pela entidade `Execução da atividade`.

## 7. Inscrições e execução das atividades

### 7.1 Inscrição em trilha

Representa a decisão da IS de colocar um empreendimento em uma trilha.

Campos principais:

- `id`
- `empreendimento_id`
- `trilha_id`
- `participacao_ciclo_id`
- `status`: ativa, pausada, cancelada ou concluída
- `inscrito_por`
- `inscrito_em`
- `pausado_em`
- `cancelado_em`
- `motivo`

Regras:

- Apenas a IS pode criar, pausar ou cancelar inscrições.
- A inscrição deve ocorrer somente em uma trilha publicada.
- A trilha base deve ser inscrita automaticamente quando o empreendimento entra no ciclo.
- O empreendimento visualiza apenas suas próprias inscrições.
- Deve ser evitada a duplicação de uma inscrição ativa para o mesmo empreendimento e trilha.

### 7.2 Execução da atividade

Representa o andamento de uma atividade para um empreendimento específico.

Campos principais:

- `id`
- `inscricao_trilha_id`
- `atividade_trilha_id`
- `status`: pendente, aguardando validação, devolvida, concluída ou reaberta
- `prazo`
- `iniciada_em`
- `enviada_em`
- `concluida_em`
- `ultima_atualizacao_em`

Essa entidade permite que a mesma atividade exista uma vez na trilha, mas possua status diferente para cada empreendimento inscrito.

### 7.3 Histórico da atividade

Registra todas as ações realizadas sobre a atividade.

Campos principais:

- `id`
- `execucao_atividade_id`
- `acao`: marcada como concluída, desfeita, validada, devolvida ou reaberta
- `autor_id`
- `comentario`
- `criado_em`

Regras:

- O empreendimento pode marcar a atividade como concluída.
- O professor pode validar ou devolver.
- A devolução exige comentário.
- O histórico nunca deve ser apagado.
- A atividade somente conta como concluída no progresso depois da validação, quando a validação for exigida.

## 8. Acompanhamentos

### 8.1 Acompanhamento

Representa uma reunião ou registro realizado pela IS sobre o empreendimento.

Campos principais:

- `id`
- `empreendimento_id`
- `titulo`
- `descricao`
- `data_reuniao`
- `criado_por`
- `criado_em`
- `atualizado_em`
- `excluido_em`

Os acompanhamentos podem ser utilizados como origem das atualizações dos eixos e dos registros do prontuário.

## 9. Desenvolvimento por eixo

### 9.1 Eixo

Representa uma área de desenvolvimento do empreendimento.

Eixos iniciais:

- Empreendedor
- Tecnológico
- Mercado
- Gestão
- Capital

Campos principais:

- `id`
- `nome`
- `descricao`
- `ativo`
- `ordem`

### 9.2 Histórico de nível por eixo

Representa a avaliação do desenvolvimento de um empreendimento em determinado eixo.

Campos principais:

- `id`
- `empreendimento_id`
- `ciclo_id`
- `eixo_id`
- `nivel`: N1, N2 ou N3
- `observacao`
- `acompanhamento_origem_id`
- `registrado_por`
- `registrado_em`

Regras:

- Somente a IS pode alterar o nível.
- Cada alteração gera um novo registro.
- O nível atual é o registro mais recente.
- O empreendimento e seus professores supervisores possuem acesso somente para leitura.
- A atualização pode ser realizada com base nas reuniões e acompanhamentos registrados.

## 10. Prontuário do empreendimento

### 10.1 Prontuário

Representa o histórico permanente do empreendimento.

Campos principais:

- `id`
- `empreendimento_id`
- `resumo_atual`
- `criado_em`
- `atualizado_em`

Cada empreendimento possui um único prontuário.

### 10.2 Registro do prontuário

Armazena demandas, problemas, observações e encaminhamentos.

Campos principais:

- `id`
- `prontuario_id`
- `tipo`: demanda, problema, observação, encaminhamento ou resolução
- `titulo`
- `descricao`
- `eixo_id`
- `prioridade`: alta, média ou acompanhar
- `status`: aberto, em andamento, resolvido ou descartado
- `visivel_ao_empreendimento`
- `criado_por`
- `criado_em`
- `resolvido_em`
- `inscricao_trilha_relacionada_id`

A ligação com `inscricao_trilha_relacionada_id` permite rastrear:

```text
Demanda → Trilha → Atividades → Resolução
```

Regras:

- O prontuário permanece mesmo quando o professor supervisor muda.
- Professores supervisores e a IS podem registrar informações.
- Nenhum registro deve ser apagado definitivamente.
- O sistema pode alertar sobre registros abertos semelhantes para evitar duplicidade e retrabalho.
- A visibilidade para o empreendimento deve ser controlada por registro.
- Ao abrir o empreendimento, as pendências abertas devem aparecer primeiro.

### 10.3 Versão do registro

Mantém as versões anteriores de um registro alterado.

Campos principais:

- `id`
- `registro_prontuario_id`
- `titulo_anterior`
- `descricao_anterior`
- `status_anterior`
- `alterado_por`
- `alterado_em`

## 11. Agendamento

O agendamento ainda está em definição. Para manter o banco preparado, a atividade pode possuir o tipo `agendamento`.

### 11.1 Agendamento

Campos principais:

- `id`
- `execucao_atividade_id`
- `empreendimento_id`
- `professor_id`
- `data_hora_inicio`
- `data_hora_fim`
- `status`: proposto, confirmado, recusado, cancelado ou realizado
- `proposto_por`
- `confirmado_por`
- `local_ou_link`
- `observacao`
- `criado_em`

Fluxo sugerido:

1. O empreendimento propõe data e horário.
2. O professor ou a IS confirma ou recusa.
3. O encontro acontece.
4. O responsável registra a realização.
5. A atividade pode ser concluída após o encontro.

Posteriormente, podem ser adicionadas:

- janelas de disponibilidade;
- horários recorrentes;
- regras de cancelamento;
- integração com calendários externos.

## 12. Auditoria

Pode existir uma tabela geral de auditoria para registrar modificações importantes.

### 12.1 Auditoria

Campos principais:

- `id`
- `usuario_id`
- `entidade`
- `entidade_id`
- `acao`
- `dados_anteriores`
- `dados_novos`
- `criado_em`

Também é recomendado que as principais entidades possuam diretamente campos como:

- `criado_por`
- `criado_em`
- `atualizado_por`
- `atualizado_em`
- `excluido_em`

## 13. Relacionamentos principais

```text
USUARIO 1 ─── N VINCULO_USUARIO_EMPREENDIMENTO N ─── 1 EMPREENDIMENTO

USUARIO 1 ─── N SUPERVISAO N ─── 1 EMPREENDIMENTO

CICLO 1 ─── N SEMESTRE_CICLO

CICLO 1 ─── N PARTICIPACAO_CICLO N ─── 1 EMPREENDIMENTO

CICLO 1 ─── N TRILHA

TRILHA 1 ─── N ATIVIDADE_TRILHA

EMPREENDIMENTO 1 ─── N INSCRICAO_TRILHA N ─── 1 TRILHA

INSCRICAO_TRILHA 1 ─── N EXECUCAO_ATIVIDADE

EXECUCAO_ATIVIDADE 1 ─── N HISTORICO_ATIVIDADE

EMPREENDIMENTO 1 ─── N ACOMPANHAMENTO

EMPREENDIMENTO 1 ─── N NIVEL_EIXO_HISTORICO N ─── 1 EIXO

EMPREENDIMENTO 1 ─── 1 PRONTUARIO

PRONTUARIO 1 ─── N REGISTRO_PRONTUARIO

REGISTRO_PRONTUARIO 1 ─── N VERSAO_REGISTRO_PRONTUARIO

EXECUCAO_ATIVIDADE 1 ─── 0..1 AGENDAMENTO
```

## 14. Regras de integridade recomendadas

- `Usuario.email` deve ser único.
- Deve existir somente uma trilha base publicada por ciclo.
- Uma trilha publicada deve possuir pelo menos uma atividade ativa.
- Uma trilha personalizada deve possuir um professor responsável.
- Uma trilha base deve estar vinculada a um ciclo.
- Uma inscrição deve apontar para uma trilha publicada no momento da inscrição.
- Não deve existir mais de uma inscrição ativa igual para o mesmo empreendimento e trilha.
- Uma atividade com progresso não pode ser apagada; somente arquivada.
- Uma trilha com progresso não pode ser apagada; somente arquivada.
- Atividades atrasadas devem ser calculadas a partir do prazo e do status atual.
- O nível por eixo deve possuir histórico imutável.
- Registros do prontuário não devem ser excluídos fisicamente.
- A devolução de atividade deve exigir comentário.
- O admin não deve possuir permissão para consultar dados de negócio.

## 15. Entidades para uma segunda versão

O projeto completo também menciona funcionalidades que podem ser adicionadas posteriormente:

- diagnóstico;
- competências;
- perguntas e respostas;
- ofertas de projetos;
- pactuações;
- evidências e arquivos;
- etapas internas da trilha;
- notificações;
- indicadores avançados;
- integração com calendários externos.

Essas entidades devem ficar fora do primeiro esquema visual principal, mas o modelo atual deve permitir sua inclusão futura.

## 16. Decisões pendentes

Antes de transformar esta proposta em um diagrama definitivo, ainda precisam ser confirmados:

1. `Hub` será uma entidade própria ou apenas outro nome para a IS?
2. Um empreendimento poderá participar de mais de um ciclo simultaneamente?
3. Quem valida atividades da trilha base: professor supervisor, IS ou ambos?
4. Qual será a regra definitiva do agendamento?
5. Quais registros do prontuário serão visíveis ao empreendimento?
6. O professor verá todas as trilhas do empreendimento ou somente as que criou?
7. O ciclo será sempre composto por quatro etapas fixas ou poderá ser configurado pela IS?

