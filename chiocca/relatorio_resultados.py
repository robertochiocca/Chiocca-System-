"""Resultados da avaliação (PROMPT.md, Fases 2 e 3), gerados nos dois idiomas a partir dos mesmos números.

Números: calculados uma vez de resultados/sinais_empresa_ano.csv (fora do git) por chiocca.metricas e gravados em
docs/resultados_numeros.json (versionado). Só entram números agregados, os casos do gabarito (públicos) e a
tabela dos casos em observação (emenda 8). Nenhuma lista de empresas em alerta fora desses casos.
Textos: docs/resultados.md (PT) e docs/en/results.md (EN), montados do JSON. Um teste confere que os dois
documentos são iguais ao que este módulo gera e que têm os mesmos números.

Uso: python -m chiocca.relatorio_resultados
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd

from chiocca import metricas as mt
from chiocca.base import RAIZ
from chiocca.sinais_amostra import AMOSTRA_FIN, AMOSTRA_NF, CORTE_M, PERCENTIL, SPREAD_PP
from chiocca.textos_resultados import render

SINAIS = RAIZ / "resultados" / "sinais_empresa_ano.csv"
EXECUCAO = RAIZ / "resultados" / "execucao.json"
LIMIARES = RAIZ / "resultados" / "limiares.csv"
GABARITO = RAIZ / "data" / "gabarito_casos.csv"
OBSERVACAO = RAIZ / "data" / "casos_em_observacao.csv"
NUMEROS = RAIZ / "docs" / "resultados_numeros.json"
DOCS = {"pt": RAIZ / "docs" / "resultados.md", "en": RAIZ / "docs" / "en" / "results.md"}
# Primeira vez que os sinais do período de teste foram calculados (PROMPT.md, Fase 3: registrar data e commit).
ABERTURA_TESTE = {"data": "2026-11-07", "commit": "9e8c758c775972ad033ff8423ace5bc4392894f9"}


def numeros(s: pd.DataFrame, gab: pd.DataFrame, obs: pd.DataFrame, execucao: dict[str, Any]) -> dict[str, Any]:
    s = mt.prepara(s)
    fora = set(obs.cd_cvm.dropna().astype(str))
    n: dict[str, Any] = {
        "execucao": execucao,
        "abertura_teste": ABERTURA_TESTE,
        "regras": {"corte_m": CORTE_M, "spread_pp": SPREAD_PP, "percentil": PERCENTIL},
    }
    situacao = s.amostra.value_counts()
    n["amostra"] = {k: int(situacao.get(k, 0)) for k in (AMOSTRA_NF, AMOSTRA_FIN, "fora_sem_receita",
                                                          "fora_sem_versao_da_epoca")}  # fmt: skip
    nf = s[s.amostra == AMOSTRA_NF]
    n["marcas"] = {
        "depreciacao_combinada": int(nf.marca_depreciacao_combinada.astype(str).eq("True").sum()),
        "cpc06": int(s[s.amostra.isin(mt.AMOSTRAS)].marca_cpc06.astype(str).eq("True").sum()),
        "juros_pagos_6_01": int((nf.juros_pagos_linhas_6_01 > 0).sum()),
        "juros_pagos_6_03": int((nf.juros_pagos_linhas_6_03 > 0).sum()),
        "dfc_md": int((nf.metodo_dfc == "DFC_MD").sum()),
        "sem_penultimo": int(nf.sem_penultimo.astype(str).eq("True").sum()),
        "empresas": int(s[s.amostra.isin(mt.AMOSTRAS)].cd_cvm.nunique()),
    }
    n["taxa"] = {
        "nf": mt.taxa_por_ano(s, AMOSTRA_NF, mt.ALERTA_SINAIS, "avaliada"),
        "fin": mt.taxa_por_ano(s, AMOSTRA_FIN, mt.ALERTA_SINAIS, "avaliada"),
        "nf_boba": mt.taxa_por_ano(s, AMOSTRA_NF, mt.ALERTA_BOBA, "boba_avaliada"),
        "fin_boba": mt.taxa_por_ano(s, AMOSTRA_FIN, mt.ALERTA_BOBA, "boba_avaliada"),
    }
    n["por_sinal"] = {
        "nf": mt.alertas_por_sinal(
            s, AMOSTRA_NF, [("alerta_mscore", "mscore"), ("alerta_dpo", "dpo"), ("alerta_juro", "juro")]
        ),
        "fin": mt.alertas_por_sinal(s, AMOSTRA_FIN, [("alerta_peso_nao_recorrente", "peso_nao_recorrente")]),
    }
    n["nao_calculaveis"] = mt.nao_calculaveis(s)

    casos = []
    for c in gab.itertuples(index=False):
        anos = mt.anos_do_periodo(c.periodo_afetado_inicio, c.periodo_afetado_fim)
        r: dict[str, Any] = {
            "caso_id": c.caso_id,
            "empresa": c.empresa,
            "cd_cvm": None if pd.isna(c.cd_cvm) else str(c.cd_cvm),
            "financeira": c.financeira,
            "inicio": None if pd.isna(c.periodo_afetado_inicio) else int(c.periodo_afetado_inicio),
            "fim": None if pd.isna(c.periodo_afetado_fim) else int(c.periodo_afetado_fim),
            "data_publica": None if pd.isna(c.data_publica) else str(c.data_publica),
            "acertavel": c.acertavel_principal == "sim",
            "parte_secundaria": None if pd.isna(c.parte_secundaria) else str(c.parte_secundaria),
        }
        if r["cd_cvm"] and r["data_publica"]:
            r |= mt.avalia_caso(s, r["cd_cvm"], anos, r["data_publica"])
            if r["acertavel"] or r["parte_secundaria"]:
                r["detalhe"] = mt.detalhe_anos(s, r["cd_cvm"], anos, r["data_publica"])
            if not r["parte_secundaria"]:
                r["emenda_3"] = mt.emenda_3(s, r["cd_cvm"], r["data_publica"])
        casos.append(r)
    n["casos"] = casos
    principais = [c for c in casos if c["acertavel"]]
    acertados = {g: sum(1 for c in principais if c["acertado"] and g in c["grupos"]) for g in (AMOSTRA_NF, AMOSTRA_FIN)}
    acertados_boba = {
        g: sum(1 for c in principais if c["acertado_boba"] and g in c["grupos"]) for g in (AMOSTRA_NF, AMOSTRA_FIN)
    }
    n["acerto"] = {
        "casos_no_gabarito": len(casos),
        "acertaveis": len(principais),
        "acertaveis_efetivos": sum(1 for c in principais if c["anos_elegiveis"]),
        "acertaveis_avaliados": sum(1 for c in principais if c["anos_avaliados"]),
        "acertados": sum(1 for c in principais if c["acertado"]),
        "acertados_boba": sum(1 for c in principais if c["acertado_boba"]),
        "acertados_com_alerta_no_teste": sum(
            1 for c in principais if c["acertado"] and any(a in mt.TESTE for a in c["anos_em_alerta"])
        ),
    }
    n["alarmes"] = {
        "nf": mt.alarmes(s, AMOSTRA_NF, mt.ALERTA_SINAIS, "avaliada", acertados[AMOSTRA_NF], fora),
        "fin": mt.alarmes(s, AMOSTRA_FIN, mt.ALERTA_SINAIS, "avaliada", acertados[AMOSTRA_FIN], fora),
        "nf_boba": mt.alarmes(s, AMOSTRA_NF, mt.ALERTA_BOBA, "boba_avaliada", acertados_boba[AMOSTRA_NF], fora),
        "fin_boba": mt.alarmes(s, AMOSTRA_FIN, mt.ALERTA_BOBA, "boba_avaliada", acertados_boba[AMOSTRA_FIN], fora),
    }
    secundarios = {}
    for parte in ("2a", "2b"):
        cs = [c for c in casos if c["parte_secundaria"] == parte]
        secundarios[parte] = {
            "casos": len(cs),
            "efetivos": sum(1 for c in cs if c.get("anos_elegiveis")),
            "acertados": sum(1 for c in cs if c.get("acertado")),
            "acertados_boba": sum(1 for c in cs if c.get("acertado_boba")),
        }
    n["secundaria"] = secundarios
    ame = gab[gab.caso_id == "americanas"].iloc[0]
    anos_e1 = [a for a in mt.ANOS if a <= mt.ANO_MAX_EMENDA_1]
    n["emenda_1"] = mt.avalia_caso(s, str(ame.cd_cvm), anos_e1, mt.DATA_EMENDA_1)
    e3 = [c for c in casos if "emenda_3" in c]
    n["emenda_3"] = {
        "casos": len(e3),
        "com_dfp": sum(1 for c in e3 if c["emenda_3"]["exercicio"] is not None),
        "em_alerta": sum(1 for c in e3 if c["emenda_3"]["em_alerta"]),
        "alerta_boba": sum(1 for c in e3 if c["emenda_3"]["alerta_boba"]),
    }
    observ = []
    for o in obs.itertuples(index=False):
        anos = mt.anos_do_periodo(o.periodo_afetado_inicio, o.periodo_afetado_fim)
        observ.append(
            {"caso_id": o.caso_id, "empresa": o.empresa, "cd_cvm": str(o.cd_cvm), "data_publica": str(o.data_publica),
             "inicio": None if pd.isna(o.periodo_afetado_inicio) else int(o.periodo_afetado_inicio),
             "fim": None if pd.isna(o.periodo_afetado_fim) else int(o.periodo_afetado_fim)}
            | mt.observacao(s, str(o.cd_cvm), anos, str(o.data_publica))
        )  # fmt: skip
    n["observacao"] = observ
    limiares = s.attrs.get("limiares")
    n["previsoes"] = {
        "irb": [mt.linha_ano(s, "24180", a) for a in (2018, 2019)],
        "limite_fin": limiares,
    }
    return n


def main() -> None:
    s = pd.read_csv(SINAIS, dtype={"cd_cvm": str}, low_memory=False)
    gab = pd.read_csv(GABARITO, dtype={"cd_cvm": str})
    obs = pd.read_csv(OBSERVACAO, dtype={"cd_cvm": str})
    execucao = json.loads(EXECUCAO.read_text(encoding="utf-8")) if EXECUCAO.exists() else {}
    lim = pd.read_csv(LIMIARES)
    lim = lim[(lim.grupo == AMOSTRA_FIN) & (lim.sinal == "peso_nao_recorrente")]
    s.attrs["limiares"] = {str(a): v for a, v in zip(lim.exercicio, lim.limite_p90) if a in (2018, 2019)}
    n = numeros(s, gab, obs, execucao)
    NUMEROS.write_text(json.dumps(n, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    escreve_docs(json.loads(NUMEROS.read_text(encoding="utf-8")))


def escreve_docs(n: dict[str, Any], docs: dict[str, Path] = DOCS) -> None:
    for lang, caminho in docs.items():
        caminho.write_text(render(n, lang), encoding="utf-8")


if __name__ == "__main__":
    main()
