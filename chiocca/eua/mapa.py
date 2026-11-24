"""O mapa das contas do estudo dos EUA (pré-registro dos EUA, seções 3.1, 3.1.1 e 3.1.3), sobre as linhas dos Financial
Statement Data Sets.

As listas de tags são as do texto registrado, na ordem de preferência; as de `chiocca/eua/fsds.py` são as da Fase 0 e
das contagens de cobertura, e um teste confere que as finais coincidem. Nenhuma tag fora das candidatas entra.

Regras de implementação que o texto registrado não detalha, as mesmas do exemplo calculado à mão
(`tests/referencia/gerar_exemplo_eua.py`, regras (i) a (vi)):
(i)   valor de uma tag numa data: só da própria companhia (`coreg` e `segments` vazios), em USD, na taxonomia us-gaap,
      com `qtrs` 0 nas contas de saldo e 4 nas de fluxo; com mais de um, o primeiro na ordem do arquivo. Um valor que
      não é número conta como ausente;
(ii)  data de t-1: a data dos números da versão usada (todas as linhas de `num.txt` da entrega) entre 330 e 400 dias
      antes da data de referência, a mais frequente; no empate, a mais recente. t-1 vem do mesmo 10-K;
(iii) (em `chiocca.eua.estudo`) versão pública no corte;
(iv)  números do Benford: os da versão usada, da própria companhia, em unidades que começam por USD, na data de
      referência, com `qtrs` 0 ou 4, diferentes de zero, cuja tag está em `pre.txt` da entrega numa demonstração BS, IS
      ou CF, fora de parênteses (`inpth` 0); cada número uma vez (tag, versão, data, `qtrs` e unidade);
(v)   (em `chiocca.eua.estudo`) ordem de entrada pelo CIK;
(vi)  sinais das despesas na convenção da DFP: custo das vendas, SG&A e despesa financeira negativos; a depreciação
      como vem (positiva, como na DFC indireta); a SG&A em `despesas_vendas` e zero em `despesas_gerais_adm`.
"""

from __future__ import annotations

import math
from collections.abc import Mapping
from datetime import date

import numpy as np
import pandas as pd

COLUNAS_NUM = ["adsh", "tag", "version", "ddate", "qtrs", "uom", "segments", "coreg", "value"]
COLUNAS_PRE = ["adsh", "report", "line", "stmt", "inpth", "rfile", "tag", "version", "plabel", "negating"]

SALDO: dict[str, tuple[str, ...]] = {
    "ativo_total": ("Assets",),
    "ativo_circulante": ("AssetsCurrent",),
    "contas_a_receber": ("AccountsReceivableNetCurrent", "ReceivablesNetCurrent"),
    "imobilizado": ("PropertyPlantAndEquipmentNet",),
    "passivo_circulante": ("LiabilitiesCurrent",),
    "patrimonio_liquido": (
        "StockholdersEquity",
        "StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest",
    ),
    "emprestimos_lp": ("LongTermDebtNoncurrent", "LongTermDebtAndCapitalLeaseObligations"),
}
FLUXO: dict[str, tuple[str, ...]] = {
    "caixa_operacional": (
        "NetCashProvidedByUsedInOperatingActivities",
        "NetCashProvidedByUsedInOperatingActivitiesContinuingOperations",
    ),
    "depreciacao": ("DepreciationDepletionAndAmortization", "DepreciationAndAmortization", "Depreciation"),
    "lucro_liquido": ("NetIncomeLoss", "ProfitLoss"),
}
RECEITA: tuple[str, ...] = (
    "Revenues",
    "RevenueFromContractWithCustomerExcludingAssessedTax",
    "SalesRevenueNet",
    "SalesRevenueGoodsNet",
    "RevenueFromContractWithCustomerIncludingAssessedTax",
    "SalesRevenueServicesNet",
    "OilAndGasRevenue",
)
CUSTO: tuple[str, ...] = ("CostOfRevenue", "CostOfGoodsAndServicesSold", "CostOfGoodsSold")
JUROS: tuple[str, ...] = (
    "InterestExpense",
    "InterestExpenseDebt",
    "InterestExpenseNonoperating",
    "InterestAndDebtExpense",
)
JUROS_LARGO = frozenset({"InterestAndDebtExpense"})
FORNECEDORES: tuple[str, ...] = ("AccountsPayableCurrent", "AccountsPayableAndAccruedLiabilitiesCurrent")
FORNECEDORES_LARGO = frozenset({"AccountsPayableAndAccruedLiabilitiesCurrent"})
EQUITY_COM_MINORITARIOS: tuple[str, ...] = (
    "StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest",
    "StockholdersEquity",
)
BRUTO, SGA = "GrossProfit", "SellingGeneralAndAdministrativeExpense"
CONTINUADAS, DESCONTINUADAS = "IncomeLossFromContinuingOperations", "IncomeLossFromDiscontinuedOperationsNetOfTax"
DIVIDA_CP, PARTES_DIVIDA_CP = "DebtCurrent", ("LongTermDebtCurrent", "ShortTermBorrowings")
PASSIVO, PASSIVO_E_PL = "Liabilities", "LiabilitiesAndStockholdersEquity"

