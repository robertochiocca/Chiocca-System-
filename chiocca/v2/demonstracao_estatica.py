"""Demonstração estática (pedido de 10/11/2026): as investigações do modo demonstração geradas por script, para a
interface ser publicada como site estático, sem API rodando.

Companhias: as do modo demonstração (`chiocca.v2.api.empresas_da_demonstracao`, as companhias dos casos do gabarito
sem os casos em observação). Datas de cada companhia: a data de corte de cada exercício do período afetado do caso,
a do exercício anterior a ele e 31/12/2024 (só exercícios de 2010 a 2023, o lacre). Em cada data, a investigação de
cada um desses exercícios cuja DFP já tinha sido entregue até ela. Companhia cujo período afetado fica todo fora de
2010 a 2023 (ou não está informado) entra só com 31/12/2024 e o último exercício entregue até essa data.

Os arquivos são a própria saída da API (`chiocca.v2.api`, chamada em processo, com o modo demonstração ligado), nas
duas línguas: a investigação em JSON e em PDF, a empresa na data e "como o motor foi testado". O `indice.json` é a
rota /api/v1/demonstracao (`chiocca.v2.demonstracao`): em ordem alfabética, as companhias com o caso do gabarito,
os nomes conhecidos até 31/12/2024 (para a busca por nome), as datas com o rótulo de cada uma e os destaques da
página inicial; o plano da geração sai dela.
Um teste confere que os arquivos são iguais à saída da API para as mesmas entradas. As investigações saem sem
carimbo de tempo (decisão de 12/11/2026): a data da geração e o commit ficam no manifesto.json, e duas gerações do
mesmo conteúdo dão os mesmos bytes (o histórico do gh-pages só cresce com o que mudou).

Os arquivos ficam em web/public/demo/ (fora do git: os PDFs não entram no repositório).

Uso: python -m chiocca.v2.demonstracao_estatica [--processos N] [--destino PASTA]
"""

from __future__ import annotations

import json
import subprocess
import sys
import time
from collections import defaultdict
from collections.abc import Callable
from datetime import date, datetime, timezone
from multiprocessing import get_context
from pathlib import Path
from typing import Any

import pandas as pd

from chiocca import base
from chiocca.corte import data_corte
from chiocca.v2 import busca
from chiocca.v2.lacre import DATA_REFERENCIA_MAXIMA, DATA_REFERENCIA_MINIMA, ULTIMO_EXERCICIO_LIBERADO

DESTINO = base.RAIZ / "web" / "public" / "demo"
LINGUAS = ("pt", "en")
PRIMEIRO = 2010
Plano = dict[str, dict[str, list[int]]]  # cd_cvm -> data -> exercícios


def _exercicios_do_caso(casos: pd.DataFrame) -> set[int]:
    anos: set[int] = set()
    for c in casos.itertuples(index=False):
        if pd.notna(c.periodo_afetado_inicio) and pd.notna(c.periodo_afetado_fim):
            ini, fim = int(c.periodo_afetado_inicio), int(c.periodo_afetado_fim)
            anos |= set(range(ini - 1, fim + 1))  # o período afetado e o exercício anterior a ele
    return {a for a in anos if PRIMEIRO <= a <= ULTIMO_EXERCICIO_LIBERADO}


def _fim_do_exercicio(fontes: Any, cd: str, ano: int) -> str | None:
    d = fontes.consulta("SELECT min(DT_REFER) AS d FROM versoes WHERE cd_cvm = ? AND exercicio = ?", [cd, ano]).d
    return None if d.empty or pd.isna(d.iloc[0]) else str(d.iloc[0])[:10]


def plano(fontes: Any, empresas: set[str], gabarito: pd.DataFrame) -> Plano:
    """Para cada companhia, as datas e, em cada data, os exercícios com DFP entregue até ela."""
    gabarito = gabarito.assign(cd=gabarito.cd_cvm.fillna("").astype(str).str.lstrip("0"))
    out: Plano = {}
    for cd in sorted(empresas, key=int):
        anos = _exercicios_do_caso(gabarito[gabarito.cd == cd])
        datas: set[date] = {DATA_REFERENCIA_MAXIMA}
        for a in anos:
            fim = _fim_do_exercicio(fontes, cd, a)
            if fim:
                d = data_corte(fim)
                if DATA_REFERENCIA_MINIMA <= d <= DATA_REFERENCIA_MAXIMA:
                    datas.add(d)
        por_data: dict[str, list[int]] = {}
        for d in sorted(datas):
            entregues = busca.exercicios_na_data(fontes, cd, d)
            exs = [a for a in entregues if a in anos] if anos else entregues[-1:]
            if exs and (anos or d == DATA_REFERENCIA_MAXIMA):
                por_data[d.isoformat()] = exs
        if por_data:
            out[cd] = por_data
    return out


def _sem_carimbos(x: Any) -> Any:
    if isinstance(x, dict):
        return {k: _sem_carimbos(v) for k, v in x.items() if k not in ("gerado_em", "calculado_em")}
    if isinstance(x, list):
        return [_sem_carimbos(v) for v in x]
    return x


# ---- geração (a mesma API, em processo) ----

_CLIENTE: Any = None


def _cliente(fabrica: Callable[[], Any] | None) -> Any:
    global _CLIENTE
    if _CLIENTE is None:
        from fastapi.testclient import TestClient

        from chiocca.v2 import api
        from chiocca.v2.armazem import FontesArmazem
        from chiocca.v2.linhagem import Localizador

        if fabrica is None:
            fa = FontesArmazem()
            loc = Localizador(base.BRUTOS, fa.cache_enet, base.RAIZ / "data" / "manifesto_brutos.csv")
            _CLIENTE = TestClient(api.criar_app(lambda: fa, loc, modo_demonstracao=True, carimbo=False))
        else:
            _CLIENTE = TestClient(api.criar_app(fabrica, None, modo_demonstracao=True, carimbo=False))
    return _CLIENTE


