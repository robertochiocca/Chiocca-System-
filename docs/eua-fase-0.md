# Fase 0 dos EUA: reconhecimento dos dados

> **Reconhecimento, sem nenhum sinal calculado.** Objetivo: saber se dá para fazer, nos EUA, um estudo pré-registrado com os dados como eram na época, testando os sinais do v1 e do v2 do Chiocca e a regra boba contra um rótulo público de demonstrações erradas. Só inventário e contagens; nada de 2024 em diante; nenhum nome de pessoa física nem de companhia; nenhum valor de sinal, acerto, alerta ou ranking. A frente dos EUA fica fora do README e do produto até decisão de Roberto.

## 1. Acesso à SEC

A SEC pede um User-Agent com nome e contato e no máximo 10 pedidos por segundo; sem o contato, recusa o pedido (HTTP 403). Os scripts leem o User-Agent da variável de ambiente `SEC_USER_AGENT`, que nenhum arquivo versionado nem log guarda, e esperam pelo menos 0,11 segundo entre pedidos. Em 23/11/2026, com a variável definida nas configurações do ambiente, foram baixados os **60 de 60 arquivos trimestrais** dos Financial Statement Data Sets (4,6 GB) e o histórico de entregas do EDGAR (`submissions.zip`, 1,6 GB, retrato da SEC baixado em 23/11/2026). Os arquivos ficam em `data/eua/`, fora do Git, com o tamanho e o SHA-256 de cada um em `data/eua_manifesto.csv`.

## 2. Balanços: os Financial Statement Data Sets da SEC

Os números das demonstrações em XBRL, num zip por trimestre de entrega desde 2009 (aqui, de 2009q1 a 2023q4: os 10-K dos exercícios de 2023, quase todos entregues em 2024, ficam de fora). Os dois arquivos usados são `sub.txt` (uma linha por entrega: CIK, formulário, data de referência, exercício fiscal, datas de entrega e se a entrega foi emendada depois) e `num.txt` (uma linha por número: tag, taxonomia, data, trimestres cobertos, unidade e valor).

- **10-K e 10-K/A:** a entrega original e cada emenda são entregas separadas, cada uma com a sua data; `prevrpt` marca a entrega que foi emendada depois.
- **A versão pública numa data de corte:** por companhia e exercício, a última entrega entregue até a data, entre o 10-K original e os 10-K/A com números das contas do mapa, como o "como era" do Chiocca no Brasil. Uma emenda sem esses números (só a parte III do 10-K, por exemplo) não muda a versão. O comparativo do exercício seguinte traz os números de t-1 como apresentados depois.

### 2.1 Estrutura dos arquivos

Cada zip traz `sub.txt`, `num.txt`, `pre.txt` e `tag.txt` (texto separado por tabulação) e um `readme.htm`. As colunas usadas foram conferidas em todos os 60 trimestres antes de qualquer conta. 2009q1 não tem nenhuma entrega (só os cabeçalhos): os primeiros 10-K em XBRL entram a partir de 2009q2. O último trimestre (2023q4):

| Arquivo | Colunas | Linhas |
| --- | ---: | ---: |
| `num.txt` | 10 | 3.699.124 |
| `pre.txt` | 10 | 769.208 |
| `readme.htm` | — | — |
| `sub.txt` | 36 | 6.882 |
| `tag.txt` | 9 | 88.228 |

As colunas de `sub.txt` (36) e de `num.txt` (10) são as mesmas nos 60 trimestres. `num.txt` traz `coreg` (co-registrante) e `segments` (segmento): o código só conta o número da própria companhia, com as duas vazias.

### 2.2 10-K e 10-K/A por exercício e datas de entrega

Por exercício fiscal declarado pela companhia (`fy`). O prazo é a diferença em dias entre a data de referência e a entrega do 10-K original. As emendas com números são os 10-K/A com alguma tag do mapa na data de referência; as demais (a maioria) só trazem a parte III ou a capa. O exercício de 2023 está incompleto: a maior parte foi entregue em 2024.

