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
    # Caixa amplo coerente: saldos da DFC (130 e 90) = caixa + aplicações financeiras nos dois balanços.
    amplo = _empresa(**{"6.05.02@ÚLTIMO": 130.0e6, "6.05.01@ÚLTIMO": 90.0e6}).assign(cd_cvm="4", dt_refer="2020-12-31")
    aplicacoes = pd.DataFrame([("BPA", o, "1.01.02", "Aplicações Financeiras", 30.0e6, "4", "2020-12-31")
                               for o in ("ÚLTIMO", "PENÚLTIMO")], columns=amplo.columns)  # fmt: skip
    amplo = pd.concat([amplo, aplicacoes])
    pd.concat([boa, ruim, amplo]).to_csv(tmp_path / "contas_2020.csv.gz", index=False)
    meta = pd.DataFrame(
        [
            ("1", 2020, "2020-12-31", "ok", "nao_financeiro", "dados_abertos"),
            ("2", 2020, "2020-12-31", "ok", "nao_financeiro", "enet"),
            ("3", 2024, "2024-12-31", "ok", "nao_financeiro", "dados_abertos"),  # lacrado: contas_2024 nem existe
            ("4", 2020, "2020-12-31", "ok", "nao_financeiro", "dados_abertos"),
        ],
        columns=["cd_cvm", "exercicio", "dt_refer", "status", "plano", "fonte"],
    ).assign(versao=1, ultima_versao=1, dt_receb="2021-03-01", tipo="con")
    n, identidades = rc.calcula(meta, tmp_path)
    assert n["empresa_anos"] == 3 and n["ultimo_exercicio"] == 2023
    x = n["conferencias"]["ativo_igual_passivo"]["colunas"]["ÚLTIMO"]
    assert (x["aplicaveis"], x["falhas"], x["falhas_por_origem"]) == (3, 1, {"enet": 1})
    assert x["faixas"]["acima_10"] == 1  # 1.500 contra 1.000
    caixa = n["conferencias"]["dfc_saldo_final_no_balanco"]["colunas"]["ÚLTIMO"]
    assert (caixa["falhas"], caixa["caixa_amplo"]) == (0, 1)  # fecha com caixa amplo: não é falha
    assert n["com_falha_antes"]["reconciliacao"] == 1 and n["com_falha_depois"].get("reconciliacao", 0) == 0
    assert n["com_falha_depois"]["identidade"] == 1
    assert n["por_ano"] == {"2020": {"empresa_anos": 3, "com_falha_de_identidade": 1}}
    assert [(r["cd_cvm"], r["conferencias"]) for r in identidades] == [("2", "ativo_igual_passivo;passivo_partes")]
    inv = rc.investiga_identidades(
        identidades, tmp_path, tmp_path / "sem_brutos", tmp_path / "x.csv", tmp_path / "y.csv"
    )
    assert inv["empresa_anos"] == 1 and inv["primeira_versao"] == 1 and inv["causa"] == "nao_determinada"
