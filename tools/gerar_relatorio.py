"""Gera docs/P12-relatorio-final.docx e .pdf a partir da planilha e dos documentos.

Uso: tools/.venv/bin/python tools/gerar_relatorio.py
Rode de novo depois de preencher as abas Aceitacao e NaoFuncionais ou a data do P01.
A planilha precisa ter os valores calculados gravados (salve no Excel ou no LibreOffice).
"""
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor
from openpyxl import load_workbook

RAIZ = Path(__file__).resolve().parent.parent
DOCS = RAIZ / "docs"
GRAFICOS = DOCS / "graficos"
SAIDA = DOCS / "P12-relatorio-final.docx"
COR_GRAFICO = "#0F4C5C"
COR_TITULO = RGBColor(0x0F, 0x4C, 0x5C)
REPO = "https://github.com/mcoldibelli/testes"


def linhas(ws, ate=None):
    return [r[:ate] for r in ws.iter_rows(min_row=2, values_only=True) if r[0]]


def pct(v):
    return f"{v * 100:.1f}%".replace(".", ",")


def tabela_md(arquivo, cabecalho):
    """Linhas da tabela Markdown cujo cabeçalho começa com o texto dado."""
    saida, dentro = [], False
    for t in (DOCS / arquivo).read_text(encoding="utf-8").splitlines():
        if t.startswith("| " + cabecalho):
            dentro = True
            continue
        if dentro:
            if not t.startswith("|"):
                break
            if not t.startswith("|---"):
                saida.append([c.strip().replace("`", "").replace("*", "") for c in t.strip("|").split("|")])
    return saida


def campo_p01(rotulo):
    for t in (DOCS / "P01-ficha-do-sistema.md").read_text(encoding="utf-8").splitlines():
        partes = [p.strip() for p in t.split("|")]
        if len(partes) > 2 and partes[1] == rotulo:
            return partes[2]
    raise KeyError(rotulo)


def ler_dados():
    wb = load_workbook(DOCS / "P2_TQS_planilha.xlsx", data_only=True)
    metricas = {r[0]: r for r in linhas(wb["Metricas"], 5)}
    if metricas["Casos planejados"][1] is None:
        raise SystemExit("A planilha não tem valores calculados: abra e salve no Excel ou no LibreOffice.")
    return {
        "req": linhas(wb["Requisitos"], 5),
        "riscos": linhas(wb["Riscos"], 7),
        "casos": linhas(wb["Casos"], 15),
        "exec": linhas(wb["Execucoes"], 10),
        "def": linhas(wb["Defeitos"], 18),
        "rastro": linhas(wb["Rastreabilidade"], 8),
        "nf": linhas(wb["NaoFuncionais"], 11),
        "ac": linhas(wb["Aceitacao"], 9),
        "auto": linhas(wb["Automacao"], 6),
        "met": metricas,
        "diario": linhas(wb["Diario"], 6),
    }


def graficos(d):
    GRAFICOS.mkdir(exist_ok=True)
    plt.rcParams.update({"font.family": "Arial", "font.size": 10, "axes.spines.top": False, "axes.spines.right": False})
    m = d["met"]

    def fim(fig, nome):
        fig.tight_layout()
        fig.savefig(GRAFICOS / nome, dpi=200)
        plt.close(fig)

    rotulos = ["Percentual de execução", "Aprovação no 1º ciclo", "Aprovação final", "Cobertura de requisitos", "Taxa de automação"]
    valores = [m["Percentual de execução"][1], m["Aprovação no 1º ciclo"][1], m["Taxa de aprovação"][1],
               m["Cobertura de requisitos"][1], m["Taxa de automação"][1]]
    fig, ax = plt.subplots(figsize=(6.6, 2.7))
    barras = ax.barh(rotulos, [v * 100 for v in valores], color=COR_GRAFICO, height=0.5)
    ax.bar_label(barras, [pct(v) for v in valores], padding=4)
    ax.invert_yaxis()
    ax.set_xlim(0, 115)
    ax.set_xticks([])
    ax.spines["bottom"].set_visible(False)
    fim(fig, "indicadores.png")

    sev = ["Crítica", "Alta", "Média", "Baixa"]
    vals = [m[f"Defeitos - {s}"][1] for s in sev]
    fig, ax = plt.subplots(figsize=(4.4, 2.5))
    barras = ax.bar(sev, vals, color=COR_GRAFICO, width=0.45)
    ax.bar_label(barras, padding=3)
    ax.set_yticks([])
    ax.spines["left"].set_visible(False)
    fim(fig, "defeitos_severidade.png")

    niveis = {"Unitário": "Unitário", "Integração": "Integração Go", "Integração/API": "API (Postman)", "Sistema/interface": "Interface (Selenium)"}
    cont = [sum(1 for a in d["auto"] if a[1] == k) for k in niveis]
    fig, ax = plt.subplots(figsize=(4.8, 2.5))
    barras = ax.barh(list(niveis.values()), cont, color=COR_GRAFICO, height=0.5)
    ax.bar_label(barras, padding=4)
    ax.invert_yaxis()
    ax.set_xticks([])
    ax.spines["bottom"].set_visible(False)
    fim(fig, "testes_por_nivel.png")