| Exercício | Companhias com 10-K | 10-K | 10-K/A | 10-K/A com números | 10-K emendados depois | Prazo mediano (dias) | Prazo, 10% a 90% (dias) | Até 90 dias |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 2009 | 425 | 425 | 18 | 18 | 12 | 56 | 46–60 | 100% |
| 2010 | 1.308 | 1.310 | 80 | 78 | 31 | 56 | 47–60 | 99% |
| 2011 | 6.541 | 6.546 | 628 | 620 | 303 | 75 | 54–105 | 84% |
| 2012 | 6.920 | 6.928 | 692 | 686 | 301 | 74 | 52–105 | 76% |
| 2013 | 6.905 | 6.934 | 566 | 563 | 287 | 73 | 52–105 | 81% |
| 2014 | 6.813 | 6.833 | 421 | 416 | 236 | 72 | 51–105 | 83% |
| 2015 | 6.455 | 6.463 | 319 | 316 | 174 | 71 | 50–105 | 82% |
| 2016 | 5.974 | 5.982 | 293 | 293 | 179 | 69 | 50–106 | 84% |
| 2017 | 5.905 | 5.912 | 276 | 275 | 179 | 68 | 51–105 | 81% |
| 2018 | 5.768 | 5.772 | 209 | 206 | 145 | 67 | 50–105 | 81% |
| 2019 | 5.601 | 5.607 | 206 | 204 | 140 | 66 | 50–107 | 84% |
| 2020 | 5.746 | 5.751 | 570 | 569 | 404 | 68 | 49–100 | 87% |
| 2021 | 6.493 | 6.497 | 319 | 318 | 257 | 70 | 49–102 | 86% |
| 2022 | 6.219 | 6.220 | 289 | 289 | 263 | 69 | 48–103 | 86% |
| 2023 | 685 | 685 | 33 | 33 | 31 | 69 | 45–105 | 82% |

### 2.3 A versão pública numa data de corte

Por exercício, em 31 de dezembro do ano seguinte (t+1) e do outro (t+2), só cortes até 31/12/2023: quantas companhias têm uma versão pública e em quantas ela já é uma emenda com números, e não o 10-K original.

| Exercício | Companhias em t+1 | Emenda em t+1 | Companhias em t+2 | Emenda em t+2 |
| --- | ---: | ---: | ---: | ---: |
| 2009 | 425 | 12 | 425 | 12 |
| 2010 | 1.301 | 23 | 1.305 | 27 |
| 2011 | 6.473 | 240 | 6.521 | 288 |
| 2012 | 6.846 | 255 | 6.899 | 285 |
| 2013 | 6.844 | 246 | 6.893 | 277 |
| 2014 | 6.745 | 199 | 6.794 | 226 |
| 2015 | 6.367 | 137 | 6.431 | 156 |
| 2016 | 5.889 | 141 | 5.950 | 168 |
| 2017 | 5.836 | 167 | 5.886 | 177 |
| 2018 | 5.704 | 119 | 5.747 | 134 |
| 2019 | 5.517 | 113 | 5.590 | 126 |
| 2020 | 5.722 | 376 | 5.745 | 390 |
| 2021 | 6.479 | 211 | 6.493 | 243 |
| 2022 | 6.219 | 215 | — | — |
| 2023 | — | — | — | — |

### 2.4 O mapa das contas para as tags us-gaap e a cobertura por ano

As contas que os sinais do v1 e do v2 usam, com as tags candidatas na ordem de preferência. Benford usa todos os números e não precisa de mapa; a DVA não existe nos EUA (a depreciação vem da DFC); nos EUA, despesas de vendas e administrativas costumam vir juntas (SG&A), e muitas companhias não apresentam o resultado bruto. As financeiras (peso de ganhos não recorrentes) ficam sem mapa nesta fase.

| Conta | Tags us-gaap candidatas |
| --- | --- |
| `ativo_total` | `Assets` |
| `ativo_circulante` | `AssetsCurrent` |
| `contas_a_receber` | `AccountsReceivableNetCurrent`, `ReceivablesNetCurrent` |
| `imobilizado` | `PropertyPlantAndEquipmentNet` |
| `passivo_circulante` | `LiabilitiesCurrent` |
| `fornecedores` | `AccountsPayableCurrent`, `AccountsPayableAndAccruedLiabilitiesCurrent` |
| `emprestimos_cp` | `DebtCurrent`, `LongTermDebtCurrent`, `ShortTermBorrowings` |
| `emprestimos_lp` | `LongTermDebtNoncurrent`, `LongTermDebtAndCapitalLeaseObligations` |
| `patrimonio_liquido` | `StockholdersEquity`, `StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest` |
| `receita_liquida` | `Revenues`, `RevenueFromContractWithCustomerExcludingAssessedTax`, `SalesRevenueNet` |
| `custo_vendas` | `CostOfRevenue`, `CostOfGoodsAndServicesSold`, `CostOfGoodsSold` |
| `resultado_bruto` | `GrossProfit` |
| `despesas_vendas_gerais_adm` | `SellingGeneralAndAdministrativeExpense` |
| `despesas_financeiras` | `InterestExpense` |
| `lucro_operacoes_continuadas` | `IncomeLossFromContinuingOperations`, `IncomeLossFromContinuingOperationsBeforeIncomeTaxesExtraordinaryItemsNoncontrollingInterest` |
| `lucro_liquido` | `NetIncomeLoss`, `ProfitLoss` |
| `caixa_operacional` | `NetCashProvidedByUsedInOperatingActivities` |
| `depreciacao` | `DepreciationDepletionAndAmortization`, `DepreciationAndAmortization`, `Depreciation` |
| `juros_pagos` | `InterestPaidNet`, `InterestPaid` |

