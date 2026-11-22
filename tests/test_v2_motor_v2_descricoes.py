"""Descrições sem rótulo do motor v2 (pedido de 22/11/2026): documentos gerados do JSON versionado, só agregados de
2010 a 2023, sem o gabarito, e contas pequenas conferidas à mão."""

from __future__ import annotations

import ast
import json
import math
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from chiocca.sinais import mscore as ms
from chiocca.v2 import motor_v2_descricoes as md

RAIZ = Path(__file__).resolve().parents[1]


def _d() -> dict:
    return json.loads(md.SAIDA.read_text(encoding="utf-8"))


@pytest.mark.parametrize("lang", ["pt", "en"])
def test_documento_igual_a_saida_do_script(lang: str) -> None:
    assert md.DOCS[lang].read_text(encoding="utf-8") == md.render(_d(), lang)


def test_so_agregados_de_2010_a_2023() -> None:
    d = _d()
    assert d["anos"] == [2010, 2023]
    texto = md.SAIDA.read_text(encoding="utf-8")
    assert '"cd_cvm"' not in texto and "denominacao" not in texto
    blocos = (
        d["depi_dva"]["por_ano"],
        d["subcontas_3_06_02"]["por_ano"],
        d["quantidade_de_numeros"]["mediana_por_ano"],
        d["fracao"]["nao_financeira"]["por_ano"],
        d["fracao"]["financeira"]["por_ano"],
    )
    for bloco in blocos:
        assert {int(a) for a in bloco} == set(range(2010, 2024))


def test_nao_le_o_gabarito_nem_importa_metricas_ou_o_estudo_2() -> None:
    fonte = Path(md.__file__).read_text(encoding="utf-8")
    assert "gabarito_" not in fonte and "data/gabarito" not in fonte
    importados = set()
    for no in ast.walk(ast.parse(fonte)):
        if isinstance(no, ast.ImportFrom) and no.module:
            importados |= {no.module} | {f"{no.module}.{a.name}" for a in no.names}
        elif isinstance(no, ast.Import):
            importados |= {a.name for a in no.names}
    proibidos = ("chiocca.metricas", "chiocca.v2.estudo2", "chiocca.relatorio_resultados", "chiocca.v2.gabarito")
    assert not [m for m in importados if m.startswith(proibidos)]


def test_contagens_batem_com_o_json_do_estudo_1() -> None:
    d = _d()
    r = json.loads((RAIZ / "docs/resultados_numeros.json").read_text(encoding="utf-8"))
    m = r["nao_calculaveis"]["mscore"]
    assert d["depi_dva"]["empresa_anos_nf"] == m["empresa_anos"] and d["depi_dva"]["mscore_v1"] == m["calculaveis"]
    falta = d["depi_dva"]["depi_falta_por_motivo"]
    assert falta["conta_ausente"] == r["nao_calculaveis"]["DEPI"]["motivos"]["conta_ausente:depreciacao"]
    assert d["depi_dva"]["mscore_v2"] == m["calculaveis"] + d["depi_dva"]["mscore_novo"]
    calc = d["fracao"]["nao_financeira"]["total"]["calculaveis"]
    for sinal, col in (("dpo", "alerta_dpo"), ("juro", "alerta_juro")):
        assert calc[sinal] == sum(v["calculaveis"] for v in r["por_sinal"]["nf"][col].values())
    assert calc["mscore_v2"] == d["depi_dva"]["mscore_v2"]


def test_opcao_ii_alerta_pelo_menos_10_por_cento_e_entregas_somam() -> None:
    d = _d()
    for g in ("nao_financeira", "financeira"):
        for x in d["fracao"][g]["por_ano"].values():
            assert x["ii"]["alertas"] >= math.floor(0.1 * x["avaliaveis"])
            assert x["i"]["uniao"] <= x["avaliaveis"]
    e = d["entregas_dfp_2023"]
    assert sum(w["entregas"] for w in e["semanas"]) == e["ate_o_corte"]
    assert e["ate_o_corte"] + e["depois_do_corte"] + e["antes_de_2024"] == e["companhias"]


def test_primeiro_digito_e_desvio_de_benford() -> None:
    assert md.primeiro_digito(np.array([123.0, 0.045, -9.0, 0.0, 1000.0])).tolist() == [1, 4, 9, 1]
    exata = (md.BENFORD * 1_000_000).round()
    assert md.desvio_benford(exata[None, :])[0] == pytest.approx(0, abs=1e-6)
    so_um = np.zeros((1, 9))
    so_um[0, 0] = 10
    assert md.desvio_benford(so_um)[0] == pytest.approx(np.abs(np.eye(9)[0] - md.BENFORD).mean())


def test_ajuste_por_faixa_tem_media_1_em_cada_faixa() -> None:
    n = pd.Series(range(1, 21), dtype=float)
    mad = pd.Series(np.linspace(0.01, 0.2, 20))
    adj = md.ajusta_por_faixa(mad, n, faixas=5)
    faixa = pd.qcut(n.rank(method="first"), 5, labels=False)
    assert adj.groupby(faixa).mean().tolist() == pytest.approx([1.0] * 5)


def test_depi_pela_dva_igual_ao_do_v1_com_a_mesma_depreciacao() -> None:
    t = {"depreciacao": 10.0, "imobilizado": 90.0}
    t1 = {"depreciacao": 20.0, "imobilizado": 80.0}
    assert md.depi_pela_dva(10.0, 20.0, 90.0, 80.0) == pytest.approx(ms.depi(t, t1)) == pytest.approx(2.0)
    assert math.isnan(md.depi_pela_dva(0.0, 20.0, 90.0, 80.0))  # taxa de t igual a zero: não calculável
    assert math.isnan(md.depi_pela_dva(float("nan"), 20.0, 90.0, 80.0))


def test_opcoes_numa_tabela_pequena() -> None:
    g = pd.DataFrame({"a": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10.0], "b": [10, 9, 8, 7, 6, 5, 4, 3, 2, np.nan]})
    x = md.opcoes(g, ("a", "b"))
    assert x["avaliaveis"] == 10 and x["calculaveis"] == {"a": 10, "b": 9}
    assert x["i"]["por_sinal"] == {"a": 1, "b": 1} and x["i"]["uniao"] == 2 and x["i"]["pares"] == {"a+b": 0}
    # (ii): o maior percentil de cada linha; a primeira linha (b no topo) e a décima (a no topo) empatam em 1,0
    assert x["ii"]["alertas"] == 2 and x["ii"]["sinal_no_maximo"] == {"a": 1, "b": 1}
