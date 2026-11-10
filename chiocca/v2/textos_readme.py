"""Textos do README gerados dos JSONs versionados (pedido de 09/11/2026): a seção "Limitações", em PT e EN.

Cada limitação traz uma frase e o link para o documento onde está o número. Nenhum número é escrito à mão: todos
vêm de `docs/resultados_numeros.json` (estudo 1), da análise depois do resultado (`chiocca.v2.analises_pos_estudo_1`)
e do invariante (`docs/invariante_numeros.json`). Um teste confere que o README traz exatamente estes textos.
"""

from __future__ import annotations

import json
from typing import Any

from chiocca import base
from chiocca.formato import decimal, inteiro, pct
from chiocca.v2 import analises_pos_estudo_1 as pos_estudo
from chiocca.v2 import invariante

LINKS = {
    "pt": {"resumo": "docs/resumo.md", "resultados": "docs/resultados.md", "analise": "docs/analises-pos-estudo-1.md",
           "armazem": "docs/armazenamento-temporal.md"},
    "en": {"resumo": "docs/summary.md", "resultados": "docs/en/results.md", "analise": "docs/en/post-study-1-analyses.md",
           "armazem": "docs/en/temporal-storage.md"},
}  # fmt: skip

T = {
    "pt": [
        "O juro implícito responde sozinho por {pj} das empresa-anos não financeiras em alerta ({jt} de {et}): a despesa financeira (3.06.02) inclui variação cambial, juros de arrendamento e outros itens que não são juros dos empréstimos ([resumo]({resumo})).",
        "O M-score ficou sem valor em {mnc} de {mtot} empresa-anos; em {cd}, faltou o DEPI. O motivo mais comum é a DFC sem linha de depreciação na seção 6.01.01 ({dep} empresa-anos); quando a depreciação vem somada à amortização na mesma linha, o total é usado e o DEPI é calculado ([resultados]({resultados})).",
        "O corte de {corte} do M-score vem de Beneish (1999), estimado com empresas dos EUA, e não foi recalibrado para o Brasil ([resumo]({resumo})).",
        "O IRB não pode ser acertado com DFP anual (emenda 3); pegá-lo exigiria dados trimestrais (ITR) ([resumo]({resumo})).",
        "Poucos casos: {n} acertáveis em {casos} no gabarito, nenhum deles financeiro ([resumo]({resumo})).",
        "O número de acertos não superou o acaso no teste descritivo feito depois do resultado: {obs} acertos, contra {e2} esperados sem supor anos independentes ({e1} supondo anos independentes) ([análise]({analise})).",
        "Versões antigas recuperadas pelo ENET só existem para demonstrações consolidadas: de 2010 a 2023, {ind} empresa-anos com a versão da época só em demonstração individual ficaram de fora (emenda 8) ([armazenamento temporal]({armazem})).",
    ],
    "en": [
        "The implied interest rate alone accounts for {pj} of non-financial company-years in alert ({jt} of {et}): finance costs (3.06.02) include exchange differences, lease interest and other items that are not interest on borrowings ([summary]({resumo})).",
        "The M-score had no value in {mnc} of {mtot} company-years; in {cd}, DEPI was missing. The most common reason is a cash flow statement with no depreciation line in section 6.01.01 ({dep} company-years); when depreciation is combined with amortization in the same line, the total is used and DEPI is computed ([results]({resultados})).",
        "The M-score cut-off of {corte} comes from Beneish (1999), estimated with US companies, and was not recalibrated for Brazil ([summary]({resumo})).",
        "IRB cannot be detected with annual DFPs (amendment 3); catching it would require quarterly data (ITR) ([summary]({resumo})).",
        "Few cases: {n} detectable out of {casos} in the ground truth, none of them financial ([summary]({resumo})).",
        "The number of detections did not beat chance in the descriptive test done after the result: {obs} detections, against {e2} expected without assuming independent years ({e1} assuming independent years) ([analysis]({analise})).",
        "Old versions recovered from ENET exist only for consolidated statements: from 2010 to 2023, {ind} company-years whose point-in-time version had individual statements only were left out (amendment 8) ([temporal storage]({armazem})).",
    ],
}  # fmt: skip


def limitacoes(lang: str) -> list[str]:
    """As limitações do README, com os números lidos dos JSONs."""
    n: dict[str, Any] = json.loads(pos_estudo.NUMEROS_ESTUDO_1.read_text(encoding="utf-8"))
    r = pos_estudo.calcula(n, pos_estudo.le_dados())
    inv = json.loads(invariante.NUMEROS.read_text(encoding="utf-8"))
    jb = n["descritiva"]["juro"]
    so_juro = jb["antes"]["so_juro"] + jb["depois"]["so_juro"]
    em = jb["antes"]["em_alerta"] + jb["depois"]["em_alerta"]
    m = n["nao_calculaveis"]["mscore"]
    i = lambda x: inteiro(x, lang)  # noqa: E731
    valores = dict(
        pj=pct(so_juro / em, lang), jt=i(so_juro), et=i(em), mnc=i(m["nao_calculaveis"]), mtot=i(m["empresa_anos"]),
        cd=i(n["descritiva"]["depi"]["amostra"]["com_depi"]),
        dep=i(n["nao_calculaveis"]["DEPI"]["motivos"]["conta_ausente:depreciacao"]),
        corte=decimal(n["regras"]["corte_m"], lang, 2), n=i(n["acerto"]["acertaveis"]),
        casos=i(n["acerto"]["casos_no_gabarito"]), obs=i(r["observados"]), e1=decimal(r["esperado"], lang, 2),
        e2=decimal(r["variante"]["esperado"], lang, 2),
        ind=i(invariante.situacao_total(inv)[base.INDISPONIVEL_INDIVIDUAL]), **LINKS[lang],
    )  # fmt: skip
    textos = [t.format(**valores) for t in T[lang]]
    zeros = pos_estudo.frase_readme_nao_preenchidas(r, lang, LINKS[lang]["analise"])
    return textos + ([zeros] if zeros else [])


