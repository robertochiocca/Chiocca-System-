"""Ficha de alerta (PROMPT.md, Fase 4): `ficha(cd_cvm, exercicio, lang="pt")`.

Texto curto, em PT ou EN, com os sinais que dispararam e os que não dispararam, o valor de cada componente, as
contas da DFP de origem, o link do documento no ENET da CVM e a frase fixa. Lê resultados/ e data/base/, que ficam
fora do git: a ficha de uma empresa fora do gabarito não é publicada neste repositório (regra 6 do PROMPT).

Uso: python -m chiocca.ficha <código CVM> <exercício> [pt|en]
"""

from __future__ import annotations

import sys
from typing import Any

import pandas as pd

from chiocca.base import RAIZ
from chiocca.formato import data, decimal, pct
from chiocca.sinais.mscore import COEFICIENTES
from chiocca.sinais_amostra import AMOSTRA_FIN, AMOSTRA_NF, CORTE_M, SPREAD_PP

SINAIS = RAIZ / "resultados" / "sinais_empresa_ano.csv"
LIMIARES = RAIZ / "resultados" / "limiares.csv"
META = RAIZ / "data" / "base" / "empresa_ano.csv"
ENET = "https://www.rad.cvm.gov.br/ENET/frmGerenciaPaginaFRE.aspx?NumeroSequencialDocumento={}&CodigoTipoInstituicao=2"
FRASE = {
    "pt": "Alerta estatístico baseado em demonstrações públicas. Não é acusação, não é recomendação de investimento.",
    "en": "Statistical alert based on public financial statements. Not an accusation, not investment advice.",
}
# Contas de origem de cada componente (códigos confirmados na Fase 0; depreciação e juros pagos por texto na DFC).
ORIGEM = {
    "DSRI": ("contas a receber (1.01.03), receita (3.01)", "trade receivables (1.01.03), net revenue (3.01)"),
    "GMI": ("resultado bruto (3.03), receita (3.01)", "gross profit (3.03), net revenue (3.01)"),
    "AQI": ("ativo circulante (1.01), imobilizado (1.02.03), ativo total (1)",
            "current assets (1.01), property, plant and equipment (1.02.03), total assets (1)"),
    "SGI": ("receita (3.01)", "net revenue (3.01)"),
    "DEPI": ("depreciação na DFC (6.01.01, por texto), imobilizado (1.02.03)",
             "depreciation in the cash flow statement (6.01.01, by text), property, plant and equipment (1.02.03)"),
    "SGAI": ("despesas com vendas (3.04.01) e gerais e administrativas (3.04.02), receita (3.01)",
             "selling (3.04.01) and general and administrative expenses (3.04.02), net revenue (3.01)"),
    "TATA": ("resultado das operações continuadas (3.09), caixa operacional (6.01, sem juros pagos), ativo total (1)",
             "profit from continuing operations (3.09), operating cash flow (6.01, excluding interest paid), total assets (1)"),
    "LVGI": ("passivo circulante (2.01), empréstimos de longo prazo (2.02.01), ativo total (1)",
             "current liabilities (2.01), long-term borrowings (2.02.01), total assets (1)"),
    "dpo": ("fornecedores (2.01.02), custo das vendas (3.02)", "trade payables (2.01.02), cost of sales (3.02)"),
    "juro": ("despesas financeiras (3.06.02), empréstimos (2.01.04 e 2.02.01)",
             "finance costs (3.06.02), borrowings (2.01.04 and 2.02.01)"),
    "lucro_sem_caixa": ("lucro líquido (3.11), caixa operacional (6.01, sem juros pagos), ativo total (1)",
                        "net income (3.11), operating cash flow (6.01, excluding interest paid), total assets (1)"),
    "peso_nao_recorrente": ('linhas da DRE "outras receitas operacionais" e "resultado antes dos tributos", por texto',
                            'income statement lines "outras receitas operacionais" (other operating income) and '
                            '"resultado antes dos tributos" (income before taxes), by text'),
}  # fmt: skip
T: dict[str, dict[str, Any]] = {
    "pt": {
        "titulo": "Ficha de alerta · {nome} (código CVM {cd}) · exercício {ano}",
        "documento": "DFP {tipo}, versão {versao}, entregue em {dt_receb}; versão pública na data de corte ({corte}). Documento: {link}",
        "con": "consolidada",
        "ind": "individual",
        "grupo_nf": "Grupo: não financeiras (M-score, salto do DPO, juro implícito).",
        "grupo_fin": "Grupo: financeiras (peso de ganhos não recorrentes).",
        "fora": "Empresa-ano fora da amostra do estudo ({motivo}); sem sinais.",
        "em_alerta": "Em alerta neste exercício: {r}.",
        "dispararam": "Sinais que dispararam: {x}.",
        "nao_dispararam": "Sinais que não dispararam: {x}.",
        "nao_calculaveis": "Sinais não calculáveis: {x}.",
        "nenhum": "nenhum",
        "m": "M-score: {v} (alerta se > {corte}).",
        "m_nc": "M-score: não calculável ({motivo}).",
        "comp": "- {c}: {v} (contribuição {k}); contas: {o}.",
        "comp_nc": "- {c}: não calculável ({motivo}); contas: {o}.",
        "dpo": "Salto do DPO: {v} dias (alerta no decil superior do ano: ≥ {lim} dias); contas: {o}.",
        "juro": "Juro implícito: {j} contra CDI médio de {cdi}, diferença de {v} p.p. (alerta se > {s} p.p.); contas: {o}.",
        "lsc": "Lucro sem caixa (só na ficha, não dispara alerta): {v} do ativo médio; contas: {o}.",
        "pnr": "Peso não recorrente: {v} (alerta no decil superior do ano: ≥ {lim}); contas: {o}.",
        "nc": "não calculável ({motivo})",
        "sim": "sim",
        "nao": "não",
        "nomes": {"mscore": "M-score", "dpo": "salto do DPO", "juro": "juro implícito",
                  "peso_nao_recorrente": "peso não recorrente"},
        "motivos": {"fora_sem_receita": "sem receita", "fora_sem_versao_da_epoca": "sem versão da época"},
    },
    "en": {
        "titulo": "Alert sheet · {nome} (CVM code {cd}) · fiscal year {ano}",
        "documento": "{tipo} DFP, version {versao}, filed on {dt_receb}; the version public on the cut-off date ({corte}). Document: {link}",
        "con": "Consolidated",
        "ind": "Individual (parent company only)",
        "grupo_nf": "Group: non-financial companies (M-score, DPO jump, implied interest rate).",
        "grupo_fin": "Group: financial companies (weight of non-recurring gains).",
        "fora": "Company-year outside the study sample ({motivo}); no signals.",
        "em_alerta": "In alert for this fiscal year: {r}.",
        "dispararam": "Signals that fired: {x}.",
        "nao_dispararam": "Signals that did not fire: {x}.",
        "nao_calculaveis": "Signals not computable: {x}.",
        "nenhum": "none",
        "m": "M-score: {v} (alert if > {corte}).",
        "m_nc": "M-score: not computable ({motivo}).",
        "comp": "- {c}: {v} (contribution {k}); accounts: {o}.",
        "comp_nc": "- {c}: not computable ({motivo}); accounts: {o}.",
        "dpo": "DPO jump: {v} days (alert in the top decile of the year: ≥ {lim} days); accounts: {o}.",
        "juro": "Implied interest rate: {j} against an average CDI rate of {cdi}, a difference of {v} p.p. (alert if > {s} p.p.); accounts: {o}.",
        "lsc": "Accruals (alert sheet only, does not trigger alerts): {v} of average total assets; accounts: {o}.",
        "pnr": "Non-recurring weight: {v} (alert in the top decile of the year: ≥ {lim}); accounts: {o}.",
        "nc": "not computable ({motivo})",
        "sim": "yes",
        "nao": "no",
        "nomes": {"mscore": "M-score", "dpo": "DPO jump", "juro": "implied interest rate",
                  "peso_nao_recorrente": "non-recurring weight"},
        "motivos": {"fora_sem_receita": "no revenue", "fora_sem_versao_da_epoca": "no point-in-time version"},
    },
}  # fmt: skip


