"""Segundo cálculo do exemplo resolvido, separado do pacote chiocca.

Origem: escrito na conversa de planejamento (claude.ai, com o Claude), antes do
código do motor, e usado para gerar data/exemplo_resolvido.json. Não importa
nada do pacote chiocca: é uma implementação à parte, a partir da mesma
especificação. O teste de referência confere que o motor reproduz estes valores.
Limite: as duas implementações partem da mesma especificação e foram escritas
com ajuda de IA; a conferência pega erro de implementação, não erro na
especificação.

Entradas fictícias -> valores esperados. Gera data/exemplo_resolvido.json, o
teste de referência do motor (cada valor tem que ser reproduzido dentro da
tolerância) e a fonte dos números da seção de cálculos do dossiê.

Uso: python tests/referencia/gerar_exemplo_resolvido.py saida.json
"""

import json
import math
import sys
from pathlib import Path

OUT = Path(sys.argv[1])

# Empresa fictícia, valores em R$ mil, convenção de sinal da DFP:
# custos, despesas e saídas de caixa NEGATIVOS; depreciação como valor positivo
# (soma de volta na DFC). "depreciacao" é só depreciação, sem amortização de
# intangíveis (Beneish 1999). "emissao_titulos" vale 1 se houve emissão de ações
# ou dívida no ano (F-score). Do ano t-2 só entram as contas que o F-score usa.
ENTRADAS = {
    "t-2": {"ativo_total": 8400, "contas_a_receber": 1400},
    "t-1": {
        "receita_liquida": 10000,
        "custo_vendas": -7000,
        "resultado_bruto": 3000,
        "despesas_vendas": -1200,
        "despesas_gerais_adm": -600,
        "outras_receitas_operacionais": 0,
        "ebit": 1200,
        "despesas_financeiras": -300,
        "lucro_operacoes_continuadas": 600,
        "lucro_liquido": 600,
        "caixa_operacional": 700,
        "contas_a_receber": 1500,
        "ativo_circulante": 4000,
        "imobilizado": 3000,
        "ativo_total": 9000,
        "depreciacao": 300,
        "fornecedores": 1400,
        "emprestimos_cp": 800,
        "emprestimos_lp": 1700,
        "passivo_circulante": 3000,
        "passivo_nao_circulante": 2200,
        "patrimonio_liquido": 3800,
        "caixa_equivalentes": 600,
        "aplicacoes_financeiras": 400,
        "estoques": 1200,
        "investimentos": 0,
        "ir_csll_a_pagar": 90,
        "receitas_financeiras": 60,
        "dividendos_pagos": -120,
        "capex": -300,
        "emissao_titulos": 0,
    },
    "t": {
        "receita_liquida": 11500,
        "custo_vendas": -7820,
        "resultado_bruto": 3680,
        "despesas_vendas": -1250,
        "despesas_gerais_adm": -620,
        "outras_receitas_operacionais": 150,
        "ebit": 1960,
        "despesas_financeiras": -520,
        "lucro_operacoes_continuadas": 1000,
        "lucro_liquido": 1000,
        "caixa_operacional": 400,
        "contas_a_receber": 2300,
        "ativo_circulante": 5200,
        "imobilizado": 3100,
        "ativo_total": 10600,
        "depreciacao": 280,
        "fornecedores": 2600,
        "emprestimos_cp": 700,
        "emprestimos_lp": 1600,
        "passivo_circulante": 4000,
        "passivo_nao_circulante": 2000,
        "patrimonio_liquido": 4600,
        "caixa_equivalentes": 450,
        "aplicacoes_financeiras": 550,
        "estoques": 1500,
        "investimentos": 0,
        "ir_csll_a_pagar": 140,
        "receitas_financeiras": 40,
        "dividendos_pagos": -200,
        "capex": -380,
        "emissao_titulos": 0,
    },
}
CDI_MEDIO_T = 0.12  # ILUSTRATIVO, não é o CDI real de nenhum ano