A cobertura é a fração dos 10-K originais de cada exercício com valor em dólar na data de referência, da própria companhia (sem co-registrante nem segmento), na taxonomia us-gaap. Por conta (alguma das tags candidatas):

| Conta | 2009 | 2010 | 2011 | 2012 | 2013 | 2014 | 2015 | 2016 | 2017 | 2018 | 2019 | 2020 | 2021 | 2022 | 2023 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `ativo_total` | 97% | 98% | 97% | 98% | 97% | 98% | 98% | 98% | 98% | 98% | 98% | 99% | 99% | 99% | 99% |
| `ativo_circulante` | 82% | 79% | 74% | 75% | 76% | 76% | 76% | 76% | 76% | 77% | 78% | 78% | 81% | 81% | 87% |
| `contas_a_receber` | 71% | 70% | 53% | 53% | 54% | 54% | 54% | 55% | 55% | 56% | 56% | 53% | 52% | 53% | 61% |
| `imobilizado` | 87% | 85% | 75% | 75% | 75% | 76% | 76% | 76% | 77% | 78% | 75% | 70% | 65% | 66% | 72% |
| `passivo_circulante` | 82% | 79% | 73% | 75% | 75% | 76% | 76% | 76% | 76% | 77% | 77% | 78% | 81% | 80% | 86% |
| `fornecedores` | 73% | 71% | 66% | 68% | 70% | 70% | 70% | 70% | 70% | 71% | 72% | 71% | 72% | 72% | 79% |
| `emprestimos_cp` | 57% | 48% | 27% | 26% | 27% | 27% | 28% | 28% | 29% | 29% | 28% | 27% | 25% | 25% | 32% |
| `emprestimos_lp` | 68% | 57% | 29% | 30% | 30% | 31% | 32% | 33% | 34% | 34% | 33% | 32% | 30% | 30% | 36% |
| `patrimonio_liquido` | 96% | 96% | 93% | 93% | 93% | 94% | 94% | 94% | 95% | 95% | 96% | 97% | 97% | 97% | 98% |
| `receita_liquida` | 80% | 74% | 66% | 67% | 68% | 67% | 68% | 69% | 68% | 73% | 73% | 72% | 68% | 69% | 75% |
| `custo_vendas` | 52% | 52% | 42% | 44% | 44% | 44% | 44% | 44% | 46% | 49% | 49% | 47% | 45% | 45% | 61% |
| `resultado_bruto` | 26% | 34% | 36% | 37% | 37% | 37% | 36% | 36% | 37% | 37% | 37% | 36% | 35% | 36% | 53% |
| `despesas_vendas_gerais_adm` | 49% | 45% | 31% | 31% | 31% | 31% | 31% | 32% | 32% | 32% | 33% | 32% | 29% | 30% | 42% |
| `despesas_financeiras` | 64% | 68% | 62% | 62% | 62% | 61% | 60% | 59% | 59% | 58% | 57% | 55% | 51% | 51% | 53% |
| `lucro_operacoes_continuadas` | 28% | 21% | 30% | 34% | 38% | 41% | 46% | 49% | 50% | 52% | 54% | 53% | 63% | 69% | 73% |
| `lucro_liquido` | 96% | 98% | 93% | 94% | 94% | 95% | 96% | 96% | 97% | 98% | 98% | 99% | 99% | 99% | 99% |
| `caixa_operacional` | 90% | 93% | 87% | 85% | 77% | 61% | 56% | 55% | 75% | 93% | 97% | 97% | 98% | 98% | 97% |
| `depreciacao` | 79% | 81% | 73% | 74% | 75% | 75% | 76% | 76% | 77% | 78% | 77% | 74% | 71% | 73% | 75% |
| `juros_pagos` | 48% | 56% | 64% | 65% | 66% | 65% | 66% | 67% | 67% | 68% | 68% | 66% | 62% | 64% | 67% |

Por tag:

