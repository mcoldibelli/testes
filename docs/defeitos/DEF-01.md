### Requisito e caso relacionados

RF-03 / CT-14

### Ambiente e versão

macOS 26.6.2, Firefox 156.0.1, sistema 1.0.0 (commit 8bfb1c6), Go 1.26.5, banco SQLite iniciado com `make reset`

### Pré-condições

Sistema iniciado com `make reset`. Usuário logado como `admin@teste.local`. O cliente "Mercado Bom Preço" (CPF 11144477735) existe nos dados iniciais.

### Dados utilizados

Termo de busca: `111.444.777-35`

### Passos para reproduzir

1. Abrir **Clientes**.
2. Digitar `111.444.777-35` no campo de busca.
3. Clicar em **Buscar**.

### Resultado esperado

A lista mostra somente "Mercado Bom Preço".

### Resultado obtido

A tela mostra "Nenhum cliente encontrado.". A busca pelo mesmo CPF sem máscara (`11144477735`) encontra o cliente (CT-13, aprovado).

### Severidade

Média

### Prioridade

Média

### Evidências

`docs/evidencias/execucao/EX-014_CT-14.png` (busca com máscara, sem resultado)
`docs/evidencias/execucao/EX-013_CT-13.png` (mesma busca sem máscara, com resultado)
