"""Seção "Limites" da página de investigação: texto fixo com os números lidos da saída do estudo 1."""

from __future__ import annotations

import json

import pytest

from chiocca.v2 import analises_pos_estudo_1 as ap
from chiocca.v2 import limites
from tests.test_v2_docs import numeros


def test_mesmos_numeros_nos_dois_idiomas() -> None:
    assert numeros(" ".join(limites.textos("pt")), "pt") == numeros(" ".join(limites.textos("en")), "en")


def test_texto_fixo_de_roberto() -> None:
    pt = limites.textos("pt")
    assert pt[0].startswith("Não ter alerta não é atestado. Em Dechow, Sloan e Sweeney (1995)")
    assert "28,1% de 32 empresas punidas pela SEC (Tabela 7, p. 32)" in pt[0]
    assert pt[1].startswith(
        "No estudo 1, 49,9% das empresas-ano ficaram em alerta, e o número de acertos não superou o acaso"
    )
    assert pt[2] == ("Os modelos de risco usam números que podem estar manipulados (Pereira e Martins 2015, p. 29). "
                     "Por isso as três famílias não se somam.")  # fmt: skip


def test_para_se_os_acertos_superassem_o_acaso() -> None:
    n = json.loads(ap.NUMEROS_ESTUDO_1.read_text(encoding="utf-8"))
    for c in n["casos"]:
        if c["acertavel"]:
            c["acertado"] = True
    with pytest.raises(ValueError):
        limites.textos("pt", n, None)
