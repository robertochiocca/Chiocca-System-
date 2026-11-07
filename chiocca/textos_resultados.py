"""Textos de docs/resultados.md (PT) e docs/en/results.md (EN), montados de docs/resultados_numeros.json.

Uma fonte de números, dois textos (PROMPT.md, projeto bilíngue). Nenhum número é escrito à mão aqui: todos
vêm do JSON gerado por chiocca.relatorio_resultados. Os termos em inglês seguem glossario_pt_en.yaml.
"""

from __future__ import annotations

from typing import Any

from chiocca.formato import data, decimal, inteiro, pct
from chiocca.sinais.mscore import COEFICIENTES, INTERCEPTO

NF, FIN = "nao_financeira", "financeira"

# Rótulos de contas que aparecem nos motivos de "não calculável": (PT, EN, código da CVM).
CONTAS = {
    "depreciacao": ("depreciação, linhas da DFC na seção 6.01.01", "depreciation, cash flow lines in section 6.01.01"),
    "contas_a_receber": ("contas a receber (1.01.03)", "trade receivables (1.01.03)"),
    "resultado_bruto": ("resultado bruto (3.03)", "gross profit (3.03)"),
    "ativo_total": ("ativo total (conta 1)", "total assets (account 1)"),
    "receita_liquida": ("receita líquida (3.01)", "net revenue (3.01)"),
    "despesas_vendas": ("despesas com vendas (3.04.01)", "selling expenses (3.04.01)"),
    "passivo_circulante": ("passivo circulante (2.01)", "current liabilities (2.01)"),
    "fornecedores": ("fornecedores (2.01.02)", "trade payables (2.01.02)"),
    "emprestimos_cp": ("empréstimos e financiamentos de curto prazo (2.01.04)", "short-term borrowings (2.01.04)"),
    "custo_vendas": ("custo dos bens e/ou serviços vendidos (3.02)", "cost of sales (3.02)"),
    "despesas_financeiras": ("despesas financeiras (3.06.02)", "finance costs (3.06.02)"),
    "numerador": (
        'linha "outras receitas operacionais"',
        '"outras receitas operacionais" line (other operating income)',
    ),
    "denominador": (
        'linha "resultado antes dos tributos"',
        '"resultado antes dos tributos" line (income before taxes)',
    ),
    "patrimonio_liquido": ("patrimônio líquido", "shareholders' equity"),
}
# Parte do denominador que deu zero ou negativo.
PECAS = {
    "t-1": ("índice de t−1 igual a zero", "t−1 ratio equal to zero"),
    "receita t-1": ("receita de t−1", "t−1 revenue"),
    "receita t": ("receita de t", "t revenue"),
    "margem t": ("margem bruta de t", "t gross margin"),
    "ativo t-1": ("ativo total de t−1", "t−1 total assets"),
    "ativo t": ("ativo total de t", "t total assets"),
    "base t-1": ("depreciação + imobilizado de t−1", "t−1 depreciation + property, plant and equipment"),
    "base t": ("depreciação + imobilizado de t", "t depreciation + property, plant and equipment"),
    "taxa t": ("taxa de depreciação de t", "t depreciation rate"),
    "custo t": ("custo das vendas de t", "t cost of sales"),
    "custo t-1": ("custo das vendas de t−1", "t−1 cost of sales"),
    "divida media": ("dívida média (sem empréstimos em t e t−1)", "average debt (no borrowings in t and t−1)"),
    "ativo medio": ("ativo total médio", "average total assets"),
    "denominador": (
        'linha "resultado antes dos tributos"',
        '"resultado antes dos tributos" line (income before taxes)',
    ),
    "ativo_total": ("ativo total", "total assets"),
}
TIPOS = {
    "conta_ausente": ("conta ausente", "missing account"),
    "divisao_por_zero": ("denominador zero", "zero denominator"),
    "denominador_negativo": ("receita negativa no denominador", "negative revenue in the denominator"),
    "plano_de_contas": ("plano de contas", "chart of accounts"),
    "componente": ("componente não calculável", "component not computable"),
    "cdi_ausente": ("CDI ausente", "CDI rate missing"),
    "patrimonio_liquido_ambiguo": ("mais de uma linha de patrimônio líquido no nível mais alto",
                                   "more than one top-level shareholders' equity line"),
    "denominador_ambiguo": ('mais de uma linha "resultado antes dos tributos"',
                            'more than one "resultado antes dos tributos" line'),
}  # fmt: skip
PLANOS = {"banco": ("de banco", "bank"), "outro": ("não reconhecido", "not recognized")}
SINAIS = {
    "mscore": ("M-score (M)", "M-score (M)"),
    "dpo": ("Variação do DPO", "DPO change"),
    "juro": ("Juro implícito", "Implied interest rate"),
    "lucro_sem_caixa": ("Lucro sem caixa (só na ficha)", "Accruals (alert sheet only)"),
    "peso_nao_recorrente": ("Peso não recorrente (financeiras)", "Non-recurring weight (financial companies)"),
    "alavancagem_nf": ("Regra boba, não financeiras", "Naive baseline rule, non-financial"),
    "alavancagem_fin": ("Regra boba, financeiras", "Naive baseline rule, financial"),
}


def motivo(m: str, lang: str) -> str:
    k = 0 if lang == "pt" else 1
    tipo, _, det = m.partition(":")
    rotulo = TIPOS.get(tipo, (tipo, tipo))[k]
    if not det:
        return rotulo
    if tipo == "conta_ausente":
        return f"{rotulo}: {CONTAS.get(det, (det, det))[k]}"
    if tipo == "plano_de_contas":
        return (
            f"{rotulo} {PLANOS.get(det, (det, det))[k]}"
            if lang == "pt"
            else f"{PLANOS.get(det, (det, det))[k]} {rotulo}"
        )
    if tipo == "componente":
        return f"{rotulo}: {det}"
    sinal, _, resto = det.partition(" ")
    if sinal in (*COEFICIENTES, "DPO") and resto in PECAS:
        return f"{rotulo}: {sinal}, {PECAS[resto][k]}"
    return f"{rotulo}: {PECAS.get(det, (det, det))[k]}"


