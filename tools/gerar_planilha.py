"""Gera docs/P2_TQS_planilha.xlsx: requisitos, riscos, casos, execuções, defeitos,
rastreabilidade, testes não funcionais, aceitação, automação, métricas e diário.

Uso: tools/.venv/bin/python tools/gerar_planilha.py

Os resultados (execuções, defeitos, medições) NÃO vêm preenchidos: o grupo registra
somente o que executou. Os indicadores da aba Metricas são fórmulas e se atualizam sozinhos.
"""
from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.datavalidation import DataValidation

SAIDA = Path(__file__).resolve().parent.parent / "docs" / "P2_TQS_planilha.xlsx"
MAX_LINHAS = 300  # linhas preparadas para execuções e defeitos

FONTE = "Arial"
COR_CABECALHO = "B5121B"
COR_ENTRADA = "FFF2CC"  # amarelo claro: células que o grupo preenche

REQUISITOS = [
    ("RF-01", "O usuário entra com e-mail e senha. Depois de 5 falhas seguidas, o e-mail fica bloqueado por 15 minutos.",
     "Funcional", "Alta", "Credenciais válidas abrem o painel; senha errada mostra 'e-mail ou senha inválidos'; a 6ª tentativa depois de 5 falhas mostra a mensagem de bloqueio."),
    ("RF-02", "Cadastrar cliente: nome de 3 a 100 caracteres, CPF válido e único, e-mail válido, telefone opcional com 10 ou 11 dígitos.",
     "Funcional", "Alta", "Dados válidos gravam o cliente e mostram 'Cliente cadastrado com sucesso.'; cada regra violada mostra erro no campo e mantém os dados digitados."),
    ("RF-03", "Buscar clientes por parte do nome ou do CPF.",
     "Funcional", "Média", "A lista mostra somente clientes cujo nome ou CPF contém o texto buscado; sem resultado mostra 'Nenhum cliente encontrado.'."),
    ("RF-04", "Abrir ordem de serviço (OS) para cliente existente: descrição de 10 a 500 caracteres, prioridade, valor de R$ 0,00 a R$ 50.000,00. Prazo = abertura + SLA (BAIXA 72 h, MEDIA 48 h, ALTA 24 h, CRITICA 4 h).",
     "Funcional", "Alta", "A OS nasce ABERTA com o prazo calculado pelo SLA; dados fora das regras mostram erro no campo."),
    ("RF-05", "Alterar status da OS: ABERTA -> EM_ANDAMENTO ou CANCELADA; EM_ANDAMENTO -> CONCLUIDA ou CANCELADA. Cancelar exige motivo com 10 caracteres ou mais. CONCLUIDA e CANCELADA são finais.",
     "Funcional", "Alta", "Transições permitidas gravam o novo status; transições não permitidas são recusadas (HTTP 409) e o status não muda."),
    ("RF-06", "Listar OS ordenadas pelo prazo, com filtro por status e prioridade, destacando as atrasadas.",
     "Funcional", "Média", "O filtro devolve somente OS com o status/prioridade escolhidos; filtro desconhecido mostra erro."),
    ("RF-07", "Painel com total de OS, quantidade por status e quantidade de OS atrasadas (ativa e com prazo vencido).",
     "Funcional", "Média", "Total = soma das quantidades por status; OS ativa com prazo vencido conta como atrasada; no instante exato do prazo ainda não está atrasada."),
    ("RNF-01", "Desempenho: GET /api/ordens com 1.000 OS responde em até 500 ms (p95 de 20 medições) no ambiente local; login responde em até 1 s.",
     "Não funcional", "Média", "p95 medido <= 500 ms; tempo médio de login <= 1 s."),
    ("RNF-02", "Compatibilidade: os fluxos principais funcionam no Chrome e no Firefox atualizados e em tela de 375 px de largura.",
     "Não funcional", "Baixa", "Suíte Selenium aprovada nos dois navegadores; em 375 px os formulários ficam utilizáveis."),
    ("RNF-03", "Segurança básica: senha guardada só como hash PBKDF2; páginas e API exigem sessão; cookie HttpOnly e SameSite=Lax; mensagem de login não revela se o e-mail existe.",
     "Não funcional", "Alta", "Nenhuma senha em texto no banco; acesso sem sessão redireciona (páginas) ou devolve 401 (API)."),
    ("RNF-04", "Usabilidade: um usuário novo cadastra um cliente e abre uma OS sem ajuda em até 2 minutos.",
     "Não funcional", "Baixa", "Tempo <= 2 min, no máximo 1 erro, satisfação >= 4 (escala 1 a 5)."),
    ("RNF-05", "Confiabilidade: dados gravados permanecem depois de reinício controlado do servidor.",
     "Não funcional", "Média", "Clientes e OS criados antes do reinício aparecem depois dele."),
]

