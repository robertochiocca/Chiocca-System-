"""Mede a `leitor-f1-2`, a `leitor-f1-1` (sem mudança) e a regra nova do assunto do IPE numa pasta de casos (emenda 1
do pré-registro do leitor, docs/pre-registro-leitor.md, seções 10.2 a 10.7): imprime os totais e grava o resultado em
JSON.

Uso: python -m chiocca.v2.leitor_f1_2.avaliar <pasta dos casos> [--saida <arquivo.json>]

A pasta tem os casos do leitor (formato da seção 6, com o campo opcional `trechos_que_nao_devem_aparecer`) e os de
assunto (arquivos `assuntos_*.json`, formato de 10.4). Nos casos guardados novos, roda uma única vez, com o código
congelado (docs/leitor_congelado_f1_2.json), e o resultado é publicado como saiu. O comando da f1-1
(chiocca.v2.leitor.avaliar) não muda: ele faz parte dos arquivos congelados da f1-1 (10.7, item 2).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

from chiocca.v2.leitor_f1_2.avaliacao import avaliar


def _linha(nome: str, r: dict[str, Any]) -> str:
    t = r["totais"]
    return (f"{r['versao']}: precisão {t['precisao']:.3f} ({t['corretas']}/{t['unidades']}); cobertura "
            f"{t['cobertura']:.3f} ({t['encontrados']}/{t['itens']}); conferência literal "
            f"{t['conferidos']}/{t['trechos_mostrados']}; nomes vazados {t['nomes_vazados']}; cabeçalhos que saem "
            f"{t['cabecalhos_que_saem']}/{t['cabecalhos_listados']}")  # fmt: skip


def main(argv: list[str]) -> int:
    if not argv or argv[0].startswith("-"):
        print(__doc__)
        return 2
    pasta = Path(argv[0])
    saida = Path(argv[argv.index("--saida") + 1]) if "--saida" in argv else None
    r = avaliar(pasta)
    print(f"commit {r['commit']}")
    if r["leitor"]:
        print(f"{r['leitor']['f1_2']['totais']['casos']} casos do leitor")
        for nome in ("f1_2", "f1_1"):
            print(_linha(nome, r["leitor"][nome]))
        c = r["criterio_de_troca"]
        falhas = [k for k, v in c.items() if k != "troca" and not v]
        print("leitor-f1-2 substitui a leitor-f1-1" if c["troca"] else f"fica a leitor-f1-1: {falhas}")
    if r["assunto"]:
        a = r["assunto"]
        for nome in ("regra_nova", "regras_de_hoje"):
            t = a[nome]
            print(f"assunto, {nome}: {t['esperados_omitido']} com nome, {t['mostrados_indevidamente']} mostrados, "
                  f"{t['nomes_vazados']} nomes vazados; {t['esperados_mostrado']} sem nome, "
                  f"{t['omitidos_indevidamente']} omitidos (omissão indevida {t['omissao_indevida']:.3f}); "
                  f"{t['vazios']} vazios")  # fmt: skip
        falhas = [k for k, v in a["atingidas"].items() if not v]
        print("regra nova aprovada nos casos (falta a auditoria de 10.7, item 6)" if a["aprovada_nos_casos"]
              else f"ficam as regras de hoje: {falhas}")  # fmt: skip
    if saida:
        saida.write_text(json.dumps(r, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
