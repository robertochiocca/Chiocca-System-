"""Números da análise depois do estudo 1 que dependem dos dados fora do git (pedido de 08/11/2026).

Lê `resultados/sinais_empresa_ano.csv` (saída do estudo 1) e a base "como era na época" (`data/base/`), sem mudar
nenhum dos dois, e grava:
- docs/analises_pos_estudo_1_numeros.json (versionado): persistência dos alertas, variante do teste contra o acaso
  sem a premissa de independência entre os anos e a nota posterior sobre balanços não preenchidos;
- resultados/nao_preenchidas_estudo_1.csv (fora do git): as empresa-anos com balanço não preenchido e os cálculos
  do estudo 1 que usaram um zero dessas colunas.
Em seguida, monta os documentos (`chiocca.v2.analises_pos_estudo_1`) e o resumo do estudo 1 com o resultado.

Definições:
- empresa-ano: uma por exercício, empresa e grupo, como nas taxas de alerta do estudo 1 (`chiocca.metricas`);
  "avaliada" e "em alerta" valem se valem para alguma linha da empresa no exercício;
- persistência: entre as empresa-anos em alerta cuja empresa também foi avaliada no ano anterior, no mesmo grupo,
  a fração que também estava em alerta no ano anterior;
- variante: para cada caso acertável, a chance ao acaso é a fração das empresas do mesmo grupo avaliadas em todos
  os anos do período afetado que tiveram pelo menos um alerta nesses anos;
- zero tratado como valor: o sinal tem valor no estudo 1 e pelo menos uma conta de balanço que ele usa, na coluna
  com ativo total zero, vale zero.

Uso: python -m chiocca.v2.analises_pos_estudo_1_dados
"""

from __future__ import annotations

import json
from collections import Counter
from collections.abc import Mapping
from pathlib import Path
from typing import Any

import pandas as pd

from chiocca import variaveis
from chiocca.base import RAIZ
from chiocca.sinais.mscore import COEFICIENTES
from chiocca.sinais_amostra import PERCENTIL
from chiocca.v2 import conferencias as cf
from chiocca.v2.analises_pos_estudo_1 import NUMEROS_DADOS, NUMEROS_ESTUDO_1, grupo_do_caso
from chiocca.v2.lacre import so_liberados
from chiocca.v2.linhagem import ENTRADAS

SINAIS = RAIZ / "resultados" / "sinais_empresa_ano.csv"
BASE = RAIZ / "data" / "base"
CSV_NAO_PREENCHIDAS = RAIZ / "resultados" / "nao_preenchidas_estudo_1.csv"
AMOSTRAS = {"nao_financeira": "nf", "financeira": "fin"}
ALERTAS = {"mscore": "alerta_mscore", "dpo": "alerta_dpo", "juro": "alerta_juro"}
SINAIS_V1 = (*COEFICIENTES, "mscore", "dpo", "juro", "lucro_sem_caixa")
COLUNAS = {cf.ULTIMO: "ultimo", cf.PENULTIMO: "penultimo"}


def _verdade(serie: pd.Series) -> pd.Series:
    return serie.astype(str).str.lower().eq("true")


def empresa_ano(s: pd.DataFrame) -> pd.DataFrame:
    a = s[s.amostra.isin(AMOSTRAS)].assign(
        avaliada=lambda d: _verdade(d.avaliada), em_alerta=lambda d: _verdade(d.em_alerta)
    )
    return a.groupby(["exercicio", "cd_cvm", "amostra"], as_index=False).agg(
        avaliada=("avaliada", "any"), em_alerta=("em_alerta", "any")
    )


def confere_taxas(ea: pd.DataFrame, n: dict[str, Any]) -> None:
    """As empresa-anos daqui são as mesmas das taxas de alerta do estudo 1 (senão, para)."""
    for amostra, chave in AMOSTRAS.items():
        g = ea[(ea.amostra == amostra) & ea.avaliada]
        esperado = (sum(v["avaliadas"] for v in n["taxa"][chave].values()),
                    sum(v["em_alerta"] for v in n["taxa"][chave].values()))  # fmt: skip
        if (len(g), int(g.em_alerta.sum())) != esperado:
            raise ValueError(f"empresa-anos diferentes das taxas do estudo 1 em {amostra}: {len(g)} x {esperado}")


