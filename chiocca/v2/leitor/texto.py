"""Texto de cada página de um PDF (pypdf, modo layout) e a conferência literal dos trechos.

A conferência só normaliza espaços (e o espaço sem quebra) e a forma Unicode (NFC): o trecho mostrado tem de aparecer,
assim, no texto da página de onde veio. Página sem camada de texto não é lida (sem reconhecimento de texto em imagem).
"""

from __future__ import annotations

import io
import re
import unicodedata
from dataclasses import dataclass, field

import pypdf

MAX_BYTES = 40_000_000
MAX_PAGINAS = 600
MIN_CARACTERES_POR_PAGINA = 80  # abaixo disso, na média, o PDF não tem camada de texto que sirva

_ESPACOS = re.compile(r"\s+")


def normaliza(texto: str) -> str:
    """Espaços (inclusive o sem quebra) viram um espaço só; forma NFC; sem espaço nas pontas."""
    return _ESPACOS.sub(" ", unicodedata.normalize("NFC", texto).replace(" ", " ")).strip()


def confere(trecho: str, fonte: str) -> bool:
    """Conferência literal: o trecho, com os espaços normalizados, está no texto da fonte, também normalizado."""
    t = normaliza(trecho)
    return bool(t) and t in normaliza(fonte)


@dataclass
class Paginas:
    status: str  # "lido" ou "nao_lido"
    paginas: list[str] = field(default_factory=list)
    motivo: str | None = None
    extrator: str = f"pypdf {pypdf.__version__} (modo layout)"


def _texto_da_pagina(pagina: pypdf.PageObject) -> str:
    try:
        return pagina.extract_text(extraction_mode="layout") or ""
    except Exception:  # noqa: BLE001 - o modo layout falha em alguns PDFs; o modo simples ainda dá o texto
        return pagina.extract_text() or ""


def paginas_do_pdf(conteudo: bytes) -> Paginas:
    if len(conteudo) > MAX_BYTES:
        return Paginas("nao_lido", motivo="arquivo_grande_demais")
    try:
        leitor = pypdf.PdfReader(io.BytesIO(conteudo))
        n = len(leitor.pages)
    except Exception:  # noqa: BLE001 - PDF que o pypdf não abre não é lido
        return Paginas("nao_lido", motivo="pdf_invalido")
    if n == 0:
        return Paginas("nao_lido", motivo="pdf_sem_paginas")
    if n > MAX_PAGINAS:
        return Paginas("nao_lido", motivo="paginas_demais")
    textos = [_texto_da_pagina(p) for p in leitor.pages]
    if sum(len(normaliza(t)) for t in textos) / n < MIN_CARACTERES_POR_PAGINA:
        return Paginas("nao_lido", textos, motivo="sem_camada_de_texto")
    return Paginas("lido", textos)


def linhas(texto: str) -> list[str]:
    """Linhas da página com os espaços normalizados (vazia = linha em branco)."""
    return [normaliza(x) for x in texto.split("\n")]


def busca(texto: str) -> str:
    """Forma de busca: minúsculas, sem hifenização de fim de linha ("contro- ladora" vira "controladora")."""
    return re.sub(r"(\w)- (\w)", r"\1\2", normaliza(texto)).lower()
