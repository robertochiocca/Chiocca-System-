"""Contagens de estrutura da Fase 0 (partes 1 e 2 de docs/reconhecimento.md).

Só estrutura: nenhuma linha lê VL_CONTA, e Americanas e IRB são removidos antes de tudo.
Uso: CHIOCCA_CVM_RAW=<pasta> python estrutura.py [secao ...]
Seções: versoes, dominios, cadastro, planos, conind, codigos, financeiras, bancos, dfc, dva.
"""

from __future__ import annotations

import collections
import re
import sys

import pandas as pd

from comum import ANOS_COMPLETOS, ANOS_DFP, cadastro, cd, excluidos, ler_dfp, norm, sem_excluidos, tipo_plano

EXC = excluidos()
FIN_SETOR = re.compile(r"Bancos|Seguradoras|Intermedia|Arrendamento|Crédito Imob|Securitiza|Factoring|Bolsas", re.I)


def planos_fase0() -> pd.DataFrame:
    """Descrições de 3.01, 3.02 e 3.03 por (ano, tipo, cd), como na Fase 0, com o setor do cadastro."""
    linhas = []
    for ano in ANOS_COMPLETOS:
        for tipo in ("con", "ind"):
            d = sem_excluidos(ler_dfp(ano, f"DRE_{tipo}", ["CD_CVM", "ORDEM_EXERC", "CD_CONTA", "DS_CONTA"]), EXC)
            d = d[(d.ORDEM_EXERC == "ÚLTIMO") & d.CD_CONTA.isin(["3.01", "3.02", "3.03"])]
            p = d.pivot_table(index="CD_CVM", columns="CD_CONTA", values="DS_CONTA", aggfunc="first")
            for c, r in p.iterrows():
                linhas.append((ano, tipo, str(int(c)), r.get("3.01")))
    df = pd.DataFrame(linhas, columns=["ano", "tipo", "cd", "d301"])
    cad = cadastro().drop_duplicates("CD_CVM", keep="last")
    setor = dict(zip(cd(cad.CD_CVM), cad.SETOR_ATIV.fillna("(vazio)")))
    df["setor"] = df.cd.map(setor).fillna("(fora do cadastro)")
    return df


def naofin_estrito(pl: pd.DataFrame) -> set:
    """Plano não financeiro da Fase 0: 3.01 contém 'venda de bens'."""
    return {
        (r.ano, r.tipo, r.cd) for r in pl.itertuples() if isinstance(r.d301, str) and "venda de bens" in norm(r.d301)
    }


def versoes() -> None:
    print(
        "ano | docs no índice | cias | DT_REFER fora de 31/12 | (cia,ano) com >1 linha | VERSAO máx | DT_RECEB min..max"
    )
    dist: collections.Counter = collections.Counter()
    for ano in ANOS_DFP:
        idx = sem_excluidos(ler_dfp(ano, ""), EXC)
        multi = idx.groupby(["CD_CVM", "DT_REFER"]).size()
        dist.update(idx.VERSAO.astype(int))
        print(
            ano,
            len(idx),
            idx.CD_CVM.nunique(),
            (~idx.DT_REFER.str.endswith("-12-31")).sum(),
            (multi > 1).sum(),
            idx.VERSAO.astype(int).max(),
            idx.DT_RECEB.min(),
            idx.DT_RECEB.max(),
            sep=" | ",
        )
    print("VERSAO no índice:", dict(sorted(dist.items())))
    print(
        "\nano | (cia,ano) BPA_con | versão do arquivo = máx do índice | última versão depois do corte | dessas, v1 até o corte"
    )
    for ano in ANOS_COMPLETOS:
        idx = sem_excluidos(ler_dfp(ano, "", ["CD_CVM", "DT_REFER", "VERSAO", "DT_RECEB"]), EXC)
        idx["VERSAO"] = idx.VERSAO.astype(int)
        df = sem_excluidos(ler_dfp(ano, "BPA_con", ["CD_CVM", "DT_REFER", "VERSAO"]), EXC).drop_duplicates()
        df["VERSAO"] = df.VERSAO.astype(int)
        assert df.groupby(["CD_CVM", "DT_REFER"]).size().max() == 1, "mais de uma versão no arquivo"
        mx = idx.groupby(["CD_CVM", "DT_REFER"]).VERSAO.max()
        m = df.set_index(["CD_CVM", "DT_REFER"]).VERSAO
        eq = sum(m[k] == mx.get(k) for k in m.index)
        corte = f"{ano + 1}-04-30"
        last = idx.loc[idx.groupby(["CD_CVM", "DT_REFER"]).VERSAO.idxmax()]
        tarde = last[(last.DT_RECEB > corte) & last.DT_REFER.str.startswith(str(ano))]
        v1 = idx[idx.VERSAO == idx.groupby(["CD_CVM", "DT_REFER"]).VERSAO.transform("min")]
        v1ok = set(v1[v1.DT_RECEB <= corte].set_index(["CD_CVM", "DT_REFER"]).index)
        n_v1ok = sum(k in v1ok for k in tarde.set_index(["CD_CVM", "DT_REFER"]).index)
        print(ano, len(m), f"{eq}/{len(m)}", len(tarde), n_v1ok, sep=" | ")


