"""Fórmulas ligadas aos dados (Fase 2): contas por código, linhas da DFC por texto, regra boba e emenda 10.

Fixture sintética no formato de data/base/contas_<ano>.csv.gz (valores em reais, despesas negativas).
"""

from __future__ import annotations

import pandas as pd
import pytest

from chiocca import variaveis as v
from chiocca.sinais import mscore
from chiocca.sinais.resultado import DENOMINADOR_NEGATIVO, DIVISAO_POR_ZERO

U, P = v.ULTIMO, v.PENULTIMO


def _contas(linhas: list[tuple[str, str, str, str, float]], dfc: str = "DFC_MI") -> pd.DataFrame:
    d = pd.DataFrame(linhas, columns=["demonstracao", "ordem", "cd_conta", "ds_conta", "valor"])
    d["demonstracao"] = d.demonstracao.replace("DFC", dfc)
    return d


BASE = [
    ("BPA", U, "1", "Ativo Total", 1000.0),
    ("BPA", P, "1", "Ativo Total", 900.0),
    ("BPA", U, "1.02.03", "Imobilizado", 400.0),
    ("BPA", P, "1.02.03", "Imobilizado", 380.0),
    ("BPP", U, "2.01.02", "Fornecedores", 50.0),
    ("BPP", U, "2.03", "Patrimônio Líquido Consolidado", 300.0),
    ("BPP", U, "2.03.01", "Patrimônio Líquido Atribuído ao Controlador", 280.0),
    ("DRE", U, "3.01", "Receita de Venda de Bens e/ou Serviços", 800.0),
    ("DRE", U, "3.02", "Custo dos Bens e/ou Serviços Vendidos", -500.0),
    ("DFC", U, "6.01", "Caixa Líquido Atividades Operacionais", 120.0),
    ("DFC", U, "6.01.01", "Caixa Gerado nas Operações", 150.0),
    ("DFC", U, "6.01.01.02", "Depreciação  e  AMORTIZAÇÃO", 30.0),
    ("DFC", U, "6.01.01.03", "Depreciação de direito de uso", 5.0),
    ("DFC", P, "6.01.01.02", "Depreciação", 28.0),
    ("DFC", U, "6.01.03", "Outros", -30.0),
    ("DFC", U, "6.01.03.01", "Juros Pagos", -20.0),
    ("DFC", U, "6.01.03.02", "Juros sobre capital próprio pagos", -4.0),
    ("DFC", U, "6.01.03.03", "Juros recebidos de aplicações (pagamento)", 3.0),
    ("DFC", U, "6.02.01", "Pagamento de juros capitalizados", -7.0),
    ("DFC", U, "6.03.02", "Pagamentos de juros sobre empréstimos", -11.0),
]


def test_contas_por_codigo_t_e_t_menos_1() -> None:
    c = _contas(BASE)
    t, t1 = v.le_ordem(c, U), v.le_ordem(c, P)
    assert t.valores["ativo_total"] == 1000.0 and t1.valores["ativo_total"] == 900.0
    assert t.valores["custo_vendas"] == -500.0
    assert t1.valores["fornecedores"] is None  # ausente fica ausente, não vira zero
    assert t.valores["patrimonio_liquido"] == 300.0


def test_depreciacao_soma_e_marca() -> None:
    c = _contas(BASE)
    t, t1 = v.le_ordem(c, U), v.le_ordem(c, P)
    assert t.valores["depreciacao"] == 35.0  # as duas linhas que contêm "deprecia" em 6.01.01
    assert t.depreciacao_combinada  # uma delas também contém "amortiza"
    assert t1.valores["depreciacao"] == 28.0 and not t1.depreciacao_combinada


def test_juros_pagos_saem_do_caixa_operacional() -> None:
    t = v.le_ordem(_contas(BASE), U)
    assert t.juros_pagos_em_6_01 == ("6.01.03.01",)  # sem JCP, sem "recebid"
    assert t.juros_pagos_em_6_03 == ("6.03.02",)  # já em financiamento: não muda o caixa operacional
    assert t.valores["caixa_operacional_apresentado"] == 120.0
    assert t.valores["caixa_operacional"] == 140.0  # 120 − (−20); a linha em 6.02 fica fora (seção)


def test_sem_juros_pagos_o_caixa_fica_como_apresentado() -> None:
    linhas = [x for x in BASE if "Juros Pagos" not in x[3]]
    t = v.le_ordem(_contas(linhas), U)
    assert t.valores["juros_pagos_em_6_01"] is None and t.valores["caixa_operacional"] == 120.0