RISCOS = [
    ("R-01", "CPF inválido aceito no cadastro, gerando cliente com documento inconsistente", "RF-02", "Média", "Alto", "Alta", "PE e valor limite no CPF (CT-07); UT-01; API-06"),
    ("R-02", "Transição de status indevida (ex.: cancelar OS concluída)", "RF-05", "Média", "Alto", "Alta", "Tabela de decisão com 16 combinações (UT-08); CT-25; API-13"),
    ("R-03", "Prazo (SLA) calculado errado, escondendo OS atrasada", "RF-04", "Média", "Alto", "Alta", "CT-17, CT-29; UT-07, UT-11, IT-07"),
    ("R-04", "Acesso às páginas ou à API sem autenticação", "RNF-03", "Baixa", "Alto", "Alta", "CT-30, CT-31; IT-03, IT-10; API-04"),
    ("R-05", "Força bruta no login por falta de bloqueio", "RF-01", "Média", "Alto", "Alta", "CT-04, CT-05; IT-02"),
    ("R-06", "OS gravada para cliente inexistente (integridade)", "RF-04", "Baixa", "Médio", "Média", "CT-21; IT-05; API-09"),
    ("R-07", "Valor digitado no formato brasileiro com milhar (1.500,00) é recusado ou mal interpretado", "RF-04", "Alta", "Médio", "Alta", "CT-19, CT-20; UT-12"),
    ("R-08", "Listagem de OS lenta com volume de dados", "RNF-01", "Baixa", "Médio", "Média", "NF-01"),
    ("R-09", "Busca de cliente não encontra o CPF digitado com máscara", "RF-03", "Média", "Médio", "Média", "CT-13, CT-14"),
    ("R-10", "Senha exposta em texto no banco ou no log", "RNF-03", "Baixa", "Alto", "Alta", "NF-05"),
    ("R-11", "Dados de uma execução afetam a seguinte (ambiente não restaurado)", "RNF-05", "Média", "Médio", "Média", "Iniciar com -reset antes de cada ciclo; CPF aleatório nos scripts; NF-08"),
]

