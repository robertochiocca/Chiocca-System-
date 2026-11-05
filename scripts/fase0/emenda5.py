"""Estrutura das linhas que a Emenda 5 usa nas financeiras e das contas 2.01/2.02 da regra boba.

Só rótulos (CD_CONTA, DS_CONTA). Sem Americanas e IRB (o IRB está em autorizados.py).
"""

from __future__ import annotations

import collections

from comum import ANOS_COMPLETOS, cd, excluidos, ler_dfp, norm, planos, sem_excluidos


def main() -> None:
    exc = excluidos()
    pl = planos(exc)
    grupo = {(r.ano, r.tipo, r.cd): r.plano for r in pl.itertuples()}
    num_desc: dict[str, collections.Counter] = collections.defaultdict(collections.Counter)
    den_n: dict[str, collections.Counter] = collections.defaultdict(collections.Counter)
    bpp: dict[str, collections.Counter] = collections.defaultdict(collections.Counter)
    for ano in ANOS_COMPLETOS:
        for tipo in ("con", "ind"):
            d = sem_excluidos(ler_dfp(ano, f"DRE_{tipo}", ["CD_CVM", "ORDEM_EXERC", "CD_CONTA", "DS_CONTA"]), exc)
            d = d[d.ORDEM_EXERC == "ÚLTIMO"].copy()
            d["cd"] = cd(d.CD_CVM)
            d["n"] = d.DS_CONTA.map(norm)
            for c, g in d.groupby("cd"):
                p = grupo.get((ano, tipo, c), "sem_3.01")
                if p not in ("banco", "seguradora"):
                    continue
                num = g[g.n.str.startswith("outras receitas")]
                codes = set(num.CD_CONTA)
                num = num[[x.rsplit(".", 1)[0] not in codes for x in num.CD_CONTA]]  # Emenda 4
                for r in num.itertuples():
                    nivel = r.CD_CONTA if r.CD_CONTA.count(".") <= 2 else r.CD_CONTA.rsplit(".", 1)[0] + ".xx"
                    num_desc[p][(nivel, r.n[:60])] += 1
                den_n[p][len(g[g.n.str.startswith("resultado antes dos tributos")])] += 1
            if ano in (2012, 2019, 2023):
                b = sem_excluidos(ler_dfp(ano, f"BPP_{tipo}", ["CD_CVM", "ORDEM_EXERC", "CD_CONTA", "DS_CONTA"]), exc)
                b = b[(b.ORDEM_EXERC == "ÚLTIMO") & (b.CD_CONTA.str.count(r"\.") <= 1)].copy()
                b["cd"] = cd(b.CD_CVM)
                for r in b.drop_duplicates(["cd", "CD_CONTA"]).itertuples():
                    p = grupo.get((ano, tipo, r.cd), "sem_3.01")
                    if p in ("banco", "seguradora"):
                        bpp[p][(r.CD_CONTA, r.DS_CONTA.strip())] += 1
    for p in ("banco", "seguradora"):
        print(f"\n=== plano {p}: linhas do numerador pela Emenda 5 (começa com 'outras receitas', regra da Emenda 4)")
        for (c, n), q in num_desc[p].most_common(15):
            print(f"  {c} | {n} | {q}")
        print(f"  empresa-anos por nº de linhas do denominador ('resultado antes dos tributos'): {dict(den_n[p])}")
        print(f"  BPP nível 1-2 (DFP 2012, 2019, 2023): {sorted(bpp[p].items())}")


if __name__ == "__main__":
    main()
