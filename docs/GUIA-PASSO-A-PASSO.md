# Guia passo a passo até a entrega

Este guia vale a partir do commit `f6557a1`. Siga as partes na ordem.
Os dados para copiar foram conferidos contra o sistema: cada um produz o resultado esperado do catálogo.

## Parte A: antes de começar

1. Faça o push dos commits pendentes: `git push`.
2. Entregue o `docs/P01-ficha-do-sistema.md` ao professor. Peça três coisas: aprovação do sistema, do uso de Go (seção 8.3) e do trabalho individual (seção 4.1).
3. Registre a entrega do P01 no Diario da planilha.

A execução manual pode começar antes da resposta. Se o professor pedir ajustes, eu adapto.

## Parte B: execução manual (31 casos, cerca de 1 h)

### B.1 Preparar

1. Inicie o sistema com os dados zerados. Esta é a primeira vez, então use o reset:
   ```bash
   cd ~/Downloads/tqs-p2-ordens-servico
   make reset
   ```
   Deixe esse terminal aberto. **Não reinicie o sistema com `make reset` no meio da execução**, porque isso apaga os dados que os casos seguintes usam.
2. Mande os prints direto para a pasta de evidências: `Cmd+Shift+5` > **Opções** > **Outro local** > escolha `docs/evidencias/execucao`.
3. Abra http://localhost:8080 no Chrome.
4. Tire **um print por tentativa** (`Cmd+Shift+4` e selecione a área), mostrando o resultado e a URL.

### B.2 Casos

Em cada caso: **Faça** os passos, **confira** o resultado e anote **Aprovado** ou **Reprovado**.
Se o resultado for diferente do esperado em qualquer detalhe, é **Reprovado**. Anote o que apareceu.

#### CT-01 Login válido
Faça: abra http://localhost:8080/login e entre com o e-mail e a senha abaixo.

```text
admin@teste.local
```

```text
Admin@123
```

Confira: abre o Painel e aparece "Administrador" no topo.
Depois clique em **Sair** para os próximos casos.

#### CT-02 Senha errada
Faça: entre com `admin@teste.local` e a senha abaixo.

```text
senha-errada
```

Confira: mensagem "e-mail ou senha inválidos" e continua na tela de login.

#### CT-03 E-mail não cadastrado
Faça: entre com o e-mail abaixo e a senha `Admin@123`.

```text
naoexiste@teste.local
```

Confira: **a mesma** mensagem do CT-02, sem dizer que o e-mail não existe.

#### CT-05 Quatro falhas e acerto (faça antes do CT-04)
Faça: entre 4 vezes com `tecnico@teste.local` e a senha `errada`. Na 5ª vez, use a senha certa:

```text
tecnico@teste.local
```

```text
Tecnico@123
```

Confira: na 5ª vez o login é aceito. Depois clique em **Sair**.

#### CT-04 Bloqueio depois de 5 falhas
Faça: entre 5 vezes com `tecnico@teste.local` e a senha `errada`. Na 6ª vez, use `Tecnico@123`.
Confira: a 6ª tentativa mostra "usuário bloqueado por excesso de tentativas; tente novamente em 15 minutos".
O técnico fica bloqueado por 15 minutos. Os próximos casos usam o admin, então isso não atrapalha.

**Entre como `admin@teste.local` / `Admin@123` para todos os casos a seguir.**

#### CT-06 Cadastrar cliente válido
Faça: **Clientes** > **Novo cliente**, preencha e clique em **Salvar**.
Nome:
```text
Ana Souza
```
CPF:
```text
529.982.247-25
```
E-mail:
```text
Ana@Teste.Local
```
Telefone:
```text
(14) 99999-0000
```

Confira: mensagem "Cliente cadastrado com sucesso."; na lista, o CPF aparece como `52998224725` e o e-mail como `ana@teste.local`.

#### CT-07 CPF com dígito errado
Faça: Novo cliente com nome `Maria Teste`, e-mail `maria@teste.local` e o CPF abaixo.

```text
529.982.247-24
```

Confira: erro "CPF inválido" no campo CPF; nome e e-mail continuam preenchidos.

