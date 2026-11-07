"""Comparação de texto do estudo (pré-registro, Emenda 7): sem maiúsculas, acentos nem espaços repetidos."""

from __future__ import annotations

import re
import unicodedata


def normaliza(texto: object) -> str:
    t = unicodedata.normalize("NFKD", str(texto))
    t = "".join(c for c in t if not unicodedata.combining(c)).lower()
    return re.sub(r"\s+", " ", t).strip()
