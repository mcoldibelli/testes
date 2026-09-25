# P11: Roteiro de TDD, CI/CD e melhoria contínua

Este roteiro diz **o que** o grupo faz. As evidências (commits, capturas, logs) são geradas pelo grupo durante a execução
e registradas na aba Diario da planilha e no Apêndice J do relatório.

## 1. Análise de qualidade: linha de base (antes do TDD)

1. `make sonar-up` e aguardar cerca de 1 minuto.
2. Abrir http://localhost:9000, entrar com `admin` / `admin` e trocar a senha.
3. *My Account > Security > Generate Token* (tipo *Global Analysis Token*). O token não vai para o repositório.
4. `make sonar SONAR_TOKEN=<token>`.
5. Registrar na planilha e no relatório: bugs, vulnerabilidades, code smells, cobertura, duplicação e *Quality Gate*. Capturar a tela do painel.

## 2. Evolução por TDD

**Comportamento escolhido:** aceitar valor com separador de milhar no formulário de OS, como `1.500,00` (risco R-07).
Hoje o sistema recusa esse formato (UT-12 confirma: `"1.500,00"` é inválido).

**Regra nova:** o ponto é separador de milhar somente quando o texto também tem vírgula decimal e os grupos têm 3 dígitos (`1.500,00`, `12.345,6`).
`1500.50` continua aceito como decimal. `1.50,00` continua inválido.

| Etapa | O que fazer | Evidência |
|---|---|---|
| RED | Em `internal/domain/valor_test.go`, trocar a expectativa de `"1.500,00"` para `150000, true` e incluir `"12.345,6"` e `"1.50,00"`. Rodar `make test-unit`. O teste precisa falhar **pelo motivo esperado** (valor recusado). | captura da falha; commit `test: valor com separador de milhar (RED)` |
| GREEN | Mudar só o necessário em `ParseValor` (`internal/domain/valor.go`) para o teste passar. | captura com `ok`; commit `feat: aceita separador de milhar no valor (GREEN)` |
| REFACTOR | Melhorar o código sem mudar o comportamento (ex.: nome da regex, comentário da regra). Rodar **todos** os testes: `make test-unit test-integracao`. | captura com todos aprovados; commit `refactor: organiza parse de valor (REFACTOR)` |

Não crie o teste depois da implementação (manual, seção 9.14). A ordem dos commits no histórico do git é a prova.

## 3. CI/CD: execução com falha e correção

1. Criar uma branch: `git switch -c demo-ci`.
2. Quebrar um teste de forma controlada (ex.: em `TestNovaOrdem_PrazoPorPrioridade`, trocar `4 * time.Hour` por `5 * time.Hour`).
3. `git push` e abrir um pull request. Capturar o pipeline **vermelho** e o log do passo que falhou.
4. Desfazer a mudança, fazer `push` de novo e capturar o pipeline **verde**.
5. Baixar o artefato `resultados-<número>` da execução verde e guardar na pasta 12 do Drive.

## 4. Análise de qualidade: depois das correções e do TDD

Repetir `make sonar SONAR_TOKEN=<token>` e comparar com a linha de base:

| Indicador | Linha de base | Depois | Diferença | Interpretação |
|---|---|---|---|---|
| Bugs | | | | |
| Vulnerabilidades | | | | |
| Code smells | | | | |
| Cobertura (%) | | | | |
| Duplicação (%) | | | | |
| Quality Gate | | | | |

## 5. Plano de melhoria contínua

Preencher com base nos defeitos reais, nas métricas e no SonarQube. Formato:

| Ação | Motivo (dado que originou) | Prioridade | Responsável | Critério de verificação |
|---|---|---|---|---|
| | | | | |
