"""Lista do motor v2 (emenda 5 do estudo 2, itens 1 e 5): o registro da lista e as entradas. A lista não fica no
repositório; o teste confere que o registro, o manifesto, o lock e o registro do código do v2 continuam coerentes, que a
lista foi calculada dentro da meta do calendário e que os arquivos de entrada são os mesmos da lista do v1."""

from __future__ import annotations

import hashlib
import json
import re
from datetime import date
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
REGISTRO = RAIZ / "docs" / "motor_v2_lista_lacrada.json"
R = json.loads(REGISTRO.read_text(encoding="utf-8"))


def _sha(caminho: Path) -> str:
    return hashlib.sha256(caminho.read_bytes()).hexdigest()


def test_registro_da_lista_do_v2() -> None:
    assert re.fullmatch(r"[0-9a-f]{64}", R["sha256"]) and R["duas_execucoes_iguais"] is True and R["bytes"] > 0
    assert re.fullmatch(r"[0-9a-f]{40}", R["commit_do_calculo"]) and R["python"].startswith("3.13.")
    assert R["requirements_lock_sha256"] == _sha(RAIZ / "requirements-lock.txt")
    assert R["registro_do_codigo"] == "docs/motor_v2_codigo_congelado.json"
    assert R["registro_do_codigo_sha256"] == _sha(RAIZ / R["registro_do_codigo"])
    assert R["exercicios"] == [2024, 2025] and R["pendentes_enet"] == 0


def test_mesmas_entradas_da_lista_do_v1() -> None:
    v1 = json.loads((RAIZ / "docs" / "estudo_2_lista_lacrada.json").read_text(encoding="utf-8"))
    assert R["manifesto"] == v1["manifesto"] and R["manifesto_sha256"] == v1["manifesto_sha256"]
    assert R["manifesto_sha256"] == _sha(RAIZ / R["manifesto"]) and R["entradas_conferidas_pelo_manifesto"] == 31
    assert R["empresa_anos"] == v1["empresa_anos"] and R["sha256"] != v1["sha256"]
    assert R["entradas_no_cabecalho"] == 32  # 4 zips, o cadastro, o CDI e as 26 tabelas do ENET


def test_dentro_da_meta_do_calendario() -> None:
    """Pré-registro do motor v2, seção 9: meta do lacre em 31/01/2027; dentro dela, sem o rótulo "não prospectivo"."""
    calculada = date.fromisoformat(R["calculada_em"])
    congelado = date.fromisoformat(
        json.loads((RAIZ / R["registro_do_codigo"]).read_text(encoding="utf-8"))["congelado_em"]
    )
    assert congelado <= calculada <= date(2027, 1, 31)
    assert R["calendario"] == {"meta_do_lacre": "2027-01-31", "dentro_da_meta": True, "rotulo_nao_prospectivo": False}


CARIMBO = RAIZ / "docs" / "carimbos" / "motor-v2-lista.txt"
CABECALHO_OTS = b"\x00OpenTimestamps\x00\x00Proof\x00\xbf\x89\xe2\xe8\x84\xe8\x92\x94"


def test_carimbo_da_lista_do_v2() -> None:
    """O arquivo de hashes tem os dois commits (o do cálculo e o do SHA-256) e os SHA-256 da lista, do manifesto e do
    registro do código; o .ots carimba o SHA-256 desse arquivo (o `ots upgrade` fica para depois)."""
    linhas = [x.split("  ", 1) for x in CARIMBO.read_text(encoding="utf-8").splitlines() if not x.startswith("#")]
    hashes = {nome: h for h, nome in linhas}
    assert linhas[0] == [R["commit_do_calculo"], "commit do cálculo da lista do v2"]
    assert re.fullmatch(r"[0-9a-f]{40}", linhas[1][0]) and linhas[1][1] == "commit com o SHA-256 da lista do v2"
    assert hashes["lista_motor_v2.csv"] == R["sha256"] and hashes[R["manifesto"]] == R["manifesto_sha256"]
    assert hashes[R["registro_do_codigo"]] == R["registro_do_codigo_sha256"]
    ots = CARIMBO.with_name(CARIMBO.name + ".ots").read_bytes()
    assert ots.startswith(CABECALHO_OTS) and ots[len(CABECALHO_OTS)] == 1 and ots[len(CABECALHO_OTS) + 1] == 0x08
    assert ots[len(CABECALHO_OTS) + 2 : len(CABECALHO_OTS) + 34] == hashlib.sha256(CARIMBO.read_bytes()).digest()
