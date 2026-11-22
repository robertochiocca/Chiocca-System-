"""make demo (pedido de 21/11/2026): um comando só serve a demonstração com os dados de amostra já versionados, sem
baixar nada da CVM e sem tocar nos exercícios de 2024 em diante; o CI confere o alvo (job demo)."""

from __future__ import annotations

import json
import re
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
PROIBIDOS = ("python", "chiocca.dados", "baixar", "buscar", "cvm.gov.br", "curl", "wget", "fetch(", "https://")


def _receita(alvo: str) -> str:
    """As linhas de um alvo do Makefile (as que começam com tabulação, logo depois de `alvo:`)."""
    texto = (RAIZ / "Makefile").read_text(encoding="utf-8")
    m = re.search(rf"^{re.escape(alvo)}:.*\n((?:\t.*\n)+)", texto, re.MULTILINE)
    assert m, f"alvo {alvo} não encontrado"
    return m.group(1)


def test_make_demo_nao_baixa_nada() -> None:
    receita = _receita("demo") + _receita("web/node_modules/.package-lock.json")
    assert "npm run build:estatico" in receita and "node scripts/demonstracao-local.mjs" in receita
    script = (RAIZ / "web/scripts/demonstracao-local.mjs").read_text(encoding="utf-8")
    codigo = "\n".join(linha for linha in script.splitlines() if not linha.lstrip().startswith("//"))
    for termo in PROIBIDOS:
        assert termo not in receita.lower(), termo
        assert termo not in codigo, termo
    assert "montarDados(raiz, { ficticias: false })" in codigo


def test_exemplos_servidos_sao_de_exercicios_anteriores_a_2024() -> None:
    exemplos = sorted((RAIZ / "docs/exemplos").glob("*.json"))
    assert len(exemplos) == 4
    for caminho in exemplos:
        assert [x["exercicio"] for x in json.loads(caminho.read_text(encoding="utf-8"))["exercicios"]] == [2021]


def test_ci_confere_o_make_demo() -> None:
    ci = (RAIZ / ".github/workflows/ci.yml").read_text(encoding="utf-8")
    m = re.search(r"^  demo:\n((?:    .*\n|\n)+)", ci, re.MULTILINE)  # o job demo, até o próximo job ou o fim
    assert m
    passos = m.group(1)
    assert "make demo" in passos and "/demo/indice.json" in passos and "pkill -f demonstracao-local.mjs" in passos


def test_readme_ensina_o_make_demo() -> None:
    for readme in ("README.md", "README.en.md"):
        assert "`make demo`" in (RAIZ / readme).read_text(encoding="utf-8"), readme
