# US Phase 0: data reconnaissance

> **Reconnaissance, with no signal computed.** Goal: find out whether a pre-registered US study is feasible, with the data as they were at the time, testing Chiocca's v1 and v2 signals and the naive rule against a public label of misstated financial statements. Inventory and counts only; in the US, fiscal years through 2024 (Roberto's decision of 2026-11-24), and nothing from Brazilian fiscal years 2024 on; no names of individuals or companies; no signal value, hit, alert or ranking. The US front stays out of the README and the product until Roberto decides.

## 1. Access to the SEC

The SEC asks for a User-Agent with a name and contact and at most 10 requests per second; without the contact it refuses the request (HTTP 403). The scripts read the User-Agent from the environment variable `SEC_USER_AGENT`, which no versioned file or log keeps, and wait at least 0.11 second between requests. On 2026-11-23, with the variable set in the environment settings, **all 68 of 68 quarterly files** of the Financial Statement Data Sets (5.5 GB) and the EDGAR filing history (`submissions.zip`, 1.6 GB, the SEC snapshot downloaded on 2026-11-23) were downloaded. The files stay in `data/eua/`, outside Git, with each file's size and SHA-256 in `data/eua_manifesto.csv`.

## 2. Balance sheets: the SEC Financial Statement Data Sets

The financial statement numbers in XBRL, one zip per filing quarter since 2009 (here, from 2009q1 to 2025q4: the fiscal years through 2024, with the late 10-Ks and the amendments of 2025). The two files used are `sub.txt` (one row per filing: CIK, form, report date, fiscal year, filing dates and whether the filing was later amended) and `num.txt` (one row per number: tag, taxonomy, date, quarters covered, unit and value).

- **10-K and 10-K/A:** the original filing and each amendment are separate filings, each with its date; `prevrpt` flags a filing that was later amended.
- **The public version at a cutoff date:** per company and fiscal year, the last filing made by that date, between the original 10-K and the 10-K/As with numbers for the mapped accounts, like Chiocca's "as it was" in Brazil. An amendment without those numbers (only Part III of the 10-K, for example) does not change the version. The next year's comparative column shows the t-1 numbers as presented later.

### 2.1 File structure

Each zip has `sub.txt`, `num.txt`, `pre.txt` and `tag.txt` (tab-separated text) and a `readme.htm`. The columns used were checked in all 68 quarters before any count. 2009q1 has no filing (headers only): the first XBRL 10-Ks come in from 2009q2. The last quarter (2025q4):

| File | Columns | Rows |
| --- | ---: | ---: |
| `num.txt` | 10 | 3,832,977 |
| `pre.txt` | 10 | 719,346 |
| `readme.htm` | — | — |
| `sub.txt` | 36 | 6,304 |
| `tag.txt` | 9 | 84,907 |

The columns of `sub.txt` (36) and `num.txt` (10) are the same in all 68 quarters. `num.txt` has `coreg` (co-registrant) and `segments`: the code counts only the company's own number, with both empty.

### 2.2 10-K and 10-K/A by fiscal year and filing dates

By the fiscal year the company declares (`fy`). The lag is the number of days between the report date and the filing of the original 10-K. Amendments with numbers are the 10-K/As with some mapped tag at the report date; the others (most of them) carry only Part III or the cover page. Declared fiscal years from 2025 on are left out.

| Fiscal year | Companies with a 10-K | 10-K | 10-K/A | 10-K/A with numbers | 10-Ks later amended | Median lag (days) | Lag, 10% to 90% (days) | Within 90 days |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 2009 | 425 | 425 | 18 | 18 | 12 | 56 | 46–60 | 100% |
| 2010 | 1,308 | 1,310 | 80 | 78 | 31 | 56 | 47–60 | 99% |
| 2011 | 6,541 | 6,546 | 628 | 620 | 303 | 75 | 54–105 | 84% |
| 2012 | 6,920 | 6,928 | 692 | 686 | 301 | 74 | 52–105 | 76% |
| 2013 | 6,905 | 6,934 | 566 | 563 | 287 | 73 | 52–105 | 81% |
| 2014 | 6,813 | 6,833 | 421 | 416 | 236 | 72 | 51–105 | 83% |
| 2015 | 6,455 | 6,463 | 319 | 316 | 174 | 71 | 50–105 | 82% |
| 2016 | 5,974 | 5,982 | 293 | 293 | 179 | 69 | 50–106 | 84% |
| 2017 | 5,905 | 5,912 | 276 | 275 | 179 | 68 | 51–105 | 81% |
| 2018 | 5,768 | 5,772 | 209 | 206 | 145 | 67 | 50–105 | 81% |
| 2019 | 5,602 | 5,608 | 206 | 204 | 140 | 66 | 50–107 | 84% |
| 2020 | 5,748 | 5,753 | 571 | 570 | 404 | 68 | 49–100 | 87% |
| 2021 | 6,495 | 6,501 | 322 | 321 | 257 | 70 | 49–102 | 86% |
| 2022 | 6,239 | 6,241 | 326 | 326 | 263 | 69 | 48–104 | 86% |
| 2023 | 5,804 | 5,807 | 329 | 329 | 192 | 67 | 47–106 | 80% |
| 2024 | 5,479 | 5,486 | 184 | 183 | 6 | 65 | 47–92 | 88% |

