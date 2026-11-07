"""Fase B do v2: validade, conferências de qualidade, linhagem e confiança, com fixtures sintéticas e sem rede."""

from __future__ import annotations

import io
import zipfile
from pathlib import Path

import pandas as pd
import pytest

from chiocca import variaveis
from chiocca.sinais import mscore
from chiocca.sinais.resultado import Resultado as ResultadoV1
from chiocca.v2 import conferencias as cf
from chiocca.v2 import confianca as cn
from chiocca.v2 import linhagem as lh
from chiocca.v2 import validade as vd

U, P = "ÚLTIMO", "PENÚLTIMO"
MI = 1_000_000.0
M = vd.Motivo("motivo", "reason")


# ----------------------------------------------------------------------------------------------- validade
def test_estados_e_invariantes() -> None:
    assert vd.Resultado.de_valor(1.5).ok
    assert vd.Resultado.indefinido(M).texto("en") == "reason"
    assert vd.Resultado.implausivel(-3.0, M).valor == -3.0
    with pytest.raises(ValueError):
        vd.Resultado(None, "ok")
    with pytest.raises(ValueError):
        vd.Resultado(1.0, "indefinido", M)
    with pytest.raises(ValueError):
        vd.Resultado(1.0, "implausivel")
    with pytest.raises(ValueError):
        vd.Resultado(float("nan"), "ok")
    with pytest.raises(ValueError):
        vd.Motivo("só português", " ")


def test_ponte_com_o_motor_v1_nao_muda_o_valor() -> None:
    r = vd.de_resultado_v1(ResultadoV1(None, "conta_ausente:fornecedores"))
    assert r.status == "indefinido" and r.codigo == "conta_ausente:fornecedores"
    assert r.texto("pt") == "conta ausente: fornecedores (2.01.02)"
    assert vd.de_resultado_v1(ResultadoV1(-0.24)).valor == -0.24
    assert vd.de_resultado_v1(ResultadoV1(-0.24), [M]).status == "implausivel"


def test_variacao_percentual_so_com_base_positiva() -> None:
    g = vd.Motivo("receita", "revenue")
    assert vd.variacao_percentual(100.0, 150.0, g).valor == pytest.approx(50.0)
    assert vd.variacao_percentual(0.0, 10.0, g).status == "indefinido"
    assert vd.variacao_percentual(-100.0, -50.0, g).status == "indefinido"


# ------------------------------------------------------------------------------------------- conferências
def _empresa(**troca: float) -> pd.DataFrame:
    """Empresa-ano fictícia em que todas as identidades fecham (valores em R$ milhões, gravados em reais)."""
    base = {
        ("BPA", "1"): 1000.0, ("BPA", "1.01"): 600.0, ("BPA", "1.01.01"): 100.0, ("BPA", "1.01.03"): 200.0,
        ("BPA", "1.01.04"): 150.0, ("BPA", "1.02"): 400.0, ("BPA", "1.02.03"): 300.0,
        ("BPP", "2"): 1000.0, ("BPP", "2.01"): 300.0, ("BPP", "2.01.02"): 80.0, ("BPP", "2.02"): 200.0,
        ("BPP", "2.03"): 500.0, ("BPP", "2.01.04"): 50.0, ("BPP", "2.02.01"): 150.0,
        ("DRE", "3.01"): 2000.0, ("DRE", "3.02"): -1200.0, ("DRE", "3.03"): 800.0, ("DRE", "3.04"): -500.0,
        ("DRE", "3.04.01"): -200.0, ("DRE", "3.04.02"): -150.0, ("DRE", "3.05"): 300.0, ("DRE", "3.06"): -50.0,
        ("DRE", "3.06.02"): -60.0, ("DRE", "3.07"): 250.0, ("DRE", "3.08"): -80.0, ("DRE", "3.09"): 170.0,
        ("DRE", "3.10"): 0.0, ("DRE", "3.11"): 170.0,
        ("DFC_MI", "6.01"): 150.0, ("DFC_MI", "6.01.01.02"): 40.0, ("DFC_MI", "6.02"): -60.0,
        ("DFC_MI", "6.03"): -50.0, ("DFC_MI", "6.04"): 0.0, ("DFC_MI", "6.05"): 40.0,
        ("DFC_MI", "6.05.01"): 60.0, ("DFC_MI", "6.05.02"): 100.0,
    }  # fmt: skip
    nomes = {"6.01.01.02": "Depreciação e Amortização"}
    linhas = []
    for (dem, cod), v in base.items():
        for ordem, k in ((U, 1.0), (P, 0.9)):
            valor = troca.get(f"{cod}@{ordem}", v * k * MI)
            linhas.append((dem, ordem, cod, nomes.get(cod, f"Conta {cod}"), valor))
    d = pd.DataFrame(linhas, columns=["demonstracao", "ordem", "cd_conta", "ds_conta", "valor"])
    # Saldo inicial da DFC de t = caixa do balanço de t−1 (reconciliação entre colunas).
    d.loc[(d.cd_conta == "1.01.01") & (d.ordem == P), "valor"] = 60.0 * MI
    # Na coluna de t−1, a DFC também fecha com esse caixa: saldo final 60, variação 36, saldo inicial 24.
    d.loc[(d.cd_conta == "6.05.02") & (d.ordem == P), "valor"] = 60.0 * MI
    d.loc[(d.cd_conta == "6.05.01") & (d.ordem == P), "valor"] = 24.0 * MI
    return d


