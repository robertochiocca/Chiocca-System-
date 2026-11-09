"""As dependências com versão fixada no pyproject.toml são as instaladas (localmente e no CI)."""

from __future__ import annotations

import re
import tomllib
from importlib.metadata import version

from chiocca.base import RAIZ


def test_versoes_fixadas_sao_as_instaladas() -> None:
    deps = tomllib.loads((RAIZ / "pyproject.toml").read_text(encoding="utf-8"))["project"]["dependencies"]
    fixadas: dict[str, str] = {}
    for d in deps:
        if m := re.fullmatch(r"([A-Za-z0-9_.-]+)==([0-9][^\s;]*)", d):
            fixadas[m.group(1)] = m.group(2)
    assert {"duckdb", "pyarrow"} <= set(fixadas)
    for pacote, esperada in fixadas.items():
        assert version(pacote) == esperada, pacote
