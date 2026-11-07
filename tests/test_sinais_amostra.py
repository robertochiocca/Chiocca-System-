"""Sinais e alertas da amostra (Fase 2) numa base sintética mínima, sem rede e sem dados reais."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from chiocca import sinais_amostra as sa

DT = "2020-12-31"
U, P = "ÚLTIMO", "PENÚLTIMO"


def _nao_financeira(cd: str, receita: float = 1000.0, fornecedores: float = 50.0) -> list[tuple]:
    linhas = []
    for ordem, k in ((U, 1.0), (P, 0.9)):
        for dem, cod, desc, val in (
            ("BPA", "1", "Ativo Total", 1000.0),
            ("BPA", "1.01", "Ativo Circulante", 500.0),
            ("BPA", "1.01.03", "Contas a Receber", 100.0),
            ("BPA", "1.02.03", "Imobilizado", 300.0),
            ("BPP", "2.01", "Passivo Circulante", 200.0),
            ("BPP", "2.01.02", "Fornecedores", fornecedores),
            ("BPP", "2.01.04", "Empréstimos e Financiamentos", 80.0),
            ("BPP", "2.02.01", "Empréstimos e Financiamentos", 120.0),
            ("BPP", "2.03", "Patrimônio Líquido Consolidado", 400.0),
            ("DRE", "3.01", "Receita de Venda de Bens e/ou Serviços", receita),
            ("DRE", "3.02", "Custo dos Bens e/ou Serviços Vendidos", -700.0),
            ("DRE", "3.03", "Resultado Bruto", 300.0),
            ("DRE", "3.04.01", "Despesas com Vendas", -50.0),
            ("DRE", "3.04.02", "Despesas Gerais e Administrativas", -40.0),
            ("DRE", "3.06.02", "Despesas Financeiras", -30.0),
            ("DRE", "3.09", "Resultado Líquido das Operações Continuadas", 60.0),
            ("DRE", "3.11", "Lucro/Prejuízo Consolidado do Período", 60.0),
            ("DFC_MI", "6.01", "Caixa Líquido Atividades Operacionais", 50.0),
            ("DFC_MI", "6.01.01.02", "Depreciação e Amortização", 30.0),
        ):
            linhas.append((cd, DT, dem, ordem, cod, desc, val * k))
    return linhas


def _financeira(cd: str, outras: float, resultado: float) -> list[tuple]:
    return [
        (cd, DT, "BPA", U, "1", "Ativo Total", 5000.0),
        (cd, DT, "BPP", U, "2.08", "Patrimônio Líquido Consolidado", 500.0),
        (cd, DT, "DRE", U, "3.01", "Receitas da Intermediação Financeira", 900.0),
        (cd, DT, "DRE", U, "3.04.05", "Outras Receitas Operacionais", outras),
        (cd, DT, "DRE", U, "3.05", "Resultado Antes dos Tributos sobre o Lucro", resultado),
    ]


@pytest.fixture
def base(tmp_path: Path) -> tuple[pd.DataFrame, Path]:
    meta = pd.DataFrame(
        [
            ("100", "nao_financeira", "nao_financeiro", "ok", False),
            ("200", "nao_financeira", "nao_financeiro", "ok", True),  # sem receita
            ("300", "financeira", "banco", "ok", False),
            ("400", "nao_financeira", "nao_financeiro", "sem_versao_ate_corte", None),
            ("500", "nao_financeira", "banco", "ok", False),  # não candidata no plano de banco
            ("600", "financeira", "banco", "ok", False),
        ],
        columns=["cd_cvm", "grupo", "plano", "status", "sem_receita"],
    )
    meta["exercicio"], meta["dt_refer"], meta["tipo"], meta["fonte"] = 2020, DT, "con", "dados_abertos"
    meta["dt_receb"], meta["data_corte"] = "2021-03-01", "2021-04-30"
    linhas = (
        _nao_financeira("100")
        + _nao_financeira("200", receita=0.0)
        + _financeira("300", 50.0, 100.0)
        + _nao_financeira("500")
        + _financeira("600", -10.0, 100.0)
    )
    contas = pd.DataFrame(
        linhas, columns=["cd_cvm", "dt_refer", "demonstracao", "ordem", "cd_conta", "ds_conta", "valor"]
    )
    contas.to_csv(tmp_path / "contas_2020.csv.gz", index=False)
    return meta, tmp_path


def test_amostra_e_sinais(base: tuple[pd.DataFrame, Path]) -> None:
    meta, pasta = base
    s = sa.calcula(meta, pasta, range(2020, 2021)).set_index("cd_cvm")
    assert s.loc["100", "amostra"] == sa.AMOSTRA_NF and s.loc["200", "amostra"] == sa.FORA_SEM_RECEITA
    assert s.loc["300", "amostra"] == sa.AMOSTRA_FIN and s.loc["400", "amostra"] == sa.FORA_STATUS
    assert pd.notna(s.loc["100", "mscore"]) and pd.isna(s.loc["100", "mscore_motivo"])
    assert s.loc["100", "dpo"] == pytest.approx(50 / 700 * 365 - 45 / 630 * 365)  # mesmo prazo nos dois anos
    assert s.loc["100", "juro_implicito"] == pytest.approx(30 / 190)
    assert s.loc["100", "cdi_medio"] == pytest.approx(0.0277, abs=1e-4)
    assert bool(s.loc["100", "marca_depreciacao_combinada"]) and not bool(
        s.loc["100", "marca_cpc06"]
    )  # exercício de 2020
    assert s.loc["300", "peso_nao_recorrente"] == pytest.approx(0.5)
    assert s.loc["600", "peso_nao_recorrente"] == 0.0  # parte positiva do total (emenda 4)
    assert s.loc["300", "alavancagem"] == pytest.approx(0.9)
    assert s.loc["500", "mscore_motivo"] == "plano_de_contas:banco"
    assert s.loc["500", "alavancagem"] == pytest.approx(0.6)  # regra boba vale para qualquer plano


def test_alertas(base: tuple[pd.DataFrame, Path]) -> None:
    meta, pasta = base
    s, limiares = sa.alertas(sa.calcula(meta, pasta, range(2020, 2021)))
    s = s.set_index("cd_cvm")
    assert bool(s.loc["100", "alerta_juro"])  # 15,8% contra CDI de 2,8% + 10 p.p.
    assert bool(s.loc["100", "em_alerta"]) and bool(s.loc["100", "avaliada"])
    assert pd.isna(s.loc["500", "alerta_mscore"]) and not bool(s.loc["500", "avaliada"])
    assert bool(s.loc["300", "alerta_peso_nao_recorrente"]) and not bool(s.loc["600", "alerta_peso_nao_recorrente"])
    assert pd.isna(s.loc["200", "alerta_regra_boba"])  # fora da amostra
    assert set(limiares.grupo) == {sa.AMOSTRA_NF, sa.AMOSTRA_FIN}


def test_decil_superior() -> None:
    valores = pd.Series([1.0, 2, 3, 4, 5, 6, 7, 8, 9, 10, None])
    alerta, limite = sa.decil_superior(valores)
    assert limite == pytest.approx(9.1)
    assert list(alerta.iloc[:10]) == [False] * 9 + [True]
    assert pd.isna(alerta.iloc[10])
    vazio, sem_limite = sa.decil_superior(pd.Series([None, None], dtype=float))
    assert sem_limite is None and vazio.isna().all()


def test_cpc06() -> None:
    assert sa.cpc06("2019-12-31") and sa.cpc06("2020-06-30")
    assert not sa.cpc06("2019-06-30") and not sa.cpc06("2020-12-31")