| Tag | 2009 | 2010 | 2011 | 2012 | 2013 | 2014 | 2015 | 2016 | 2017 | 2018 | 2019 | 2020 | 2021 | 2022 | 2023 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `Assets` | 97% | 98% | 97% | 98% | 97% | 98% | 98% | 98% | 98% | 98% | 98% | 99% | 99% | 99% | 99% |
| `AssetsCurrent` | 82% | 79% | 74% | 75% | 76% | 76% | 76% | 76% | 76% | 77% | 78% | 78% | 81% | 81% | 87% |
| `AccountsReceivableNetCurrent` | 51% | 53% | 46% | 47% | 47% | 48% | 48% | 48% | 49% | 49% | 49% | 48% | 46% | 47% | 53% |
| `ReceivablesNetCurrent` | 20% | 17% | 7% | 7% | 7% | 7% | 7% | 7% | 7% | 7% | 7% | 6% | 5% | 5% | 8% |
| `PropertyPlantAndEquipmentNet` | 87% | 85% | 75% | 75% | 75% | 76% | 76% | 76% | 77% | 78% | 75% | 70% | 65% | 66% | 72% |
| `LiabilitiesCurrent` | 82% | 79% | 73% | 75% | 75% | 76% | 76% | 76% | 76% | 77% | 77% | 78% | 81% | 80% | 86% |
| `AccountsPayableCurrent` | 61% | 61% | 53% | 53% | 53% | 54% | 54% | 54% | 55% | 56% | 56% | 56% | 57% | 57% | 62% |
| `AccountsPayableAndAccruedLiabilitiesCurrent` | 12% | 11% | 14% | 16% | 17% | 17% | 16% | 16% | 16% | 16% | 16% | 16% | 15% | 15% | 18% |
| `DebtCurrent` | 20% | 12% | 4% | 4% | 4% | 4% | 5% | 5% | 5% | 5% | 4% | 4% | 3% | 4% | 5% |
| `LongTermDebtCurrent` | 24% | 26% | 16% | 16% | 17% | 17% | 18% | 18% | 18% | 18% | 17% | 18% | 17% | 16% | 20% |
| `ShortTermBorrowings` | 20% | 16% | 8% | 8% | 7% | 7% | 7% | 8% | 8% | 8% | 8% | 8% | 6% | 7% | 9% |
| `LongTermDebtNoncurrent` | 45% | 41% | 22% | 22% | 23% | 23% | 25% | 25% | 26% | 26% | 26% | 25% | 24% | 24% | 28% |
| `LongTermDebtAndCapitalLeaseObligations` | 24% | 16% | 7% | 7% | 8% | 8% | 8% | 8% | 8% | 8% | 8% | 7% | 6% | 6% | 8% |
| `StockholdersEquity` | 81% | 84% | 87% | 89% | 89% | 90% | 90% | 90% | 91% | 91% | 92% | 93% | 93% | 93% | 92% |
| `StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest` | 64% | 57% | 29% | 28% | 30% | 30% | 31% | 32% | 32% | 33% | 33% | 31% | 30% | 31% | 34% |
| `Revenues` | 53% | 43% | 41% | 42% | 42% | 43% | 42% | 43% | 44% | 46% | 39% | 36% | 32% | 32% | 33% |
| `RevenueFromContractWithCustomerExcludingAssessedTax` | 0% | 0% | 0% | 0% | 0% | 0% | 0% | 0% | 0% | 27% | 37% | 39% | 38% | 40% | 43% |
| `SalesRevenueNet` | 29% | 33% | 26% | 27% | 27% | 27% | 27% | 27% | 26% | 2% | 0% | 0% | 0% | 0% | 0% |
| `CostOfRevenue` | 16% | 15% | 14% | 15% | 15% | 16% | 16% | 17% | 18% | 19% | 18% | 18% | 18% | 19% | 24% |
| `CostOfGoodsAndServicesSold` | 16% | 17% | 12% | 12% | 12% | 11% | 11% | 11% | 11% | 29% | 32% | 30% | 27% | 27% | 37% |
| `CostOfGoodsSold` | 26% | 25% | 21% | 21% | 21% | 21% | 21% | 21% | 21% | 2% | 0% | 0% | 0% | 0% | 0% |
| `GrossProfit` | 26% | 34% | 36% | 37% | 37% | 37% | 36% | 36% | 37% | 37% | 37% | 36% | 35% | 36% | 53% |
| `SellingGeneralAndAdministrativeExpense` | 49% | 45% | 31% | 31% | 31% | 31% | 31% | 32% | 32% | 32% | 33% | 32% | 29% | 30% | 42% |
| `InterestExpense` | 64% | 68% | 62% | 62% | 62% | 61% | 60% | 59% | 59% | 58% | 57% | 55% | 51% | 51% | 53% |
| `IncomeLossFromContinuingOperations` | 28% | 21% | 15% | 15% | 15% | 14% | 12% | 11% | 9% | 8% | 8% | 7% | 7% | 6% | 7% |
| `IncomeLossFromContinuingOperationsBeforeIncomeTaxesExtraordinaryItemsNoncontrollingInterest` | 0% | 0% | 18% | 23% | 27% | 31% | 39% | 42% | 46% | 48% | 50% | 49% | 61% | 67% | 72% |
| `NetIncomeLoss` | 85% | 87% | 86% | 88% | 88% | 90% | 90% | 90% | 91% | 92% | 92% | 93% | 94% | 93% | 95% |
| `ProfitLoss` | 60% | 54% | 32% | 32% | 33% | 32% | 33% | 33% | 36% | 44% | 48% | 48% | 52% | 50% | 46% |
| `NetCashProvidedByUsedInOperatingActivities` | 90% | 93% | 87% | 85% | 77% | 61% | 56% | 55% | 75% | 93% | 97% | 97% | 98% | 98% | 97% |
| `DepreciationDepletionAndAmortization` | 32% | 38% | 36% | 37% | 38% | 38% | 39% | 39% | 40% | 40% | 41% | 39% | 38% | 39% | 41% |
| `DepreciationAndAmortization` | 35% | 32% | 25% | 24% | 25% | 25% | 26% | 25% | 25% | 24% | 24% | 23% | 22% | 23% | 20% |
| `Depreciation` | 18% | 19% | 21% | 22% | 22% | 22% | 22% | 22% | 22% | 22% | 22% | 20% | 19% | 20% | 21% |
| `InterestPaidNet` | 25% | 25% | 13% | 13% | 13% | 13% | 14% | 14% | 32% | 54% | 61% | 60% | 58% | 60% | 62% |
| `InterestPaid` | 22% | 31% | 51% | 52% | 52% | 52% | 53% | 53% | 36% | 14% | 7% | 5% | 4% | 3% | 5% |

