"""Métricas da avaliação a partir de resultados/sinais_empresa_ano.csv (pré-registro, seções 5 a 8, e emendas).

- **Acerto (seção 5):** um caso é acertado se a empresa entrou em alerta em pelo menos um exercício do período
  afetado, usando só dados públicos antes da `data_publica`: entram os exercícios de 2010 a 2023 em que a
  empresa-ano está na amostra do seu grupo e a versão da época foi entregue (DT_RECEB) antes da data.
- **Taxa de alerta (seção 6):** por exercício e grupo, empresas em alerta ÷ empresas avaliadas (com pelo menos um
  sinal de alerta calculável); o tamanho da amostra vem ao lado.
- **Alarmes por acerto (emenda 10):** (empresas em alerta − casos acertados) ÷ casos acertados, com empresas
  distintas que tiveram pelo menos um alerta no período de teste (2017 a 2023, seção 8), por grupo. Empresas dos
  casos em observação ficam fora (emenda 8).
- **Regra boba (seção 7 e emenda 7):** as mesmas contas, com o alerta da regra boba no lugar dos sinais.
- **Secundárias:** emenda 1 (Americanas: qualquer exercício até 2021 com DFP antes de 11/01/2023); emenda 3
  (última DFP antes da data pública, mesmo fora do período afetado); emenda 9 (partes 2a e 2b).
- **Casos em observação (emenda 8):** se houve alerta em exercício com DFP entregue antes da data do caso.
"""

from __future__ import annotations

from collections import Counter
from datetime import date
from typing import Any

import pandas as pd

from chiocca.sinais import mscore
from chiocca.sinais_amostra import AMOSTRA_FIN, AMOSTRA_NF, ANOS

TESTE = range(2017, 2024)  # pré-registro, seção 8
AMOSTRAS = (AMOSTRA_NF, AMOSTRA_FIN)
ALERTA_SINAIS = "em_alerta"
ALERTA_BOBA = "alerta_regra_boba"
DATA_EMENDA_1 = "2023-01-11"
ANO_MAX_EMENDA_1 = 2021


def _sim(serie: pd.Series) -> pd.Series:
    """Coluna de alerta lida do CSV (True/False/vazio) como booleano, com vazio = sem alerta."""
    return serie.astype("string").str.lower().eq("true").fillna(False).astype(bool)


def prepara(s: pd.DataFrame) -> pd.DataFrame:
    s = s.copy()
    for col in [c for c in s.columns if c.startswith("alerta_")] + ["em_alerta", "avaliada"]:
        s[col] = _sim(s[col])
    s["boba_avaliada"] = s.alavancagem.notna() & s.amostra.isin(AMOSTRAS)
    return s


def anos_do_periodo(inicio: Any, fim: Any) -> list[int]:
    if pd.isna(inicio) or pd.isna(fim):
        return []
    return [a for a in range(int(inicio), int(fim) + 1) if a in ANOS]


def _antes(dt_receb: Any, data_publica: str) -> bool:
    return not pd.isna(dt_receb) and str(dt_receb)[:10] < data_publica


def linhas_do_caso(s: pd.DataFrame, cd_cvm: str, anos: list[int], data_publica: str) -> pd.DataFrame:
    linhas = s[(s.cd_cvm == cd_cvm) & s.exercicio.isin(anos)].copy()
    linhas["antes_da_data"] = [_antes(d, data_publica) for d in linhas.dt_receb]
    linhas["elegivel"] = linhas.amostra.isin(AMOSTRAS) & linhas.antes_da_data
    return linhas.sort_values(["exercicio", "dt_refer"])


def avalia_caso(s: pd.DataFrame, cd_cvm: str, anos: list[int], data_publica: str) -> dict[str, Any]:
    """Resultado de um caso pela regra da seção 5, com os sinais e com a regra boba."""
    linhas = linhas_do_caso(s, cd_cvm, anos, data_publica)
    eleg = linhas[linhas.elegivel]
    return {
        "anos_periodo": anos,
        "anos_elegiveis": sorted(set(int(a) for a in eleg.exercicio)),
        "anos_avaliados": sorted(set(int(a) for a in eleg[eleg.avaliada].exercicio)),
        "anos_em_alerta": sorted(set(int(a) for a in eleg[eleg[ALERTA_SINAIS]].exercicio)),
        "anos_alerta_boba": sorted(set(int(a) for a in eleg[eleg[ALERTA_BOBA]].exercicio)),
        "acertado": bool(eleg[ALERTA_SINAIS].any()),
        "acertado_boba": bool(eleg[ALERTA_BOBA].any()),
        "grupos": sorted(set(str(g) for g in eleg.amostra)),
        "corte_depois_da_data": bool((eleg.data_corte.astype(str) >= data_publica).any()),
        "anos_fora": fora_da_amostra(linhas, anos),
    }


