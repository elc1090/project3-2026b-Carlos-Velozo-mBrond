# F0 · Fundação — spec

**Estado:** aprovado · **Data:** 2026-11-04
**Spec mãe:** [`SGIS_SPEC_MVP_v0.4.md`](../SGIS_SPEC_MVP_v0.4.md), seções 4, 6, 7 e 11 · **Constituição:** [`00-constituicao.md`](../00-constituicao.md)

---

## 1. Objetivo

Garantir as regras que valem para **todo** o sistema, independentemente de feature: nada fica disponível sem login, o admin não acessa dados de negócio, o login não leva a sites externos, e os testes rodam sozinhos a cada mudança. Depois da F0, uma tela nova nasce protegida mesmo que quem a escreveu esqueça de protegê-la.

## 2. Requisitos cobertos

| ID | Prior. | Resumo |
|---|---|---|
| ACE-00 | M | Todo endereço exige login; anônimo vai ao login, inclusive em endereço que não existe |
| ACE-00a | M | Lista fechada de exceções públicas |
| ACE-00b | M | Rota nova nasce protegida; torná-la pública exige marcação explícita |
| RN-14 | — | Toda rota exige login, salvo a lista fechada |
| RN-16 | — | O admin não acessa dados de negócio |
| RNF-01 | M | Segurança (aqui: redirecionamento seguro depois do login) |
| RNF-03 | M | Teste "toda rota exige login" rodando na CI |
| Telas | — | Páginas de erro 403 e 404 (seção 10 da spec mãe) |

**Fica para outras features:** expiração da sessão por inatividade (ACE-03) e o resto de contas são da **F1**; os testes de isolamento de cada recurso (RNF-02) ficam com a feature dona do recurso.

## 3. Regras

### 3.1 Nada sem login
1. Qualquer endereço aberto sem sessão leva à tela de login, guardando o endereço pedido para voltar a ele depois de entrar. Isso vale também para endereços que **não existem**: o visitante não descobre quais páginas o sistema tem.
2. As únicas exceções são as da seção 3.2. Nenhuma outra página, nem a de erro, mostra conteúdo a quem não entrou.
3. Para um usuário **logado**, um endereço que não existe mostra a página de "não encontrado" normalmente.

### 3.2 Lista fechada de exceções públicas
| Exceção | Comportamento |
|---|---|
| Tela de login | Formulário de login |
| Verificação de saúde | Responde só `ok`, sem nenhum dado; serve para o Render saber se o serviço está no ar |
| `robots.txt` | Pede que nenhum buscador indexe o site |
| Arquivos estáticos | Todos os do sistema, que não têm dados (decisão 7.6) |

Qualquer endereço novo fora dessa lista nasce protegido. Acrescentar uma exceção é mudar esta spec.

### 3.3 Admin sem dados de negócio
1. O `/admin/` serve **só para gerenciar contas** (usuários e papéis).
2. Empreendimentos, trilhas, atividades e inscrições **não aparecem** no `/admin/` para ninguém. Esses dados só são vistos e alterados pelas telas do sistema, que aplicam as regras de cada feature (permissões, estados, "nada se apaga"). A única exceção é informar os dados do empreendimento ao criar um empreendedor (F1, 3.3.4); depois disso, o admin não os vê nem altera.
3. A entrada no `/admin/` segue a mesma regra de 3.1: quem não entrou vai para a tela de login do sistema (decisão 7.1).

### 3.4 Login sem redirecionamento para fora
1. Depois de entrar, o usuário volta ao endereço que tinha pedido, **desde que seja do próprio SGIS**.
2. Se o endereço guardado apontar para outro site, ou for inválido, o usuário vai para a página inicial.

### 3.5 Páginas de erro
1. **403 (acesso negado):** página do SGIS, com o cabeçalho do sistema, dizendo que o usuário não tem permissão, e um link para a página inicial. Não diz o que existe naquele endereço.
2. **404 (não encontrado):** página do SGIS, só para usuários logados (anônimos vão ao login, 3.1.1).
3. Em produção, nenhuma página de erro mostra detalhes técnicos.

### 3.6 Testes automáticos a cada mudança (CI)
1. A cada envio de código ao GitHub e a cada pull request, toda a suíte de testes roda e o sistema confere que não há migração pendente.
2. Um teste percorre **todas as rotas registradas** sem sessão e falha se alguma responder fora da lista de exceções. Assim, uma rota nova desprotegida quebra a CI.
3. O resultado aparece no GitHub, junto do commit ou do pull request.

## 4. Critérios de aceite

**Nada sem login**
- **A-01 (ACE-00, RN-14):** *Dado* um visitante sem sessão, *quando* abre uma página interna (por exemplo, a lista de trilhas), *então* vai ao login e, depois de entrar, volta para ela.
- **A-02 (ACE-00):** *Dado* um visitante sem sessão, *quando* abre um endereço que não existe, *então* vai ao login, e não vê a página de "não encontrado".
- **A-03 (ACE-00):** *Dado* um usuário logado, *quando* abre um endereço que não existe, *então* vê a página 404 do SGIS.

