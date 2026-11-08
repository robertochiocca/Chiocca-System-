"""Números da análise depois do estudo 1 que dependem dos dados: persistência, variante e zero tratado como valor."""

from __future__ import annotations

import pandas as pd
import pytest

from chiocca import variaveis
from chiocca.v2 import analises_pos_estudo_1_dados as ad


def _sinais(linhas: list[tuple[int, str, str, bool, bool]]) -> pd.DataFrame:
    return pd.DataFrame(
        [{"exercicio": a, "cd_cvm": cd, "dt_refer": f"{a}-12-31", "amostra": am, "avaliada": av, "em_alerta": al}
         for a, cd, am, av, al in linhas]
    )  # fmt: skip


NF = "nao_financeira"


def test_empresa_ano_junta_linhas_do_mesmo_exercicio() -> None:
    s = _sinais(
        [(2014, "1", NF, True, False), (2014, "1", NF, True, True), (2014, "2", "fora_sem_receita", False, False)]
    )
    ea = ad.empresa_ano(s)
    assert len(ea) == 1 and bool(ea.em_alerta.iloc[0])


def test_persistencia() -> None:
    s = _sinais([
        (2013, "1", NF, True, True), (2014, "1", NF, True, True),     # alerta seguido de alerta
        (2013, "2", NF, True, False), (2014, "2", NF, True, True),    # alerta sem alerta antes
        (2014, "3", NF, True, True),                                   # sem ano anterior avaliado
        (2013, "4", NF, True, False), (2014, "4", NF, True, False),
    ])  # fmt: skip
    p = ad.persistencia(ad.empresa_ano(s))["nf"]
    assert p == {"em_alerta_com_anterior_avaliado": 2, "anterior_tambem_em_alerta": 1, "avaliadas": 7, "em_alerta": 4}


def test_variante_conta_so_empresas_avaliadas_em_todos_os_anos() -> None:
    s = _sinais([
        (2013, "1", NF, True, False), (2014, "1", NF, True, True),
        (2013, "2", NF, True, False), (2014, "2", NF, True, False),
        (2014, "3", NF, True, True),                                   # só um dos dois anos: fica fora
    ])  # fmt: skip
    n = {"casos": [{"acertavel": True, "caso_id": "x", "cd_cvm": "2", "grupos": [NF], "anos_periodo": [2013, 2014]}]}
    assert ad.variante(n, ad.empresa_ano(s)) == [
        {"caso_id": "x", "empresas": 2, "com_alerta": 1, "empresa_do_caso_incluida": True}
    ]


def test_zero_tratado_como_valor() -> None:
    t1 = variaveis.PENULTIMO
    valores = {"emprestimos_cp": 0.0, "emprestimos_lp": 0.0, "ativo_total": 0.0, "receita_liquida": 0.0}
    assert ad._zeros("juro", t1, valores) == ["emprestimos_cp", "emprestimos_lp"]
    assert ad._zeros("lucro_sem_caixa", t1, valores) == ["ativo_total"]
    assert ad._zeros("SGI", t1, valores) == []  # só DRE: não é balanço
    assert ad._zeros("TATA", t1, valores) == []  # TATA só usa a coluna do exercício
    assert "ativo_total" in ad._zeros("mscore", t1, valores)


def test_confere_taxas_para_quando_diverge() -> None:
    ea = ad.empresa_ano(_sinais([(2014, "1", NF, True, True)]))
    n = {"taxa": {"nf": {"2014": {"avaliadas": 1, "em_alerta": 1}}, "fin": {}}}
    ad.confere_taxas(ea, n)
    with pytest.raises(ValueError):
        ad.confere_taxas(ea, {"taxa": {"nf": {"2014": {"avaliadas": 2, "em_alerta": 1}}, "fin": {}}})
