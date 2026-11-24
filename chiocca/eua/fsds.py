"""Os Financial Statement Data Sets da SEC (Fase 0 dos EUA): os números das demonstrações em XBRL, por trimestre de
entrega, desde 2009.

Cada trimestre é um zip com arquivos de texto separados por tabulação; os dois que o reconhecimento usa são `sub.txt`
(uma linha por entrega: o número da entrega, o CIK, o formulário, a data de referência, o exercício fiscal, as datas de
entrega e se a entrega foi depois emendada) e `num.txt` (uma linha por número: a tag, a versão da taxonomia, a data, os
trimestres cobertos, a unidade e o valor). As colunas usadas são conferidas em cada arquivo antes de qualquer conta
(`exige`); a estrutura completa de cada arquivo é registrada como veio (`estrutura`).

Limite (decisão de Roberto de 24/11/2026): os exercícios dos EUA vão até 2024 (data de referência até 31/12/2024); os
trimestres de entrega vão até 2025T4 (`TRIMESTRES`), para pegar os 10-K do exercício de 2024 entregues com atraso e
as emendas. O lacre dos exercícios brasileiros de 2024 em diante não trata dos dados dos EUA.

O código foi escrito e testado com um arquivo sintético no formato descrito acima e rodou nos trimestres da SEC,
baixados com o User-Agent da variável de ambiente (`chiocca.eua.sec`): de 2009T1 a 2023T4 em 23/11/2026 e de 2024T1
a 2025T4 em 24/11/2026.

O ano de cada 10-K para ligar aos AAERs (`ano`) segue a convenção da Compustat, usada por Bao et al. (2020): o ano da
data de referência, ou o ano anterior quando o exercício termina de janeiro a maio. O exercício fiscal declarado pela
companhia (`fy`) é usado nas contagens por exercício.
"""

from __future__ import annotations

import io
import zipfile
from collections import defaultdict
from collections.abc import Iterable
from pathlib import Path
from typing import Any

import pandas as pd

from chiocca.eua.sec import DADOS, Cliente

URL = "https://www.sec.gov/files/dera/data/financial-statement-data-sets/{t}.zip"
ULTIMO_TRIMESTRE_ANO = 2025  # entregas até 31/12/2025 (exercícios até 2024 e as entregas atrasadas)
TRIMESTRES = [f"{a}q{q}" for a in range(2009, ULTIMO_TRIMESTRE_ANO + 1) for q in range(1, 5)]
PASTA = DADOS / "fsds"
COLUNAS_SUB = ["adsh", "cik", "sic", "form", "period", "fy", "fp", "filed", "prevrpt"]
COLUNAS_NUM = ["adsh", "tag", "version", "ddate", "qtrs", "uom"]
FORMULARIOS = ("10-K", "10-K/A", "10-KT", "10-KT/A")

# As contas que os sinais do v1 e do v2 usam, com as tags us-gaap candidatas, na ordem de preferência (proposta da
# Fase 0, a ser conferida pela cobertura). Benford usa todos os números da entrega e não precisa de mapa; a DVA não
# existe nos EUA (a depreciação vem da DFC). O peso de ganhos não recorrentes das financeiras não tem mapa aqui: os
# bancos
# usam outras linhas da taxonomia.
MAPA: dict[str, tuple[str, ...]] = {
    "ativo_total": ("Assets",),
    "ativo_circulante": ("AssetsCurrent",),
    "contas_a_receber": ("AccountsReceivableNetCurrent", "ReceivablesNetCurrent"),
    "imobilizado": ("PropertyPlantAndEquipmentNet",),
    "passivo_circulante": ("LiabilitiesCurrent",),
    "fornecedores": ("AccountsPayableCurrent", "AccountsPayableAndAccruedLiabilitiesCurrent"),
    "emprestimos_cp": ("DebtCurrent", "LongTermDebtCurrent", "ShortTermBorrowings"),
    "emprestimos_lp": ("LongTermDebtNoncurrent", "LongTermDebtAndCapitalLeaseObligations"),
    "patrimonio_liquido": (
        "StockholdersEquity",
        "StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest",
    ),
    "receita_liquida": ("Revenues", "RevenueFromContractWithCustomerExcludingAssessedTax", "SalesRevenueNet"),
    "custo_vendas": ("CostOfRevenue", "CostOfGoodsAndServicesSold", "CostOfGoodsSold"),
    "resultado_bruto": ("GrossProfit",),
    "despesas_vendas_gerais_adm": ("SellingGeneralAndAdministrativeExpense",),
    "despesas_financeiras": ("InterestExpense",),
    "lucro_operacoes_continuadas": (
        "IncomeLossFromContinuingOperations",
        "IncomeLossFromContinuingOperationsBeforeIncomeTaxesExtraordinaryItemsNoncontrollingInterest",
    ),
    "lucro_liquido": ("NetIncomeLoss", "ProfitLoss"),
    "caixa_operacional": ("NetCashProvidedByUsedInOperatingActivities",),
    "depreciacao": ("DepreciationDepletionAndAmortization", "DepreciationAndAmortization", "Depreciation"),
    "juros_pagos": ("InterestPaidNet", "InterestPaid"),
}
TAGS = sorted({t for ts in MAPA.values() for t in ts})

