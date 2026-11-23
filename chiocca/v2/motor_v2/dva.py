"""Depreciação pela DVA (pré-registro do motor v2, seção 3.1, item "A depreciação, nesta ordem", passo 2).

Quando o DEPI do v1 não é calculável e a versão usada é a dos dados abertos, a depreciação de t e t-1 vem da DVA da
mesma DFP: a conta 7.04.01, 7.05.01 ou 7.07.01 cujo nome contém "deprecia", nessa ordem de preferência, do mesmo tipo
(consolidado ou individual) e da mesma versão, em valor absoluto. Nas versões do ENET, que não trazem a DVA, nada muda.

A DVA vem do mesmo zip da DFP que o v1 lê (`dfp_cia_aberta_<ano>.zip`), com o valor em reais pela escala do arquivo,
como as outras contas (`chiocca.cvm`). A comparação de nomes é a do estudo (`chiocca.texto.normaliza`: sem maiúsculas,
acentos nem espaços repetidos). Se a mesma conta e coluna aparecem mais de uma vez, vale a primeira linha do arquivo.
"""

from __future__ import annotations

import io
import zipfile
from pathlib import Path

import pandas as pd

from chiocca.cvm import TIPOS, cd_texto
from chiocca.texto import normaliza
from chiocca.v2.motor_v2 import abertura
from chiocca.variaveis import PENULTIMO, ULTIMO

CONTAS_DEPRECIACAO = ("7.04.01", "7.05.01", "7.07.01")  # nessa ordem de preferência
ESCALAS = {"MIL": 1000.0, "UNIDADE": 1.0}
CHAVE = ["cd_cvm", "dt_refer", "tipo", "versao"]
COLUNAS = [*CHAVE, "ordem", "cd_conta", "ds_conta", "valor"]
COLUNAS_DEPRECIACAO = [*CHAVE, "conta_dva_t", "depreciacao_dva_t", "conta_dva_t1", "depreciacao_dva_t1"]


def em_reais(bruto: pd.DataFrame, tipo: str) -> pd.DataFrame:
    """As linhas de um arquivo da DVA dos dados abertos (colunas da CVM, tudo como texto), com o valor em reais."""
    escala = bruto.ESCALA_MOEDA.map(ESCALAS)
    if escala.isna().any():
        raise ValueError(f"escala desconhecida na DVA: {set(bruto.ESCALA_MOEDA[escala.isna()])}")
    return pd.DataFrame({"cd_cvm": cd_texto(bruto.CD_CVM), "dt_refer": bruto.DT_REFER, "tipo": tipo,
                         "versao": bruto.VERSAO.astype(int), "ordem": bruto.ORDEM_EXERC, "cd_conta": bruto.CD_CONTA,
                         "ds_conta": bruto.DS_CONTA, "valor": bruto.VL_CONTA.astype(float) * escala})  # fmt: skip


def le(pasta: Path, ano: int) -> pd.DataFrame:
    """As linhas da DVA consolidada e individual do exercício, do zip da DFP na pasta dos arquivos brutos."""
    abertura.garantir_exercicio(ano)
    partes = []
    with zipfile.ZipFile(Path(pasta) / f"dfp_cia_aberta_{ano}.zip") as z:
        nomes = set(z.namelist())
        for tipo in TIPOS:
            arquivo = f"dfp_cia_aberta_DVA_{tipo}_{ano}.csv"
            if arquivo in nomes:
                bruto = pd.read_csv(io.BytesIO(z.read(arquivo)), sep=";", encoding="latin1", dtype=str)
                partes.append(em_reais(bruto, tipo))
    return pd.concat(partes, ignore_index=True) if partes else pd.DataFrame(columns=COLUNAS)


def depreciacao(linhas: pd.DataFrame) -> pd.DataFrame:
    """Por empresa-ano, tipo e versão: a conta escolhida e a depreciação, em módulo, de t (ÚLTIMO) e de t-1
    (PENÚLTIMO). A escolha é por coluna, como nas descrições sem rótulo."""
    casa = linhas.cd_conta.isin(CONTAS_DEPRECIACAO) & linhas.ds_conta.map(normaliza).str.contains("deprecia")
    d = linhas[casa & linhas.ordem.isin([ULTIMO, PENULTIMO])].copy()
    if d.empty:
        return pd.DataFrame(columns=COLUNAS_DEPRECIACAO)
    d["preferencia"] = d.cd_conta.map({c: i for i, c in enumerate(CONTAS_DEPRECIACAO)})
    d = d.sort_values("preferencia", kind="stable").drop_duplicates([*CHAVE, "ordem"])
    d["valor"] = d.valor.abs()
    out = d.pivot(index=CHAVE, columns="ordem", values=["cd_conta", "valor"])
    resultado = pd.DataFrame(index=out.index)
    for ordem, sufixo in ((ULTIMO, "t"), (PENULTIMO, "t1")):
        tem = ordem in out.columns.get_level_values(1)
        resultado[f"conta_dva_{sufixo}"] = out[("cd_conta", ordem)] if tem else None
        resultado[f"depreciacao_dva_{sufixo}"] = out[("valor", ordem)].astype(float) if tem else float("nan")
    return resultado.reset_index()[COLUNAS_DEPRECIACAO]