z, a, b = ENTRADAS["t-2"], ENTRADAS["t-1"], ENTRADAS["t"]
for ano in ("t-1", "t"):  # coerência interna do exemplo
    d = ENTRADAS[ano]
    assert d["receita_liquida"] + d["custo_vendas"] == d["resultado_bruto"], ano
    assert (
        d["resultado_bruto"] + d["despesas_vendas"] + d["despesas_gerais_adm"] + d["outras_receitas_operacionais"]
        == d["ebit"]
    ), ano
    assert d["passivo_circulante"] + d["passivo_nao_circulante"] + d["patrimonio_liquido"] == d["ativo_total"], ano
    assert (
        d["caixa_equivalentes"] + d["aplicacoes_financeiras"] + d["contas_a_receber"] + d["estoques"]
        <= d["ativo_circulante"]
    ), ano
    assert d["fornecedores"] + d["emprestimos_cp"] + d["ir_csll_a_pagar"] <= d["passivo_circulante"], ano
    assert d["emprestimos_lp"] <= d["passivo_nao_circulante"], ano
assert a["imobilizado"] + abs(b["capex"]) - b["depreciacao"] == b["imobilizado"]  # imobilizado fecha
assert a["patrimonio_liquido"] + b["lucro_liquido"] - abs(b["dividendos_pagos"]) == b["patrimonio_liquido"]  # PL fecha


def margem(d):
    return d["resultado_bruto"] / d["receita_liquida"]


def aq(d):
    return 1 - (d["ativo_circulante"] + d["imobilizado"]) / d["ativo_total"]


def taxa_dep(d):
    return d["depreciacao"] / (d["depreciacao"] + d["imobilizado"])


def sga(d):
    return (abs(d["despesas_vendas"]) + abs(d["despesas_gerais_adm"])) / d["receita_liquida"]


def alav(d):
    return (d["passivo_circulante"] + d["emprestimos_lp"]) / d[
        "ativo_total"
    ]  # Beneish 1999: passivo circulante + dívida de LP


def dpo(d):
    return d["fornecedores"] / abs(d["custo_vendas"]) * 365


def divida(d):
    return d["emprestimos_cp"] + d["emprestimos_lp"]


def caixa_total(d):
    return d["caixa_equivalentes"] + d["aplicacoes_financeiras"]


def media(x, y):
    return (x + y) / 2


comp = {
    "DSRI": (b["contas_a_receber"] / b["receita_liquida"]) / (a["contas_a_receber"] / a["receita_liquida"]),
    "GMI": margem(a) / margem(b),
    "AQI": aq(b) / aq(a),
    "SGI": b["receita_liquida"] / a["receita_liquida"],
    "DEPI": taxa_dep(a) / taxa_dep(b),
    "SGAI": sga(b) / sga(a),
    "TATA": (b["lucro_operacoes_continuadas"] - b["caixa_operacional"]) / b["ativo_total"],
    "LVGI": alav(b) / alav(a),
}
COEF = {
    "const": -4.84,
    "DSRI": 0.920,
    "GMI": 0.528,
    "AQI": 0.404,
    "SGI": 0.892,
    "DEPI": 0.115,
    "SGAI": -0.172,
    "TATA": 4.679,
    "LVGI": -0.327,
}
contrib = {k: COEF[k] * v for k, v in comp.items()}
m = COEF["const"] + sum(contrib.values())

juro = abs(b["despesas_financeiras"]) / ((divida(a) + divida(b)) / 2)

# TATA alternativo (versão de balanço do artigo de 1999). Não entra no M do exemplo;
# serve para mostrar que a escolha da versão muda o número (decidir no pré-registro).
d_ac = b["ativo_circulante"] - a["ativo_circulante"]
d_cx = caixa_total(b) - caixa_total(a)
d_pc = b["passivo_circulante"] - a["passivo_circulante"]
d_dcp = b["emprestimos_cp"] - a["emprestimos_cp"]
d_ir = b["ir_csll_a_pagar"] - a["ir_csll_a_pagar"]
tata_bal = (d_ac - d_cx - (d_pc - d_dcp - d_ir) - b["depreciacao"]) / b["ativo_total"]

