"""Tabela de transações com partes relacionadas do Formulário de Referência (dados abertos da CVM).

Fonte: data/brutos/cvm/fre_cia_aberta_<ano>.zip, arquivo fre_cia_aberta_transacao_parte_relacionada_<ano>.csv, com
a versão e a data de entrega pelo índice fre_cia_aberta_<ano>.csv (conferido em 11/11/2026: a tabela só tem a última
versão de cada companhia no ano). O Formulário de Referência de um ano é entregue nesse ano, com informações do
exercício anterior: o exercício E usa o formulário do ano E + 1.

Regras (decisões de 11/11/2026): só a última versão, e só quando entregue até a data de referência; na linhagem,
"única versão disponível nos dados abertos; versões anteriores do Formulário de Referência não estão nos dados
abertos". Entregue depois da data: "não disponível na data". O nome da parte só aparece quando a tabela diz pessoa
jurídica e o detector de nomes não o marca; os campos de texto passam pelo mesmo detector.
"""

from __future__ import annotations

import csv
import io
import zipfile
from datetime import date
from functools import lru_cache
from pathlib import Path
from typing import Any

import pandas as pd

from chiocca import base
from chiocca.v2.leitor import nomes

PRIMEIRO_ANO, ULTIMO_ANO = 2010, 2024  # o de 2024 traz o exercício de 2023; o de 2025 já é do exercício lacrado
CAMPOS_TEXTO = {"Relacao_Emissor": "relacao", "Objeto_Contrato": "objeto", "Garantia_Seguro": "garantia",
                "Natureza_Razao_Operacao": "natureza", "Duracao_Transacao": "duracao", "Taxa_Juros": "taxa_juros"}  # fmt: skip
CAMPOS_VALOR = {"Data_Transacao": "data_transacao", "Montante_Envolvido": "montante", "Saldo_Existente": "saldo"}
TEXTOS = {
    "pt": {"parte_omitida": "parte relacionada (nome omitido)", "campo_omitido": "texto omitido (nome de pessoa física)",
           "linhagem": "única versão disponível nos dados abertos; versões anteriores do Formulário de Referência não "
                       "estão nos dados abertos",
           "nao_disponivel": "não disponível na data", "sem_formulario": "sem Formulário de Referência nos dados abertos",
           "sem_linhas": "o Formulário de Referência não traz transações com partes relacionadas na tabela"},
    "en": {"parte_omitida": "related party (name omitted)", "campo_omitido": "text omitted (natural-person name)",
           "linhagem": "only version available in the open data; earlier versions of the Reference Form are not in "
                       "the open data",
           "nao_disponivel": "not available on the date", "sem_formulario": "no Reference Form in the open data",
           "sem_linhas": "the Reference Form lists no related-party transactions in the table"},
}  # fmt: skip


def _vazio(v: Any) -> bool:
    return v is None or (isinstance(v, float) and pd.isna(v)) or not str(v).strip()


def linha(registro: dict[str, Any], lang: str) -> dict[str, Any]:
    """Uma transação na saída: nome só de pessoa jurídica não marcada; campos de texto pelo detector."""
    t = TEXTOS[lang]
    tipo = None if _vazio(registro.get("Tipo_Pessoa")) else str(registro["Tipo_Pessoa"]).strip().upper()
    parte = None if _vazio(registro.get("Parte_Relacionada")) else str(registro["Parte_Relacionada"]).strip()
    mostra_parte = tipo == "PJ" and parte is not None and not nomes.tem_nome_de_pessoa(parte)
    out: dict[str, Any] = {"parte": parte if mostra_parte else t["parte_omitida"], "parte_omitida": not mostra_parte,
                           "tipo_pessoa": tipo}  # fmt: skip
    for origem, destino in CAMPOS_TEXTO.items():
        v = None if _vazio(registro.get(origem)) else str(registro[origem]).strip()
        out[destino] = t["campo_omitido"] if v is not None and nomes.tem_nome_de_pessoa(v) else v
    for origem, destino in CAMPOS_VALOR.items():
        out[destino] = None if _vazio(registro.get(origem)) else str(registro[origem]).strip()
    return out


def arquivo(ano: int, brutos: Path | None = None) -> Path:
    return (brutos or base.BRUTOS) / f"fre_cia_aberta_{ano}.zip"


@lru_cache(maxsize=4)
def _tabelas(caminho: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    with zipfile.ZipFile(caminho) as z:
        nome_idx = next(n for n in z.namelist() if n.startswith("fre_cia_aberta_2") and n.count("_") == 3)
        idx = pd.read_csv(z.open(nome_idx), sep=";", encoding="latin1", dtype=str)
        nome_tab = next(n for n in z.namelist() if "transacao_parte_relacionada" in n)
        bruto = z.read(nome_tab).decode("latin1")
    # Aspas soltas dentro dos campos quebram a leitura com aspas; conferido em 11/11/2026 que, de 2010 a 2024, toda linha
    # física tem o número de campos do cabeçalho: a leitura é sem tratamento de aspas, e a linha é a linha do arquivo.
    tab = pd.read_csv(io.StringIO(bruto), sep=";", dtype=str, quoting=csv.QUOTE_NONE, keep_default_na=False)
    tab["linha_arquivo"] = range(2, len(tab) + 2)
    return idx, tab


def transacoes(cd_cvm: str, exercicio: int, data_referencia: date, lang: str, brutos: Path | None = None
               ) -> dict[str, Any]:  # fmt: skip
    """O bloco do Formulário de Referência para a investigação (exercício E: formulário do ano E + 1)."""
    t = TEXTOS[lang]
    ano = exercicio + 1
    caminho = arquivo(ano, brutos)
    if not (PRIMEIRO_ANO <= ano <= ULTIMO_ANO) or not caminho.exists():
        return {"status": "sem_formulario", "motivo": t["sem_formulario"], "ano_formulario": ano, "linhas": []}
    idx, tab = _tabelas(str(caminho))
    cd = str(cd_cvm).lstrip("0")
    da_cia = idx[idx.CD_CVM.str.lstrip("0") == cd]
    if da_cia.empty:
        return {"status": "sem_formulario", "motivo": t["sem_formulario"], "ano_formulario": ano, "linhas": []}
    ultima = da_cia.assign(v=da_cia.VERSAO.astype(int)).sort_values("v").iloc[-1]
    documento: dict[str, Any] = {"tipo": "FRE", "ano": ano, "versao": int(ultima.VERSAO), "dt_receb": str(ultima.DT_RECEB)[:10],
                 "num_doc": str(ultima.ID_DOC), "origem": "dados_abertos", "arquivo": caminho.name,
                 "linhagem": t["linhagem"]}  # fmt: skip
    if str(documento["dt_receb"]) > data_referencia.isoformat():
        return {"status": "nao_disponivel_na_data", "motivo": t["nao_disponivel"], "ano_formulario": ano,
                "documento": documento, "linhas": []}  # fmt: skip
    linhas_cia = tab[tab.ID_Documento == str(ultima.ID_DOC)]
    if linhas_cia.empty:
        return {"status": "sem_linhas", "motivo": t["sem_linhas"], "ano_formulario": ano, "documento": documento,
                "linhas": []}  # fmt: skip
    saida = [linha(r, lang) | {"linha_arquivo": int(r["linha_arquivo"])} for r in linhas_cia.to_dict("records")]
    return {"status": "disponivel", "motivo": None, "ano_formulario": ano, "documento": documento, "linhas": saida}
