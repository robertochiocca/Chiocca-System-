"""Contexto e famílias de contexto (Fase C2, segunda parte), pelas especificações de docs/contratos.md, seção 3.

Nada aqui é regra de alerta nem muda o motor v1: percentis, histórico, Altman Z'' (risco financeiro) e Piotroski F
(qualidade financeira) são exibição, ao lado dos sinais do motor, e as famílias nunca se somam.

- **Percentil** (`percentil`): posição do valor entre os valores de referência, em percentual, pelo posto médio:
  100 × (quantos são menores + metade dos iguais) ÷ n. Com menos de `N_MINIMO` (10) valores, fica nulo com o motivo.
- **Histórico** (`historico`): a série da própria empresa nos exercícios anteriores, como era na data de referência;
  mediana, quartis (interpolação linear) e a faixa de Tukey (quartis ± 1,5 × IQR), com a posição do valor atual
  (dentro, acima ou abaixo). Com menos de `EXERCICIOS_MINIMOS` (5) exercícios anteriores, fica nulo com o motivo.
  Método descrito no contrato (detecção do `insights.py` da Carchuna, só a faixa; o código não foi trazido).
- **Altman Z''** (`altman_z2`), Altman (2000), p. 27: Z'' = 6,56·X1 + 3,26·X2 + 6,72·X3 + 1,05·X4, com
  X1 = (1.01 − 2.01) ÷ 1; X2 = (2.03.04 + 2.03.05) ÷ 1 (adaptação brasileira); X3 = 3.05 ÷ 1; X4 = 2.03 ÷ (2.01 + 2.02).
  Sem a constante do Emerging Market Score, sem tabela de rating e sem zonas: a fonte disponível não define zonas
  para o Z''. Financeiras: "não se aplica". Conta ausente ou ativo total zero: não calculável, sem imputação.
- **Piotroski F** (`piotroski_f`), Piotroski (2000), pp. 7-10: nove sinais binários, com AT início = ativo total de
  t−1 e AT médio = média do ativo total de t e t−1. Valores de t−1 do comparativo (PENÚLTIMO) da DFP de t; de t−2,
  do comparativo da DFP de t−1 na versão pública na data. Mostra "F = x/9 (y calculáveis)"; componente que falta não
  é imputado. Dívida de longo prazo zero nos dois anos: ΔLEVER = 0, com marca (o artigo só define "caiu = 1,
  subiu = 0", p. 8; o 0 no empate é escolha do projeto). EQ_OFFER: linhas de 6.03 achadas pelo padrão congelado de
  "emissões" (reconhecimento, parte 4.2) e, entre elas, só as de ações ou capital, que é a definição do próprio
  artigo ("did not issue common equity", p. 9), não uma adaptação. A adaptação é só esta: ações preferenciais também
  contam, porque no Brasil são capital próprio, e a linha é identificada por texto na DFC. Soma positiva é emissão
  (0), soma zero é não emissão (1); sem linha ou com soma negativa, não calculável.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

import pandas as pd

from chiocca.texto import normaliza
from chiocca.v2.validade import Motivo, Resultado

N_MINIMO = 10
EXERCICIOS_MINIMOS = 5
COEF_Z2 = {"X1": 6.56, "X2": 3.26, "X3": 6.72, "X4": 1.05}
SEM_ZONA = Motivo(
    "sem zona de corte: a fonte disponível não define zonas para o Z''",
    "no cut-off zone: the available source does not define zones for Z''",
)
VALIDADE_Z2 = Motivo(
    "coeficientes estimados fora do Brasil; modelos de falência perdem validade com o tempo (Pereira e Martins 2015, p. 25)",
    "coefficients estimated outside Brazil; bankruptcy models lose validity over time (Pereira and Martins 2015, p. 25)",
)
NAO_SE_APLICA = Motivo("não se aplica a financeiras", "does not apply to financial companies")
DIVIDA_ZERO = Motivo(
    "sem dívida de longo prazo nos dois anos: a variação da alavancagem (ΔLEVER) é zero e o sinal vale 0 (escolha do projeto; o artigo só define caiu = 1, subiu = 0, p. 8)",
    "no long-term debt in either year: the change in leverage (ΔLEVER) is zero and the signal is 0 (project choice; the article only defines fell = 1, rose = 0, p. 8)",
)
ADAPTACAO_EQ = Motivo(
    'Sem emissão de ações (EQ_OFFER), pela DFC: linhas de 6.03 do padrão congelado de "emissões" (reconhecimento, parte 4.2), só as de ações ou capital, como define o artigo ("did not issue common equity", p. 9); adaptação: ações preferenciais também contam, porque no Brasil são capital próprio, e a linha é identificada por texto na DFC',
    'No equity issuance (EQ_OFFER), from the cash flow statement: 6.03 lines of the frozen "emissões" pattern (reconnaissance, part 4.2), only those about shares or capital, as the article defines it ("did not issue common equity", p. 9); adaptation: preferred shares also count, because in Brazil they are equity, and the line is identified by text in the cash flow statement',
)


def _motivo(pt: str, en: str) -> Motivo:
    return Motivo(pt, en)


def percentil(valor: float, referencia: list[float], n_minimo: int = N_MINIMO) -> dict[str, Any]:
    vals = [float(v) for v in referencia if v is not None and not pd.isna(v)]
    n = len(vals)
    if n < n_minimo:
        return {"valor": None, "n": n, "motivo": _motivo(f"menos de {n_minimo} empresas com o valor calculável",
                                                          f"fewer than {n_minimo} companies with a computable value")}  # fmt: skip
    menores = sum(1 for v in vals if v < valor)
    iguais = sum(1 for v in vals if v == valor)
    return {"valor": 100.0 * (menores + 0.5 * iguais) / n, "n": n, "motivo": None}


def distribuicao(referencia: list[float], n_minimo: int = N_MINIMO, faixas: int = 10) -> dict[str, Any]:
    """Distribuição agregada do setor e ano (Fase E): quantis e histograma de faixas iguais entre os percentis 5 e 95,
    com as contagens abaixo e acima. Sem nome nem valor de nenhuma empresa; com menos de `n_minimo`, só o motivo."""
    vals = sorted(float(v) for v in referencia if v is not None and not pd.isna(v))
    n = len(vals)
    if n < n_minimo:
        return {"n": n, "motivo": _motivo(f"menos de {n_minimo} empresas com o valor calculável",
                                          f"fewer than {n_minimo} companies with a computable value")}  # fmt: skip
    s = pd.Series(vals)
    quantis = {f"p{q}": float(s.quantile(q / 100)) for q in (10, 25, 50, 75, 90)}
    baixo, alto = float(s.quantile(0.05)), float(s.quantile(0.95))
    if alto <= baixo:
        alto = baixo + 1e-9
    passo = (alto - baixo) / faixas
    limites = [baixo + i * passo for i in range(faixas + 1)]
    contagens = [0] * faixas
    for v in vals:
        if baixo <= v <= alto:
            contagens[min(int((v - baixo) / passo), faixas - 1)] += 1
    return {"n": n, "quantis": quantis, "limites": limites, "contagens": contagens,
            "abaixo": sum(1 for v in vals if v < baixo), "acima": sum(1 for v in vals if v > alto), "motivo": None}  # fmt: skip


def historico(serie: dict[int, float | None], atual: float | None, minimo: int = EXERCICIOS_MINIMOS) -> dict[str, Any]:
    anos = sorted(a for a, v in serie.items() if v is not None and not pd.isna(v))
    pontos = [[a, float(v)] for a, v in sorted(serie.items()) if a in anos and v is not None]  # para a linha do tempo
    if len(anos) < minimo or atual is None:
        return {"exercicios": anos, "serie": pontos,
                "motivo": _motivo(f"menos de {minimo} exercícios anteriores com valor",
                                  f"fewer than {minimo} previous fiscal years with a value")}  # fmt: skip
    s = pd.Series([float(v) for a, v in sorted(serie.items()) if a in anos and v is not None])
    q1, q3, med = float(s.quantile(0.25)), float(s.quantile(0.75)), float(s.median())
    iqr = q3 - q1
    baixo, alto = q1 - 1.5 * iqr, q3 + 1.5 * iqr
    posicao = "acima" if atual > alto else "abaixo" if atual < baixo else "dentro"
    return {"exercicios": anos, "serie": pontos, "mediana": med, "q1": q1, "q3": q3, "faixa_tukey": [baixo, alto],
            "posicao": posicao, "motivo": None}  # fmt: skip


def _v(contas: pd.DataFrame, dem: str, cod: str, ordem: str) -> float | None:
    c = contas[(contas.demonstracao == dem) & (contas.cd_conta == cod) & (contas.ordem == ordem)]
    return None if c.empty else float(c.valor.iloc[0])


@dataclass
class Indicador:
    """Um indicador de contexto com os componentes, as contas usadas e as marcas."""

    resultado: Resultado
    componentes: dict[str, Any] = field(default_factory=dict)
    contas: list[tuple[str, str, str]] = field(default_factory=list)  # (demonstração, código, coluna)
    marcas: list[Motivo] = field(default_factory=list)
    texto: str | None = None


CONTAS_Z2 = [("BPA", "1"), ("BPA", "1.01"), ("BPP", "2.01"), ("BPP", "2.02"), ("BPP", "2.03"), ("BPP", "2.03.04"),
             ("BPP", "2.03.05"), ("DRE", "3.05")]  # fmt: skip


def altman_z2(contas: pd.DataFrame, grupo: str | None) -> Indicador:
    if grupo == "financeira":
        return Indicador(Resultado.indefinido(NAO_SE_APLICA, codigo="nao_se_aplica"))
    usadas = [(d, c, "ÚLTIMO") for d, c in CONTAS_Z2]
    v = {c: _v(contas, d, c, "ÚLTIMO") for d, c in CONTAS_Z2}
    faltam = [c for c, x in v.items() if x is None]
    if faltam:
        return Indicador(Resultado.indefinido(_motivo("conta ausente: " + ", ".join(faltam), "missing account: " + ", ".join(faltam)),
                                              codigo="conta_ausente"), contas=usadas)  # fmt: skip
    at, pc, pnc = v["1"], v["2.01"], v["2.02"]
    if not at or not (pc or pnc):
        return Indicador(Resultado.indefinido(_motivo("divisão por zero (ativo total ou passivo zero)",
                                                      "division by zero (total assets or liabilities zero)"),
                                              codigo="divisao_por_zero"), contas=usadas)  # fmt: skip
    assert at is not None and pc is not None and pnc is not None
    x = {
        "X1": (v["1.01"] - pc) / at,  # type: ignore[operator]
        "X2": (v["2.03.04"] + v["2.03.05"]) / at,  # type: ignore[operator]
        "X3": v["3.05"] / at,  # type: ignore[operator]
        "X4": v["2.03"] / (pc + pnc),  # type: ignore[operator]
    }
    z = sum(COEF_Z2[k] * x[k] for k in COEF_Z2)
    return Indicador(Resultado.de_valor(z), componentes=x, contas=usadas, marcas=[SEM_ZONA, VALIDADE_Z2])


SINAIS_F = ("ROA", "CFO", "ΔROA", "ACCRUAL", "ΔLEVER", "ΔLIQUID", "EQ_OFFER", "ΔMARGIN", "ΔTURN")
# Rótulos de exibição (pedido de 10/11/2026): nome legível com a sigla do artigo entre parênteses, como nos índices do
# M-score. A tela usa os mesmos (web/lib/textos.ts, conferido por teste).
ROTULOS_F = {
    "ROA": ("Lucro sobre o ativo (ROA)", "Return on assets (ROA)"),
    "CFO": ("Caixa operacional sobre o ativo (CFO)", "Operating cash flow on assets (CFO)"),
    "ΔROA": ("Variação do ROA (ΔROA)", "Change in ROA (ΔROA)"),
    "ACCRUAL": ("Caixa maior que o lucro (ACCRUAL)", "Cash above earnings (ACCRUAL)"),
    "ΔLEVER": ("Variação da alavancagem (ΔLEVER)", "Change in leverage (ΔLEVER)"),
    "ΔLIQUID": ("Variação da liquidez corrente (ΔLIQUID)", "Change in current ratio (ΔLIQUID)"),
    "EQ_OFFER": ("Sem emissão de ações (EQ_OFFER)", "No equity issuance (EQ_OFFER)"),
    "ΔMARGIN": ("Variação da margem bruta (ΔMARGIN)", "Change in gross margin (ΔMARGIN)"),
    "ΔTURN": ("Variação do giro do ativo (ΔTURN)", "Change in asset turnover (ΔTURN)"),
}
TERMOS_EMISSAO = ("captac", "emiss", "ingress")
SAIDAS_EMISSAO = ("pagamento", "amortiza", "liquida", "resgat")
ACOES = re.compile(r"\b(acoes|acao|capital)\b")


def _div(a: float | None, b: float | None) -> float | None:
    return None if a is None or b is None or b == 0 else a / b


def linhas_emissao_acoes(contas: pd.DataFrame) -> pd.DataFrame:
    """Linhas de 6.03 do padrão congelado de "emissões" e, entre elas, só as de ações ou capital (palavra inteira)."""
    dfc = contas[contas.demonstracao.astype(str).str.startswith("DFC") & (contas.ordem == "ÚLTIMO")]
    dfc = dfc[dfc.cd_conta.astype(str).str.startswith("6.03")]
    textos = [normaliza(x) for x in dfc.ds_conta]
    casa = [any(t in s for t in TERMOS_EMISSAO) and not any(t in s for t in SAIDAS_EMISSAO) and bool(ACOES.search(s))
            for s in textos]  # fmt: skip
    return dfc[pd.Series(casa, index=dfc.index, dtype=bool)]


def piotroski_f(contas_t: pd.DataFrame, contas_t1: pd.DataFrame | None, grupo: str | None) -> Indicador:
    """contas_t: DFP de t (ÚLTIMO = t, PENÚLTIMO = t−1); contas_t1: DFP de t−1 na data (PENÚLTIMO = t−2)."""
    if grupo == "financeira":
        return Indicador(Resultado.indefinido(NAO_SE_APLICA, codigo="nao_se_aplica"))
    U, P = "ÚLTIMO", "PENÚLTIMO"

    def g(c: pd.DataFrame | None, dem: str, cod: str, ordem: str) -> float | None:
        return None if c is None else _v(c, dem, cod, ordem)

    at_t, at_1, at_2 = g(contas_t, "BPA", "1", U), g(contas_t, "BPA", "1", P), g(contas_t1, "BPA", "1", P)
    ll_t, ll_1 = g(contas_t, "DRE", "3.09", U), g(contas_t, "DRE", "3.09", P)
    cfo_t = next(
        (_v(contas_t, d, "6.01", U) for d in ("DFC_MI", "DFC_MD") if _v(contas_t, d, "6.01", U) is not None), None
    )
    roa_t, roa_1 = _div(ll_t, at_1), _div(ll_1, at_2)
    cfo_at = _div(cfo_t, at_1)
    lp_t, lp_1 = g(contas_t, "BPP", "2.02.01", U), g(contas_t, "BPP", "2.02.01", P)
    med_t = None if at_t is None or at_1 is None else (at_t + at_1) / 2
    med_1 = None if at_1 is None or at_2 is None else (at_1 + at_2) / 2
    lev_t, lev_1 = _div(lp_t, med_t), _div(lp_1, med_1)
    liq_t = _div(g(contas_t, "BPA", "1.01", U), g(contas_t, "BPP", "2.01", U))
    liq_1 = _div(g(contas_t, "BPA", "1.01", P), g(contas_t, "BPP", "2.01", P))
    mg_t = _div(g(contas_t, "DRE", "3.03", U), g(contas_t, "DRE", "3.01", U))
    mg_1 = _div(g(contas_t, "DRE", "3.03", P), g(contas_t, "DRE", "3.01", P))
    giro_t = _div(g(contas_t, "DRE", "3.01", U), at_1)
    giro_1 = _div(g(contas_t, "DRE", "3.01", P), at_2)
    marcas: list[Motivo] = [ADAPTACAO_EQ]

    def b(cond: bool | None) -> int | None:
        return None if cond is None else int(cond)

    def maior(a: float | None, c: float | None) -> bool | None:
        return None if a is None or c is None else a > c

    if lp_t == 0 and lp_1 == 0 and med_t and med_1:
        delever: int | None = 0
        marcas.append(DIVIDA_ZERO)
    else:
        delever = b(None if lev_t is None or lev_1 is None else lev_t < lev_1)
    emissao = linhas_emissao_acoes(contas_t)
    soma = float(emissao.valor.sum()) if not emissao.empty else None
    eq = None if soma is None or soma < 0 else int(soma == 0)
    sinais: dict[str, int | None] = {
        "ROA": b(None if roa_t is None else roa_t > 0), "CFO": b(None if cfo_at is None else cfo_at > 0),
        "ΔROA": b(maior(roa_t, roa_1)), "ACCRUAL": b(maior(cfo_at, roa_t)), "ΔLEVER": delever,
        "ΔLIQUID": b(maior(liq_t, liq_1)), "EQ_OFFER": eq, "ΔMARGIN": b(maior(mg_t, mg_1)), "ΔTURN": b(maior(giro_t, giro_1)),
    }  # fmt: skip
    calculaveis = [v for v in sinais.values() if v is not None]
    x, y = sum(calculaveis), len(calculaveis)
    usadas = [("BPA", "1", U), ("BPA", "1", P), ("DRE", "3.09", U), ("DRE", "3.09", P), ("DFC", "6.01", U),
              ("BPP", "2.02.01", U), ("BPP", "2.02.01", P), ("BPA", "1.01", U), ("BPA", "1.01", P), ("BPP", "2.01", U),
              ("BPP", "2.01", P), ("DRE", "3.03", U), ("DRE", "3.03", P), ("DRE", "3.01", U), ("DRE", "3.01", P)]  # fmt: skip
    usadas += [("DFC", str(c), U) for c in emissao.cd_conta]
    res = Resultado.de_valor(float(x)) if y else Resultado.indefinido(
        _motivo("nenhum dos nove sinais é calculável", "none of the nine signals is computable"), codigo="nao_calculavel")  # fmt: skip
    componentes: dict[str, Any] = {"sinais": sinais, "x": x, "y": y, "codigos_emissao": [str(c) for c in emissao.cd_conta],
                                   "contas_t2": contas_t1 is not None}  # fmt: skip
    return Indicador(res, componentes=componentes, contas=usadas, marcas=marcas, texto=f"F = {x}/9 ({y} calculáveis)")