def _grava(destino: Path, caminho: str, conteudo: bytes) -> int:
    alvo = destino / caminho
    alvo.parent.mkdir(parents=True, exist_ok=True)
    alvo.write_bytes(conteudo)
    return len(conteudo)


def _json(r: Any) -> bytes:
    if r.status_code != 200:
        raise RuntimeError(f"{r.url}: HTTP {r.status_code} {r.text[:300]}")
    return (json.dumps(r.json(), ensure_ascii=False, indent=1) + "\n").encode("utf-8")


def gerar_grupo(args: tuple[str, int, list[str], str, Callable[[], Any] | None]) -> list[tuple[str, int]]:
    """Um exercício e uma data, para várias companhias: o corte transversal da data é calculado uma vez só."""
    data, exercicio, empresas, destino, fabrica = args
    c = _cliente(fabrica)
    escritos = []
    for cd in empresas:
        for lang in LINGUAS:
            base_url = f"/api/v1/investigacoes/{cd}/{exercicio}"
            q = {"data_referencia": data, "idioma": lang}
            caminho = f"investigacoes/{cd}/{exercicio}/{data}/{lang}"
            corpo = _json(c.get(base_url, params=q))
            escritos.append((f"{caminho}.json", _grava(Path(destino), f"{caminho}.json", corpo)))
            pdf = c.get(f"{base_url}/pdf", params=q)
            if pdf.status_code != 200:
                raise RuntimeError(f"PDF {cd} {exercicio} {data} {lang}: HTTP {pdf.status_code}")
            escritos.append((f"{caminho}.pdf", _grava(Path(destino), f"{caminho}.pdf", pdf.content)))
    return escritos


def gerar(destino: Path = DESTINO, processos: int = 1, fabrica: Callable[[], Any] | None = None) -> dict[str, Any]:
    """Gera a demonstração estática em `destino`. `fabrica` (testes) devolve as fontes; sem ela, o armazém real. O
    plano (companhias e datas) e o `indice.json` vêm da rota /api/v1/demonstracao (chiocca.v2.demonstracao)."""
    inicio = time.monotonic()
    destino = Path(destino)
    destino.mkdir(parents=True, exist_ok=True)
    global _CLIENTE
    _CLIENTE = None
    c = _cliente(fabrica)
    r_indice = c.get("/api/v1/demonstracao")
    indice = _json(r_indice)
    plano_pronto: Plano = {e["cd_cvm"]: e["datas"] for e in r_indice.json()["empresas"]}
    escritos: list[tuple[str, int]] = []
    # empresa na data, nas duas línguas (rápido: só a própria companhia)
    for cd, datas in plano_pronto.items():
        for data in datas:
            for lang in LINGUAS:
                r = c.get(f"/api/v1/empresas/{cd}", params={"data_referencia": data, "idioma": lang})
                caminho = f"empresas/{cd}/{data}/{lang}.json"
                escritos.append((caminho, _grava(destino, caminho, _json(r))))
    testado = _json(c.get("/api/v1/como-o-motor-foi-testado"))
    escritos.append(("como-o-motor-foi-testado.json", _grava(destino, "como-o-motor-foi-testado.json", testado)))
    # investigações, agrupadas por exercício e data
    grupos: dict[tuple[str, int], list[str]] = defaultdict(list)
    for cd, datas in plano_pronto.items():
        for data, exs in datas.items():
            for ex in exs:
                grupos[(data, ex)].append(cd)
    tarefas = [(d, ex, cds, str(destino), fabrica) for (d, ex), cds in sorted(grupos.items())]
    if processos > 1 and fabrica is None:
        with get_context("fork").Pool(processos, initializer=_zera_cliente) as pool:
            for parte in pool.imap_unordered(gerar_grupo, tarefas):
                escritos += parte
    else:
        for tarefa in tarefas:
            escritos += gerar_grupo(tarefa)
    escritos.append(("indice.json", _grava(destino, "indice.json", indice)))
    manifesto = {
        "gerado_por": "python -m chiocca.v2.demonstracao_estatica",
        # a data da geração fica só aqui: as investigações saem sem carimbo, e o arquivo que não mudou de conteúdo sai
        # com os mesmos bytes (o gh-pages só recebe o que mudou)
        "gerado_em": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "commit": _commit(),
        "empresas": len(plano_pronto),
        "investigacoes": sum(len(exs) for d in plano_pronto.values() for exs in d.values()),
        "arquivos": len(escritos) + 1,
        "bytes": sum(n for _, n in escritos),
        "segundos": round(time.monotonic() - inicio, 1),
        "processos": processos,
    }
    _grava(destino, "manifesto.json", (json.dumps(manifesto, ensure_ascii=False, indent=1) + "\n").encode("utf-8"))
    return manifesto


def _commit() -> str | None:
    try:
        return subprocess.run(["git", "rev-parse", "HEAD"], cwd=base.RAIZ, capture_output=True, text=True,
                              check=True).stdout.strip()  # fmt: skip
    except (OSError, subprocess.CalledProcessError):
        return None


def _zera_cliente() -> None:
    global _CLIENTE
    _CLIENTE = None


def main(argv: list[str]) -> None:
    processos = int(argv[argv.index("--processos") + 1]) if "--processos" in argv else 1
    destino = Path(argv[argv.index("--destino") + 1]) if "--destino" in argv else DESTINO
    m = gerar(destino, processos)
    print(json.dumps(m, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main(sys.argv[1:])
