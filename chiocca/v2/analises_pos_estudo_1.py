"""Análise descritiva depois do resultado do estudo 1, não pré-registrada: quantos acertos o acaso daria?

Autorizada por Roberto em 07/11/2026 (resposta 4 às perguntas da Fase A); persistência, variante sem a premissa de
independência e nota posterior sobre balanços não preenchidos pedidas em 08/11/2026. Não altera nenhum arquivo do
estudo 1: lê `docs/resultados_numeros.json` (saída versionada do estudo) e `docs/analises_pos_estudo_1_numeros.json`
(gerado por `chiocca.v2.analises_pos_estudo_1_dados`, que precisa dos dados fora do git), e grava
`docs/analises-pos-estudo-1.md` (PT) e `docs/en/post-study-1-analyses.md` (EN).

Modelo, como pedido:
- para cada caso acertável, a chance de ser "acertado" ao acaso é p = 1 − Π (1 − taxa de alerta do grupo no ano),
  sobre os anos do período afetado que estão nos dados, com as taxas de alerta observadas no estudo 1 (empresas em
  alerta ÷ empresas avaliadas, por exercício e grupo);
- o número de acertos ao acaso segue a distribuição binomial de Poisson (soma de Bernoullis com p diferentes),
  calculada de forma exata por convolução, sem scipy;
- variante sem independência entre os anos: p = fração das empresas do mesmo grupo, avaliadas em todos os anos do
  período afetado, que tiveram pelo menos um alerta nesses anos.

Uso: python -m chiocca.v2.analises_pos_estudo_1
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from chiocca.base import RAIZ
from chiocca.formato import decimal, inteiro, pct
from chiocca.sinais.mscore import COEFICIENTES

NUMEROS_ESTUDO_1 = RAIZ / "docs" / "resultados_numeros.json"
NUMEROS_DADOS = RAIZ / "docs" / "analises_pos_estudo_1_numeros.json"
DOCS = {"pt": RAIZ / "docs" / "analises-pos-estudo-1.md", "en": RAIZ / "docs" / "en" / "post-study-1-analyses.md"}
GRUPO_TAXA = {"nao_financeira": "nf", "financeira": "fin"}


def binomial_de_poisson(probabilidades: list[float]) -> list[float]:
    """P(K = k), k = 0..n, para K = soma de Bernoullis independentes com as probabilidades dadas."""
    pmf = [1.0]
    for p in probabilidades:
        if not 0.0 <= p <= 1.0:
            raise ValueError(f"probabilidade fora de [0, 1]: {p}")
        nova = [0.0] * (len(pmf) + 1)
        for k, q in enumerate(pmf):
            nova[k] += q * (1 - p)
            nova[k + 1] += q * p
        pmf = nova
    return pmf


def cauda_superior(pmf: list[float], k: int) -> float:
    """P(K ≥ k)."""
    return float(sum(pmf[k:]))


def grupo_do_caso(c: dict[str, Any]) -> str:
    return str(c["grupos"][0]) if c["grupos"] else "nao_financeira"


def _distribuicao(ps: list[float], observados: int) -> dict[str, Any]:
    pmf = binomial_de_poisson(ps)
    return {"pmf": pmf, "esperado": sum(ps), "variancia": sum(p * (1 - p) for p in ps),
            "p_cauda": cauda_superior(pmf, observados)}  # fmt: skip


def le_dados(caminho: Path = NUMEROS_DADOS) -> dict[str, Any] | None:
    return json.loads(caminho.read_text(encoding="utf-8")) if caminho.exists() else None


def calcula(n: dict[str, Any], dados: dict[str, Any] | None = None) -> dict[str, Any]:
    casos = []
    for c in n["casos"]:
        if not c["acertavel"]:
            continue
        grupo = grupo_do_caso(c)
        taxas_grupo = n["taxa"][GRUPO_TAXA[grupo]]
        anos = list(c["anos_periodo"])
        taxas = {str(a): taxas_grupo[str(a)]["em_alerta"] / taxas_grupo[str(a)]["avaliadas"] for a in anos}
        nao = 1.0
        for t in taxas.values():
            nao *= 1 - t
        casos.append(
            {
                "caso_id": c["caso_id"],
                "empresa": c["empresa"],
                "grupo": grupo,
                "anos": anos,
                "anos_iguais_aos_avaliados": anos == list(c["anos_avaliados"]),
                "taxas": taxas,
                "p_acaso": 1 - nao,
                "acertado": bool(c["acertado"]),
            }
        )
    observados = sum(c["acertado"] for c in casos)
    r = {"casos": casos, "observados": observados,
         "todos_anos_iguais": all(c["anos_iguais_aos_avaliados"] for c in casos)}  # fmt: skip
    r |= _distribuicao([c["p_acaso"] for c in casos], observados)
    if dados is None:
        return r
    por_id = {v["caso_id"]: v for v in dados["variante"]}
    if set(por_id) != {c["caso_id"] for c in casos}:
        raise ValueError("a variante não tem os mesmos casos acertáveis do estudo 1")
    var = []
    for c in casos:
        v = por_id[c["caso_id"]]
        var.append(c | {"empresas": v["empresas"], "com_alerta": v["com_alerta"], "p_acaso": v["com_alerta"] / v["empresas"],
                        "empresa_do_caso_incluida": v["empresa_do_caso_incluida"]})  # fmt: skip
    r["variante"] = {"casos": var} | _distribuicao([c["p_acaso"] for c in var], observados)
    r["persistencia"] = dados["persistencia"]
    r["nao_preenchidas"] = dados["nao_preenchidas"]
    return r


T: dict[str, dict[str, Any]] = {
    "pt": {
        "titulo": "# Análises depois do estudo 1",
        "rotulo": "**Análise descritiva depois do resultado, não pré-registrada.** Autorizada por Roberto Chiocca em 07/11/2026; as seções 2 a 4 foram pedidas em 08/11/2026. Não altera o estudo 1 (branch `estudo-1-final`): lê `docs/resultados_numeros.json` e `docs/analises_pos_estudo_1_numeros.json` e é gerada por `python -m chiocca.v2.analises_pos_estudo_1`. Não edite à mão: um teste compara este arquivo com a saída do script.",
        "h1": "## 1. Quantos acertos o acaso daria?",
        "modelo": "Para cada um dos {n} casos acertáveis, a chance de ser acertado ao acaso é 1 − produto de (1 − taxa de alerta do grupo no ano), sobre os anos do período afetado que estão nos dados, com as taxas de alerta observadas no estudo 1 (empresas em alerta ÷ empresas avaliadas). O número de acertos ao acaso segue a distribuição binomial de Poisson, calculada de forma exata, sem aproximação.",
        "anos_iguais": "Em todos os {n} casos, os anos do período afetado nos dados são os mesmos exercícios avaliados no estudo 1.",
        "anos_diferentes": "Em alguns casos, os anos do período afetado nos dados não coincidem com os exercícios avaliados no estudo 1; a conta usa os anos do período afetado.",
        "resultado": "**Resultado.** Acertos esperados ao acaso: {esperado} (desvio-padrão de {dp}). Acertos observados no estudo 1: {obs} de {n}. Probabilidade de {obs} ou mais acertos ao acaso: {p}.",
        "col_casos": "| Caso | Exercícios do período afetado | Taxa de alerta do grupo em cada ano | Chance ao acaso | Acertado no estudo 1 |",
        "col_pmf": "| Acertos ao acaso | Probabilidade | Probabilidade de pelo menos esse número |",
        "h_premissas": "**Premissas e o que elas fazem com o resultado.**",
        "premissa_independencia": "Independência entre os anos de um mesmo caso. Se os alertas se repetem na mesma empresa, essa premissa exagera o acaso: a chance de pelo menos um alerta em vários anos é menor que a calculada com anos independentes. Por isso, {esperado} é um teto para os acertos esperados ao acaso. A seção 2 mede a repetição, e a seção 3 refaz a conta sem essa premissa.",
        "premissa_independencia_sem_dados": "Independência entre os anos de um mesmo caso. Se os alertas se repetem na mesma empresa, essa premissa exagera o acaso: a chance de pelo menos um alerta em vários anos é menor que a calculada com anos independentes. Por isso, {esperado} é um teto para os acertos esperados ao acaso.",
        "premissas": [
            "Independência entre os casos.",
            "Cada caso tem a taxa de alerta média do seu grupo no ano. As empresas do gabarito podem ser diferentes da média (por exemplo, menores ou mais endividadas), e a taxa delas, ao acaso, pode ser maior ou menor que a média; a direção do efeito não é conhecida.",
            "As taxas são as do próprio estudo 1, que incluem as empresas do gabarito.",
            "Esta conta não substitui as métricas pré-registradas (acerto e alarmes por acerto), e não foi decidida antes de ver o resultado.",
        ],
        "h2": "## 2. Os alertas se repetem na mesma empresa?",
        "persistencia": "Persistência: entre as empresa-anos em alerta cuja empresa também foi avaliada no ano anterior, no mesmo grupo, a fração que também estava em alerta no ano anterior. A comparação é com a taxa geral de alerta (empresa-anos em alerta ÷ empresa-anos avaliadas, 2010 a 2023). Cada empresa conta uma vez por exercício, como nas taxas do estudo 1.",
        "col_persistencia": "| Grupo | Em alerta, com o ano anterior avaliado | Também em alerta no ano anterior | Persistência | Taxa geral de alerta |",
        "grupos": {"nf": "Não financeiras", "fin": "Financeiras", "total": "Total"},
        "resultado_persistencia": "**Resultado.** Nas não financeiras, {p} das empresa-anos em alerta também estavam em alerta no ano anterior, contra taxa de alerta de {t} das empresa-anos não financeiras avaliadas. Os alertas se repetem na mesma empresa, e a premissa de independência entre os anos da seção 1 exagera o acaso.",
        "h3": "## 3. Variante sem a premissa de independência entre os anos",
        "modelo_variante": "Para cada caso, a chance ao acaso é a fração das empresas do mesmo grupo, com dados em todos os anos do período afetado, que tiveram pelo menos um alerta nesses anos. \"Com dados\" quer dizer avaliada no estudo 1 (pelo menos um sinal de alerta calculável) em cada um desses anos. A repetição dos alertas na mesma empresa entra na conta como aconteceu. O número de acertos ao acaso segue de novo a distribuição binomial de Poisson exata.",
        "resultado_variante": "**Resultado.** Acertos esperados ao acaso: {esperado} (desvio-padrão de {dp}), contra {esperado1} na seção 1. Acertos observados no estudo 1: {obs} de {n}. Probabilidade de {obs} ou mais acertos ao acaso: {p}, contra {p1} na seção 1.",
        "col_variante": "| Caso | Exercícios do período afetado | Empresas avaliadas em todos esses anos | Com pelo menos um alerta | Chance ao acaso | Acertado no estudo 1 |",
        "premissas_variante": [
            "Independência entre os casos, como na seção 1.",
            "Só entram as empresas avaliadas em todos os anos do período afetado. Empresas que entraram ou saíram no meio do período ficam fora, e a taxa de alerta delas pode ser diferente.",
            "As frações incluem as empresas do gabarito: em {k} dos {n} casos, a própria empresa do caso está entre as contadas.",
            "Esta conta também não substitui as métricas pré-registradas, e não foi decidida antes de ver o resultado.",
        ],
        "h4": "## 4. Nota posterior: balanços não preenchidos no estudo 1",
        "rotulo_nota": "**Nota posterior, de 08/11/2026.** Verificação pedida na resposta à Fase B (item 1c). Não muda o estudo 1: só relata.",
        "nota_colunas": "A conferência \"não preenchido\" da v2 (`chiocca.v2.conferencias`) achou {c} colunas de balanço com ativo total zero na base do estudo 1: {u} na coluna do exercício (ÚLTIMO) e {pn} no comparativo (PENÚLTIMO), em {ea} empresa-anos. Dessas empresa-anos, {nf} estão na amostra de não financeiras, {fin} na de financeiras e {fora} fora da amostra. Em {tz} das colunas, o balanço inteiro está zerado; nas outras {tp}, só o total.",
        "nota_criterio": "Critério: um cálculo do estudo 1 usou zero como valor quando o sinal tem valor no estudo 1 e pelo menos uma conta de balanço que ele usa, numa dessas colunas, vale zero.",
        "nota_sim": "**Resultado: sim.** Em {z} empresa-anos, pelo menos um cálculo do estudo 1 usou como valor um zero de balanço de uma dessas colunas.",
        "nota_nao": "**Resultado: não.** Nenhum cálculo do estudo 1 usou como valor um zero de balanço dessas colunas.",
        "col_nota": "| Sinal | Empresa-anos calculadas com zero | Alertas desse sinal nessas empresa-anos |",
        "sem_alerta_componente": "componente do M-score: não dispara alerta sozinho",
        "sem_alerta_contexto": "só contexto: não dispara alerta",
        "nota_juro": "Juro implícito: em {jm} empresa-anos, a dívida (curto mais longo prazo) é zero numa das colunas. A dívida média de t e t−1 fica na metade da dívida do outro ano, e o juro implícito fica no dobro do que daria com a dívida desse outro ano.",
        "nota_so_por_isso": "Empresa-anos em alerta no estudo 1 só por sinais calculados com zero: {sa}. Empresa-anos avaliadas só por sinais calculados com zero: {sv}.",
        "nota_dpo_nenhum": "Salto do DPO: {d} valores calculados com zero entraram no limite do decil superior do ano. Sem eles, nenhum alerta de DPO de outra empresa-ano mudaria.",
        "nota_dpo_algum": "Salto do DPO: {d} valores calculados com zero entraram no limite do decil superior do ano. Sem eles, {f} alertas de DPO de outras empresa-anos mudariam, {gd} deles no período afetado de um caso do gabarito.",
        "nota_gabarito_nenhum": "Gabarito: nenhuma dessas empresa-anos está no período afetado de um caso. Os {obs} acertos do estudo 1 não mudam.",
        "nota_gabarito_algum": "Gabarito: {g} dessas empresa-anos estão no período afetado de um caso; a lista fora do git mostra quais.",
        "h_sem": "**Sem as {z} empresa-anos afetadas** (mesmo rótulo: análise descritiva depois do resultado, não pré-registrada; o estudo 1 não muda). Taxa de alerta e alarmes por acerto recalculados pelas funções do estudo 1 (`chiocca.metricas`), sem essas empresa-anos:",
        "col_sem": "| Não financeiras | Estudo 1 | Sem as {z} empresa-anos afetadas |",
        "linha_taxa": "Taxa de alerta das empresa-anos avaliadas",
        "linha_teste": "Alarmes por acerto, período de teste (2017–2023)",
        "linha_inteiro": "Alarmes por acerto, período inteiro (2010–2023)",
        "linha_acertos": "Casos acertados",
        "de": "de",
        "recalculo_igual": "Recalcular os alertas pelas regras do estudo 1, com os limites do decil sem essas empresa-anos, dá os mesmos números.",
        "recalculo_diferente": "Recalcular os alertas pelas regras do estudo 1, com os limites do decil sem essas empresa-anos, muda os números; a tabela usa os alertas como no estudo.",
        "readme_nota": "Depois do resultado, as conferências acharam {z} empresa-anos em que um balanço não preenchido entrou no cálculo como zero; {sa} alertas dependem disso. Nenhum caso do gabarito foi afetado. Detalhes na [nota posterior]({link}), seção 4.",
        "nota_produto": "No produto, a regra é outra: indicador que depende de balanço não preenchido fica \"não calculável\", nunca calculado com zero (`chiocca.v2.linhagem.aplicar_nao_preenchido`). A lista das empresa-anos fica em `resultados/nao_preenchidas_estudo_1.csv`, fora do git.",
        "sim": "sim",
        "nao": "não",
        "resumo": "**Depois do resultado (análise descritiva, não pré-registrada).** Com anos independentes, o acaso daria {e1} acertos em média, e {obs} ou mais com chance de {p1}. Como os alertas se repetem na mesma empresa ({pers} das empresa-anos em alerta das não financeiras também estavam em alerta no ano anterior, contra taxa de alerta de {taxa} das empresa-anos não financeiras avaliadas), esse número é um teto. Com a chance de cada caso medida nas empresas do mesmo grupo, sem supor anos independentes, o acaso daria {e2} acertos, e {obs} ou mais com chance de {p2}. Detalhes em [`docs/analises-pos-estudo-1.md`]({link}).",
        "link": "analises-pos-estudo-1.md",
    },
    "en": {
        "titulo": "# Analyses after study 1",
        "rotulo": "**Descriptive analysis after the result, not pre-registered.** Authorized by Roberto Chiocca on 2026-11-07; sections 2 to 4 were requested on 2026-11-08. It does not change study 1 (branch `estudo-1-final`): it reads `docs/resultados_numeros.json` and `docs/analises_pos_estudo_1_numeros.json` and is generated by `python -m chiocca.v2.analises_pos_estudo_1`. Do not edit by hand: a test compares this file with the script output.",
        "h1": "## 1. How many detections would chance produce?",
        "modelo": "For each of the {n} detectable cases, the chance of being detected by chance is 1 − product of (1 − the group's alert rate in the year), over the years of the affected period that are in the data, using the alert rates observed in study 1 (companies in alert ÷ evaluated companies). The number of detections by chance follows the Poisson binomial distribution, computed exactly, with no approximation.",
        "anos_iguais": "In all {n} cases, the years of the affected period in the data are the same fiscal years evaluated in study 1.",
        "anos_diferentes": "In some cases, the years of the affected period in the data do not match the fiscal years evaluated in study 1; the calculation uses the years of the affected period.",
        "resultado": "**Result.** Expected detections by chance: {esperado} (standard deviation of {dp}). Detections observed in study 1: {obs} of {n}. Probability of {obs} or more detections by chance: {p}.",
        "col_casos": "| Case | Fiscal years of the affected period | Group alert rate in each year | Chance probability | Detected in study 1 |",
        "col_pmf": "| Detections by chance | Probability | Probability of at least that number |",
        "h_premissas": "**Assumptions and what they do to the result.**",
        "premissa_independencia": "Independence across the years of the same case. If alerts repeat at the same company, this assumption overstates chance: the chance of at least one alert over several years is lower than computed with independent years. So {esperado} is a ceiling for the expected detections by chance. Section 2 measures the repetition, and section 3 redoes the calculation without this assumption.",
        "premissa_independencia_sem_dados": "Independence across the years of the same case. If alerts repeat at the same company, this assumption overstates chance: the chance of at least one alert over several years is lower than computed with independent years. So {esperado} is a ceiling for the expected detections by chance.",
        "premissas": [
            "Independence across cases.",
            "Each case has its group's average alert rate in the year. Ground-truth companies may differ from the average (for example, smaller or more leveraged), and their chance rate may be higher or lower than the average; the direction of the effect is not known.",
            "The rates are study 1's own, which include the ground-truth companies.",
            "This calculation does not replace the pre-registered metrics (detection and false alarms per detected case), and it was not decided before seeing the result.",
        ],
        "h2": "## 2. Do alerts repeat at the same company?",
        "persistencia": "Persistence: among company-years in alert whose company was also evaluated in the previous year, in the same group, the fraction that was also in alert in the previous year. The comparison is with the overall alert rate (company-years in alert ÷ evaluated company-years, 2010 to 2023). Each company counts once per fiscal year, as in study 1's rates.",
        "col_persistencia": "| Group | In alert, with the previous year evaluated | Also in alert in the previous year | Persistence | Overall alert rate |",
        "grupos": {"nf": "Non-financial companies", "fin": "Financial companies", "total": "Total"},
        "resultado_persistencia": "**Result.** Among non-financial companies, {p} of company-years in alert were also in alert in the previous year, against an alert rate of {t} of evaluated non-financial company-years. Alerts repeat at the same company, and section 1's assumption of independence across years overstates chance.",
        "h3": "## 3. Variant without the assumption of independence across years",
        "modelo_variante": "For each case, the chance probability is the fraction of companies in the same group, with data in every year of the affected period, that had at least one alert in those years. \"With data\" means evaluated in study 1 (at least one computable alert signal) in each of those years. The repetition of alerts at the same company enters the calculation as it happened. The number of detections by chance again follows the exact Poisson binomial distribution.",
        "resultado_variante": "**Result.** Expected detections by chance: {esperado} (standard deviation of {dp}), against {esperado1} in section 1. Detections observed in study 1: {obs} of {n}. Probability of {obs} or more detections by chance: {p}, against {p1} in section 1.",
        "col_variante": "| Case | Fiscal years of the affected period | Companies evaluated in all those years | With at least one alert | Chance probability | Detected in study 1 |",
        "premissas_variante": [
            "Independence across cases, as in section 1.",
            "Only companies evaluated in every year of the affected period enter. Companies that entered or left in the middle of the period are left out, and their alert rate may be different.",
            "The fractions include the ground-truth companies: in {k} of the {n} cases, the case company itself is among those counted.",
            "This calculation does not replace the pre-registered metrics either, and it was not decided before seeing the result.",
        ],
        "h4": "## 4. Later note: unfilled balance sheets in study 1",
        "rotulo_nota": "**Later note, of 2026-11-08.** Check requested in the reply to Phase B (item 1c). It does not change study 1: it only reports.",
        "nota_colunas": "The v2 \"not filled in\" check (`chiocca.v2.conferencias`) found {c} balance sheet columns with zero total assets in the study 1 base: {u} in the fiscal-year column (ÚLTIMO) and {pn} in the prior-year column (PENÚLTIMO), in {ea} company-years. Of these company-years, {nf} are in the non-financial sample, {fin} in the financial sample and {fora} outside the sample. In {tz} of the columns, the whole balance sheet is zero; in the other {tp}, only the total.",
        "nota_criterio": "Criterion: a study 1 calculation used zero as a value when the signal has a value in study 1 and at least one balance sheet account it uses, in one of these columns, is zero.",
        "nota_sim": "**Result: yes.** In {z} company-years, at least one study 1 calculation used a balance sheet zero from one of these columns as a value.",
        "nota_nao": "**Result: no.** No study 1 calculation used a balance sheet zero from these columns as a value.",
        "col_nota": "| Signal | Company-years computed with zero | Alerts from this signal in these company-years |",
        "sem_alerta_componente": "M-score component: does not trigger alerts by itself",
        "sem_alerta_contexto": "context only: does not trigger alerts",
        "nota_juro": "Implied interest rate: in {jm} company-years, debt (current plus non-current) is zero in one of the columns. The average debt of t and t−1 is half the other year's debt, and the implied interest rate is double what it would be with that other year's debt.",
        "nota_so_por_isso": "Company-years in alert in study 1 only because of signals computed with zero: {sa}. Company-years evaluated only because of signals computed with zero: {sv}.",
        "nota_dpo_nenhum": "DPO jump: {d} values computed with zero entered the top-decile threshold of the year. Without them, no DPO alert of another company-year would change.",
        "nota_dpo_algum": "DPO jump: {d} values computed with zero entered the top-decile threshold of the year. Without them, {f} DPO alerts of other company-years would change, {gd} of them in the affected period of a ground-truth case.",
        "nota_gabarito_nenhum": "Ground truth: none of these company-years is in a case's affected period. Study 1's {obs} detections do not change.",
        "nota_gabarito_algum": "Ground truth: {g} of these company-years are in a case's affected period; the list outside git shows which.",
        "h_sem": "**Without the {z} affected company-years** (same label: descriptive analysis after the result, not pre-registered; study 1 does not change). Alert rate and false alarms per detected case recomputed with study 1's functions (`chiocca.metricas`), without these company-years:",
        "col_sem": "| Non-financial companies | Study 1 | Without the {z} affected company-years |",
        "linha_taxa": "Alert rate of evaluated company-years",
        "linha_teste": "False alarms per detected case, test period (2017–2023)",
        "linha_inteiro": "False alarms per detected case, whole period (2010–2023)",
        "linha_acertos": "Detected cases",
        "de": "of",
        "recalculo_igual": "Recomputing the alerts with study 1's rules, with the top-decile thresholds without these company-years, gives the same numbers.",
        "recalculo_diferente": "Recomputing the alerts with study 1's rules, with the top-decile thresholds without these company-years, changes the numbers; the table uses the alerts as in the study.",
        "readme_nota": "After the result, the data checks found {z} company-years in which an unfilled balance sheet entered the calculation as zero; {sa} alerts depend on it. No ground-truth case was affected. Details in the [later note]({link}), section 4.",
        "nota_produto": "In the product, the rule is different: an indicator that depends on an unfilled balance sheet is \"not computable\", never computed with zero (`chiocca.v2.linhagem.aplicar_nao_preenchido`). The list of company-years is in `resultados/nao_preenchidas_estudo_1.csv`, outside git.",
        "sim": "yes",
        "nao": "no",
        "resumo": "**After the result (descriptive analysis, not pre-registered).** With independent years, chance would produce {e1} detections on average, and {obs} or more with a probability of {p1}. Since alerts repeat at the same company ({pers} of non-financial company-years in alert were also in alert in the previous year, against an alert rate of {taxa} of evaluated non-financial company-years), this number is a ceiling. With each case's chance measured on companies in the same group, without assuming independent years, chance would produce {e2} detections, and {obs} or more with a probability of {p2}. Details in [`docs/en/post-study-1-analyses.md`]({link}).",
        "link": "en/post-study-1-analyses.md",
    },
}  # fmt: skip


def _pmf(t: dict[str, Any], pmf: list[float], lang: str) -> list[str]:
    linhas = [t["col_pmf"], "| --- | --- | --- |"]
    for k, q in enumerate(pmf):
        linhas.append(f"| {inteiro(k, lang)} | {pct(q, lang, 1)} | {pct(cauda_superior(pmf, k), lang, 1)} |")
    return linhas


def _taxa(x: dict[str, int]) -> float:
    return x["em_alerta"] / x["avaliadas"]


def _persistencia(x: dict[str, int]) -> float:
    return x["anterior_tambem_em_alerta"] / x["em_alerta_com_anterior_avaliado"]


def render(r: dict[str, Any], lang: str) -> str:
    t = T[lang]
    i = lambda x: inteiro(x, lang)  # noqa: E731
    n = len(r["casos"])
    linhas = [t["titulo"], "", t["rotulo"], "", t["h1"], "", t["modelo"].format(n=i(n)), ""]
    linhas.append((t["anos_iguais"] if r["todos_anos_iguais"] else t["anos_diferentes"]).format(n=i(n)))
    linhas += ["", t["resultado"].format(
        esperado=decimal(r["esperado"], lang, 2), dp=decimal(r["variancia"] ** 0.5, lang, 2),
        obs=i(r["observados"]), n=i(n), p=pct(r["p_cauda"], lang, 1)), ""]  # fmt: skip
    linhas += [t["col_casos"], "| --- | --- | --- | --- | --- |"]
    for c in r["casos"]:
        taxas = "; ".join(f"{a}: {pct(v, lang)}" for a, v in c["taxas"].items())
        anos = ", ".join(str(a) for a in c["anos"])
        linhas.append(f"| {c['empresa']} (`{c['caso_id']}`) | {anos} | {taxas} | {pct(c['p_acaso'], lang)} | "
                      f"{t['sim'] if c['acertado'] else t['nao']} |")  # fmt: skip
    linhas += [""] + _pmf(t, r["pmf"], lang)
    independencia = t["premissa_independencia" if "variante" in r else "premissa_independencia_sem_dados"]
    linhas += ["", t["h_premissas"], "", "- " + independencia.format(esperado=decimal(r["esperado"], lang, 2))]
    linhas += ["- " + x for x in t["premissas"]]
    if "variante" not in r:
        return "\n".join(linhas) + "\n"
    pe = r["persistencia"]
    linhas += ["", t["h2"], "", t["persistencia"], "", t["col_persistencia"], "| --- | --- | --- | --- | --- |"]
    for k in ("nf", "fin", "total"):
        x = pe[k]
        linhas.append(f"| {t['grupos'][k]} | {i(x['em_alerta_com_anterior_avaliado'])} | "
                      f"{i(x['anterior_tambem_em_alerta'])} | {pct(_persistencia(x), lang)} | {pct(_taxa(x), lang)} |")  # fmt: skip
    linhas += [
        "",
        t["resultado_persistencia"].format(p=pct(_persistencia(pe["nf"]), lang), t=pct(_taxa(pe["nf"]), lang)),
    ]
    v = r["variante"]
    linhas += ["", t["h3"], "", t["modelo_variante"], "", t["resultado_variante"].format(
        esperado=decimal(v["esperado"], lang, 2), dp=decimal(v["variancia"] ** 0.5, lang, 2),
        esperado1=decimal(r["esperado"], lang, 2), obs=i(r["observados"]), n=i(n), p=pct(v["p_cauda"], lang, 1),
        p1=pct(r["p_cauda"], lang, 1)), ""]  # fmt: skip
    linhas += [t["col_variante"], "| --- | --- | --- | --- | --- | --- |"]
    for c in v["casos"]:
        anos = ", ".join(str(a) for a in c["anos"])
        linhas.append(f"| {c['empresa']} (`{c['caso_id']}`) | {anos} | {i(c['empresas'])} | {i(c['com_alerta'])} | "
                      f"{pct(c['p_acaso'], lang)} | {t['sim'] if c['acertado'] else t['nao']} |")  # fmt: skip
    linhas += [""] + _pmf(t, v["pmf"], lang) + ["", t["h_premissas"], ""]
    k = sum(c["empresa_do_caso_incluida"] for c in v["casos"])
    linhas += ["- " + x.format(k=i(k), n=i(n)) for x in t["premissas_variante"]]
    linhas += _nota(r, t, lang)
    return "\n".join(linhas) + "\n"


def _nota(r: dict[str, Any], t: dict[str, Any], lang: str) -> list[str]:
    from chiocca.v2.linhagem import ROTULOS

    i = lambda x: inteiro(x, lang)  # noqa: E731
    np_ = r["nao_preenchidas"]
    co, am = np_["colunas"], np_["na_amostra"]
    linhas = ["", t["h4"], "", t["rotulo_nota"], "", t["nota_colunas"].format(
        c=i(co["ultimo"] + co["penultimo"]), u=i(co["ultimo"]), pn=i(co["penultimo"]), ea=i(np_["empresa_anos"]),
        nf=i(am["nao_financeira"]), fin=i(am["financeira"]), fora=i(am["fora"]),
        tz=i(np_["colunas_balanco_todo_zero"]), tp=i(np_["colunas_so_total_zero"])), "", t["nota_criterio"], ""]  # fmt: skip
    if not np_["com_zero_tratado_como_valor"]:
        return linhas + [t["nota_nao"], "", t["nota_produto"]]
    linhas += [t["nota_sim"].format(z=i(np_["com_zero_tratado_como_valor"])), "", t["col_nota"], "| --- | --- | --- |"]
    for sinal, x in np_["por_sinal"].items():
        rotulo = ROTULOS[sinal][0 if lang == "pt" else 1]
        if sinal in ("mscore", "dpo", "juro"):
            alertas = i(x["alertas"])
        else:
            alertas = t["sem_alerta_componente" if sinal in COEFICIENTES else "sem_alerta_contexto"]
        linhas.append(f"| {rotulo} | {i(x['empresa_anos'])} | {alertas} |")
    linhas.append("")
    if "juro" in np_["por_sinal"]:
        linhas.append("- " + t["nota_juro"].format(jm=i(np_["juro_com_divida_zero_num_dos_anos"])))
    linhas.append("- " + t["nota_so_por_isso"].format(sa=i(np_["em_alerta_so_por_sinal_com_zero"]),
                                                       sv=i(np_["avaliadas_so_por_sinal_com_zero"])))  # fmt: skip
    if np_["dpo_com_zero_no_limite"]:
        f = np_["alertas_dpo_que_mudariam_sem_eles"]
        linhas.append("- " + t["nota_dpo_algum" if f else "nota_dpo_nenhum"].format(
            d=i(np_["dpo_com_zero_no_limite"]), f=i(f), gd=i(np_["alertas_dpo_que_mudariam_no_periodo_de_um_caso"])))  # fmt: skip
    if np_["no_periodo_de_um_caso"]:
        linhas.append("- " + t["nota_gabarito_algum"].format(g=i(np_["no_periodo_de_um_caso"])))
    elif not np_["alertas_dpo_que_mudariam_no_periodo_de_um_caso"]:
        linhas.append("- " + t["nota_gabarito_nenhum"].format(obs=i(r["observados"])))
    if "sem_as_afetadas" in np_:
        linhas += [""] + _sem_as_afetadas(np_["sem_as_afetadas"], t, lang)
    return linhas + ["", t["nota_produto"]]


def _sem_as_afetadas(x: dict[str, Any], t: dict[str, Any], lang: str) -> list[str]:
    i = lambda v: inteiro(v, lang)  # noqa: E731
    z = i(x["empresa_anos_retiradas"])

    def taxa(m: dict[str, Any]) -> str:
        tx = m["taxa_nf"]
        return f"{pct(tx['em_alerta'] / tx['avaliadas'], lang)} ({i(tx['em_alerta'])} {t['de']} {i(tx['avaliadas'])})"

    def alarmes(m: dict[str, Any], k: str) -> str:
        v = m["alarmes_nf"][k]["alarmes_por_acerto"]
        return "—" if v is None else decimal(v, lang, 1)

    e, s = x["estudo"], x["sem"]
    return [
        t["h_sem"].format(z=z), "", t["col_sem"].format(z=z), "| --- | --- | --- |",
        f"| {t['linha_taxa']} | {taxa(e)} | {taxa(s)} |",
        f"| {t['linha_teste']} | {alarmes(e, 'teste')} | {alarmes(s, 'teste')} |",
        f"| {t['linha_inteiro']} | {alarmes(e, 'inteiro')} | {alarmes(s, 'inteiro')} |",
        f"| {t['linha_acertos']} | {i(e['acertados'])} {t['de']} {i(e['acertaveis'])} | {i(s['acertados'])} {t['de']} {i(s['acertaveis'])} |",
        "", t["recalculo_igual" if x["alertas_recalculados_iguais"] else "recalculo_diferente"],
    ]  # fmt: skip


def frase_readme_nao_preenchidas(r: dict[str, Any], lang: str, link: str) -> str | None:
    """Frase do README sobre os balanços não preenchidos no estudo 1 (pedido de 08/11/2026)."""
    np_ = r.get("nao_preenchidas")
    if not np_ or not np_.get("com_zero_tratado_como_valor"):
        return None
    if np_["no_periodo_de_um_caso"] or np_["alertas_dpo_que_mudariam_no_periodo_de_um_caso"]:
        raise ValueError("há caso do gabarito afetado: a frase fixa do README deixaria de valer")
    return str(T[lang]["readme_nota"].format(
        z=inteiro(np_["com_zero_tratado_como_valor"], lang), sa=inteiro(np_["em_alerta_so_por_sinal_com_zero"], lang),
        link=link))  # fmt: skip


def resumo(r: dict[str, Any], lang: str, link: str | None = None) -> str | None:
    """O resultado em um parágrafo, com o rótulo, para o resumo do estudo 1 e o README (pedido de 08/11/2026)."""
    if "variante" not in r:
        return None
    t, pe, v = T[lang], r["persistencia"]["nf"], r["variante"]
    return str(t["resumo"].format(
        e1=decimal(r["esperado"], lang, 2), p1=pct(r["p_cauda"], lang, 1), obs=inteiro(r["observados"], lang),
        pers=pct(_persistencia(pe), lang), taxa=pct(_taxa(pe), lang), e2=decimal(v["esperado"], lang, 2),
        p2=pct(v["p_cauda"], lang, 1), link=link if link is not None else t["link"]))  # fmt: skip


def resumo_dos_arquivos(lang: str, link: str | None = None) -> str | None:
    dados = le_dados()
    if dados is None:
        return None
    return resumo(calcula(json.loads(NUMEROS_ESTUDO_1.read_text(encoding="utf-8")), dados), lang, link)


def main(caminho: Path = NUMEROS_ESTUDO_1) -> dict[str, Any]:
    r = calcula(json.loads(caminho.read_text(encoding="utf-8")), le_dados())
    for lang, destino in DOCS.items():
        destino.write_text(render(r, lang), encoding="utf-8")
    return r


if __name__ == "__main__":
    r = main()
    print(f"esperado {r['esperado']:.3f}; observados {r['observados']}; P(K >= observados) = {r['p_cauda']:.4f}")
    if "variante" in r:
        print(
            f"variante: esperado {r['variante']['esperado']:.3f}; P(K >= observados) = {r['variante']['p_cauda']:.4f}"
        )