# Ampliação do mapa da receita (decisão de Roberto de 24/11/2026: as tags são escolhidas só pelas contagens de
# cobertura). Escritas antes de qualquer contagem: as tags us-gaap de receita total (não componentes, custos nem
# saldos) que podem entrar depois das três da proposta da Fase 0. A regra (`ampliar_receita`): entram em ordem gulosa,
# pelo maior ganho de cobertura nos 10-K da amostra (não financeiras, sem as SPACs, exercícios de 2011 a 2024), e cada
# uma só entra se acrescentar pelo menos `GANHO_MINIMO` dessas entregas.
RECEITA_CANDIDATAS: tuple[str, ...] = (
    "RevenueFromContractWithCustomerIncludingAssessedTax",
    "SalesRevenueGoodsNet",
    "SalesRevenueServicesNet",
    "SalesRevenueGoodsGross",
    "RevenuesExcludingInterestAndDividends",
    "RegulatedAndUnregulatedOperatingRevenue",
    "ElectricUtilityRevenue",
    "OilAndGasRevenue",
    "RevenueMineralSales",
    "RealEstateRevenueNet",
    "OperatingLeasesIncomeStatementLeaseRevenue",
    "OperatingLeaseLeaseIncome",
    "HealthCareOrganizationRevenue",
    "ContractsRevenue",
)
GANHO_MINIMO = 0.005
# Tags fora do mapa dos sinais, só para a cobertura das regras do rascunho (passivo total da regra boba).
TAGS_EXTRAS: tuple[str, ...] = ("Liabilities", "LiabilitiesAndStockholdersEquity")

# Ampliação de `despesas_financeiras` e de `caixa_operacional` (pedido de 24/11/2026, terceira rodada), pela mesma regra
# da receita. Escritas antes de qualquer contagem: as tags us-gaap do mesmo conceito contábil (juros da dívida; caixa
# líquido das atividades operacionais, inclusive a variante só de operações continuadas). As de conceito mais largo
# entram com uma marca (`CONCEITO_LARGO`), como a de fornecedores. Ficam fora os juros líquidos de receita de juros e os
# juros pagos (outros conceitos) e as tags de componentes (só da dívida de longo prazo, só com partes relacionadas).
AMPLIACOES: dict[str, dict[str, tuple[str, ...]]] = {
    "despesas_financeiras": {
        "base": MAPA["despesas_financeiras"],
        "candidatas": (
            "InterestExpenseNonoperating",
            "InterestExpenseOperating",
            "InterestExpenseDebt",
            "InterestExpenseBorrowings",
            "InterestAndDebtExpense",  # juros e outros encargos da dívida: mais largo
            "InterestCostsIncurred",  # inclui os juros capitalizados: mais largo
        ),
    },
    "caixa_operacional": {
        "base": MAPA["caixa_operacional"],
        "candidatas": ("NetCashProvidedByUsedInOperatingActivitiesContinuingOperations",),
    },
}
CONCEITO_LARGO: tuple[str, ...] = ("InterestAndDebtExpense", "InterestCostsIncurred")
TAGS_AMPLIACOES: tuple[str, ...] = tuple(t for a in AMPLIACOES.values() for t in (*a["base"], *a["candidatas"]))


class ColunaAusente(ValueError):
    pass


def exige(colunas: Iterable[str], esperadas: list[str], arquivo: str) -> None:
    faltam = [c for c in esperadas if c not in set(colunas)]
    if faltam:
        raise ColunaAusente(f"{arquivo}: faltam as colunas {faltam}")


