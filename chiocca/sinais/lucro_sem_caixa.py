"""Lucro que não vira caixa (sinal `lucro_sem_caixa` do catálogo, fase mvp).

O que mede: a distância entre o lucro líquido e o caixa operacional, em proporção do ativo médio. Já
entra no M-score pelo TATA; aqui aparece sozinho na ficha de alerta e não dispara alerta (pré-registro,
seção 4).

Referência acadêmica: Sloan (1996), The Accounting Review. Livro: Financial Shenanigans, 4ª ed.,
capítulo 7 (pp. 100-112 do PDF do catálogo).

Contas: lucro_liquido 3.11; caixa_operacional 6.01; ativo_total 1.
Fórmula: (lucro_liquido_t - caixa_operacional_t) / média(ativo_total, t e t-1).
"""

from __future__ import annotations

from typing import Mapping

from chiocca.sinais.resultado import NaoCalculavel, Resultado, conta, divide

Valores = Mapping[str, float | None]


def accruals(t: Valores, t1: Valores) -> Resultado:
    try:
        ativo_medio = (conta(t, "ativo_total") + conta(t1, "ativo_total")) / 2
        numerador = conta(t, "lucro_liquido") - conta(t, "caixa_operacional")
        return Resultado(divide(numerador, ativo_medio, "ativo medio"))
    except NaoCalculavel as e:
        return Resultado(None, f"{e.motivo}:{e.detalhe}")