def dominios() -> None:
    esc: collections.Counter = collections.Counter()
    moe: collections.Counter = collections.Counter()
    ordm: collections.Counter = collections.Counter()
    mix = nfil = 0
    for ano in ANOS_COMPLETOS:
        for f in ("BPA_con", "BPA_ind", "DRE_con", "DRE_ind", "DFC_MI_con", "DFC_MI_ind"):
            d = sem_excluidos(ler_dfp(ano, f, ["CD_CVM", "DT_REFER", "MOEDA", "ESCALA_MOEDA", "ORDEM_EXERC"]), EXC)
            esc.update(d.ESCALA_MOEDA)
            moe.update(d.MOEDA)
            ordm.update(d.ORDEM_EXERC)
            g = d.groupby(["CD_CVM", "DT_REFER"]).ESCALA_MOEDA.nunique()
            mix += int((g > 1).sum())
            nfil += len(g)
    print(
        "ESCALA_MOEDA:",
        dict(esc),
        "| MOEDA:",
        dict(moe),
        "| ORDEM_EXERC:",
        dict(ordm),
        f"| mais de uma escala: {mix} de {nfil}",
    )


def cadastro_resumo() -> None:
    cad = cadastro()
    print("linhas:", len(cad), "| CD_CVM distintos:", cad.CD_CVM.nunique(), "| SIT:", dict(cad.SIT.value_counts()))
    cad["CD"] = cd(cad.CD_CVM)
    sit = cad.sort_values("DT_INI_SIT").drop_duplicates("CD", keep="last").set_index("CD").SIT
    for ano in (2010, 2015, 2019, 2023):
        ids = set(cd(sem_excluidos(ler_dfp(ano, "", ["CD_CVM"]), EXC).CD_CVM))
        print(
            f"DFP {ano}: {len(ids)} empresas | situação hoje:",
            dict(pd.Series([sit.get(i, "(fora do cadastro)") for i in ids]).value_counts()),
        )


def planos() -> None:
    pl = planos_fase0()
    print("descrição de 3.01 (normalizada), empresa-anos:")
    print(pl.d301.map(norm).value_counts().head(12).to_string())
    pl["plano"] = pl.d301.map(norm)
    top = pl.plano.value_counts().head(6).index
    t = pl[pl.plano.isin(top)].groupby(["setor", "plano"]).cd.nunique().unstack(fill_value=0)
    print(t[t.sum(axis=1) > 0].to_string())


def conind() -> None:
    for ano in (2012, 2019, 2023):
        i = set(sem_excluidos(ler_dfp(ano, "DRE_ind", ["CD_CVM"]), EXC).CD_CVM)
        c = set(sem_excluidos(ler_dfp(ano, "DRE_con", ["CD_CVM"]), EXC).CD_CVM)
        print(
            ano,
            "individual",
            len(i),
            "| consolidada",
            len(c),
            "| só individual",
            len(i - c),
            "| só consolidada",
            len(c - i),
        )
    md: collections.Counter = collections.Counter()
    for ano in ANOS_COMPLETOS:
        for tipo in ("con", "ind"):
            d = sem_excluidos(ler_dfp(ano, f"DFC_MD_{tipo}", ["CD_CVM", "ORDEM_EXERC"]), EXC)
            md[tipo] += d[d.ORDEM_EXERC == "ÚLTIMO"].CD_CVM.nunique()
    print("empresa-anos com DFC_MD:", dict(md))


