# P01: Ficha de proposta e aprovação do sistema (Apêndice A)

| Campo | Preenchimento do grupo |
|---|---|
| Turma e grupo | _preencher_ |
| Integrantes | _preencher_ |
| Nome do sistema | Ordens de Serviço (versão 1.0.0) |
| Origem do sistema | Sistema acadêmico desenvolvido pelo grupo (manual, seção 5.2) |
| Link do repositório | _preencher_ |
| Licença/autorização | Código do próprio grupo. Licença: _definir (ex.: MIT)_ |
| Tecnologias principais | Go 1.26, SQLite, HTML (server-side), Postman/Newman, Selenium + pytest, SonarQube, GitHub Actions |
| Como executar | `go run ./cmd/server` e abrir http://localhost:8080 (detalhes no README) |
| Fluxos selecionados | 1. Login com bloqueio por tentativas · 2. Cadastro de cliente (formulário) · 3. Busca de clientes · 4. Abertura de OS com SLA (formulário) · 5. Mudança de status da OS · 6. Lista de OS com filtros · 7. Painel de indicadores |
| Integrações existentes | Interface HTML → serviço → banco SQLite; API JSON → serviço → banco; o mesmo serviço atende a interface e a API |
| Justificativa da escolha | Atende todos os requisitos mínimos da seção 5.3: código-fonte do grupo, execução local, 7 fluxos (2 formulários), persistência, integração entre camadas, dados fictícios e reset do ambiente (`-reset`). As regras têm intervalos e estados (CPF, limites de texto e valor, SLA, máquina de estados), o que permite aplicar particionamento de equivalência, valor limite e tabela de decisão. |
| Riscos de viabilidade | (1) O framework de teste unitário não é JUnit: o pacote `testing` do Go precisa de aprovação (manual, seção 8.3). (2) O Selenium roda em Python porque não há cliente oficial em Go. (3) O SonarQube analisa Go, mas exige Docker na máquina. |
| Decisão do professor | Aprovado / Aprovado com ajustes / Não aprovado |
| Ajustes solicitados | |
| Data da aprovação | |