# Rendimento do caixa (novo, fase 2)
rend = b["receitas_financeiras"] / media(caixa_total(a), caixa_total(b))

# Dividendos sem caixa (novo, fase 2)
fcl = b["caixa_operacional"] - abs(b["capex"])
cobertura = abs(b["dividendos_pagos"]) / fcl if fcl > 0 else None


# F-score de Dechow et al. (2011), Modelo 1
def wc(d):
    return (d["ativo_circulante"] - caixa_total(d)) - (d["passivo_circulante"] - d["emprestimos_cp"])


def nco(d):
    return (d["ativo_total"] - d["ativo_circulante"] - d["investimentos"]) - (
        d["passivo_circulante"] + d["passivo_nao_circulante"] - d["passivo_circulante"] - d["emprestimos_lp"]
    )


def fin(d):
    return (d["aplicacoes_financeiras"] + d["investimentos"]) - (d["emprestimos_lp"] + d["emprestimos_cp"])


at_med = media(a["ativo_total"], b["ativo_total"])
fv = {
    "rsst_acc": ((wc(b) - wc(a)) + (nco(b) - nco(a)) + (fin(b) - fin(a))) / at_med,
    "ch_rec": (b["contas_a_receber"] - a["contas_a_receber"]) / at_med,
    "ch_inv": (b["estoques"] - a["estoques"]) / at_med,
    "soft_assets": (b["ativo_total"] - b["imobilizado"] - caixa_total(b)) / b["ativo_total"],
    "ch_cs": (b["receita_liquida"] - (b["contas_a_receber"] - a["contas_a_receber"]))
    / (a["receita_liquida"] - (a["contas_a_receber"] - z["contas_a_receber"]))
    - 1,
    "ch_roa": b["lucro_liquido"] / at_med - a["lucro_liquido"] / media(z["ativo_total"], a["ativo_total"]),
    "issue": b["emissao_titulos"],
}
FCOEF = {
    "const": -7.893,
    "rsst_acc": 0.790,
    "ch_rec": 2.518,
    "ch_inv": 1.191,
    "soft_assets": 1.979,
    "ch_cs": 0.171,
    "ch_roa": -0.932,
    "issue": 1.029,
}
fval = FCOEF["const"] + sum(FCOEF[k] * v for k, v in fv.items())
fprob = math.exp(fval) / (1 + math.exp(fval))
PROB_INCONDICIONAL = 0.0037
res = {
    "mscore_beneish": {
        "componentes": {k: round(v, 4) for k, v in comp.items()},
        "contribuicoes": {k: round(v, 4) for k, v in contrib.items()},
        "M": round(m, 4),
        "acima_de_-1.78": m > -1.78,
        "acima_de_-2.22": m > -2.22,
    },
    "dpo_salto": {
        "DPO_t-1_dias": round(dpo(a), 2),
        "DPO_t_dias": round(
            dpo(b), 4
        ),  # arredondamento ajustado para seguir o commit 70d71a5 (tolerância de 0,0001 do próprio JSON); a versão usada na Fase 0 está em eca771b; nenhuma conta mudou
        "variacao_dias": round(
            dpo(b) - dpo(a), 4
        ),  # arredondamento ajustado para seguir o commit 70d71a5 (tolerância de 0,0001 do próprio JSON); a versão usada na Fase 0 está em eca771b; nenhuma conta mudou
    },
    "juro_implicito": {
        "divida_media": (divida(a) + divida(b)) / 2,
        "juro_implicito": round(juro, 4),
        "cdi_medio_ilustrativo": CDI_MEDIO_T,
        "spread_pp": round(
            (juro - CDI_MEDIO_T) * 100, 4
        ),  # arredondamento ajustado para seguir o commit 70d71a5 (tolerância de 0,0001 do próprio JSON); a versão usada na Fase 0 está em eca771b; nenhuma conta mudou
    },
    "lucro_sem_caixa": {
        "accruals_sobre_ativo_medio": round(
            (b["lucro_liquido"] - b["caixa_operacional"]) / ((a["ativo_total"] + b["ativo_total"]) / 2), 4
        )
    },
    "peso_nao_recorrente_proxy": {
        "outras_receitas_sobre_ebit": round(b["outras_receitas_operacionais"] / abs(b["ebit"]), 4)
    },
    "tata_versao_balanco": {
        "variacoes": {
            "ativo_circulante": d_ac,
            "caixa_e_aplicacoes": d_cx,
            "passivo_circulante": d_pc,
            "emprestimos_cp": d_dcp,
            "ir_csll_a_pagar": d_ir,
        },
        "TATA_balanco": round(tata_bal, 4),
        "TATA_fluxo_de_caixa_usado_no_M": round(comp["TATA"], 4),
    },
    "rendimento_caixa": {
        "caixa_medio": media(caixa_total(a), caixa_total(b)),
        "rendimento": round(rend, 4),
        "cdi_medio_ilustrativo": CDI_MEDIO_T,
        "diferenca_pp": round((rend - CDI_MEDIO_T) * 100, 2),
    },
    "dividendos_sem_caixa": {
        "fluxo_livre": fcl,
        "dividendos_pagos": abs(b["dividendos_pagos"]),
        "cobertura_dividendos_sobre_fluxo_livre": round(cobertura, 4) if cobertura is not None else None,
        "dividendos_sobre_caixa_operacional": round(abs(b["dividendos_pagos"]) / b["caixa_operacional"], 4),
    },
    "fscore_dechow": {
        "variaveis": {k: round(v, 4) for k, v in fv.items()},
        "valor_previsto": round(fval, 4),
        "probabilidade": round(fprob, 6),
        "F": round(fprob / PROB_INCONDICIONAL, 4),
        "acima_de_1": fprob / PROB_INCONDICIONAL > 1,
        "acima_de_2.45": fprob / PROB_INCONDICIONAL > 2.45,
    },
}

