"""Monta a base "como era na época" para todas as empresa-anos da DFP (Fase 1). Nenhum sinal é calculado.

Saídas, fora do git (data/base/):
- empresa_ano.csv: uma linha por empresa-ano (código CVM e data de referência), com a versão usada, a
  fonte (dados abertos ou ENET), o status, o tipo (consolidado ou individual), o setor e a origem do setor,
  o plano de contas, o grupo (financeira ou não financeira), a marca de "sem receita" e a situação no
  cadastro;
- contas_<ano>.csv.gz: as contas das empresa-anos com status ok, nas colunas ÚLTIMO e PENÚLTIMO, em reais;
- data/cache/enet/pendentes.txt: documentos cuja versão da época precisa vir do ENET (consolidado).

Uso: python -m chiocca.montar_base [ano_inicial ano_final]   (padrão: 2010 a 2025)
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

from chiocca import base, grupos
from chiocca.cvm import Fontes

SAIDA = base.RAIZ / "data" / "base"
ANOS_PADRAO = (2010, 2025)


def situacao_cadastro(fontes: Fontes) -> dict[str, str]:
    cad = fontes.cadastro()
    sit: dict[str, str] = {}
    for cd, g in cad.groupby("cd_cvm"):
        valores = set(g.SIT.dropna())
        sit[str(cd)] = "ATIVO" if "ATIVO" in valores else (sorted(valores)[0] if valores else "sem_situacao")
    return sit


def receita(contas: pd.DataFrame) -> float | None:
    r = contas[(contas.demonstracao == "DRE") & (contas.ordem == "ÚLTIMO") & (contas.cd_conta == "3.01")]
    return None if r.empty else float(r.valor.iloc[0])


def monta(fontes: Fontes, anos: range, saida: Path = SAIDA) -> pd.DataFrame:
    saida.mkdir(parents=True, exist_ok=True)
    sit = situacao_cadastro(fontes)
    linhas = []
    pendentes = []
    for ano in anos:
        idx = fontes.indice_dfp(ano)
        pares = idx[["cd_cvm", "DT_REFER", "CNPJ_CIA", "DENOM_CIA"]].drop_duplicates(["cd_cvm", "DT_REFER"])
        partes = []
        for p in pares.itertuples():
            leitura = base.como_era(fontes, p.cd_cvm, ano, dt_refer=p.DT_REFER)
            if leitura.status == base.PENDENTE_ENET:
                pendentes.append(f"{leitura.num_doc} {leitura.versao}")
            st, origem = (
                grupos.setor(fontes, p.cd_cvm, ano, leitura.data_corte) if leitura.data_corte else (None, "nenhum")
            )
            plano = grupos.plano_de_contas(grupos.descricao_301(leitura.contas)) if leitura.status == base.OK else None
            rec = receita(leitura.contas) if leitura.status == base.OK else None
            linhas.append(
                {
                    "exercicio": ano,
                    "cd_cvm": p.cd_cvm,
                    "dt_refer": p.DT_REFER,
                    "cnpj": p.CNPJ_CIA,
                    "denominacao": p.DENOM_CIA,
                    "data_corte": leitura.data_corte,
                    "status": leitura.status,
                    "versao": leitura.versao,
                    "dt_receb": leitura.dt_receb,
                    "ultima_versao": leitura.ultima_versao,
                    "tipo": leitura.tipo,
                    "fonte": leitura.fonte,
                    "num_doc": leitura.num_doc,
                    "repetidas_iguais": leitura.repetidas_iguais,
                    "setor": st,
                    "origem_setor": origem,
                    "plano": plano,
                    "grupo": grupos.grupo(st, plano) if plano else None,
                    "sem_receita": (rec is None or rec == 0) if leitura.status == base.OK else None,
                    "situacao_cadastro": sit.get(p.cd_cvm, "fora_do_cadastro"),
                }
            )
            if leitura.status == base.OK:
                c = leitura.contas.copy()
                c.insert(0, "dt_refer", leitura.dt_refer)
                c.insert(0, "cd_cvm", leitura.cd_cvm)
                partes.append(c)
        if partes:
            pd.concat(partes, ignore_index=True).to_csv(saida / f"contas_{ano}.csv.gz", index=False)
        print(ano, len(pares), flush=True)
    meta = pd.DataFrame(linhas)
    meta.to_csv(saida / "empresa_ano.csv", index=False)
    fontes.cache_enet.mkdir(parents=True, exist_ok=True)
    (fontes.cache_enet / "pendentes.txt").write_text("\n".join(pendentes) + ("\n" if pendentes else ""))
    return meta


if __name__ == "__main__":
    a, b = (int(sys.argv[1]), int(sys.argv[2])) if len(sys.argv) == 3 else ANOS_PADRAO
    m = monta(Fontes(base.BRUTOS, base.CACHE_ENET), range(a, b + 1))
    print(m.groupby(["exercicio", "status"]).size().unstack(fill_value=0).to_string())
