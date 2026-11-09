"""Reapresentação pelo comparativo do ano seguinte (regra de 09/11/2026 em docs/contratos.md, seção 4).

Quando, na data de referência, já existe a DFP de t+1 (versão pública na data, pelo `como_era` do motor v1), cada
conta de t na versão usada (coluna ÚLTIMO) é comparada com a coluna PENÚLTIMO da DFP de t+1: mesma demonstração (a
DFC pelo prefixo), mesmo código de conta, mesmo tipo (consolidado com consolidado). Conta que só existe numa das
colunas não entra. Diferença acima de `TOLERANCIA` (R$ 1.000 por conta, a das conferências) vira evidência para a
investigação, com texto neutro. Nada disso muda cálculo ou alerta do motor v1.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Any

import pandas as pd

from chiocca import base
from chiocca.v2.conferencias import TOLERANCIA_POR_PARCELA
from chiocca.v2.lacre import ULTIMO_EXERCICIO_LIBERADO
from chiocca.v2.validade import Motivo

TOLERANCIA = TOLERANCIA_POR_PARCELA
TEXTO = Motivo(
    "valor diferente no comparativo do ano seguinte (reapresentação ou reclassificação)",
    "different value in the following year's comparative (restatement or reclassification)",
)


@dataclass(frozen=True)
class DiferencaComparativo:
    demonstracao: str
    cd_conta: str
    ds_conta: str
    valor: float  # na versão usada de t (ÚLTIMO)
    valor_comparativo: float  # no PENÚLTIMO da DFP de t+1
    diferenca: float  # comparativo − valor
    versao: int | None
    dt_receb: str | None
    num_doc: str | None
    versao_seguinte: int | None
    dt_receb_seguinte: str | None
    num_doc_seguinte: str | None
    texto: Motivo = TEXTO


def _coluna(contas: pd.DataFrame, ordem: str) -> pd.DataFrame:
    c = contas[contas.ordem == ordem].copy()
    c["dem"] = c.demonstracao.astype(str).where(~c.demonstracao.astype(str).str.startswith("DFC"), "DFC")
    return c.drop_duplicates(["dem", "cd_conta"]).set_index(["dem", "cd_conta"])


def _juntas(leitura_t: base.Leitura, leitura_seguinte: base.Leitura) -> pd.DataFrame | None:
    if leitura_t.status != base.OK or leitura_seguinte.status != base.OK or leitura_t.tipo != leitura_seguinte.tipo:
        return None
    t, s = _coluna(leitura_t.contas, "ÚLTIMO"), _coluna(leitura_seguinte.contas, "PENÚLTIMO")
    return t[["demonstracao", "ds_conta", "valor"]].join(
        s[["valor"]].rename(columns={"valor": "comparativo"}), how="inner"
    )


def contas_comparadas(leitura_t: base.Leitura, leitura_seguinte: base.Leitura) -> int:
    juntas = _juntas(leitura_t, leitura_seguinte)
    return 0 if juntas is None else int(len(juntas))


def comparar(leitura_t: base.Leitura, leitura_seguinte: base.Leitura) -> list[DiferencaComparativo]:
    """Diferenças entre o ÚLTIMO de t e o PENÚLTIMO de t+1, acima da tolerância."""
    juntas = _juntas(leitura_t, leitura_seguinte)
    if juntas is None:
        return []
    juntas = juntas[(juntas.comparativo - juntas.valor).abs() > TOLERANCIA]
    return [
        DiferencaComparativo(str(r.demonstracao), str(cod), str(r.ds_conta), float(r.valor), float(r.comparativo),
                             float(r.comparativo - r.valor), leitura_t.versao,
                             None if leitura_t.dt_receb is None else str(leitura_t.dt_receb), leitura_t.num_doc,
                             leitura_seguinte.versao,
                             None if leitura_seguinte.dt_receb is None else str(leitura_seguinte.dt_receb),
                             leitura_seguinte.num_doc)  # fmt: skip
        for (_, cod), r in juntas.iterrows()
    ]


def leitura_seguinte(fontes: Any, cd_cvm: str, exercicio: int, data_referencia: date) -> base.Leitura | None:
    """A DFP de t+1 na versão pública na data, se o exercício seguinte estiver liberado."""
    if exercicio + 1 > ULTIMO_EXERCICIO_LIBERADO:
        return None
    return base.como_era(fontes, cd_cvm, exercicio + 1, corte=data_referencia)


def diferencas(
    fontes: Any, leitura_t: base.Leitura, exercicio: int, data_referencia: date
) -> tuple[DiferencaComparativo, ...]:
    if leitura_t.status != base.OK:
        return ()
    seguinte = leitura_seguinte(fontes, leitura_t.cd_cvm, exercicio, data_referencia)
    return tuple(comparar(leitura_t, seguinte)) if seguinte is not None else ()


def contagem(fontes: Any, data_referencia: date, anos: range | list[int]) -> dict[str, Any]:
    """Descritivo: empresa-anos com alguma diferença no comparativo do ano seguinte, na data de referência."""
    out: dict[str, Any] = {}
    for ano in anos:
        if ano + 1 > ULTIMO_EXERCICIO_LIBERADO:
            continue
        idx = fontes.indice_dfp(ano)
        comparadas = com_diferenca = 0
        for p in idx[["cd_cvm", "DT_REFER"]].drop_duplicates().itertuples(index=False):
            lt = base.como_era(fontes, p.cd_cvm, ano, corte=data_referencia, dt_refer=p.DT_REFER)
            seg = leitura_seguinte(fontes, p.cd_cvm, ano, data_referencia) if lt.status == base.OK else None
            if seg is None or seg.status != base.OK or seg.tipo != lt.tipo:
                continue
            comparadas += 1
            com_diferenca += int(bool(comparar(lt, seg)))
        out[str(ano)] = {"comparadas": comparadas, "com_diferenca": com_diferenca}
    return out