## 3. Rótulos

### 3.1 Os AAERs

**era-py 0.0.37** (PyPI, de Ian Gow, os dados do livro *Empirical Research in Accounting: Tools and Methods*): licença do pacote MIT; as tabelas não trazem licença própria, e a origem da ligação gvkey–CIK não é informada. Por isso nada delas é copiado para o repositório: a roda fica em `data/eua/`, com o SHA-256 no manifesto (`5f79fc223a17af9147b65a9a24f918355fc8a31f9341cd7fed8c0267b3591c0c`).

- **O índice de AAERs da SEC** (`aaer_dates`, atualizado pelo autor até 08/10/2026): número, data, descrição e ano. Até 2023, 3.277 AAERs (3.248 números distintos), de 1999 a 2023. A descrição traz nomes de companhias e de pessoas físicas e não é lida aqui.
- **As empresa-anos de Bao et al. (2020)** (`aaer_firm_year`): 415 linhas, 412 AAERs e 402 companhias, identificadas pelo gvkey (Compustat), com o primeiro e o último ano afetados, de 1990 a 2014: 990 empresa-anos com balanço errado alegado. 233 dos AAERs afetam mais de um ano.
- **A ligação gvkey–CIK** (`gvkey_ciks`): 49.089 ligações, 29.099 gvkeys e 27.708 CIKs, com as datas de cada ligação. Com ela, cada empresa-ano de Bao et al. se liga ao CIK da SEC sem a Compustat.
- **A base da CFRM (Berkeley), usada por Dechow et al. (2011):** hoje vendida pelo site da USC (página "Buy the Data", pagamento pelo cashnet; o preço não aparece no texto da página); os termos proíbem passar a base a terceiros, exceto coautores; cobre 4.581 AAERs emitidos de 17/05/1982 a 31/12/2025, com o nome e os identificadores da companhia, as contas afetadas e os anos e trimestres errados (a página não diz quais identificadores). Só as condições de acesso foram lidas.
- **A lista pública de AAERs no site da SEC:** não foi lida diretamente; o índice do era-py é uma cópia dela, com a data da atualização.

**Como ligar cada AAER ao CIK sem a Compustat.** Até 2014, pelas empresa-anos de Bao et al. e pela ligação gvkey–CIK do era-py. Depois de 2014, não há base livre com os anos errados: o caminho é ler cada AAER no site da SEC (a companhia é parte do processo) e casar o nome com o arquivo de nomes e CIKs da SEC, guardando só a companhia e o CIK.

### 3.2 Um rótulo novo: os 8-K com o item 4.02

Desde agosto de 2004, a companhia entrega um 8-K com o item 4.02 (*Non-Reliance on Previously Issued Financial Statements or a Related Audit Report or Completed Interim Review*) quando ela, ou o auditor, conclui que demonstrações já publicadas não devem mais ser usadas por causa de um erro; a republicação vem depois. É o mesmo conceito da republicação do estudo 2 no Brasil: a informação publicada estava errada, por erro ou de propósito, sem dizer qual. A fonte é o campo de itens (`items`) do histórico de entregas de cada companhia no EDGAR (`submissions.zip`), que lista os itens de cada 8-K; só a data, o formulário, os itens e o CIK são lidos, em memória, sem o texto do 8-K nem o nome da companhia (`chiocca/eua/itens.py`). Uma entrega de várias companhias conta uma vez nas contagens de entregas.

## 4. Contagens

### 4.1 AAERs de Bao et al. com 10-K nos dados da SEC

