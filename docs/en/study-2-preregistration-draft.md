# Study 2 pre-registration (draft for review)

> **Draft of 2026-11-15, written by the agent with Roberto's decisions of the same day, for review.** It is not registered yet: it has no hash, the seal has not changed and nothing from fiscal years 2024 and 2025 has been downloaded for the study. It applies only after Roberto approves the text and it enters a commit, with its hash recorded in the next commit, as in study 1 and the reader.
>
> Why this exists: engine v1 was built and measured on fiscal years 2010 to 2023. Fiscal years 2024 and 2025 were sealed from the start (`chiocca/v2/lacre.py`) precisely for a clean test, on data nobody has looked at. Deciding beforehand how the test is done is what makes the result trustworthy.

Basis: the draft plan ([`docs/en/study-2-plan.md`](study-2-plan.md)), with the numbers in [`docs/estudo_2_numeros.json`](../estudo_2_numeros.json), and study 1's pre-registration ([`docs/pre-registro.md`](../pre-registro.md)), whose computation rules apply here unchanged.

## 1. Questions

1. **Primary.** With public data available at the time, did engine v1, without any change, alert for the accounting irregularities of fiscal years 2024 and 2025 before they came to light, by 2029-12-31?
2. **Secondary.** Did the company-years in alert in 2024 and 2025 have more material restatements in the following fiscal year than those not in alert? And study 1's naive rule, side by side?

## 2. Sample

- **Companies:** all listed companies with a 2024 or 2025 DFP at the CVM, financial and non-financial, including those whose registration is later cancelled, with study 1's two groups (non-financial: M-score, DPO and implied interest; financial: weight of non-recurring gains).
- **Fiscal years:** 2024 and 2025. From the CVM index metadata, 683 companies filed the 2024 DFP by the cut-off (2025-04-30) and 649 the 2025 one by the cut-off (2026-04-30). In study 1, about 600 non-financial companies were evaluated per year.
- **Exclusions:** study 1's, unchanged (non-financial companies with no revenue in the year; company-years with no version public by the cut-off; version at the time individual only when the open-data version is after the cut-off, amendment 8).
- **Secondary outcome:** non-financial companies only. For financial companies, the income statement uses another chart of accounts, and account 3.11 may not be net income; they enter only the descriptive part.

## 3. Rule: engine v1 unchanged

- **As it was at the time:** each company-year uses only the version of the DFP public at the cut-off, 2025-04-30 for 2024 and 2026-04-30 for 2025, as in study 1. When the open-data version is after the cut-off, the version at the time comes from the ENET HTML route, consolidated only (study 1 amendments 5 and 8).
- **Signals and alerts:** those in section 4 of study 1's pre-registration, with the computation choices of section 4.1 and the data rules of amendments 1 to 11 (M > −1.78; DPO jump in the top decile of the year; implied interest above the year's average CDI plus 10 p.p.; weight of non-recurring gains in the top decile of the year, for financial companies). The deciles are computed within each fiscal year, as in study 1. The CDI comes from the Central Bank's SGS 4389 series (`data/cdi_sgs4389.csv`, which already runs to 2025-12-31).
- **Code:** engine v1 as it is at the registration commit, the same code that reproduces study 1 in the invariant (9,474 of 9,474 company-years). The engine files and the study script enter a SHA-256 record, with a test that flags any change. No line of the engine changes in this study.

### 3.1 Data and download

