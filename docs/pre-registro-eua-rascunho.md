# Rascunho do pré-registro do estudo dos EUA

> **Rascunho, não é registro.** Escrito em 24/11/2026 pelo agente e atualizado no mesmo dia com as decisões de Roberto sobre os pontos em aberto ([Fase 0, seção 5.1](eua-fase-0.md)), antes de qualquer sinal americano calculado. Continua rascunho, para a revisão final do Claude (claude.ai) e de Roberto; nada aqui vale até o texto ser registrado (o commit que o introduz como registro e o hash anotado no commit seguinte), com meta de 31/01/2027 e reserva de 31/03/2027. A frente dos EUA fica fora do README e do produto. Alerta, não acusação: um 8-K com o item 4.02 é uma declaração de que demonstrações publicadas não valem mais, não uma acusação de fraude; nenhum alerta por companhia é publicado.

Base: a [Fase 0 dos EUA](eua-fase-0.md), com os números de [`docs/eua_fase0_numeros.json`](eua_fase0_numeros.json), e os pré-registros do [estudo 1](pre-registro.md), do [estudo 2](pre-registro-estudo-2.md) e do [motor v2](pre-registro-motor-v2.md), cujas regras valem aqui com só as adaptações da seção 3.

## 1. Pergunta

Com os 10-K como eram na época, os alertas do motor v1 e do motor v2, congelados no Brasil, e a regra boba separam as empresa-anos seguidas de um 8-K com o item 4.02 nos 12 meses depois do corte das que não foram? E o v2 separa melhor que o v1?

**Rótulo: retrospectivo.** Os dados de 2011 a 30/04/2026 já são públicos, e as contagens de 8-K 4.02 por ano já apareceram na Fase 0, sem nenhuma ligação com sinal. O teste é limpo porque as regras são fixas (sem treino), foram escritas e congeladas no Brasil, e este texto é registrado antes de qualquer sinal americano.

## 2. Os sinais: o v1 e o v2 congelados

- **v1:** as regras da seção 4 do pré-registro do estudo 1, com as emendas, no código registrado em [`docs/estudo_2_codigo_congelado.json`](estudo_2_codigo_congelado.json): M-score acima de -1,78; salto do DPO no decil superior do exercício; juro implícito acima da taxa de referência média do ano mais 10 p.p.; alerta quando pelo menos um sinal dispara.
- **v2:** as regras do pré-registro do motor v2, no código registrado em [`docs/motor_v2_codigo_congelado.json`](motor_v2_codigo_congelado.json): percentis do M-score, do salto do DPO, do juro implícito e do desvio de Benford padronizado, dentro do exercício e do grupo; escore igual ao maior percentil; alerta quando o escore fica no quantil de 90% ou acima.
- **O código:** as funções de sinal dos dois registros são chamadas sem mudar nenhuma linha. O script dos EUA só monta as entradas de cada empresa-ano a partir do XBRL e aplica as adaptações da seção 3. Só o grupo das não financeiras (seção 4).

## 3. As adaptações (as únicas), cada uma com o motivo

### 3.1 O mapa das contas para as tags us-gaap

Valores da própria companhia (sem co-registrante nem segmento), em dólar, na taxonomia us-gaap: o balanço na data de referência; o resultado e o fluxo de caixa do exercício (quatro trimestres). O ano anterior (t-1) vem do mesmo 10-K, como a coluna do exercício anterior da DFP. Conta faltante ou denominador zero: "não calculável", como no v1, sem imputação. O sinal das despesas segue a convenção da DFP (negativo), e o código do v1 já usa o valor absoluto onde precisa.

