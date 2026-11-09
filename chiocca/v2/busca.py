"""Busca de empresas e dados cadastrais na data de referência (Fase D).

Regra do projeto (09/11/2026, docs/contratos.md, seção 6): a busca é só por nome, código CVM ou CNPJ, e o resultado
sai em ordem alfabética da denominação. Nenhuma função aqui ordena empresas por alerta, percentil ou escore, e o
resultado não traz nenhum sinal. A empresa entra na busca se tem DFP de exercício liberado entregue até a data.

O nome mostrado é o da época: o do FCA entregue até a data; sem FCA, o do índice da DFP (que pode ser o nome atual,
marcado em `origem_denominacao`). A busca por nome olha só os nomes conhecidos na data, para não achar uma empresa
por um nome que ela só teve depois.
"""

from __future__ import annotations

import re
import unicodedata
from datetime import date
from typing import Any

import pandas as pd

from chiocca.v2.lacre import ULTIMO_EXERCICIO_LIBERADO

LIMITE_PADRAO, LIMITE_MAXIMO = 20, 50
MINIMO_NOME = 3
CRITERIOS = ("nome", "cd_cvm", "cnpj")
ORDEM = "denominacao"  # a única ordem possível: alfabética, nunca por alerta, percentil ou escore


class BuscaInvalida(ValueError):
    """Busca vazia ou curta demais; a API recusa com o motivo."""


def normaliza(texto: str) -> str:
    """Sem acento, sem diferença de maiúsculas e com espaços simples."""
    sem = "".join(c for c in unicodedata.normalize("NFKD", str(texto)) if not unicodedata.combining(c))
    return re.sub(r"\s+", " ", sem).strip().casefold()


def criterio(busca: str) -> tuple[str, str]:
    """Nome, código CVM (até 6 dígitos) ou CNPJ (14 dígitos, com ou sem pontuação)."""
    b = (busca or "").strip()
    digitos = re.sub(r"[.\-/\s]", "", b)
    if digitos.isdigit() and len(digitos) == 14:
        return "cnpj", digitos
    if digitos.isdigit() and len(digitos) <= 6:
        return "cd_cvm", digitos.lstrip("0") or "0"
    n = normaliza(b)
    if len(n) < MINIMO_NOME:
        raise BuscaInvalida(f"busca por nome precisa de pelo menos {MINIMO_NOME} caracteres")
    return "nome", n


def _universo(fontes: Any, d: date) -> pd.DataFrame:
    """Empresas com DFP de exercício liberado entregue até a data, com o CNPJ e o nome do índice da última."""
    return fontes.consulta(
        """
        SELECT cd_cvm, arg_max(CNPJ_CIA, CAST(dt_receb AS DATE)) AS cnpj,
               arg_max(DENOM_CIA, CAST(dt_receb AS DATE)) AS nome_indice
        FROM versoes WHERE CAST(dt_receb AS DATE) <= ? AND exercicio <= ? GROUP BY cd_cvm
        """,
        [d, ULTIMO_EXERCICIO_LIBERADO],
    )


def _nomes_fca(fontes: Any, d: date) -> pd.DataFrame:
    return fontes.consulta(
        "SELECT cd_cvm, nome, CAST(dt_receb AS DATE) AS dt_receb, versao FROM nomes WHERE CAST(dt_receb AS DATE) <= ?",
        [d],
    )


def primeiro_ano_com_codigo(fontes: Any) -> int | None:
    a = fontes.consulta("SELECT min(ano) AS a FROM valores_mobiliarios").a
    return None if a.empty or pd.isna(a.iloc[0]) else int(a.iloc[0])


def codigos(fontes: Any, cd_cvm: str, d: date) -> tuple[list[dict[str, Any]], str | None]:
    """Códigos de negociação na data e, se a lista sai vazia, o motivo (derivado do armazém)."""
    cods = fontes.codigos_negociacao(cd_cvm, d) if hasattr(fontes, "codigos_negociacao") else []
    if cods:
        return cods, None
    ano = primeiro_ano_com_codigo(fontes) if hasattr(fontes, "consulta") else None
    desde = f" (nos dados abertos, o campo só vem preenchido a partir do FCA de {ano})" if ano else ""
    return [], f"nenhum código de negociação no FCA entregue até a data{desde}"


def buscar(fontes: Any, busca: str, d: date, limite: int = LIMITE_PADRAO) -> dict[str, Any]:
    tipo, chave = criterio(busca)
    if not 1 <= limite <= LIMITE_MAXIMO:
        raise BuscaInvalida(f"limite de 1 a {LIMITE_MAXIMO}")
    u = _universo(fontes, d)
    nomes = _nomes_fca(fontes, d)
    ultimo = nomes.sort_values(["dt_receb", "versao"]).groupby("cd_cvm").tail(1).set_index("cd_cvm").nome
    u["denominacao"] = u.cd_cvm.map(ultimo)
    u["origem_denominacao"] = u.denominacao.notna().map({True: "fca", False: "indice_dfp"})
    u["denominacao"] = u.denominacao.fillna(u.nome_indice)
    if tipo == "cnpj":
        achadas = u[u.cnpj.astype(str).str.replace(r"\D", "", regex=True) == chave]
    elif tipo == "cd_cvm":
        achadas = u[u.cd_cvm == chave]
    else:
        conhecidos = pd.concat([nomes[["cd_cvm", "nome"]],
                                u.loc[u.origem_denominacao == "indice_dfp", ["cd_cvm", "nome_indice"]].rename(
                                    columns={"nome_indice": "nome"})])  # fmt: skip
        pares = zip(conhecidos.cd_cvm, conhecidos.nome)
        bate = {str(c) for c, n in pares if isinstance(n, str) and chave in normaliza(n)}
        achadas = u[u.cd_cvm.isin(bate)]
    ordem = achadas.denominacao.map(lambda x: normaliza(str(x)))
    achadas = achadas.assign(_ordem=ordem).sort_values(["_ordem", "cd_cvm"])  # alfabética; nunca por sinal
    resultados = []
    for r in achadas.head(limite).itertuples(index=False):
        cods, motivo = codigos(fontes, str(r.cd_cvm), d)
        resultados.append({"cd_cvm": str(r.cd_cvm), "cnpj": r.cnpj, "denominacao": r.denominacao,
                           "origem_denominacao": r.origem_denominacao, "codigos_negociacao": cods,
                           "motivo_codigos_negociacao": motivo})  # fmt: skip
    return {"busca": busca, "criterio": tipo, "data_referencia": d.isoformat(), "ordem": ORDEM,
            "total": int(len(achadas)), "resultados": resultados}  # fmt: skip


def exercicios_na_data(fontes: Any, cd_cvm: str, d: date) -> list[int]:
    """Exercícios liberados com DFP entregue até a data."""
    e = fontes.consulta(
        "SELECT DISTINCT exercicio FROM versoes WHERE cd_cvm = ? AND CAST(dt_receb AS DATE) <= ? AND exercicio <= ? "
        "ORDER BY exercicio",
        [cd_cvm, d, ULTIMO_EXERCICIO_LIBERADO],
    )
    return [int(x) for x in e.exercicio]
