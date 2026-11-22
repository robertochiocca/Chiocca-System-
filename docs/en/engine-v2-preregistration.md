# Engine v2 pre-registration

> **Registered on 2026-11-22.** Written by the agent with Roberto's decisions and reviewed by Roberto with Claude (claude.ai), who approved the text without changes (section 12). The commit that introduces this version is the registration, and its hash is noted in the next commit, without changing any rule, as in study 1, the reader and study 2. Amendment 5 to study 2, which adds the v2 arm, was registered in the same commit, in section 13 of the [study 2 pre-registration](study-2-preregistration.md).
>
> Basis: the [engine v2 plan](engine-v2-plan.md), with Roberto's decisions of 2026-11-22, and the [label-free descriptions](engine-v2-descriptions.md), with fiscal years up to 2023 only. No value from fiscal year 2024 onward was read; of the DFPs from 2024 onward, only metadata.

## 1. What v2 is

Engine v2 is engine v1 with three changes, each tied to a documented v1 failure in study 1: (1) DEPI from the DVA when the DFC does not give DEPI; (2) the standardized Benford deviation as a new signal, in both groups; (3) the alert by score, on 10% of the year within the group, instead of the fixed cut-offs. Everything else is v1's: the "as it was at the time" base, the samples, the exclusions, the groups and the formulas of the signals that already existed. v2 is evaluated as one more arm in study 2's secondary evaluation (amendment 5) and, later, in a prospective test of its own with fiscal years 2026, with its own pre-registration. The product stays on v1; switching to v2 is a separate decision, after the 2027 evaluation.

## 2. Sample, groups and version used

As in v1 (study 1 pre-registration, sections 2 and 3, and amendments): listed companies with a DFP, in two groups, non-financial and financial; the same exclusions; each company-year with the DFP version public at the cut-off, and, when the open-data version is later than the cut-off, the point-in-time version through the ENET route, consolidated only.

## 3. Signals by group

| Group | Score signals |
| --- | --- |
| Non-financial | M-score (with DEPI from the DVA), DPO jump, implied interest, standardized Benford deviation |
| Financial | share of non-recurring gains, standardized Benford deviation |

Earnings not backed by cash stay on the alert sheet, outside the score, as in v1 (study 1 pre-registration, section 4: they already enter the M-score through TATA). In every signal, a higher value means more unusual.

### 3.1 M-score, with DEPI from the DVA

- **Formula (Beneish, 1999), as in v1:** M = -4.84 + 0.920 DSRI + 0.528 GMI + 0.404 AQI + 0.892 SGI + 0.115 DEPI - 0.172 SGAI + 4.679 TATA - 0.327 LVGI, with v1's components and calculation choices (signal catalog; study 1 pre-registration, section 4.1). The -1.78 cut-off no longer exists: M enters the score through its percentile (section 4).
- **DEPI:** rate at t-1 ÷ rate at t, with rate = depreciation ÷ (depreciation + property, plant and equipment).
- **Depreciation, in this order:** (1) the DFC's, as in v1 (sub-accounts of 6.01.01 whose name contains "deprecia"; the line combining depreciation and amortization enters by its total, with the flag); (2) if v1's DEPI cannot be computed and the version used is the open-data one, the DVA's: account 7.04.01, 7.05.01 or 7.07.01 whose name contains "deprecia", in that order of preference, of the same type (consolidated or individual) and from the same DFP, in the t and t-1 columns, in absolute value, with the flag "depreciation from the DVA". In ENET versions, which do not bring the DVA, DEPI stays as in v1.
- **Coverage in the descriptions (2010 to 2023):** the M-score goes from 5,390 to 6,017 of the 6,938 non-financial company-years.

### 3.2 DPO jump, implied interest and share of non-recurring gains

- **DPO jump:** as in v1, DPO at t minus DPO at t-1, with DPO = trade payables ÷ |cost of sales| × 365.
- **Implied interest:** as in v1, |finance costs| ÷ average short- and long-term borrowings at t and t-1, minus the year's average CDI (SGS 4389). Within a year, the order is the same as the implied rate's. The 3.06.02 sub-accounts do not enter: they appear in 8.8% to 12.4% of the evaluated non-financial companies from 2019 to 2023, below the 50% criterion written before the description.
- **Share of non-recurring gains (financial companies):** as in v1.

### 3.3 Standardized Benford deviation