#### CT-08 CPF já cadastrado
Faça: Novo cliente com nome `Outro Nome`, e-mail `outro@teste.local` e o CPF do CT-06 sem máscara:

```text
52998224725
```

Confira: erro "CPF já cadastrado".

#### CT-09 Limites do nome (4 tentativas, 4 prints)
Use o e-mail `limite@teste.local` em todas.

1. Nome com **2** caracteres e CPF `158.813.998-03`:
```text
Jo
```
Confira: erro "deve ter entre 3 e 100 caracteres".
2. Nome com **3** caracteres e o mesmo CPF `158.813.998-03`:
```text
Ana
```
Confira: cadastro aceito.
3. Nome com **100** caracteres e CPF `698.797.309-17`:
```text
Cliente Nome Limite Cliente Nome Limite Cliente Nome Limite Cliente Nome Limite Cliente Nome Limiteo
```
Confira: cadastro aceito.
4. Nome com **101** caracteres e CPF `114.170.753-50`:
```text
Cliente Nome Limite Cliente Nome Limite Cliente Nome Limite Cliente Nome Limite Cliente Nome Limite C
```
Confira: erro "deve ter entre 3 e 100 caracteres".

#### CT-10 E-mail inválido (2 tentativas)
Nome `Ana Souza`, CPF `114.170.753-50`. Use cada e-mail:

```text
ana.teste.local
```

```text
ana@teste
```

Confira: erro "e-mail inválido" nas duas.

#### CT-11 Limites do telefone (4 tentativas)
Nome `Ana Souza`, e-mail `ana@teste.local`.

1. **9** dígitos, CPF `114.170.753-50`:
```text
999994444
```
Confira: erro "deve ter 10 ou 11 dígitos".
2. **10** dígitos, mesmo CPF `114.170.753-50`:
```text
(14) 3333-4444
```
Confira: aceito.
3. **11** dígitos, CPF `645.568.151-77`:
```text
(14) 99999-4444
```
Confira: aceito.
4. **12** dígitos, CPF `884.472.940-72`:
```text
(14) 999999-4444
```
Confira: erro "deve ter 10 ou 11 dígitos".

#### CT-12 Buscar por parte do nome
Faça: **Clientes**, busque:
```text
Mercado
```

Confira: aparece **somente** "Mercado Bom Preço".

#### CT-13 Buscar por CPF só com dígitos

```text
11144477735
```

Confira: aparece **somente** "Mercado Bom Preço".

#### CT-14 Buscar por CPF com máscara

```text
111.444.777-35
```

Confira: aparece **somente** "Mercado Bom Preço".

#### CT-15 Busca sem resultado

```text
zzzz
```

Confira: mensagem "Nenhum cliente encontrado.".

#### CT-16 Abrir OS válida
Faça: **Ordens de serviço** > **Nova ordem**. Cliente **Mercado Bom Preço**, prioridade **ALTA**, e:
Descrição:
```text
Alarme dispara sem motivo
```
Valor:
```text
150,00
```

Clique em **Abrir ordem** e depois no número da OS criada.
Confira: mensagem de sucesso; no detalhe, status ABERTA, valor R$ 150,00 e prazo = "Aberta em" + 24 h. **Anote o número desta OS: ela é usada no CT-22.**

#### CT-17 Prazo por prioridade (4 OS)
Faça: abra 4 OS para **Clínica Vida Plena**, uma de cada prioridade (BAIXA, MEDIA, ALTA, CRITICA), com a descrição:

```text
Teste de prazo por prioridade
```

Confira no detalhe de cada uma: prazo = abertura + 72 h, 48 h, 24 h e 4 h.

#### CT-18 Limites da descrição (4 tentativas)
Cliente **Mercado Bom Preço**, prioridade **MEDIA**, valor vazio.

