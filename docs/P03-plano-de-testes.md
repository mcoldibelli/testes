# P03: Plano de testes

Versão do plano: 1.1 · Data: 05/11/2026 · Responsável: Marcelo A. B. Coldibelli

## Identificação e versão do sistema

Ordens de Serviço, versão 1.0.0, commit de origem `8bfb1c6`; correções e TDD até o commit `f107a8d` (repositório: <https://github.com/mcoldibelli/testes>).

## Objetivo

Verificar se o sistema atende aos requisitos RF-01 a RF-07 e RNF-01 a RNF-05, e mostrar quais riscos, defeitos e melhorias permanecem antes de o sistema ir para usuários.

## Escopo

Os 12 requisitos do P02 e as regras RN-01 a RN-11. Os fluxos são login, cadastro e busca de clientes, abertura de OS, mudança de status, lista de OS com filtros e painel.

## Fora do escopo

O que o P02, seção 3, lista como fora do escopo. Também: teste de carga, teste de invasão e teste em ambiente de produção.

## Níveis e tipos de teste

| Nível | O que verifica | Ferramenta | Quantidade planejada (mínimo do manual) |
|---|---|---|---|
| Unitário | Regras puras do pacote `internal/domain` sem banco nem rede | Go `testing` | 12 (6) |
| Integração | HTTP → serviço → banco SQLite real, com relógio controlado | Go `testing` + `httptest` | 12 |
| Integração/API | Contrato, status HTTP e encadeamento de dados da API JSON | Postman + Newman | 16 (5) |
| Sistema/interface | Fluxos ponta a ponta no navegador | Selenium + pytest | 8 (4) |
| Sistema manual | Casos CT-01 a CT-31 | Navegador + planilha | 31 (24) |
| Aceitação | Cenários AC-01 a AC-04 com pessoa que não fez os testes | Roteiro + planilha | 4 (4) |
| Não funcional | NF-01 a NF-08: desempenho, compatibilidade, segurança básica, usabilidade e confiabilidade | Script Python, DevTools, Selenium | 8 em 5 categorias (6 em 3) |

Estratégia: a maioria dos testes fica nos níveis mais baixos, que são rápidos e estáveis. Os testes de interface cobrem só os fluxos críticos. Os riscos de prioridade Alta são testados primeiro.

## Técnicas

- **Particionamento de equivalência:** CPF (válido, com máscara, dígito errado, letras), e-mail, formato do valor, filtros.
- **Análise de valor limite:** nome (2/3/100/101), descrição (9/10/500/501), valor (-0,01/0,00/50.000,00/50.000,01), telefone (9/10/11/12), motivo (9/10), falhas de login (4/5), prazo (1 s antes, exato, 1 s depois).
- **Tabela de decisão:** 16 combinações de status de origem e destino (UT-08); prazo por prioridade.
- **Casos de uso / fluxo:** ciclo de vida da OS (CT-22) e cenários de aceitação.

## Ambiente e ferramentas

| Item | Versão |
|---|---|
| Sistema operacional | macOS 26.6.2 (Apple M2 Pro) e `ubuntu-latest` no CI |
| Go | 1.26 |
| Python / Selenium / pytest | 3.12+ / 4.49.0 / 8.4.2 |
| Node / Newman | 22 / 6 |
| Navegadores | Chrome 154.0.8037.93, Firefox 156.0.1 |
| SonarQube | Community (imagem Docker `sonarqube:community`) |
| CI | GitHub Actions, `ubuntu-latest` |

## Dados de teste

Somente dados fictícios. `-reset` cria 2 usuários, 3 clientes e 6 OS. Os scripts geram CPF válido e aleatório a cada execução. Não usar dados pessoais reais (manual, seção 15).

## Responsabilidades

| Papel | Integrante | Atividades |
|---|---|---|
| Coordenação e planejamento | Marcelo A. B. Coldibelli | plano, riscos, cronograma, diário, relatório |
| Análise e execução manual | Marcelo A. B. Coldibelli | casos, execução, evidências, defeitos, aceitação |
| Automação e qualidade | Marcelo A. B. Coldibelli | scripts, pipeline, SonarQube, métricas, TDD |

## Critérios de entrada

- Sistema aprovado pelo professor (P01).
- Build sem erro e `make test-unit` aprovado.
- Ambiente restaurado com `make reset`.
- Casos do ciclo revisados na planilha.

## Critérios de saída

- 100% dos casos planejados executados (ou bloqueio justificado).
- Nenhum defeito de severidade Crítica ou Alta aberto; defeitos Média/Baixa abertos listados como risco residual no relatório.
- Todos os requisitos com pelo menos 1 teste executado (cobertura de requisitos = 100%).
- Pipeline aprovado na versão final.

## Critérios de suspensão e retomada

- **Suspender** quando: o sistema não inicia; um defeito bloqueia mais de 30% dos casos do ciclo; ou o ambiente fica inconsistente (dados de execução anterior).
- **Retomar** quando: a correção estiver no repositório, o pipeline estiver aprovado e o ambiente tiver sido restaurado com `make reset`. Na retomada, executar o reteste dos casos afetados e a regressão dos casos de prioridade Alta.

## Cronograma

| Marco (manual, seção 7) | Entrega | Data realizada (histórico do repositório) |
|---|---|---|
| 1 - Fundamentos | grupo, opções de sistema, níveis | 29/09/2026 (`e97db23`) |
| 2 - Planejamento | aprovação, escopo, riscos, este plano | 24/09/2026 (`8bfb1c6`); versão 1.1 em 05/11/2026 |
| 3 - Especificação | catálogo de casos | 24/09/2026 (`8bfb1c6`) |
| 4 - Execução e defeitos | execução manual, issues | 29/09 a 01/10/2026 |
| 5 - Automação | unitários, SonarQube linha de base | 24/09/2026 (scripts); 29/09/2026 (linha de base) |
| 6 - Integração e sistema | Newman, Selenium | 24/09/2026 (scripts); última execução em 05/11/2026 |
| 7 - Aceitação e não funcionais | AC e NF | NF em 01/10/2026; AC-01 a AC-04 e NF-07 não executados até 05/11/2026 |
| 8 - Métricas | aba Metricas interpretada | 05/11/2026 |
| 9 - TDD, CI/CD e melhoria | ciclo TDD, pipeline, 2ª análise | 05/11/2026 |
| Entrega final | Drive completo | data da P2 |

## Riscos do processo

| Risco | Resposta |
|---|---|
| Pouca disponibilidade de um integrante | Papéis acumuláveis; diário semanal |
| Ferramenta não instala no laboratório | Usar computador pessoal (manual, seção 8.4); Selenium Manager baixa o driver sozinho |
| Falta de internet na apresentação | Vídeo de contingência, capturas e logs locais |
| Teste automatizado instável | Espera explícita (`WebDriverWait`), dados aleatórios, reexecução registrada |

## Produtos e comunicação

Produtos P01 a P14 conforme o README, seção 12. Versões parciais no repositório (histórico git) e no Drive, com data no nome do arquivo. Comunicação: trabalho individual; com o professor, pelos canais definidos em aula e no Connect+ (manual, seção 4.4); decisões registradas no diário.
