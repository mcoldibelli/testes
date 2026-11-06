"""Gera docs/P13-apresentacao.pptx e .pdf a partir da planilha.

Uso: tools/.venv/bin/python tools/gerar_apresentacao.py
Rode de novo depois de preencher as abas Aceitacao e NaoFuncionais.
"""
import re
import subprocess
import sys
from pathlib import Path

from PIL import Image
from pptx import Presentation
from pptx.chart.data import CategoryChartData
from pptx.dml.color import RGBColor
from pptx.enum.chart import XL_CHART_TYPE, XL_LABEL_POSITION
from pptx.enum.dml import MSO_THEME_COLOR as TEMA
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.opc.constants import RELATIONSHIP_TYPE as RT
from pptx.util import Inches, Pt

sys.path.insert(0, str(Path(__file__).resolve().parent))
from gerar_relatorio import DOCS, GRAFICOS, ler_dados, pct, tabela_md

SAIDA = DOCS / "P13-apresentacao.pptx"
CORES = {"dk1": "1B2A30", "lt1": "FFFFFF", "dk2": "0F4C5C", "lt2": "EAF1F3", "accent1": "0F4C5C", "accent2": "C8511B",
         "accent3": "5F7C86", "accent4": "2E7D5B", "accent5": "8A9BA1", "accent6": "D9E4E7", "hlink": "0F4C5C", "folHlink": "5F7C86"}


def aplicar_tema(prs):
    """Grava cores e fontes no tema, para mudar a aparência em um só lugar."""
    parte = prs.slide_master.part.part_related_by(RT.THEME)
    xml = parte.blob.decode("utf-8")
    for nome, cor in CORES.items():
        xml = re.sub(rf"(<a:{nome}>).*?(</a:{nome}>)", rf'\g<1><a:srgbClr val="{cor}"/>\g<2>', xml, flags=re.S)
    xml = re.sub(r'(<a:majorFont>\s*<a:latin typeface=")[^"]*', r"\g<1>Cambria", xml)
    xml = re.sub(r'(<a:minorFont>\s*<a:latin typeface=")[^"]*', r"\g<1>Calibri", xml)
    parte._blob = xml.encode("utf-8")


def preparar_layout(prs):
    """Adapta o layout "Title Only" ao formato 16:9, com o título sempre na mesma posição."""
    prs.slide_width, prs.slide_height = Inches(13.333), Inches(7.5)
    layout = prs.slide_layouts[5]
    for ph in layout.placeholders:
        if ph.placeholder_format.type == 1 or ph.placeholder_format.idx == 0:
            ph.left, ph.top, ph.width, ph.height = Inches(0.6), Inches(0.4), Inches(12.1), Inches(1.0)
        else:
            ph._element.getparent().remove(ph._element)
    for ph in list(prs.slide_master.placeholders):
        if ph.placeholder_format.idx == 0:
            ph.left, ph.top, ph.width, ph.height = Inches(0.6), Inches(0.4), Inches(12.1), Inches(1.0)
        elif ph.placeholder_format.idx == 1:
            ph.left, ph.top, ph.width, ph.height = Inches(0.6), Inches(1.6), Inches(12.1), Inches(5.2)
        else:
            ph._element.getparent().remove(ph._element)
    return layout


def texto(slide, x, y, w, h, conteudo, tam=16, cor=TEMA.TEXT_1, negrito=False, ancora=MSO_ANCHOR.TOP, nome=None, alinhar=PP_ALIGN.LEFT, fonte=None):
    """conteudo: texto ou lista de parágrafos; **trecho** vira negrito."""
    caixa = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    if nome:
        caixa.name = nome
    tf = caixa.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = ancora
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    itens = conteudo if isinstance(conteudo, list) else [conteudo]
    for i, item in enumerate(itens):
        par = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        par.alignment = alinhar
        par.space_after = Pt(7)
        for j, trecho in enumerate(re.split(r"\*\*", item)):
            if not trecho:
                continue
            r = par.add_run()
            r.text = trecho
            r.font.size = Pt(tam)
            r.font.bold = negrito or j % 2 == 1
            r.font.color.theme_color = cor
            if fonte:
                r.font.name = fonte
    return caixa


def cartao(slide, x, y, w, h, fundo=TEMA.BACKGROUND_2, nome="Cartão"):
    s = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(x), Inches(y), Inches(w), Inches(h))
    s.adjustments[0] = 0.05
    s.fill.solid()
    s.fill.fore_color.theme_color = fundo
    s.line.fill.background()
    s.shadow.inherit = False
    s.name = nome
    return s


