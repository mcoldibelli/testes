# Sistema de Ordens de Serviço: Projeto P2 de Testes e Qualidade de Software

## 1. Integrantes

| Nome | RA | Papel |
|---|---|---|
| Marcelo A. B. Coldibelli | 24210023 | Coordenação e planejamento; análise e execução manual; automação e qualidade |

Trabalho individual: um integrante acumula os três papéis (manual, seção 4.2). A decisão do professor está no P01.

Turma: B · Grupo: AP1-TIM 26 · Professor: Prof. Dr. Elvio Gilberto da Silva

## 2. Sistema e versão

**Ordens de Serviço**, versão **1.0.0**. Aplicação web para uma empresa de manutenção de sistemas de segurança.
O sistema cadastra clientes, abre ordens de serviço (OS) com prazo calculado pela prioridade, controla o status da OS e mostra um painel com as OS atrasadas.

Origem (manual, seção 5.2): sistema acadêmico desenvolvido pelo grupo.

## 3. Repositório

<https://github.com/mcoldibelli/testes>

## 4. Tecnologias

| Camada | Tecnologia |
|---|---|
| Linguagem e servidor web | Go 1.26 (`net/http`, `html/template`) |
| Banco de dados | SQLite (driver Go puro `modernc.org/sqlite`) |
| Testes unitários e de integração | pacote `testing` do Go, `net/http/httptest` |
| Testes de API | Postman (coleção) e Newman (linha de comando) |
| Testes de sistema/interface | Selenium 4 + pytest (Python) |
| Análise de qualidade | SonarQube Community (Docker) |
| CI/CD | GitHub Actions |
| Defeitos | GitHub Issues |

O Selenium não tem cliente oficial em Go. Por isso, os testes de interface usam Python, que é uma linguagem com cliente oficial.

Arquitetura resumida:

```
navegador ──HTML──┐
Postman  ──JSON───┤→ internal/web (rotas, sessão) → internal/app (casos de uso) → internal/store (SQL) → SQLite
                  │                                         ↓
                  │                                 internal/domain (regras de negócio puras)
```

## 5. Pré-requisitos

- Go 1.26 ou mais novo: <https://go.dev/doc/install>
- Python 3.10 ou mais novo (testes Selenium)
- Node.js 18 ou mais novo (Newman, via `npx`)
- Google Chrome (e Firefox para o teste de compatibilidade)
- Docker (somente para o servidor do SonarQube; com 4 GB de memória no Docker Desktop funciona)
- `make` (já vem no macOS e no Linux; no Windows, use os comandos do `Makefile` diretamente)

## 6. Instalação

```bash
git clone <link-do-repositório>
cd tqs-p2-ordens-servico
go mod download
make e2e-setup        # cria tests/e2e/.venv com Selenium e pytest
```

## 7. Configuração

| Parâmetro | Padrão | Uso |
|---|---|---|
| `-addr` | `:8080` | endereço HTTP |
| `-db` | `dados/ordens.db` | arquivo do banco |
| `-reset` | `false` | apaga o banco e recria os dados fictícios |
| `BASE_URL` (variável) | `http://localhost:8080` | endereço usado pelos testes Selenium e pelo script de desempenho |
| `BROWSER` (variável) | `chrome` | navegador dos testes Selenium (`chrome` ou `firefox`) |
| `HEADLESS` (variável) | `1` | `0` abre o navegador visível durante os testes |

## 8. Banco e dados

O banco é um arquivo SQLite criado na primeira execução. Com o banco vazio, o sistema cria dados fictícios:
2 usuários, 3 clientes e 6 OS abertas.

**Restaurar o ambiente entre execuções:** `make reset` (ou `go run ./cmd/server -reset`).
Faça isso antes de cada ciclo de testes manuais. Os scripts automatizados geram CPF aleatório e podem ser repetidos sem reset.

## 9. Execução

```bash
make run              # ou: go run ./cmd/server
```

Abra <http://localhost:8080>. Para parar: `Ctrl+C` (o servidor termina as requisições em andamento antes de sair).

## 10. Execução dos testes