def secao_limitacoes(lang: str) -> str:
    """O corpo da seção "Limitações" do README (sem o título)."""
    abertura = {
        "pt": "As limitações do estudo 1 estão no [resumo](docs/resumo.md) e nos [resultados](docs/resultados.md). As principais:",
        "en": "Study 1's limitations are in the [summary](docs/summary.md) and the [results](docs/en/results.md). The main ones:",
    }[lang]
    return abertura + "\n\n" + "\n".join("- " + x for x in limitacoes(lang))


# Pedido de 09/11/2026: o README separa a correção do software da efetividade da detecção.
SEPARACAO = {
    "pt": {
        "h_correcao": "#### Correção do software",
        "correcao": "Os testes automáticos (pytest) rodam no CI em Python 3.12 e 3.13. O invariante reproduz o estudo 1 a partir do armazém temporal: {i} de {e} empresa-anos iguais ao estudo, coluna por coluna ([armazenamento temporal](docs/armazenamento-temporal.md)). O exemplo resolvido confere cada fórmula contra valores calculados à mão (`data/exemplo_resolvido.json`), e as conferências de qualidade testam os próprios dados da CVM ([conferências](docs/conferencias.md)). Isso mostra que o software calcula o que o pré-registro manda e reproduz o estudo 1.",
        "h_efetividade": "#### Efetividade da detecção",
        "efetividade": "No estudo 1, o motor acertou {a} de {n} casos acertáveis, com {xi} alarmes por acerto no período inteiro e taxa de alerta de {taxa} das empresa-anos não financeiras avaliadas ([resumo](docs/resumo.md)). A [ficha do motor](docs/ficha-do-motor.md) reúne esses números, o teste contra o acaso, o uso pretendido e o que fica fora de escopo.",
        "nao_prova": "Uma coisa não prova a outra: o software estar correto não faz os alertas acertarem, e um acerto não mostra que o cálculo está certo. A correção é conferida pelos testes; a efetividade, só pelo estudo, com gabarito e pré-registro.",
    },
    "en": {
        "h_correcao": "#### Software correctness",
        "correcao": "The automated tests (pytest) run in CI on Python 3.12 and 3.13. The invariant reproduces study 1 from the temporal store: {i} of {e} company-years equal to the study, column by column ([temporal storage](docs/en/temporal-storage.md)). The worked example checks every formula against hand-calculated values (`data/exemplo_resolvido.json`), and the quality checks test the CVM data itself ([data checks](docs/en/data-checks.md)). This shows that the software computes what the pre-registration prescribes and reproduces study 1.",
        "h_efetividade": "#### Detection effectiveness",
        "efetividade": "In study 1, the engine detected {a} of {n} detectable cases, with {xi} false alarms per detected case over the whole period and an alert rate of {taxa} of evaluated non-financial company-years ([summary](docs/summary.md)). The [engine card](docs/en/engine-card.md) brings these figures together with the test against chance, the intended use and what is out of scope.",
        "nao_prova": "One does not prove the other: correct software does not make the alerts right, and a detection does not show that the calculation is correct. Correctness is checked by the tests; effectiveness only by the study, with a ground truth and a pre-registration.",
    },
}  # fmt: skip


def separacao(lang: str) -> dict[str, str]:
    """As duas partes do README, com os números lidos dos JSONs (invariante e estudo 1)."""
    from chiocca.v2 import ficha_do_motor

    t = SEPARACAO[lang]
    inv = json.loads(invariante.NUMEROS.read_text(encoding="utf-8"))
    x = ficha_do_motor.numeros()
    i = lambda v: inteiro(v, lang)  # noqa: E731
    return {
        "correcao": t["correcao"].format(i=i(sum(v["empresa_anos_iguais"] for v in inv["exercicios"].values())),
                                         e=i(sum(v["empresa_anos_estudo"] for v in inv["exercicios"].values()))),
        "efetividade": t["efetividade"].format(a=i(x["acerto"]["acertados"]), n=i(x["acerto"]["acertaveis"]),
                                               xi=decimal(x["alarmes_por_acerto_nf"]["periodo_inteiro"], lang, 1),
                                               taxa=pct(x["taxa_de_alerta"]["nao_financeiras"], lang)),
        "nao_prova": t["nao_prova"], "h_correcao": t["h_correcao"], "h_efetividade": t["h_efetividade"],
    }  # fmt: skip