### 2.3 The public version at a cutoff date

By fiscal year, on December 31 of the next year (t+1) and of the one after (t+2), only cutoffs through 2025-12-31: how many companies have a public version and in how many it is already an amendment with numbers, not the original 10-K.

| Fiscal year | Companies at t+1 | Amendment at t+1 | Companies at t+2 | Amendment at t+2 |
| --- | ---: | ---: | ---: | ---: |
| 2009 | 425 | 12 | 425 | 12 |
| 2010 | 1,301 | 23 | 1,305 | 27 |
| 2011 | 6,473 | 240 | 6,521 | 288 |
| 2012 | 6,846 | 255 | 6,899 | 285 |
| 2013 | 6,844 | 246 | 6,893 | 277 |
| 2014 | 6,745 | 199 | 6,794 | 226 |
| 2015 | 6,367 | 137 | 6,431 | 156 |
| 2016 | 5,889 | 141 | 5,950 | 168 |
| 2017 | 5,836 | 167 | 5,886 | 177 |
| 2018 | 5,704 | 119 | 5,747 | 134 |
| 2019 | 5,517 | 113 | 5,590 | 126 |
| 2020 | 5,722 | 376 | 5,745 | 390 |
| 2021 | 6,479 | 211 | 6,493 | 243 |
| 2022 | 6,219 | 215 | 6,231 | 244 |
| 2023 | 5,783 | 222 | 5,804 | 252 |
| 2024 | 5,479 | 139 | — | — |

### 2.4 The map from accounts to us-gaap tags and coverage by year

The accounts the v1 and v2 signals use, with candidate tags in order of preference. Benford uses all numbers and needs no map; the DVA does not exist in the US (depreciation comes from the cash flow statement); in the US, selling and administrative expenses usually come together (SG&A), and many companies do not present gross profit. Financial companies (weight of non-recurring gains) have no map in this phase.

| Account | Candidate us-gaap tags |
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

Coverage is the share of each fiscal year's original 10-Ks with a dollar value at the report date, for the company itself (no co-registrant or segment), in the us-gaap taxonomy. By account (any of the candidate tags):

