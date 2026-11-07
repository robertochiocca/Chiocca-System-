"""Análise secundária da emenda 5, rotulada como tal: empresa-anos sem versão da época, com a versão disponível.

A emenda 5 tira da análise principal as empresa-anos cuja versão da época não pôde ser obtida (com a emenda 8, as
que só têm demonstração individual reentregue depois do corte) e manda, numa análise secundária, incluí-las com a
versão disponível: a última, a dos dados abertos, entregue depois da data de corte. Isso usa informação posterior
ao corte nessas empresa-anos; por isso não entra na conta principal.

O grupo segue a regra congelada (setor do FCA entregue até o corte, plano de contas da DFP usada) e a exclusão por
falta de receita vale igual. Os decis de cada ano são recalculados com as empresa-anos incluídas.

Uso: python -m chiocca.emenda5   (precisa de data/brutos e data/base; grava em resultados/, fora do git)
"""

from __future__ import annotations

from datetime import date
from pathlib import Path

import pandas as pd

from chiocca import base, grupos, montar_base
from chiocca.cvm import Fontes
from chiocca.sinais_amostra import ANOS, BASE, SAIDA, alertas, calcula

INDISPONIVEIS = (base.INDISPONIVEL_INDIVIDUAL, base.INDISPONIVEL_ENET)
CORTE_ABERTO = date(2100, 12, 31)  # qualquer versão entregue até hoje: a dos dados abertos
PASTA = SAIDA / "emenda5_base"


def leituras_disponiveis(fontes: Fontes, meta: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Linhas de meta e contas das empresa-anos sem versão da época, lidas na versão disponível."""
    linhas, partes = [], []
    alvo = meta[meta.status.isin(INDISPONIVEIS) & meta.exercicio.isin(ANOS)]
    for e in alvo.itertuples(index=False):
        leitura = base.como_era(fontes, e.cd_cvm, int(e.exercicio), corte=CORTE_ABERTO, dt_refer=e.dt_refer)
        corte = date.fromisoformat(str(e.data_corte))
        st, origem = grupos.setor(fontes, e.cd_cvm, int(e.exercicio), corte)
        ok = leitura.status == base.OK
        plano = grupos.plano_de_contas(grupos.descricao_301(leitura.contas)) if ok else None
        rec = montar_base.receita(leitura.contas) if ok else None
        nova = e._asdict() | {
            "status": leitura.status,
            "versao": leitura.versao,
            "dt_receb": leitura.dt_receb,
            "tipo": leitura.tipo,
            "fonte": "disponivel_emenda5",
            "num_doc": leitura.num_doc,
            "setor": st,
            "origem_setor": origem,
            "plano": plano,
            "grupo": grupos.grupo(st, plano) if plano else None,
            "sem_receita": (rec is None or rec == 0) if ok else None,
        }
        linhas.append(nova)
        if ok:
            c = leitura.contas.copy()
            c.insert(0, "dt_refer", leitura.dt_refer)
            c.insert(0, "cd_cvm", leitura.cd_cvm)
            partes.append(c)
    contas = pd.concat(partes, ignore_index=True) if partes else pd.DataFrame()
    return pd.DataFrame(linhas), contas


def monta_base_estendida(
    meta: pd.DataFrame, extra_meta: pd.DataFrame, extra_contas: pd.DataFrame, base_dir: Path = BASE, pasta: Path = PASTA
) -> pd.DataFrame:
    """Grava contas_<ano>.csv.gz com as empresa-anos incluídas e devolve a meta estendida."""
    pasta.mkdir(parents=True, exist_ok=True)
    chave = ["cd_cvm", "dt_refer", "exercicio"]
    resto = meta.merge(extra_meta[chave], on=chave, how="left", indicator=True)
    estendida = pd.concat([resto[resto._merge == "left_only"].drop(columns="_merge"), extra_meta], ignore_index=True)
    for ano in ANOS:
        c = pd.read_csv(base_dir / f"contas_{ano}.csv.gz", dtype={"cd_cvm": str, "cd_conta": str, "ds_conta": str})
        novos = extra_meta[extra_meta.exercicio == ano][["cd_cvm", "dt_refer"]]
        if not extra_contas.empty and not novos.empty:
            c = pd.concat([c, extra_contas.merge(novos, on=["cd_cvm", "dt_refer"])], ignore_index=True)
        c.to_csv(pasta / f"contas_{ano}.csv.gz", index=False)
    return estendida


def main() -> None:
    meta = pd.read_csv(BASE / "empresa_ano.csv", dtype={"cd_cvm": str, "num_doc": str})
    meta = meta[meta.exercicio.isin(ANOS)]
    fontes = Fontes(base.BRUTOS, base.CACHE_ENET)
    extra_meta, extra_contas = leituras_disponiveis(fontes, meta)
    estendida = monta_base_estendida(meta, extra_meta, extra_contas)
    s, limiares = alertas(calcula(estendida, PASTA))
    chaves = set(zip(extra_meta.cd_cvm, extra_meta.dt_refer))
    s["incluida_emenda5"] = [(c, d) in chaves for c, d in zip(s.cd_cvm, s.dt_refer)]
    s.to_csv(SAIDA / "sinais_emenda5.csv", index=False)
    limiares.to_csv(SAIDA / "limiares_emenda5.csv", index=False)
    print(extra_meta.status.value_counts().to_string())
    print(s[s.incluida_emenda5].amostra.value_counts().to_string())


if __name__ == "__main__":
    main()
