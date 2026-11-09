"""Exemplos de referência da investigação (pedidos de 09/11/2026): Americanas, exercício 2021, em duas datas.

- 30/04/2022: a DFP de 2021 recém-entregue, antes da reapresentação;
- 31/12/2024: a data máxima; a DFP de 2022 (entregue em 16/11/2023) traz no comparativo os valores de 2021
  reapresentados, e as diferenças em totais e linhas-chave acima de 1% do ativo total aparecem como evidência
  destacada, com o texto neutro (regra de materialidade em docs/contratos.md, seção 4).

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
CD_CVM, EXERCICIO = "20990", 2021
DATAS = ("2022-04-30", "2024-12-31")
LINGUAS = ("pt", "en")


def nome(lang: str, data: str = DATAS[0]) -> str:
    return f"americanas_{EXERCICIO}_em_{data}_{lang}"


NOMES = [nome(lang, d) for d in DATAS for lang in LINGUAS]
PARES = [(d, lang) for d in DATAS for lang in LINGUAS]


def gerar(lang: str, gerado_em: str | None = None, data: str = DATAS[0]) -> dict[str, Any]:
    fa = FontesArmazem()
    loc = Localizador(base.BRUTOS, fa.cache_enet, base.RAIZ / "data" / "manifesto_brutos.csv")
    return investigacao.gerar(fa, CD_CVM, EXERCICIO, data, lang, loc, gerado_em)


def main() -> None:
    PASTA.mkdir(parents=True, exist_ok=True)
    gerado_em = None
    for data in DATAS:
        for lang in LINGUAS:
            inv = gerar(lang, gerado_em, data)
            gerado_em = inv["gerado_em"]  # o mesmo carimbo em todos os exemplos
            caminho = PASTA / f"{nome(lang, data)}.json"
            caminho.write_text(json.dumps(inv, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
            guardado = json.loads(caminho.read_text(encoding="utf-8"))
            (PASTA / f"{nome(lang, data)}.pdf").write_bytes(pdf_investigacao.gerar(guardado))
            print(caminho, flush=True)


if __name__ == "__main__":
    main()
