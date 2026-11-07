"""Data de corte (pré-registro, seção 3, e emenda 5).

Exercício que termina em 31/12: 30 de abril do ano seguinte. Regra geral (emenda 5): último dia do quarto
mês depois do fim do exercício, o que dá 30/04 para quem fecha em 31/12.
"""

from __future__ import annotations

import calendar
from datetime import date


def data_corte(fim_exercicio: date | str) -> date:
    d = date.fromisoformat(fim_exercicio) if isinstance(fim_exercicio, str) else fim_exercicio
    mes = d.month + 4
    ano = d.year + (mes - 1) // 12
    mes = (mes - 1) % 12 + 1
    return date(ano, mes, calendar.monthrange(ano, mes)[1])
