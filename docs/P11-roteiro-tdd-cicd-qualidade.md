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

### Registro da execução (Apêndice J)

| Etapa | Evidência e descrição |
|---|---|
| Comportamento escolhido | Aceitar `1.500,00` e `12.345,6` no valor da OS (risco R-07, requisito RF-04). |
| RED: teste falhando | Commit `a31aa49`. `ParseValor("1.500,00")` e `ParseValor("12.345,6")` devolvem "use o formato 1234,56". Evidência: [`TDD-1_RED.txt`](evidencias/tdd/TDD-1_RED.txt). |
| GREEN: implementação mínima | Commit `5568311`. Nova regex de milhar em `ParseValor`; o ponto é removido antes da validação existente. Evidência: [`TDD-2_GREEN.txt`](evidencias/tdd/TDD-2_GREEN.txt). |
| REFACTOR: melhoria | Commit `f107a8d`. Regexes agrupadas, `formatoValor` renomeada para `formatoDecimal`, regra documentada. `make test-unit test-integracao`: 25 aprovados, 0 reprovados. Evidência: [`TDD-3_REFACTOR.txt`](evidencias/tdd/TDD-3_REFACTOR.txt). |
| Verificação no sistema | Formulário real em servidor iniciado: `1.500,00` grava 150000 centavos e a tela mostra `R$ 1.500,00`; `1.50,00`, `abc`, `10,555` e `50.000,01` são recusados e não gravam OS. Evidência: [`TDD-4_verificacao_no_sistema.txt`](evidencias/tdd/TDD-4_verificacao_no_sistema.txt). |
| Commits relacionados | `a31aa49`, `5568311`, `f107a8d`, na branch `entrega-final`. |

## 3. CI/CD: execução com falha e correção

1. Criar uma branch: `git switch -c demo-ci`.
2. Quebrar um teste de forma controlada (ex.: em `TestNovaOrdem_PrazoPorPrioridade`, trocar `4 * time.Hour` por `5 * time.Hour`).
3. `git push` e abrir um pull request. Capturar o pipeline **vermelho** e o log do passo que falhou.
4. Desfazer a mudança, fazer `push` de novo e capturar o pipeline **verde**.
5. Baixar o artefato `resultados-<número>` da execução verde e guardar na pasta 12 do Drive.

### Registro da execução (Apêndice J)