| Conta | Tags e regra | Motivo |
| --- | --- | --- |
| `ativo_total`, `ativo_circulante`, `contas_a_receber`, `imobilizado`, `passivo_circulante`, `patrimonio_liquido`, `depreciacao`, `custo_vendas`, `lucro_liquido` | as da proposta da Fase 0, na ordem de preferência | o mesmo conceito da conta da DFP |
| `caixa_operacional` | `NetCashProvidedByUsedInOperatingActivities`, `NetCashProvidedByUsedInOperatingActivitiesContinuingOperations`, nessa ordem (seção 3.1.3) | a variante só de operações continuadas cobre os 10-K que não trazem o total; exclui o caixa das operações descontinuadas |
| `receita_liquida` | `Revenues`, `RevenueFromContractWithCustomerExcludingAssessedTax`, `SalesRevenueNet`, `SalesRevenueGoodsNet`, `RevenueFromContractWithCustomerIncludingAssessedTax`, `SalesRevenueServicesNet`, `OilAndGasRevenue`, nessa ordem: as três da Fase 0 e as que a regra da seção 3.1.1 escolheu | com as três tags, a receita cobre de 66% a 73% dos 10-K de 2011 a 2024, e a regra das sem receita tiraria companhias que têm receita em outra tag |
| `resultado_bruto` | `GrossProfit`; se ausente, receita menos custo das vendas | na DFP a linha 3.03 é obrigatória; no US GAAP o lucro bruto é opcional (cobertura de 35% a 37%) |
| `despesas_vendas` + `despesas_gerais_adm` | `SellingGeneralAndAdministrativeExpense`, que já junta as duas | o v1 soma as duas contas; no US GAAP elas vêm juntas |
| `lucro_operacoes_continuadas` | `IncomeLossFromContinuingOperations`; se ausente, o lucro líquido menos `IncomeLossFromDiscontinuedOperationsNetOfTax`, quando houver | a conta 3.09 é depois dos impostos; a tag antes dos impostos da proposta da Fase 0 sai, por ser outro conceito |
| `emprestimos_cp` | `DebtCurrent`; se ausente, a soma de `LongTermDebtCurrent` e `ShortTermBorrowings` presentes | no US GAAP a dívida de curto prazo pode vir em linhas separadas |
| `emprestimos_lp` | `LongTermDebtNoncurrent`; se ausente, `LongTermDebtAndCapitalLeaseObligations` | o mesmo conceito, com a segunda tag como reserva |
| `despesas_financeiras` | `InterestExpense`, `InterestExpenseDebt`, `InterestExpenseNonoperating`, `InterestAndDebtExpense` (*), nessa ordem (seção 3.1.3); as marcadas com (*) são de conceito mais largo e entram com a marca | limite registrado: a despesa financeira da DFP inclui variação cambial e outros encargos; as tags americanas são de juros |
| `fornecedores` | `AccountsPayableCurrent`; se ausente, `AccountsPayableAndAccruedLiabilitiesCurrent`, com a marca de que inclui provisões | a segunda tag é mais larga |
| `passivo_total` (regra boba) | `Liabilities`; se ausente, `LiabilitiesAndStockholdersEquity` menos o patrimônio líquido com minoritários | a regra boba usa passivo total ÷ ativo total, e muitas companhias não apresentam o total do passivo |

O desvio de Benford usa os valores diferentes de zero do exercício na demonstração do balanço, do resultado e do fluxo de caixa do 10-K (pela coluna `stmt` de `pre.txt`: BS, IS e CF), o equivalente americano de BPA, BPP, DRE e DFC, com o mínimo de 20 números do v2. A DVA não existe nos EUA: o DEPI do v2 é o do v1, pela depreciação do fluxo de caixa. A cobertura de cada conta com as regras acima está na seção 3.1.2 (só contagens).

### 3.1.1 A ampliação da receita, só pela cobertura

Decisão de Roberto de 24/11/2026: as tags da receita são escolhidas só pelas contagens de cobertura, e a lista final entra no texto registrado. A lista de candidatas e a regra foram escritas no código (`RECEITA_CANDIDATAS` e `ampliar_receita`, em `chiocca/eua/fsds.py`) antes de qualquer contagem: só tags us-gaap de receita total, sem componentes, custos ou saldos. Partindo das três tags da Fase 0, entra a cada passo a candidata que cobre mais 10-K da amostra ainda sem receita (não financeiras, sem as SPACs, exercícios de 2011 a 2024: 65.096 10-K), se o ganho for de pelo menos 0,5% dessas entregas. O valor é o anual (quatro trimestres) na data de referência.