# (id, título, requisito, nível/tipo, técnica, prioridade, pré-condições, dados, passos, esperado, candidato, automatizado por)
LOGADO = "Sistema iniciado com -reset; usuário logado como admin@teste.local"
CASOS = [
    ("CT-01", "Login com credenciais válidas", "RF-01", "Sistema / positivo", "Particionamento de equivalência", "Alta",
     "Sistema iniciado com -reset", "admin@teste.local / Admin@123",
     "1. Abrir /login\n2. Informar e-mail e senha\n3. Clicar em Entrar",
     "Painel aberto; nome 'Administrador' no topo", "Sim", "ST-01; API-03; IT-01"),
    ("CT-02", "Login com senha errada", "RF-01", "Sistema / negativo", "Particionamento de equivalência", "Alta",
     "Sistema iniciado com -reset", "admin@teste.local / senha-errada",
     "1. Abrir /login\n2. Informar e-mail e senha errada\n3. Clicar em Entrar",
     "Mensagem 'e-mail ou senha inválidos'; permanece em /login", "Sim", "ST-02; API-02; IT-01"),
    ("CT-03", "Login com e-mail não cadastrado", "RF-01", "Sistema / negativo", "Particionamento de equivalência", "Média",
     "Sistema iniciado com -reset", "naoexiste@teste.local / Admin@123",
     "1. Abrir /login\n2. Informar e-mail inexistente\n3. Clicar em Entrar",
     "Mesma mensagem do CT-02 (não revela se o e-mail existe)", "Não", ""),
    ("CT-04", "Bloqueio depois de 5 falhas seguidas", "RF-01", "Sistema / limite", "Análise de valor limite", "Alta",
     "Sistema iniciado com -reset", "tecnico@teste.local; senha errada 5 vezes; depois Tecnico@123",
     "1. Errar a senha 5 vezes\n2. Informar a senha certa",
     "Mensagem de bloqueio por 15 minutos; login recusado", "Sim", "IT-02"),
    ("CT-05", "Quatro falhas e acerto na 5ª tentativa", "RF-01", "Sistema / limite", "Análise de valor limite", "Média",
     "Sistema iniciado com -reset", "tecnico@teste.local; senha errada 4 vezes; depois Tecnico@123",
     "1. Errar a senha 4 vezes\n2. Informar a senha certa",
     "Login aceito; painel aberto", "Sim", ""),
    ("CT-06", "Cadastrar cliente válido com CPF mascarado", "RF-02", "Sistema / positivo", "Particionamento de equivalência", "Alta",
     LOGADO, "Nome 'Ana Souza'; CPF 529.982.247-25; e-mail Ana@Teste.Local; telefone (14) 99999-0000",
     "1. Clientes > Novo cliente\n2. Preencher os campos\n3. Salvar",
     "Mensagem 'Cliente cadastrado com sucesso.'; lista mostra CPF 52998224725 e e-mail em minúsculas", "Sim", "ST-03; API-05; IT-04"),
    ("CT-07", "CPF com dígito verificador errado", "RF-02", "Sistema / negativo", "Particionamento de equivalência", "Alta",
     LOGADO, "CPF 529.982.247-24 (último dígito errado)",
     "1. Novo cliente\n2. Preencher nome e e-mail válidos e o CPF\n3. Salvar",
     "Erro 'CPF inválido' no campo; nome e e-mail continuam preenchidos", "Sim", "ST-04; API-06; UT-01"),
    ("CT-08", "CPF já cadastrado", "RF-02", "Sistema / negativo", "Particionamento de equivalência", "Alta",
     LOGADO + "; cliente do CT-06 cadastrado", "CPF 52998224725 (sem máscara)",
     "1. Novo cliente\n2. Usar o CPF do CT-06\n3. Salvar",
     "Erro 'CPF já cadastrado'", "Sim", "API-07; IT-04"),
    ("CT-09", "Limites do nome (2, 3, 100 e 101 caracteres)", "RF-02", "Sistema / limite", "Análise de valor limite", "Média",
     LOGADO, "Nomes com 2, 3, 100 e 101 caracteres; CPF válido novo em cada tentativa",
     "1. Cadastrar com cada tamanho de nome",
     "2 e 101: erro 'deve ter entre 3 e 100 caracteres'; 3 e 100: cadastro aceito", "Sim", "UT-02"),
    ("CT-10", "E-mail inválido", "RF-02", "Sistema / negativo", "Particionamento de equivalência", "Média",
     LOGADO, "ana.teste.local; ana@teste",
     "1. Cadastrar com cada e-mail",
     "Erro 'e-mail inválido' nos dois casos", "Sim", "UT-03"),
    ("CT-11", "Limites do telefone (9, 10, 11 e 12 dígitos)", "RF-02", "Sistema / limite", "Análise de valor limite", "Baixa",
     LOGADO, "999994444; (14) 3333-4444; (14) 99999-4444; (14) 999999-4444",
     "1. Cadastrar com cada telefone",
     "9 e 12 dígitos: erro 'deve ter 10 ou 11 dígitos'; 10 e 11: aceito", "Sim", "UT-03 (9, 10, 11)"),
    ("CT-12", "Buscar cliente por parte do nome", "RF-03", "Sistema / positivo", "Particionamento de equivalência", "Média",
     LOGADO, "Busca 'Mercado'",
     "1. Clientes\n2. Digitar a busca\n3. Buscar",
     "Somente 'Mercado Bom Preço' na lista", "Sim", ""),
    ("CT-13", "Buscar cliente por CPF só com dígitos", "RF-03", "Sistema / positivo", "Particionamento de equivalência", "Média",
     LOGADO, "Busca '11144477735'",
     "1. Clientes\n2. Digitar o CPF\n3. Buscar",
     "Somente 'Mercado Bom Preço' na lista", "Sim", "ST-03"),
    ("CT-14", "Buscar cliente por CPF com máscara", "RF-03", "Sistema / alternativo", "Particionamento de equivalência", "Média",
     LOGADO, "Busca '111.444.777-35'",
     "1. Clientes\n2. Digitar o CPF com máscara\n3. Buscar",
     "Somente 'Mercado Bom Preço' na lista", "Sim", ""),
    ("CT-15", "Busca sem resultado", "RF-03", "Sistema / negativo", "Particionamento de equivalência", "Baixa",
     LOGADO, "Busca 'zzzz'",
     "1. Clientes\n2. Digitar a busca\n3. Buscar",
     "Mensagem 'Nenhum cliente encontrado.'", "Não", ""),
    ("CT-16", "Abrir OS válida (ALTA, R$ 150,00)", "RF-04", "Sistema / positivo", "Particionamento de equivalência", "Alta",
     LOGADO, "Cliente 'Mercado Bom Preço'; descrição 'Alarme dispara sem motivo'; ALTA; valor 150,00",
     "1. Ordens > Nova ordem\n2. Preencher\n3. Abrir ordem\n4. Abrir o detalhe da OS",
     "Mensagem de sucesso; status ABERTA; prazo = abertura + 24 h; valor R$ 150,00", "Sim", "ST-05"),
    ("CT-17", "Prazo por prioridade", "RF-04", "Sistema / positivo", "Tabela de decisão", "Alta",
     LOGADO, "4 OS: BAIXA, MEDIA, ALTA, CRITICA",
     "1. Abrir uma OS de cada prioridade\n2. Comparar abertura e prazo no detalhe",
     "Prazo = abertura + 72 h, 48 h, 24 h e 4 h", "Sim", "UT-07; API-08"),
    ("CT-18", "Limites da descrição (9, 10, 500 e 501 caracteres)", "RF-04", "Sistema / limite", "Análise de valor limite", "Média",
     LOGADO, "Descrições com 9, 10, 500 e 501 caracteres",
     "1. Abrir OS com cada descrição",
     "9 e 501: erro 'deve ter entre 10 e 500 caracteres'; 10 e 500: aceita", "Sim", "UT-05; API-10"),
    ("CT-19", "Limites do valor (0,00; 50000,00; 50000,01)", "RF-04", "Sistema / limite", "Análise de valor limite", "Média",
     LOGADO, "Valores 0,00; 50000,00; 50000,01",
     "1. Abrir OS com cada valor",
     "0,00 e 50000,00: aceita; 50000,01: erro 'deve estar entre R$ 0,00 e R$ 50.000,00'", "Sim", "UT-06"),
    ("CT-20", "Valor em formato inválido", "RF-04", "Sistema / negativo", "Particionamento de equivalência", "Média",
     LOGADO, "Valores 'abc' e '10,555'",
     "1. Abrir OS com cada valor",
     "Erro 'use o formato 1234,56'; outros campos mantidos", "Sim", "UT-12"),
    ("CT-21", "Abrir OS sem selecionar cliente", "RF-04", "Sistema / negativo", "Particionamento de equivalência", "Média",
     LOGADO, "Cliente 'Selecione'; demais campos válidos",
     "1. Nova ordem\n2. Não escolher cliente\n3. Abrir ordem",
     "Erro 'cliente obrigatório' no campo cliente", "Não", ""),
    ("CT-22", "Fluxo ABERTA -> EM_ANDAMENTO -> CONCLUIDA", "RF-05", "Sistema / positivo", "Tabela de decisão", "Alta",
     LOGADO + "; OS ABERTA existente", "OS do CT-16",
     "1. Abrir o detalhe da OS\n2. Mudar para EM_ANDAMENTO\n3. Mudar para CONCLUIDA",
     "Status CONCLUIDA; 'Concluída em' preenchido; sem botões de ação", "Sim", "ST-05; API-11; API-12; IT-06"),
    ("CT-23", "Cancelar com motivo de 10 caracteres", "RF-05", "Sistema / limite", "Análise de valor limite", "Média",
     LOGADO + "; OS ABERTA existente", "Motivo '1234567890'",
     "1. Detalhe da OS\n2. Informar o motivo\n3. Mudar para CANCELADA",
     "Status CANCELADA; motivo exibido", "Sim", "UT-09"),
    ("CT-24", "Cancelar sem motivo e com 9 caracteres", "RF-05", "Sistema / limite", "Análise de valor limite", "Média",
     LOGADO + "; OS ABERTA existente", "Motivo vazio; motivo '123456789'",
     "1. Detalhe da OS\n2. Tentar cancelar com cada motivo",
     "Erro sobre o motivo; status continua ABERTA", "Sim", "ST-06; UT-09"),
    ("CT-25", "Cancelar OS concluída", "RF-05", "Integração / negativo", "Tabela de decisão", "Alta",
     "Token válido; OS CONCLUIDA existente", "PATCH /api/ordens/{id}/status com CANCELADA",
     "1. Enviar a requisição pelo Postman",
     "HTTP 409 'transição de status não permitida'; status continua CONCLUIDA", "Sim", "API-13; IT-06; UT-08"),
    ("CT-26", "Filtrar OS por status", "RF-06", "Sistema / positivo", "Particionamento de equivalência", "Média",
     LOGADO + "; OS em status diferentes", "Status EM_ANDAMENTO",
     "1. Ordens\n2. Escolher o status\n3. Filtrar",
     "Somente OS EM_ANDAMENTO na lista", "Sim", "IT-08; API-15"),
    ("CT-27", "Filtro com status desconhecido", "RF-06", "Sistema / negativo", "Particionamento de equivalência", "Baixa",
     LOGADO, "URL /ordens?status=PAUSADA",
     "1. Abrir a URL no navegador",
     "Mensagem de erro; nenhuma lista", "Sim", "IT-08"),
    ("CT-28", "Painel: total igual à soma por status", "RF-07", "Sistema / positivo", "Particionamento de equivalência", "Média",
     LOGADO, "Dados iniciais do -reset",
     "1. Abrir o Painel\n2. Somar as quantidades por status",
     "Soma = Total", "Sim", "API-16"),
    ("CT-29", "OS CRITICA atrasada aparece no painel", "RF-07", "Sistema / limite", "Análise de valor limite", "Alta",
     LOGADO + "; relógio do computador ajustável", "OS CRITICA nova",
     "1. Abrir OS CRITICA\n2. Adiantar o relógio do computador em 5 h\n3. Recarregar o Painel e a lista",
     "Atrasadas +1; OS listada em 'Ordens atrasadas' e marcada '(atrasada)'", "Sim", "IT-07; UT-11"),
    ("CT-30", "Página protegida sem login", "RNF-03", "Sistema / negativo", "Particionamento de equivalência", "Alta",
     "Navegador sem sessão (janela anônima)", "URL /clientes",
     "1. Abrir a URL",
     "Redireciona para /login", "Sim", "IT-10; IT-03; API-04"),
    ("CT-31", "Sair e voltar pelo navegador", "RNF-03", "Sistema / negativo", "Particionamento de equivalência", "Média",
     LOGADO, "",
     "1. Abrir Clientes\n2. Clicar em Sair\n3. Usar o botão Voltar e recarregar",
     "Depois de recarregar, redireciona para /login", "Sim", ""),
]

