"""Resumo de uma página (PROMPT.md, Fase 5): docs/resumo.md (PT) e docs/summary.md (EN).

Montado de docs/resultados_numeros.json, como os resultados. Nenhum número é escrito à mão aqui, e nenhum adjetivo
aparece sem número ao lado.
"""

from __future__ import annotations

from typing import Any

from chiocca.formato import data, decimal, inteiro, pct
from chiocca.sinais.mscore import COEFICIENTES

T: dict[str, dict[str, Any]] = {
    "pt": {
        "titulo": "# Resumo · Chiocca System",
        "gerado": "Gerado por `python -m chiocca.relatorio_resultados` a partir de `docs/resultados_numeros.json`. Detalhes, tabelas e fontes em [`docs/resultados.md`](resultados.md). Alerta estatístico baseado em demonstrações públicas. Não é acusação, não é recomendação de investimento.",
        "h_pergunta": "**Pergunta.**",
        "pergunta": "Com dados públicos disponíveis na época, os sinais do catálogo teriam alertado para os casos do gabarito antes de eles virem a público? Quantos alarmes falsos isso custaria?",
        "h_desenho": "**Desenho.**",
        "desenho": [
            "Pré-registro assinado em {assinatura}, com {emendas} emendas; só a última foi escrita depois dos resultados, e ela muda apenas a métrica de alarmes.",
            "Todas as companhias abertas com DFP na CVM, de 2010 a 2023, inclusive as canceladas: {nf} empresa-anos de não financeiras com receita e {fin} de financeiras, de {emp} empresas.",
            "\"Como era na época\": cada empresa-ano usa a versão da DFP pública na data de corte (último dia do quarto mês depois do exercício); versões reentregues depois vêm do ENET da CVM.",
            "Não financeiras: M-score (alerta se M > {corte}), salto do DPO (decil superior do ano) e juro implícito (acima do CDI médio + {spread} p.p.). Financeiras: peso de ganhos não recorrentes (decil superior do ano).",
            "Gabarito: {casos} casos, dos quais {acertaveis} acertáveis no estudo principal. Período de teste, 2017 a 2023, aberto uma vez, em {abertura}.",
        ],
        "h_resultado": "**Resultado.**",
        "resultado": [
            "Acerto: {a} de {n} casos acertáveis ({a} de {casos} no gabarito inteiro).",
            "Alarmes por acerto nas não financeiras (emenda 11): {xt} no período de teste, com {at} acertos por alerta dentro dele, e {xi} no período inteiro. Taxa de alerta: {taxa} das empresa-anos avaliadas.",
            "Financeiras: nenhum caso acertável. O IRB não teve alerta na DFP de 2018 ({p}, contra limite de {lim}).",
        ],
        "h_boba": "**Regra boba lado a lado** (decil mais endividado de cada ano e grupo; sem vencedor declarado, emenda 11):",
        "col_boba": "| Não financeiras | Sinais | Regra boba |",
        "linhas_boba": {"acertados": "Casos acertados (de {n})", "acertados_teste": "Acertos por alerta em 2017–2023",
                        "teste": "Alarmes por acerto, período de teste", "inteiro": "Alarmes por acerto, período inteiro",
                        "taxa": "Taxa de alerta, 2010–2023"},
        "h_errado": "**O que deu errado e por quê.**",
        "errado": [
            "O juro implícito sozinho responde por {pj} das empresa-anos em alerta ({jt} de {et}). A despesa financeira (3.06.02) inclui, por definição, variação cambial, juros de arrendamento e outros itens que não são juros dos empréstimos (2.01.04 e 2.02.01); essa decomposição não foi medida. Sem ele, a taxa de alerta seria {taxa_sem}, e não {taxa}.",
            "O M-score ficou sem valor em {mnc} de {mtot} empresa-anos; em {cd}, faltou o DEPI. Em {k} dos {n} casos acertáveis o M não existiu porque a DFC não tem linha de depreciação ({kmd} deles com DFC pelo método direto). Com valores neutros, o acerto seria {an} de {n}.",
            "Só {at} dos {a} acertos têm alerta no período de teste: em {antes17} dos {n} casos acertáveis, o período afetado termina antes de 2017.",
            "A emenda 10 punha numerador e acertos em janelas diferentes ({x10} alarmes por acerto); a emenda 11 corrigiu isso depois dos resultados, e as duas versões estão no relatório.",
        ],
        "h_previsoes": "**Previsões do pré-registro (seção 4.2).**",
        "previsoes": [
            "Acertaram: o M-score da Americanas disparou antes de 2023, com M = {m} em 2021; o DPO, com {dpo} dias, e o juro implícito, com {juro} p.p. acima do CDI, não dispararam; o GMI ficou em {gmi}, abaixo de 1; o IRB não teve alerta antes da data pública.",
            "Erraram: o M da Americanas não foi puxado por TATA e AQI, com contribuições de {ctata} e {caqi}, e sim por SGI e DSRI, com {csgi} e {cdsri}, as duas maiores contribuições.",
        ],
        "h_americanas": "**Americanas: parte do alerta de 2021 vem da fusão.**",
        "americanas": "Em 2021 a B2W (código CVM 20990) recebeu as operações da Lojas Americanas por cisão parcial (assembleia de 10/06/2021). O comparativo de 2020 é só da B2W: a receita foi de R$ {r20} milhões para R$ {r21} milhões, e o SGI de {sgi} vem dessa troca de perímetro. Com a Lojas Americanas consolidada de 2020 como base, o SGI cai para {sgil} (contribuição de {csgil}, contra {csgi}), e o M continua acima do corte, em {ml}, puxado por DSRI e AQI, com índices de {dsril} e {aqil}. Na leitura reapresentada da DFP de 2022, o M também fica acima do corte, em {mr}. Essa explicação foi feita depois do resultado e não é teste.",
        "h_limites": "**Limitações.**",
        "limites": [
            "Poucos casos: {n} acertáveis em {casos} no gabarito, nenhum deles financeiro; o teto do estudo principal é {n} de {casos}.",
            "O IRB não pode ser acertado com DFP anual (emenda 3); pegá-lo exigiria dados trimestrais (ITR).",
            "Sinais calibrados nos EUA: o corte de {corte} vem de Beneish (1999) e não foi recalibrado para o Brasil.",
            "Despesa financeira (3.06.02) que não separa os juros dos empréstimos: o juro implícito dispara em {pjuro} das empresa-anos em que é calculável.",
            "DFC pelo método direto sem linha de depreciação em {md} empresa-anos, com M não calculável (limitação aceita na emenda 11).",
            "O caso da Americanas veio a público por dentro, pelo fato relevante da própria companhia de {data_ame}, e não por um sinal das demonstrações.",
            "A emenda 11 foi escrita depois de ver os resultados; a versão anterior da métrica continua no relatório.",
        ],
    },
    "en": {
        "titulo": "# Summary · Chiocca System",
        "gerado": "Generated by `python -m chiocca.relatorio_resultados` from `docs/resultados_numeros.json`. Details, tables and sources in [`docs/en/results.md`](en/results.md). Statistical alert based on public financial statements. Not an accusation, not investment advice.",
        "h_pergunta": "**Question.**",
        "pergunta": "Using public data available at the time, would the catalog signals have flagged the ground-truth cases before they became public? How many false alarms would that cost?",
        "h_desenho": "**Design.**",
        "desenho": [
            "Pre-registration signed on {assinatura}, with {emendas} amendments; only the last one was written after the results, and it changes only the false-alarm metric.",
            "All listed companies filing DFPs with the CVM, 2010 to 2023, including delisted ones: {nf} company-years of non-financial companies with revenue and {fin} of financial companies, from {emp} companies.",
            "Point-in-time: each company-year uses the DFP version that was public on the cut-off date (last day of the fourth month after fiscal year-end); versions refiled later come from the CVM's ENET system.",
            "Non-financial companies: M-score (alert if M > {corte}), DPO jump (top decile of the year) and implied interest rate (above the average CDI rate + {spread} p.p.). Financial companies: weight of non-recurring gains (top decile of the year).",
            "Ground truth: {casos} cases, of which {acertaveis} are detectable in the main study. Test period, 2017 to 2023, opened once, on {abertura}.",
        ],
        "h_resultado": "**Result.**",
        "resultado": [
            "Detection: {a} of {n} detectable cases ({a} of {casos} in the whole ground truth).",
            "False alarms per detected case among non-financial companies (amendment 11): {xt} in the test period, with {at} detections by an alert within it, and {xi} over the whole period. Alert rate: {taxa} of evaluated company-years.",
            "Financial companies: no detectable case. IRB had no alert in its 2018 DFP ({p}, against a threshold of {lim}).",
        ],
        "h_boba": "**Naive baseline rule side by side** (most leveraged decile of each year and group; no winner declared, amendment 11):",
        "col_boba": "| Non-financial | Signals | Naive baseline |",
        "linhas_boba": {"acertados": "Detected cases (of {n})", "acertados_teste": "Detections by an alert in 2017–2023",
                        "teste": "False alarms per detected case, test period",
                        "inteiro": "False alarms per detected case, whole period", "taxa": "Alert rate, 2010–2023"},
        "h_errado": "**What went wrong and why.**",
        "errado": [
            "The implied interest rate alone accounts for {pj} of company-years in alert ({jt} of {et}). Finance costs (3.06.02) include, by definition, exchange differences, lease interest and other items that are not interest on borrowings (2.01.04 and 2.02.01); this breakdown was not measured. Without it, the alert rate would be {taxa_sem} instead of {taxa}.",
            "The M-score had no value in {mnc} of {mtot} company-years; in {cd}, DEPI was missing. In {k} of the {n} detectable cases M did not exist because the cash flow statement has no depreciation line ({kmd} of them with a direct-method statement). With neutral values, detection would be {an} of {n}.",
            "Only {at} of the {a} detections have an alert in the test period: in {antes17} of the {n} detectable cases, the affected period ends before 2017.",
            "Amendment 10 put the numerator and the detections in different windows ({x10} false alarms per detected case); amendment 11 fixed this after the results, and both versions are in the report.",
        ],
        "h_previsoes": "**Pre-registered predictions (section 4.2).**",
        "previsoes": [
            "Right: Americanas' M-score fired before 2023, with M = {m} in 2021; the DPO, at {dpo} days, and the implied interest rate, at {juro} p.p. above CDI, did not fire; GMI was {gmi}, below 1; IRB had no alert before the public date.",
            "Wrong: Americanas' M was not driven by TATA and AQI, with contributions of {ctata} and {caqi}, but by SGI and DSRI, with {csgi} and {cdsri}, the two largest contributions.",
        ],
        "h_americanas": "**Americanas: the 2021 alert comes partly from the combination.**",
        "americanas": "In 2021, B2W (CVM code 20990) received the Lojas Americanas operations through a partial spin-off (shareholders' meeting of 2021-06-10). The 2020 comparative is B2W alone: net revenue went from R${r20} million to R${r21} million, and the SGI of {sgi} comes from this change of perimeter. With Lojas Americanas' 2020 consolidated statements as the base, SGI falls to {sgil} (a contribution of {csgil}, against {csgi}), and M stays above the cut-off, at {ml}, driven by DSRI and AQI, with indices of {dsril} and {aqil}. In the restated reading from the 2022 DFP, M is also above the cut-off, at {mr}. This explanation was made after the result and is not a test.",
        "h_limites": "**Limitations.**",
        "limites": [
            "Few cases: {n} detectable out of {casos} in the ground truth, none of them financial; the main-study ceiling is {n} of {casos}.",
            "IRB cannot be detected with annual DFPs (amendment 3); catching it would require quarterly data (ITR).",
            "Signals calibrated in the US: the {corte} cut-off comes from Beneish (1999) and was not recalibrated for Brazil.",
            "Finance costs (3.06.02) that do not separate interest on borrowings: the implied interest rate fires in {pjuro} of the company-years where it is computable.",
            "Direct-method cash flow statements have no depreciation line in {md} company-years, leaving M not computable (a limitation accepted in amendment 11).",
            "The Americanas case became public from the inside, through the company's own material fact notice of {data_ame}, not through a signal in the financial statements.",
            "Amendment 11 was written after seeing the results; the earlier version of the metric remains in the report.",
        ],
    },
}  # fmt: skip


