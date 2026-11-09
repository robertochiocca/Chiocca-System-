"""Fixtures sintéticas no formato dos arquivos de dados abertos da CVM (testes sem rede).

Procedência: empresas FICTÍCIAS. As colunas e a codificação (CSV separado por ";" em latin1, dentro de um
zip por ano) seguem os dicionários de dados da DFP e do FCA e os arquivos baixados em 05/11/2026
(docs/reconhecimento.md, 1.1 e 1.2). Nenhum valor real da CVM é usado aqui.
"""

from __future__ import annotations

import io
import zipfile
from pathlib import Path

import pandas as pd

COLS_IDX = ["CNPJ_CIA", "DT_REFER", "VERSAO", "DENOM_CIA", "CD_CVM", "CATEG_DOC", "ID_DOC", "DT_RECEB", "LINK_DOC"]
COLS_DEM = [
    "CNPJ_CIA", "DT_REFER", "VERSAO", "DENOM_CIA", "CD_CVM", "GRUPO_DFP", "MOEDA", "ESCALA_MOEDA",
    "ORDEM_EXERC", "DT_INI_EXERC", "DT_FIM_EXERC", "CD_CONTA", "DS_CONTA", "VL_CONTA", "ST_CONTA_FIXA",
]  # fmt: skip
LINK = "http://www.rad.cvm.gov.br/ENETCONSULTA/frmDownloadDocumento.aspx?CodigoInstituicao=1&NumeroSequencialDocumento="


def _csv(df: pd.DataFrame) -> bytes:
    return df.to_csv(sep=";", index=False).encode("latin1")


def doc(cd: str, dt_refer: str, versao: int, dt_receb: str, num: int) -> dict[str, object]:
    return {
        "CNPJ_CIA": f"00.000.{cd:0>3}/0001-00", "DT_REFER": dt_refer, "VERSAO": versao, "DENOM_CIA": f"EMPRESA {cd}",
        "CD_CVM": f"{cd:0>6}", "CATEG_DOC": "DFP", "ID_DOC": num, "DT_RECEB": dt_receb, "LINK_DOC": LINK + str(num),
    }  # fmt: skip


def linha(cd: str, dt_refer: str, versao: int, ordem: str, conta: str, desc: str, valor: float, escala: str = "MIL",
          dt_ini: str = "") -> dict[str, object]:  # fmt: skip
    return {
        "CNPJ_CIA": f"00.000.{cd:0>3}/0001-00", "DT_REFER": dt_refer, "VERSAO": versao, "DENOM_CIA": f"EMPRESA {cd}",
        "CD_CVM": f"{cd:0>6}", "GRUPO_DFP": "", "MOEDA": "REAL", "ESCALA_MOEDA": escala, "ORDEM_EXERC": ordem,
        "DT_INI_EXERC": dt_ini, "DT_FIM_EXERC": dt_refer, "CD_CONTA": conta, "DS_CONTA": desc,
        "VL_CONTA": f"{valor:.10f}", "ST_CONTA_FIXA": "S",
    }  # fmt: skip


def dre(
    cd: str,
    dt: str,
    versao: int,
    receita_ult: float,
    receita_pen: float,
    desc_301: str = "Receita de Venda de Bens e/ou Serviços",
) -> list[dict[str, object]]:  # noqa: E501
    return [
        linha(cd, dt, versao, "ÚLTIMO", "3.01", desc_301, receita_ult),
        linha(cd, dt, versao, "PENÚLTIMO", "3.01", desc_301, receita_pen),
        linha(cd, dt, versao, "ÚLTIMO", "3.11", "Lucro/Prejuízo Consolidado do Período", receita_ult / 10),
    ]


def bpa(cd: str, dt: str, versao: int, ativo: float) -> list[dict[str, object]]:
    return [
        linha(cd, dt, versao, "ÚLTIMO", "1", "Ativo Total", ativo),
        linha(cd, dt, versao, "PENÚLTIMO", "1", "Ativo Total", ativo),
    ]


