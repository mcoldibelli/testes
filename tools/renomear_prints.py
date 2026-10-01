"""Renomeia os prints da execução manual para o padrão EX-NNN_CT-NN.png.

Uso: python3 tools/renomear_prints.py CT-01 CT-02 CT-09 CT-09

Pega as imagens de docs/evidencias/execucao que ainda não começam com "EX-",
na ordem em que foram criadas, e dá a cada uma o caso informado, na mesma ordem.
O número da execução é o número do caso (CT-07 -> EX-007), como na aba Execucoes.
Reteste: se o caso já tem print, ele recebe o próximo número livre (EX-032, EX-033, ...).
Um caso com vários prints recebe _1, _2, ... no fim do nome.
Mostra o plano e só renomeia depois da confirmação.
"""
import re
import sys
from collections import Counter
from pathlib import Path

PASTA = Path(__file__).resolve().parent.parent / "docs" / "evidencias" / "execucao"
EXTENSOES = {".png", ".jpg", ".jpeg"}


def main():
    casos = sys.argv[1:]
    if not casos or any(not re.fullmatch(r"CT-\d{2}", c) for c in casos):
        sys.exit("uso: python3 tools/renomear_prints.py CT-01 CT-02 ...  (um caso por print, na ordem)")

    prints = sorted((p for p in PASTA.iterdir() if p.suffix.lower() in EXTENSOES and not p.name.startswith("EX-")),
                    key=lambda p: p.stat().st_birthtime if hasattr(p.stat(), "st_birthtime") else p.stat().st_mtime)
    if len(prints) != len(casos):
        sys.exit(f"{len(prints)} prints novos em {PASTA}, mas {len(casos)} casos informados. Os números precisam ser iguais.")

    usados = [int(m.group(1)) for p in PASTA.iterdir() if (m := re.match(r"EX-(\d{3})_", p.name))]
    proximo = max(usados, default=0) + 1
    numero = {}
    for caso in dict.fromkeys(casos):
        if any(PASTA.glob(f"EX-*_{caso}[._]*")):
            numero[caso], proximo = proximo, proximo + 1
        else:
            numero[caso] = int(caso[3:])

    total = Counter(casos)
    vistos = Counter()
    plano = []
    for origem, caso in zip(prints, casos):
        vistos[caso] += 1
        sufixo = f"_{vistos[caso]}" if total[caso] > 1 else ""
        destino = PASTA / f"EX-{numero[caso]:03d}_{caso}{sufixo}{origem.suffix.lower()}"
        if destino.exists():
            sys.exit(f"já existe: {destino.name}. Nada foi renomeado.")
        plano.append((origem, destino))

    for origem, destino in plano:
        print(f"{origem.name}  ->  {destino.name}")
    if input("Renomear? [s/N] ").strip().lower() != "s":
        sys.exit("Cancelado. Nada foi renomeado.")
    for origem, destino in plano:
        origem.rename(destino)
    print(f"{len(plano)} arquivos renomeados.")


if __name__ == "__main__":
    main()
