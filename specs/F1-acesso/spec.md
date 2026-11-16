# F1 · Acesso e contas — spec

**Estado:** aprovado · **Data:** 2026-11-04
**Spec mãe:** [`SGIS_SPEC_MVP_v0.4.md`](../SGIS_SPEC_MVP_v0.4.md), seção 5 (F1) e jornadas J-1 e J-8 · **Constituição:** [`00-constituicao.md`](../00-constituicao.md) · **Depende de:** [`F0-fundacao`](../F0-fundacao/spec.md)

---

## 1. Objetivo

Cada pessoa entra com a própria conta, cai na área do seu papel e cuida da própria senha. A IS cria e mantém as contas de professores e empreendedores sem precisar de e-mail nem de convite; o admin faz o mesmo para todos os papéis. Contas nunca são apagadas, só desativadas.

## 2. Requisitos cobertos

| ID | Prior. | Resumo |
|---|---|---|
| ACE-01 | M | Login por e-mail (sem diferenciar maiúsculas) e senha, com erro genérico |
| ACE-02 | M | Depois do login, a área do papel |
| ACE-03 | M | Logout e expiração da sessão por inatividade |
| ACE-04 | M | A IS cria professor e empreendedor; o admin cria qualquer papel |
| ACE-05 | M | Empreendedor criado junto com o empreendimento |
| ACE-06 | M | Troca de senha obrigatória no primeiro acesso |
| ACE-07 | M | Trocar a própria senha |
| ACE-08 | M | "Esqueci a senha": orientação no login e redefinição pela IS |
| ACE-09 | M | Gestão de contas: listar, editar, desativar e reativar |
| ACE-10 | M | Conta desativada não entra e perde as sessões |
| ACE-11 | M | Ninguém se desativa nem desativa o último admin |
| ACE-12 | M | Senha com os validadores do Django e mínimo de 10 caracteres |
| ACE-13 | M | Primeiro admin por comando; IS inicial por variáveis de ambiente |
| ACE-14 | S | Bloqueio por tentativas |
| RN-01 | — | Um papel por usuário; o empreendedor representa exatamente um empreendimento |
| RN-13 | — | Conta desativada não entra e perde as sessões |

## 3. Regras

### 3.1 Login e sessão
1. Entra-se com **e-mail e senha**. O e-mail vale do mesmo jeito com ou sem maiúsculas, e é sempre guardado em minúsculas, venha a conta de onde vier (tela da IS, `/admin/`, comando de implantação).
2. Qualquer falha (e-mail inexistente, senha errada, conta desativada) mostra a **mesma mensagem**: "e-mail ou senha incorretos". O sistema não revela se a conta existe nem se está desativada.
3. Depois de entrar, o usuário vai para a **página inicial do seu papel** (seção 3.2), ou para a página que tinha pedido antes do login (F0, 3.4).
4. A sessão **expira depois de um tempo sem uso** (2 horas, decisão 7.3); o usuário volta para o login. "Sair" encerra a sessão na hora.

### 3.2 Página inicial por papel
| Papel | Vai para |
|---|---|
| IS | A página inicial da IS, com atalhos para contas, trilhas e inscrições |
| Professor | Suas trilhas |
| Empreendedor | As trilhas do seu empreendimento |
| Admin | A gestão de contas |

Até as features seguintes criarem os painéis de cada papel (F6, F9), a página inicial da IS é a atual, com os atalhos.

### 3.3 Criação de contas
1. A **IS** cria contas de **professor** e de **empreendedor**: nome, e-mail e uma **senha inicial**. A IS nunca cria contas IS nem admin, nem forjando o formulário.
2. O **admin** cria contas de **qualquer papel**.
3. O e-mail é **único**, sem diferenciar maiúsculas: `Maria@x.com` e `maria@x.com` são a mesma conta.
4. Ao criar um **empreendedor**, a IS ou o admin informa também os **dados do empreendimento** dele. Os dois são criados juntos: se um falhar, nenhum é salvo. O empreendimento criado entra na pré-incubação como qualquer empreendimento novo (F4).
5. Toda conta criada por outra pessoa nasce com **troca de senha obrigatória** (3.5).

### 3.4 Senhas
1. Toda senha definida no sistema, por quem quer que seja (criação, redefinição, troca), passa pelos validadores do Django: **mínimo de 10 caracteres**, não pode ser comum, só números, nem parecida com o nome ou o e-mail.
2. Senha nunca aparece em tela depois de salva, nem em mensagem, nem em endereço.