1. **9** caracteres:
```text
Troca sen
```
Confira: erro "deve ter entre 10 e 500 caracteres".
2. **10** caracteres:
```text
Troca sens
```
Confira: aceita.
3. **500** caracteres:
```text
Manutencao preventiva do sistema de alarme Manutencao preventiva do sistema de alarme Manutencao preventiva do sistema de alarme Manutencao preventiva do sistema de alarme Manutencao preventiva do sistema de alarme Manutencao preventiva do sistema de alarme Manutencao preventiva do sistema de alarme Manutencao preventiva do sistema de alarme Manutencao preventiva do sistema de alarme Manutencao preventiva do sistema de alarme Manutencao preventiva do sistema de alarme Manutencao preventiva do si
```
Confira: aceita.
4. **501** caracteres:
```text
Manutencao preventiva do sistema de alarme Manutencao preventiva do sistema de alarme Manutencao preventiva do sistema de alarme Manutencao preventiva do sistema de alarme Manutencao preventiva do sistema de alarme Manutencao preventiva do sistema de alarme Manutencao preventiva do sistema de alarme Manutencao preventiva do sistema de alarme Manutencao preventiva do sistema de alarme Manutencao preventiva do sistema de alarme Manutencao preventiva do sistema de alarme Manutencao preventiva do sis
```
Confira: erro "deve ter entre 10 e 500 caracteres".

#### CT-19 Limites do valor (3 tentativas)
Cliente **Mercado Bom Preço**, prioridade **BAIXA**, descrição `Teste de valor limite`. Use cada valor:

```text
0,00
```

```text
50000,00
```

```text
50000,01
```

Confira: os dois primeiros são aceitos; o terceiro mostra "deve estar entre R$ 0,00 e R$ 50.000,00".

#### CT-20 Valor em formato inválido (2 tentativas)
Mesmos dados do CT-19, com cada valor:

```text
abc
```

```text
10,555
```

Confira: erro "use o formato 1234,56" e os outros campos continuam preenchidos.

#### CT-21 Abrir OS sem cliente
Faça: Nova ordem sem escolher o cliente (deixe "Selecione"), prioridade ALTA, descrição `Alarme dispara sem motivo`.
Confira: erro "cliente obrigatório".

#### CT-22 Iniciar e concluir a OS
Faça: abra o detalhe da OS do CT-16. Clique em **Mudar para EM_ANDAMENTO** e depois em **Mudar para CONCLUIDA**.
Confira: status CONCLUIDA, "Concluída em" preenchido e nenhum botão de mudar status. **Anote o número desta OS: é usada no CT-25.**

#### CT-23 Cancelar com motivo de 10 caracteres
Faça: **Ordens de serviço**, filtre por status **ABERTA** e abra uma OS. Escreva o motivo abaixo e clique em **Mudar para CANCELADA**.

```text
1234567890
```

Confira: status CANCELADA e o motivo aparece no detalhe.

#### CT-24 Cancelar sem motivo e com 9 caracteres (2 tentativas)
Faça: abra **outra** OS ABERTA. Tente cancelar com o motivo vazio e depois com:

```text
123456789
```

Confira: nas duas vezes aparece um erro sobre o motivo e o status continua ABERTA.

#### CT-25 Cancelar OS concluída (pela API, no terminal)
Troque `NUMERO` pelo número da OS do CT-22 e rode num **segundo** terminal:
```bash
TOKEN=$(curl -s -X POST localhost:8080/api/login -d '{"email":"admin@teste.local","senha":"Admin@123"}' | python3 -c 'import sys,json;print(json.load(sys.stdin)["token"])')
curl -i -X PATCH localhost:8080/api/ordens/NUMERO/status -H "Authorization: Bearer $TOKEN" -d '{"status":"CANCELADA","motivo":"Cliente desistiu do serviço"}'
```
Confira: `HTTP/1.1 409 Conflict` e a mensagem "transição de status não permitida". Recarregue o detalhe da OS no navegador: continua CONCLUIDA. Tire print do terminal e da tela.

#### CT-26 Filtrar por status
Faça: **Ordens de serviço**, status **EM_ANDAMENTO**, **Filtrar**.
Se não houver nenhuma OS em andamento, antes abra uma OS ABERTA e clique em **Mudar para EM_ANDAMENTO**.
Confira: a lista mostra **somente** OS EM_ANDAMENTO.

#### CT-27 Filtro com status desconhecido
Faça: abra esta URL:

```text
http://localhost:8080/ordens?status=PAUSADA
```