class Relatorio:
    def __init__(self, paginas):
        self.paginas = paginas  # título da seção -> página, da passada anterior
        self.titulos = []
        self.figura = 0
        self.tab = 0
        doc = self.doc = Document()
        doc.settings.element.find(qn("w:zoom")).set(qn("w:percent"), "100")
        sec = doc.sections[0]
        sec.page_width, sec.page_height = Cm(21), Cm(29.7)
        sec.left_margin, sec.top_margin = Cm(3), Cm(2.5)
        sec.right_margin, sec.bottom_margin = Cm(2), Cm(2)
        st = doc.styles["Normal"]
        st.font.name, st.font.size = "Arial", Pt(11)
        st.element.rPr.rFonts.set(qn("w:eastAsia"), "Arial")
        st.paragraph_format.space_after = Pt(6)
        st.paragraph_format.line_spacing = 1.15
        for nome, tam, antes in (("Heading 1", 15, 0), ("Heading 2", 12, 12), ("Title", 22, 0)):
            h = doc.styles[nome]
            h.font.name, h.font.size, h.font.bold = "Arial", Pt(tam), True
            h.font.color.rgb = COR_TITULO
            h.element.rPr.rFonts.set(qn("w:asciiTheme"), "")
            for at in list(h.element.rPr.rFonts.attrib):
                if "Theme" in at:
                    del h.element.rPr.rFonts.attrib[at]
            h.element.rPr.rFonts.set(qn("w:ascii"), "Arial")
            h.element.rPr.rFonts.set(qn("w:hAnsi"), "Arial")
            h.paragraph_format.space_before = Pt(antes)
            h.paragraph_format.space_after = Pt(8)
            h.paragraph_format.keep_with_next = True
        pe = sec.footer.paragraphs[0]
        pe.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        r = pe.add_run()
        for tipo, texto in (("begin", None), (None, "PAGE"), ("end", None)):
            if tipo:
                el = OxmlElement("w:fldChar")
                el.set(qn("w:fldCharType"), tipo)
            else:
                el = OxmlElement("w:instrText")
                el.text = texto
            r._r.append(el)

    def h1(self, texto):
        self.doc.add_paragraph().add_run().add_break(WD_BREAK.PAGE)
        self.doc.add_heading(texto, 1)
        self.titulos.append(texto)

    def h2(self, texto):
        self.doc.add_heading(texto, 2)

    def p(self, texto, negrito=False, centro=False, tam=None):
        par = self.doc.add_paragraph()
        for i, trecho in enumerate(re.split(r"\*\*", texto)):
            r = par.add_run(trecho)
            r.bold = negrito or i % 2 == 1
            if tam:
                r.font.size = Pt(tam)
        par.alignment = WD_ALIGN_PARAGRAPH.CENTER if centro else WD_ALIGN_PARAGRAPH.LEFT
        return par

    def lista(self, itens):
        for t in itens:
            par = self.doc.add_paragraph(style="List Bullet")
            for i, trecho in enumerate(re.split(r"\*\*", t)):
                par.add_run(trecho).bold = i % 2 == 1

    def legenda(self, tipo, texto):
        if tipo == "Tabela":
            self.tab += 1
            n = self.tab
        else:
            self.figura += 1
            n = self.figura
        par = self.p(f"{tipo} {n}: {texto}", negrito=True, tam=9.5)
        par.paragraph_format.keep_with_next = tipo == "Tabela"
        par.paragraph_format.space_before = Pt(6)

    def tabela(self, legenda, cab, dados, larguras, tam=8.5):
        self.legenda("Tabela", legenda)
        t = self.doc.add_table(rows=1, cols=len(cab))
        t.style = "Table Grid"
        t.alignment = WD_TABLE_ALIGNMENT.CENTER
        t.autofit = False
        for j, largura in enumerate(larguras):
            t.columns[j].width = Cm(largura)
        linhas_t = [cab] + [["" if c is None else str(c) for c in lin] for lin in dados]
        for i, lin in enumerate(linhas_t):
            cels = t.rows[0].cells if i == 0 else t.add_row().cells
            for j, txt in enumerate(lin):
                cels[j].width = Cm(larguras[j])
                par = cels[j].paragraphs[0]
                par.paragraph_format.space_after = Pt(1)
                par.paragraph_format.line_spacing = 1.0
                run = par.add_run(txt.replace("\n", " "))
                run.font.size = Pt(tam)
                if i == 0:
                    run.bold = True
                    run.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
                    fundo = OxmlElement("w:shd")
                    fundo.set(qn("w:val"), "clear")
                    fundo.set(qn("w:fill"), "0F4C5C")
                    cels[j]._tc.get_or_add_tcPr().append(fundo)
        cab_el = OxmlElement("w:tblHeader")
        t.rows[0]._tr.get_or_add_trPr().append(cab_el)
        for lin in t.rows:
            nao = OxmlElement("w:cantSplit")
            lin._tr.get_or_add_trPr().append(nao)
        self.doc.add_paragraph().paragraph_format.space_after = Pt(4)

    def imagem(self, caminho, legenda, largura, alt):
        par = self.doc.add_paragraph()
        par.alignment = WD_ALIGN_PARAGRAPH.CENTER
        par.paragraph_format.keep_with_next = True
        fig = par.add_run().add_picture(str(caminho), width=Cm(largura))
        fig._inline.docPr.set("descr", alt)
        self.legenda("Figura", legenda)


