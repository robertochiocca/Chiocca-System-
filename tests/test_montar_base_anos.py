"""A montagem da base fora dos scripts dos estudos (pedido de 24/11/2026, depois do desvio de 23/11/2026, registrado
no plano do v2): `chiocca/montar_base.py` é congelado e, sem anos, usa o padrão de 2010 a 2025, que processa exercícios
lacrados. Por isso:

- todo comando documentado ou de automação (`python -m chiocca.montar_base`) traz os anos de 2010 a 2023;
- nenhum código não congelado chama o script sem os anos (`main`, o padrão `ANOS_PADRAO` ou o módulo por subprocesso),
  e toda chamada direta a `montar_base.monta` passa um intervalo que termina antes de 2024.

Os arquivos congelados (os registros de SHA-256 em `docs/*congelado*.json`) ficam de fora: não mudam.
"""

from __future__ import annotations

import json
import re
import subprocess

from chiocca.base import RAIZ

COMANDO = re.compile(r"python -m chiocca\.montar_base(?P<resto>[^\n`]*)")
DOCUMENTOS = ("docs/como-reproduzir.md", "docs/en/how-to-reproduce.md", "README.md", "README.en.md", "Makefile")


def _versionados() -> list[str]:
    return subprocess.run(["git", "ls-files"], cwd=RAIZ, capture_output=True, text=True, check=True).stdout.split()


def _congelados() -> set[str]:
    out: set[str] = set()
    for registro in sorted((RAIZ / "docs").glob("*congelado*.json")):
        texto = registro.read_text(encoding="utf-8")
        out |= set(re.findall(r'"((?:chiocca|tests|data)/[^"]+)"', texto))
        json.loads(texto)  # o registro continua sendo um JSON válido
    return out


def test_comandos_documentados_com_os_anos() -> None:
    arquivos = [a for a in _versionados() if a in DOCUMENTOS or a.startswith((".github/", "scripts/"))]
    achados = 0
    for a in arquivos:
        for m in COMANDO.finditer((RAIZ / a).read_text(encoding="utf-8", errors="ignore")):
            achados += 1
            assert m.group("resto").split()[:2] == ["2010", "2023"], f"{a}: {m.group(0)}"
    assert achados >= 2  # os dois comandos de "Como reproduzir"


def test_codigo_nao_congelado_nunca_chama_a_montagem_sem_os_anos() -> None:
    congelados = _congelados()
    assert "chiocca/montar_base.py" in congelados
    proibido = re.compile(r"montar_base\.(main|ANOS_PADRAO)\b|[\"']chiocca\.montar_base[\"']")
    chamada = re.compile(r"montar_base\.monta\((?P<args>[^)]*\))")
    for a in _versionados():
        if not a.endswith(".py") or a in congelados or a == "tests/test_montar_base_anos.py":
            continue
        texto = (RAIZ / a).read_text(encoding="utf-8")
        assert not proibido.search(texto), a
        for m in chamada.finditer(texto):
            assert "range(" in m.group("args"), f"{a}: montar_base.monta sem um intervalo explícito: {m.group(0)}"
            for fim in re.findall(r"range\([^,]+,\s*(\d{4})\)", m.group("args")):
                assert int(fim) <= 2024, f"{a}: {m.group(0)}"  # range(a, 2024) termina em 2023
