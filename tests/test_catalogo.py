"""A fórmula do M-score no código é a do catalogo_sinais.yaml (fonte única de verdade dos sinais).

O catálogo é lido como texto para não trazer dependência além de pandas e numpy para o núcleo.
"""

from __future__ import annotations

import re
from pathlib import Path

from chiocca.sinais import mscore

CATALOGO = (Path(__file__).resolve().parents[1] / "catalogo_sinais.yaml").read_text(encoding="utf-8")


def _formula_mscore() -> str:
    bloco = CATALOGO.split("- id: mscore_beneish", 1)[1].split("- id:", 1)[0]
    m = re.search(r"formula: >\n(.*?)\n    componentes:", bloco, re.S)
    assert m, "fórmula do M-score não encontrada no catálogo"
    return re.sub(r"\s+", " ", m.group(1)).strip()


def test_coeficientes_iguais_ao_catalogo() -> None:
    formula = _formula_mscore()
    intercepto = re.search(r"M = (-?[\d.]+)", formula)
    assert intercepto and float(intercepto.group(1)) == mscore.INTERCEPTO
    termos = dict((nome, float(sinal + valor)) for sinal, valor, nome in re.findall(r"([+-]) ([\d.]+)\*(\w+)", formula))
    assert termos == mscore.COEFICIENTES


def test_sinais_mvp_do_catalogo() -> None:
    mvp = re.findall(r"- id: (\w+)\n(?:(?!- id:).)*?fase: mvp", CATALOGO, re.S)
    assert set(mvp) == {"mscore_beneish", "dpo_salto", "juro_implicito", "lucro_sem_caixa", "peso_nao_recorrente"}
