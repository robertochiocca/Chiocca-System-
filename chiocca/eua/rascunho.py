"""Rascunho do pré-registro do estudo dos EUA (pedido de 24/11/2026, item 4): não é registro. Escrito antes de qualquer
sinal americano calculado, com as decisões de Roberto de 24/11/2026 (Fase 0, seção 5.1). Os números citados da Fase 0
saem de `docs/eua_fase0_numeros.json` (`render`); o resto do texto são regras e datas. Um teste confere que os
documentos em PT e EN são a saída deste módulo.

Uso: python -m chiocca.eua.rascunho
"""

from __future__ import annotations

import json
from typing import Any

from chiocca.base import RAIZ
from chiocca.eua import fase0, fsds
from chiocca.formato import inteiro, pct

DOCS = {
    "pt": RAIZ / "docs" / "pre-registro-eua-rascunho.md",
    "en": RAIZ / "docs" / "en" / "us-preregistration-draft.md",
}
PRIMEIRO, ULTIMO = 2011, 2024  # exercícios da amostra (ano da data de referência), decisão de 24/11/2026
SEMENTE = 20270430

PT = """# Rascunho do pré-registro do estudo dos EUA

> **Rascunho, não é registro.** Escrito em 24/11/2026 pelo agente e atualizado no mesmo dia com as decisões de Roberto sobre os pontos em aberto ([Fase 0, seção 5.1](eua-fase-0.md)), antes de qualquer sinal americano calculado. Continua rascunho, para a revisão do Claude (claude.ai) e de Roberto; nada aqui vale até o texto ser registrado (o commit que o introduz como registro e o hash anotado no commit seguinte), com meta de 31/01/2027 e reserva de 31/03/2027. A frente dos EUA fica fora do README e do produto. Alerta, não acusação: um 8-K com o item 4.02 é uma declaração de que demonstrações publicadas não valem mais, não uma acusação de fraude; nenhum alerta por companhia é publicado.

Base: a [Fase 0 dos EUA](eua-fase-0.md), com os números de [`docs/eua_fase0_numeros.json`](eua_fase0_numeros.json), e os pré-registros do [estudo 1](pre-registro.md), do [estudo 2](pre-registro-estudo-2.md) e do [motor v2](pre-registro-motor-v2.md), cujas regras valem aqui com só as adaptações da seção 3.

## 1. Pergunta

Com os 10-K como eram na época, os alertas do motor v1 e do motor v2, congelados no Brasil, e a regra boba separam as empresa-anos seguidas de um 8-K com o item 4.02 nos 12 meses depois do corte das que não foram? E o v2 separa melhor que o v1?

**Rótulo: retrospectivo.** Os dados de {primeiro} a 30/04/2026 já são públicos, e as contagens de 8-K 4.02 por ano já apareceram na Fase 0, sem nenhuma ligação com sinal. O teste é limpo porque as regras são fixas (sem treino), foram escritas e congeladas no Brasil, e este texto é registrado antes de qualquer sinal americano.

## 2. Os sinais: o v1 e o v2 congelados

- **v1:** as regras da seção 4 do pré-registro do estudo 1, com as emendas, no código registrado em [`docs/estudo_2_codigo_congelado.json`](estudo_2_codigo_congelado.json): M-score acima de -1,78; salto do DPO no decil superior do exercício; juro implícito acima da taxa de referência média do ano mais 10 p.p.; alerta quando pelo menos um sinal dispara.
- **v2:** as regras do pré-registro do motor v2, no código registrado em [`docs/motor_v2_codigo_congelado.json`](motor_v2_codigo_congelado.json): percentis do M-score, do salto do DPO, do juro implícito e do desvio de Benford padronizado, dentro do exercício e do grupo; escore igual ao maior percentil; alerta quando o escore fica no quantil de 90% ou acima.
- **O código:** as funções de sinal dos dois registros são chamadas sem mudar nenhuma linha. O script dos EUA só monta as entradas de cada empresa-ano a partir do XBRL e aplica as adaptações da seção 3. Só o grupo das não financeiras (seção 4).

## 3. As adaptações (as únicas), cada uma com o motivo

### 3.1 O mapa das contas para as tags us-gaap

Valores da própria companhia (sem co-registrante nem segmento), em dólar, na taxonomia us-gaap: o balanço na data de referência; o resultado e o fluxo de caixa do exercício (quatro trimestres). O ano anterior (t-1) vem do mesmo 10-K, como a coluna do exercício anterior da DFP. Conta faltante ou denominador zero: "não calculável", como no v1, sem imputação. O sinal das despesas segue a convenção da DFP (negativo), e o código do v1 já usa o valor absoluto onde precisa.

| Conta | Tags e regra | Motivo |
| --- | --- | --- |
| `ativo_total`, `ativo_circulante`, `contas_a_receber`, `imobilizado`, `passivo_circulante`, `patrimonio_liquido`, `caixa_operacional`, `depreciacao`, `custo_vendas`, `lucro_liquido` | as da proposta da Fase 0, na ordem de preferência | o mesmo conceito da conta da DFP |
| `receita_liquida` | {ordem_receita}, nessa ordem: as três da Fase 0 e as que a regra da seção 3.1.1 escolheu | com as três tags, a receita cobre de {rec_min} a {rec_max} dos 10-K de {primeiro} a {ultimo}, e a regra das sem receita tiraria companhias que têm receita em outra tag |
| `resultado_bruto` | `GrossProfit`; se ausente, receita menos custo das vendas | na DFP a linha 3.03 é obrigatória; no US GAAP o lucro bruto é opcional (cobertura de {bruto_min} a {bruto_max}) |
| `despesas_vendas` + `despesas_gerais_adm` | `SellingGeneralAndAdministrativeExpense`, que já junta as duas | o v1 soma as duas contas; no US GAAP elas vêm juntas |
| `lucro_operacoes_continuadas` | `IncomeLossFromContinuingOperations`; se ausente, o lucro líquido menos `IncomeLossFromDiscontinuedOperationsNetOfTax`, quando houver | a conta 3.09 é depois dos impostos; a tag antes dos impostos da proposta da Fase 0 sai, por ser outro conceito |
| `emprestimos_cp` | `DebtCurrent`; se ausente, a soma de `LongTermDebtCurrent` e `ShortTermBorrowings` presentes | no US GAAP a dívida de curto prazo pode vir em linhas separadas |
| `emprestimos_lp` | `LongTermDebtNoncurrent`; se ausente, `LongTermDebtAndCapitalLeaseObligations` | o mesmo conceito, com a segunda tag como reserva |
| `despesas_financeiras` | `InterestExpense` | limite registrado: a despesa financeira da DFP inclui variação cambial e outros encargos; a tag americana é só de juros |
| `fornecedores` | `AccountsPayableCurrent`; se ausente, `AccountsPayableAndAccruedLiabilitiesCurrent`, com a marca de que inclui provisões | a segunda tag é mais larga |
| `passivo_total` (regra boba) | `Liabilities`; se ausente, `LiabilitiesAndStockholdersEquity` menos o patrimônio líquido com minoritários | a regra boba usa passivo total ÷ ativo total, e muitas companhias não apresentam o total do passivo |

O desvio de Benford usa os valores diferentes de zero do exercício na demonstração do balanço, do resultado e do fluxo de caixa do 10-K (pela coluna `stmt` de `pre.txt`: BS, IS e CF), o equivalente americano de BPA, BPP, DRE e DFC, com o mínimo de 20 números do v2. A DVA não existe nos EUA: o DEPI do v2 é o do v1, pela depreciação do fluxo de caixa. A cobertura de cada conta com as regras acima está na seção 3.1.2 (só contagens).

### 3.1.1 A ampliação da receita, só pela cobertura

Decisão de Roberto de 24/11/2026: as tags da receita são escolhidas só pelas contagens de cobertura, e a lista final entra no texto registrado. A lista de candidatas e a regra foram escritas no código (`RECEITA_CANDIDATAS` e `ampliar_receita`, em `chiocca/eua/fsds.py`) antes de qualquer contagem: só tags us-gaap de receita total, sem componentes, custos ou saldos. Partindo das três tags da Fase 0, entra a cada passo a candidata que cobre mais 10-K da amostra ainda sem receita (não financeiras, sem as SPACs, exercícios de {primeiro} a {ultimo}: {n_am} 10-K), se o ganho for de pelo menos {ganho_min} dessas entregas. O valor é o anual (quatro trimestres) na data de referência.

{tabela_receita}

Entraram {n_escolhidas} tags. **A lista final da receita, nesta ordem de preferência: {ordem_receita}.**

Contagem de descoberta, só para transparência: entre os {sem_tres} 10-K da amostra sem nenhuma das três tags da Fase 0, as 15 tags us-gaap mais frequentes com "Revenue" ou "Sales" no nome (valor anual na data de referência). As que estão fora das candidatas não entram pela regra; se alguma for de receita total, entrar exige uma decisão de Roberto antes do registro (seção 10).

{tabela_descoberta}

### 3.1.2 A cobertura do mapa ampliado

A fração dos 10-K da amostra com cada conta pelas regras da seção 3.1: presença do valor na data de referência, como na seção 2.4 da Fase 0, e, para a receita, o valor anual diferente de zero. No conjunto de {primeiro} a {ultimo}, e o menor e o maior ano. Só contagens.

{tabela_cobertura}

Com o mapa ampliado, a regra das sem receita tira {sem_amp} dos {n_am} 10-K da amostra, contra {sem_f0} com as três tags da Fase 0.

### 3.2 A taxa que substitui o CDI

A Effective Federal Funds Rate, série diária DFF do FRED (Federal Reserve Bank of St. Louis), cuja fonte é a publicação H.15 do Federal Reserve: pública, gratuita e sem chave. Como `chiocca.cdi.medio`, a média das taxas diárias nos 12 meses que terminam no fim do exercício, com o mesmo corte de 10 p.p. Motivo: é a taxa do overnight interbancário dos EUA, o papel do CDI no Brasil. Limite registrado: a DFF anualiza em base de 360 dias corridos e o CDI em base de 252 dias úteis. O arquivo da série entra no repositório, como `data/cdi_sgs4389.csv`, com o SHA-256 no manifesto.

### 3.3 A data de corte

A mesma regra do estudo 1 (emenda 5, `chiocca.corte.data_corte`): o último dia do quarto mês depois do fim do exercício. Motivo: o prazo do 10-K é de 60, 75 ou 90 dias, conforme o porte, e, de {primeiro} a {ultimo}, o décimo de 10-K entregues mais tarde saiu até {p90} dias depois da data de referência (seção 2.2 da Fase 0). A versão usada é a pública no corte: a última entrega até a data entre o 10-K original e os 10-K/A com números das contas (seção 2.3 da Fase 0). A companhia sem 10-K com XBRL até o corte fica fora daquele exercício, como no Brasil.

### 3.4 O que não se adapta

As financeiras ficam fora (decisão de Roberto de 24/11/2026): o mapa não tem as contas delas, e por isso o grupo das financeiras e o peso de ganhos não recorrentes não existem neste estudo. A DVA (seção 3.1). O leitor de documentos.

## 4. Amostra e exclusões

- **Universo:** os 10-K originais dos Financial Statement Data Sets com data de referência de {primeiro} a {ultimo} (o exercício é o ano da data de referência, como na DFP). {primeiro}, porque o XBRL vale para todas as companhias a partir dos períodos depois de 15/06/2011; {ultimo}, porque a janela de 12 meses desse exercício já terminou, em 30/04/2026 (decisão de Roberto de 24/11/2026).
- **Exclusões, nesta ordem, cada uma contada no relatório:** (1) sem versão pública com XBRL até o corte; (2) as financeiras pela SIC, de 6000 a 6999, exceto 6770 (seção 3.4); (3) as SPACs, SIC 6770, regra explícita decidida por Roberto em 24/11/2026; (4) as sem receita (receita ausente ou zero, a regra do estudo 1, pelo mapa ampliado); (5) as sem nenhum sinal calculável. A SIC e a receita são as da versão usada.
- **O tamanho, pela Fase 0 (exercício declarado, mapa da Fase 0):** de {primeiro} a {ultimo}, {n10k} 10-K originais: {fin} de financeiras, {spac} de SPACs ({spac_sem} delas já sem receita) e {sem_dem} das demais sem receita pelo mapa da Fase 0; ficam {ficam10k}. Com o mapa ampliado (seção 3.1.2), as demais sem receita são {sem_amp}, e ficam {ficam_amp10k}.

## 5. O desfecho: o 8-K com o item 4.02, por caso

- **Episódio (o caso):** o primeiro 8-K de uma companhia com o item 4.02 no campo de itens do EDGAR abre um episódio; todo 8-K ou 8-K/A com o item 4.02 da mesma companhia nos 365 dias seguintes pertence a ele; depois disso, um novo 8-K 4.02 abre outro episódio. Cada episódio conta uma vez, a resposta à crítica de Walker e de Gow a Bao et al. (Fase 0, seção 5.1).
- **Janela:** a empresa-ano t é positiva se um episódio se abre depois do corte de t e até 12 meses depois dele. As janelas de exercícios seguidos da mesma companhia não se sobrepõem, e cada episódio cai em no máximo uma empresa-ano. Os episódios fora de qualquer empresa-ano da amostra entram só na descrição.
- **Fonte:** o campo de itens do histórico de entregas do EDGAR (`submissions.zip`), baixado de novo no dia do cálculo, com o SHA-256 no manifesto, e só os 8-K entregues até 30/04/2026, o fim da janela do exercício de {ultimo}.
- **O tamanho, pela Fase 0:** de 2009 a 30/04/2026, {antes} companhias-ano com 8-K 4.02 e 10-K nos dados da SEC antes do 8-K: {antes_fin} de financeiras, {antes_spac} de SPACs e {antes_sem} das demais sem receita pelo mapa da Fase 0; ficam {antes_ficam}, de {ficam_min} a {ficam_max} por ano de entrega de 2012 a 2025. Com o mapa ampliado, ficam {antes_ficam_amp}, de {ficam_amp_min} a {ficam_amp_max} por ano.
- **Limites:** o item 4.02 não diz quais demonstrações deixaram de valer: o desfecho é uma declaração de não confiabilidade nos 12 meses seguintes, sem garantia de que trata do exercício t. As republicações sem 8-K ("little r") ficam de fora. Nada disso é chamado de fraude.

## 6. Métricas: as do estudo 2

- **Medida principal:** a diferença de risco DR = P(positiva | em alerta) − P(positiva | fora de alerta), nas empresa-anos avaliadas pelo v1, com todos os exercícios juntos; também a razão de taxas.
- **Bootstrap por companhia:** sorteiam-se companhias com reposição, cada uma com todas as suas empresa-anos; 10.000 reamostragens, com a semente {semente} (decisão de Roberto de 24/11/2026); o intervalo é o percentil unilateral de 95%. As funções são `taxas`, `dr`, `bootstrap_por_companhia` e `limite_inferior` de `chiocca/v2/estudo2/secundaria.py`, chamadas sem mudar nenhuma linha.
- **Resultado:** "associação positiva" se o limite inferior do intervalo unilateral de 95% da DR ficar acima de zero; senão, "sem evidência de associação".
- **Regra boba lado a lado:** o decil mais endividado (passivo total ÷ ativo total) de cada exercício, como no estudo 1, com a mesma DR e o bootstrap pareado (as mesmas reamostragens): "o motor separa melhor que a regra boba" só se o limite inferior da diferença ficar acima de zero.
- **O v2 pareado com o v1:** como na emenda 5 do estudo 2. O alerta do v2 sai de todas as empresa-anos que o v2 avalia; as medidas são calculadas nas empresa-anos avaliadas pelo v1; "o v2 separa melhor que o v1" só se o limite inferior da diferença pareada ficar acima de zero; senão, sem vencedor declarado.
- **Descritivas:** as métricas de ranking do estudo 2 (precisão e lift no topo de 1%, 5% e 10% e NDCG@k), cada exercício separado e os AAERs (seção 7). Só agregados: nenhuma lista de companhias por alerta.

## 7. Os AAERs de 2009 a 2014: descrição à parte

Para os {casos} casos de Bao et al. ({ea} empresa-anos) com 10-K nos dados da SEC (Fase 0, seção 4.1): quantos casos o v1, o v2 e a regra boba alertaram em pelo menos um exercício afetado, com a versão pública no corte. Só contagens, sem teste e sem lista. Em 2009 e 2010, só as companhias maiores entregavam em XBRL.

## 8. Previsões escritas antes dos dados

Revistas em 24/11/2026 para o período novo ({primeiro} a {ultimo}) e o mapa ampliado. Nenhuma faixa mudou; o motivo de cada uma vem ao lado.

1. **Taxa de alerta do v1:** entre 25% e 45% das não financeiras avaliadas em cada exercício. Motivo: o M-score acima de -1,78 marca parte relevante das companhias americanas, e o decil do DPO soma 10%; o juro implícito dispara menos que no Brasil, porque a despesa de juros americana não inclui variação cambial. **Sem ajuste:** o período novo acrescenta exercícios de juros altos (2022 a 2024), em que o juro implícito dispara menos (o corte sobe com a taxa de referência), mas o M-score e o DPO não dependem dos juros, e a faixa já cobre essa variação.
2. **Taxa de alerta do v2:** entre 10,0% e 11,0% em cada exercício. **Sem ajuste:** vem da construção do decil.
3. **Taxa do desfecho:** entre 1,5% e 4% das empresa-anos avaliadas. **Sem ajuste:** com o mapa ampliado, ficam {antes_ficam_amp} companhias-ano com 8-K 4.02 e 10-K antes (seção 5), de {ficam_amp_min} a {ficam_amp_max} por ano de entrega, contra cerca de {media_am} 10-K da amostra por exercício antes da regra das sem receita: perto de 2% a 3%.
4. **DR do v1:** positiva, com razão de taxas entre 1,1 e 1,5, e "associação positiva" mais provável que não. **Sem ajuste:** a amostra maior só reforça o poder.
5. **DR do v2:** positiva, com razão de taxas entre 1,2 e 2,0, e "associação positiva". **Sem ajuste.**
6. **O v2 pareado com o v1:** diferença positiva, com o limite inferior acima de zero ("o v2 separa melhor que o v1"). Motivo: o grupo em alerta do v2 é menor e mais extremo. **Sem ajuste.**
7. **O v2 contra a regra boba:** sem vencedor declarado. Motivo: o endividamento também se associa a republicações, pela dificuldade financeira. **Sem ajuste.**
8. **AAERs:** dos {casos} casos, entre 30% e 60% em alerta no v1 e entre 10% e 30% no v2 em pelo menos um exercício afetado. **Sem ajuste:** a descrição dos AAERs não depende do período da amostra.

## 9. Calendário: meta e reserva

| Etapa | Meta | Reserva |
| --- | --- | --- |
| Decisões de Roberto e este rascunho. | 24/11/2026 | 24/11/2026 |
| Revisão do rascunho pelo Claude (claude.ai) e por Roberto; nenhum sinal calculado. | 15/12/2026 | 15/12/2026 |
| Código do estudo escrito e testado só em dados sintéticos; nenhum sinal americano calculado. | 15/01/2027 | 31/01/2027 |
| Registro do pré-registro e carimbo; código congelado com registro de SHA-256. | 31/01/2027 | 31/03/2027 |
| Cálculo único, depois do carimbo, com os dados da SEC e os 8-K baixados de novo no dia. | 28/02/2027 | 30/04/2027 |
| Relatório em PT e EN, separado do estudo 2 do Brasil. | 31/03/2027 | 31/05/2027 |

## 10. Decisões de Roberto de 24/11/2026 e o que falta antes do registro

Decidido: (a) as financeiras ficam fora (seção 3.4); (b) as tags da receita são escolhidas só pelas contagens de cobertura, e a lista final entra no texto registrado (seção 3.1.1); (c) a amostra vai até o exercício de {ultimo}, com os dados da SEC e os 8-K baixados de novo no dia do cálculo; (d) a semente é {semente}; (e) os arquivos da SEC ficam fora do Git, com o SHA-256 no manifesto e o download por script; (f) o calendário tem meta e reserva (seção 9).

Para a revisão do Claude (claude.ai) e de Roberto, antes do registro:

1. As tags da contagem de descoberta fora das candidatas (seção 3.1.1): nenhuma entra sem decisão de Roberto.
2. O exercício pela data de referência, como na DFP; as contagens da Fase 0 usam o exercício declarado pela companhia (`fy`), e a diferença entre os dois é pequena.
3. Duas contas com queda de cobertura, provavelmente por troca de tag na taxonomia (a conferir): `despesas_financeiras` cai para {df_min} em {df_ano}, e `caixa_operacional` fica abaixo de 80% de {co_ini} a {co_fim} (mínimo de {co_min}, em {co_ano}). Sem ampliação, o juro implícito e o TATA do M-score ficam não calculáveis nessas companhias-ano. Recomendação, para Roberto decidir antes do registro: a mesma regra da receita (candidatas escritas antes de contar, ganho mínimo de {ganho_min}), com candidatas como `InterestExpenseNonoperating` e `InterestExpenseDebt` para a despesa financeira e `NetCashProvidedByUsedInOperatingActivitiesContinuingOperations` para o caixa operacional.
4. A leitura do texto inteiro, que é registrado como estiver depois da revisão.

## 11. O que fica de fora

As financeiras, a DVA e o leitor (seção 3.4); qualquer lista ou ordem de companhias por alerta; qualquer recomendação de investimento; e, até decisão de Roberto, a frente dos EUA no README e no produto.
"""