def render(n: dict[str, Any], lang: str) -> str:
    t = T[lang]

    def i(x: int) -> str:
        return inteiro(x, lang)

    def d(x: float, casas: int = 1) -> str:
        return decimal(x, lang, casas)

    ac, am, al = n["acerto"], n["amostra"], n["alarmes"]
    nf_, nfb = al["nf"], al["nf_boba"]
    tx = {k: [sum(v["em_alerta"] for v in n["taxa"][k].values()), sum(v["avaliadas"] for v in n["taxa"][k].values())]
          for k in ("nf", "nf_boba")}  # fmt: skip
    taxa = pct(tx["nf"][0] / tx["nf"][1], lang)
    jb = n["descritiva"]["juro"]
    so_juro = jb["antes"]["so_juro"] + jb["depois"]["so_juro"]
    em = jb["antes"]["em_alerta"] + jb["depois"]["em_alerta"]
    sem = jb["antes"]["sem_juro"] + jb["depois"]["sem_juro"]
    aval = jb["antes"]["avaliada"] + jb["depois"]["avaliada"]
    juro_calc = sum(v["calculaveis"] for v in n["por_sinal"]["nf"]["alerta_juro"].values())
    juro_al = sum(v["alertas"] for v in n["por_sinal"]["nf"]["alerta_juro"].values())
    nc = n["nao_calculaveis"]["mscore"]
    dp = n["descritiva"]["depi"]
    princ = [c for c in dp["casos"] if c["principal"]]
    ame = next(c for c in n["casos"] if c["caso_id"] == "americanas")
    r21 = ame["detalhe"][-1]
    irb18 = n["previsoes"]["irb"][0]
    lim = n["previsoes"]["limite_fin"].get(str(irb18["exercicio"]))
    corte = d(n["regras"]["corte_m"], 2)
    comuns = dict(
        n=i(ac["acertaveis"]), casos=i(ac["casos_no_gabarito"]), a=i(ac["acertados"]), at=i(ac["acertados_teste"]),
        corte=corte, spread=i(int(n["regras"]["spread_pp"])), taxa=taxa,
    )  # fmt: skip

    def x_(a: dict[str, Any]) -> str:
        return d(a["alarmes_por_acerto"]) if a["alarmes_por_acerto"] is not None else "—"

    antes17 = sum(1 for c in n["casos"] if c["acertavel"] and max(c["anos_periodo"]) < 2017)
    contrib = {c: d(COEFICIENTES[c] * v, 2) for c, v in r21["componentes"].items() if v is not None}
    linhas = [t["titulo"], "", t["gerado"], "", t["h_pergunta"], t["pergunta"], "", t["h_desenho"], ""]
    linhas += ["- " + x.format(emendas=i(n["pre_registro"]["emendas"]),
                               assinatura=data(n["pre_registro"]["assinatura"], lang), nf=i(am["nao_financeira"]), fin=i(am["financeira"]),
                               emp=i(n["marcas"]["empresas"]), acertaveis=i(ac["acertaveis"]),
                               abertura=data(n["abertura_teste"]["data"], lang), **comuns)
               for x in t["desenho"]]  # fmt: skip
    linhas += ["", t["h_resultado"], ""]
    linhas += ["- " + x.format(xt=x_(nf_["teste"]), xi=x_(nf_["inteiro"]),
                               p=d(irb18["peso_nao_recorrente"], 3), lim=d(lim, 3) if lim is not None else "—", **comuns)
               for x in t["resultado"]]  # fmt: skip
    lb = t["linhas_boba"]
    linhas += ["", t["h_boba"], "", t["col_boba"], "| --- | --- | --- |"]
    linhas += [
        f"| {lb['acertados'].format(n=i(ac['acertaveis']))} | {i(ac['acertados'])} | {i(ac['acertados_boba'])} |",
        f"| {lb['acertados_teste']} | {i(ac['acertados_teste'])} | {i(ac['acertados_boba_teste'])} |",
        f"| {lb['teste']} | {x_(nf_['teste'])} | {x_(nfb['teste'])} |",
        f"| {lb['inteiro']} | {x_(nf_['inteiro'])} | {x_(nfb['inteiro'])} |",
        f"| {lb['taxa']} | {taxa} | {pct(tx['nf_boba'][0] / tx['nf_boba'][1], lang)} |",
    ]
    rob = n["robustez"]["avaliacao"]
    linhas += ["", t["h_errado"], ""]
    linhas += ["- " + x.format(pj=pct(so_juro / em, lang), jt=i(so_juro), et=i(em), taxa_sem=pct(sem / aval, lang),
                               mnc=i(nc["nao_calculaveis"]), mtot=i(nc["empresa_anos"]),
                               cd=i(dp["amostra"]["com_depi"]), k=i(len(princ)),
                               kmd=i(sum(c["dfc_md"] for c in princ)), an=i(rob["acertados"]),
                               x10=x_(nf_["emenda_10"]), antes17=i(antes17), **comuns)
               for x in t["errado"]]  # fmt: skip
    linhas += ["", t["h_previsoes"], ""]
    linhas += ["- " + x.format(m=d(r21["mscore"], 2), dpo=d(r21["dpo"]), juro=d(r21["juro"]),
                               gmi=d(r21["componentes"]["GMI"], 2), ctata=contrib["TATA"], caqi=contrib["AQI"],
                               csgi=contrib["SGI"], cdsri=contrib["DSRI"])
               for x in t["previsoes"]]  # fmt: skip
    if "americanas" in n:
        a_ = n["americanas"]
        o_, b_, r_ = a_["original"], a_["base_lasa"], a_["reapresentada"]
        linhas += ["", t["h_americanas"], ""]
        linhas.append(t["americanas"].format(
            r20=d(o_["contas_t1"]["receita_liquida"] / 1e6, 0), r21=d(o_["contas_t"]["receita_liquida"] / 1e6, 0),
            sgi=d(o_["componentes"]["SGI"]["valor"], 2), sgil=d(b_["componentes"]["SGI"]["valor"], 2),
            csgi=d(COEFICIENTES["SGI"] * o_["componentes"]["SGI"]["valor"], 2),
            csgil=d(COEFICIENTES["SGI"] * b_["componentes"]["SGI"]["valor"], 2),
            ml=d(b_["m"]["valor"], 2), dsril=d(b_["componentes"]["DSRI"]["valor"], 2),
            aqil=d(b_["componentes"]["AQI"]["valor"], 2), mr=d(r_["m"]["valor"], 2)))  # fmt: skip
    linhas += ["", t["h_limites"], ""]
    linhas += ["- " + x.format(pjuro=pct(juro_al / juro_calc, lang), md=i(n["marcas"]["dfc_md"]),
                               data_ame=data(ame["data_publica"], lang), **comuns)
               for x in t["limites"]]  # fmt: skip
    return "\n".join(linhas) + "\n"
