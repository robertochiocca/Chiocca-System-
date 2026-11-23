"""Exemplo calculado à mão do motor v2 (pré-registro do motor v2, seção 6), separado do pacote chiocca.

Origem: escrito em 23/11/2026, antes de qualquer código do v2, a partir do texto registrado do pré-registro do motor v2
(commit 313c52d, seções 3.1, 3.3 e 6), como o exemplo resolvido do estudo 1 (gerar_exemplo_resolvido.py). Não importa o
pacote chiocca, o numpy nem o pandas: é uma implementação à parte, com aritmética exata nas bordas das faixas. O código
do v2 tem de reproduzir estes valores. Limite: as duas implementações partem do mesmo texto e foram escritas com ajuda
de IA; a conferência pega erro de implementação, não erro no texto.

(a) Benford: uma tabela fictícia de empresa-anos (dois grupos num exercício e uma empresa-ano sozinha noutro), com as
    linhas de cada uma; saem os dígitos, a quantidade de números, o desvio, as faixas e o desvio padronizado.
(b) DEPI pela DVA: uma empresa-ano fictícia não financeira, dos dados abertos, sem linha de depreciação na DFC; saem os
    oito componentes do M-score, o DEPI do v1 (não calculável), a depreciação da DVA, o DEPI pela DVA e o M do v2.

Uso: python tests/referencia/gerar_exemplo_motor_v2.py saida.json
"""

import json
import math
import re
import sys
import unicodedata
from fractions import Fraction
from pathlib import Path

OUT = Path(sys.argv[1])

ULTIMO, PENULTIMO = "ÚLTIMO", "PENÚLTIMO"
TOLERANCIA = 1e-9

# ---------------------------------------------------------------------------------------------------------------------
# (a) Benford (seção 3.3)
# ---------------------------------------------------------------------------------------------------------------------

LEI = [math.log10(1 + 1 / d) for d in range(1, 10)]
MINIMO = 20  # pelo menos 20 números
FAIXAS = 5  # quintis da quantidade de números
DEMONSTRATIVOS = ("BPA", "BPP", "DRE", "DFC_MI", "DFC_MD")  # BPA, BPP, DRE e DFC (método indireto ou direto)

# Empresa-ano fictícia: (nome, exercício, grupo, DFC, quantos números de cada primeiro dígito, de 1 a 9, são gerados).
# A ordem da tabela é a ordem de entrada: o rank(method="first") desfaz os empates de quantidade por ela.
# E01 e E06 têm 24 números cada e ficam em faixas diferentes (E01 vem antes); E03 tem 19 (abaixo do mínimo); E09 tem
# exatamente 20; E14 está sozinha no exercício de 2021 (faixa de um membro só, sem desvio-padrão); nas financeiras, com
# seis empresa-anos, só a primeira faixa tem dois membros.
TABELA = [
    ("E01", 2020, "nao_financeira", "DFC_MI", [7, 4, 3, 2, 2, 2, 1, 2, 1]),
    ("E02", 2020, "nao_financeira", "DFC_MI", [9, 6, 3, 3, 2, 2, 2, 2, 1]),  # + 0,0347 (dígito 3), abaixo
    ("E03", 2020, "nao_financeira", "DFC_MD", [6, 3, 3, 2, 1, 1, 1, 1, 1]),
    ("E04", 2020, "nao_financeira", "DFC_MI", [12, 7, 5, 4, 3, 3, 2, 2, 2]),
    ("E05", 2020, "nao_financeira", "DFC_MI", [3, 3, 3, 3, 2, 2, 2, 2, 2]),
    ("E06", 2020, "nao_financeira", "DFC_MD", [8, 4, 3, 2, 2, 1, 2, 1, 1]),
    ("E07", 2020, "nao_financeira", "DFC_MI", [5, 4, 4, 4, 4, 4, 4, 3, 3]),
    ("E08", 2020, "nao_financeira", "DFC_MI", [8, 5, 3, 3, 2, 2, 2, 1, 1]),
    ("E09", 2020, "nao_financeira", "DFC_MI", [6, 4, 2, 2, 2, 1, 1, 1, 1]),
    ("E10", 2020, "nao_financeira", "DFC_MI", [14, 8, 6, 4, 4, 3, 2, 2, 2]),
    ("E11", 2020, "nao_financeira", "DFC_MD", [9, 5, 4, 3, 2, 2, 2, 1, 1]),
    ("E12", 2020, "nao_financeira", "DFC_MI", [10, 6, 4, 3, 3, 2, 2, 2, 1]),
    ("E13", 2020, "nao_financeira", "DFC_MI", [11, 7, 5, 4, 3, 3, 2, 2, 1]),
    ("E14", 2021, "nao_financeira", "DFC_MI", [7, 5, 3, 2, 2, 2, 2, 1, 1]),
    ("F01", 2020, "financeira", "DFC_MI", [6, 4, 3, 2, 2, 1, 1, 1, 1]),
    ("F02", 2020, "financeira", "DFC_MI", [8, 4, 3, 3, 2, 2, 2, 1, 1]),
    ("F03", 2020, "financeira", "DFC_MI", [2, 2, 2, 2, 2, 2, 3, 3, 2]),
    ("F04", 2020, "financeira", "DFC_MD", [9, 5, 4, 3, 2, 2, 2, 2, 1]),
    ("F05", 2020, "financeira", "DFC_MI", [7, 4, 3, 2, 2, 2, 1, 1, 1]),
    ("F06", 2020, "financeira", "DFC_MI", [8, 5, 4, 3, 2, 2, 2, 1, 1]),
]