| Candidata | Ganho no primeiro passo | Entrou | Ganho quando entrou |
| --- | ---: | --- | ---: |
| `RevenueFromContractWithCustomerIncludingAssessedTax` | 2.457 | sim | 2.457 |
| `SalesRevenueGoodsNet` | 2.635 | sim | 2.635 |
| `SalesRevenueServicesNet` | 1.061 | sim | 1.047 |
| `SalesRevenueGoodsGross` | 88 | não | — |
| `RevenuesExcludingInterestAndDividends` | 8 | não | — |
| `RegulatedAndUnregulatedOperatingRevenue` | 227 | não | — |
| `ElectricUtilityRevenue` | 86 | não | — |
| `OilAndGasRevenue` | 502 | sim | 501 |
| `RevenueMineralSales` | 76 | não | — |
| `RealEstateRevenueNet` | 51 | não | — |
| `OperatingLeasesIncomeStatementLeaseRevenue` | 38 | não | — |
| `OperatingLeaseLeaseIncome` | 0 | não | — |
| `HealthCareOrganizationRevenue` | 113 | não | — |
| `ContractsRevenue` | 189 | não | — |

Entraram 4 tags. **A lista final da receita, nesta ordem de preferência: `Revenues`, `RevenueFromContractWithCustomerExcludingAssessedTax`, `SalesRevenueNet`, `SalesRevenueGoodsNet`, `RevenueFromContractWithCustomerIncludingAssessedTax`, `SalesRevenueServicesNet`, `OilAndGasRevenue`.**

Contagem de descoberta, só para transparência: entre os 17.440 10-K da amostra sem nenhuma das três tags da Fase 0, as 15 tags us-gaap mais frequentes com "Revenue" ou "Sales" no nome (valor anual na data de referência). As que estão fora das candidatas não entram pela regra; se alguma for de receita total, entrar exige uma decisão de Roberto antes do registro (seção 10).

| Tag | 10-K sem as três tags com ela | Candidata |
| --- | ---: | --- |
| `SalesRevenueGoodsNet` | 2.635 | sim |
| `RevenueFromContractWithCustomerIncludingAssessedTax` | 2.457 | sim |
| `IncreaseDecreaseInDeferredRevenue` | 1.472 | não |
| `SalesRevenueServicesNet` | 1.061 | sim |
| `CostOfRevenue` | 802 | não |
| `OilAndGasRevenue` | 502 | sim |
| `OilAndGasSalesRevenue` | 267 | não |
| `RegulatedAndUnregulatedOperatingRevenue` | 227 | sim |
| `ContractsRevenue` | 189 | sim |
| `GainLossOnSalesOfAssetsAndAssetImpairmentCharges` | 161 | não |
| `RevenueFromRelatedParties` | 150 | não |
| `GainsLossesOnSalesOfAssets` | 147 | não |
| `UnregulatedOperatingRevenue` | 135 | não |
| `RegulatedOperatingRevenueGas` | 131 | não |
| `OtherSalesRevenueNet` | 131 | não |

### 3.1.2 A cobertura do mapa ampliado

A fração dos 10-K da amostra com cada conta pelas regras da seção 3.1: presença do valor na data de referência, como na seção 2.4 da Fase 0, e, para a receita, o valor anual diferente de zero. No conjunto de 2011 a 2024, e o menor e o maior ano. Só contagens.

| Conta | 2011 a 2024 | Menor ano | Maior ano |
| --- | ---: | ---: | ---: |
| `receita_liquida` | 80,2% | 77,1% | 83,5% |
| `ativo_total` | 98,6% | 97,7% | 99,6% |
| `ativo_circulante` | 94,9% | 93,6% | 96,7% |
| `contas_a_receber` | 69,2% | 66,9% | 71,0% |
| `imobilizado` | 80,8% | 73,3% | 86,0% |
| `passivo_circulante` | 94,3% | 92,8% | 96,4% |
| `fornecedores` | 87,2% | 84,4% | 89,2% |
| `emprestimos_cp` | 31,7% | 29,3% | 34,0% |
| `emprestimos_lp` | 39,9% | 37,6% | 42,8% |
| `patrimonio_liquido` | 96,4% | 95,2% | 97,9% |
| `custo_vendas` | 58,1% | 56,0% | 61,6% |
| `resultado_bruto` | 61,0% | 59,8% | 63,4% |
| `despesas_vendas_gerais_adm` | 39,6% | 38,6% | 40,7% |
| `despesas_financeiras` | 60,3% | 54,5% | 67,1% |
| `lucro_operacoes_continuadas` | 97,4% | 95,0% | 99,4% |
| `lucro_liquido` | 97,0% | 94,1% | 99,4% |
| `caixa_operacional` | 98,8% | 97,7% | 99,7% |
| `depreciacao` | 82,8% | 81,1% | 84,7% |
| `passivo_total` | 98,0% | 96,8% | 99,2% |