def escreve_dfp(
    pasta: Path, ano: int, indice: list[dict[str, object]], arquivos: dict[str, list[dict[str, object]]]
) -> None:
    with zipfile.ZipFile(pasta / f"dfp_cia_aberta_{ano}.zip", "w") as z:
        z.writestr(f"dfp_cia_aberta_{ano}.csv", _csv(pd.DataFrame(indice, columns=COLS_IDX)))
        for nome, linhas in arquivos.items():
            z.writestr(f"dfp_cia_aberta_{nome}_{ano}.csv", _csv(pd.DataFrame(linhas, columns=COLS_DEM)))


def escreve_fca(pasta: Path, ano: int, versoes: list[tuple[str, int, str, str]]) -> None:
    """versoes: (cd, versao, dt_receb, setor)."""
    idx, geral, vm = [], [], []
    for k, (cd, versao, receb, setor) in enumerate(versoes):
        idd = 9000 + k
        idx.append({"CNPJ_CIA": f"00.000.{cd:0>3}/0001-00", "DT_REFER": f"{ano}-01-01", "VERSAO": versao,
                    "DENOM_CIA": f"EMPRESA {cd}", "CD_CVM": f"{cd:0>6}", "CATEG_DOC": "FCA", "ID_DOC": idd,
                    "DT_RECEB": receb, "LINK_DOC": LINK + str(idd)})  # fmt: skip
        geral.append({"CNPJ_Companhia": f"00.000.{cd:0>3}/0001-00", "Data_Referencia": f"{ano}-01-01",
                      "Versao": versao, "ID_Documento": idd, "Codigo_CVM": f"{cd:0>6}",
                      "Setor_Atividade": setor})  # fmt: skip
        for codigo, valor in ((f"EMP{cd}3", "Ações Ordinárias"), ("", "Debêntures")):  # debênture sem código fica fora
            vm.append({"CNPJ_Companhia": f"00.000.{cd:0>3}/0001-00", "Data_Referencia": f"{ano}-01-01",
                       "Versao": versao, "ID_Documento": idd, "Valor_Mobiliario": valor,
                       "Codigo_Negociacao": codigo or None, "Mercado": "Bolsa",
                       "Data_Inicio_Negociacao": f"{ano - 5}-01-02", "Data_Fim_Negociacao": None})  # fmt: skip
    with zipfile.ZipFile(pasta / f"fca_cia_aberta_{ano}.zip", "w") as z:
        z.writestr(f"fca_cia_aberta_{ano}.csv", _csv(pd.DataFrame(idx)))
        z.writestr(f"fca_cia_aberta_geral_{ano}.csv", _csv(pd.DataFrame(geral)))
        z.writestr(f"fca_cia_aberta_valor_mobiliario_{ano}.csv", _csv(pd.DataFrame(vm)))


def escreve_cadastro(pasta: Path, linhas: list[tuple[str, str, str]]) -> None:
    """linhas: (cd, SIT, SETOR_ATIV)."""
    d = pd.DataFrame([{"CNPJ_CIA": f"00.000.{c:0>3}/0001-00", "DENOM_SOCIAL": f"EMPRESA {c}", "SIT": s, "CD_CVM": c,
                       "SETOR_ATIV": st} for c, s, st in linhas])  # fmt: skip
    (pasta / "cad_cia_aberta.csv").write_bytes(d.to_csv(sep=";", index=False).encode("latin1"))


def escreve_cache_enet(cache: Path, num: int, linhas: list[tuple[str, str, str, str, float]]) -> None:
    cache.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(linhas, columns=["demonstracao", "ordem", "cd_conta", "ds_conta", "valor"]).to_csv(
        cache / f"{num}_con.csv", index=False
    )


def zip_bytes(arquivos: dict[str, bytes]) -> bytes:
    b = io.BytesIO()
    with zipfile.ZipFile(b, "w") as z:
        for n, c in arquivos.items():
            z.writestr(n, c)
    return b.getvalue()
