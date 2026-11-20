"""Registro de SHA-256 do motor v1 e do script do estudo 2 (pré-registro do estudo 2, seções 3, 8 e 9).

Dois conjuntos, cada um com todos os arquivos do pacote `chiocca` que o script carrega (o fecho dos imports, medido num
processo novo) e os arquivos do próprio pacote `chiocca.v2.estudo2`:
- `lista`: o cálculo da lista e o gabarito (`chiocca.v2.estudo2.lista` e `gabarito`), congelados até a avaliação
  primária; inclui o motor v1 inteiro que a lista usa;
- `secundaria`: a avaliação secundária (`chiocca.v2.estudo2.secundaria`, que lê a lista e confere o gabarito),
  congelada até ela; inclui a regra de materialidade do produto (`chiocca/v2/comparativo.py`) e o que ela importa.
O `chiocca/v2/lacre.py` entra pelo texto sem o bloco da abertura (`abertura.sem_o_bloco_da_abertura`): o commit que abre
o lacre só acrescenta esse bloco no fim do arquivo. Também ficam registrados a versão menor do Python, o SHA-256 do
`requirements-lock.txt` e o da série do CDI, entrada versionada do motor. `tests/test_v2_estudo2_script.py` falha com
qualquer mudança.

Uso: python -m chiocca.v2.estudo2.registro            (mostra o registro calculado)
     python -m chiocca.v2.estudo2.registro --gravar   (grava docs/estudo_2_codigo_congelado.json)
"""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

from chiocca import base, cdi
from chiocca.v2.estudo2 import abertura

REGISTRO = base.RAIZ / "docs" / "estudo_2_codigo_congelado.json"
PACOTE = base.RAIZ / "chiocca" / "v2" / "estudo2"
LACRE = "chiocca/v2/lacre.py"
CONJUNTOS = {
    "lista": ("chiocca.v2.estudo2.lista", "chiocca.v2.estudo2.gabarito"),
    "secundaria": ("chiocca.v2.estudo2.secundaria", "chiocca.v2.estudo2.lista", "chiocca.v2.estudo2.gabarito"),
}


def fecho(modulos: tuple[str, ...]) -> list[str]:
    """Arquivos do pacote chiocca carregados ao importar os módulos (num processo novo), mais os do pacote do estudo."""
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


def sha256_registrado(caminho: str) -> str:
    """SHA-256 do arquivo; o do lacre, sem o bloco da abertura."""
    p = base.RAIZ / caminho
    if caminho == LACRE:
        sem_o_bloco = abertura.sem_o_bloco_da_abertura(p.read_text(encoding="utf-8"))
        return hashlib.sha256(sem_o_bloco.encode("utf-8")).hexdigest()
    return hashlib.sha256(p.read_bytes()).hexdigest()


def calcular() -> dict[str, Any]:
    return {
        "o_que_e": "registro de SHA-256 do motor v1 e do script do estudo 2 (pré-registro do estudo 2, seções 3, 8 "
        "e 9): tests/test_v2_estudo2_script.py falha com qualquer mudança; o lacre entra sem o bloco da abertura",
        "python": f"{sys.version_info[0]}.{sys.version_info[1]}",
        "requirements_lock_sha256": hashlib.sha256((base.RAIZ / "requirements-lock.txt").read_bytes()).hexdigest(),
        "entradas_versionadas": {"data/cdi_sgs4389.csv": hashlib.sha256(cdi.SNAPSHOT.read_bytes()).hexdigest()},
        "conjuntos": {nome: {c: sha256_registrado(c) for c in fecho(mods)} for nome, mods in CONJUNTOS.items()},
    }


if __name__ == "__main__":
    r = calcular()
    if "--gravar" in sys.argv:
        REGISTRO.write_text(json.dumps(r, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(json.dumps(r, ensure_ascii=False, indent=1))
