"""Quais exercícios o script do motor v2 pode ler (emenda 5 do estudo 2, item 4).

O produto continua com o lacre de `chiocca.v2.lacre` (`ULTIMO_EXERCICIO_LIBERADO` e a data máxima não mudam). O código
do v2 lê, além dos exercícios liberados, só os que o commit da sessão do lacre da lista do v2 puser numa constante
própria, `CONSTANTE`, no bloco do estudo no fim de `chiocca/v2/lacre.py` (o bloco fica fora do hash do registro do v1).

Antes dessa sessão, a constante não existe, e todo exercício acima de `ULTIMO_EXERCICIO_LIBERADO` é recusado antes de
qualquer leitura. A constante da lista do v1 não vale para o v2.
"""

from __future__ import annotations

from chiocca.v2 import lacre

CONSTANTE = "ESTUDO_2_MOTOR_V2_EXERCICIOS"


def exercicios_do_v2() -> tuple[int, ...]:
    """Os exercícios abertos só para o script do v2; vazio antes do commit da sessão do lacre da lista do v2."""
    return tuple(int(a) for a in getattr(lacre, CONSTANTE, ()))


def garantir_exercicio(exercicio: int) -> int:
    """Exercício que o código do v2 pode ler; senão, `ExercicioLacrado` antes de qualquer leitura."""
    if lacre.liberado(exercicio) or int(exercicio) in exercicios_do_v2():
        return int(exercicio)
    raise lacre.ExercicioLacrado(int(exercicio))
