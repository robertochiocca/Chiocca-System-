"""Textos de docs/resultados.md (PT) e docs/en/results.md (EN), montados de docs/resultados_numeros.json.

Uma fonte de números, dois textos (PROMPT.md, projeto bilíngue). Nenhum número é escrito à mão aqui: todos
vêm do JSON gerado por chiocca.relatorio_resultados. Os termos em inglês seguem glossario_pt_en.yaml.
"""

from __future__ import annotations

from typing import Any

from chiocca.corte import data_corte
from chiocca.formato import data, decimal, inteiro, pct
from chiocca.sinais.mscore import COEFICIENTES, INTERCEPTO

NF, FIN = "nao_financeira", "financeira"

# Contas da tabela das duas leituras da Americanas: (PT, EN), com o código da CVM.
CONTAS_TABELA = {
    "receita_liquida": ("Receita líquida (3.01)", "Net revenue (3.01)"),
    "custo_vendas": ("Custo dos bens e/ou serviços vendidos (3.02)", "Cost of sales (3.02)"),
    "resultado_bruto": ("Resultado bruto (3.03)", "Gross profit (3.03)"),
    "contas_a_receber": ("Contas a receber (1.01.03)", "Trade receivables (1.01.03)"),
    "estoques": ("Estoques (1.01.04)", "Inventories (1.01.04)"),
    "ativo_circulante": ("Ativo circulante (1.01)", "Current assets (1.01)"),
    "imobilizado": ("Imobilizado (1.02.03)", "Property, plant and equipment (1.02.03)"),
    "ativo_total": ("Ativo total (conta 1)", "Total assets (account 1)"),
    "fornecedores": ("Fornecedores (2.01.02)", "Trade payables (2.01.02)"),
    "passivo_circulante": ("Passivo circulante (2.01)", "Current liabilities (2.01)"),
    "emprestimos_cp": ("Empréstimos e financiamentos, curto prazo (2.01.04)", "Borrowings, current (2.01.04)"),
    "emprestimos_lp": ("Empréstimos e financiamentos, longo prazo (2.02.01)", "Borrowings, non-current (2.02.01)"),
    "despesas_vendas": ("Despesas com vendas (3.04.01)", "Selling expenses (3.04.01)"),
    "despesas_gerais_adm": ("Despesas gerais e administrativas (3.04.02)",
                            "General and administrative expenses (3.04.02)"),
    "despesas_financeiras": ("Despesas financeiras (3.06.02)", "Finance costs (3.06.02)"),
    "lucro_operacoes_continuadas": ("Resultado líquido das operações continuadas (3.09)",
                                    "Profit from continuing operations (3.09)"),
    "lucro_liquido": ("Lucro líquido (3.11)", "Net income (3.11)"),
    "caixa_operacional": ("Caixa operacional sem juros pagos (seção 6.01)",
                          "Operating cash flow excluding interest paid (section 6.01)"),
    "depreciacao": ("Depreciação, linhas da DFC (seção 6.01.01)", "Depreciation, cash flow lines (section 6.01.01)"),
}  # fmt: skip

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
        "titulo": "# Resultados do estudo",
        "gerado": "Gerado por `python -m chiocca.relatorio_resultados` a partir de `resultados/sinais_empresa_ano.csv` (fora do git), que sai de `python -m chiocca.sinais_amostra`. Não edite à mão: um teste compara este arquivo com a saída do script. Só aparecem números agregados, os casos do gabarito, que são públicos, e a tabela dos casos em observação (emenda 8). Nenhuma lista de empresas em alerta sai deste repositório.",
        "execucao": "Sinais calculados em {data} com o código do commit `{commit}`. O período de teste (exercícios de 2017 a 2023, pré-registro, seção 8) foi aberto em {abertura}, com o commit `{commit_abertura}`, na primeira execução da amostra inteira. As regras foram aplicadas como estão no pré-registro, sem nenhum corte alternativo testado, e o resultado é mostrado como saiu (seção 9). Depois de ver os resultados, entrou só a emenda 11, que corrige a métrica de alarmes por acerto e não muda sinal, corte ou caso.",
        "h_resumo": "## Números principais",
        "amostra": "**Amostra, 2010 a 2023:** {nf} empresa-anos de não financeiras com receita e {fin} de financeiras, de {empresas} empresas. Ficaram de fora {sem_receita} empresa-anos de não financeiras sem receita (seção 2) e {sem_versao} sem versão da época (emenda 5).",
        "acerto": "**Acerto (seção 5):** {acertados} de {acertaveis} casos acertáveis. Depois da exclusão das empresas sem receita, continuam acertáveis {efetivos} de {acertaveis} (emenda 9). Contando todos os {casos} casos do gabarito, são {acertados} de {casos}, com teto de {acertaveis} de {casos} no estudo principal.",
        "acerto_boba": "**Regra boba (seção 7):** {acertados_boba} de {acertaveis} casos acertáveis.",
        "alarmes_nf": "**Alarmes por acerto, não financeiras (emenda 11, numerador e acertos na mesma janela):** no período de teste, 2017 a 2023, ({e} − {a}) ÷ {a} = {x}, com {e} empresas em alerta de {aval} avaliadas e {a} casos acertados por alerta dentro do período; no período inteiro, 2010 a 2023, ({ei} − {ai}) ÷ {ai} = {xi}, com {ei} empresas em alerta de {avali}. Com a regra boba: ({eb} − {ab}) ÷ {ab} = {xb} no período de teste e ({ebi} − {abi}) ÷ {abi} = {xbi} no período inteiro.",
        "alarmes_fin": "**Financeiras:** {e} empresas em alerta de {aval} avaliadas no período de teste e {ei} de {avali} no período inteiro. Alarmes por acerto não calculável: nenhum caso acertável é financeira. Com a regra boba: {eb} e {ebi} empresas em alerta.",
        "teste_acertados": "**Versão da emenda 10, inconsistente** (empresas em alerta no período de teste, acertos de todo o período): {x10} com os sinais e {xb10} com a regra boba. Fica registrada; a emenda 11 a substitui.",
        "taxa_total": "**Taxa de alerta, 2010 a 2023, somando os exercícios:** não financeiras, {em} empresas em alerta de {aval} avaliadas ({p}); financeiras, {emf} de {avalf} ({pf}).",
        "comparacao": "**Lado a lado, sem declarar vencedor (emenda 11):** acerto, {a} casos com os sinais e {b} com a regra boba; acertos por alerta no período de teste, {at} e {bt}; alarmes por acerto nas não financeiras, {x} e {y} no período de teste e {xi} e {yi} no período inteiro.",
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
        "escolhas_intro": "O pré-registro não desce a estes detalhes. Cada um foi fixado antes de rodar a amostra, sem testar alternativa. A emenda 11 aceitou as escolhas como registradas; a DFC pelo método direto sem linha de depreciação fica como limitação.",
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
        "h_alarmes": "## Alarmes por acerto e regra boba",
        "alarmes_intro": "Emenda 11: (empresas em alerta − casos acertados) ÷ casos acertados, com numerador e acertos na mesma janela. No período de teste entram só os casos acertados por alerta em exercício de 2017 a 2023; no período inteiro, todos. A versão da emenda 10 (empresas do período de teste, acertos de todo o período) fica na tabela, identificada como inconsistente. As {obs} empresas dos casos em observação ficam fora. A emenda 11 foi escrita depois de ver os resultados da Fase 2.",
        "col_alarmes": "| Grupo | Regra | Janela | Empresas avaliadas | Empresas em alerta | Casos acertados | Alarmes por acerto |",
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
        "h_nao_feito": "## O que ficou de fora",
        "nao_feito": [
            "Dados trimestrais (ITR), que seriam necessários para alcançar o IRB antes da data pública (pré-registro, seção 4.2).",
            "Qualquer mudança de regra, corte ou caso: depende de novo pré-registro assinado.",
        ],
        "janelas": {
            "teste": "Teste, 2017–2023 (emenda 11)",
            "inteiro": "Inteiro, 2010–2023 (emenda 11)",
            "emenda_10": "Emenda 10 (inconsistente)",
        },
        "h_duas": "## Duas leituras da Americanas (exercício de 2021)",
        "duas_intro": 'Original: DFP de 2021, versão {vo}, entregue em {do}, a versão da época. Reapresentada: comparativo da DFP de 2022, versão {vr}, entregue em {dr}, depois do corte de {cr}; é uma leitura posterior, não "como era na época". A DFP de 2022 não traz 2020, e a reapresentação ajustou os efeitos anteriores a 2021 no saldo de abertura, sem separar por ano (emenda 1). Por isso t−1 é o mesmo nas duas leituras: o comparativo da DFP de 2021.',
        "col_duas": "| Item | Original | Reapresentada |",
        "duas_itens": {
            "m": "M",
            "alerta_m": "Alerta do M-score",
            "dpo": "Salto do DPO (dias)",
            "alerta_dpo": "Alerta do DPO",
            "juro": "Juro implícito − CDI médio (p.p.)",
            "alerta_juro": "Alerta do juro implícito",
            "lsc": "Lucro sem caixa (do ativo médio)",
        },
        "duas_contas_intro": "**Contas de 2021 nas duas leituras, em R$ milhões:**",
        "col_duas_contas": "| Conta | Original | Reapresentada | Diferença |",
        "duas_texto": "Nas duas leituras o M fica acima de {corte}: {mo} e {mr}. Na reapresentada, o GMI vai de {go} para {gr}, o LVGI de {lo} para {lr} e o juro implícito de {jo} para {jr} p.p. acima do CDI médio.",
        "h_rob": "## Robustez com valores neutros (pré-registro, seção 4.1)",
        "rob_intro": "Teste de robustez, fora da conta principal. AQI, DEPI e SGAI não calculáveis por conta ausente ou denominador zero recebem o valor neutro 1, como no artigo de 1999; os outros componentes e motivos ficam como estão. Valores neutros usados em {usou} empresa-anos; M calculável em {mc} empresa-anos (estudo principal: {m0}); alertas do M: {am} (estudo principal: {am0}). Casos cujos exercícios em alerta mudaram: {mud}.",
        "col_lado": "| Métrica | Estudo principal | {alt} |",
        "alt_rob": "Valores neutros",
        "alt_e5": "Secundária da emenda 5",
        "lado": {
            "acertados": "Casos acertados (de {n})",
            "acertados_teste": "Acertados por alerta em 2017–2023",
            "alarmes_teste": "Alarmes por acerto, não financeiras, período de teste",
            "alarmes_inteiro": "Alarmes por acerto, não financeiras, período inteiro",
            "taxa": "Taxa de alerta das não financeiras, 2010–2023 (soma dos exercícios)",
            "2a": "Secundária 2a, acertados (de {n})",
            "2b": "Secundária 2b, acertados (de {n})",
            "b_acertados": "Regra boba: casos acertados (de {n})",
            "b_alarmes_teste": "Regra boba: alarmes por acerto, período de teste",
            "b_alarmes_inteiro": "Regra boba: alarmes por acerto, período inteiro",
        },
        "nenhum": "nenhum",
        "h_e5": "## Secundária da emenda 5 (rotulada; fora da conta principal)",
        "e5_intro": "Inclui {n} empresa-anos sem versão da época, lidas na versão disponível, entregue depois do corte: {nf} de não financeiras com receita, {fin} de financeiras e {sr} de não financeiras sem receita, que continuam fora. Os decis de cada ano foram recalculados com elas. Casos cujos exercícios em alerta mudaram: com os sinais, {mud}; com a regra boba, {mudb}.",
        "h_ficha": "## Ficha de alerta (Fase 4)",
        "ficha_intro": "`python -m chiocca.ficha <código CVM> <exercício> [pt|en]` gera a ficha de qualquer empresa-ano a partir de `resultados/`, que fica fora do git. Exemplo com um caso do gabarito, que é público:",
        "h_desc": "## Explicação depois do resultado, não teste",
        "desc_intro": "Análise descritiva feita depois de ver os resultados. Não muda regra, corte ou caso, e não serve como teste: as perguntas e as comparações foram escolhidas sabendo o resultado.",
        "desc_a_titulo": "**(a) SGI e DSRI da Americanas em 2021.**",
        "desc_a": [
            "Fonte: ata da assembleia geral extraordinária da B2W (código 20990, depois Americanas S.A.) de 10/06/2021, que aprovou a cisão parcial da Lojas Americanas (código 8087) com todos os ativos operacionais e passivos relacionados vertidos para a B2W pelo valor contábil de 31/12/2020; o fato relevante de 28/04/2021 diz que as variações patrimoniais a partir dessa data-base também ficam com a B2W. Documentos e hashes em docs/fontes.md.",
            "SGI: o comparativo de 2020 na DFP de 2021 é só da B2W, com receita de R$ {r20} milhões; a receita de 2021 é de R$ {r21} milhões. A Lojas Americanas consolidada, que já incluía a B2W, teve receita de R$ {rl} milhões em 2020. O SGI de {sgi} vem dessa troca de perímetro.",
            "DSRI: contas a receber ÷ receita foi de {x21} em 2021, {x20} na B2W em 2020 e {xl} na Lojas Americanas em 2020. O DSRI de {dsri} não se explica só pela fusão, porque a razão de 2021 fica acima das duas.",
            "Trocando t−1 pela DFP consolidada de 2020 da Lojas Americanas (perímetros não idênticos): SGI {sgil}, DSRI {dsril}, AQI {aqil} e M = {ml}, {alml}. Sem o efeito do SGI, o M continuaria acima de {corte}, puxado por DSRI e AQI.",
        ],
        "desc_b_titulo": "**(b) Quanto da taxa de alerta vem só do juro implícito.** Não financeiras; empresas por exercício.",
        "col_desc_b": "| Exercício | Avaliadas | Em alerta | Só pelo juro implícito | Parte dos alertas | Taxa de alerta sem o juro implícito |",
        "desc_b_texto": "De 2010 a 2018, {pa} dos alertas vêm só do juro implícito; de 2019 a 2023, depois da adoção do CPC 06 (R2), {pd}. Sem o juro implícito, a taxa de alerta seria {ta} e {td}, contra {ta0} e {td0} com ele.",
        "desc_c_titulo": "**(c) Casos que perderam o M-score por falta do DEPI.**",
        "desc_c": "Na amostra, {m0} empresa-anos de não financeiras ficaram sem M; em {cd}, o DEPI está entre os componentes que faltaram, e em {sd} ele é o único ({md} delas com DFC pelo método direto). Dos {n} casos acertáveis, {k} ficaram sem M em todos os exercícios avaliados por causa do DEPI, e em {ks} deles o DEPI foi o único componente que faltou. Com o valor neutro do teste de robustez, o M dispararia em {kn} desses {k} casos; {kv} deles não tinha sido acertado no estudo principal. Na análise secundária, outros {ksec} casos ficaram sem M com o DEPI entre os componentes que faltaram.",
        "col_desc_c": "| Caso | Exercícios | DFC pelo método direto | M com DEPI neutro | Acertado no estudo principal |",
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
        "titulo": "# Study results",
        "gerado": "Generated by `python -m chiocca.relatorio_resultados` from `resultados/sinais_empresa_ano.csv` (not in git), which comes from `python -m chiocca.sinais_amostra`. Do not edit by hand: a test compares this file with the script output. Only aggregate numbers, the ground-truth cases, which are public, and the table of cases under observation (amendment 8) appear here. No list of companies in alert leaves this repository.",
        "execucao": "Signals computed on {data} with the code at commit `{commit}`. The test period (fiscal years 2017 to 2023, pre-registration, section 8) was opened on {abertura}, at commit `{commit_abertura}`, in the first run over the whole sample. The rules were applied exactly as pre-registered, with no alternative cut-off tested, and the result is shown as it came out (section 9). After seeing the results, only amendment 11 was added: it corrects the false-alarms-per-detected-case metric and changes no signal, cut-off or case.",
        "h_resumo": "## Key numbers",
        "amostra": "**Sample, 2010 to 2023:** {nf} company-years of non-financial companies with revenue and {fin} of financial companies, from {empresas} companies. Left out: {sem_receita} company-years of non-financial companies with no revenue (section 2) and {sem_versao} with no point-in-time version (amendment 5).",
        "acerto": "**Detection (section 5):** {acertados} of {acertaveis} detectable cases. After excluding companies with no revenue, {efetivos} of {acertaveis} remain detectable (amendment 9). Counting all {casos} ground-truth cases, it is {acertados} of {casos}, with a ceiling of {acertaveis} of {casos} in the main study.",
        "acerto_boba": "**Naive baseline rule (section 7):** {acertados_boba} of {acertaveis} detectable cases.",
        "alarmes_nf": "**False alarms per detected case, non-financial (amendment 11, numerator and detections in the same window):** in the test period, 2017 to 2023, ({e} − {a}) ÷ {a} = {x}, with {e} companies in alert out of {aval} evaluated and {a} cases detected by an alert within that period; over the whole period, 2010 to 2023, ({ei} − {ai}) ÷ {ai} = {xi}, with {ei} companies in alert out of {avali}. With the naive baseline rule: ({eb} − {ab}) ÷ {ab} = {xb} in the test period and ({ebi} − {abi}) ÷ {abi} = {xbi} over the whole period.",
        "alarmes_fin": "**Financial companies:** {e} companies in alert out of {aval} evaluated in the test period and {ei} of {avali} over the whole period. False alarms per detected case not computable: no detectable case is a financial company. With the naive baseline rule: {eb} and {ebi} companies in alert.",
        "teste_acertados": "**Amendment 10 version, inconsistent** (companies in alert in the test period, detections from the whole period): {x10} with the signals and {xb10} with the naive baseline rule. It stays on record; amendment 11 replaces it.",
        "taxa_total": "**Alert rate, 2010 to 2023, summed over fiscal years:** non-financial, {em} companies in alert out of {aval} evaluated ({p}); financial, {emf} of {avalf} ({pf}).",
        "comparacao": "**Side by side, with no winner declared (amendment 11):** detection, {a} cases with the signals and {b} with the naive baseline rule; detections by an alert in the test period, {at} and {bt}; false alarms per detected case among non-financial companies, {x} and {y} in the test period and {xi} and {yi} over the whole period.",
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
        "escolhas_intro": "The pre-registration does not go down to these details. Each was fixed before running the sample, with no alternative tested. Amendment 11 accepted the choices as recorded; the direct-method cash flow statement with no depreciation line stays as a limitation.",
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
        "h_alarmes": "## False alarms per detected case and naive baseline rule",
        "alarmes_intro": "Amendment 11: (companies in alert − detected cases) ÷ detected cases, with numerator and detections in the same window. The test period counts only cases detected by an alert in a fiscal year from 2017 to 2023; the whole period counts all of them. The amendment 10 version (companies from the test period, detections from the whole period) stays in the table, labeled as inconsistent. The {obs} companies of the cases under observation are left out. Amendment 11 was written after seeing the Phase 2 results.",
        "col_alarmes": "| Group | Rule | Window | Evaluated companies | Companies in alert | Detected cases | False alarms per detected case |",
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
        "h_nao_feito": "## Left out",
        "nao_feito": [
            "Quarterly data (ITR), which would be needed to reach IRB before the public date (pre-registration, section 4.2).",
            "Any change of rule, cut-off or case: it requires a new signed pre-registration.",
        ],
        "janelas": {
            "teste": "Test, 2017–2023 (amendment 11)",
            "inteiro": "Whole period, 2010–2023 (amendment 11)",
            "emenda_10": "Amendment 10 (inconsistent)",
        },
        "h_duas": "## Two readings of Americanas (fiscal year 2021)",
        "duas_intro": "Original: the 2021 DFP, version {vo}, filed on {do}, the point-in-time version. Restated: the prior-year column of the 2022 DFP, version {vr}, filed on {dr}, after the cut-off date of {cr}; it is a later reading, not point-in-time. The 2022 DFP does not include 2020, and the restatement adjusted the effects before 2021 in the opening balance, without a year-by-year split (amendment 1). That is why t−1 is the same in both readings: the prior-year column of the 2021 DFP.",
        "col_duas": "| Item | Original | Restated |",
        "duas_itens": {
            "m": "M",
            "alerta_m": "M-score alert",
            "dpo": "DPO jump (days)",
            "alerta_dpo": "DPO alert",
            "juro": "Implied interest rate − average CDI (p.p.)",
            "alerta_juro": "Implied interest alert",
            "lsc": "Accruals (of average total assets)",
        },
        "duas_contas_intro": "**2021 accounts in both readings, in R$ million:**",
        "col_duas_contas": "| Account | Original | Restated | Difference |",
        "duas_texto": "In both readings M is above {corte}: {mo} and {mr}. In the restated reading, GMI goes from {go} to {gr}, LVGI from {lo} to {lr} and the implied interest rate from {jo} to {jr} p.p. above the average CDI rate.",
        "h_rob": "## Robustness test with neutral values (pre-registration, section 4.1)",
        "rob_intro": "Robustness test, outside the main count. AQI, DEPI and SGAI that were not computable because of a missing account or a zero denominator get the neutral value 1, as in the 1999 article; the other components and reasons stay as they are. Neutral values used in {usou} company-years; M computable in {mc} company-years (main study: {m0}); M-score alerts: {am} (main study: {am0}). Cases whose fiscal years in alert changed: {mud}.",
        "col_lado": "| Metric | Main study | {alt} |",
        "alt_rob": "Neutral values",
        "alt_e5": "Amendment 5 secondary analysis",
        "lado": {
            "acertados": "Detected cases (of {n})",
            "acertados_teste": "Detected by an alert in 2017–2023",
            "alarmes_teste": "False alarms per detected case, non-financial, test period",
            "alarmes_inteiro": "False alarms per detected case, non-financial, whole period",
            "taxa": "Alert rate of non-financial companies, 2010–2023 (sum over fiscal years)",
            "2a": "Secondary part 2a, detected (of {n})",
            "2b": "Secondary part 2b, detected (of {n})",
            "b_acertados": "Naive baseline rule: detected cases (of {n})",
            "b_alarmes_teste": "Naive baseline rule: false alarms per detected case, test period",
            "b_alarmes_inteiro": "Naive baseline rule: false alarms per detected case, whole period",
        },
        "nenhum": "none",
        "h_e5": "## Amendment 5 secondary analysis (labeled; outside the main count)",
        "e5_intro": "It includes {n} company-years with no point-in-time version, read from the available version, filed after the cut-off date: {nf} non-financial with revenue, {fin} financial and {sr} non-financial with no revenue, which stay out. The deciles of each year were recomputed with them. Cases whose fiscal years in alert changed: with the signals, {mud}; with the naive baseline rule, {mudb}.",
        "h_ficha": "## Alert sheet (Phase 4)",
        "ficha_intro": "`python -m chiocca.ficha <CVM code> <fiscal year> [pt|en]` produces the sheet for any company-year from `resultados/`, which is not in git. Example with a ground-truth case, which is public:",
        "h_desc": "## Explanation after the result, not a test",
        "desc_intro": "Descriptive analysis done after seeing the results. It changes no rule, cut-off or case, and it does not count as a test: the questions and comparisons were chosen knowing the result.",
        "desc_a_titulo": "**(a) Americanas' SGI and DSRI in 2021.**",
        "desc_a": [
            "Source: minutes of the B2W extraordinary shareholders' meeting (CVM code 20990, later Americanas S.A.) of 2021-06-10, which approved the partial spin-off of Lojas Americanas (CVM code 8087), with all its operating assets and related liabilities transferred to B2W at their book value as of 2020-12-31; the material fact notice of 2021-04-28 says that equity changes from that base date also go to B2W. Documents and hashes in docs/en/sources.md.",
            "SGI: the 2020 comparative in the 2021 DFP is B2W alone, with net revenue of R${r20} million; 2021 net revenue is R${r21} million. Lojas Americanas on a consolidated basis, which already included B2W, had net revenue of R${rl} million in 2020. The SGI of {sgi} comes from this change of perimeter.",
            "DSRI: trade receivables ÷ net revenue was {x21} in 2021, {x20} at B2W in 2020 and {xl} at Lojas Americanas in 2020. The DSRI of {dsri} is not explained by the combination alone, because the 2021 ratio is above both.",
            "Replacing t−1 with the 2020 consolidated DFP of Lojas Americanas (perimeters not identical): SGI {sgil}, DSRI {dsril}, AQI {aqil} and M = {ml}, {alml}. Without the SGI effect, M would still be above {corte}, driven by DSRI and AQI.",
        ],
        "desc_b_titulo": "**(b) How much of the alert rate comes from the implied interest rate alone.** Non-financial companies; companies per fiscal year.",
        "col_desc_b": "| Fiscal year | Evaluated | In alert | Implied interest only | Share of alerts | Alert rate without implied interest |",
        "desc_b_texto": "From 2010 to 2018, {pa} of the alerts come from the implied interest rate alone; from 2019 to 2023, after CPC 06 (R2) was adopted, {pd}. Without the implied interest rate, the alert rate would be {ta} and {td}, against {ta0} and {td0} with it.",
        "desc_c_titulo": "**(c) Cases that lost the M-score because DEPI was missing.**",
        "desc_c": "In the sample, {m0} non-financial company-years have no M; in {cd}, DEPI is among the missing components, and in {sd} it is the only one ({md} of them with a direct-method cash flow statement). Of the {n} detectable cases, {k} had no M in any evaluated fiscal year because of DEPI, and in {ks} of them DEPI was the only missing component. With the neutral value of the robustness test, M would fire in {kn} of these {k} cases; {kv} of them had not been detected in the main study. In the secondary analysis, another {ksec} cases had no M with DEPI among the missing components.",
        "col_desc_c": "| Case | Fiscal years | Direct-method cash flow statement | M with neutral DEPI | Detected in the main study |",
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

    def x_(a: dict[str, Any]) -> str:
        return d(a["alarmes_por_acerto"]) if a["alarmes_por_acerto"] is not None else t["nao_calc"]

    nf_, nfb, fi_, fib = al["nf"], al["nf_boba"], al["fin"], al["fin_boba"]
    linhas += [
        "- " + t["amostra"].format(nf=i(am[NF]), fin=i(am[FIN]), empresas=i(n["marcas"]["empresas"]),
                                   sem_receita=i(am["fora_sem_receita"]), sem_versao=i(am["fora_sem_versao_da_epoca"])),
        "- " + t["acerto"].format(acertados=i(ac["acertados"]), acertaveis=i(ac["acertaveis"]),
                                  efetivos=i(ac["acertaveis_efetivos"]), casos=i(ac["casos_no_gabarito"])),
        "- " + t["acerto_boba"].format(acertados_boba=i(ac["acertados_boba"]), acertaveis=i(ac["acertaveis"])),
        "- " + t["alarmes_nf"].format(
            e=i(nf_["teste"]["empresas_em_alerta"]), aval=i(nf_["teste"]["empresas_avaliadas"]),
            a=i(nf_["teste"]["casos_acertados"]), x=x_(nf_["teste"]),
            ei=i(nf_["inteiro"]["empresas_em_alerta"]), avali=i(nf_["inteiro"]["empresas_avaliadas"]),
            ai=i(nf_["inteiro"]["casos_acertados"]), xi=x_(nf_["inteiro"]),
            eb=i(nfb["teste"]["empresas_em_alerta"]), ab=i(nfb["teste"]["casos_acertados"]), xb=x_(nfb["teste"]),
            ebi=i(nfb["inteiro"]["empresas_em_alerta"]), abi=i(nfb["inteiro"]["casos_acertados"]),
            xbi=x_(nfb["inteiro"])),
        "- " + t["alarmes_fin"].format(e=i(fi_["teste"]["empresas_em_alerta"]), aval=i(fi_["teste"]["empresas_avaliadas"]),
                                       ei=i(fi_["inteiro"]["empresas_em_alerta"]),
                                       avali=i(fi_["inteiro"]["empresas_avaliadas"]),
                                       eb=i(fib["teste"]["empresas_em_alerta"]),
                                       ebi=i(fib["inteiro"]["empresas_em_alerta"])),
        "- " + t["teste_acertados"].format(x10=x_(nf_["emenda_10"]), xb10=x_(nfb["emenda_10"])),
        "- " + t["taxa_total"].format(em=i(soma["nf"]["em"]), aval=i(soma["nf"]["aval"]),
                                      p=pct(soma["nf"]["em"] / soma["nf"]["aval"], lang),
                                      emf=i(soma["fin"]["em"]), avalf=i(soma["fin"]["aval"]),
                                      pf=pct(soma["fin"]["em"] / soma["fin"]["aval"], lang)),
        "- " + t["comparacao"].format(a=i(ac["acertados"]), b=i(ac["acertados_boba"]), at=i(ac["acertados_teste"]),
                                      bt=i(ac["acertados_boba_teste"]), x=x_(nf_["teste"]), y=x_(nfb["teste"]),
                                      xi=x_(nf_["inteiro"]), yi=x_(nfb["inteiro"])),
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
               "|" + " --- |" * 7]  # fmt: skip
    for grupo, chave in (("nf", "nf"), ("nf", "nf_boba"), ("fin", "fin"), ("fin", "fin_boba")):
        regra = t["boba"] if chave.endswith("boba") else t["sinais"]
        for janela in ("teste", "inteiro", "emenda_10"):
            a = al[chave][janela]
            linhas.append(f"| {t[grupo]} | {regra} | {t['janelas'][janela]} | {i(a['empresas_avaliadas'])} | "
                          f"{i(a['empresas_em_alerta'])} | {i(a['casos_acertados'])} | {x_(a)} |")  # fmt: skip

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

    # Duas leituras da Americanas
    lado_k = 0 if lang == "pt" else 1
    if "americanas" in n:
        a_ = n["americanas"]
        o_, r_ = a_["original"], a_["reapresentada"]
        linhas += ["", t["h_duas"], "", t["duas_intro"].format(
            vo=o_["versao"], do=data(o_["dt_receb"][:10], lang), vr=r_["versao"], dr=data(r_["dt_receb"][:10], lang),
            cr=data(data_corte("2022-12-31"), lang)), "", t["col_duas"], "| --- | --- | --- |"]  # fmt: skip

        def val(x: dict[str, Any], casas: int = 2) -> str:
            return d(x["valor"], casas) if x["valor"] is not None else t["nc"]

        it = t["duas_itens"]
        linhas.append(f"| {it['m']} | {val(o_['m'])} | {val(r_['m'])} |")
        linhas.append(f"| {it['alerta_m']} | {sn(o_['alerta_m'])} | {sn(r_['alerta_m'])} |")
        for comp in COEFICIENTES:
            linhas.append(f"| {comp} | {val(o_['componentes'][comp])} | {val(r_['componentes'][comp])} |")
        linhas.append(f"| {it['dpo']} | {val(o_['dpo'], 1)} | {val(r_['dpo'], 1)} |")
        linhas.append(f"| {it['alerta_dpo']} | {sn(o_['alerta_dpo'])} | {sn(r_['alerta_dpo'])} |")
        jo = d(o_["juro_spread"]) if o_["juro_spread"] is not None else t["nc"]
        jr = d(r_["juro_spread"]) if r_["juro_spread"] is not None else t["nc"]
        linhas.append(f"| {it['juro']} | {jo} | {jr} |")
        linhas.append(f"| {it['alerta_juro']} | {sn(o_['alerta_juro'])} | {sn(r_['alerta_juro'])} |")
        lo = pct(o_["lucro_sem_caixa"]["valor"], lang) if o_["lucro_sem_caixa"]["valor"] is not None else t["nc"]
        lr = pct(r_["lucro_sem_caixa"]["valor"], lang) if r_["lucro_sem_caixa"]["valor"] is not None else t["nc"]
        linhas.append(f"| {it['lsc']} | {lo} | {lr} |")
        linhas += ["", t["duas_contas_intro"], "", t["col_duas_contas"], "| --- | --- | --- | --- |"]
        for conta, rot in CONTAS_TABELA.items():
            vo_, vr_ = o_["contas_t"].get(conta), r_["contas_t"].get(conta)
            if vo_ is None and vr_ is None:
                continue
            fo = d(vo_ / 1e6) if vo_ is not None else t["nc"]
            fr = d(vr_ / 1e6) if vr_ is not None else t["nc"]
            dif = d((vr_ - vo_) / 1e6) if vo_ is not None and vr_ is not None else "—"
            linhas.append(f"| {rot[lado_k]} | {fo} | {fr} | {dif} |")
        linhas += ["", t["duas_texto"].format(
            corte=corte, mo=val(o_["m"]), mr=val(r_["m"]), go=val(o_["componentes"]["GMI"]),
            gr=val(r_["componentes"]["GMI"]), lo=val(o_["componentes"]["LVGI"]), lr=val(r_["componentes"]["LVGI"]),
            jo=jo, jr=jr)]  # fmt: skip

    def mudancas(m: dict[str, list[list[int]]]) -> str:
        if not m:
            return t["nenhum"]
        return "; ".join(f"`{c}`: {anos(a)} → {anos(b)}" for c, (a, b) in m.items())

    def lado_a_lado(alt: dict[str, Any], alt_boba: dict[str, Any] | None, rotulo: str) -> list[str]:
        base_s = {"acertados": ac["acertados"], "acertados_teste": ac["acertados_teste"]}
        rot = t["lado"]
        out = ["", t["col_lado"].format(alt=rotulo), "| --- | --- | --- |"]
        sec0 = n["secundaria"]
        taxa0 = soma["nf"]["em"] / soma["nf"]["aval"]
        taxa1 = alt["taxa"]["nf"]["em_alerta"] / alt["taxa"]["nf"]["avaliadas"]
        out += [
            f"| {rot['acertados'].format(n=i(ac['acertaveis']))} | {i(base_s['acertados'])} | {i(alt['acertados'])} |",
            f"| {rot['acertados_teste']} | {i(base_s['acertados_teste'])} | {i(alt['acertados_teste'])} |",
            f"| {rot['alarmes_teste']} | {x_(nf_['teste'])} | {x_(alt['alarmes']['nf']['teste'])} |",
            f"| {rot['alarmes_inteiro']} | {x_(nf_['inteiro'])} | {x_(alt['alarmes']['nf']['inteiro'])} |",
            f"| {rot['taxa']} | {pct(taxa0, lang)} | {pct(taxa1, lang)} |",
            f"| {rot['2a'].format(n=i(sec0['2a']['casos']))} | {i(sec0['2a']['acertados'])} | "
            f"{i(alt['secundaria']['2a']['acertados'])} |",
            f"| {rot['2b'].format(n=i(sec0['2b']['casos']))} | {i(sec0['2b']['acertados'])} | "
            f"{i(alt['secundaria']['2b']['acertados'])} |",
        ]
        if alt_boba is not None:
            out += [
                f"| {rot['b_acertados'].format(n=i(ac['acertaveis']))} | {i(ac['acertados_boba'])} | "
                f"{i(alt_boba['acertados'])} |",
                f"| {rot['b_alarmes_teste']} | {x_(nfb['teste'])} | {x_(alt_boba['alarmes']['nf']['teste'])} |",
                f"| {rot['b_alarmes_inteiro']} | {x_(nfb['inteiro'])} | {x_(alt_boba['alarmes']['nf']['inteiro'])} |",
            ]
        return out

    # Robustez com valores neutros
    rb = n["robustez"]
    linhas += ["", t["h_rob"], "", t["rob_intro"].format(
        usou=i(rb["usou_neutro"]), mc=i(rb["m_calculaveis"]), m0=i(nc["mscore"]["calculaveis"]),
        am=i(rb["alertas_m"]), am0=i(sum(v["alertas"] for v in n["por_sinal"]["nf"]["alerta_mscore"].values())),
        mud=mudancas(rb["mudaram"]))]  # fmt: skip
    linhas += lado_a_lado(rb["avaliacao"], None, t["alt_rob"])

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

    # Secundária da emenda 5
    if "emenda5" in n:
        e5 = n["emenda5"]
        inc = e5["incluidas"]
        linhas += [
            "",
            t["h_e5"],
            "",
            t["e5_intro"].format(
                n=i(e5["incluidas_total"]),
                nf=i(inc.get(NF, 0)),
                fin=i(inc.get(FIN, 0)),
                sr=i(inc.get("fora_sem_receita", 0)),
                mud=mudancas(e5["mudaram"]),
                mudb=mudancas(e5["mudaram_boba"]),
            ),
        ]
        linhas += lado_a_lado(e5["sinais"], e5["boba"], t["alt_e5"])

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
    # Ficha de alerta
    if "ficha_exemplo" in n:
        from chiocca.ficha import texto as texto_ficha

        linhas += ["", t["h_ficha"], "", t["ficha_intro"], ""]
        linhas += [("> " + x) if x else ">" for x in texto_ficha(n["ficha_exemplo"], lang).rstrip("\n").split("\n")]

    # Explicação depois do resultado
    linhas += ["", t["h_desc"], "", t["desc_intro"]]
    if "americanas" in n:
        a_ = n["americanas"]
        o_, b_ = a_["original"], a_["base_lasa"]

        def razao_(c: dict[str, Any]) -> float:
            return c["contas_a_receber"] / c["receita_liquida"]

        ml = b_["m"]["valor"]
        linhas += ["", t["desc_a_titulo"], ""]
        campos = dict(
            r20=d(o_["contas_t1"]["receita_liquida"] / 1e6, 0), r21=d(o_["contas_t"]["receita_liquida"] / 1e6, 0),
            rl=d(b_["contas_t1"]["receita_liquida"] / 1e6, 0), sgi=d(o_["componentes"]["SGI"]["valor"], 2),
            x21=d(razao_(o_["contas_t"]), 2), x20=d(razao_(o_["contas_t1"]), 2), xl=d(razao_(b_["contas_t1"]), 2),
            dsri=d(o_["componentes"]["DSRI"]["valor"], 2), sgil=d(b_["componentes"]["SGI"]["valor"], 2),
            dsril=d(b_["componentes"]["DSRI"]["valor"], 2), aqil=d(b_["componentes"]["AQI"]["valor"], 2),
            ml=d(ml, 2) if ml is not None else t["nc"], alml=t["alerta"] if b_["alerta_m"] else t["sem_alerta"],
            corte=corte,
        )  # fmt: skip
        linhas += ["- " + x.format(**campos) for x in t["desc_a"]]
    jb = n["descritiva"]["juro"]
    linhas += ["", t["desc_b_titulo"], "", t["col_desc_b"], "|" + " --- |" * 6]

    def linha_b(rot: str, v: dict[str, int]) -> str:
        parte = pct(v["so_juro"] / v["em_alerta"], lang) if v["em_alerta"] else "—"
        sem = pct(v["sem_juro"] / v["avaliada"], lang) if v["avaliada"] else "—"
        return f"| {rot} | {i(v['avaliada'])} | {i(v['em_alerta'])} | {i(v['so_juro'])} | {parte} | {sem} |"

    for ano, v in jb["por_ano"].items():
        linhas.append(linha_b(ano, v))
    linhas.append(linha_b("**2010–2018**", jb["antes"]))
    linhas.append(linha_b("**2019–2023**", jb["depois"]))
    an, de = jb["antes"], jb["depois"]
    linhas += ["", t["desc_b_texto"].format(
        pa=pct(an["so_juro"] / an["em_alerta"], lang), pd=pct(de["so_juro"] / de["em_alerta"], lang),
        ta=pct(an["sem_juro"] / an["avaliada"], lang), td=pct(de["sem_juro"] / de["avaliada"], lang),
        ta0=pct(an["em_alerta"] / an["avaliada"], lang), td0=pct(de["em_alerta"] / de["avaliada"], lang))]  # fmt: skip
    dp = n["descritiva"]["depi"]
    princ = [c for c in dp["casos"] if c["principal"]]
    linhas += ["", t["desc_c_titulo"], "", t["desc_c"].format(
        m0=i(dp["amostra"]["m_nao_calculavel"]), cd=i(dp["amostra"]["com_depi"]), sd=i(dp["amostra"]["so_depi"]),
        md=i(dp["amostra"]["so_depi_dfc_md"]), n=i(ac["acertaveis"]), k=i(len(princ)),
        ks=i(sum(c["so_depi"] for c in princ)), kn=i(sum(c["alerta_m_neutro"] for c in princ)),
        kv=i(sum(c["alerta_m_neutro"] and not c["acertado"] for c in princ)),
        ksec=i(len(dp["casos"]) - len(princ))), "", t["col_desc_c"], "|" + " --- |" * 5]  # fmt: skip
    for c in princ:
        mn = ", ".join(sinal(v, v is not None and v > n["regras"]["corte_m"], 2) for v in c["m_neutro"])
        linhas.append(f"| `{c['caso_id']}` | {anos(c['anos'])} | {sn(c['dfc_md'])} | {mn} | {sn(c['acertado'])} |")

    linhas += ["", t["h_nao_feito"], ""] + ["- " + x for x in t["nao_feito"]]
    return "\n".join(linhas) + "\n"
