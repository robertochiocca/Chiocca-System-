"""Reapresentação pelo comparativo do ano seguinte (regra de 09/11/2026 em docs/contratos.md, seção 4).

Quando, na data de referência, já existe a DFP de t+1 (versão pública na data, pelo `como_era` do motor v1), cada
conta de t na versão usada (coluna ÚLTIMO) é comparada com a coluna PENÚLTIMO da DFP de t+1: mesma demonstração (a
DFC pelo prefixo), mesmo código de conta, mesmo tipo (consolidado com consolidado). Conta que só existe numa das
colunas não entra. Diferença acima de `TOLERANCIA` (R$ 1.000 por conta, a das conferências) vira evidência para a
investigação, com texto neutro. Nada disso muda cálculo ou alerta do motor v1.

Materialidade (regra de 09/11/2026, também na seção 4 dos contratos): grupo (a) são os totais e linhas-chave
(`LINHAS_CHAVE`, os códigos do motor v1); grupo (b), as reclassificações nas demais linhas. Destacada é a diferença do
grupo (a) acima de 1% do ativo total da versão usada (`MATERIALIDADE`). Nada disso vira sinal de alerta.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Any

import pandas as pd

from chiocca import base, variaveis
from chiocca.v2.conferencias import TOLERANCIA_POR_PARCELA
from chiocca.v2.lacre import ULTIMO_EXERCICIO_LIBERADO
from chiocca.v2.validade import Motivo

TOLERANCIA = TOLERANCIA_POR_PARCELA
MATERIALIDADE = 0.01  # destacada: diferença do grupo (a) acima de 1% do ativo total da versão usada
CHAVES = ("ativo_total", "passivo_circulante", "passivo_nao_circulante", "patrimonio_liquido", "receita_liquida",
          "lucro_liquido", "caixa_operacional_apresentado")  # fmt: skip
LINHAS_CHAVE: tuple[tuple[str, str], ...] = tuple(variaveis.CONTAS[k] for k in CHAVES)  # a DFC já vem pelo prefixo
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
    grupo: str = "b"  # "a": totais e linhas-chave; "b": reclassificações nas demais linhas
    destacada: bool = False  # grupo (a) acima de 1% do ativo total da versão usada
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


def ativo_total(contas: pd.DataFrame) -> float | None:
    """Ativo total (BPA 1, coluna ÚLTIMO) da versão usada; base do limite de destaque."""
    v = contas[(contas.demonstracao == "BPA") & (contas.ordem == "ÚLTIMO") & (contas.cd_conta == "1")].valor
    return None if v.empty or pd.isna(v.iloc[0]) else float(v.iloc[0])


def limite_destaque(contas: pd.DataFrame) -> float | None:
    """1% do ativo total da versão usada; sem ativo total positivo, nada é destacado."""
    at = ativo_total(contas)
    return MATERIALIDADE * at if at is not None and at > 0 else None


def contas_comparadas(leitura_t: base.Leitura, leitura_seguinte: base.Leitura) -> int:
    juntas = _juntas(leitura_t, leitura_seguinte)
    return 0 if juntas is None else int(len(juntas))


def comparar(leitura_t: base.Leitura, leitura_seguinte: base.Leitura) -> list[DiferencaComparativo]:
    """Diferenças entre o ÚLTIMO de t e o PENÚLTIMO de t+1, acima da tolerância."""
    juntas = _juntas(leitura_t, leitura_seguinte)
    if juntas is None:
        return []
    juntas = juntas[(juntas.comparativo - juntas.valor).abs() > TOLERANCIA]
    limite = limite_destaque(leitura_t.contas)
    out = []
    for (dem, cod), r in juntas.iterrows():
        dif = float(r.comparativo - r.valor)
        grupo = "a" if (dem, cod) in LINHAS_CHAVE else "b"
        out.append(
            DiferencaComparativo(str(r.demonstracao), str(cod), str(r.ds_conta), float(r.valor), float(r.comparativo),
                                 dif, leitura_t.versao, None if leitura_t.dt_receb is None else str(leitura_t.dt_receb),
                                 leitura_t.num_doc, leitura_seguinte.versao,
                                 None if leitura_seguinte.dt_receb is None else str(leitura_seguinte.dt_receb),
                                 leitura_seguinte.num_doc, grupo=grupo,
                                 destacada=grupo == "a" and limite is not None and abs(dif) > limite)  # fmt: skip
        )
    return out


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
        comparadas = com_diferenca = com_destacada = 0
        for p in idx[["cd_cvm", "DT_REFER"]].drop_duplicates().itertuples(index=False):
            lt = base.como_era(fontes, p.cd_cvm, ano, corte=data_referencia, dt_refer=p.DT_REFER)
            seg = leitura_seguinte(fontes, p.cd_cvm, ano, data_referencia) if lt.status == base.OK else None
            if seg is None or seg.status != base.OK or seg.tipo != lt.tipo:
                continue
            comparadas += 1
            difs = comparar(lt, seg)
            com_diferenca += int(bool(difs))
            com_destacada += int(any(x.destacada for x in difs))
        out[str(ano)] = {"comparadas": comparadas, "com_diferenca": com_diferenca, "com_destacada": com_destacada}
    return out