def fora_da_amostra(linhas: pd.DataFrame, anos: list[int]) -> list[list[Any]]:
    """Exercícios do período que não entram na conta, com o motivo."""
    out: list[list[Any]] = []
    for a in anos:
        r = linhas[linhas.exercicio == a]
        if r.empty:
            out.append([a, "sem_dfp"])
        elif not r.elegivel.any():
            x = r.iloc[0]
            out.append([a, x.amostra if x.amostra not in AMOSTRAS else "depois_da_data"])
    return out


def _valor(x: Any) -> float | None:
    return None if pd.isna(x) else float(x)


def detalhe_anos(s: pd.DataFrame, cd_cvm: str, anos: list[int], data_publica: str) -> list[dict[str, Any]]:
    """Uma linha por exercício do período afetado: situação, sinais e alertas (casos do gabarito são públicos)."""
    out = []
    for r in linhas_do_caso(s, cd_cvm, anos, data_publica).itertuples(index=False):
        out.append(
            {
                "exercicio": int(r.exercicio),
                "dt_receb": None if pd.isna(r.dt_receb) else str(r.dt_receb)[:10],
                "amostra": r.amostra,
                "antes_da_data": bool(r.antes_da_data),
                "mscore": _valor(r.mscore),
                "mscore_motivo": None if pd.isna(r.mscore_motivo) else str(r.mscore_motivo),
                "alerta_mscore": bool(r.alerta_mscore),
                "dpo": _valor(r.dpo),
                "alerta_dpo": bool(r.alerta_dpo),
                "juro": _valor(r.juro),
                "alerta_juro": bool(r.alerta_juro),
                "peso_nao_recorrente": _valor(getattr(r, "peso_nao_recorrente", None)),
                "alerta_peso_nao_recorrente": bool(r.alerta_peso_nao_recorrente),
                "em_alerta": bool(r.em_alerta),
                "alerta_boba": bool(r.alerta_regra_boba),
                "componentes": {c: _valor(getattr(r, c, None)) for c in mscore.COEFICIENTES},
            }
        )
    return out


def linha_ano(s: pd.DataFrame, cd_cvm: str, exercicio: int) -> dict[str, Any] | None:
    """Situação e sinal das financeiras de uma empresa-ano (previsão do IRB, pré-registro 4.2)."""
    r = s[(s.cd_cvm == cd_cvm) & (s.exercicio == exercicio)]
    if r.empty:
        return None
    x = r.iloc[0]
    return {
        "exercicio": exercicio,
        "amostra": str(x.amostra),
        "dt_receb": None if pd.isna(x.dt_receb) else str(x.dt_receb)[:10],
        "peso_nao_recorrente": _valor(x.peso_nao_recorrente),
        "peso_motivo": None if pd.isna(x.peso_nao_recorrente_motivo) else str(x.peso_nao_recorrente_motivo),
        "alerta": bool(x.alerta_peso_nao_recorrente),
    }


def taxa_por_ano(s: pd.DataFrame, grupo: str, alerta: str, avaliada: str) -> dict[str, dict[str, int]]:
    out = {}
    g = s[s.amostra == grupo]
    for ano in ANOS:
        a = g[g.exercicio == ano]
        out[str(ano)] = {
            "amostra": int(a.cd_cvm.nunique()),
            "avaliadas": int(a[a[avaliada]].cd_cvm.nunique()),
            "em_alerta": int(a[a[alerta]].cd_cvm.nunique()),
        }
    return out


