"""Estudo 2: o congelamento da parte 1 do gabarito (seção 5 do pré-registro e emenda 1). O SHA-256 dos três arquivos
fica em docs/estudo_2_gabarito_parte_1_congelado.json; qualquer mudança de um byte faz este teste falhar. O registro
da busca é só documento: nenhum código o lê."""

from __future__ import annotations

import csv
import hashlib
import io
import json
import subprocess
from pathlib import Path
from typing import Any

RAIZ = Path(__file__).resolve().parents[1]
REGISTRO = RAIZ / "docs" / "estudo_2_gabarito_parte_1_congelado.json"
PARTE_1 = RAIZ / "data" / "gabarito_estudo_2_parte_1.csv"
BUSCA = ("docs/gabarito-estudo-2-parte-1-busca.md", "docs/en/study-2-ground-truth-part-1-search.md")

# os valores enviados por Roberto com os arquivos (19/11/2026)
ENVIADOS = {
    "data/gabarito_estudo_2_parte_1.csv": "541396895deaa4aa5e5223c392c60e248aa7ef1093a430c7b556cbefb092983c",
    "docs/gabarito-estudo-2-parte-1-busca.md": "ef4bcdf38505204e3db7f55e8886b0cab835a68f390f71279252acbdaa66aba6",
    "docs/en/study-2-ground-truth-part-1-search.md": "9e048e93c3d440259825da6827690761e8e416b5224180c45c3f9ae82d8728f8",
}


def _registro() -> Any:
    return json.loads(REGISTRO.read_text(encoding="utf-8"))


def test_parte_1_congelada_nao_mudou() -> None:
    registro = _registro()
    assert registro["arquivos"] == ENVIADOS
    for caminho, esperado in registro["arquivos"].items():
        assert hashlib.sha256((RAIZ / caminho).read_bytes()).hexdigest() == esperado, f"{caminho} mudou"


def test_formato_da_parte_1() -> None:
    conteudo = PARTE_1.read_bytes()
    assert not conteudo.startswith(b"\xef\xbb\xbf") and b"\r" not in conteudo and conteudo.endswith(b"\n")
    linhas = list(csv.reader(io.StringIO(conteudo.decode("utf-8"), newline="")))
    with (RAIZ / "data" / "gabarito_casos.csv").open(encoding="utf-8", newline="") as f:
        cabecalho_do_estudo_1 = next(csv.reader(f))
    assert linhas[0] == cabecalho_do_estudo_1 + ["parte"]
    casos = linhas[1:]
    assert len(casos) == _registro()["casos"] == 0  # "parte 1: nenhum caso"
    assert all(len(linha) == len(linhas[0]) for linha in casos)


def test_registro_da_busca_fora_do_codigo() -> None:
    versionados = subprocess.run(["git", "ls-files"], cwd=RAIZ, capture_output=True, text=True, check=True).stdout
    este = str(Path(__file__).resolve().relative_to(RAIZ))
    for caminho in versionados.split():
        if caminho.endswith((".py", ".ts", ".tsx", ".mjs", ".js")) and caminho != este:
            texto = (RAIZ / caminho).read_text(encoding="utf-8")
            for documento in BUSCA:
                assert Path(documento).stem not in texto, f"{caminho} cita {documento}"


# ---- carimbo OpenTimestamps (docs/carimbos/estudo-2-parte-1.txt e o .ots; `ots upgrade` numa sessão seguinte) ----
CARIMBO = RAIZ / "docs" / "carimbos" / "estudo-2-parte-1.txt"
COMMIT_DO_CONGELAMENTO = "ee51d054c056a8ba987799cced4e181d9cd7e152"
CABECALHO_OTS = b"\x00OpenTimestamps\x00\x00Proof\x00\xbf\x89\xe2\xe8\x84\xe8\x92\x94"


def test_carimbo_com_os_commits_e_os_hashes_da_parte_1() -> None:
    registro = _registro()
    linhas = [x.split("  ", 1) for x in CARIMBO.read_text(encoding="utf-8").splitlines() if not x.startswith("#")]
    commits = [registro["commit_de_registro"], registro["commit_da_emenda_1"], COMMIT_DO_CONGELAMENTO]
    assert [h for h, _ in linhas[:3]] == commits
    assert {c: h for h, c in linhas[3:]} == registro["arquivos"]


def test_ots_e_do_arquivo_de_hashes() -> None:
    ots = CARIMBO.with_name(CARIMBO.name + ".ots").read_bytes()
    assert ots.startswith(CABECALHO_OTS) and ots[len(CABECALHO_OTS)] == 1  # versão 1 do formato
    assert ots[len(CABECALHO_OTS) + 1] == 0x08  # o resumo do arquivo é SHA-256
    resumo = ots[len(CABECALHO_OTS) + 2 : len(CABECALHO_OTS) + 34]
    assert resumo == hashlib.sha256(CARIMBO.read_bytes()).digest()