T: dict[str, dict[str, Any]] = {
    "pt": {
        "titulo": "# Resultados (Fase 2)",
        "gerado": "Gerado por `python -m chiocca.relatorio_resultados` a partir de `resultados/sinais_empresa_ano.csv` (fora do git), que sai de `python -m chiocca.sinais_amostra`. Não edite à mão: um teste compara este arquivo com a saída do script. Só aparecem números agregados, os casos do gabarito, que são públicos, e a tabela dos casos em observação (emenda 8). Nenhuma lista de empresas em alerta sai deste repositório.",
        "execucao": "Sinais calculados em {data} com o código do commit `{commit}`. O período de teste (exercícios de 2017 a 2023, pré-registro, seção 8) foi aberto em {abertura}, com o commit `{commit_abertura}`, na primeira execução da amostra inteira. As regras foram aplicadas como estão no pré-registro, sem nenhum corte alternativo testado. O resultado é mostrado como saiu (seção 9).",
        "h_resumo": "## Números principais",
        "amostra": "**Amostra, 2010 a 2023:** {nf} empresa-anos de não financeiras com receita e {fin} de financeiras, de {empresas} empresas. Ficaram de fora {sem_receita} empresa-anos de não financeiras sem receita (seção 2) e {sem_versao} sem versão da época (emenda 5).",
        "acerto": "**Acerto (seção 5):** {acertados} de {acertaveis} casos acertáveis. Depois da exclusão das empresas sem receita, continuam acertáveis {efetivos} de {acertaveis} (emenda 9). Contando todos os {casos} casos do gabarito, são {acertados} de {casos}, com teto de {acertaveis} de {casos} no estudo principal.",
        "acerto_boba": "**Regra boba (seção 7):** {acertados_boba} de {acertaveis} casos acertáveis.",
        "alarmes_nf": "**Alarmes por acerto (emenda 10), não financeiras, 2017 a 2023:** {e} empresas em alerta, de {aval} avaliadas; ({e} − {a}) ÷ {a} = {x}. Com a regra boba: {eb} empresas em alerta, de {avalb}; ({eb} − {ab}) ÷ {ab} = {xb}.",
        "alarmes_fin": "**Financeiras, 2017 a 2023:** {e} empresas em alerta, de {aval} avaliadas. Alarmes por acerto não calculável: nenhum caso acertável é financeira. Com a regra boba: {eb} empresas em alerta, de {avalb}.",
        "teste_acertados": "Dos {acertados} casos acertados, {k} têm alerta no período de teste. A fórmula da emenda 10 desconta os {acertados} casos acertados das empresas em alerta.",
        "taxa_total": "**Taxa de alerta, 2010 a 2023, somando os exercícios:** não financeiras, {em} empresas em alerta de {aval} avaliadas ({p}); financeiras, {emf} de {avalf} ({pf}).",
        "comparacao": "**Comparação com a regra boba:** o detector acerta {a} casos e a regra boba, {b}. Nas não financeiras, o detector tem {x} alarmes por acerto e a regra boba, {y}: {r} vezes mais. O pré-registro manda pôr essa comparação no resumo.",
        "h_regras": "## Regras aplicadas",
        "regras": [
            "**Versão da época:** a de cada empresa-ano na data de corte, da base da Fase 1; t vem do ÚLTIMO e t−1 do PENÚLTIMO da mesma DFP (emenda 5).",
            "**Contas:** pelos códigos confirmados na Fase 0 (reconhecimento, parte 1.4). Depreciação e juros pagos pelos padrões de texto congelados (reconhecimento, parte 4.2), com a regra de conta-mãe e a comparação de texto da emenda 7.",
            "**Juros pagos:** os que estão no caixa operacional (seção 6.01) passam para o financiamento em todas as empresas; o caixa operacional ajustado entra no TATA e no lucro sem caixa (pré-registro, seção 4.1).",
            "**Depreciação e amortização numa linha só:** usa-se o total e a empresa-ano é marcada (seção 4.1).",
            "**Conta ausente, denominador zero ou receita negativa no denominador:** não calculável (seção 4.1 e emenda 10). Sem valores neutros e sem aparar extremos (seção 4.1).",
            "**CDI:** série 4389 do SGS do Banco Central (docs/fontes.md); CDI médio do ano = média das taxas diárias nos 12 meses que terminam na data de referência da DFP.",
            "**Alertas (seção 4):** M > {corte}; variação do DPO no decil superior do ano dentro das não financeiras; juro implícito > CDI médio + {spread} p.p.; peso não recorrente no decil superior do ano dentro das financeiras. Não financeira em alerta = pelo menos um dos três sinais; o lucro sem caixa não dispara alerta.",
            "**Regra boba (emenda 7):** (ativo total − patrimônio líquido de nível mais alto) ÷ ativo total, decil superior de cada ano dentro de cada grupo.",
            "**Acerto (seção 5):** alerta em pelo menos um exercício do período afetado, entre 2010 e 2023, com a versão da época entregue antes da data pública. Em todos esses exercícios, a data de corte também é anterior à data pública ({corte_depois} exceções).",
        ],
        "h_escolhas": "## Escolhas de implementação desta fase",
        "escolhas_intro": "O pré-registro não desce a estes detalhes. Cada um foi fixado antes de rodar a amostra, sem testar alternativa, e fica aqui para revisão.",
        "escolhas": [
            "**Decil superior:** valor maior ou igual ao percentil {p} dos valores calculáveis do exercício e do grupo (percentil com interpolação linear, o padrão do pandas).",
            "**Empresa avaliada:** com pelo menos um sinal de alerta do grupo calculável. A taxa de alerta é empresas em alerta ÷ empresas avaliadas; o tamanho da amostra vem ao lado.",
            "**DFC pelo método direto:** os padrões de texto foram aplicados à DFC que a empresa tem. Nas {md} empresa-anos com DFC pelo método direto, não há linha de depreciação, e o M-score fica não calculável (conta ausente).",
            "**Não financeiras em outro plano de contas:** os códigos da Fase 0 valem para o plano não financeiro. Nas {plano} empresa-anos de não financeiras no plano de banco ou não reconhecido, M-score, DPO e juro implícito ficam não calculáveis (motivo: plano de contas).",
            "**Juros pagos não achados:** o caixa operacional fica como apresentado. Linhas achadas na seção 6.01 (movidas) em {j601} empresa-anos e na seção 6.03 (já no financiamento) em {j603}.",
            "**Casos em observação na conta de alarmes:** a empresa inteira fica fora, em todos os anos (a Oi tem caso em observação nas DFs de 2015 e 2016 e também caso no gabarito, Oi 2014, na secundária).",
            "**Emenda 3:** aplicada aos {e3} casos do gabarito fora da análise secundária que têm código CVM e data pública; a última DFP é a da empresa-ano mais recente da amostra entregue antes da data.",
            "**Marca do CPC 06 (R2):** exercícios que começam em 2019 ({cpc06} empresa-anos). A marca não muda nenhum cálculo.",
        ],
        "h_taxa": "## Taxa de alerta por ano",
        "taxa_nf": "**Não financeiras.** Empresas por exercício. Nas colunas dos sinais: empresa-anos com alerta ÷ empresa-anos com o sinal calculável.",
        "taxa_fin": "**Financeiras.**",
        "col_taxa_nf": "| Exercício | Amostra | Avaliadas | Em alerta | Taxa | M > {corte} | Salto do DPO | Juro implícito | Regra boba |",
        "col_taxa_fin": "| Exercício | Amostra | Avaliadas | Em alerta | Taxa | Regra boba |",
        "total": "Total (soma dos exercícios)",
        "h_casos": "## Casos acertáveis, caso a caso",
        "casos_intro": "Os {n} casos acertáveis do gabarito (emendas 8 e 9). Exercícios avaliados: na amostra, com versão da época entregue antes da data pública e com pelo menos um sinal calculável.",
        "col_casos": "| Caso | Código CVM | Período afetado nos dados | Data pública | Exercícios avaliados | Exercícios em alerta | Fora da conta | Acertado | Regra boba |",
        "detalhe_intro": "**Sinais por exercício.** M: valor do M-score (alerta se > {corte}). DPO: variação do prazo de pagamento, em dias (alerta no decil superior do ano). Juro: juro implícito menos CDI médio, em p.p. (alerta se > {spread}). n.c. = não calculável, com os componentes que faltaram. Em negrito, o sinal que disparou.",
        "col_detalhe": "| Caso | Exercício | M | DPO | Juro − CDI | Em alerta | Regra boba |",
        "h_alarmes": "## Alarmes por acerto e regra boba (2017 a 2023)",
        "alarmes_intro": "Emenda 10: (empresas em alerta − casos acertados) ÷ casos acertados, com empresas distintas que tiveram pelo menos um alerta no período de teste. As {obs} empresas dos casos em observação ficam fora. Casos acertados: os do estudo principal, em qualquer exercício do período afetado.",
        "col_alarmes": "| Grupo | Regra | Empresas avaliadas | Empresas em alerta | Casos acertados | Alarmes por acerto |",
        "h_previsoes": "## Previsões do pré-registro (seção 4.2)",
        "prev_ame": "**Americanas.** Previsão: o M-score dispara em pelo menos um ano antes de 2023, puxado por TATA e AQI e não pelo GMI; DPO e juro implícito não disparam. Resultado no exercício de {ano}: M = {m} ({alerta_m}); DPO {alerta_dpo}; juro implícito {alerta_juro}. Componentes e contribuições (coeficiente × índice; M = {intercepto} + soma):",
        "col_comp": "| Componente | Índice | Contribuição |",
        "prev_irb": "**IRB.** Previsão: o sinal não dispara antes da data pública. A DFP de 2019 foi entregue em {dt2019}, depois de {data_irb}; a última antes da data é a de {ano}. Peso não recorrente em {ano}: {p} (limite do decil superior do ano nas financeiras: {lim}); {alerta}. Por isso o IRB não pode ser acertado (emenda 3).",
        "h_secundarias": "## Análises secundárias (rotuladas; fora da conta principal)",
        "emenda_1": "**Emenda 1, Americanas:** alerta em algum exercício até 2021 com DFP entregue antes de {data}? {r}. Exercícios em alerta: {anos}. Regra boba: {rb}.",
        "emenda_3_intro": "**Emenda 3, alerta na última DFP publicada antes da data pública** (mede alerta antecipado, não acerto): {alerta} de {com_dfp} casos com DFP na amostra antes da data; regra boba, {boba}. Casos sem DFP na amostra antes da data: {sem}.",
        "col_e3": "| Caso | Data pública | Última DFP antes da data | Em alerta | Regra boba |",
        "emenda_9_intro": "**Emenda 9, partes 2a e 2b:** mesma regra de acerto, com a primeira data pública documentada. Parte 2a: {a2a} de {c2a} casos acertados ({e2a} com exercício na amostra antes da data); regra boba, {b2a}. Parte 2b, teto otimista: {a2b} de {c2b} ({e2b} com exercício na amostra antes da data); regra boba, {b2b}.",
        "col_sec": "| Caso | Parte | Período afetado nos dados | Data pública | Exercícios avaliados | Exercícios em alerta | Fora da conta | Acertado | Regra boba |",
        "h_obs": "## Casos em observação (emenda 8)",
        "obs_intro": "Fora das métricas de acerto e de alarme. A tabela mostra se houve alerta em exercício com DFP entregue antes da data do caso: a abertura do processo, para a Oi, que ainda não tem decisão; o julgamento, para as companhias do grupo de fronteira.",
        "col_obs": "| Caso | Código CVM | Data | Período | Exercícios com DFP antes da data | Na amostra | Sem receita | Em alerta |",
        "h_nc": "## Não calculável, por sinal e motivo",
        "nc_intro": "Empresa-anos da amostra de cada grupo, de 2010 a 2023. No M-score, uma empresa-ano entra uma vez em cada componente que faltou. Em {sem_pen} empresa-anos de não financeiras, a DFP da época não traz nenhuma conta no comparativo (PENÚLTIMO): tudo o que depende de t−1 fica não calculável, e o motivo mostra a primeira conta procurada.",
        "col_nc": "| Sinal | Empresa-anos | Calculáveis | Não calculáveis |",
        "col_nc_motivo": "| Sinal | Motivo | Empresa-anos |",
        "h_marcas": "## Marcas",
        "marcas": "Depreciação somada com amortização ou exaustão: {dep} empresa-anos de não financeiras. Exercícios marcados pelo CPC 06 (R2): {cpc06}. DFC pelo método direto: {md}.",
        "h_nao_feito": "## O que não foi feito nesta fase",
        "nao_feito": [
            "As duas leituras da Americanas (números originais e reapresentados, componente por componente), o teste de robustez com valores neutros (pré-registro, seção 4.1) e a análise secundária da emenda 5 (empresa-anos com versão da época indisponível, pela versão disponível): ficam para a fase seguinte.",
            "Ficha de alerta (Fase 4) e resumo de uma página (Fase 5).",
        ],
        "sim": "sim",
        "nao": "não",
        "alerta": "alerta",
        "sem_alerta": "sem alerta",
        "nc": "n.c.",
        "sem_dfp": "sem DFP na amostra",
        "nf": "Não financeiras",
        "fin": "Financeiras",
        "sinais": "Sinais",
        "boba": "Regra boba",
        "nao_calc": "não calculável",
        "fora": {
            "fora_sem_receita": "sem receita",
            "fora_sem_versao_da_epoca": "sem versão da época",
            "depois_da_data": "DFP depois da data",
            "sem_dfp": "sem DFP nos dados",
        },
    },
    "en": {
        "titulo": "# Results (Phase 2)",
        "gerado": "Generated by `python -m chiocca.relatorio_resultados` from `resultados/sinais_empresa_ano.csv` (not in git), which comes from `python -m chiocca.sinais_amostra`. Do not edit by hand: a test compares this file with the script output. Only aggregate numbers, the ground-truth cases, which are public, and the table of cases under observation (amendment 8) appear here. No list of companies in alert leaves this repository.",
        "execucao": "Signals computed on {data} with the code at commit `{commit}`. The test period (fiscal years 2017 to 2023, pre-registration, section 8) was opened on {abertura}, at commit `{commit_abertura}`, in the first run over the whole sample. The rules were applied exactly as pre-registered, with no alternative cut-off tested. The result is shown as it came out (section 9).",
        "h_resumo": "## Key numbers",
        "amostra": "**Sample, 2010 to 2023:** {nf} company-years of non-financial companies with revenue and {fin} of financial companies, from {empresas} companies. Left out: {sem_receita} company-years of non-financial companies with no revenue (section 2) and {sem_versao} with no point-in-time version (amendment 5).",
        "acerto": "**Detection (section 5):** {acertados} of {acertaveis} detectable cases. After excluding companies with no revenue, {efetivos} of {acertaveis} remain detectable (amendment 9). Counting all {casos} ground-truth cases, it is {acertados} of {casos}, with a ceiling of {acertaveis} of {casos} in the main study.",
        "acerto_boba": "**Naive baseline rule (section 7):** {acertados_boba} of {acertaveis} detectable cases.",
        "alarmes_nf": "**False alarms per detected case (amendment 10), non-financial, 2017 to 2023:** {e} companies in alert, out of {aval} evaluated; ({e} − {a}) ÷ {a} = {x}. With the naive baseline rule: {eb} companies in alert, out of {avalb}; ({eb} − {ab}) ÷ {ab} = {xb}.",
        "alarmes_fin": "**Financial companies, 2017 to 2023:** {e} companies in alert, out of {aval} evaluated. False alarms per detected case not computable: no detectable case is a financial company. With the naive baseline rule: {eb} companies in alert, out of {avalb}.",
        "teste_acertados": "Of the {acertados} detected cases, {k} have an alert in the test period. The amendment 10 formula subtracts all {acertados} detected cases from the companies in alert.",
        "taxa_total": "**Alert rate, 2010 to 2023, summed over fiscal years:** non-financial, {em} companies in alert out of {aval} evaluated ({p}); financial, {emf} of {avalf} ({pf}).",
        "comparacao": "**Comparison with the naive baseline rule:** the detector catches {a} cases and the naive baseline rule, {b}. Among non-financial companies, the detector has {x} false alarms per detected case and the naive baseline rule, {y}: {r} times as many. The pre-registration requires this comparison in the summary.",
        "h_regras": "## Rules applied",
        "regras": [
            "**Point-in-time version:** each company-year as of its cut-off date, from the Phase 1 base; t comes from the ÚLTIMO (current year) column and t−1 from the PENÚLTIMO (prior year) column of the same DFP (amendment 5).",
            "**Accounts:** by the codes confirmed in Phase 0 (reconnaissance, part 1.4). Depreciation and interest paid by the frozen text patterns (reconnaissance, part 4.2), with the parent-account rule and the text comparison of amendment 7.",
            "**Interest paid:** amounts in operating cash flow (section 6.01) are moved to financing for all companies; the adjusted operating cash flow enters TATA and accruals (pre-registration, section 4.1).",
            "**Depreciation and amortization in a single line:** the total is used and the company-year is flagged (section 4.1).",
            "**Missing account, zero denominator or negative revenue in the denominator:** not computable (section 4.1 and amendment 10). No neutral values and no winsorizing (section 4.1).",
            "**CDI rate:** Banco Central do Brasil SGS series 4389 (docs/en/sources.md); average CDI of the year = average of the daily rates over the 12 months ending on the DFP reference date.",
            "**Alerts (section 4):** M > {corte}; DPO change in the top decile of the year among non-financial companies; implied interest rate > average CDI + {spread} p.p.; non-recurring weight in the top decile of the year among financial companies. A non-financial company is in alert when at least one of the three signals fires; accruals do not trigger alerts.",
            "**Naive baseline rule (amendment 7):** (total assets − top-level shareholders' equity) ÷ total assets, top decile of each year within each group.",
            "**Detection (section 5):** an alert in at least one fiscal year of the affected period, between 2010 and 2023, with the point-in-time version filed before the public date. In all those fiscal years the cut-off date is also before the public date ({corte_depois} exceptions).",
        ],
        "h_escolhas": "## Implementation choices in this phase",
        "escolhas_intro": "The pre-registration does not go down to these details. Each was fixed before running the sample, with no alternative tested, and is listed here for review.",
        "escolhas": [
            "**Top decile:** a value greater than or equal to the {p}th percentile of the computable values of the fiscal year and group (percentile with linear interpolation, the pandas default).",
            "**Evaluated company:** at least one of the group's alert signals is computable. The alert rate is companies in alert ÷ evaluated companies; the sample size is shown alongside.",
            "**Direct-method cash flow statement:** the text patterns were applied to whichever cash flow statement the company files. In the {md} company-years with a direct-method statement there is no depreciation line, and the M-score is not computable (missing account).",
            "**Non-financial companies on another chart of accounts:** the Phase 0 codes apply to the non-financial chart. In the {plano} non-financial company-years on the bank chart or an unrecognized one, the M-score, DPO and implied interest rate are not computable (reason: chart of accounts).",
            "**Interest paid not found:** operating cash flow stays as reported. Lines found in section 6.01 (moved) in {j601} company-years and in section 6.03 (already in financing) in {j603}.",
            "**Cases under observation in the false-alarm count:** the whole company is left out, in every year (Oi has a case under observation for its 2015 and 2016 statements and also a ground-truth case, Oi 2014, in the secondary analysis).",
            "**Amendment 3:** applied to the {e3} ground-truth cases outside the secondary analysis that have a CVM code and a public date; the last DFP is the most recent company-year in the sample filed before that date.",
            "**CPC 06 (R2) flag:** fiscal years starting in 2019 ({cpc06} company-years). The flag changes no calculation.",
        ],
        "h_taxa": "## Alert rate by year",
        "taxa_nf": "**Non-financial companies.** Companies per fiscal year. Signal columns: company-years with an alert ÷ company-years with the signal computable.",
        "taxa_fin": "**Financial companies.**",
        "col_taxa_nf": "| Fiscal year | Sample | Evaluated | In alert | Rate | M > {corte} | DPO jump | Implied interest | Naive baseline |",
        "col_taxa_fin": "| Fiscal year | Sample | Evaluated | In alert | Rate | Naive baseline |",
        "total": "Total (sum over fiscal years)",
        "h_casos": "## Detectable cases, one by one",
        "casos_intro": "The {n} detectable ground-truth cases (amendments 8 and 9). Evaluated fiscal years: in the sample, with the point-in-time version filed before the public date and with at least one computable signal.",
        "col_casos": "| Case | CVM code | Affected period in the data | Public date | Evaluated fiscal years | Fiscal years in alert | Not counted | Detected | Naive baseline |",
        "detalhe_intro": "**Signals by fiscal year.** M: M-score value (alert if > {corte}). DPO: change in days payable outstanding, in days (alert in the top decile of the year). Interest: implied interest rate minus average CDI, in p.p. (alert if > {spread}). n.c. = not computable, with the missing components. Bold: the signal fired.",
        "col_detalhe": "| Case | Fiscal year | M | DPO | Interest − CDI | In alert | Naive baseline |",
        "h_alarmes": "## False alarms per detected case and naive baseline rule (2017 to 2023)",
        "alarmes_intro": "Amendment 10: (companies in alert − detected cases) ÷ detected cases, counting distinct companies with at least one alert in the test period. The {obs} companies of the cases under observation are left out. Detected cases: those of the main study, in any fiscal year of the affected period.",
        "col_alarmes": "| Group | Rule | Evaluated companies | Companies in alert | Detected cases | False alarms per detected case |",
        "h_previsoes": "## Pre-registered predictions (section 4.2)",
        "prev_ame": "**Americanas.** Prediction: the M-score fires in at least one year before 2023, driven by TATA and AQI and not by GMI; DPO and implied interest do not fire. Result for fiscal year {ano}: M = {m} ({alerta_m}); DPO {alerta_dpo}; implied interest {alerta_juro}. Components and contributions (coefficient × index; M = {intercepto} + sum):",
        "col_comp": "| Component | Index | Contribution |",
        "prev_irb": "**IRB.** Prediction: the signal does not fire before the public date. The 2019 DFP was filed on {dt2019}, after {data_irb}; the last one before that date is for {ano}. Non-recurring weight in {ano}: {p} (top-decile threshold of the year among financial companies: {lim}); {alerta}. That is why IRB cannot be detected (amendment 3).",
        "h_secundarias": "## Secondary analyses (labeled; outside the main count)",
        "emenda_1": "**Amendment 1, Americanas:** an alert in any fiscal year up to 2021 with the DFP filed before {data}? {r}. Fiscal years in alert: {anos}. Naive baseline rule: {rb}.",
        "emenda_3_intro": "**Amendment 3, alert in the last DFP published before the public date** (measures early warning, not detection): {alerta} of {com_dfp} cases with a DFP in the sample before that date; naive baseline rule, {boba}. Cases with no DFP in the sample before that date: {sem}.",
        "col_e3": "| Case | Public date | Last DFP before that date | In alert | Naive baseline |",
        "emenda_9_intro": "**Amendment 9, parts 2a and 2b:** same detection rule, with the first documented public date. Part 2a: {a2a} of {c2a} cases detected ({e2a} with a fiscal year in the sample before that date); naive baseline rule, {b2a}. Part 2b, optimistic ceiling: {a2b} of {c2b} ({e2b} with a fiscal year in the sample before that date); naive baseline rule, {b2b}.",
        "col_sec": "| Case | Part | Affected period in the data | Public date | Evaluated fiscal years | Fiscal years in alert | Not counted | Detected | Naive baseline |",
        "h_obs": "## Cases under observation (amendment 8)",
        "obs_intro": "Outside the detection and false-alarm metrics. The table shows whether there was an alert in a fiscal year whose DFP was filed before the case date: the opening of the proceeding for Oi, which has no decision yet; the judgment for the boundary-group companies.",
        "col_obs": "| Case | CVM code | Date | Period | Fiscal years with a DFP before that date | In the sample | No revenue | In alert |",
        "h_nc": "## Not computable, by signal and reason",
        "nc_intro": "Company-years in each group's sample, 2010 to 2023. For the M-score, a company-year counts once for each missing component. In {sem_pen} non-financial company-years, the point-in-time DFP has no account at all in the prior-year column (PENÚLTIMO): everything that depends on t−1 is not computable, and the reason shows the first account looked up.",
        "col_nc": "| Signal | Company-years | Computable | Not computable |",
        "col_nc_motivo": "| Signal | Reason | Company-years |",
        "h_marcas": "## Flags",
        "marcas": "Depreciation summed with amortization or depletion: {dep} non-financial company-years. Fiscal years flagged for CPC 06 (R2): {cpc06}. Direct-method cash flow statement: {md}.",
        "h_nao_feito": "## Not done in this phase",
        "nao_feito": [
            "The two readings of Americanas (original and restated figures, component by component), the robustness test with neutral values (pre-registration, section 4.1) and the amendment 5 secondary analysis (company-years with no point-in-time version, using the available version): left for the next phase.",
            "Alert sheet (Phase 4) and one-page summary (Phase 5).",
        ],
        "sim": "yes",
        "nao": "no",
        "alerta": "alert",
        "sem_alerta": "no alert",
        "nc": "n.c.",
        "sem_dfp": "no DFP in the sample",
        "nf": "Non-financial",
        "fin": "Financial",
        "sinais": "Signals",
        "boba": "Naive baseline",
        "nao_calc": "not computable",
        "fora": {
            "fora_sem_receita": "no revenue",
            "fora_sem_versao_da_epoca": "no point-in-time version",
            "depois_da_data": "DFP after the date",
            "sem_dfp": "no DFP in the data",
        },
    },
}


