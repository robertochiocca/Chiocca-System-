"""Grupo (financeira / não financeira) pela regra da Emenda 5 e da decisão de 05/11/2026.

O setor (FCA do ano; sem FCA, cadastro) define a candidata a financeira; o plano de contas
da DFP (consolidada se existir, senão individual) decide o grupo. Só estrutura.
"""

from __future__ import annotations

import collections


from comum import ANOS_COMPLETOS, cadastro, cd, excluidos, ler_fca_geral, planos

SETORES_FINANCEIROS = [
    "Bancos",
    "Intermediação Financeira",
    "Arrendamento Mercantil",
    "Seguradoras e Corretoras",
    "Crédito Imobiliário",
    "Emp. Adm. Part. - Bancos",
    "Emp. Adm. Part. - Intermediação Financeira",
    "Emp. Adm. Part. - Arrendamento Mercantil",
    "Emp. Adm. Part. - Seguradoras e Corretoras",
    "Emp. Adm. Part. - Crédito Imobiliário",
]


def setor_por_ano() -> dict[tuple[int, str], str]:
    """Setor do FCA de cada ano (última versão do ano)."""
    out: dict[tuple[int, str], str] = {}
    for ano in ANOS_COMPLETOS:
        f = ler_fca_geral(ano)
        f["Versao"] = f.Versao.astype(int)
        f = f.sort_values("Versao").drop_duplicates("Codigo_CVM", keep="last")
        for r in f.itertuples():
            if isinstance(r.Setor_Atividade, str):
                out[(ano, str(int(r.Codigo_CVM)))] = r.Setor_Atividade
    return out


def main() -> None:
    exc = excluidos()
    pl = planos(exc)
    # consolidada quando existir, senão individual (Emenda 5)
    pl = pl.sort_values("tipo").drop_duplicates(["ano", "cd"], keep="first")  # 'con' < 'ind'
    fca = setor_por_ano()
    cad = cadastro().drop_duplicates("CD_CVM", keep="last")
    setor_cad = dict(zip(cd(cad.CD_CVM), cad.SETOR_ATIV))
    cont: collections.Counter = collections.Counter()
    fonte: collections.Counter = collections.Counter()
    fora_fin: collections.Counter = collections.Counter()
    for r in pl.itertuples():
        s = fca.get((r.ano, r.cd))
        fonte["FCA do ano" if s else ("cadastro" if isinstance(setor_cad.get(r.cd), str) else "sem setor")] += 1
        s = s or setor_cad.get(r.cd)
        cand = s in SETORES_FINANCEIROS
        fin = cand and r.plano in ("banco", "seguradora")
        cont[(("candidata" if cand else "não candidata"), r.plano, "financeira" if fin else "não financeira")] += 1
        if not cand and r.plano in ("banco", "seguradora"):
            fora_fin[(s if isinstance(s, str) else "(sem setor)", r.plano)] += 1
    print("Empresa-anos 2010-2025 (sem Americanas e IRB), demonstração usada = consolidada se existir:")
    print(f"  origem do setor: {dict(fonte)}")
    for k, v in sorted(cont.items()):
        print(f"  {k[0]} | plano {k[1]} | grupo {k[2]} | {v}")
    print("  não candidatas com plano de banco/seguradora (setor | plano | empresa-anos):")
    for (s, p), v in fora_fin.most_common():
        print(f"    {s} | {p} | {v}")


if __name__ == "__main__":
    main()
