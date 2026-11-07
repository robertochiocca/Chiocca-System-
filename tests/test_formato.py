from __future__ import annotations

from datetime import date

import pytest

from chiocca import formato


def test_formatos_pt() -> None:
    assert formato.moeda(1234.56, "pt") == "R$ 1.234,56"
    assert formato.pct(0.125, "pt") == "12,5%"
    assert formato.data(date(2025, 12, 31), "pt") == "31/12/2025"
    assert formato.inteiro(1234567, "pt") == "1.234.567"


def test_formatos_en() -> None:
    assert formato.moeda(1234.56, "en") == "R$1,234.56"
    assert formato.pct(0.125, "en") == "12.5%"
    assert formato.data("2025-12-31", "en") == "2025-12-31"
    assert formato.inteiro(1234567, "en") == "1,234,567"


def test_idioma_desconhecido() -> None:
    with pytest.raises(ValueError):
        formato.inteiro(1, "es")
