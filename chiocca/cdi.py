"""CDI médio do ano para o sinal de juro implícito (pré-registro, seção 4: juro implícito > CDI médio + 10 p.p.).

Fonte: Banco Central do Brasil, SGS, série 4389, "Taxa de juros - CDI anualizada base 252" (% a.a., diária),
pela API https://api.bcb.gov.br/dados/serie/bcdata.sgs.4389/dados. A identificação foi conferida nos dados
em 07/11/2026: os valores são iguais aos da série 12 (CDI, % a.d.) anualizada em 252 dias úteis e diferem
dos da Selic (série 1178). Detalhes em docs/fontes.md.

O snapshot versionado fica em data/cdi_sgs4389.csv (data ISO e valor em % a.a.). "CDI médio do ano" é a
média simples das taxas diárias do exercício: os 12 meses que terminam na data de referência da DFP (o ano
civil, para quem fecha em 31/12).

Uso: python -m chiocca.cdi   (baixa a série de 2009 a 2025 e regrava o snapshot)
"""

from __future__ import annotations

import json
import urllib.request
from datetime import date
from functools import lru_cache
from pathlib import Path

import pandas as pd

RAIZ = Path(__file__).resolve().parents[1]
SNAPSHOT = RAIZ / "data" / "cdi_sgs4389.csv"
SERIE = 4389
URL = "https://api.bcb.gov.br/dados/serie/bcdata.sgs.{serie}/dados?formato=json&dataInicial={ini}&dataFinal={fim}"
AGENTE = "Mozilla/5.0 (compatible; chiocca-system/0.1)"


def baixar(ano_ini: int = 2009, ano_fim: int = 2025) -> pd.DataFrame:
    """A API devolve no máximo 10 anos de série diária por pedido; baixa em blocos de 5 anos."""
    partes = []
    for a in range(ano_ini, ano_fim + 1, 5):
        b = min(a + 4, ano_fim)
        url = URL.format(serie=SERIE, ini=f"01/01/{a}", fim=f"31/12/{b}")
        with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": AGENTE}), timeout=120) as r:
            partes.extend(json.load(r))
    d = pd.DataFrame(partes)
    d["data"] = pd.to_datetime(d.data, format="%d/%m/%Y").dt.date
    d["valor"] = d.valor.astype(float)
    return d.drop_duplicates("data").sort_values("data").reset_index(drop=True)


@lru_cache(maxsize=1)
def serie(caminho: Path = SNAPSHOT) -> pd.DataFrame:
    d = pd.read_csv(caminho)
    d["data"] = pd.to_datetime(d.data).dt.date
    return d


def medio(fim_exercicio: date | str, caminho: Path = SNAPSHOT) -> float | None:
    """Média das taxas diárias (em fração ao ano) nos 12 meses que terminam em fim_exercicio."""
    fim = date.fromisoformat(fim_exercicio) if isinstance(fim_exercicio, str) else fim_exercicio
    try:
        inicio = fim.replace(year=fim.year - 1)
    except ValueError:  # 29/02
        inicio = fim.replace(year=fim.year - 1, day=28)
    s = serie(caminho)
    janela = s[(s.data > inicio) & (s.data <= fim)]
    return None if janela.empty else float(janela.valor.mean()) / 100


if __name__ == "__main__":
    d = baixar()
    d.to_csv(SNAPSHOT, index=False)
    print(len(d), d.data.min(), d.data.max())