EN = """# Draft pre-registration of the US study

> **Draft, not a registration.** Written on 2026-11-24 by the agent and updated on the same day with Roberto's decisions on the open points ([Phase 0, section 5.1](us-phase-0.md)), before any US signal was computed. It is still a draft, for review by Claude (claude.ai) and Roberto; nothing here holds until the text is registered (the commit that introduces it as the registration and the hash noted in the next commit), with a target of 2027-01-31 and a fallback of 2027-03-31. The US front stays out of the README and the product. Alert, not accusation: an 8-K with Item 4.02 is a statement that published financial statements can no longer be relied upon, not an accusation of fraud; no alert by company is published.

Basis: [US Phase 0](us-phase-0.md), with the numbers in [`docs/eua_fase0_numeros.json`](../eua_fase0_numeros.json), and the pre-registrations of [study 1](../pre-registro.md), [study 2](study-2-preregistration.md) and [engine v2](engine-v2-preregistration.md), whose rules hold here with only the adaptations in section 3.

## 1. Question

With the 10-Ks as they were at the time, do the alerts of engine v1 and engine v2, frozen in Brazil, and the naive rule separate the company-years followed by an 8-K with Item 4.02 within 12 months after the cut-off from those that were not? And does v2 separate better than v1?

**Label: retrospective.** The data from {primeiro} to 2026-04-30 are already public, and the counts of 8-K 4.02 by year already appeared in Phase 0, with no link to any signal. The test is clean because the rules are fixed (no training), were written and frozen in Brazil, and this text is registered before any US signal.

## 2. The signals: v1 and v2, frozen

- **v1:** the rules in section 4 of the study 1 pre-registration, with the amendments, in the code registered in [`docs/estudo_2_codigo_congelado.json`](../estudo_2_codigo_congelado.json): M-score above -1.78; DPO jump in the top decile of the fiscal year; implied interest above the year's average reference rate plus 10 p.p.; alert when at least one signal fires.
- **v2:** the rules of the engine v2 pre-registration, in the code registered in [`docs/motor_v2_codigo_congelado.json`](../motor_v2_codigo_congelado.json): percentiles of the M-score, the DPO jump, implied interest and the standardized Benford deviation, within the fiscal year and the group; score equal to the highest percentile; alert when the score is at or above the 90% quantile.
- **The code:** the signal functions of both registries are called without changing a line. The US script only builds each company-year's inputs from XBRL and applies the adaptations in section 3. Only the non-financial group (section 4).

## 3. The adaptations (the only ones), each with its reason

### 3.1 The map from accounts to us-gaap tags

The company's own values (no co-registrant or segment), in dollars, in the us-gaap taxonomy: the balance sheet at the report date; the income statement and cash flow for the fiscal year (four quarters). The prior year (t-1) comes from the same 10-K, like the DFP's prior-year column. Missing account or zero denominator: "not computable", as in v1, with no imputation. Expense signs follow the DFP convention (negative), and the v1 code already uses the absolute value where it needs to.

| Account | Tags and rule | Reason |
| --- | --- | --- |
| `ativo_total`, `ativo_circulante`, `contas_a_receber`, `imobilizado`, `passivo_circulante`, `patrimonio_liquido`, `caixa_operacional`, `depreciacao`, `custo_vendas`, `lucro_liquido` | those of the Phase 0 proposal, in order of preference | the same concept as the DFP account |
| `receita_liquida` | {ordem_receita}, in this order: the three Phase 0 tags and those the rule in section 3.1.1 chose | with the three tags, revenue covers {rec_min} to {rec_max} of the {primeiro} to {ultimo} 10-Ks, and the no-revenue rule would remove companies that have revenue in another tag |
| `resultado_bruto` | `GrossProfit`; if missing, revenue minus cost of sales | in the DFP line 3.03 is mandatory; under US GAAP gross profit is optional (coverage of {bruto_min} to {bruto_max}) |
| `despesas_vendas` + `despesas_gerais_adm` | `SellingGeneralAndAdministrativeExpense`, which already joins both | v1 adds the two accounts; under US GAAP they come together |
| `lucro_operacoes_continuadas` | `IncomeLossFromContinuingOperations`; if missing, net income minus `IncomeLossFromDiscontinuedOperationsNetOfTax`, when present | account 3.09 is after taxes; the pre-tax tag of the Phase 0 proposal is dropped, being a different concept |
| `emprestimos_cp` | `DebtCurrent`; if missing, the sum of `LongTermDebtCurrent` and `ShortTermBorrowings` present | under US GAAP short-term debt may come in separate lines |
| `emprestimos_lp` | `LongTermDebtNoncurrent`; if missing, `LongTermDebtAndCapitalLeaseObligations` | the same concept, with the second tag as a fallback |
| `despesas_financeiras` | `InterestExpense` | recorded limitation: the DFP's financial expense includes FX variation and other charges; the US tag is interest only |
| `fornecedores` | `AccountsPayableCurrent`; if missing, `AccountsPayableAndAccruedLiabilitiesCurrent`, flagged as including accruals | the second tag is wider |
| `passivo_total` (naive rule) | `Liabilities`; if missing, `LiabilitiesAndStockholdersEquity` minus equity including noncontrolling interest | the naive rule uses total liabilities ÷ total assets, and many companies do not present total liabilities |

The Benford deviation uses the fiscal year's nonzero values in the 10-K's balance sheet, income statement and cash flow statement (by the `stmt` column of `pre.txt`: BS, IS and CF), the US equivalent of BPA, BPP, DRE and DFC, with v2's minimum of 20 numbers. The DVA does not exist in the US: v2's DEPI is v1's, from cash-flow depreciation. The coverage of each account under the rules above is in section 3.1.2 (counts only).

### 3.1.1 The revenue widening, by coverage only

Roberto's decision of 2026-11-24: the revenue tags are chosen by coverage counts only, and the final list goes into the registered text. The candidate list and the rule were written in the code (`RECEITA_CANDIDATAS` and `ampliar_receita`, in `chiocca/eua/fsds.py`) before any count: only us-gaap tags for total revenue, with no components, costs or balances. Starting from the three Phase 0 tags, at each step the candidate that covers the most sample 10-Ks still without revenue enters (non-financial, without SPACs, fiscal years {primeiro} to {ultimo}: {n_am} 10-Ks), if the gain is at least {ganho_min} of those filings. The value is the annual one (four quarters) at the report date.

{tabela_receita}

{n_escolhidas} tags entered. **The final revenue list, in this order of preference: {ordem_receita}.**

Discovery count, for transparency only: among the {sem_tres} sample 10-Ks with none of the three Phase 0 tags, the 15 most frequent us-gaap tags with "Revenue" or "Sales" in the name (annual value at the report date). Those outside the candidates do not enter by the rule; if any is a total-revenue tag, entering requires a decision by Roberto before registration (section 10).

{tabela_descoberta}

### 3.1.2 Coverage of the widened map

The share of sample 10-Ks with each account under the rules in section 3.1: presence of the value at the report date, as in Phase 0 section 2.4, and, for revenue, a nonzero annual value. Over {primeiro} to {ultimo} as a whole, and the lowest and highest year. Counts only.

{tabela_cobertura}

With the widened map, the no-revenue rule removes {sem_amp} of the {n_am} sample 10-Ks, against {sem_f0} with the three Phase 0 tags.

### 3.2 The rate that replaces the CDI

The Effective Federal Funds Rate, daily series DFF on FRED (Federal Reserve Bank of St. Louis), sourced from the Federal Reserve's H.15 release: public, free and with no key. Like `chiocca.cdi.medio`, the average of the daily rates over the 12 months ending at the fiscal year end, with the same 10 p.p. cut-off. Reason: it is the US overnight interbank rate, the CDI's role in Brazil. Recorded limitation: DFF annualizes on a 360 calendar-day basis and the CDI on a 252 business-day basis. The series file goes into the repository, like `data/cdi_sgs4389.csv`, with its SHA-256 in the manifest.

### 3.3 The cut-off date

The same rule as study 1 (amendment 5, `chiocca.corte.data_corte`): the last day of the fourth month after the fiscal year end. Reason: the 10-K deadline is 60, 75 or 90 days, depending on size, and, from {primeiro} to {ultimo}, the latest-filed tenth of 10-Ks came out up to {p90} days after the report date (Phase 0, section 2.2). The version used is the one public at the cut-off: the last filing by that date between the original 10-K and the 10-K/As with account numbers (Phase 0, section 2.3). A company with no XBRL 10-K by the cut-off is out for that fiscal year, as in Brazil.

### 3.4 What is not adapted

Financial companies stay out (Roberto's decision of 2026-11-24): the map has no accounts for them, so the financial group and the weight of non-recurring gains do not exist in this study. The DVA (section 3.1). The document reader.

## 4. Sample and exclusions

- **Universe:** the original 10-Ks in the Financial Statement Data Sets with a report date from {primeiro} to {ultimo} (the fiscal year is the year of the report date, as in the DFP). {primeiro}, because XBRL applies to all companies from periods after 2011-06-15; {ultimo}, because the 12-month window of that fiscal year has already ended, on 2026-04-30 (Roberto's decision of 2026-11-24).
- **Exclusions, in this order, each counted in the report:** (1) no public XBRL version by the cut-off; (2) financial companies by SIC, 6000 to 6999, except 6770 (section 3.4); (3) SPACs, SIC 6770, an explicit rule decided by Roberto on 2026-11-24; (4) companies without revenue (revenue missing or zero, the study 1 rule, by the widened map); (5) those with no computable signal. SIC and revenue are those of the version used.
- **The size, from Phase 0 (declared fiscal year, Phase 0 map):** from {primeiro} to {ultimo}, {n10k} original 10-Ks: {fin} financial, {spac} SPACs ({spac_sem} of them already without revenue) and {sem_dem} others without revenue by the Phase 0 map; {ficam10k} remain. With the widened map (section 3.1.2), the others without revenue are {sem_amp}, and {ficam_amp10k} remain.

## 5. The outcome: the 8-K with Item 4.02, per case

- **Episode (the case):** a company's first 8-K with Item 4.02 in the EDGAR items field opens an episode; every 8-K or 8-K/A with Item 4.02 from the same company within the next 365 days belongs to it; after that, a new 8-K 4.02 opens another episode. Each episode counts once, the answer to Walker's and Gow's critique of Bao et al. (Phase 0, section 5.1).
- **Window:** company-year t is positive if an episode opens after the cut-off of t and within 12 months of it. The windows of consecutive fiscal years of the same company do not overlap, and each episode falls into at most one company-year. Episodes outside any sample company-year enter the description only.
- **Source:** the items field of the EDGAR filing history (`submissions.zip`), downloaded again on the day of the computation, with its SHA-256 in the manifest, and only the 8-Ks filed through 2026-04-30, the end of the window of fiscal {ultimo}.
- **The size, from Phase 0:** from 2009 to 2026-04-30, {antes} company-years with an 8-K 4.02 and a 10-K in the SEC data before the 8-K: {antes_fin} financial, {antes_spac} SPACs and {antes_sem} others without revenue by the Phase 0 map; {antes_ficam} remain, from {ficam_min} to {ficam_max} a year by filing year from 2012 to 2025. With the widened map, {antes_ficam_amp} remain, from {ficam_amp_min} to {ficam_amp_max} a year.
- **Limitations:** Item 4.02 does not say which statements stopped being reliable: the outcome is a non-reliance statement within the next 12 months, with no guarantee that it concerns fiscal year t. Restatements without an 8-K ("little r") are left out. None of this is called fraud.

## 6. Metrics: those of study 2

- **Main measure:** the risk difference DR = P(positive | alert) − P(positive | no alert), on the company-years evaluated by v1, with all fiscal years together; also the rate ratio.
- **Bootstrap by company:** companies are drawn with replacement, each with all its company-years; 10,000 resamples, with seed {semente} (Roberto's decision of 2026-11-24); the interval is the one-sided 95% percentile. The functions are `taxas`, `dr`, `bootstrap_por_companhia` and `limite_inferior` from `chiocca/v2/estudo2/secundaria.py`, called without changing a line.
- **Result:** "positive association" if the lower bound of the one-sided 95% interval of the DR is above zero; otherwise, "no evidence of association".
- **Naive rule side by side:** the most leveraged decile (total liabilities ÷ total assets) of each fiscal year, as in study 1, with the same DR and the paired bootstrap (the same resamples): "the engine separates better than the naive rule" only if the lower bound of the difference is above zero.
- **v2 paired with v1:** as in study 2's amendment 5. v2's alert comes from all company-years v2 evaluates; the measures are computed on the company-years evaluated by v1; "v2 separates better than v1" only if the lower bound of the paired difference is above zero; otherwise, no winner declared.
- **Descriptive:** study 2's ranking metrics (precision and lift at the top 1%, 5% and 10% and NDCG@k), each fiscal year separately and the AAERs (section 7). Aggregates only: no list of companies by alert.

## 7. The 2009 to 2014 AAERs: a separate description

For the {casos} Bao et al. cases ({ea} company-years) with a 10-K in the SEC data (Phase 0, section 4.1): how many cases v1, v2 and the naive rule alerted in at least one affected fiscal year, with the version public at the cut-off. Counts only, with no test and no list. In 2009 and 2010, only the largest companies filed in XBRL.

## 8. Predictions written before the data

Revised on 2026-11-24 for the new period ({primeiro} to {ultimo}) and the widened map. No range changed; the reason for each is given next to it.

1. **v1 alert rate:** between 25% and 45% of the evaluated non-financial companies in each fiscal year. Reason: the M-score above -1.78 flags a relevant share of US companies, and the DPO decile adds 10%; implied interest fires less than in Brazil, because US interest expense does not include FX variation. **No adjustment:** the new period adds high-rate fiscal years (2022 to 2024), in which implied interest fires less (the cut-off rises with the reference rate), but the M-score and the DPO do not depend on rates, and the range already covers that variation.
2. **v2 alert rate:** between 10.0% and 11.0% in each fiscal year. **No adjustment:** it comes from the construction of the decile.
3. **Outcome rate:** between 1.5% and 4% of the evaluated company-years. **No adjustment:** with the widened map, {antes_ficam_amp} company-years with an 8-K 4.02 and a 10-K before remain (section 5), from {ficam_amp_min} to {ficam_amp_max} a year by filing year, against about {media_am} sample 10-Ks per fiscal year before the no-revenue rule: about 2% to 3%.
4. **v1 DR:** positive, with a rate ratio between 1.1 and 1.5, and "positive association" more likely than not. **No adjustment:** the larger sample only adds power.
5. **v2 DR:** positive, with a rate ratio between 1.2 and 2.0, and "positive association". **No adjustment.**
6. **v2 paired with v1:** a positive difference, with the lower bound above zero ("v2 separates better than v1"). Reason: v2's alert group is smaller and more extreme. **No adjustment.**
7. **v2 against the naive rule:** no winner declared. Reason: leverage is also associated with restatements, through financial distress. **No adjustment.**
8. **AAERs:** of the {casos} cases, between 30% and 60% in alert under v1 and between 10% and 30% under v2 in at least one affected fiscal year. **No adjustment:** the AAER description does not depend on the sample period.

## 9. Timeline: target and fallback

| Step | Target | Fallback |
| --- | --- | --- |
| Roberto's decisions and this draft. | 2026-11-24 | 2026-11-24 |
| Review of the draft by Claude (claude.ai) and Roberto; no signal computed. | 2026-12-15 | 2026-12-15 |
| Study code written and tested on synthetic data only; no US signal computed. | 2027-01-15 | 2027-01-31 |
| Pre-registration registered and timestamped; code frozen with a SHA-256 registry. | 2027-01-31 | 2027-03-31 |
| Single computation, after the timestamp, with the SEC data and the 8-Ks downloaded again on the day. | 2027-02-28 | 2027-04-30 |
| Report in PT and EN, separate from Brazil's study 2. | 2027-03-31 | 2027-05-31 |

## 10. Roberto's decisions of 2026-11-24 and what is left before registration

Decided: (a) financial companies stay out (section 3.4); (b) the revenue tags are chosen by coverage counts only, and the final list goes into the registered text (section 3.1.1); (c) the sample goes to fiscal {ultimo}, with the SEC data and the 8-Ks downloaded again on the day of the computation; (d) the seed is {semente}; (e) the SEC files stay outside Git, with their SHA-256 in the manifest and the download by script; (f) the timeline has a target and a fallback (section 9).

For review by Claude (claude.ai) and Roberto, before registration:

1. The discovery-count tags outside the candidates (section 3.1.1): none enters without a decision by Roberto.
2. The fiscal year by the report date, as in the DFP; Phase 0 counts use the fiscal year declared by the company (`fy`), and the difference between the two is small.
3. Two accounts with a drop in coverage, probably from a tag change in the taxonomy (to be checked): `despesas_financeiras` falls to {df_min} in {df_ano}, and `caixa_operacional` stays below 80% from {co_ini} to {co_fim} (minimum of {co_min}, in {co_ano}). Without widening, implied interest and the M-score's TATA are not computable in those company-years. Recommendation, for Roberto to decide before registration: the same rule as for revenue (candidates written before counting, minimum gain of {ganho_min}), with candidates such as `InterestExpenseNonoperating` and `InterestExpenseDebt` for financial expense and `NetCashProvidedByUsedInOperatingActivitiesContinuingOperations` for operating cash flow.
4. Reading the whole text, which is registered as it stands after the review.

## 11. What is left out

Financial companies, the DVA and the reader (section 3.4); any list or ordering of companies by alert; any investment recommendation; and, until Roberto decides, the US front in the README and the product.
"""