def persistencia(ea: pd.DataFrame) -> dict[str, dict[str, int]]:
    av = ea[ea.avaliada]
    anterior = av[["exercicio", "cd_cvm", "amostra", "em_alerta"]].assign(exercicio=lambda d: d.exercicio + 1)
    pares = av.merge(anterior, on=["exercicio", "cd_cvm", "amostra"], suffixes=("", "_anterior"))
    out = {}
    for chave, amostra in (("nf", "nao_financeira"), ("fin", "financeira"), ("total", None)):
        x = pares if amostra is None else pares[pares.amostra == amostra]
        g = av if amostra is None else av[av.amostra == amostra]
        em = x[x.em_alerta]
        out[chave] = {
            "em_alerta_com_anterior_avaliado": int(len(em)),
            "anterior_tambem_em_alerta": int(em.em_alerta_anterior.sum()),
            "avaliadas": int(len(g)),
            "em_alerta": int(g.em_alerta.sum()),
        }
    return out


def variante(n: dict[str, Any], ea: pd.DataFrame) -> list[dict[str, Any]]:
    av = ea[ea.avaliada]
    out = []
    for c in n["casos"]:
        if not c["acertavel"]:
            continue
        anos = [int(a) for a in c["anos_periodo"]]
        x = av[(av.amostra == grupo_do_caso(c)) & av.exercicio.isin(anos)]
        por = x.groupby("cd_cvm").agg(anos=("exercicio", "nunique"), alerta=("em_alerta", "any"))
        todos = por[por.anos == len(anos)]
        out.append({
            "caso_id": c["caso_id"], "empresas": int(len(todos)), "com_alerta": int(todos.alerta.sum()),
            "empresa_do_caso_incluida": str(c["cd_cvm"]) in set(todos.index),
        })  # fmt: skip
    return out


def _zeros(sinal: str, coluna: str, valores: Mapping[str, float | None]) -> list[str]:
    """Contas de balanço da coluna que o sinal usa e que valem zero."""
    if sinal == "mscore":
        return sorted({z for comp in COEFICIENTES for z in _zeros(comp, coluna, valores)})
    return sorted({var for var, col in ENTRADAS.get(sinal, []) if col == coluna and var in variaveis.CONTAS
                   and variaveis.CONTAS[var][0] in ("BPA", "BPP") and valores.get(var) == 0.0})  # fmt: skip


def colunas_nao_preenchidas(meta: pd.DataFrame, base: Path = BASE) -> list[dict[str, Any]]:
    """As colunas com ativo total zero (conferência "não preenchido") e os valores de cada uma."""
    meta = so_liberados(meta)
    meta = meta[meta.status == "ok"]
    out = []
    for ano in sorted(meta.exercicio.unique()):
        m = meta[meta.exercicio == ano]
        contas = pd.read_csv(base / f"contas_{ano}.csv.gz", dtype={"cd_cvm": str, "cd_conta": str, "ds_conta": str})
        grupos = {k: g for k, g in contas.groupby(["cd_cvm", "dt_refer"])}
        for e in m.itertuples(index=False):
            g = grupos[(e.cd_cvm, e.dt_refer)]
            plano = e.plano if isinstance(e.plano, str) else "outro"
            for coluna in sorted(cf.colunas_nao_preenchidas(cf.conferir(g, plano))):
                bal = g[(g.ordem == coluna) & g.demonstracao.isin(["BPA", "BPP"])]
                out.append({"exercicio": int(ano), "cd_cvm": e.cd_cvm, "dt_refer": e.dt_refer, "coluna": coluna,
                            "balanco_todo_zero": bool(bal.valor.abs().sum() == 0),
                            "valores": variaveis.le_ordem(g, coluna).valores})  # fmt: skip
    return out


