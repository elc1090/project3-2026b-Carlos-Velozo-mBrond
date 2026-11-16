# F3 · Trilhas — spec

**Estado:** Aprovado · **Data:** 2026-10-23
**Spec mãe:** [`SGIS_SPEC_MVP_v0.4.md`](../SGIS_SPEC_MVP_v0.4.md), seção 5 (F3) · **Constituição:** [`00-constituicao.md`](../00-constituicao.md)

---

## 1. Objetivo

Permitir que a IS mantenha as três trilhas de etapa e que professores e a IS criem trilhas personalizadas, cada uma com suas atividades, passando por rascunho, publicação e arquivamento. É a base das features seguintes: a inscrição (F4) e a execução (F5) dependem de existir trilha publicada com atividades.

## 2. Requisitos cobertos

| ID | Prior. | Resumo |
|---|---|---|
| TRL-01 | M | Dois tipos: trilha de etapa (IS, uma por etapa) e trilha personalizada |
| TRL-02 | M | Professor ou IS cria trilha personalizada: título, descrição e atividades |
| TRL-03 | M | IS mantém a trilha de cada etapa |
| TRL-04 | M | Campos da atividade |
| TRL-05 | M | Estados rascunho → publicada → arquivada |
| TRL-06 | M | Editar trilha publicada |
| TRL-07 | M | Quem edita |
| TRL-08 | S | Reordenar atividades |
| TRL-10 | M | Quem vê trilhas |
| RN-08 | — | Exatamente uma trilha de etapa por etapa |
| RN-10 | — | Atividade e trilha com progresso são arquivadas, nunca apagadas |

**Não cobertos aqui:** TRL-09 (duplicar, prioridade C) fica para depois.

## 3. Regras

### 3.1 Tipos de trilha
1. Uma **trilha de etapa** pertence a uma etapa: Pré-incubação, Incubação ou Desincubação. A dona é a IS.
2. Uma **trilha personalizada** não pertence a nenhuma etapa. O dono é quem a criou: um professor ou a IS.
3. O tipo, a etapa e o dono são definidos pelo sistema no momento da criação e **nunca mudam**.

### 3.2 Trilhas de etapa
1. Existem **sempre exatamente três** trilhas de etapa, uma por etapa. O sistema as cria; **a IS não cria nem arquiva trilhas de etapa**, apenas as edita e publica.
2. Elas nascem em **rascunho**, sem atividades, exceto a de Pré-incubação, que já existe hoje (ver 6).
3. Qualquer pessoa com papel IS pode editar as trilhas de etapa: a dona é "a IS", não um usuário específico.

### 3.3 Trilhas personalizadas
1. Professores e a IS criam trilhas personalizadas. Cada um pode ter várias.
2. Uma trilha personalizada criada pela IS **não é uma trilha de etapa**: os empreendimentos só entram nela por inscrição, como em qualquer trilha personalizada.
3. Toda trilha personalizada nasce em **rascunho**.
4. O dono edita, publica e arquiva a sua trilha.
5. **A IS tem plenos poderes sobre as trilhas personalizadas de professores**, como se fosse a dona: edita, publica e arquiva, com as mesmas regras de estado do dono (3.5). O único cuidado extra é uma **confirmação**: antes de qualquer alteração numa trilha de professor, a IS vê qual professor é o dono e confirma que quer alterar.
6. O dono continua sendo o professor: é ele quem **valida** as atividades (RN-04). Os poderes da IS são sobre a **edição** da trilha, não sobre a validação.
7. Uma trilha personalizada de um professor só é editada pelo próprio professor ou pela IS. Outro professor nunca edita.

### 3.4 Atividades
1. Campos: título (obrigatório), descrição, tipo (Leitura, Link ou Tarefa), endereço, obrigatória (padrão sim), exige validação (padrão sim), prazo e ordem.
2. O **endereço** é obrigatório quando o tipo é Link e deve ser um endereço web válido. Nos outros tipos é opcional.
3. **Prazo:** fixo (uma data), em dias após a inscrição, ou sem prazo. Nunca os dois ao mesmo tempo. Dias após a inscrição é um número inteiro maior que zero.
4. A **ordem** define a sequência em que o empreendimento vê as atividades. Atividade nova entra no fim.

### 3.5 Estados da trilha

| De | Para | Quem | Condição |
|---|---|---|---|
| Rascunho | Publicada | Dono ou IS | Pelo menos uma atividade ativa |
| Publicada | Arquivada | Dono ou IS | Só trilhas personalizadas, e sem inscrição ativa ou pausada |

