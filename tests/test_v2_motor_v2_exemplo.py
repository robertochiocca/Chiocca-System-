"""Exemplo calculado à mão do motor v2 (pré-registro do motor v2, seção 6; pedido de 23/11/2026, item 1).

O script `tests/referencia/gerar_exemplo_motor_v2.py` foi escrito antes de qualquer código do v2 e não importa o pacote
`chiocca`, o numpy nem o pandas. O teste roda o script num diretório temporário e exige que a saída seja igual, byte a
byte, a `data/exemplo_motor_v2.json`, e confere o SHA-256 do arquivo: nenhum valor esperado muda para um teste passar.
Alguns valores também foram conferidos à mão, fora do script, e estão escritos aqui. A reprodução pelo código do v2 fica
no teste do v2.
"""

from __future__ import annotations

import ast
import hashlib
import json
import math
import subprocess
import sys
from pathlib import Path
from typing import Any

from chiocca.base import RAIZ

SCRIPT = RAIZ / "tests" / "referencia" / "gerar_exemplo_motor_v2.py"
JSON = RAIZ / "data" / "exemplo_motor_v2.json"
SHA256_ESPERADO = "6d0037e0fb16277ecaf71bbbbc1b3d1112bd2e570b82377b8b27dbfdcb268775"


def _ex() -> dict[str, Any]:
    return json.loads(JSON.read_text(encoding="utf-8"))


def _benford() -> dict[str, dict[str, Any]]:
    return {e["empresa_ano"]: e for e in _ex()["benford"]["esperado"]}


def test_script_nao_importa_o_pacote_nem_numpy_nem_pandas() -> None:
    arvore = ast.parse(SCRIPT.read_text(encoding="utf-8"))
    modulos = {a.name for n in ast.walk(arvore) if isinstance(n, ast.Import) for a in n.names}
    modulos |= {n.module or "" for n in ast.walk(arvore) if isinstance(n, ast.ImportFrom)}
    assert modulos == {"json", "math", "re", "sys", "unicodedata", "fractions", "pathlib"}


def test_script_reproduz_o_json_versionado(tmp_path: Path) -> None:
    saida = tmp_path / "saida.json"
    subprocess.run([sys.executable, "-I", str(SCRIPT), str(saida)], cwd=tmp_path, check=True, capture_output=True)
    assert json.loads(saida.read_text(encoding="utf-8")) == _ex()
    assert saida.read_bytes() == JSON.read_bytes()


def test_arquivo_nao_mudou() -> None:
    assert hashlib.sha256(JSON.read_bytes()).hexdigest() == SHA256_ESPERADO


def test_benford_cobre_os_casos_do_texto() -> None:
    """O exemplo passa pelos casos da seção 3.3: o mínimo de 20 números (19 fica de fora, 20 entra), as linhas que não
    contam, o valor abaixo de 1, o empate de quantidade desfeito pela ordem, as faixas desiguais (12 empresa-anos em 5
    faixas: 3, 2, 2, 2 e 3) e a faixa de um membro só, sem desvio-padrão."""
    ex, b = _ex(), _benford()
    entradas = {e["empresa_ano"]: e["linhas"] for e in ex["benford"]["entradas"]}
    assert b["E03"]["n_numeros"] == 19 and b["E03"]["padronizado"] is None and b["E03"]["faixa"] is None
    assert len(entradas["E03"]) == 24  # 19 que contam e 5 que não contam (com elas, seriam 20 ou mais)
    assert b["E09"]["n_numeros"] == 20 and b["E09"]["padronizado"] is not None
    assert ["DRE", "ÚLTIMO", 0.0347] in entradas["E02"] and b["E02"]["contagens"][2] == 4
    assert b["E01"]["n_numeros"] == b["E06"]["n_numeros"] == 24 and (b["E01"]["faixa"], b["E06"]["faixa"]) == (0, 1)
    nf = [e for e in b.values() if e["empresa_ano"].startswith("E") and e["empresa_ano"] != "E14"]
    tamanhos = [sum(1 for e in nf if e["faixa"] == k) for k in range(5)]
    assert tamanhos == [3, 2, 2, 2, 3]
    assert b["E14"]["membros_da_faixa"] == ["E14"] and b["E14"]["padronizado"] is None
    fin = [e for e in b.values() if e["empresa_ano"].startswith("F")]
    assert sorted(e["empresa_ano"] for e in fin if e["padronizado"] is not None) == ["F01", "F03"]


def test_benford_conferido_a_mao() -> None:
    """E05 (22 números: 3, 3, 3, 3, 2, 2, 2, 2, 2) e a faixa 0 das não financeiras (E01, E05, E09), conta à mão."""
    b = _benford()
    lei = [math.log10(1 + 1 / d) for d in range(1, 10)]
    assert b["E05"]["contagens"] == [3, 3, 3, 3, 2, 2, 2, 2, 2]
    desvio = sum(abs(c / 22 - p) for c, p in zip([3, 3, 3, 3, 2, 2, 2, 2, 2], lei)) / 9
    assert abs(b["E05"]["desvio"] - desvio) < 1e-12 and abs(desvio - 0.045421) < 1e-6
    d = [b[x]["desvio"] for x in ("E01", "E05", "E09")]
    media = sum(d) / 3
    dp = math.sqrt(sum((x - media) ** 2 for x in d) / 2)
    assert abs(b["E05"]["padronizado"] - (d[1] - media) / dp) < 1e-12
    assert abs(b["E05"]["padronizado"] - 1.1547) < 1e-4


def test_depi_pela_dva_conferido_a_mao() -> None:
    """Depreciação da DVA (7.04.01 consolidada da versão usada, em MIL): 1.200 e 1.000 mil; imobilizado de 8,8 e 9,0
    milhões. Taxas 0,12 e 0,10; DEPI 0,10 ÷ 0,12; M = -1,940268 (conta à mão dos oito termos)."""
    e = _ex()["depi_pela_dva"]["esperado"]
    assert e["v1"]["DEPI"] is None and e["v1"]["M"] is None and e["depreciacao_dfc"] == {"t": None, "t-1": None}
    assert e["depreciacao_dva"] == {"t": 1_200_000.0, "t-1": 1_000_000.0, "conta_t": "7.04.01", "conta_t-1": "7.04.01"}
    assert abs(e["taxa_depreciacao"]["t"] - 0.12) < 1e-12 and abs(e["taxa_depreciacao"]["t-1"] - 0.10) < 1e-12
    assert abs(e["v2"]["DEPI"] - 0.10 / 0.12) < 1e-12
    assert abs(e["v2"]["M"] - (-1.940268)) < 1e-6 and e["v2"]["marca_depreciacao_dva"] is True
    assert e["se_a_versao_fosse_do_enet"] == {"DEPI": None, "M": None, "marca_depreciacao_dva": False}