**Exceções**
- **A-04 (ACE-00a):** *Dado* um visitante sem sessão, *então* a tela de login, a verificação de saúde, o `robots.txt` e os arquivos estáticos respondem sem pedir login.
- **A-05 (ACE-00a):** *Dado* a verificação de saúde, *então* ela responde só `ok`, sem nenhum dado do sistema.
- **A-06 (ACE-00a):** *Dado* o `robots.txt`, *então* ele pede a todos os buscadores que não indexem nenhuma página.

**Rota nova protegida**
- **A-07 (ACE-00b, RNF-03):** *Dado* o teste que percorre todas as rotas, *quando* alguém acrescenta uma rota sem proteção, *então* o teste falha. *Quando* a rota é marcada explicitamente como pública e acrescentada à lista de exceções, *então* o teste passa.

**Admin**
- **A-08 (RN-16):** *Dado* o admin no `/admin/`, *então* ele vê e gerencia usuários, e não encontra empreendimentos, trilhas, atividades nem inscrições, nem pelo endereço direto.
- **A-09 (RN-16, 3.3.3):** *Dado* um visitante sem sessão, *quando* abre o `/admin/`, *então* vai à tela de login do sistema.

**Login seguro**
- **A-10 (RNF-01):** *Dado* um link de login que manda voltar para outro site, *quando* o usuário entra, *então* vai para a página inicial do SGIS, não para o outro site.
- **A-11 (RNF-01):** *Dado* um link de login que manda voltar para uma página do SGIS, *quando* o usuário entra, *então* vai para essa página.

**Páginas de erro**
- **A-12 (seção 10):** *Dado* um usuário que tenta abrir uma página de outro papel, *então* vê a página 403 do SGIS, com link para o início e sem detalhes técnicos.

**CI**
- **A-13 (RNF-03):** *Dado* um envio de código ao GitHub ou um pull request, *então* os testes e a checagem de migrações rodam sozinhos, e o resultado aparece no GitHub.

## 5. Fora de escopo

- Expiração da sessão por inatividade, troca obrigatória de senha, gestão de contas: **F1**.
- Bloqueio por tentativas de login (ACE-14, prioridade S): **F1**.
- Testes de isolamento de cada recurso (RNF-02): cada feature cuida dos seus.
- Backup, LGPD e termo de privacidade: antes de um piloto com dados reais (seção 11 da spec mãe).

## 6. Situação atual (de [`levantamento-codigo-v0.4.md`](../levantamento-codigo-v0.4.md))

- **Proteção view por view:** cada tela tem `@login_required` ou `@papel_requerido`. Funciona para as telas que existem, mas uma tela nova sem o decorator fica aberta, e um endereço inexistente responde 404 a quem não entrou.
- **Sem verificação de saúde nem `robots.txt`.** O `base.html` já tem `<meta name="robots" content="noindex">`.
- **O `/admin/` mostra empreendimentos, trilhas e inscrições** e permite alterá-los, passando por cima das regras das telas.
- **O login redireciona para qualquer endereço** recebido em `next`, inclusive de outro site (*open redirect*).
- **Páginas 403 e 404 são as padrão do Django**, sem o visual do SGIS.
- **Sem CI:** os testes só rodam quando alguém roda à mão. Há 110 testes.

## 7. Decisões

| # | Pergunta | Decisão |
|---|---|---|
| 7.1 | O `/admin/` tem tela de login própria: exceção pública ou login do sistema? | O admin usa a **tela de login do sistema** e só depois abre o `/admin/`. A lista de exceções continua fechada. |
| 7.2 | O superusuário técnico também perde o acesso a dados de negócio pelo `/admin/`? | Sim, **ninguém** vê empreendimentos, trilhas, atividades nem inscrições pelo `/admin/`. Correções de dados viram tarefas com migração ou comando, revisadas. |
| 7.3 | Endereço da verificação de saúde | `/saude/`, configurado também no Render como *health check path*. |
| 7.4 | Onde a CI roda? | GitHub Actions. |
| 7.5 | A CI impede o merge quando falha? | Sim, quando o merge for por PR (proteção da `main`). Merges diretos pelo responsável continuam possíveis. |
| 7.6 | Todos os arquivos estáticos podem ser públicos, inclusive os do `/admin/`? | Sim. Eles não têm dados, e filtrar arquivo por arquivo exigiria código próprio sem ganho de segurança. |
| 7.7 | O admin pode informar dados de empreendimento? | Só ao criar um empreendedor, porque todo empreendedor tem um empreendimento (F1, decisão 7.8). |