AUTOMACAO = [
    ("UT-01", "Unitário", "Go testing", "internal/domain/cliente_test.go", "CT-07", "RF-02"),
    ("UT-02", "Unitário", "Go testing", "internal/domain/cliente_test.go", "CT-09", "RF-02"),
    ("UT-03", "Unitário", "Go testing", "internal/domain/cliente_test.go", "CT-10; CT-11", "RF-02"),
    ("UT-04", "Unitário", "Go testing", "internal/domain/cliente_test.go", "CT-06", "RF-02"),
    ("UT-05", "Unitário", "Go testing", "internal/domain/ordem_test.go", "CT-18", "RF-04"),
    ("UT-06", "Unitário", "Go testing", "internal/domain/ordem_test.go", "CT-19", "RF-04"),
    ("UT-07", "Unitário", "Go testing", "internal/domain/ordem_test.go", "CT-17", "RF-04"),
    ("UT-08", "Unitário", "Go testing", "internal/domain/ordem_test.go", "CT-25", "RF-05"),
    ("UT-09", "Unitário", "Go testing", "internal/domain/ordem_test.go", "CT-23; CT-24", "RF-05"),
    ("UT-10", "Unitário", "Go testing", "internal/domain/ordem_test.go", "CT-22", "RF-05"),
    ("UT-11", "Unitário", "Go testing", "internal/domain/ordem_test.go", "CT-29", "RF-07"),
    ("UT-12", "Unitário", "Go testing", "internal/domain/valor_test.go", "CT-19; CT-20", "RF-04"),
    ("IT-01", "Integração", "Go testing + httptest + SQLite", "internal/web/integracao_test.go", "CT-01; CT-02", "RF-01"),
    ("IT-02", "Integração", "Go testing + httptest + SQLite", "internal/web/integracao_test.go", "CT-04", "RF-01"),
    ("IT-03", "Integração", "Go testing + httptest + SQLite", "internal/web/integracao_test.go", "CT-30", "RNF-03"),
    ("IT-04", "Integração", "Go testing + httptest + SQLite", "internal/web/integracao_test.go", "CT-06; CT-08", "RF-02"),
    ("IT-05", "Integração", "Go testing + httptest + SQLite", "internal/web/integracao_test.go", "", "RF-04"),
    ("IT-06", "Integração", "Go testing + httptest + SQLite", "internal/web/integracao_test.go", "CT-22; CT-25", "RF-05"),
    ("IT-07", "Integração", "Go testing + httptest + SQLite", "internal/web/integracao_test.go", "CT-29", "RF-07"),
    ("IT-08", "Integração", "Go testing + httptest + SQLite", "internal/web/integracao_test.go", "CT-26; CT-27", "RF-06"),
    ("IT-09", "Integração", "Go testing + httptest + SQLite", "internal/web/integracao_test.go", "", "RNF-03"),
    ("IT-10", "Integração", "Go testing + httptest + SQLite", "internal/web/integracao_test.go", "CT-30", "RNF-03"),
] + [
    (f"API-{i:02d}", "Integração/API", "Postman + Newman", "tests/postman/ordens-servico.postman_collection.json", casos, req)
    for i, casos, req in [
        (1, "", "RNF-05"), (2, "CT-02", "RF-01"), (3, "CT-01", "RF-01"), (4, "CT-30", "RNF-03"),
        (5, "CT-06", "RF-02"), (6, "CT-07", "RF-02"), (7, "CT-08", "RF-02"), (8, "CT-17", "RF-04"),
        (9, "", "RF-04"), (10, "CT-18", "RF-04"), (11, "CT-22", "RF-05"), (12, "CT-22", "RF-05"),
        (13, "CT-25", "RF-05"), (14, "CT-22", "RF-05"), (15, "CT-26", "RF-06"), (16, "CT-28", "RF-07"),
    ]
] + [
    ("ST-01", "Sistema/interface", "Selenium + pytest", "tests/e2e/test_fluxos.py", "CT-01", "RF-01"),
    ("ST-02", "Sistema/interface", "Selenium + pytest", "tests/e2e/test_fluxos.py", "CT-02", "RF-01"),
    ("ST-03", "Sistema/interface", "Selenium + pytest", "tests/e2e/test_fluxos.py", "CT-06; CT-13", "RF-02"),
    ("ST-04", "Sistema/interface", "Selenium + pytest", "tests/e2e/test_fluxos.py", "CT-07", "RF-02"),
    ("ST-05", "Sistema/interface", "Selenium + pytest", "tests/e2e/test_fluxos.py", "CT-16; CT-22", "RF-04"),
    ("ST-06", "Sistema/interface", "Selenium + pytest", "tests/e2e/test_fluxos.py", "CT-24", "RF-05"),
]

