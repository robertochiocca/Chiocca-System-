# US study pre-registration

> **Registered on 2026-11-24.** Written by the agent with Roberto's decisions ([Phase 0, section 5.1](us-phase-0.md)) and reviewed by Roberto with Claude (claude.ai), who approved the registration with the three adjustments in section 14. The commit that introduces this file is the registration, and its hash is noted in the next commit, without changing any rule, as in study 2 and engine v2. No US signal was computed before registration. The US front stays out of the README and the product. Alert, not accusation: an 8-K with Item 4.02 is a statement that published financial statements can no longer be relied upon, not an accusation of fraud; no alert by company is published.

Basis: [US Phase 0](us-phase-0.md), with the numbers in [`docs/eua_fase0_numeros.json`](../eua_fase0_numeros.json), and the pre-registrations of [study 1](../pre-registro.md), [study 2](study-2-preregistration.md) and [engine v2](engine-v2-preregistration.md), whose rules hold here with only the adaptations in section 3.

## 1. Question

With the 10-Ks as they were at the time, do the alerts of engine v1 and engine v2, frozen in Brazil, and the naive rule separate the company-years followed by an 8-K with Item 4.02 within 12 months after the cut-off from those that were not? And does v2 separate better than v1?

**Label: retrospective.** The data from 2011 to 2026-04-30 are already public, and the counts of 8-K 4.02 by year already appeared in Phase 0, with no link to any signal. The test is clean because the rules are fixed (no training), were written and frozen in Brazil, and this text is registered before any US signal.

## 2. The signals: v1 and v2, frozen

- **v1:** the rules in section 4 of the study 1 pre-registration, with the amendments, in the code registered in [`docs/estudo_2_codigo_congelado.json`](../estudo_2_codigo_congelado.json): M-score above -1.78; DPO jump in the top decile of the fiscal year; implied interest above the year's average reference rate plus 10 p.p.; alert when at least one signal fires.
- **v2:** the rules of the engine v2 pre-registration, in the code registered in [`docs/motor_v2_codigo_congelado.json`](../motor_v2_codigo_congelado.json): percentiles of the M-score, the DPO jump, implied interest and the standardized Benford deviation, within the fiscal year and the group; score equal to the highest percentile; alert when the score is at or above the 90% quantile.
- **The code:** the signal functions of both registries are called without changing a line. The US script only builds each company-year's inputs from XBRL and applies the adaptations in section 3. Only the non-financial group (section 4).

## 3. The adaptations (the only ones), each with its reason

### 3.1 The map from accounts to us-gaap tags

The company's own values (no co-registrant or segment), in dollars, in the us-gaap taxonomy: the balance sheet at the report date; the income statement and cash flow for the fiscal year (four quarters). The prior year (t-1) comes from the same 10-K, like the DFP's prior-year column. Missing account or zero denominator: "not computable", as in v1, with no imputation. Expense signs follow the DFP convention (negative), and the v1 code already uses the absolute value where it needs to.

