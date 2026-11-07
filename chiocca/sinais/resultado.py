"""Tipo comum de resultado: um valor ou "não calculável" com o motivo (regra 5 do PROMPT.md).

Dado faltante nunca vira zero. Quem chama recebe o motivo e conta a falha no relatório.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Mapping

# Motivos padronizados de "não calculável" (os textos ao usuário ficam nos catálogos de mensagens).
CONTA_AUSENTE = "conta_ausente"
DIVISAO_POR_ZERO = "divisao_por_zero"
EMPRESA_FINANCEIRA = "empresa_financeira"
DENOMINADOR_NEGATIVO = "denominador_negativo"


@dataclass(frozen=True)
class Resultado:
    """Valor de um cálculo, ou None com o motivo de não ter sido calculado."""

    valor: float | None
    motivo: str | None = None

    @property
    def calculavel(self) -> bool:
        return self.valor is not None


class NaoCalculavel(Exception):
    """Interrompe um cálculo; o motivo vira Resultado(None, motivo)."""

    def __init__(self, motivo: str, detalhe: str = "") -> None:
        super().__init__(f"{motivo}: {detalhe}" if detalhe else motivo)
        self.motivo = motivo
        self.detalhe = detalhe


def conta(valores: Mapping[str, float | None], nome: str) -> float:
    """Lê uma conta; ausente ou NaN interrompe o cálculo (nunca vira zero)."""
    v = valores.get(nome)
    if v is None or (isinstance(v, float) and math.isnan(v)):
        raise NaoCalculavel(CONTA_AUSENTE, nome)
    return float(v)


def divide(numerador: float, denominador: float, nome: str) -> float:
    if denominador == 0:
        raise NaoCalculavel(DIVISAO_POR_ZERO, nome)
    return numerador / denominador


def divide_por_positivo(numerador: float, denominador: float, nome: str) -> float:
    """Divisão em que o denominador tem que ser positivo (pré-registro, emenda 10: receita ≤ 0)."""
    if denominador < 0:
        raise NaoCalculavel(DENOMINADOR_NEGATIVO, nome)
    return divide(numerador, denominador, nome)