def numero(slide, x, y, w, valor, legenda, h=1.65, cor=TEMA.ACCENT_1):
    cartao(slide, x, y, w, h, nome=f"Indicador {legenda}")
    texto(slide, x + 0.2, y + 0.15, w - 0.4, 0.8, valor, tam=38, cor=cor, negrito=True, fonte="Cambria")
    texto(slide, x + 0.2, y + 0.98, w - 0.4, h - 1.05, legenda, tam=13, cor=TEMA.TEXT_1)


def grafico(slide, x, y, w, h, categorias, valores, tipo, fmt="0", titulo=None, maximo=None):
    dados = CategoryChartData(number_format=fmt)
    dados.categories = categorias
    dados.add_series(titulo or "Valor", valores)
    g = slide.shapes.add_chart(tipo, Inches(x), Inches(y), Inches(w), Inches(h), dados).chart
    g.has_legend = False
    g.has_title = bool(titulo)
    if titulo:
        g.chart_title.text_frame.text = titulo
        run = g.chart_title.text_frame.paragraphs[0].runs[0]
        run.font.size, run.font.bold = Pt(14), True
    g.font.size = Pt(13)
    g.font.color.theme_color = TEMA.TEXT_1
    plot = g.plots[0]
    plot.gap_width = 60
    plot.has_data_labels = True
    plot.data_labels.show_value = True
    plot.data_labels.number_format = fmt
    plot.data_labels.number_format_is_linked = False
    plot.data_labels.position = XL_LABEL_POSITION.OUTSIDE_END
    plot.data_labels.font.size = Pt(13)
    plot.series[0].format.fill.solid()
    plot.series[0].format.fill.fore_color.theme_color = TEMA.ACCENT_1
    va = g.value_axis
    va.visible = False
    va.has_major_gridlines = False
    va.minimum_scale = 0
    if maximo:
        va.maximum_scale = maximo
    ca = g.category_axis
    ca.format.line.color.theme_color = TEMA.ACCENT_5
    ca.has_major_gridlines = False
    if tipo == XL_CHART_TYPE.BAR_CLUSTERED:
        ca.reverse_order = True
    return g


def tabela(slide, x, y, w, larguras, linhas, tam=12, alt=0.42):
    forma = slide.shapes.add_table(len(linhas), len(linhas[0]), Inches(x), Inches(y), Inches(w), Inches(alt * len(linhas)))
    t = forma.table
    estilo = t._tbl.tblPr.find("{http://schemas.openxmlformats.org/drawingml/2006/main}tableStyleId")
    if estilo is not None:
        estilo.text = "{5940675A-B579-460E-94D1-54222C63F5DA}"  # sem preenchimento, com grade
    for j, l in enumerate(larguras):
        t.columns[j].width = Inches(l)
    for i, lin in enumerate(linhas):
        t.rows[i].height = Inches(alt)
        for j, v in enumerate(lin):
            c = t.cell(i, j)
            c.margin_left = c.margin_right = Inches(0.08)
            c.margin_top = c.margin_bottom = Inches(0.03)
            c.vertical_anchor = MSO_ANCHOR.MIDDLE
            c.text_frame.word_wrap = True
            par = c.text_frame.paragraphs[0]
            r = par.add_run()
            r.text = str(v)
            r.font.size = Pt(tam)
            r.font.bold = i == 0
            r.font.color.theme_color = TEMA.BACKGROUND_1 if i == 0 else TEMA.TEXT_1
            c.fill.solid()
            c.fill.fore_color.theme_color = TEMA.ACCENT_1 if i == 0 else TEMA.BACKGROUND_1


def slide_conteudo(prs, layout, titulo, notas):
    s = prs.slides.add_slide(layout)
    s.shapes.title.text = titulo
    p = s.shapes.title.text_frame.paragraphs[0]
    p.alignment = PP_ALIGN.LEFT
    p.runs[0].font.size, p.runs[0].font.bold = Pt(30), True
    p.runs[0].font.color.theme_color = TEMA.TEXT_2
    s.shapes.title.text_frame.vertical_anchor = MSO_ANCHOR.MIDDLE
    s.notes_slide.notes_text_frame.text = notas
    return s


