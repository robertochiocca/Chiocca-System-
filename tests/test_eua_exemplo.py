"""Exemplo calculado à mão do estudo dos EUA (pré-registro dos EUA, seção 7; pedido de 24/11/2026, quinta rodada).

O script `tests/referencia/gerar_exemplo_eua.py` foi escrito depois do registro e antes de qualquer código do estudo e
não importa o pacote `chiocca`, o numpy nem o pandas. O teste roda o script num diretório temporário e exige que a saída
seja igual, byte a byte, a `data/exemplo_eua.json`, e confere o SHA-256 do arquivo: nenhum valor esperado muda para um
teste passar. Alguns valores também foram conferidos à mão, fora do script, e estão escritos aqui. A reprodução pelo
código do estudo fica no teste do estudo.
"""

from __future__ import annotations

import ast
import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

from chiocca.base import RAIZ

SCRIPT = RAIZ / "tests" / "referencia" / "gerar_exemplo_eua.py"
JSON = RAIZ / "data" / "exemplo_eua.json"
SHA256_ESPERADO = "dc0da0d000157e58da273826f8e2cb4da6cd4622c33b7bf00646ab883e92d297"


def _ex() -> dict[str, Any]:
    return json.loads(JSON.read_text(encoding="utf-8"))


def _por_cik() -> dict[str, dict[str, Any]]:
    return {r["cik"]: r for r in _ex()["esperado"]["empresa_anos"]}


def test_script_nao_importa_o_pacote_nem_numpy_nem_pandas() -> None:
    arvore = ast.parse(SCRIPT.read_text(encoding="utf-8"))
    modulos = {a.name for n in ast.walk(arvore) if isinstance(n, ast.Import) for a in n.names}
    modulos |= {n.module or "" for n in ast.walk(arvore) if isinstance(n, ast.ImportFrom)}
    assert modulos == {"json", "math", "re", "sys", "datetime", "fractions", "pathlib"}


def test_script_reproduz_o_json_versionado(tmp_path: Path) -> None:
    saida = tmp_path / "saida.json"
    subprocess.run([sys.executable, "-I", str(SCRIPT), str(saida)], cwd=tmp_path, check=True, capture_output=True)
    assert json.loads(saida.read_text(encoding="utf-8")) == _ex()
    assert saida.read_bytes() == JSON.read_bytes()


def test_arquivo_nao_mudou() -> None:
    assert hashlib.sha256(JSON.read_bytes()).hexdigest() == SHA256_ESPERADO


def test_cobre_as_regras_do_texto_registrado() -> None:
    """Cada regra da seção 7 aparece pelo menos uma vez: as quatro exclusões, a versão pública no corte (a emenda antes
    do corte vale, a depois do corte e a só de capa não), as reservas do mapa e as duas marcas, o Benford abaixo do
    mínimo e os alertas de cada sinal do v1, da regra boba e do v2."""
    r = _por_cik()
    situacoes = {x["situacao"] for x in r.values()}
    assert situacoes == {
        "nao_financeira",
        "fora_financeira",
        "fora_spac",
        "fora_sem_receita",
        "fora_sem_versao_publica",
    }
    zeta = r["9000006"]
    assert len(zeta["entregas"]) == 4 and zeta["versao_usada"] == zeta["entregas"][2]  # a emenda de 15/04/2023
    origens = {v for x in r.values() for v in (x.get("origem_t") or {}).values() if v}
    for esperada in ("SalesRevenueGoodsNet", "RevenueFromContractWithCustomerIncludingAssessedTax", "OilAndGasRevenue",
                     "receita menos custo das vendas", "InterestExpenseNonoperating", "InterestAndDebtExpense",
                     "NetCashProvidedByUsedInOperatingActivitiesContinuingOperations",
                     "LongTermDebtCurrent + ShortTermBorrowings", "lucro líquido menos descontinuadas",
                     "LongTermDebtAndCapitalLeaseObligations", "AccountsPayableAndAccruedLiabilitiesCurrent",
                     "LiabilitiesAndStockholdersEquity - "
                     "StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest"):  # fmt: skip
        assert esperada in origens, esperada
    marcas = {m for x in r.values() for m in (x.get("marcas") or [])}
    assert marcas == {"fornecedores_com_provisoes", "despesa_financeira_de_conceito_mais_largo"}
    grupo = [x for x in r.values() if x["situacao"] == "nao_financeira"]
    assert (
        len(grupo) == 16 and r["9000005"]["benford_motivo"] == "menos_de_20_numeros" and r["9000005"]["mscore"] is None
    )
    for alerta in ("alerta_mscore", "alerta_dpo", "alerta_juro", "alerta_regra_boba", "v2_em_alerta"):
        assert any(x[alerta] for x in grupo), alerta
    assert sorted(x["faixa_benford"] for x in grupo if x["faixa_benford"] is not None) == sorted([0, 1, 2, 3, 4] * 3)


def test_valores_conferidos_a_mao() -> None:
    """Conferidos fora do script: o corte, a taxa média da janela e o M-score, o DPO e o juro da companhia Alfa."""
    ex, alfa = _ex()["esperado"], _por_cik()["9000001"]
    assert ex["data_corte"] == "2023-04-30" and ex["taxa_media"] == 0.02  # 2,0% em todos os dias da janela
    t, t1 = alfa["contas_t"], alfa["contas_t1"]
    assert (t["receita_liquida"], t1["receita_liquida"], t["contas_a_receber"], t1["contas_a_receber"]) == (
        1_200_000, 1_000_000, 210_000, 150_000)  # fmt: skip
    assert abs(alfa["mscore_componentes"]["DSRI"] - (210_000 / 1_200_000) / (150_000 / 1_000_000)) < 1e-12
    assert abs(alfa["dpo"] - (120_000 / 760_000 - 90_000 / 600_000) * 365) < 1e-9
    assert abs(alfa["juro"] - (22_000 / ((60_000 + 230_000 + 50_000 + 200_000) / 2) - 0.02) * 100) < 1e-9
    assert t["despesas_vendas"] == -230_000 and t["despesas_gerais_adm"] == 0 and t["custo_vendas"] == -760_000