1. Não há volta: publicada não volta a rascunho, e arquivada não volta a publicada.
2. **Rascunho:** tudo é editável. Atividades podem ser criadas, editadas e apagadas.
3. **Publicada:** só se pode
   - ajustar os textos da trilha (título, descrição);
   - ajustar os textos das atividades existentes (título, descrição, endereço);
   - acrescentar atividades **no fim**;
   - arquivar uma atividade.

   Tipo, obrigatoriedade, exigência de validação e prazo de uma atividade existente **não mudam** depois da publicação, porque já valem para empreendimentos inscritos.
4. **Arquivada:** nada é editável. A trilha continua visível para quem já a via.
5. Uma trilha ou atividade **nunca é apagada** depois de publicada. Atividade arquivada some da trilha para novas inscrições, mas continua no histórico de quem a fez.
6. Reordenar (TRL-08) só é possível enquanto a trilha está em rascunho.
7. Uma trilha personalizada com inscrição ativa ou pausada **não pode ser arquivada**. O dono pede à IS para concluir ou cancelar as inscrições antes.

### 3.6 Quem vê

| Quem | Vê |
|---|---|
| IS | Todas as trilhas, em qualquer estado |
| Professor | As suas (em qualquer estado); as trilhas de etapa (leitura); em leitura, as outras trilhas personalizadas, publicadas, em que algum empreendimento que ele atende esteja ou tenha estado inscrito |
| Empreendedor | Só as trilhas em que o seu empreendimento está ou esteve inscrito (nunca rascunho) |
| Admin | Nenhuma (RN-16) |

"Professor que atende" segue a definição da spec mãe (seção 2).

## 4. Critérios de aceite

**Tipos e dono**
- **A-01 (TRL-01, TRL-02):** *Dado* um professor ou a IS, *quando* cria uma trilha, *então* ela é uma trilha personalizada, quem a criou é o dono, e ela nasce em rascunho.
- **A-02 (TRL-01, TRL-03):** *Dado* o sistema instalado, *então* existem exatamente três trilhas de etapa, uma para cada etapa.
- **A-03 (TRL-02, RN-08):** *Dado* a IS, *quando* cria uma nova trilha, *então* ela é personalizada e **não** se torna trilha de etapa; continuam existindo só três trilhas de etapa. *Quando* a IS tenta arquivar uma trilha de etapa, *então* o sistema recusa.
- **A-04 (TRL-01):** *Dado* um formulário de trilha enviado com etapa, dono ou estado forjados, *então* esses valores são ignorados e o sistema usa os seus (personalizada, quem enviou, rascunho).

**Atividades**
- **A-05 (TRL-04):** *Dado* uma atividade do tipo Link sem endereço, ou com endereço inválido, *quando* é salva, *então* o sistema recusa.
- **A-06 (TRL-04):** *Dado* uma atividade com prazo fixo e prazo em dias ao mesmo tempo, *quando* é salva, *então* o sistema recusa.
- **A-07 (TRL-04):** *Dado* uma atividade criada sem informar obrigatoriedade nem validação, *então* ela é obrigatória e exige validação.
- **A-08 (TRL-04):** *Dado* uma trilha com atividades, *quando* uma nova é acrescentada, *então* ela fica por último.

**Estados**
- **A-09 (TRL-05):** *Dado* uma trilha em rascunho sem atividades, *quando* o dono tenta publicar, *então* o sistema recusa. Com uma atividade, publica.
- **A-10 (TRL-05):** *Dado* uma trilha publicada, *então* ela não volta a rascunho.
- **A-11 (TRL-06):** *Dado* uma trilha publicada, *quando* o dono altera o título de uma atividade, *então* a alteração é salva. *Quando* tenta alterar o tipo, a obrigatoriedade, a validação ou o prazo dela, *então* o sistema recusa.
- **A-12 (TRL-06):** *Dado* uma trilha publicada, *quando* o dono acrescenta uma atividade, *então* ela entra no fim.
- **A-13 (RN-10):** *Dado* uma trilha publicada, *quando* o dono tenta apagar uma atividade, *então* o sistema só oferece arquivar.
- **A-14 (TRL-05):** *Dado* uma trilha arquivada, *quando* alguém tenta editá-la, *então* o sistema recusa.
- **A-15 (TRL-05):** *Dado* uma trilha personalizada com uma inscrição ativa ou pausada, *quando* o dono tenta arquivá-la, *então* o sistema recusa e explica o motivo.