- **Already in the environment:** the 2024 to 2026 DFP zips were downloaded on 2026-11-07, with the rest of study 1's open data, and are in `data/brutos/cvm/` (outside git), with their SHA-256 in `data/manifesto_brutos.csv`. None of their values was read: the warehouse only holds fiscal years 2010 to 2023, and the seal refuses any fiscal year above 2023 (`tests/test_v2_lacre.py`). The metadata of the 2024 and 2025 DFP index (who filed and when) were read by the monitor and by the draft plan, with no values.
- **In the opening session (section 9):** the 2024 and 2025 DFP zips are downloaded again, in the CVM version of the day, with size and SHA-256 in the manifest, because the environment is temporary and the CVM files change with refilings. The version-at-the-time rule gives the same result with the 2026-11-07 files or with those of the day: whatever changes between them comes from ENET.
- **ENET, volume and pace:** only the documents of the company-years whose open-data version is after the cut-off and that have consolidated statements. From the metadata, 139 companies have more than one version of the 2024 DFP and 76 of the 2025 one: that is the ceiling, because part of the refilings happened before the cut-off. In study 1, there were 390 documents in 14 fiscal years, about 28 per fiscal year. I expect between 50 and 250 documents. The pace is study 1's (`chiocca/enet.py`): one request at a time; per document, the document page (up to 10 attempts, with 2 seconds between them) and the 4 tables (BPA, BPP, DRE and DFC), with 1 second between them; up to 3 retries per document, waiting 5, 10 and 15 seconds; a generic client identifier. That is about 6 to 10 seconds per document, or 5 to 40 minutes in all, and a few MB in the cache (`data/cache/enet/`, outside git).
- **Data archive:** the two zips, the ENET tables and the manifest go to an orphan branch `estudo-2-dados` in this repository, pushed without force push, like `gh-pages` (it asks Roberto's authorization for that branch when this text is approved). The SHA-256 of each file stays in the study manifest, versioned on the development branch. At the secondary evaluation, the 2026 DFP zip joins the same branch.

## 4. Outcomes

### 4.1 Primary: an accounting irregularity that comes to light

- A ground-truth case (section 5) whose affected period includes 2024 or 2025 and whose public date falls by 2029-12-31.
- **Hit:** as in study 1, the company was in alert in at least one fiscal year of the affected period (2024 or 2025), using only the version public at the cut-off and before the public date. If the public date falls before 2026-04-30, only the 2024 DFP can count.
- **Lead time:** months between the filing of the first DFP in alert in the affected period and the public date, as in section 5 of study 1's analyses, now pre-registered.

### 4.2 Secondary: material restatement

- **Material restatement (narrow definition, the one tested):** in DFP t+1, in the version public at t+1's cut-off (2026-04-30 for t = 2024; 2027-04-30 for t = 2025), the comparative of t has a highlighted difference in equity (BPP 2.03) or in net income (DRE 3.11) relative to the version of t used by the engine. "Highlighted" is the product's materiality rule (`chiocca/v2/comparativo.py`): a difference above the tolerance and, in absolute value, above 1% of total assets of the version of t used.
- **Broad rule (descriptive only):** a highlighted difference in any line of the product's group (a) (total assets, current liabilities, non-current liabilities, equity, revenue, net income and operating cash flow).
- **Company-years evaluated:** non-financial companies with the version of t used by the engine and a version of t+1 at t+1's cut-off, of the same type (consolidated or individual).
- **Expected rate:** from 2013 to 2022, 4.7% of company-years had a restatement by the narrow definition and 14.2% by the broad one.

### 4.3 The 2024 comparative inside the 2025 DFP (decision 4)

To compute the 2025 alerts, the engine reads the 2025 DFP, which carries the 2024 comparative: that is the data of the 2024 secondary outcome. Rules:
- the study script reads those values only as engine input (the 2025 ratios use the previous year);
- the script stores no comparison between versions, including between the 2024 version used and the 2024 comparative in the 2025 DFP;
- nobody computes or looks at the 2024 restatement before the list is sealed (section 8);
- the comparison is made only at the secondary evaluation, by its own script, frozen with the rest.

## 5. Ground truth and blinding

- **Who writes it:** Roberto, with Claude (claude.ai), outside this environment, without the list and without running the code, like the reader's held-out cases. The agent in this environment neither chooses nor writes cases.
- **Sources:** (1) CVM sanctioning proceedings about the financial statements; (2) material fact notices that admit an accounting error or fraud; (3) CVM restatement or republication orders; (4) for financial companies, the Central Bank. The content of IPE filings after 2024-12-31 is still not read in this environment: Roberto reads it, outside it.
- **Fields and criterion:** study 1's (`data/gabarito_casos.csv`), plus the part (1 or 2) and the type `refazimento_cvm`. `data_publica` is the first documented public date (opening of the proceeding, material fact notice, restatement order or first news item with a source); the affected period comes from the fiscal years named in the document; without a document giving the years, the case is not detectable. Cases without a misstatement in the financial statements (only insider trading or governance) stay out. Each case with two sources, as in study 1's amendment 9.
- **Part 1:** the cases already public on the seal date. Written after this pre-registration is registered and frozen (SHA-256 in a commit) before the seal is opened. It can be described right after the seal, separately from the others.
- **Part 2:** the cases that come to light by 2029-12-31. Written after that date and frozen before the list is opened for the primary outcome.
- **Limit of the blinding:** the code and the data are public, and anyone can recompute the list; the list file stays with Roberto, unencrypted. The blinding is procedural: Roberto commits not to open the file or run the code before freezing each part, and the ground-truth criteria are document-based. Describing part 1 right after the seal reveals the alert of that part's companies; if one of them has a new case in part 2, that is recorded in the report.

## 6. Dates

| Step | When |
| --- | --- |
| Registration of this pre-registration (commit and hash) | after Roberto's review |
| Part 1 of the ground truth frozen | after the registration, before the opening |
| Opening the seal, computing and sealing the list (sections 8 and 9) | in a single session, after part 1 |
| Description of part 1 | right after the seal |
| Secondary evaluation, single | in a session from 2027-05-31, once the 2026 DFPs are filed by the 2027-04-30 cut-off |
| Part 2 of the ground truth frozen | from 2030-01-01 |
| Primary evaluation | after part 2, with the cases public by 2029-12-31 |

Nothing is looked at before those dates: no preview of the primary outcome and no computation of the secondary one before the single evaluation.

## 7. Tests, metrics and what counts as a result

### 7.1 Primary (descriptive)

- For each detectable case: hit or not, which signals fired, in which fiscal year, and the lead time.
- Totals: hits out of detectable cases, for parts 1 and 2 together and separately, and the alert rate of each fiscal year.
- The chance of each total by luck (each case hit at the alert rate of its group in the fiscal year) is reported only as description. With the expected number of cases (about 1.6 by 2029-12-31 at study 1's medium rate), no test against chance is a result criterion. The ranking metrics stay descriptive only.

### 7.2 Secondary (the test)

- **Main measure:** the risk difference RD = P(narrow restatement | in alert) − P(narrow restatement | not in alert), in the evaluated non-financial company-years of both fiscal years together; also the rate ratio.
- **Each company's two company-years:** a bootstrap by company. Companies are drawn with replacement, each with its 2024 and 2025 company-years; 10,000 resamples, with seed 20270531. The interval is the one-sided 95% percentile.
- **Result:** "positive association" if the lower bound of the one-sided 95% interval of the RD is above zero; otherwise, "no evidence of association". With 1,200 company-years and a rate of 4.7%, the approximate power is 0.45 for a rate ratio of 1.5 and 0.82 for 2.0 (assuming independent company-years; with the bootstrap by company, it is lower).
- **Naive rule side by side:** the most leveraged decile (total liabilities ÷ total assets) of each fiscal year, as in study 1, with the same RD and the same bootstrap. The comparison is the difference between the engine's RD and the naive rule's, with a paired bootstrap (the same resamples): "the engine separates better than the naive rule" only if the lower bound of the one-sided 95% interval is above zero; otherwise, no winner declared.
- **Ranking metrics (secondary to this outcome):** precision at the top 1%, 5% and 10%, lift at the top (top precision ÷ overall rate) and NDCG@k (k = 1%, 5% and 10% of the company-years), with relevance 1 for a narrow restatement, reimplemented in Python from the definitions of Bao et al. (2020, Table 3) and checked against a hand-computed example, as in the roadmap. Ranking order: number of signals fired, then the M-score (highest first; without an M-score, after those that have one), then the CVM code. Intervals by the same bootstrap by company; the engine and the naive rule (ordered by leverage) in the same draws.
- **Descriptive:** the product's broad rule, the financial companies and each fiscal year separately.

### 7.3 Predictions written before the data

- An alert rate for non-financial companies between 40% and 60% in each fiscal year, driven by implied interest, as in study 1 (a rate of 49.9%, with 59.8% of the company-years in alert coming from implied interest).
- For the secondary outcome, I expect a positive but small RD: implied interest fires because of exchange-rate variation and leases, which have no direct relation to restatements.

### 7.4 If the result is bad

The study is published all the same, with the result it gave, on the dates in section 6.

## 8. Custody of the sealed list

- **The file:** a CSV in a fixed format (UTF-8, LF line breaks, sorted by CVM code and fiscal year, numbers with fixed decimals, no generation date in the content), with all evaluated company-years, in alert or not, the signals and the value of each signal; in the header, the code commit and the SHA-256 of each input file.
- **The proof:** the file's SHA-256 in a commit pushed to GitHub, and the recomputation at the evaluation: the engine is deterministic, and the frozen script, with the files of the `estudo-2-dados` branch and the lock versions (pandas 3.0.5, numpy 2.5.3), must produce the same file, byte for byte. A test in the opening session runs the script twice and checks that the SHA-256 is the same.
- **Timestamp:** the environment reaches the OpenTimestamps calendars (checked on 2026-11-15). In the opening session, the agent stamps the hash file (the SHA-256 of the list and of the manifest) with `opentimestamps-client` and puts the `.ots` in the repository; in a later session, after the Bitcoin confirmation, the `.ots` is upgraded (`ots upgrade`). If the calendars do not answer that day, Roberto stamps the hash file on the opentimestamps.org site and returns the `.ots`.
- **Where the list file lives:** it comes to Roberto, unencrypted, through the session's file delivery; he keeps it in two private places (a private repository and Drive). The copy is deleted from the environment in the same session. No age or GPG key: the recomputation is the main proof.

## 9. Opening the seal

**Before, in this order:**
1. This pre-registration registered: a commit, with its hash recorded in the next commit.
2. Part 1 of the ground truth frozen (SHA-256 in a commit).
3. The study script (computing the list and, separately, the secondary evaluation) and the SHA-256 record of the engine files and of the script, with the test that flags a change; study 1's invariant passing.

**The commit that opens the seal, only for the study:** a constant of its own in `chiocca/v2/lacre.py` (for example, `ESTUDO_2_EXERCICIOS = (2024, 2025)` and the cut-off of each), read only by the study script. `ULTIMO_EXERCICIO_LIBERADO` stays 2023, and the product's maximum date stays 2024-12-31: the interface, the API, the demo and the monitor (metadata only after 2024-12-31) do not change. A test checks that only the study script uses the constant and reads 2024 and 2025. At the secondary evaluation, a second opening, also only for the study, lets its script read from the 2026 DFP only the 2025 comparative.

**In the same session, after the commit:** download the data (section 3.1), compute the list, check the recomputation, record the SHA-256 in a commit, stamp it, send the file to Roberto, delete the copy and archive the data on the `estudo-2-dados` branch. Nothing else from 2024 and 2025 is computed until the dates in section 6.

## 10. What stays out

- Any change to engine v1: the improvements (implied interest, DEPI from the DVA, discretionary accruals, F-score, recalibrated cut-offs, ITR, supervised learning) come later, in the order of the draft plan, each with its own pre-registration and evaluated on data that were not used to develop it.
- Using fiscal years 2024 and 2025 to develop or tune anything.
- A public list of companies in alert, or any order by alert, percentile or score. Only what section 7 describes is published: ground-truth cases and aggregate counts.
- Opening the product to 2024 and 2025 before the primary evaluation.
- Reading in this environment the content of IPE documents filed after 2024-12-31.
- Tests against chance on the primary outcome as a result criterion.

## Points for Roberto's review

1. The secondary outcome for non-financial companies only (section 2), because of account 3.11 at financial companies.
2. The ranking order for the ranking metrics (section 7.2): number of signals, then the M-score, then the CVM code.
3. The bootstrap seed, 20270531, and the 10,000 resamples.
4. The date of the secondary evaluation, from 2027-05-31.
5. The orphan branch `estudo-2-dados` to archive the data, pushed without force push.
6. The predictions in section 7.3.

---

Signed by: (to be filled at registration) · Date: (to be filled)
