"""Leitura dos arquivos de dados abertos da CVM (DFP, FCA e cadastro) baixados por chiocca.dados.

Os arquivos de demonstrações trazem só a última versão de cada documento; o índice da DFP traz todas as
versões, com a data de recebimento (docs/reconhecimento.md, 1.3). Valores são convertidos para reais:
ESCALA_MOEDA = MIL multiplica por 1.000 (reconhecimento, 2.9).
"""

from __future__ import annotations

import io
import re
import zipfile
from functools import lru_cache
from pathlib import Path

import pandas as pd

# Demonstrações usadas pelos sinais mvp. A DFC entra pelos dois métodos (indireto e direto).
DEMONSTRACOES = ("BPA", "BPP", "DRE", "DFC_MI", "DFC_MD")
TIPOS = ("con", "ind")
COLUNAS_CONTAS = ["cd_cvm", "dt_refer", "versao", "tipo", "demonstracao", "ordem", "cd_conta", "ds_conta", "valor"]


def cd_texto(s: pd.Series) -> pd.Series:
    """CD_CVM como texto sem zeros à esquerda (o índice traz '001023', o cadastro traz '1023')."""
    return s.astype(str).str.strip().str.lstrip("0").replace("", "0")


def num_doc(link: str) -> str:
    m = re.search(r"NumeroSequencialDocumento=(\d+)", link)
    if not m:
        raise ValueError(f"link sem NumeroSequencialDocumento: {link}")
    return m.group(1)


class Fontes:
    """Acesso aos arquivos brutos de uma pasta (data/brutos/cvm ou uma fixture de teste)."""

    def __init__(self, pasta: Path, cache_enet: Path | None = None) -> None:
        self.pasta = Path(pasta)
        self.cache_enet = Path(cache_enet) if cache_enet else self.pasta.parent.parent / "cache" / "enet"
        # Os métodos com lru_cache ficam presos a esta instância.
        self.indice_dfp = lru_cache(maxsize=None)(self._indice_dfp)  # type: ignore[method-assign]
        self.contas_abertas = lru_cache(maxsize=2)(self._contas_abertas)  # type: ignore[method-assign]
        self.fca = lru_cache(maxsize=None)(self._fca)  # type: ignore[method-assign]
        self.cadastro = lru_cache(maxsize=1)(self._cadastro)  # type: ignore[method-assign]

    def _zip(self, nome: str) -> zipfile.ZipFile:
        return zipfile.ZipFile(self.pasta / nome)

    def _indice_dfp(self, ano: int) -> pd.DataFrame:
        with self._zip(f"dfp_cia_aberta_{ano}.zip") as z:
            d = pd.read_csv(io.BytesIO(z.read(f"dfp_cia_aberta_{ano}.csv")), sep=";", encoding="latin1", dtype=str)
        d = d.drop_duplicates()
        d["cd_cvm"] = cd_texto(d.CD_CVM)
        d["versao"] = d.VERSAO.astype(int)
        d["dt_receb"] = pd.to_datetime(d.DT_RECEB).dt.date
        d["num_doc"] = d.LINK_DOC.map(num_doc)
        return d[["cd_cvm", "CNPJ_CIA", "DENOM_CIA", "DT_REFER", "versao", "dt_receb", "num_doc", "ID_DOC", "LINK_DOC"]]

    def _contas_abertas(self, ano: int) -> dict[tuple[str, str, str], pd.DataFrame]:
        """(cd_cvm, dt_refer, tipo) -> contas daquela empresa-ano, só a última versão (a dos arquivos)."""
        partes = []
        with self._zip(f"dfp_cia_aberta_{ano}.zip") as z:
            nomes = set(z.namelist())
            for dem in DEMONSTRACOES:
                for tipo in TIPOS:
                    arq = f"dfp_cia_aberta_{dem}_{tipo}_{ano}.csv"
                    if arq not in nomes:
                        continue
                    d = pd.read_csv(io.BytesIO(z.read(arq)), sep=";", encoding="latin1", dtype=str)
                    escala = d.ESCALA_MOEDA.map({"MIL": 1000.0, "UNIDADE": 1.0})
                    if escala.isna().any():
                        raise ValueError(f"escala desconhecida em {arq}: {set(d.ESCALA_MOEDA[escala.isna()])}")
                    partes.append(
                        pd.DataFrame(
                            {
                                "cd_cvm": cd_texto(d.CD_CVM),
                                "dt_refer": d.DT_REFER,
                                "versao": d.VERSAO.astype(int),
                                "tipo": tipo,
                                "demonstracao": dem,
                                "ordem": d.ORDEM_EXERC,
                                "cd_conta": d.CD_CONTA,
                                "ds_conta": d.DS_CONTA,
                                "valor": d.VL_CONTA.astype(float) * escala,
                            }
                        )
                    )
        if not partes:
            return {}
        tudo = pd.concat(partes, ignore_index=True)
        return {k: g.reset_index(drop=True) for k, g in tudo.groupby(["cd_cvm", "dt_refer", "tipo"], sort=False)}

    def _fca(self, ano: int) -> pd.DataFrame:
        """Versões do FCA do ano, com data de recebimento e setor de atividade."""
        arq = f"fca_cia_aberta_{ano}.zip"
        if not (self.pasta / arq).exists():
            return pd.DataFrame(columns=["cd_cvm", "versao", "dt_receb", "setor"])
        with self._zip(arq) as z:
            idx = pd.read_csv(io.BytesIO(z.read(f"fca_cia_aberta_{ano}.csv")), sep=";", encoding="latin1", dtype=str)
            geral = pd.read_csv(
                io.BytesIO(z.read(f"fca_cia_aberta_geral_{ano}.csv")), sep=";", encoding="latin1", dtype=str
            )
        idx = idx.drop_duplicates()
        g = geral[["ID_Documento", "Setor_Atividade"]].drop_duplicates("ID_Documento")
        d = idx.merge(g, left_on="ID_DOC", right_on="ID_Documento", how="left")
        return pd.DataFrame(
            {
                "cd_cvm": cd_texto(d.CD_CVM),
                "versao": d.VERSAO.astype(int),
                "dt_receb": pd.to_datetime(d.DT_RECEB).dt.date,
                "setor": d.Setor_Atividade,
            }
        )

    def _cadastro(self) -> pd.DataFrame:
        d = pd.read_csv(self.pasta / "cad_cia_aberta.csv", sep=";", encoding="latin1", dtype=str)
        d["cd_cvm"] = cd_texto(d.CD_CVM)
        return d