| Account | 2009 | 2010 | 2011 | 2012 | 2013 | 2014 | 2015 | 2016 | 2017 | 2018 | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `ativo_total` | 97% | 98% | 97% | 98% | 97% | 98% | 98% | 98% | 98% | 98% | 98% | 99% | 99% | 99% | 99% | 99% |
| `ativo_circulante` | 82% | 79% | 74% | 75% | 76% | 76% | 76% | 76% | 76% | 77% | 78% | 78% | 81% | 81% | 78% | 77% |
| `contas_a_receber` | 71% | 70% | 53% | 53% | 54% | 54% | 54% | 55% | 55% | 56% | 56% | 53% | 51% | 53% | 53% | 53% |
| `imobilizado` | 87% | 85% | 75% | 75% | 75% | 76% | 76% | 76% | 77% | 78% | 75% | 70% | 65% | 66% | 67% | 66% |
| `passivo_circulante` | 82% | 79% | 73% | 75% | 75% | 76% | 76% | 76% | 76% | 77% | 77% | 78% | 81% | 80% | 78% | 76% |
| `fornecedores` | 73% | 71% | 66% | 68% | 70% | 70% | 70% | 70% | 70% | 71% | 72% | 71% | 72% | 72% | 70% | 68% |
| `emprestimos_cp` | 57% | 48% | 27% | 26% | 27% | 27% | 28% | 28% | 29% | 29% | 28% | 27% | 25% | 25% | 25% | 26% |
| `emprestimos_lp` | 68% | 57% | 29% | 30% | 30% | 31% | 32% | 33% | 34% | 34% | 33% | 32% | 30% | 30% | 31% | 31% |
| `patrimonio_liquido` | 96% | 96% | 93% | 93% | 93% | 94% | 94% | 94% | 95% | 95% | 96% | 97% | 97% | 97% | 97% | 97% |
| `receita_liquida` | 80% | 74% | 66% | 67% | 68% | 67% | 68% | 69% | 68% | 73% | 73% | 72% | 68% | 69% | 71% | 71% |
| `custo_vendas` | 52% | 52% | 42% | 44% | 44% | 44% | 44% | 44% | 46% | 49% | 49% | 47% | 45% | 45% | 47% | 46% |
| `resultado_bruto` | 26% | 34% | 36% | 37% | 37% | 37% | 36% | 36% | 37% | 37% | 37% | 36% | 35% | 36% | 37% | 36% |
| `despesas_vendas_gerais_adm` | 49% | 45% | 31% | 31% | 31% | 31% | 31% | 32% | 32% | 32% | 33% | 32% | 29% | 30% | 32% | 32% |
| `despesas_financeiras` | 64% | 68% | 62% | 62% | 62% | 61% | 60% | 59% | 59% | 58% | 57% | 55% | 50% | 51% | 53% | 17% |
| `lucro_operacoes_continuadas` | 28% | 21% | 30% | 34% | 38% | 41% | 46% | 49% | 50% | 52% | 54% | 53% | 63% | 69% | 70% | 70% |
| `lucro_liquido` | 96% | 98% | 93% | 94% | 94% | 95% | 96% | 96% | 97% | 98% | 98% | 99% | 99% | 99% | 99% | 99% |
| `caixa_operacional` | 90% | 93% | 87% | 85% | 77% | 61% | 56% | 55% | 75% | 93% | 97% | 97% | 98% | 98% | 98% | 97% |
| `depreciacao` | 79% | 81% | 73% | 74% | 75% | 75% | 76% | 76% | 77% | 78% | 77% | 74% | 71% | 72% | 74% | 75% |
| `juros_pagos` | 48% | 56% | 64% | 65% | 66% | 65% | 66% | 67% | 67% | 68% | 68% | 66% | 62% | 64% | 65% | 65% |

By tag:

