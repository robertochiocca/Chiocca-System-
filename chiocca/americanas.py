"""Americanas (código CVM 20990), exercício de 2021: duas leituras e uma comparação descritiva.

1. **Duas leituras (PROMPT.md, Fase 3).** Original: a DFP de 2021, versão da época (ÚLTIMO para t, PENÚLTIMO para
   t−1). Reapresentada: o comparativo (PENÚLTIMO) da DFP de 2022, única versão, entregue em 16/11/2023, depois do
   corte de 30/04/2023; é uma leitura posterior, não "como era na época". A DFP de 2022 não traz 2020, e a
   reapresentação ajustou os efeitos anteriores a 2021 no saldo de abertura, sem separar por ano (emenda 1);
   por isso t−1 é o mesmo nas duas leituras (PENÚLTIMO da DFP de 2021).
2. **Comparação com a base da Lojas Americanas (explicação depois do resultado, não teste).** Em 2021 a B2W
   (código 20990) recebeu, por cisão parcial da Lojas Americanas (código 8087), todos os ativos operacionais e
   passivos relacionados, com data-base de 31/12/2020 (ata da AGE de 10/06/2021). O comparativo de 2020 na DFP
   de 2021 é só da B2W. A comparação troca t−1 pela DFP consolidada de 2020 da Lojas Americanas, que já
   consolidava a B2W. Os perímetros não são idênticos; serve só para ver de onde vêm SGI e DSRI.

Uso: python -m chiocca.americanas   (precisa de data/brutos; grava resultados/americanas.json, fora do git)
"""

from __future__ import annotations

import json
from datetime import date
from typing import Any

import pandas as pd

from chiocca import base, cdi, variaveis
from chiocca.cvm import Fontes
from chiocca.sinais import dpo, juro_implicito, lucro_sem_caixa, mscore
from chiocca.sinais.resultado import Resultado
from chiocca.sinais_amostra import CORTE_M, SAIDA, SPREAD_PP

CD, ANO, LASA = "20990", 2021, "8087"
CORTE_ABERTO = date(2100, 12, 31)
CONTAS_MOSTRADAS = [
    "receita_liquida",
    "custo_vendas",
    "resultado_bruto",
    "contas_a_receber",
    "estoques",
    "ativo_circulante",
    "imobilizado",
    "ativo_total",
    "fornecedores",
    "passivo_circulante",
    "emprestimos_cp",
    "emprestimos_lp",
    "despesas_vendas",
    "despesas_gerais_adm",
    "despesas_financeiras",
    "lucro_operacoes_continuadas",
    "lucro_liquido",
    "caixa_operacional",
    "depreciacao",
]


def _r(r: Resultado) -> dict[str, Any]:
    return {"valor": r.valor, "motivo": r.motivo}


def sinais(contas: pd.DataFrame, dt_refer: str, limite_dpo: float | None) -> dict[str, Any]:
    t, t1 = variaveis.le_ordem(contas, variaveis.ULTIMO), variaveis.le_ordem(contas, variaveis.PENULTIMO)
    m = mscore.calcula(t.valores, t1.valores)
    j = juro_implicito.juro(t.valores, t1.valores)
    taxa_cdi = cdi.medio(dt_refer)
    spread = None if j.valor is None or taxa_cdi is None else juro_implicito.spread_pp(j.valor, taxa_cdi)
    d = dpo.variacao(t.valores, t1.valores)
    return {
        "componentes": {k: _r(v) for k, v in m.componentes.items()},
        "m": _r(m.m),
        "alerta_m": m.m.valor is not None and m.m.valor > CORTE_M,
        "dpo": _r(d),
        "alerta_dpo": d.valor is not None and limite_dpo is not None and d.valor >= limite_dpo,
        "juro_spread": spread,
        "alerta_juro": spread is not None and spread > SPREAD_PP,
        "lucro_sem_caixa": _r(lucro_sem_caixa.accruals(t.valores, t1.valores)),
        "contas_t": {k: t.valores.get(k) for k in CONTAS_MOSTRADAS},
        "contas_t1": {k: t1.valores.get(k) for k in CONTAS_MOSTRADAS},
    }


def _ordem(contas: pd.DataFrame, de: str, para: str) -> pd.DataFrame:
    c = contas[contas.ordem == de].copy()
    c["ordem"] = para
    return c


def calcula(fontes: Fontes, limite_dpo: float | None) -> dict[str, Any]:
    orig = base.como_era(fontes, CD, ANO)
    reap = base.como_era(fontes, CD, ANO + 1, corte=CORTE_ABERTO)
    lasa = base.como_era(fontes, LASA, ANO - 1)
    if base.OK not in (orig.status,) or reap.status != base.OK or lasa.status != base.OK:
        raise RuntimeError(f"leituras indisponíveis: {orig.status}, {reap.status}, {lasa.status}")
    assert orig.contas is not None and reap.contas is not None and lasa.contas is not None
    t1_orig = _ordem(orig.contas, variaveis.PENULTIMO, variaveis.PENULTIMO)
    reapresentada = pd.concat([_ordem(reap.contas, variaveis.PENULTIMO, variaveis.ULTIMO), t1_orig])
    base_lasa = pd.concat(
        [
            _ordem(orig.contas, variaveis.ULTIMO, variaveis.ULTIMO),
            _ordem(lasa.contas, variaveis.ULTIMO, variaveis.PENULTIMO),
        ]
    )
    dt = str(orig.dt_refer)
    return {
        "original": {"versao": orig.versao, "dt_receb": str(orig.dt_receb), "tipo": orig.tipo}
        | sinais(orig.contas, dt, limite_dpo),
        "reapresentada": {"versao": reap.versao, "dt_receb": str(reap.dt_receb), "tipo": reap.tipo}
        | sinais(reapresentada, dt, limite_dpo),
        "base_lasa": {"versao": lasa.versao, "dt_receb": str(lasa.dt_receb), "tipo": lasa.tipo}
        | sinais(base_lasa, dt, limite_dpo),
        "limite_dpo": limite_dpo,
        "cdi_medio": cdi.medio(dt),
    }


def main() -> None:
    lim = pd.read_csv(SAIDA / "limiares.csv")
    sel = lim[(lim.exercicio == ANO) & (lim.grupo == "nao_financeira") & (lim.sinal == "dpo")]
    limite = None if sel.empty else float(sel.limite_p90.iloc[0])
    r = calcula(Fontes(base.BRUTOS, base.CACHE_ENET), limite)
    (SAIDA / "americanas.json").write_text(json.dumps(r, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    for k in ("original", "reapresentada", "base_lasa"):
        x = r[k]
        print(
            k,
            x["versao"],
            x["dt_receb"],
            x["tipo"],
            "M",
            x["m"]["valor"],
            "dpo",
            x["dpo"]["valor"],
            "juro",
            x["juro_spread"],
        )
        print("   ", {c: None if v["valor"] is None else round(v["valor"], 3) for c, v in x["componentes"].items()})


if __name__ == "__main__":
    main()
