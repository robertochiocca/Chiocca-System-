"""Omissões do leitor em uso em documentos reais: a parte dos trechos que sai omitida pelo detector de nomes de pessoa
física, nos documentos do ENET pré-baixados para a demonstração (data/cache/enet_documentos/, fora do git).

    python -m chiocca.v2.leitura_real   # grava docs/leitor_documentos_reais.json

Roda o leitor em uso na seção (a leitor-f1-2 desde 13/11/2026, chiocca.v2.leitor_f1_2.ler, congelada, sem mudar nada
nela) em cada documento do cache: as notas explicativas
(PDF) e o relatório do auditor. Conta os trechos de todas as verificações (partes relacionadas, campos do item 18,
condições de mercado, risco sacado e relatório do auditor) e quantos saem omitidos. O número entra num dos limites da
seção (chiocca/v2/leitura_exibicao.py) e na documentação; um teste confere os textos com o JSON. Não é medida do
pré-registro: os documentos reais não têm gabarito.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

from chiocca import base
from chiocca.v2.leitor import enet_documentos
from chiocca.v2.leitor_f1_2 import ler

DESTINO = base.RAIZ / "docs" / "leitor_documentos_reais.json"
MEDIDA = base.RAIZ / "docs" / "leitor_medida_f1_2.json"  # o leitor e o commit do congelamento medido


def trechos_da_leitura(ld: dict[str, Any]) -> list[dict[str, Any]]:
    pr, rs, rel = ld["partes_relacionadas"], ld["risco_sacado"], ld["relatorio_do_auditor"]
    return [*pr["trechos"], *pr["campos_cpc05_18"], *pr["condicoes_de_mercado"], *rs["trechos"], *rel["trechos"]]


def contar(pasta: Path = enet_documentos.CACHE) -> dict[str, Any]:
    docs = sorted(p.name for p in pasta.iterdir() if p.is_dir() and (p / "notas.pdf").exists())
    por_doc = []
    for num_doc in docs:
        notas, _ = enet_documentos.notas(num_doc, pasta=pasta, rede=False)
        texto, meta = enet_documentos.relatorio_do_auditor(num_doc, pasta=pasta, rede=False)
        rel = {"titulo": meta.get("titulo"), "texto": texto} if texto else None
        ts = trechos_da_leitura(ler.ler(notas, rel, None, "pt"))
        notas_ts = [x for x in ts if x["verificacao"] != "parecer"]
        por_doc.append({"num_doc": num_doc, "trechos": len(ts), "omitidos": sum(x["omitido"] for x in ts),
                        "trechos_notas": len(notas_ts),
                        "omitidos_notas": sum(x["omitido"] for x in notas_ts)})  # fmt: skip
    trechos = sum(x["trechos"] for x in por_doc)
    omitidos = sum(x["omitidos"] for x in por_doc)
    medida = json.loads(MEDIDA.read_text(encoding="utf-8"))
    return {
        "o_que_e": "trechos omitidos pelo detector de nomes nos documentos reais da demonstração (sem gabarito; não é "
        "a medida do pré-registro)",
        "gerado_por": "python -m chiocca.v2.leitura_real",
        "leitor": medida["leitor_novo"],
        "commit": medida["commit"],
        "fonte": "data/cache/enet_documentos/ (notas explicativas e relatório do auditor da DFP de cada investigação "
        "da demonstração)",
        "documentos": len(por_doc),
        "trechos": trechos,
        "omitidos": omitidos,
        "fracao_omitidos": round(omitidos / trechos, 3) if trechos else None,
        "trechos_notas": sum(x["trechos_notas"] for x in por_doc),
        "omitidos_notas": sum(x["omitidos_notas"] for x in por_doc),
        "por_documento": por_doc,
    }


def main(argv: list[str]) -> None:
    destino = Path(argv[argv.index("--destino") + 1]) if "--destino" in argv else DESTINO
    r = contar()
    destino.write_text(json.dumps(r, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in r.items() if k != "por_documento"}, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main(sys.argv[1:])
