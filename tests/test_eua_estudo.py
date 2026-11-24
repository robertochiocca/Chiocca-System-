"""O código do estudo dos EUA (pré-registro dos EUA, seções 2 a 7 e 10), testado só em dados sintéticos e no exemplo
calculado à mão (`data/exemplo_eua.json`). Nenhum teste lê os arquivos da SEC: nenhum sinal é calculado sobre dados
reais antes do congelamento e da autorização de Roberto.
"""

from __future__ import annotations

import json
import math
import zipfile
from datetime import date, timedelta
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import pytest

from chiocca.base import RAIZ
from chiocca.eua import estudo, fsds, mapa
from chiocca.sinais import mscore
from chiocca.v2.estudo2 import secundaria

EXEMPLO = RAIZ / "data" / "exemplo_eua.json"
TOLERANCIA = 1e-9


def _ex() -> dict[str, Any]:
    return json.loads(EXEMPLO.read_text(encoding="utf-8"))


def _tabelas(ex: dict[str, Any]) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    e = ex["entradas"]
    return (pd.DataFrame(e["sub"], columns=e["colunas_sub"]), pd.DataFrame(e["num"], columns=e["colunas_num"]),
            pd.DataFrame(e["pre"], columns=e["colunas_pre"]))  # fmt: skip


def _taxa(ex: dict[str, Any], pasta: Path) -> Path:
    """A taxa fictícia do exemplo no formato de `data/eua_dff.csv`."""
    t = ex["entradas"]["taxa"]
    dias, d = [], date.fromisoformat(t["de"])
    while d <= date.fromisoformat(t["ate"]):
        dias.append((d.isoformat(), t["valor"]))
        d += timedelta(days=1)
    dias = sorted(dias + [(x, v) for x, v in t["fora_da_janela"]])
    caminho = pasta / "taxa.csv"
    caminho.write_text("data,valor\n" + "".join(f"{x},{v}\n" for x, v in dias), encoding="utf-8")
    return caminho


def _vazio(x: Any) -> bool:
    return x is None or x is pd.NA or (isinstance(x, float) and math.isnan(x))


def _igual(obtido: Any, esperado: Any, onde: str) -> None:
    if esperado is None:
        assert _vazio(obtido), (onde, obtido)
    elif isinstance(esperado, bool):
        assert not _vazio(obtido) and bool(obtido) is esperado, (onde, obtido, esperado)
    elif isinstance(esperado, (int, float)):
        assert not _vazio(obtido) and abs(float(obtido) - esperado) <= TOLERANCIA, (onde, obtido, esperado)
    elif isinstance(esperado, dict):
        assert set(obtido) == set(esperado), (onde, sorted(obtido), sorted(esperado))
        for k in esperado:
            _igual(obtido[k], esperado[k], f"{onde}.{k}")
    elif isinstance(esperado, list):
        assert len(obtido) == len(esperado), (onde, obtido, esperado)
        for i, (a, b) in enumerate(zip(obtido, esperado)):
            _igual(a, b, f"{onde}[{i}]")
    else:
        assert obtido == esperado, (onde, obtido, esperado)


def _calcula_exemplo(tmp_path: Path) -> tuple[dict[str, Any], estudo.EmpresaAnos, pd.DataFrame, pd.DataFrame]:
    ex = _ex()
    sub, num, pre = _tabelas(ex)
    ea = estudo.empresa_anos(estudo.extrai(estudo.do_exercicio(sub), num, pre), _taxa(ex, tmp_path))
    s, limites = estudo.motores(ea)
    return ex, ea, s, limites


# ---- o mapa: as listas do texto registrado ----