### 3.5 Troca de senha
1. **Pelo próprio usuário**, em "Minha conta": informa a senha atual, a nova e a confirmação. Continua logado depois da troca.
2. **Troca obrigatória:** enquanto a conta estiver marcada para trocar a senha, qualquer página leva à tela de troca; só "Sair" continua disponível. Depois da troca, a marcação some.
3. **"Esqueci a senha":** não há recuperação por e-mail. A tela de login mostra: "Esqueceu a senha? Entre em contato com a Incubadora Social."
4. **Redefinição pela IS:** a IS define uma nova senha para um professor ou empreendedor, e a conta volta a exigir troca no próximo acesso. O admin pode fazer o mesmo para qualquer conta. A redefinição encerra as sessões abertas daquela conta.

### 3.6 Gestão de contas
1. **A IS** vê a lista de **professores e empreendedores**: nome, e-mail, papel, status (ativa ou desativada) e data de criação, com filtro por papel e por status.
2. **A IS** edita **nome e e-mail** dessas contas, redefine a senha (3.5.4), desativa e reativa. O **papel não muda** depois de criado.
3. **O admin** faz o mesmo para **todas** as contas, pelo `/admin/` (F0, 3.3).
4. **Nada é apagado:** uma conta sai de uso sendo desativada.
5. **Conta desativada** não entra e perde as sessões abertas na próxima ação.
6. **Ninguém desativa a si mesmo**, e a **última conta ativa de admin** não pode ser desativada nem perder o papel de admin.
7. Desativar um empreendedor não desativa o empreendimento dele, e vice-versa.

### 3.7 Contas iniciais
1. A **primeira conta de admin** é criada na implantação, por comando, com o e-mail em minúsculas.
2. A **conta inicial da IS** vem das variáveis de ambiente `IS_EMAIL` e `IS_SENHA_INICIAL`, e nasce com troca de senha obrigatória.

## 4. Critérios de aceite

**Login e sessão**
- **A-01 (ACE-01):** *Dado* uma conta `maria@x.com`, *quando* alguém entra com `Maria@X.com` e a senha certa, *então* entra.
- **A-02 (ACE-01, RN-13):** *Dado* senha errada, e-mail inexistente ou conta desativada, *então* a mensagem é a mesma nos três casos e ninguém entra.
- **A-03 (ACE-02):** *Dado* cada papel, *quando* entra sem página pedida, *então* vai para a página inicial do seu papel (3.2).
- **A-04 (ACE-03):** *Dado* um usuário logado, *quando* fica sem usar o sistema por mais que o tempo de expiração, *então* a próxima página pede login de novo.

**Criação de contas**
- **A-05 (ACE-04, J-1):** *Dado* a IS, *quando* cria um professor, *então* a conta existe com o papel professor e troca de senha obrigatória. *Quando* tenta criar uma conta IS ou admin, inclusive forjando o formulário, *então* o sistema recusa.
- **A-06 (ACE-04, ACE-05):** *Dado* o admin, *quando* cria uma conta de qualquer papel, *então* ela é criada com troca de senha obrigatória. *Quando* cria um empreendedor sem os dados do empreendimento, *então* nem a conta nem o empreendimento são criados. *Quando* informa esses dados, *então* os dois são criados, ligados, e depois disso o empreendimento não aparece no `/admin/`.
- **A-07 (ACE-01, 3.3.3):** *Dado* uma conta `maria@x.com`, *quando* alguém tenta criar `MARIA@x.com`, *então* o sistema recusa.
- **A-08 (ACE-05, J-1):** *Dado* a IS, *quando* cria um empreendedor com os dados do empreendimento, *então* os dois são criados, ligados, e o empreendimento entra na pré-incubação. *Quando* os dados do empreendimento são inválidos, *então* nem a conta nem o empreendimento são criados.

**Senhas**
- **A-09 (ACE-12):** *Dado* uma senha de 9 caracteres, comum, só numérica ou parecida com o e-mail, *quando* é definida em qualquer lugar (criação, redefinição, troca), *então* é recusada.
- **A-10 (ACE-07):** *Dado* um usuário logado, *quando* troca a senha com a senha atual certa, *então* a nova vale e ele continua logado. *Com a senha atual errada*, *então* nada muda.
- **A-11 (ACE-06, J-1):** *Dado* uma conta com troca obrigatória, *quando* o usuário entra, *então* toda página leva à troca de senha, exceto "Sair". *Depois de trocar*, *então* usa o sistema normalmente.
- **A-12 (ACE-08):** *Dado* a tela de login, *então* ela mostra a orientação para falar com a IS em caso de esquecimento.
- **A-13 (ACE-08):** *Dado* a IS, *quando* redefine a senha de um empreendedor, *então* a senha antiga deixa de valer, as sessões dele terminam e o próximo acesso exige troca. *Quando* tenta redefinir a senha de uma conta IS ou admin, *então* o sistema recusa.

