# F2 · Empreendimentos — spec

**Estado:** aprovado · **Data:** 2026-11-04
**Spec mãe:** [`SGIS_SPEC_MVP_v0.4.md`](../SGIS_SPEC_MVP_v0.4.md), seção 5 (F2) · **Constituição:** [`00-constituicao.md`](../00-constituicao.md) · **Depende de:** [`F1-acesso`](../F1-acesso/spec.md) (criação do empreendimento junto com o empreendedor)

---

## 1. Objetivo

Dar à IS o cadastro completo dos empreendimentos e a cada pessoa envolvida uma página de perfil do empreendimento, com os dados, a etapa atual e as trilhas. O perfil é o lugar onde as features seguintes acrescentam os níveis por eixo (F8) e o prontuário (F7).

## 2. Requisitos cobertos

| ID | Prior. | Resumo |
|---|---|---|
| EMP-01 | M | Cadastro e edição pela IS: nome, tipo, descrição, contato |
| EMP-02 | M | Um único representante por empreendimento |
| EMP-03 | M | Lista da IS com filtros: ativos, desativados, por etapa atual |
| EMP-04 | M | Perfil do empreendimento |
| EMP-05 | M | Quem vê o perfil |
| EMP-06 | S | Desativar sem apagar histórico; o representante perde o acesso |
| RN-01, RN-02 | — | Empreendedor representa exatamente um empreendimento; empreendimento tem um único representante |
| RN-03 | — | Sem supervisão: o professor só se relaciona com o empreendimento pelas trilhas |

## 3. Regras

### 3.1 Dados do empreendimento
1. Campos: **nome** (obrigatório), **tipo** (MEI, Associação, Coletivo ou Outro; obrigatório), **descrição**, **e-mail de contato** e **telefone de contato** (opcionais).
2. O e-mail de contato é do empreendimento e **não** é usado para login; o login é o e-mail da conta do representante (F1).

### 3.2 Criação e representante
1. Um empreendimento **só é criado junto com o seu representante**, na criação da conta de empreendedor pela IS ou pelo admin (F1, ACE-05). Não existe empreendimento sem representante. Os campos desta seção entram no mesmo formulário.
2. Cada empreendimento tem **exatamente um representante**, que é uma conta com papel empreendedor.
3. Cada empreendedor representa **exatamente um** empreendimento.
4. O representante **não muda** pelas telas do MVP. Se a pessoa mudar, a IS desativa a conta antiga e o empreendimento continua com ela como representante; a troca de representante fica para depois.

### 3.3 Edição
1. Só a **IS** edita os dados do empreendimento (3.1). O representante e os professores só leem.
2. O representante não é trocado pela edição (3.2.4).

### 3.4 Lista da IS
1. Mostra nome, tipo, representante, etapa atual e situação (ativo ou desativado).
2. Filtros combináveis: **ativos / desativados** e **etapa atual** (Pré-incubação, Incubação, Desincubação, sem etapa).
3. A **etapa atual** é calculada a partir das inscrições (F4, INS-05), nunca guardada.

### 3.5 Perfil do empreendimento
1. Mostra: **dados** (3.1), **representante**, **etapa atual**, **trilhas em que está ou esteve inscrito**, com o status de cada inscrição.
2. As seções de **níveis por eixo** (F8) e **prontuário** (F7) entram no perfil quando essas features forem feitas.
3. **Quem vê** (EMP-05): a IS vê o perfil de todos; um professor vê o perfil dos empreendimentos que **atende** (inscritos, agora ou antes, em alguma trilha dele); o representante vê o do **próprio** empreendimento. O admin não vê (RN-16).
4. Quem não pode ver recebe acesso negado (403), pela lista e pelo endereço direto.

### 3.6 Desativação (prioridade S)
1. A **IS** desativa e reativa um empreendimento. Nada é apagado: dados, inscrições e histórico continuam.
2. **Empreendimento desativado:**
   - não pode receber novas inscrições (já é assim hoje);
   - o **representante não consegue entrar** no sistema enquanto o empreendimento estiver desativado, com a mesma mensagem genérica de login da F1; a conta dele continua ativa e volta a entrar quando o empreendimento for reativado;
   - as inscrições existentes ficam como estão.
3. Desativar o empreendimento não desativa a conta do representante, e vice-versa (F1, decisão 7.5).

## 4. Critérios de aceite