T = {"pt": PT, "en": EN}


CONTAS_COBERTURA = ("receita_liquida", "ativo_total", "ativo_circulante", "contas_a_receber", "imobilizado",
                    "passivo_circulante", "fornecedores", "emprestimos_cp", "emprestimos_lp", "patrimonio_liquido",
                    "custo_vendas", "resultado_bruto", "despesas_vendas_gerais_adm", "despesas_financeiras",
                    "lucro_operacoes_continuadas", "lucro_liquido", "caixa_operacional", "depreciacao",
                    "passivo_total")  # fmt: skip
CABECALHOS = {
    "pt": {"receita": "| Candidata | Ganho no primeiro passo | Entrou | Ganho quando entrou |", "sim": "sim", "nao": "não",
           "descoberta": "| Tag | 10-K sem as três tags com ela | Candidata |", "cobertura": "| Conta | {primeiro} a {ultimo} | Menor ano | Maior ano |"},
    "en": {"receita": "| Candidate | Gain at the first step | Entered | Gain when it entered |", "sim": "yes", "nao": "no",
           "descoberta": "| Tag | 10-Ks without the three tags with it | Candidate |", "cobertura": "| Account | {primeiro} to {ultimo} | Lowest year | Highest year |"},
}  # fmt: skip


def _tabelas(m: dict[str, Any], lang: str) -> dict[str, str]:
    """As tabelas da ampliação da receita, da descoberta e da cobertura, do JSON da Fase 0."""
    c, i = CABECALHOS[lang], (lambda v: inteiro(int(v), lang))
    p1 = lambda x: pct(x, lang, 1)  # noqa: E731
    amp = m["ampliacao"]
    linhas = [c["receita"], "| --- | ---: | --- | ---: |"]
    for t in m["candidatas"]:
        entrou = t in amp["escolhidas"]
        linhas.append(f"| `{t}` | {i(amp['ganho_no_primeiro_passo'].get(t, 0))} | {c['sim'] if entrou else c['nao']} | "
                      f"{i(amp['ganhos'][t]) if entrou else '—'} |")  # fmt: skip
    descoberta = [c["descoberta"], "| --- | ---: | --- |"]
    descoberta += [f"| `{t}` | {i(n)} | {c['sim'] if t in m['candidatas'] or t in fsds.MAPA['receita_liquida'] else c['nao']} |"
                   for t, n in m["descoberta"]]  # fmt: skip
    anos = [str(a) for a in range(PRIMEIRO, ULTIMO + 1)]
    cob = m["cobertura_por_ano"]
    n = sum(cob[a]["10k"] for a in anos)
    cobertura = [c["cobertura"].format(primeiro=PRIMEIRO, ultimo=ULTIMO), "| --- | ---: | ---: | ---: |"]
    for conta in CONTAS_COBERTURA:
        conjunto = sum(cob[a][conta] * cob[a]["10k"] for a in anos) / n
        cobertura.append(f"| `{conta}` | {p1(conjunto)} | {p1(min(cob[a][conta] for a in anos))} | "
                         f"{p1(max(cob[a][conta] for a in anos))} |")  # fmt: skip
    return {"tabela_receita": "\n".join(linhas), "tabela_descoberta": "\n".join(descoberta),
            "tabela_cobertura": "\n".join(cobertura)}  # fmt: skip