def test_listas_do_mapa_sao_as_do_texto_registrado() -> None:
    texto = (RAIZ / "docs" / "pre-registro-eua.md").read_text(encoding="utf-8")

    def em_ordem(tags: tuple[str, ...]) -> str:
        return ", ".join(f"`{t}`" for t in tags)

    assert f"**A lista final da receita, nesta ordem de preferência: {em_ordem(mapa.RECEITA)}.**" in texto
    assert em_ordem(mapa.JUROS[:3]) + ", `InterestAndDebtExpense` (*), nessa ordem" in texto
    assert em_ordem(mapa.FLUXO["caixa_operacional"]) + ", nessa ordem" in texto
    assert mapa.RECEITA[:3] == fsds.MAPA["receita_liquida"] and set(mapa.RECEITA[3:]) <= set(fsds.RECEITA_CANDIDATAS)
    juros = fsds.AMPLIACOES["despesas_financeiras"]
    assert mapa.JUROS[:1] == juros["base"] and set(mapa.JUROS[1:]) <= set(juros["candidatas"])
    assert mapa.JUROS_LARGO <= set(fsds.CONCEITO_LARGO) and mapa.FORNECEDORES == fsds.MAPA["fornecedores"]
    for nome in ("ativo_total", "ativo_circulante", "contas_a_receber", "imobilizado", "passivo_circulante",
                 "patrimonio_liquido", "emprestimos_lp"):  # fmt: skip
        assert mapa.SALDO[nome] == fsds.MAPA[nome], nome
    for nome in ("depreciacao", "lucro_liquido"):
        assert mapa.FLUXO[nome] == fsds.MAPA[nome], nome
    assert mapa.CUSTO == fsds.MAPA["custo_vendas"]


# ---- o exemplo calculado à mão, reproduzido pelo código ----


def test_reproduz_o_exemplo_calculado_a_mao(tmp_path: Path) -> None:
    ex, ea, s, limites = _calcula_exemplo(tmp_path)
    esperado = ex["esperado"]
    por_cik = {r["cd_cvm"]: r for r in s.to_dict("records")}
    assert sorted(por_cik) == sorted(r["cik"] for r in esperado["empresa_anos"])
    componentes = list(mscore.COEFICIENTES)
    for r in esperado["empresa_anos"]:
        o, cik = por_cik[r["cik"]], r["cik"]
        _igual(o["amostra"], r["situacao"], f"{cik}.situacao")
        _igual(o["versao"], r["versao_usada"], f"{cik}.versao_usada")
        if "contas_t" in r:
            d = ea.detalhe[(cik, esperado["data_de_referencia"])]
            for k in ("data_anterior", "contas_t", "contas_t1", "origem_t", "marcas"):
                _igual(d[k], r[k], f"{cik}.{k}")
        if r["situacao"] != "nao_financeira":
            assert not o["avaliada"] and not o["avaliada_v2"] and not o["em_alerta"] and not o["em_alerta_v2"]
            continue
        _igual({k: o[k] for k in componentes}, r["mscore_componentes"], f"{cik}.componentes")
        for k in ("mscore", "dpo_t", "dpo_t1", "dpo", "juro_implicito", "taxa_media", "juro", "alavancagem",
                  "n_numeros_benford", "desvio_benford", "alerta_mscore", "alerta_dpo", "alerta_juro",
                  "alerta_regra_boba", "faixa_benford", "benford", "benford_motivo", "pct_mscore", "pct_dpo",
                  "pct_juro", "pct_benford", "escore"):  # fmt: skip
            _igual(o[k], r[k], f"{cik}.{k}")
        _igual([o[f"benford_d{d}"] for d in range(1, 10)], r["benford_contagens"], f"{cik}.benford_contagens")
        _igual(o["avaliada"], r["v1_avaliada"], f"{cik}.v1_avaliada")
        _igual(o["em_alerta"], r["v1_em_alerta"], f"{cik}.v1_em_alerta")
        _igual(o["n_sinais"], r["v1_n_sinais"], f"{cik}.v1_n_sinais")
        _igual(o["avaliada_v2"], r["v2_avaliada"], f"{cik}.v2_avaliada")
        _igual(o["em_alerta_v2"], r["v2_em_alerta"], f"{cik}.v2_em_alerta")
    nf = limites[limites.grupo == "nao_financeira"]
    lim = {(m, x): v for m, x, v in zip(nf.motor, nf.sinal, nf.limite_p90)}
    _igual(lim[("v1", "dpo")], esperado["limites"]["dpo"], "limite dpo")
    _igual(lim[("v1", "alavancagem")], esperado["limites"]["alavancagem"], "limite alavancagem")
    _igual(lim[("v2", "escore")], esperado["limites"]["escore"], "limite escore")
    _igual(estudo.data_corte(esperado["data_de_referencia"]).isoformat(), esperado["data_corte"], "corte")