**Quem edita**
- **A-16 (TRL-07):** *Dado* um professor, *quando* tenta editar, publicar ou arquivar a trilha de outro professor, *então* o acesso é negado (403).
- **A-17 (TRL-07):** *Dado* um professor, *quando* tenta editar uma trilha de etapa ou uma trilha personalizada da IS, *então* o acesso é negado.
- **A-18 (TRL-07):** *Dado* a IS, *quando* tenta editar, publicar ou arquivar uma trilha personalizada de um professor, *então* vê antes uma confirmação com o nome do professor dono; só depois de confirmar a alteração é feita. *Quando* cancela a confirmação, *então* nada muda.
- **A-18b (RN-04):** *Dado* uma trilha de professor editada pela IS, *então* o dono continua sendo o professor, e só ele valida as atividades dela.
- **A-19 (TRL-07):** *Dado* um empreendedor ou o admin, *quando* tenta abrir qualquer tela de edição de trilha, *então* o acesso é negado.

**Quem vê**
- **A-20 (TRL-10):** *Dado* uma trilha personalizada em rascunho, *então* só o dono e a IS a veem.
- **A-21 (TRL-10):** *Dado* o empreendimento A inscrito na trilha do professor X e na do professor Y, *quando* X abre a trilha de Y, *então* a vê em leitura. *Dado* o professor Z, que não atende A, *quando* tenta abrir a trilha de Y, *então* o acesso é negado.
- **A-22 (TRL-10):** *Dado* um empreendedor, *quando* tenta abrir uma trilha em que seu empreendimento nunca foi inscrito, *então* o acesso é negado.

**Reordenar (S)**
- **A-23 (TRL-08):** *Dado* uma trilha em rascunho, *quando* o dono muda a ordem das atividades, *então* a nova ordem é a que o empreendimento verá. *Dado* uma trilha publicada, *então* a ordem não pode ser mudada.

## 5. Fora de escopo

- Inscrição em trilha, avançar etapa e a regra "inscrição só em trilha publicada": **F4**.
- Execuções, progresso e o que acontece com quem já está inscrito quando uma atividade é acrescentada ou arquivada: **F5**.
- Duplicar trilha (TRL-09).
- Etapas internas, vídeos, questionários e upload de arquivos.

## 6. Situação atual

**Atualizada em 2026-10-28, com a F3 concluída** (`main` em `1dea3a8`). Todos os critérios de aceite da seção 4 têm teste passando em `trilhas/test_f3.py`.

- A trilha tem `etapa` (vazia nas personalizadas) e `status` (rascunho, publicada, arquivada). As três trilhas de etapa existem e não têm usuário dono: a dona é a IS.
- Atividades (`AtividadeTrilha`) com tipo, endereço, obrigatoriedade, exigência de validação, prazo e ordem.
- Professor e IS criam trilhas personalizadas; o dono e a IS editam, publicam e arquivam; atividades são criadas, editadas, apagadas (só em rascunho), arquivadas e reordenadas (só em rascunho), tudo pela interface.
- Todas as regras de "quem pode" e "quando pode" estão em `trilhas/regras.py`.
- A IS só altera trilha de professor depois de confirmar (formulário com caixa de confirmação ou página intermediária), checado no servidor.
- Listas por papel: o professor vê as suas, as de etapa e as de outros nos empreendimentos que atende; a IS filtra por tipo e estado; o empreendedor vê as inscritas.

**Como foi feita a conversão** (migrações `trilhas/0006` a `0008`, T1): a antiga trilha de pré-incubação virou a trilha de etapa Pré-incubação, publicada, sem perder inscrições; as trilhas personalizadas existentes ficaram publicadas; as de Incubação e Desincubação foram criadas em rascunho.

**O que ficou para outras features:**
- Inscrever só em trilha publicada e avançar etapa: **F4**.
- Execuções e progresso das atividades: **F5**.
- Duplicar trilha (TRL-09, prioridade C): não implementado.

## 7. Decisões

| # | Pergunta | Decisão |
|---|---|---|
| 7.1 | A IS pode criar ou arquivar trilhas de etapa? | Não. São fixas: o sistema cria as três, e a IS só edita e publica. A IS pode criar trilhas **personalizadas** à vontade. |
| 7.2 | A trilha de pré-incubação publicada sem atividades pode existir? | Sim, só como exceção da conversão. A partir daí vale a regra de publicação. |
| 7.3 | Pode arquivar trilha personalizada com inscrições ativas ou pausadas? | Não. É preciso concluir ou cancelar as inscrições antes. |
| 7.4 | Trilhas personalizadas que já existem viram publicadas ou rascunho? | Publicadas. |
| 7.5 | O endereço da atividade Link pode ser editado depois da publicação? | Sim, como texto. |
| 7.6 | A IS pode editar trilhas personalizadas de professores? | Sim, com plenos poderes de edição, como se fosse a dona (3.3.5). |
| 7.7 | O que é o "cuidado extra" da IS ao editar trilha de professor? | Só uma confirmação antes de alterar, mostrando de qual professor é a trilha. |