def codigos() -> None:
    import yaml  # só para ler o catálogo

    pl = planos_fase0()
    naofin = naofin_estrito(pl)
    cat = yaml.safe_load(open("catalogo_sinais.yaml", encoding="utf-8"))["contas_dfp_a_confirmar"]
    alvo = {k: v.split()[0] for k, v in cat.items()}
    alvo.update(
        {
            "passivo_total_cod2": "2",
            "ir_csll_a_pagar_sub": "2.01.03.01.01",
            "resultado_antes_tributos": "3.07",
            "dfc_caixa_gerado_op": "6.01.01",
            "dfc_invest": "6.02",
            "dfc_financ": "6.03",
        }
    )
    arq = {"1": "BPA", "2": "BPP", "3": "DRE", "6": "DFC_MI"}
    pres: collections.Counter = collections.Counter()
    base: collections.Counter = collections.Counter()
    fixa: collections.Counter = collections.Counter()
    desc: dict = collections.defaultdict(collections.Counter)
    for ano in ANOS_COMPLETOS:
        for tipo in ("con", "ind"):
            for f in ("BPA", "BPP", "DRE", "DFC_MI"):
                d = sem_excluidos(
                    ler_dfp(ano, f"{f}_{tipo}", ["CD_CVM", "ORDEM_EXERC", "CD_CONTA", "DS_CONTA", "ST_CONTA_FIXA"]), EXC
                )
                d = d[d.ORDEM_EXERC == "ÚLTIMO"].copy()
                d["cd"] = cd(d.CD_CVM)
                d = d[[(ano, tipo, c) in naofin for c in d.cd]]
                base[(f, tipo)] += d.cd.nunique()
                s = d[d.CD_CONTA.isin({c for c in alvo.values() if arq[c.split(".")[0]] == f})]
                for r in s.drop_duplicates(["cd", "CD_CONTA"]).itertuples():
                    pres[(r.CD_CONTA, tipo)] += 1
                    fixa[(r.CD_CONTA, r.ST_CONTA_FIXA)] += 1
                    desc[r.CD_CONTA][r.DS_CONTA.strip()] += 1
    print("base:", dict(base))
    for k, c in alvo.items():
        f = arq[c.split(".")[0]]
        tot = fixa[(c, "S")] + fixa[(c, "N")]
        print(
            k,
            c,
            f,
            f"{pres[(c, 'con')] / max(base[(f, 'con')], 1):.1%}",
            f"{pres[(c, 'ind')] / max(base[(f, 'ind')], 1):.1%}",
            f"{fixa[(c, 'S')] / tot:.1%}" if tot else "-",
            desc[c].most_common(2),
            sep=" | ",
        )


