"""Mede o leitor numa pasta de casos (docs/pre-registro-leitor.md): imprime os totais e grava o resultado em JSON.

Uso: python -m chiocca.v2.leitor.avaliar <pasta dos casos> [--saida <arquivo.json>]

Nos casos guardados, roda uma única vez, com o leitor congelado, e o resultado é publicado como saiu.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from chiocca.v2.leitor.avaliacao import avaliar


def main(argv: list[str]) -> int:
    if not argv or argv[0].startswith("-"):
        print(__doc__)
        return 2
    pasta = Path(argv[0])
    saida = Path(argv[argv.index("--saida") + 1]) if "--saida" in argv else None
    r = avaliar(pasta)
    t = r["totais"]
    print(f"leitor {r['leitor']} (commit {r['commit']}), {t['casos']} casos")
    print(f"precisão {t['precisao']:.3f} ({t['corretas']}/{t['unidades']}); cobertura {t['cobertura']:.3f} "
          f"({t['encontrados']}/{t['itens']}); conferência literal {t['conferidos']}/{t['trechos_mostrados']}; "
          f"nomes vazados {t['nomes_vazados']}")  # fmt: skip
    print("aprovado" if r["aprovado"] else f"não aprovado: {[k for k, v in r['atingidas'].items() if not v]}")
    if saida:
        saida.write_text(json.dumps(r, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