**Dados e criação**
- **A-01 (EMP-01):** *Dado* a IS criando um empreendedor (F1), *então* o formulário pede também nome, tipo, descrição, e-mail e telefone de contato do empreendimento, e todos são salvos.
- **A-02 (EMP-01):** *Dado* um tipo fora da lista, ou um e-mail de contato inválido, *quando* a IS salva, *então* o sistema recusa e nada é criado.
- **A-03 (EMP-01):** *Dado* a IS, *quando* edita o nome e o telefone de um empreendimento, *então* a mudança é salva. *Dado* um professor ou o representante, *quando* tenta editar, *então* o acesso é negado.

**Representante**
- **A-04 (EMP-02, RN-01, RN-02):** *Dado* um empreendedor que já representa um empreendimento, *então* não há como ligá-lo a um segundo. *Dado* uma conta que não é de empreendedor, *então* ela não pode ser representante.
- **A-05 (3.2.4):** *Dado* a edição do empreendimento, mesmo forjando o formulário, *então* o representante não muda.

**Lista**
- **A-06 (EMP-03):** *Dado* empreendimentos ativos e desativados, em etapas diferentes, *quando* a IS filtra por "desativados" ou por uma etapa, *então* aparecem só os que correspondem, e os filtros se combinam.
- **A-07 (EMP-03, INS-05):** *Dado* um empreendimento que avançou para a Incubação (F4), *então* a lista mostra "Incubação" como etapa atual, sem que nenhum campo de etapa tenha sido gravado.

**Perfil**
- **A-08 (EMP-04):** *Dado* um empreendimento com inscrições, *quando* a IS abre o perfil, *então* vê os dados, o representante, a etapa atual e as trilhas com o status de cada inscrição.
- **A-09 (EMP-05):** *Dado* o professor X, dono de uma trilha em que o empreendimento A esteve inscrito, *então* X vê o perfil de A, mesmo com a inscrição encerrada. *Dado* o professor Z, que nunca atendeu A, *então* recebe 403.
- **A-10 (EMP-05):** *Dado* o representante de A, *então* vê o perfil de A e recebe 403 no perfil de B. *Dado* o admin, *então* recebe 403 em qualquer perfil.

**Desativação (S)**
- **A-11 (EMP-06):** *Dado* um empreendimento desativado, *então* ele continua no banco com as inscrições, a IS o vê no filtro "desativados", e ele não aparece na lista de empreendimentos para inscrever.
- **A-12 (EMP-06):** *Dado* o representante de um empreendimento desativado, *quando* tenta entrar, *então* não entra e vê a mensagem genérica de login. *Quando* a IS reativa o empreendimento, *então* ele volta a entrar.

## 5. Fora de escopo

- Criação da conta do empreendedor e a regra "criados juntos": **F1** (ACE-05). A F2 só acrescenta os campos ao formulário.
- Níveis por eixo e prontuário no perfil: **F8** e **F7**.
- Progresso das trilhas no perfil: **F5**.
- Troca de representante e mais de um representante por empreendimento: fora do MVP.

## 6. Situação atual (de [`levantamento-codigo-v0.4.md`](../levantamento-codigo-v0.4.md))

- O model tem nome, **tipo como texto livre**, descrição, `desativado_em` e o **representante** (FK). Faltam e-mail e telefone de contato.
- **Sobra do modelo antigo:** o campo `usuario_professor_supervisor`, que a v0.4 descartou (RN-03). Aparece no admin e no `popular_banco`, e precisa sair.
- Nada impede um empreendedor de representar dois empreendimentos, nem uma conta que não é de empreendedor de ser representante.
- **Não há tela** de empreendimentos: lista, perfil e edição só existem no `/admin/`, que a F0 vai fechar para dados de negócio.
- Empreendimento desativado já não pode ser inscrito; o representante dele continua entrando normalmente.
- Os empreendimentos que já existem têm o tipo em texto livre ("alimentos", "Artesanato / Textil").

## 7. Decisões

| # | Pergunta | Decisão |
|---|---|---|
| 7.1 | O que fazer com o tipo em texto livre dos empreendimentos que já existem? | A migração converte para "Outro" e acrescenta o texto antigo ao fim da descrição. |
| 7.2 | O representante pode ser trocado no MVP? | Não. A troca de representante fica para depois do MVP. |
| 7.3 | Desativar o empreendimento pausa as inscrições ativas? | Não; as inscrições ficam como estão. A IS pausa ou cancela à mão se quiser. |
| 7.4 | Desativar o empreendimento tira o acesso do representante (pendência 7 da spec mãe)? | Sim, como em 3.6.2: o representante não entra enquanto o empreendimento estiver desativado; a conta dele continua ativa. |
| 7.5 | O que fazer com dados de produção fora de RN-01? | Cada empreendedor fica com **exatamente um** empreendimento. A produção é consultada antes da migração; havendo casos, a IS diz qual é o certo, e a correção vira um comando revisado (F0, decisão 7.2). |