# Valores gerados: (dígito + mantissa) × 10^expoente, em reais, um em cada três negativo (o dígito é o de |valor|), e os
# demonstrativos em rodízio. Com mantissa 0 e dígito 1 saem potências exatas de 10.
MANTISSAS = [0.0, 0.5, 0.25, 0.75, 0.125, 0.875, 0.375, 0.625]
EXPOENTES = [3, 4, 5, 6, 2, 7, 8]

# Linhas que contam, além das geradas: um valor abaixo de 1 (primeiro dígito significativo 3).
CONTAM_A_MAIS = {"E02": [["DRE", ULTIMO, 0.0347]]}

# Linhas que não contam: coluna do exercício anterior, demonstrativos fora dos quatro, zero e valor ausente. Vão em E03
# (com elas, teria 20 números) e em E09 (com elas, passaria do mínimo por mais), entre outras.
NAO_CONTAM = [
    ["BPA", PENULTIMO, 512000.0],
    ["DVA", ULTIMO, 70000.0],
    ["DMPL", ULTIMO, 2500.0],
    ["BPP", ULTIMO, 0.0],
    ["DRE", ULTIMO, None],
]
COM_LINHAS_QUE_NAO_CONTAM = ("E01", "E03", "E05", "E09", "F01")


def linhas_geradas(planejado, dfc):
    linhas = []
    i = 0
    for digito, quantos in enumerate(planejado, start=1):
        for _ in range(quantos):
            demonstrativo = ("BPA", "BPP", "DRE", dfc)[i % 4]
            valor = (digito + MANTISSAS[i % len(MANTISSAS)]) * 10 ** EXPOENTES[i % len(EXPOENTES)]
            if i % 3 == 2:
                valor = -valor
            linhas.append([demonstrativo, ULTIMO, valor])
            i += 1
    return linhas


def primeiro_digito(valor):
    """Primeiro dígito significativo de |valor|, pela notação científica em texto (sem logaritmo)."""
    return int(f"{abs(valor):.15e}"[0])


def conta_no_benford(linha):
    demonstrativo, ordem, valor = linha
    return demonstrativo in DEMONSTRATIVOS and ordem == ULTIMO and valor is not None and valor != 0


def faixas_por_quantidade(quantidades):
    """Quintis de quantidade de números: posição pela quantidade, empates pela ordem de entrada (rank 'first'); bordas
    1 + (N - 1) k / 5, k = 0..5, em frações exatas; a posição r fica na primeira faixa k com r <= borda k+1."""
    n_total = len(quantidades)
    ordem = sorted(range(n_total), key=lambda i: (quantidades[i], i))
    posicao = [0] * n_total
    for p, i in enumerate(ordem):
        posicao[i] = p + 1
    bordas = [1 + Fraction(n_total - 1) * k / FAIXAS for k in range(FAIXAS + 1)]
    return [next(k for k in range(FAIXAS) if r <= bordas[k + 1]) for r in posicao]


