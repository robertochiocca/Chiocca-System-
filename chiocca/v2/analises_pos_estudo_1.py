"""Análise descritiva depois do resultado do estudo 1, não pré-registrada: quantos acertos o acaso daria?

Autorizada por Roberto em 07/11/2026 (resposta 4 às perguntas da Fase A). Não altera nenhum arquivo do estudo 1:
lê `docs/resultados_numeros.json`, que é saída versionada do estudo, e grava `docs/analises-pos-estudo-1.md` (PT)
e `docs/en/post-study-1-analyses.md` (EN).

Modelo, como pedido:
- para cada caso acertável, a chance de ser "acertado" ao acaso é p = 1 − Π (1 − taxa de alerta do grupo no ano),
  sobre os anos do período afetado que estão nos dados, com as taxas de alerta observadas no estudo 1 (empresas em
  alerta ÷ empresas avaliadas, por exercício e grupo);
- o número de acertos ao acaso segue a distribuição binomial de Poisson (soma de Bernoullis com p diferentes),
  calculada de forma exata por convolução, sem scipy.

Uso: python -m chiocca.v2.analises_pos_estudo_1
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from chiocca.base import RAIZ
from chiocca.formato import decimal, inteiro, pct

NUMEROS_ESTUDO_1 = RAIZ / "docs" / "resultados_numeros.json"
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


def calcula(n: dict[str, Any]) -> dict[str, Any]:
    casos = []
    for c in n["casos"]:
        if not c["acertavel"]:
            continue
        grupo = c["grupos"][0] if c["grupos"] else "nao_financeira"
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
    pmf = binomial_de_poisson([c["p_acaso"] for c in casos])
    observados = sum(c["acertado"] for c in casos)
    return {
        "casos": casos,
        "pmf": pmf,
        "esperado": sum(c["p_acaso"] for c in casos),
        "variancia": sum(c["p_acaso"] * (1 - c["p_acaso"]) for c in casos),
        "observados": observados,
        "p_cauda": cauda_superior(pmf, observados),
        "todos_anos_iguais": all(c["anos_iguais_aos_avaliados"] for c in casos),
    }


T: dict[str, dict[str, Any]] = {
    "pt": {
        "titulo": "# Análises depois do estudo 1",
        "rotulo": "**Análise descritiva depois do resultado, não pré-registrada.** Autorizada por Roberto Chiocca em 07/11/2026. Não altera o estudo 1 (branch `estudo-1-final`): lê `docs/resultados_numeros.json` e é gerada por `python -m chiocca.v2.analises_pos_estudo_1`. Não edite à mão: um teste compara este arquivo com a saída do script.",
        "h1": "## 1. Quantos acertos o acaso daria?",
        "modelo": "Para cada um dos {n} casos acertáveis, a chance de ser acertado ao acaso é 1 − produto de (1 − taxa de alerta do grupo no ano), sobre os anos do período afetado que estão nos dados, com as taxas de alerta observadas no estudo 1 (empresas em alerta ÷ empresas avaliadas). O número de acertos ao acaso segue a distribuição binomial de Poisson, calculada de forma exata, sem aproximação.",
        "anos_iguais": "Em todos os {n} casos, os anos do período afetado nos dados são os mesmos exercícios avaliados no estudo 1.",
        "anos_diferentes": "Em alguns casos, os anos do período afetado nos dados não coincidem com os exercícios avaliados no estudo 1; a conta usa os anos do período afetado.",
        "resultado": "**Resultado.** Acertos esperados ao acaso: {esperado} (desvio-padrão de {dp}). Acertos observados no estudo 1: {obs} de {n}. Probabilidade de {obs} ou mais acertos ao acaso: {p}.",
        "col_casos": "| Caso | Exercícios do período afetado | Taxa de alerta do grupo em cada ano | Chance ao acaso | Acertado no estudo 1 |",
        "col_pmf": "| Acertos ao acaso | Probabilidade | Probabilidade de pelo menos esse número |",
        "h_premissas": "**Premissas e o que elas fazem com o resultado.**",
        "premissas": [
            "Independência entre os anos de um mesmo caso: a chance de alerta num ano não depende do ano anterior. Se os alertas se repetem na mesma empresa de um ano para outro (isso não foi medido aqui), a chance real de pelo menos um alerta em vários anos é menor que a calculada, e a probabilidade acima superestima o acaso.",
            "Independência entre os casos.",
            "Cada caso tem a taxa de alerta média do seu grupo no ano. As empresas do gabarito podem ser diferentes da média (por exemplo, menores ou mais endividadas), e a taxa delas, ao acaso, pode ser maior ou menor que a média; a direção do efeito não é conhecida.",
            "As taxas são as do próprio estudo 1, que incluem as empresas do gabarito.",
            "Esta conta não substitui as métricas pré-registradas (acerto e alarmes por acerto), e não foi decidida antes de ver o resultado.",
        ],
        "sim": "sim",
        "nao": "não",
    },
    "en": {
        "titulo": "# Analyses after study 1",
        "rotulo": "**Descriptive analysis after the result, not pre-registered.** Authorized by Roberto Chiocca on 2026-11-07. It does not change study 1 (branch `estudo-1-final`): it reads `docs/resultados_numeros.json` and is generated by `python -m chiocca.v2.analises_pos_estudo_1`. Do not edit by hand: a test compares this file with the script output.",
        "h1": "## 1. How many detections would chance produce?",
        "modelo": "For each of the {n} detectable cases, the chance of being detected by chance is 1 − product of (1 − the group's alert rate in the year), over the years of the affected period that are in the data, using the alert rates observed in study 1 (companies in alert ÷ evaluated companies). The number of detections by chance follows the Poisson binomial distribution, computed exactly, with no approximation.",
        "anos_iguais": "In all {n} cases, the years of the affected period in the data are the same fiscal years evaluated in study 1.",
        "anos_diferentes": "In some cases, the years of the affected period in the data do not match the fiscal years evaluated in study 1; the calculation uses the years of the affected period.",
        "resultado": "**Result.** Expected detections by chance: {esperado} (standard deviation of {dp}). Detections observed in study 1: {obs} of {n}. Probability of {obs} or more detections by chance: {p}.",
        "col_casos": "| Case | Fiscal years of the affected period | Group alert rate in each year | Chance probability | Detected in study 1 |",
        "col_pmf": "| Detections by chance | Probability | Probability of at least that number |",
        "h_premissas": "**Assumptions and what they do to the result.**",
        "premissas": [
            "Independence across the years of the same case: the chance of an alert in one year does not depend on the previous year. If alerts repeat at the same company from one year to the next (this was not measured here), the real chance of at least one alert over several years is lower than computed, and the probability above overstates chance.",
            "Independence across cases.",
            "Each case has its group's average alert rate in the year. Ground-truth companies may differ from the average (for example, smaller or more leveraged), and their chance rate may be higher or lower than the average; the direction of the effect is not known.",
            "The rates are study 1's own, which include the ground-truth companies.",
            "This calculation does not replace the pre-registered metrics (detection and false alarms per detected case), and it was not decided before seeing the result.",
        ],
        "sim": "yes",
        "nao": "no",
    },
}  # fmt: skip


def render(r: dict[str, Any], lang: str) -> str:
    t = T[lang]
    n = len(r["casos"])
    linhas = [t["titulo"], "", t["rotulo"], "", t["h1"], "", t["modelo"].format(n=inteiro(n, lang)), ""]
    linhas.append((t["anos_iguais"] if r["todos_anos_iguais"] else t["anos_diferentes"]).format(n=inteiro(n, lang)))
    linhas += ["", t["resultado"].format(
        esperado=decimal(r["esperado"], lang, 2), dp=decimal(r["variancia"] ** 0.5, lang, 2),
        obs=inteiro(r["observados"], lang), n=inteiro(n, lang), p=pct(r["p_cauda"], lang, 1)), ""]  # fmt: skip
    linhas += [t["col_casos"], "| --- | --- | --- | --- | --- |"]
    for c in r["casos"]:
        taxas = "; ".join(f"{a}: {pct(v, lang)}" for a, v in c["taxas"].items())
        anos = ", ".join(str(a) for a in c["anos"])
        linhas.append(f"| {c['empresa']} (`{c['caso_id']}`) | {anos} | {taxas} | {pct(c['p_acaso'], lang)} | "
                      f"{t['sim'] if c['acertado'] else t['nao']} |")  # fmt: skip
    linhas += ["", t["col_pmf"], "| --- | --- | --- |"]
    for k, q in enumerate(r["pmf"]):
        linhas.append(f"| {inteiro(k, lang)} | {pct(q, lang, 1)} | {pct(cauda_superior(r['pmf'], k), lang, 1)} |")
    linhas += ["", t["h_premissas"], ""] + ["- " + x for x in t["premissas"]]
    return "\n".join(linhas) + "\n"


def main(caminho: Path = NUMEROS_ESTUDO_1) -> dict[str, Any]:
    r = calcula(json.loads(caminho.read_text(encoding="utf-8")))
    for lang, destino in DOCS.items():
        destino.write_text(render(r, lang), encoding="utf-8")
    return r


if __name__ == "__main__":
    r = main()
    print(f"esperado {r['esperado']:.3f}; observados {r['observados']}; P(K >= observados) = {r['p_cauda']:.4f}")
