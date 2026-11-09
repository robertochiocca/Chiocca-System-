"""Exemplo de referência da investigação (pedido de 09/11/2026): Americanas, exercício 2021, em 30/04/2022.

Gera, em PT e EN, o JSON (`chiocca.v2.investigacao`) e o PDF gerado dele (`chiocca.v2.pdf_investigacao`), em
docs/exemplos/. Um teste regenera o JSON a partir do armazém (quando ele existe) e confere que é igual ao guardado, e
regenera o PDF a partir do JSON guardado (sempre, também no CI).

Uso: python -m chiocca.v2.exemplos   (precisa de data/armazem e de data/brutos para as localizações)
"""

from __future__ import annotations

import json
from typing import Any

from chiocca import base
from chiocca.v2 import investigacao, pdf_investigacao
from chiocca.v2.armazem import FontesArmazem
from chiocca.v2.linhagem import Localizador

PASTA = base.RAIZ / "docs" / "exemplos"
CD_CVM, EXERCICIO, DATA = "20990", 2021, "2022-04-30"


def nome(lang: str) -> str:
    return f"americanas_{EXERCICIO}_em_{DATA}_{lang}"


NOMES = [nome("pt"), nome("en")]


def gerar(lang: str, gerado_em: str | None = None) -> dict[str, Any]:
    fa = FontesArmazem()
    loc = Localizador(base.BRUTOS, fa.cache_enet, base.RAIZ / "data" / "manifesto_brutos.csv")
    return investigacao.gerar(fa, CD_CVM, EXERCICIO, DATA, lang, loc, gerado_em)


def main() -> None:
    PASTA.mkdir(parents=True, exist_ok=True)
    gerado_em = None
    for lang in ("pt", "en"):
        inv = gerar(lang, gerado_em)
        gerado_em = inv["gerado_em"]  # o mesmo carimbo nas duas línguas
        (PASTA / f"{nome(lang)}.json").write_text(
            json.dumps(inv, ensure_ascii=False, indent=1) + "\n", encoding="utf-8"
        )
        guardado = json.loads((PASTA / f"{nome(lang)}.json").read_text(encoding="utf-8"))
        (PASTA / f"{nome(lang)}.pdf").write_bytes(pdf_investigacao.gerar(guardado))
        print(PASTA / f"{nome(lang)}.json", flush=True)


if __name__ == "__main__":
    main()