| Etapa | Evidência e descrição |
|---|---|
| Pipeline: arquivo e gatilho | `.github/workflows/ci.yml`; gatilhos `push` e `pull_request`. Etapas: preparação, `go vet`, testes Go com `-race` e cobertura, build, Newman, Selenium e publicação do artefato. |
| Pipeline: execução com falha | PR [#5](https://github.com/mcoldibelli/testes/pull/5), commit `a049d06`, com o prazo da prioridade CRITICA trocado para 5 h no teste. [Run 42134250857](https://github.com/mcoldibelli/testes/actions/runs/42134250857) (push) e [run 42134260225](https://github.com/mcoldibelli/testes/actions/runs/42134260225) (PR) falharam no passo "Testes unitários e de integração (Go)", em `TestNovaOrdem_PrazoPorPrioridade`. Evidência: [`CI-1_FALHA_run-42134250857.txt`](evidencias/cicd/CI-1_FALHA_run-42134250857.txt). |
| Pipeline: execução aprovada | Commit `2bc5bda` desfaz a mudança. [Run 42134677760](https://github.com/mcoldibelli/testes/actions/runs/42134677760) (push) e [run 42134685386](https://github.com/mcoldibelli/testes/actions/runs/42134685386) (PR) aprovados. Artefato `resultados-15`: 25 testes Go, 16 de API e 8 de interface aprovados; cobertura 35,4%. Evidência: [`CI-2_APROVADO_run-42134677760.txt`](evidencias/cicd/CI-2_APROVADO_run-42134677760.txt). |
| Aprendizados e melhoria | O pipeline parou a mudança errada sem ação manual, e o log aponta o teste e o valor esperado. As anotações do CI mostram duas ações futuras: atualizar as actions em Node.js 20 e o rótulo `ubuntu-latest` (seção 5). |

## 4. Análise de qualidade: depois das correções e do TDD

Repetir `make sonar` (com `SONAR_TOKEN` no ambiente) e comparar com a linha de base.

Linha de base: 29/09/2026, commit `e97db23`, SonarQube Community Build 26.9, perfil *Sonar way*, 1.629 linhas de código.
Evidência: [`evidencias/SONAR_LINHA-DE-BASE_2026-09-29.png`](evidencias/SONAR_LINHA-DE-BASE_2026-09-29.png).
Aviso da análise: a versão do Python não foi informada (`sonar.python.version`); afeta só os 2 scripts Selenium.

| Indicador | Linha de base | Depois | Diferença | Interpretação |
|---|---|---|---|---|
| Bugs | 0 | 0 | 0 | Sem bugs novos depois das correções e do TDD. |
| Vulnerabilidades | 0 (0 security hotspots) | 0 (0 security hotspots) | 0 | Sem achados. A análise estática não detecta a falta de token CSRF (seção 5). |
| Code smells | 0 | 0 | 0 | As correções não aumentaram a dívida técnica medida. |
| Cobertura (%) | 33,8 | 37,8 | +4,0 | Subiu com IT-11, IT-12 e os testes das correções. O valor é baixo porque conta cada pacote só com os testes dele (seção 5). |
| Duplicação (%) | 0,0 | 0,0 | 0 | Sem código duplicado. |
| Quality Gate | Passed | Passed | igual | O código continua aprovado no perfil *Sonar way*. |

A cobertura do SonarQube (33,8%) conta linhas. O `go tool cover` (31,8%) conta instruções. Por isso os dois números são diferentes.

Depois: 05/11/2026, commit `f107a8d`, SonarQube Community Build 26.11, perfil *Sonar way*, 1.642 linhas de código. `go tool cover`: 35,4%.
Evidências: [`SONAR_DEPOIS_2026-11-05.png`](evidencias/sonar/SONAR_DEPOIS_2026-11-05.png) e [`SONAR_DEPOIS_2026-11-05.txt`](evidencias/sonar/SONAR_DEPOIS_2026-11-05.txt).

Limitação da comparação: o contêiner da linha de base não existia mais em 05/11/2026. A segunda análise usou uma instância nova e uma versão mais recente do SonarQube (26.9 e 26.11). Os valores da linha de base vêm do registro de 29/09/2026.

## 5. Plano de melhoria contínua

Ações baseadas nos defeitos reais, nas métricas, no SonarQube e nas anotações do CI.

| Ação | Motivo (dado que originou) | Prioridade | Responsável | Critério de verificação |
|---|---|---|---|---|
| Executar AC-01 a AC-04 e NF-07 com pessoa que não fez os testes | Cobertura de requisitos de 91,7%: RNF-04 não testado; nenhum cenário de aceitação executado | Alta | Marcelo A. B. Coldibelli | Decisão preenchida nos 4 cenários, NF-07 com resultado, cobertura de requisitos de 100% |
| Incluir token CSRF nos formulários | README, seção 14: sem token CSRF; o `SameSite=Lax` só reduz o risco | Alta | Marcelo A. B. Coldibelli | Novo teste de integração: POST sem token devolve 403 |
| Manter o bloqueio de login depois de reinício | README, seção 14: o bloqueio fica na memória e é zerado ao reiniciar (risco R-05) | Média | Marcelo A. B. Coldibelli | Novo teste de integração: e-mail bloqueado continua bloqueado depois de reiniciar |
| Medir cobertura com `-coverpkg=./...` no Makefile e no CI | Cobertura de 35,4% por pacote contra 64,0% com `-coverpkg`; `store` e `app` aparecem com 0% | Média | Marcelo A. B. Coldibelli | `cobertura.txt` do CI e SonarQube mostram `store` e `app` acima de 0% |
| Automatizar CT-05, CT-12 e CT-31 | Taxa de automação de 89,3% (25 de 28 candidatos) | Média | Marcelo A. B. Coldibelli | Taxa de automação de 100%, com pipeline aprovado |
| Atualizar as actions e fixar a versão do runner | Anotações do CI: Node.js 20 obsoleto e migração de `ubuntu-latest` | Baixa | Marcelo A. B. Coldibelli | Execução do pipeline sem essas duas anotações |
| Informar `sonar.python.version` | Aviso nas duas análises do SonarQube | Baixa | Marcelo A. B. Coldibelli | Análise sem esse aviso |
