"""Funções comuns dos scripts da Fase 0 (reconhecimento da estrutura dos dados da CVM).

Regra da Fase 0: só estrutura. Nenhuma função deste módulo lê a coluna VL_CONTA.
A pasta dos arquivos baixados vem da variável de ambiente CHIOCCA_CVM_RAW
(padrão: data/brutos/cvm, fora do git).
"""

from __future__ import annotations

import io
import os
import re
import unicodedata
import zipfile
from pathlib import Path

import pandas as pd

RAW = Path(os.environ.get("CHIOCCA_CVM_RAW", "data/brutos/cvm"))
ANOS_DFP = range(2010, 2027)
ANOS_COMPLETOS = range(2010, 2026)

# Casos do gabarito: removidos das contagens de estrutura da Fase 0.
# 22837 (Drogarias Americanas SA) saiu só por ter "Americanas" no nome.
PADRAO_EXCLUIR = re.compile(r"AMERICANAS|B2W|\bIRB\b|IRB[- ]?BRASIL", re.I)

COLS_ESTRUTURA = [
    "CNPJ_CIA",
    "DT_REFER",
    "VERSAO",
    "DENOM_CIA",
    "CD_CVM",
    "GRUPO_DFP",
    "MOEDA",
    "ESCALA_MOEDA",
    "ORDEM_EXERC",
    "DT_INI_EXERC",
    "DT_FIM_EXERC",
    "CD_CONTA",
    "DS_CONTA",
    "ST_CONTA_FIXA",
]  # VL_CONTA fica de fora de propósito
COLS_INDICE = ["CNPJ_CIA", "DT_REFER", "VERSAO", "DENOM_CIA", "CD_CVM", "CATEG_DOC", "ID_DOC", "DT_RECEB", "LINK_DOC"]


def norm(s: object) -> str:
    """Minúsculas, sem acento e sem espaços nas pontas."""
    t = unicodedata.normalize("NFKD", str(s))
    return "".join(c for c in t if not unicodedata.combining(c)).lower().strip()


def cadastro() -> pd.DataFrame:
    return pd.read_csv(RAW / "cad_cia_aberta.csv", sep=";", encoding="latin1", dtype=str)


def ler_dfp(ano: int, nome: str, cols: list[str] | None = None) -> pd.DataFrame:
    """Lê um arquivo do zip da DFP sem VL_CONTA. nome: '' (índice), 'BPA_con', 'DRE_ind', ..."""
    arq = f"dfp_cia_aberta_{nome}_{ano}.csv" if nome else f"dfp_cia_aberta_{ano}.csv"
    with zipfile.ZipFile(RAW / f"dfp_cia_aberta_{ano}.zip") as z:
        if arq not in z.namelist():
            return pd.DataFrame()
        raw = z.read(arq)
    cab = raw[:4000].decode("latin1").splitlines()[0].split(";")
    pedidas = cols or (COLS_INDICE if not nome else COLS_ESTRUTURA)
    use = [c for c in pedidas if c in cab and c != "VL_CONTA"]
    return pd.read_csv(io.BytesIO(raw), sep=";", encoding="latin1", dtype=str, usecols=use)


def ler_fca_geral(ano: int) -> pd.DataFrame:
    with zipfile.ZipFile(RAW / f"fca_cia_aberta_{ano}.zip") as z:
        raw = z.read(f"fca_cia_aberta_geral_{ano}.csv")
    return pd.read_csv(io.BytesIO(raw), sep=";", encoding="latin1", dtype=str)


def cd(s: pd.Series) -> pd.Series:
    """CD_CVM como texto sem zeros à esquerda."""
    return s.astype(int).astype(str)


def excluidos() -> dict[str, str]:
    """CD_CVM dos casos do gabarito (e homônimos), achados por nome no cadastro e nos índices."""
    cad = cadastro()
    m = cad["DENOM_SOCIAL"].fillna("").str.contains(PADRAO_EXCLUIR) | cad["DENOM_COMERC"].fillna("").str.contains(
        PADRAO_EXCLUIR
    )
    out = {str(int(r.CD_CVM)): r.DENOM_SOCIAL for r in cad[m].itertuples()}
    for ano in ANOS_DFP:
        idx = ler_dfp(ano, "", ["CD_CVM", "DENOM_CIA"])
        mm = idx["DENOM_CIA"].fillna("").str.contains(PADRAO_EXCLUIR)
        for r in idx[mm].drop_duplicates().itertuples():
            out.setdefault(str(int(r.CD_CVM)), r.DENOM_CIA)
    return out


def sem_excluidos(df: pd.DataFrame, exc: dict[str, str]) -> pd.DataFrame:
    if df.empty or "CD_CVM" not in df:
        return df
    return df[~cd(df["CD_CVM"]).isin(exc)]


def tipo_plano(desc_301: object) -> str:
    """Plano de contas pela descrição da conta 3.01 da DRE."""
    p = norm(desc_301) if isinstance(desc_301, str) else ""
    if "intermediacao financeira" in p:
        return "banco"
    if p in ("receitas das operacoes", "receitas das atividades seguradoras/resseguradoras"):
        return "seguradora"
    if "venda de bens" in p or "vendas" in p:
        return "nao_financeiro"
    return "outro"


def planos(exc: dict[str, str]) -> pd.DataFrame:
    """Uma linha por (ano, tipo con/ind, cd) com a descrição de 3.01 e o plano de contas."""
    linhas = []
    for ano in ANOS_COMPLETOS:
        for tipo in ("con", "ind"):
            d = sem_excluidos(ler_dfp(ano, f"DRE_{tipo}", ["CD_CVM", "ORDEM_EXERC", "CD_CONTA", "DS_CONTA"]), exc)
            d = d[(d.ORDEM_EXERC == "ÚLTIMO") & (d.CD_CONTA == "3.01")]
            for r in d.drop_duplicates("CD_CVM").itertuples():
                linhas.append((ano, tipo, str(int(r.CD_CVM)), r.DS_CONTA))
    df = pd.DataFrame(linhas, columns=["ano", "tipo", "cd", "d301"])
    df["plano"] = df.d301.map(tipo_plano)
    return df