NAO_FUNCIONAIS = [
    ("NF-01", "Desempenho", "RNF-01", "Medir o tempo de GET /api/ordens com 1.000 OS", "Máquina local; sistema iniciado com -reset",
     "p95 de 20 medições <= 500 ms", "python3 tools/medir_desempenho.py listagem", "1.000 OS criadas pelo script; 20 medições"),
    ("NF-02", "Desempenho", "RNF-01", "Medir o tempo de POST /api/login", "Máquina local",
     "Média de 10 medições <= 1 s", "python3 tools/medir_desempenho.py login", "10 medições"),
    ("NF-03", "Compatibilidade", "RNF-02", "Executar a suíte Selenium no Chrome e no Firefox", "Chrome e Firefox atualizados",
     "6 de 6 testes aprovados nos dois navegadores", "make test-e2e e depois BROWSER=firefox make test-e2e", "1 execução por navegador"),
    ("NF-04", "Compatibilidade", "RNF-02", "Usar login, cadastro de cliente e abertura de OS em 375 px de largura", "Chrome DevTools, modo dispositivo (iPhone SE)",
     "Campos e botões visíveis e utilizáveis sem rolagem horizontal", "Executar CT-01, CT-06 e CT-16 no modo dispositivo; capturar tela", "1 execução"),
    ("NF-05", "Segurança básica", "RNF-03", "Confirmar que a senha não é guardada em texto e que o cookie é HttpOnly", "Banco dados/ordens.db; Chrome DevTools",
     "senha_hash é binário de 32 bytes; cookie 'sessao' com HttpOnly e SameSite=Lax",
     "sqlite3 dados/ordens.db \"select email, length(senha_hash) from usuarios\"; DevTools > Application > Cookies", "1 verificação"),
    ("NF-06", "Segurança básica", "RNF-03", "Confirmar que a mensagem de login não revela se o e-mail existe", "Sistema local",
     "Mensagem idêntica para senha errada e e-mail inexistente", "Comparar os resultados de CT-02 e CT-03", "1 verificação"),
    ("NF-07", "Usabilidade", "RNF-04", "Roteiro de tarefa com participante que não construiu o sistema", "Sistema local; cronômetro",
     "Tempo <= 2 min; no máximo 1 erro; satisfação >= 4 (1 a 5)", "Pedir: 'cadastre o cliente X e abra uma OS ALTA para ele'. Não ajudar. Anotar tempo, erros e nota", "Pelo menos 1 participante"),
    ("NF-08", "Confiabilidade", "RNF-05", "Reiniciar o servidor e conferir os dados", "Sistema local",
     "Clientes e OS criados antes do reinício continuam na lista", "Criar 1 cliente e 1 OS; Ctrl+C; iniciar sem -reset; conferir", "1 reinício"),
]