def fundo_escuro(slide):
    f = slide.background.fill
    f.solid()
    f.fore_color.theme_color = TEMA.TEXT_2


def main():
    d = ler_dados()
    m = d["met"]
    prs = Presentation()
    aplicar_tema(prs)
    layout = preparar_layout(prs)
    ac_feitos = sum(1 for a in d["ac"] if a[8])
    nf_feitos = sum(1 for n in d["nf"] if n[9])
    cob = m["Cobertura de requisitos"][1]
    primeira = [e for e in d["exec"] if int(e[0][3:]) <= 31]
    aprov1 = sum(e[5] == "Aprovado" for e in primeira)
    niveis = {"Unitário": "Unitário", "Integração": "Integração Go", "Integração/API": "API (Postman)", "Sistema/interface": "Interface (Selenium)"}
    cont = [sum(1 for a in d["auto"] if a[1] == k) for k in niveis]
    pendente = ac_feitos < len(d["ac"]) or cob < 1

    # 1
    s = slide_conteudo(prs, layout, "Ordens de Serviço", "Apresente-se, diga o nome do sistema e a pergunta do projeto: o sistema está pronto para uso, dentro do escopo testado?")
    fundo_escuro(s)
    t = s.shapes.title
    t.left, t.top, t.width, t.height = Inches(0.9), Inches(2.1), Inches(11.5), Inches(1.2)
    t.text_frame.paragraphs[0].runs[0].font.size = Pt(50)
    t.text_frame.paragraphs[0].runs[0].font.color.theme_color = TEMA.BACKGROUND_1
    texto(s, 0.9, 3.4, 11.5, 0.7, "Planejamento, execução e avaliação da qualidade de um sistema de software", tam=22, cor=TEMA.ACCENT_6)
    texto(s, 0.9, 5.3, 11.5, 1.2, ["Marcelo A. B. Coldibelli (RA 24210023), Turma B", "Testes e Qualidade de Software, UNISAGRADO, 2026. Prof. Dr. Elvio Gilberto da Silva"], tam=16, cor=TEMA.BACKGROUND_1)

    # 2
    s = slide_conteudo(prs, layout, "O sistema controla ordens de serviço com prazo por prioridade",
                       "Explique a finalidade. O objetivo é avaliar a qualidade, não construir um sistema grande. Cite o que ficou fora do escopo. O trabalho é individual e o sistema foi aprovado no P01.")
    texto(s, 0.6, 1.65, 6.2, 4.9, [
        "**Finalidade:** cadastrar clientes, abrir OS, controlar o status e mostrar as OS atrasadas.",
        "**Objetivo do projeto:** produzir evidências para avaliar comportamento, confiabilidade, usabilidade e prontidão.",
        "**Tecnologia:** Go 1.26, SQLite, HTML no servidor e API JSON.",
        "**Fora do escopo:** edição e exclusão de registros, perfis de usuário, recuperação de senha, teste de carga e produção.",
    ], tam=20)
    numero(s, 7.3, 1.65, 2.6, "7", "requisitos funcionais (mínimo 6)", h=2.25)
    numero(s, 10.1, 1.65, 2.6, "5", "requisitos não funcionais (mínimo 2)", h=2.25)
    numero(s, 7.3, 4.1, 2.6, str(len(d["riscos"])), "riscos documentados (mínimo 8)", h=2.25)
    numero(s, 10.1, 4.1, 2.6, "7", "fluxos no escopo, com 2 formulários", h=2.25)

    # 3
    s = slide_conteudo(prs, layout, "Os riscos altos definiram a ordem dos testes",
                       "Explique a matriz: probabilidade e impacto definem a prioridade. Os riscos altos foram testados primeiro. A maior parte dos testes fica nos níveis mais baixos, que são rápidos e estáveis.")
    altos = [r for r in d["riscos"] if r[5] == "Alta"][:5]
    tabela(s, 0.6, 1.65, 7.3, [0.8, 4.0, 2.5], [["ID", "Risco de prioridade Alta", "Teste"]] + [[r[0], r[1], ", ".join(re.findall(r"(?:CT|UT|IT|API)-\d+", r[6]))] for r in altos], tam=14, alt=0.8)
    grafico(s, 8.2, 1.55, 4.6, 4.8, list(niveis.values()), cont, XL_CHART_TYPE.BAR_CLUSTERED, titulo=f"{sum(cont)} testes automatizados, por nível")

    # 4
    s = slide_conteudo(prs, layout, "CT-20 revelou o defeito de maior impacto: DEF-02",
                       "Mostre o caminho: caso de teste, evidência e defeito. O CT-20 esperava erro sem gravar. A tela mostrou o erro, mas gravou a OS com R$ 0,00. A correção teve um teste antes, o IT-11, e depois reteste e regressão.")
    recorte = GRAFICOS / "EX-020_recorte.png"
    Image.open(DOCS / "evidencias/execucao/EX-020_CT-20_3.png").crop((550, 810, 1500, 1050)).save(recorte)
    s.shapes.add_picture(str(recorte), Inches(0.6), Inches(1.9), width=Inches(7.6)).name = "Recorte da evidência EX-020"
    texto(s, 0.6, 3.95, 7.6, 0.4, "Recorte de EX-020_CT-20_3.png: as OS 16 e 17 foram gravadas com R$ 0,00", tam=13, cor=TEMA.ACCENT_3)
    texto(s, 0.6, 4.55, 7.6, 1.8, ["**Técnica do caso:** particionamento de equivalência no formato do valor.", "**Dados:** valores abc e 10,555, com os outros campos válidos."], tam=17)
    cartao(s, 8.5, 1.65, 4.2, 4.75)
    texto(s, 8.75, 1.85, 3.7, 4.4, [
        "**Esperado:** erro \"use o formato 1234,56\" e nenhuma OS gravada.",
        "**Obtido:** o erro aparece, mas a OS é gravada com R$ 0,00.",
        "**Severidade:** Alta, porque afeta dados.",
        "**Correção:** teste IT-11 primeiro, commit 418b428, reteste EX-032.",
        "**Issue:** #2, encerrada.",
    ], tam=16)

    # 5
    s = slide_conteudo(prs, layout, f"A execução manual encontrou 4 defeitos, todos corrigidos",
                       f"Primeiro ciclo: {aprov1} de {len(primeira)} aprovados. Depois das correções, 10 execuções de reteste e regressão. A aprovação final não indica ausência de defeitos: indica o estado depois das correções. Nenhum defeito foi reaberto.")
    numero(s, 0.6, 1.65, 3.0, str(len(d["casos"])), "casos manuais (mínimo 24)")
    numero(s, 3.8, 1.65, 3.0, str(len(d["exec"])), "execuções, com reteste e regressão")
    numero(s, 0.6, 3.55, 3.0, pct(m["Aprovação no 1º ciclo"][1]), f"aprovação no 1º ciclo ({aprov1} de {len(primeira)})")
    numero(s, 3.8, 3.55, 3.0, pct(m["Taxa de reabertura"][1]), "taxa de reabertura (0 de 4)")
    sev = ["Crítica", "Alta", "Média", "Baixa"]
    grafico(s, 7.2, 1.55, 5.6, 4.9, sev, [m[f"Defeitos - {x}"][1] for x in sev], XL_CHART_TYPE.COLUMN_CLUSTERED, titulo="Defeitos por severidade", maximo=3)

    # 6
    s = slide_conteudo(prs, layout, "Demonstração: os testes rodam em quatro níveis",
                       "Demonstração ao vivo em dois níveis: make test-unit e make test-api, com o sistema em execução. Mostre que os testes validam resultados. Sem internet ou com falha, use o vídeo de contingência.")
    colunas = [("Unitário", cont[0], "make test-unit", "Regras puras: CPF, prazo, valor e transições"),
               ("Integração Go", cont[1], "make test-integracao", "HTTP, serviço e SQLite real"),
               ("API", cont[2], "make test-api", "Status, contrato e dados encadeados"),
               ("Interface", cont[3], "make test-e2e", "Fluxos no navegador, com captura de tela")]
    for i, (nome, q, cmd, desc) in enumerate(colunas):
        x = 0.6 + i * 3.08
        cartao(s, x, 1.65, 2.88, 3.5, nome=f"Nível {nome}")
        texto(s, x + 0.2, 1.8, 2.5, 0.8, str(q), tam=38, negrito=True, cor=TEMA.ACCENT_1, fonte="Cambria")
        texto(s, x + 0.2, 2.65, 2.5, 0.4, nome, tam=17, negrito=True)
        texto(s, x + 0.2, 3.1, 2.5, 1.1, desc, tam=14)
        texto(s, x + 0.2, 4.45, 2.5, 0.5, cmd, tam=13, cor=TEMA.ACCENT_2, negrito=True, fonte="Courier New")
    texto(s, 0.6, 5.5, 12.1, 0.9, f"Última execução aprovada do CI: 25 testes Go, 16 de API e 8 de interface. Taxa de automação: {pct(m['Taxa de automação'][1])} dos casos candidatos.", tam=17)

    # 7
    s = slide_conteudo(prs, layout, f"{nf_feitos} de {len(d['nf'])} não funcionais atendem; aceitação: {ac_feitos} de {len(d['ac'])}",
                       "Mostre os resultados medidos. DEF-04 surgiu no NF-04 e foi corrigido. Se a aceitação e o NF-07 ainda estiverem pendentes, diga isso diretamente: eles precisam de uma pessoa que não fez os testes, e nenhum resultado foi inventado.")
    tabela(s, 0.6, 1.65, 7.7, [1.1, 3.4, 3.2], [["ID", "Verificação", "Resultado"],
           ["NF-01", "Lista com 1.000 OS, p95 até 500 ms", "4,3 ms: atende"],
           ["NF-02", "Login, média até 1 s", "66,6 ms: atende"],
           ["NF-03", "Selenium em Chrome e Firefox", "8 de 8 nos dois: atende"],
           ["NF-04", "Telas em 375 px", "Atende depois do DEF-04"],
           ["NF-05, 06", "Hash, cookie e mensagem de login", "Atende"],
           ["NF-07", "Usabilidade com participante", next(n[9] for n in d["nf"] if n[0] == "NF-07") or "Não executado"],
           ["NF-08", "Dados depois de reinício", "Atende"]], tam=14, alt=0.58)
    cartao(s, 8.6, 1.65, 4.1, 4.64)
    if ac_feitos < len(d["ac"]):
        linhas_ac = ["**Aceitação**", "AC-01 a AC-04 estão especificados, mas não foram executados.", "**Motivo:** falta uma pessoa que não tenha feito os testes (manual, seção 9.11).", "Nenhum resultado foi registrado sem execução."]
    else:
        linhas_ac = ["**Aceitação**"] + [f"**{a[0]}:** {a[8]}" for a in d["ac"]]
    texto(s, 8.85, 1.85, 3.6, 4.2, linhas_ac, tam=17)

    # 8
    s = slide_conteudo(prs, layout, f"A cobertura de requisitos, de {pct(cob)}, limita a conclusão",
                       "Explique cada barra. Aprovação final e aprovação no primeiro ciclo medem coisas diferentes. A cobertura de requisitos é o indicador que ainda limita a conclusão. Os defeitos por status: 4 encerrados, 0 reabertos.")
    rot = ["Execução", "Aprovação no 1º ciclo", "Aprovação final", "Cobertura de requisitos", "Automação"]
    vals = [m["Percentual de execução"][1], m["Aprovação no 1º ciclo"][1], m["Taxa de aprovação"][1], cob, m["Taxa de automação"][1]]
    grafico(s, 0.6, 1.55, 7.6, 4.9, rot, vals, XL_CHART_TYPE.BAR_CLUSTERED, fmt="0.0%", maximo=1.2)
    texto(s, 8.6, 1.75, 4.1, 4.6, [
        f"**Aprovação final de {pct(m['Taxa de aprovação'][1])}:** é o estado depois das correções, não a ausência de defeitos.",
        f"**1º ciclo de {pct(m['Aprovação no 1º ciclo'][1])}:** mostra a qualidade da versão original.",
        f"**Automação de {pct(m['Taxa de automação'][1])}:** faltam CT-05, CT-12 e CT-31.",
        "**Cobertura de código:** 35,4% por pacote e 64,0% com -coverpkg.",
    ], tam=16)

    # 9
    s = slide_conteudo(prs, layout, "TDD: o valor 1.500,00 passou a ser aceito",
                       "Mostre git log. RED: o teste novo falhou porque o valor era recusado. GREEN: o mínimo de código. REFACTOR: nomes e comentário, com todos os testes aprovados. Depois, abra uma OS com 1.500,00 no sistema.")
    etapas = [("RED", "a31aa49", "UT-12 exige 1.500,00 = 150000. O teste falha: o valor é recusado.", TEMA.ACCENT_2),
              ("GREEN", "5568311", "Nova regex de milhar em ParseValor. O teste passa.", TEMA.ACCENT_4),
              ("REFACTOR", "f107a8d", "Nomes e regra documentada. 25 testes aprovados, 0 reprovados.", TEMA.ACCENT_1)]
    for i, (nome, commit, desc, cor) in enumerate(etapas):
        x = 0.6 + i * 4.1
        cartao(s, x, 1.65, 3.9, 3.2, nome=f"Etapa {nome}")
        texto(s, x + 0.25, 1.85, 3.4, 0.6, nome, tam=26, negrito=True, cor=cor, fonte="Cambria")
        texto(s, x + 0.25, 2.5, 3.4, 0.4, "commit " + commit, tam=14, cor=TEMA.ACCENT_3, fonte="Courier New")
        texto(s, x + 0.25, 3.0, 3.4, 1.7, desc, tam=16)
    texto(s, 0.6, 5.2, 12.1, 1.2, ["**No sistema em execução:** 1.500,00 grava R$ 1.500,00. 1.50,00, abc, 10,555 e 50.000,01 são recusados e não gravam OS."], tam=19)

    # 10
    s = slide_conteudo(prs, layout, "O pipeline parou a falha, e a análise de qualidade continua aprovada",
                       "Abra a aba Actions no PR 5: a execução com falha e a execução aprovada. Depois compare as duas análises do SonarQube. Avise que a segunda análise usou uma instância nova e outra versão.")
    cartao(s, 0.6, 1.65, 5.6, 4.7)
    texto(s, 0.85, 1.85, 5.1, 4.3, [
        "**GitHub Actions, PR #5**",
        "**Falha controlada:** run 42134250857, commit a049d06, em TestNovaOrdem_PrazoPorPrioridade.",
        "**Correção:** run 42134677760, commit 2bc5bda, aprovado.",
        "**Gatilhos:** push e pull_request.",
        "**Etapas:** go vet, testes Go com -race, build, Newman, Selenium e artefato.",
    ], tam=17)
    sonar = tabela_md("P11-roteiro-tdd-cicd-qualidade.md", "Indicador")
    curtos = {"Vulnerabilidades": "0"}
    tabela(s, 6.5, 1.65, 6.2, [2.6, 1.8, 1.8], [["SonarQube", "Linha de base", "Depois"]] + [[x[0], curtos.get(x[0], x[1]), curtos.get(x[0], x[2])] for x in sonar], tam=15, alt=0.56)
    texto(s, 6.5, 5.75, 6.2, 0.6, "Análises em 26.9 e 26.11: a segunda usou uma instância nova.", tam=12, cor=TEMA.ACCENT_3)

    # 11
    s = slide_conteudo(prs, layout, "Situação do sistema e próximas melhorias",
                       "Dê a conclusão com clareza. Cite as melhorias de prioridade Alta. Termine e passe para as perguntas.")
    fundo_escuro(s)
    s.shapes.title.text_frame.paragraphs[0].runs[0].font.color.theme_color = TEMA.BACKGROUND_1
    conclusao = (f"O sistema se comportou como especificado no escopo testado, mas ainda não pode ser declarado pronto: cobertura de requisitos de {pct(cob)} e aceitação com {ac_feitos} de {len(d['ac'])} cenários."
                 if pendente else "Todos os critérios de saída foram atendidos. O sistema está pronto para uso dentro do escopo testado, com riscos residuais.")
    texto(s, 0.6, 1.7, 5.8, 4.6, conclusao, tam=22, cor=TEMA.BACKGROUND_1)
    plano = tabela_md("P11-roteiro-tdd-cicd-qualidade.md", "Ação")
    texto(s, 6.9, 1.7, 5.8, 0.5, "Melhorias priorizadas", tam=18, negrito=True, cor=TEMA.ACCENT_6)
    texto(s, 6.9, 2.3, 5.8, 4.2, [f"**{x[2]}:** {x[0]}" for x in plano[:5]], tam=17, cor=TEMA.BACKGROUND_1)

    prs.core_properties.title = "Ordens de Serviço: apresentação final do Projeto P2"
    prs.core_properties.author = "Marcelo A. B. Coldibelli"
    prs.save(SAIDA)
    subprocess.run(["soffice", "--headless", "--convert-to", "pdf", "--outdir", str(DOCS), str(SAIDA)], check=True, capture_output=True, timeout=180)
    print(f"Gerados {SAIDA.name} e {SAIDA.with_suffix('.pdf').name}: {len(prs.slides)} slides")


if __name__ == "__main__":
    main()
