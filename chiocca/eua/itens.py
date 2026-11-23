"""Um rótulo novo para a Fase 0 dos EUA (pedido de 23/11/2026, tarefa 3): os 8-K com o item 4.02 ("Non-Reliance on
Previously Issued Financial Statements or a Related Audit Report or Completed Interim Review"), a comunicação de que as
demonstrações já publicadas não devem mais ser usadas, o mesmo conceito da republicação do estudo 2 no Brasil.

A fonte é o campo de itens (`items`) do histórico de entregas de cada companhia no EDGAR, no arquivo único
`submissions.zip` da SEC (um JSON por companhia, com as entregas recentes e, para quem tem mais de mil, arquivos
complementares `-submissions-NNN.json`). Só contagens: nenhum valor de sinal, acerto, alerta ou ranking, e nenhum
nome de companhia ou de pessoa é guardado (só o CIK, em memória).

Nada de 2024 em diante: só as entregas com data até 31/12/2023 entram nas contas (o arquivo da SEC é um retrato do dia
em que foi baixado e traz entregas até essa data).
"""

from __future__ import annotations

import json
import zipfile
from collections import defaultdict
from collections.abc import Iterable, Iterator
from pathlib import Path
from typing import Any

from chiocca.eua.sec import DADOS, Cliente

URL = "https://www.sec.gov/Archives/edgar/daily-index/bulkdata/submissions.zip"
ARQUIVO = DADOS / "edgar" / "submissions.zip"
PRIMEIRO_ANO = 2009
ULTIMO_ANO = 2023
ITEM = "4.02"


def baixar(cliente: Cliente, destino: Path = ARQUIVO) -> list[dict[str, Any]]:
    """Baixa o submissions.zip se ainda não está na pasta (um pedido só)."""
    return [] if destino.exists() else [cliente.baixar(URL, destino)]


def tem_item(itens: str, item: str = ITEM) -> bool:
    """Se o campo de itens do EDGAR (itens separados por vírgula, como "4.02,9.01") traz o item."""
    return item in {x.strip() for x in itens.split(",")}


def _colunas(bloco: dict[str, Any]) -> Iterator[tuple[str, str, str, str]]:
    """(número da entrega, data, formulário, itens) de um bloco de entregas no formato do EDGAR."""
    n = len(bloco.get("accessionNumber", []))
    itens = bloco.get("items") or [""] * n
    yield from zip(bloco["accessionNumber"], bloco["filingDate"], bloco["form"], itens)


def entregas(caminho: Path = ARQUIVO, formularios: Iterable[str] = ("8-K", "8-K/A", "10-K", "10-K/A")
             ) -> Iterator[dict[str, Any]]:  # fmt: skip
    """As entregas dos formulários pedidos, de 2009 a 2023, uma linha por companhia e entrega (uma entrega de várias
    companhias aparece uma vez para cada CIK)."""
    alvo = set(formularios)
    with zipfile.ZipFile(caminho) as z:
        for nome in z.namelist():
            if not nome.endswith(".json"):
                continue
            dados = json.loads(z.read(nome))
            if "filings" in dados:  # o arquivo principal da companhia
                cik, bloco = int(dados["cik"]), dados["filings"]["recent"]
            else:  # arquivo complementar: CIK##########-submissions-NNN.json
                cik, bloco = int(nome[3:13]), dados
            for adsh, dia, form, itens in _colunas(bloco):
                if form in alvo and PRIMEIRO_ANO <= int(dia[:4]) <= ULTIMO_ANO:
                    yield {"cik": cik, "adsh": adsh, "data": dia, "form": form, "itens": itens or ""}


def contagens(linhas: Iterable[dict[str, Any]], ciks_10k: dict[int, str], sic_6770: set[int] | None = None
              ) -> dict[str, Any]:  # fmt: skip
    """Por ano de entrega: os 8-K e 8-K/A com o item 4.02, as companhias e os casos novos, quantos se ligam a um CIK
    com 10-K nos dados da SEC (`ciks_10k`: CIK -> data, AAAAMMDD, do primeiro 10-K nos Financial Statement Data Sets)
    e quantos 10-K e 10-K/A. Um caso é uma companhia com 8-K 4.02 num ano; o primeiro caso da companhia desde 2009 é
    contado à parte (cada companhia uma vez). `sic_6770`: os CIKs com o código SIC 6770 (blank checks, as SPACs) nos
    dados da SEC."""
    sic_6770 = sic_6770 or set()
    por_ano: dict[str, dict[str, Any]] = defaultdict(lambda: defaultdict(set))
    primeiro: dict[int, str] = {}
    for x in linhas:
        ano, form = x["data"][:4], x["form"]
        a = por_ano[ano]
        if form in ("10-K", "10-K/A"):
            a[form].add(x["adsh"])
        elif tem_item(x["itens"]):
            a[form + " 4.02"].add(x["adsh"])
            if form == "8-K":
                a["ciks"].add(x["cik"])
                if x["data"][:10].replace("-", "") >= ciks_10k.get(x["cik"], "99999999"):
                    a["ciks_com_10k_antes"].add(x["cik"])
                if x["cik"] not in primeiro or x["data"] < primeiro[x["cik"]]:
                    primeiro[x["cik"]] = x["data"]
    novos: dict[str, int] = defaultdict(int)
    for dia in primeiro.values():
        novos[dia[:4]] += 1
    out = {}
    for ano in sorted(por_ano):
        a = por_ano[ano]
        out[ano] = {
            "8k_402": len(a["8-K 4.02"]),
            "8k_a_402": len(a["8-K/A 4.02"]),
            "companhias_8k_402": len(a["ciks"]),
            "companhias_8k_402_sic_6770": len(a["ciks"] & sic_6770),
            "companhias_novas_8k_402": novos[ano],
            "companhias_com_10k_fsds": sum(c in ciks_10k for c in a["ciks"]),
            "companhias_com_10k_fsds_antes": len(a["ciks_com_10k_antes"]),
            "10k_edgar": len(a["10-K"]),
            "10k_a_edgar": len(a["10-K/A"]),
        }
    return out
