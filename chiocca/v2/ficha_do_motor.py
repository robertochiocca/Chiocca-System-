"""Ficha do motor (pedido de 09/11/2026), no formato de model card, em PT e EN.

Os números saem de `docs/resultados_numeros.json` (o mesmo JSON do resumo do estudo 1) e da análise descritiva
depois do resultado (`chiocca.v2.analises_pos_estudo_1`: teste contra o acaso e antecedência dos acertos). As
limitações são as do README (`chiocca.v2.textos_readme`). `numeros()` também alimenta a rota da API e a página
"Como o motor foi testado" da interface, para que os três mostrem os mesmos números.

Uso: python -m chiocca.v2.ficha_do_motor   (grava docs/ficha-do-motor.md e docs/en/engine-card.md)
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from chiocca.base import RAIZ
from chiocca.formato import data, decimal, inteiro, pct
from chiocca.v2 import analises_pos_estudo_1 as pos_estudo
from chiocca.v2 import textos_readme
from chiocca.v2.investigacao import AVISO, motor
from chiocca.v2.lacre import ULTIMO_EXERCICIO_LIBERADO

DOCS = {"pt": RAIZ / "docs" / "ficha-do-motor.md", "en": RAIZ / "docs" / "en" / "engine-card.md"}


def numeros(caminho: Path = pos_estudo.NUMEROS_ESTUDO_1) -> dict[str, Any]:
    """Os números da avaliação do estudo 1, todos lidos dos JSONs versionados."""
    n = json.loads(Path(caminho).read_text(encoding="utf-8"))
    r = pos_estudo.calcula(n, pos_estudo.le_dados())
    tx = {k: [sum(v["em_alerta"] for v in n["taxa"][k].values()), sum(v["avaliadas"] for v in n["taxa"][k].values())]
          for k in ("nf", "fin")}  # fmt: skip
    ant = r["antecedencia"]
    out: dict[str, Any] = {
        "motor": motor(),
        "pre_registro": {"assinatura": n["pre_registro"]["assinatura"], "emendas": n["pre_registro"]["emendas"]},
        "dados": {"primeiro_exercicio": 2010, "ultimo_exercicio": ULTIMO_EXERCICIO_LIBERADO,
                  "empresa_anos_nao_financeiras": n["amostra"]["nao_financeira"],
                  "empresa_anos_financeiras": n["amostra"]["financeira"]},  # fmt: skip
        "acerto": {k: n["acerto"][k] for k in ("casos_no_gabarito", "acertaveis", "acertados", "acertados_boba",
                                               "acertados_teste", "acertados_boba_teste")},  # fmt: skip
        "alarmes_por_acerto_nf": {"periodo_inteiro": n["alarmes"]["nf"]["inteiro"]["alarmes_por_acerto"],
                                  "teste": n["alarmes"]["nf"]["teste"]["alarmes_por_acerto"]},  # fmt: skip
        "taxa_de_alerta": {"nao_financeiras": tx["nf"][0] / tx["nf"][1],
                           "com_financeiras": (tx["nf"][0] + tx["fin"][0]) / (tx["nf"][1] + tx["fin"][1])},  # fmt: skip
        "acaso": {"observados": r["observados"], "esperado_anos_independentes": r["esperado"],
                  "p_anos_independentes": r["p_cauda"]},  # fmt: skip
        "antecedencia": {"casos": [{k: c[k] for k in ("caso_id", "empresa", "exercicio", "dt_receb", "data_publica",
                                                      "meses")} for c in ant["casos"]],
                         "mediana_meses": ant["mediana_meses"], "minimo_meses": ant["minimo_meses"],
                         "maximo_meses": ant["maximo_meses"]},  # fmt: skip
    }
    if "variante" in r:
        out["acaso"] |= {"esperado_sem_independencia": r["variante"]["esperado"],
                         "p_sem_independencia": r["variante"]["p_cauda"]}  # fmt: skip
    return out


T: dict[str, dict[str, Any]] = {
    "pt": {
        "titulo": "# Ficha do motor",
        "gerado": "Gerada por `python -m chiocca.v2.ficha_do_motor` a partir de `docs/resultados_numeros.json` (o mesmo JSON do [resumo](resumo.md)) e da [análise descritiva depois do resultado](analises-pos-estudo-1.md). Não edite à mão: um teste compara este arquivo com a saída do script. Formato de model card.",
        "h_versao": "## Versão",
        "versao": ["Motor: {v1}. O estudo 1 está congelado nesse commit; o produto usa o motor como está.",
                   "Camada do produto: {v2} (contexto, confiança, linhagem, investigação, API e interface), sem mudar nenhum valor do motor.",
                   "Pré-registro assinado em {assinatura}, com {emendas} emendas ([`docs/pre-registro.md`](pre-registro.md))."],
        "h_uso": "## Uso pretendido",
        "uso": ["Apontar onde olhar nas demonstrações financeiras públicas de companhias abertas brasileiras, para análise humana.",
                "Cada sinal vem com a regra, o contexto (percentil no setor e no ano, histórico da própria empresa), a confiança nos dados e o lastro até a linha do documento."],
        "h_fora": "## Fora de escopo",
        "fora": ["Decisão de investimento.", "Acusação: um alerta é sinal estatístico, não prova de irregularidade.",
                 "Decisão automática sobre pessoas ou empresas."],
        "h_dados": "## Dados",
        "dados": ["Demonstrações financeiras padronizadas (DFP) da CVM, dos dados abertos e, para versões antigas, do ENET, lidas \"como eram\": em cada data, só o que tinha sido entregue até ela.",
                  "Exercícios de {ini} a {fim}; os de {fim1} em diante estão lacrados e reservados ao estudo 2.",
                  "Amostra do estudo 1: {nf} empresa-anos não financeiras e {fin} financeiras; gabarito de {casos} casos públicos (condenação da CVM ou fraude admitida), {n} deles acertáveis."],
        "h_avaliacao": "## Avaliação (estudo 1)",
        "avaliacao": ["Acertos: {a} de {n} casos acertáveis (a regra boba acertou {ab}); na janela de teste, {at} (regra boba: {abt}).",
                      "Alarmes por acerto, não financeiras: {xi} no período inteiro e {xt} na janela de teste.",
                      "Taxa de alerta: {taxa} das empresa-anos não financeiras avaliadas ({taxa_total} incluindo as financeiras).",
                      "Teste contra o acaso (análise descritiva depois do resultado, não pré-registrada): sem supor anos independentes, o acaso daria {e2} acertos, e {obs} ou mais com chance de {p2}; supondo anos independentes, {e1} acertos ({p1}). O número de acertos não superou o acaso.",
                      "Antecedência dos acertos (mesma natureza): mediana de {med} meses entre a entrega da primeira DFP em alerta no período afetado e a data pública do caso, de {mn} a {mx} meses."],
        "h_limitacoes": "## Limitações",
        "limitacoes_abertura": "As mesmas da seção \"Limitações\" do README:",
        "h_etica": "## Considerações éticas",
        "etica": ["Alerta, não acusação. Toda saída leva o aviso fixo: \"{aviso}\"",
                  "Sem ranking público: nenhuma lista de empresas ordenada por alerta, percentil ou escore, em nenhuma saída (documentos, API e interface).",
                  "Os resultados por empresa ficam fora do git (`resultados/`); o gabarito só tem casos públicos.",
                  "Sem dados pessoais: nem CPF nem nome de pessoa física (auditor pessoa física aparece sem nome)."],
    },
    "en": {
        "titulo": "# Engine card",
        "gerado": "Generated by `python -m chiocca.v2.ficha_do_motor` from `docs/resultados_numeros.json` (the same JSON as the [summary](../summary.md)) and the [descriptive analysis after the result](post-study-1-analyses.md). Do not edit by hand: a test compares this file with the script output. Model card format.",
        "h_versao": "## Version",
        "versao": ["Engine: {v1}. Study 1 is frozen at that commit; the product uses the engine as it is.",
                   "Product layer: {v2} (context, confidence, lineage, investigation, API and interface), without changing any engine value.",
                   "Pre-registration signed on {assinatura}, with {emendas} amendments ([`docs/pre-registro.md`](../pre-registro.md))."],
        "h_uso": "## Intended use",
        "uso": ["Point to where to look in the public financial statements of Brazilian listed companies, for human analysis.",
                "Each signal comes with the rule, the context (percentile in the sector and year, the company's own history), the confidence in the data and the lineage down to the document line."],
        "h_fora": "## Out of scope",
        "fora": ["Investment decisions.", "Accusation: an alert is a statistical signal, not proof of wrongdoing.",
                 "Automated decisions about people or companies."],
        "h_dados": "## Data",
        "dados": ["CVM standardized financial statements (DFP), from the open data and, for old versions, from ENET, read \"as they were\": on each date, only what had been filed by then.",
                  "Fiscal years {ini} to {fim}; {fim1} onward are sealed and reserved for study 2.",
                  "Study 1 sample: {nf} non-financial and {fin} financial company-years; ground truth of {casos} public cases (CVM conviction or admitted fraud), {n} of them detectable."],
        "h_avaliacao": "## Evaluation (study 1)",
        "avaliacao": ["Detections: {a} of {n} detectable cases (the naive rule detected {ab}); in the test window, {at} (naive rule: {abt}).",
                      "False alarms per detected case, non-financial: {xi} over the whole period and {xt} in the test window.",
                      "Alert rate: {taxa} of evaluated non-financial company-years ({taxa_total} including financial ones).",
                      "Test against chance (descriptive analysis after the result, not pre-registered): without assuming independent years, chance would give {e2} detections, and {obs} or more with probability {p2}; assuming independent years, {e1} detections ({p1}). The number of detections did not beat chance.",
                      "Lead time of the detections (same nature): median of {med} months between the filing of the first DFP in alert in the affected period and the case's public date, from {mn} to {mx} months."],
        "h_limitacoes": "## Limitations",
        "limitacoes_abertura": "The same as in the README's \"Limitations\" section:",
        "h_etica": "## Ethical considerations",
        "etica": ["Alert, not accusation. Every output carries the fixed notice: \"{aviso}\"",
                  "No public ranking: no list of companies ranked by alert, percentile or score, in any output (documents, API and interface).",
                  "Per-company results stay out of git (`resultados/`); the ground truth only has public cases.",
                  "No personal data: no CPF and no natural person's name (an individual auditor appears without a name)."],
    },
}  # fmt: skip


def _limitacoes_doc(lang: str) -> list[str]:
    """As limitações do README, com os links ajustados para quem lê a partir de docs/ (PT) ou docs/en/ (EN)."""
    if lang == "pt":
        return [x.replace("](docs/", "](") for x in textos_readme.limitacoes(lang)]
    return [x.replace("](docs/en/", "](").replace("](docs/", "](../") for x in textos_readme.limitacoes(lang)]


def render(lang: str) -> str:
    t, x = T[lang], numeros()
    i = lambda v: inteiro(v, lang)  # noqa: E731
    d = lambda v, c=1: "—" if v is None else decimal(v, lang, c)  # noqa: E731
    ac, ac_ = x["acerto"], x["acaso"]
    v = dict(
        v1=x["motor"]["v1"], v2=x["motor"]["v2"], assinatura=data(x["pre_registro"]["assinatura"], lang),
        emendas=i(x["pre_registro"]["emendas"]), ini=x["dados"]["primeiro_exercicio"], fim=x["dados"]["ultimo_exercicio"],
        fim1=x["dados"]["ultimo_exercicio"] + 1, nf=i(x["dados"]["empresa_anos_nao_financeiras"]),
        fin=i(x["dados"]["empresa_anos_financeiras"]), casos=i(ac["casos_no_gabarito"]), n=i(ac["acertaveis"]),
        a=i(ac["acertados"]), ab=i(ac["acertados_boba"]), at=i(ac["acertados_teste"]), abt=i(ac["acertados_boba_teste"]),
        xi=d(x["alarmes_por_acerto_nf"]["periodo_inteiro"]), xt=d(x["alarmes_por_acerto_nf"]["teste"]),
        taxa=pct(x["taxa_de_alerta"]["nao_financeiras"], lang), taxa_total=pct(x["taxa_de_alerta"]["com_financeiras"], lang),
        obs=i(ac_["observados"]), e1=d(ac_["esperado_anos_independentes"], 2), p1=pct(ac_["p_anos_independentes"], lang, 1),
        e2=d(ac_.get("esperado_sem_independencia"), 2), p2=pct(ac_["p_sem_independencia"], lang, 1) if "p_sem_independencia" in ac_ else "—",
        med=d(x["antecedencia"]["mediana_meses"]), mn=d(x["antecedencia"]["minimo_meses"]),
        mx=d(x["antecedencia"]["maximo_meses"]), aviso=AVISO[lang],
    )  # fmt: skip
    linhas = [t["titulo"], "", t["gerado"], "", f"> {AVISO[lang]}"]
    for h, k in (("h_versao", "versao"), ("h_uso", "uso"), ("h_fora", "fora"), ("h_dados", "dados"),
                 ("h_avaliacao", "avaliacao")):  # fmt: skip
        linhas += ["", t[h], ""] + ["- " + s.format(**v) for s in t[k]]
    linhas += ["", t["h_limitacoes"], "", t["limitacoes_abertura"], ""] + ["- " + s for s in _limitacoes_doc(lang)]
    linhas += ["", t["h_etica"], ""] + ["- " + s.format(**v) for s in t["etica"]]
    return "\n".join(linhas) + "\n"


def main() -> None:
    for lang, caminho in DOCS.items():
        caminho.write_text(render(lang), encoding="utf-8")
        print(caminho)


if __name__ == "__main__":
    main()
