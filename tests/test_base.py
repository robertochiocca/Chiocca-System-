"""Base "como era na época" (PROMPT.md, Fase 1), com fixtures sintéticas e sem rede."""

from __future__ import annotations

from datetime import date
from pathlib import Path

import pandas as pd
import pytest

from chiocca import base, enet, grupos, montar_base
from chiocca.corte import data_corte
from chiocca.cvm import Fontes
from tests import fixtures_cvm as fx

DT = "2020-12-31"


@pytest.fixture
def mundo(tmp_path: Path) -> Fontes:
    brutos, cache = tmp_path / "brutos", tmp_path / "cache"
    brutos.mkdir()
    indice_2020 = [
        fx.doc("100", DT, 1, "2021-03-15", 1001),  # A: reapresenta depois do corte
        fx.doc("100", DT, 2, "2021-07-20", 1002),
        fx.doc("200", DT, 1, "2021-03-01", 2001),  # B: só individual, reapresenta depois do corte
        fx.doc("200", DT, 2, "2021-06-01", 2002),
        fx.doc("300", DT, 1, "2021-03-20", 3001),  # C: cancelada no cadastro
        fx.doc("400", DT, 1, "2021-03-20", 4001),  # D: fora do cadastro
        fx.doc("500", DT, 1, "2021-06-01", 5001),  # E: nenhuma versão até o corte
        fx.doc("600", DT, 1, "2021-03-01", 6001),  # F: conta repetida com valores iguais
        fx.doc("700", DT, 1, "2021-03-01", 7001),  # G: conta repetida com valores diferentes
        fx.doc("800", "2020-06-30", 1, "2020-09-30", 8001),  # H: exercício que termina em junho
        fx.doc("900", DT, 1, "2021-03-01", 9001),  # I: banco, setor do FCA mudou depois do corte
        fx.doc("910", DT, 1, "2021-03-01", 9101),  # J: securitizadora no plano de banco
        fx.doc("920", DT, 1, "2021-03-01", 9201),  # K: setor Bancos no plano não financeiro
        fx.doc("930", DT, 1, "2021-03-01", 9301),  # L: sem receita, setor só no cadastro
    ]
    banco = "Receitas da Intermediação Financeira"
    con_dre = (
        fx.dre("100", DT, 2, 900, 800)
        + fx.dre("300", DT, 1, 50, 40)
        + fx.dre("400", DT, 1, 60, 50)
        + fx.dre("500", DT, 1, 70, 60)
        + fx.dre("600", DT, 1, 80, 70)
        + fx.dre("700", DT, 1, 90, 80)
        + fx.dre(
            "800",
            "2020-06-30",
            1,
            10,
            9,
        )
        + fx.dre("900", DT, 1, 500, 400, banco)
        + fx.dre("910", DT, 1, 30, 20, banco)
        + fx.dre("920", DT, 1, 30, 20)
        + fx.dre("930", DT, 1, 0, 0)
    )
    con_bpa = (
        fx.bpa("100", DT, 2, 5000)
        + fx.bpa("300", DT, 1, 100)
        + fx.bpa("600", DT, 1, 300)
        + [fx.linha("600", DT, 1, "ÚLTIMO", "1", "Ativo Total", 300)]  # repetida, mesmo valor
        + fx.bpa("700", DT, 1, 300)
        + [fx.linha("700", DT, 1, "ÚLTIMO", "1", "Ativo Total", 301)]  # repetida, valor diferente
    )
    ind_dre = fx.dre("200", DT, 2, 20, 10) + fx.dre("100", DT, 2, 880, 790)
    fx.escreve_dfp(brutos, 2020, indice_2020, {"DRE_con": con_dre, "BPA_con": con_bpa, "DRE_ind": ind_dre})
    # DFP de 2021 da empresa A: o comparativo (PENÚLTIMO) traz o número de 2020 já corrigido.
    fx.escreve_dfp(
        brutos,
        2021,
        [fx.doc("100", "2021-12-31", 1, "2022-03-10", 1101)],
        {"DRE_con": fx.dre("100", "2021-12-31", 1, 1200, 900), "BPA_con": fx.bpa("100", "2021-12-31", 1, 5500)},
    )
    # Versão 1 da empresa A, como veio do ENET (consolidado, valores em reais): o número original.
    fx.escreve_cache_enet(
        cache,
        1001,
        [
            ("DRE", "ÚLTIMO", "3.01", "Receita de Venda de Bens e/ou Serviços", 1_000_000.0),
            ("DRE", "PENÚLTIMO", "3.01", "Receita de Venda de Bens e/ou Serviços", 800_000.0),
            ("BPA", "ÚLTIMO", "1", "Ativo Total", 5_000_000.0),
            ("DFC", "ÚLTIMO", "6.01", "Caixa Líquido Atividades Operacionais", 70_000.0),
        ],
    )
    fx.escreve_fca(
        brutos,
        2020,
        [
            ("900", 1, "2020-05-01", "Bancos"),
            ("900", 2, "2021-06-01", "Securitização de Recebíveis"),  # entregue depois do corte: não vale
            ("910", 1, "2020-05-01", "Securitização de Recebíveis"),
            ("920", 1, "2020-05-01", "Bancos"),
        ],
    )
    fx.escreve_cadastro(
        brutos,
        [("100", "ATIVO", "Comércio"), ("200", "ATIVO", "Comércio"), ("300", "CANCELADA", "Têxtil"),
         ("930", "ATIVO", "Serviços em Geral")],
    )  # fmt: skip
    return Fontes(brutos, cache)


