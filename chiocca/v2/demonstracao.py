"""Dados da demonstração (Fase E2, 10/11/2026): as companhias do modo demonstração, em ordem alfabética, com o caso
do gabarito (tipo, data pública, período afetado e fonte), as datas de cada uma, o rótulo de cada data e a data
inicial, e os destaques da página inicial, tirados dos exemplos versionados de docs/exemplos/.

É a rota /api/v1/demonstracao e, na demonstração estática, o `indice.json` (a mesma saída, conferida por teste). A
lista mostra o caso, nunca o resultado dos sinais: nada aqui é ordenado nem filtrado por alerta, percentil ou escore.
Das notas do gabarito não sai nada (elas citam pessoas); só o tipo do caso, a data pública, o período e a fonte.
"""

from __future__ import annotations

import json
from collections.abc import Callable
from typing import Any

import pandas as pd

from chiocca import base
from chiocca.corte import data_corte
from chiocca.v2 import busca
from chiocca.v2.lacre import DATA_REFERENCIA_MAXIMA

TIPOS = ("processo_cvm", "fraude_confirmada", "republicacao")
ROTULOS = ("exercicio_anterior", "periodo_afetado", "depois_da_revelacao", "data_maxima")
CAMPOS_EMPRESA = ("cd_cvm", "cnpj", "denominacao", "origem_denominacao", "codigos_negociacao",
                  "motivo_codigos_negociacao")  # fmt: skip


def gabarito() -> pd.DataFrame:
    gab = pd.read_csv(base.RAIZ / "data" / "gabarito_casos.csv", dtype=str)
    return gab.assign(cd=gab.cd_cvm.fillna("").astype(str).str.lstrip("0"))


def _texto(v: Any) -> str | None:
    return None if v is None or pd.isna(v) or not str(v).strip() else str(v).strip()


def casos_da_empresa(gab: pd.DataFrame, cd: str) -> list[dict[str, Any]]:
    """Os casos do gabarito da companhia, pela data pública (sem data por último): tipo, data, período e fonte."""
    casos = []
    for c in gab[gab.cd == cd].itertuples(index=False):
        ini, fim = _texto(c.periodo_afetado_inicio), _texto(c.periodo_afetado_fim)
        tipos = [t for t in (_texto(c.tipo_evento) or "").split(";") if t]
        casos.append({"caso_id": str(c.caso_id), "tipo_evento": tipos, "data_publica": _texto(c.data_publica),
                      "periodo_afetado": [int(ini), int(fim)] if ini and fim else None,
                      "fonte": _texto(c.fonte_principal_url)})  # fmt: skip
    return sorted(casos, key=lambda x: (x["data_publica"] is None, x["data_publica"] or "", x["caso_id"]))


def _exercicio_de_cada_data(fontes: Any, cd: str, anos: set[int]) -> dict[str, int]:
    """Para cada exercício, a data de corte (a mesma conta do plano da demonstração estática)."""
    from chiocca.v2.demonstracao_estatica import _fim_do_exercicio

    out = {}
    for a in sorted(anos):
        fim = _fim_do_exercicio(fontes, cd, a)
        if fim:
            out[data_corte(fim).isoformat()] = a
    return out


def rotulos_das_datas(
    datas: list[str], exercicio_da_data: dict[str, int], casos: list[dict[str, Any]]
) -> dict[str, str]:
    """Rótulo de cada data: o corte do exercício anterior ao período afetado, o de um exercício do período afetado, ou
    31/12/2024 (depois da revelação, se todas as datas públicas forem anteriores; senão, só a data máxima)."""
    periodos = [c["periodo_afetado"] for c in casos if c["periodo_afetado"]]
    publicas = [c["data_publica"] for c in casos if c["data_publica"]]
    maxima = DATA_REFERENCIA_MAXIMA.isoformat()
    out = {}
    for d in datas:
        a = exercicio_da_data.get(d)
        if d == maxima or a is None:
            revelado = bool(publicas) and len(publicas) == len(casos) and max(publicas) < d
            out[d] = "depois_da_revelacao" if revelado else "data_maxima"
        elif any(ini <= a <= fim for ini, fim in periodos):
            out[d] = "periodo_afetado"
        else:
            out[d] = "exercicio_anterior"
    return out


def destaques() -> dict[str, Any]:
    """Os cartões "Na época" e "Depois" da página inicial, tirados dos exemplos versionados (a Americanas, exercício
    2021): o patrimônio líquido de 2021 como entregue e como apareceu no comparativo da DFP seguinte."""
    from chiocca.v2 import exemplos

    na_epoca, depois = exemplos.DATAS
    antes = json.loads((exemplos.PASTA / f"{exemplos.nome('pt', na_epoca)}.json").read_text(encoding="utf-8"))
    inv = json.loads((exemplos.PASTA / f"{exemplos.nome('pt', depois)}.json").read_text(encoding="utf-8"))
    pl = next(
        x for x in inv["mudancas"]["comparativo_destacadas"] if (x["demonstracao"], x["cd_conta"]) == ("BPP", "2.03")
    )
    return {"cd_cvm": exemplos.CD_CVM, "exercicio": exemplos.EXERCICIO, "na_epoca": na_epoca, "depois": depois,
            "denominacao_na_epoca": antes["empresa"]["denominacao"],
            "patrimonio_liquido": {"valor": pl["valor"], "valor_comparativo": pl["valor_comparativo"],
                                   "exercicio_comparativo": exemplos.EXERCICIO + 1,
                                   "dt_receb_comparativo": pl["dt_receb_seguinte"]}}  # fmt: skip


def montar(
    fontes: Any,
    empresa_na_data: Callable[[str, str], dict[str, Any]],
    empresas: set[str],
    gab: pd.DataFrame | None = None,
) -> dict[str, Any]:
    """A saída da rota: `empresa_na_data(cd, data)` devolve o bloco da empresa na data (o da rota da empresa)."""
    from chiocca.v2.demonstracao_estatica import _exercicios_do_caso, plano

    gab = gabarito() if gab is None else gab
    planos = plano(fontes, empresas, gab)
    out = []
    for cd, datas in planos.items():
        ultima = max(datas)
        e = empresa_na_data(cd, ultima)
        nomes = set(fontes.consulta("SELECT DISTINCT nome FROM nomes WHERE cd_cvm = ? AND CAST(dt_receb AS DATE) <= ?",
                                    [cd, DATA_REFERENCIA_MAXIMA]).nome.dropna())  # fmt: skip
        nomes |= {e["denominacao"]} if e["denominacao"] else set()
        casos = casos_da_empresa(gab, cd)
        ex_da_data = _exercicio_de_cada_data(fontes, cd, _exercicios_do_caso(gab[gab.cd == cd]))
        rotulos = rotulos_das_datas(list(datas), ex_da_data, casos)
        afetadas = [d for d in datas if rotulos[d] == "periodo_afetado"]
        extra = {"nomes": sorted(nomes), "datas": datas, "rotulos_datas": rotulos,
                 "data_inicial": afetadas[0] if afetadas else ultima, "casos": casos}  # fmt: skip
        out.append({k: e[k] for k in CAMPOS_EMPRESA} | extra)
    out.sort(key=lambda x: (busca.normaliza(str(x["denominacao"])), x["cd_cvm"]))
    return {"ordem": busca.ORDEM, "empresas": out, "destaques": destaques()}
