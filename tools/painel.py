"""Painel de progresso do projeto em http://localhost:8090.

Uso: make painel   (ou tools/.venv/bin/python tools/painel.py)

Cada consulta a /dados.json lê o estado atual dos arquivos do projeto:
planilha (docs/P2_TQS_planilha.xlsx), git, P01, P11, GitHub Actions e pasta entrega/.
Não existe arquivo de progresso separado: o que muda nesses arquivos aparece no painel.
"""
import json
import subprocess
import time
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from openpyxl import load_workbook

RAIZ = Path(__file__).resolve().parent.parent
PLANILHA = RAIZ / "docs" / "P2_TQS_planilha.xlsx"
HTML = Path(__file__).resolve().parent / "painel.html"
PORTA = 8090


def comando(*args):
    """Roda um comando e devolve a saída, ou None se falhar (ex.: gh sem login)."""
    try:
        r = subprocess.run(args, cwd=RAIZ, capture_output=True, text=True, timeout=15)
        return r.stdout if r.returncode == 0 else None
    except (OSError, subprocess.TimeoutExpired):
        return None


def linhas(ws, colunas):
    """Linhas com a primeira coluna pedida preenchida, como dicionários."""
    saida = []
    for r in range(2, ws.max_row + 1):
        valores = {nome: ws.cell(r, col).value for nome, col in colunas.items()}
        if valores[next(iter(colunas))] not in (None, ""):
            saida.append(valores)
    return saida


def ler_planilha():
    wb = load_workbook(PLANILHA, read_only=False)
    casos = linhas(wb["Casos"], {"id": 1, "titulo": 2, "requisito": 3})
    # Último resultado por caso: a última linha preenchida em Execucoes vale (reteste = linha nova).
    ultimo = {}
    for e in linhas(wb["Execucoes"], {"caso": 2, "resultado": 6, "data": 4}):
        if e["resultado"]:
            ultimo[e["caso"]] = e
    for c in casos:
        e = ultimo.get(c["id"])
        c["resultado"] = e["resultado"] if e else "Não executado"
        c["data"] = str(e["data"]) if e and e["data"] else ""
    return {
        "casos": casos,
        "defeitos": linhas(wb["Defeitos"], {"id": 1, "titulo": 2, "caso": 4, "severidade": 11, "status": 14}),
        "aceitacao": linhas(wb["Aceitacao"], {"id": 1, "decisao": 9}),
        "nao_funcionais": linhas(wb["NaoFuncionais"], {"id": 1, "categoria": 2, "conclusao": 10}),
        "metricas": linhas(wb["Metricas"], {"indicador": 1, "interpretacao": 5}),
        "diario": linhas(wb["Diario"], {"data": 1, "atividade": 2, "tempo": 5}),
    }


def celula_tabela(arquivo, rotulo, coluna):
    """Valor de uma coluna da linha "| rotulo | ... |" de uma tabela Markdown."""
    for linha in (RAIZ / arquivo).read_text(encoding="utf-8").splitlines():
        partes = [p.strip() for p in linha.split("|")]
        if len(partes) > coluna and partes[1] == rotulo:
            return partes[coluna]
    return ""


_cache_ci = {"quando": 0.0, "valor": None}


def pipeline_falha_e_correcao():
    # O gh leva quase 1 s; o resultado fica guardado por 60 s para a página responder rápido.
    if time.monotonic() - _cache_ci["quando"] < 60:
        return _cache_ci["valor"]
    _cache_ci["valor"] = _consultar_ci()
    _cache_ci["quando"] = time.monotonic()
    return _cache_ci["valor"]


def _consultar_ci():
    saida = comando("gh", "run", "list", "--limit", "50", "--json", "conclusion,createdAt")
    if saida is None:
        return None  # gh indisponível: estado desconhecido
    runs = sorted(json.loads(saida), key=lambda r: r["createdAt"])
    falhou = False
    for r in runs:
        falhou = falhou or r["conclusion"] == "failure"
        if falhou and r["conclusion"] == "success":
            return True
    return False


def existe(*padroes):
    return any(any(RAIZ.glob(p)) for p in padroes)


def etapa(nome, feito, total, detalhe=""):
    return {"nome": nome, "feito": feito, "total": total, "detalhe": detalhe}


def etapa_defeitos(defeitos, abertos, execucao_completa):
    detalhe = f"{len(defeitos)} registrados, {len(abertos)} abertos"
    if defeitos:
        return etapa("Defeitos tratados", len(defeitos) - len(abertos), len(defeitos), detalhe)
    # Sem defeitos: a etapa só termina quando a execução manual termina.
    return etapa("Defeitos tratados", int(execucao_completa), 1, detalhe)


