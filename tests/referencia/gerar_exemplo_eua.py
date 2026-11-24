"""Exemplo calculado à mão do estudo dos EUA (pré-registro dos EUA, seção 7), separado do pacote chiocca.

Origem: escrito em 24/11/2026, depois do registro (commit a527b9e) e antes de qualquer código do estudo, a partir do
texto registrado (seções 2, 3, 4 e 7), como os exemplos do estudo 1 e do motor v2. Não importa o pacote chiocca, o
numpy nem o pandas: é uma implementação à parte, com frações exatas nas bordas das faixas. O código do estudo tem de
reproduzir estes valores. Limite: as duas implementações partem do mesmo texto e foram escritas com ajuda de IA; a
conferência pega erro de implementação, não erro no texto.

Um grupo FICTÍCIO de 14 companhias com 10-K do exercício de 2022 (data de referência 31/12/2022), em linhas no formato
dos Financial Statement Data Sets (`sub.txt`, `num.txt` e `pre.txt`), e uma taxa de referência fictícia. Dez companhias
são avaliadas; as outras quatro testam as exclusões (financeira, SPAC, sem receita e sem versão pública até o corte).

Regras de implementação que o texto registrado não detalha e que este exemplo fixa (o código segue as mesmas):
(i)   valor de uma tag numa data: só da própria companhia (`coreg` e `segments` vazios), em USD, na taxonomia us-gaap,
      com `qtrs` 0 nas contas de saldo e 4 nas de fluxo; com mais de um, o primeiro na ordem do arquivo;
(ii)  data de t-1: a data dos números da versão usada entre 330 e 400 dias antes da data de referência (a mais
      frequente; no empate, a mais recente); t-1 vem do mesmo 10-K;
(iii) versão pública no corte (`data_corte`: último dia do quarto mês depois do fim do exercício): entre o 10-K original
      e os 10-K/A com pelo menos um valor de uma tag do mapa na data de referência, a última entregue até o corte
      (no mesmo dia, a de maior número de entrega); só os números dessa entrega valem;
(iv)  números do Benford: os da versão usada, da própria companhia, em unidades que começam por USD (com o lucro por
      ação, como na DFP), na data de referência, com `qtrs` 0 ou 4, diferentes de zero, cuja tag está em `pre.txt` da
      entrega numa demonstração BS, IS ou CF, fora de parênteses (`inpth` 0); cada número uma vez;
(v)   ordem de entrada (empates de quantidade nas faixas do Benford): pelo CIK, crescente;
(vi)  sinais das despesas na convenção da DFP: custo das vendas, despesas de vendas e administrativas e despesa
      financeira negativos; a depreciação positiva, como na DFC indireta; as despesas de vendas e as administrativas
      (que o v1 soma) vêm juntas na SG&A: `despesas_vendas` recebe a SG&A e `despesas_gerais_adm`, zero.

Uso: python tests/referencia/gerar_exemplo_eua.py saida.json
"""

import json
import math
import re
import sys
from datetime import date, timedelta
from fractions import Fraction
from pathlib import Path

OUT = Path(sys.argv[1])
TOLERANCIA = 1e-9

PERIODO, ANTERIOR, DOIS_ANTES = "20221231", "20211231", "20201231"
EXERCICIO = 2022

# ---------------------------------------------------------------------------------------------------------------------
# O mapa das contas (pré-registro dos EUA, seções 3.1, 3.1.1 e 3.1.3), na ordem de preferência
# ---------------------------------------------------------------------------------------------------------------------

SALDO = {
    "ativo_total": ["Assets"],
    "ativo_circulante": ["AssetsCurrent"],
    "contas_a_receber": ["AccountsReceivableNetCurrent", "ReceivablesNetCurrent"],
    "imobilizado": ["PropertyPlantAndEquipmentNet"],
    "passivo_circulante": ["LiabilitiesCurrent"],
    "patrimonio_liquido": [
        "StockholdersEquity",
        "StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest",
    ],
    "emprestimos_lp": ["LongTermDebtNoncurrent", "LongTermDebtAndCapitalLeaseObligations"],
}
FLUXO = {
    "caixa_operacional": [
        "NetCashProvidedByUsedInOperatingActivities",
        "NetCashProvidedByUsedInOperatingActivitiesContinuingOperations",
    ],
    "depreciacao": ["DepreciationDepletionAndAmortization", "DepreciationAndAmortization", "Depreciation"],
    "lucro_liquido": ["NetIncomeLoss", "ProfitLoss"],
}
RECEITA = [
    "Revenues",
    "RevenueFromContractWithCustomerExcludingAssessedTax",
    "SalesRevenueNet",
    "SalesRevenueGoodsNet",
    "RevenueFromContractWithCustomerIncludingAssessedTax",
    "SalesRevenueServicesNet",
    "OilAndGasRevenue",
]
CUSTO = ["CostOfRevenue", "CostOfGoodsAndServicesSold", "CostOfGoodsSold"]
JUROS = ["InterestExpense", "InterestExpenseDebt", "InterestExpenseNonoperating", "InterestAndDebtExpense"]
JUROS_LARGO = {"InterestAndDebtExpense"}
FORNECEDORES = ["AccountsPayableCurrent", "AccountsPayableAndAccruedLiabilitiesCurrent"]
FORNECEDORES_LARGO = {"AccountsPayableAndAccruedLiabilitiesCurrent"}
EQUITY_COM_MINORITARIOS = [
    "StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest",
    "StockholdersEquity",
]
TAGS_DO_MAPA = sorted(
    {
        *(t for ts in SALDO.values() for t in ts),
        *(t for ts in FLUXO.values() for t in ts),
        *RECEITA,
        *CUSTO,
        *JUROS,
        *FORNECEDORES,
        "GrossProfit",
        "SellingGeneralAndAdministrativeExpense",
        "IncomeLossFromContinuingOperations",
        "IncomeLossFromDiscontinuedOperationsNetOfTax",
        "DebtCurrent",
        "LongTermDebtCurrent",
        "ShortTermBorrowings",
        "Liabilities",
        "LiabilitiesAndStockholdersEquity",
    }
)
TAGS_DE_FLUXO = {
    *(t for ts in FLUXO.values() for t in ts),
    *RECEITA,
    *CUSTO,
    *JUROS,
    "GrossProfit",
    "SellingGeneralAndAdministrativeExpense",
    "IncomeLossFromContinuingOperations",
    "IncomeLossFromDiscontinuedOperationsNetOfTax",
}
DEMONSTRACAO = {
    **{t: "IS" for t in TAGS_DE_FLUXO},
    **{t: "CF" for t in FLUXO["caixa_operacional"] + FLUXO["depreciacao"]},
}

