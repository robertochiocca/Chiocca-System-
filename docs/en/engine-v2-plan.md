# Engine v2: draft plan

Draft of 2026-11-22, requested by Roberto, with his decisions of the same day (summary at the end). **It is not the pre-registration and has no engine code.** It was written without any value from fiscal year 2024 onward. Study 1 figures come from [`docs/resultados_numeros.json`](../resultados_numeros.json); study 2 figures, from [`docs/estudo_2_numeros.json`](../estudo_2_numeros.json), metadata only; dates and rules, from the [study 2 pre-registration](study-2-preregistration.md), which does not change in this round: the amendment in section 4 is only a draft. A test checks each figure against the JSON files.

**Status (2026-11-22):** the [engine v2 pre-registration](engine-v2-preregistration.md) and amendment 5 to study 2 were registered in commit `313c52db5df2f11b0a4f9d7920e486e688a9f381`; the hash was noted in commit `29e472b130a61f1358b97694eddbeaba6e9bbb88`, and the stamp went in with commit `13564a22074aca81a7b96dcdf9c8cda4fe3a9c81`. This plan stays as the record of the decisions that led to the pre-registration.

## Goal

- **Attempt v2 in study 2** (Roberto's decision, 2026-11-22), as one more arm in the secondary evaluation (from 2027-05-31), next to v1 and the naive rule, through amendment 5, which only adds the arm. The v1 analysis does not change at all: list, registry, outcomes, metrics, seed, criteria and predictions stay as pre-registered.
- **Prospective target:** v2 frozen by 2027-01-25 (code and its own SHA-256 registry) and its list for 2024 and 2025 sealed by 2027-01-31, before most of the 2026 DFPs are filed.
- **Fallback:** if the target is not met, the freeze by 2027-03-31 and the seal by 2027-04-15 apply, before the 2027-04-30 cut-off, with the label "not prospective", with no further extension. If the fallback is not met either, v2 does not enter study 2; the v1 evaluation proceeds as pre-registered.
- **Label by company-year, in any case:** a 2025 company-year counts as prospective for v2 if its 2026 DFP was received after the commit with the SHA-256 of v2's list, by the DT_RECEB in the CVM index; with more than one version, the first filing (the smallest DT_RECEB) counts, because an earlier version would already have made the 2025 comparative public. The 2024 company-years are not prospective in either arm. The v2 arm is reported in total and in the prospective subset.

## 1. Candidate changes

Each change answers a documented failure of v1 in fiscal years 2010 to 2023. The final choice (section 2) uses only label-free criteria; study 1 case counts are known, but they do not enter the choice.

### 1.1 Implied interest revised

- **v1 failure.** Implied interest alone accounts for 59.8% of non-financial company-years in alert (2,001 of 3,345). It flags 40.7% of the company-years where it can be computed (2,528 of 6,214), between 31.5% and 52.1% depending on the year. Finance costs (3.06.02) include exchange-rate variation, lease interest and other items that are not interest on borrowings, and the fixed cut-off (the year's average CDI plus 10 pp) does not follow the year.
- **Change, with the DFP only.** (a) Remove from finance costs the 3.06.02 sub-accounts whose name indicates exchange-rate variation or leases, when the company breaks them out, located by text like v1's depreciation in the cash flow statement, with each failure recorded; (b) replace the fixed cut-off with the cut-off by fraction of the year (1.3).
- **Stays out.** The version based on the notes to the financial statements (item 2 of section g of the [study 2 plan](study-2-plan.md)) needs the notes, which are not among the inputs (section 3).
- **Decision:** (b) enters through 1.3. (a) enters only if the description shows enough coverage of the sub-accounts, in the open-data versions and in the ENET ones. Proposed criterion, to be closed in v2's pre-registration: (a) enters if, in each fiscal year from 2019 to 2023, at least half of the evaluated non-financial company-years break 3.06.02 into at least one sub-account recognizable by name as exchange-rate variation or leases.

### 1.2 Depreciation from the DVA

- **v1 failure.** The M-score had no value in 1,548 of 6,938 company-years; in 1,306, DEPI was missing. The most common reason is a cash flow statement with no depreciation line in section 6.01.01 (1,135 company-years).
- **Change.** When the cash flow statement does not bring depreciation, use the DVA's fixed account "Depreciação, Amortização e Exaustão" (7.04.01 in most charts of accounts; 7.05.01 or 7.07.01 in others, [reconnaissance](reconnaissance.md)). It combines depreciation and amortization: the rule v1 already applies to the combined cash-flow line holds (use the total and flag the company-year). The cash flow statement stays first, and v2 equals v1 wherever v1 already computes DEPI.
- **Limit.** The DVA is in the DFP zips, but study 2's 26 ENET documents bring only BPA, BPP, DRE and DFC. In company-years whose point-in-time version comes from ENET, there is no DVA for that version; using the DVA of a later version would break the "as it was at the time" rule. There, DEPI stays as in v1.

### 1.3 Label-free cut-offs

- **v1 failure.** The fixed cut-offs give very different and unstable fractions across signals and years: the M-score above -1.78 flags 15.0% of the company-years where it can be computed (810 of 5,390), between 8.9% and 24.5% depending on the year; implied interest, 40.7% (between 31.5% and 52.1%); the DPO jump, in the top decile, 10.1% (641 of 6,341). The -1.78 cut-off comes from Beneish (1999), with US companies, and was not recalibrated for Brazil. The alert rate of non-financial companies was 49.9% (3,345 of 6,704).
- **Change.** Each signal flags a fixed fraction of the year's company-years where it can be computed, within each group (non-financial and financial), as the DPO and the naive rule already do. The cut-off comes only from the signal's distribution in the year, without the ground truth.
- **The fraction: two options, described with fiscal years up to 2023 only, by year and group.** (i) The top decile in each signal, with the resulting rate of the union (company-years with at least one alert) and the overlap between signals. (ii) The alert on 10% of the year, within the group, with company-years ranked by the highest percentile among the computable signals, the same rate as the naive rule, with how many times each signal sets that maximum. The choice goes into v2's pre-registration, using only these descriptions. Provisional recommendation: (ii), because it fixes the alert rate at the naive rule's and makes the comparison with it direct.

### 1.4 Adjusted Benford deviation

- **Origin.** Item 9 of section g of the [study 2 plan](study-2-plan.md), based on Chakrabarty et al.'s (2025) AB-score, in a label-free version ([references](references.md)).
- **v1 failure it answers.** Coverage: the M-score had no value in 1,548 of 6,938 company-years (22.3%), and the Benford deviation can be computed for almost all of them.
- **What.** The mean absolute deviation of the first-digit distribution of the figures in the DFP version used, normalized within the year by bins of the number of figures (the article's `B_Input`) and by the year (`B_Year`); alert in the top decile of the year, within each group. The article's coefficients, estimated with US AAERs, are not used.
- **Input choice.** Only the figures in BPA, BPP, DRE and DFC, the four statements that exist both in the DFP zips and in the ENET documents: this way, every company-year is measured on the same set of statements, wherever its version comes from.
- **Before deciding:** describe, with fiscal years up to 2023 only, the distribution of the number of figures per company-year, which defines the bins. In the article, on its own, it flags too much: it enters as a complementary signal, with the same fraction as the others.
- **Decision:** it also enters for financial companies, within the group. It does not depend on the chart of accounts, and today financial companies have a single signal.

### 1.5 Discretionary accruals

- **Can it be done with the DFP only?** Yes, in part. Modified Jones uses total accruals, the change in revenue and receivables, property, plant and equipment and assets at t-1, all in the t DFP (columns t and t-1). It also needs the sector, and the CVM registry brings only the current sector (`SETOR_ATIV`); each year's sector is in the FCA.
- **Decision: it stays out of v2.** (1) The regression by sector and year needs at least 10 companies per cell, and study 1 evaluated from 408 to 601 non-financial companies per year: with a split by sector, many cells fall below 10, and the choice of classification and of how to treat small cells would be a free parameter, with no clear label-free criterion; (2) total accruals are already in the M-score (TATA); (3) the time until 2027-03-31 does not fit one more model with estimation. It stays for a later version, with its own pre-registration.

### 1.6 Dechow et al. (2011) F-score

- **Can it be done with the DFP only?** Not with study 2's inputs. Model 1 uses the change in ROA and the change in cash sales, which need t-2 balances (average assets at t-1 and receivables at t-2). The t DFP brings only t and t-1; for 2024, t-2 would be in the 2023 DFP, which is not on the `estudo-2-dados` branch (section 3).
- **Decision: it stays out of v2.** Besides the missing input, the coefficients were estimated with US AAERs, the same problem as the -1.78 cut-off, and most of the information (accruals, receivables) is already in the M-score.

### 1.7 Out of this version

- **ITR (quarterly data):** they are not among study 2's inputs, and the case that motivated them (IRB, which cannot be detected with the annual DFP) is financial and depends on 2024 and 2025 quarterly data that were never downloaded.
- **Supervised learning:** it needs labels to train, and the rule in section 2 forbids using the ground truth to choose or tune anything; with 13 detectable cases in study 1, there would also be nothing to train on.

### 1.8 What does not change

The DPO and the share of non-recurring gains stay as in v1, only with the cut-off by fraction of the year (the DPO is already the top decile). The M-score keeps Beneish's coefficients; the cut-off (1.3) and DEPI (1.2) change. A company-year is in alert if at least one signal is at the top, as in v1.

## 2. Development rule

- **Fiscal years up to 2023 only.** The product seal stays at 2023 and 2024-12-31: v2's code is written and measured with `ULTIMO_EXERCICIO_LIBERADO = 2023`. No data from 2024 onward are read before v2's seal session.
- **Choices only by label-free criteria:** coverage (share of company-years where the signal can be computed), alert rate (of each signal and of the union), stability (change in the rate across years and persistence of the alert at the same company) and correctness tests (a hand-computed example for each change; with all changes switched off, v2 reproduces v1 in the invariant's 9,474 company-years).
- **Study 1's ground truth is not used** to choose or tune anything. v2's development code does not read `data/gabarito_casos.csv` or import study 1's metrics; a test checks it.
- **v2's detections on study 1 cases** appear only after the freeze, as an in-sample description, labeled "inside the development sample, not a test". No detection, case or alert by company of the ground truth is computed or shown before that; the descriptions are only aggregates by year and group.
- **The choices go into v2's pre-registration**, before any code: the closed list of changes, the label-free rule that decides each one (for example, "it enters if coverage exceeds X%") and the ranking order. Between the pre-registration and the freeze, only implementation and tests, with no free choice.
- **Label-free descriptions, before the pre-registration (by 2026-12-10),** with fiscal years up to 2023 only: DEPI coverage from the DVA; coverage of the 3.06.02 sub-accounts, in the open data and in the ENET versions; the distribution of the number of figures per company-year in BPA, BPP, DRE and DFC; the rates of options (i) and (ii) for the fraction (1.3); and, with metadata only, the distribution of the filing dates of the 2023 DFP (received in 2024), to estimate how many 2025 company-years would be prospective with the seal on 2027-01-31. Result in [`docs/en/engine-v2-descriptions.md`](engine-v2-descriptions.md), generated from [`docs/motor_v2_descricoes.json`](../motor_v2_descricoes.json).

## 3. Inputs

v2's list runs only on what is already on the `estudo-2-dados` branch and on the versioned CDI, the same files as v1's list, checked against the SHA-256 in the study manifest ([`data/estudo_2_manifesto.csv`](../../data/estudo_2_manifesto.csv)). No file is downloaded.

| Input | What it brings |
| --- | --- |
| 2024 and 2025 DFP zips | BPA, BPP, DRE, DRA, DFC, DMPL and DVA, consolidated and individual, plus the index and the auditor's report |
| 2024 and 2025 FCA zips and the registry | registration data, with the sector |
| 26 ENET documents | only consolidated BPA, BPP, DRE and DFC, for the company-years whose open-data version is later than the cut-off |
| `data/cdi_sgs4389.csv` | the CDI from SGS series 4389, up to 2025-12-31 |

| Change | Needs another input? | Status |
| --- | --- | --- |
| Implied interest, sub-accounts and cut-off by fraction | no | candidate |
| Implied interest from the notes | yes (notes) | out |
| DEPI from the DVA | no (the DVA is in the zips); in ENET company-years, it stays as in v1 | candidate |
| Label-free cut-offs | no | candidate |
| Adjusted Benford deviation | no (only BPA, BPP, DRE and DFC) | candidate |
| Discretionary accruals | no (DFP and registry or FCA) | out by recommendation (1.5) |
| F-score | yes (t-2 balances, from the t-1 DFP) | out |
| ITR | yes | out |
| Supervised learning | yes (labels) | out |

In development, the inputs are study 1's (the 2010 to 2023 open data, checked against the raw-data manifest, and the same CDI).

## 4. Draft text of the study 2 amendment

**Current text:** the amendment 5 draft that goes to registration is in [`docs/en/study-2-amendment-5-draft.md`](study-2-amendment-5-draft.md), next to the [engine v2 pre-registration draft](engine-v2-preregistration.md). The text below stays as the record of this stage of the plan.

Draft with Roberto's decisions; it is not registered in this round. It will be amendment 5: amendment 4 was reserved for the ENET contingency and was neither used nor registered, and the text of amendment 5 says so.

> **Amendment 5 · (date) · engine v2 arm in the secondary evaluation (before any 2024 or 2025 value computed by v2)**
>
> Amendment 4 was reserved for the ENET contingency (the 2026-11-07 tables that could not be downloaded again) and was neither used nor registered: the 26 tables were downloaded again, all identical.
>
> 1. **New arm.** Engine v2, frozen with its own SHA-256 registry (without changing `docs/estudo_2_codigo_congelado.json`), computes the list for fiscal years 2024 and 2025 on the same input files as v1's list (the `estudo-2-dados` branch, checked against the manifest's SHA-256, and `data/cdi_sgs4389.csv`). No file is downloaded. Target: frozen by 2027-01-25 and list sealed by 2027-01-31. Fallback, if the target is not met: frozen by 2027-03-31 and list sealed by 2027-04-15, with the label "not prospective". Without the fallback met, the arm does not exist, with no further extension.
> 2. **What does not change.** Everything this pre-registration says about v1: the sealed list, the registry, the outcomes, the metrics, the seed, the criteria, the dates and the predictions in section 7.3. The report shows v1 first, exactly as pre-registered, and then the v2 arm.
> 3. **The arm's metrics.** Those of section 7.2, with the same seed (20270531) and the same 10,000 resamples by company, through the frozen functions in `chiocca/v2/estudo2/secundaria.py`, without changing any line. The paired comparison uses the company-years evaluated by v1: since the draw depends only on the seed and on the set of companies, the resamples are the same as v1's. The company-years that only v2 can evaluate (for example, through the Benford deviation) are reported separately, as description only. Comparisons: v2's RD, with the same "positive association" criterion; the difference between v2 and the naive rule, paired; the difference between v2 and v1, paired: "v2 separates better than v1" only if the lower bound of the one-sided 95% interval is above zero; otherwise, no winner declared. The ranking metrics of section 7.2 use v2's order defined in its pre-registration. v2's predictions are written in its pre-registration, before the freeze.
> 4. **Opening the seal only for v2's script.** A constant of its own in the study block of `chiocca/v2/lacre.py` (the block stays outside the hash of v1's registry), read only by v2's script. `ULTIMO_EXERCICIO_LIBERADO` stays at 2023, and the product's maximum date stays at 2024-12-31. The test that restricts the study constants starts accepting v2's script, and only it.
> 5. **Seal and timestamp.** As in section 8: the same file format, two runs with the same SHA-256, the SHA-256 in a commit pushed to GitHub, the OpenTimestamps stamp (and `ots upgrade` after confirmation), the file for Roberto without encryption and the copy deleted from the environment in the same session. At the evaluation, the byte-for-byte recomputation is the proof.
> 6. **Roberto without opening the list.** As in section 5: Roberto does not open v2's file or run its code before freezing part 2 of the ground truth, because the v2 arm also has the descriptive primary outcome (item 7). At the secondary evaluation, v2's list is recomputed by the script, and only the aggregate measures of section 7.2 come out; the agent does not describe any v2 alert by company.
> 7. **Part 2 cases public before v2's seal.** For the v2 arm, part 2 is split by the date of the commit with the SHA-256 of v2's list: part 2a, with the cases whose qualifying document (amendment 1, item 1) becomes public between the freeze of part 1 (2026-11-19) and that commit, and part 2b, with those public after it and up to 2029-12-31. In the primary outcome (descriptive), v2's detections are reported separately for parts 2a and 2b; the comparison with v1 uses only 2b, and 2a carries the label "public before v2's seal". For v1, nothing changes: part 2 stays whole.
> 8. **Prospective label by company-year.** A 2025 company-year counts as prospective for v2 if the first filing of its 2026 DFP (the smallest DT_RECEB in the CVM index) is later than the commit with the SHA-256 of v2's list. The 2024 ones are not prospective in either arm: the 2024 restatements (in the 2025 DFP, cut-off 2026-04-30) were public before this plan. The v2 arm is reported in total and in the prospective subset; if the fallback applies, the whole arm also carries the label "not prospective".

## 5. Calendar

| Step | Deadline | If it slips |
| --- | --- | --- |
| This draft and Roberto's decisions | 2026-11-22 | — |
| Label-free descriptions, with fiscal years up to 2023 only (section 2) | 2026-12-10 | A change whose description is not ready by v2's pre-registration does not enter. |
| Engine v2 pre-registration (closed list of changes, 1.1 (a) coverage criterion, fraction option, label-free rules, ranking order, predictions) and amendment 5 to study 2, registered | 2026-12-20 | The target and fallback dates do not change. Without the pre-registration and the amendment registered before the seal session, v2 does not enter. |
| Target: v2 frozen (code, SHA-256 registry, hand-computed example, v1 invariant with the changes switched off) | 2027-01-25 | The fallback applies. |
| Target: seal session (opening only for v2's script, check of the inputs' SHA-256, computation twice, SHA-256 in a commit, timestamp, file for Roberto, copy deleted) | 2027-01-31 | The fallback applies. |
| Fallback: v2 frozen | 2027-03-31 | It does not enter, with no further extension. |
| Fallback: seal session, with the label "not prospective" | from 2027-04-01 to 2027-04-15 | It does not enter, with no further extension. If the OpenTimestamps calendars do not respond, Roberto stamps through the website, as in section 8 of the pre-registration; the commit with the SHA-256 counts as the seal. |
| Cut-off of the 2026 DFP | 2027-04-30 | pre-registration date, does not change |
| `ots upgrade` of the v2 list's stamp | after confirmation on Bitcoin | no effect on the study |
| Single secondary evaluation, both arms in the same session (v1 first, as pre-registered) | from 2027-05-31 | "From": the date can pass with no effect on either arm. |

## 6. Risks and next step

- **Prospective only in part.** Even with the target, the 2024 company-years are not prospective, and the 2025 ones count as prospective only by the filing date of the 2026 DFP (section "Goal"). That is why the choices are closed in v2's pre-registration (2026-12-20), and the agent reads no data from 2024 onward during development. The description of the 2023 DFP filing dates estimates the size of the prospective subset.
- **Little time.** For the target, from 2026-12-20 to 2027-01-25 there are about five weeks to implement three changes and the tests; for the fallback, about fourteen weeks. If any change is not ready, it is dropped and v2 freezes without it; v2 does not wait.
- **Next step, after this study: a prospective test of v2's own** (Roberto's decision, 2026-11-22): a list for fiscal years 2026 (the 2026 DFP, after the 2027-04-30 cut-off), sealed before any of its restatements is public, with the restatement in the 2027 DFP (cut-off 2028-04-30) as the outcome, with its own pre-registration later. For now, it stays only in this plan.

## Roberto's decisions (2026-11-22)

| Decision | What was decided |
| --- | --- |
| 1. Attempt v2 in study 2 | yes |
| 2. Calendar | prospective target (frozen by 2027-01-25, seal by 2027-01-31) and fallback (2027-03-31 and 2027-04-15, with the label "not prospective"), with no further extension; prospective label by 2025 company-year, by the DT_RECEB of the 2026 DFP; 2024 not prospective in either arm; descriptions by 2026-12-10; v2 pre-registration and amendment by 2026-12-20 |
| 3. Changes | 1.2, 1.3 and 1.4; 1.1 (b) through 1.3; 1.1 (a) only with enough coverage of the sub-accounts, by the criterion proposed and closed in the pre-registration; 1.5 and 1.6 out |
| 4. Cut-off fraction | describe options (i) and (ii) with fiscal years up to 2023 only; the choice goes into the pre-registration, using only these descriptions; provisional recommendation: (ii) |
| 5. Benford for financial companies | yes, within the group |
| 6. Amendment | amendment 5; the text records that amendment 4 was reserved for the ENET contingency and was neither used nor registered |
| 7. Evaluated set | the paired comparison uses the company-years evaluated by v1; those only v2 evaluates are reported separately, as description only |
| 8. v2's detections on study 1 cases | only after the freeze, as an in-sample description; nothing by company of the ground truth before that |
| 9. Prospective test of v2's own, with fiscal years 2026 | yes, with its own pre-registration later; for now, only in the plan |