@pytest.mark.parametrize(
    "fim,corte",
    [("2020-12-31", date(2021, 4, 30)), ("2020-06-30", date(2020, 10, 31)), ("2019-10-31", date(2020, 2, 29)),
     ("2019-09-30", date(2020, 1, 31))],
)  # fmt: skip
def test_data_corte(fim: str, corte: date) -> None:
    assert data_corte(fim) == corte


def _receita(leitura: base.Leitura, ordem: str = "ÚLTIMO") -> float:
    return leitura.valores(ordem)[("DRE", "3.01")]


def test_reapresentacao_original_antes_e_corrigido_depois(mundo: Fontes) -> None:
    antes = base.como_era(mundo, "100", 2020)  # corte do pré-registro: 30/04/2021
    assert (antes.status, antes.versao, antes.fonte, antes.tipo) == (base.OK, 1, "enet", "con")
    assert _receita(antes) == 1_000_000.0
    depois = base.como_era(mundo, "100", 2020, corte=date(2021, 12, 31))
    assert (depois.status, depois.versao, depois.fonte) == (base.OK, 2, "dados_abertos")
    assert _receita(depois) == 900_000.0  # 900 em R$ mil, convertido para reais


def test_duas_leituras(mundo: Fontes) -> None:
    d = base.duas_leituras(mundo, "100", 2020)
    r = d[(d.demonstracao == "DRE") & (d.cd_conta == "3.01")].iloc[0]
    assert (r.original, r.reapresentado) == (1_000_000.0, 900_000.0)


def test_dfc_do_enet_herda_o_metodo(mundo: Fontes) -> None:
    antes = base.como_era(mundo, "100", 2020)
    assert set(antes.contas.demonstracao) == {"DRE", "BPA", "DFC_MI"}


def test_sem_cache_do_enet_fica_pendente(mundo: Fontes) -> None:
    enet.caminho_cache(mundo.cache_enet, "1001").unlink()
    assert base.como_era(mundo, "100", 2020).status == base.PENDENTE_ENET


def test_so_individual_com_versao_posterior_fica_indisponivel(mundo: Fontes) -> None:
    assert base.como_era(mundo, "200", 2020).status == base.INDISPONIVEL_INDIVIDUAL


def test_sem_versao_ate_o_corte(mundo: Fontes) -> None:
    assert base.como_era(mundo, "500", 2020).status == base.SEM_VERSAO_ATE_CORTE