def baixar(cliente: Cliente, trimestres: Iterable[str] = TRIMESTRES, pasta: Path = PASTA) -> list[dict[str, Any]]:
    """Baixa os zips que ainda não estão na pasta e devolve as linhas do manifesto (os que não existem na SEC entram
    como erro, sem parar o resto)."""
    linhas = []
    for t in trimestres:
        if not t[:4].isdigit() or int(t[:4]) > ULTIMO_TRIMESTRE_ANO:
            raise ValueError(f"{t}: depois do limite de {ULTIMO_TRIMESTRE_ANO}")
        destino = pasta / f"{t}.zip"
        if not destino.exists():
            linhas.append(cliente.baixar(URL.format(t=t), destino))
    return linhas


def estrutura(zip_caminho: Path) -> dict[str, Any]:
    """Os arquivos do zip, com as colunas e o número de linhas de cada arquivo de texto."""
    out: dict[str, Any] = {}
    with zipfile.ZipFile(zip_caminho) as z:
        for nome in sorted(z.namelist()):
            if not nome.endswith(".txt"):
                out[nome] = {"bytes": z.getinfo(nome).file_size}
                continue
            with z.open(nome) as f:
                cabecalho = f.readline().decode("utf-8").rstrip("\r\n").split("\t")
                linhas = sum(1 for _ in f)
            out[nome] = {"colunas": cabecalho, "linhas": linhas, "bytes": z.getinfo(nome).file_size}
    return out


def submissoes(zip_caminho: Path) -> pd.DataFrame:
    """As entregas de 10-K (e emendas) do trimestre, com as colunas usadas."""
    with zipfile.ZipFile(zip_caminho) as z:
        sub = pd.read_csv(io.BytesIO(z.read("sub.txt")), sep="\t", dtype=str, keep_default_na=False)
    exige(sub.columns, COLUNAS_SUB, f"{zip_caminho.name}/sub.txt")
    sub = sub[sub.form.isin(FORMULARIOS)][COLUNAS_SUB].copy()
    sub["trimestre"] = zip_caminho.stem
    sub["ano"] = ano_compustat(sub.period)
    return sub


def ano_compustat(period: pd.Series) -> pd.Series:
    """O ano do exercício pela convenção da Compustat: o ano da data de referência, ou o anterior se o exercício
    termina de janeiro a maio."""
    p = pd.to_datetime(period, format="%Y%m%d", errors="coerce")
    return (p.dt.year - (p.dt.month <= 5).astype(int)).astype("Int64")


def resumo(sub: pd.DataFrame) -> dict[str, Any]:
    """Por exercício fiscal: companhias com 10-K original, emendas, entregas emendadas depois e o prazo de entrega."""
    entrega, referencia = pd.to_datetime(sub.filed, format="%Y%m%d"), pd.to_datetime(sub.period, format="%Y%m%d")
    s = sub.assign(fy=pd.to_numeric(sub.fy, errors="coerce"), prazo=(entrega - referencia).dt.days)
    original = s[s.form == "10-K"]
    out: dict[str, Any] = {}
    for fy, g in original.dropna(subset=["fy"]).groupby("fy"):
        emendas = s[(s.form == "10-K/A") & (s.fy == fy)]
        out[str(int(fy))] = {"companhias_com_10k": int(g.cik.nunique()), "entregas_10k": len(g),
                             "entregas_10k_a": len(emendas), "10k_emendados_depois": int((g.prevrpt == "1").sum()),
                             "prazo_mediano_dias": float(g.prazo.median()),
                             "prazo_p10_dias": float(g.prazo.quantile(0.1)),
                             "prazo_p90_dias": float(g.prazo.quantile(0.9)),
                             "ate_90_dias": float((g.prazo <= 90).mean())}  # fmt: skip
    return out


def versao_publica(sub: pd.DataFrame, com_numeros: set[str], corte: str) -> pd.DataFrame:
    """A versão pública numa data de corte (AAAAMMDD): por companhia e exercício (`fy`), a última entrega até a data,
    entre o 10-K original e os 10-K/A com números das contas (`com_numeros`, os adsh das emendas com alguma tag do
    mapa); emendas sem números (só a parte III, por exemplo) não mudam a versão. Só companhia e exercício com o 10-K
    original entregue até a data."""
    s = sub[(sub.form == "10-K") | ((sub.form == "10-K/A") & sub.adsh.isin(com_numeros))]
    s = s[(s.filed <= corte) & (s.fy != "")].sort_values(["cik", "fy", "filed", "form"])
    com_original = set(zip(s.cik[s.form == "10-K"], s.fy[s.form == "10-K"]))  # só com o 10-K original
    s = s[pd.Series([par in com_original for par in zip(s.cik, s.fy)], index=s.index, dtype=bool)]
    return s.groupby(["cik", "fy"], as_index=False).last()


