### Requisito e caso relacionados

RF-02 / CT-11 (também em RF-04 / CT-19)

### Ambiente e versão

macOS 26.6.2, Firefox 156.0.1, sistema 1.0.0 (commit 8bfb1c6), Go 1.26.5, banco SQLite iniciado com `make reset`

### Pré-condições

Sistema iniciado com `make reset`. Usuário logado como `admin@teste.local`.

### Dados utilizados

Novo cliente: nome `Ana Souza`, CPF `114.170.753-50`, e-mail `ana@teste.local`, telefone `999994444` (9 dígitos).
Nova ordem: cliente Mercado Bom Preço, prioridade BAIXA, descrição `Teste de valor limite`, valor `50000,01`.

### Passos para reproduzir

1. Abrir **Clientes** > **Novo cliente** e preencher os dados acima.
2. Clicar em **Salvar**.
3. Ver onde aparece a mensagem de erro do telefone.
4. Abrir **Ordens de serviço** > **Nova ordem**, preencher os dados acima e clicar em **Abrir ordem**.
5. Ver onde aparece a mensagem de erro do valor.

### Resultado esperado

A mensagem de erro aparece embaixo do campo, como nos outros campos do formulário (nome, CPF, e-mail, descrição).

### Resultado obtido

A mensagem aparece na mesma linha do botão (**Salvar** ou **Abrir ordem**), à esquerda dele. Acontece só com o último campo de cada formulário: telefone (cliente) e valor (OS). O texto da mensagem está correto.

### Severidade

Baixa

### Prioridade

Baixa

### Evidências

`docs/evidencias/execucao/EX-011_CT-11_1.png` (telefone com 9 dígitos)
`docs/evidencias/execucao/EX-011_CT-11_4.png` (telefone com 12 dígitos)
`docs/evidencias/execucao/EX-019_CT-19_3.png` (valor 50000,01)
