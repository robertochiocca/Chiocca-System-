"""Sinais e alertas da amostra inteira, como era na época (PROMPT.md, Fase 2; pré-registro, seção 4).

Lê a base da Fase 1 (data/base/, fora do git) e grava em resultados/ (fora do git, regra 6 do PROMPT):
- resultados/sinais_empresa_ano.csv: uma linha por empresa-ano de 2010 a 2023 com versão da época, com o
  grupo, a situação na amostra, cada sinal (valor ou motivo de "não calculável"), as marcas e os alertas;
- resultados/limiares.csv: o limite do decil superior de cada ano e grupo.

Amostra (pré-registro, seção 2, e emendas 5, 9 e 10):
- financeiras: todas as empresa-anos do grupo com versão da época; sinal peso_nao_recorrente;
- não financeiras: as do grupo com receita (conta 3.01 presente e diferente de zero); sinais M-score, DPO e
  juro implícito, e lucro sem caixa só na ficha. As contas por código valem para o plano não financeiro
  (reconhecimento 1.4); nas não financeiras que usam outro plano, esses sinais ficam "não calculável"
  (motivo plano_de_contas).

Regras de alerta (pré-registro, seção 4, sem ajuste):
- M > −1,78;
- variação do DPO no decil superior do ano, dentro das não financeiras;
- juro implícito > CDI médio do ano + 10 p.p.;
- peso_nao_recorrente no decil superior do ano, dentro das financeiras;
- regra boba (seção 7 e emenda 7): alavancagem no decil superior do ano, dentro de cada grupo.
"Decil superior do ano" = valor maior ou igual ao percentil 90 dos valores calculáveis daquele exercício e
grupo (percentil com interpolação linear, o padrão do pandas). Empresa-ano "em alerta" = pelo menos um
sinal do grupo disparou; "avaliada" = pelo menos um sinal de alerta do grupo calculável.

Uso: python -m chiocca.sinais_amostra
"""

from __future__ import annotations

import json
import subprocess
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

from chiocca import cdi, grupos, variaveis
from chiocca.base import RAIZ
from chiocca.sinais import dpo, juro_implicito, lucro_sem_caixa, mscore, peso_nao_recorrente
from chiocca.sinais.resultado import Resultado

BASE = RAIZ / "data" / "base"
SAIDA = RAIZ / "resultados"
ANOS = range(2010, 2024)  # pré-registro, seção 2
CORTE_M = -1.78
SPREAD_PP = 10.0
PERCENTIL = 0.9

# Situação de cada empresa-ano na amostra.
AMOSTRA_NF = "nao_financeira"
AMOSTRA_FIN = "financeira"
FORA_SEM_RECEITA = "fora_sem_receita"
FORA_STATUS = "fora_sem_versao_da_epoca"

PLANO_DE_CONTAS = "plano_de_contas"
SINAIS_NF = ("mscore", "dpo", "juro")


def _r(prefixo: str, r: Resultado) -> dict[str, Any]:
    return {prefixo: r.valor, f"{prefixo}_motivo": r.motivo}


def cpc06(dt_refer: str) -> bool:
    """Exercício que começa em 2019, o de adoção do CPC 06 (R2) (pré-registro 4.1: manter e marcar)."""
    fim = date.fromisoformat(dt_refer)
    return date(2019, 12, 31) <= fim <= date(2020, 12, 30)


def sinais_nao_financeira(contas: pd.DataFrame, dt_refer: str) -> dict[str, Any]:
    t, t1 = variaveis.le_ordem(contas, variaveis.ULTIMO), variaveis.le_ordem(contas, variaveis.PENULTIMO)
    linha: dict[str, Any] = {
        "metodo_dfc": variaveis.metodo_dfc(contas),
        "marca_depreciacao_combinada": t.depreciacao_combinada or t1.depreciacao_combinada,
        "juros_pagos_linhas_6_01": len(t.juros_pagos_em_6_01),
        "juros_pagos_linhas_6_03": len(t.juros_pagos_em_6_03),
    }
    m = mscore.calcula(t.valores, t1.valores)
    for nome, r in m.componentes.items():
        linha.update(_r(nome, r))
    linha.update(_r("mscore", m.m))
    linha.update(_r("dpo", dpo.variacao(t.valores, t1.valores)))
    j = juro_implicito.juro(t.valores, t1.valores)
    taxa_cdi = cdi.medio(dt_refer)
    linha["cdi_medio"] = taxa_cdi
    linha["juro_implicito"] = j.valor
    if j.valor is None:
        linha.update(_r("juro", Resultado(None, j.motivo)))
    elif taxa_cdi is None:
        linha.update(_r("juro", Resultado(None, "cdi_ausente")))
    else:
        linha.update(_r("juro", Resultado(juro_implicito.spread_pp(j.valor, taxa_cdi))))
    linha.update(_r("lucro_sem_caixa", lucro_sem_caixa.accruals(t.valores, t1.valores)))
    return linha


