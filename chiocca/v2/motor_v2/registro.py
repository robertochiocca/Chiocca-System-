"""Registro de SHA-256 do motor v2 (pré-registro do motor v2, seção 6; decisão de Roberto, 23/11/2026).

Congelado em 23/11/2026, antes da meta de 25/01/2027. Dois conjuntos, cada um com todos os arquivos do pacote `chiocca`
que o script carrega (o fecho dos imports, medido num processo novo) e os arquivos do próprio pacote
`chiocca.v2.motor_v2`:
- `lista`: a lista do v2 (`chiocca.v2.motor_v2.lista`), com o motor v1 que ela usa e a lista do v1
  (`chiocca/v2/estudo2/lista.py`);
- `avaliacao`: o braço do v2 na avaliação secundária do estudo 2 (`chiocca.v2.motor_v2.avaliacao`), com as funções
  congeladas da avaliação secundária do v1 (`chiocca/v2/estudo2/secundaria.py`) e o que elas importam.
O `chiocca/v2/lacre.py` entra pelo texto sem o bloco do estudo (`chiocca.v2.estudo2.registro.sha256_registrado`), como
no registro do v1: a constante da sessão do lacre da lista do v2 entra nesse bloco e não muda o registro. Também ficam
registrados a versão menor do Python, o SHA-256 do `requirements-lock.txt`, o da série do CDI e os do exemplo calculado
à mão (o script e o JSON dele). A conferência do invariante (`chiocca/v2/motor_v2_invariante.py`) fica fora. O registro
do v1 (`docs/estudo_2_codigo_congelado.json`) não muda. `tests/test_v2_motor_v2_congelado.py` falha com qualquer
mudança.

Uso: python -m chiocca.v2.motor_v2.registro            (mostra o registro calculado)
     python -m chiocca.v2.motor_v2.registro --gravar   (grava docs/motor_v2_codigo_congelado.json)
"""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

from chiocca import base, cdi
from chiocca.v2.estudo2.registro import sha256_registrado

REGISTRO = base.RAIZ / "docs" / "motor_v2_codigo_congelado.json"
PACOTE = base.RAIZ / "chiocca" / "v2" / "motor_v2"
CONGELADO_EM = "2026-11-23"
CONJUNTOS = {
    "lista": ("chiocca.v2.motor_v2.lista",),
    "avaliacao": ("chiocca.v2.motor_v2.avaliacao", "chiocca.v2.motor_v2.lista"),
}
EXEMPLO = ("tests/referencia/gerar_exemplo_motor_v2.py", "data/exemplo_motor_v2.json")


def fecho(modulos: tuple[str, ...]) -> list[str]:
    """Arquivos do pacote chiocca carregados ao importar os módulos (num processo novo), mais os do pacote do v2."""
    codigo = (
        "import sys\n"
        f"for m in {list(modulos)!r}: __import__(m)\n"
        "for n, m in sorted(sys.modules.items()):\n"
        "    f = getattr(m, '__file__', None)\n"
        "    if n == 'chiocca' or n.startswith('chiocca.'): print(f)\n"
    )
    saida = subprocess.run([sys.executable, "-c", codigo], cwd=base.RAIZ, capture_output=True, text=True, check=True)
    arquivos = {Path(x).resolve().relative_to(base.RAIZ).as_posix() for x in saida.stdout.split()}
    arquivos |= {p.relative_to(base.RAIZ).as_posix() for p in PACOTE.glob("*.py")}
    return sorted(arquivos)


def _sha256(caminho: str) -> str:
    return hashlib.sha256((base.RAIZ / caminho).read_bytes()).hexdigest()


def calcular() -> dict[str, Any]:
    return {
        "o_que_e": "registro de SHA-256 do motor v2 (pré-registro do motor v2, seção 6): "
        "tests/test_v2_motor_v2_congelado.py falha com qualquer mudança; o lacre entra sem o bloco do estudo",
        "congelado_em": CONGELADO_EM,
        "python": f"{sys.version_info[0]}.{sys.version_info[1]}",
        "requirements_lock_sha256": _sha256("requirements-lock.txt"),
        "entradas_versionadas": {"data/cdi_sgs4389.csv": hashlib.sha256(cdi.SNAPSHOT.read_bytes()).hexdigest()},
        "exemplo_calculado_a_mao": {c: _sha256(c) for c in EXEMPLO},
        "conjuntos": {nome: {c: sha256_registrado(c) for c in fecho(mods)} for nome, mods in CONJUNTOS.items()},
    }


if __name__ == "__main__":
    r = calcular()
    if "--gravar" in sys.argv:
        REGISTRO.write_text(json.dumps(r, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(json.dumps(r, ensure_ascii=False, indent=1))