def financeiras() -> None:
    pl = planos_fase0()
    pl["grupo"] = pl.d301.map(tipo_plano)
    pl.loc[(pl.grupo == "nao_financeiro") & pl.setor.str.contains(FIN_SETOR), "grupo"] = "setor_fin_plano_nao_fin"
    chave = {(r.ano, r.tipo, r.cd): r.grupo for r in pl.itertuples()}
    num_t, den_t = "outras receitas operacionais", "resultado antes dos tributos sobre o lucro"
    est: dict = collections.defaultdict(collections.Counter)
    cods: dict = collections.defaultdict(collections.Counter)
    quase: collections.Counter = collections.Counter()
    nivel = lambda x: x if x.count(".") <= 2 else x.rsplit(".", 1)[0] + ".xx"  # noqa: E731
    for ano in ANOS_COMPLETOS:
        for tipo in ("con", "ind"):
            d = sem_excluidos(
                ler_dfp(ano, f"DRE_{tipo}", ["CD_CVM", "ORDEM_EXERC", "CD_CONTA", "DS_CONTA", "ST_CONTA_FIXA"]), EXC
            )
            d = d[d.ORDEM_EXERC == "ÚLTIMO"].copy()
            d["cd"] = cd(d.CD_CVM)
            d["n"] = d.DS_CONTA.map(norm)
            for c, g in d.groupby("cd"):
                grp = chave.get((ano, tipo, c), "sem_3.01")
                if grp == "nao_financeiro":
                    continue
                e = est[grp]
                e["empresa-anos"] += 1
                num = g[g.n.str.contains(num_t, regex=False)]
                den = g[g.n.str.contains(den_t, regex=False)]
                e["numerador achado"] += bool(len(num))
                e["numerador >1 linha"] += len(num) > 1
                e[f"denominador {min(len(den), 2)} linha(s)"] += 1
                codes = set(num.CD_CONTA)
                e["mãe e subconta"] += any(x.rsplit(".", 1)[0] in codes for x in codes)
                for r in num.itertuples():
                    cods[(grp, "NUM")][(nivel(r.CD_CONTA), r.ST_CONTA_FIXA, r.n[:60])] += 1
                for r in den.itertuples():
                    cods[(grp, "DEN")][(r.CD_CONTA, r.ST_CONTA_FIXA, r.n[:60])] += 1
                parecidas = g[
                    g.n.str.contains("outras receitas")
                    & g.n.str.contains("operac")
                    & ~g.n.str.contains(num_t, regex=False)
                ]
                for r in parecidas.itertuples():
                    quase[(grp, nivel(r.CD_CONTA), r.n[:60])] += 1
    for grp, e in est.items():
        print(grp, dict(e))
    for k, c in sorted(cods.items()):
        print(k, c.most_common(8))
    print("parecidas que não casam:", quase.most_common(12))


def bancos() -> None:
    pl = planos_fase0()
    banco = {(r.ano, r.tipo, r.cd) for r in pl.itertuples() if tipo_plano(r.d301) == "banco"}
    por_ano: collections.Counter = collections.Counter()
    falta: collections.Counter = collections.Counter()
    leiaute: collections.Counter = collections.Counter()
    nivel2: collections.Counter = collections.Counter()
    for ano in ANOS_COMPLETOS:
        for tipo in ("con", "ind"):
            d = sem_excluidos(ler_dfp(ano, f"DRE_{tipo}", ["CD_CVM", "ORDEM_EXERC", "CD_CONTA", "DS_CONTA"]), EXC)
            d = d[d.ORDEM_EXERC == "ÚLTIMO"].copy()
            d["cd"] = cd(d.CD_CVM)
            for c, g in d.groupby("cd"):
                if (ano, tipo, c) not in banco:
                    continue
                por_ano[ano] += 1
                if (
                    not g.DS_CONTA.map(norm)
                    .str.contains("resultado antes dos tributos sobre o lucro", regex=False)
                    .any()
                ):
                    falta[ano] += 1
                    for r in g[g.CD_CONTA.str.count(r"\.") == 1].drop_duplicates("CD_CONTA").itertuples():
                        nivel2[(r.CD_CONTA, r.DS_CONTA.strip())] += 1
                d307 = g[g.CD_CONTA == "3.07"].DS_CONTA.map(norm)
                if len(d307):
                    leiaute[(tipo, "antigo" if "tributacao/participacoes" in d307.iloc[0] else "IFRS")] += 1
    print("banco por ano (empresa-anos | sem denominador):", {a: (por_ano[a], falta[a]) for a in sorted(por_ano)})
    print("leiaute por arquivo:", dict(leiaute))
    print("contas de nível 2 nos casos sem denominador:", sorted(nivel2.most_common(14)))