def test_le_o_trimestre_no_formato_da_sec(tmp_path: Path) -> None:
    """O mesmo exemplo num zip no formato dos Financial Statement Data Sets (com as colunas que o estudo não usa e
    blocos pequenos, para cruzar a divisão em blocos) dá as mesmas entregas que as tabelas em memória."""
    ex = _ex()
    sub, num, pre = _tabelas(ex)
    z = tmp_path / "2023q1.zip"
    with zipfile.ZipFile(z, "w") as f:
        f.writestr("sub.txt", sub.assign(fye="1231", accepted="").to_csv(sep="\t", index=False))
        f.writestr("num.txt", num.assign(footnote="").to_csv(sep="\t", index=False))
        f.writestr("pre.txt", pre.to_csv(sep="\t", index=False))
    lida = estudo.le_trimestre(z, bloco=97)
    direta = estudo.extrai(estudo.do_exercicio(sub), num, pre)
    assert lida.valores == direta.valores and lida.anterior == direta.anterior
    pd.testing.assert_frame_equal(lida.benford.reset_index(drop=True), direta.benford.reset_index(drop=True))
    with zipfile.ZipFile(tmp_path / "sem_coluna.zip", "w") as f:
        f.writestr("sub.txt", sub.to_csv(sep="\t", index=False))
        f.writestr("num.txt", num.drop(columns="segments").to_csv(sep="\t", index=False))
        f.writestr("pre.txt", pre.to_csv(sep="\t", index=False))
    with pytest.raises(fsds.ColunaAusente):
        estudo.le_trimestre(tmp_path / "sem_coluna.zip")


# ---- a amostra: versão pública, exclusões e ordem de entrada ----


def _entregas(linhas: list[tuple[str, str, str, str, str, str]], com_numeros: set[str]) -> estudo.Entregas:
    sub = pd.DataFrame(linhas, columns=estudo.COLUNAS_SUB)
    valores = {a: {("Assets", p, "0"): 1.0} for a, p in zip(sub.adsh, sub.period) if a in com_numeros}
    return estudo.Entregas(sub=sub, valores=valores)


def test_versao_publica_no_corte_e_exclusoes() -> None:
    e = _entregas(
        [("a1", "20", "3571", "10-K", "20221231", "20230301"),  # o original
         ("a2", "20", "6022", "10-K/A", "20221231", "20230410"),  # emenda com números até o corte: a usada (SIC dela)
         ("a3", "20", "3571", "10-K/A", "20221231", "20230420"),  # emenda sem números: não muda a versão
         ("a4", "20", "3571", "10-K/A", "20221231", "20230501"),  # depois do corte
         ("b1", "3", "6770", "10-K", "20220630", "20221030"),  # SPAC; corte em 31/10/2022
         ("c1", "100", "3571", "10-K", "20221231", "20230501"),  # entregue depois do corte
         ("c2", "100", "3571", "10-K/A", "20211231", "20220301"),  # emenda sem 10-K original: fora do universo
         ("d1", "7", "6999", "10-K", "20220930", "20221201"),
         ("d2", "7", "6999", "10-K", "20220930", "20221201"),  # no mesmo dia, o de maior número de entrega
         ("e1", "9", "", "10-K", "20221231", "20230315")],  # fmt: skip
        com_numeros={"a2", "a4"},
    )
    v = estudo.versoes(e)
    assert list(v.cd_cvm) == ["3", "7", "9", "20", "100"]  # ordem de entrada pelo CIK
    por = {r["cd_cvm"]: r for r in v.to_dict("records")}
    assert por["20"]["versao"] == "a2" and por["20"]["sic"] == "6022" and por["20"]["amostra"] == estudo.FORA_FINANCEIRA
    assert por["20"]["entregas"] == 4 and por["20"]["data_corte"] == "2023-04-30"
    assert por["3"]["amostra"] == estudo.FORA_SPAC and por["3"]["data_corte"] == "2022-10-31"
    assert por["100"]["amostra"] == estudo.FORA_SEM_VERSAO and pd.isna(por["100"]["versao"])
    assert por["7"]["versao"] == "d2" and por["7"]["amostra"] == estudo.FORA_FINANCEIRA
    assert pd.isna(por["9"]["amostra"]) and por["9"]["versao"] == "e1"
    assert estudo.financeira("6000") and estudo.financeira("6999") and not estudo.financeira("6770")
    assert not estudo.financeira("5999") and not estudo.financeira("7000") and not estudo.financeira("")


