"""Salto no prazo médio de pagamento a fornecedores (sinal `dpo_salto` do catálogo, fase mvp).

O que mede: quantos dias a empresa leva para pagar fornecedores e quanto isso mudou de um ano para o
outro. Pagar mais tarde infla o caixa operacional uma vez só; dívida com banco mantida em
"Fornecedores" (risco sacado) alonga o prazo e esconde endividamento.

Livro: Financial Shenanigans, 4ª ed., capítulos 12 e 14 (pp. 168-185 e 203-219 do PDF do catálogo).
Norma: Ofícios-Circulares CVM/SNC/SEP 01/2017 e 01/2018.

Contas: fornecedores 2.01.02; custo_vendas 3.02 (negativo na DFP; usa-se o valor absoluto).
Fórmula: DPO = fornecedores / |custo_vendas| * 365; sinal = DPO_t - DPO_t-1. A regra de alerta
(decil superior do ano) é do pré-registro e é aplicada na avaliação, não aqui.
"""

from __future__ import annotations

from typing import Mapping

from chiocca.sinais.resultado import NaoCalculavel, Resultado, conta, divide

Valores = Mapping[str, float | None]
DIAS = 365


def dpo(v: Valores, rotulo: str = "t") -> float:
    return divide(conta(v, "fornecedores"), abs(conta(v, "custo_vendas")), f"DPO custo {rotulo}") * DIAS


def variacao(t: Valores, t1: Valores) -> Resultado:
    try:
        return Resultado(dpo(t, "t") - dpo(t1, "t-1"))
    except NaoCalculavel as e:
        return Resultado(None, f"{e.motivo}:{e.detalhe}")
