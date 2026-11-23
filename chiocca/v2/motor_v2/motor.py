"""O motor v2 sobre os sinais do v1: as três mudanças, cada uma com uma chave (pré-registro do motor v2, seções 1, 3
e 4).

Entrada: os sinais do v1 de um ou mais exercícios (`chiocca.sinais_amostra.calcula`, antes dos alertas), com a coluna
`versao` (a versão usada); as contas da versão usada (as mesmas que o v1 leu); e, com a mudança do DEPI, a depreciação
da DVA (`dva.depreciacao`).

1. **DEPI pela DVA** (`Mudancas.depi_dva`): nas não financeiras do plano não financeiro, dos dados abertos, com o
   DEPI do v1 não calculável e a depreciação da DVA de t e de t-1, o M-score é recalculado pelas funções do v1
   (`chiocca.variaveis.le_ordem` e `chiocca.sinais.mscore.calcula`), com essa depreciação no lugar da da DFC. Se o
   DEPI sai calculável, `DEPI`, `mscore` e os motivos passam a ser os do v2, com `marca_depreciacao_dva`.
2. **Desvio de Benford padronizado** (`Mudancas.benford`): a coluna `benford`, nos dois grupos (`benford.py`).
3. **Alerta pelo escore** (`Mudancas.escore`): `avaliada` e `em_alerta` passam a ser os do escore (`escore.py`); os
   alertas por sinal do v1 (corte do M-score, decis do DPO e do peso, juro acima do CDI) saem. O alerta da regra boba
   (`alerta_regra_boba`), o comparador do estudo 2, fica como no v1.

Com as três chaves desligadas, a saída é a do v1 (`chiocca.sinais_amostra.alertas`), coluna por coluna: é o invariante
da seção 6. O lucro que não vira caixa continua na saída, fora do escore.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from chiocca import sinais_amostra, variaveis
from chiocca.sinais import mscore
from chiocca.sinais_amostra import AMOSTRA_FIN, AMOSTRA_NF
from chiocca.v2.motor_v2 import benford, escore
from chiocca.v2.motor_v2.dva import COLUNAS_DEPRECIACAO

CHAVE = ["cd_cvm", "dt_refer"]
DADOS_ABERTOS = "dados_abertos"
PLANO_NAO_FINANCEIRO = "nao_financeiro"
SINAIS_DAS_REGRAS = ("mscore", "dpo", "juro", "peso_nao_recorrente", "alavancagem")
ALERTAS_POR_SINAL_DO_V1 = ("alerta_mscore", "alerta_dpo", "alerta_juro", "alerta_peso_nao_recorrente")


@dataclass(frozen=True)
class Mudancas:
    """As três mudanças do v2; desligadas, o v2 é o v1."""

    depi_dva: bool = True
    benford: bool = True
    escore: bool = True


TODAS = Mudancas()
NENHUMA = Mudancas(depi_dva=False, benford=False, escore=False)


def aplica_depi_dva(s: pd.DataFrame, contas: pd.DataFrame, depreciacao: pd.DataFrame) -> pd.DataFrame:
    """O M-score com a depreciação da DVA onde o DEPI do v1 não é calculável (seção 3.1)."""
    s = s.copy()
    s["marca_depreciacao_dva"] = False
    s["depreciacao_dva_t"] = np.nan
    s["depreciacao_dva_t1"] = np.nan
    if "DEPI" not in s.columns:  # nenhuma não financeira do plano não financeiro no conjunto
        return s
    candidata = (
        (s.amostra == AMOSTRA_NF) & (s.plano == PLANO_NAO_FINANCEIRO) & (s.fonte == DADOS_ABERTOS) & s.DEPI.isna()
    )
    if not candidata.any() or depreciacao.empty:
        return s
    chave = ["cd_cvm", "dt_refer", "tipo", "versao"]
    alvo = s.loc[candidata, chave].assign(versao=lambda d: d.versao.astype(int)).reset_index(names="_linha")
    dep = depreciacao[COLUNAS_DEPRECIACAO].assign(versao=lambda d: d.versao.astype(int))
    alvo = alvo.merge(dep, on=chave, how="left").set_index("_linha")
    alvo = alvo[alvo.depreciacao_dva_t.notna() & alvo.depreciacao_dva_t1.notna()]
    if alvo.empty:
        return s
    precisa = set(zip(alvo.cd_cvm, alvo.dt_refer))
    por_empresa = {k: g for k, g in contas.groupby(CHAVE) if k in precisa}
    for i, r in alvo.iterrows():
        c = por_empresa[(r.cd_cvm, r.dt_refer)]
        t = dict(variaveis.le_ordem(c, variaveis.ULTIMO).valores, depreciacao=float(r.depreciacao_dva_t))
        t1 = dict(variaveis.le_ordem(c, variaveis.PENULTIMO).valores, depreciacao=float(r.depreciacao_dva_t1))
        s.at[i, "depreciacao_dva_t"] = r.depreciacao_dva_t
        s.at[i, "depreciacao_dva_t1"] = r.depreciacao_dva_t1
        m = mscore.calcula(t, t1)
        depi = m.componentes["DEPI"]
        if depi.valor is None:
            continue
        s.at[i, "DEPI"], s.at[i, "DEPI_motivo"] = depi.valor, depi.motivo
        s.at[i, "mscore"], s.at[i, "mscore_motivo"] = m.m.valor, m.m.motivo
        s.at[i, "marca_depreciacao_dva"] = True
    return s


def aplica_benford(s: pd.DataFrame, contas: pd.DataFrame) -> pd.DataFrame:
    """O desvio de Benford padronizado nas empresa-anos dos dois grupos (seção 3.3)."""
    s = s.copy()
    nos_grupos = s.amostra.isin([AMOSTRA_NF, AMOSTRA_FIN])
    chaves = set(zip(s.loc[nos_grupos, "cd_cvm"], s.loc[nos_grupos, "dt_refer"]))
    alvo = contas[[k in chaves for k in zip(contas.cd_cvm, contas.dt_refer)]]
    c = benford.contagens(alvo).set_index(CHAVE)
    pares = pd.MultiIndex.from_arrays([s.cd_cvm, s.dt_refer])
    s["n_numeros_benford"] = c.n_numeros_benford.reindex(pares).fillna(0).astype(int).to_numpy()
    s["desvio_benford"] = c.desvio_benford.reindex(pares).astype(float).to_numpy()
    for col in ("faixa_benford", "benford"):
        s[col] = np.nan
    s["benford_motivo"] = None
    for _, idx in s[nos_grupos].groupby(["exercicio", "amostra"], sort=True).groups.items():
        p = benford.padroniza(s.loc[idx, "desvio_benford"], s.loc[idx, "n_numeros_benford"])
        s.loc[idx, ["faixa_benford", "benford", "benford_motivo"]] = p[["faixa_benford", "benford", "benford_motivo"]]
    return s


def calcula(
    s: pd.DataFrame, contas: pd.DataFrame, depreciacao: pd.DataFrame | None = None, mudancas: Mudancas = TODAS
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Sinais e alertas do v2 (ou do v1, com as mudanças desligadas). Devolve (sinais, limiares)."""
    if s.duplicated(CHAVE).any():
        raise ValueError("empresa-ano repetida (cd_cvm, dt_refer) nos sinais")
    s = s.copy()
    for col in SINAIS_DAS_REGRAS:  # um grupo sem nenhuma empresa não tem a coluna do sinal dele, como no v1
        if col not in s.columns:
            s[col] = float("nan")
    if mudancas.depi_dva:
        if depreciacao is None:
            raise ValueError("a mudança do DEPI pela DVA precisa da depreciação da DVA")
        s = aplica_depi_dva(s, contas, depreciacao)
    if mudancas.benford:
        s = aplica_benford(s, contas)
    s, limiares = sinais_amostra.alertas(s)
    if mudancas.escore:
        s, do_escore = escore.alerta(s, escore.sinais_do_escore(mudancas.benford))
        s = s.drop(columns=list(ALERTAS_POR_SINAL_DO_V1))
        limiares = pd.concat([limiares[limiares.sinal == "alavancagem"], do_escore], ignore_index=True)
    return s, limiares
