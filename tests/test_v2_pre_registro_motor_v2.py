"""Rascunho do pré-registro do motor v2 e da emenda 5 ao estudo 2 (pedido de 22/11/2026): os números saem do código, das
descrições sem rótulo e das constantes do estudo 2; nada é digitado à mão, e o pré-registro do estudo 2 não muda."""

from __future__ import annotations

import json
from math import sqrt
from pathlib import Path
from statistics import NormalDist

import pytest

from chiocca.formato import data, decimal, inteiro, pct
from chiocca.sinais import mscore as ms
from chiocca.v2 import motor_v2_descricoes as md

RAIZ = Path(__file__).resolve().parents[1]
PRE = {"pt": RAIZ / "docs/pre-registro-motor-v2.md", "en": RAIZ / "docs/en/engine-v2-preregistration.md"}
EMENDA = {"pt": RAIZ / "docs/estudo-2-emenda-5-rascunho.md", "en": RAIZ / "docs/en/study-2-amendment-5-draft.md"}


def _poder(razao: float, n: int = 1200, fracao: float = 0.10, p0: float = 0.047) -> float:
    """Poder aproximado do teste unilateral de 95% da DR, supondo empresa-anos independentes (seção 7, item 2)."""
    n1 = n * fracao
    p1 = razao * p0
    ep = sqrt(p1 * (1 - p1) / n1 + p0 * (1 - p0) / (n - n1))
    return NormalDist().cdf((p1 - p0) / ep - NormalDist().inv_cdf(0.95))


@pytest.mark.parametrize("lang", ["pt", "en"])
def test_formula_e_contas_saem_do_codigo(lang: str) -> None:
    doc = PRE[lang].read_text(encoding="utf-8")
    assert decimal(ms.INTERCEPTO, lang, 2) in doc
    for comp, coef in ms.COEFICIENTES.items():
        assert f"{decimal(abs(coef), lang, 3)} {comp}" in doc, comp
    assert all(conta in doc for conta in md.CONTAS_DVA_DEPRECIACAO)
    assert md.FAIXAS_BENFORD == 5 and "5" in doc and "quantile(0.9)" in doc and md.PERCENTIL == 0.9
    assert "rank(pct=True)" in doc and 'rank(method="first")' in doc


@pytest.mark.parametrize("lang", ["pt", "en"])
def test_numeros_das_descricoes(lang: str) -> None:
    doc = PRE[lang].read_text(encoding="utf-8")
    d = json.loads(md.SAIDA.read_text(encoding="utf-8"))
    i = lambda v: inteiro(v, lang)  # noqa: E731
    m = d["depi_dva"]
    assert f"{i(m['mscore_v1'])}" in doc and f"{i(m['mscore_v2'])}" in doc and i(m["empresa_anos_nf"]) in doc
    sub = d["subcontas_3_06_02"]["por_ano"]
    taxas = [sub[str(a)]["cambial_ou_arrendamento"] / sub[str(a)]["avaliadas"] for a in md.ANOS_CRITERIO]
    assert pct(min(taxas), lang) in doc and pct(max(taxas), lang) in doc
    topo = d["benford_quintis"]["nao_financeira"]["padronizado"]["topo_benford"]
    fatias = [x / sum(topo) for x in topo]
    assert pct(min(fatias), lang) in doc and pct(max(fatias), lang) in doc
    for g in ("nao_financeira", "financeira"):
        z = d["benford_quintis"][g]["ii_padronizado"]
        assert pct(z["alertas"] / z["avaliaveis"], lang) in doc, g
    e = d["entregas_dfp_2023"]
    assert pct(e["depois_de"]["2024-01-31"] / e["ate_o_corte"], lang) in doc


@pytest.mark.parametrize("lang", ["pt", "en"])
def test_previsoes_com_o_poder_recalculado(lang: str) -> None:
    doc = PRE[lang].read_text(encoding="utf-8")
    for razao in (1.5, 2.0, 2.5):
        assert decimal(_poder(razao), lang, 2) in doc, razao
    assert f" {round(1200 * 0.10 * 0.047)} " in doc  # republicações esperadas no alerta sem associação
    assert inteiro(1200, lang) in doc and decimal(4.7, lang, 1) in doc


@pytest.mark.parametrize("lang", ["pt", "en"])
def test_calendario_constantes_e_rotulos(lang: str) -> None:
    from chiocca.v2.estudo2 import secundaria

    pre, emenda = PRE[lang].read_text(encoding="utf-8"), EMENDA[lang].read_text(encoding="utf-8")
    inv = json.loads((RAIZ / "docs/invariante_numeros.json").read_text(encoding="utf-8"))
    assert inteiro(sum(v["empresa_anos_iguais"] for v in inv["exercicios"].values()), lang) in pre
    for d in ("2026-12-20", "2027-01-25", "2027-01-31", "2027-03-31", "2027-04-15", "2027-04-30", "2026-11-19",
              "2029-12-31"):  # fmt: skip
        assert data(d, lang) in pre, d
    assert data(secundaria.DATA_MINIMA.isoformat(), lang) in pre
    assert str(secundaria.SEMENTE) in emenda and inteiro(secundaria.REAMOSTRAGENS, lang) in emenda
    assert "DT_RECEB" in pre and "DT_RECEB" in emenda
    rascunho = ("Ainda não é registro", "Emenda 5 ·", "não foi usada nem registrada") if lang == "pt" else (
        "It is not yet a registration", "Amendment 5 ·", "neither used nor registered")  # fmt: skip
    assert rascunho[0] in pre and rascunho[0] in emenda
    assert rascunho[1] in emenda and rascunho[2] in emenda


def test_pre_registro_do_estudo_2_nao_tem_a_emenda_5() -> None:
    pre = (RAIZ / "docs/pre-registro-estudo-2.md").read_text(encoding="utf-8")
    assert "Emenda 5" not in pre and "motor v2" not in pre.lower()


@pytest.mark.parametrize("lang", ["pt", "en"])
def test_revisoes_antes_do_registro(lang: str) -> None:
    """Pedido de 22/11/2026: Benford com 20 números, escore escolhido pela descrição, características conhecidas, o
    produto no v1 e o carimbo do registro."""
    doc = PRE[lang].read_text(encoding="utf-8")
    d = json.loads(md.SAIDA.read_text(encoding="utf-8"))
    i = lambda v: inteiro(v, lang)  # noqa: E731
    q = d["quantidade_de_numeros"]["grupos"]
    assert f" {md.MINIMO_NUMEROS_BENFORD} " in doc and f" {i(round(min(g['min'] for g in q.values())))})" in doc
    ek = d["escore_por_numero_de_sinais"]
    assert ek["escolhida"] == "maximo"
    for v in ("maximo", "potencia"):
        assert decimal(100 * ek["maior_distancia"][v], lang, 1) in doc, v
    mx = ek["grupos"]["nao_financeira"]["maximo"]
    for v in mx["por_k"].values():
        assert pct(v["alertas"] / v["empresa_anos"], lang) in doc
    topo = mx["topo_por_quintil"]
    assert pct(topo[0] / sum(topo), lang) in doc and pct(topo[-1] / sum(topo), lang) in doc
    sem = d["benford_quintis"]["nao_financeira"]["sem_benford"]["topo_ii"]
    assert pct(sem[0] / sum(sem), lang) in doc
    produto = "O produto continua com o v1" if lang == "pt" else "The product stays on v1"
    assert produto in doc and "OpenTimestamps" in doc and "docs/carimbos/" in doc
