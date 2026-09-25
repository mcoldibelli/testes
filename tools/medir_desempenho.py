"""Medições de desempenho para NF-01 e NF-02 (RNF-01). Usa só a biblioteca padrão.

Uso (com o sistema rodando):
  python3 tools/medir_desempenho.py listagem   # cria OS até existirem 1.000 e mede GET /api/ordens 20 vezes
  python3 tools/medir_desempenho.py login      # mede POST /api/login 10 vezes

Cada medição vai para resultados/desempenho_<teste>_<data>.csv (evidência).
Variável BASE_URL muda o endereço (padrão http://localhost:8080).
"""
import csv
import json
import math
import os
import sys
import time
import urllib.request
from datetime import datetime
from pathlib import Path

BASE_URL = os.environ.get("BASE_URL", "http://localhost:8080")
CREDENCIAIS = {"email": "admin@teste.local", "senha": "Admin@123"}
TOTAL_ORDENS = 1000


def chamar(metodo, caminho, corpo=None, token=None):
    dados = json.dumps(corpo).encode() if corpo is not None else None
    req = urllib.request.Request(BASE_URL + caminho, data=dados, method=metodo)
    req.add_header("Content-Type", "application/json")
    if token:
        req.add_header("Authorization", "Bearer " + token)
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read())


def medir(func):
    inicio = time.perf_counter()
    func()
    return (time.perf_counter() - inicio) * 1000


def p95(valores):
    """Percentil 95 pelo método do posto mais próximo (nearest-rank)."""
    ordenados = sorted(valores)
    return ordenados[math.ceil(0.95 * len(ordenados)) - 1]


def salvar(teste, tempos):
    pasta = Path("resultados")
    pasta.mkdir(exist_ok=True)
    arquivo = pasta / f"desempenho_{teste}_{datetime.now():%Y%m%d-%H%M%S}.csv"
    with arquivo.open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["medicao", "tempo_ms"])
        w.writerows((i, f"{t:.2f}") for i, t in enumerate(tempos, start=1))
    return arquivo


def relatar(teste, tempos, criterio, limite_ms):
    media = sum(tempos) / len(tempos)
    valor = p95(tempos) if criterio == "p95" else media
    print(f"medições (ms): {', '.join(f'{t:.1f}' for t in tempos)}")
    print(f"média = {media:.1f} ms | p95 = {p95(tempos):.1f} ms | máx = {max(tempos):.1f} ms")
    print(f"critério: {criterio} <= {limite_ms} ms -> {'ATENDE' if valor <= limite_ms else 'NÃO ATENDE'}")
    print(f"evidência: {salvar(teste, tempos)}")


def listagem():
    token = chamar("POST", "/api/login", CREDENCIAIS)["token"]
    existentes = len(chamar("GET", "/api/ordens", token=token))
    cliente_id = chamar("GET", "/api/clientes", token=token)[0]["id"]
    faltam = max(0, TOTAL_ORDENS - existentes)
    print(f"OS existentes: {existentes}; criando {faltam}...")
    for i in range(faltam):
        chamar("POST", "/api/ordens", {"cliente_id": cliente_id, "descricao": f"Carga de desempenho {i:04d}",
                                       "prioridade": "MEDIA", "valor_centavos": 10000}, token)
    total = len(chamar("GET", "/api/ordens", token=token))
    print(f"OS na base: {total}")
    chamar("GET", "/api/ordens", token=token)  # aquecimento, fora da medição
    tempos = [medir(lambda: chamar("GET", "/api/ordens", token=token)) for _ in range(20)]
    relatar("listagem", tempos, "p95", 500)


def login():
    tempos = [medir(lambda: chamar("POST", "/api/login", CREDENCIAIS)) for _ in range(10)]
    relatar("login", tempos, "média", 1000)


if __name__ == "__main__":
    testes = {"listagem": listagem, "login": login}
    if len(sys.argv) != 2 or sys.argv[1] not in testes:
        sys.exit(f"uso: python3 {sys.argv[0]} listagem|login")
    testes[sys.argv[1]]()
