"""Escore, alerta e ranking do motor v2 (pré-registro do motor v2, seção 4).

- **Percentil de cada sinal:** dentro do exercício e do grupo, entre as empresa-anos com o sinal calculável, pelo
  `rank(pct=True)` do pandas (empates recebem a média das posições). Em todos os sinais, valor maior é mais incomum.
- **Escore:** o maior percentil entre os sinais calculáveis da empresa-ano.
- **Avaliada:** com pelo menos um sinal calculável.
- **Alerta:** escore maior ou igual ao quantil de 90% do escore entre as avaliadas do exercício e do grupo, pelo
  `quantile(0.9)` do pandas, com interpolação linear.
- **Ranking:** o escore, do maior para o menor, e as empresa-anos sem escore depois; desempate pelo código CVM
  (numérico, crescente) e, entre as empresa-anos da mesma companhia, pelo exercício (emenda 2, item 3(b), do estudo 2).
- **Ficha:** o percentil de cada sinal e qual define o escore (os empatados no maior percentil, separados por ";").
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from chiocca.sinais_amostra import AMOSTRA_FIN, AMOSTRA_NF

PERCENTIL = 0.9
SINAIS_DO_ESCORE = {AMOSTRA_NF: ("mscore", "dpo", "juro", "benford"), AMOSTRA_FIN: ("peso_nao_recorrente", "benford")}
TODOS_OS_SINAIS = ("mscore", "dpo", "juro", "peso_nao_recorrente", "benford")
COLUNAS = [*(f"pct_{x}" for x in TODOS_OS_SINAIS), "escore", "n_sinais_calculaveis", "sinal_do_escore", "avaliada",
           "em_alerta"]  # fmt: skip


def sinais_do_escore(com_benford: bool) -> dict[str, tuple[str, ...]]:
    """Os sinais de cada grupo; sem a mudança do Benford, os do v1."""
    return {g: tuple(x for x in s if com_benford or x != "benford") for g, s in SINAIS_DO_ESCORE.items()}


def alerta(s: pd.DataFrame, sinais: dict[str, tuple[str, ...]]) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Percentis, escore, avaliada e alerta de cada empresa-ano, dentro do exercício e do grupo (`amostra`). Fora dos
    dois grupos, nem avaliada nem em alerta. Devolve (sinais, limiares), com o limite de cada exercício e grupo."""
    s = s.copy()
    for x in TODOS_OS_SINAIS:
        s[f"pct_{x}"] = np.nan
    s["escore"] = np.nan
    s["n_sinais_calculaveis"] = 0
    s["sinal_do_escore"] = None
    s["avaliada"] = False
    s["em_alerta"] = False
    limiares = []
    for (ano, grupo), idx in (
        s[s.amostra.isin(list(sinais))].groupby(["exercicio", "amostra"], sort=True).groups.items()
    ):
        nomes = sinais[str(grupo)]
        pcts = pd.DataFrame({x: s.loc[idx, x].astype(float).rank(pct=True) for x in nomes}, index=idx)
        escore = pcts.max(axis=1)
        avaliada = escore.notna()
        limite = float(escore[avaliada].quantile(PERCENTIL)) if avaliada.any() else None
        for x in nomes:
            s.loc[idx, f"pct_{x}"] = pcts[x]
        s.loc[idx, "escore"] = escore
        s.loc[idx, "n_sinais_calculaveis"] = pcts.notna().sum(axis=1)
        no_maximo = pcts.eq(escore, axis=0)
        s.loc[idx, "sinal_do_escore"] = [";".join(x for x in nomes if no_maximo.at[i, x]) or None for i in idx]
        s.loc[idx, "avaliada"] = avaliada
        s.loc[idx, "em_alerta"] = avaliada & (escore >= limite) if limite is not None else False
        limiares.append({"exercicio": ano, "grupo": grupo, "sinal": "escore", "n": int(avaliada.sum()),
                         "limite_p90": limite})  # fmt: skip
    s["avaliada"] = s.avaliada.astype(bool)
    s["em_alerta"] = s.em_alerta.astype(bool)
    return s, pd.DataFrame(limiares, columns=["exercicio", "grupo", "sinal", "n", "limite_p90"])


def posicoes_no_ranking(s: pd.DataFrame) -> np.ndarray:
    """Posição de cada linha de `s` no ranking do v2 (0 = topo)."""
    chave = pd.DataFrame({"sem": s.escore.isna().to_numpy(), "e": -s.escore.fillna(0.0).to_numpy(dtype=float),
                          "cd": s.cd_cvm.astype(int).to_numpy(), "ex": s.exercicio.astype(int).to_numpy()})  # fmt: skip
    ordem = chave.sort_values(["sem", "e", "cd", "ex"], kind="stable").index.to_numpy()
    pos = np.empty(len(s), dtype=np.int64)
    pos[ordem] = np.arange(len(s))
    return pos
