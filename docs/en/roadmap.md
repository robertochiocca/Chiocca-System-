# Roadmap: ideas outside this stage

Noted for later, with no commitment. Nothing here goes into the v2 product without authorization, and nothing changes study 1.

## Study 2 (with fiscal years 2024 onward, sealed today)

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
- Confidence intervals by paired bootstrap: engine and naive rule compared on the same resamples, resampling by company, because alerts repeat (73.8% of non-financial company-years in alert were also in alert the year before; [analyses](post-study-1-analyses.md), section 2). Adapted from FraudShield's `evaluate.py` (ARMAND-cod-eng/fraud-detection-ensemble, MIT), with an origin header and an entry in [`docs/en/code-origin.md`](code-origin.md); the exact file and commit are checked when adapting (2026-11-09).
- Lead time of the alert as a pre-registered metric: in study 1 it exists only as a descriptive analysis after the result ([analyses](post-study-1-analyses.md), section 5) (2026-11-09).
- A 24-month gap between the calibration period and the test period.
- A pre-registration rule for cases spanning several years, with an automatic test for a missing year of data and for a changed case identifier: this was the error Walker pointed out in 2021 in Bao et al. (2020) and that the 2022 erratum acknowledged.

## Product: context indicators (recorded on 2026-11-08)

Context only, with no alert, and only after they are specified in the plan:

- Accruals ÷ average total assets, with a percentile (Sloan 1996, p. 6).
- SMTH1 = −σ(earnings ÷ TA) ÷ σ(CFO ÷ TA) over 5 years, requiring 5 DFPs public on the reference date (Gonçalves et al. 2024, pp. 10-11).

## Phase F: related-party reader (recorded on 2026-11-08)

- Fields of item 18 of CPC 05 (R1), organized by the categories of item 19.
- Also read the parent-company note, because consolidation eliminates intra-group transactions (Gonçalves et al. 2024, p. 9).
- The phrase "on market terms" is recorded as a fact, without proof (item 23).
- Before starting Phase F: check whether the Reference Form (Formulário de Referência) open data has a structured table of related-party transactions. Only check and report.

## Do not

- Do not copy the JarFraud/FraudDetection CSV into the repository: it is derived from Compustat.
- Do not use the Z' zones for Z'' or the 1979 coefficients as a yardstick.

## Review when Starlette changes (recorded on 2026-11-09)

- The API tests use `TestClient` with httpx, and Starlette warns that this combination is deprecated and suggests `httpx2`. The warning stays as it is; review it when Starlette changes (a new version pinned in the lock or the end of httpx support).

## Product, after Phase F

- Docker and deployment with observability.
- Comparison of versions of the notes to the financial statements across fiscal years.
- Monte Carlo and stress scenarios only as a robustness test of the indicators, never as a detector.