def _por_id(confs: list[cf.Conferencia], coluna: str = U) -> dict[str, cf.Conferencia]:
    return {c.id: c for c in confs if c.coluna == coluna}


def test_empresa_coerente_passa_em_tudo() -> None:
    confs = cf.conferir(_empresa(), "nao_financeiro")
    assert not cf.falhas(confs), [(c.id, c.coluna, c.diferenca) for c in cf.falhas(confs)]
    assert all(c.resultado == "ok" for c in _por_id(confs).values())


def test_identidade_reconciliacao_e_plausibilidade_que_falham() -> None:
    troca = {"2@ÚLTIMO": 1500.0 * MI, "1.01.01@ÚLTIMO": 90.0 * MI, "3.02@ÚLTIMO": 1200.0 * MI}
    confs = _por_id(cf.conferir(_empresa(**troca), "nao_financeiro"))
    assert confs["ativo_igual_passivo"].resultado == "falhou" and confs["ativo_igual_passivo"].diferenca == -500.0 * MI
    assert confs["dfc_saldo_final_no_balanco"].resultado == "falhou"
    assert confs["dfc_saldo_final_no_balanco"].tipo == cf.RECONCILIACAO
    assert confs["sinal_dre:3.02"].resultado == "falhou"
    assert confs["dre_resultado_bruto"].resultado == "falhou"  # 2000 + 1200 ≠ 800


def test_tolerancia_de_arredondamento() -> None:
    confs = _por_id(cf.conferir(_empresa(**{"2@ÚLTIMO": 1000.0 * MI + 1500.0}), "nao_financeiro"))
    assert confs["ativo_igual_passivo"].resultado == "ok"  # 2 parcelas × R$ 1.000
    confs = _por_id(cf.conferir(_empresa(**{"2@ÚLTIMO": 1000.0 * MI + 2500.0}), "nao_financeiro"))
    assert confs["ativo_igual_passivo"].resultado == "falhou"


def test_conta_ausente_e_outro_plano_nao_se_aplicam() -> None:
    d = _empresa()
    sem_604 = d[d.cd_conta != "6.04"]
    c = _por_id(cf.conferir(sem_604, "nao_financeiro"))["dfc_soma"]
    assert c.resultado == "nao_aplicavel" and c.motivo is not None and "6.04" in c.motivo.pt  # ausente não vira zero
    banco = _por_id(cf.conferir(d, "banco"))
    assert banco["ativo_partes"].resultado == "nao_aplicavel"
    assert banco["ativo_igual_passivo"].resultado == "ok" and banco["dfc_soma"].resultado == "ok"
    assert "saldo_negativo:1.01.03" not in banco


# ----------------------------------------------------------------------------------------------- linhagem
def _doc(origem: str = "dados_abertos", tipo: str = "con") -> lh.Documento:
    return lh.Documento("DFP", "123", 2020, "2020-12-31", "555", 2, "2021-03-10", origem, tipo)


def test_linhagem_usa_o_valor_do_motor_v1_e_aponta_as_linhas() -> None:
    contas = _empresa()
    ficha = lh.ficha_v1(contas, _doc(), "nao_financeira", "2026-11-07T00:00:00Z", cdi_medio=0.10)
    t, t1 = variaveis.le_ordem(contas, U), variaveis.le_ordem(contas, P)
    m = mscore.calcula(t.valores, t1.valores)
    assert ficha.linhagens["DSRI"].valor == m.componentes["DSRI"].valor
    assert ficha.linhagens["mscore"].valor == m.m.valor
    dsri = ficha.linhagens["DSRI"]
    codigos = sorted((ficha.evidencias[i].cd_conta, ficha.evidencias[i].coluna) for i in dsri.entradas)
    assert codigos == [("1.01.03", P), ("1.01.03", U), ("3.01", P), ("3.01", U)]
    assert dict(((v, c), x) for v, c, x in dsri.valores)[("receita_liquida", U)] == 2000.0 * MI
    dep = [
        ficha.evidencias[i] for i in ficha.linhagens["DEPI"].entradas if ficha.evidencias[i].cd_conta == "6.01.01.02"
    ]
    assert {e.coluna for e in dep} == {U, P}
    assert any("amortização" in x.pt for x in ficha.linhagens["DEPI"].transformacoes)
    assert any("como apresentado" in x.pt for x in ficha.linhagens["TATA"].transformacoes)
    assert ficha.linhagens["juro"].motor.startswith("motor v1 (estudo 1)")


