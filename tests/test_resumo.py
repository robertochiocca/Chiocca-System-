"""O resumo de uma página sai do script, cabe numa página e tem os mesmos números em PT e EN (PROMPT.md, Fase 5)."""

from __future__ import annotations

import json

import pytest

from chiocca import relatorio_resultados as rr
from chiocca import textos_resumo as tr
from tests.test_relatorio_resultados import _extrai

pytestmark = pytest.mark.skipif(not rr.NUMEROS.exists(), reason="docs/resultados_numeros.json ainda não gerado")


def _numeros() -> dict:
    return json.loads(rr.NUMEROS.read_text(encoding="utf-8"))


@pytest.mark.parametrize("lang", ["pt", "en"])
def test_resumo_igual_a_saida_do_script(lang: str) -> None:
    assert rr.RESUMO[lang].read_text(encoding="utf-8") == tr.render(_numeros(), lang)


def test_mesmos_numeros_nos_dois_idiomas() -> None:
    pt = _extrai(rr.RESUMO["pt"].read_text(encoding="utf-8"), "pt")
    en = _extrai(rr.RESUMO["en"].read_text(encoding="utf-8"), "en")
    assert pt == en


@pytest.mark.parametrize("lang", ["pt", "en"])
def test_uma_pagina_e_sem_linguagem_de_acusacao(lang: str) -> None:
    texto = rr.RESUMO[lang].read_text(encoding="utf-8")
    assert len(texto.splitlines()) <= 60
    baixo = texto.lower()
    assert "fraude" not in baixo and "fraud" not in baixo and "suspeit" not in baixo and "suspect" not in baixo


def test_catalogo_completo() -> None:
    assert tr.T["pt"].keys() == tr.T["en"].keys()
    for chave, pt in tr.T["pt"].items():
        en = tr.T["en"][chave]
        if isinstance(pt, (list, dict)):
            assert len(pt) == len(en), chave
        else:
            assert pt.strip() and en.strip() and pt != en, chave
