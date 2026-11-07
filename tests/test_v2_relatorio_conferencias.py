"""Relatório agregado das conferências (Fase B do v2): por script, mesmos números em PT e EN, lacre respeitado."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pytest

from chiocca.v2 import relatorio_conferencias as rc
from tests.test_v2_docs import numeros
from tests.test_v2_motor_confianca import _empresa


@pytest.mark.parametrize("lang", ["pt", "en"])
def test_documento_igual_a_saida_do_script(lang: str) -> None:
    n = json.loads(rc.NUMEROS.read_text(encoding="utf-8"))
    assert rc.DOCS[lang].read_text(encoding="utf-8") == rc.render(n, lang)


def test_mesmos_numeros_nos_dois_idiomas() -> None:
    pt, en = rc.DOCS["pt"].read_text(encoding="utf-8"), rc.DOCS["en"].read_text(encoding="utf-8")
    assert numeros(pt, "pt") == numeros(en, "en")


def test_calculo_numa_base_sintetica_e_lacre(tmp_path: Path) -> None:
    boa = _empresa().assign(cd_cvm="1", dt_refer="2020-12-31")
    ruim = _empresa(**{"2@ÚLTIMO": 1500.0e6}).assign(cd_cvm="2", dt_refer="2020-12-31")
    pd.concat([boa, ruim]).to_csv(tmp_path / "contas_2020.csv.gz", index=False)
    meta = pd.DataFrame(
        [
            ("1", 2020, "2020-12-31", "ok", "nao_financeiro", "dados_abertos"),
            ("2", 2020, "2020-12-31", "ok", "nao_financeiro", "enet"),
            ("3", 2024, "2024-12-31", "ok", "nao_financeiro", "dados_abertos"),  # lacrado: contas_2024 nem existe
        ],
        columns=["cd_cvm", "exercicio", "dt_refer", "status", "plano", "fonte"],
    )
    n = rc.calcula(meta, tmp_path)
    assert n["empresa_anos"] == 2 and n["ultimo_exercicio"] == 2023
    x = n["conferencias"]["ativo_igual_passivo"]["colunas"]["ÚLTIMO"]
    assert (x["aplicaveis"], x["falhas"], x["falhas_por_origem"]) == (2, 1, {"enet": 1})
    assert x["faixas"]["acima_10"] == 1  # 1.500 contra 1.000
    assert n["empresa_anos_com_falha"]["identidade"] == 1
    assert n["por_ano"] == {"2020": {"empresa_anos": 2, "com_falha_de_identidade": 1}}