def test_so_os_exercicios_do_estudo() -> None:
    sub = pd.DataFrame(
        [("x1", "1", "1", "10-K", "20081231", "1"), ("x2", "1", "1", "10-K", "20091231", "1"),
         ("x3", "1", "1", "10-K", "20241231", "1"), ("x4", "1", "1", "10-K", "20250131", "1"),
         ("x5", "1", "1", "10-Q", "20221231", "1"), ("x6", "1", "1", "10-KT", "20221231", "1")],
        columns=estudo.COLUNAS_SUB,
    )  # fmt: skip
    assert list(estudo.do_exercicio(sub).adsh) == ["x2", "x3"]
    assert list(estudo.do_exercicio(sub, estudo.EXERCICIOS).adsh) == ["x3"]
    assert (estudo.EXERCICIOS.start, estudo.EXERCICIOS.stop - 1) == (2011, 2024)


# ---- o mapa, regra por regra, em linhas sintéticas ----


def _num(*linhas: tuple[str, ...]) -> pd.DataFrame:
    return pd.DataFrame([("a", *x) for x in linhas], columns=mapa.COLUNAS_NUM)


def test_valor_so_da_companhia_em_dolar_us_gaap_e_o_primeiro() -> None:
    num = _num(
        ("Assets", "us-gaap/2022", "20221231", "0", "USD", "", "SUB", "9"),  # co-registrante
        ("Assets", "us-gaap/2022", "20221231", "0", "USD", "Axis=X", "", "8"),  # segmento
        ("Assets", "us-gaap/2022", "20221231", "0", "EUR", "", "", "7"),
        ("Assets", "0000000001-22", "20221231", "0", "USD", "", "", "6"),  # taxonomia da companhia
        ("Assets", "us-gaap/2022", "20221231", "0", "USD", "", "", ""),  # sem número
        ("Assets", "us-gaap/2022", "20221231", "0", "USD", "", "", "100"),
        ("Assets", "us-gaap/2022", "20221231", "0", "USD", "", "", "200"),  # o segundo não vale
        ("Revenues", "us-gaap/2022", "20221231", "1", "USD", "", "", "5"),  # trimestre
        ("Revenues", "us-gaap/2022", "20221231", "4", "USD", "", "", "50"),
    )
    v = mapa.valores_do_mapa(num)["a"]
    c, o, _ = mapa.contas(v, "20221231")
    assert c["ativo_total"] == 100 and c["receita_liquida"] == 50 and o["receita_liquida"] == "Revenues"
    assert c["contas_a_receber"] is None and c["resultado_bruto"] is None
    assert mapa.tem_numero_do_mapa(v, "20221231") and not mapa.tem_numero_do_mapa(v, "20211231")


def test_data_de_t1_mais_frequente_entre_330_e_400_dias() -> None:
    num = _num(*[("X", "v", d, "0", "USD", "", "", "1") for d in
                 ("20211231", "20211231", "20211130", "20211130", "20201231", "20221231", "20220131")])  # fmt: skip
    contagem = mapa.contagem_de_datas(num)
    assert mapa.datas_anteriores(contagem, {"a": "20221231"}) == {"a": "20211231"}  # empate: a mais recente
    assert mapa.datas_anteriores(mapa.contagem_de_datas(_num()), {"a": "20221231"}) == {"a": None}


def test_benford_so_nas_demonstracoes_e_uma_vez() -> None:
    num = _num(
        ("Assets", "us-gaap/2022", "20221231", "0", "USD", "", "", "1000"),
        ("Assets", "us-gaap/2022", "20221231", "0", "USD", "", "", "1000"),  # repetido
        ("EarningsPerShareBasic", "us-gaap/2022", "20221231", "4", "USD/shares", "", "", "2.5"),
        ("Shares", "us-gaap/2022", "20221231", "0", "shares", "", "", "3000"),  # não é dólar
        ("Other", "us-gaap/2022", "20221231", "0", "USD", "", "", "0"),  # zero
        ("Eq", "us-gaap/2022", "20221231", "4", "USD", "", "", "4000"),  # demonstração das mutações
        ("Par", "us-gaap/2022", "20221231", "0", "USD", "", "", "5000"),  # entre parênteses
        ("Assets", "us-gaap/2022", "20211231", "0", "USD", "", "", "6000"),  # outra data
        ("Custom", "a", "20221231", "0", "USD", "", "", "7000"),
    )
    pre = pd.DataFrame(
        [("a", "2", "1", "BS", "0", "H", "Assets", "us-gaap/2022", "x", "0"),
         ("a", "4", "1", "IS", "0", "H", "Assets", "us-gaap/2022", "x", "0"),  # a mesma tag em outra demonstração
         ("a", "4", "2", "IS", "0", "H", "EarningsPerShareBasic", "us-gaap/2022", "x", "0"),
         ("a", "2", "2", "BS", "0", "H", "Shares", "us-gaap/2022", "x", "0"),
         ("a", "2", "3", "BS", "0", "H", "Other", "us-gaap/2022", "x", "0"),
         ("a", "5", "1", "EQ", "0", "H", "Eq", "us-gaap/2022", "x", "0"),
         ("a", "2", "4", "BS", "1", "H", "Par", "us-gaap/2022", "x", "0"),
         ("a", "6", "1", "CF", "0", "H", "Custom", "a", "x", "0")],
        columns=mapa.COLUNAS_PRE,
    )  # fmt: skip
    b = mapa.numeros_do_benford(num, pre, {"a": "20221231"})
    assert list(zip(b.demonstracao, b.valor)) == [("BPA", 1000.0), ("DRE", 2.5), ("DFC_MI", 7000.0)]