| Account | Tags and rule | Reason |
| --- | --- | --- |
| `ativo_total`, `ativo_circulante`, `contas_a_receber`, `imobilizado`, `passivo_circulante`, `patrimonio_liquido`, `depreciacao`, `custo_vendas`, `lucro_liquido` | those of the Phase 0 proposal, in order of preference | the same concept as the DFP account |
| `caixa_operacional` | `NetCashProvidedByUsedInOperatingActivities`, `NetCashProvidedByUsedInOperatingActivitiesContinuingOperations`, in this order (section 3.1.3) | the continuing-operations variant covers the 10-Ks that do not report the total; it excludes discontinued-operations cash flows |
| `receita_liquida` | `Revenues`, `RevenueFromContractWithCustomerExcludingAssessedTax`, `SalesRevenueNet`, `SalesRevenueGoodsNet`, `RevenueFromContractWithCustomerIncludingAssessedTax`, `SalesRevenueServicesNet`, `OilAndGasRevenue`, in this order: the three Phase 0 tags and those the rule in section 3.1.1 chose | with the three tags, revenue covers 66% to 73% of the 2011 to 2024 10-Ks, and the no-revenue rule would remove companies that have revenue in another tag |
| `resultado_bruto` | `GrossProfit`; if missing, revenue minus cost of sales | in the DFP line 3.03 is mandatory; under US GAAP gross profit is optional (coverage of 35% to 37%) |
| `despesas_vendas` + `despesas_gerais_adm` | `SellingGeneralAndAdministrativeExpense`, which already joins both | v1 adds the two accounts; under US GAAP they come together |
| `lucro_operacoes_continuadas` | `IncomeLossFromContinuingOperations`; if missing, net income minus `IncomeLossFromDiscontinuedOperationsNetOfTax`, when present | account 3.09 is after taxes; the pre-tax tag of the Phase 0 proposal is dropped, being a different concept |
| `emprestimos_cp` | `DebtCurrent`; if missing, the sum of `LongTermDebtCurrent` and `ShortTermBorrowings` present | under US GAAP short-term debt may come in separate lines |
| `emprestimos_lp` | `LongTermDebtNoncurrent`; if missing, `LongTermDebtAndCapitalLeaseObligations` | the same concept, with the second tag as a fallback |
| `despesas_financeiras` | `InterestExpense`, `InterestExpenseDebt`, `InterestExpenseNonoperating`, `InterestAndDebtExpense` (*), in this order (section 3.1.3); those marked (*) have a wider concept and enter with the flag | recorded limitation: the DFP's financial expense includes FX variation and other charges; the US tags are interest |
| `fornecedores` | `AccountsPayableCurrent`; if missing, `AccountsPayableAndAccruedLiabilitiesCurrent`, flagged as including accruals | the second tag is wider |
| `passivo_total` (naive rule) | `Liabilities`; if missing, `LiabilitiesAndStockholdersEquity` minus equity including noncontrolling interest | the naive rule uses total liabilities ÷ total assets, and many companies do not present total liabilities |

The Benford deviation uses the fiscal year's nonzero values in the 10-K's balance sheet, income statement and cash flow statement (by the `stmt` column of `pre.txt`: BS, IS and CF), the US equivalent of BPA, BPP, DRE and DFC, with v2's minimum of 20 numbers. The DVA does not exist in the US: v2's DEPI is v1's, from cash-flow depreciation. The coverage of each account under the rules above is in section 3.1.2 (counts only).

### 3.1.1 The revenue widening, by coverage only

Roberto's decision of 2026-11-24: the revenue tags are chosen by coverage counts only, and the final list goes into the registered text. The candidate list and the rule were written in the code (`RECEITA_CANDIDATAS` and `ampliar_receita`, in `chiocca/eua/fsds.py`) before any count: only us-gaap tags for total revenue, with no components, costs or balances. Starting from the three Phase 0 tags, at each step the candidate that covers the most sample 10-Ks still without revenue enters (non-financial, without SPACs, fiscal years 2011 to 2024: 65,096 10-Ks), if the gain is at least 0.5% of those filings. The value is the annual one (four quarters) at the report date.

| Candidate | Gain at the first step | Entered | Gain when it entered |
| --- | ---: | --- | ---: |
| `RevenueFromContractWithCustomerIncludingAssessedTax` | 2,457 | yes | 2,457 |
| `SalesRevenueGoodsNet` | 2,635 | yes | 2,635 |
| `SalesRevenueServicesNet` | 1,061 | yes | 1,047 |
| `SalesRevenueGoodsGross` | 88 | no | — |
| `RevenuesExcludingInterestAndDividends` | 8 | no | — |
| `RegulatedAndUnregulatedOperatingRevenue` | 227 | no | — |
| `ElectricUtilityRevenue` | 86 | no | — |
| `OilAndGasRevenue` | 502 | yes | 501 |
| `RevenueMineralSales` | 76 | no | — |
| `RealEstateRevenueNet` | 51 | no | — |
| `OperatingLeasesIncomeStatementLeaseRevenue` | 38 | no | — |
| `OperatingLeaseLeaseIncome` | 0 | no | — |
| `HealthCareOrganizationRevenue` | 113 | no | — |
| `ContractsRevenue` | 189 | no | — |

4 tags entered. **The final revenue list, in this order of preference: `Revenues`, `RevenueFromContractWithCustomerExcludingAssessedTax`, `SalesRevenueNet`, `SalesRevenueGoodsNet`, `RevenueFromContractWithCustomerIncludingAssessedTax`, `SalesRevenueServicesNet`, `OilAndGasRevenue`.**