| Tag | 2009 | 2010 | 2011 | 2012 | 2013 | 2014 | 2015 | 2016 | 2017 | 2018 | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `Assets` | 97% | 98% | 97% | 98% | 97% | 98% | 98% | 98% | 98% | 98% | 98% | 99% | 99% | 99% | 99% | 99% |
| `AssetsCurrent` | 82% | 79% | 74% | 75% | 76% | 76% | 76% | 76% | 76% | 77% | 78% | 78% | 81% | 81% | 78% | 77% |
| `AccountsReceivableNetCurrent` | 51% | 53% | 46% | 47% | 47% | 48% | 48% | 48% | 49% | 49% | 49% | 48% | 46% | 47% | 48% | 48% |
| `ReceivablesNetCurrent` | 20% | 17% | 7% | 7% | 7% | 7% | 7% | 7% | 7% | 7% | 7% | 6% | 5% | 5% | 6% | 5% |
| `PropertyPlantAndEquipmentNet` | 87% | 85% | 75% | 75% | 75% | 76% | 76% | 76% | 77% | 78% | 75% | 70% | 65% | 66% | 67% | 66% |
| `LiabilitiesCurrent` | 82% | 79% | 73% | 75% | 75% | 76% | 76% | 76% | 76% | 77% | 77% | 78% | 81% | 80% | 78% | 76% |
| `AccountsPayableCurrent` | 61% | 61% | 53% | 53% | 53% | 54% | 54% | 54% | 55% | 56% | 56% | 56% | 56% | 57% | 55% | 55% |
| `AccountsPayableAndAccruedLiabilitiesCurrent` | 12% | 11% | 14% | 16% | 17% | 17% | 16% | 16% | 16% | 16% | 16% | 16% | 15% | 15% | 14% | 14% |
| `DebtCurrent` | 20% | 12% | 4% | 4% | 4% | 4% | 5% | 5% | 5% | 5% | 4% | 4% | 3% | 4% | 4% | 4% |
| `LongTermDebtCurrent` | 24% | 26% | 16% | 16% | 17% | 17% | 18% | 18% | 18% | 18% | 17% | 18% | 17% | 16% | 16% | 16% |
| `ShortTermBorrowings` | 20% | 16% | 8% | 8% | 7% | 7% | 7% | 8% | 8% | 8% | 8% | 8% | 6% | 7% | 7% | 7% |
| `LongTermDebtNoncurrent` | 45% | 41% | 22% | 22% | 23% | 23% | 25% | 25% | 26% | 26% | 26% | 25% | 24% | 24% | 24% | 25% |
| `LongTermDebtAndCapitalLeaseObligations` | 24% | 16% | 7% | 7% | 8% | 8% | 8% | 8% | 8% | 8% | 8% | 7% | 6% | 6% | 6% | 7% |
| `StockholdersEquity` | 81% | 84% | 87% | 89% | 89% | 90% | 90% | 90% | 91% | 91% | 92% | 93% | 93% | 93% | 92% | 92% |
| `StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest` | 64% | 57% | 29% | 28% | 30% | 30% | 31% | 32% | 32% | 33% | 33% | 31% | 30% | 31% | 32% | 33% |
| `Revenues` | 53% | 43% | 41% | 42% | 42% | 43% | 42% | 43% | 44% | 46% | 39% | 36% | 32% | 33% | 33% | 32% |
| `RevenueFromContractWithCustomerExcludingAssessedTax` | 0% | 0% | 0% | 0% | 0% | 0% | 0% | 0% | 0% | 27% | 37% | 39% | 38% | 39% | 41% | 42% |
| `SalesRevenueNet` | 29% | 33% | 26% | 27% | 27% | 27% | 27% | 27% | 26% | 2% | 0% | 0% | 0% | 0% | 0% | 0% |
| `CostOfRevenue` | 16% | 15% | 14% | 15% | 15% | 16% | 16% | 17% | 18% | 19% | 18% | 18% | 18% | 19% | 19% | 19% |
| `CostOfGoodsAndServicesSold` | 16% | 17% | 12% | 12% | 12% | 11% | 11% | 11% | 11% | 29% | 32% | 30% | 27% | 27% | 28% | 28% |
| `CostOfGoodsSold` | 26% | 25% | 21% | 21% | 21% | 21% | 21% | 21% | 21% | 2% | 0% | 0% | 0% | 0% | 0% | 0% |
| `GrossProfit` | 26% | 34% | 36% | 37% | 37% | 37% | 36% | 36% | 37% | 37% | 37% | 36% | 35% | 36% | 37% | 36% |
| `SellingGeneralAndAdministrativeExpense` | 49% | 45% | 31% | 31% | 31% | 31% | 31% | 32% | 32% | 32% | 33% | 32% | 29% | 30% | 32% | 32% |
| `InterestExpense` | 64% | 68% | 62% | 62% | 62% | 61% | 60% | 59% | 59% | 58% | 57% | 55% | 50% | 51% | 53% | 17% |
| `IncomeLossFromContinuingOperations` | 28% | 21% | 15% | 15% | 15% | 14% | 12% | 11% | 9% | 8% | 8% | 7% | 7% | 6% | 6% | 6% |
| `IncomeLossFromContinuingOperationsBeforeIncomeTaxesExtraordinaryItemsNoncontrollingInterest` | 0% | 0% | 18% | 23% | 27% | 31% | 39% | 42% | 46% | 48% | 50% | 49% | 61% | 67% | 69% | 69% |
| `NetIncomeLoss` | 85% | 87% | 86% | 88% | 88% | 90% | 90% | 90% | 91% | 92% | 92% | 93% | 94% | 93% | 94% | 93% |
| `ProfitLoss` | 60% | 54% | 32% | 32% | 33% | 32% | 33% | 33% | 36% | 44% | 48% | 48% | 52% | 50% | 49% | 49% |
| `NetCashProvidedByUsedInOperatingActivities` | 90% | 93% | 87% | 85% | 77% | 61% | 56% | 55% | 75% | 93% | 97% | 97% | 98% | 98% | 98% | 97% |
| `DepreciationDepletionAndAmortization` | 32% | 38% | 36% | 37% | 38% | 38% | 39% | 39% | 40% | 40% | 41% | 39% | 38% | 39% | 40% | 40% |
| `DepreciationAndAmortization` | 35% | 32% | 25% | 24% | 25% | 25% | 26% | 25% | 25% | 24% | 24% | 23% | 22% | 23% | 24% | 24% |
| `Depreciation` | 18% | 19% | 21% | 22% | 22% | 22% | 22% | 22% | 22% | 22% | 22% | 20% | 19% | 20% | 20% | 20% |
| `InterestPaidNet` | 25% | 25% | 13% | 13% | 13% | 13% | 14% | 14% | 32% | 54% | 61% | 60% | 58% | 60% | 62% | 63% |
| `InterestPaid` | 22% | 31% | 51% | 52% | 52% | 52% | 53% | 53% | 36% | 14% | 7% | 5% | 4% | 3% | 3% | 2% |