def benford():
    entradas, esperado = [], {}
    quantidade: dict[str, int] = {}
    desvio_de: dict[str, float] = {}
    for nome, exercicio, grupo, dfc, planejado in TABELA:
        linhas = linhas_geradas(planejado, dfc) + CONTAM_A_MAIS.get(nome, [])
        if nome in COM_LINHAS_QUE_NAO_CONTAM:
            linhas = linhas + NAO_CONTAM
        entradas.append({"empresa_ano": nome, "exercicio": exercicio, "grupo": grupo, "linhas": linhas})
        contagens = [0] * 9
        for linha in linhas:
            if conta_no_benford(linha):
                contagens[primeiro_digito(linha[2]) - 1] += 1
        n = sum(contagens)
        frequencias = [c / n for c in contagens]
        desvio = math.fsum(abs(f - b) for f, b in zip(frequencias, LEI)) / 9
        quantidade[nome], desvio_de[nome] = n, desvio
        esperado[nome] = {
            "empresa_ano": nome,
            "contagens": contagens,
            "n_numeros": n,
            "frequencias": frequencias,
            "desvio": desvio,
            "faixa": None,
            "membros_da_faixa": None,
            "media_da_faixa": None,
            "dp_da_faixa": None,
            "padronizado": None,
            "motivo": "menos de 20 números" if n < MINIMO else None,
        }
    # Faixas e padronização dentro do exercício e do grupo, só entre as empresa-anos com pelo menos 20 números.
    conjuntos: dict[tuple[int, str], list[str]] = {}
    for nome, exercicio, grupo, *_ in TABELA:
        if quantidade[nome] >= MINIMO:
            conjuntos.setdefault((exercicio, grupo), []).append(nome)
    for nomes in conjuntos.values():
        faixa = faixas_por_quantidade([quantidade[x] for x in nomes])
        for k in range(FAIXAS):
            membros = [x for x, f in zip(nomes, faixa) if f == k]
            if not membros:
                continue
            desvios = [desvio_de[x] for x in membros]
            media = math.fsum(desvios) / len(desvios)
            dp = None
            if len(desvios) > 1:  # desvio-padrão amostral (n - 1)
                dp = math.sqrt(math.fsum((d - media) ** 2 for d in desvios) / (len(desvios) - 1))
            for x in membros:
                r = esperado[x]
                r.update(faixa=k, membros_da_faixa=membros, media_da_faixa=media, dp_da_faixa=dp)
                if dp is not None and dp > 0:
                    r["padronizado"] = (desvio_de[x] - media) / dp
                else:
                    r["motivo"] = "faixa sem desvio-padrão (um membro só)"
    return {
        "lei": LEI,
        "minimo_numeros": MINIMO,
        "faixas": FAIXAS,
        "entradas": entradas,
        "esperado": [esperado[nome] for nome, *_ in TABELA],
    }


# ---------------------------------------------------------------------------------------------------------------------
# (b) DEPI pela DVA (seção 3.1)
# ---------------------------------------------------------------------------------------------------------------------

INTERCEPTO = -4.84
COEFICIENTES = {"DSRI": 0.920, "GMI": 0.528, "AQI": 0.404, "SGI": 0.892, "DEPI": 0.115, "SGAI": -0.172, "TATA": 4.679,
                "LVGI": -0.327}  # fmt: skip
CONTAS_DVA = ("7.04.01", "7.05.01", "7.07.01")  # nessa ordem de preferência
ESCALA = {"MIL": 1000, "UNIDADE": 1}

EMPRESA_ANO = {"exercicio": 2020, "grupo": "nao_financeira", "fonte": "dados_abertos", "tipo": "con", "versao": 2}

# Contas da DFP usada, em reais: (demonstrativo, código, descrição, t, t-1). A DFC não tem linha de depreciação: o v1
# não calcula o DEPI nem o M.
CONTAS = [
    ("BPA", "1", "Ativo Total", 34_000_000, 30_000_000),
    ("BPA", "1.01", "Ativo Circulante", 13_000_000, 12_000_000),
    ("BPA", "1.01.03", "Contas a Receber", 6_600_000, 5_000_000),
    ("BPA", "1.02.03", "Imobilizado", 8_800_000, 9_000_000),
    ("BPP", "2.01", "Passivo Circulante", 8_500_000, 7_000_000),
    ("BPP", "2.02.01", "Empréstimos e Financiamentos", 7_000_000, 6_000_000),
    ("DRE", "3.01", "Receita de Venda de Bens e/ou Serviços", 44_000_000, 40_000_000),
    ("DRE", "3.03", "Resultado Bruto", 12_320_000, 12_000_000),
    ("DRE", "3.04.01", "Despesas com Vendas", -3_520_000, -3_000_000),
    ("DRE", "3.04.02", "Despesas Gerais e Administrativas", -2_200_000, -2_000_000),
    ("DRE", "3.09", "Resultado Líquido das Operações Continuadas", 3_400_000, 3_000_000),
    ("DFC_MI", "6.01", "Caixa Líquido Atividades Operacionais", 2_000_000, 3_500_000),
    ("DFC_MI", "6.01.01", "Caixa Gerado nas Operações", 4_000_000, 4_200_000),
    ("DFC_MI", "6.01.01.01", "Lucro Líquido do Exercício", 3_400_000, 3_000_000),
    ("DFC_MI", "6.01.01.02", "Provisões", 600_000, 1_200_000),
    ("DFC_MI", "6.01.02", "Variações nos Ativos e Passivos", -2_000_000, -700_000),
]

