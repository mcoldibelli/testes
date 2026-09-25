# P02: Requisitos, escopo e riscos

A lista completa, com critérios de aceitação, está nas abas **Requisitos** e **Riscos** de `P2_TQS_planilha.xlsx`.
Este documento resume o escopo e explica a classificação.

## 1. Requisitos no escopo

| ID | Requisito | Prioridade |
|---|---|---|
| RF-01 | Login com e-mail e senha; bloqueio de 15 min depois de 5 falhas seguidas | Alta |
| RF-02 | Cadastro de cliente (nome 3 a 100, CPF válido e único, e-mail, telefone opcional 10 ou 11 dígitos) | Alta |
| RF-03 | Busca de clientes por parte do nome ou do CPF | Média |
| RF-04 | Abertura de OS (descrição 10 a 500, prioridade, valor R$ 0,00 a R$ 50.000,00, prazo pelo SLA) | Alta |
| RF-05 | Mudança de status pela máquina de estados; cancelamento exige motivo | Alta |
| RF-06 | Lista de OS com filtros de status e prioridade | Média |
| RF-07 | Painel: total, quantidade por status e OS atrasadas | Média |
| RNF-01 | Desempenho: lista com 1.000 OS em até 500 ms (p95); login em até 1 s | Média |
| RNF-02 | Compatibilidade: Chrome, Firefox e tela de 375 px | Baixa |
| RNF-03 | Segurança básica: hash de senha, sessão obrigatória, cookie HttpOnly, mensagem de login neutra | Alta |
| RNF-04 | Usabilidade: usuário novo cadastra cliente e abre OS em até 2 min | Baixa |
| RNF-05 | Confiabilidade: dados permanecem depois de reinício controlado | Média |

Total: 7 funcionais e 5 não funcionais (mínimo do manual: 6 e 2).

## 2. Regras de negócio numeradas

| Regra | Descrição |
|---|---|
| RN-01 | Nome do cliente: 3 a 100 caracteres, sem contar espaços nas pontas |
| RN-02 | CPF: 11 dígitos, com ou sem máscara `000.000.000-00`, dígitos verificadores válidos, não todos iguais, único |
| RN-03 | E-mail em formato válido, com ponto no domínio; gravado em minúsculas |
| RN-04 | Telefone opcional; se informado, 10 ou 11 dígitos |
| RN-05 | Descrição da OS: 10 a 500 caracteres |
| RN-06 | Prazo = abertura + SLA: BAIXA 72 h, MEDIA 48 h, ALTA 24 h, CRITICA 4 h |
| RN-07 | Valor: R$ 0,00 a R$ 50.000,00, até 2 casas decimais, formato `1234,56` |
| RN-08 | Transições: ABERTA → EM_ANDAMENTO ou CANCELADA; EM_ANDAMENTO → CONCLUIDA ou CANCELADA; cancelar exige motivo com 10 ou mais caracteres |
| RN-09 | OS atrasada: status ABERTA ou EM_ANDAMENTO e hora atual depois do prazo |
| RN-10 | 5 falhas de login seguidas bloqueiam o e-mail por 15 minutos |
| RN-11 | OS só pode ser aberta para cliente existente |

## 3. Fora do escopo

- Cadastro e edição de usuários (os usuários vêm dos dados iniciais).
- Edição e exclusão de clientes e de OS.
- Perfis e permissões diferentes por usuário.
- Recuperação de senha e envio de e-mail.
- Teste de carga, teste de invasão e qualquer teste destrutivo (manual, seção 15).
- Implantação em produção.

## 4. Critério de classificação dos riscos

Conforme o manual, seção 9.3:

| Classificação | Probabilidade | Impacto | Prioridade |
|---|---|---|---|
| Baixo | Pouco provável | Consequência pequena e reversível | Executar depois dos fluxos principais |
| Médio | Possível | Prejudica parte do uso, mas há alternativa | Executar no ciclo principal |
| Alto | Provável ou recorrente | Bloqueia tarefa importante ou compromete dados | Executar primeiro e repetir depois das correções |

A prioridade do risco é **Alta** quando: (a) o impacto é Alto e a probabilidade é Média ou Alta; ou (b) a probabilidade é Alta e o impacto é Médio ou Alto; ou (c) o risco é de segurança.
Nos outros casos, a prioridade é **Média** se probabilidade ou impacto for Médio, e **Baixa** se os dois forem Baixos.
A aba **Riscos** lista R-01 a R-11 com o requisito ligado e o teste que responde a cada risco.
