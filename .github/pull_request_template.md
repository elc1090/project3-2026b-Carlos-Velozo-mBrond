## O que muda

<!-- Uma ou duas frases. -->

**Tipo:** <!-- docs · feat · fix · refactor -->
**Feature:** <!-- ex.: F5 · Execução e validação (specs/F5-execucao/) -->
**Tarefa:** <!-- item do tasks.md -->

Closes #

## Requisitos da spec

<!-- IDs da spec mãe ou do spec.md da feature que este PR implementa ou altera. -->

- 

## Critérios de aceite cobertos

<!-- Cada critério (Dado / Quando / Então) e o teste que o cobre. -->

| Critério | Teste |
|---|---|
|  |  |

## Checklist

- [ ] `spec.md` e `plan.md` da feature estão aprovados *(não se aplica a PR de documentação)*
- [ ] Implementa só o que a spec pede, nada a mais
- [ ] Regra nova ou alterada? A spec foi atualizada antes, neste PR ou em outro já aprovado
- [ ] Controles de acesso têm teste do caso **negado**
- [ ] Testes citam o ID que cobrem
- [ ] `python manage.py test` passa
- [ ] `python manage.py makemigrations --check --dry-run` não acusa migração pendente
- [ ] Migrações novas são reversíveis
- [ ] Nenhum segredo, senha ou dado real no código

## Como testar manualmente

<!-- Papel usado, telas e passos. -->

1. 

## Observações

<!-- Dúvidas, decisões tomadas durante a implementação, pontos para o revisor olhar com atenção. Se usou IA, diga em quê. -->