# Linhas da DVA no arquivo dos dados abertos (VL_CONTA na escala do arquivo): (tipo, versão, código, descrição, escala,
# t, t-1). Só a 7.04.01 consolidada da versão 2 vale; as outras testam o tipo, a versão, a preferência entre as contas
# e o nome.
DVA = [
    ("con", 2, "7.04", "Retenções", "MIL", -1_300, -1_100),
    ("con", 2, "7.04.01", "Depreciação, Amortização e Exaustão", "MIL", -1_200, -1_000),
    ("con", 2, "7.04.02", "Outras", "MIL", -100, -100),
    ("con", 2, "7.05.01", "Depreciação de Direito de Uso", "MIL", -300, -250),
    ("con", 2, "7.07.01", "Juros", "MIL", -400, -350),
    ("ind", 2, "7.04.01", "Depreciação, Amortização e Exaustão", "MIL", -900, -800),
    ("con", 1, "7.04.01", "Depreciação, Amortização e Exaustão", "MIL", -5_000, -5_000),
]


def sem_acento(texto):
    return "".join(c for c in unicodedata.normalize("NFKD", texto) if not unicodedata.combining(c)).lower()


def linhas_das_contas():
    linhas = []
    for demonstrativo, codigo, descricao, t, t1 in CONTAS:
        linhas.append([demonstrativo, ULTIMO, codigo, descricao, float(t)])
        linhas.append([demonstrativo, PENULTIMO, codigo, descricao, float(t1)])
    return linhas


def linhas_da_dva():
    linhas = []
    for tipo, versao, codigo, descricao, escala, t, t1 in DVA:
        for ordem, valor in ((ULTIMO, t), (PENULTIMO, t1)):
            linhas.append({"tipo": tipo, "versao": versao, "ordem": ordem, "cd_conta": codigo, "ds_conta": descricao,
                           "escala_moeda": escala, "vl_conta": float(valor)})  # fmt: skip
    return linhas


def valores(linhas, ordem):
    por_codigo = {(d[:3], c): v for d, o, c, _, v in linhas if o == ordem}
    v = {
        "ativo_total": por_codigo[("BPA", "1")],
        "ativo_circulante": por_codigo[("BPA", "1.01")],
        "contas_a_receber": por_codigo[("BPA", "1.01.03")],
        "imobilizado": por_codigo[("BPA", "1.02.03")],
        "passivo_circulante": por_codigo[("BPP", "2.01")],
        "emprestimos_lp": por_codigo[("BPP", "2.02.01")],
        "receita_liquida": por_codigo[("DRE", "3.01")],
        "resultado_bruto": por_codigo[("DRE", "3.03")],
        "despesas_vendas": por_codigo[("DRE", "3.04.01")],
        "despesas_gerais_adm": por_codigo[("DRE", "3.04.02")],
        "lucro_operacoes_continuadas": por_codigo[("DRE", "3.09")],
        "caixa_operacional": por_codigo[("DFC", "6.01")],  # sem juros pagos em 6.01
    }
    # Depreciação da DFC como no v1: subcontas de 6.01.01 cujo nome contém "deprecia". Não há nenhuma.
    dep = [x for d, o, c, n, x in linhas if o == ordem and d.startswith("DFC") and c.startswith("6.01.01.")
           and "deprecia" in sem_acento(n)]  # fmt: skip
    v["depreciacao"] = sum(dep) if dep else None
    return v


def depreciacao_da_dva(linhas, ordem):
    """Primeira conta, na ordem de preferência, do mesmo tipo e versão, com "deprecia" no nome; em reais e em módulo."""
    alvo = (EMPRESA_ANO["tipo"], EMPRESA_ANO["versao"], ordem)
    for codigo in CONTAS_DVA:
        for x in linhas:
            if (x["tipo"], x["versao"], x["ordem"]) == alvo and x["cd_conta"] == codigo:
                if "deprecia" in sem_acento(x["ds_conta"]):
                    return codigo, abs(x["vl_conta"] * ESCALA[x["escala_moeda"]])
    return None, None


