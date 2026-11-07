"""Os documentos da base saem do script e têm os mesmos números em PT e EN (regra 2 e paridade do PROMPT.md)."""

from __future__ import annotations

import json
import re

import pytest

from chiocca import relatorio_base as rb

pytestmark = pytest.mark.skipif(not rb.NUMEROS.exists(), reason="docs/base_numeros.json ainda não gerado")


def _numeros() -> dict:
    return json.loads(rb.NUMEROS.read_text(encoding="utf-8"))


@pytest.mark.parametrize("lang", ["pt", "en"])
def test_documento_igual_a_saida_do_script(lang: str) -> None:
    assert rb.DOCS[lang].read_text(encoding="utf-8") == rb.render(_numeros(), lang)


def _extrai(texto: str, lang: str) -> list[float]:
    # Identificadores não são quantidades: código de conta (3.01) e parte de documento (4.1).
    texto = re.sub(r"\b(conta|account|parte|part) \d+(\.\d+)+", r"\1", texto)
    if lang == "pt":
        texto = re.sub(r"(\d{2})/(\d{2})/(\d{4})", r"\3 \2 \1", texto)
        brutos = re.findall(r"\d[\d.]*(?:,\d+)?", texto)
        return sorted(float(x.replace(".", "").replace(",", ".")) for x in brutos)
    texto = re.sub(r"(\d{4})-(\d{2})-(\d{2})", r"\1 \2 \3", texto)
    brutos = re.findall(r"\d[\d,]*(?:\.\d+)?", texto)
    return sorted(float(x.replace(",", "")) for x in brutos)


def test_mesmos_numeros_nos_dois_idiomas() -> None:
    pt = _extrai(rb.DOCS["pt"].read_text(encoding="utf-8"), "pt")
    en = _extrai(rb.DOCS["en"].read_text(encoding="utf-8"), "en")
    assert pt == en


def test_catalogo_de_mensagens_completo() -> None:
    assert rb.TEXTOS["pt"].keys() == rb.TEXTOS["en"].keys()
    for chave in rb.TEXTOS["pt"]:
        assert rb.TEXTOS["pt"][chave].strip() and rb.TEXTOS["en"][chave].strip()
        if chave != "total":  # "Total" é igual nos dois idiomas
            assert rb.TEXTOS["pt"][chave] != rb.TEXTOS["en"][chave], chave