| Exercício | Empresa-anos com AAER (Bao et al.) | Ligadas a um CIK | Com 10-K nos dados da SEC | Empresa-anos com 10-K (todas as companhias) |
| --- | ---: | ---: | ---: | ---: |
| 2009 | 31 | 30 | 3 | 444 |
| 2010 | 26 | 24 | 5 | 1.337 |
| 2011 | 22 | 22 | 15 | 6.728 |
| 2012 | 19 | 19 | 14 | 6.931 |
| 2013 | 11 | 11 | 6 | 6.889 |
| 2014 | 4 | 4 | 4 | 6.803 |
| **Total** | **113** | **110** | **47** | 29.132 |

O exercício é o da convenção da Compustat, usada por Bao et al.: o ano da data de referência, ou o anterior quando o exercício termina de janeiro a maio. Uma empresa-ano de Bao et al. tem 10-K nos dados da SEC quando algum CIK ligado ao gvkey naquele ano entregou um 10-K original com XBRL para aquele exercício. **De 2009 a 2014, 113 empresa-anos com AAER, 110 ligadas a um CIK e 47 com 10-K nos dados da SEC**, contra cerca de 6.800 companhias com 10-K por ano de 2011 a 2014, quando o XBRL já valia para todas. Contando cada caso (AAER) uma vez: **25 casos**, de 25 companhias, com pelo menos um exercício afetado com 10-K de 2009 a 2014 (pelo primeiro desses exercícios: 2009: 3, 2010: 3, 2011: 9, 2012: 8, 2013: 1, 2014: 1). Os anos mais recentes têm menos casos porque um AAER costuma sair anos depois dos fatos, e a base termina em 2014. O índice da SEC tem 1.572 AAERs emitidos de 2009 a 2023, de todos os tipos (não só balanço errado).

### 4.2 8-K com o item 4.02 e 10-K/A por ano de entrega

| Ano de entrega | 8-K 4.02 | 8-K/A 4.02 | Companhias com 8-K 4.02 | Delas com SIC 6770 (SPACs) | Primeira vez desde 2009 | Com 10-K nos dados da SEC | Com 10-K nos dados da SEC antes do 8-K | 10-K (EDGAR) | 10-K/A (EDGAR) | 10-K/A com XBRL (dados da SEC) |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 2009 | 388 | 116 | 361 | 3 | 361 | 219 | 0 | 9.494 | 2.277 | 2 |
| 2010 | 387 | 104 | 362 | 3 | 320 | 226 | 0 | 8.890 | 2.111 | 18 |
| 2011 | 346 | 82 | 315 | 8 | 258 | 237 | 13 | 8.561 | 1.983 | 98 |
| 2012 | 302 | 63 | 278 | 7 | 228 | 250 | 139 | 8.154 | 1.814 | 680 |
| 2013 | 273 | 66 | 255 | 11 | 199 | 247 | 219 | 7.832 | 1.727 | 641 |
| 2014 | 213 | 44 | 194 | 9 | 147 | 188 | 170 | 7.770 | 1.477 | 534 |
| 2015 | 201 | 21 | 186 | 7 | 149 | 179 | 166 | 7.659 | 1.210 | 424 |
| 2016 | 166 | 18 | 152 | 3 | 105 | 150 | 140 | 7.259 | 1.129 | 302 |
| 2017 | 133 | 13 | 123 | 5 | 95 | 119 | 115 | 6.984 | 914 | 286 |
| 2018 | 130 | 7 | 124 | 3 | 100 | 121 | 117 | 6.827 | 989 | 307 |
| 2019 | 97 | 6 | 90 | 4 | 64 | 89 | 87 | 6.660 | 983 | 234 |
| 2020 | 96 | 8 | 92 | 5 | 71 | 90 | 85 | 6.508 | 905 | 192 |
| 2021 | 840 | 26 | 678 | 492 | 650 | 669 | 382 | 6.933 | 1.081 | 532 |
| 2022 | 288 | 19 | 270 | 132 | 170 | 267 | 189 | 7.538 | 863 | 334 |
| 2023 | 240 | 29 | 219 | 61 | 138 | 213 | 207 | 7.118 | 879 | 335 |
| **Total** | **4.100** | **622** | **3.699** | **753** | **3.055** | **3.264** | **2.029** | **114.187** | **20.342** | **4.919** |

Uma companhia conta uma vez por ano; "primeira vez desde 2009" conta cada companhia uma vez no período. "Com 10-K nos dados da SEC" quer dizer que o CIK tem um 10-K original nos Financial Statement Data Sets de 2009q1 a 2023q4; "antes do 8-K", que o primeiro desses 10-K foi entregue até a data do 8-K (há demonstrações em XBRL da época para comparar). **De 2009 a 2023: 4.100 8-K com o item 4.02, de 3.699 companhias-ano; 3.055 companhias distintas; 3.264 companhias-ano com 10-K nos dados da SEC, 2.029 delas com o 10-K antes do 8-K.** Os 10-K/A são de todos os tipos (a maioria só completa a parte III); a última coluna conta os que estão nos dados da SEC, por ano de entrega. O pico de 2021 coincide com a declaração da equipe da SEC de 12/04/2021 sobre a contabilização de warrants das SPACs (companhias de aquisição, sem operação), seguida de muitas republicações: 492 das 678 companhias com 8-K 4.02 em 2021 têm o código SIC 6770 (blank checks) nos dados da SEC; de 2009 a 2023, 753 companhias-ano.

