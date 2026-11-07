"""Fim do estudo: emenda 11, valores neutros, secundária da emenda 5, duas leituras, ficha e análise descritiva.

Tabelas sintéticas pequenas, sem rede e sem dados reais.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from chiocca import americanas, descritiva, emenda5, ficha, robustez, variaveis
from chiocca import metricas as mt
from chiocca.sinais.mscore import COEFICIENTES

NF, FIN = "nao_financeira", "financeira"


def _linha(cd: str, ano: int, alerta: bool | None, **extra: object) -> dict:
    comps = {c: 1.0 for c in COEFICIENTES} | {"TATA": 0.0}
    base: dict = {
        "cd_cvm": cd, "exercicio": ano, "dt_refer": f"{ano}-12-31", "dt_receb": f"{ano + 1}-03-15",
        "data_corte": f"{ano + 1}-04-30", "amostra": NF, "alerta_mscore": str(bool(alerta)), "alerta_dpo": "False",
        "alerta_juro": "False", "alerta_peso_nao_recorrente": "", "alerta_regra_boba": "False",
        "em_alerta": str(bool(alerta)), "avaliada": str(alerta is not None), "alavancagem": 0.5,
        "mscore": -1.0 if alerta else (None if alerta is None else -3.0), "mscore_motivo": None,
        "dpo": 1.0, "juro": 1.0, "metodo_dfc": "DFC_MI",
    }  # fmt: skip
    for c, v in comps.items():
        base[c], base[f"{c}_motivo"] = v, None
    return base | extra


def _gab(casos: list[tuple]) -> pd.DataFrame:
    return pd.DataFrame(
        casos,
        columns=["caso_id", "cd_cvm", "periodo_afetado_inicio", "periodo_afetado_fim", "data_publica",
                 "acertavel_principal", "parte_secundaria"],
    )  # fmt: skip


def test_alarmes_nas_duas_janelas_da_emenda_11() -> None:
    s = mt.prepara(pd.DataFrame([
        _linha("1", 2012, True),  # caso A: acertado só antes do período de teste
        _linha("2", 2018, True),  # caso B: acertado dentro do período de teste
        _linha("3", 2018, True), _linha("4", 2012, True), _linha("5", 2019, False),
    ]))  # fmt: skip
    gab = _gab([("a", "1", 2012, 2012, "2015-01-01", "sim", None), ("b", "2", 2018, 2018, "2020-01-01", "sim", None)])
    r = mt.avaliacao(s, gab, set(), mt.ALERTA_SINAIS, "avaliada")
    assert (r["acertados"], r["acertados_teste"]) == (2, 1)
    al = r["alarmes"]["nf"]
    assert al["teste"]["empresas_em_alerta"] == 2 and al["teste"]["alarmes_por_acerto"] == pytest.approx(1.0)  # (2−1)/1
    assert al["inteiro"]["empresas_em_alerta"] == 4 and al["inteiro"]["alarmes_por_acerto"] == pytest.approx(1.0)
    assert al["emenda_10"]["alarmes_por_acerto"] == pytest.approx(0.0)  # (2−2)/2: janelas misturadas
    assert r["alarmes"]["fin"]["teste"]["alarmes_por_acerto"] is None


def test_valores_neutros_so_para_conta_ausente_ou_denominador_zero() -> None:
    s = mt.prepara(pd.DataFrame([
        _linha("1", 2015, None, DEPI=None, DEPI_motivo="conta_ausente:depreciacao", DSRI=3.0),
        _linha("2", 2015, None, SGAI=None, SGAI_motivo="denominador_negativo:SGAI receita t"),
        _linha("3", 2015, None, DSRI=None, DSRI_motivo="divisao_por_zero:DSRI t-1"),
        _linha("4", 2015, True, amostra=FIN, em_alerta="True", avaliada="True"),
    ]))  # fmt: skip
    r = robustez.neutros(s).set_index("cd_cvm")
    esperado = -4.84 + sum(v for c, v in COEFICIENTES.items() if c != "TATA") + 2 * COEFICIENTES["DSRI"]  # DSRI = 3
    assert r.loc["1", "mscore_neutro"] == pytest.approx(esperado) and bool(r.loc["1", "usou_neutro"])
    assert bool(r.loc["1", "alerta_mscore_neutro"]) and bool(r.loc["1", "em_alerta_neutro"])
    assert pd.isna(r.loc["2", "mscore_neutro"])  # receita negativa não recebe valor neutro
    assert pd.isna(r.loc["3", "mscore_neutro"])  # DSRI não tem valor neutro no artigo de 1999
    assert bool(r.loc["4", "em_alerta_neutro"]) and pd.isna(r.loc["4", "mscore_neutro"])  # financeira como estava


def test_juro_por_ano() -> None:
    s = mt.prepara(pd.DataFrame([
        _linha("1", 2015, False, alerta_juro="True", em_alerta="True"),  # só pelo juro
        _linha("2", 2015, True),  # pelo M
        _linha("3", 2020, False, alerta_juro="True", alerta_dpo="True", em_alerta="True"),
        _linha("4", 2020, False),
    ]))  # fmt: skip
    j = descritiva.juro_por_ano(s)
    assert j["por_ano"]["2015"] == {"avaliada": 2, "em_alerta": 2, "so_juro": 1, "sem_juro": 1, "juro": 1}
    assert j["depois"] == {"avaliada": 2, "em_alerta": 1, "so_juro": 0, "sem_juro": 1}


def test_casos_sem_m_por_falta_do_depi() -> None:
    s = mt.prepara(pd.DataFrame([
        _linha("1", 2014, False, mscore=None, mscore_motivo="componente_nao_calculavel:DEPI", DEPI=None,
               DEPI_motivo="conta_ausente:depreciacao", alerta_dpo="True", em_alerta="True", metodo_dfc="DFC_MD",
               DSRI=3.0),
        _linha("2", 2014, False),
    ]))  # fmt: skip
    gab = _gab([("a", "1", 2014, 2014, "2016-01-01", "sim", None), ("b", "2", 2014, 2014, "2016-01-01", "sim", None)])
    d = descritiva.depi(s, robustez.neutros(s), gab)
    assert d["amostra"] == {"m_nao_calculavel": 1, "com_depi": 1, "so_depi": 1, "so_depi_dfc_md": 1}
    assert [c["caso_id"] for c in d["casos"]] == ["a"]
    c = d["casos"][0]
    assert c["so_depi"] and c["dfc_md"] and c["acertado"] and c["alerta_m_neutro"]


def _dados_ficha(amostra: str = NF) -> dict:
    s = pd.DataFrame([_linha("20", 2021, True, juro_implicito=0.15, cdi_medio=0.045, lucro_sem_caixa=0.04,
                             lucro_sem_caixa_motivo=None, dpo_motivo=None, juro_motivo=None, amostra=amostra,
                             peso_nao_recorrente=0.2, peso_nao_recorrente_motivo=None)])  # fmt: skip
    meta = pd.DataFrame(
        [
            {
                "cd_cvm": "20",
                "exercicio": 2021,
                "denominacao": "EMPRESA FICTICIA S.A.",
                "tipo": "con",
                "versao": 1.0,
                "dt_receb": "2022-02-24",
                "data_corte": "2022-04-30",
                "num_doc": "999",
            }
        ]
    )
    lim = pd.DataFrame(
        [
            {"exercicio": 2021, "grupo": NF, "sinal": "dpo", "n": 10, "limite_p90": 30.0},
            {"exercicio": 2021, "grupo": FIN, "sinal": "peso_nao_recorrente", "n": 10, "limite_p90": 1.0},
        ]
    )
    return ficha.dados_ficha("20", 2021, s, meta, lim)  # fmt: skip


@pytest.mark.parametrize("lang", ["pt", "en"])
def test_ficha_de_alerta(lang: str) -> None:
    texto = ficha.texto(_dados_ficha(), lang)
    assert texto.rstrip().endswith(ficha.FRASE[lang])
    assert "NumeroSequencialDocumento=999" in texto
    assert ("Sinais que dispararam: M-score." if lang == "pt" else "Signals that fired: M-score.") in texto
    assert "1.01.03" in texto and "3.06.02" in texto  # conta de origem de cada componente
    assert "fraud" not in texto.lower() and "suspeit" not in texto.lower() and "suspect" not in texto.lower()


def test_ficha_de_financeira() -> None:
    texto = ficha.texto(_dados_ficha(FIN), "pt")
    assert "Peso não recorrente: 0,200" in texto and "≥ 1,000" in texto


def test_base_estendida_da_emenda_5(tmp_path: Path) -> None:
    base_dir, pasta = tmp_path / "base", tmp_path / "e5"
    base_dir.mkdir()
    cols = ["cd_cvm", "dt_refer", "demonstracao", "ordem", "cd_conta", "ds_conta", "valor"]
    for ano in emenda5.ANOS:
        pd.DataFrame([("1", f"{ano}-12-31", "BPA", "ÚLTIMO", "1", "Ativo Total", 10.0)], columns=cols).to_csv(
            base_dir / f"contas_{ano}.csv.gz", index=False
        )
    meta = pd.DataFrame([{"cd_cvm": "1", "dt_refer": "2015-12-31", "exercicio": 2015, "status": "ok"},
                         {"cd_cvm": "2", "dt_refer": "2015-12-31", "exercicio": 2015,
                          "status": "versao_da_epoca_indisponivel_individual"}])  # fmt: skip
    extra_meta = pd.DataFrame([{"cd_cvm": "2", "dt_refer": "2015-12-31", "exercicio": 2015, "status": "ok"}])
    extra_contas = pd.DataFrame([("2", "2015-12-31", "BPA", "ÚLTIMO", "1", "Ativo Total", 20.0)], columns=cols)
    est = emenda5.monta_base_estendida(meta, extra_meta, extra_contas, base_dir, pasta)
    assert sorted(zip(est.cd_cvm, est.status)) == [("1", "ok"), ("2", "ok")]
    c = pd.read_csv(pasta / "contas_2015.csv.gz", dtype={"cd_cvm": str})
    assert sorted(c.cd_cvm) == ["1", "2"]


def test_leitura_reapresentada_troca_so_o_ano_t() -> None:
    linhas = [("DRE", o, "3.01", "Receita", v) for o, v in (("ÚLTIMO", 100.0), ("PENÚLTIMO", 80.0))]
    c = pd.DataFrame(linhas, columns=["demonstracao", "ordem", "cd_conta", "ds_conta", "valor"])
    t = americanas._ordem(c, variaveis.PENULTIMO, variaveis.ULTIMO)
    assert list(t.ordem) == ["ÚLTIMO"] and list(t.valor) == [80.0]
