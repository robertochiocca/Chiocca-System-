"""Montagem do branch gh-pages (pedido de 10/11/2026): só o site exportado, o .nojekyll e o manifesto com o commit de
origem, os comandos, a data e o hash de cada arquivo; o .git da cópia de trabalho fica intacto."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from chiocca.v2 import gh_pages

DEMO = {"empresas": 2, "investigacoes": 3, "arquivos": 9, "bytes": 100, "segundos": 1.0}
VARREDURA = {"prefixo": "/Chiocca-System-", "empresas": 2, "investigacoes_abertas": 6, "com_aviso_de_diferenca": 1,
             "problemas": {}}  # fmt: skip


def _site(raiz: Path, base_path: str = "/Chiocca-System-") -> Path:
    site = raiz / "out"
    (site / "demo" / "investigacoes").mkdir(parents=True)
    (site / "index.html").write_text(f'<script src="{base_path}/_next/static/a.js"></script>', encoding="utf-8")
    (site / "demo" / "manifesto.json").write_text(json.dumps(DEMO), encoding="utf-8")
    (site / "demo" / "investigacoes" / "pt.pdf").write_bytes(b"%PDF-1.4 teste")
    (site / "_next").mkdir()
    (site / "_next" / "a.js").write_text("x", encoding="utf-8")
    return site


def test_monta_o_site_com_nojekyll_e_manifesto(tmp_path: Path) -> None:
    site, destino = _site(tmp_path), tmp_path / "gh-pages"
    destino.mkdir()
    (destino / ".git").write_text("gitdir: ../.git/worktrees/gh-pages", encoding="utf-8")
    (destino / "velho.html").write_text("sai", encoding="utf-8")  # arquivo da montagem anterior
    origem = {"repositorio": "robertochiocca/Chiocca-System-", "branch": "b", "commit": "c" * 40}
    m = gh_pages.montar(site, destino, origem, "2026-11-10T00:00:00+00:00", VARREDURA)
    assert (destino / ".git").read_text(encoding="utf-8").startswith("gitdir:") and not (
        destino / "velho.html"
    ).exists()
    assert (destino / ".nojekyll").read_bytes() == b""
    salvo = json.loads((destino / "manifesto.json").read_text(encoding="utf-8"))
    assert salvo == m and m["origem"] == origem and m["comandos"] == gh_pages.COMANDOS and m["data"].startswith("2026")
    esperado = {".nojekyll", "index.html", "_next/a.js", "demo/manifesto.json", "demo/investigacoes/pt.pdf"}
    assert set(m["arquivos"]) == esperado  # nem o .git nem o próprio manifesto
    for nome, h in m["arquivos"].items():
        assert hashlib.sha256((destino / nome).read_bytes()).hexdigest() == h
    assert m["total"] == {"arquivos": 5, "bytes": sum((destino / a).stat().st_size for a in esperado)}
    assert m["demonstracao"] == DEMO and m["varredura"]["investigacoes_abertas"] == 6


def test_recusa_site_sem_subpasta_ou_varredura_com_problema(tmp_path: Path) -> None:
    destino = tmp_path / "gh-pages"
    destino.mkdir()
    origem = {"repositorio": "r", "branch": "b", "commit": "c"}
    with pytest.raises(SystemExit, match="NEXT_PUBLIC_BASE_PATH"):
        gh_pages.montar(_site(tmp_path / "a", base_path=""), destino, origem, "d", VARREDURA)
    site = _site(tmp_path / "b")
    with pytest.raises(SystemExit, match="varredura"):
        gh_pages.montar(site, destino, origem, "d", VARREDURA | {"problemas": {"x": ["erro"]}})
    with pytest.raises(SystemExit, match="todas as investigações"):
        gh_pages.montar(site, destino, origem, "d", VARREDURA | {"investigacoes_abertas": 2})
