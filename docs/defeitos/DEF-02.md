### Requisito e caso relacionados

RF-04 / CT-20

### Ambiente e versão

macOS 26.6.2, Firefox 156.0.1, sistema 1.0.0 (commit 8bfb1c6), Go 1.26.5, banco SQLite iniciado com `make reset`

### Pré-condições

Sistema iniciado com `make reset`. Usuário logado como `admin@teste.local`.

### Dados utilizados

Cliente Mercado Bom Preço, prioridade BAIXA, descrição `Teste de valor limite`, valor `abc` e depois `10,555`.

### Passos para reproduzir

1. Abrir **Ordens de serviço** > **Nova ordem**.
2. Escolher o cliente, a prioridade e a descrição acima.
3. No campo Valor, digitar `abc`.
4. Clicar em **Abrir ordem**.
5. Abrir **Ordens de serviço** e procurar a OS nova na lista.

### Resultado esperado

Erro "use o formato 1234,56", os outros campos continuam preenchidos e a OS não é criada.

### Resultado obtido

O erro aparece e os campos continuam preenchidos, mas a OS é gravada com valor R$ 0,00. Na execução, foram criadas a OS 16 (valor `abc`) e a OS 17 (valor `10,555`). O usuário vê o erro, tenta de novo e cria OS duplicadas sem saber.

### Severidade

Alta

### Prioridade

Alta

### Evidências

`docs/evidencias/execucao/EX-020_CT-20_1.png` (valor `abc`, erro na tela)
`docs/evidencias/execucao/EX-020_CT-20_2.png` (valor `10,555`, erro na tela)
`docs/evidencias/execucao/EX-020_CT-20_3.png` (lista com as OS 16 e 17 gravadas com R$ 0,00)