# ---- o desfecho: episódios e janelas ----


def test_episodios_de_365_dias() -> None:
    ep = estudo.episodios({"5": ["2015-01-10", "2015-06-01", "2016-01-10", "2016-01-11", "2016-03-01",
                                 "2026-04-30", "2026-05-01"], "6": []})  # fmt: skip
    assert [(x.isoformat(), n) for x, n in zip(ep.abertura, ep.dias_com_8k)] == [
        ("2015-01-10", 3), ("2016-01-11", 2), ("2026-04-30", 1)]  # fmt: skip
    assert set(ep.cd_cvm) == {"5"}


def test_janela_de_12_meses_e_cada_episodio_uma_vez() -> None:
    s = pd.DataFrame({"cd_cvm": ["1", "1", "2", "2"],
                      "data_corte": ["2016-04-30", "2017-04-30", "2016-04-30", "2016-09-30"]})  # fmt: skip
    ep = pd.DataFrame({"cd_cvm": ["1", "1", "1", "1", "2", "3"],
                       "abertura": [date(2016, 4, 30), date(2016, 5, 1), date(2017, 5, 1), date(2018, 4, 30),
                                    date(2016, 10, 15), date(2016, 6, 1)]})  # fmt: skip
    positiva, caiu = estudo.desfecho(s, ep)
    assert positiva.tolist() == [True, True, False, True]
    assert [None if pd.isna(x) else int(x) for x in caiu.empresa_ano] == [None, 0, 1, 1, 3, None]
    assert estudo.fim_da_janela(date(2023, 2, 28)) == date(2024, 2, 29)
    assert estudo.fim_da_janela(date(2024, 2, 29)) == date(2025, 2, 28)
    assert estudo.fim_da_janela(estudo.data_corte("2024-12-31")).isoformat() == estudo.ULTIMA_DATA_8K


def test_datas_dos_8k_so_com_o_item_402() -> None:
    linhas = [{"cik": 7, "form": "8-K", "data": "2020-01-02", "itens": "4.02,9.01"},
              {"cik": 7, "form": "8-K/A", "data": "2020-02-02", "itens": "4.02"},
              {"cik": 7, "form": "8-K", "data": "2020-03-02", "itens": "4.01"},
              {"cik": 8, "form": "10-K", "data": "2020-03-02", "itens": "4.02"}]  # fmt: skip
    assert estudo.datas_dos_8k(linhas) == {"7": ["2020-01-02", "2020-02-02"]}


# ---- as medidas, pelas funções congeladas do estudo 2 ----


def _nf_sintetico(n: int = 300, semente: int = 7) -> pd.DataFrame:
    rng = np.random.default_rng(semente)
    cd = rng.integers(1, 80, size=n).astype(str)
    v1 = rng.random(n) < 0.3
    return pd.DataFrame({"cd_cvm": cd, "exercicio": rng.integers(2011, 2025, size=n), "positiva": rng.random(n) < 0.1,
                         "em_alerta": v1, "em_alerta_v2": v1 & (rng.random(n) < 0.4),
                         "alerta_regra_boba": pd.array(rng.random(n) < 0.1, dtype="boolean"),
                         "n_sinais": v1.astype(int), "mscore": rng.normal(-2, 1, n), "escore": rng.random(n),
                         "alavancagem": rng.random(n)})  # fmt: skip