Discovery count, for transparency only: among the 17,440 sample 10-Ks with none of the three Phase 0 tags, the 15 most frequent us-gaap tags with "Revenue" or "Sales" in the name (annual value at the report date). No tag outside the candidates enters, even if it looks like total revenue: the candidate lists written before the count are final (Roberto's adjustment of 2026-11-24).

| Tag | 10-Ks without the three tags with it | Candidate |
| --- | ---: | --- |
| `SalesRevenueGoodsNet` | 2,635 | yes |
| `RevenueFromContractWithCustomerIncludingAssessedTax` | 2,457 | yes |
| `IncreaseDecreaseInDeferredRevenue` | 1,472 | no |
| `SalesRevenueServicesNet` | 1,061 | yes |
| `CostOfRevenue` | 802 | no |
| `OilAndGasRevenue` | 502 | yes |
| `OilAndGasSalesRevenue` | 267 | no |
| `RegulatedAndUnregulatedOperatingRevenue` | 227 | yes |
| `ContractsRevenue` | 189 | yes |
| `GainLossOnSalesOfAssetsAndAssetImpairmentCharges` | 161 | no |
| `RevenueFromRelatedParties` | 150 | no |
| `GainsLossesOnSalesOfAssets` | 147 | no |
| `UnregulatedOperatingRevenue` | 135 | no |
| `RegulatedOperatingRevenueGas` | 131 | no |
| `OtherSalesRevenueNet` | 131 | no |

### 3.1.2 Coverage of the widened map

The share of sample 10-Ks with each account under the rules in section 3.1: presence of the value at the report date, as in Phase 0 section 2.4, and, for revenue, a nonzero annual value. Over 2011 to 2024 as a whole, and the lowest and highest year. Counts only.

| Account | 2011 to 2024 | Lowest year | Highest year |
| --- | ---: | ---: | ---: |
| `receita_liquida` | 80.2% | 77.1% | 83.5% |
| `ativo_total` | 98.6% | 97.7% | 99.6% |
| `ativo_circulante` | 94.9% | 93.6% | 96.7% |
| `contas_a_receber` | 69.2% | 66.9% | 71.0% |
| `imobilizado` | 80.8% | 73.3% | 86.0% |
| `passivo_circulante` | 94.3% | 92.8% | 96.4% |
| `fornecedores` | 87.2% | 84.4% | 89.2% |
| `emprestimos_cp` | 31.7% | 29.3% | 34.0% |
| `emprestimos_lp` | 39.9% | 37.6% | 42.8% |
| `patrimonio_liquido` | 96.4% | 95.2% | 97.9% |
| `custo_vendas` | 58.1% | 56.0% | 61.6% |
| `resultado_bruto` | 61.0% | 59.8% | 63.4% |
| `despesas_vendas_gerais_adm` | 39.6% | 38.6% | 40.7% |
| `despesas_financeiras` | 60.3% | 54.5% | 67.1% |
| `lucro_operacoes_continuadas` | 97.4% | 95.0% | 99.4% |
| `lucro_liquido` | 97.0% | 94.1% | 99.4% |
| `caixa_operacional` | 98.8% | 97.7% | 99.7% |
| `depreciacao` | 82.8% | 81.1% | 84.7% |
| `passivo_total` | 98.0% | 96.8% | 99.2% |

With the widened map, the no-revenue rule removes 12,873 of the 65,096 sample 10-Ks, against 19,409 with the three Phase 0 tags. Financial expense and operating cash flow already use the tags of section 3.1.3.

### 3.1.3 Widening financial expense and operating cash flow

Roberto's request of 2026-11-24: the same rule as for revenue, for the two accounts that were losing coverage. Each account's candidates were written in the code (`AMPLIACOES` and `CONCEITO_LARGO`, in `chiocca/eua/fsds.py`) before any count, all of the same accounting concept: interest on debt; net cash from operating activities, including the continuing-operations-only variant. Those with a wider concept (`InterestAndDebtExpense`, interest and other debt charges, and `InterestCostsIncurred`, which includes capitalized interest) enter with a flag, like the accounts payable one. Net interest (net of interest income) and interest paid (other concepts) and component tags are left out. They enter in order of largest gain, with at least 0.5% of the sample 10-Ks, by the annual value (four quarters) at the report date. No tag outside the candidates enters: the lists written before the count are final.

**First, the use of each tag by year** (share of sample 10-Ks with the tag's annual value), to see whether the drops come from a tag change in the taxonomy:

| Account | Tag | 2011 | 2012 | 2013 | 2014 | 2015 | 2016 | 2017 | 2018 | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `despesas_financeiras` | `InterestExpense` | 59.5% | 59.2% | 58.6% | 57.8% | 56.2% | 55.2% | 54.8% | 53.5% | 53.6% | 51.9% | 50.3% | 49.0% | 49.2% | 16.9% |
| `despesas_financeiras` | `InterestExpenseNonoperating` | 0.0% | 0.0% | 0.0% | 0.0% | 0.0% | 0.0% | 0.0% | 0.0% | 0.0% | 0.0% | 0.0% | 0.0% | 0.5% | 33.1% |
| `despesas_financeiras` | `InterestExpenseOperating` | 0.0% | 0.0% | 0.0% | 0.0% | 0.0% | 0.0% | 0.0% | 0.0% | 0.0% | 0.0% | 0.0% | 0.0% | 0.0% | 1.6% |
| `despesas_financeiras` | `InterestExpenseDebt` | 4.2% | 3.5% | 3.9% | 3.3% | 3.4% | 3.2% | 3.1% | 3.2% | 3.6% | 3.6% | 3.3% | 2.9% | 2.9% | 3.0% |
| `despesas_financeiras` | `InterestExpenseBorrowings` | 0.1% | 0.1% | 0.1% | 0.2% | 0.2% | 0.1% | 0.1% | 0.1% | 0.1% | 0.1% | 0.1% | 0.1% | 0.1% | 0.1% |
| `despesas_financeiras` | `InterestAndDebtExpense` | 3.2% | 3.0% | 3.1% | 3.1% | 3.1% | 3.1% | 2.9% | 2.4% | 2.2% | 1.9% | 2.0% | 2.4% | 2.3% | 2.4% |
| `despesas_financeiras` | `InterestCostsIncurred` | 0.3% | 0.2% | 0.3% | 0.3% | 0.3% | 0.3% | 0.3% | 0.3% | 0.3% | 0.3% | 0.3% | 0.3% | 0.3% | 0.2% |
| `caixa_operacional` | `NetCashProvidedByUsedInOperatingActivities` | 86.9% | 84.7% | 77.9% | 62.1% | 57.0% | 55.0% | 74.6% | 92.6% | 96.0% | 96.4% | 97.1% | 97.8% | 97.5% | 97.5% |
| `caixa_operacional` | `NetCashProvidedByUsedInOperatingActivitiesContinuingOperations` | 15.4% | 17.2% | 24.1% | 40.0% | 45.5% | 47.5% | 27.7% | 9.9% | 6.8% | 6.3% | 5.7% | 5.3% | 5.2% | 5.4% |

Reading: in 2024, the use of `InterestExpense` falls to 16.9% and that of `InterestExpenseNonoperating` rises from 0.5% in the previous year to 33.1%; from 2013 to 2017, the continuing-operations-only variant reaches 47.5% of the 10-Ks, in the year the total falls to 55.0%. The drops come from a tag change, not from missing data.

| Account | Candidate | Wider concept | Gain at the first step | Entered | Gain when it entered |
| --- | --- | --- | ---: | --- | ---: |
| `despesas_financeiras` | `InterestExpenseNonoperating` | no | 1,392 | yes | 1,387 |
| `despesas_financeiras` | `InterestExpenseOperating` | no | 67 | no | — |
| `despesas_financeiras` | `InterestExpenseDebt` | no | 1,822 | yes | 1,822 |
| `despesas_financeiras` | `InterestExpenseBorrowings` | no | 67 | no | — |
| `despesas_financeiras` | `InterestAndDebtExpense` | yes | 1,414 | yes | 1,379 |
| `despesas_financeiras` | `InterestCostsIncurred` | yes | 149 | no | — |
| `caixa_operacional` | `NetCashProvidedByUsedInOperatingActivitiesContinuingOperations` | no | 9,632 | yes | 9,632 |

By the annual value, financial expense coverage goes from 52.3% to 59.3% over 2011 to 2024 and, in 2024, from 16.9% to 54.8%; 1,379 filings are covered only by a wider-concept tag, with the flag. Operating cash flow goes from 83.2% to 98.0% and, in 2016, from 55.0% to 97.6%. Some companies have no debt and no interest expense, so financial expense does not come close to 100%.

### 3.2 The rate that replaces the CDI

The Effective Federal Funds Rate, daily series DFF on FRED (Federal Reserve Bank of St. Louis), sourced from the Federal Reserve's H.15 release: public, free and with no key. Like `chiocca.cdi.medio`, the average of the daily rates over the 12 months ending at the fiscal year end, with the same 10 p.p. cut-off. Reason: it is the US overnight interbank rate, the CDI's role in Brazil. Recorded limitation: DFF annualizes on a 360 calendar-day basis and the CDI on a 252 business-day basis. The series file goes into the repository, like `data/cdi_sgs4389.csv`, with its SHA-256 in the manifest.

### 3.3 The cut-off date

The same rule as study 1 (amendment 5, `chiocca.corte.data_corte`): the last day of the fourth month after the fiscal year end. Reason: the 10-K deadline is 60, 75 or 90 days, depending on size, and, from 2011 to 2024, the latest-filed tenth of 10-Ks came out up to 107 days after the report date (Phase 0, section 2.2). The version used is the one public at the cut-off: the last filing by that date between the original 10-K and the 10-K/As with account numbers (Phase 0, section 2.3). A company with no XBRL 10-K by the cut-off is out for that fiscal year, as in Brazil.

### 3.4 What is not adapted

Financial companies stay out (Roberto's decision of 2026-11-24): the map has no accounts for them, so the financial group and the weight of non-recurring gains do not exist in this study. The DVA (section 3.1). The document reader.

## 4. Sample and exclusions

- **Universe:** the original 10-Ks in the Financial Statement Data Sets with a report date from 2011 to 2024 (the fiscal year is the year of the report date, as in the DFP). 2011, because XBRL applies to all companies from periods after 2011-06-15; 2024, because the 12-month window of that fiscal year has already ended, on 2026-04-30 (Roberto's decision of 2026-11-24).
- **Exclusions, in this order, each counted in the report:** (1) no public XBRL version by the cut-off; (2) financial companies by SIC, 6000 to 6999, except 6770 (section 3.4); (3) SPACs, SIC 6770, an explicit rule decided by Roberto on 2026-11-24; (4) companies without revenue (revenue missing or zero, the study 1 rule, by the widened map); (5) those with no computable signal. SIC and revenue are those of the version used.
- **The size, from Phase 0 (declared fiscal year, Phase 0 map):** from 2011 to 2024, 86,766 original 10-Ks: 18,628 financial, 3,042 SPACs (2,905 of them already without revenue) and 19,409 others without revenue by the Phase 0 map; 45,687 remain. With the widened map (section 3.1.2), the others without revenue are 12,873, and 52,223 remain.

## 5. The outcome: the 8-K with Item 4.02, per case

- **Episode (the case):** a company's first 8-K with Item 4.02 in the EDGAR items field opens an episode; every 8-K or 8-K/A with Item 4.02 from the same company within the next 365 days belongs to it; after that, a new 8-K 4.02 opens another episode. Each episode counts once, the answer to Walker's and Gow's critique of Bao et al. (Phase 0, section 5.1).
- **Window:** company-year t is positive if an episode opens after the cut-off of t and within 12 months of it. The windows of consecutive fiscal years of the same company do not overlap, and each episode falls into at most one company-year. Episodes outside any sample company-year enter the description only.
- **Source:** the items field of the EDGAR filing history (`submissions.zip`), downloaded again on the day of the computation, with its SHA-256 in the manifest, and only the 8-Ks filed through 2026-04-30, the end of the window of fiscal 2024.
- **The size, from Phase 0:** from 2009 to 2026-04-30, 2,386 company-years with an 8-K 4.02 and a 10-K in the SEC data before the 8-K: 263 financial, 363 SPACs and 617 others without revenue by the Phase 0 map; 1,143 remain, from 48 to 111 a year by filing year from 2012 to 2025. With the widened map, 1,312 remain, from 58 to 136 a year.
- **Limitations:** Item 4.02 does not say which statements stopped being reliable: the outcome is a non-reliance statement within the next 12 months, with no guarantee that it concerns fiscal year t. Restatements without an 8-K ("little r") are left out. None of this is called fraud.

## 6. Metrics: those of study 2

- **Main measure:** the risk difference DR = P(positive | alert) − P(positive | no alert), on the company-years evaluated by v1, with all fiscal years together; also the rate ratio.
- **Bootstrap by company:** companies are drawn with replacement, each with all its company-years; 10,000 resamples, with seed 20270430 (Roberto's decision of 2026-11-24); the interval is the one-sided 95% percentile. The functions are `taxas`, `dr`, `bootstrap_por_companhia` and `limite_inferior` from `chiocca/v2/estudo2/secundaria.py`, called without changing a line.
- **Result:** "positive association" if the lower bound of the one-sided 95% interval of the DR is above zero; otherwise, "no evidence of association".
- **Naive rule side by side:** the most leveraged decile (total liabilities ÷ total assets) of each fiscal year, as in study 1, with the same DR and the paired bootstrap (the same resamples): "the engine separates better than the naive rule" only if the lower bound of the difference is above zero.
- **v2 paired with v1:** as in study 2's amendment 5. v2's alert comes from all company-years v2 evaluates; the measures are computed on the company-years evaluated by v1; "v2 separates better than v1" only if the lower bound of the paired difference is above zero; otherwise, no winner declared.
- **Descriptive:** study 2's ranking metrics (precision and lift at the top 1%, 5% and 10% and NDCG@k), each fiscal year separately and the AAERs (section 8). Aggregates only: no list of companies by alert.

## 7. The hand-computed example

Before any study code, a hand-computed example, in a separate script (`tests/referencia/gerar_exemplo_eua.py`), outside the `chiocca` package and without importing it, like the study 1 and engine v2 examples, with exact arithmetic at the boundaries:

- **A fictitious XBRL 10-K:** rows in the format of `sub.txt`, `num.txt` and `pre.txt`, with chosen values, for a small group of fictitious non-financial companies, in the fiscal year and the previous one, so that each rule of the account map (section 3.1) appears at least once: the first tag of each account and the fallbacks (revenue through a widening tag, derived gross profit, income from continuing operations through net income, short-term debt by the sum, financial expense through a widening tag and through `InterestAndDebtExpense`, with the flag, operating cash flow through the continuing-operations variant, accounts payable through the wider tag, with the flag, and total liabilities by the difference); co-registrant, segment, other-currency and other-date numbers, which must not enter; and a missing account, which leaves a signal not computable.
- **The public version at the cut-off (section 3.3):** the original 10-K and amendments with account numbers, one filed by the cut-off, which becomes the version used, and another after the cut-off, which does not enter, and an amendment without those numbers, which does not change the version.
- **The v1 and v2 signals (section 2):** the eight components and the M-score, the DPO jump, implied interest against a fictitious reference rate, the Benford deviation, the percentiles, the score and the alerts of v1, v2 and the naive rule, in a group small enough to check by hand.
- **The check:** the study code must reproduce the script's values, with a test, and the script goes into the study's SHA-256 registry at the freeze (section 10). Limitation, as in engine v2: both implementations start from the same text; the check catches implementation errors, not errors in the text.

## 8. The 2009 to 2014 AAERs: a separate description

For the 25 Bao et al. cases (47 company-years) with a 10-K in the SEC data (Phase 0, section 4.1): how many cases v1, v2 and the naive rule alerted in at least one affected fiscal year, with the version public at the cut-off. Counts only, with no test and no list. In 2009 and 2010, only the largest companies filed in XBRL.

## 9. Predictions written before the data

Revised on 2026-11-24 for the new period (2011 to 2024) and the widened map, and again after widening financial expense and operating cash flow (section 3.1.3). No range changed; the reason for each is given next to it.

1. **v1 alert rate:** between 25% and 45% of the evaluated non-financial companies in each fiscal year. Reason: the M-score above -1.78 flags a relevant share of US companies, and the DPO decile adds 10%; implied interest fires less than in Brazil, because US interest expense does not include FX variation. **No adjustment:** the new period adds high-rate fiscal years (2022 to 2024), in which implied interest fires less (the cut-off rises with the reference rate), but the M-score and the DPO do not depend on rates, and the range already covers that variation. **No adjustment after section 3.1.3:** with more interest and more operating cash flow available, implied interest and the M-score are computed in more company-years (implied interest above all in 2024), which may raise the alert rate a little in those years, within the range.
2. **v2 alert rate:** between 10.0% and 11.0% in each fiscal year. **No adjustment:** it comes from the construction of the decile, whatever the coverage.
3. **Outcome rate:** between 1.5% and 4% of the evaluated company-years. **No adjustment:** with the widened map, 1,312 company-years with an 8-K 4.02 and a 10-K before remain (section 5), from 58 to 136 a year by filing year, against about 4,600 sample 10-Ks per fiscal year before the no-revenue rule: about 2% to 3%.
4. **v1 DR:** positive, with a rate ratio between 1.1 and 1.5, and "positive association" more likely than not. **No adjustment:** the larger sample only adds power.
5. **v2 DR:** positive, with a rate ratio between 1.2 and 2.0, and "positive association". **No adjustment.**
6. **v2 paired with v1:** a positive difference, with the lower bound above zero ("v2 separates better than v1"). Reason: v2's alert group is smaller and more extreme. **No adjustment.**
7. **v2 against the naive rule:** no winner declared. Reason: leverage is also associated with restatements, through financial distress. **No adjustment.**
8. **AAERs:** of the 25 cases, between 30% and 60% in alert under v1 and between 10% and 30% under v2 in at least one affected fiscal year. **No adjustment:** the AAER description does not depend on the sample period.

## 10. Order and timeline: target and fallback

The order is fixed: (1) registration of this text; (2) the hand-computed example (section 7), before any study code; (3) the study code, tested only on synthetic data and on the hand-computed example, with no signal computed on real data; (4) the freeze, with the SHA-256 registry of the code and of the example script; (5) only then the single computation, with the SEC data and the 8-Ks downloaded again on the day; (6) the report.

| Step | Target | Fallback |
| --- | --- | --- |
| Registration of this text and timestamp. | 2026-12-05 | 2027-01-31 |
| Hand-computed example, code tested only on synthetic data and on the example, and freeze. | 2027-01-15 | 2027-03-31 |
| Single computation, after the freeze. | 2027-01-31 | 2027-04-30 |
| Report in PT and EN, separate from Brazil's study 2. | 2027-02-28 | 2027-05-31 |

The fallback keeps the dates of the reviewed version's fallback (2027-01-31, 2027-03-31, 2027-04-30 and 2027-05-31), in the new order.

## 11. Roberto's decisions of 2026-11-24

(a) Financial companies stay out (section 3.4); (b) the revenue tags are chosen by coverage counts only, and the final list is in section 3.1.1; (c) the sample goes to fiscal 2024, with the SEC data and the 8-Ks downloaded again on the day of the computation; (d) the seed is 20270430; (e) the SEC files stay outside Git, with their SHA-256 in the manifest and the download by script; (f) financial expense and operating cash flow by the same rule as revenue (section 3.1.3); (g) no tag outside the candidates enters (sections 3.1.1 and 3.1.3); (h) the hand-computed example (section 7); (i) the order and the timeline, with a target and a fallback (section 10).

The fiscal year is the year of the report date, as in the DFP; Phase 0 counts use the fiscal year declared by the company (`fy`), and the difference between the two is small.

## 12. What is left out

Financial companies, the DVA and the reader (section 3.4); any list or ordering of companies by alert; any investment recommendation; and, until Roberto decides, the US front in the README and the product.

## 13. Registration

- Date: 2026-11-24.
- Commit: the one that introduces this version under this name. Its hash is noted here in the next commit, without changing any rule above.
- Hash of the registration commit: `a527b9eca9ab0f087b04f1c97ed737bc63188456` (noted in the next commit, without changing any rule above).
- Timestamp, as in study 2 and engine v2: `docs/carimbos/eua-registro.txt`, with the hash of the registration commit and the SHA-256 of this file in PT, as it is in the registration commit, stamped with OpenTimestamps; the `.ots` goes into the repository, and `ots upgrade` is run after confirmation on Bitcoin.
- Freeze: the study code and the script of the section 7 example go into a SHA-256 registry of the study's own, before the single computation (section 10).

## 14. Roberto's review (2026-11-24)

Roberto read the whole text, with Claude's (claude.ai) review, and approved the registration with three adjustments. The text read was the one in commit `8c529c7fd215e268304570296a1aaf5332e0acb2`; the adjustments went in with commit `08d15363cbe7191bfe2a661e86f88fafa1228f8d`, before registration, without changing any other rule.

1. **Tags outside the candidates:** none enters; the candidate lists written before the count are final (sections 3.1.1 and 3.1.3).
2. **The hand-computed example (section 7):** a fictitious XBRL 10-K, with chosen values, going through the account map (including the fallbacks and the flags), the public version at the cut-off and the v1 and v2 signals, in a separate script, written before the study code; the code must reproduce the values, and the script goes into the study's SHA-256 registry.
3. **The order and the timeline (section 10):** first the registration of the text; then the code, tested only on synthetic data and on the hand-computed example; the freeze; and only then the single computation; with a target and a fallback.
