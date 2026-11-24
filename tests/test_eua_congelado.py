"""Congelamento do estudo dos EUA (pré-registro dos EUA, seções 7, 10 e 13; pedido de 24/11/2026, quinta rodada,
item 3).

`docs/eua_codigo_congelado.json` guarda o SHA-256 de cada arquivo que o código do estudo carrega (o fecho dos imports
de `chiocca.eua.estudo`, com as funções congeladas do v1, do v2 e de `secundaria`), do script do exemplo calculado à mão
e do JSON dele, da série DFF e do lock. Qualquer mudança num desses arquivos faz este teste falhar. Os registros do v1
e do v2 não mudam (os testes deles, e o SHA-256 de cada um, guardado aqui só para conferência).
"""

from __future__ import annotations

import json
import sys
from datetime import date

import pytest

from chiocca.base import RAIZ
from chiocca.eua import estudo, registro

GRAVADO = json.loads(registro.REGISTRO.read_text(encoding="utf-8"))


def test_estudo_congelado_nao_mudou() -> None:
    atual = registro.calcular()
    assert GRAVADO["python"] == "3.13" and GRAVADO["congelado_em"] == registro.CONGELADO_EM
    for chave in ("o_que_e", "pre_registro", "meta", "reserva", "requirements_lock_sha256", "registros_do_brasil",
                  "exemplo_calculado_a_mao", "entradas_versionadas"):  # fmt: skip
        assert GRAVADO[chave] == atual[chave], chave
    assert set(GRAVADO["codigo"]) == set(atual["codigo"]), "os arquivos do código do estudo mudaram"
    mudaram = [c for c, h in GRAVADO["codigo"].items() if atual["codigo"][c] != h]
    assert not mudaram, f"mudou depois do congelamento: {mudaram}"


def test_congelado_antes_da_meta_e_depois_do_registro() -> None:
    assert date(2026, 11, 24) <= date.fromisoformat(GRAVADO["congelado_em"]) <= date.fromisoformat(GRAVADO["meta"])
    assert (GRAVADO["meta"], GRAVADO["reserva"]) == ("2027-01-15", "2027-03-31")  # seção 10
    texto = (RAIZ / "docs" / "pre-registro-eua.md").read_text(encoding="utf-8")
    assert f"`{GRAVADO['pre_registro']['commit_de_registro']}`" in texto


def test_escopo_do_registro() -> None:
    codigo = set(GRAVADO["codigo"])
    eua = {f"chiocca/eua/{x}.py" for x in ("__init__", "estudo", "mapa", "fsds", "itens", "rotulos", "sec", "registro")}
    congeladas = {"chiocca/sinais/mscore.py", "chiocca/sinais/dpo.py", "chiocca/sinais/juro_implicito.py",
                  "chiocca/sinais/lucro_sem_caixa.py", "chiocca/sinais/resultado.py", "chiocca/sinais_amostra.py",
                  "chiocca/cdi.py", "chiocca/corte.py", "chiocca/variaveis.py", "chiocca/v2/motor_v2/motor.py",
                  "chiocca/v2/motor_v2/benford.py", "chiocca/v2/motor_v2/escore.py",
                  "chiocca/v2/estudo2/secundaria.py", "chiocca/v2/lacre.py"}  # fmt: skip
    assert eua <= codigo and congeladas <= codigo
    assert not {"chiocca/eua/fase0.py", "chiocca/eua/pre_registro.py"} & codigo  # fora do cálculo
    assert set(GRAVADO["exemplo_calculado_a_mao"]) == {"tests/referencia/gerar_exemplo_eua.py", "data/exemplo_eua.json"}
    assert set(GRAVADO["entradas_versionadas"]) == {"data/eua_dff.csv"}


def test_funcoes_congeladas_iguais_aos_registros_do_brasil() -> None:
    """Cada arquivo do v1 e do v2 que o estudo carrega tem, aqui, o mesmo SHA-256 dos registros do Brasil."""
    brasil: dict[str, str] = {}
    v1 = json.loads((RAIZ / "docs" / "estudo_2_codigo_congelado.json").read_text(encoding="utf-8"))
    v2 = json.loads((RAIZ / "docs" / "motor_v2_codigo_congelado.json").read_text(encoding="utf-8"))
    for r in (v1, v2):
        for conjunto in r["conjuntos"].values():
            brasil.update(conjunto)
    comuns = set(brasil) & set(GRAVADO["codigo"])
    assert {"chiocca/sinais/mscore.py", "chiocca/v2/motor_v2/motor.py", "chiocca/v2/estudo2/secundaria.py"} <= comuns
    assert all(GRAVADO["codigo"][c] == brasil[c] for c in comuns), [
        c for c in comuns if GRAVADO["codigo"][c] != brasil[c]
    ]


def test_o_calculo_unico_confere_o_registro() -> None:
    if sys.version_info[:2] == (3, 13):
        estudo.confere_congelamento()
    else:
        with pytest.raises(SystemExit, match="Python 3.13"):
            estudo.confere_congelamento()
