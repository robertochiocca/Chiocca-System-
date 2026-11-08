"""O exemplo resolvido sai de um script separado do pacote (`tests/referencia/gerar_exemplo_resolvido.py`).

O script foi escrito antes do motor e não importa o pacote `chiocca`. O teste roda o script num diretório
temporário e compara a saída com `data/exemplo_resolvido.json`.

Três valores do JSON passaram de 2 para 4 casas decimais no commit 70d71a5 (decisão de Roberto, 05/11/2026),
porque com 2 casas ficavam fora da tolerância de 0,0001 do próprio arquivo. O script continua arredondando esses
três a 2 casas. Por isso o teste exige igualdade exata em todo o resto e, nesses três, que o valor do JSON
arredondado a 2 casas seja o do script. A saída do script é igual, byte a byte, ao JSON da Fase 0 (commit eca771b).
"""

from __future__ import annotations

import ast
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

from chiocca.base import RAIZ

SCRIPT = RAIZ / "tests" / "referencia" / "gerar_exemplo_resolvido.py"
JSON = RAIZ / "data" / "exemplo_resolvido.json"
QUATRO_CASAS_NO_JSON = {
    ("esperado", "dpo_salto", "DPO_t_dias"),
    ("esperado", "dpo_salto", "variacao_dias"),
    ("esperado", "juro_implicito", "spread_pp"),
}


def _diferencas(x: Any, y: Any, caminho: tuple[str, ...] = ()) -> dict[tuple[str, ...], tuple[Any, Any]]:
    if isinstance(x, dict) and isinstance(y, dict):
        out: dict[tuple[str, ...], tuple[Any, Any]] = {}
        for k in set(x) | set(y):
            out |= _diferencas(x.get(k), y.get(k), (*caminho, k))
        return out
    return {} if x == y else {caminho: (x, y)}


def test_script_nao_importa_o_pacote() -> None:
    arvore = ast.parse(SCRIPT.read_text(encoding="utf-8"))
    modulos = {a.name for n in ast.walk(arvore) if isinstance(n, ast.Import) for a in n.names}
    modulos |= {n.module or "" for n in ast.walk(arvore) if isinstance(n, ast.ImportFrom)}
    assert modulos == {"json", "math", "sys", "pathlib"}


def test_script_reproduz_o_exemplo_resolvido(tmp_path: Path) -> None:
    saida = tmp_path / "saida.json"
    subprocess.run([sys.executable, "-I", str(SCRIPT), str(saida)], cwd=tmp_path, check=True, capture_output=True)
    gerado = json.loads(saida.read_text(encoding="utf-8"))
    versionado = json.loads(JSON.read_text(encoding="utf-8"))
    dif = _diferencas(gerado, versionado)
    assert set(dif) == QUATRO_CASAS_NO_JSON
    for do_script, do_json in dif.values():
        assert do_script == round(do_json, 2)
        assert abs(do_json - round(do_json, 4)) < 1e-12  # 4 casas no JSON