Com o mapa ampliado, a regra das sem receita tira 12.873 dos 65.096 10-K da amostra, contra 19.409 com as três tags da Fase 0. A despesa financeira e o caixa operacional já estão com as tags da seção 3.1.3.

### 3.1.3 A ampliação da despesa financeira e do caixa operacional

Pedido de Roberto de 24/11/2026: a mesma regra da receita para as duas contas que perdiam cobertura. As candidatas de cada conta foram escritas no código (`AMPLIACOES` e `CONCEITO_LARGO`, em `chiocca/eua/fsds.py`) antes de qualquer contagem, todas do mesmo conceito contábil: juros da dívida; caixa líquido das atividades operacionais, inclusive a variante só de operações continuadas. As de conceito mais largo (`InterestAndDebtExpense`, juros e outros encargos da dívida, e `InterestCostsIncurred`, que inclui os juros capitalizados) entram com uma marca, como a de fornecedores. Ficam fora os juros líquidos de receita de juros e os juros pagos (outros conceitos) e as tags de componentes. Entram pela ordem de maior ganho, com pelo menos 0,5% dos 10-K da amostra, pelo valor anual (quatro trimestres) na data de referência.

**Antes, o uso de cada tag por ano** (fração dos 10-K da amostra com o valor anual da tag), para ver se as quedas vêm de troca de tag na taxonomia:

| Conta | Tag | 2011 | 2012 | 2013 | 2014 | 2015 | 2016 | 2017 | 2018 | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `despesas_financeiras` | `InterestExpense` | 59,5% | 59,2% | 58,6% | 57,8% | 56,2% | 55,2% | 54,8% | 53,5% | 53,6% | 51,9% | 50,3% | 49,0% | 49,2% | 16,9% |
| `despesas_financeiras` | `InterestExpenseNonoperating` | 0,0% | 0,0% | 0,0% | 0,0% | 0,0% | 0,0% | 0,0% | 0,0% | 0,0% | 0,0% | 0,0% | 0,0% | 0,5% | 33,1% |
| `despesas_financeiras` | `InterestExpenseOperating` | 0,0% | 0,0% | 0,0% | 0,0% | 0,0% | 0,0% | 0,0% | 0,0% | 0,0% | 0,0% | 0,0% | 0,0% | 0,0% | 1,6% |
| `despesas_financeiras` | `InterestExpenseDebt` | 4,2% | 3,5% | 3,9% | 3,3% | 3,4% | 3,2% | 3,1% | 3,2% | 3,6% | 3,6% | 3,3% | 2,9% | 2,9% | 3,0% |
| `despesas_financeiras` | `InterestExpenseBorrowings` | 0,1% | 0,1% | 0,1% | 0,2% | 0,2% | 0,1% | 0,1% | 0,1% | 0,1% | 0,1% | 0,1% | 0,1% | 0,1% | 0,1% |
| `despesas_financeiras` | `InterestAndDebtExpense` | 3,2% | 3,0% | 3,1% | 3,1% | 3,1% | 3,1% | 2,9% | 2,4% | 2,2% | 1,9% | 2,0% | 2,4% | 2,3% | 2,4% |
| `despesas_financeiras` | `InterestCostsIncurred` | 0,3% | 0,2% | 0,3% | 0,3% | 0,3% | 0,3% | 0,3% | 0,3% | 0,3% | 0,3% | 0,3% | 0,3% | 0,3% | 0,2% |
| `caixa_operacional` | `NetCashProvidedByUsedInOperatingActivities` | 86,9% | 84,7% | 77,9% | 62,1% | 57,0% | 55,0% | 74,6% | 92,6% | 96,0% | 96,4% | 97,1% | 97,8% | 97,5% | 97,5% |
| `caixa_operacional` | `NetCashProvidedByUsedInOperatingActivitiesContinuingOperations` | 15,4% | 17,2% | 24,1% | 40,0% | 45,5% | 47,5% | 27,7% | 9,9% | 6,8% | 6,3% | 5,7% | 5,3% | 5,2% | 5,4% |