def alertas_por_sinal(
    s: pd.DataFrame, grupo: str, colunas: list[tuple[str, str]]
) -> dict[str, dict[str, dict[str, int]]]:
    """Por sinal e exercício: empresa-anos com o sinal calculável e com alerta."""
    g = s[s.amostra == grupo]
    out: dict[str, dict[str, dict[str, int]]] = {}
    for col, valor in colunas:
        out[col] = {}
        for ano in ANOS:
            a = g[g.exercicio == ano]
            out[col][str(ano)] = {"calculaveis": int(a[valor].notna().sum()), "alertas": int(a[col].sum())}
    return out


def alarmes(
    s: pd.DataFrame, grupo: str, alerta: str, avaliada: str, acertados: int, fora: set[str], anos: range = TESTE
) -> dict:
    """(empresas em alerta − casos acertados) ÷ casos acertados, com empresas distintas com alerta em `anos`."""
    t = s[(s.amostra == grupo) & s.exercicio.isin(anos) & ~s.cd_cvm.isin(fora)]
    em_alerta = int(t[t[alerta]].cd_cvm.nunique())
    return {
        "empresas_avaliadas": int(t[t[avaliada]].cd_cvm.nunique()),
        "empresas_em_alerta": em_alerta,
        "casos_acertados": acertados,
        "alarmes_por_acerto": None if acertados == 0 else (em_alerta - acertados) / acertados,
    }


def acerto_por_coluna(s: pd.DataFrame, cd_cvm: str, anos: list[int], data_publica: str, alerta: str) -> dict:
    """Acerto de um caso (seção 5) com uma coluna de alerta qualquer, no período inteiro e no período de teste."""
    linhas = linhas_do_caso(s, cd_cvm, anos, data_publica)
    eleg = linhas[linhas.elegivel]
    em_alerta = sorted(set(int(a) for a in eleg[eleg[alerta]].exercicio))
    return {
        "anos_em_alerta": em_alerta,
        "acertado": bool(em_alerta),
        "acertado_teste": any(a in TESTE for a in em_alerta),
        "grupos": sorted(set(str(g) for g in eleg.amostra)),
        "elegivel": not eleg.empty,
    }


def avaliacao(s: pd.DataFrame, gab: pd.DataFrame, fora: set[str], alerta: str, avaliada: str) -> dict[str, Any]:
    """Pacote de métricas de uma regra de alerta: acerto, alarmes por acerto (emendas 10 e 11), 2a e 2b, taxa.

    Emenda 11: (a) período de teste, 2017–2023, com os casos acertados por alerta dentro dele; (b) período inteiro,
    2010–2023, com todos os casos acertados. A versão da emenda 10 (empresas do teste, acertos de todo o período)
    fica junto, identificada como inconsistente.
    """
    casos: dict[str, dict[str, Any]] = {}
    for c in gab.itertuples(index=False):
        if pd.isna(c.cd_cvm) or pd.isna(c.data_publica):
            continue
        acertavel = c.acertavel_principal == "sim"
        parte = None if pd.isna(c.parte_secundaria) else str(c.parte_secundaria)
        if not acertavel and not parte:
            continue
        anos = anos_do_periodo(c.periodo_afetado_inicio, c.periodo_afetado_fim)
        r = acerto_por_coluna(s, str(c.cd_cvm), anos, str(c.data_publica), alerta)
        casos[str(c.caso_id)] = r | {"acertavel": acertavel, "parte_secundaria": parte}
    principais = [r for r in casos.values() if r["acertavel"]]
    out: dict[str, Any] = {
        "acertados": sum(r["acertado"] for r in principais),
        "acertados_teste": sum(r["acertado_teste"] for r in principais),
        "acertaveis": len(principais),
        "casos": {k: {"acertado": r["acertado"], "acertado_teste": r["acertado_teste"],
                      "anos_em_alerta": r["anos_em_alerta"]} for k, r in casos.items()},
        "secundaria": {},
        "alarmes": {},
        "taxa": {},
    }  # fmt: skip
    for parte in ("2a", "2b"):
        cs = [r for r in casos.values() if r["parte_secundaria"] == parte]
        out["secundaria"][parte] = {"casos": len(cs), "efetivos": sum(r["elegivel"] for r in cs),
                                    "acertados": sum(r["acertado"] for r in cs)}  # fmt: skip
    for grupo, chave in ((AMOSTRA_NF, "nf"), (AMOSTRA_FIN, "fin")):
        a_tudo = sum(1 for r in principais if r["acertado"] and grupo in r["grupos"])
        a_teste = sum(1 for r in principais if r["acertado_teste"] and grupo in r["grupos"])
        out["alarmes"][chave] = {
            "emenda_10": alarmes(s, grupo, alerta, avaliada, a_tudo, fora, TESTE),
            "teste": alarmes(s, grupo, alerta, avaliada, a_teste, fora, TESTE),
            "inteiro": alarmes(s, grupo, alerta, avaliada, a_tudo, fora, ANOS),
        }
        g = s[s.amostra == grupo]
        em = sum(int(g[(g.exercicio == a) & g[alerta]].cd_cvm.nunique()) for a in ANOS)
        av = sum(int(g[(g.exercicio == a) & g[avaliada]].cd_cvm.nunique()) for a in ANOS)
        out["taxa"][chave] = {"em_alerta": em, "avaliadas": av}
    return out


