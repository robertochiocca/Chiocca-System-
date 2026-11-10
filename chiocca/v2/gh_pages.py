"""Monta o branch gh-pages com a demonstração estática (pedido de 10/11/2026): só o site exportado, um `.nojekyll`
na raiz (sem ele, o GitHub Pages ignora a pasta `_next`) e um `manifesto.json` com o commit de origem, os comandos
usados, a data e o hash (SHA-256) de cada arquivo.

O gh-pages é um branch gerado: é a única exceção à regra de nenhum PDF no Git (docs/contratos.md, seção 7). A
primeira montagem cria o branch órfão; as seguintes entram como commits normais, sem force push.

Uso, da raiz do repositório, com a árvore limpa no commit de origem e uma cópia de trabalho do gh-pages em DESTINO
(`git worktree add DESTINO gh-pages`, ou `git worktree add --orphan -b gh-pages DESTINO` na primeira vez):

    python -m chiocca.v2.demonstracao_estatica --processos 4
    cd web && NEXT_PUBLIC_BASE_PATH=/Chiocca-System- npm run build:estatico
    npm run -s varrer:demo > ../varredura.json && cd ..
    python -m chiocca.v2.gh_pages DESTINO --varredura varredura.json

Depois, em DESTINO: git add -A, git commit e git push (sem --force).
"""

from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from chiocca import base

BASE_PATH = "/Chiocca-System-"
SITE = base.RAIZ / "web" / "out"
COMANDOS = [
    "python -m chiocca.v2.demonstracao_estatica --processos 4",
    f"cd web && NEXT_PUBLIC_BASE_PATH={BASE_PATH} npm run build:estatico",
    "cd web && npm run -s varrer:demo",
    "python -m chiocca.v2.gh_pages DESTINO --varredura varredura.json",
]
MANIFESTO = "manifesto.json"


def _git(*args: str) -> str:
    return subprocess.run(["git", *args], cwd=base.RAIZ, check=True, capture_output=True, text=True).stdout.strip()


def _sha256(caminho: Path) -> str:
    h = hashlib.sha256()
    with caminho.open("rb") as f:
        for bloco in iter(lambda: f.read(1 << 20), b""):
            h.update(bloco)
    return h.hexdigest()


def conferir_site(site: Path, base_path: str = BASE_PATH) -> dict[str, Any]:
    """O site exportado tem de ter a demonstração e ter sido construído para a subpasta do GitHub Pages."""
    indice, demo = site / "index.html", site / "demo" / "manifesto.json"
    if not indice.exists() or not demo.exists():
        raise SystemExit(f"falta o site exportado com a demonstração em {site}: gere e construa antes (veja o uso)")
    if f'"{base_path}/_next/' not in indice.read_text(encoding="utf-8"):
        raise SystemExit(f"o site não foi construído com NEXT_PUBLIC_BASE_PATH={base_path}")
    manifesto: dict[str, Any] = json.loads(demo.read_text(encoding="utf-8"))
    return manifesto


def conferir_varredura(varredura: dict[str, Any], demo: dict[str, Any], base_path: str = BASE_PATH) -> dict[str, Any]:
    """A varredura (npm run varrer:demo) tem de ter rodado no mesmo site, debaixo da subpasta, sem nenhum problema."""
    if varredura.get("problemas") or varredura.get("prefixo") != base_path:
        raise SystemExit(
            f"varredura com problema ou em outro prefixo: {json.dumps(varredura, ensure_ascii=False)[:500]}"
        )
    if varredura.get("investigacoes_abertas") != 2 * demo["investigacoes"]:  # as duas línguas
        raise SystemExit("a varredura não abriu todas as investigações da demonstração")
    return {k: varredura[k] for k in ("prefixo", "empresas", "investigacoes_abertas", "com_aviso_de_diferenca")}


def montar(site: Path, destino: Path, origem: dict[str, str], data: str, varredura: dict[str, Any]) -> dict[str, Any]:
    """Troca o conteúdo de `destino` (menos o .git) pelo site, com o .nojekyll e o manifesto; devolve o manifesto."""
    demo = conferir_site(site)
    resumo_varredura = conferir_varredura(varredura, demo)
    for item in destino.iterdir():
        if item.name == ".git":
            continue
        shutil.rmtree(item) if item.is_dir() else item.unlink()
    shutil.copytree(site, destino, dirs_exist_ok=True)
    (destino / ".nojekyll").write_bytes(b"")
    caminhos = [p for p in sorted(destino.rglob("*")) if p.is_file() and ".git" not in p.relative_to(destino).parts]
    arquivos = {p.relative_to(destino).as_posix(): _sha256(p) for p in caminhos}  # o manifesto da raiz ainda não existe
    manifesto = {
        "gerado_por": "python -m chiocca.v2.gh_pages",
        "origem": origem,
        "comandos": COMANDOS,
        "data": data,
        "base_path": BASE_PATH,
        "demonstracao": {k: demo[k] for k in ("empresas", "investigacoes", "arquivos", "bytes", "segundos")},
        "varredura": resumo_varredura,
        "total": {"arquivos": len(arquivos), "bytes": sum((destino / a).stat().st_size for a in arquivos)},
        "arquivos": arquivos,
    }
    (destino / MANIFESTO).write_text(json.dumps(manifesto, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    return manifesto


def main(argv: list[str]) -> None:
    if not argv or argv[0].startswith("-") or "--varredura" not in argv:
        raise SystemExit(__doc__)
    destino = Path(argv[0])
    if not (destino / ".git").exists():
        raise SystemExit(f"{destino} não é uma cópia de trabalho do gh-pages (git worktree)")
    if _git("status", "--porcelain"):
        raise SystemExit("a árvore tem mudanças: a demonstração sai de um commit, com a árvore limpa")
    varredura = json.loads(Path(argv[argv.index("--varredura") + 1]).read_text(encoding="utf-8"))
    origem = {"repositorio": "robertochiocca/Chiocca-System-", "branch": _git("rev-parse", "--abbrev-ref", "HEAD"),
              "commit": _git("rev-parse", "HEAD")}  # fmt: skip
    data = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    m = montar(SITE, destino, origem, data, varredura)
    print(json.dumps({k: v for k, v in m.items() if k != "arquivos"}, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main(sys.argv[1:])
