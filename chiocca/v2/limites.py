"""Seção "Limites" da página de investigação: texto fixo, em PT e EN (pedido de Roberto, 08/11/2026).

O texto é fixo; só os números do estudo 1 mudam com a saída dele e vêm de `docs/resultados_numeros.json` e da análise
depois do resultado (`docs/analises_pos_estudo_1_numeros.json`), nunca digitados à mão. A página de investigação usa
este texto na Fase C2; `docs/contratos.md` e `docs/en/contracts.md` trazem a mesma saída, conferida por teste.
"""

from __future__ import annotations

import json
from typing import Any

from chiocca.formato import decimal, inteiro, pct
from chiocca.v2 import analises_pos_estudo_1 as pos_estudo

T = {
    "pt": {
        "atestado": "Não ter alerta não é atestado. Em Dechow, Sloan e Sweeney (1995), o modelo de accruals com mais poder rejeitou 'sem manipulação' em só 28,1% de 32 empresas punidas pela SEC (Tabela 7, p. 32).",
        "estudo": "No estudo 1, {taxa} das empresas-ano ficaram em alerta, e o número de acertos não superou o acaso num teste descritivo feito depois do resultado: {obs} acertos em {casos} casos acertáveis, contra {e2} esperados ao acaso sem supor anos independentes ({e1} supondo anos independentes).",
        "estudo_sem_variante": "No estudo 1, {taxa} das empresas-ano ficaram em alerta, e o número de acertos não superou o acaso num teste descritivo feito depois do resultado: {obs} acertos em {casos} casos acertáveis, contra {e1} esperados ao acaso.",
        "familias": "Os modelos de risco usam números que podem estar manipulados (Pereira e Martins 2015, p. 29). Por isso as três famílias não se somam.",
    },
    "en": {
        "atestado": "No alert is not a clean bill of health. In Dechow, Sloan and Sweeney (1995), the most powerful accruals model rejected 'no manipulation' for only 28.1% of 32 companies sanctioned by the SEC (Table 7, p. 32).",
        "estudo": "In study 1, {taxa} of company-years were in alert, and the number of detections did not beat chance in a descriptive test done after the result: {obs} detections in {casos} detectable cases, against {e2} expected by chance without assuming independent years ({e1} assuming independent years).",
        "estudo_sem_variante": "In study 1, {taxa} of company-years were in alert, and the number of detections did not beat chance in a descriptive test done after the result: {obs} detections in {casos} detectable cases, against {e1} expected by chance.",
        "familias": "Risk models use numbers that may be manipulated (Pereira and Martins 2015, p. 29). That is why the three families are not added up.",
    },
}  # fmt: skip


def textos(lang: str, n: dict[str, Any] | None = None, dados: dict[str, Any] | None = None) -> list[str]:
    """Os três parágrafos da seção "Limites", com os números lidos da saída do estudo 1."""
    if n is None:
        n = json.loads(pos_estudo.NUMEROS_ESTUDO_1.read_text(encoding="utf-8"))
        dados = pos_estudo.le_dados() if dados is None else dados
    r = pos_estudo.calcula(n, dados)
    taxa = n["taxa"]["nf"]
    em, av = sum(v["em_alerta"] for v in taxa.values()), sum(v["avaliadas"] for v in taxa.values())
    esperados = [r["esperado"]] + ([r["variante"]["esperado"]] if "variante" in r else [])
    if r["observados"] > min(esperados):
        raise ValueError("os acertos superam o esperado ao acaso: o texto fixo deixaria de valer")
    t = T[lang]
    estudo = t["estudo" if "variante" in r else "estudo_sem_variante"].format(
        taxa=pct(em / av, lang), obs=inteiro(r["observados"], lang), casos=inteiro(len(r["casos"]), lang),
        e1=decimal(r["esperado"], lang, 2), e2=decimal(r["variante"]["esperado"], lang, 2) if "variante" in r else "",
    )  # fmt: skip
    return [t["atestado"], estudo, t["familias"]]
