"""Documentos do v2 escritos à mão: cada um tem o par em inglês, com os mesmos números (paridade do PROMPT.md)."""

from __future__ import annotations

import re
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[1]
PARES = [
    ("docs/inventario.md", "docs/en/inventory.md"),
    ("docs/contratos.md", "docs/en/contracts.md"),
    ("docs/plano-v2.md", "docs/en/plan-v2.md"),
    ("docs/origem-do-codigo.md", "docs/en/code-origin.md"),
    ("docs/roadmap.md", "docs/en/roadmap.md"),
    ("docs/motor-de-confianca.md", "docs/en/trust-engine.md"),
]
AVISO_PT = "Sinal estatístico baseado em demonstrações públicas. Não é acusação, não é recomendação de investimento."
AVISO_EN = "Statistical signal based on public financial statements. Not an accusation, not investment advice."


def numeros(texto: str, lang: str) -> list[float]:
    """Números de um texto, depois de levar o formato PT (1.234,5 e 31/12/2025) ao formato EN."""
    texto = re.sub(r"`[^`\n]*`", " ", texto)  # identificadores e hashes em código
    if lang == "pt":
        texto = re.sub(r"(\d{2})/(\d{2})/(\d{4})", r"\3 \2 \1", texto)
        texto = re.sub(r"(?<=\d)\.(?=\d{3}\b)", "", texto)  # separador de milhar
        texto = re.sub(r"(?<=\d),(?=\d)", ".", texto)  # vírgula decimal
    else:
        texto = re.sub(r"(\d{4})-(\d{2})-(\d{2})", r"\1 \2 \3", texto)
        texto = re.sub(r"(?<=\d),(?=\d{3}\b)", "", texto)
    return sorted(float(x) for x in re.findall(r"\d+(?:\.\d+)?", texto))


@pytest.mark.parametrize("pt,en", PARES)
def test_par_em_ingles_com_os_mesmos_numeros(pt: str, en: str) -> None:
    texto_pt = (RAIZ / pt).read_text(encoding="utf-8")
    texto_en = (RAIZ / en).read_text(encoding="utf-8")
    assert numeros(texto_pt, "pt") == numeros(texto_en, "en")


def test_aviso_fixo_nos_contratos() -> None:
    assert AVISO_PT in (RAIZ / "docs/contratos.md").read_text(encoding="utf-8")
    assert AVISO_EN in (RAIZ / "docs/en/contracts.md").read_text(encoding="utf-8")


def test_numeros_no_formato_de_cada_lingua() -> None:
    assert numeros("2.200 linhas, 0,053 e 31/12/2024", "pt") == numeros("2,200 lines, 0.053 and 2024-12-31", "en")
