"""Quais exercícios o script do estudo 2 pode ler (pré-registro do estudo 2, seção 9).

O produto continua com o lacre de `chiocca.v2.lacre` (`ULTIMO_EXERCICIO_LIBERADO` e a data máxima não mudam). O script
do estudo lê, além dos exercícios liberados, só:
- os exercícios que o commit de abertura puser em `lacre.ESTUDO_2_EXERCICIOS` (por exemplo, `(2024, 2025)`);
- na avaliação secundária, a DFP seguinte que a segunda abertura puser em `lacre.ESTUDO_2_SEGUNDA_ABERTURA` (por
  exemplo, `(2026,)`), só para o comparativo do exercício anterior.

Antes da abertura, as duas constantes não existem, e todo exercício acima de `ULTIMO_EXERCICIO_LIBERADO` é recusado
antes de qualquer leitura. As constantes entram no fim de `chiocca/v2/lacre.py`, num bloco próprio entre as linhas
`MARCA_INICIO` e `MARCA_FIM`; o registro de SHA-256 do código (`chiocca.v2.estudo2.registro`) confere o resto do
arquivo, que não pode mudar.
"""

from __future__ import annotations

from chiocca.v2 import lacre

MARCA_INICIO = "# >>> estudo 2: abertura do lacre, só para o script do estudo (pré-registro do estudo 2, seção 9)"
MARCA_FIM = "# <<< estudo 2"
CONSTANTE = "ESTUDO_2_EXERCICIOS"
CONSTANTE_SEGUNDA = "ESTUDO_2_SEGUNDA_ABERTURA"


def exercicios_do_estudo() -> tuple[int, ...]:
    """Os exercícios abertos só para o estudo; vazio antes do commit de abertura."""
    return tuple(int(a) for a in getattr(lacre, CONSTANTE, ()))


def segunda_abertura() -> tuple[int, ...]:
    """As DFP seguintes abertas só para o comparativo da avaliação secundária; vazio antes da segunda abertura."""
    return tuple(int(a) for a in getattr(lacre, CONSTANTE_SEGUNDA, ()))


def garantir_exercicio(exercicio: int) -> int:
    """Exercício que o cálculo da lista pode ler; senão, `ExercicioLacrado` antes de qualquer leitura."""
    if lacre.liberado(exercicio) or int(exercicio) in exercicios_do_estudo():
        return int(exercicio)
    raise lacre.ExercicioLacrado(int(exercicio))


def garantir_seguinte(exercicio_seguinte: int) -> int:
    """DFP de t+1 que a avaliação secundária pode ler, só pelo comparativo de t."""
    if int(exercicio_seguinte) in segunda_abertura():
        return int(exercicio_seguinte)
    return garantir_exercicio(exercicio_seguinte)


def sem_o_bloco_da_abertura(texto: str) -> str:
    """O texto de `chiocca/v2/lacre.py` sem o bloco do estudo (as linhas entre as marcas, inclusive)."""
    linhas = texto.splitlines(keepends=True)
    if not any(x.rstrip("\n") == MARCA_INICIO for x in linhas):
        return texto
    inicio = next(i for i, x in enumerate(linhas) if x.rstrip("\n") == MARCA_INICIO)
    fim = next(i for i, x in enumerate(linhas) if i > inicio and x.rstrip("\n") == MARCA_FIM)
    antes = linhas[:inicio]
    while antes and not antes[-1].strip():  # as linhas em branco que o formatador põe antes do bloco
        antes.pop()
    return "".join(antes + linhas[fim + 1 :])
