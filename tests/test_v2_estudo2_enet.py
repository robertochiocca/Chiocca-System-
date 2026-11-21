"""Estudo 2: o registro das tentativas de baixar de novo as tabelas do ENET (emenda 3, item 3). Só hashes, tamanhos e
contagens; o teste confere que o registro é coerente."""

from __future__ import annotations

import json
import re
from pathlib import Path

REGISTRO = Path(__file__).resolve().parents[1] / "docs" / "estudo_2_enet_tentativas.json"


def test_registro_das_tentativas_coerente() -> None:
    r = json.loads(REGISTRO.read_text(encoding="utf-8"))
    tabelas = r["tabelas"]
    assert len(tabelas) == r["resumo"]["tabelas"] == 26
    for t in tabelas:
        assert re.fullmatch(r"enet/\d+_con\.csv", t["arquivo"])
        assert re.fullmatch(r"[0-9a-f]{64}", t["sha256_copia_de_07_11"])
        if t["sha256_baixada"] is None:
            assert t["identica"] is None and t["tentativa"] is None
        else:
            assert t["identica"] == (t["sha256_baixada"] == t["sha256_copia_de_07_11"])
    baixadas = [t for t in tabelas if t["sha256_baixada"] is not None]
    assert r["resumo"]["baixadas_de_novo"] == len(baixadas) and r["resumo"]["faltam"] == 26 - len(baixadas)
    assert r["resumo"]["diferentes_das_de_07_11"] == sum(not t["identica"] for t in baixadas)
    faltam = 26
    for k, tentativa in enumerate(r["tentativas"], start=1):
        assert tentativa["n"] == k and tentativa["pedidas"] == faltam
        assert tentativa["vieram"] == sum(t["tentativa"] == k for t in tabelas)
        faltam -= tentativa["vieram"]
        assert tentativa["faltam"] == faltam
    assert faltam == r["resumo"]["faltam"]