TAGS_DE_FLUXO = frozenset(
    {*(t for ts in FLUXO.values() for t in ts), *RECEITA, *CUSTO, *JUROS, BRUTO, SGA, CONTINUADAS, DESCONTINUADAS}
)
TAGS_DO_MAPA = frozenset(
    {*(t for ts in SALDO.values() for t in ts), *TAGS_DE_FLUXO, *FORNECEDORES, DIVIDA_CP, *PARTES_DIVIDA_CP, PASSIVO,
     PASSIVO_E_PL}  # fmt: skip
)
MARCA_JUROS = "despesa_financeira_de_conceito_mais_largo"
MARCA_FORNECEDORES = "fornecedores_com_provisoes"
DEMONSTRACOES_BENFORD = {"BS": "BPA", "IS": "DRE", "CF": "DFC_MI"}  # os nomes da DFP que o Benford do v2 conta
DIAS_T1 = (330, 400)

Valores = Mapping[tuple[str, str, str], float]  # (tag, data, qtrs) -> valor, de uma entrega


def numero(texto: pd.Series) -> pd.Series:
    return pd.to_numeric(texto, errors="coerce")


def proprios(num: pd.DataFrame) -> pd.DataFrame:
    """As linhas da própria companhia (sem co-registrante nem segmento), com `qtrs` 0 ou 4 e valor numérico (`v`)."""
    f = num[(num.coreg == "") & (num.segments == "") & num.qtrs.isin(["0", "4"])]
    f = f.assign(v=numero(f.value))
    return f[np.isfinite(f.v.to_numpy(dtype=float))]


def valores_do_mapa(num: pd.DataFrame) -> dict[str, dict[tuple[str, str, str], float]]:
    """Por entrega, os valores das tags do mapa em dólar, na taxonomia us-gaap: o primeiro de cada (tag, data, qtrs)."""
    f = proprios(num)
    f = f[f.version.str.startswith("us-gaap") & (f.uom == "USD") & f.tag.isin(TAGS_DO_MAPA)]
    f = f.drop_duplicates(["adsh", "tag", "ddate", "qtrs"], keep="first")
    out: dict[str, dict[tuple[str, str, str], float]] = {}
    for a, t, d, q, v in zip(f.adsh, f.tag, f.ddate, f.qtrs, f.v):
        out.setdefault(a, {})[(t, d, q)] = float(v)
    return out


def tem_numero_do_mapa(valores: Valores, periodo: str) -> bool:
    """Se a entrega traz pelo menos um valor de uma tag do mapa na data de referência (regra (iii))."""
    return any(d == periodo for _, d, _ in valores)


def _dia(texto: str) -> date | None:
    """A data AAAAMMDD, ou None se não é uma data válida (a linha fica fora da contagem de t-1)."""
    try:
        return date(int(texto[:4]), int(texto[4:6]), int(texto[6:8])) if len(texto) == 8 and texto.isdigit() else None
    except ValueError:
        return None


def contagem_de_datas(num: pd.DataFrame) -> pd.Series:
    """Quantas linhas de `num.txt` cada entrega tem em cada data (todas as linhas, sem filtro)."""
    return num.groupby(["adsh", "ddate"], sort=False).size()


def datas_anteriores(contagem: pd.Series, periodos: Mapping[str, str]) -> dict[str, str | None]:
    """A data de t-1 de cada entrega (regra (ii)), pela contagem de linhas por (entrega, data)."""
    candidatas: dict[str, dict[str, int]] = {}
    for (a, d), n in contagem.items():
        if a in periodos and (dia := _dia(d)) is not None and (fim := _dia(periodos[a])) is not None:
            if DIAS_T1[0] <= (fim - dia).days <= DIAS_T1[1]:
                candidatas.setdefault(a, {})[d] = int(n)
    out: dict[str, str | None] = {}
    for a in periodos:
        c = candidatas.get(a, {})
        out[a] = max(c, key=lambda x: (c[x], x)) if c else None
    return out


def _valor(v: Valores, tag: str, data: str | None, fluxo: bool) -> float | None:
    return None if data is None else v.get((tag, data, "4" if fluxo else "0"))


def _primeiro(v: Valores, tags: tuple[str, ...], data: str | None, fluxo: bool) -> tuple[float | None, str | None]:
    for tag in tags:
        x = _valor(v, tag, data, fluxo)
        if x is not None:
            return x, tag
    return None, None


