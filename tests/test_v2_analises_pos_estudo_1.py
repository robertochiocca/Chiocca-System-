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


def _r() -> dict:
    return ap.calcula(json.loads(ap.NUMEROS_ESTUDO_1.read_text(encoding="utf-8")), ap.le_dados())


@pytest.mark.parametrize("lang", ["pt", "en"])
def test_documento_igual_a_saida_do_script(lang: str) -> None:
    assert ap.DOCS[lang].read_text(encoding="utf-8") == ap.render(_r(), lang)


@pytest.mark.parametrize(
    "lang,link", [("pt", "docs/analises-pos-estudo-1.md"), ("en", "docs/en/post-study-1-analyses.md")]
)
def test_readme_traz_o_resultado_com_o_rotulo(lang: str, link: str) -> None:
    paragrafo = ap.resumo(_r(), lang, link)
    assert paragrafo is not None
    assert paragrafo in (ap.RAIZ / "README.md").read_text(encoding="utf-8")
    assert ("não pré-registrada" if lang == "pt" else "not pre-registered") in paragrafo


def test_variante_e_teto() -> None:
    r = _r()
    assert "variante" in r and r["variante"]["esperado"] <= r["esperado"]
    assert r["variante"]["p_cauda"] <= r["p_cauda"]


def test_variante_com_numeros_sinteticos() -> None:
    n = {
        "taxa": {"nf": {"2014": {"em_alerta": 1, "avaliadas": 2}}},
        "casos": [{"acertavel": True, "caso_id": "x", "empresa": "X", "grupos": ["nao_financeira"],
                   "anos_periodo": [2014], "anos_avaliados": [2014], "acertado": False}],
    }  # fmt: skip
    dados = {
        "variante": [{"caso_id": "x", "empresas": 4, "com_alerta": 1, "empresa_do_caso_incluida": True}],
        "persistencia": {k: {"em_alerta_com_anterior_avaliado": 4, "anterior_tambem_em_alerta": 3, "avaliadas": 10,
                             "em_alerta": 5} for k in ("nf", "fin", "total")},
        "nao_preenchidas": {},
    }  # fmt: skip
    r = ap.calcula(n, dados)
    assert r["variante"]["casos"][0]["p_acaso"] == pytest.approx(0.25)
    assert r["variante"]["esperado"] == pytest.approx(0.25) and r["variante"]["p_cauda"] == pytest.approx(1.0)
    texto = ap.resumo(r, "pt")
    assert texto is not None and "75,0%" in texto and "50,0%" in texto
    with pytest.raises(ValueError):
        ap.calcula(n, dados | {"variante": []})


def test_mesmos_numeros_e_rotulo_nos_dois_idiomas() -> None:
    pt, en = ap.DOCS["pt"].read_text(encoding="utf-8"), ap.DOCS["en"].read_text(encoding="utf-8")
    assert numeros(pt, "pt") == numeros(en, "en")
    assert "não pré-registrada" in pt and "not pre-registered" in en


@pytest.mark.parametrize(
    "lang,link", [("pt", "docs/analises-pos-estudo-1.md"), ("en", "docs/en/post-study-1-analyses.md")]
)
def test_readme_cita_os_balancos_nao_preenchidos(lang: str, link: str) -> None:
    frase = ap.frase_readme_nao_preenchidas(_r(), lang, link)
    assert frase is not None and frase in (ap.RAIZ / "README.md").read_text(encoding="utf-8")


@pytest.mark.parametrize(
    "caminho,taxa,definicao",
    [("README.md", "49,9%", "não financeiras"), ("docs/resumo.md", "49,9%", "não financeiras"),
     ("README.md", "49.9%", "non-financial"), ("docs/summary.md", "49.9%", "non-financial")],
)  # fmt: skip
def test_taxa_de_alerta_sempre_com_a_mesma_definicao(caminho: str, taxa: str, definicao: str) -> None:
    """Pedido de 08/11/2026: a taxa de alerta citada é sempre a das empresa-anos não financeiras avaliadas."""
    blocos = (ap.RAIZ / caminho).read_text(encoding="utf-8").split("\n\n")
    citados = [b for b in blocos if taxa in b]
    assert citados and all(definicao in b.lower() for b in citados)
