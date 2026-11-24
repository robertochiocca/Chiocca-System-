# Roadmap: ideas outside this stage

Noted for later, with no commitment. Nothing here goes into the v2 product without authorization, and nothing changes study 1.

## Study 2 (with fiscal years 2024 onward, sealed today)

- **Status (2026-11-22):** engine v1, unchanged, computed the list for the sealed fiscal years, sealed on 2026-11-21. The [engine v2 pre-registration](engine-v2-preregistration.md) (DEPI from the DVA, standardized Benford and the alert by score) and amendment 5 to study 2, which adds v2 as an arm of the secondary evaluation, were registered on 2026-11-22 (commit `313c52db5df2f11b0a4f9d7920e486e688a9f381`; hash noted in commit `29e472b130a61f1358b97694eddbeaba6e9bbb88`; OpenTimestamps stamp in commit `13564a22074aca81a7b96dcdf9c8cda4fe3a9c81`). v2's code starts later, in a separate round. Engine v2 was frozen on 2026-11-23 (commit `320ec04bdd378938a192e5f93636a44febdc6a29`, [SHA-256 registry](../motor_v2_codigo_congelado.json)), after the hand-computed example and the invariant (9,474 of 9,474 company-years equal to v1 with the changes off); the [in-sample description](engine-v2-in-sample.md) carries the label "within the development sample, not a test".
- Run engine v1 unchanged on the sealed fiscal years, as a clean test, before any improvement.
- DEPI without a depreciation line in the cash flow statement: the value-added statement (DVA) has a fixed account "Depreciação, Amortização e Exaustão" (depreciation, amortization and depletion; reconnaissance, part 1.7), which may solve the direct-method cases. It requires a new pre-registration.
- Implied interest rate: separate exchange differences and lease interest from finance costs, using the notes to the financial statements, before comparing with the CDI rate.
- Quarterly data (ITR), for cases like IRB.
- Stock-return test, with Calahonda's `data.py`, `metrics.py` and `ratios.py`.
- The Dechow and others (2011) F-score, already in the catalog as a phase 2 signal.
- Validate the context indicators (Altman Z'' and Piotroski F) in Brazil before any use as an alert.
- Supervised learning only as exploration: 13 detectable cases are not enough to train and validate a model, and no project text claims that machine learning beats the logit. Any model (Isolation Forest, XGBoost) only with a reliable labeled base, out-of-sample validation and comparison against engine v1 and the naive baseline rule.
- Sector-specific or Brazil-recalibrated cut-offs, always with a pre-registration.

Recorded on 2026-11-08, for the new study 2 pre-registration, before opening fiscal years 2024 onward:

- Discretionary accruals by sector and year, with the modified Jones model and the margin model, with at least 10 companies per sector-year (Peasnell, Pope and Young 2000, pp. 11 and 15). Paulo's (2007, p. 168) Quadro 03 serves as a checklist.
- Dechow and Dichev (2002) only with a lag, because the model uses cash flows of t+1.
- Earnings just above zero or the previous year's earnings (Martinez 2001, pp. 72-80).
- Ranking metrics: precision at the top 1%, 5% and 10% and NDCG@k, reimplemented in Python from the definitions in Bao et al. (2020, Table 3, p. 21) and checked against JarFraud/FraudDetection's `evaluate.m`, without copying code (the repository has no license file), with tests that reproduce a small hand-calculated example (correction of 2026-11-09).
- Lift at the top of the list, together with precision at the top and NDCG@k (2026-11-09).
- Confidence intervals by paired bootstrap: engine and naive rule compared on the same resamples, resampling by company, because alerts repeat (73.8% of non-financial company-years in alert were also in alert the year before; [analyses](post-study-1-analyses.md), section 2). Adapted from the `bootstrap` function in FraudShield's `src/fraudshield/training/evaluate.py` (ARMAND-cod-eng/fraud-detection-ensemble, MIT), around line 142 (path given by Roberto on 2026-11-10), with an origin header and an entry in [`docs/en/code-origin.md`](code-origin.md); the exact commit is left for when it is adapted.
- Lead time of the alert as a pre-registered metric: in study 1 it exists only as a descriptive analysis after the result ([analyses](post-study-1-analyses.md), section 5) (2026-11-09).
- A 24-month gap between the calibration period and the test period.
- A pre-registration rule for cases spanning several years, with an automatic test for a missing year of data and for a changed case identifier: this was the error Walker pointed out in 2021 in Bao et al. (2020) and that the 2022 erratum acknowledged.