| Nível | Comando | Precisa do sistema rodando? |
|---|---|---|
| Unitário (UT-01 a UT-12) | `make test-unit` | Não |
| Integração Go (IT-01 a IT-12) | `make test-integracao` | Não (sobe servidor e banco temporários) |
| Cobertura | `make cobertura` | Não |
| API (API-01 a API-16) | `make test-api` | Sim |
| Sistema/interface (ST-01 a ST-08) | `make test-e2e` | Sim |
| Compatibilidade Firefox | `BROWSER=firefox make test-e2e` | Sim |
| Desempenho (NF-01, NF-02) | `python3 tools/medir_desempenho.py listagem` e `... login` | Sim (use `make reset` antes) |
| Análise de qualidade | `make sonar-up` e depois `export SONAR_TOKEN=<token>` e `make sonar` | Não |
| Painel de progresso | `make painel` e abrir http://localhost:8090 | Não |

Os testes Selenium salvam uma captura de tela de cada teste em `tests/e2e/evidencias/`.
Quando um teste falha, eles salvam também o HTML da página e o erro completo.
O script de desempenho grava as medições em `resultados/`.

## 11. Pipeline

Arquivo: `.github/workflows/ci.yml`. Ele roda em todo `push` e `pull request`:
`go vet`, testes Go com `-race` e cobertura, build, Newman e Selenium.
Os resultados (JUnit XML, cobertura, capturas) ficam no artefato `resultados-<número>` de cada execução.

Acesso: aba **Actions** do repositório.

## 12. Localização dos documentos

| Produto | Local |
|---|---|
| P01 Ficha do sistema | `docs/P01-ficha-do-sistema.md` |
| P02 Requisitos, escopo e riscos | `docs/P02-requisitos-escopo-riscos.md` e abas Requisitos/Riscos da planilha |
| P03 Plano de testes | `docs/P03-plano-de-testes.md` |
| P04 Casos, P05 Rastreabilidade, P06 Execuções, P10 Métricas, P14 Diário | `docs/P2_TQS_planilha.xlsx` |
| P07 Defeitos | GitHub Issues, aba Defeitos da planilha e `docs/P07-defeitos.csv` |
| P08 Scripts | `internal/**/*_test.go`, `tests/postman/`, `tests/e2e/` |
| P09 Aceitação e não funcionais | abas Aceitacao e NaoFuncionais da planilha |
| P11 TDD, CI/CD e melhoria | `docs/P11-roteiro-tdd-cicd-qualidade.md` e `docs/evidencias/tdd`, `docs/evidencias/cicd` |
| P12 Relatório final | `docs/P12-relatorio-final.docx` e `.pdf` (gerados por `tools/gerar_relatorio.py`) |
| P13 Apresentação e roteiro | `docs/P13-apresentacao.pptx` e `.pdf` (gerados por `tools/gerar_apresentacao.py`) e `docs/P13-roteiro-de-demonstracao.md` |
| Estrutura do Drive | `make entrega` cria as pastas 00 a 16 em `entrega/` |

Para gerar a planilha de novo (apaga o que foi preenchido): `tools/.venv/bin/python tools/gerar_planilha.py`
(crie antes o venv: `python3 -m venv tools/.venv && tools/.venv/bin/pip install openpyxl==3.1.5`).
Os geradores do relatório e da apresentação também precisam de `python-docx`, `python-pptx` e `matplotlib` nesse venv, e do LibreOffice para gerar os PDFs.

## 13. Credenciais fictícias

| Perfil | E-mail | Senha |
|---|---|---|
| Administrador | `admin@teste.local` | `Admin@123` |
| Técnico | `tecnico@teste.local` | `Tecnico@123` |

Todos os dados são fictícios. Os CPFs dos dados iniciais são números válidos gerados para teste.

## 14. Problemas conhecidos

- As sessões ficam na memória. Ao reiniciar o servidor, todos precisam entrar de novo.
- O bloqueio de login (5 falhas) também fica na memória e é zerado ao reiniciar.
- A lista de clientes e a lista de seleção de clientes na tela de nova OS mostram no máximo 200 clientes.
- Os formulários não têm token CSRF. O cookie `SameSite=Lax` reduz o risco, mas não o elimina.

## 15. Contato do grupo

Marcelo A. B. Coldibelli, GitHub: <https://github.com/mcoldibelli>