def test_medidas_pelas_funcoes_do_estudo_2() -> None:
    nf = _nf_sintetico()
    m = estudo.medidas(nf, reamostragens=200)
    y = nf.positiva.to_numpy(bool)
    for braco, col in (("v1", "em_alerta"), ("v2", "em_alerta_v2")):
        t = secundaria.taxas(nf[col].to_numpy(bool), y)
        assert m[braco]["dr"] == pytest.approx(t["dr"]) and m[braco]["em_alerta"] == t["em_alerta"]
    assert m["v2_menos_v1"]["diferenca_dr"] == pytest.approx(m["v2"]["dr"] - m["v1"]["dr"])
    assert m["v1_menos_regra_boba"]["diferenca_dr"] == pytest.approx(m["v1"]["dr"] - m["boba"]["dr"])
    assert m["semente"] == estudo.SEMENTE == 20270430 and m["reamostragens"] == 200
    assert m["companhias"] == nf.cd_cvm.nunique() and set(m["ranking"]) == {"1%", "5%", "10%"}
    assert m == estudo.medidas(nf, reamostragens=200)  # o mesmo sorteio
    b = secundaria.bootstrap_por_companhia(nf.cd_cvm.to_numpy(str),
                                           {"dr": lambda i: secundaria.dr(nf.em_alerta.to_numpy(bool)[i], y[i])},
                                           200, estudo.SEMENTE)  # fmt: skip
    assert m["v1"]["dr_limite_inferior_95"] == pytest.approx(secundaria.limite_inferior(b["dr"]))
    for x in ("v1", "v2", "boba"):
        assert m[x]["resultado"] in ("associação positiva", "sem evidência de associação")
    assert estudo.REAMOSTRAGENS == 10_000 and estudo.medidas(nf.iloc[:0]) == {"empresa_anos": 0, "companhias": 0}


# ---- os AAERs: só contagens ----


def test_aaers_so_contagens() -> None:
    firmas = pd.DataFrame({"p_aaer": ["A1", "A2", "A3", "A4"], "gvkey": ["g1", "g2", "g3", "g4"],
                           "min_year": [2010, 2012, 2008, 2015], "max_year": [2011, 2012, 2009, 2016]})  # fmt: skip
    ligacoes = pd.DataFrame({"gvkey": ["g1", "g2", "g3"], "cik": [11, 22, 33],
                             "first_date": [date(2000, 1, 1)] * 3, "last_date": [date(2030, 1, 1)] * 3})  # fmt: skip
    s = pd.DataFrame({"cd_cvm": ["11", "11", "22", "33"], "periodo": ["20101231", "20120331", "20121231", "20091231"],
                      "amostra": ["nao_financeira", "nao_financeira", "fora_financeira", "nao_financeira"],
                      "avaliada": [True, True, False, False], "em_alerta": [False, True, False, False],
                      "em_alerta_v2": [False, False, False, False],
                      "alerta_regra_boba": pd.array([True, None, None, None], dtype="boolean")})  # fmt: skip
    r = estudo.aaers(s, firmas, ligacoes)
    # A1: 2010 e 2011 (o exercício que termina em 31/03/2012 é 2011 pela Compustat); A2: financeira; A3: 2009, sem
    # sinal; A4: fora de 2009 a 2014.
    assert r == {"casos_com_anos_afetados": 3, "casos_com_empresa_ano_calculada": 3,
                 "casos_com_nao_financeira_avaliada_pelo_v1": 1, "casos_em_alerta_v1": 1, "casos_em_alerta_v2": 0,
                 "casos_em_alerta_regra_boba": 1}  # fmt: skip


# ---- o estudo inteiro no exemplo, e só agregados no resultado ----