ACEITACAO = [
    ("AC-01", "RF-02, RF-03", "Dado que sou atendente, quando cadastro um cliente novo com o CPF digitado com máscara, então encontro esse cliente na busca pelo CPF.",
     "Cliente fictício escolhido pelo participante", "Cliente cadastrado e encontrado na busca"),
    ("AC-02", "RF-04", "Dado um cliente cadastrado, quando abro uma OS CRITICA para ele, então consigo informar ao cliente o prazo de atendimento.",
     "Cliente 'Clínica Vida Plena'", "Participante informa um prazo igual à abertura + 4 h"),
    ("AC-03", "RF-05", "Dado uma OS aberta, quando o técnico inicia e conclui o atendimento, então a OS aparece como CONCLUIDA e não aceita mais mudanças.",
     "OS aberta dos dados iniciais", "OS CONCLUIDA, sem botões de ação"),
    ("AC-04", "RF-07", "Dado que sou supervisor, quando abro o painel, então sei quantas OS estão atrasadas e consigo abrir uma delas.",
     "OS CRITICA com prazo vencido (ver CT-29)", "Participante informa a quantidade correta e abre a OS"),
]

METRICAS = [
    # (indicador, fórmula, fonte, cálculo)
    ("Casos planejados", "=COUNTA(Casos!A2:A200)", "Aba Casos", "contagem de casos"),
    ("Casos executados", "=COUNTIF(Casos!O2:O200,\"Aprovado\")+COUNTIF(Casos!O2:O200,\"Reprovado\")", "Aba Casos, coluna Último resultado", "aprovados + reprovados"),
    ("Percentual de execução", "=IF(B2=0,0,B3/B2)", "Casos", "casos executados / casos planejados x 100"),
    ("Taxa de aprovação", "=IF(B3=0,0,COUNTIF(Casos!O2:O200,\"Aprovado\")/B3)", "Casos", "casos aprovados / casos executados x 100"),
    ("Taxa de reprovação", "=IF(B3=0,0,COUNTIF(Casos!O2:O200,\"Reprovado\")/B3)", "Casos", "casos reprovados / casos executados x 100"),
    ("Cobertura de requisitos", "=IF(COUNTA(Rastreabilidade!A2:A50)=0,0,COUNTIF(Rastreabilidade!F2:F50,\">0\")/COUNTA(Rastreabilidade!A2:A50))",
     "Rastreabilidade", "requisitos com teste executado / requisitos no escopo x 100"),
    ("Taxa de automação", "=IF(COUNTIF(Casos!K2:K200,\"Sim\")=0,0,COUNTIFS(Casos!K2:K200,\"Sim\",Casos!L2:L200,\"<>\")/COUNTIF(Casos!K2:K200,\"Sim\"))",
     "Casos, colunas Candidato e Automatizado por", "casos automatizados / casos planejados para automação x 100"),
    ("Defeitos - Crítica", "=COUNTIF(Defeitos!K2:K300,\"Crítica\")", "Defeitos", "contagem por severidade"),
    ("Defeitos - Alta", "=COUNTIF(Defeitos!K2:K300,\"Alta\")", "Defeitos", "contagem por severidade"),
    ("Defeitos - Média", "=COUNTIF(Defeitos!K2:K300,\"Média\")", "Defeitos", "contagem por severidade"),
    ("Defeitos - Baixa", "=COUNTIF(Defeitos!K2:K300,\"Baixa\")", "Defeitos", "contagem por severidade"),
] + [
    (f"Defeitos - {s}", f"=COUNTIF(Defeitos!N2:N300,\"{s}\")", "Defeitos", "contagem por status")
    for s in ["Novo", "Em análise", "Em correção", "Pronto para reteste", "Encerrado", "Reaberto"]
] + [
    ("Taxa de reabertura", "=IF(COUNTIF(Defeitos!P2:P300,\"Sim\")=0,0,COUNTIF(Defeitos!Q2:Q300,\"Sim\")/COUNTIF(Defeitos!P2:P300,\"Sim\"))",
     "Defeitos, colunas Retestado e Reaberto", "defeitos reabertos / defeitos retestados x 100"),
]

PERCENTUAIS = {"Percentual de execução", "Taxa de aprovação", "Taxa de reprovação", "Cobertura de requisitos", "Taxa de automação", "Taxa de reabertura"}

borda = Border(*(Side(style="thin", color="BFBFBF"),) * 4)


def aba(wb, titulo, cabecalho, larguras, linhas=(), entrada=()):
    """Cria a aba com cabeçalho formatado. 'entrada' lista as colunas (1-based) que o grupo preenche."""
    ws = wb.create_sheet(titulo)
    ws.append(cabecalho)
    for linha in linhas:
        ws.append(list(linha))
    for i, largura in enumerate(larguras, start=1):
        ws.column_dimensions[get_column_letter(i)].width = largura
    for cel in ws[1]:
        cel.font = Font(name=FONTE, bold=True, color="FFFFFF")
        cel.fill = PatternFill("solid", fgColor=COR_CABECALHO)
        cel.alignment = Alignment(wrap_text=True, vertical="center", horizontal="center")
        cel.border = borda
    ws.freeze_panes = "B2"
    return ws


