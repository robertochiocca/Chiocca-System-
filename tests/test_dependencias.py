"""Versões travadas: o pyproject.toml fixa as dependências de execução, e o requirements-lock.txt, todas, inclusive as
transitivas. Pedido de 09/11/2026: o estudo 1 foi gerado com pandas 3.0.5 e numpy 2.5.3, e o CI instala do lock."""

from __future__ import annotations

import re
import tomllib
from importlib.metadata import PackageNotFoundError, version

from packaging.utils import canonicalize_name

from chiocca.base import RAIZ


def _lock() -> dict[str, str]:
    linhas = (RAIZ / "requirements-lock.txt").read_text(encoding="utf-8").splitlines()
    return {canonicalize_name(n): v for n, v in (x.split("==") for x in linhas if x and not x.startswith("#"))}


def test_pyproject_fixa_as_versoes_do_estudo_1_e_o_lock_concorda() -> None:
    deps = tomllib.loads((RAIZ / "pyproject.toml").read_text(encoding="utf-8"))["project"]["dependencies"]
    fixadas: dict[str, str] = {}
    for d in deps:
        if m := re.fullmatch(r"([A-Za-z0-9_.-]+)==([0-9][^\s;]*)", d):
            fixadas[canonicalize_name(m.group(1))] = m.group(2)
    assert fixadas == {"pandas": "3.0.5", "numpy": "2.5.3", "duckdb": "2.0.0", "pyarrow": "26.0.1",
                       "fastapi": "0.162.2", "pydantic": "2.13.5", "uvicorn": "0.54.0",
                       "pypdf": "6.21.4"}  # fmt: skip  # pypdf: Fase F1, decisão de 11/11/2026
    lock = _lock()
    assert all(lock[n] == v for n, v in fixadas.items())
    assert {"pytest", "ruff", "black", "mypy", "httpx"} <= set(lock)  # httpx: o TestClient da API (Fase D)


def test_pacotes_instalados_nas_versoes_do_lock() -> None:
    """No CI tudo vem do lock; aqui, só o que está instalado neste Python (os verificadores rodam isolados)."""
    conferidos = 0
    for nome, esperada in _lock().items():
        try:
            assert version(nome) == esperada, nome
            conferidos += 1
        except PackageNotFoundError:
            continue
    assert conferidos >= 8