def nao_preenchidas(
    flags: list[dict[str, Any]], s: pd.DataFrame, n: dict[str, Any]
) -> tuple[dict[str, Any], pd.DataFrame]:
    """1c: alguma dessas empresa-anos entrou num cálculo do estudo 1 com zero tratado como valor?"""
    s = s.copy()
    chave = ["exercicio", "cd_cvm", "dt_refer"]
    por_chave: dict[tuple[int, str, str], dict[str, Any]] = {}
    for f in flags:
        linha = s[(s.exercicio == f["exercicio"]) & (s.cd_cvm == f["cd_cvm"]) & (s.dt_refer == f["dt_refer"])]
        if len(linha) != 1:
            raise ValueError(f"empresa-ano sem linha única nos sinais do estudo 1: {f['exercicio']} {f['cd_cvm']}")
        r = linha.iloc[0]
        k = (f["exercicio"], f["cd_cvm"], f["dt_refer"])
        d = por_chave.setdefault(k, {"exercicio": k[0], "cd_cvm": k[1], "dt_refer": k[2], "amostra": r.amostra,
                                     "colunas": [], "balanco_todo_zero": [], "zeros": {}, "dividas": []})  # fmt: skip
        d["colunas"].append(f["coluna"])
        d["dividas"].append(sum(f["valores"].get(v) or 0.0 for v in ("emprestimos_cp", "emprestimos_lp")))
        d["balanco_todo_zero"].append(f["balanco_todo_zero"])
        for sinal in SINAIS_V1:
            if pd.isna(r[sinal]):
                continue
            z = _zeros(sinal, f["coluna"], f["valores"])
            if z:
                d["zeros"].setdefault(sinal, []).extend(f"{var} ({f['coluna']})" for var in z)
    casos = {(str(c["cd_cvm"]), int(a)) for c in n["casos"] for a in (c.get("anos_periodo") or [])}
    por_sinal: dict[str, dict[str, int]] = {}
    so_alerta = so_avaliada = juro_metade = 0
    linhas = []
    for d in por_chave.values():
        r = s[(s.exercicio == d["exercicio"]) & (s.cd_cvm == d["cd_cvm"]) & (s.dt_refer == d["dt_refer"])].iloc[0]
        for sinal in d["zeros"]:
            x = por_sinal.setdefault(sinal, {"empresa_anos": 0, "alertas": 0})
            x["empresa_anos"] += 1
            if sinal in ALERTAS and str(r[ALERTAS[sinal]]).lower() == "true":
                x["alertas"] += 1
        # Dívida (curto + longo prazo) zero numa das colunas: a dívida média fica na metade da do outro ano.
        juro_metade += int("juro" in d["zeros"] and any(x == 0.0 for x in d["dividas"]))
        disparados = {sg for sg, col in ALERTAS.items() if str(r[col]).lower() == "true"}
        calculaveis = {sg for sg, col in ALERTAS.items() if str(r[col]).lower() in ("true", "false")}
        if d["amostra"] == "nao_financeira":
            so_alerta += int(bool(disparados) and disparados <= set(d["zeros"]))
            so_avaliada += int(bool(calculaveis) and calculaveis <= set(d["zeros"]))
        linhas.append({**{c: d[c] for c in chave}, "amostra": d["amostra"], "colunas": ";".join(d["colunas"]),
                       "balanco_todo_zero": ";".join(str(b) for b in d["balanco_todo_zero"]),
                       "sinais_com_zero": ";".join(f"{sg}: {', '.join(v)}" for sg, v in d["zeros"].items()),
                       "em_alerta": r.em_alerta, "no_periodo_de_um_caso": (d["cd_cvm"], d["exercicio"]) in casos})  # fmt: skip
    # DPO: os valores calculados com zero entraram no limite do decil superior do ano.
    dpo_zero = {k for k, d in por_chave.items() if "dpo" in d["zeros"]}
    nf = s[s.amostra == "nao_financeira"]
    mudam = mudam_em_caso = 0
    for ano in sorted({k[0] for k in dpo_zero}):
        g = nf[nf.exercicio == ano]
        fora = g.apply(lambda r: (int(r.exercicio), r.cd_cvm, r.dt_refer) in dpo_zero, axis=1)
        valores = g.loc[~fora, "dpo"].astype(float).dropna()
        limite = float(valores.quantile(PERCENTIL))
        for r in g[~fora & g.dpo.notna()].itertuples(index=False):
            novo = float(r.dpo) >= limite
            if novo != (str(r.alerta_dpo).lower() == "true"):
                mudam += 1
                mudam_em_caso += int((r.cd_cvm, int(r.exercicio)) in casos)
    colunas = Counter(COLUNAS[f["coluna"]] for f in flags)
    todo_zero = Counter(f["balanco_todo_zero"] for f in flags)
    amostras = Counter(d["amostra"] if d["amostra"] in AMOSTRAS else "fora" for d in por_chave.values())
    com_zero = [d for d in por_chave.values() if d["zeros"]]
    out = {
        "colunas": {"ultimo": colunas.get("ultimo", 0), "penultimo": colunas.get("penultimo", 0)},
        "colunas_balanco_todo_zero": todo_zero.get(True, 0),
        "colunas_so_total_zero": todo_zero.get(False, 0),
        "empresa_anos": len(por_chave),
        "na_amostra": {"nao_financeira": amostras.get("nao_financeira", 0),
                       "financeira": amostras.get("financeira", 0), "fora": amostras.get("fora", 0)},  # fmt: skip
        "com_zero_tratado_como_valor": len(com_zero),
        "por_sinal": dict(sorted(por_sinal.items(), key=lambda kv: SINAIS_V1.index(kv[0]))),
        "juro_com_divida_zero_num_dos_anos": juro_metade,
        "em_alerta_so_por_sinal_com_zero": so_alerta,
        "avaliadas_so_por_sinal_com_zero": so_avaliada,
        "dpo_com_zero_no_limite": len(dpo_zero),
        "alertas_dpo_que_mudariam_sem_eles": mudam,
        "no_periodo_de_um_caso": sum(1 for d in por_chave.values() if (d["cd_cvm"], d["exercicio"]) in casos),
        "alertas_dpo_que_mudariam_no_periodo_de_um_caso": mudam_em_caso,
    }
    return out, pd.DataFrame(linhas)