def formatar_corpo(ws, ultima_linha, entrada=()):
    for linha in ws.iter_rows(min_row=2, max_row=ultima_linha, max_col=ws.max_column):
        for cel in linha:
            cel.font = Font(name=FONTE, size=10)
            cel.alignment = Alignment(wrap_text=True, vertical="top")
            cel.border = borda
            if cel.column in entrada:
                cel.fill = PatternFill("solid", fgColor=COR_ENTRADA)


def validacao(ws, opcoes, intervalo):
    dv = DataValidation(type="list", formula1='"' + ",".join(opcoes) + '"', allow_blank=True)
    ws.add_data_validation(dv)
    dv.add(intervalo)


def main():
    wb = Workbook()
    leia = wb.active
    leia.title = "LEIA-ME"
    textos = [
        "Planilha do Projeto P2 - Testes e Qualidade de Software - Sistema de Ordens de Serviço",
        "",
        "Células em AMARELO são preenchidas pelo grupo. As demais têm dados do plano ou fórmulas: não editar as fórmulas.",
        "Execucoes: uma linha por execução. Para reteste, crie uma linha nova com o mesmo caso (a última linha preenchida vale).",
        "Resultado: Aprovado, Reprovado, Bloqueado ou Não executado. Data no formato 25/09/2026. Evidência: nome do arquivo na pasta 05 do Drive.",
        "Exemplo de preenchimento (NÃO é um resultado real): EX-001 | CT-01 | 25/09/2026 | v1.0.0 | Aprovado | EX-001_CT-01.png | (vazio) | Nome",
        "Defeitos: copie o link da issue do GitHub na coluna R. Retestado/Reaberto: Sim ou Não.",
        "Metricas: todos os indicadores são fórmulas calculadas a partir de Casos, Execucoes, Defeitos, Rastreabilidade e NaoFuncionais.",
        "Regra do manual (seção 15): registre somente execuções reais. Não preencha resultados por estimativa.",
    ]
    for t in textos:
        leia.append([t])
    leia.column_dimensions["A"].width = 130
    for linha in leia.iter_rows():
        for cel in linha:
            cel.font = Font(name=FONTE, size=11)
    leia["A1"].font = Font(name=FONTE, size=14, bold=True)

    ws = aba(wb, "Requisitos", ["ID", "Descrição verificável", "Tipo", "Prioridade", "Critério de aceitação"],
             [9, 60, 14, 11, 60], REQUISITOS)
    formatar_corpo(ws, ws.max_row)

    ws = aba(wb, "Riscos", ["ID", "Risco", "Requisito", "Probabilidade", "Impacto", "Prioridade", "Resposta/teste"],
             [7, 50, 11, 13, 10, 11, 45], RISCOS)
    formatar_corpo(ws, ws.max_row)

    cab_casos = ["ID do caso", "Título", "Requisito", "Nível/tipo", "Técnica aplicada", "Prioridade", "Pré-condições",
                 "Dados de entrada", "Passos numerados", "Resultado esperado", "Candidato à automação", "Automatizado por",
                 "Responsável", "Linha da última execução (auxiliar)", "Último resultado"]
    ws = aba(wb, "Casos", cab_casos, [8, 30, 9, 16, 20, 10, 28, 30, 38, 40, 11, 20, 14, 11, 14], CASOS)
    for r in range(2, ws.max_row + 1):
        ws.cell(r, 14, f"=SUMPRODUCT(MAX((Execucoes!$B$2:$B${MAX_LINHAS}=A{r})*(Execucoes!$F$2:$F${MAX_LINHAS}<>\"\")*ROW(Execucoes!$B$2:$B${MAX_LINHAS})))")
        ws.cell(r, 15, f"=IF(N{r}=0,\"Não executado\",INDEX(Execucoes!$F$1:$F${MAX_LINHAS},N{r}))")
    formatar_corpo(ws, ws.max_row, entrada=(13,))

    ws = aba(wb, "Execucoes", ["Execução", "Caso", "Requisito", "Data", "Versão", "Resultado", "Evidência", "Defeito", "Executor", "Observação"],
             [10, 8, 10, 12, 10, 14, 30, 10, 16, 40])
    for i in range(2, MAX_LINHAS + 1):
        if i - 2 < len(CASOS):
            ws.cell(i, 1, f"EX-{i - 1:03d}")
            ws.cell(i, 2, CASOS[i - 2][0])
        ws.cell(i, 3, f"=IFERROR(INDEX(Casos!$C$2:$C$200,MATCH(B{i},Casos!$A$2:$A$200,0)),\"\")")
    formatar_corpo(ws, MAX_LINHAS, entrada=(1, 2, 4, 5, 6, 7, 8, 9, 10))
    validacao(ws, ["Aprovado", "Reprovado", "Bloqueado", "Não executado"], f"F2:F{MAX_LINHAS}")

    ws = aba(wb, "Defeitos", ["ID", "Título", "Requisito", "Caso", "Ambiente e versão", "Pré-condições", "Dados utilizados",
                              "Passos para reproduzir", "Resultado esperado", "Resultado obtido", "Severidade", "Prioridade",
                              "Evidências", "Status", "Responsável", "Retestado", "Reaberto", "Link da issue"],
             [8, 30, 9, 8, 18, 22, 20, 35, 25, 25, 10, 10, 20, 16, 14, 10, 10, 30])
    formatar_corpo(ws, MAX_LINHAS, entrada=tuple(range(1, 19)))
    validacao(ws, ["Crítica", "Alta", "Média", "Baixa"], f"K2:K{MAX_LINHAS}")
    validacao(ws, ["Alta", "Média", "Baixa"], f"L2:L{MAX_LINHAS}")
    validacao(ws, ["Novo", "Em análise", "Em correção", "Pronto para reteste", "Encerrado", "Reaberto"], f"N2:N{MAX_LINHAS}")
    validacao(ws, ["Sim", "Não"], f"P2:Q{MAX_LINHAS}")

    ws = aba(wb, "Rastreabilidade", ["Requisito", "Risco(s)", "Caso(s)", "Automação", "Não funcional", "Execuções", "Defeito(s)", "Situação"],
             [10, 18, 36, 36, 14, 11, 11, 16])
    for r, (rid, *_) in enumerate(REQUISITOS, start=2):
        ws.cell(r, 1, rid)
        ws.cell(r, 2, "; ".join(x[0] for x in RISCOS if x[2] == rid))
        ws.cell(r, 3, "; ".join(c[0] for c in CASOS if c[2] == rid))
        ws.cell(r, 4, "; ".join(a[0] for a in AUTOMACAO if a[5] == rid))
        ws.cell(r, 5, "; ".join(n[0] for n in NAO_FUNCIONAIS if n[2] == rid))
        # Conta só execuções com resultado Aprovado ou Reprovado (Bloqueado não é teste executado).
        ws.cell(r, 6, f"=COUNTIFS(Execucoes!$C$2:$C${MAX_LINHAS},A{r},Execucoes!$F$2:$F${MAX_LINHAS},\"Aprovado\")"
                      f"+COUNTIFS(Execucoes!$C$2:$C${MAX_LINHAS},A{r},Execucoes!$F$2:$F${MAX_LINHAS},\"Reprovado\")"
                      f"+COUNTIFS(NaoFuncionais!$C$2:$C$100,A{r},NaoFuncionais!$I$2:$I$100,\"<>\")")
        ws.cell(r, 7, f"=COUNTIF(Defeitos!$C$2:$C${MAX_LINHAS},A{r})")
        ws.cell(r, 8, f"=IF(F{r}=0,\"Não testado\",IF(COUNTIFS(Casos!$C$2:$C$200,A{r},Casos!$O$2:$O$200,\"Reprovado\")"
                      f"+COUNTIFS(NaoFuncionais!$C$2:$C$100,A{r},NaoFuncionais!$J$2:$J$100,\"Não atende\")>0,\"Com falha\",\"Atendido\"))")
    formatar_corpo(ws, ws.max_row)

    ws = aba(wb, "NaoFuncionais", ["ID", "Categoria", "Requisito", "Objetivo", "Ambiente", "Métrica/critério", "Procedimento",
                                    "Dados e repetições", "Resultado obtido", "Conclusão", "Evidências"],
             [7, 15, 9, 32, 24, 28, 40, 20, 28, 16, 24], NAO_FUNCIONAIS)
    formatar_corpo(ws, ws.max_row, entrada=(9, 10, 11))
    validacao(ws, ["Atende", "Atende parcialmente", "Não atende"], "J2:J100")

    ws = aba(wb, "Aceitacao", ["ID", "Requisito", "Cenário (Dado/Quando/Então)", "Dados", "Critério de sucesso", "Participante",
                               "Observações", "Dificuldades", "Decisão"],
             [7, 12, 55, 25, 30, 16, 28, 28, 18], ACEITACAO)
    formatar_corpo(ws, ws.max_row, entrada=(6, 7, 8, 9))
    validacao(ws, ["Aceito", "Aceito com ressalvas", "Não aceito"], "I2:I50")

    ws = aba(wb, "Automacao", ["ID do teste", "Nível", "Ferramenta", "Arquivo", "Caso(s) manual(is)", "Requisito"],
             [10, 16, 28, 48, 16, 10], AUTOMACAO)
    formatar_corpo(ws, ws.max_row)

    ws = aba(wb, "Metricas", ["Indicador", "Valor", "Fonte dos dados", "Cálculo", "Interpretação (grupo)"],
             [28, 12, 34, 44, 60], [(m[0], m[1], m[2], m[3], "") for m in METRICAS])
    formatar_corpo(ws, ws.max_row, entrada=(5,))
    for r in range(2, ws.max_row + 1):
        if ws.cell(r, 1).value in PERCENTUAIS:
            ws.cell(r, 2).number_format = "0.0%"

    ws = aba(wb, "Diario", ["Data", "Atividade", "Responsável principal", "Colaboradores", "Tempo (h)", "Evidência"],
             [12, 50, 20, 24, 10, 36])
    formatar_corpo(ws, 100, entrada=tuple(range(1, 7)))

    SAIDA.parent.mkdir(exist_ok=True)
    wb.save(SAIDA)
    print(f"gerado: {SAIDA} ({len(REQUISITOS)} requisitos, {len(RISCOS)} riscos, {len(CASOS)} casos, "
          f"{len(AUTOMACAO)} testes automatizados, {len(NAO_FUNCIONAIS)} não funcionais, {len(ACEITACAO)} aceitação)")


if __name__ == "__main__":
    main()
