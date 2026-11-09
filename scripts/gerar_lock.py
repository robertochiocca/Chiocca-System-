"""Gera requirements-lock.txt: todas as dependências do projeto, inclusive as transitivas, nas versões instaladas.

Parte das dependências declaradas no pyproject.toml (as de execução e as de `dev`) e segue os requisitos de cada
pacote instalado, com os marcadores avaliados no ambiente atual. Procura primeiro no Python que roda o script (onde
estão pandas, numpy, duckdb, pyarrow e pytest) e depois nos ambientes isolados das ferramentas instaladas pelo `uv`
(mypy, black e ruff, em ~/.local/share/uv/tools). Pacote que está no Python principal fica com a versão de lá (é a
que os testes usam, com `python -m pytest`); dos ambientes isolados entram só os que faltam nele. Versões diferentes
entre os ambientes são listadas na saída. Pedido de Roberto em 09/11/2026: o CI instala a partir
deste arquivo, e o estudo 1 foi gerado com pandas 3.0.5 e numpy 2.5.3.

Uso: python scripts/gerar_lock.py
"""

from __future__ import annotations

import sys
import tomllib
from importlib.metadata import Distribution, PackageNotFoundError, distribution, distributions
from pathlib import Path

from packaging.requirements import Requirement
from packaging.utils import canonicalize_name

RAIZ = Path(__file__).resolve().parents[1]
FERRAMENTAS = Path.home() / ".local" / "share" / "uv" / "tools"
DIVERGENTES: dict[str, list[str]] = {}


def _procura(nome: str) -> list[Distribution]:
    achados = []
    try:
        achados.append(distribution(nome))
    except PackageNotFoundError:
        pass
    for site in sorted(FERRAMENTAS.glob("*/lib/python*/site-packages")):
        achados += [
            d
            for d in distributions(path=[str(site)])
            if canonicalize_name(d.metadata["Name"]) == canonicalize_name(nome)
        ]
    return achados


def fecho(raizes: list[Requirement]) -> dict[str, str]:
    versoes: dict[str, str] = {}
    pendentes = [(r, frozenset(r.extras)) for r in raizes]
    vistos: set[tuple[str, frozenset[str]]] = set()
    while pendentes:
        req, extras = pendentes.pop()
        nome = canonicalize_name(req.name)
        if (nome, extras) in vistos:
            continue
        vistos.add((nome, extras))
        achados = _procura(req.name)
        if not achados:
            raise SystemExit(f"pacote não instalado: {req.name}")
        dist = achados[0]  # o do Python principal, se existir
        if len({d.version for d in achados}) > 1:
            DIVERGENTES[nome] = sorted({d.version for d in achados})
        versoes[nome] = dist.version
        for texto in dist.requires or []:
            sub = Requirement(texto)
            ambientes = [{"extra": e} for e in extras] or [{"extra": ""}]
            if sub.marker is None or any(sub.marker.evaluate(a) for a in ambientes):
                pendentes.append((sub, frozenset(sub.extras)))
    return versoes


def main() -> None:
    projeto = tomllib.loads((RAIZ / "pyproject.toml").read_text(encoding="utf-8"))["project"]
    raizes = [Requirement(r) for r in projeto["dependencies"] + projeto["optional-dependencies"]["dev"]]
    versoes = fecho(raizes)
    linhas = [
        "# Gerado por scripts/gerar_lock.py: dependências do projeto e transitivas, nas versões deste ambiente",
        f"# (Python {sys.version_info.major}.{sys.version_info.minor}), com pandas e numpy nas versões que geraram o estudo 1. O CI instala daqui.",
        *[f"{n}=={v}" for n, v in sorted(versoes.items())],
    ]
    (RAIZ / "requirements-lock.txt").write_text("\n".join(linhas) + "\n", encoding="utf-8")
    print(len(versoes), "pacotes")
    for nome, vs in sorted(DIVERGENTES.items()):
        print(f"versões diferentes entre ambientes: {nome} {vs}; usada {versoes[nome]}")


if __name__ == "__main__":
    main()