def escrever(d, paginas):
    r = Relatorio(paginas)
    m = d["met"]
    ac_feitos = [a for a in d["ac"] if a[8]]
    nf07 = next(n for n in d["nf"] if n[0] == "NF-07")
    nf_feitos = [n for n in d["nf"] if n[9]]
    data_p01 = campo_p01("Data da aprovação")
    data_p01 = "a informar" if "informar" in data_p01 else data_p01
    decisao = campo_p01("Decisão do professor")
    primeira = [e for e in d["exec"] if int(e[0][3:]) <= 31]
    aprov1 = sum(e[5] == "Aprovado" for e in primeira)
    sim = sum(c[10] == "Sim" for c in d["casos"])
    auto = sum(1 for c in d["casos"] if c[10] == "Sim" and c[11])
    tecnicas = {}
    for c in d["casos"]:
        tecnicas[c[4]] = tecnicas.get(c[4], 0) + 1
    niveis = {}
    for a in d["auto"]:
        niveis[a[1]] = niveis.get(a[1], 0) + 1
    cob = m["Cobertura de requisitos"][1]
    nao_testados = [x[0] for x in d["rastro"] if x[7] == "Não testado"]

    # Capa
    for t, tam, neg in (("UNISAGRADO", 20, True), ("Curso de Ciência da Computação", 13, False), ("Disciplina: Testes e Qualidade de Software", 13, False)):
        r.p(t, negrito=neg, centro=True, tam=tam)
    for _ in range(5):
        r.doc.add_paragraph()
    r.p("Projeto Integrado P2", negrito=True, centro=True, tam=20)
    r.p("Planejamento, execução e avaliação da qualidade de um sistema de software", centro=True, tam=14)
    r.p("Relatório final", centro=True, tam=14)
    r.p("Sistema: Ordens de Serviço, versão 1.0.0", negrito=True, centro=True, tam=13)
    for _ in range(6):
        r.doc.add_paragraph()
    r.p("Integrante: Marcelo A. B. Coldibelli (RA 24210023)", centro=True)
    r.p("Professor: Prof. Dr. Elvio Gilberto da Silva", centro=True)
    r.p("2026", centro=True)

    # Folha de identificação
    r.doc.add_paragraph().add_run().add_break(WD_BREAK.PAGE)
    r.p("Folha de identificação", negrito=True, tam=15)
    r.tabela("Dados do trabalho", ["Campo", "Valor"], [
        ("Turma e grupo", "Turma B, grupo AP1-TIM 26"),
        ("Integrante e papéis", "Marcelo A. B. Coldibelli: coordenação e planejamento; análise e execução manual; automação e qualidade (trabalho individual)"),
        ("Decisão do professor sobre o sistema (P01)", f"{decisao}. Data: {data_p01}"),
        ("Repositório", REPO),
        ("Defeitos", REPO + "/issues"),
        ("Pipeline", REPO + "/actions"),
        ("Versão testada", "1.0.0 (commit 8bfb1c6), com correções e TDD até o commit f107a8d"),
    ], [5.5, 10.5], tam=9.5)
    r.p("Declaração de participação", negrito=True)
    r.p("O trabalho é individual. O único integrante responde por todas as atividades registradas no Diário de Participação (Apêndice L).")
    r.p("Uso de inteligência artificial (manual, seção 15)", negrito=True)
    r.p("O assistente Claude Code (Anthropic) foi usado como apoio ao longo do projeto, inclusive nas correções de defeitos indicadas em docs/GUIA-PASSO-A-PASSO.md (parte C). Em 05/11/2026, ele executou os comandos do ciclo de TDD e do pipeline e a segunda análise do SonarQube, interpretou as métricas e redigiu este relatório e a apresentação, sempre a partir dos arquivos e dos resultados reais do projeto. As execuções manuais EX-001 a EX-041 têm o integrante como executor. O integrante é responsável por revisar, compreender e validar todo o conteúdo antes da entrega.")

    # Sumário
    r.doc.add_paragraph().add_run().add_break(WD_BREAK.PAGE)
    r.p("Sumário", negrito=True, tam=15)
    marcador_sumario = r.doc.add_paragraph()

    # 1
    r.h1("1. Introdução")
    r.p("**Contexto.** Uma empresa de manutenção de sistemas de segurança precisa registrar clientes e controlar ordens de serviço (OS) com prazo definido pela prioridade. O sistema Ordens de Serviço atende a esse cenário e é o objeto de teste deste projeto.")
    r.p("**Problema.** Como demonstrar, por meio de um processo de teste planejado, executado e documentado, que o sistema atende aos requisitos selecionados e quais riscos, defeitos e oportunidades de melhoria permanecem antes de sua disponibilização aos usuários?")
    r.p("**Justificativa.** O sistema tem regras com intervalos e estados (CPF, limites de texto e de valor, prazo por prioridade, máquina de estados). Essas regras permitem aplicar particionamento de equivalência, análise de valor limite e tabela de decisão. O código-fonte está disponível, então todos os níveis de teste são possíveis.")
    r.p("**Objetivo.** Elaborar e executar uma estratégia integrada de testes e qualidade, com evidências técnicas e gerenciais para avaliar o comportamento, a confiabilidade, a usabilidade e a prontidão do sistema dentro do escopo definido.")

    # 2
    r.h1("2. Caracterização do sistema")
    r.p("**Finalidade.** Cadastrar clientes, abrir OS com prazo calculado pela prioridade, controlar o status da OS e mostrar um painel com as OS atrasadas.")
    r.p("**Usuários.** Atendente, técnico e supervisor. O sistema usa dois usuários fictícios criados nos dados iniciais; o escopo não inclui perfis diferentes por usuário.")
    r.tabela("Tecnologias", ["Camada", "Tecnologia"], [
        ("Linguagem e servidor web", "Go 1.26 (net/http, html/template)"),
        ("Banco de dados", "SQLite (driver Go modernc.org/sqlite)"),
        ("Testes unitários e de integração", "Pacote testing do Go, net/http/httptest"),
        ("Testes de API", "Postman (coleção) e Newman"),
        ("Testes de interface", "Selenium 4 e pytest (Python)"),
        ("Análise de qualidade", "SonarQube Community (Docker)"),
        ("CI/CD e defeitos", "GitHub Actions e GitHub Issues"),
    ], [7, 9])
    r.p("**Arquitetura resumida.** O navegador (HTML) e os clientes da API (JSON) chamam internal/web, que trata rotas e sessão. Esse pacote chama internal/app (casos de uso), que usa internal/domain (regras de negócio puras) e internal/store (SQL no SQLite).")
    r.p("**Versão testada.** 1.0.0, commit de origem 8bfb1c6. As correções de defeitos e a evolução por TDD foram aplicadas até o commit f107a8d.")

    # 3
    r.h1("3. Escopo, requisitos e riscos")
    r.p("**Incluído.** 7 requisitos funcionais e 5 não funcionais (mínimo do manual: 6 e 2). **Excluído.** Cadastro e edição de usuários; edição e exclusão de clientes e de OS; perfis diferentes; recuperação de senha e envio de e-mail; teste de carga, de invasão ou destrutivo; implantação em produção.")
    r.tabela("Requisitos no escopo", ["ID", "Descrição", "Tipo", "Prioridade"], [x[:4] for x in d["req"]], [1.7, 9.9, 2.4, 2])
    r.tabela("Matriz de riscos", ["ID", "Risco", "Req.", "Prob.", "Impacto", "Prior.", "Resposta/teste"], d["riscos"], [1.2, 4.4, 1.5, 1.3, 1.6, 1.3, 4.7], tam=8)
    r.p("R-12 a R-15 foram incluídos em 05/11/2026, na revisão final, porque RF-06, RF-07, RNF-02 e RNF-04 não tinham risco ligado. Eles não orientaram a execução dos testes de setembro e outubro.")

    # 4
    r.h1("4. Planejamento dos testes")
    r.p("O plano completo está em docs/P03-plano-de-testes.md. A estratégia concentra a maior parte dos testes nos níveis mais baixos, que são rápidos e estáveis, e usa testes de interface só nos fluxos críticos. Os riscos de prioridade Alta são testados primeiro.")
    r.tabela("Níveis e ferramentas", ["Nível", "O que verifica", "Ferramenta", "Qtd. (mínimo)"], [
        ("Unitário", "Regras puras, sem banco nem rede", "Go testing", f"{niveis['Unitário']} (6)"),
        ("Integração", "HTTP, serviço e SQLite real", "Go testing, httptest", str(niveis["Integração"])),
        ("Integração/API", "Contrato, status e encadeamento", "Postman, Newman", f"{niveis['Integração/API']} (5)"),
        ("Sistema/interface", "Fluxos ponta a ponta", "Selenium, pytest", f"{niveis['Sistema/interface']} (4)"),
        ("Sistema manual", "CT-01 a CT-31", "Navegador, planilha", f"{len(d['casos'])} (24)"),
        ("Aceitação", "AC-01 a AC-04", "Roteiro, planilha", f"{len(d['ac'])} (4)"),
        ("Não funcional", "NF-01 a NF-08, em 5 categorias", "Script, DevTools, Selenium", f"{len(d['nf'])} (6)"),
    ], [3, 6, 4, 3])
    r.p("**Ambiente.** macOS 26.6.2 (Apple M2 Pro), Chrome 154.0.8037.93, Firefox 156.0.1, e ubuntu-latest no CI. **Dados.** Somente dados fictícios; o parâmetro -reset recria 2 usuários, 3 clientes e 6 OS, e os scripts geram CPF aleatório.")
    r.p("**Critérios de entrada.** Sistema aprovado, build sem erro, make test-unit aprovado, ambiente restaurado e casos revisados.")
    r.p("**Critérios de saída.** 100% dos casos executados; nenhum defeito Crítico ou Alto aberto; cobertura de requisitos de 100%; pipeline aprovado na versão final.")
    r.p("**Suspensão e retomada.** Suspender quando o sistema não inicia, quando um defeito bloqueia mais de 30% do ciclo ou quando o ambiente fica inconsistente. Retomar com a correção no repositório, o pipeline aprovado e o ambiente restaurado.")

    # 5
    r.h1("5. Especificação dos casos")
    r.p(f"O catálogo completo tem {len(d['casos'])} casos e está na aba Casos de docs/P2_TQS_planilha.xlsx (P04). A aba registra requisito, nível, técnica, prioridade, pré-condições, dados, passos, resultado esperado e automação de cada caso.")
    r.tabela("Técnicas aplicadas nos casos manuais", ["Técnica", "Casos", "Exemplos"], [
        ("Particionamento de equivalência", tecnicas["Particionamento de equivalência"], "CPF válido, com máscara e com dígito errado; formato do valor; filtros"),
        ("Análise de valor limite", tecnicas["Análise de valor limite"], "Nome (2/3/100/101), descrição (9/10/500/501), telefone (9/10/11/12), falhas de login (4/5)"),
        ("Tabela de decisão", tecnicas["Tabela de decisão"], "Transições de status e prazo por prioridade; UT-08 cobre 16 combinações"),
    ], [5.5, 1.5, 9])
    r.p(f"{sim} casos são candidatos à automação; {auto} já têm teste automatizado ligado. Os 3 casos não candidatos são CT-03, CT-15 e CT-21.")

    # 6
    r.h1("6. Execução manual e defeitos")
    r.p(f"O primeiro ciclo ocorreu em 29 e 30/09/2026, com {len(primeira)} execuções: {aprov1} aprovadas e {len(primeira) - aprov1} reprovadas (CT-14 e CT-20). Em 01/10/2026 foram feitas mais 10 execuções de reteste e regressão, todas aprovadas. No total são {len(d['exec'])} execuções, com evidências em docs/evidencias/execucao. Depois do TDD, CT-19 e CT-20 foram verificados pelo formulário em execução, por requisições HTTP (docs/evidencias/tdd/TDD-4_verificacao_no_sistema.txt); essa verificação não foi registrada como execução manual.")
    r.tabela("Defeitos registrados", ["ID", "Título", "Caso", "Sev.", "Status", "Issue"], [
        (x[0], x[1], x[3], x[10], x[13], "#" + x[17].rsplit("/", 1)[1]) for x in d["def"]
    ], [1.3, 8.2, 1.9, 1.2, 1.9, 1.3])
    r.p("**Defeito mais relevante: DEF-02.** No CT-20, a tela mostrava o erro \"use o formato 1234,56\", mas a OS era gravada com R$ 0,00. O defeito compromete dados, por isso a severidade é Alta. A correção veio com um teste escrito antes (IT-11), seguida do reteste EX-032 e da regressão de CT-19 e CT-16.")
    r.imagem(DOCS / "evidencias/execucao/EX-020_CT-20_3.png", "evidência do DEF-02: as OS 16 e 17 gravadas com R$ 0,00 depois do erro (EX-020)", 15, "Lista de ordens de serviço com as OS 16 e 17 gravadas com valor zero.")
    r.p("DEF-01 e DEF-03 seguiram o mesmo processo, com IT-12 e ST-07. DEF-04 surgiu no NF-04 e foi corrigido com ST-08. A exportação dos defeitos está em docs/P07-defeitos.csv.")

    # 7
    r.h1("7. Automação")
    r.p(f"A automação tem {len(d['auto'])} testes em 4 níveis, indicados na aba Automacao com o caso manual ou requisito que cada um representa. O pipeline executa todos a cada envio de código.")
    r.imagem(GRAFICOS / "testes_por_nivel.png", "testes automatizados por nível (aba Automacao)", 10, "Barras: unitário 12, integração Go 12, API 16, interface 8.")
    r.tabela("Resultado na execução aprovada do CI (run 42134677760, artefato resultados-15)", ["Conjunto", "Comando local", "Resultado"], [
        ("Testes Go (unitário e integração)", "make test-unit test-integracao", "25 aprovados, 0 reprovados"),
        ("API (Postman e Newman)", "make test-api", "16 aprovados"),
        ("Interface (Selenium e pytest)", "make test-e2e", "8 aprovados"),
    ], [6, 5, 5])
    r.p("**Limitações.** O Selenium usa Python porque não há cliente oficial em Go. Os testes de API e de interface exigem o sistema em execução. CT-05, CT-12 e CT-31 ainda não são automatizados.")

    # 8
    r.h1("8. Integração e sistema")
    r.p("**Comunicações validadas.** Interface HTML, serviço e banco SQLite (IT-01 a IT-12, com httptest e banco real). API JSON, serviço e banco (API-01 a API-16, com status, contrato, mensagens de erro e encadeamento de dados).")
    r.p("**Fluxos ponta a ponta.** ST-01 a ST-08 cobrem login válido e inválido, cadastro e busca por CPF, CPF inválido, abertura e conclusão de OS, cancelamento sem motivo, posição da mensagem de erro e listas em 375 px, no navegador real. Cada teste salva uma captura de tela, e uma falha também salva o HTML da página e o erro.")

    # 9
    r.h1("9. Aceitação e não funcionais")
    r.h2("Aceitação")
    if len(ac_feitos) == len(d["ac"]):
        r.tabela("Cenários de aceitação", ["ID", "Critério de sucesso", "Participante", "Dificuldades", "Decisão"], [(a[0], a[4], a[5], a[7], a[8]) for a in d["ac"]], [1.5, 5.8, 3, 3.2, 2.5])
    else:
        r.p(f"**Situação em 05/11/2026: {len(ac_feitos)} de {len(d['ac'])} cenários executados.** Os cenários AC-01 a AC-04 estão especificados, mas falta uma pessoa que não tenha feito os testes para executá-los (manual, seção 9.11). Nenhum resultado foi registrado sem execução.")
        r.tabela("Cenários de aceitação especificados", ["ID", "Requisito", "Cenário", "Critério de sucesso", "Decisão"], [(a[0], a[1], a[2], a[4], a[8] or "Não executado") for a in d["ac"]], [1.5, 1.8, 6.5, 3.9, 2.3])
    r.h2("Não funcionais")
    r.tabela("Testes não funcionais", ["ID", "Categoria", "Critério", "Resultado resumido", "Conclusão"], [
        (n[0], n[1], n[5], (n[8] or "Não executado: falta participante.")[:230] + ("..." if n[8] and len(n[8]) > 230 else ""), n[9] or "Não executado") for n in d["nf"]
    ], [1.3, 2.4, 3.8, 6.4, 2.1], tam=8)
    r.p(f"{len(nf_feitos)} de {len(d['nf'])} verificações foram concluídas, em 4 categorias: desempenho, compatibilidade, segurança básica e confiabilidade. O mínimo do manual é 6 verificações em 3 categorias. O resultado completo e as evidências estão na aba NaoFuncionais e em docs/evidencias/nao-funcionais.")
    if not nf07[9]:
        r.p("A categoria usabilidade não tem resultado porque NF-07 precisa de um participante que não construiu o sistema.")

    # 10
    r.h1("10. Métricas e indicadores")
    r.tabela("Painel de métricas (Apêndice K; fórmulas na aba Metricas)", ["Indicador", "Valor", "Cálculo", "Interpretação"], [
        (n, pct(m[n][1]), m[n][3], m[n][4]) for n in ("Percentual de execução", "Taxa de aprovação", "Aprovação no 1º ciclo", "Taxa de reprovação", "Cobertura de requisitos", "Taxa de automação", "Taxa de reabertura")
    ], [3, 1.4, 4.6, 7], tam=8)
    r.imagem(GRAFICOS / "indicadores.png", "indicadores do processo de teste (aba Metricas)", 14, "Barras: execução 100%, aprovação no primeiro ciclo 93,5%, aprovação final 100%, cobertura de requisitos e automação.")
    r.p(f"A aprovação final de {pct(m['Taxa de aprovação'][1])} não indica ausência de defeitos: ela mostra os casos depois das correções. O indicador da versão original é a aprovação no primeiro ciclo, de {pct(m['Aprovação no 1º ciclo'][1])}. A cobertura de requisitos de {pct(cob)} é o indicador que limita a conclusão.")
    r.imagem(GRAFICOS / "defeitos_severidade.png", "defeitos por severidade (aba Metricas)", 9, "Barras: crítica 0, alta 1, média 1, baixa 2.")
    r.tabela("Defeitos por severidade e por status", ["Grupo", "Contagem", "Interpretação"], [
        (n.replace("Defeitos - ", ""), m[n][1], m[n][4]) for n in ("Defeitos - Crítica", "Defeitos - Alta", "Defeitos - Média", "Defeitos - Baixa", "Defeitos - Encerrado", "Defeitos - Reaberto")
    ], [2.4, 2, 11.6])
    r.p("Os status Novo, Em análise, Em correção e Pronto para reteste têm contagem 0.")
    r.p(f"**Cobertura de código.** O CI informa {pct(m['Cobertura de código (Go, por pacote)'][1])} porque conta cada pacote só com os testes dele. Com -coverpkg=./..., o valor é {pct(m['Cobertura de código (Go, -coverpkg)'][1])}, porque inclui store e app, que os testes de web usam.")

    # 11
    r.h1("11. TDD, CI/CD e melhoria contínua")
    r.h2("Ciclo de TDD")
    r.tabela("Evolução por TDD: aceitar 1.500,00 no valor da OS", ["Etapa", "Commit", "O que ocorreu"], [
        ("RED", "a31aa49", "UT-12 passou a exigir 1.500,00 = 150000 e 12.345,6 = 1234560. O teste falhou porque os dois valores eram recusados."),
        ("GREEN", "5568311", "Nova regex de milhar em ParseValor, com o mínimo de código. Teste aprovado."),
        ("REFACTOR", "f107a8d", "Regexes agrupadas, nome formatoDecimal e regra documentada. 25 testes Go aprovados, 0 reprovados."),
    ], [2.2, 2, 11.8])
    r.h2("Pipeline")
    r.p("Arquivo .github/workflows/ci.yml, com gatilhos push e pull_request. Etapas: preparação, go vet, testes Go com -race e cobertura, build, Newman, Selenium e publicação do artefato.")
    r.tabela("Demonstração no PR #5", ["Execução", "Commit", "Resultado"], [
        ("Run 42134250857 (push) e 42134260225 (PR)", "a049d06", "Falha controlada: TestNovaOrdem_PrazoPorPrioridade, no passo de testes Go"),
        ("Run 42134677760 (push) e 42134685386 (PR)", "2bc5bda", "Aprovado depois de desfazer a mudança; artefato resultados-15"),
    ], [6.5, 1.8, 7.7])
    r.h2("Análise de qualidade")
    r.tabela("SonarQube: linha de base e segunda análise", ["Indicador", "Linha de base", "Depois", "Diferença", "Interpretação"], tabela_md("P11-roteiro-tdd-cicd-qualidade.md", "Indicador"), [2.6, 2.3, 2.3, 1.6, 7.2])
    r.p("Limitação: o contêiner da linha de base não existia mais em 05/11/2026. A segunda análise usou uma instância nova e outra versão (26.9 e 26.11). Os valores da linha de base vêm do registro de 29/09/2026 (commit e97db23).")
    r.imagem(DOCS / "evidencias/sonar/SONAR_DEPOIS_2026-11-05.png", "segunda análise do SonarQube, em 05/11/2026", 13, "Painel do SonarQube com Quality Gate aprovado e cobertura de 37,8%.")
    r.h2("Plano de melhoria contínua")
    r.tabela("Ações priorizadas", ["Ação", "Motivo", "Prior.", "Critério de verificação"], [(x[0], x[1], x[2], x[4]) for x in tabela_md("P11-roteiro-tdd-cicd-qualidade.md", "Ação")], [5, 5, 1.2, 4.8], tam=8)
    r.p("Responsável por todas as ações: Marcelo A. B. Coldibelli.")

    # 12
    r.h1("12. Discussão dos resultados")
    r.h2("Pontos fortes")
    r.lista([
        "Cada um dos 4 defeitos teve teste automatizado escrito antes da correção, reteste e nenhuma reabertura.",
        "Os testes automatizados rodam a cada envio de código, em 4 níveis, e cobrem 25 dos 28 casos candidatos.",
        "Os valores de desempenho ficaram muito abaixo dos limites: p95 de 4,3 ms contra 500 ms e login médio de 66,6 ms contra 1 s, em ambiente local.",
    ])
    r.h2("Pontos frágeis e limitações")
    frageis = [
        "O teste manual e os testes não funcionais foram feitos por uma só pessoa, que também construiu o sistema. Isso reduz a independência dos resultados.",
        "As medições de desempenho usam uma só máquina local e não representam uso real.",
        "As execuções se concentram em 29/09 a 01/10 e em 05/11/2026; o Diário mostra pouco trabalho distribuído ao longo do semestre.",
        "Os riscos R-12 a R-15 entraram na matriz só na revisão final.",
    ]
    if len(ac_feitos) < len(d["ac"]):
        frageis.insert(0, "A aceitação não foi executada, então não há validação do ponto de vista do usuário.")
    r.lista(frageis)
    r.h2("Riscos residuais")
    residuais = [
        "Os formulários não têm token CSRF; o cookie SameSite=Lax só reduz o risco.",
        "O bloqueio de login e as sessões ficam na memória e são perdidos ao reiniciar (R-05).",
        "As listas de clientes mostram no máximo 200 registros.",
    ]
    if not nf07[9]:
        residuais.insert(0, "R-15: usabilidade não verificada (NF-07 não executado).")
    r.lista(residuais)

    # 13
    r.h1("13. Conclusão")
    r.p(f"O processo de teste executou {len(d['casos'])} casos manuais em {len(d['exec'])} execuções, {len(d['auto'])} testes automatizados e {len(nf_feitos)} verificações não funcionais. Encontrou 4 defeitos reais, todos corrigidos e retestados, e nenhum ficou aberto. A evolução por TDD, o pipeline e as duas análises de qualidade têm evidências.")
    if nao_testados or len(ac_feitos) < len(d["ac"]):
        r.p(f"**Prontidão.** Dentro do escopo funcional testado, o sistema se comportou como especificado. Porém, o critério de saída de cobertura de requisitos não foi atendido ({pct(cob)}: {', '.join(nao_testados) or 'sem pendência'} sem teste), e a aceitação tem {len(ac_feitos)} de {len(d['ac'])} cenários executados. Por isso, o sistema ainda não pode ser declarado pronto para uso.")
    else:
        r.p(f"**Prontidão.** Todos os critérios de saída do plano foram atendidos, com cobertura de requisitos de {pct(cob)} e {len(ac_feitos)} cenários de aceitação executados. O sistema está pronto para uso dentro do escopo testado, com os riscos residuais da seção 12.")
    r.p("**Recomendações.** Executar as ações de prioridade Alta do plano de melhoria antes de qualquer disponibilização a usuários. Não usar o sistema em produção sem tratar os riscos residuais.")

    # Referências
    r.h1("Referências")
    r.lista([
        "SILVA, Elvio Gilberto da. Projeto Integrado P2: manual completo de desenvolvimento e entrega para os estudantes. UNISAGRADO, 2026.",
        "Go. Documentação do pacote testing. https://pkg.go.dev/testing",
        "Selenium. Documentação oficial. https://www.selenium.dev/documentation/",
        "Postman. Newman: linha de comando. https://learning.postman.com/docs/collections/using-newman-cli/",
        "SonarSource. Documentação do SonarQube Community Build. https://docs.sonarsource.com/sonarqube-community-build/",
        "GitHub. Documentação do GitHub Actions. https://docs.github.com/actions",
        "Anthropic. Claude Code, assistente de IA usado como apoio. https://claude.com/claude-code",
    ])

    # Apêndices
    r.h1("Apêndices e anexos")
    r.tabela("Apêndice H: matriz de rastreabilidade", ["Requisito", "Risco", "Casos", "Automação", "NF", "Exec.", "Def.", "Situação"], d["rastro"], [1.5, 1.5, 3.2, 4.1, 1.5, 1, 0.8, 1.9], tam=7.5)
    r.tabela("Apêndice L: diário de participação", ["Data", "Atividade", "Responsável", "Colaboradores", "Tempo (h)"], [x[:5] for x in d["diario"]], [1.9, 7.6, 2.6, 2.6, 1.3], tam=8)
    r.p("Apêndice M: declaração final do grupo", negrito=True)
    r.p("Declaramos que os arquivos entregues representam o trabalho efetivamente realizado pelo grupo, que as execuções e métricas são reais, que os dados utilizados são fictícios e que respeitamos as autorizações, licenças e orientações da disciplina.")
    r.p("Integrante 1: ______________________________  Data: ____/____/________")
    r.tabela("Anexos no repositório e no Drive", ["Produto", "Local"], [
        ("P04, P05, P06, P10, P14", "docs/P2_TQS_planilha.xlsx"),
        ("P06 evidências", "docs/evidencias/execucao"),
        ("P07 defeitos", "Issues do repositório e docs/P07-defeitos.csv"),
        ("P08 scripts", "internal/**/*_test.go, tests/postman, tests/e2e"),
        ("P09 evidências", "docs/evidencias/nao-funcionais e aba Aceitacao"),
        ("P11 TDD, CI/CD e qualidade", "docs/P11-roteiro-tdd-cicd-qualidade.md, docs/evidencias/tdd, cicd e sonar"),
    ], [6, 10], tam=9)

    # Sumário preenchido com a página de cada seção
    for titulo in r.titulos:
        par = marcador_sumario.insert_paragraph_before()
        par.paragraph_format.tab_stops.add_tab_stop(Cm(16), alignment=2, leader=1)
        par.add_run(f"{titulo}\t{paginas.get(titulo, '')}")
    return r.doc, r.titulos


