"""Rascunho do pré-registro do motor v2 e da emenda 5 ao estudo 2 (pedido de 22/11/2026): os números saem do código, das
descrições sem rótulo e das constantes do estudo 2; nada é digitado à mão, e o pré-registro do estudo 2 não muda."""

from __future__ import annotations

import hashlib
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
ESTUDO_2 = {"pt": RAIZ / "docs/pre-registro-estudo-2.md", "en": RAIZ / "docs/en/study-2-preregistration.md"}
CABECALHO_EMENDA_5 = {"pt": "\n### Emenda 5 · 22/11/2026 ·", "en": "\n### Amendment 5 · 2026-11-22 ·"}
# SHA-256 do pré-registro do estudo 2 antes da emenda 5 (o arquivo inteiro no commit 31866e6): a emenda só acrescenta.
ESTUDO_2_ANTES_DA_EMENDA_5 = {
    "pt": "4d3e206d27496b0e4393f21a8ba82b04f831bf5a7538955ad75af91eade1cc43",
    "en": "875fdb06ab5a6d561f0ebfd9897888a3fdf3e79166e0c8e3e5f57661ef19895e",
}


def _emenda_5(lang: str) -> str:
    """O texto registrado da emenda 5, na seção 13 do pré-registro do estudo 2."""
    return CABECALHO_EMENDA_5[lang] + ESTUDO_2[lang].read_text(encoding="utf-8").split(CABECALHO_EMENDA_5[lang], 1)[1]


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

    pre, emenda = PRE[lang].read_text(encoding="utf-8"), _emenda_5(lang)
    inv = json.loads((RAIZ / "docs/invariante_numeros.json").read_text(encoding="utf-8"))
    assert inteiro(sum(v["empresa_anos_iguais"] for v in inv["exercicios"].values()), lang) in pre
    for d in ("2026-12-20", "2027-01-25", "2027-01-31", "2027-03-31", "2027-04-15", "2027-04-30", "2026-11-19",
              "2029-12-31"):  # fmt: skip
        assert data(d, lang) in pre, d
    assert data(secundaria.DATA_MINIMA.isoformat(), lang) in pre
    assert str(secundaria.SEMENTE) in emenda and inteiro(secundaria.REAMOSTRAGENS, lang) in emenda
    assert "DT_RECEB" in pre and "DT_RECEB" in emenda
    registro = ("**Registrado em 22/11/2026.**", "Emenda 5 ·", "não foi usada nem registrada") if lang == "pt" else (
        "**Registered on 2026-11-22.**", "Amendment 5 ·", "neither used nor registered")  # fmt: skip
    assert registro[0] in pre and registro[1] in emenda and registro[2] in emenda


@pytest.mark.parametrize("lang", ["pt", "en"])
def test_emenda_5_registrada_sem_mudar_o_resto_do_estudo_2(lang: str) -> None:
    """Registro de 22/11/2026: a emenda 5 entra na seção 13 do pré-registro do estudo 2, depois da emenda 3, e o texto
    anterior a ela fica igual, byte a byte, ao arquivo de antes do registro."""
    texto = ESTUDO_2[lang].read_text(encoding="utf-8")
    antes = texto.split(CABECALHO_EMENDA_5[lang], 1)[0]
    assert hashlib.sha256(antes.encode("utf-8")).hexdigest() == ESTUDO_2_ANTES_DA_EMENDA_5[lang]
    assert texto.count("### Emenda 5") + texto.count("### Amendment 5") == 1


@pytest.mark.parametrize("lang", ["pt", "en"])
def test_pre_registro_do_v2_registrado_com_a_revisao_de_roberto(lang: str) -> None:
    doc = PRE[lang].read_text(encoding="utf-8")
    assert ("rascunho" if lang == "pt" else "draft") not in doc.lower()
    if lang == "pt":
        assert "# Pré-registro do motor v2\n" in doc and "- Data: 22/11/2026." in doc
        assert "## 12. Revisão de Roberto (22/11/2026)" in doc
    else:
        assert "# Engine v2 pre-registration\n" in doc and "- Date: 2026-11-22." in doc
        assert "## 12. Roberto's review (2026-11-22)" in doc
    revisao = doc.split("\n## 12.", 1)[1]
    assert revisao.count("\n1. ") == 1 and "\n8. " in revisao
    aviso = RAIZ / ("docs/estudo-2-emenda-5-rascunho.md" if lang == "pt" else "docs/en/study-2-amendment-5-draft.md")
    assert ("seção 13" if lang == "pt" else "section 13") in aviso.read_text(encoding="utf-8")


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


@pytest.mark.parametrize("lang", ["pt", "en"])
def test_emenda_5_item_3_alerta_da_lista_inteira_medidas_no_conjunto_do_v1(lang: str) -> None:
    """Pedido de 22/11/2026: o alerta do v2 sai da lista do v2 inteira, e todas as medidas do braço são calculadas só
    nas empresa-anos avaliadas pelo v1."""
    emenda = _emenda_5(lang)
    item_3 = emenda.split("\n3. ", 1)[1].split("\n4. ", 1)[0]
    if lang == "pt":
        frases = ("O alerta do v2 sai da lista do v2 inteira", "entre todas as empresa-anos que o v2 avalia",
                  "são calculadas só nas empresa-anos que a seção 7.2 avalia para o v1", "subconjunto prospectivo",
                  "ficam à parte, só como descrição")  # fmt: skip
    else:
        frases = ("v2's alert comes from the whole v2 list", "among all the company-years that v2 evaluates",
                  "is computed only on the company-years that section 7.2 evaluates for v1", "prospective subset",
                  "reported separately, as description only")  # fmt: skip
    assert all(f in item_3 for f in frases)
