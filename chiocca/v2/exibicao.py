"""Exibição da v2 (tela e PDF): número negativo com o sinal de menos (−, U+2212), e não com o hífen (pedido de
10/11/2026). Vale para os números que a v2 formata e para os textos da investigação que ela entrega à tela e ao PDF,
inclusive regras como "M > −1,78". Os arquivos e textos do estudo 1 não mudam: `chiocca/formato.py` e os documentos
gerados por ele continuam com o hífen.
"""

from __future__ import annotations

import re
from typing import Any

from chiocca import formato

MENOS = "−"
# Hífen usado como sinal: no começo do texto ou depois de espaço, parêntese, sinal de comparação ou de igual, e antes de
# um algarismo. Datas (2024-12-31), intervalos (2010-2023), códigos e palavras compostas ficam como estão.
_SINAL = re.compile(r"(?<![\w.,\-−/])-(?=\d)")
# Campos que são dado literal ou identificador, e não texto de exibição: ficam como vieram.
LITERAIS = frozenset({"id", "codigo", "motivo_v1", "url", "arquivo", "sha256", "trecho", "ds_conta", "num_doc"})


def com_sinal_de_menos(texto: str) -> str:
    return _SINAL.sub(MENOS, texto)


def decimal(x: float, lang: str, casas: int = 1) -> str:
    return com_sinal_de_menos(formato.decimal(x, lang, casas))


def pct(x: float, lang: str, casas: int = 1) -> str:
    return com_sinal_de_menos(formato.pct(x, lang, casas))


def inteiro(n: int, lang: str) -> str:
    return com_sinal_de_menos(formato.inteiro(n, lang))


def textos_com_sinal_de_menos(x: Any, chave: str | None = None) -> Any:
    """Aplica `com_sinal_de_menos` a todo texto de exibição de um JSON da v2; dado literal (trecho do parecer, nome da
    conta como veio da CVM), identificador e as evidências ficam como vieram."""
    if chave in LITERAIS or chave == "evidencias":
        return x
    if isinstance(x, str):
        return com_sinal_de_menos(x)
    if isinstance(x, dict):
        return {k: textos_com_sinal_de_menos(v, k) for k, v in x.items()}
    if isinstance(x, list):
        return [textos_com_sinal_de_menos(v, chave) for v in x]
    return x
