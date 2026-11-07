"""Nomes distintos de setor no cadastro (SETOR_ATIV, atual) e no FCA (Setor_Atividade, por ano)."""

from __future__ import annotations

import collections

from comum import cadastro, ler_fca_geral, ANOS_DFP


def main() -> None:
    cad = cadastro().drop_duplicates("CD_CVM")
    print("Cadastro (SETOR_ATIV), empresas distintas por nome de setor:")
    for nome, n in cad.SETOR_ATIV.fillna("(vazio)").value_counts().sort_index().items():
        print(f"  {nome} | {n}")
    anos_por_nome: dict[str, set[int]] = collections.defaultdict(set)
    emp_por_nome: dict[str, set[str]] = collections.defaultdict(set)
    for ano in ANOS_DFP:
        f = ler_fca_geral(ano)
        for r in f[["Codigo_CVM", "Setor_Atividade"]].itertuples():
            nome = r.Setor_Atividade if isinstance(r.Setor_Atividade, str) else "(vazio)"
            anos_por_nome[nome].add(ano)
            emp_por_nome[nome].add(str(r.Codigo_CVM))
    print("\nFCA 2010-2026 (Setor_Atividade): nome | empresas distintas | primeiro-último ano")
    for nome in sorted(anos_por_nome):
        a = anos_por_nome[nome]
        print(f"  {nome} | {len(emp_por_nome[nome])} | {min(a)}-{max(a)}")
    so_fca = set(anos_por_nome) - set(cad.SETOR_ATIV.fillna("(vazio)"))
    so_cad = set(cad.SETOR_ATIV.fillna("(vazio)")) - set(anos_por_nome)
    print(f"\nSó no FCA: {sorted(so_fca)}\nSó no cadastro: {sorted(so_cad)}")


def tabela_markdown() -> str:
    """Tabela única: nome | empresas no cadastro | empresas no FCA | anos no FCA."""
    cad = cadastro().drop_duplicates("CD_CVM")
    n_cad = cad.SETOR_ATIV.fillna("(vazio)").value_counts().to_dict()
    anos: dict[str, set[int]] = collections.defaultdict(set)
    emp: dict[str, set[str]] = collections.defaultdict(set)
    for ano in ANOS_DFP:
        f = ler_fca_geral(ano)
        for r in f[["Codigo_CVM", "Setor_Atividade"]].itertuples():
            nome = r.Setor_Atividade if isinstance(r.Setor_Atividade, str) else "(vazio)"
            anos[nome].add(ano)
            emp[nome].add(str(r.Codigo_CVM))
    linhas = ["| Nome do setor | Empresas no cadastro | Empresas no FCA | Anos no FCA |", "| --- | --- | --- | --- |"]
    for nome in sorted(set(n_cad) | set(anos), key=lambda s: (s == "(vazio)", s)):
        a = anos.get(nome)
        linhas.append(
            f"| {nome} | {n_cad.get(nome, '—')} | {len(emp[nome]) if a else '—'} | {f'{min(a)}–{max(a)}' if a else '—'} |"
        )
    return "\n".join(linhas)


if __name__ == "__main__":
    import sys

    print(tabela_markdown() if "--tabela" in sys.argv else "", end="")
    if "--tabela" not in sys.argv:
        main()
