"""Padrões de texto finais da DFC (Emenda 5) e sua cobertura. Só rótulos, sem valores.

Texto comparado: DS_CONTA em minúsculas, sem acento e sem espaços nas pontas (comum.norm).
Seção: prefixo do CD_CONTA. Se a conta-mãe e a subconta casam, conta só a mãe (mesma regra
da Emenda 4), para não somar o mesmo valor duas vezes.
"""

from __future__ import annotations

import collections

from comum import ANOS_COMPLETOS, cd, excluidos, ler_dfp, norm, planos, sem_excluidos

PADROES = {
    "depreciacao": {"secoes": ("6.01.01",), "todos": [["deprecia"]], "nenhum": []},
    "juros_pagos": {
        "secoes": ("6.01", "6.03"),
        "todos": [["juros"], ["pago", "pagos", "pagamento", "pagamentos"]],
        "nenhum": ["capital proprio", "recebid"],
    },
    "capex": {
        "secoes": ("6.02",),
        "todos": [["aquisic", "adic", "compra", "investimento"], ["imobilizado", "intangivel"]],
        "nenhum": ["venda", "alienac", "baixa", "recebimento"],
    },
    "dividendos_pagos": {"secoes": ("6.03",), "todos": [["dividendo", "capital proprio"]], "nenhum": ["recebid"]},
    "ir_csll_pagos": {
        "secoes": ("6.01",),
        "todos": [
            ["imposto de renda", "ir e cs", "irpj", "ir/cs", "ir/csll"],
            ["pago", "pagos", "pagamento", "pagamentos"],
        ],
        "nenhum": [],
    },
    "emissao_titulos": {
        "secoes": ("6.03",),
        "todos": [["captac", "emiss", "ingress"]],
        "nenhum": ["pagamento", "amortiza", "liquida", "resgat"],
    },
}


def casa(texto: str, p: dict) -> bool:
    return all(any(t in texto for t in grupo) for grupo in p["todos"]) and not any(t in texto for t in p["nenhum"])


def main() -> None:
    exc = excluidos()
    pl = planos(exc)
    naofin = {(r.ano, r.tipo, r.cd) for r in pl.itertuples() if r.plano == "nao_financeiro"}
    base: collections.Counter = collections.Counter()
    achou: collections.Counter = collections.Counter()
    top: dict[str, collections.Counter] = collections.defaultdict(collections.Counter)
    mae_filha: collections.Counter = collections.Counter()
    dep_comb: collections.Counter = collections.Counter()
    emiss_gasto: collections.Counter = collections.Counter()
    for ano in ANOS_COMPLETOS:
        for tipo in ("con", "ind"):
            d = sem_excluidos(ler_dfp(ano, f"DFC_MI_{tipo}", ["CD_CVM", "ORDEM_EXERC", "CD_CONTA", "DS_CONTA"]), exc)
            d = d[d.ORDEM_EXERC == "ÚLTIMO"].copy()
            d["cd"] = cd(d.CD_CVM)
            d = d[[(ano, tipo, c) in naofin for c in d.cd]]
            d["n"] = d.DS_CONTA.map(norm)
            for c, g in d.groupby("cd"):
                base[tipo] += 1
                for nome, p in PADROES.items():
                    m = g[
                        g.CD_CONTA.apply(lambda x: any(x.startswith(s + ".") for s in p["secoes"]))
                        & g.n.apply(lambda t: casa(t, p))
                    ]
                    if m.empty:
                        continue
                    codes = set(m.CD_CONTA)
                    filhas = [x for x in codes if x.rsplit(".", 1)[0] in codes]
                    if filhas:
                        mae_filha[nome] += 1
                    m = m[[x.rsplit(".", 1)[0] not in codes for x in m.CD_CONTA]]
                    achou[(nome, tipo)] += 1
                    for t in m.n:
                        top[nome][t[:70]] += 1
                    if nome == "depreciacao":
                        dep_comb[
                            (
                                "marcar (com amortização/exaustão)"
                                if m.n.str.contains("amortiza|exaust").any()
                                else "só depreciação"
                            )
                        ] += 1
                    if nome == "emissao_titulos" and m.n.str.contains("gasto|custo").any():
                        emiss_gasto["tem linha de gasto/custo de emissão"] += 1
    print(f"base (empresa-anos de plano não financeiro com DFC_MI): {dict(base)}")
    for nome in PADROES:
        print(
            f"\n=== {nome}: con {achou[(nome, 'con')] / base['con']:.1%} | ind {achou[(nome, 'ind')] / base['ind']:.1%} | "
            f"empresa-anos com mãe e filha casando: {mae_filha[nome]}"
        )
        for t, q in top[nome].most_common(10):
            print(f"    {q:6d}  {t}")
    print("\ndepreciação:", dict(dep_comb))
    print("emissões:", dict(emiss_gasto))


if __name__ == "__main__":
    main()
