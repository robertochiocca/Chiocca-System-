"""Estudo 2: o registro da lista lacrada (seção 8) e o manifesto dos arquivos de entrada (emendas 2 e 3). A lista não
fica no repositório; o teste confere que o registro, o manifesto, o lock e o registro do código continuam coerentes."""

from __future__ import annotations

import csv
import hashlib
import json
import re
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
REGISTRO = RAIZ / "docs" / "estudo_2_lista_lacrada.json"


def _sha(caminho: Path) -> str:
    return hashlib.sha256(caminho.read_bytes()).hexdigest()


def test_registro_da_lista_lacrada() -> None:
    r = json.loads(REGISTRO.read_text(encoding="utf-8"))
    assert re.fullmatch(r"[0-9a-f]{64}", r["sha256"]) and r["duas_execucoes_iguais"] is True
    assert re.fullmatch(r"[0-9a-f]{40}", r["commit_do_calculo"]) and r["python"].startswith("3.13.")
    assert r["requirements_lock_sha256"] == _sha(RAIZ / "requirements-lock.txt")
    assert r["registro_do_codigo_sha256"] == _sha(RAIZ / r["registro_do_codigo"])
    assert r["manifesto_sha256"] == _sha(RAIZ / r["manifesto"])
    assert r["exercicios"] == [2024, 2025] and r["pendentes_enet"] == 0


def test_manifesto_dos_arquivos_de_entrada() -> None:
    r = json.loads(REGISTRO.read_text(encoding="utf-8"))
    with (RAIZ / r["manifesto"]).open(encoding="utf-8", newline="") as f:
        linhas = list(csv.DictReader(f))
    brutos = [x for x in linhas if not x["arquivo"].startswith("enet/")]
    enet = [x for x in linhas if x["arquivo"].startswith("enet/")]
    assert sorted(x["arquivo"] for x in brutos) == sorted(
        ["dfp_cia_aberta_2024.zip", "dfp_cia_aberta_2025.zip", "fca_cia_aberta_2024.zip", "fca_cia_aberta_2025.zip",
         "cad_cia_aberta.csv"]
    )  # fmt: skip
    assert all(int(x["bytes"]) <= 95 * 1024 * 1024 for x in linhas)
    tentativas = json.loads((RAIZ / r["tabelas_enet"]["registro"]).read_text(encoding="utf-8"))
    baixadas = {t["arquivo"]: t for t in tentativas["tabelas"]}
    assert len(enet) == len(baixadas) == r["tabelas_enet"]["baixadas_de_novo"] == 26
    for x in enet:
        t = baixadas[x["arquivo"]]
        assert x["sha256"] == t["sha256_baixada"] and x["sha256_copia_de_07_11"] == t["sha256_copia_de_07_11"]
    assert sum(x["sha256"] != x["sha256_copia_de_07_11"] for x in enet) == r["tabelas_enet"]["diferentes_das_de_07_11"]


CARIMBO = RAIZ / "docs" / "carimbos" / "estudo-2-lista.txt"
CABECALHO_OTS = b"\x00OpenTimestamps\x00\x00Proof\x00\xbf\x89\xe2\xe8\x84\xe8\x92\x94"


def test_carimbo_da_lista() -> None:
    r = json.loads(REGISTRO.read_text(encoding="utf-8"))
    linhas = [x.split("  ", 1) for x in CARIMBO.read_text(encoding="utf-8").splitlines() if not x.startswith("#")]
    hashes = {nome: h for h, nome in linhas}
    assert linhas[0][0] == r["commit_do_calculo"]
    assert hashes["lista_estudo_2.csv"] == r["sha256"] and hashes[r["manifesto"]] == r["manifesto_sha256"]
    ots = CARIMBO.with_name(CARIMBO.name + ".ots").read_bytes()
    assert ots.startswith(CABECALHO_OTS) and ots[len(CABECALHO_OTS) + 1] == 0x08
    assert ots[len(CABECALHO_OTS) + 2 : len(CABECALHO_OTS) + 34] == hashlib.sha256(CARIMBO.read_bytes()).digest()