def _v(x: Any) -> float | None:
    return None if x is None or pd.isna(x) else float(x)


def _s(x: Any) -> str | None:
    return None if x is None or pd.isna(x) else str(x)


def dados_ficha(cd_cvm: str, exercicio: int, s: pd.DataFrame, meta: pd.DataFrame, lim: pd.DataFrame) -> dict[str, Any]:
    """Tudo o que a ficha mostra, num dicionário serializável (para testar e para o exemplo publicado)."""
    r = s[(s.cd_cvm.astype(str) == str(cd_cvm)) & (s.exercicio == exercicio)]
    if r.empty:
        raise KeyError(f"empresa-ano {cd_cvm}/{exercicio} não está em resultados/")
    x = r.iloc[0]
    m = meta[(meta.cd_cvm.astype(str) == str(cd_cvm)) & (meta.exercicio == exercicio)].iloc[0]

    def limite(grupo: str, sinal: str) -> float | None:
        sel = lim[(lim.exercicio == exercicio) & (lim.grupo == grupo) & (lim.sinal == sinal)]
        return None if sel.empty else _v(sel.limite_p90.iloc[0])

    d: dict[str, Any] = {
        "cd_cvm": str(cd_cvm),
        "exercicio": int(exercicio),
        "nome": str(m.denominacao),
        "tipo": _s(m.tipo),
        "versao": None if pd.isna(m.versao) else int(m.versao),
        "dt_receb": _s(m.dt_receb),
        "data_corte": str(m.data_corte),
        "num_doc": None if pd.isna(m.num_doc) else str(m.num_doc).split(".")[0],
        "amostra": str(x.amostra),
    }
    sim = {"True", "true", True}
    if x.amostra == AMOSTRA_NF:
        d["componentes"] = {c: {"valor": _v(x[c]), "motivo": _s(x[f"{c}_motivo"])} for c in COEFICIENTES}
        d |= {
            "mscore": _v(x.mscore), "mscore_motivo": _s(x.mscore_motivo), "alerta_mscore": x.alerta_mscore in sim,
            "dpo": _v(x.dpo), "dpo_motivo": _s(x.dpo_motivo), "alerta_dpo": x.alerta_dpo in sim,
            "limite_dpo": limite(AMOSTRA_NF, "dpo"),
            "juro_implicito": _v(x.juro_implicito), "cdi_medio": _v(x.cdi_medio), "juro": _v(x.juro),
            "juro_motivo": _s(x.juro_motivo), "alerta_juro": x.alerta_juro in sim,
            "lucro_sem_caixa": _v(x.lucro_sem_caixa), "lucro_sem_caixa_motivo": _s(x.lucro_sem_caixa_motivo),
        }  # fmt: skip
    elif x.amostra == AMOSTRA_FIN:
        d |= {
            "peso_nao_recorrente": _v(x.peso_nao_recorrente),
            "peso_nao_recorrente_motivo": _s(x.peso_nao_recorrente_motivo),
            "alerta_peso_nao_recorrente": x.alerta_peso_nao_recorrente in sim,
            "limite_peso_nao_recorrente": limite(AMOSTRA_FIN, "peso_nao_recorrente"),
        }
    d["em_alerta"] = x.em_alerta in sim
    return d