Leitura: em 2024, o uso de `InterestExpense` cai para 16,9% e o de `InterestExpenseNonoperating` sobe de 0,5% no ano anterior para 33,1%; de 2013 a 2017, a variante só de operações continuadas chega a 47,5% dos 10-K, no ano em que o total cai para 55,0%. As quedas vêm de troca de tag, não de falta do dado.

| Conta | Candidata | Conceito mais largo | Ganho no primeiro passo | Entrou | Ganho quando entrou |
| --- | --- | --- | ---: | --- | ---: |
| `despesas_financeiras` | `InterestExpenseNonoperating` | não | 1.392 | sim | 1.387 |
| `despesas_financeiras` | `InterestExpenseOperating` | não | 67 | não | — |
| `despesas_financeiras` | `InterestExpenseDebt` | não | 1.822 | sim | 1.822 |
| `despesas_financeiras` | `InterestExpenseBorrowings` | não | 67 | não | — |
| `despesas_financeiras` | `InterestAndDebtExpense` | sim | 1.414 | sim | 1.379 |
| `despesas_financeiras` | `InterestCostsIncurred` | sim | 149 | não | — |
| `caixa_operacional` | `NetCashProvidedByUsedInOperatingActivitiesContinuingOperations` | não | 9.632 | sim | 9.632 |

Pelo valor anual, a cobertura da despesa financeira passa de 52,3% para 59,3% no conjunto de 2011 a 2024 e, em 2024, de 16,9% para 54,8%; 1.379 entregas ficam cobertas só por uma tag de conceito mais largo, com a marca. A do caixa operacional passa de 83,2% para 98,0% e, em 2016, de 55,0% para 97,6%. Uma parte das companhias não tem dívida nem despesa de juros, e por isso a despesa financeira não chega perto de 100%.

### 3.2 A taxa que substitui o CDI

A Effective Federal Funds Rate, série diária DFF do FRED (Federal Reserve Bank of St. Louis), cuja fonte é a publicação H.15 do Federal Reserve: pública, gratuita e sem chave. Como `chiocca.cdi.medio`, a média das taxas diárias nos 12 meses que terminam no fim do exercício, com o mesmo corte de 10 p.p. Motivo: é a taxa do overnight interbancário dos EUA, o papel do CDI no Brasil. Limite registrado: a DFF anualiza em base de 360 dias corridos e o CDI em base de 252 dias úteis. O arquivo da série entra no repositório, como `data/cdi_sgs4389.csv`, com o SHA-256 no manifesto.

### 3.3 A data de corte

A mesma regra do estudo 1 (emenda 5, `chiocca.corte.data_corte`): o último dia do quarto mês depois do fim do exercício. Motivo: o prazo do 10-K é de 60, 75 ou 90 dias, conforme o porte, e, de 2011 a 2024, o décimo de 10-K entregues mais tarde saiu até 107 dias depois da data de referência (seção 2.2 da Fase 0). A versão usada é a pública no corte: a última entrega até a data entre o 10-K original e os 10-K/A com números das contas (seção 2.3 da Fase 0). A companhia sem 10-K com XBRL até o corte fica fora daquele exercício, como no Brasil.

### 3.4 O que não se adapta

As financeiras ficam fora (decisão de Roberto de 24/11/2026): o mapa não tem as contas delas, e por isso o grupo das financeiras e o peso de ganhos não recorrentes não existem neste estudo. A DVA (seção 3.1). O leitor de documentos.

## 4. Amostra e exclusões

- **Universo:** os 10-K originais dos Financial Statement Data Sets com data de referência de 2011 a 2024 (o exercício é o ano da data de referência, como na DFP). 2011, porque o XBRL vale para todas as companhias a partir dos períodos depois de 15/06/2011; 2024, porque a janela de 12 meses desse exercício já terminou, em 30/04/2026 (decisão de Roberto de 24/11/2026).
- **Exclusões, nesta ordem, cada uma contada no relatório:** (1) sem versão pública com XBRL até o corte; (2) as financeiras pela SIC, de 6000 a 6999, exceto 6770 (seção 3.4); (3) as SPACs, SIC 6770, regra explícita decidida por Roberto em 24/11/2026; (4) as sem receita (receita ausente ou zero, a regra do estudo 1, pelo mapa ampliado); (5) as sem nenhum sinal calculável. A SIC e a receita são as da versão usada.
- **O tamanho, pela Fase 0 (exercício declarado, mapa da Fase 0):** de 2011 a 2024, 86.766 10-K originais: 18.628 de financeiras, 3.042 de SPACs (2.905 delas já sem receita) e 19.409 das demais sem receita pelo mapa da Fase 0; ficam 45.687. Com o mapa ampliado (seção 3.1.2), as demais sem receita são 12.873, e ficam 52.223.