def componentes_sem_depi(t, t1):
    def sga(v):
        return (abs(v["despesas_vendas"]) + abs(v["despesas_gerais_adm"])) / v["receita_liquida"]

    def aq(v):
        return 1 - (v["ativo_circulante"] + v["imobilizado"]) / v["ativo_total"]

    def alav(v):
        return (v["passivo_circulante"] + v["emprestimos_lp"]) / v["ativo_total"]

    return {
        "DSRI": (t["contas_a_receber"] / t["receita_liquida"]) / (t1["contas_a_receber"] / t1["receita_liquida"]),
        "GMI": (t1["resultado_bruto"] / t1["receita_liquida"]) / (t["resultado_bruto"] / t["receita_liquida"]),
        "AQI": aq(t) / aq(t1),
        "SGI": t["receita_liquida"] / t1["receita_liquida"],
        "SGAI": sga(t) / sga(t1),
        "TATA": (t["lucro_operacoes_continuadas"] - t["caixa_operacional"]) / t["ativo_total"],
        "LVGI": alav(t) / alav(t1),
    }


def depi_dva():
    contas, dva = linhas_das_contas(), linhas_da_dva()
    t, t1 = valores(contas, ULTIMO), valores(contas, PENULTIMO)
    assert t["depreciacao"] is None and t1["depreciacao"] is None  # o v1 não calcula o DEPI
    sem_depi = componentes_sem_depi(t, t1)
    conta_t, dep_t = depreciacao_da_dva(dva, ULTIMO)
    conta_t1, dep_t1 = depreciacao_da_dva(dva, PENULTIMO)
    taxa_t = dep_t / (dep_t + t["imobilizado"])
    taxa_t1 = dep_t1 / (dep_t1 + t1["imobilizado"])
    depi = taxa_t1 / taxa_t
    componentes = {n: (depi if n == "DEPI" else sem_depi[n]) for n in COEFICIENTES}
    contribuicoes = {n: COEFICIENTES[n] * componentes[n] for n in COEFICIENTES}
    m = INTERCEPTO + math.fsum(contribuicoes.values())
    return {
        "empresa_ano": EMPRESA_ANO,
        "contas": contas,
        "dva": dva,
        "esperado": {
            "depreciacao_dfc": {"t": None, "t-1": None},
            "v1": {"componentes": {n: (None if n == "DEPI" else sem_depi[n]) for n in COEFICIENTES}, "DEPI": None,
                   "M": None},  # fmt: skip
            "depreciacao_dva": {"t": dep_t, "t-1": dep_t1, "conta_t": conta_t, "conta_t-1": conta_t1},
            "taxa_depreciacao": {"t": taxa_t, "t-1": taxa_t1},
            "v2": {"componentes": componentes, "contribuicoes": contribuicoes, "DEPI": depi, "M": m,
                   "marca_depreciacao_dva": True},  # fmt: skip
            # Se a versão usada fosse a do ENET (sem DVA), o DEPI ficaria como no v1.
            "se_a_versao_fosse_do_enet": {"DEPI": None, "M": None, "marca_depreciacao_dva": False},
        },
    }


SAIDA = {
    "sobre": (
        "Empresa-anos FICTÍCIAS para o exemplo calculado à mão do motor v2 (pré-registro do motor v2, seção 6). "
        "Valores em reais nas contas e na escala do arquivo na DVA. O código do v2 tem de reproduzir cada valor "
        "esperado dentro da tolerância."
    ),
    "about_en": (
        "FICTITIOUS company-years for the hand-computed example of engine v2 (engine v2 preregistration, section 6). "
        "Account values in reais; DVA values in the file's scale. The v2 code must reproduce every expected value "
        "within the tolerance."
    ),
    "pre_registro": "docs/pre-registro-motor-v2.md, seções 3.1, 3.3 e 6 (commit de registro 313c52d)",
    "tolerancia_absoluta": TOLERANCIA,
    "benford": benford(),
    "depi_pela_dva": depi_dva(),
}


def compacta(texto):
    """Listas sem lista ou objeto dentro (as linhas e os vetores) numa linha só; o JSON não muda."""
    return re.sub(r"\[([^\[\]{}]*)\]", lambda m: "[" + re.sub(r"\n\s*", " ", m.group(1)).strip() + "]", texto)


OUT.write_text(compacta(json.dumps(SAIDA, ensure_ascii=False, indent=1)) + "\n", encoding="utf-8")