def para_pdf(docx, destino):
    subprocess.run(["soffice", "--headless", "--convert-to", "pdf", "--outdir", str(destino), str(docx)],
                   check=True, capture_output=True, timeout=180)
    return Path(destino) / (Path(docx).stem + ".pdf")


def paginas_do_pdf(pdf, titulos):
    texto = subprocess.run(["pdftotext", "-layout", str(pdf), "-"], check=True, capture_output=True, text=True).stdout
    paginas, resultado = texto.split("\f"), {}
    for titulo in titulos:
        for n, pagina in enumerate(paginas, 1):
            # A primeira linha com o título exato, depois do sumário (página 3).
            if n > 3 and any(linha.strip() == titulo for linha in pagina.splitlines()):
                resultado[titulo] = n
                break
    return resultado


def main():
    d = ler_dados()
    graficos(d)
    paginas = {}
    with tempfile.TemporaryDirectory() as tmp:
        for _ in range(2):  # a segunda passada grava as páginas no sumário
            doc, titulos = escrever(d, paginas)
            caminho = Path(tmp) / SAIDA.name
            doc.save(caminho)
            pdf = para_pdf(caminho, tmp)
            paginas = paginas_do_pdf(pdf, titulos)
        faltam = [t for t in titulos if t not in paginas]
        if faltam:
            raise SystemExit(f"Títulos não encontrados no PDF: {faltam}")
        shutil.copy(caminho, SAIDA)
        shutil.copy(pdf, SAIDA.with_suffix(".pdf"))
    print(f"Gerados {SAIDA.name} e {SAIDA.with_suffix('.pdf').name}: {paginas}")


if __name__ == "__main__":
    main()