## 5. O desfecho: o 8-K com o item 4.02, por caso

- **Episódio (o caso):** o primeiro 8-K de uma companhia com o item 4.02 no campo de itens do EDGAR abre um episódio; todo 8-K ou 8-K/A com o item 4.02 da mesma companhia nos 365 dias seguintes pertence a ele; depois disso, um novo 8-K 4.02 abre outro episódio. Cada episódio conta uma vez, a resposta à crítica de Walker e de Gow a Bao et al. (Fase 0, seção 5.1).
- **Janela:** a empresa-ano t é positiva se um episódio se abre depois do corte de t e até 12 meses depois dele. As janelas de exercícios seguidos da mesma companhia não se sobrepõem, e cada episódio cai em no máximo uma empresa-ano. Os episódios fora de qualquer empresa-ano da amostra entram só na descrição.
- **Fonte:** o campo de itens do histórico de entregas do EDGAR (`submissions.zip`), baixado de novo no dia do cálculo, com o SHA-256 no manifesto, e só os 8-K entregues até 30/04/2026, o fim da janela do exercício de 2024.
- **O tamanho, pela Fase 0:** de 2009 a 30/04/2026, 2.386 companhias-ano com 8-K 4.02 e 10-K nos dados da SEC antes do 8-K: 263 de financeiras, 363 de SPACs e 617 das demais sem receita pelo mapa da Fase 0; ficam 1.143, de 48 a 111 por ano de entrega de 2012 a 2025. Com o mapa ampliado, ficam 1.312, de 58 a 136 por ano.
- **Limites:** o item 4.02 não diz quais demonstrações deixaram de valer: o desfecho é uma declaração de não confiabilidade nos 12 meses seguintes, sem garantia de que trata do exercício t. As republicações sem 8-K ("little r") ficam de fora. Nada disso é chamado de fraude.

## 6. Métricas: as do estudo 2

- **Medida principal:** a diferença de risco DR = P(positiva | em alerta) − P(positiva | fora de alerta), nas empresa-anos avaliadas pelo v1, com todos os exercícios juntos; também a razão de taxas.
- **Bootstrap por companhia:** sorteiam-se companhias com reposição, cada uma com todas as suas empresa-anos; 10.000 reamostragens, com a semente 20270430 (decisão de Roberto de 24/11/2026); o intervalo é o percentil unilateral de 95%. As funções são `taxas`, `dr`, `bootstrap_por_companhia` e `limite_inferior` de `chiocca/v2/estudo2/secundaria.py`, chamadas sem mudar nenhuma linha.
- **Resultado:** "associação positiva" se o limite inferior do intervalo unilateral de 95% da DR ficar acima de zero; senão, "sem evidência de associação".
- **Regra boba lado a lado:** o decil mais endividado (passivo total ÷ ativo total) de cada exercício, como no estudo 1, com a mesma DR e o bootstrap pareado (as mesmas reamostragens): "o motor separa melhor que a regra boba" só se o limite inferior da diferença ficar acima de zero.
- **O v2 pareado com o v1:** como na emenda 5 do estudo 2. O alerta do v2 sai de todas as empresa-anos que o v2 avalia; as medidas são calculadas nas empresa-anos avaliadas pelo v1; "o v2 separa melhor que o v1" só se o limite inferior da diferença pareada ficar acima de zero; senão, sem vencedor declarado.
- **Descritivas:** as métricas de ranking do estudo 2 (precisão e lift no topo de 1%, 5% e 10% e NDCG@k), cada exercício separado e os AAERs (seção 7). Só agregados: nenhuma lista de companhias por alerta.

## 7. Os AAERs de 2009 a 2014: descrição à parte

