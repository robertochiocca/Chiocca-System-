"""Métricas da avaliação (seções 5 a 8 e emendas 1, 3, 8, 9 e 10) numa tabela sintética de sinais."""

from __future__ import annotations

import pandas as pd
import pytest

from chiocca import metricas as mt

NF, FIN = "nao_financeira", "financeira"


def _linha(cd: str, ano: int, alerta: bool | None, boba: bool = False, amostra: str = NF, **extra: object) -> dict:
    base: dict = {
        "cd_cvm": cd,
        "exercicio": ano,
        "dt_refer": f"{ano}-12-31",
        "dt_receb": f"{ano + 1}-03-15",
        "data_corte": f"{ano + 1}-04-30",
        "amostra": amostra,
        "alerta_mscore": "" if alerta is None else str(alerta),
        "alerta_dpo": "",
        "alerta_juro": "",
        "alerta_peso_nao_recorrente": "",
        "alerta_regra_boba": str(boba),
        "em_alerta": str(bool(alerta)),
        "avaliada": str(alerta is not None),
        "alavancagem": 0.5,
        "mscore": 0.0 if alerta else (None if alerta is None else -3.0),
        "mscore_motivo": None if alerta is not None else "componente_nao_calculavel:DEPI,SGI",
    }
    return base | extra


@pytest.fixture
def s() -> pd.DataFrame:
    linhas = [
        _linha("1", 2014, True),  # caso: alerta no período, antes da data
        _linha("1", 2015, False, dt_receb="2016-05-20"),  # entregue depois da data pública
        _linha("1", 2018, True),
        _linha("2", 2018, True),
        _linha("2", 2019, True),  # mesma empresa, conta uma vez
        _linha("3", 2018, False, boba=True),
        _linha("4", 2016, True),  # fora do período de teste
        _linha("5", 2020, True),  # empresa em observação
        _linha("6", 2018, None),  # nada calculável: não avaliada
        _linha("7", 2018, True, amostra=FIN),
        _linha("8", 2013, False, amostra="fora_sem_receita"),
    ]
    return mt.prepara(pd.DataFrame(linhas))


def test_acerto_usa_so_dados_antes_da_data(s: pd.DataFrame) -> None:
    r = mt.avalia_caso(s, "1", [2014, 2015], "2016-04-01")
    assert r["acertado"] and r["anos_elegiveis"] == [2014] and r["anos_em_alerta"] == [2014]
    assert r["anos_fora"] == [[2015, "depois_da_data"]]
    assert not r["acertado_boba"]
    nao = mt.avalia_caso(s, "1", [2015], "2016-04-01")
    assert not nao["acertado"] and nao["anos_elegiveis"] == []


def test_fora_da_amostra_e_sem_dfp(s: pd.DataFrame) -> None:
    r = mt.avalia_caso(s, "8", [2012, 2013], "2020-01-01")
    assert r["anos_fora"] == [[2012, "sem_dfp"], [2013, "fora_sem_receita"]] and not r["acertado"]


def test_alarmes_por_acerto_da_emenda_10(s: pd.DataFrame) -> None:
    a = mt.alarmes(s, NF, mt.ALERTA_SINAIS, "avaliada", acertados=1, fora={"5"})
    # empresas com alerta de 2017 a 2023, sem a de observação: 1, 2 → 2; (2 − 1) ÷ 1 = 1
    assert a["empresas_em_alerta"] == 2 and a["empresas_avaliadas"] == 3
    assert a["alarmes_por_acerto"] == pytest.approx(1.0)
    assert mt.alarmes(s, NF, mt.ALERTA_SINAIS, "avaliada", 0, set())["alarmes_por_acerto"] is None
    boba = mt.alarmes(s, NF, mt.ALERTA_BOBA, "boba_avaliada", acertados=1, fora={"5"})
    assert boba["empresas_em_alerta"] == 1 and boba["empresas_avaliadas"] == 4


def test_taxa_por_ano(s: pd.DataFrame) -> None:
    t = mt.taxa_por_ano(s, NF, mt.ALERTA_SINAIS, "avaliada")
    assert t["2018"] == {"amostra": 4, "avaliadas": 3, "em_alerta": 2}
    assert mt.taxa_por_ano(s, FIN, mt.ALERTA_SINAIS, "avaliada")["2018"]["em_alerta"] == 1


def test_emenda_3_ultima_dfp_antes_da_data(s: pd.DataFrame) -> None:
    assert mt.emenda_3(s, "1", "2016-04-01") == {"exercicio": 2014, "em_alerta": True, "alerta_boba": False}
    assert mt.emenda_3(s, "1", "2010-01-01")["exercicio"] is None


def test_nao_calculaveis_conta_cada_componente(s: pd.DataFrame) -> None:
    nc = mt.nao_calculaveis(s.assign(**{c: None for c in ["DSRI", "GMI", "AQI", "SGI", "DEPI", "SGAI", "TATA",
                                                          "LVGI", "dpo", "juro", "lucro_sem_caixa",
                                                          "peso_nao_recorrente"]},
                                     **{f"{c}_motivo": None for c in ["DSRI", "GMI", "AQI", "SGI", "DEPI", "SGAI",
                                                                      "TATA", "LVGI", "dpo", "juro",
                                                                      "lucro_sem_caixa", "peso_nao_recorrente",
                                                                      "alavancagem"]}))  # fmt: skip
    assert nc["mscore"]["nao_calculaveis"] == 1
    assert nc["mscore"]["motivos"] == {"componente:DEPI": 1, "componente:SGI": 1}


def test_observacao(s: pd.DataFrame) -> None:
    o = mt.observacao(s, "5", [], "2022-01-01")
    assert o["anos_em_alerta"] == [2020] and o["anos_na_amostra"] == [2020]


def test_anos_do_periodo() -> None:
    assert mt.anos_do_periodo(2007, 2011) == [2010, 2011]
    assert mt.anos_do_periodo(None, None) == []