def test_conta_mae_e_subconta_conta_so_a_mae() -> None:
    linhas = BASE + [("DFC", U, "6.01.03.01.01", "Juros pagos sobre debêntures", -8.0)]
    t = v.le_ordem(_contas(linhas), U)
    assert t.juros_pagos_em_6_01 == ("6.01.03.01",) and t.valores["juros_pagos_em_6_01"] == -20.0


def test_dfc_pelo_metodo_direto() -> None:
    linhas = [
        ("DFC", U, "6.01", "Caixa Líquido Atividades Operacionais", 90.0),
        ("DFC", U, "6.01.01", "Caixa Gerado nas Operações", 100.0),
        ("DFC", U, "6.01.01.01", "Recebimentos de clientes", 900.0),
        ("DFC", U, "6.01.01.05", "Pagamento de juros", -15.0),
    ]
    c = _contas(linhas, dfc="DFC_MD")
    t = v.le_ordem(c, U)
    assert v.metodo_dfc(c) == "DFC_MD"
    assert t.valores["depreciacao"] is None  # sem linha de depreciação: DEPI não calculável
    assert t.valores["caixa_operacional"] == 105.0


def test_padroes_ignoram_maiusculas_acentos_e_espacos() -> None:
    assert v.casa("  JUROS   PAGOS  ", v.JUROS_PAGOS)
    assert v.casa("Pagamentos de Juros", v.JUROS_PAGOS)
    assert not v.casa("Juros sobre Capital Próprio Pagos", v.JUROS_PAGOS)
    assert not v.casa("Juros Recebidos", v.JUROS_PAGOS)
    assert not v.casa("Juros e variações monetárias", v.JUROS_PAGOS)
    assert v.casa("DEPRECIAÇÕES", v.DEPRECIACAO)


def test_secao_pelo_prefixo_do_codigo() -> None:
    assert v.na_secao("6.01.01.02", ("6.01.01",)) and v.na_secao("6.01.01", ("6.01.01",))
    assert not v.na_secao("6.01.010", ("6.01.01",)) and not v.na_secao("6.01.02.01", ("6.01.01",))


def test_alavancagem_da_regra_boba() -> None:
    r = v.alavancagem(_contas(BASE))
    assert r.valor == pytest.approx(0.7)  # (1000 − 300) / 1000, com o PL de nível mais alto (2.03)
    banco = _contas(
        [
            ("BPA", U, "1", "Ativo Total", 2000.0),
            ("BPP", U, "2", "Passivo Total", 2000.0),
            ("BPP", U, "2.08", "Patrimônio Líquido Consolidado", 200.0),
            ("BPP", U, "2.08.01", "Patrimônio Líquido Atribuído ao Controlador", 190.0),
        ]
    )
    assert v.alavancagem(banco).valor == pytest.approx(0.9)
    assert v.alavancagem(_contas(BASE[:1])).motivo == "conta_ausente:patrimonio_liquido"


def test_linhas_da_dre_para_financeiras() -> None:
    assert v.linhas_dre(_contas(BASE))[0] == ("3.01", "Receita de Venda de Bens e/ou Serviços", 800.0)


def _mscore_base() -> dict[str, float | None]:
    return {
        "contas_a_receber": 100.0,
        "receita_liquida": 1000.0,
        "resultado_bruto": 300.0,
        "ativo_circulante": 500.0,
        "imobilizado": 300.0,
        "ativo_total": 1000.0,
        "depreciacao": 30.0,
        "despesas_vendas": -50.0,
        "despesas_gerais_adm": -40.0,
        "lucro_operacoes_continuadas": 60.0,
        "caixa_operacional": 50.0,
        "passivo_circulante": 200.0,
        "emprestimos_lp": 100.0,
    }


def test_receita_negativa_deixa_os_indices_de_receita_nao_calculaveis() -> None:
    t, t1 = _mscore_base(), _mscore_base()
    t["receita_liquida"] = -10.0
    m = mscore.calcula(t, t1)
    for nome in ("DSRI", "GMI", "SGAI"):
        assert str(m.componentes[nome].motivo).startswith(DENOMINADOR_NEGATIVO)
    assert m.componentes["SGI"].valor == pytest.approx(-0.01)  # divide pela receita de t−1, que é positiva
    assert m.componentes["TATA"].valor is not None and m.m.valor is None
    t1["receita_liquida"] = -10.0
    t["receita_liquida"] = 1000.0
    assert mscore.calcula(t, t1).componentes["SGI"].motivo == f"{DENOMINADOR_NEGATIVO}:SGI receita t-1"
    t1["receita_liquida"] = 0.0
    assert mscore.calcula(t, t1).componentes["SGI"].motivo == f"{DIVISAO_POR_ZERO}:SGI receita t-1"