# ---------------------------------------------------------------------------------------------------------------------
# As companhias fictícias e os números de cada 10-K
# ---------------------------------------------------------------------------------------------------------------------

# Valores de referência (t-1, t), em dólares, que cada companhia multiplica pela escala e ajusta.
BASE = {
    "receita": (1_000_000, 1_200_000),
    "custo": (600_000, 760_000),
    "bruto": (400_000, 440_000),
    "receber": (150_000, 210_000),
    "circulante": (500_000, 560_000),
    "imobilizado": (300_000, 320_000),
    "ativo": (1_100_000, 1_250_000),
    "passivo_circulante": (250_000, 300_000),
    "fornecedores": (90_000, 120_000),
    "cp": (50_000, 60_000),
    "lp": (200_000, 230_000),
    "passivo": (600_000, 700_000),
    "pl": (500_000, 550_000),
    "sga": (200_000, 230_000),
    "juros": (18_000, 22_000),
    "lucro_cont": (80_000, 95_000),
    "lucro": (80_000, 95_000),
    "caixa": (100_000, 70_000),
    "depreciacao": (30_000, 31_000),
}

# (CIK, nome fictício, SIC, escala, ajustes por chave (t-1, t), papel). Os papéis dizem quais tags a entrega usa.
COMPANHIAS = [
    (9000001, "ALFA FICTICIA INC", "3571", 1.0, {}, "base"),
    (
        9000002,
        "BETA FICTICIA INC",
        "2834",
        1.3,
        {"fornecedores": (100_000, 110_000)},
        "receita_ampliada_bruto_derivado",
    ),
    (9000003, "GAMA FICTICIA INC", "3674", 0.8, {"juros": (15_000, 17_000)}, "juros_caixa_divida_somada"),
    (9000004, "DELTA FICTICIA INC", "5812", 1.6, {"lucro": (90_000, 101_000)}, "juros_largos_lucro_passivo"),
    (9000005, "EPSILON FICTICIA INC", "7372", 0.6, {}, "sem_receber"),
    (9000006, "ZETA FICTICIA INC", "3714", 2.0, {}, "emendas"),
    (9000007, "ETA FICTICIA INC", "4911", 1.1, {"passivo": (900_000, 1_100_000)}, "receita_contrato_divida_total"),
    (9000008, "TETA FICTICIA INC", "2911", 0.9, {"fornecedores": (80_000, 300_000)}, "receita_petroleo"),
    (
        9000009,
        "IOTA FICTICIA INC",
        "3841",
        0.7,
        {"cp": (10_000, 12_000), "lp": (20_000, 22_000), "juros": (8_000, 9_000)},
        "base",
    ),
    (
        9000010,
        "CAPA FICTICIA INC",
        "5331",
        1.2,
        {
            "receber": (100_000, 400_000),
            "bruto": (450_000, 330_000),
            "custo": (550_000, 870_000),
            "lucro_cont": (60_000, 160_000),
            "caixa": (90_000, 20_000),
        },
        "base",
    ),
    (9000011, "LAMBDA FICTICIA BANCORP", "6022", 3.0, {}, "base"),
    (9000012, "MI FICTICIA ACQUISITION CORP", "6770", 0.5, {}, "base"),
    (9000013, "NI FICTICIA HOLDINGS INC", "3990", 0.4, {}, "sem_receita"),
    (9000014, "XI FICTICIA INC", "3420", 1.0, {}, "entregue_depois_do_corte"),
    (9000015, "OMICRON FICTICIA INC", "3089", 1.4, {}, "base"),
    (9000016, "PI FICTICIA INC", "2086", 0.75, {}, "base"),
    (9000017, "RO FICTICIA INC", "3559", 1.9, {}, "base"),
    (9000018, "SIGMA FICTICIA INC", "7389", 0.55, {}, "base"),
    (9000019, "TAU FICTICIA INC", "4213", 1.15, {}, "base"),
    (9000020, "UPSILON FICTICIA INC", "3949", 2.4, {}, "base"),
]
FILLERS = {
    9000001: 6,
    9000002: 9,
    9000003: 4,
    9000004: 12,
    9000005: 0,
    9000006: 7,
    9000007: 5,
    9000008: 11,
    9000009: 8,
    9000010: 13,
    9000011: 5,
    9000012: 5,
    9000013: 5,
    9000014: 5,
    9000015: 15,
    9000016: 3,
    9000017: 10,
    9000018: 16,
    9000019: 2,
    9000020: 14,
}
# Perturbação por companhia nos valores de t, para que nenhum sinal empate entre companhias por arredondamento.
PERTURBA = {
    "receber": 0.013,
    "fornecedores": 0.021,
    "juros": 0.017,
    "caixa": -0.019,
    "passivo": 0.011,
    "sga": 0.007,
    "depreciacao": 0.009,
}


