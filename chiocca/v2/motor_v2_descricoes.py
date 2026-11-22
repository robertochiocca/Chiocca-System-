"""Descrições sem rótulo para o pré-registro do motor v2 (pedido de 22/11/2026; docs/motor-v2-plano.md, seção 2).

Só exercícios de 2010 a 2023 (o lacre recusa os outros) e só agregados por ano e grupo: nenhum caso, acerto ou alerta
por companhia, e o gabarito não é lido. Entradas, todas fora do git e locais: os sinais do estudo 1
(`resultados/sinais_empresa_ano.csv`, de `python -m chiocca.sinais_amostra`), a base "como era na época"
(`data/base/contas_AAAA.csv.gz`, BPA, BPP, DRE e DFC da versão usada) e os zips da DFP em `data/brutos/cvm` (a DVA e o
índice com as datas de entrega). Saída versionada: `docs/motor_v2_descricoes.json` e os documentos gerados dele.

O que é descrito:
1. A cobertura do DEPI pela DVA (conta fixa 7.04.01, 7.05.01 ou 7.07.01 "Depreciação, Amortização e Exaustão"), só
   onde a DFC não traz a depreciação e a versão usada é a dos dados abertos (as versões do ENET não têm DVA).
2. A cobertura das subcontas de 3.06.02 reconhecíveis como variação cambial ou arrendamento, com o critério proposto
   no plano (metade das empresa-anos não financeiras avaliadas, em cada exercício de 2019 a 2023).
3. A quantidade de números por empresa-ano em BPA, BPP, DRE e DFC (coluna do exercício, valores diferentes de zero).
4. As duas opções de fração do plano (1.3): (i) o decil superior em cada sinal; (ii) os 10% do ano com o maior
   percentil entre os sinais. O desvio de Benford entra numa versão provisória (o desvio médio absoluto do primeiro
   dígito dividido pela média do desvio da mesma faixa de quantidade de números, quintis dentro do ano e do grupo); a
   normalização final fica no pré-registro do v2.
5. Só com metadados: as datas da primeira entrega da DFP de 2023 (recebidas em 2024), por semana.
6. Decisão de Roberto de 22/11/2026: o Benford final usa a normalização do artigo, (desvio - média da faixa) ÷
   desvio-padrão da faixa, dentro do ano, do grupo e da faixa de quantidade de números. Aqui, o topo do Benford e o
   topo da opção (ii) por quintil de quantidade de números, nas duas normalizações.
"""

from __future__ import annotations

import io
import json
import math
import re
import unicodedata
import zipfile
from datetime import date, timedelta
from typing import Any

import numpy as np
import pandas as pd

from chiocca import base
from chiocca.cvm import cd_texto
from chiocca.formato import data, inteiro, pct
from chiocca.sinais import mscore as ms
from chiocca.v2 import lacre

RAIZ = base.RAIZ
SINAIS = RAIZ / "resultados" / "sinais_empresa_ano.csv"
BASE = RAIZ / "data" / "base"
BRUTOS = RAIZ / "data" / "brutos" / "cvm"
SAIDA = RAIZ / "docs" / "motor_v2_descricoes.json"
DOCS = {"pt": RAIZ / "docs" / "motor-v2-descricoes.md", "en": RAIZ / "docs" / "en" / "engine-v2-descriptions.md"}

ANOS = range(2010, 2024)
NF, FIN = "nao_financeira", "financeira"
SINAIS_V2 = {NF: ("mscore_v2", "dpo", "juro", "benford"), FIN: ("peso_nao_recorrente", "benford")}
NOMES = {
    "mscore_v2": ("M-score (DEPI pela DVA quando falta na DFC)", "M-score (DEPI from the DVA when missing in the DFC)"),
    "dpo": ("salto do DPO", "DPO jump"),
    "juro": ("juro implícito (fórmula do v1)", "implied interest (v1 formula)"),
    "benford": ("desvio de Benford ajustado (provisório)", "adjusted Benford deviation (provisional)"),
    "peso_nao_recorrente": ("peso de ganhos não recorrentes", "share of non-recurring gains"),
}
DEMONSTRATIVOS_BENFORD = ("BPA", "BPP", "DRE", "DFC_MI", "DFC_MD")
CONTAS_DVA_DEPRECIACAO = ("7.04.01", "7.05.01", "7.07.01")
CAMBIAL = re.compile(r"cambi")
ARRENDAMENTO = re.compile(r"arrendament|leasing|direito de uso")
CRITERIO_COBERTURA = 0.5
ANOS_CRITERIO = range(2019, 2024)
FAIXAS_BENFORD = 5
PERCENTIL = 0.9
BENFORD = np.log10(1 + 1 / np.arange(1, 10))
COMPONENTES_SEM_DEPI = ("DSRI", "GMI", "AQI", "SGI", "SGAI", "TATA", "LVGI")
# Datas de entrega (metadados da DFP de 2023): o análogo de 2024 das datas da meta do plano (25/01 e 31/01/2027).
DT_REFER_2023 = "2023-12-31"
CORTE_2023 = date(2024, 4, 30)
DATAS_META_2024 = (date(2024, 1, 25), date(2024, 1, 31))


