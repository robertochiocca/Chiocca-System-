"""Juro implícito sobre a dívida declarada (sinal `juro_implicito` do catálogo, fase mvp).

O que mede: a despesa financeira dividida pela dívida bancária média. Muito acima do CDI do ano, sugere
financiamento fora da linha de empréstimos. É hipótese, não regra: a despesa financeira também traz
juros de arrendamento, desconto de recebíveis e variação cambial.

Livro: Financial Shenanigans, 4ª ed., capítulos 10 e 12 (pp. 142-155 e 168-185 do PDF do catálogo).

Contas: despesas_financeiras 3.06.02 (negativa na DFP; usa-se o valor absoluto); emprestimos_cp 2.01.04;
emprestimos_lp 2.02.01. Fórmula: |despesas_financeiras_t| / média(empréstimos CP + LP, t e t-1).
A comparação com o CDI médio do ano (regra do pré-registro: juro > CDI + 10 p.p.) usa a série do CDI
com procedência registrada, que entra na Fase 2.
"""

from __future__ import annotations

from typing import Mapping

from chiocca.sinais.resultado import NaoCalculavel, Resultado, conta, divide

Valores = Mapping[str, float | None]


def divida_media(t: Valores, t1: Valores) -> float:
    d_t = conta(t, "emprestimos_cp") + conta(t, "emprestimos_lp")
    d_t1 = conta(t1, "emprestimos_cp") + conta(t1, "emprestimos_lp")
    return (d_t + d_t1) / 2


def juro(t: Valores, t1: Valores) -> Resultado:
    try:
        return Resultado(divide(abs(conta(t, "despesas_financeiras")), divida_media(t, t1), "divida media"))
    except NaoCalculavel as e:
        return Resultado(None, f"{e.motivo}:{e.detalhe}")


def spread_pp(juro_implicito: float, cdi_medio: float) -> float:
    """Diferença em pontos percentuais entre o juro implícito e o CDI médio do ano."""
    return (juro_implicito - cdi_medio) * 100
