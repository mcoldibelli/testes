### Requisito e caso relacionados

RNF-02 / NF-04 (fluxos de CT-06 e CT-16)

### Ambiente e versão

macOS 26.6.2, Google Chrome 154.0.8037.93 (DevTools, modo dispositivo iPhone SE, 375 x 667), sistema 1.0.0 (commit 14c38fa), Go 1.26.5, banco SQLite iniciado com `make reset`

### Pré-condições

Sistema iniciado com `make reset`. Usuário logado como `admin@teste.local`. Chrome com DevTools aberto no modo dispositivo **iPhone SE**.

### Dados utilizados

Nova ordem: cliente Mercado Bom Preço, prioridade ALTA, descrição `Alarme dispara sem motivo`, valor `150,00`.

### Passos para reproduzir

1. Abrir **Ordens de serviço** > **Nova ordem**, preencher os dados acima e clicar em **Abrir ordem**.
2. Ver a lista de ordens que aparece depois da mensagem de sucesso.
3. Abrir **Clientes** e ver a lista de clientes.

### Resultado esperado

As listas cabem na largura da tela (375 px), sem rolagem horizontal da página, como os formulários de login, cliente e ordem.

### Resultado obtido

As tabelas das listas passam da largura da tela e a página inteira rola na horizontal. Na lista de ordens, a coluna Prioridade aparece cortada e as colunas Status, Prazo e Valor ficam fora da tela. Medição com o Chrome em emulação iPhone SE: `/ordens` tem 669 px de largura e `/clientes` tem 680 px, para 375 px de tela. As páginas `/login`, `/`, `/clientes/novo`, `/ordens/nova` e `/ordens/1` têm 375 px.

### Severidade

Baixa

### Prioridade

Baixa

### Evidências

`docs/evidencias/nao-funcionais/NF-04_CT-16.png` (lista de ordens cortada em 375 px)
`docs/evidencias/nao-funcionais/NF-04_largura_375px.txt` (largura de cada página em 375 px)