def test_linhagem_de_financeira() -> None:
    linhas = [("DRE", U, "3.04.05", "Outras Receitas Operacionais", 50.0),
              ("DRE", U, "3.05", "Resultado Antes dos Tributos sobre o Lucro", 100.0)]  # fmt: skip
    contas = pd.DataFrame(linhas, columns=["demonstracao", "ordem", "cd_conta", "ds_conta", "valor"])
    f = lh.ficha_v1(contas, _doc(), "financeira", "x")
    assert f.linhagens["peso_nao_recorrente"].valor == pytest.approx(0.5)
    assert len(f.linhagens["peso_nao_recorrente"].entradas) == 2


def test_localizador_acha_a_linha_nos_dados_abertos_e_no_enet(tmp_path: Path) -> None:
    brutos, cache = tmp_path / "brutos", tmp_path / "enet"
    brutos.mkdir()
    cache.mkdir()
    csv = ("CNPJ_CIA;DT_REFER;VERSAO;CD_CVM;ESCALA_MOEDA;ORDEM_EXERC;CD_CONTA;DS_CONTA;VL_CONTA\n"
           "1;2020-12-31;2;000123;MIL;ÚLTIMO;1;Ativo Total;1\n"
           "1;2020-12-31;2;000123;MIL;ÚLTIMO;1.01.03;Contas a Receber;0,2\n")  # fmt: skip
    with zipfile.ZipFile(brutos / "dfp_cia_aberta_2020.zip", "w") as z:
        z.writestr("dfp_cia_aberta_BPA_con_2020.csv", csv.encode("latin1"))
    pd.DataFrame([("BPA", U, "1", "Ativo Total", 1000.0), ("DRE", U, "3.01", "Receita", 5.0)],
                 columns=["demonstracao", "ordem", "cd_conta", "ds_conta", "valor"]).to_csv(cache / "555_con.csv",
                                                                                           index=False)  # fmt: skip
    loc = lh.Localizador(brutos, cache)
    achou = loc.localizar(_doc(), "BPA", U, "1.01.03")
    assert achou == {"arquivo": "dfp_cia_aberta_2020.zip/dfp_cia_aberta_BPA_con_2020.csv", "linha": 3, "escala": "MIL"}
    assert loc.localizar(_doc("enet"), "DRE", U, "3.01") == {"arquivo": "data/cache/enet/555_con.csv", "linha": 3}
    assert loc.localizar(_doc(), "BPA", U, "9.99") is None
    assert loc.sha256_enet("555") is not None and loc.sha256_enet("999") is None
    assert isinstance(io.BytesIO, type)  # (io usado acima pelo zipfile; mantém o import explícito)


# ----------------------------------------------------------------------------------------------- confiança
ESTUDO = {"acertados": 7, "acertaveis": 13, "alarmes_inteiro": 108.3, "taxa_alerta": 0.499, "juro_frequencia": 0.407}


def test_nivel_por_regra_escrita() -> None:
    confs = cf.conferir(_empresa(), "nao_financeiro")
    ok = vd.Resultado.de_valor(1.0)
    k = cn.avaliar("DSRI", ok, confs, _doc(), "2021-04-30", estudo=ESTUDO)
    assert [c.nome for c in k.criterios] == ["fonte", "completude", "consistencia", "atualidade", "metodo"]
    assert k.nivel == "media"  # o método do motor v1 fica em atenção pelo resultado do estudo 1
    assert "7 de 13" in k.criterios[-1].motivo.pt and "7 of 13" in k.criterios[-1].motivo.en
    ruim = cf.conferir(_empresa(**{"2@ÚLTIMO": 1500.0 * MI}), "nao_financeiro")
    assert cn.avaliar("LVGI", ok, ruim, _doc(), "2021-04-30", estudo=ESTUDO).nivel == "baixa"
    nc = vd.Resultado.indefinido(vd.Motivo("conta ausente", "missing account"))
    assert cn.avaliar("DSRI", nc, confs, _doc(), "2021-04-30", estudo=ESTUDO).criterios[1].resultado == "problema"


def test_criterios_de_fonte_atualidade_e_completude() -> None:
    confs = cf.conferir(_empresa(), "nao_financeiro")
    ok = vd.Resultado.de_valor(1.0)
    k = cn.avaliar("TATA", ok, confs, _doc(tipo="ind"), "2021-03-01", versoes_conhecidas=2, juros_em_6_01=False,
                   estudo=ESTUDO)  # fmt: skip
    por = {c.nome: c for c in k.criterios}
    assert por["fonte"].resultado == "atencao"
    assert por["atualidade"].resultado == "atencao" and "2 versões" in por["atualidade"].motivo.pt
    assert por["completude"].resultado == "atencao"
    assert (
        cn.avaliar("altman_z2", ok, confs, _doc(), "2021-04-30", estudo=ESTUDO)
        .criterios[-1]
        .motivo.en.startswith("context indicator")
    )


def test_confianca_nao_tem_nota_numerica() -> None:
    k = cn.avaliar("DSRI", vd.Resultado.de_valor(1.0), [], _doc(), "2021-04-30", estudo=ESTUDO)
    assert not hasattr(k, "pct") and k.nivel in ("alta", "media", "baixa")
