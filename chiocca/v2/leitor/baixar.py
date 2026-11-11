"""Pré-baixa do ENET, para o cache (data/cache/enet_documentos/, fora do git), as notas explicativas e o relatório do
auditor dos documentos da demonstração: a versão da DFP usada em cada investigação gerada em web/public/demo/
(decisão de 11/11/2026: só os documentos da demonstração). Uma requisição por vez, com o intervalo e as tentativas de
`enet_documentos`. No fim, imprime quantos documentos vieram, quantos não têm o grupo e quantos falharam.

Uso: python -m chiocca.v2.leitor.baixar [pasta da demonstração]
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from chiocca import base
from chiocca.v2.leitor import enet_documentos

DEMO = base.RAIZ / "web" / "public" / "demo"


def documentos_da_demonstracao(demo: Path = DEMO) -> list[str]:
    """Os números (NumeroSequencialDocumento) das versões de DFP usadas nas investigações da demonstração."""
    nums: set[str] = set()
    for arq in demo.glob("investigacoes/*/*/*/pt.json"):
        inv = json.loads(arq.read_text(encoding="utf-8"))
        for e in inv.get("exercicios", []):
            if e.get("num_doc") and e.get("situacao") == "ok":
                nums.add(str(e["num_doc"]))
    return sorted(nums, key=int)


def main(argv: list[str]) -> int:
    demo = Path(argv[0]) if argv else DEMO
    nums = documentos_da_demonstracao(demo)
    contas = {"notas": 0, "relatorio": 0, "sem_notas": 0, "sem_relatorio": 0, "falhas": 0}
    falhas = []
    for k, num in enumerate(nums, 1):
        for nome, f in (("notas", enet_documentos.notas), ("relatorio", enet_documentos.relatorio_do_auditor)):
            try:
                conteudo, meta = f(num)
                contas[nome if conteudo is not None else f"sem_{nome}"] += 1
            except enet_documentos.FalhaDocumento as e:
                contas["falhas"] += 1
                falhas.append(f"{num}\t{nome}\t{e}")
        print(f"{k}/{len(nums)} {num}", flush=True)
    print(json.dumps({"documentos": len(nums), **contas}, ensure_ascii=False))
    if falhas:
        (enet_documentos.CACHE / "falhas.txt").write_text("\n".join(falhas) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
