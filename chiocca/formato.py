"""Formatação de números, porcentagens, datas e moeda por idioma, num lugar só (PROMPT.md, projeto bilíngue).

PT: R$ 1.234,56 · 12,5% · 31/12/2025 · 1.234
EN: R$1,234.56 · 12.5% · 2025-12-31 · 1,234 (a moeda continua sendo o real)
"""

from __future__ import annotations

from datetime import date

IDIOMAS = ("pt", "en")


def _troca(texto_en: str, lang: str) -> str:
    if lang == "en":
        return texto_en
    if lang == "pt":
        return texto_en.replace(",", "§").replace(".", ",").replace("§", ".")
    raise ValueError(f"idioma desconhecido: {lang}")


def inteiro(n: int, lang: str) -> str:
    return _troca(f"{int(n):,}", lang)


def decimal(x: float, lang: str, casas: int = 1) -> str:
    return _troca(f"{x:,.{casas}f}", lang)


def pct(x: float, lang: str, casas: int = 1) -> str:
    """x em fração (0.125 -> 12,5% / 12.5%)."""
    return decimal(100 * x, lang, casas) + "%"


def moeda(x: float, lang: str, casas: int = 2) -> str:
    return ("R$ " if lang == "pt" else "R$") + decimal(x, lang, casas)


def data(d: date | str, lang: str) -> str:
    d = date.fromisoformat(d) if isinstance(d, str) else d
    if lang == "pt":
        return d.strftime("%d/%m/%Y")
    if lang == "en":
        return d.isoformat()
    raise ValueError(f"idioma desconhecido: {lang}")
