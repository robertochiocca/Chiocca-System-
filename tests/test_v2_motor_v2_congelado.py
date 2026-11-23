"""Congelamento do motor v2 (pré-registro do motor v2, seção 6; decisão de Roberto, 23/11/2026).

`docs/motor_v2_codigo_congelado.json` guarda o SHA-256 de cada arquivo da lista do v2 e da avaliação do braço do v2
(com tudo o que elas importam do pacote `chiocca`), do lock, da série do CDI e do exemplo calculado à mão. Qualquer
mudança num desses arquivos faz este teste falhar. O `lacre.py` entra sem o bloco do estudo: a constante da sessão do
lacre da lista do v2 não quebra o congelamento. O registro do v1 não muda (`tests/test_v2_estudo2_script.py`).
"""

from __future__ import annotations

import hashlib
import json
from datetime import date

from chiocca.base import RAIZ
from chiocca.v2.estudo2 import abertura
from chiocca.v2.motor_v2 import abertura as abertura_v2
from chiocca.v2.motor_v2 import registro

GRAVADO = json.loads(registro.REGISTRO.read_text(encoding="utf-8"))
LACRE = "chiocca/v2/lacre.py"


def test_codigo_do_v2_congelado_nao_mudou() -> None:
    atual = registro.calcular()
    assert GRAVADO["python"] == "3.13" and GRAVADO["congelado_em"] == registro.CONGELADO_EM
    assert GRAVADO["requirements_lock_sha256"] == atual["requirements_lock_sha256"]
    assert GRAVADO["entradas_versionadas"] == atual["entradas_versionadas"]
    assert GRAVADO["exemplo_calculado_a_mao"] == atual["exemplo_calculado_a_mao"]
    for nome in registro.CONJUNTOS:
        assert set(GRAVADO["conjuntos"][nome]) == set(atual["conjuntos"][nome]), f"arquivos de {nome} mudaram"
        mudaram = [c for c, h in GRAVADO["conjuntos"][nome].items() if atual["conjuntos"][nome][c] != h]
        assert not mudaram, f"mudou depois do congelamento: {mudaram}"


def test_congelado_antes_da_meta() -> None:
    assert date.fromisoformat(GRAVADO["congelado_em"]) <= date(2027, 1, 25)


def test_lacre_entra_sem_o_bloco_do_estudo() -> None:
    """A constante do v2, posta no bloco do estudo pelo commit da sessão do lacre, não muda o SHA-256 registrado: o
    texto sem o bloco é o mesmo com ou sem ela."""
    texto = (RAIZ / LACRE).read_text(encoding="utf-8")
    linha = f"{abertura_v2.CONSTANTE} = (2024, 2025)\n"
    assert abertura.MARCA_FIM in texto and linha in texto
    fechado = texto.replace(linha, "")
    sem_o_bloco = abertura.sem_o_bloco_da_abertura(texto)
    assert sem_o_bloco == abertura.sem_o_bloco_da_abertura(fechado) and abertura_v2.CONSTANTE not in sem_o_bloco
    esperado = hashlib.sha256(sem_o_bloco.encode("utf-8")).hexdigest()
    for nome in registro.CONJUNTOS:
        assert GRAVADO["conjuntos"][nome][LACRE] == esperado
    assert hashlib.sha256(texto.encode("utf-8")).hexdigest() != esperado  # o arquivo inteiro não é o que se registra


def test_escopo_do_registro() -> None:
    lista, aval = set(GRAVADO["conjuntos"]["lista"]), set(GRAVADO["conjuntos"]["avaliacao"])
    pacote = {p.relative_to(RAIZ).as_posix() for p in registro.PACOTE.glob("*.py")}
    assert pacote <= lista and pacote <= aval and lista <= aval
    v1 = {"chiocca/sinais_amostra.py", "chiocca/variaveis.py", "chiocca/sinais/mscore.py", "chiocca/texto.py",
          "chiocca/v2/estudo2/lista.py", LACRE}  # fmt: skip
    assert v1 <= lista
    assert {"chiocca/v2/estudo2/secundaria.py", "chiocca/v2/comparativo.py"} <= aval - lista
    fora = {"chiocca/v2/motor_v2_invariante.py", "chiocca/v2/motor_v2_descricoes.py", "chiocca/v2/api.py",
            "chiocca/metricas.py", "chiocca/avaliacao.py", "chiocca/v2/estudo2/gabarito.py"}  # fmt: skip
    assert not fora & aval
    assert set(GRAVADO["exemplo_calculado_a_mao"]) == set(registro.EXEMPLO)


def test_arquivos_do_v1_com_o_mesmo_hash_nos_dois_registros() -> None:
    """Os arquivos do v1 que o v2 importa estão congelados nos dois registros, com o mesmo SHA-256."""
    v1 = json.loads((RAIZ / "docs" / "estudo_2_codigo_congelado.json").read_text(encoding="utf-8"))["conjuntos"]
    nos_dois = set(GRAVADO["conjuntos"]["avaliacao"]) & set(v1["secundaria"])
    assert "chiocca/v2/estudo2/secundaria.py" in nos_dois and LACRE in nos_dois
    for c in nos_dois:
        assert GRAVADO["conjuntos"]["avaliacao"][c] == v1["secundaria"][c], c