def render(n: dict[str, Any], lang: str) -> str:
    t = T[lang]

    def i(x: int) -> str:
        return inteiro(x, lang)

    def d(x: float, casas: int = 1) -> str:
        return decimal(x, lang, casas)

    def sn(x: bool) -> str:
        return t["sim"] if x else t["nao"]

    def anos(xs: list[int]) -> str:
        return ", ".join(str(a) for a in xs) if xs else "—"

    def nome(c: dict[str, Any]) -> str:
        return f"{c['empresa']} (`{c['caso_id']}`)"

    def fora(c: dict[str, Any]) -> str:
        xs = c.get("anos_fora") or []
        return "; ".join(f"{a}: {t['fora'][m]}" for a, m in xs) if xs else "—"

    def periodo(c: dict[str, Any]) -> str:
        return anos(c.get("anos_periodo") or [])

    def sinal(v: float | None, alerta: bool, casas: int = 1, motivo_nc: str | None = None) -> str:
        if v is None:
            return t["nc"] + (f" ({motivo_nc})" if motivo_nc else "")
        s = d(v, casas)
        return f"**{s}**" if alerta else s

    corte = d(n["regras"]["corte_m"], 2)
    spread = i(int(n["regras"]["spread_pp"]))
    ac, am = n["acerto"], n["amostra"]
    al = n["alarmes"]
    principais = [c for c in n["casos"] if c["acertavel"]]
    linhas: list[str] = [t["titulo"], "", t["gerado"], ""]
    ex = n["execucao"]
    linhas += [
        t["execucao"].format(
            data=data(ex.get("inicio_utc", "")[:10], lang) if ex.get("inicio_utc") else "—",
            commit=ex.get("commit", "—")[:7],
            abertura=data(n["abertura_teste"]["data"], lang),
            commit_abertura=n["abertura_teste"]["commit"][:7],
        ),
        "",
        t["h_resumo"],
        "",
    ]
    soma = {k: {"em": 0, "aval": 0} for k in ("nf", "fin")}
    for k in soma:
        for v in n["taxa"][k].values():
            soma[k]["em"] += v["em_alerta"]
            soma[k]["aval"] += v["avaliadas"]
    no_teste = n["acerto"]["acertados_com_alerta_no_teste"]
    razao = al["nf"]["alarmes_por_acerto"] / al["nf_boba"]["alarmes_por_acerto"]
    linhas += [
        "- " + t["amostra"].format(nf=i(am[NF]), fin=i(am[FIN]), empresas=i(n["marcas"]["empresas"]),
                                   sem_receita=i(am["fora_sem_receita"]), sem_versao=i(am["fora_sem_versao_da_epoca"])),
        "- " + t["acerto"].format(acertados=i(ac["acertados"]), acertaveis=i(ac["acertaveis"]),
                                  efetivos=i(ac["acertaveis_efetivos"]), casos=i(ac["casos_no_gabarito"])),
        "- " + t["acerto_boba"].format(acertados_boba=i(ac["acertados_boba"]), acertaveis=i(ac["acertaveis"])),
        "- " + t["alarmes_nf"].format(e=i(al["nf"]["empresas_em_alerta"]), aval=i(al["nf"]["empresas_avaliadas"]),
                                      a=i(al["nf"]["casos_acertados"]), x=d(al["nf"]["alarmes_por_acerto"]),
                                      eb=i(al["nf_boba"]["empresas_em_alerta"]),
                                      avalb=i(al["nf_boba"]["empresas_avaliadas"]),
                                      ab=i(al["nf_boba"]["casos_acertados"]),
                                      xb=d(al["nf_boba"]["alarmes_por_acerto"])),
        "- " + t["alarmes_fin"].format(e=i(al["fin"]["empresas_em_alerta"]), aval=i(al["fin"]["empresas_avaliadas"]),
                                       eb=i(al["fin_boba"]["empresas_em_alerta"]),
                                       avalb=i(al["fin_boba"]["empresas_avaliadas"])),
        "- " + t["teste_acertados"].format(acertados=i(ac["acertados"]), k=i(no_teste)),
        "- " + t["taxa_total"].format(em=i(soma["nf"]["em"]), aval=i(soma["nf"]["aval"]),
                                      p=pct(soma["nf"]["em"] / soma["nf"]["aval"], lang),
                                      emf=i(soma["fin"]["em"]), avalf=i(soma["fin"]["aval"]),
                                      pf=pct(soma["fin"]["em"] / soma["fin"]["aval"], lang)),
        "- " + t["comparacao"].format(a=i(ac["acertados"]), b=i(ac["acertados_boba"]),
                                      x=d(al["nf"]["alarmes_por_acerto"]), y=d(al["nf_boba"]["alarmes_por_acerto"]),
                                      r=d(razao)),
        "",
        t["h_regras"],
        "",
    ]  # fmt: skip
    corte_depois = sum(1 for c in principais if c.get("corte_depois_da_data"))
    for r in t["regras"]:
        linhas.append("- " + r.format(corte=corte, spread=spread, corte_depois=i(corte_depois)))
    nc = n["nao_calculaveis"]
    plano = sum(v for k, v in nc["mscore"]["motivos"].items() if k.startswith("plano_de_contas"))
    e3 = n["emenda_3"]
    mc = n["marcas"]
    linhas += ["", t["h_escolhas"], "", t["escolhas_intro"], ""]
    for r in t["escolhas"]:
        linhas.append(
            "- " + r.format(p=i(int(round(100 * n["regras"]["percentil"]))), md=i(mc["dfc_md"]), plano=i(plano),
                            j601=i(mc["juros_pagos_6_01"]), j603=i(mc["juros_pagos_6_03"]), e3=i(e3["casos"]),
                            cpc06=i(mc["cpc06"]))
        )  # fmt: skip

    # Taxa de alerta por ano
    linhas += ["", t["h_taxa"], "", t["taxa_nf"], "", t["col_taxa_nf"].format(corte=corte), "|" + " --- |" * 9]
    tot = dict.fromkeys(("amostra", "avaliadas", "em_alerta", "bm", "bc"), 0)
    ps = n["por_sinal"]["nf"]
    tot_s = {k: [0, 0] for k in ps}
    for ano, v in n["taxa"]["nf"].items():
        b = n["taxa"]["nf_boba"][ano]
        cel = []
        for k in ("alerta_mscore", "alerta_dpo", "alerta_juro"):
            x = ps[k][ano]
            tot_s[k][0] += x["alertas"]
            tot_s[k][1] += x["calculaveis"]
            cel.append(f"{i(x['alertas'])} / {i(x['calculaveis'])}")
        taxa = pct(v["em_alerta"] / v["avaliadas"], lang) if v["avaliadas"] else "—"
        tb = pct(b["em_alerta"] / b["avaliadas"], lang) if b["avaliadas"] else "—"
        linhas.append(f"| {ano} | {i(v['amostra'])} | {i(v['avaliadas'])} | {i(v['em_alerta'])} | {taxa} | "
                      + " | ".join(cel) + f" | {tb} |")  # fmt: skip
        for k in ("amostra", "avaliadas", "em_alerta"):
            tot[k] += v[k]
        tot["bm"] += b["em_alerta"]
        tot["bc"] += b["avaliadas"]
    cel = [f"{i(tot_s[k][0])} / {i(tot_s[k][1])}" for k in ("alerta_mscore", "alerta_dpo", "alerta_juro")]
    linhas.append(
        f"| **{t['total']}** | {i(tot['amostra'])} | {i(tot['avaliadas'])} | {i(tot['em_alerta'])} | "
        f"{pct(tot['em_alerta'] / tot['avaliadas'], lang)} | "
        + " | ".join(cel)
        + f" | {pct(tot['bm'] / tot['bc'], lang)} |"
    )
    linhas += ["", t["taxa_fin"], "", t["col_taxa_fin"], "|" + " --- |" * 6]
    tot = dict.fromkeys(("amostra", "avaliadas", "em_alerta", "bm", "bc"), 0)
    for ano, v in n["taxa"]["fin"].items():
        b = n["taxa"]["fin_boba"][ano]
        taxa = pct(v["em_alerta"] / v["avaliadas"], lang) if v["avaliadas"] else "—"
        tb = pct(b["em_alerta"] / b["avaliadas"], lang) if b["avaliadas"] else "—"
        linhas.append(f"| {ano} | {i(v['amostra'])} | {i(v['avaliadas'])} | {i(v['em_alerta'])} | {taxa} | {tb} |")
        for k in ("amostra", "avaliadas", "em_alerta"):
            tot[k] += v[k]
        tot["bm"] += b["em_alerta"]
        tot["bc"] += b["avaliadas"]
    linhas.append(
        f"| **{t['total']}** | {i(tot['amostra'])} | {i(tot['avaliadas'])} | {i(tot['em_alerta'])} | "
        f"{pct(tot['em_alerta'] / tot['avaliadas'], lang)} | {pct(tot['bm'] / tot['bc'], lang)} |"
    )

    # Casos acertáveis
    linhas += ["", t["h_casos"], "", t["casos_intro"].format(n=i(len(principais))), "", t["col_casos"],
               "|" + " --- |" * 9]  # fmt: skip
    for c in principais:
        linhas.append(
            f"| {nome(c)} | {c['cd_cvm']} | {periodo(c)} | {data(c['data_publica'], lang)} | "
            f"{anos(c['anos_avaliados'])} | {anos(c['anos_em_alerta'])} | {fora(c)} | {sn(c['acertado'])} | "
            f"{sn(c['acertado_boba'])} |"
        )
    linhas += ["", t["detalhe_intro"].format(corte=corte, spread=spread), "", t["col_detalhe"], "|" + " --- |" * 7]
    for c in principais:
        for r in c["detalhe"]:
            falta = None
            if r["mscore"] is None and r["mscore_motivo"]:
                partes = r["mscore_motivo"].split(":", 1)
                falta = partes[1] if partes[0] == "componente_nao_calculavel" else None
            linhas.append(
                f"| `{c['caso_id']}` | {r['exercicio']} | {sinal(r['mscore'], r['alerta_mscore'], 2, falta)} | "
                f"{sinal(r['dpo'], r['alerta_dpo'])} | {sinal(r['juro'], r['alerta_juro'])} | "
                f"{sn(r['em_alerta'])} | {sn(r['alerta_boba'])} |"
            )

    # Alarmes por acerto
    linhas += ["", t["h_alarmes"], "", t["alarmes_intro"].format(obs=i(len(n["observacao"]))), "", t["col_alarmes"],
               "|" + " --- |" * 6]  # fmt: skip
    for grupo, chave in (("nf", "nf"), ("nf", "nf_boba"), ("fin", "fin"), ("fin", "fin_boba")):
        a = al[chave]
        x = d(a["alarmes_por_acerto"]) if a["alarmes_por_acerto"] is not None else t["nao_calc"]
        regra = t["boba"] if chave.endswith("boba") else t["sinais"]
        linhas.append(f"| {t[grupo]} | {regra} | {i(a['empresas_avaliadas'])} | {i(a['empresas_em_alerta'])} | "
                      f"{i(a['casos_acertados'])} | {x} |")  # fmt: skip

    # Previsões
    ame = next(c for c in n["casos"] if c["caso_id"] == "americanas")
    r = ame["detalhe"][-1]
    linhas += ["", t["h_previsoes"], ""]
    linhas.append(
        t["prev_ame"].format(
            ano=r["exercicio"],
            m=d(r["mscore"], 2) if r["mscore"] is not None else t["nc"],
            alerta_m=t["alerta"] if r["alerta_mscore"] else t["sem_alerta"],
            alerta_dpo=t["alerta"] if r["alerta_dpo"] else t["sem_alerta"],
            alerta_juro=t["alerta"] if r["alerta_juro"] else t["sem_alerta"],
            intercepto=d(INTERCEPTO, 2),
        )
    )
    linhas += ["", t["col_comp"], "| --- | --- | --- |"]
    for comp, v in r["componentes"].items():
        contrib = d(COEFICIENTES[comp] * v, 2) if v is not None else t["nc"]
        linhas.append(f"| {comp} | {d(v, 2) if v is not None else t['nc']} | {contrib} |")
    irb = next(c for c in n["casos"] if c["caso_id"] == "irb")
    p18, p19 = n["previsoes"]["irb"]
    lim = n["previsoes"]["limite_fin"].get(str(p18["exercicio"]))
    linhas += [
        "",
        t["prev_irb"].format(
            dt2019=data(p19["dt_receb"], lang),
            data_irb=data(irb["data_publica"], lang),
            ano=p18["exercicio"],
            p=d(p18["peso_nao_recorrente"], 3) if p18["peso_nao_recorrente"] is not None else t["nc"],
            lim=d(lim, 3) if lim is not None else t["nc"],
            alerta=t["alerta"] if p18["alerta"] else t["sem_alerta"],
        ),
    ]

    # Secundárias
    e1 = n["emenda_1"]
    linhas += ["", t["h_secundarias"], ""]
    linhas.append("- " + t["emenda_1"].format(data=data("2023-01-11", lang), r=sn(e1["acertado"]),
                                              anos=anos(e1["anos_em_alerta"]), rb=sn(e1["acertado_boba"])))  # fmt: skip
    linhas.append(
        "- " + t["emenda_3_intro"].format(alerta=i(e3["em_alerta"]), com_dfp=i(e3["com_dfp"]), boba=i(e3["alerta_boba"]),
                                          sem=i(e3["casos"] - e3["com_dfp"]))
    )  # fmt: skip
    linhas += ["", t["col_e3"], "|" + " --- |" * 5]
    for c in n["casos"]:
        if "emenda_3" not in c or c["emenda_3"]["exercicio"] is None:
            continue
        x = c["emenda_3"]
        linhas.append(f"| {nome(c)} | {data(c['data_publica'], lang)} | {x['exercicio']} | {sn(x['em_alerta'])} | "
                      f"{sn(x['alerta_boba'])} |")  # fmt: skip
    sec = n["secundaria"]
    linhas += ["", "- " + t["emenda_9_intro"].format(
        a2a=i(sec["2a"]["acertados"]), c2a=i(sec["2a"]["casos"]), e2a=i(sec["2a"]["efetivos"]),
        b2a=i(sec["2a"]["acertados_boba"]), a2b=i(sec["2b"]["acertados"]), c2b=i(sec["2b"]["casos"]),
        e2b=i(sec["2b"]["efetivos"]), b2b=i(sec["2b"]["acertados_boba"]))]  # fmt: skip
    linhas += ["", t["col_sec"], "|" + " --- |" * 9]
    for parte in ("2a", "2b"):
        for c in n["casos"]:
            if c["parte_secundaria"] != parte:
                continue
            linhas.append(
                f"| {nome(c)} | {parte} | {periodo(c)} | {data(c['data_publica'], lang)} | "
                f"{anos(c['anos_avaliados'])} | {anos(c['anos_em_alerta'])} | {fora(c)} | {sn(c['acertado'])} | "
                f"{sn(c['acertado_boba'])} |"
            )

    # Observação
    linhas += ["", t["h_obs"], "", t["obs_intro"], "", t["col_obs"], "|" + " --- |" * 8]
    for o in n["observacao"]:
        per = f"{o['inicio']}–{o['fim']}" if o["inicio"] else "—"
        linhas.append(
            f"| {o['empresa']} | {o['cd_cvm']} | {data(o['data_publica'], lang)} | {per} | {anos(o['anos_com_dfp_antes'])} | "
            f"{anos(o['anos_na_amostra'])} | {anos(o['anos_sem_receita'])} | {anos(o['anos_em_alerta'])} |"
        )

    # Não calculável
    linhas += [
        "",
        t["h_nc"],
        "",
        t["nc_intro"].format(sem_pen=i(mc["sem_penultimo"])),
        "",
        t["col_nc"],
        "| --- | --- | --- | --- |",
    ]

    def nome_sinal(k: str) -> str:
        return SINAIS[k][0 if lang == "pt" else 1] if k in SINAIS else k

    for k, v in nc.items():
        linhas.append(
            f"| {nome_sinal(k)} | {i(v['empresa_anos'])} | {i(v['calculaveis'])} | {i(v['nao_calculaveis'])} |"
        )
    linhas += ["", t["col_nc_motivo"], "| --- | --- | --- |"]
    for k, v in nc.items():
        for m, q in v["motivos"].items():
            linhas.append(f"| {nome_sinal(k)} | {motivo(m, lang)} | {i(q)} |")

    linhas += ["", t["h_marcas"], "", t["marcas"].format(dep=i(mc["depreciacao_combinada"]), cpc06=i(mc["cpc06"]),
                                                          md=i(mc["dfc_md"]))]  # fmt: skip
    linhas += ["", t["h_nao_feito"], ""] + ["- " + x for x in t["nao_feito"]]
    return "\n".join(linhas) + "\n"
