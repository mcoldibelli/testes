# P13: Roteiro de apresentação e demonstração

Tempo de referência do manual (seção 13): exposição de 12 a 15 minutos e até 5 minutos para perguntas.
O professor informa a ordem e o tempo definitivo. O texto de cada slide está nas notas de `P13-apresentacao.pptx`.

## 1. Preparar antes de entrar na sala

Abra três terminais na pasta do projeto, com a branch final:

```bash
make reset          # terminal 1: sistema com dados fictícios
make test-api       # terminal 2: confirme que passa antes da aula
make test-e2e       # terminal 2: confirme que passa antes da aula
```

Deixe abertos no navegador:
- <http://localhost:8080> (entrar com `admin@teste.local` / `Admin@123`)
- Aba **Actions** do repositório, com as execuções do PR #5
- `docs/P2_TQS_planilha.xlsx`, aba Metricas
- `docs/evidencias/execucao/EX-020_CT-20_3.png` (evidência do DEF-02)

## 2. Sequência

| Tempo | Slide | O que falar e mostrar |
|---|---|---|
| 1 min | 1 e 2 | Sistema, objetivo e escopo |
| 2 min | 3 | Principais riscos e estratégia de teste |
| 2 min | 4 e 5 | CT-20, evidência e DEF-02; resultado da execução manual |
| 3 min | 6 | **Demonstração:** `make test-unit` e `make test-api` (dois níveis automatizados) |
| 2 min | 7 e 8 | Aceitação, não funcionais e métricas, com a limitação da cobertura de requisitos |
| 3 min | 9 e 10 | **Demonstração:** `git log` do TDD e execuções do PR #5 na aba Actions; SonarQube |
| 1 min | 11 | Situação do sistema e melhorias propostas |

## 3. Perguntas que o professor pode fazer

Você precisa responder sem ler (manual, seção 14.1):
- Por que `1.500,00` falhou no RED e o que `formatoMilhar` valida?
- Por que a cobertura é 35,4% no CI e 64,0% com `-coverpkg`?
- Por que a aprovação final é 100%, mas a cobertura de requisitos não?
- Qual a diferença entre severidade e prioridade no DEF-02?
- Por que o RNF-04 está como "Não testado"?
- O que foi feito com apoio de IA, e como você validou esse conteúdo?

## 4. Vídeo de contingência (3 a 5 minutos)

Grave com QuickTime Player (Arquivo > Nova Gravação de Tela) ou `Cmd+Shift+5`. Salve em MP4 ou MOV na pasta 14 do Drive.

1. `make reset` e login no sistema.
2. `make test-unit test-integracao`, mostrando o resultado aprovado.
3. Em outro terminal, `make test-api` e `make test-e2e`, mostrando o resultado aprovado.
4. `git log --oneline` com os commits RED, GREEN e REFACTOR.
5. Aba Actions: a execução com falha e a execução aprovada do PR #5.
6. Abertura de uma OS com valor `1.500,00`, mostrando `R$ 1.500,00` na tela.

Sem internet: use o vídeo, as capturas em `docs/evidencias` e os logs em `docs/evidencias/cicd`.