## 3. Labels

### 3.1 The AAERs

**era-py 0.0.37** (PyPI, by Ian Gow, the data for the book *Empirical Research in Accounting: Tools and Methods*): package license MIT; the tables carry no license of their own, and the source of the gvkey–CIK link is not stated. So nothing from them is copied into the repository: the wheel stays in `data/eua/`, with its SHA-256 in the manifest (`5f79fc223a17af9147b65a9a24f918355fc8a31f9341cd7fed8c0267b3591c0c`).

- **The SEC AAER index** (`aaer_dates`, refreshed by the author through 2026-10-08): number, date, description and year. Through 2023, 3,277 AAERs (3,248 distinct numbers), from 1999 to 2023. The description carries names of companies and individuals and is not read here.
- **The Bao et al. (2020) company-years** (`aaer_firm_year`): 415 rows, 412 AAERs and 402 companies, identified by gvkey (Compustat), with the first and last affected years, from 1990 to 2014: 990 company-years with an alleged misstatement. 233 of the AAERs affect more than one year.
- **The gvkey–CIK link** (`gvkey_ciks`): 49,089 links, 29,099 gvkeys and 27,708 CIKs, with the dates of each link. With it, each Bao et al. company-year links to the SEC CIK without Compustat.
- **The CFRM (Berkeley) database, used by Dechow et al. (2011):** now sold through the USC site ("Buy the Data" page, payment through cashnet; the price does not appear in the page text); the terms forbid passing the data to third parties, except co-authors; it covers 4,581 AAERs issued from 1982-05-17 to 2025-12-31, with the company's name and identifiers, the affected accounts and the misstated years and quarters (the page does not say which identifiers). Only the access conditions were read.
- **The public AAER list on the SEC site:** not read directly; the era-py index is a copy of it, with the refresh date.

**How to link each AAER to the CIK without Compustat.** Through 2014, through the Bao et al. company-years and the era-py gvkey–CIK link. After 2014, there is no free database with the misstated years: the path is to read each AAER on the SEC site (the company is a party) and match the name against the SEC file of names and CIKs, keeping only the company and the CIK.

### 3.2 A new label: 8-Ks with Item 4.02

Since August 2004, a company files an 8-K with Item 4.02 (*Non-Reliance on Previously Issued Financial Statements or a Related Audit Report or Completed Interim Review*) when it, or its auditor, concludes that previously issued statements should no longer be relied upon because of an error; the restatement follows. It is the same concept as the restatement in Brazil's study 2: the published information was wrong, by error or on purpose, without saying which. The source is the items field (`items`) of each company's filing history on EDGAR (`submissions.zip`), which lists the items of each 8-K; only the date, form, items and CIK are read, in memory, with no 8-K text or company name (`chiocca/eua/itens.py`). A filing by several companies counts once in the filing counts.

## 4. Counts

### 4.1 Bao et al. AAERs with a 10-K in the SEC data

| Fiscal year | Company-years with an AAER (Bao et al.) | Linked to a CIK | With a 10-K in the SEC data | Company-years with a 10-K (all companies) |
| --- | ---: | ---: | ---: | ---: |
| 2009 | 31 | 30 | 3 | 444 |
| 2010 | 26 | 24 | 5 | 1,337 |
| 2011 | 22 | 22 | 15 | 6,728 |
| 2012 | 19 | 19 | 14 | 6,931 |
| 2013 | 11 | 11 | 6 | 6,889 |
| 2014 | 4 | 4 | 4 | 6,803 |
| **Total** | **113** | **110** | **47** | 29,132 |

The fiscal year follows the Compustat convention used by Bao et al.: the year of the report date, or the previous one when the fiscal year ends from January to May. A Bao et al. company-year has a 10-K in the SEC data when some CIK linked to the gvkey in that year filed an original XBRL 10-K for that fiscal year. **From 2009 to 2014, 113 company-years with an AAER, 110 linked to a CIK and 47 with a 10-K in the SEC data**, against about 6,800 companies with a 10-K a year from 2011 to 2014, when XBRL already applied to all. Counting each case (AAER) once: **25 cases**, from 25 companies, with at least one affected fiscal year with a 10-K from 2009 to 2014 (by the first such year: 2009: 3, 2010: 3, 2011: 9, 2012: 8, 2013: 1, 2014: 1). The most recent years have fewer cases because an AAER usually comes out years after the facts, and the database ends in 2014. The SEC index has 1,572 AAERs issued from 2009 to 2023, of all kinds (not only misstatements).

