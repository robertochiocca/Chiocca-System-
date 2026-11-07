"""Teste de robustez com valores neutros (pré-registro, seção 4.1). Não substitui o estudo principal.

A seção 4.1 decide "não calculável" para conta faltante ou denominador zero, e deixa os valores neutros do artigo
de 1999 (AQI = 1; DEPI = SGAI = 1) só como teste de robustez. Aqui, nas não financeiras, o AQI, o DEPI e o SGAI
que ficaram não calculáveis por conta ausente ou denominador zero recebem o valor neutro 1. Os outros componentes,
os outros motivos (receita negativa, plano de contas) e os outros sinais ficam como no estudo principal.
"""

from __future__ import annotations

import pandas as pd

from chiocca.sinais.mscore import COEFICIENTES, INTERCEPTO
from chiocca.sinais_amostra import AMOSTRA_FIN, AMOSTRA_NF, CORTE_M

NEUTROS = {"AQI": 1.0, "DEPI": 1.0, "SGAI": 1.0}
MOTIVOS_NEUTROS = ("conta_ausente", "divisao_por_zero")


def neutros(s: pd.DataFrame) -> pd.DataFrame:
    """Acrescenta mscore_neutro, alerta_mscore_neutro, em_alerta_neutro e avaliada_neutro (s já preparado)."""
    s = s.copy()
    nf = s.amostra == AMOSTRA_NF
    fin = s.amostra == AMOSTRA_FIN
    comps = {}
    usou = pd.Series(False, index=s.index)
    for c in COEFICIENTES:
        v = pd.to_numeric(s[c], errors="coerce")
        if c in NEUTROS:
            tipo = s[f"{c}_motivo"].astype("string").str.split(":").str[0]
            troca = v.isna() & tipo.isin(MOTIVOS_NEUTROS).fillna(False) & nf
            usou |= troca
            v = v.mask(troca, NEUTROS[c])
        comps[c] = v
    m = INTERCEPTO + sum(COEFICIENTES[c] * comps[c] for c in COEFICIENTES)
    s["mscore_neutro"] = m.where(nf)
    s["usou_neutro"] = usou
    s["alerta_mscore_neutro"] = (s.mscore_neutro > CORTE_M).fillna(False) & nf
    dpo, juro = pd.to_numeric(s.dpo, errors="coerce"), pd.to_numeric(s.juro, errors="coerce")
    s["em_alerta_neutro"] = (nf & (s.alerta_mscore_neutro | s.alerta_dpo | s.alerta_juro)) | (fin & s.em_alerta)
    s["avaliada_neutro"] = (nf & (s.mscore_neutro.notna() | dpo.notna() | juro.notna())) | (fin & s.avaliada)
    return s