Para os 25 casos de Bao et al. (47 empresa-anos) com 10-K nos dados da SEC (Fase 0, seção 4.1): quantos casos o v1, o v2 e a regra boba alertaram em pelo menos um exercício afetado, com a versão pública no corte. Só contagens, sem teste e sem lista. Em 2009 e 2010, só as companhias maiores entregavam em XBRL.

## 8. Previsões escritas antes dos dados

Revistas em 24/11/2026 para o período novo (2011 a 2024) e o mapa ampliado, e de novo depois da ampliação da despesa financeira e do caixa operacional (seção 3.1.3). Nenhuma faixa mudou; o motivo de cada uma vem ao lado.

1. **Taxa de alerta do v1:** entre 25% e 45% das não financeiras avaliadas em cada exercício. Motivo: o M-score acima de -1,78 marca parte relevante das companhias americanas, e o decil do DPO soma 10%; o juro implícito dispara menos que no Brasil, porque a despesa de juros americana não inclui variação cambial. **Sem ajuste:** o período novo acrescenta exercícios de juros altos (2022 a 2024), em que o juro implícito dispara menos (o corte sobe com a taxa de referência), mas o M-score e o DPO não dependem dos juros, e a faixa já cobre essa variação. **Sem ajuste depois da seção 3.1.3:** com mais juros e mais caixa operacional calculáveis, o juro implícito e o M-score passam a ser calculados em mais empresa-anos (o juro implícito, sobretudo em 2024), o que pode subir um pouco a taxa de alerta nesses anos, dentro da faixa.
2. **Taxa de alerta do v2:** entre 10,0% e 11,0% em cada exercício. **Sem ajuste:** vem da construção do decil, com qualquer cobertura.
3. **Taxa do desfecho:** entre 1,5% e 4% das empresa-anos avaliadas. **Sem ajuste:** com o mapa ampliado, ficam 1.312 companhias-ano com 8-K 4.02 e 10-K antes (seção 5), de 58 a 136 por ano de entrega, contra cerca de 4.600 10-K da amostra por exercício antes da regra das sem receita: perto de 2% a 3%.
4. **DR do v1:** positiva, com razão de taxas entre 1,1 e 1,5, e "associação positiva" mais provável que não. **Sem ajuste:** a amostra maior só reforça o poder.
5. **DR do v2:** positiva, com razão de taxas entre 1,2 e 2,0, e "associação positiva". **Sem ajuste.**
6. **O v2 pareado com o v1:** diferença positiva, com o limite inferior acima de zero ("o v2 separa melhor que o v1"). Motivo: o grupo em alerta do v2 é menor e mais extremo. **Sem ajuste.**
7. **O v2 contra a regra boba:** sem vencedor declarado. Motivo: o endividamento também se associa a republicações, pela dificuldade financeira. **Sem ajuste.**
8. **AAERs:** dos 25 casos, entre 30% e 60% em alerta no v1 e entre 10% e 30% no v2 em pelo menos um exercício afetado. **Sem ajuste:** a descrição dos AAERs não depende do período da amostra.

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

Decidido: (a) as financeiras ficam fora (seção 3.4); (b) as tags da receita são escolhidas só pelas contagens de cobertura, e a lista final entra no texto registrado (seção 3.1.1); (c) a amostra vai até o exercício de 2024, com os dados da SEC e os 8-K baixados de novo no dia do cálculo; (d) a semente é 20270430; (e) os arquivos da SEC ficam fora do Git, com o SHA-256 no manifesto e o download por script; (f) o calendário tem meta e reserva (seção 9).

Para a revisão do Claude (claude.ai) e de Roberto, antes do registro:

1. As tags da contagem de descoberta fora das candidatas (seção 3.1.1): nenhuma entra sem decisão de Roberto.
2. O exercício pela data de referência, como na DFP; as contagens da Fase 0 usam o exercício declarado pela companhia (`fy`), e a diferença entre os dois é pequena.
3. As quedas de cobertura da despesa financeira e do caixa operacional: tratadas na seção 3.1.3, pela mesma regra da receita (terceira rodada, 24/11/2026).
4. A leitura do texto inteiro, que é registrado como estiver depois da revisão.

## 11. O que fica de fora

As financeiras, a DVA e o leitor (seção 3.4); qualquer lista ou ordem de companhias por alerta; qualquer recomendação de investimento; e, até decisão de Roberto, a frente dos EUA no README e no produto.
