# Draft pre-registration of the US study

> **Draft, not a registration.** Written on 2026-11-24 by the agent, with Roberto's decisions of the same date ([Phase 0, section 5.1](us-phase-0.md)), before any US signal was computed. Nothing here holds until Roberto reviews it and the text is registered (the commit that introduces it as the registration and the hash noted in the next commit), by 2027-03-31. The US front stays out of the README and the product. Alert, not accusation: an 8-K with Item 4.02 is a statement that published financial statements can no longer be relied upon, not an accusation of fraud; no alert by company is published.

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
| `ativo_total`, `ativo_circulante`, `contas_a_receber`, `imobilizado`, `passivo_circulante`, `patrimonio_liquido`, `caixa_operacional`, `depreciacao`, `custo_vendas`, `lucro_liquido` | those of the Phase 0 proposal, in order of preference | the same concept as the DFP account |
| `receita_liquida` | the three Phase 0 tags and the tags the widening adds before registration, chosen by coverage only (counts) | revenue covers 66% to 73% of the 2011 to 2024 10-Ks with the three tags; without the widening, the no-revenue rule would remove companies that have revenue |
| `resultado_bruto` | `GrossProfit`; if missing, revenue minus cost of sales | in the DFP line 3.03 is mandatory; under US GAAP gross profit is optional (coverage of 35% to 37%) |
| `despesas_vendas` + `despesas_gerais_adm` | `SellingGeneralAndAdministrativeExpense`, which already joins both | v1 adds the two accounts; under US GAAP they come together |
| `lucro_operacoes_continuadas` | `IncomeLossFromContinuingOperations`; if missing, net income minus `IncomeLossFromDiscontinuedOperationsNetOfTax`, when present | account 3.09 is after taxes; the pre-tax tag of the Phase 0 proposal is dropped, being a different concept |
| `emprestimos_cp` | `DebtCurrent`; if missing, the sum of `LongTermDebtCurrent` and `ShortTermBorrowings` present | under US GAAP short-term debt may come in separate lines |
| `emprestimos_lp` | `LongTermDebtNoncurrent`; if missing, `LongTermDebtAndCapitalLeaseObligations` | the same concept, with the second tag as a fallback |
| `despesas_financeiras` | `InterestExpense` | recorded limitation: the DFP's financial expense includes FX variation and other charges; the US tag is interest only |
| `fornecedores` | `AccountsPayableCurrent`; if missing, `AccountsPayableAndAccruedLiabilitiesCurrent`, flagged as including accruals | the second tag is wider |
| `passivo_total` (naive rule) | `Liabilities`; if missing, `LiabilitiesAndStockholdersEquity` minus equity including noncontrolling interest | the naive rule uses total liabilities ÷ total assets, and many companies do not present total liabilities |

The Benford deviation uses the fiscal year's nonzero values in the 10-K's balance sheet, income statement and cash flow statement (by the `stmt` column of `pre.txt`: BS, IS and CF), the US equivalent of BPA, BPP, DRE and DFC, with v2's minimum of 20 numbers. The DVA does not exist in the US: v2's DEPI is v1's, from cash-flow depreciation. Before registration, the coverage of each account under the rules above is counted (counts only) and goes into the registered text.

### 3.2 The rate that replaces the CDI

The Effective Federal Funds Rate, daily series DFF on FRED (Federal Reserve Bank of St. Louis), sourced from the Federal Reserve's H.15 release: public, free and with no key. Like `chiocca.cdi.medio`, the average of the daily rates over the 12 months ending at the fiscal year end, with the same 10 p.p. cut-off. Reason: it is the US overnight interbank rate, the CDI's role in Brazil. Recorded limitation: DFF annualizes on a 360 calendar-day basis and the CDI on a 252 business-day basis. The series file goes into the repository, like `data/cdi_sgs4389.csv`, with its SHA-256 in the manifest.

### 3.3 The cut-off date

The same rule as study 1 (amendment 5, `chiocca.corte.data_corte`): the last day of the fourth month after the fiscal year end. Reason: the 10-K deadline is 60, 75 or 90 days, depending on size, and, from 2011 to 2024, the latest-filed tenth of 10-Ks came out up to 107 days after the report date (Phase 0, section 2.2). The version used is the one public at the cut-off: the last filing by that date between the original 10-K and the 10-K/As with account numbers (Phase 0, section 2.3). A company with no XBRL 10-K by the cut-off is out for that fiscal year, as in Brazil.

### 3.4 What is not adapted

Financial companies: the map has no accounts for them, so the financial group and the weight of non-recurring gains do not exist in this study. The DVA (section 3.1). The document reader.

## 4. Sample and exclusions