def calcula(meta: pd.DataFrame, base: Path = BASE, anos: range = ANOS) -> pd.DataFrame:
    linhas = []
    for ano in anos:
        m = meta[meta.exercicio == ano]
        contas = pd.read_csv(base / f"contas_{ano}.csv.gz", dtype={"cd_cvm": str, "cd_conta": str, "ds_conta": str})
        por_empresa = {k: g for k, g in contas.groupby(["cd_cvm", "dt_refer"])}
        for e in m.itertuples(index=False):
            linha: dict[str, Any] = {
                "exercicio": ano,
                "cd_cvm": e.cd_cvm,
                "dt_refer": e.dt_refer,
                "grupo": e.grupo,
                "plano": e.plano,
                "tipo": e.tipo,
                "fonte": e.fonte,
                "dt_receb": e.dt_receb,
                "data_corte": e.data_corte,
                "status": e.status,
            }
            if e.status != "ok":
                linha["amostra"] = FORA_STATUS
            elif e.grupo == grupos.FINANCEIRA:
                linha["amostra"] = AMOSTRA_FIN
            elif bool(e.sem_receita):
                linha["amostra"] = FORA_SEM_RECEITA
            else:
                linha["amostra"] = AMOSTRA_NF
            if linha["amostra"] in (AMOSTRA_FIN, AMOSTRA_NF):
                c = por_empresa[(e.cd_cvm, e.dt_refer)]
                linha["marca_cpc06"] = cpc06(e.dt_refer)
                linha.update(_r("alavancagem", variaveis.alavancagem(c)))
                if linha["amostra"] == AMOSTRA_FIN:
                    linha.update(_r("peso_nao_recorrente", peso_nao_recorrente.financeiras(variaveis.linhas_dre(c))))
                elif e.plano == "nao_financeiro":
                    linha.update(sinais_nao_financeira(c, e.dt_refer))
                else:
                    falta = Resultado(None, f"{PLANO_DE_CONTAS}:{e.plano}")
                    for nome in (*mscore.COEFICIENTES, *SINAIS_NF, "lucro_sem_caixa"):
                        linha.update(_r(nome, falta))
            linhas.append(linha)
    return pd.DataFrame(linhas)


def decil_superior(valores: pd.Series) -> tuple[pd.Series, float | None]:
    """Alerta quando o valor é ≥ percentil 90 dos calculáveis; não calculável fica sem alerta (NA)."""
    ok = valores.dropna()
    if ok.empty:
        return pd.Series(pd.NA, index=valores.index, dtype="boolean"), None
    limite = float(ok.quantile(PERCENTIL))
    return (valores >= limite).astype("boolean").mask(valores.isna()), limite


def alertas(s: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    s = s.copy()
    for col in ("alerta_mscore", "alerta_dpo", "alerta_juro", "alerta_peso_nao_recorrente", "alerta_regra_boba"):
        s[col] = pd.Series(pd.NA, index=s.index, dtype="boolean")
    limiares = []
    nf = s.amostra == AMOSTRA_NF
    fin = s.amostra == AMOSTRA_FIN
    s.loc[nf, "alerta_mscore"] = (s.loc[nf, "mscore"] > CORTE_M).astype("boolean").mask(s.loc[nf, "mscore"].isna())
    s.loc[nf, "alerta_juro"] = (s.loc[nf, "juro"] > SPREAD_PP).astype("boolean").mask(s.loc[nf, "juro"].isna())
    for ano in sorted(s.exercicio.unique()):
        for grupo, filtro, sinal, col in (
            (AMOSTRA_NF, nf, "dpo", "alerta_dpo"),
            (AMOSTRA_FIN, fin, "peso_nao_recorrente", "alerta_peso_nao_recorrente"),
            (AMOSTRA_NF, nf, "alavancagem", "alerta_regra_boba"),
            (AMOSTRA_FIN, fin, "alavancagem", "alerta_regra_boba"),
        ):
            idx = s.index[filtro & (s.exercicio == ano)]
            alerta, limite = decil_superior(s.loc[idx, sinal].astype(float))
            s.loc[idx, col] = alerta
            limiares.append({"exercicio": ano, "grupo": grupo, "sinal": sinal, "n": int(alerta.notna().sum()),
                             "limite_p90": limite})  # fmt: skip
    cols_nf = ["alerta_mscore", "alerta_dpo", "alerta_juro"]
    s["avaliada"] = False
    s["em_alerta"] = False
    s.loc[nf, "avaliada"] = s.loc[nf, cols_nf].notna().any(axis=1)
    s.loc[nf, "em_alerta"] = s.loc[nf, cols_nf].fillna(False).any(axis=1)
    s.loc[fin, "avaliada"] = s.loc[fin, "alerta_peso_nao_recorrente"].notna()
    s.loc[fin, "em_alerta"] = s.loc[fin, "alerta_peso_nao_recorrente"].fillna(False).astype(bool)
    return s, pd.DataFrame(limiares)


def _git(*args: str) -> str:
    return subprocess.run(["git", *args], cwd=RAIZ, capture_output=True, text=True, check=True).stdout.strip()


def main() -> None:
    inicio = datetime.now(timezone.utc).isoformat(timespec="seconds")
    meta = pd.read_csv(BASE / "empresa_ano.csv", dtype={"cd_cvm": str, "num_doc": str})
    meta = meta[meta.exercicio.isin(ANOS)]
    s, limiares = alertas(calcula(meta))
    SAIDA.mkdir(exist_ok=True)
    s.to_csv(SAIDA / "sinais_empresa_ano.csv", index=False)
    limiares.to_csv(SAIDA / "limiares.csv", index=False)
    execucao = {
        "commit": _git("rev-parse", "HEAD"),
        "codigo_sem_alteracao_local": _git("status", "--porcelain", "--untracked-files=no", "--", "chiocca") == "",
        "inicio_utc": inicio,
        "fim_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }
    (SAIDA / "execucao.json").write_text(json.dumps(execucao, indent=1) + "\n", encoding="utf-8")
    print(s.amostra.value_counts().to_string())


if __name__ == "__main__":
    main()