Confira: mensagem de erro e nenhuma lista.

#### CT-28 Painel: total igual à soma
Faça: abra o **Painel** e some as quantidades de ABERTA, EM_ANDAMENTO, CONCLUIDA e CANCELADA.
Confira: a soma é igual ao **Total**.

#### CT-30 Página protegida sem login
Faça: abra uma **janela anônima** (`Cmd+Shift+N`) e acesse:

```text
http://localhost:8080/clientes
```

Confira: o navegador vai para a tela de login.

#### CT-31 Sair e voltar pelo navegador
Faça: na janela normal, abra **Clientes**, clique em **Sair**, use o botão **Voltar** do navegador e recarregue a página (`Cmd+R`).
Confira: depois de recarregar, vai para a tela de login.

#### CT-29 OS atrasada (por último: mexe no relógio)
1. Abra uma OS **CRITICA** para **Mercado Bom Preço** com a descrição `Teste de atraso`. Anote o valor de **Atrasadas** no Painel.
2. Adiante o relógio em 5 horas: **Ajustes do Sistema** > **Geral** > **Data e Hora** > desligue **Definir hora e data automaticamente** e ajuste a hora para +5 h.
3. Recarregue o **Painel** e a lista de **Ordens de serviço**.
4. Confira: **Atrasadas** aumentou 1; a OS aparece em "Ordens atrasadas" e está marcada "(atrasada)" na lista.
5. **Religue a hora automática** logo em seguida.

Se o sistema pedir login de novo, é normal: entre e continue.

### B.3 Registrar

1. Renomeie os prints na ordem em que foram tirados. Exemplo para os primeiros casos:
   ```bash
   python3 tools/renomear_prints.py CT-01 CT-02 CT-03 CT-05 CT-04 CT-06 CT-07 CT-08 CT-09 CT-09 CT-09 CT-09
   ```
   O script mostra o plano e só renomeia depois da confirmação.
2. Me mande o resultado de cada caso. Exemplo: "todos aprovados, menos CT-14: a lista ficou vazia". Eu preencho a aba Execucoes.
3. Para cada Reprovado, eu escrevo a issue de defeito com o modelo do repositório (Apêndice G), e você confere e publica.
4. Registre no Diario: data, "Execução manual CT-01 a CT-31", tempo gasto.

## Parte C: depois da execução manual

| Passo | O que fazer | Quem | Onde está o detalhe |
|---|---|---|---|
| C.1 | Corrigir os defeitos com teste antes (o teste falha, a correção faz passar) e depois fazer reteste e regressão | eu corrijo, você executa o reteste | este guia, B.2 |
| C.2 | Aceitação AC-01 a AC-04 com uma pessoa que não fez os testes (ex.: colega de outro grupo) | você | aba Aceitacao |
| C.3 | Não funcionais NF-01 a NF-08 | você, com os comandos prontos | aba NaoFuncionais |
| C.4 | TDD do valor `1.500,00`: RED, GREEN e REFACTOR, um commit cada | você, eu acompanho | P11, seção 2 |
| C.5 | Pipeline com falha e depois com correção | você, eu acompanho | P11, seção 3 |
| C.6 | Segunda análise do SonarQube e comparação | você | P11, seção 4 |
| C.7 | Plano de melhoria contínua | eu faço o rascunho com os dados reais, você revisa | P11, seção 5 |
| C.8 | Interpretação das métricas | eu faço o rascunho, você revisa | aba Metricas |
| C.9 | Relatório final (DOCX e PDF) e apresentação (PPTX e PDF) | eu monto a partir dos resultados, você revisa | manual, seções 12 e 13 |
| C.10 | Vídeo de contingência (3 a 5 min) mostrando os testes automatizados | você | manual, seção 13.2 |
| C.11 | Drive: `make entrega`, copiar os arquivos, COMPROVANTE_DE_ENTREGA, testar os links | você, eu confiro a lista | manual, seção 11 |
| C.12 | Dar acesso ao professor no GitHub (Settings > Collaborators), com o repositório privado | você | manual, seção 11.6 |

Registre cada passo no Diario no mesmo dia em que fizer.