def calcula(
    meta: pd.DataFrame, s: pd.DataFrame, n: dict[str, Any], base: Path = BASE
) -> tuple[dict[str, Any], pd.DataFrame]:
    ea = empresa_ano(s)
    confere_taxas(ea, n)
    np_, lista = nao_preenchidas(colunas_nao_preenchidas(meta, base), s, n)
    out = {
        "gerado_por": "python -m chiocca.v2.analises_pos_estudo_1_dados",
        "persistencia": persistencia(ea),
        "variante": variante(n, ea),
        "nao_preenchidas": np_,
    }
    return out, lista


def main() -> None:
    from chiocca import relatorio_resultados
    from chiocca.v2 import analises_pos_estudo_1

    n = json.loads(NUMEROS_ESTUDO_1.read_text(encoding="utf-8"))
    meta = pd.read_csv(BASE / "empresa_ano.csv", dtype={"cd_cvm": str, "num_doc": str})
    s = pd.read_csv(SINAIS, dtype={"cd_cvm": str})
    out, lista = calcula(meta, s, n)
    CSV_NAO_PREENCHIDAS.parent.mkdir(exist_ok=True)
    lista.to_csv(CSV_NAO_PREENCHIDAS, index=False)
    NUMEROS_DADOS.write_text(json.dumps(out, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    analises_pos_estudo_1.main()
    relatorio_resultados.escreve_docs(n)


if __name__ == "__main__":
    main()