def test_calcula_no_exemplo_so_com_agregados(tmp_path: Path) -> None:
    ex = _ex()
    sub, num, pre = _tabelas(ex)
    e = estudo.extrai(estudo.do_exercicio(sub), num, pre)
    datas = {"9000001": ["2023-04-15"], "9000008": ["2023-06-01", "2023-09-01"], "9000010": ["2024-04-30"],
             "9000011": ["2023-06-01"], "9999999": ["2023-06-01"]}  # fmt: skip
    vazio = pd.DataFrame(columns=["p_aaer", "gvkey", "min_year", "max_year"])
    lig = pd.DataFrame(columns=["gvkey", "cik", "first_date", "last_date"])
    r, s = estudo.calcula(e, datas, vazio, lig, taxa=_taxa(ex, tmp_path), reamostragens=100)
    assert r["exclusoes"] == {"empresa_anos": 20, "(1) fora_sem_versao_publica": 1, "(2) fora_financeira": 1,
                              "(3) fora_spac": 1, "(4) fora_sem_receita": 1, "(5) sem_nenhum_sinal": 0,
                              "nao_financeiras_avaliadas_v1": 16, "so_o_v2_avalia": 0}  # fmt: skip
    assert r["episodios"]["em_empresa_ano_da_amostra"] == 2 and r["episodios"]["total_ate_2026-04-30"] == 5
    assert sorted(s.cd_cvm[s.positiva]) == ["9000008", "9000010"]
    assert r["medidas"]["v1"]["em_alerta"] == {"empresa_anos": 9, "republicacoes": 2, "taxa": 2 / 9}
    assert r["medidas"]["v2"]["em_alerta"]["republicacoes"] == 2 and r["por_exercicio"]["2022"]["avaliadas_v1"] == 16
    texto = json.dumps(r, ensure_ascii=False)
    assert "900000" not in texto and "FICTICIA" not in texto  # nenhum CIK, nome ou lista por companhia


def test_calculo_unico_so_com_autorizacao(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    with pytest.raises(SystemExit, match="autorização de Roberto"):
        estudo.main([])
    existente = tmp_path / "ja.json"
    existente.write_text("{}", encoding="utf-8")
    with pytest.raises(SystemExit, match="o cálculo é único"):
        estudo.main(["--calculo-unico", "--saida", str(existente)])
    monkeypatch.setattr(estudo, "REGISTRO", tmp_path / "nao_existe.json")
    with pytest.raises(SystemExit, match="ainda não foi congelado"):
        estudo.main(["--calculo-unico", "--saida", str(tmp_path / "novo.json")])
    assert not (tmp_path / "novo.json").exists() and not estudo.SAIDA.exists()


def test_taxa_dff_versionada_no_formato_do_cdi() -> None:
    from chiocca import cdi
    from chiocca.eua import sec, taxa

    d = pd.read_csv(taxa.ARQUIVO)
    assert list(d.columns) == ["data", "valor"] and d.data.is_monotonic_increasing and d.data.is_unique
    assert d.data.iloc[0] <= "2010-01-01" and d.data.iloc[-1] >= "2024-12-31"
    linha = next(x for x in sec.le_manifesto() if x["arquivo"] == taxa.NOME_NO_MANIFESTO)
    assert linha["sha256"] == sec.sha256(taxa.ARQUIVO) and "id=DFF" in linha["url"]
    media = cdi.medio("2022-12-31", caminho=taxa.ARQUIVO)
    assert media is not None and 0 < media < 0.1
    assert taxa.converte("observation_date,DFF\n2020-01-01,1.5\n2020-01-02,.\n") == "data,valor\n2020-01-01,1.5\n"


def test_confere_o_registro_de_congelamento(tmp_path: Path) -> None:
    import hashlib
    import sys

    python = f"{sys.version_info[0]}.{sys.version_info[1]}"
    arquivo = "chiocca/eua/mapa.py"
    certo = hashlib.sha256((RAIZ / arquivo).read_bytes()).hexdigest()
    registro = tmp_path / "registro.json"

    def grava(py: str, h: str) -> None:
        r = {"python": py, "exemplo_calculado_a_mao": {}, "entradas_versionadas": {}, "codigo": {arquivo: h}}
        registro.write_text(json.dumps(r), encoding="utf-8")

    with pytest.raises(SystemExit, match="ainda não foi congelado"):
        estudo.confere_congelamento(tmp_path / "nao_existe.json")
    grava("2.7", certo)
    with pytest.raises(SystemExit, match="Python 2.7"):
        estudo.confere_congelamento(registro)
    grava(python, "0" * 64)
    with pytest.raises(SystemExit, match="mapa.py"):
        estudo.confere_congelamento(registro)
    grava(python, certo)
    estudo.confere_congelamento(registro)


def test_data_invalida_fica_fora_da_contagem_de_t1() -> None:
    contagem = pd.Series({("a", "20210231"): 9, ("a", "2021123"): 9, ("a", "20211231"): 1})
    assert mapa.datas_anteriores(contagem, {"a": "20221231"}) == {"a": "20211231"}
    assert mapa.datas_anteriores(contagem, {"a": "2022XX31"}) == {"a": None}
