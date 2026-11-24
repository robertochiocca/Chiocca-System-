"""Registro de SHA-256 do estudo dos EUA (pré-registro dos EUA, seções 7, 10 e 13; pedido de 24/11/2026, quinta rodada,
item 3).

Congelado em 24/11/2026, antes da meta de 15/01/2027 (reserva: 31/03/2027), depois do exemplo calculado à mão e do
código do estudo, testado só em dados sintéticos e no exemplo. Guarda:
- `codigo`: todos os arquivos do pacote `chiocca` que o código do estudo carrega (o fecho dos imports de
  `chiocca.eua.estudo`, medido num processo novo), inclusive as funções congeladas do v1, do v2 e de
  `chiocca/v2/estudo2/secundaria.py`, e este módulo. O `chiocca/v2/lacre.py` entra sem o bloco do estudo
  (`chiocca.v2.estudo2.registro.sha256_registrado`), como nos registros do v1 e do v2;
- `exemplo_calculado_a_mao`: o script (`tests/referencia/gerar_exemplo_eua.py`) e o JSON dele (`data/exemplo_eua.json`);
- `entradas_versionadas`: a série DFF (`data/eua_dff.csv`), a taxa que substitui o CDI (seção 3.2);
- a versão menor do Python e o SHA-256 do `requirements-lock.txt`;
- `registros_do_brasil`: o SHA-256 dos registros do v1 e do v2, só para conferência. Eles não mudam.

`tests/test_eua_congelado.py` falha com qualquer mudança. O cálculo único (`chiocca.eua.estudo.main`) confere este
registro antes de ler qualquer dado e só começa com a autorização de Roberto, depois do PR e da release do congelamento.

Uso: python -m chiocca.eua.registro            (mostra o registro calculado)
     python -m chiocca.eua.registro --gravar   (grava docs/eua_codigo_congelado.json)
"""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

from chiocca.base import RAIZ
from chiocca.v2.estudo2.registro import sha256_registrado

REGISTRO = RAIZ / "docs" / "eua_codigo_congelado.json"
CONGELADO_EM = "2026-11-24"
META, RESERVA = "2027-01-15", "2027-03-31"
COMMIT_DO_PRE_REGISTRO = "a527b9eca9ab0f087b04f1c97ed737bc63188456"
MODULOS = ("chiocca.eua.estudo",)
ESTE_MODULO = "chiocca/eua/registro.py"
EXEMPLO = ("tests/referencia/gerar_exemplo_eua.py", "data/exemplo_eua.json")
ENTRADAS = ("data/eua_dff.csv",)
REGISTROS_DO_BRASIL = ("docs/estudo_2_codigo_congelado.json", "docs/motor_v2_codigo_congelado.json")


def fecho(modulos: tuple[str, ...] = MODULOS) -> list[str]:
    """Arquivos do pacote chiocca carregados ao importar os módulos (num processo novo), mais este módulo."""
    codigo = (
        "import sys\n"
        f"for m in {list(modulos)!r}: __import__(m)\n"
        "for n, m in sorted(sys.modules.items()):\n"
        "    f = getattr(m, '__file__', None)\n"
        "    if n == 'chiocca' or n.startswith('chiocca.'): print(f)\n"
    )
    saida = subprocess.run([sys.executable, "-c", codigo], cwd=RAIZ, capture_output=True, text=True, check=True)
    arquivos = {Path(x).resolve().relative_to(RAIZ).as_posix() for x in saida.stdout.split()}
    return sorted(arquivos | {ESTE_MODULO})


def _sha256(caminho: str) -> str:
    return hashlib.sha256((RAIZ / caminho).read_bytes()).hexdigest()


def calcular() -> dict[str, Any]:
    return {
        "o_que_e": "registro de SHA-256 do estudo dos EUA (pré-registro dos EUA, seções 7, 10 e 13): "
        "tests/test_eua_congelado.py falha com qualquer mudança; o lacre entra sem o bloco do estudo",
        "pre_registro": {"arquivo": "docs/pre-registro-eua.md", "commit_de_registro": COMMIT_DO_PRE_REGISTRO},
        "congelado_em": CONGELADO_EM,
        "meta": META,
        "reserva": RESERVA,
        "python": f"{sys.version_info[0]}.{sys.version_info[1]}",
        "requirements_lock_sha256": _sha256("requirements-lock.txt"),
        "registros_do_brasil": {c: _sha256(c) for c in REGISTROS_DO_BRASIL},
        "exemplo_calculado_a_mao": {c: _sha256(c) for c in EXEMPLO},
        "entradas_versionadas": {c: _sha256(c) for c in ENTRADAS},
        "codigo": {c: sha256_registrado(c) for c in fecho()},
    }


if __name__ == "__main__":
    r = calcular()
    if "--gravar" in sys.argv:
        REGISTRO.write_text(json.dumps(r, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(json.dumps(r, ensure_ascii=False, indent=1))