## US study (outside the product)

- **Status (2026-11-24):** [Phase 0](us-phase-0.md) counted the SEC data and the labels, and the [US study pre-registration](us-preregistration.md) was registered on 2026-11-24 (commit `a527b9eca9ab0f087b04f1c97ed737bc63188456`; hash noted in commit `14b78c5897083ee47cc962704230b55db47d7e55`; OpenTimestamps stamp in commit `7c45d5344acc60f871d1f59747968938a386923b`), before any US signal. Main outcome: the 8-K with Item 4.02, per episode; the 2009 to 2014 AAERs as description only. Then, in the registered order and on the same day, the hand-computed example, the study code, tested only on synthetic data and on the example, and the freeze, before the target of 2027-01-15 (commit `dd9b662e1f2d52355722b6fe102d7e5515782115`; SHA-256 registry in [`docs/eua_codigo_congelado.json`](../eua_codigo_congelado.json); [procedure notes](us-procedure-notes.md), in which no value from the SEC files was read). No US signal was computed. Next steps: the single computation, only with Roberto's authorization, after the PR and the freeze release (target 2027-01-31), and the report (target 2027-02-28). Nothing from the US goes into the README or the product before the single computation and the "US in the product" phase, in the [plan](plan-v2.md).

## Product: context indicators (recorded on 2026-11-08)

Context only, with no alert, and only after they are specified in the plan:

- Accruals ÷ average total assets, with a percentile (Sloan 1996, p. 6).
- SMTH1 = −σ(earnings ÷ TA) ÷ σ(CFO ÷ TA) over 5 years, requiring 5 DFPs public on the reference date (Gonçalves et al. 2024, pp. 10-11).

## Phase F: related-party reader (recorded on 2026-11-08)

- Fields of item 18 of CPC 05 (R1), organized by the categories of item 19.
- Also read the parent-company note, because consolidation eliminates intra-group transactions (Gonçalves et al. 2024, p. 9).
- The phrase "on market terms" is recorded as a fact, without proof (item 23).
- Before starting Phase F: check whether the Reference Form (Formulário de Referência) open data has a structured table of related-party transactions. Only check and report.
  - Checked on 2026-11-11: it does (`fre_cia_aberta_transacao_parte_relacionada_<ano>.csv`), only with each company's last version in the year. Used in Phase F1.

## Outside Phase F (recorded on 2026-11-11)

- LLM: outside Phase F, by Roberto's decision. The reader is extractive only. If it comes back, every citation goes through the same literal check.
- Earlier versions of the Reference Form (only on ENET; the open data has the last one).
- Text recognition in PDFs without a text layer and ITR explanatory notes.

## Do not

- Do not copy the JarFraud/FraudDetection CSV into the repository: it is derived from Compustat.
- Do not use the Z' zones for Z'' or the 1979 coefficients as a yardstick.

## Review when Starlette changes (recorded on 2026-11-09)

- The API tests use `TestClient` with httpx, and Starlette warns that this combination is deprecated and suggests `httpx2`. The warning stays as it is; review it when Starlette changes (a new version pinned in the lock or the end of httpx support).

## Product, after Phase F

- Docker and deployment with observability.
- Comparison of versions of the notes to the financial statements across fiscal years.
- Monte Carlo and stress scenarios only as a robustness test of the indicators, never as a detector.
