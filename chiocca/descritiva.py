"""Análise descritiva feita depois de ver os resultados da Fase 2: explicação depois do resultado, não teste.

Nada aqui muda regra, corte ou caso (emenda 11). Os números só descrevem de onde vieram os alertas e as falhas.
- juro_por_ano: quanto da taxa de alerta das não financeiras vem só do juro implícito, por exercício, antes e
  depois de 2019 (ano de adoção do CPC 06 (R2), que trouxe os juros de arrendamento para a despesa financeira);
- depi: quantos casos e empresa-anos perderam o M-score por falta do DEPI.
"""

from __future__ import annotations

from typing import Any

import pandas as pd

from chiocca import metricas as mt
from chiocca.sinais_amostra import AMOSTRA_NF, ANOS

ANTES, DEPOIS = range(2010, 2019), range(2019, 2024)


def _por_empresa_ano(s: pd.DataFrame) -> pd.DataFrame:
    nf = s[s.amostra == AMOSTRA_NF]
    return nf.groupby(["exercicio", "cd_cvm"]).agg(
        avaliada=("avaliada", "any"),
        em_alerta=("em_alerta", "any"),
        m=("alerta_mscore", "any"),
        dpo=("alerta_dpo", "any"),
        juro=("alerta_juro", "any"),
    ).reset_index()  # fmt: skip


def juro_por_ano(s: pd.DataFrame) -> dict[str, Any]:
    e = _por_empresa_ano(s)
    e["so_juro"] = e.juro & ~e.m & ~e.dpo
    e["sem_juro"] = e.m | e.dpo
    por_ano = {}
    for ano in ANOS:
        a = e[e.exercicio == ano]
        por_ano[str(ano)] = {k: int(a[k].sum()) for k in ("avaliada", "em_alerta", "so_juro", "sem_juro", "juro")}
    out: dict[str, Any] = {"por_ano": por_ano}
    for nome, anos in (("antes", ANTES), ("depois", DEPOIS)):
        out[nome] = {k: sum(por_ano[str(a)][k] for a in anos) for k in ("avaliada", "em_alerta", "so_juro", "sem_juro")}
    return out


def _faltando(motivo: Any) -> list[str]:
    if pd.isna(motivo) or not str(motivo).startswith("componente_nao_calculavel:"):
        return []
    return str(motivo).split(":", 1)[1].split(",")


def depi(s: pd.DataFrame, s_neutro: pd.DataFrame, gab: pd.DataFrame) -> dict[str, Any]:
    nf = s[s.amostra == AMOSTRA_NF]
    falta = nf.mscore_motivo.map(_faltando)
    com_depi = falta.map(lambda f: "DEPI" in f)
    so_depi = falta.map(lambda f: f == ["DEPI"])
    amostra = {
        "m_nao_calculavel": int(nf.mscore.isna().sum()),
        "com_depi": int(com_depi.sum()),
        "so_depi": int(so_depi.sum()),
        "so_depi_dfc_md": int((so_depi & (nf.metodo_dfc == "DFC_MD")).sum()),
    }
    casos = []
    for c in gab.itertuples(index=False):
        parte = None if pd.isna(c.parte_secundaria) else str(c.parte_secundaria)
        if (c.acertavel_principal != "sim" and not parte) or pd.isna(c.cd_cvm) or pd.isna(c.data_publica):
            continue
        anos = mt.anos_do_periodo(c.periodo_afetado_inicio, c.periodo_afetado_fim)
        linhas = mt.linhas_do_caso(s, str(c.cd_cvm), anos, str(c.data_publica))
        eleg = linhas[linhas.elegivel & (linhas.amostra == AMOSTRA_NF)]
        if eleg.empty:
            continue
        sem_m = eleg[eleg.mscore.isna()]
        perdeu = [int(r.exercicio) for r in sem_m.itertuples() if "DEPI" in _faltando(r.mscore_motivo)]
        if not perdeu or len(sem_m) != len(eleg):
            continue  # o caso tem M em algum exercício elegível, ou perdeu por outro componente
        neutro = s_neutro.loc[eleg.index]
        casos.append(
            {
                "caso_id": str(c.caso_id),
                "principal": c.acertavel_principal == "sim",
                "parte_secundaria": parte,
                "anos": perdeu,
                "so_depi": all(_faltando(r.mscore_motivo) == ["DEPI"] for r in sem_m.itertuples()),
                "dfc_md": bool((eleg.metodo_dfc == "DFC_MD").any()),
                "m_neutro": [None if pd.isna(v) else float(v) for v in neutro.mscore_neutro],
                "alerta_m_neutro": bool(neutro.alerta_mscore_neutro.any()),
                "acertado": bool(eleg.em_alerta.any()),
            }
        )
    return {"amostra": amostra, "casos": casos}
