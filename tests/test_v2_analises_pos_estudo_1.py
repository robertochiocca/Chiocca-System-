"""Análise depois do estudo 1 (descritiva, não pré-registrada): distribuição binomial de Poisson exata."""

from __future__ import annotations

import json
import math

import pytest

from chiocca.v2 import analises_pos_estudo_1 as ap
from tests.test_v2_docs import numeros


def test_binomial_de_poisson_coincide_com_a_binomial_quando_p_e_igual() -> None:
    p, n = 0.3, 7
    pmf = ap.binomial_de_poisson([p] * n)
    for k in range(n + 1):
        assert pmf[k] == pytest.approx(math.comb(n, k) * p**k * (1 - p) ** (n - k))
    assert sum(pmf) == pytest.approx(1.0)


def test_probabilidades_diferentes_e_cauda() -> None:
    pmf = ap.binomial_de_poisson([0.5, 0.2])
    assert pmf == pytest.approx([0.4, 0.5, 0.1])
    assert ap.cauda_superior(pmf, 1) == pytest.approx(0.6)
    with pytest.raises(ValueError):
        ap.binomial_de_poisson([1.2])


def test_chance_de_um_caso_com_varios_anos() -> None:
    n = {
        "taxa": {"nf": {"2014": {"em_alerta": 1, "avaliadas": 2}, "2015": {"em_alerta": 1, "avaliadas": 4}}},
        "casos": [{"acertavel": True, "caso_id": "x", "empresa": "X", "grupos": ["nao_financeira"],
                   "anos_periodo": [2014, 2015], "anos_avaliados": [2014, 2015], "acertado": True}],
    }  # fmt: skip
    r = ap.calcula(n)
    assert r["casos"][0]["p_acaso"] == pytest.approx(1 - 0.5 * 0.75)
    assert r["observados"] == 1 and r["p_cauda"] == pytest.approx(0.625)


@pytest.mark.parametrize("lang", ["pt", "en"])
def test_documento_igual_a_saida_do_script(lang: str) -> None:
    r = ap.calcula(json.loads(ap.NUMEROS_ESTUDO_1.read_text(encoding="utf-8")))
    assert ap.DOCS[lang].read_text(encoding="utf-8") == ap.render(r, lang)


def test_mesmos_numeros_e_rotulo_nos_dois_idiomas() -> None:
    pt, en = ap.DOCS["pt"].read_text(encoding="utf-8"), ap.DOCS["en"].read_text(encoding="utf-8")
    assert numeros(pt, "pt") == numeros(en, "en")
    assert "não pré-registrada" in pt and "not pre-registered" in en