def dfc() -> None:
    pl = planos_fase0()
    naofin = naofin_estrito(pl)
    cat = {
        "depreciacao": (["deprecia"], ("6.01.01",)),
        "juros_pagos": (["juros pagos"], ("6.01", "6.03")),
        "capex": (["aquisicao de imobilizado", "intangivel"], ("6.02",)),
        "dividendos_pagos": (["dividendos", "juros sobre o capital proprio"], ("6.03",)),
        "ir_csll_pagos": (["imposto de renda e contribuicao social pagos"], ("6.01",)),
        "emissao_titulos": (["captacao", "emissao de acoes", "debentures"], ("6.03",)),
    }
    var = {
        "juros_pagos": ["pagamento de juros", "juros sobre emprestimos pagos", "pagamentos de juros"],
        "capex": [
            "aquisicoes de imobilizado",
            "adicoes ao imobilizado",
            "aquisicao de ativo imobilizado",
            "compra de imobilizado",
        ],
        "ir_csll_pagos": [
            "imposto de renda e contribuicao social pago",
            "ir e cs pagos",
            "ir e csll pagos",
            "pagamento de imposto de renda",
            "imposto de renda pago",
        ],
        "dividendos_pagos": ["juros sobre capital proprio"],
    }
    base: collections.Counter = collections.Counter()
    hit: collections.Counter = collections.Counter()
    secs: dict = collections.defaultdict(collections.Counter)
    varhit: collections.Counter = collections.Counter()
    extra: collections.Counter = collections.Counter()
    for ano in ANOS_COMPLETOS:
        for tipo in ("con", "ind"):
            d = sem_excluidos(ler_dfp(ano, f"DFC_MI_{tipo}", ["CD_CVM", "ORDEM_EXERC", "CD_CONTA", "DS_CONTA"]), EXC)
            d = d[d.ORDEM_EXERC == "ÚLTIMO"].copy()
            d["cd"] = cd(d.CD_CVM)
            d = d[[(ano, tipo, c) in naofin for c in d.cd]]
            d["n"] = d.DS_CONTA.map(norm)
            for c, g in d.groupby("cd"):
                base[tipo] += 1
                for nome, (pads, sec) in cat.items():
                    m = g[pd.Series([any(p in s for p in pads) for s in g.n], index=g.index, dtype=bool)]
                    m_sec = m[
                        pd.Series(
                            [any(x.startswith(s + ".") for s in sec) for x in m.CD_CONTA], index=m.index, dtype=bool
                        )
                    ]
                    hit[(nome, tipo)] += bool(len(m_sec))
                    for x in m.CD_CONTA:
                        secs[nome][x[:4]] += 1
                    if m_sec.empty and nome in var and any(any(p in s for p in var[nome]) for s in g.n):
                        varhit[nome] += 1
                    if nome == "depreciacao" and len(m_sec):
                        extra[
                            (
                                "dep: só linha combinada"
                                if all("amortiza" in s for s in m_sec.n)
                                else "dep: tem linha só de depreciação"
                            )
                        ] += 1
                    if nome == "emissao_titulos" and m_sec.n.str.contains("debentures").any():
                        extra[
                            (
                                "deb: com pagamento/amortização"
                                if m_sec.n.str.contains("pagamento|amortiza|liquida").any()
                                else "deb: só captação/emissão"
                            )
                        ] += 1
    print("base:", dict(base))
    for nome in cat:
        print(
            nome,
            f"con {hit[(nome, 'con')] / base['con']:.1%}",
            f"ind {hit[(nome, 'ind')] / base['ind']:.1%}",
            "| linhas por seção:",
            dict(secs[nome]),
            "| variantes não pegas:",
            varhit.get(nome, "-"),
        )
    print(dict(extra))


def dva() -> None:
    c: collections.Counter = collections.Counter()
    for ano in (2012, 2019, 2023):
        d = sem_excluidos(
            ler_dfp(ano, "DVA_ind", ["CD_CVM", "ORDEM_EXERC", "CD_CONTA", "DS_CONTA", "ST_CONTA_FIXA"]), EXC
        )
        d = d[(d.ORDEM_EXERC == "ÚLTIMO") & (d.CD_CONTA.str.count(r"\.") <= 2)]
        for r in d.drop_duplicates(["CD_CVM", "CD_CONTA"]).itertuples():
            if "deprecia" in norm(r.DS_CONTA):
                c[(r.CD_CONTA, r.ST_CONTA_FIXA)] += 1
    print("DVA, contas com 'deprecia':", c.most_common(4))


SECOES = {
    "versoes": versoes,
    "dominios": dominios,
    "cadastro": cadastro_resumo,
    "planos": planos,
    "conind": conind,
    "codigos": codigos,
    "financeiras": financeiras,
    "bancos": bancos,
    "dfc": dfc,
    "dva": dva,
}

if __name__ == "__main__":
    for nome in sys.argv[1:] or list(SECOES):
        print(f"\n===== {nome}")
        SECOES[nome]()