def texto(d: dict[str, Any], lang: str = "pt") -> str:
    from chiocca.textos_resultados import motivo as rotulo_motivo

    t = T[lang]
    k = 0 if lang == "pt" else 1

    def num(v: float, casas: int = 2) -> str:
        return decimal(v, lang, casas)

    linhas = [t["titulo"].format(nome=d["nome"], cd=d["cd_cvm"], ano=d["exercicio"]), ""]
    if d["dt_receb"]:
        link = ENET.format(d["num_doc"]) if d["num_doc"] else "—"
        linhas.append(t["documento"].format(tipo=t.get(d["tipo"] or "", d["tipo"] or "—"), versao=d["versao"],
                                            dt_receb=data(d["dt_receb"][:10], lang),
                                            corte=data(d["data_corte"][:10], lang), link=link))  # fmt: skip
    if d["amostra"] not in (AMOSTRA_NF, AMOSTRA_FIN):
        linhas += ["", t["fora"].format(motivo=t["motivos"].get(d["amostra"], d["amostra"])), "", FRASE[lang]]
        return "\n".join(linhas) + "\n"
    nomes = t["nomes"]
    if d["amostra"] == AMOSTRA_NF:
        sinais = {"mscore": (d["mscore"], d["alerta_mscore"], d["mscore_motivo"]),
                  "dpo": (d["dpo"], d["alerta_dpo"], d["dpo_motivo"]),
                  "juro": (d["juro"], d["alerta_juro"], d["juro_motivo"])}  # fmt: skip
        linhas += ["", t["grupo_nf"]]
    else:
        sinais = {"peso_nao_recorrente": (d["peso_nao_recorrente"], d["alerta_peso_nao_recorrente"],
                                          d["peso_nao_recorrente_motivo"])}  # fmt: skip
        linhas += ["", t["grupo_fin"]]
    disp = [nomes[n] for n, (v, a, _) in sinais.items() if v is not None and a]
    nao = [nomes[n] for n, (v, a, _) in sinais.items() if v is not None and not a]
    nc = [nomes[n] for n, (v, _, _) in sinais.items() if v is None]
    linhas += [
        t["em_alerta"].format(r=t["sim"] if d["em_alerta"] else t["nao"]),
        t["dispararam"].format(x=", ".join(disp) or t["nenhum"]),
        t["nao_dispararam"].format(x=", ".join(nao) or t["nenhum"]),
    ]
    if nc:
        linhas.append(t["nao_calculaveis"].format(x=", ".join(nc)))
    linhas.append("")
    if d["amostra"] == AMOSTRA_NF:
        corte = num(CORTE_M)
        if d["mscore"] is not None:
            linhas.append(t["m"].format(v=num(d["mscore"]), corte=corte))
        else:
            linhas.append(t["m_nc"].format(motivo=rotulo_motivo(d["mscore_motivo"] or "", lang)))
        for c, comp in d["componentes"].items():
            o = ORIGEM[c][k]
            if comp["valor"] is None:
                linhas.append(t["comp_nc"].format(c=c, motivo=rotulo_motivo(comp["motivo"] or "", lang), o=o))
            else:
                linhas.append(t["comp"].format(c=c, v=num(comp["valor"]), k=num(COEFICIENTES[c] * comp["valor"]), o=o))
        linhas.append("")
        if d["dpo"] is None:
            linhas.append(
                f"{nomes['dpo'].capitalize()}: {t['nc'].format(motivo=rotulo_motivo(d['dpo_motivo'] or '', lang))}."
            )
        else:
            lim = num(d["limite_dpo"], 1) if d["limite_dpo"] is not None else "—"
            linhas.append(t["dpo"].format(v=num(d["dpo"], 1), lim=lim, o=ORIGEM["dpo"][k]))
        if d["juro"] is None:
            linhas.append(
                f"{nomes['juro'].capitalize()}: {t['nc'].format(motivo=rotulo_motivo(d['juro_motivo'] or '', lang))}."
            )
        else:
            linhas.append(t["juro"].format(j=pct(d["juro_implicito"], lang), cdi=pct(d["cdi_medio"], lang),
                                           v=num(d["juro"], 1), s=num(SPREAD_PP, 0), o=ORIGEM["juro"][k]))  # fmt: skip
        if d["lucro_sem_caixa"] is not None:
            linhas.append(t["lsc"].format(v=pct(d["lucro_sem_caixa"], lang), o=ORIGEM["lucro_sem_caixa"][k]))
    else:
        if d["peso_nao_recorrente"] is None:
            linhas.append(f"{nomes['peso_nao_recorrente'].capitalize()}: "
                          f"{t['nc'].format(motivo=rotulo_motivo(d['peso_nao_recorrente_motivo'] or '', lang))}.")  # fmt: skip
        else:
            lim = num(d["limite_peso_nao_recorrente"], 3) if d["limite_peso_nao_recorrente"] is not None else "—"
            linhas.append(t["pnr"].format(v=num(d["peso_nao_recorrente"], 3), lim=lim,
                                          o=ORIGEM["peso_nao_recorrente"][k]))  # fmt: skip
    linhas += ["", FRASE[lang]]
    return "\n".join(linhas) + "\n"


def ficha(cd_cvm: str, exercicio: int, lang: str = "pt") -> str:
    s = pd.read_csv(SINAIS, dtype={"cd_cvm": str}, low_memory=False)
    meta = pd.read_csv(META, dtype={"cd_cvm": str, "num_doc": str})
    lim = pd.read_csv(LIMIARES)
    return texto(dados_ficha(cd_cvm, exercicio, s, meta, lim), lang)


if __name__ == "__main__":
    print(ficha(sys.argv[1], int(sys.argv[2]), sys.argv[3] if len(sys.argv) > 3 else "pt"))