- **The figures:** the non-zero values in the fiscal-year column of BPA, BPP, DRE and DFC of the version used, the four statements that exist in the open data and in ENET. From each, the first significant digit of |value|.
- **The deviation:** the mean absolute deviation between the frequency of each digit from 1 to 9 and Benford's law, log10(1 + 1/d), summed and divided by 9.
- **The bins:** the quintiles of the number of figures, within the fiscal year and the group, among the company-years with at least 20 figures (pandas `qcut` over `rank(method="first")`, 5 bins).
- **The standardization (Chakrabarty et al.'s, 2025):** (deviation - mean deviation in the bin) ÷ standard deviation of the deviation in the bin (sample, n - 1). The article's coefficients, estimated with US AAERs, are not used.
- **Computable** if the company-year has at least 20 figures (no company-year from 2010 to 2023 has fewer than 23) and the bin has a standard deviation above zero.
- **In the descriptions (2010 to 2023):** the top of the standardized deviation stays between 18.0% and 21.3% in each quintile of the number of figures among non-financial companies; it does not concentrate in companies with few figures.

## 4. Score, alert and ranking

- **Percentile of each signal:** within the fiscal year and the group, among the company-years where the signal can be computed, by pandas `rank(pct=True)` (ties get the average position).
- **Score:** the highest percentile among the company-year's computable signals. It was chosen, against that highest percentile raised to the number of computable signals, by the label-free description in section 7 of the descriptions, with the criterion written by Roberto before running (the version with the smaller of the largest distances between the rate by number of computable signals and the group rate stays; in a tie, the simple highest percentile): the largest distance was 6.8 pp with the highest percentile and 12.9 pp with the version raised to the number of signals.
- **Evaluated:** a company-year with at least one computable signal.
- **Alert:** score greater than or equal to the 90% quantile of the score among the evaluated company-years of the fiscal year and group, by pandas `quantile(0.9)`, with linear interpolation, like v1's decile. The rate stays close to 10% by construction; ties at the threshold can push it slightly above.
- **Ranking for study 2's ranking metrics:** the score, from highest to lowest, with company-years without a score after; ties broken by CVM code, in ascending order, and, between the two company-years of the same company, by fiscal year, in ascending order (study 2, amendment 2, item 3(b)).
- **Alert sheet:** each signal with its value, its percentile and which one sets the score; earnings not backed by cash appear without entering the score.
- **Known characteristics, with no correction.** (1) The alert rate varies with the number of computable signals: among non-financial companies from 2010 to 2023, 7.0% with one signal, 16.9% with two, 14.5% with three and 9.1% with four. (2) The top concentrates in companies with few figures: 32.0% of the alerts in the quintile with the fewest figures and 11.1% in the quintile with the most, among non-financial companies. This comes from the M-score, the DPO and implied interest, not from Benford: without Benford, the first quintile would hold 31.5% of the alerts, and the top of the standardized Benford stays between 18.0% and 21.3% in each quintile. In the 2027 report, the distribution of v2's alerts by quintile of the number of figures enters only in aggregate, as description.

## 5. Development rule

- **Fiscal years up to 2023 only.** v2's code is written and measured with the product seal at 2023 and 2024-12-31. No data from 2024 onward are read before the seal session of v2's list.
- **Label-free criteria only:** coverage, alert rate, stability across years and correctness tests. The choices in this pre-registration were made that way, with the descriptions.
- **The ground truth is not used** to choose or tune anything. v2's code does not read `data/gabarito_casos.csv` or import study 1's metrics; a test checks it.
- **v2's detections on study 1 cases** only after the freeze, as an in-sample description, labeled "inside the development sample, not a test". No detection, case or alert by company of the ground truth is computed or shown before that.

## 6. Freeze

- **Its own SHA-256 registry** (`docs/motor_v2_codigo_congelado.json`), with a test that flags any change. v1's registry (`docs/estudo_2_codigo_congelado.json`) does not change.
- **A hand-computed example from a separate script,** written before v2's code, like study 1's worked example: (a) Benford, on a fictitious table of company-years, with the digits, the deviation, the bins and the standardization; (b) DEPI from the DVA, on a fictitious company-year with no depreciation in the DFC. v2 must reproduce the script's values.
- **Invariant:** with the three changes switched off (DEPI from the DFC only, no Benford and v1's alert rules), v2 reproduces v1 in the 9,474 company-years of the study 1 invariant.
- **Description of the frozen v2, in sample:** the alert rates and coverage from 2010 to 2023 and, only then, the detections on study 1 cases, labeled.

## 7. Predictions written before the data (v2 arm in study 2)

1. **Alert rate:** between 10.0% and 11.0% of the evaluated non-financial companies in each fiscal year and between 10% and 14% of the financial ones. Reason: the alert is the score's top decile; ties at the threshold and small groups pull the rate slightly up. In the 2010 to 2023 descriptions, with the standardized Benford, the rate was 10.1% among non-financial companies and 11.6% among financial ones.
2. **v2's RD:** positive, with a rate ratio between 1.0 and 2.0, and "no evidence of association" as the most likely result. Reason: with about 1,200 evaluated company-years and 10% in alert, there are about 120 company-years in alert, and, at the 4.7% rate, about 6 restatements would be expected among them with no association at all. Assuming independent company-years, the approximate power of the one-sided test is 0.25 for a rate ratio of 1.5, 0.53 for 2.0 and 0.76 for 2.5; with the bootstrap by company, it is lower. The signals measure accruals, payment terms and financing, which only partly end in a restatement.
3. **Paired difference v2 minus v1 (RD):** no winner declared. Reason: v1 flags close to half of the company-years (study 2's prediction is 40% to 60%) and v2, 10%; the two RDs come from alert groups of very different sizes, and the interval of the difference is wide.
4. **v2 against the naive rule:** no winner declared. Reason: both flag 10% of the company-years, the alert groups are small, and the naive rule's leverage is also related to financial distress, which can lead to restatements.
5. **Prospective subset:** with the target met, most of the 2025 company-years are prospective. Reason: in the descriptions, 98.7% of the first filings of the 2023 DFP up to the cut-off came after 2024-01-31.

## 8. Prospective label, parts 2a and 2b and Roberto without opening the list

- **Prospective label by company-year:** a 2025 company-year is prospective for v2 if the first filing of its 2026 DFP (the smallest DT_RECEB in the CVM index) is later than the commit with the SHA-256 of v2's list. The 2024 ones are not prospective in either arm. The v2 arm is reported in total and in the prospective subset; if the calendar's fallback applies, the whole arm also carries the label "not prospective".
- **Parts 2a and 2b:** for the v2 arm, part 2 of study 2's ground truth is split by the date of that commit: 2a, with the cases whose qualifying document (study 2, amendment 1, item 1) becomes public between the freeze of part 1 (2026-11-19) and the commit; 2b, with those public after it and up to 2029-12-31. The comparison with v1 in the descriptive primary outcome uses only 2b; 2a carries the label "public before v2's seal". For v1, nothing changes.
- **Roberto without opening the list:** Roberto does not open v2's list file or run its code before freezing part 2 of the ground truth. At the secondary evaluation, the list is recomputed by the script, and only aggregate measures come out; the agent does not describe any v2 alert by company.

## 9. Calendar

| Step | Deadline | If it slips |
| --- | --- | --- |
| Registration of this pre-registration and of amendment 5 to study 2, with the OpenTimestamps stamp | 2026-12-20 | The dates below do not change. Without both registered before the seal session, v2 does not enter study 2. |
| Target: v2 frozen (SHA-256 registry, hand-computed example, invariant) | 2027-01-25 | The fallback applies. |
| Target: seal session of v2's list | 2027-01-31 | The fallback applies. |
| Fallback: v2 frozen | 2027-03-31 | It does not enter, with no further extension. |
| Fallback: seal session, with the label "not prospective" | from 2027-04-01 to 2027-04-15 | It does not enter, with no further extension. |
| Cut-off of the 2026 DFP | 2027-04-30 | study 2 pre-registration date, does not change |
| Secondary evaluation, both arms in the same session (v1 first) | from 2027-05-31 | "From": the date can pass. |
| Prospective test of v2's own, with fiscal years 2026 | later, with its own pre-registration | — |

## 10. What stays out

The 3.06.02 sub-accounts in implied interest; discretionary accruals and the Dechow et al. (2011) F-score, for the reasons in the plan; quarterly data (ITR); supervised learning; any data from 2024 onward in development; any change to engine v1 or its registry.

## 11. Registration

- Date: 2026-11-22.
- Commit: the one that introduces this version under this name, the same one that registers amendment 5 to study 2. Its hash is noted here in the next commit, without changing any rule above.
- Timestamp, as in study 2: `docs/carimbos/motor-v2-registro.txt`, with the hash of the registration commit and the SHA-256 of the two registered files (this pre-registration and study 2's with amendment 5), stamped with OpenTimestamps; the `.ots` goes into the repository, and `ots upgrade` is run after confirmation on Bitcoin. If the calendars do not respond, Roberto stamps through the opentimestamps.org website and returns the `.ots`.

## 12. Roberto's review (2026-11-22)

Roberto read the whole text, in the version of commit `fbb9bb2f11eaebc03dfedf2c68d671e299e9d9de`, and amendment 5's, in the version of commit `31866e6f00d2004021a506bdb9f56b8a93bb7d5c`, with Claude (claude.ai), and approved both without changes:

1. The three changes: DEPI from the DVA, the standardized Benford deviation as a signal in both groups and the alert by score.
2. The score by the simple highest percentile, one version for the whole engine, financial companies included, with the alert on 10% of the year within the group.
3. Benford with at least 20 figures and the standardization by bin of the number of figures.
4. The predictions in section 7.
5. The prospective label by company-year.
6. Parts 2a and 2b.
7. The calendar with the target and the fallback.
8. The product staying on v1; switching to v2 is a separate decision, after the 2027 evaluation.
