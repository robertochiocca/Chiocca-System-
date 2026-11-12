"""Trechos do leitor: segmentos de texto de uma página (parágrafo ou linha de tabela) e a saída de cada trecho, com
a conferência literal e a omissão por nome de pessoa física.

Um segmento nunca atravessa a página: o trecho mostrado tem de estar no texto da página de onde veio.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from chiocca.v2.leitor import nomes
from chiocca.v2.leitor.texto import busca, confere, linhas, normaliza

_NUMERO = re.compile(r"^\(?[-−–]?\d[\d.,]*\)?%?$|^[-−–—]$")
_INICIO_DE_ITEM = re.compile(r"^([A-ZÀ-Ý0-9(•\-–—]|[a-z]\))")
OMITIDO = {
    "pt": "trecho omitido; ver página {p} do documento",
    "en": "excerpt omitted; see page {p} of the document",
}
OMITIDO_SEM_PAGINA = {
    "pt": "trecho omitido; ver o relatório do auditor no documento",
    "en": "excerpt omitted; see the auditor's report in the document",
}


def linha_de_tabela(linha: str) -> bool:
    """Linha com dois ou mais números (valores de colunas), como as linhas das tabelas das notas."""
    return sum(1 for t in linha.split() if _NUMERO.match(t)) >= 2


@dataclass(frozen=True)
class Segmento:
    pagina: int  # começa em 1
    texto: str  # linhas da página juntadas com um espaço (é trecho literal da página)

    @property
    def busca(self) -> str:
        return busca(self.texto)


def segmentos(texto_da_pagina: str, pagina: int, de: int = 0, ate: int | None = None) -> list[Segmento]:
    """Parágrafos e linhas de tabela das linhas [de, ate) da página. Um parágrafo termina em linha em branco, em linha
    de tabela ou quando a linha anterior acaba em ponto (ou dois-pontos, ponto e vírgula) e a seguinte começa como item
    ou frase nova."""
    ls = linhas(texto_da_pagina)[de:ate]
    out: list[Segmento] = []
    atual: list[str] = []

    def fecha() -> None:
        if atual:
            out.append(Segmento(pagina, " ".join(atual)))
            atual.clear()

    for linha in ls:
        if not linha:
            fecha()
        elif linha_de_tabela(linha):
            fecha()
            out.append(Segmento(pagina, linha))
        else:
            if atual and re.search(r"[.:;]$", atual[-1]) and _INICIO_DE_ITEM.match(linha):
                fecha()
            atual.append(linha)
    fecha()
    return out


@dataclass(frozen=True)
class Trecho:
    verificacao: str
    rotulo: str | None
    pagina: int | None
    texto: str
    negacao: bool | None = None
    cortado: bool = False

    def saida(self, fonte: str, lang: str) -> dict[str, Any]:
        """O trecho na saída do leitor: mostrado (com a conferência literal) ou omitido por nome de pessoa física."""
        omitir = nomes.tem_nome_de_pessoa(self.texto)
        aviso = OMITIDO[lang].format(p=self.pagina) if self.pagina is not None else OMITIDO_SEM_PAGINA[lang]
        return {
            "verificacao": self.verificacao, "rotulo": self.rotulo, "pagina": self.pagina,
            "texto": None if omitir else normaliza(self.texto), "omitido": omitir,
            "aviso_omissao": aviso if omitir else None, "conferido": confere(self.texto, fonte),
            "negacao": self.negacao, "cortado": self.cortado, "idioma_original": "pt",
        }  # fmt: skip


def corta(texto: str, limite: int = 1200) -> tuple[str, bool]:
    """Corta um trecho longo no fim da última frase antes do limite (o começo continua literal)."""
    t = normaliza(texto)
    if len(t) <= limite:
        return t, False
    m = list(re.finditer(r"[.;](?=\s)", t[:limite]))
    fim = m[-1].end() if m and m[-1].end() > limite // 3 else limite
    return t[:fim].rstrip(), True
