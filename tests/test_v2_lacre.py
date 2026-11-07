"""Lacre dos exercícios de 2024 em diante (v2, regra 2): nada acima de ULTIMO_EXERCICIO_LIBERADO é calculado."""

from __future__ import annotations

import pandas as pd
import pytest

from chiocca import sinais_amostra
from chiocca.v2 import lacre


def test_limite_padrao_e_2023() -> None:
    assert lacre.ULTIMO_EXERCICIO_LIBERADO == 2023


def test_exercicio_acima_do_lacre_e_recusado() -> None:
    assert lacre.garantir_liberado(2023) == 2023
    for ano in (2024, 2025, 2030):
        with pytest.raises(lacre.ExercicioLacrado):
            lacre.garantir_liberado(ano)
    assert not lacre.liberado(2024) and lacre.liberado(2010)


def test_filtro_tira_exercicios_lacrados() -> None:
    t = pd.DataFrame({"exercicio": [2022, 2023, 2024, 2025], "valor": [1, 2, 3, 4]})
    assert list(lacre.so_liberados(t).exercicio) == [2022, 2023]


def test_exercicio_pela_data_de_referencia() -> None:
    assert lacre.exercicio_de("2023-12-31") == 2023 and lacre.exercicio_de("2024-06-30") == 2024


def test_motor_v1_nao_calcula_acima_do_lacre() -> None:
    # O cálculo da amostra do estudo 1, que o produto reaproveita, para em 2023.
    assert max(sinais_amostra.ANOS) <= lacre.ULTIMO_EXERCICIO_LIBERADO