## 5. Decisões

### 5.1 Decisões de Roberto (24/11/2026)

1. **Desfecho principal: o 8-K com o item 4.02**, o mesmo conceito da republicação do estudo 2. Os AAERs de 2009 a 2014 ficam só como descrição, sem teste.
2. **Desfecho por caso:** cada episódio contado uma vez (uma companhia, um episódio de 8-K 4.02, com os 8-K e 8-K/A do mesmo episódio juntos), com bootstrap por companhia, como no estudo 2. É a resposta à crítica de Walker (2021 e 2022) e de Gow (2022) a Bao et al. (2020), em que fraudes de vários anos que atravessam o treino e o teste inflam a medida; aqui os sinais são regras fixas, sem treino, e cada caso conta uma vez.
3. **Exclusões por regra explícita:** as SPACs (código SIC 6770, blank checks, nos dados da SEC), além das sem receita (receita ausente ou zero, a regra do estudo 1). As contagens abaixo dizem quantas SPACs a regra das sem receita já tiraria; nenhum valor de sinal, acerto ou alerta.

10-K originais por exercício declarado (`fy`). A receita é o valor anual (quatro trimestres) da primeira tag de `receita_liquida` do mapa que a entrega traz. As financeiras pela SIC (6000 a 6999, sem as SPACs) aparecem à parte porque o mapa desta fase não tem a receita delas; no Brasil, a regra das sem receita vale só para as não financeiras. **A contagem das sem receita é um teto:** inclui as companhias cuja receita está em tags fora do mapa (a cobertura da conta `receita_liquida` fica entre 66% e 80% dos 10-K, seção 2.4); o mapa da receita é ampliado no pré-registro, antes de qualquer sinal.

| Exercício | 10-K | Sem receita | Delas financeiras (SIC 6000 a 6999) | SPACs (SIC 6770) | SPACs já sem receita | SPACs que só a regra nova tira |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 2009 | 425 | 85 | 26 | 0 | 0 | 0 |
| 2010 | 1.310 | 341 | 114 | 2 | 2 | 0 |
| 2011 | 6.546 | 2.808 | 977 | 195 | 178 | 17 |
| 2012 | 6.928 | 2.957 | 951 | 174 | 165 | 9 |
| 2013 | 6.934 | 2.899 | 929 | 166 | 152 | 14 |
| 2014 | 6.833 | 2.754 | 895 | 150 | 135 | 15 |
| 2015 | 6.463 | 2.562 | 854 | 136 | 127 | 9 |
| 2016 | 5.982 | 2.301 | 767 | 111 | 99 | 12 |
| 2017 | 5.912 | 2.272 | 758 | 115 | 106 | 9 |
| 2018 | 5.772 | 1.933 | 660 | 124 | 112 | 12 |
| 2019 | 5.607 | 1.840 | 624 | 140 | 126 | 14 |
| 2020 | 5.751 | 1.963 | 607 | 280 | 274 | 6 |
| 2021 | 6.497 | 2.426 | 610 | 633 | 629 | 4 |
| 2022 | 6.220 | 2.204 | 588 | 442 | 437 | 5 |
| 2023 | 685 | 214 | 47 | 11 | 10 | 1 |
| **Total** | **77.865** | **29.559** | **9.407** | **2.679** | **2.552** | **127** |

Companhias-ano com 8-K 4.02 e 10-K nos dados da SEC antes do 8-K (seção 4.2), pelo último 10-K entregue até o primeiro 8-K 4.02 do ano posterior ao primeiro 10-K da companhia (a receita e o SIC são os desse 10-K):

| Ano de entrega | Com 10-K antes do 8-K | Sem receita | SPACs (SIC 6770) | SPACs já sem receita | Ficam depois das duas regras |
| --- | ---: | ---: | ---: | ---: | ---: |
| 2009 | 0 | 0 | 0 | 0 | 0 |
| 2010 | 0 | 0 | 0 | 0 | 0 |
| 2011 | 13 | 1 | 0 | 0 | 12 |
| 2012 | 139 | 57 | 3 | 2 | 81 |
| 2013 | 219 | 92 | 7 | 7 | 127 |
| 2014 | 170 | 68 | 7 | 6 | 101 |
| 2015 | 166 | 52 | 2 | 1 | 113 |
| 2016 | 140 | 58 | 1 | 1 | 82 |
| 2017 | 115 | 51 | 2 | 1 | 63 |
| 2018 | 117 | 42 | 1 | 1 | 75 |
| 2019 | 87 | 30 | 2 | 2 | 57 |
| 2020 | 85 | 30 | 2 | 1 | 54 |
| 2021 | 382 | 297 | 214 | 214 | 85 |
| 2022 | 189 | 94 | 56 | 56 | 95 |
| 2023 | 207 | 103 | 35 | 34 | 103 |
| **Total** | **2.029** | **975** | **332** | **326** | **1.048** |