- **Universe:** the original 10-Ks in the Financial Statement Data Sets with a report date from 2011 to 2024 (the fiscal year is the year of the report date, as in the DFP). 2011, because XBRL applies to all companies from periods after 2011-06-15; 2024, because the 12-month window of that fiscal year has already ended, on 2026-04-30 (Roberto's decision of 2026-11-24).
- **Exclusions, in this order, each counted in the report:** (1) no public XBRL version by the cut-off; (2) financial companies by SIC, 6000 to 6999, except 6770 (section 3.4); (3) SPACs, SIC 6770, an explicit rule decided by Roberto on 2026-11-24; (4) companies without revenue (revenue missing or zero, the study 1 rule, by the widened map); (5) those with no computable signal. SIC and revenue are those of the version used.
- **The size, from Phase 0 (declared fiscal year, Phase 0 map):** from 2011 to 2024, 86,766 original 10-Ks: 18,628 financial, 3,042 SPACs (2,905 of them already without revenue) and 19,409 others without revenue (a ceiling, because the Phase 0 revenue map was not widened); 45,687 remain.

## 5. The outcome: the 8-K with Item 4.02, per case

- **Episode (the case):** a company's first 8-K with Item 4.02 in the EDGAR items field opens an episode; every 8-K or 8-K/A with Item 4.02 from the same company within the next 365 days belongs to it; after that, a new 8-K 4.02 opens another episode. Each episode counts once, the answer to Walker's and Gow's critique of Bao et al. (Phase 0, section 5.1).
- **Window:** company-year t is positive if an episode opens after the cut-off of t and within 12 months of it. The windows of consecutive fiscal years of the same company do not overlap, and each episode falls into at most one company-year. Episodes outside any sample company-year enter the description only.
- **Source:** the items field of the EDGAR filing history (`submissions.zip`), downloaded again on the day of the computation, with its SHA-256 in the manifest, and only the 8-Ks filed through 2026-04-30, the end of the window of fiscal 2024.
- **The size, from Phase 0:** from 2009 to 2026-04-30, 2,386 company-years with an 8-K 4.02 and a 10-K in the SEC data before the 8-K: 263 financial, 363 SPACs and 617 others without revenue by the Phase 0 map; 1,143 remain, from 48 to 111 a year by filing year from 2012 to 2025.
- **Limitations:** Item 4.02 does not say which statements stopped being reliable: the outcome is a non-reliance statement within the next 12 months, with no guarantee that it concerns fiscal year t. Restatements without an 8-K ("little r") are left out. None of this is called fraud.

## 6. Metrics: those of study 2

- **Main measure:** the risk difference DR = P(positive | alert) − P(positive | no alert), on the company-years evaluated by v1, with all fiscal years together; also the rate ratio.
- **Bootstrap by company:** companies are drawn with replacement, each with all its company-years; 10,000 resamples, with seed 20270430; the interval is the one-sided 95% percentile. The functions are `taxas`, `dr`, `bootstrap_por_companhia` and `limite_inferior` from `chiocca/v2/estudo2/secundaria.py`, called without changing a line.
- **Result:** "positive association" if the lower bound of the one-sided 95% interval of the DR is above zero; otherwise, "no evidence of association".
- **Naive rule side by side:** the most leveraged decile (total liabilities ÷ total assets) of each fiscal year, as in study 1, with the same DR and the paired bootstrap (the same resamples): "the engine separates better than the naive rule" only if the lower bound of the difference is above zero.
- **v2 paired with v1:** as in study 2's amendment 5. v2's alert comes from all company-years v2 evaluates; the measures are computed on the company-years evaluated by v1; "v2 separates better than v1" only if the lower bound of the paired difference is above zero; otherwise, no winner declared.
- **Descriptive:** study 2's ranking metrics (precision and lift at the top 1%, 5% and 10% and NDCG@k), each fiscal year separately and the AAERs (section 7). Aggregates only: no list of companies by alert.

## 7. The 2009 to 2014 AAERs: a separate description

For the 25 Bao et al. cases (47 company-years) with a 10-K in the SEC data (Phase 0, section 4.1): how many cases v1, v2 and the naive rule alerted in at least one affected fiscal year, with the version public at the cut-off. Counts only, with no test and no list. In 2009 and 2010, only the largest companies filed in XBRL.

## 8. Predictions written before the data

1. **v1 alert rate:** between 25% and 45% of the evaluated non-financial companies in each fiscal year. Reason: the M-score above -1.78 flags a relevant share of US companies, and the DPO decile adds 10%; implied interest fires less than in Brazil, because US interest expense does not include FX variation.
2. **v2 alert rate:** between 10.0% and 11.0% in each fiscal year, by the construction of the decile.
3. **Outcome rate:** between 1.5% and 4% of the evaluated company-years. Reason: the counts in section 5, about a hundred company-years a year, against a few thousand evaluated.
4. **v1 DR:** positive, with a rate ratio between 1.1 and 1.5, and "positive association" more likely than not, given the sample size.
5. **v2 DR:** positive, with a rate ratio between 1.2 and 2.0, and "positive association".
6. **v2 paired with v1:** a positive difference, with the lower bound above zero ("v2 separates better than v1"). Reason: v2's alert group is smaller and more extreme.
7. **v2 against the naive rule:** no winner declared. Reason: leverage is also associated with restatements, through financial distress.
8. **AAERs:** of the 25 cases, between 30% and 60% in alert under v1 and between 10% and 30% under v2 in at least one affected fiscal year.

## 9. Timeline through May 2027

| By | Step |
| --- | --- |
| 2026-11-24 | Roberto's decisions: the label, the outcome per case and the exclusions. This draft. |
| 2026-12-15 | Roberto's review of this draft; no signal computed. |
| 2027-01-31 | Study code written and tested on synthetic data only; coverage of the widened map counted (counts only); no US signal computed. |
| 2027-03-31 | Pre-registration registered and timestamped; code frozen with a SHA-256 registry. |
| 2027-04-30 | Single computation, after the timestamp, with the SEC files downloaded again on the day. |
| 2027-05-31 | Report in PT and EN, separate from Brazil's study 2. |

## 10. Open points for Roberto, before registration

1. The exclusion of financial companies (section 3.4).
2. The tags of the revenue widening and the derivations in section 3.1, chosen by coverage.
3. Decided by Roberto on 2026-11-24: the sample goes to fiscal 2024, with the 8-Ks through 2026-04-30.
4. The seed (20270430, the date of the single computation).
5. The data archive: the SEC files exceed 6 GB and stay outside Git, with their SHA-256 in the manifest and the download by script.

## 11. What is left out

Financial companies, the DVA and the reader (section 3.4); any list or ordering of companies by alert; any investment recommendation; and, until Roberto decides, the US front in the README and the product.