def valores_da(cik, escala, ajustes):
    """Os valores (t-1, t) de cada chave, em dólares inteiros; t perturbado pelo índice da companhia."""
    i = cik - 9000001
    out = {}
    for chave, (v1, v0) in BASE.items():
        a1, a0 = ajustes.get(chave, (v1, v0))
        if chave not in ajustes and chave in PERTURBA:
            a0 = a0 * (1 + PERTURBA[chave] * i)
        out[chave] = (round(a1 * escala), round(a0 * escala))
    return out


def tags_da(papel):
    """As tags que a entrega usa para cada chave (ou uma lista de tags somadas), conforme o papel."""
    t = {
        "receita": ["Revenues"],
        "custo": ["CostOfRevenue"],
        "bruto": ["GrossProfit"],
        "receber": ["AccountsReceivableNetCurrent"],
        "circulante": ["AssetsCurrent"],
        "imobilizado": ["PropertyPlantAndEquipmentNet"],
        "ativo": ["Assets"],
        "passivo_circulante": ["LiabilitiesCurrent"],
        "fornecedores": ["AccountsPayableCurrent"],
        "cp": ["LongTermDebtCurrent"],
        "lp": ["LongTermDebtNoncurrent"],
        "passivo": ["Liabilities"],
        "pl": ["StockholdersEquity"],
        "sga": ["SellingGeneralAndAdministrativeExpense"],
        "juros": ["InterestExpense"],
        "lucro_cont": ["IncomeLossFromContinuingOperations"],
        "lucro": ["NetIncomeLoss"],
        "caixa": ["NetCashProvidedByUsedInOperatingActivities"],
        "depreciacao": ["DepreciationDepletionAndAmortization"],
    }
    t["cp"] = ["DebtCurrent"]
    if papel == "receita_ampliada_bruto_derivado":
        t.update(
            receita=["SalesRevenueGoodsNet"], bruto=[], fornecedores=["AccountsPayableAndAccruedLiabilitiesCurrent"]
        )
    elif papel == "juros_caixa_divida_somada":
        t.update(
            juros=["InterestExpenseNonoperating"],
            caixa=["NetCashProvidedByUsedInOperatingActivitiesContinuingOperations"],
            cp=["LongTermDebtCurrent", "ShortTermBorrowings"],
        )
    elif papel == "juros_largos_lucro_passivo":
        t.update(
            juros=["InterestAndDebtExpense"], lucro_cont=[], passivo=[], lp=["LongTermDebtAndCapitalLeaseObligations"]
        )
    elif papel == "sem_receber":
        t.update(receber=[])
    elif papel == "receita_contrato_divida_total":
        t.update(receita=["RevenueFromContractWithCustomerIncludingAssessedTax"])
    elif papel == "receita_petroleo":
        t.update(receita=["OilAndGasRevenue"])
    elif papel == "sem_receita":
        t.update(receita=[], bruto=[])
    return t


def adsh(cik, k):
    return f"{cik:010d}-23-{k:06d}"


