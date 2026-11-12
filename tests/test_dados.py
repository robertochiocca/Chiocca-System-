"""Verificação por hash dos arquivos brutos, sem rede."""

from __future__ import annotations

import csv
import hashlib
from pathlib import Path

from chiocca import dados


def _manifesto(pasta: Path, arquivos: dict[str, bytes]) -> Path:
    m = pasta / "manifesto.csv"
    with m.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["arquivo", "url", "bytes", "sha256", "baixado_em_utc"])
        for nome, conteudo in arquivos.items():
            w.writerow([nome, "https://exemplo/" + nome, len(conteudo), hashlib.sha256(conteudo).hexdigest(), "x"])
    return m


def test_verificar_aceita_arquivos_iguais(tmp_path: Path) -> None:
    (tmp_path / "a.zip").write_bytes(b"abc")
    m = _manifesto(tmp_path, {"a.zip": b"abc"})
    assert dados.verificar(tmp_path, m) == []


def test_verificar_acusa_arquivo_alterado_e_faltante(tmp_path: Path) -> None:
    (tmp_path / "a.zip").write_bytes(b"abd")
    m = _manifesto(tmp_path, {"a.zip": b"abc", "b.zip": b"x"})
    assert dados.verificar(tmp_path, m) == ["hash diferente: a.zip", "faltando: b.zip"]


def test_manifesto_versionado_cobre_todos_os_anos() -> None:
    with dados.MANIFESTO.open(encoding="utf-8", newline="") as f:
        nomes = {linha["arquivo"] for linha in csv.DictReader(f)}
    esperados = {u.rsplit("/", 1)[1] for u in dados.urls() + dados.urls_fre()}  # FRE: Fase F1, 2010 a 2024
    assert nomes == esperados