def versoes_por_ano(sub: pd.DataFrame, com_numeros: set[str], anos_depois: tuple[int, ...] = (1, 2),
                    ultimo_corte: str = "20251231") -> dict[str, Any]:  # fmt: skip
    """Por exercício e por corte em 31/12 de t+1 e de t+2 (só cortes até 2025): quantas companhias têm uma versão
    pública e em quantas ela é uma emenda, e não o 10-K original."""
    out: dict[str, Any] = {}
    fys = sorted({int(x) for x in sub[sub.form == "10-K"].fy if x.isdigit()})
    for fy in fys:
        linha = {}
        for k in anos_depois:
            corte = f"{fy + k}1231"
            if corte > ultimo_corte:
                continue
            v = versao_publica(sub[sub.fy == str(fy)], com_numeros, corte)
            linha[f"t+{k}"] = {"companhias": len(v), "emenda": int((v.form == "10-K/A").sum())}
        out[str(fy)] = linha
    return out


def cobertura_tags(
    zip_caminho: Path,
    sub: pd.DataFrame,
    tags: list[str] = TAGS,
    formularios: tuple[str, ...] = ("10-K",),
    receitas_anuais: bool = False,
    tags_anuais: tuple[str, ...] = (),
) -> pd.DataFrame:
    """Para cada entrega do trimestre nos formulários pedidos (o 10-K original, por padrão), as tags (das candidatas)
    com valor em dólar na data de referência da entrega, da companhia (sem co-registrante), na taxonomia us-gaap; e a
    receita do exercício (`receita`: o valor anual, de quatro trimestres, da primeira tag de `receita_liquida` do mapa
    que a entrega traz, ou vazio), para a regra das sem receita, a mesma do estudo 1: receita ausente ou zero. Com
    `receitas_anuais`, também o valor anual de cada tag us-gaap cujo nome tem "Revenue" ou "Sales" (`receitas_anuais`,
    um dicionário tag -> valor), para a ampliação do mapa da receita pela cobertura (só contagens); e o valor anual de
    cada uma das `tags_anuais` (`anuais_extras`, outro dicionário), para as outras ampliações."""
    alvo = sub[sub.form.isin(formularios)].set_index("adsh")
    with zipfile.ZipFile(zip_caminho) as z:
        with z.open("num.txt") as f:
            cabecalho = f.readline().decode("utf-8").rstrip("\r\n").split("\t")
    exige(cabecalho, COLUNAS_NUM, f"{zip_caminho.name}/num.txt")
    usar = COLUNAS_NUM + ["value"] + [c for c in ("coreg", "segments") if c in cabecalho]
    presentes: dict[str, set[str]] = defaultdict(set)
    receitas: dict[str, dict[str, float]] = defaultdict(dict)
    anuais: dict[str, dict[str, float]] = defaultdict(dict)
    extras: dict[str, dict[str, float]] = defaultdict(dict)
    tags_receita = MAPA["receita_liquida"]
    with zipfile.ZipFile(zip_caminho) as z:
        for bloco in pd.read_csv(z.open("num.txt"), sep="\t", dtype=str, keep_default_na=False, usecols=usar,
                                 chunksize=500_000):  # fmt: skip
            nome = bloco.tag.isin([*tags, *tags_anuais])
            if receitas_anuais:
                nome = nome | bloco.tag.str.contains(r"Revenue|Sales")
            b = bloco[bloco.adsh.isin(alvo.index) & nome & bloco.version.str.startswith("us-gaap")
                      & (bloco.uom == "USD")]  # fmt: skip
            for col in ("coreg", "segments"):
                if col in b.columns:
                    b = b[b[col] == ""]
            b = b[b.ddate.values == alvo.loc[b.adsh, "period"].values]
            if receitas_anuais:
                ra = b[b.tag.str.contains(r"Revenue|Sales") & (b.qtrs == "4")]
                for a, t, v in zip(ra.adsh, ra.tag, pd.to_numeric(ra.value, errors="coerce")):
                    if pd.notna(v):
                        anuais[a].setdefault(t, float(v))
            if tags_anuais:
                rx = b[b.tag.isin(tags_anuais) & (b.qtrs == "4")]
                for a, t, v in zip(rx.adsh, rx.tag, pd.to_numeric(rx.value, errors="coerce")):
                    if pd.notna(v):
                        extras[a].setdefault(t, float(v))
            b = b[b.tag.isin(tags)]
            for a, t in zip(b.adsh, b.tag):
                presentes[a].add(t)
            r = b[b.tag.isin(tags_receita) & (b.qtrs == "4")]
            for a, t, v in zip(r.adsh, r.tag, pd.to_numeric(r.value, errors="coerce")):
                if pd.notna(v):
                    receitas[a].setdefault(t, float(v))

    def receita(a: str) -> float | None:
        return next((receitas[a][t] for t in tags_receita if t in receitas[a]), None)

    return pd.DataFrame(
        [
            {"adsh": a, "form": alvo.at[a, "form"], "fy": alvo.at[a, "fy"], **{t: t in presentes[a] for t in tags},
             "receita": receita(a), **({"receitas_anuais": dict(anuais[a])} if receitas_anuais else {}),
             **({"anuais_extras": dict(extras[a])} if tags_anuais else {})}
            for a in alvo.index
        ],
        columns=["adsh", "form", "fy", *tags, "receita", *(["receitas_anuais"] if receitas_anuais else []),
                 *(["anuais_extras"] if tags_anuais else [])],
    )  # fmt: skip