### 4.2 8-Ks with Item 4.02 and 10-K/As by filing year

| Filing year | 8-K 4.02 | 8-K/A 4.02 | Companies with an 8-K 4.02 | Of them with SIC 6770 (SPACs) | First time since 2009 | With a 10-K in the SEC data | With a 10-K in the SEC data before the 8-K | 10-K (EDGAR) | 10-K/A (EDGAR) | 10-K/A with XBRL (SEC data) |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 2009 | 388 | 116 | 361 | 3 | 361 | 220 | 0 | 9,494 | 2,277 | 2 |
| 2010 | 387 | 104 | 362 | 3 | 320 | 226 | 0 | 8,890 | 2,111 | 18 |
| 2011 | 346 | 82 | 315 | 8 | 258 | 237 | 13 | 8,561 | 1,983 | 98 |
| 2012 | 302 | 63 | 278 | 7 | 228 | 250 | 139 | 8,154 | 1,814 | 680 |
| 2013 | 273 | 66 | 255 | 11 | 199 | 247 | 219 | 7,832 | 1,727 | 641 |
| 2014 | 213 | 44 | 194 | 9 | 147 | 188 | 170 | 7,770 | 1,477 | 534 |
| 2015 | 201 | 21 | 186 | 7 | 149 | 179 | 166 | 7,659 | 1,210 | 424 |
| 2016 | 166 | 18 | 152 | 3 | 105 | 150 | 140 | 7,259 | 1,129 | 302 |
| 2017 | 133 | 13 | 123 | 5 | 95 | 119 | 115 | 6,984 | 914 | 286 |
| 2018 | 130 | 7 | 124 | 3 | 100 | 121 | 117 | 6,827 | 989 | 307 |
| 2019 | 97 | 6 | 90 | 4 | 64 | 89 | 87 | 6,660 | 983 | 234 |
| 2020 | 96 | 8 | 92 | 5 | 71 | 90 | 85 | 6,508 | 905 | 192 |
| 2021 | 840 | 26 | 678 | 492 | 650 | 669 | 382 | 6,933 | 1,081 | 532 |
| 2022 | 288 | 19 | 270 | 132 | 170 | 268 | 189 | 7,538 | 863 | 334 |
| 2023 | 240 | 29 | 219 | 61 | 138 | 217 | 207 | 7,118 | 879 | 335 |
| 2024 | 237 | 13 | 218 | 49 | 159 | 217 | 209 | 6,631 | 859 | 315 |
| 2025 | 132 | 17 | 123 | 24 | 70 | 118 | 115 | 6,431 | 708 | 223 |
| 2026 | 35 | 0 | 35 | 6 | 24 | 33 | 33 | 5,450 | 418 | 0 |
| **Total** | **4,504** | **652** | **4,075** | **832** | **3,308** | **3,638** | **2,386** | **132,699** | **22,327** | **5,457** |

A company counts once per year; "first time since 2009" counts each company once in the period. "With a 10-K in the SEC data" means the CIK has an original 10-K in the Financial Statement Data Sets from 2009q1 to 2025q4; "before the 8-K", that the first of those 10-Ks was filed by the date of the 8-K (there are XBRL statements from the time to compare). **From 2009 to 2026-04-30: 4,504 8-Ks with Item 4.02, from 4,075 company-years; 3,308 distinct companies; 3,638 company-years with a 10-K in the SEC data, 2,386 of them with the 10-K before the 8-K.** The 10-K/As are of all kinds (most only complete Part III); the last column counts those in the SEC data, by filing year. The 2021 peak coincides with the SEC staff statement of 2021-04-12 on the accounting for SPAC warrants (acquisition companies with no operations), followed by many restatements: 492 of the 678 companies with an 8-K 4.02 in 2021 have SIC code 6770 (blank checks) in the SEC data; from 2009 to 2026-04-30, 832 company-years. The year 2026 only goes to 2026-04-30, the end of the window of fiscal 2024.

## 5. Decisions

### 5.1 Roberto's decisions (2026-11-24)

