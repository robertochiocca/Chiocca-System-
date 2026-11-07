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
- Machine learning (Isolation Forest, XGBoost) only with a reliable labeled base, out-of-sample validation and comparison against engine v1 and the naive baseline rule.
- Sector-specific or Brazil-recalibrated cut-offs, always with a pre-registration.

## Product, after Phase F

- Docker and deployment with observability.
- Comparison of versions of the notes to the financial statements across fiscal years.
- Monte Carlo and stress scenarios only as a robustness test of the indicators, never as a detector.
