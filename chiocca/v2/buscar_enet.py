"""Busca no ENET das versões que faltam no armazém (Fase C2): comando separado, nunca dentro de uma consulta.

Uma consulta numa data de referência pode precisar de uma versão de DFP que não está no armazém: a versão da data não
é a última (os dados abertos só trazem a última) e o consolidado dela não está no cache do ENET. A consulta não baixa
nada: devolve `versao_pendente_enet` (pergunta 9 do plano). Este comando é o caminho para buscar:

1. `pendentes`: roda o `como_era` do motor v1 sobre o armazém na data e lista as versões pendentes;
2. `buscar`: baixa cada uma com `chiocca.enet.baixa_para_cache` (rota do estudo 1, só consolidado, emenda 8) para
   `data/cache/enet`, com as mesmas regras do lacre: só exercícios liberados e só versões entregues até a data máxima;
3. remonta o armazém (`chiocca.v2.armazem.montar`), que copia as versões novas.

Uso: python -m chiocca.v2.buscar_enet AAAA-MM-DD [exercicio ...] [--listar]
     sem exercícios, todos os liberados; com --listar, só lista, sem rede.
"""

from __future__ import annotations

import json
import re
import sys
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from datetime import date
from pathlib import Path
from typing import Any

import pandas as pd

from chiocca import base, enet
from chiocca.cvm import Fontes
from chiocca.v2 import armazem
from chiocca.v2.lacre import (
    DATA_REFERENCIA_MAXIMA,
    ULTIMO_EXERCICIO_LIBERADO,
    garantir_data_referencia,
    garantir_liberado,
)

COLUNAS = ["cd_cvm", "exercicio", "dt_refer", "versao", "num_doc", "dt_receb"]


def pendentes(
    fontes: armazem.FontesArmazem, data_referencia: date | str, exercicios: range | list[int]
) -> pd.DataFrame:
    """Versões que o motor v1 precisaria na data e que não estão no armazém (só consolidado, rota do ENET)."""
    d = garantir_data_referencia(data_referencia)
    linhas: list[dict[str, Any]] = []
    for ano in exercicios:
        garantir_liberado(ano)
        idx = fontes.indice_dfp(ano)
        for p in idx[["cd_cvm", "DT_REFER"]].drop_duplicates().itertuples(index=False):
            leitura = base.como_era(fontes, p.cd_cvm, ano, corte=d, dt_refer=p.DT_REFER)  # type: ignore[arg-type]
            if leitura.status == base.PENDENTE_ENET:
                linhas.append({"cd_cvm": leitura.cd_cvm, "exercicio": ano, "dt_refer": leitura.dt_refer,
                               "versao": leitura.versao, "num_doc": leitura.num_doc,
                               "dt_receb": leitura.dt_receb})  # fmt: skip
    return pd.DataFrame(linhas, columns=COLUNAS)


def escala_da_pagina(pagina: str) -> str | None:
    """Escala informada na página do ENET: "Reais Mil" é MIL; "Reais" sem "Mil" é UNIDADE; sem nenhum dos dois, nada."""
    texto = enet._limpa(pagina)
    if "Reais Mil" in texto:
        return "MIL"
    return "UNIDADE" if re.search(r"\bReais\b", texto) else None


@contextmanager
def _registrando_escala() -> Iterator[dict[str, str]]:
    """Durante a busca, anota a escala de cada página lida pela rota do estudo 1, sem mudar o que ela grava."""
    original = enet.parse_tabela
    escalas: dict[str, str] = {}

    def com_escala(pagina: str, demonstracao: str) -> pd.DataFrame:
        esc = escala_da_pagina(pagina)
        if esc is not None:
            escalas[demonstracao] = esc
        return original(pagina, demonstracao)

    enet.parse_tabela = com_escala  # type: ignore[assignment]
    try:
        yield escalas
    finally:
        enet.parse_tabela = original  # type: ignore[assignment]


def baixar_com_escala(cache: Path, num_doc: str, versao: int) -> pd.DataFrame:
    """`chiocca.enet.baixa_para_cache` e, se a página informar, a escala em `<documento>_escala.json` (09/11/2026)."""
    with _registrando_escala() as escalas:
        d = enet.baixa_para_cache(cache, num_doc, versao)
    if escalas:
        (cache / f"{num_doc}_escala.json").write_text(json.dumps(escalas, sort_keys=True) + "\n", encoding="utf-8")
    return d


def buscar(
    lista: pd.DataFrame,
    cache: Path = base.CACHE_ENET,
    baixar: Callable[[Path, str, int], pd.DataFrame] = baixar_com_escala,
) -> pd.DataFrame:
    """Baixa cada versão pendente para o cache do ENET. Devolve a lista com o resultado de cada uma."""
    resultados = []
    for r in lista.itertuples(index=False):
        garantir_liberado(int(r.exercicio))
        if pd.to_datetime(r.dt_receb).date() > DATA_REFERENCIA_MAXIMA:
            raise ValueError(f"versão entregue depois de {DATA_REFERENCIA_MAXIMA}: só metadados ({r.num_doc})")
        if enet.le_cache(cache, str(r.num_doc)) is not None:
            resultados.append("ja_no_cache")
            continue
        try:
            baixar(cache, str(r.num_doc), int(r.versao))
            resultados.append("baixado")
        except enet.FalhaENET as e:
            resultados.append(f"falha: {e}")
    return lista.assign(resultado=resultados)


def main(argv: list[str]) -> pd.DataFrame:
    listar = "--listar" in argv
    args = [a for a in argv if a != "--listar"]
    if not args:
        raise SystemExit(__doc__)
    anos = [int(a) for a in args[1:]] or list(range(armazem.PRIMEIRO_EXERCICIO, ULTIMO_EXERCICIO_LIBERADO + 1))
    lista = pendentes(armazem.FontesArmazem(), args[0], anos)
    print(lista.to_string(index=False) if not lista.empty else "nenhuma versão pendente", flush=True)
    if listar or lista.empty:
        return lista
    r = buscar(lista)
    print(r[["num_doc", "resultado"]].to_string(index=False), flush=True)
    if (r.resultado == "baixado").any():
        armazem.montar(Fontes(base.BRUTOS, base.CACHE_ENET))
        print("armazém remontado", flush=True)
    return r


if __name__ == "__main__":
    main(sys.argv[1:])