def montar_dados():
    p = ler_planilha()
    casos, defeitos = p["casos"], p["defeitos"]
    executados = sum(c["resultado"] in ("Aprovado", "Reprovado") for c in casos)
    abertos = [d for d in defeitos if d["status"] != "Encerrado"]
    commits = comando("git", "log", "--pretty=%s", "-200") or ""
    decisao = celula_tabela("docs/P01-ficha-do-sistema.md", "Decisão do professor", 2)
    aprovado = decisao not in ("", "Aprovado / Aprovado com ajustes / Não aprovado")
    ci = pipeline_falha_e_correcao()
    entrega = RAIZ / "entrega"
    pastas = sum(1 for x in entrega.iterdir() if x.is_dir()) if entrega.exists() else 0

    etapas = [
        etapa("P01 aprovado pelo professor", int(aprovado), 1, decisao if aprovado else "aguardando decisão"),
        etapa("SonarQube: linha de base", int(celula_tabela("docs/P11-roteiro-tdd-cicd-qualidade.md", "Bugs", 2) != ""), 1),
        etapa("Execução manual", executados, len(casos), f"{executados} de {len(casos)} casos"),
        etapa_defeitos(defeitos, abertos, execucao_completa=executados == len(casos)),
        etapa("Aceitação", sum(bool(a["decisao"]) for a in p["aceitacao"]), len(p["aceitacao"])),
        etapa("Não funcionais", sum(bool(n["conclusao"]) for n in p["nao_funcionais"]), len(p["nao_funcionais"])),
        etapa("TDD (RED, GREEN, REFACTOR)", sum(f"({x})" in commits for x in ("RED", "GREEN", "REFACTOR")), 3),
        etapa("Pipeline com falha e correção", int(bool(ci)), 1, "gh indisponível" if ci is None else ""),
        etapa("SonarQube: segunda análise", int(celula_tabela("docs/P11-roteiro-tdd-cicd-qualidade.md", "Bugs", 3) != ""), 1),
        etapa("Interpretação das métricas", sum(bool(m["interpretacao"]) for m in p["metricas"]), len(p["metricas"])),
        etapa("Relatório (DOCX e PDF)", int(existe("docs/*elatorio*.docx", "entrega/13_*/*.docx")) + int(existe("docs/*elatorio*.pdf", "entrega/13_*/*.pdf")), 2),
        etapa("Apresentação (PPTX e PDF)", int(existe("docs/*.pptx", "entrega/14_*/*.pptx")) + int(existe("docs/*presenta*.pdf", "entrega/14_*/*.pdf")), 2),
        etapa("Vídeo de contingência", int(existe("docs/**/*.mp4", "entrega/14_*/*.mp4")), 1),
        etapa("Drive montado", int(pastas >= 17) + int(existe("entrega/**/COMPROVANTE_DE_ENTREGA*.pdf")), 2, f"{pastas} de 17 pastas"),
    ]
    return {
        "atualizado": datetime.now().strftime("%H:%M:%S"),
        "etapas": etapas,
        "casos": casos,
        "defeitos": defeitos,
        "diario": {"registros": len(p["diario"]), "horas": sum(float(x["tempo"] or 0) for x in p["diario"]),
                   "ultimo": p["diario"][-1] if p["diario"] else None},
        "commits": (comando("git", "log", "--pretty=%h|%ad|%s", "--date=format:%d/%m %H:%M", "-6") or "").splitlines(),
    }


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/":
            self.responder(200, "text/html; charset=utf-8", HTML.read_bytes())
        elif self.path == "/dados.json":
            try:
                corpo = json.dumps(montar_dados(), ensure_ascii=False, default=str).encode()
                self.responder(200, "application/json; charset=utf-8", corpo)
            except Exception as e:  # ex.: planilha aberta e sendo gravada no Excel
                corpo = json.dumps({"erro": f"{type(e).__name__}: {e}"}, ensure_ascii=False).encode()
                self.responder(503, "application/json; charset=utf-8", corpo)
        else:
            self.responder(404, "text/plain", b"nao encontrado")

    def responder(self, status, tipo, corpo):
        self.send_response(status)
        self.send_header("Content-Type", tipo)
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(corpo)

    def log_message(self, *args):
        pass  # sem log a cada consulta de 5 s


if __name__ == "__main__":
    print(f"Painel em http://localhost:{PORTA}  (Ctrl+C para parar)")
    ThreadingHTTPServer(("127.0.0.1", PORTA), Handler).serve_forever()