def linhas_da_entrega(cik, numero, papel, v, fillers, mexe=None):
    """As linhas de num.txt e pre.txt de uma entrega (10-K ou 10-K/A com números)."""
    a = adsh(cik, numero)
    tags = tags_da(papel)
    num: list[list[str]] = []
    pre: list[list[str]] = []

    def fato(tag, ddate, qtrs, valor, uom="USD", version="us-gaap/2022", coreg="", segments=""):
        num.append([a, tag, version, ddate, str(qtrs), uom, segments, coreg, str(valor)])

    def apresenta(tag, stmt, version="us-gaap/2022", inpth="0"):
        pre.append([a, "2", str(len(pre) + 1), stmt, inpth, "H", tag, version, tag, "0"])

    v = dict(v)
    if mexe:
        v.update(mexe)
    for chave, lista in tags.items():
        if not lista:
            continue
        valores = v[chave]
        fluxo = lista[0] in TAGS_DE_FLUXO
        for tag in lista:
            partes = (valores[0] // len(lista), valores[1] // len(lista)) if len(lista) > 1 else valores
            if len(lista) > 1 and tag == lista[-1]:  # a soma fecha no valor da chave
                partes = (valores[0] - partes[0] * (len(lista) - 1), valores[1] - partes[1] * (len(lista) - 1))
            sinal = 1
            fato(tag, PERIODO, 4 if fluxo else 0, partes[1] * sinal)
            fato(tag, ANTERIOR, 4 if fluxo else 0, partes[0] * sinal)
            if fluxo:  # o 10-K traz três anos de resultado: t-2 não pode virar t-1
                fato(tag, DOIS_ANTES, 4, round(partes[0] * 0.9))
            apresenta(tag, DEMONSTRACAO.get(tag, "BS"))
    if (
        papel == "juros_largos_lucro_passivo"
    ):  # o lucro das operações continuadas sai do lucro líquido e o passivo total
        descontinuadas = (-4_000, 6_000)  # da diferença entre o passivo mais o PL e o PL com minoritários
        for ddate, x in ((ANTERIOR, descontinuadas[0]), (PERIODO, descontinuadas[1])):
            fato("IncomeLossFromDiscontinuedOperationsNetOfTax", ddate, 4, x)
        apresenta("IncomeLossFromDiscontinuedOperationsNetOfTax", "IS")
        minoritarios = (40_000, 50_000)
        for ddate, i in ((ANTERIOR, 0), (PERIODO, 1)):
            fato(
                "StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest",
                ddate,
                0,
                v["pl"][i] + minoritarios[i],
            )
            fato("LiabilitiesAndStockholdersEquity", ddate, 0, v["ativo"][i])
        apresenta("StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest", "BS")
        apresenta("LiabilitiesAndStockholdersEquity", "BS")
    # Lucro por ação (USD/shares, conta no Benford) e ações (shares, não conta)
    fato("EarningsPerShareBasic", PERIODO, 4, "1.25", uom="USD/shares")
    apresenta("EarningsPerShareBasic", "IS")
    fato("WeightedAverageNumberOfSharesOutstandingBasic", PERIODO, 4, 76000, uom="shares")
    apresenta("WeightedAverageNumberOfSharesOutstandingBasic", "IS")
    # Números que não podem entrar no mapa nem no Benford
    fato("Assets", PERIODO, 0, 7_777_777, coreg="SUBSIDIARIA FICTICIA")
    fato("Revenues", PERIODO, 4, 333_333, segments="ProductOrServiceAxis=Fict")
    fato("Assets", PERIODO, 0, 8_888_888, uom="EUR")
    fato("Revenues", PERIODO, 1, 444_444)  # trimestre
    fato("Revenues", "20220630", 2, 555_555)  # outra data
    fato("Revenues", PERIODO, 4, 666_666, version=f"{cik:010d}-22")  # taxonomia da companhia
    fato("StockRepurchasedDuringPeriodValue", PERIODO, 4, 25_000)
    apresenta("StockRepurchasedDuringPeriodValue", "EQ")  # demonstração das mutações, fora do Benford
    fato("AllowanceForDoubtfulAccountsReceivableCurrent", PERIODO, 0, 4_000)
    apresenta("AllowanceForDoubtfulAccountsReceivableCurrent", "BS", inpth="1")  # entre parênteses
    fato("OtherAssetsNoncurrent", PERIODO, 0, 0)
    apresenta("OtherAssetsNoncurrent", "BS")  # zero
    fato("EntityCommonStockSharesOutstanding", PERIODO, 0, 80000, uom="shares")  # da capa, sem pre
    # Linhas extras do balanço, da taxonomia da companhia, com o primeiro dígito escolhido
    for k in range(fillers):
        digito = (k * (cik % 7 + 2)) % 9 + 1
        tag = f"FictItem{k + 1:02d}"
        fato(tag, PERIODO, 0, digito * 10_000 + 37, version=f"{cik:010d}-22")
        apresenta(tag, "BS", version=f"{cik:010d}-22")
    return num, pre


def entregas():
    """sub.txt, num.txt e pre.txt de todas as entregas do exemplo."""
    sub, num, pre = [], [], []

    def entrega(cik, nome, sic, numero, form, filed, papel, v, fillers, mexe=None, so_capa=False):
        a = adsh(cik, numero)
        sub.append([a, str(cik), nome, sic, form, PERIODO, str(EXERCICIO), "FY", filed, "0"])
        if so_capa:  # 10-K/A só com a capa (parte III): nenhuma tag do mapa
            num.append([a, "EntityCommonStockSharesOutstanding", "dei/2022", PERIODO, "0", "shares", "", "", "80000"])
            return
        n, p = linhas_da_entrega(cik, numero, papel, v, fillers, mexe)
        num.extend(n)
        pre.extend(p)

    for cik, nome, sic, escala, ajustes, papel in COMPANHIAS:
        v = valores_da(cik, escala, ajustes)
        filed = "20230515" if papel == "entregue_depois_do_corte" else "20230301"
        entrega(cik, nome, sic, 1, "10-K", filed, papel, v, FILLERS[cik])
        if papel == "emendas":
            entrega(cik, nome, sic, 2, "10-K/A", "20230320", papel, v, 0, so_capa=True)
            mexe = {"receita": (v["receita"][0], v["receita"][1] - 300_000), "receber": (v["receber"][0], 500_000)}
            entrega(cik, nome, sic, 3, "10-K/A", "20230415", papel, v, FILLERS[cik] + 2, mexe=mexe)
            mexe2 = {"receita": (v["receita"][0], 9_000_000)}
            entrega(cik, nome, sic, 4, "10-K/A", "20230610", papel, v, FILLERS[cik], mexe=mexe2)
    for linha in sub:  # o 10-K original das companhias com emenda depois fica marcado (prevrpt)
        if linha[1] == "9000006" and linha[4] == "10-K":
            linha[9] = "1"
    return sub, num, pre


# ---------------------------------------------------------------------------------------------------------------------
# A taxa de referência fictícia (a Effective Federal Funds Rate no estudo, seção 3.2)
# ---------------------------------------------------------------------------------------------------------------------

TAXA: dict = {
    "de": "2022-01-01",
    "ate": "2022-12-31",
    "valor": 2.0,
    "fora_da_janela": [["2021-12-31", 9.0], ["2023-01-01", 9.0]],
}


def taxa_media(fim):
    """Média das taxas diárias nos 12 meses que terminam no fim do exercício (sem o dia de um ano antes), em fração."""
    inicio = date(fim.year - 1, fim.month, fim.day)
    dias = []
    d = date.fromisoformat(TAXA["de"])
    while d <= date.fromisoformat(TAXA["ate"]):
        dias.append((d, TAXA["valor"]))
        d += timedelta(days=1)
    dias += [(date.fromisoformat(x), v) for x, v in TAXA["fora_da_janela"]]
    janela = [v for x, v in dias if inicio < x <= fim]
    return math.fsum(janela) / len(janela) / 100


# ---------------------------------------------------------------------------------------------------------------------
# As regras: versão pública, valores, mapa, sinais
# ---------------------------------------------------------------------------------------------------------------------


def data_corte(fim):
    mes = fim.month + 4
    ano = fim.year + (mes - 1) // 12
    mes = (mes - 1) % 12 + 1
    proximo = date(ano + (mes == 12), mes % 12 + 1, 1)
    return proximo - timedelta(days=1)


def do_dia(texto):
    return date(int(texto[:4]), int(texto[4:6]), int(texto[6:]))


def valor(linhas, tag, ddate, fluxo):
    for a, t, version, d, qtrs, uom, segments, coreg, v in linhas:
        if (
            t == tag
            and d == ddate
            and version.startswith("us-gaap")
            and uom == "USD"
            and not coreg
            and not segments
            and qtrs == ("4" if fluxo else "0")
        ):
            return float(v)
    return None


def tem_numero_do_mapa(linhas):
    return any(
        t in TAGS_DO_MAPA
        and d == PERIODO
        and version.startswith("us-gaap")
        and uom == "USD"
        and not coreg
        and not segments
        and qtrs in ("0", "4")
        for a, t, version, d, qtrs, uom, segments, coreg, v in linhas
    )


def data_anterior(linhas):
    fim = do_dia(PERIODO)
    contagem: dict[str, int] = {}
    for linha in linhas:
        d = do_dia(linha[3])
        if 330 <= (fim - d).days <= 400:
            contagem[linha[3]] = contagem.get(linha[3], 0) + 1
    return max(contagem, key=lambda x: (contagem[x], x)) if contagem else None


def primeiro(linhas, tags, ddate, fluxo):
    for tag in tags:
        x = valor(linhas, tag, ddate, fluxo)
        if x is not None:
            return x, tag
    return None, None


def mapa(linhas, ddate):
    """As contas da versão usada numa data, com a tag de onde cada uma veio e as marcas."""
    contas, origem, marcas = {}, {}, []
    for conta, tags in SALDO.items():
        contas[conta], origem[conta] = primeiro(linhas, tags, ddate, False)
    for conta, tags in FLUXO.items():
        contas[conta], origem[conta] = primeiro(linhas, tags, ddate, True)
    receita, origem["receita_liquida"] = primeiro(linhas, RECEITA, ddate, True)
    contas["receita_liquida"] = receita
    custo, origem["custo_vendas"] = primeiro(linhas, CUSTO, ddate, True)
    contas["custo_vendas"] = None if custo is None else -custo
    bruto = valor(linhas, "GrossProfit", ddate, True)
    if bruto is not None:
        contas["resultado_bruto"], origem["resultado_bruto"] = bruto, "GrossProfit"
    elif receita is not None and custo is not None:
        contas["resultado_bruto"], origem["resultado_bruto"] = receita - custo, "receita menos custo das vendas"
    else:
        contas["resultado_bruto"], origem["resultado_bruto"] = None, None
    sga = valor(linhas, "SellingGeneralAndAdministrativeExpense", ddate, True)
    contas["despesas_vendas"] = None if sga is None else -sga
    contas["despesas_gerais_adm"] = None if sga is None else 0.0
    origem["despesas_vendas"] = "SellingGeneralAndAdministrativeExpense" if sga is not None else None
    cont = valor(linhas, "IncomeLossFromContinuingOperations", ddate, True)
    if cont is not None:
        contas["lucro_operacoes_continuadas"], origem["lucro_operacoes_continuadas"] = (
            cont,
            "IncomeLossFromContinuingOperations",
        )
    elif contas["lucro_liquido"] is not None:
        desc = valor(linhas, "IncomeLossFromDiscontinuedOperationsNetOfTax", ddate, True)
        contas["lucro_operacoes_continuadas"] = contas["lucro_liquido"] - (desc or 0.0)
        origem["lucro_operacoes_continuadas"] = (
            "lucro líquido menos descontinuadas" if desc is not None else "lucro líquido"
        )
    else:
        contas["lucro_operacoes_continuadas"], origem["lucro_operacoes_continuadas"] = None, None
    dc = valor(linhas, "DebtCurrent", ddate, False)
    if dc is not None:
        contas["emprestimos_cp"], origem["emprestimos_cp"] = dc, "DebtCurrent"
    else:
        partes = [(t, valor(linhas, t, ddate, False)) for t in ("LongTermDebtCurrent", "ShortTermBorrowings")]
        presentes = [(t, x) for t, x in partes if x is not None]
        contas["emprestimos_cp"] = math.fsum(x for _, x in presentes) if presentes else None
        origem["emprestimos_cp"] = " + ".join(t for t, _ in presentes) or None
    juros, origem["despesas_financeiras"] = primeiro(linhas, JUROS, ddate, True)
    contas["despesas_financeiras"] = None if juros is None else -juros
    if origem["despesas_financeiras"] in JUROS_LARGO:
        marcas.append("despesa_financeira_de_conceito_mais_largo")
    contas["fornecedores"], origem["fornecedores"] = primeiro(linhas, FORNECEDORES, ddate, False)
    if origem["fornecedores"] in FORNECEDORES_LARGO:
        marcas.append("fornecedores_com_provisoes")
    passivo = valor(linhas, "Liabilities", ddate, False)
    if passivo is not None:
        contas["passivo_total"], origem["passivo_total"] = passivo, "Liabilities"
    else:
        total = valor(linhas, "LiabilitiesAndStockholdersEquity", ddate, False)
        pl_total, tag_pl = primeiro(linhas, EQUITY_COM_MINORITARIOS, ddate, False)
        ok = total is not None and pl_total is not None
        contas["passivo_total"] = total - pl_total if ok else None
        origem["passivo_total"] = f"LiabilitiesAndStockholdersEquity - {tag_pl}" if ok else None
    return contas, origem, marcas


COEF = {
    "DSRI": 0.920,
    "GMI": 0.528,
    "AQI": 0.404,
    "SGI": 0.892,
    "DEPI": 0.115,
    "SGAI": -0.172,
    "TATA": 4.679,
    "LVGI": -0.327,
}
INTERCEPTO = -4.84


def componentes(t, t1):
    def razao(a, b):
        return None if a is None or b is None or b == 0 else a / b

    def pos(a, b):  # denominador positivo (receita)
        return None if a is None or b is None or b <= 0 else a / b

    def fx(f):
        try:
            return f()
        except TypeError:  # alguma conta ausente
            return None

    c = {}
    c["DSRI"] = fx(
        lambda: razao(
            pos(t["contas_a_receber"], t["receita_liquida"]), pos(t1["contas_a_receber"], t1["receita_liquida"])
        )
    )
    c["GMI"] = fx(
        lambda: razao(
            pos(t1["resultado_bruto"], t1["receita_liquida"]), pos(t["resultado_bruto"], t["receita_liquida"])
        )
    )
    aq = lambda v: 1 - (v["ativo_circulante"] + v["imobilizado"]) / v["ativo_total"]  # noqa: E731
    c["AQI"] = fx(lambda: razao(aq(t), aq(t1)))
    c["SGI"] = fx(lambda: pos(t["receita_liquida"], t1["receita_liquida"]))
    dep = lambda v: abs(v["depreciacao"]) / (abs(v["depreciacao"]) + v["imobilizado"])  # noqa: E731
    c["DEPI"] = fx(lambda: razao(dep(t1), dep(t)))
    sga = lambda v: pos(abs(v["despesas_vendas"]) + abs(v["despesas_gerais_adm"]), v["receita_liquida"])  # noqa: E731
    c["SGAI"] = fx(lambda: razao(sga(t), sga(t1)))
    c["TATA"] = fx(lambda: razao(t["lucro_operacoes_continuadas"] - t["caixa_operacional"], t["ativo_total"]))
    lv = lambda v: (v["passivo_circulante"] + v["emprestimos_lp"]) / v["ativo_total"]  # noqa: E731
    c["LVGI"] = fx(lambda: razao(lv(t), lv(t1)))
    m = None if any(x is None for x in c.values()) else INTERCEPTO + math.fsum(COEF[k] * x for k, x in c.items())
    return c, m


def dpo(v):
    if v["fornecedores"] is None or v["custo_vendas"] in (None, 0):
        return None
    return v["fornecedores"] / abs(v["custo_vendas"]) * 365


def quantil(valores, q=Fraction(9, 10)):
    """Quantil com interpolação linear entre as posições (o padrão do pandas)."""
    x = sorted(valores)
    h = (len(x) - 1) * q
    lo = math.floor(h)
    if lo + 1 >= len(x):
        return x[lo]
    return x[lo] + float(h - lo) * (x[lo + 1] - x[lo])


def percentis(valores):
    """rank(pct=True): posição média dos empates ÷ quantidade de valores calculáveis."""
    ok = [(i, v) for i, v in enumerate(valores) if v is not None]
    n = len(ok)
    out: list[float | None] = [None] * len(valores)
    for i, v in ok:
        menores = sum(1 for _, w in ok if w < v)
        iguais = sum(1 for _, w in ok if w == v)
        out[i] = (menores + (iguais + 1) / 2) / n
    return out


LEI = [math.log10(1 + 1 / d) for d in range(1, 10)]
MINIMO, FAIXAS = 20, 5


def primeiro_digito(x):
    return int(f"{abs(x):.15e}"[0])


def numeros_do_benford(num, pre, a):
    na_demonstracao = {
        (t, version)
        for aa, rep, ln, stmt, inpth, rf, t, version, pl, neg in pre
        if aa == a and stmt in ("BS", "IS", "CF") and inpth == "0"
    }
    vistos, out = set(), []
    for aa, t, version, d, qtrs, uom, segments, coreg, v in num:
        chave = (t, version, d, qtrs, uom)
        if (
            aa == a
            and (t, version) in na_demonstracao
            and d == PERIODO
            and qtrs in ("0", "4")
            and uom.startswith("USD")
            and not coreg
            and not segments
            and float(v) != 0
            and chave not in vistos
        ):
            vistos.add(chave)
            out.append(float(v))
    return out


def faixas_por_quantidade(quantidades):
    n_total = len(quantidades)
    ordem = sorted(range(n_total), key=lambda i: (quantidades[i], i))
    posicao = [0] * n_total
    for p, i in enumerate(ordem):
        posicao[i] = p + 1
    bordas = [1 + Fraction(n_total - 1) * k / FAIXAS for k in range(FAIXAS + 1)]
    return [next(k for k in range(FAIXAS) if r <= bordas[k + 1]) for r in posicao]


def calcula():
    sub, num, pre = entregas()
    corte = data_corte(do_dia(PERIODO))
    taxa = taxa_media(do_dia(PERIODO))
    linhas_de: dict[str, list[list[str]]] = {}
    for linha in num:
        linhas_de.setdefault(linha[0], []).append(linha)
    resultado = []
    for cik, nome, sic, *_ in COMPANHIAS:
        minhas = [s for s in sub if s[1] == str(cik)]
        candidatas = [
            s for s in minhas if s[4] == "10-K" or (s[4] == "10-K/A" and tem_numero_do_mapa(linhas_de.get(s[0], [])))
        ]
        ate_o_corte = [s for s in candidatas if do_dia(s[8]) <= corte]
        r: dict = {"cik": str(cik), "sic": sic, "entregas": [s[0] for s in minhas]}
        if not ate_o_corte:
            r.update(situacao="fora_sem_versao_publica", versao_usada=None)
            resultado.append(r)
            continue
        usada = max(ate_o_corte, key=lambda s: (s[8], s[0]))
        r["versao_usada"] = usada[0]
        linhas = linhas_de[usada[0]]
        if sic.isdigit() and 6000 <= int(sic) <= 6999 and sic != "6770":
            r["situacao"] = "fora_financeira"
        elif sic == "6770":
            r["situacao"] = "fora_spac"
        else:
            r["situacao"] = None
        anterior = data_anterior(linhas)
        t, origem, marcas = mapa(linhas, PERIODO)
        t1, origem1, marcas1 = mapa(linhas, anterior)
        r.update(
            data_anterior=anterior, contas_t=t, contas_t1=t1, origem_t=origem, marcas=sorted(set(marcas + marcas1))
        )
        if r["situacao"] is None and (t["receita_liquida"] is None or t["receita_liquida"] == 0):
            r["situacao"] = "fora_sem_receita"
        if r["situacao"] is None:
            r["situacao"] = "nao_financeira"
            comp, m = componentes(t, t1)
            d_t, d_t1 = dpo(t), dpo(t1)
            r["mscore_componentes"], r["mscore"] = comp, m
            r["dpo_t"], r["dpo_t1"] = d_t, d_t1
            r["dpo"] = None if d_t is None or d_t1 is None else d_t - d_t1
            divida = None
            if None not in (t["emprestimos_cp"], t["emprestimos_lp"], t1["emprestimos_cp"], t1["emprestimos_lp"]):
                divida = (t["emprestimos_cp"] + t["emprestimos_lp"] + t1["emprestimos_cp"] + t1["emprestimos_lp"]) / 2
            jur = None if t["despesas_financeiras"] is None or not divida else abs(t["despesas_financeiras"]) / divida
            r["juro_implicito"], r["taxa_media"] = jur, taxa
            r["juro"] = None if jur is None else (jur - taxa) * 100
            r["alavancagem"] = (
                None if t["passivo_total"] is None or not t["ativo_total"] else t["passivo_total"] / t["ativo_total"]
            )
            nums = numeros_do_benford(num, pre, usada[0])
            contagens = [0] * 9
            for x in nums:
                contagens[primeiro_digito(x) - 1] += 1
            n = len(nums)
            r["benford_contagens"], r["n_numeros_benford"] = contagens, n
            r["desvio_benford"] = math.fsum(abs(c / n - b) for c, b in zip(contagens, LEI)) / 9 if n else None
        resultado.append(r)
    grupo = [r for r in resultado if r["situacao"] == "nao_financeira"]
    # v1: decis do ano (DPO e regra boba), M > -1,78 e juro > taxa + 10 p.p.
    limites = {}
    for sinal in ("dpo", "alavancagem"):
        ok = [r[sinal] for r in grupo if r[sinal] is not None]
        limites[sinal] = quantil(ok)
    for r in grupo:
        r["alerta_mscore"] = None if r["mscore"] is None else r["mscore"] > -1.78
        r["alerta_dpo"] = None if r["dpo"] is None else r["dpo"] >= limites["dpo"]
        r["alerta_juro"] = None if r["juro"] is None else r["juro"] > 10.0
        r["alerta_regra_boba"] = None if r["alavancagem"] is None else r["alavancagem"] >= limites["alavancagem"]
        alertas = [r["alerta_mscore"], r["alerta_dpo"], r["alerta_juro"]]
        r["v1_avaliada"] = any(a is not None for a in alertas)
        r["v1_em_alerta"] = any(a is True for a in alertas)
        r["v1_n_sinais"] = sum(1 for a in alertas if a is True)
    # Benford: faixas e padronização entre as empresa-anos com pelo menos 20 números (ordem de entrada pelo CIK)
    elegiveis = [r for r in grupo if r["n_numeros_benford"] >= MINIMO]
    faixa = faixas_por_quantidade([r["n_numeros_benford"] for r in elegiveis])
    for r in grupo:
        r.update(
            faixa_benford=None,
            benford=None,
            benford_motivo=None if r["n_numeros_benford"] >= MINIMO else "menos_de_20_numeros",
        )
    for k in range(FAIXAS):
        membros = [r for r, f in zip(elegiveis, faixa) if f == k]
        if not membros:
            continue
        desvios = [r["desvio_benford"] for r in membros]
        media = math.fsum(desvios) / len(desvios)
        dp = math.sqrt(math.fsum((d - media) ** 2 for d in desvios) / (len(desvios) - 1)) if len(desvios) > 1 else None
        for r in membros:
            r["faixa_benford"] = k
            if dp:
                r["benford"] = (r["desvio_benford"] - media) / dp
            else:
                r["benford_motivo"] = "faixa_sem_desvio_padrao"
    # v2: percentis, escore (o maior percentil), avaliada e alerta (escore no quantil de 90% ou acima)
    for sinal in ("mscore", "dpo", "juro", "benford"):
        for r, p in zip(grupo, percentis([r[sinal] for r in grupo])):
            r[f"pct_{sinal}"] = p
    for r in grupo:
        pcts = [r[f"pct_{s}"] for s in ("mscore", "dpo", "juro", "benford") if r[f"pct_{s}"] is not None]
        r["escore"] = max(pcts) if pcts else None
        r["v2_avaliada"] = bool(pcts)
    limites["escore"] = quantil([r["escore"] for r in grupo if r["escore"] is not None])
    for r in grupo:
        r["v2_em_alerta"] = r["escore"] is not None and r["escore"] >= limites["escore"]
    return sub, num, pre, corte, taxa, limites, resultado


SUB, NUM, PRE, CORTE, TAXA_MEDIA, LIMITES, RESULTADO = calcula()


def confere_folgas():
    """Autoconferência: no grupo avaliado, os valores de cada sinal são distintos com folga e longe dos limites, para
    que a ordem dos percentis e os alertas não dependam de arredondamento entre implementações."""
    grupo = [r for r in RESULTADO if r["situacao"] == "nao_financeira"]
    for sinal in ("mscore", "dpo", "juro", "alavancagem", "benford", "escore"):
        xs = sorted(r[sinal] for r in grupo if r[sinal] is not None)
        for a, b in zip(xs, xs[1:]):
            assert b - a > 1e-6 or (sinal == "escore" and a == b == 1.0), (sinal, a, b)
    for sinal, limite in (
        ("mscore", -1.78),
        ("juro", 10.0),
        ("dpo", LIMITES["dpo"]),
        ("alavancagem", LIMITES["alavancagem"]),
    ):
        assert all(abs(r[sinal] - limite) > 1e-6 for r in grupo if r[sinal] is not None), sinal


confere_folgas()

SAIDA = {
    "sobre": (
        "Companhias e 10-K FICTÍCIOS para o exemplo calculado à mão do estudo dos EUA (pré-registro dos EUA, "
        "seção 7). Valores em dólares. O código do estudo tem de reproduzir cada valor esperado dentro da "
        "tolerância."
    ),
    "about_en": (
        "FICTITIOUS companies and 10-Ks for the hand-computed example of the US study (US pre-registration, "
        "section 7). Values in dollars. The study code must reproduce every expected value within the "
        "tolerance."
    ),
    "pre_registro": "docs/pre-registro-eua.md, seções 2, 3, 4 e 7 (commit de registro a527b9e)",
    "tolerancia_absoluta": TOLERANCIA,
    "regras_de_implementacao": [
        "(i) valor: própria companhia, USD, us-gaap, qtrs 0 (saldo) ou 4 (fluxo), o primeiro na ordem do arquivo",
        "(ii) t-1: a data dos números entre 330 e 400 dias antes da data de referência, a mais frequente",
        "(iii) versão pública: 10-K original ou 10-K/A com números do mapa, a última entregue até o corte",
        "(iv) Benford: própria companhia, unidades USD, data de referência, qtrs 0 ou 4, diferente de zero, BS/IS/CF",
        "(v) ordem de entrada pelo CIK",
        "(vi) despesas negativas (custo, SG&A, juros); depreciação positiva; SG&A em despesas_vendas",
    ],
    "entradas": {
        "colunas_sub": ["adsh", "cik", "name", "sic", "form", "period", "fy", "fp", "filed", "prevrpt"],
        "colunas_num": ["adsh", "tag", "version", "ddate", "qtrs", "uom", "segments", "coreg", "value"],
        "colunas_pre": ["adsh", "report", "line", "stmt", "inpth", "rfile", "tag", "version", "plabel", "negating"],
        "sub": SUB,
        "num": NUM,
        "pre": PRE,
        "taxa": TAXA,
    },
    "esperado": {
        "exercicio": EXERCICIO,
        "data_de_referencia": "2022-12-31",
        "data_corte": CORTE.isoformat(),
        "taxa_media": TAXA_MEDIA,
        "limites": LIMITES,
        "empresa_anos": RESULTADO,
    },
}


def compacta(texto):
    """Listas sem lista ou objeto dentro (as linhas e os vetores) numa linha só; o JSON não muda."""
    return re.sub(r"\[([^\[\]{}]*)\]", lambda m: "[" + re.sub(r"\n\s*", " ", m.group(1)).strip() + "]", texto)


OUT.write_text(compacta(json.dumps(SAIDA, ensure_ascii=False, indent=1)) + "\n", encoding="utf-8")