def nao_calculaveis(s: pd.DataFrame) -> dict[str, dict[str, Any]]:
    """Por sinal: empresa-anos da amostra do grupo, quantas calculáveis e a contagem por motivo."""
    nf, fin = s[s.amostra == AMOSTRA_NF], s[s.amostra == AMOSTRA_FIN]
    out: dict[str, dict[str, Any]] = {}
    for nome, g in [(n, nf) for n in ("mscore", *mscore.COEFICIENTES, "dpo", "juro", "lucro_sem_caixa")] + [
        ("peso_nao_recorrente", fin),
        ("alavancagem_nf", nf),
        ("alavancagem_fin", fin),
    ]:
        col = "alavancagem" if nome.startswith("alavancagem") else nome
        motivos = g[f"{col}_motivo"].dropna().astype(str)
        if nome == "mscore":  # um M não calculável conta em cada componente que faltou
            contagem: Counter[str] = Counter()
            for m in motivos:
                partes = m.split(":", 1)
                if partes[0] == "componente_nao_calculavel":
                    contagem.update("componente:" + c for c in partes[1].split(",") if not c.startswith("plano"))
                    contagem.update(c for c in partes[1].split(",") if c.startswith("plano"))
                else:
                    contagem[m] += 1
        else:
            contagem = Counter(motivos)
        out[nome] = {
            "empresa_anos": int(len(g)),
            "calculaveis": int(g[col].notna().sum()),
            "nao_calculaveis": int(g[col].isna().sum()),
            "motivos": dict(sorted(contagem.items(), key=lambda kv: (-kv[1], kv[0]))),
        }
    return out


def emenda_3(s: pd.DataFrame, cd_cvm: str, data_publica: str) -> dict[str, Any]:
    """Alerta na última DFP publicada antes da data pública, entre as empresa-anos da amostra."""
    linhas = s[(s.cd_cvm == cd_cvm) & s.amostra.isin(AMOSTRAS)]
    linhas = linhas[[_antes(d, data_publica) for d in linhas.dt_receb]]
    if linhas.empty:
        return {"exercicio": None, "em_alerta": None, "alerta_boba": None}
    ultimo = int(linhas.exercicio.max())
    u = linhas[linhas.exercicio == ultimo]
    return {"exercicio": ultimo, "em_alerta": bool(u[ALERTA_SINAIS].any()), "alerta_boba": bool(u[ALERTA_BOBA].any())}


def observacao(s: pd.DataFrame, cd_cvm: str, anos: list[int], data_publica: str) -> dict[str, Any]:
    linhas = linhas_do_caso(s, cd_cvm, anos or list(ANOS), data_publica)
    antes = linhas[linhas.antes_da_data]
    eleg = antes[antes.elegivel]
    return {
        "anos_com_dfp_antes": sorted(set(int(a) for a in antes.exercicio)),
        "anos_na_amostra": sorted(set(int(a) for a in eleg.exercicio)),
        "anos_sem_receita": sorted(set(int(a) for a in antes[antes.amostra == "fora_sem_receita"].exercicio)),
        "anos_em_alerta": sorted(set(int(a) for a in eleg[eleg[ALERTA_SINAIS]].exercicio)),
        "grupos": sorted(set(str(g) for g in eleg.amostra)),
    }


def hoje() -> str:
    return date.today().isoformat()