**Gestão de contas**
- **A-14 (ACE-09):** *Dado* a IS, *então* a lista de contas mostra professores e empreendedores, com os filtros, e não mostra contas IS nem admin.
- **A-15 (ACE-09):** *Dado* a IS, *quando* edita nome e e-mail de um professor, *então* a mudança é salva. *Quando* tenta mudar o papel, inclusive forjando o formulário, *então* o papel não muda.
- **A-16 (ACE-10, J-8):** *Dado* um usuário com sessão aberta, *quando* a IS o desativa, *então* a próxima página o leva ao login e ele não consegue entrar. *Quando* a IS o reativa, *então* ele entra de novo.
- **A-17 (ACE-11, J-8):** *Dado* qualquer usuário, *quando* tenta desativar a si mesmo, *então* o sistema recusa. *Dado* só um admin ativo, *quando* alguém tenta desativá-lo ou tirar seu papel de admin, *então* o sistema recusa.
- **A-18 (ACE-09):** *Dado* qualquer tela de contas, *então* não existe ação de apagar conta.
- **A-19 (ACE-09):** *Dado* um professor ou empreendedor, *quando* tenta abrir a gestão de contas, *então* o acesso é negado.

**Contas iniciais**
- **A-20 (ACE-13):** *Dado* `IS_EMAIL` e `IS_SENHA_INICIAL` definidos numa instalação nova, *então* a conta da IS é criada com o e-mail em minúsculas e troca de senha obrigatória.

## 5. Fora de escopo

- Proteção de todas as rotas, `/admin/` só com contas, redirecionamento seguro depois do login: **F0**.
- Editar os dados do empreendimento, listar e desativar empreendimentos: **F2**. Aqui só entra a criação do empreendimento junto com o empreendedor (ACE-05).
- Inscrição automática na pré-incubação: já existe (signal); a regra de "só se publicada" é da **F4**.
- Recuperação de senha por e-mail e convites: fora do MVP.
- Mais de um representante por empreendimento: fora do MVP.

## 6. Situação atual (de [`levantamento-codigo-v0.4.md`](../levantamento-codigo-v0.4.md))

- **Login** por e-mail e senha, com o e-mail convertido para minúsculas só na tela de login. O `create_user` não converte (só o domínio), então contas do `/admin/` ou do `createsuperuser` podem ter maiúsculas e aí não entram. A mensagem de conta desativada existe no código, mas não é alcançada.
- **Página inicial** única para todos, com atalhos conforme o papel.
- **Sessão** dura 2 semanas (padrão do Django), sem expiração por inatividade.
- **Criação de contas pela IS** (`/usuarios/novo/`): professor e empreendedor, com validação de senha e e-mail único sem diferenciar maiúsculas. Não cria o empreendimento junto.
- **Troca da própria senha** em "Minha conta" (`/conta/senha/`), com senha atual, confirmação e validadores, mantendo a sessão. Veio do repositório de entrega sem spec (exceção ao Art. 1.1); os testes dela entram na revisão desta feature.
- **Não existem:** troca obrigatória, orientação de "esqueci a senha", redefinição pela IS, lista e edição de contas, desativação pelas telas, proteção contra desativar a si mesmo ou o último admin.
- **Senha mínima** de 8 caracteres (padrão do Django); a spec pede 10.
- **Conta inicial da IS** pela migração `usuarios/0002`, sem troca obrigatória. Em produção ela já existe e teve a senha substituída pelo `popular_banco` (exceção E-03).

## 7. Decisões

| # | Pergunta | Decisão |
|---|---|---|
| 7.1 | A ACE-05 precisa dos campos novos do empreendimento (F2). Quem vem antes? | A F1 cria o empreendimento com os campos atuais (nome, tipo, descrição). A F2 acrescenta os novos campos ao mesmo formulário. |
| 7.2 | A IS pode mudar o papel de uma conta? | Não. Papel errado: desativar e criar outra conta. |
| 7.3 | Depois de quanto tempo sem uso a sessão expira? | 2 horas. |
| 7.4 | A página inicial de cada papel muda agora? | Sim: professor vai para as suas trilhas, empreendedor para as trilhas do empreendimento, admin para a gestão de contas; a IS fica na página atual até a F9. |
| 7.5 | Desativar um empreendedor desativa o empreendimento (e vice-versa)? | Não, são ações separadas. Desativar o empreendimento é da F2 (EMP-06). |
| 7.6 | O bloqueio por tentativas (ACE-14) entra agora? | Não. Fica para antes de um piloto com dados reais. |
| 7.7 | A conta da IS que já existe em produção passa a exigir troca de senha? | Sim, a migração marca as contas IS existentes para trocar a senha no próximo acesso. |
| 7.8 | O admin pode criar uma conta de empreendedor? | Sim, informando os dados do empreendimento no formulário de criação do `/admin/`. Depois disso, o admin não vê nem altera o empreendimento. |