1. **Main outcome: the 8-K with Item 4.02**, the same concept as study 2's restatement. The 2009 to 2014 AAERs stay as description only, with no test.
2. **Outcome per case:** each episode counted once (one company, one 8-K 4.02 episode, with the 8-Ks and 8-K/As of the same episode together), with the bootstrap by company, as in study 2. It answers the critique by Walker (2021 and 2022) and Gow (2022) of Bao et al. (2020), where multi-year frauds spanning training and test inflate the metric; here the signals are fixed rules, with no training, and each case counts once.
3. **Exclusions by explicit rule:** SPACs (SIC code 6770, blank checks, in the SEC data), on top of the companies without revenue (revenue missing or zero, the study 1 rule). The counts below say how many SPACs the no-revenue rule would already remove; no signal value, hit or alert.
4. **Financial companies out:** companies with SIC 6000 to 6999, without the SPACs, stay out of the study, because the map has no accounts for them.
5. **The revenue tags** are chosen by coverage counts only, and the final list goes into the text that is registered.
6. **Period:** fiscal years 2011 to 2024 (report date through 2024-12-31), with the SEC data and the 8-Ks downloaded again on the day of the computation, because the 12-month window of all those fiscal years has already ended (the last one, on 2026-04-30). This Phase 0's counts go that far: 10-Ks filed through 2025-12-31 and 8-Ks through 2026-04-30.
7. **The bootstrap seed** is 20270430.
8. **The SEC files** stay outside Git, with their SHA-256 in the manifest and the download by script.
9. **Timeline with a target and a fallback** (section 5.4). No US signal is computed before registration.

Original 10-Ks by declared fiscal year (`fy`). Revenue is the annual value (four quarters) of the first `receita_liquida` tag in the map that the filing has. Financial companies by SIC (6000 to 6999, without SPACs) appear separately because this phase's map has no revenue for them; in Brazil, the no-revenue rule applies to non-financial companies only. **The no-revenue count is a ceiling:** it includes companies whose revenue sits in tags outside the map (coverage of the `receita_liquida` account is between 66% and 80% of 10-Ks, section 2.4); the revenue map is widened in the pre-registration, before any signal.

| Fiscal year | 10-K | Financial (SIC 6000 to 6999, without SPACs) | SPACs (SIC 6770) | SPACs already without revenue | Others without revenue | Remaining |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 2009 | 425 | 75 | 0 | 0 | 59 | 291 |
| 2010 | 1,310 | 279 | 2 | 2 | 225 | 804 |
| 2011 | 6,546 | 1,571 | 195 | 178 | 1,653 | 3,127 |
| 2012 | 6,928 | 1,539 | 174 | 165 | 1,841 | 3,374 |
| 2013 | 6,934 | 1,514 | 166 | 152 | 1,818 | 3,436 |
| 2014 | 6,833 | 1,501 | 150 | 135 | 1,724 | 3,458 |
| 2015 | 6,463 | 1,429 | 136 | 127 | 1,581 | 3,317 |
| 2016 | 5,982 | 1,336 | 111 | 99 | 1,435 | 3,100 |
| 2017 | 5,912 | 1,317 | 115 | 106 | 1,408 | 3,072 |
| 2018 | 5,772 | 1,276 | 124 | 112 | 1,161 | 3,211 |
| 2019 | 5,608 | 1,219 | 140 | 126 | 1,091 | 3,158 |
| 2020 | 5,753 | 1,203 | 280 | 274 | 1,084 | 3,186 |
| 2021 | 6,501 | 1,201 | 633 | 629 | 1,189 | 3,478 |
| 2022 | 6,241 | 1,197 | 442 | 437 | 1,189 | 3,413 |
| 2023 | 5,807 | 1,166 | 208 | 201 | 1,166 | 3,267 |
| 2024 | 5,486 | 1,159 | 168 | 164 | 1,069 | 3,090 |
| **Total** | **88,501** | **18,982** | **3,044** | **2,907** | **19,693** | **46,782** |

Company-years with an 8-K 4.02 and a 10-K in the SEC data before the 8-K (section 4.2), by the last 10-K filed by the year's first 8-K 4.02 after the company's first 10-K (revenue and SIC are those of that 10-K):

