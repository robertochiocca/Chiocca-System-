"""Rascunho do plano do motor v2 (pedido de 22/11/2026): cada número dos dois documentos sai dos JSONs versionados,
do manifesto do estudo 2 ou das constantes congeladas do estudo; nenhum é digitado à mão."""

from __future__ import annotations

import csv
import json
import re
from pathlib import Path
from typing import Any

import pytest

from chiocca.formato import data, decimal, inteiro, pct

RAIZ = Path(__file__).resolve().parents[1]
DOCS = {"pt": RAIZ / "docs/motor-v2-plano.md", "en": RAIZ / "docs/en/engine-v2-plan.md"}
DE = {"pt": "de", "en": "of"}


def _resultados() -> dict[str, Any]:
    return json.loads((RAIZ / "docs/resultados_numeros.json").read_text(encoding="utf-8"))


def _soma(por_ano: dict[str, dict[str, int]]) -> tuple[int, int, float, float]:
    alertas = sum(v["alertas"] for v in por_ano.values())
    calculaveis = sum(v["calculaveis"] for v in por_ano.values())
    taxas = [v["alertas"] / v["calculaveis"] for v in por_ano.values()]
    return alertas, calculaveis, min(taxas), max(taxas)


@pytest.mark.parametrize("lang", ["pt", "en"])
def test_numeros_do_estudo_1_saem_do_json(lang: str) -> None:
    doc = DOCS[lang].read_text(encoding="utf-8")
    r = _resultados()
    i, de = (lambda v: inteiro(v, lang)), DE[lang]
    sinais = r["por_sinal"]["nf"]
    for nome in ("alerta_mscore", "alerta_juro", "alerta_dpo"):
        a, c, menor, maior = _soma(sinais[nome])
        assert f"{pct(a / c, lang)}" in doc and f"{i(a)} {de} {i(c)}" in doc, nome
        if nome != "alerta_dpo":
            assert pct(menor, lang) in doc and pct(maior, lang) in doc, nome
    taxa = r["taxa"]["nf"]
    em_alerta, avaliadas = sum(v["em_alerta"] for v in taxa.values()), sum(v["avaliadas"] for v in taxa.values())
    assert f"{pct(em_alerta / avaliadas, lang)} ({i(em_alerta)} {de} {i(avaliadas)})" in doc
    por_ano = [v["avaliadas"] for v in taxa.values()]
    assert f"{i(min(por_ano))} " in doc and f" {i(max(por_ano))} " in doc
    m = r["nao_calculaveis"]["mscore"]
    assert f"{i(m['nao_calculaveis'])} {de} {i(m['empresa_anos'])}" in doc
    assert pct(m["nao_calculaveis"] / m["empresa_anos"], lang) in doc
    assert i(m["motivos"]["componente:DEPI"]) in doc
    assert decimal(r["regras"]["corte_m"], lang, 2) in doc and f"{decimal(r['regras']['spread_pp'], lang, 0)} p" in doc
    assert r["regras"]["percentil"] == 0.9  # o decil superior citado no plano
    assert f" {i(r['acerto']['acertaveis'])} " in doc


@pytest.mark.parametrize("lang", ["pt", "en"])
def test_numeros_iguais_aos_das_limitacoes_do_readme(lang: str) -> None:
    """A participação do juro implícito e a DFC sem linha de depreciação são as mesmas das limitações do README,
    geradas dos JSONs."""
    from chiocca.v2 import textos_readme

    doc = DOCS[lang].read_text(encoding="utf-8")
    juro, mscore = textos_readme.limitacoes(lang)[:2]
    m = re.search(r"(\d+[,.]\d%)[^(]*\((\d[\d.,]* (?:de|of) \d[\d.,]*)\)", juro)
    assert m and m.group(1) in doc and f"({m.group(2)})" in doc
    d = re.search(r"\((\d[\d.,]*) (?:empresa-anos|company-years)\)", mscore)
    assert d and f"({d.group(1)} " in doc


@pytest.mark.parametrize("lang", ["pt", "en"])
def test_entradas_datas_e_constantes(lang: str) -> None:
    from chiocca.v2.estudo2 import secundaria

    doc = DOCS[lang].read_text(encoding="utf-8")
    with (RAIZ / "data/estudo_2_manifesto.csv").open(encoding="utf-8") as f:
        enet = [r for r in csv.DictReader(f) if r["arquivo"].startswith("enet/")]
    assert f" {inteiro(len(enet), lang)} " in doc
    inv = json.loads((RAIZ / "docs/invariante_numeros.json").read_text(encoding="utf-8"))
    assert inteiro(sum(v["empresa_anos_iguais"] for v in inv["exercicios"].values()), lang) in doc
    assert str(secundaria.SEMENTE) in doc and inteiro(secundaria.REAMOSTRAGENS, lang) in doc
    assert data(secundaria.DATA_MINIMA.isoformat(), lang) in doc
    for d in ("2026-12-10", "2026-12-20", "2027-01-25", "2027-01-31", "2027-03-31", "2027-04-15", "2027-04-30",
              "2026-11-19", "2029-12-31"):  # fmt: skip
        assert data(d, lang) in doc, d


def test_plano_guarda_o_rascunho_da_emenda_5_e_o_motor_v2_so_entra_no_estudo_2_pela_emenda() -> None:
    """A seção 4 do plano guarda o rascunho da etapa; no pré-registro do estudo 2, o motor v2 só aparece na emenda 5,
    registrada em 22/11/2026, que diz que a emenda 4 (contingência do ENET) não foi usada nem registrada."""
    pre = (RAIZ / "docs/pre-registro-estudo-2.md").read_text(encoding="utf-8")
    antes, emenda_5 = pre.split("\n### Emenda 5 ·", 1)
    assert "motor v2" not in antes.lower() and "Emenda 4" not in antes and "motor v2" in emenda_5
    pt, en = DOCS["pt"].read_text(encoding="utf-8"), DOCS["en"].read_text(encoding="utf-8")
    assert "**Emenda 5 ·" in pt and "não foi usada nem registrada" in pt
    assert "**Amendment 5 ·" in en and "neither used nor registered" in en


@pytest.mark.parametrize("lang", ["pt", "en"])
def test_rotulo_prospectivo_por_empresa_ano(lang: str) -> None:
    """Decisão de Roberto (22/11/2026): 2025 prospectiva pelo DT_RECEB da DFP de 2026; 2024 não prospectiva."""
    doc = DOCS[lang].read_text(encoding="utf-8")
    assert "DT_RECEB" in doc
    assert ("não prospectivas nos dois braços" in doc) if lang == "pt" else ("not prospective in either arm" in doc)
