"""Auditoria em dados reais da regra nova do assunto do IPE, antes de ligar (emenda 1 do pré-registro do leitor,
seção 10.7, item 6).

    python -m chiocca.v2.auditoria_assunto <arquivo da amostra, fora do git>

População: os assuntos dos fatos relevantes e comunicados ao mercado dos dados abertos do IPE de 2010 a 2024, um por
documento entregue (como em chiocca.v2.ipe.contar), não vazios, que a regra nova (chiocca.v2.leitor_f1_2.assunto,
congelada) mostra e as regras de hoje (chiocca.v2.ipe.regra_de_omissao) omitem. Como a regra só olha o texto, a
unidade do sorteio é o texto distinto: 400 textos, sorteados com random.Random(20261113).sample sobre a lista em ordem.

A amostra (os textos) vai para o arquivo dado, fora do git, para ser lida; no repositório fica só
docs/assunto_auditoria.json, com o procedimento, os tamanhos, o SHA-256 da população e da amostra e as contagens da
leitura, sem nenhum texto (10.7, item 6: as contagens são relatadas sem escrever os nomes).
"""

from __future__ import annotations

import hashlib
import json
import random
import sys
from pathlib import Path
from typing import Any

from chiocca import base
from chiocca.v2 import ipe
from chiocca.v2.leitor_f1_2 import assunto

SEMENTE = 20261113
TAMANHO = 400
DESTINO = base.RAIZ / "docs" / "assunto_auditoria.json"


def _sha(textos: list[str]) -> str:
    return hashlib.sha256("\n".join(textos).encode("utf-8")).hexdigest()


def populacao(brutos: Path | None = None) -> tuple[list[str], int, list[dict[str, Any]]]:
    """(textos distintos em ordem, número de documentos, arquivos do IPE usados)."""
    docs: dict[str, str] = {}
    arquivos = []
    for ano, p, tab in ipe._tabelas(brutos):
        arquivos.append(ipe._fonte(ano, p))
        for r in tab.itertuples(index=False):
            docs.setdefault(r.id_documento, r.Assunto.strip())
    escolhidos = [t for t in docs.values() if t and assunto.regra(t) == "mostrado" and ipe.regra_de_omissao(t)]
    return sorted(set(escolhidos)), len(escolhidos), arquivos


def amostra(textos: list[str]) -> list[str]:
    return random.Random(SEMENTE).sample(textos, TAMANHO)


def main(argv: list[str]) -> int:
    if not argv:
        print(__doc__)
        return 2
    textos, documentos, arquivos = populacao()
    sorteados = amostra(textos)
    Path(argv[0]).write_text("\n".join(f"{i:3d} | {t}" for i, t in enumerate(sorteados, 1)) + "\n", encoding="utf-8")
    print(json.dumps({"documentos": documentos, "textos_distintos": len(textos), "amostra": len(sorteados),
                      "sha256_populacao": _sha(textos), "sha256_amostra": _sha(sorteados),
                      "arquivos": arquivos}, ensure_ascii=False, indent=1))  # fmt: skip
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
