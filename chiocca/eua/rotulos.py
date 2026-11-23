"""Rótulos dos EUA (Fase 0): os AAERs no pacote `era-py`, de Ian Gow (dados do livro "Empirical Research in Accounting:
Tools and Methods"), lidos do arquivo do PyPI, sem copiar dados para o repositório.

- `aaer_dates`: o índice de AAERs do site da SEC (número, data, descrição e ano). A descrição traz nomes de companhias e
  de pessoas físicas: não é lida aqui nem gravada em nenhum arquivo; só contagens por ano.
- `aaer_firm_year`: as empresa-anos com AAER de Bao et al. (2020), com o identificador do AAER, o gvkey (Compustat) e o
  primeiro e o último ano afetados.
- `gvkey_ciks`: a tabela de ligação do gvkey ao CIK da SEC, com as datas de início e fim de cada ligação.

O pacote é MIT (License-Expression do PyPI); as tabelas não trazem licença própria, e a origem de `gvkey_ciks` não é
informada. Por isso nada delas é copiado: o arquivo fica em `data/eua/era_py/`, fora do Git, com o SHA-256 no manifesto.
Nada de 2024 em diante: as linhas do índice com ano a partir de 2024 são descartadas antes de qualquer conta.
"""

from __future__ import annotations

import hashlib
import io
import json
import urllib.request
import zipfile
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

from chiocca.eua.sec import DADOS

VERSAO = "0.0.37"
PYPI = f"https://pypi.org/pypi/era-py/{VERSAO}/json"
RODA = DADOS / "era_py" / f"era_py-{VERSAO}-py3-none-any.whl"
ULTIMO_ANO = 2023  # nada de 2024 em diante (limite do pedido de 23/11/2026)
PRIMEIRO_ANO_XBRL = 2009  # os Financial Statement Data Sets começam em 2009


def baixar(destino: Path = RODA) -> dict[str, Any]:
    """Baixa a roda do PyPI e confere o SHA-256 publicado pelo PyPI; devolve a linha do manifesto."""
    info = json.load(urllib.request.urlopen(PYPI, timeout=60))
    roda = next(u for u in info["urls"] if u["filename"] == destino.name)
    conteudo = urllib.request.urlopen(roda["url"], timeout=120).read()
    if hashlib.sha256(conteudo).hexdigest() != roda["digests"]["sha256"]:
        raise RuntimeError("o SHA-256 da roda não é o publicado pelo PyPI")
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_bytes(conteudo)
    agora = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    return {"arquivo": destino.relative_to(DADOS).as_posix(), "url": roda["url"], "bytes": len(conteudo),
            "sha256": roda["digests"]["sha256"], "baixado_em_utc": agora}  # fmt: skip


def _tabela(nome: str, roda: Path = RODA) -> tuple[pd.DataFrame, dict[str, Any]]:
    with zipfile.ZipFile(roda) as z:
        dados = pd.read_parquet(io.BytesIO(z.read(f"era_data/_data/{nome}.parquet")))
        meta = json.loads(z.read(f"era_data/_data/{nome}.meta.json"))
    return dados, meta


def licenca(roda: Path = RODA) -> str:
    with zipfile.ZipFile(roda) as z:
        meta = z.read(f"era_py-{VERSAO}.dist-info/METADATA").decode("utf-8")
    return next(x.split(": ", 1)[1] for x in meta.splitlines() if x.startswith("License-Expression: "))


def anos_afetados(f: pd.DataFrame) -> pd.DataFrame:
    """Uma linha por empresa-ano afetada (gvkey, ano), do primeiro ao último ano de cada AAER."""
    linhas = [(g, a) for g, ini, fim in zip(f.gvkey, f.min_year, f.max_year) for a in range(int(ini), int(fim) + 1)]
    return pd.DataFrame(linhas, columns=["gvkey", "ano"]).drop_duplicates().reset_index(drop=True)


def ligadas_ao_cik(fy: pd.DataFrame, ligacoes: pd.DataFrame) -> pd.Series:
    """Se a empresa-ano tem um CIK ligado ao gvkey num período que cruza o ano (ligação com data de início até o fim do
    ano e de fim a partir do começo do ano)."""
    por_gvkey: dict[str, list[tuple[date, date]]] = {}
    for g, ini, fim in zip(ligacoes.gvkey, ligacoes.first_date, ligacoes.last_date):
        por_gvkey.setdefault(str(g), []).append((ini, fim))
    return pd.Series([any(ini <= date(int(a), 12, 31) and fim >= date(int(a), 1, 1)
                          for ini, fim in por_gvkey.get(str(g), [])) for g, a in zip(fy.gvkey, fy.ano)],
                     index=fy.index)  # fmt: skip


def contagens(roda: Path = RODA) -> dict[str, Any]:
    datas, meta_datas = _tabela("aaer_dates", roda)
    datas = datas[datas.year <= ULTIMO_ANO]
    firmas, meta_firmas = _tabela("aaer_firm_year", roda)
    ligacoes, _ = _tabela("gvkey_ciks", roda)
    fy = anos_afetados(firmas)
    fy["ligada"] = ligadas_ao_cik(fy, ligacoes)
    xbrl = fy[(fy.ano >= PRIMEIRO_ANO_XBRL) & (fy.ano <= ULTIMO_ANO)]
    return {
        "pacote": {"nome": "era-py", "versao": VERSAO, "licenca": licenca(roda),
                   "indice_atualizado": "2026-10-08" if "October 8, 2026" in meta_datas["documentation"]["details"]
                   else None},  # fmt: skip
        "indice_sec": {
            "aaers": len(datas), "numeros_distintos": int(datas.aaer_num.nunique()),
            "primeiro_ano": int(datas.year.min()), "ultimo_ano": int(datas.year.max()),
            "por_ano": {str(int(a)): int(n) for a, n in datas.groupby("year").size().items()},
        },  # fmt: skip
        "bao_et_al": {
            "fonte": meta_firmas["documentation"]["source"],
            "linhas": len(firmas), "aaers": int(firmas.p_aaer.nunique()), "gvkeys": int(firmas.gvkey.nunique()),
            "primeiro_ano_afetado": int(firmas.min_year.min()), "ultimo_ano_afetado": int(firmas.max_year.max()),
            "empresa_anos": len(fy), "anos_por_aaer_mediana": float((firmas.max_year - firmas.min_year + 1).median()),
            "aaers_de_mais_de_um_ano": int((firmas.max_year > firmas.min_year).sum()),
            "empresa_anos_xbrl_por_ano": {str(int(a)): int(n) for a, n in xbrl.groupby("ano").size().items()},
            "empresa_anos_xbrl_ligadas_por_ano": {str(int(a)): int(n)
                                                  for a, n in xbrl.groupby("ano").ligada.sum().items()},
            "empresa_anos_xbrl": len(xbrl), "empresa_anos_xbrl_ligadas_ao_cik": int(xbrl.ligada.sum()),
            "empresa_anos_ligadas_ao_cik": int(fy.ligada.sum()),
        },  # fmt: skip
        "ligacao_gvkey_cik": {"linhas": len(ligacoes), "gvkeys": int(ligacoes.gvkey.nunique()),
                              "ciks": int(ligacoes.cik.nunique())},  # fmt: skip
    }
