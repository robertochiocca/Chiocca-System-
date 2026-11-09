"""O exemplo resolvido sai de um script separado do pacote (`tests/referencia/gerar_exemplo_resolvido.py`).

O script foi escrito antes do motor e não importa o pacote `chiocca`. O teste roda o script num diretório
temporário e exige que a saída seja igual, byte a byte, a `data/exemplo_resolvido.json`, sem exceção.

Três valores do JSON passaram de 2 para 4 casas decimais no commit 70d71a5 (decisão de Roberto, 05/11/2026), porque
com 2 casas ficavam fora da tolerância de 0,0001 do próprio arquivo. Em 09/11/2026, por decisão de Roberto, o script
passou a arredondar esses três a 4 casas, com comentário ao lado; a versão usada na Fase 0 está em eca771b.
"""

from __future__ import annotations

import ast
import json
import subprocess
import sys
from pathlib import Path

from chiocca.base import RAIZ

SCRIPT = RAIZ / "tests" / "referencia" / "gerar_exemplo_resolvido.py"
JSON = RAIZ / "data" / "exemplo_resolvido.json"


def test_script_nao_importa_o_pacote() -> None:
    arvore = ast.parse(SCRIPT.read_text(encoding="utf-8"))
    modulos = {a.name for n in ast.walk(arvore) if isinstance(n, ast.Import) for a in n.names}
    modulos |= {n.module or "" for n in ast.walk(arvore) if isinstance(n, ast.ImportFrom)}
    assert modulos == {"json", "math", "sys", "pathlib"}


def test_script_reproduz_o_exemplo_resolvido(tmp_path: Path) -> None:
    saida = tmp_path / "saida.json"
    subprocess.run([sys.executable, "-I", str(SCRIPT), str(saida)], cwd=tmp_path, check=True, capture_output=True)
    assert json.loads(saida.read_text(encoding="utf-8")) == json.loads(JSON.read_text(encoding="utf-8"))
    assert saida.read_bytes() == JSON.read_bytes()