def _sem_acento(s: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFKD", str(s).lower()) if not unicodedata.combining(c))


def primeiro_digito(valores: np.ndarray) -> np.ndarray:
    """Primeiro dígito significativo de |valor| (valores diferentes de zero e finitos)."""
    v = np.abs(np.asarray(valores, dtype=float))
    v = v[np.isfinite(v) & (v > 0)]
    d = np.floor(v / 10 ** np.floor(np.log10(v))).astype(int)
    return np.clip(d, 1, 9)


def desvio_benford(contagens: np.ndarray) -> np.ndarray:
    """Desvio médio absoluto entre as frequências dos dígitos 1 a 9 (linhas) e a lei de Benford."""
    c = np.asarray(contagens, dtype=float)
    n = c.sum(axis=1, keepdims=True)
    with np.errstate(invalid="ignore", divide="ignore"):
        p = c / n
    return np.abs(p - BENFORD).mean(axis=1)


def ajusta_por_faixa(mad: pd.Series, n: pd.Series, faixas: int = FAIXAS_BENFORD) -> pd.Series:
    """Desvio dividido pela média do desvio na mesma faixa de quantidade de números (quintis, dentro do conjunto)."""
    ok = mad.notna() & (n > 0)
    out = pd.Series(np.nan, index=mad.index)
    if ok.sum() < faixas:
        return out
    faixa = pd.qcut(n[ok].rank(method="first"), faixas, labels=False)
    media = mad[ok].groupby(faixa).transform("mean")
    out[ok] = mad[ok] / media
    return out


def faixa_de_quantidade(n: pd.Series, faixas: int = FAIXAS_BENFORD) -> pd.Series:
    """Quintil (0 = menos números) da quantidade de números, dentro do conjunto; empates desfeitos pela ordem."""
    out = pd.Series(np.nan, index=n.index)
    ok = n > 0
    if ok.sum() < faixas:
        return out
    out[ok] = pd.qcut(n[ok].rank(method="first"), faixas, labels=False)
    return out


def padroniza_por_faixa(mad: pd.Series, n: pd.Series, faixas: int = FAIXAS_BENFORD) -> pd.Series:
    """Normalização do artigo: (desvio - média da faixa) ÷ desvio-padrão da faixa (amostral, n - 1), com as faixas de
    quantidade de números do conjunto (quintis); faixa com desvio-padrão zero fica sem valor."""
    ok = mad.notna() & (n > 0)
    out = pd.Series(np.nan, index=mad.index)
    if ok.sum() < faixas:
        return out
    faixa = pd.qcut(n[ok].rank(method="first"), faixas, labels=False)
    grupo = mad[ok].groupby(faixa)
    media, dp = grupo.transform("mean"), grupo.transform("std")
    out[ok] = (mad[ok] - media) / dp.where(dp > 0)
    return out


def depi_pela_dva(dep_t: float, dep_t1: float, imob_t: float, imob_t1: float) -> float:
    """DEPI do v1 (taxa de t-1 ÷ taxa de t, taxa = depreciação ÷ (depreciação + imobilizado)) com a depreciação da DVA."""
    vals = (dep_t, dep_t1, imob_t, imob_t1)
    if any(v is None or (isinstance(v, float) and math.isnan(v)) for v in vals):
        return math.nan
    dep_t, dep_t1 = abs(dep_t), abs(dep_t1)
    if dep_t + imob_t == 0 or dep_t1 + imob_t1 == 0:
        return math.nan
    taxa_t, taxa_t1 = dep_t / (dep_t + imob_t), dep_t1 / (dep_t1 + imob_t1)
    return math.nan if taxa_t == 0 else taxa_t1 / taxa_t


def _decil(valores: pd.Series) -> pd.Series:
    ok = valores.dropna()
    if ok.empty:
        return pd.Series(False, index=valores.index)
    return (valores >= ok.quantile(PERCENTIL)).fillna(False)


def alerta_ii(g: pd.DataFrame, sinais: tuple[str, ...]) -> pd.Series:
    """Opção (ii): o escore é o maior percentil entre os sinais calculáveis; alerta no decil superior do escore."""
    pcts = pd.DataFrame({s: g[s].rank(pct=True) for s in sinais}, index=g.index)
    return _decil(pcts.max(axis=1))


def _por_quintil(g: pd.DataFrame, marca: pd.Series) -> list[int]:
    return [int((marca & (g.quintil == q)).sum()) for q in range(FAIXAS_BENFORD)]


def opcoes(g: pd.DataFrame, sinais: tuple[str, ...]) -> dict[str, Any]:
    """As opções (i) e (ii) da fração num ano e grupo; só contagens."""
    avaliavel = g[list(sinais)].notna().any(axis=1)
    g = g[avaliavel]
    n = len(g)
    alertas = pd.DataFrame({s: _decil(g[s]) for s in sinais}, index=g.index)
    k = alertas.sum(axis=1)
    pares = {f"{a}+{b}": int((alertas[a] & alertas[b]).sum()) for i, a in enumerate(sinais) for b in sinais[i + 1 :]}
    pcts = pd.DataFrame({s: g[s].rank(pct=True) for s in sinais}, index=g.index)
    maximo = pcts.max(axis=1)
    alerta_ii = _decil(maximo)
    no_maximo = {s: int(((pcts[s] == maximo) & alerta_ii).sum()) for s in sinais}
    empates = int(((pcts.eq(maximo, axis=0)).sum(axis=1)[alerta_ii] > 1).sum())
    return {
        "avaliaveis": n,
        "calculaveis": {s: int(g[s].notna().sum()) for s in sinais},
        "i": {"por_sinal": {s: int(alertas[s].sum()) for s in sinais}, "uniao": int((k > 0).sum()),
              "por_numero_de_sinais": {str(j): int((k == j).sum()) for j in range(1, len(sinais) + 1)},
              "pares": pares},
        "ii": {"alertas": int(alerta_ii.sum()), "sinal_no_maximo": no_maximo, "empates_no_maximo": empates},
    }  # fmt: skip


def _soma(blocos: list[dict[str, Any]]) -> dict[str, Any]:
    """Soma, entre os anos, as contagens de opcoes()."""

    def soma(xs: list[Any]) -> Any:
        if isinstance(xs[0], dict):
            return {k: soma([x[k] for x in xs]) for k in xs[0]}
        return int(sum(xs))

    return soma(blocos)


def _contas(ano: int) -> pd.DataFrame:
    lacre.garantir_liberado(ano)
    c = pd.read_csv(BASE / f"contas_{ano}.csv.gz", dtype={"cd_cvm": str, "cd_conta": str, "ds_conta": str})
    return c[c.valor.notna()]


def _por_empresa_ano_da_base(ano: int) -> pd.DataFrame:
    """Da base do ano: dígitos (Benford), subcontas de 3.06.02 e imobilizado de t e t-1, por empresa-ano."""
    c = _contas(ano)
    chave = ["cd_cvm", "dt_refer"]
    ult = c[(c.ordem == "ÚLTIMO") & c.demonstracao.isin(DEMONSTRATIVOS_BENFORD) & (c.valor != 0)]
    v = np.abs(ult.valor.to_numpy(float))
    dig = np.floor(v / 10 ** np.floor(np.log10(v))).clip(1, 9).astype(int)
    contagem = pd.crosstab([ult.cd_cvm, ult.dt_refer], dig).reindex(columns=range(1, 10), fill_value=0)
    out = pd.DataFrame({"n_numeros": contagem.sum(axis=1), "mad": desvio_benford(contagem.to_numpy())},
                       index=contagem.index)  # fmt: skip
    sub = c[(c.demonstracao == "DRE") & (c.ordem == "ÚLTIMO") & c.cd_conta.str.startswith("3.06.02.") & (c.valor != 0)]
    nome = sub.ds_conta.map(_sem_acento)
    flags = pd.DataFrame({"sub_qualquer": True, "sub_cambial": nome.map(lambda s: bool(CAMBIAL.search(s))),
                          "sub_arrendamento": nome.map(lambda s: bool(ARRENDAMENTO.search(s)))}).set_index(
        pd.MultiIndex.from_frame(sub[chave]))  # fmt: skip
    flags = flags.groupby(level=[0, 1]).any()
    imob = c[(c.demonstracao == "BPA") & (c.cd_conta == "1.02.03")].pivot_table(
        index=chave, columns="ordem", values="valor", aggfunc="first"
    )
    imob = imob.rename(columns={"ÚLTIMO": "imob_t", "PENÚLTIMO": "imob_t1"})
    out = out.join(flags, how="outer").join(imob[[c for c in ("imob_t", "imob_t1") if c in imob]], how="outer")
    for col in ("sub_qualquer", "sub_cambial", "sub_arrendamento"):
        out[col] = out[col].astype("boolean").fillna(False).astype(bool)
    return out.reset_index()


def _dva(ano: int) -> pd.DataFrame:
    """Depreciação da DVA (t e t-1) por empresa-ano e tipo, só a última versão (a dos dados abertos)."""
    lacre.garantir_liberado(ano)
    partes = []
    with zipfile.ZipFile(BRUTOS / f"dfp_cia_aberta_{ano}.zip") as z:
        for tipo in ("con", "ind"):
            d = pd.read_csv(io.BytesIO(z.read(f"dfp_cia_aberta_DVA_{tipo}_{ano}.csv")), sep=";", encoding="latin1",
                            dtype=str)  # fmt: skip
            d = d[d.CD_CONTA.isin(CONTAS_DVA_DEPRECIACAO) & d.DS_CONTA.map(_sem_acento).str.contains("deprecia")]
            escala = d.ESCALA_MOEDA.map({"MIL": 1000.0, "UNIDADE": 1.0})
            partes.append(pd.DataFrame({"cd_cvm": cd_texto(d.CD_CVM), "dt_refer": d.DT_REFER, "tipo": tipo,
                                        "ordem": d.ORDEM_EXERC, "cd_conta": d.CD_CONTA,
                                        "dep": d.VL_CONTA.astype(float) * escala}))  # fmt: skip
    t = pd.concat(partes).sort_values("cd_conta").drop_duplicates(["cd_cvm", "dt_refer", "tipo", "ordem"])
    p = t.pivot_table(index=["cd_cvm", "dt_refer", "tipo"], columns="ordem", values="dep", aggfunc="first")
    return p.rename(columns={"ÚLTIMO": "dep_t", "PENÚLTIMO": "dep_t1"}).reset_index()


def _quantis(x: pd.Series) -> dict[str, float]:
    x = x.dropna()
    return {k: float(x.quantile(q)) for k, q in (("p5", 0.05), ("p25", 0.25), ("p50", 0.5), ("p75", 0.75),
                                                  ("p95", 0.95))} | {"min": float(x.min()), "max": float(x.max())}  # fmt: skip


def _entregas(sinais: pd.DataFrame) -> dict[str, Any]:
    """Primeira entrega da DFP de 2023 (DT_REFER 31/12/2023) por companhia, por semana; só metadados do índice."""
    with zipfile.ZipFile(BRUTOS / "dfp_cia_aberta_2023.zip") as z:
        idx = pd.read_csv(io.BytesIO(z.read("dfp_cia_aberta_2023.csv")), sep=";", encoding="latin1", dtype=str)
    idx = idx[idx.DT_REFER == DT_REFER_2023]
    primeira = (pd.to_datetime(idx.DT_RECEB).dt.date.groupby(cd_texto(idx.CD_CVM)).min()).rename("primeira")
    ate_corte = primeira[primeira <= CORTE_2023]
    inicio = date(2024, 1, 1)
    semanas = []
    d = inicio
    while d <= CORTE_2023:
        fim = min(d + timedelta(days=6), CORTE_2023)
        semanas.append({"inicio": d.isoformat(), "fim": fim.isoformat(),
                        "entregas": int(((ate_corte >= d) & (ate_corte <= fim)).sum())})  # fmt: skip
        d += timedelta(days=7)
    ref = sinais[
        (sinais.exercicio == 2022) & (sinais.amostra == NF) & sinais.avaliada & (sinais.dt_refer == "2022-12-31")
    ]
    anal = primeira.reindex(ref.cd_cvm.unique()).dropna()
    anal = anal[anal <= CORTE_2023]
    return {
        "companhias": int(len(primeira)), "antes_de_2024": int((primeira < inicio).sum()),
        "ate_o_corte": int(len(ate_corte)), "depois_do_corte": int((primeira > CORTE_2023).sum()),
        "semanas": semanas,
        "depois_de": {x.isoformat(): int((ate_corte > x).sum()) for x in DATAS_META_2024},
        "analogo_2022": {"empresa_anos": int(len(anal)),
                         "depois_de": {x.isoformat(): int((anal > x).sum()) for x in DATAS_META_2024}},
    }  # fmt: skip


def calcula() -> dict[str, Any]:
    s = pd.read_csv(SINAIS, dtype={"cd_cvm": str})
    s = lacre.so_liberados(s)
    assert set(s.exercicio) <= set(ANOS)
    s = s[s.amostra.isin([NF, FIN])].copy()
    linhas = []
    for ano in ANOS:
        b = _por_empresa_ano_da_base(ano)
        b["exercicio"] = ano
        dva = _dva(ano)
        linhas.append((b, dva))
    b = pd.concat([x for x, _ in linhas])
    dva = pd.concat([y for _, y in linhas])
    s = s.merge(b, on=["exercicio", "cd_cvm", "dt_refer"], how="left")
    s = s.merge(dva, on=["cd_cvm", "dt_refer", "tipo"], how="left")
    s["n_numeros"] = s.n_numeros.fillna(0).astype(int)
    for col in ("sub_qualquer", "sub_cambial", "sub_arrendamento"):
        s[col] = s[col].astype("boolean").fillna(False).astype(bool)

    # 1. DEPI pela DVA
    nf = s.amostra == NF
    falta = nf & s.DEPI.isna()
    aberta = s.fonte == "dados_abertos"
    tem_dva = s.dep_t.notna() & s.dep_t1.notna()
    s["depi_dva"] = [depi_pela_dva(*r) if f else math.nan for f, r in
                     zip(falta & aberta & tem_dva, s[["dep_t", "dep_t1", "imob_t", "imob_t1"]].itertuples(index=False))]  # fmt: skip
    outros = s[list(COMPONENTES_SEM_DEPI)].notna().all(axis=1)
    novo_m = falta & s.depi_dva.notna() & outros
    s["mscore_v2"] = s.mscore
    soma = sum(ms.COEFICIENTES[c] * s[c] for c in COMPONENTES_SEM_DEPI)
    s.loc[novo_m, "mscore_v2"] = ms.INTERCEPTO + soma[novo_m] + ms.COEFICIENTES["DEPI"] * s.loc[novo_m, "depi_dva"]
    motivo = s.DEPI_motivo.fillna("").str.split(":").str[0]
    depi = {
        "empresa_anos_nf": int(nf.sum()), "mscore_v1": int((nf & s.mscore.notna()).sum()),
        "depi_falta": int(falta.sum()),
        "depi_falta_por_motivo": {m: int((falta & (motivo == m)).sum()) for m in sorted(motivo[falta].unique())},
        "depi_falta_enet": int((falta & ~aberta).sum()),
        "depi_falta_com_dva": int((falta & aberta & tem_dva).sum()),
        "depi_pela_dva": int((falta & s.depi_dva.notna()).sum()),
        "mscore_novo": int(novo_m.sum()), "mscore_v2": int((nf & s.mscore_v2.notna()).sum()),
        "por_ano": {str(a): {"empresa_anos": int((nf & (s.exercicio == a)).sum()),
                             "mscore_v1": int((nf & (s.exercicio == a) & s.mscore.notna()).sum()),
                             "mscore_v2": int((nf & (s.exercicio == a) & s.mscore_v2.notna()).sum())} for a in ANOS},
    }  # fmt: skip

    # 2. Subcontas de 3.06.02, nas não financeiras avaliadas pelo v1
    av = nf & s.avaliada.astype(bool)
    sub_por_ano = {}
    for a in ANOS:
        g = s[av & (s.exercicio == a)]
        sub_por_ano[str(a)] = {"avaliadas": len(g), "qualquer": int(g.sub_qualquer.sum()),
                               "cambial": int(g.sub_cambial.sum()), "arrendamento": int(g.sub_arrendamento.sum()),
                               "cambial_ou_arrendamento": int((g.sub_cambial | g.sub_arrendamento).sum())}  # fmt: skip
    sub_por_fonte = {}
    for f in ("dados_abertos", "enet"):
        g = s[av & (s.fonte == f)]
        sub_por_fonte[f] = {"avaliadas": len(g), "qualquer": int(g.sub_qualquer.sum()),
                            "cambial_ou_arrendamento": int((g.sub_cambial | g.sub_arrendamento).sum())}  # fmt: skip
    atende = {str(a): sub_por_ano[str(a)]["cambial_ou_arrendamento"] >= CRITERIO_COBERTURA * sub_por_ano[str(a)]["avaliadas"]
              for a in ANOS_CRITERIO}  # fmt: skip
    subcontas = {"por_ano": sub_por_ano, "por_fonte": sub_por_fonte, "criterio": CRITERIO_COBERTURA,
                 "anos_criterio": [ANOS_CRITERIO[0], ANOS_CRITERIO[-1]], "atende_por_ano": atende,
                 "atende": all(atende.values())}  # fmt: skip

    # 3. Quantidade de números por empresa-ano (BPA, BPP, DRE e DFC)
    tem = s.n_numeros > 0
    quantidade = {
        "grupos": {g: _quantis(s.loc[(s.amostra == g) & tem, "n_numeros"]) | {"empresa_anos": int(((s.amostra == g) & tem).sum())}
                   for g in (NF, FIN)},
        "fontes": {f: _quantis(s.loc[(s.fonte == f) & tem, "n_numeros"]) | {"empresa_anos": int(((s.fonte == f) & tem).sum())}
                   for f in ("dados_abertos", "enet")},
        "mediana_por_ano": {str(a): float(s.loc[(s.exercicio == a) & tem, "n_numeros"].median()) for a in ANOS},
        "sem_numeros": int((~tem).sum()),
    }  # fmt: skip

    # 4. Opções da fração, por ano e grupo
    s["benford"] = np.nan
    s["benford_z"] = np.nan
    s["quintil"] = np.nan
    for (a, g), idx in s[tem].groupby(["exercicio", "amostra"]).groups.items():
        s.loc[idx, "benford"] = ajusta_por_faixa(s.loc[idx, "mad"], s.loc[idx, "n_numeros"])
        s.loc[idx, "benford_z"] = padroniza_por_faixa(s.loc[idx, "mad"], s.loc[idx, "n_numeros"])
        s.loc[idx, "quintil"] = faixa_de_quantidade(s.loc[idx, "n_numeros"])
    fracao: dict[str, Any] = {}
    for g, sinais in SINAIS_V2.items():
        por_ano = {str(a): opcoes(s[(s.amostra == g) & (s.exercicio == a)], sinais) for a in ANOS}
        v1 = {}
        for a in ANOS:
            ga = s[(s.amostra == g) & (s.exercicio == a)]
            v1[str(a)] = {
                "avaliadas": int(ga.avaliada.astype(bool).sum()),
                "em_alerta": int(ga.em_alerta.astype(bool).sum()),
            }
        so_v2 = int(((s.amostra == g) & ~s.avaliada.astype(bool) & s[list(sinais)].notna().any(axis=1)).sum())
        gg = s[s.amostra == g]
        repetidas = int(len(gg) - gg[["exercicio", "cd_cvm"]].drop_duplicates().shape[0])
        fracao[g] = {"sinais": list(sinais), "por_ano": por_ano, "total": _soma(list(por_ano.values())), "v1": v1,
                     "avaliaveis_so_pelo_v2": so_v2,
                     "linhas_alem_de_uma_por_companhia_e_ano": repetidas}  # fmt: skip

    # 6. Topo do Benford e da opção (ii) por quintil de quantidade de números, nas duas normalizações
    quintis: dict[str, Any] = {}
    for g, sinais in SINAIS_V2.items():
        gg = s[s.amostra == g]
        bloco: dict[str, Any] = {"empresa_anos": _por_quintil(gg, pd.Series(True, index=gg.index))}
        for nome, col in (("razao", "benford"), ("padronizado", "benford_z")):
            com_col = tuple(col if x == "benford" else x for x in sinais)
            topo_b = pd.Series(False, index=gg.index)
            topo_ii = pd.Series(False, index=gg.index)
            for a in ANOS:
                ga = gg[gg.exercicio == a]
                topo_b.loc[ga.index] = _decil(ga[col])
                topo_ii.loc[ga.index] = alerta_ii(ga, com_col)
            bloco[nome] = {"topo_benford": _por_quintil(gg, topo_b), "topo_ii": _por_quintil(gg, topo_ii)}
        sem_benford = tuple(x for x in sinais if x != "benford")
        topo_sem = pd.Series(False, index=gg.index)
        for a in ANOS:
            ga = gg[gg.exercicio == a]
            topo_sem.loc[ga.index] = alerta_ii(ga, sem_benford)
        bloco["sem_benford"] = {"topo_ii": _por_quintil(gg, topo_sem)}
        z = _soma([opcoes(gg[gg.exercicio == a].assign(benford=gg.loc[gg.exercicio == a, "benford_z"]), sinais)
                   for a in ANOS])  # fmt: skip
        bloco["ii_padronizado"] = {
            "avaliaveis": z["avaliaveis"],
            "calculaveis_benford": z["calculaveis"]["benford"],
        } | z["ii"]
        quintis[g] = bloco

    return {
        "o_que_e": "descrições sem rótulo para o pré-registro do motor v2 (docs/motor-v2-plano.md, seção 2); só "
        "exercícios de 2010 a 2023, só agregados por ano e grupo, sem o gabarito",
        "gerado_por": "python -m chiocca.v2.motor_v2_descricoes",
        "anos": [ANOS[0], ANOS[-1]],
        "depi_dva": depi,
        "subcontas_3_06_02": subcontas,
        "quantidade_de_numeros": quantidade,
        "fracao": fracao,
        "entregas_dfp_2023": _entregas(s),
        "benford_quintis": quintis,
    }


# --- Documento gerado (PT e EN) ---

T: dict[str, dict[str, Any]] = {
    "pt": {
        "titulo": "# Motor v2: descrições sem rótulo",
        "intro": "Gerado por `python -m chiocca.v2.motor_v2_descricoes` a partir de [`docs/motor_v2_descricoes.json`]({json}), para o pré-registro do motor v2 ([plano]({plano}), seção 2). Só exercícios de {a0} a {a1} e só agregados por ano e grupo: nenhum caso, acerto ou alerta por companhia, e o gabarito não é lido. Nada de 2024 em diante foi lido, além dos metadados do índice da DFP de 2023.",
        "h1": "## 1. DEPI pela DVA",
        "depi": "Das {nf} empresa-anos não financeiras, o M-score do v1 existe em {m1}. O DEPI falta em {falta}: {motivos}. Dessas, {enet} têm a versão da época vindo do ENET, sem DVA. Nas demais, {com_dva} têm a linha de depreciação da DVA em t e t-1, e o DEPI pela DVA fica calculável em {depi}. Com ele, o M-score passa a existir em mais {novo} empresa-anos, de {m1} para {m2} ({pm1} para {pm2} das não financeiras).",
        "motivo": {"conta_ausente": "{n} sem linha de depreciação na DFC", "divisao_por_zero": "{n} por divisão por zero", "plano_de_contas": "{n} pelo plano de contas"},
        "cab_m": "| Exercício | Empresa-anos | M-score no v1 | M-score com o DEPI pela DVA |\n| --- | --- | --- | --- |",
        "h2": "## 2. Subcontas de 3.06.02 (despesa financeira)",
        "sub": "Nas não financeiras avaliadas pelo v1, com as subcontas de 3.06.02 diferentes de zero no exercício, reconhecidas pelo nome: variação cambial (\"cambi\") e arrendamento (\"arrendament\", \"leasing\" ou \"direito de uso\").",
        "cab_s": "| Exercício | Avaliadas | Com alguma subconta | Cambial | Arrendamento | Cambial ou arrendamento |\n| --- | --- | --- | --- | --- | --- |",
        "fonte_s": "Por origem da versão: dados abertos, {ac} de {an} com alguma subconta e {bc} com cambial ou arrendamento; ENET, {ec} de {en} com alguma subconta e {fc} com cambial ou arrendamento.",
        "criterio": "**Critério proposto no plano** (a fechar no pré-registro): a mudança 1.1 (a) entra se, em cada exercício de {c0} a {c1}, pelo menos {pc} das não financeiras avaliadas tiverem uma subconta de variação cambial ou de arrendamento. Resultado desta descrição: **{res}** ({anos}).",
        "atende": "atende", "nao_atende": "não atende",
        "h3": "## 3. Quantidade de números por empresa-ano",
        "qtd": "Números diferentes de zero na coluna do exercício de BPA, BPP, DRE e DFC da versão usada, os quatro demonstrativos que existem nos dados abertos e no ENET. Empresa-anos sem nenhum número na base: {sem}.",
        "cab_q": "| Conjunto | Empresa-anos | Mínimo | P5 | P25 | Mediana | P75 | P95 | Máximo |\n| --- | --- | --- | --- | --- | --- | --- | --- | --- |",
        "conj": {"nao_financeira": "não financeiras", "financeira": "financeiras", "dados_abertos": "dados abertos", "enet": "ENET"},
        "med_ano": "Mediana por exercício: {lista}.",
        "h4": "## 4. Opções da fração (plano, 1.3)",
        "fr": "O desvio de Benford entra numa versão provisória: o desvio médio absoluto do primeiro dígito, dividido pela média do desvio na mesma faixa de quantidade de números (quintis dentro do ano e do grupo). O juro implícito usa a fórmula do v1. A taxa é sobre as empresa-anos com pelo menos um sinal do v2 calculável. (i): o decil superior em cada sinal; (ii): os 10% do ano com o maior percentil entre os sinais calculáveis. As contagens são por empresa-ano (linha da base); o estudo 1 conta companhias distintas por exercício, e a diferença vem de companhias com duas DFP no mesmo exercício: {rep_nf} linhas a mais nas não financeiras e {rep_fin} nas financeiras.",
        "grupo": {"nao_financeira": "### Não financeiras", "financeira": "### Financeiras"},
        "cab_f": "| Exercício | Avaliáveis pelo v2 | Taxa do v1 | Opção (i): união | Opção (ii) |\n| --- | --- | --- | --- | --- |",
        "total": "Total",
        "sobre": "Opção (i), de {a0} a {a1}: {uniao} de {n} empresa-anos em alerta ({pu}). Por número de sinais no topo: {ks}. Pares de sinais no topo ao mesmo tempo: {pares}. Alertas de cada sinal: {porsinal}.",
        "ii": "Opção (ii): {al} de {n} empresa-anos em alerta ({pa}). Sinal que define o maior percentil entre as alertadas (com empate, conta para cada um): {nomax}; alertas com empate no maior percentil: {emp}.",
        "so_v2": "Empresa-anos que só o v2 consegue avaliar (nenhum sinal do v1 calculável): {n}.",
        "h5": "## 5. Datas de entrega da DFP de 2023 (só metadados)",
        "ent": "Primeira entrega (o menor DT_RECEB do índice) da DFP de 2023 com data de referência 31/12/2023, por companhia: {tot} companhias, {ate} até o corte de {corte} e {dep} depois. Das entregues até o corte, {d25} ({p25}) foram depois de {m25} e {d31} ({p31}) depois de {m31}, o análogo de 2024 das datas da meta (25/01/2027 e 31/01/2027).",
        "anal": "Estimativa para o rótulo prospectivo: das {n} não financeiras avaliadas em 2022 (referência em 31/12/2022) com a DFP de 2023 entregue até o corte, {k31} ({p31}) tiveram a primeira entrega depois de {m31}, e {k25} ({p25}) depois de {m25}. Com o mesmo padrão em 2027 e o lacre em 31/01/2027, essa seria a fração prospectiva das empresa-anos de 2025; as datas da semana não coincidem entre os anos.",
        "cab_e": "| Semana | Primeiras entregas | Acumulado até o corte |\n| --- | --- | --- |",
        "h6": "## 6. Benford: o topo por quintil de quantidade de números",
        "q6": "Decisão de Roberto (22/11/2026): na versão final, o desvio de Benford é padronizado como no artigo, dentro do ano, do grupo e da faixa de quantidade de números: (desvio − média da faixa) ÷ desvio-padrão da faixa (amostral, n − 1). Abaixo, as empresa-anos no topo do Benford (o decil superior do ano, dentro do grupo) e no topo da opção (ii), por quintil de quantidade de números dentro do ano e do grupo (1 = menos números), nas duas normalizações: a divisão só pela média da faixa, usada nas seções 4 e 5, e a padronizada. Sem concentração, cada quintil teria perto de 20% de cada topo. A última coluna é a opção (ii) sem o Benford, só com os outros sinais do grupo, para separar o efeito dele do dos outros sinais.",
        "cab_q6": "| Quintil | Empresa-anos | Topo do Benford, só a média | Topo do Benford, padronizado | Topo da opção (ii), só a média | Topo da opção (ii), padronizado | Topo da opção (ii), sem o Benford |\n| --- | --- | --- | --- | --- | --- | --- |",
        "ii6": "Opção (ii) com o Benford padronizado: {al} de {n} empresa-anos em alerta ({pa}), com o Benford calculável em {cb}. Sinal que define o maior percentil entre as alertadas (com empate, conta para cada um): {nomax}; alertas com empate no maior percentil: {emp}.",
    },
    "en": {
        "titulo": "# Engine v2: label-free descriptions",
        "intro": "Generated by `python -m chiocca.v2.motor_v2_descricoes` from [`docs/motor_v2_descricoes.json`]({json}), for the engine v2 pre-registration ([plan]({plano}), section 2). Fiscal years {a0} to {a1} only and aggregates by year and group only: no case, detection or alert by company, and the ground truth is not read. Nothing from 2024 onward was read, beyond the metadata of the 2023 DFP index.",
        "h1": "## 1. DEPI from the DVA",
        "depi": "Of the {nf} non-financial company-years, the v1 M-score exists in {m1}. DEPI is missing in {falta}: {motivos}. Of those, {enet} have their point-in-time version from ENET, with no DVA. Among the others, {com_dva} have the DVA depreciation line at t and t-1, and DEPI from the DVA can be computed in {depi}. With it, the M-score exists in {novo} more company-years, from {m1} to {m2} ({pm1} to {pm2} of non-financial companies).",
        "motivo": {"conta_ausente": "{n} with no depreciation line in the DFC", "divisao_por_zero": "{n} from division by zero", "plano_de_contas": "{n} from the chart of accounts"},
        "cab_m": "| Fiscal year | Company-years | M-score in v1 | M-score with DEPI from the DVA |\n| --- | --- | --- | --- |",
        "h2": "## 2. 3.06.02 sub-accounts (finance costs)",
        "sub": "In non-financial companies evaluated by v1, with the 3.06.02 sub-accounts different from zero in the fiscal year, recognized by name: exchange-rate variation (\"cambi\") and leases (\"arrendament\", \"leasing\" or \"direito de uso\").",
        "cab_s": "| Fiscal year | Evaluated | With any sub-account | Exchange rate | Leases | Exchange rate or leases |\n| --- | --- | --- | --- | --- | --- |",
        "fonte_s": "By version source: open data, {ac} of {an} with any sub-account and {bc} with exchange rate or leases; ENET, {ec} of {en} with any sub-account and {fc} with exchange rate or leases.",
        "criterio": "**Criterion proposed in the plan** (to be closed in the pre-registration): change 1.1 (a) enters if, in each fiscal year from {c0} to {c1}, at least {pc} of the evaluated non-financial companies have an exchange-rate or lease sub-account. Result of this description: **{res}** ({anos}).",
        "atende": "met", "nao_atende": "not met",
        "h3": "## 3. Number of figures per company-year",
        "qtd": "Non-zero figures in the fiscal-year column of BPA, BPP, DRE and DFC of the version used, the four statements that exist in the open data and in ENET. Company-years with no figure in the base: {sem}.",
        "cab_q": "| Set | Company-years | Minimum | P5 | P25 | Median | P75 | P95 | Maximum |\n| --- | --- | --- | --- | --- | --- | --- | --- | --- |",
        "conj": {"nao_financeira": "non-financial", "financeira": "financial", "dados_abertos": "open data", "enet": "ENET"},
        "med_ano": "Median by fiscal year: {lista}.",
        "h4": "## 4. Fraction options (plan, 1.3)",
        "fr": "The Benford deviation enters in a provisional version: the mean absolute deviation of the first digit, divided by the mean deviation in the same bin of the number of figures (quintiles within the year and group). Implied interest uses the v1 formula. The rate is over company-years with at least one computable v2 signal. (i): the top decile in each signal; (ii): the 10% of the year with the highest percentile among the computable signals. Counts are by company-year (row of the base); study 1 counts distinct companies by fiscal year, and the difference comes from companies with two DFPs in the same fiscal year: {rep_nf} more rows among non-financial companies and {rep_fin} among financial ones.",
        "grupo": {"nao_financeira": "### Non-financial companies", "financeira": "### Financial companies"},
        "cab_f": "| Fiscal year | Evaluable by v2 | v1 rate | Option (i): union | Option (ii) |\n| --- | --- | --- | --- | --- |",
        "total": "Total",
        "sobre": "Option (i), {a0} to {a1}: {uniao} of {n} company-years in alert ({pu}). By number of signals at the top: {ks}. Pairs of signals at the top at the same time: {pares}. Alerts of each signal: {porsinal}.",
        "ii": "Option (ii): {al} of {n} company-years in alert ({pa}). Signal that sets the highest percentile among the flagged ones (with a tie, it counts for each): {nomax}; alerts with a tie at the highest percentile: {emp}.",
        "so_v2": "Company-years that only v2 can evaluate (no computable v1 signal): {n}.",
        "h5": "## 5. Filing dates of the 2023 DFP (metadata only)",
        "ent": "First filing (the smallest DT_RECEB in the index) of the 2023 DFP with reference date 2023-12-31, by company: {tot} companies, {ate} by the {corte} cut-off and {dep} after it. Of those filed by the cut-off, {d25} ({p25}) were after {m25} and {d31} ({p31}) after {m31}, the 2024 analogue of the target dates (2027-01-25 and 2027-01-31).",
        "anal": "Estimate for the prospective label: of the {n} non-financial companies evaluated in 2022 (reference date 2022-12-31) with the 2023 DFP filed by the cut-off, {k31} ({p31}) had their first filing after {m31}, and {k25} ({p25}) after {m25}. With the same pattern in 2027 and the seal on 2027-01-31, this would be the prospective share of the 2025 company-years; the weekdays do not match across years.",
        "cab_e": "| Week | First filings | Cumulative up to the cut-off |\n| --- | --- | --- |",
        "h6": "## 6. Benford: the top by quintile of the number of figures",
        "q6": "Roberto's decision (2026-11-22): in the final version, the Benford deviation is standardized as in the article, within the year, the group and the bin of the number of figures: (deviation − bin mean) ÷ bin standard deviation (sample, n − 1). Below, the company-years at the top of Benford (the year's top decile, within the group) and at the top of option (ii), by quintile of the number of figures within the year and group (1 = fewest figures), in both normalizations: division by the bin mean only, used in sections 4 and 5, and the standardized one. With no concentration, each quintile would hold about 20% of each top. The last column is option (ii) without Benford, with only the group's other signals, to separate its effect from that of the other signals.",
        "cab_q6": "| Quintile | Company-years | Benford top, mean only | Benford top, standardized | Option (ii) top, mean only | Option (ii) top, standardized | Option (ii) top, without Benford |\n| --- | --- | --- | --- | --- | --- | --- |",
        "ii6": "Option (ii) with the standardized Benford: {al} of {n} company-years in alert ({pa}), with Benford computable in {cb}. Signal that sets the highest percentile among the flagged ones (with a tie, it counts for each): {nomax}; alerts with a tie at the highest percentile: {emp}.",
    },
}  # fmt: skip


def render(d: dict[str, Any], lang: str) -> str:
    t = T[lang]
    i = lambda v: inteiro(v, lang)  # noqa: E731
    p = lambda a, b: pct(a / b, lang) if b else "—"  # noqa: E731
    e = " e " if lang == "pt" else " and "
    de = "de" if lang == "pt" else "of"
    json_link, plano = ("motor_v2_descricoes.json", "motor-v2-plano.md") if lang == "pt" else (
        "../motor_v2_descricoes.json", "engine-v2-plan.md")  # fmt: skip
    a0, a1 = d["anos"]
    out = [t["titulo"], "", t["intro"].format(json=json_link, plano=plano, a0=a0, a1=a1), ""]

    m = d["depi_dva"]
    motivos = "; ".join(
        t["motivo"][k].format(n=i(v)) for k, v in m["depi_falta_por_motivo"].items() if k in t["motivo"]
    )
    out += [t["h1"], "", t["depi"].format(nf=i(m["empresa_anos_nf"]), m1=i(m["mscore_v1"]), falta=i(m["depi_falta"]),
                                         motivos=motivos, enet=i(m["depi_falta_enet"]),
                                         com_dva=i(m["depi_falta_com_dva"]), depi=i(m["depi_pela_dva"]),
                                         novo=i(m["mscore_novo"]), m2=i(m["mscore_v2"]),
                                         pm1=p(m["mscore_v1"], m["empresa_anos_nf"]),
                                         pm2=p(m["mscore_v2"], m["empresa_anos_nf"])), "", t["cab_m"]]  # fmt: skip
    for a, x in m["por_ano"].items():
        out.append(f"| {a} | {i(x['empresa_anos'])} | {i(x['mscore_v1'])} ({p(x['mscore_v1'], x['empresa_anos'])}) | "
                   f"{i(x['mscore_v2'])} ({p(x['mscore_v2'], x['empresa_anos'])}) |")  # fmt: skip

    s = d["subcontas_3_06_02"]
    out += ["", t["h2"], "", t["sub"], "", t["cab_s"]]
    for a, x in s["por_ano"].items():
        n = x["avaliadas"]
        out.append(f"| {a} | {i(n)} | {i(x['qualquer'])} ({p(x['qualquer'], n)}) | {i(x['cambial'])} ({p(x['cambial'], n)}) | "
                   f"{i(x['arrendamento'])} ({p(x['arrendamento'], n)}) | {i(x['cambial_ou_arrendamento'])} "
                   f"({p(x['cambial_ou_arrendamento'], n)}) |")  # fmt: skip
    f_ab, f_en = s["por_fonte"]["dados_abertos"], s["por_fonte"]["enet"]
    out += ["", t["fonte_s"].format(ac=i(f_ab["qualquer"]), an=i(f_ab["avaliadas"]), bc=i(f_ab["cambial_ou_arrendamento"]),
                                    ec=i(f_en["qualquer"]), en=i(f_en["avaliadas"]), fc=i(f_en["cambial_ou_arrendamento"]))]  # fmt: skip
    anos = "; ".join(f"{a}: {t['atende'] if ok else t['nao_atende']}" for a, ok in s["atende_por_ano"].items())
    out += ["", t["criterio"].format(c0=s["anos_criterio"][0], c1=s["anos_criterio"][1], pc=pct(s["criterio"], lang, 0),
                                     res=t["atende"] if s["atende"] else t["nao_atende"], anos=anos)]  # fmt: skip

    q = d["quantidade_de_numeros"]
    out += ["", t["h3"], "", t["qtd"].format(sem=i(q["sem_numeros"])), "", t["cab_q"]]
    for bloco in ("grupos", "fontes"):
        for k, x in q[bloco].items():
            out.append(f"| {t['conj'][k]} | {i(x['empresa_anos'])} | {i(round(x['min']))} | {i(round(x['p5']))} | "
                       f"{i(round(x['p25']))} | {i(round(x['p50']))} | {i(round(x['p75']))} | {i(round(x['p95']))} | "
                       f"{i(round(x['max']))} |")  # fmt: skip
    lista = "; ".join(f"{a}: {i(round(v))}" for a, v in q["mediana_por_ano"].items())
    out += ["", t["med_ano"].format(lista=lista)]

    rep = {g: d["fracao"][g]["linhas_alem_de_uma_por_companhia_e_ano"] for g in (NF, FIN)}
    out += ["", t["h4"], "", t["fr"].format(rep_nf=i(rep[NF]), rep_fin=i(rep[FIN]))]
    for g, fr in d["fracao"].items():
        out += ["", t["grupo"][g], "", t["cab_f"]]
        for a, x in fr["por_ano"].items():
            v1 = fr["v1"][a]
            n = x["avaliaveis"]
            out.append(f"| {a} | {i(n)} | {p(v1['em_alerta'], v1['avaliadas'])} | {p(x['i']['uniao'], n)} | "
                       f"{p(x['ii']['alertas'], n)} |")  # fmt: skip
        tot = fr["total"]
        n = tot["avaliaveis"]
        v1_al = sum(v["em_alerta"] for v in fr["v1"].values())
        v1_av = sum(v["avaliadas"] for v in fr["v1"].values())
        out.append(
            f"| {t['total']} | {i(n)} | {p(v1_al, v1_av)} | {p(tot['i']['uniao'], n)} | {p(tot['ii']['alertas'], n)} |"
        )
        nome = lambda k: NOMES[k][0 if lang == "pt" else 1]  # noqa: E731
        ks = "; ".join(f"{k}: {i(v)}" for k, v in tot["i"]["por_numero_de_sinais"].items())
        pares = "; ".join(
            f"{nome(k.split('+')[0])}{e}{nome(k.split('+')[1])}, {i(v)}" for k, v in tot["i"]["pares"].items()
        )
        porsinal = "; ".join(
            f"{nome(k)}, {i(v)} {de} {i(tot['calculaveis'][k])}" for k, v in tot["i"]["por_sinal"].items()
        )
        nomax = "; ".join(f"{nome(k)}, {i(v)}" for k, v in tot["ii"]["sinal_no_maximo"].items())
        out += ["", t["sobre"].format(a0=a0, a1=a1, uniao=i(tot["i"]["uniao"]), n=i(n), pu=p(tot["i"]["uniao"], n), ks=ks,
                                      pares=pares, porsinal=porsinal),
                "", t["ii"].format(al=i(tot["ii"]["alertas"]), n=i(n), pa=p(tot["ii"]["alertas"], n), nomax=nomax,
                                   emp=i(tot["ii"]["empates_no_maximo"])),
                "", t["so_v2"].format(n=i(fr["avaliaveis_so_pelo_v2"]))]  # fmt: skip

    en = d["entregas_dfp_2023"]
    m25, m31 = DATAS_META_2024
    ate = en["ate_o_corte"]
    d25, d31 = en["depois_de"][m25.isoformat()], en["depois_de"][m31.isoformat()]
    an = en["analogo_2022"]
    k25, k31 = an["depois_de"][m25.isoformat()], an["depois_de"][m31.isoformat()]
    out += ["", t["h5"], "", t["ent"].format(tot=i(en["companhias"]), ate=i(ate), corte=data(CORTE_2023.isoformat(), lang),
                                             dep=i(en["depois_do_corte"]), d25=i(d25), p25=p(d25, ate), d31=i(d31),
                                             p31=p(d31, ate), m25=data(m25.isoformat(), lang), m31=data(m31.isoformat(), lang)),
            "", t["anal"].format(n=i(an["empresa_anos"]), k31=i(k31), p31=p(k31, an["empresa_anos"]), k25=i(k25),
                                 p25=p(k25, an["empresa_anos"]), m31=data(m31.isoformat(), lang),
                                 m25=data(m25.isoformat(), lang)),
            "", t["cab_e"]]  # fmt: skip
    acum = 0
    for w in en["semanas"]:
        acum += w["entregas"]
        out.append(f"| {data(w['inicio'], lang)} a {data(w['fim'], lang)} | {i(w['entregas'])} | {p(acum, ate)} |"
                   if lang == "pt" else
                   f"| {data(w['inicio'], lang)} to {data(w['fim'], lang)} | {i(w['entregas'])} | {p(acum, ate)} |")  # fmt: skip
    qd = d["benford_quintis"]
    out += ["", t["h6"], "", t["q6"]]
    for g, b in qd.items():
        out += ["", t["grupo"][g], "", t["cab_q6"]]
        colunas = (b["razao"]["topo_benford"], b["padronizado"]["topo_benford"], b["razao"]["topo_ii"],
                   b["padronizado"]["topo_ii"], b["sem_benford"]["topo_ii"])  # fmt: skip
        for q in range(FAIXAS_BENFORD):
            celulas = " | ".join(f"{i(c[q])} ({p(c[q], sum(c))})" for c in colunas)
            out.append(f"| {q + 1} | {i(b['empresa_anos'][q])} | {celulas} |")
        z = b["ii_padronizado"]
        nomes_z = NOMES | {"benford": ("desvio de Benford padronizado", "standardized Benford deviation")}
        nome_z = lambda k: nomes_z[k][0 if lang == "pt" else 1]  # noqa: E731
        nomax = "; ".join(f"{nome_z(k)}, {i(v)}" for k, v in z["sinal_no_maximo"].items())
        out += ["", t["ii6"].format(al=i(z["alertas"]), n=i(z["avaliaveis"]), pa=p(z["alertas"], z["avaliaveis"]),
                                    cb=i(z["calculaveis_benford"]), nomax=nomax, emp=i(z["empates_no_maximo"]))]  # fmt: skip
    return "\n".join(out) + "\n"


def main() -> None:
    d = calcula()
    SAIDA.write_text(json.dumps(d, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    for lang, caminho in DOCS.items():
        caminho.write_text(render(d, lang), encoding="utf-8")
    print(f"gravados {SAIDA.relative_to(RAIZ)} e {', '.join(str(c.relative_to(RAIZ)) for c in DOCS.values())}")


if __name__ == "__main__":
    main()
