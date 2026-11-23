"""Acesso aos arquivos da SEC (Fase 0 dos EUA), pela política de acesso justo da SEC.

- **User-Agent:** a SEC pede um User-Agent com nome e contato e recusa pedidos sem ele (HTTP 403). O valor vem só da
  variável de ambiente `SEC_USER_AGENT`, definida por Roberto nas configurações do ambiente; nenhum arquivo versionado
  nem log guarda o valor, e as mensagens de erro não o repetem. Sem a variável, nada é baixado.
- **Ritmo:** no máximo 10 pedidos por segundo (`INTERVALO` entre pedidos).
- **Manifesto:** cada arquivo baixado entra em `data/eua_manifesto.csv` (versionado) com o endereço, o tamanho, o
  SHA-256 e a hora; o arquivo fica em `data/eua/`, fora do Git.
"""

from __future__ import annotations

import csv
import hashlib
import os
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from chiocca.base import RAIZ

VARIAVEL = "SEC_USER_AGENT"
INTERVALO = 0.11  # segundos entre pedidos: menos de 10 por segundo
MANIFESTO = RAIZ / "data" / "eua_manifesto.csv"
DADOS = RAIZ / "data" / "eua"
COLUNAS = ["arquivo", "url", "bytes", "sha256", "baixado_em_utc"]


class SemUserAgent(RuntimeError):
    """A variável de ambiente do User-Agent não está definida (ou não tem um contato)."""

    def __init__(self) -> None:
        super().__init__(f"defina {VARIAVEL} (nome e contato, como pede a SEC) nas configurações do ambiente")


def agente() -> str:
    """O User-Agent da variável de ambiente; exige um contato (um "@")."""
    valor = os.environ.get(VARIAVEL, "").strip()
    if not valor or "@" not in valor:
        raise SemUserAgent()
    return valor


def sha256(caminho: Path) -> str:
    h = hashlib.sha256()
    with Path(caminho).open("rb") as f:
        for bloco in iter(lambda: f.read(1 << 20), b""):
            h.update(bloco)
    return h.hexdigest()


class Cliente:
    """Baixa arquivos da SEC no ritmo permitido, com o User-Agent da variável de ambiente."""

    def __init__(self) -> None:
        self._agente = agente()
        self._ultimo = 0.0

    def __repr__(self) -> str:  # o User-Agent não aparece em log nem em erro
        return "Cliente(SEC)"

    def baixar(self, url: str, destino: Path) -> dict[str, Any]:
        espera = INTERVALO - (time.monotonic() - self._ultimo)
        if espera > 0:
            time.sleep(espera)
        self._ultimo = time.monotonic()
        pedido = urllib.request.Request(url, headers={"User-Agent": self._agente, "Accept-Encoding": "identity"})
        destino.parent.mkdir(parents=True, exist_ok=True)
        parcial = destino.with_suffix(destino.suffix + ".parcial")
        try:
            with urllib.request.urlopen(pedido, timeout=120) as r, parcial.open("wb") as f:
                while bloco := r.read(1 << 20):
                    f.write(bloco)
        except urllib.error.HTTPError as e:
            parcial.unlink(missing_ok=True)
            raise RuntimeError(f"{url}: HTTP {e.code}") from None
        parcial.replace(destino)
        agora = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
        return {"arquivo": destino.relative_to(DADOS).as_posix() if destino.is_relative_to(DADOS) else destino.name,
                "url": url, "bytes": destino.stat().st_size, "sha256": sha256(destino),
                "baixado_em_utc": agora}  # fmt: skip


def le_manifesto(caminho: Path = MANIFESTO) -> list[dict[str, str]]:
    if not caminho.exists():
        return []
    with caminho.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def grava_manifesto(novas: list[dict[str, Any]], caminho: Path = MANIFESTO) -> None:
    """Acrescenta ou substitui as linhas pelo nome do arquivo, em ordem alfabética."""
    linhas = {x["arquivo"]: x for x in le_manifesto(caminho)}
    linhas |= {str(x["arquivo"]): {c: str(x[c]) for c in COLUNAS} for x in novas}
    with caminho.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=COLUNAS, lineterminator="\n")
        w.writeheader()
        for nome in sorted(linhas):
            w.writerow(linhas[nome])