# Avaliação: exemplo de contagem (ilustrativo)
AV: dict[str, float] = {
    "empresas_avaliadas": 300,
    "empresas_em_alerta": 30,
    "casos_no_gabarito": 3,
    "casos_acertados": 2,
}
AV["taxa_de_alerta"] = round(AV["empresas_em_alerta"] / AV["empresas_avaliadas"], 4)
AV["acerto"] = round(AV["casos_acertados"] / AV["casos_no_gabarito"], 4)
AV["alertas_fora_do_gabarito"] = AV["empresas_em_alerta"] - AV["casos_acertados"]
AV["alarmes_por_acerto"] = round(AV["alertas_fora_do_gabarito"] / AV["casos_acertados"], 2)

saida = {
    "sobre": "Empresa FICTÍCIA para teste de referência. Valores em R$ mil, com a convenção de sinal da DFP (custos e despesas negativos). O CDI e as contagens da avaliação são ilustrativos. O software tem que reproduzir cada valor esperado dentro da tolerância.",
    "about_en": "FICTITIOUS company for a reference test. Values in R$ thousand, using the DFP sign convention (costs and expenses negative). The CDI rate and the evaluation counts are illustrative. The software must reproduce every expected value within the tolerance.",
    "tolerancia_absoluta": 0.0001,
    "entradas": ENTRADAS,
    "cdi_medio_t_ilustrativo": CDI_MEDIO_T,
    "esperado": res,
    "avaliacao_exemplo": AV,
}
OUT.write_text(json.dumps(saida, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps(res, ensure_ascii=False, indent=1))
print(AV)