def valores(d: dict[str, Any], lang: str) -> dict[str, str]:
    """Os números da Fase 0 citados no rascunho, formatados para a língua."""
    f, i = d["fsds"], (lambda v: inteiro(int(v), lang))
    p0 = lambda x: pct(x, lang, 0)  # noqa: E731
    anos = [str(a) for a in range(PRIMEIRO, ULTIMO + 1)]
    ex, it, cob, pe = f["exclusoes_10k"], f["itens_8k"], f["cobertura"], f["por_exercicio"]
    soma = lambda k: sum(ex[a][k] for a in anos)  # noqa: E731
    rec = [cob[a]["contas"]["receita_liquida"] for a in anos]
    bruto = [cob[a]["contas"]["resultado_bruto"] for a in anos]
    ficam = [it[str(a)]["antes_restantes"] for a in range(2012, 2026)]
    tot = lambda k: sum(x[k] for x in it.values())  # noqa: E731
    m = f["mapa_ampliado"]
    sr, e8 = m["sem_receita_por_ano"], m["exclusoes_8k"]
    n_am = sum(sr[a]["10k"] for a in anos)
    sem_amp = sum(sr[a]["sem_receita_ampliada"] for a in anos)
    ficam_amp = [e8[str(a)]["antes_restantes"] for a in range(2012, 2026)]
    cob_am = m["cobertura_por_ano"]
    df_ano = min(anos, key=lambda a: cob_am[a]["despesas_financeiras"])
    co_ano = min(anos, key=lambda a: cob_am[a]["caixa_operacional"])
    co_baixos = [a for a in anos if cob_am[a]["caixa_operacional"] < 0.8]
    return {
        "primeiro": str(PRIMEIRO), "ultimo": str(ULTIMO), "semente": str(SEMENTE),
        "rec_min": p0(min(rec)), "rec_max": p0(max(rec)), "bruto_min": p0(min(bruto)), "bruto_max": p0(max(bruto)),
        "p90": i(max(pe[a]["prazo_p90_dias"] for a in anos)),
        "n10k": i(soma("10k")), "fin": i(soma("financeiras")), "spac": i(soma("sic_6770")),
        "spac_sem": i(soma("sic_6770_sem_receita")), "sem_dem": i(soma("sem_receita_demais")),
        "ficam10k": i(soma("restantes")),
        "antes": i(tot("companhias_com_10k_fsds_antes")), "antes_fin": i(tot("antes_financeiras")),
        "antes_spac": i(tot("antes_sic_6770")), "antes_sem": i(tot("antes_sem_receita_demais")),
        "antes_ficam": i(tot("antes_restantes")),
        "ficam_min": i(min(ficam)), "ficam_max": i(max(ficam)),
        "casos": i(f["aaer"]["casos_com_10k"]), "ea": i(f["aaer"]["empresa_anos_com_10k"]),
        "ordem_receita": ", ".join(f"`{t}`" for t in m["ampliacao"]["ordem"]),
        "n_escolhidas": i(len(m["ampliacao"]["escolhidas"])), "ganho_min": pct(m["ganho_minimo"], lang, 1),
        "n_am": i(n_am), "sem_tres": i(m["entregas_sem_as_tres_tags"]),
        "sem_amp": i(sem_amp), "sem_f0": i(sum(sr[a]["sem_receita_fase0"] for a in anos)),
        "ficam_amp10k": i(n_am - sem_amp), "media_am": i(round(n_am / len(anos), -2)),
        "antes_ficam_amp": i(sum(x["antes_restantes"] for x in e8.values())),
        "ficam_amp_min": i(min(ficam_amp)), "ficam_amp_max": i(max(ficam_amp)),
        "df_min": pct(cob_am[df_ano]["despesas_financeiras"], lang, 1), "df_ano": df_ano,
        "co_min": pct(cob_am[co_ano]["caixa_operacional"], lang, 1), "co_ano": co_ano,
        "co_ini": min(co_baixos), "co_fim": max(co_baixos),
        **_tabelas(m, lang),
    }  # fmt: skip


def render(d: dict[str, Any], lang: str) -> str:
    return T[lang].format(**valores(d, lang))


def main() -> None:
    d = json.loads(fase0.SAIDA.read_text(encoding="utf-8"))
    for lang, caminho in DOCS.items():
        caminho.write_text(render(d, lang), encoding="utf-8")
    print("gravado:", ", ".join(str(c.relative_to(RAIZ)) for c in DOCS.values()))


if __name__ == "__main__":
    main()
