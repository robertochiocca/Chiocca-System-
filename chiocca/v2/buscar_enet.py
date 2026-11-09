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

import sys
from collections.abc import Callable
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


def buscar(
    lista: pd.DataFrame,
    cache: Path = base.CACHE_ENET,
    baixar: Callable[[Path, str, int], pd.DataFrame] = enet.baixa_para_cache,
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