def test_conta_repetida(mundo: Fontes) -> None:
    iguais = base.como_era(mundo, "600", 2020)
    assert (iguais.status, iguais.repetidas_iguais) == (base.OK, 1)
    assert iguais.valores()[("BPA", "1")] == 300_000.0
    assert base.como_era(mundo, "700", 2020).status == base.CONTA_REPETIDA


def test_exercicio_que_termina_em_junho(mundo: Fontes) -> None:
    h = base.como_era(mundo, "800", 2020)
    assert (h.status, h.data_corte) == (base.OK, date(2020, 10, 31))


def test_consolidado_tem_preferencia(mundo: Fontes) -> None:
    depois = base.como_era(mundo, "100", 2020, corte=date(2021, 12, 31))
    assert depois.tipo == "con" and _receita(depois) == 900_000.0


def test_empresa_cancelada_e_fora_do_cadastro_continuam(mundo: Fontes, tmp_path: Path) -> None:
    meta = montar_base.monta(mundo, range(2020, 2022), tmp_path / "base")
    linhas = meta.set_index("cd_cvm")
    assert (linhas.loc["300", "status"], linhas.loc["300", "situacao_cadastro"]) == (base.OK, "CANCELADA")
    assert (linhas.loc["400", "status"], linhas.loc["400", "situacao_cadastro"]) == (base.OK, "fora_do_cadastro")
    contas = pd.read_csv(tmp_path / "base" / "contas_2020.csv.gz", dtype={"cd_cvm": str})
    assert {"300", "400"} <= set(contas.cd_cvm)


def test_grupos_e_sem_receita(mundo: Fontes, tmp_path: Path) -> None:
    meta = montar_base.monta(mundo, range(2020, 2021), tmp_path / "base").set_index("cd_cvm")
    assert (meta.loc["900", "setor"], meta.loc["900", "grupo"]) == ("Bancos", grupos.FINANCEIRA)  # emenda 7
    assert meta.loc["910", "grupo"] == grupos.NAO_FINANCEIRA  # não candidata, mesmo no plano de banco
    assert meta.loc["920", "grupo"] == grupos.NAO_FINANCEIRA  # candidata no plano não financeiro
    assert (meta.loc["930", "origem_setor"], bool(meta.loc["930", "sem_receita"])) == ("cadastro", True)
    assert not bool(meta.loc["300", "sem_receita"])


def test_plano_de_contas() -> None:
    assert grupos.plano_de_contas("Receitas de Intermediação Financeira") == "banco"
    assert grupos.plano_de_contas("Receitas das Operações") == "seguradora"
    assert grupos.plano_de_contas("Receita de Venda de Bens e/ou Serviços") == "nao_financeiro"
    assert grupos.plano_de_contas(None) == "outro"


def test_tabela_html_do_enet() -> None:
    pagina = (
        "<html><body><div>Valores (Reais Mil)</div><table>"
        "<tr><td>Conta</td><td>Descrição</td><td>Último</td><td>Penúltimo</td><td>Antepenúltimo</td></tr>"
        "<tr><td>3.01</td><td>Receita de Venda de Bens e/ou Servi&ccedil;os</td>"
        "<td>1.234</td><td>1.000</td><td>9</td></tr>"
        "<tr><td>3.02</td><td>Custo</td><td>(700)</td><td></td><td></td></tr>"
        "</table></body></html>"
    )
    t = enet.parse_tabela(pagina, "DRE")
    v = {(r.cd_conta, r.ordem): r.valor for r in t.itertuples()}
    assert v[("3.01", "ÚLTIMO")] == 1_234_000.0 and v[("3.01", "PENÚLTIMO")] == 1_000_000.0
    assert v[("3.02", "ÚLTIMO")] == -700_000.0
    assert v[("3.02", "PENÚLTIMO")] == 0.0  # célula vazia vale 0 (emenda 8)
    assert t.ds_conta.iloc[0] == "Receita de Venda de Bens e/ou Serviços"
