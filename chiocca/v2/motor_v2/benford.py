"""Desvio de Benford padronizado (pré-registro do motor v2, seção 3.3).

- **Os números:** os valores diferentes de zero na coluna do exercício (ÚLTIMO) de BPA, BPP, DRE e DFC (pelo método
  indireto ou direto) da versão usada, os quatro demonstrativos que existem nos dados abertos e no ENET. De cada um, o
  primeiro dígito significativo de |valor|.
- **O desvio:** (1/9) Σ |p_d − log10(1 + 1/d)|, d = 1..9, com p_d a frequência do dígito d.
- **As faixas:** os quintis da quantidade de números, dentro do exercício e do grupo, entre as empresa-anos com pelo
  menos 20 números (`qcut` do pandas sobre `rank(method="first")`, 5 faixas). Os empates de quantidade são desfeitos
  pela ordem de entrada das empresa-anos, que é a ordem do índice da DFP do exercício: a primeira linha de cada par
  (código CVM, data de referência) no `dfp_cia_aberta_<ano>.csv` do zip da DFP; na lista do estudo 2, o arquivo
  arquivado no branch `estudo-2-dados`. Com os mesmos arquivos, o recálculo é determinístico (decisão de Roberto,
  23/11/2026).
- **A padronização:** (desvio − média do desvio na faixa) ÷ desvio-padrão amostral (n − 1) do desvio na faixa.
  Calculável com pelo menos 20 números e desvio-padrão da faixa maior que zero.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from chiocca.variaveis import ULTIMO

LEI = np.log10(1 + 1 / np.arange(1, 10))
DEMONSTRATIVOS = ("BPA", "BPP", "DRE", "DFC_MI", "DFC_MD")
MINIMO_NUMEROS = 20
FAIXAS = 5
CHAVE = ["cd_cvm", "dt_refer"]
DIGITOS = [f"benford_d{d}" for d in range(1, 10)]
POUCOS_NUMEROS = "menos_de_20_numeros"
FAIXA_SEM_DESVIO = "faixa_sem_desvio_padrao"


def primeiro_digito(valores: np.ndarray) -> np.ndarray:
    """Primeiro dígito significativo de |valor| (valores finitos e diferentes de zero), lido da notação científica com
    15 algarismos: é o dígito do valor decimal da DFP, sem o erro de arredondamento de log10 em valores como 0,3, e
    absorve o erro da multiplicação pela escala (MIL × 1.000)."""
    v = np.abs(np.asarray(valores, dtype=float))
    return np.array([int(f"{x:.14e}"[0]) for x in v], dtype=np.int64)


def contagens(contas: pd.DataFrame) -> pd.DataFrame:
    """Por empresa-ano (`cd_cvm`, `dt_refer`): a quantidade de números, a contagem de cada primeiro dígito e o desvio.

    `contas` tem as colunas das contas da versão usada (`cd_cvm`, `dt_refer`, `demonstracao`, `ordem`, `valor`). As
    empresa-anos sem nenhum número não aparecem."""
    valor = pd.to_numeric(contas.valor, errors="coerce")
    conta = contas.demonstracao.isin(DEMONSTRATIVOS) & (contas.ordem == ULTIMO) & np.isfinite(valor) & (valor != 0)
    if not conta.any():
        return pd.DataFrame(columns=[*CHAVE, "n_numeros_benford", *DIGITOS, "desvio_benford"])
    c = contas.loc[conta, CHAVE].copy()
    c["digito"] = primeiro_digito(valor[conta].to_numpy())
    tabela = pd.crosstab([c.cd_cvm, c.dt_refer], c.digito).reindex(columns=range(1, 10), fill_value=0)
    n = tabela.sum(axis=1)
    frequencia = tabela.to_numpy(dtype=float) / n.to_numpy(dtype=float)[:, None]
    out = pd.DataFrame(tabela.to_numpy(), index=tabela.index, columns=DIGITOS)
    out.insert(0, "n_numeros_benford", n.to_numpy())
    out["desvio_benford"] = np.abs(frequencia - LEI).mean(axis=1)
    return out.reset_index()


def padroniza(desvio: pd.Series, n: pd.Series) -> pd.DataFrame:
    """Faixa e desvio padronizado num conjunto (um exercício e um grupo), com o motivo quando não é calculável.

    Faixa 0 = menos números. Com uma empresa-ano só acima do mínimo, ela fica na faixa 0, sozinha (o `qcut` não forma
    faixas com um valor só); faixa de um membro só não tem desvio-padrão."""
    out = pd.DataFrame({"faixa_benford": np.nan, "benford": np.nan, "benford_motivo": None}, index=desvio.index)
    elegivel = desvio.notna() & (n >= MINIMO_NUMEROS)
    out.loc[~elegivel, "benford_motivo"] = POUCOS_NUMEROS
    if elegivel.sum() == 1:
        out.loc[elegivel, "faixa_benford"] = 0
    elif elegivel.sum() > 1:
        faixa = pd.qcut(n[elegivel].rank(method="first"), FAIXAS, labels=False)
        grupo = desvio[elegivel].groupby(faixa)
        media, dp = grupo.transform("mean"), grupo.transform("std")
        out.loc[elegivel, "faixa_benford"] = faixa
        out.loc[elegivel, "benford"] = (desvio[elegivel] - media) / dp.where(dp > 0)
    out.loc[elegivel & out.benford.isna(), "benford_motivo"] = FAIXA_SEM_DESVIO
    return out
