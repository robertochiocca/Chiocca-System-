"""Metadados de Americanas e IRB autorizados por Roberto em 05/11/2026.

Só índice de documentos (versões e DT_RECEB) das DFPs de 2017 a 2022 e rótulos de
contas (CD_CONTA, DS_CONTA) do IRB. Nunca lê VL_CONTA.
"""

from __future__ import annotations

import pandas as pd

from comum import ler_dfp, cadastro, cd, norm

CNPJ_AMERICANAS = "00.776.574/0006-60"
CASOS = {"8087": "Lojas Americanas", "20990": "Americanas S.A.", "24180": "IRB"}
ANOS = range(2017, 2023)


def data_corte(dt_refer: str) -> pd.Timestamp:
    """Emenda 5: último dia do quarto mês depois do fim do exercício."""
    fim = pd.Timestamp(dt_refer)
    return (fim + pd.offsets.MonthEnd(4)).normalize()


def main() -> None:
    cad = cadastro()
    m = cad[cad.CNPJ_CIA == CNPJ_AMERICANAS]
    print(f"Cadastro, CNPJ {CNPJ_AMERICANAS}:")
    print(m[["CD_CVM", "DENOM_SOCIAL", "SIT", "DT_REG", "SETOR_ATIV"]].to_string(index=False))
    for c in CASOS:
        r = cad[cd(cad.CD_CVM) == c][
            ["CD_CVM", "CNPJ_CIA", "DENOM_SOCIAL", "SIT", "DT_CANCEL", "MOTIVO_CANCEL", "SETOR_ATIV"]
        ]
        print(f"\nCadastro, CD_CVM {c}:\n{r.to_string(index=False)}")

    print("\nÍndice da DFP (2010-2026), linhas com esse CNPJ: ano | CD_CVM | DENOM_CIA | versões")
    for ano in range(2010, 2027):
        idx = ler_dfp(ano, "", ["CNPJ_CIA", "CD_CVM", "DENOM_CIA", "VERSAO"])
        s = idx[idx.CNPJ_CIA == CNPJ_AMERICANAS]
        if len(s):
            print(
                f"  {ano} | {sorted(set(cd(s.CD_CVM)))} | {sorted(set(s.DENOM_CIA))} | {sorted(s.VERSAO.astype(int))}"
            )

    print("\nVersões das DFPs 2017-2022 (índice), corte pela Emenda 5:")
    print("caso | DFP | DT_REFER | VERSAO | DT_RECEB | corte | entregue até o corte? | é a versão dos dados abertos?")
    for ano in ANOS:
        idx = ler_dfp(ano, "", ["CD_CVM", "DT_REFER", "VERSAO", "DT_RECEB", "ID_DOC"])
        idx = idx[cd(idx.CD_CVM).isin(CASOS)].copy()
        idx["VERSAO"] = idx.VERSAO.astype(int)
        for (c, ref), g in idx.groupby([cd(idx.CD_CVM), "DT_REFER"]):
            corte = data_corte(ref)
            vmax = g.VERSAO.max()
            for r in g.sort_values("VERSAO").itertuples():
                ate = pd.Timestamp(r.DT_RECEB) <= corte
                print(
                    f"  {CASOS[c]} ({c}) | {ano} | {ref} | {r.VERSAO} | {r.DT_RECEB} | {corte.date()} | "
                    f"{'sim' if ate else 'NÃO'} | {'sim' if r.VERSAO == vmax else 'não'}"
                )

    print("\nIRB (24180): rótulos da DRE, DFP 2017-2022 (sem valores)")
    for ano in ANOS:
        for tipo in ("con", "ind"):
            d = ler_dfp(ano, f"DRE_{tipo}", ["CD_CVM", "ORDEM_EXERC", "CD_CONTA", "DS_CONTA", "ST_CONTA_FIXA"])
            d = d[(cd(d.CD_CVM) == "24180") & (d.ORDEM_EXERC == "ÚLTIMO")]
            if d.empty:
                print(f"  {ano} {tipo}: sem DRE")
                continue
            n = d.DS_CONTA.map(norm)
            num = d[n.str.startswith("outras receitas")]
            den = d[n.str.startswith("resultado antes dos tributos")]
            codes = set(num.CD_CONTA)
            num_ok = num[[c.rsplit(".", 1)[0] not in codes for c in num.CD_CONTA]]  # Emenda 4
            p301 = d[d.CD_CONTA == "3.01"].DS_CONTA.tolist()
            print(
                f"  {ano} {tipo}: 3.01 = {p301} | contas: {len(d)} | numerador (Emenda 5 + regra da Emenda 4): "
                f"{[(r.CD_CONTA, r.DS_CONTA, r.ST_CONTA_FIXA) for r in num_ok.itertuples()]} | "
                f"denominador: {[(r.CD_CONTA, r.DS_CONTA) for r in den.itertuples()]}"
            )
    d = ler_dfp(2019, "DRE_con", ["CD_CVM", "ORDEM_EXERC", "CD_CONTA", "DS_CONTA", "ST_CONTA_FIXA"])
    d = d[(cd(d.CD_CVM) == "24180") & (d.ORDEM_EXERC == "ÚLTIMO")]
    print("\nIRB, DRE consolidada da DFP 2019, todas as contas (código | descrição | fixa):")
    for r in d.itertuples():
        print(f"  {r.CD_CONTA} | {r.DS_CONTA} | {r.ST_CONTA_FIXA}")
    b = ler_dfp(2019, "BPP_con", ["CD_CVM", "ORDEM_EXERC", "CD_CONTA", "DS_CONTA"])
    b = b[(cd(b.CD_CVM) == "24180") & (b.ORDEM_EXERC == "ÚLTIMO") & (b.CD_CONTA.str.count(r"\.") <= 1)]
    print("\nIRB, BPP consolidado da DFP 2019, contas de nível 1 e 2:")
    for r in b.itertuples():
        print(f"  {r.CD_CONTA} | {r.DS_CONTA}")


if __name__ == "__main__":
    main()