| Filing year | With a 10-K before the 8-K | Financial | SPACs (SIC 6770) | SPACs already without revenue | Others without revenue | Remaining |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 2009 | 0 | 0 | 0 | 0 | 0 | 0 |
| 2010 | 0 | 0 | 0 | 0 | 0 | 0 |
| 2011 | 13 | 2 | 0 | 0 | 0 | 11 |
| 2012 | 139 | 21 | 3 | 2 | 44 | 71 |
| 2013 | 219 | 30 | 7 | 7 | 71 | 111 |
| 2014 | 170 | 22 | 7 | 6 | 52 | 89 |
| 2015 | 166 | 14 | 2 | 1 | 44 | 106 |
| 2016 | 140 | 19 | 1 | 1 | 44 | 76 |
| 2017 | 115 | 15 | 2 | 1 | 42 | 56 |
| 2018 | 117 | 16 | 1 | 1 | 33 | 67 |
| 2019 | 87 | 8 | 2 | 2 | 24 | 53 |
| 2020 | 85 | 11 | 2 | 1 | 24 | 48 |
| 2021 | 382 | 16 | 214 | 214 | 71 | 81 |
| 2022 | 189 | 18 | 56 | 56 | 30 | 85 |
| 2023 | 207 | 29 | 35 | 34 | 55 | 88 |
| 2024 | 209 | 24 | 22 | 22 | 55 | 108 |
| 2025 | 115 | 15 | 7 | 7 | 21 | 72 |
| 2026 | 33 | 3 | 2 | 2 | 7 | 21 |
| **Total** | **2,386** | **263** | **363** | **357** | **617** | **1,143** |

**From 2009 to 2026-04-30, 2,386 company-years with an 8-K 4.02 and a 10-K before: 263 financial, 363 SPACs (of which the no-revenue rule would already remove 357) and 617 others without revenue; 1,143 remain.** In the 10-Ks of fiscal years 2009 to 2024, the no-revenue rule would remove 2,907 of the 3,044 SPAC filings.

### 5.2 The label options compared in Phase 0

| Option | Period | Size | Cost | What it measures |
| --- | --- | --- | --- | --- |
| **Free AAERs (Bao et al., through era-py)** | affected fiscal years through 2014; with XBRL, 2009 to 2014 | 25 cases (47 company-years) with a 10-K in the SEC data | none (the gvkey–CIK link does not state its source) | an SEC action alleging misstated statements: rare, severe, almost always with alleged intent, and years after the facts |
| **8-K with Item 4.02** | filings from 2009 to 2026-04-30 (the item exists since August 2004) | 3,308 distinct companies; 3,638 company-years with a 10-K in the SEC data | none (EDGAR, public) | the company or its auditor declares that published statements can no longer be relied upon because of a material error, intentional or not: the concept of study 2's restatement |
| **CFRM database (USC)** | AAERs issued from 1982 to 2025 | 4,581 AAERs in all; how many with XBRL is unknown without buying | paid (price not published); terms forbid passing the data on | the same as the AAER, with the affected years and accounts |
| **Hand classification of AAERs after 2014** | AAERs issued from 2015 to 2023 | 863 AAERs to read, of all kinds; only some are misstatements | hours of reading, with the rule written beforehand and reading blind to the signals | the same as the AAER, with a risk of classification error |

**Recommendation from Claude (claude.ai), accepted by Roberto on 2026-11-24:** the 8-K with Item 4.02 as the main outcome, the same concept as study 2's restatement, and the 2009 to 2014 AAERs as a separate description, with no test. The 8-K 4.02 is public, free, covers the whole XBRL period and has enough cases to measure something; the AAER is too rare from 2009 to 2014 for a test and measures something else (the SEC action).

### 5.3 For the pre-registration

The [US study pre-registration](us-preregistration.md), registered on 2026-11-24, takes up these points.

1. **Which fiscal year the case affects.** The items field does not say which statements stopped being reliable. The rule is written before any signal, with the public version at the date (section 2.3).
2. **What cannot be done without paid data.** Misstated years of AAERs after 2014 (CFRM); the gvkey and Compustat data (WRDS); Audit Analytics restatements, which would include restatements without an 8-K 4.02 ("little r"). The era-py gvkey–CIK link does not state its source.

### 5.4 Timeline: target and fallback

| Step | Target | Fallback |
| --- | --- | --- |
| Roberto's decisions and final review of the pre-registration by Claude (claude.ai) and Roberto. | 2026-11-24 | 2026-11-24 |
| Pre-registration registered and timestamped. | 2026-12-05 | 2027-01-31 |
| Hand-computed example, code tested only on synthetic data and on the example, and freeze. | 2027-01-15 | 2027-03-31 |
| Single computation, after the freeze, with the SEC data and the 8-Ks downloaded on the day. | 2027-01-31 | 2027-04-30 |
| Report in PT and EN, separate from Brazil's study 2. | 2027-02-28 | 2027-05-31 |

Sources for the conditions and the critique: sites.google.com/usc.edu/aaerdataset (Buy the Data); econjwatch.org (Walker, 2021 and 2022); iangow.github.io/notes/published/bklyz.html (Gow, 2022); sec.gov (Form 8-K, Item 4.02; Financial Statement Data Sets; EDGAR, submissions.zip).