def contas(v: Valores, data: str | None) -> tuple[dict[str, float | None], dict[str, str | None], list[str]]:
    """As contas de uma entrega numa data (seção 3.1), com a tag ou a regra de onde cada uma veio e as marcas."""
    c: dict[str, float | None] = {}
    o: dict[str, str | None] = {}
    marcas: list[str] = []
    for nome, tags in SALDO.items():
        c[nome], o[nome] = _primeiro(v, tags, data, False)
    for nome, tags in FLUXO.items():
        c[nome], o[nome] = _primeiro(v, tags, data, True)
    receita, o["receita_liquida"] = _primeiro(v, RECEITA, data, True)
    c["receita_liquida"] = receita
    custo, o["custo_vendas"] = _primeiro(v, CUSTO, data, True)
    c["custo_vendas"] = None if custo is None else -custo
    bruto = _valor(v, BRUTO, data, True)
    if bruto is not None:
        c["resultado_bruto"], o["resultado_bruto"] = bruto, BRUTO
    elif receita is not None and custo is not None:
        c["resultado_bruto"], o["resultado_bruto"] = receita - custo, "receita menos custo das vendas"
    else:
        c["resultado_bruto"], o["resultado_bruto"] = None, None
    sga = _valor(v, SGA, data, True)
    c["despesas_vendas"] = None if sga is None else -sga
    c["despesas_gerais_adm"] = None if sga is None else 0.0
    o["despesas_vendas"] = SGA if sga is not None else None
    continuadas = _valor(v, CONTINUADAS, data, True)
    if continuadas is not None:
        c["lucro_operacoes_continuadas"], o["lucro_operacoes_continuadas"] = continuadas, CONTINUADAS
    elif (lucro := c["lucro_liquido"]) is not None:
        desc = _valor(v, DESCONTINUADAS, data, True)
        c["lucro_operacoes_continuadas"] = lucro - (desc or 0.0)
        o["lucro_operacoes_continuadas"] = "lucro líquido menos descontinuadas" if desc is not None else "lucro líquido"
    else:
        c["lucro_operacoes_continuadas"], o["lucro_operacoes_continuadas"] = None, None
    divida_cp = _valor(v, DIVIDA_CP, data, False)
    if divida_cp is not None:
        c["emprestimos_cp"], o["emprestimos_cp"] = divida_cp, DIVIDA_CP
    else:
        presentes = [(t, x) for t in PARTES_DIVIDA_CP if (x := _valor(v, t, data, False)) is not None]
        c["emprestimos_cp"] = math.fsum(x for _, x in presentes) if presentes else None
        o["emprestimos_cp"] = " + ".join(t for t, _ in presentes) or None
    juros, o["despesas_financeiras"] = _primeiro(v, JUROS, data, True)
    c["despesas_financeiras"] = None if juros is None else -juros
    if o["despesas_financeiras"] in JUROS_LARGO:
        marcas.append(MARCA_JUROS)
    c["fornecedores"], o["fornecedores"] = _primeiro(v, FORNECEDORES, data, False)
    if o["fornecedores"] in FORNECEDORES_LARGO:
        marcas.append(MARCA_FORNECEDORES)
    passivo = _valor(v, PASSIVO, data, False)
    if passivo is not None:
        c["passivo_total"], o["passivo_total"] = passivo, PASSIVO
    else:
        total = _valor(v, PASSIVO_E_PL, data, False)
        pl, tag_pl = _primeiro(v, EQUITY_COM_MINORITARIOS, data, False)
        c["passivo_total"] = total - pl if total is not None and pl is not None else None
        o["passivo_total"] = f"{PASSIVO_E_PL} - {tag_pl}" if c["passivo_total"] is not None else None
    return c, o, marcas


def numeros_do_benford(num: pd.DataFrame, pre: pd.DataFrame, periodos: Mapping[str, str]) -> pd.DataFrame:
    """Os números do Benford de cada entrega (regra (iv)): `adsh`, `demonstracao` (o nome da DFP da primeira
    demonstração BS, IS ou CF em que a tag aparece) e `valor`, na ordem do arquivo."""
    p = pre[pre.stmt.isin(list(DEMONSTRACOES_BENFORD)) & (pre.inpth == "0")]
    p = p.drop_duplicates(["adsh", "tag", "version"], keep="first")[["adsh", "tag", "version", "stmt"]]
    f = proprios(num)
    f = f[f.uom.str.startswith("USD") & (f.v != 0) & (f.ddate.to_numpy() == f.adsh.map(periodos).to_numpy())]
    f = f.drop_duplicates(["adsh", "tag", "version", "ddate", "qtrs", "uom"], keep="first")
    f = f.merge(p, on=["adsh", "tag", "version"], how="inner", sort=False)
    return pd.DataFrame(
        {
            "adsh": f.adsh.to_numpy(),
            "demonstracao": f.stmt.map(DEMONSTRACOES_BENFORD).to_numpy(),
            "valor": f.v.to_numpy(),
        }
    )
