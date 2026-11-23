# US Phase 0: data reconnaissance

> **Reconnaissance, with no signal computed.** Goal: find out whether a pre-registered US study is feasible, with the data as they were at the time, testing Chiocca's v1 and v2 signals and the naive rule against the SEC's AAERs (Accounting and Auditing Enforcement Releases). Inventory and counts only; nothing from 2024 on; no names of individuals. The US front stays out of the README and the product until Roberto decides.

## 1. Access to the SEC

The SEC asks for a User-Agent with a name and contact and at most 10 requests per second; without the contact it refuses the request (HTTP 403, checked in this session). The scripts read the User-Agent from the environment variable `SEC_USER_AGENT`, which no versioned file or log keeps. In this session the variable was not set, and the environment's privacy tool does not let the agent write the contact into a command: **0 of 60 quarterly SEC files were downloaded**. To finish Phase 0, Roberto sets `SEC_USER_AGENT` in the environment settings (environment variable) and a new session runs `python -m chiocca.eua.fase0 --baixar`.

## 2. Balance sheets: the SEC Financial Statement Data Sets

The financial statement numbers in XBRL, one zip per filing quarter since 2009 (here, from 2009q1 to 2023q4: the 10-Ks for fiscal 2023, almost all filed in 2024, are left out). The two files used are `sub.txt` (one row per filing: CIK, form, report date, fiscal year, filing dates and whether the filing was later amended) and `num.txt` (one row per number: tag, taxonomy, date, quarters covered, unit and value).

- **10-K and 10-K/A:** the original filing and each amendment are separate filings, each with its date; `prevrpt` flags a filing that was later amended.
- **The public version at a cutoff date:** per company and fiscal year, the last filing (original or amendment with XBRL numbers) filed by that date, like Chiocca's "as it was" in Brazil; the next year's comparative column shows the t-1 numbers as presented later.

**Pending (without the SEC files):** the structure checked on the files, 10-K coverage by year, amendments, filing lags and the coverage of each tag by year. The code is ready and tested on a synthetic file (`chiocca/eua/fsds.py`).

### The map from accounts to us-gaap tags (proposal)

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

## 3. Labels: the AAERs

**era-py 0.0.37** (PyPI, by Ian Gow, the data for the book *Empirical Research in Accounting: Tools and Methods*): package license MIT; the tables carry no license of their own, and the source of the gvkey–CIK link is not stated. So nothing from them is copied into the repository: the wheel stays in `data/eua/`, with its SHA-256 in the manifest (`5f79fc223a17af9147b65a9a24f918355fc8a31f9341cd7fed8c0267b3591c0c`).

- **The SEC AAER index** (`aaer_dates`, refreshed by the author through 2026-10-08): number, date, description and year. Through 2023, 3,277 AAERs (3,248 distinct numbers), from 1999 to 2023. The description carries names of companies and individuals and is not read here.
- **The Bao et al. (2020) company-years** (`aaer_firm_year`): 415 rows, 412 AAERs and 402 companies, identified by gvkey (Compustat), with the first and last affected years, from 1990 to 2014: 990 company-years with an alleged misstatement. 233 of the AAERs affect more than one year.
- **The gvkey–CIK link** (`gvkey_ciks`): 49,089 links, 29,099 gvkeys and 27,708 CIKs, with the dates of each link. With it, each Bao et al. company-year links to the SEC CIK without Compustat.
- **The CFRM (Berkeley) database, used by Dechow et al. (2011):** now sold through the USC site ("Buy the Data" page, payment through cashnet; the price does not appear in the page text); the terms forbid passing the data to third parties, except co-authors; it covers 4,581 AAERs issued from 1982-05-17 to 2025-12-31, with the company's name and identifiers, the affected accounts and the misstated years and quarters (the page does not say which identifiers). Only the access conditions were read.
- **The public AAER list on the SEC site:** not read directly (the site requires the User-Agent with a contact); the era-py index is a copy of it, with the refresh date.

**How to link each AAER to the CIK without Compustat.** Through 2014, through the Bao et al. company-years and the era-py gvkey–CIK link. After 2014, there is no free database with the misstated years: the path is to read each AAER on the SEC site (the company is a party) and match the name against the SEC file of names and CIKs (`cik-lookup-data.txt`, to be checked once access is set up), keeping only the company and the CIK.

## 4. Counts

| Fiscal year | Company-years with an AAER (Bao et al.) | Linked to a CIK | With a 10-K in the SEC data | Company-years with a 10-K |
| --- | ---: | ---: | ---: | ---: |
| 2009 | 31 | 30 | pending | pending |
| 2010 | 26 | 24 | pending | pending |
| 2011 | 22 | 22 | pending | pending |
| 2012 | 19 | 19 | pending | pending |
| 2013 | 11 | 11 | pending | pending |
| 2014 | 4 | 4 | pending | pending |

In the fiscal years with XBRL (2009 to 2014, the end of the Bao et al. affected years): 113 company-years with an AAER, of which 110 link to a CIK. The most recent years have fewer cases because an AAER usually comes out years after the fraud, and the database ends in 2014. The SEC index has 1,572 AAERs issued from 2009 to 2023, of all kinds (not only misstatements).

## 5. Decisions for Roberto

1. **Possible period.** XBRL balance sheets since 2009 (all companies since 2011). With free labels, the affected years only go to 2014: the overlap is 2009 to 2014. To go beyond 2014, buy the CFRM database (through 2025) or classify the SEC AAERs by hand.
2. **Expected size.** 113 company-years with an AAER in the XBRL fiscal years, 110 linked to a CIK, against the 10-Ks of each year (the number comes from the SEC files). With multi-year frauds counted once, the number of cases is smaller still: power will be low, as in study 1.
3. **What cannot be done without paid data.** Misstated years after 2014 (CFRM); the gvkey and Compustat data (WRDS); Audit Analytics restatements. The era-py gvkey–CIK link does not state its source.
4. **Multi-year frauds.** Walker (2021) showed that, in Bao et al. (2020), frauds spanning the training and test periods inflate the metric; the erratum (JAR, 2022) acknowledged a code error that left about 10% of these cases unrecoded, Walker (2022) criticized the erratum, and Gow (2022) discussed whether the paper should be retracted. Proposal: the outcome per case (one fraud, counted once), like the study 1 detection, with the bootstrap by company, as in study 2; the signals are fixed rules, with no training.

### Draft timeline through May 2027

| By | Step |
| --- | --- |
| 2026-12-15 | Roberto sets the User-Agent; Phase 0 ends with the SEC files (structure, 10-Ks by year, tag coverage). |
| 2027-01-15 | Decision on labels (through 2014, buy the CFRM, or classify by hand) and on the period. |
| 2027-02-28 | Draft of the US pre-registration: sample, outcome per case, metrics and naive rule. |
| 2027-03-31 | Roberto's review, registration and timestamp; code frozen. |
| 2027-05-31 | Single computation and report, separate from Brazil's study 2. |

Sources for the conditions and the critique: sites.google.com/usc.edu/aaerdataset (Buy the Data); econjwatch.org (Walker, 2021 and 2022); iangow.github.io/notes/published/bklyz.html (Gow, 2022).