def ampliar_receita(anuais: pd.Series, base: tuple[str, ...] = MAPA["receita_liquida"],
                    candidatas: tuple[str, ...] = RECEITA_CANDIDATAS, ganho_minimo: float = GANHO_MINIMO
                    ) -> dict[str, Any]:  # fmt: skip
    """A regra gulosa da ampliação, sobre os dicionários tag -> valor anual de cada 10-K da amostra: parte das tags de
    `base` e, a cada passo, acrescenta a candidata que cobre mais entregas ainda sem valor, se o ganho for de pelo
    menos `ganho_minimo` das entregas. Devolve a ordem final, o ganho de cada tag que entrou e o de cada candidata no
    primeiro passo (só contagens). Serve à receita (os padrões) e às outras contas (`AMPLIACOES`)."""
    tem = [set(d) for d in anuais]
    n = len(tem)
    cobertas = [bool(t & set(base)) for t in tem]
    escolhidas: list[str] = []
    ganhos: dict[str, int] = {}
    primeiro_passo: dict[str, int] = {}
    restantes = list(candidatas)
    while restantes:
        ganho = {c: sum(1 for t, cob in zip(tem, cobertas) if not cob and c in t) for c in restantes}
        if not primeiro_passo:
            primeiro_passo = dict(ganho)
        melhor = max(restantes, key=lambda c: (ganho[c], -restantes.index(c)))
        if n == 0 or ganho[melhor] < ganho_minimo * n:
            break
        escolhidas.append(melhor)
        ganhos[melhor] = ganho[melhor]
        cobertas = [cob or melhor in t for t, cob in zip(tem, cobertas)]
        restantes.remove(melhor)
    return {"ordem": [*base, *escolhidas], "escolhidas": escolhidas, "ganhos": ganhos,
            "ganho_no_primeiro_passo": primeiro_passo, "entregas": n}  # fmt: skip


def receita_ampliada(anuais: dict[str, float], ordem: list[str]) -> float | None:
    """O valor anual da primeira tag da ordem final que a entrega traz."""
    return next((anuais[t] for t in ordem if t in anuais), None)


def sem_receita(receita: pd.Series) -> pd.Series:
    """A regra das sem receita do estudo 1 (`chiocca.montar_base`): receita ausente ou igual a zero."""
    return receita.isna() | (receita == 0)


def cobertura_por_ano(tabela: pd.DataFrame, mapa: dict[str, tuple[str, ...]] = MAPA) -> dict[str, Any]:
    """Por exercício: a fração dos 10-K com cada conta (alguma das tags candidatas) e com cada tag."""
    out: dict[str, Any] = {}
    t = tabela[tabela.form == "10-K"] if "form" in tabela.columns else tabela
    t = t.assign(fy=pd.to_numeric(t.fy, errors="coerce")).dropna(subset=["fy"])
    for fy, g in t.groupby("fy"):
        out[str(int(fy))] = {
            "10k": len(g),
            "contas": {c: float(g[list(ts)].any(axis=1).mean()) for c, ts in mapa.items()},
            "tags": {tag: float(g[tag].mean()) for ts in mapa.values() for tag in ts},
        }
    return out
