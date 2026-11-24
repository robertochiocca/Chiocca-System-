"""A taxa que substitui o CDI no estudo dos EUA (pré-registro dos EUA, seção 3.2): a Effective Federal Funds Rate, série
diária DFF do FRED (Federal Reserve Bank of St. Louis), cuja fonte é a publicação H.15 do Federal Reserve; pública,
gratuita e sem chave.

O arquivo versionado fica em `data/eua_dff.csv`, no formato de `data/cdi_sgs4389.csv` (data ISO e valor em % a.a.), para
que a média do ano saia de `chiocca.cdi.medio` sem mudar nenhuma linha (o caminho do arquivo é o argumento `caminho`).
O SHA-256 vai para o manifesto dos EUA (`data/eua_manifesto.csv`). Os dias sem valor no FRED (".") ficam fora.

Uso: python -m chiocca.eua.taxa   (baixa a série de 2009 a 2025 e regrava o arquivo e a linha do manifesto)
"""

from __future__ import annotations

import csv
import io
import urllib.request
from datetime import datetime, timezone

from chiocca.base import RAIZ
from chiocca.eua import sec

SERIE = "DFF"
URL = "https://fred.stlouisfed.org/graph/fredgraph.csv?id={serie}&cosd={ini}&coed={fim}"
ARQUIVO = RAIZ / "data" / "eua_dff.csv"
NOME_NO_MANIFESTO = "../eua_dff.csv"  # o manifesto dos EUA guarda os caminhos a partir de data/eua/


def converte(texto: str) -> str:
    """O CSV do FRED (`observation_date,DFF`) no formato `data,valor`, sem os dias sem valor."""
    linhas = list(csv.reader(io.StringIO(texto)))
    if not linhas or linhas[0] != ["observation_date", SERIE]:
        raise ValueError(f"cabeçalho inesperado no CSV do FRED: {linhas[:1]}")
    saida = ["data,valor"]
    for dia, valor in linhas[1:]:
        if valor.strip() not in ("", "."):
            float(valor)
            saida.append(f"{dia},{valor.strip()}")
    return "\n".join(saida) + "\n"


def baixar(ini: str = "2009-01-01", fim: str = "2025-12-31") -> dict[str, str]:
    url = URL.format(serie=SERIE, ini=ini, fim=fim)
    with urllib.request.urlopen(url, timeout=120) as r:  # o User-Agent padrão do urllib (o FRED recusa outros)
        texto = r.read().decode("utf-8")
    ARQUIVO.write_text(converte(texto), encoding="utf-8")
    agora = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    return {"arquivo": NOME_NO_MANIFESTO, "url": url, "bytes": str(ARQUIVO.stat().st_size),
            "sha256": sec.sha256(ARQUIVO), "baixado_em_utc": agora}  # fmt: skip


if __name__ == "__main__":
    linha = baixar()
    sec.grava_manifesto([linha])
    print(linha)