**De 2009 a 2023, 332 companhias-ano de SPACs com 8-K 4.02 e 10-K antes; a regra das sem receita já tiraria 326, e a regra explícita tira as outras 6. Ficam 1.048 das 2.029 companhias-ano.** Nos 10-K de 2009 a 2023, a regra das sem receita tiraria 2.552 das 2.679 entregas de SPACs.

### 5.2 As opções de rótulo comparadas na Fase 0

| Opção | Período | Tamanho | Custo | O que mede |
| --- | --- | --- | --- | --- |
| **AAER gratuito (Bao et al., pelo era-py)** | exercícios afetados até 2014; com XBRL, de 2009 a 2014 | 25 casos (47 empresa-anos) com 10-K nos dados da SEC | nenhum (a ligação gvkey–CIK não informa a origem) | uma ação da SEC que alega demonstrações erradas: rara, grave, quase sempre com intenção alegada, e anos depois dos fatos |
| **8-K com o item 4.02** | entregas de 2009 a 2023 (o item existe desde agosto de 2004) | 3.055 companhias distintas; 3.264 companhias-ano com 10-K nos dados da SEC | nenhum (EDGAR, público) | a própria companhia ou o auditor declara que demonstrações publicadas não valem mais por causa de um erro relevante, intencional ou não: o conceito da republicação do estudo 2 |
| **Base da CFRM (USC)** | AAERs emitidos de 1982 a 2025 | 4.581 AAERs no total; quantos com XBRL não se sabe sem comprar | pago (preço não publicado); termos proíbem passar a base adiante | o mesmo que o AAER, com os anos e as contas afetadas |
| **Classificação manual dos AAERs depois de 2014** | AAERs emitidos de 2015 a 2023 | 863 AAERs a ler, de todos os tipos; só uma parte é de balanço errado | horas de leitura, com regra escrita antes e leitura cega aos sinais | o mesmo que o AAER, com risco de erro de classificação |

**Recomendação do Claude (claude.ai), acolhida por Roberto em 24/11/2026:** o 8-K com o item 4.02 como desfecho principal, o mesmo conceito da republicação do estudo 2, e os AAERs de 2009 a 2014 como descrição à parte, sem teste. O 8-K 4.02 é público, gratuito, cobre o período inteiro com XBRL e tem casos suficientes para medir alguma coisa; o AAER é raro demais de 2009 a 2014 para um teste e mede outra coisa (a ação da SEC).

### 5.3 Para o rascunho do pré-registro

1. **Que exercício o caso afeta.** O campo de itens não diz quais demonstrações deixaram de valer. A regra é escrita antes de qualquer sinal, com a versão pública na data (seção 2.3).
2. **Período.** Com o 8-K 4.02, de 2009 (exercícios com XBRL; todas as companhias desde 2011) a 2023 (os 8-K entregues até 31/12/2023). Os AAERs ficam de 2009 a 2014, só como descrição.
3. **O que não dá sem dados pagos.** Os anos errados dos AAERs depois de 2014 (CFRM); o gvkey e os dados da Compustat (WRDS); as republicações da Audit Analytics, que incluiriam as republicações sem 8-K 4.02 ("little r"). A ligação gvkey–CIK do era-py não informa a origem.

### 5.4 Calendário até maio de 2027

| Até | Etapa |
| --- | --- |
| 24/11/2026 | Decisões de Roberto: o rótulo, o desfecho por caso e as exclusões (seção 5.1). |
| 15/12/2026 | Rascunho do pré-registro dos EUA revisado por Roberto; nenhum sinal calculado. |
| 31/01/2027 | Código do estudo escrito e testado só em dados sintéticos; nenhum sinal americano calculado. |
| 31/03/2027 | Registro do pré-registro e carimbo; código congelado. |
| 30/04/2027 | Cálculo único, depois do carimbo. |
| 31/05/2027 | Relatório em PT e EN, separado do estudo 2 do Brasil. |

Fontes das condições e da crítica: sites.google.com/usc.edu/aaerdataset (Buy the Data); econjwatch.org (Walker, 2021 e 2022); iangow.github.io/notes/published/bklyz.html (Gow, 2022); sec.gov (Form 8-K, item 4.02; Financial Statement Data Sets; EDGAR, submissions.zip).
