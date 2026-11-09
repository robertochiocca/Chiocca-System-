"""Lacre dos exercícios de 2024 em diante (Chiocca System v2, regra 2).

Os exercícios de 2024 em diante são o teste limpo reservado ao estudo 2. Nesta etapa, o produto, os testes e as
demonstrações usam só exercícios até `ULTIMO_EXERCICIO_LIBERADO`: nenhum sinal ou indicador acima dele é calculado,
exibido ou resumido, nem para conferir.

O limite fica num lugar só, aqui no código, e não em variável de ambiente: mudá-lo exige um commit, que fica
registrado no histórico. Todo acesso do v2 a dados de um exercício passa por `garantir_liberado` ou por
`so_liberados`.
"""

from __future__ import annotations

from datetime import date

import pandas as pd

ULTIMO_EXERCICIO_LIBERADO = 2023
# Intervalo da data de referência (decisão de 07/11/2026): da primeira data de corte com DFP de 2010 ao fim de 2024.
# O lacre continua por exercício: em nenhuma data um exercício acima do limite é calculado.
DATA_REFERENCIA_MINIMA = date(2011, 4, 30)
DATA_REFERENCIA_MAXIMA = date(2024, 12, 31)


class DataForaDoIntervalo(ValueError):
    """Data de referência fora de [DATA_REFERENCIA_MINIMA, DATA_REFERENCIA_MAXIMA]."""

    def __init__(self, data: date) -> None:
        super().__init__(
            f"data de referência {data.isoformat()} fora do intervalo "
            f"{DATA_REFERENCIA_MINIMA.isoformat()} a {DATA_REFERENCIA_MAXIMA.isoformat()}"
        )
        self.data = data


class ExercicioLacrado(ValueError):
    """Pedido de exercício acima do lacre. A API traduz em recusa; o cálculo nunca começa."""

    def __init__(self, exercicio: int) -> None:
        super().__init__(
            f"exercício {exercicio} está lacrado: o último liberado é {ULTIMO_EXERCICIO_LIBERADO} "
            "(reservado ao estudo 2)"
        )
        self.exercicio = exercicio


def exercicio_de(dt_refer: str | date) -> int:
    """Exercício de uma DFP pela data de referência (a mesma convenção da base do estudo 1)."""
    return (date.fromisoformat(dt_refer) if isinstance(dt_refer, str) else dt_refer).year


def liberado(exercicio: int) -> bool:
    return int(exercicio) <= ULTIMO_EXERCICIO_LIBERADO


def garantir_liberado(exercicio: int) -> int:
    if not liberado(exercicio):
        raise ExercicioLacrado(int(exercicio))
    return int(exercicio)


def so_liberados(tabela: pd.DataFrame, coluna: str = "exercicio") -> pd.DataFrame:
    """Linhas de exercícios liberados. Para ler dados brutos antes de qualquer cálculo."""
    return tabela[pd.to_numeric(tabela[coluna], errors="coerce") <= ULTIMO_EXERCICIO_LIBERADO]


def garantir_data_referencia(data: str | date) -> date:
    """Data de referência dentro do intervalo decidido; fora dele, a consulta é recusada com o motivo."""
    d = date.fromisoformat(data) if isinstance(data, str) else data
    if not DATA_REFERENCIA_MINIMA <= d <= DATA_REFERENCIA_MAXIMA:
        raise DataForaDoIntervalo(d)
    return d
