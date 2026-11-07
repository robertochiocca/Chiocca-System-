# Chiocca System v2 plan: phases B to F

Phase A proposal. Each phase ends with code and passing tests, documentation in PT and EN, the commit hash and `git ls-remote`. Then it stops and waits for your written authorization.

The estimates are orders of magnitude for comparing phases (lines of new code, not counting tests, and number of tests), not promises.

## Code organization

- `chiocca/v2/`: the product in Python. It changes no study 1 module; it only calls them.
- `web/`: the Next.js interface (Phase E).
- Each file brought from another project carries at the top the origin project, the path, the commit and "adapted for the Chiocca System", and is listed in [`docs/en/code-origin.md`](code-origin.md).
- New dependencies only when a phase needs them: DuckDB (C), FastAPI and Pydantic (D), Node and Next.js (E), a PDF reader (F).

## Phase B: trust engine

- `validade.py`: ok, undefined and implausible states (Carchuna's class and `variacao_percentual`), with the bridge to engine v1's "not computable".
- `conferencias.py`: CVM data checks, with tolerance and evidence: balance sheet that does not balance (assets against liabilities plus equity), income statement subtotals, cash flow statement that does not reconcile with the change in cash on the balance sheet, and implausible values (for example, negative or zero total assets).
- `linhagem.py`: the "how I got to this number" sheet for each engine v1 signal, down to the DFP line (open data or ENET), with the study 1 transformations (scaling, interest paid, de-duplication, cash flow text patterns).
- `confianca.py`: the five criteria and the categorical level, with no score.
- Aggregate report, PT and EN: how many company-years up to 2023 fail each check. Aggregate numbers only.
- CI on GitHub Actions: ruff, black, mypy and pytest (adapted from DireitoAberto). The repository has no CI yet.
- Size: about 900 lines and 45 tests.

## Phase C: company investigation

- Temporal storage: DuckDB over Parquet with versions, accounts, FCA and registry up to the seal, built from `data/brutos` and `data/cache/enet`.
- `ExercicioNaData` on any reference date and the cross-section on the same date (engine v1 deciles and percentiles).
- Invariant test: on each fiscal year's cut-off date, signals and alerts match those of study 1.
- Context: percentile within the sector and the group, history with the IQR fence (Carchuna's detection).
- Financial risk (Altman Z'') and financial quality (Piotroski F) families, after transcribing the formulas from the primary source into `docs/en/sources.md`. Descriptive context only.
- "What changed", "what was known on the date", alternative explanations and limitations, with a PT and EN text catalog that cites sources.
- JSON and PDF outputs, in both languages.
- End-to-end tests: Americanas on 2022-03-31 and a company with no ground-truth case.
- Size: about 2,200 lines and 60 tests. It is the largest phase; if you prefer, it splits into C1 (temporal storage and engine v1 on the date) and C2 (families, context and outputs), with a stop between them.

## Phase D: API

- FastAPI under `/api/v1`: `saude` (health), company search (name, CVM code, CNPJ or trading code), investigation by company and date, lineage of each number and PDF.
- Pydantic contracts, generated from the same model as Phase C; API tests with the same numbers as the engine.
- Refusal of fiscal years above the seal and of dates outside the range, with the reason; request size limit.
- Size: about 600 lines and 30 tests.

## Phase E: interface

- Next.js (structure and components adapted from DireitoAberto): search, reference-date picker limited by the seal, investigation page, signal timeline, clickable evidence, comparison with sector peers (aggregate, no ranking), PDF export and the "How the engine was tested" page with the study 1 summary.
- Dark mode, mobile, PT and EN; fixed notice on every screen.
- CI with web build and type checking. Deployment (Vercel, Render or other) is your decision in this phase.
- Size: about 2,000 lines of TypeScript and build and API-contract tests.

## Phase F: document intelligence v0

- CVM monitor: DireitoAberto's version registry, with a review queue and reversal, adapted to the DFP, ITR and IPE indexes. Hash and classification of each new item (new DFP, restatement, ITR, material fact notice), without computing signals above the seal. A person decides; nothing changes the data on its own.
- Extractive reader of material fact notices, notes to the financial statements and the DFP `parecer` (auditor's report): related parties, risco sacado (supplier finance) or forfait, auditor change (FCA `auditor`), qualified opinions and guarantees. Each excerpt comes with its page and a literal check.
- Its own adversarial set, with fictitious documents and an answer key, measured as in DireitoAberto.
- LLM optional only, with every quotation going through the same check. Without a key, everything works in extractive mode.
- Size: about 1,800 lines and 50 tests.

## Questions and decisions

1. **Maximum and minimum reference date.** Proposal: maximum 2024-12-31 and minimum 2011-04-30, the first cut-off date with 2010 DFPs.
   - **Roberto's decision, 2026-11-07:** from 2011-04-30 to 2024-12-31. The seal stays by fiscal year: nothing above 2023 is computed, on any date.
2. **Documents filed after the maximum date** (material fact notices, ITRs, announcements). Proposal: the monitor records only metadata and hash, without reading or summarizing. A material fact notice from 2024 or later may reveal cases that study 2 will test.
   - **Roberto's decision, 2026-11-07:** the monitor records only metadata and hash, without reading, summarizing or extracting anything.
3. **DPO jump and implied interest rate in the possible-manipulation family**, as in engine v1. Proposal: yes, because separating them would change the study 1 "in alert" rule.
   - **Roberto's decision, 2026-11-07:** they stay in the manipulation family; the Phase C invariant still holds. Alternative explanations in the finding, with a source when available: for the implied interest rate, expensive debt, exchange differences and lease interest inside finance costs; for DPO, bargaining power with suppliers and a change in purchase mix.
4. **Categorical confidence, with no numeric score.** Proposal: yes.
   - **Accepted by default on 2026-11-07.**
5. **Dependency-free PDF** (DireitoAberto's generator, text and tables only) now, instead of matplotlib. Proposal: yes; charts stay in the interface.
   - **Accepted by default on 2026-11-07.**
6. **Binomial test on study 1** (adapted from Calahonda's Kupiec test). It is a new, non-pre-registered statistic. Proposal: only with your authorization, and labeled as descriptive, computed after the study.
   - **Roberto's decision, 2026-11-07:** authorized, as a "descriptive analysis after the result, not pre-registered", with the exact Poisson binomial distribution and without scipy. The probability that each detectable case is detected by chance is 1 − product of (1 − the group's alert rate in the year) over the years of the affected period, using the rates observed in study 1. Result in [`docs/en/post-study-1-analyses.md`](post-study-1-analyses.md), with no study 1 file changed.
7. **Display parameters:** minimum `n` of 10 companies for the sector percentile and 5 fiscal years for the history. They are not engine rules and create no alert.
   - **Accepted by default on 2026-11-07.**
8. **Organization:** `chiocca/v2/` package and interface in `web/`.
   - **Accepted by default on 2026-11-07.**
9. **Fetching from ENET** versions that are not in storage. Proposal: only through a separate command; the API answers `versao_pendente_enet` and never downloads anything inside a query.
   - **Accepted by default on 2026-11-07.**
10. **Altman Z'' and Piotroski F:** the primary source (article or book) must be accessible to transcribe the formulas. If you have the PDFs, they go into `referencias/` (not in git); otherwise I will look up the published sources and record them in `docs/en/sources.md`.
    - **Roberto's decision, 2026-11-07:** the PDFs of Altman (2000), "Predicting Financial Distress of Companies: Revisiting the Z-Score and ZETA Models", and of Piotroski (2000), Journal of Accounting Research, go into `referencias/`. No coefficient or test comes in before it is checked against them, with the page.

## Phase C split (Roberto's decision, 2026-11-07)

- **C1:** temporal storage, engine v1 on any date and the study 1 invariant. Stop.
- **C2:** context, Altman Z'', Piotroski F, JSON and PDF. Additions:
  - **Auditor's report and auditor:** a factual section in the investigation, with the type of report, an excerpt of the DFP text checked literally, the auditor and auditor changes from the FCA. It is not a signal family and produces no score or alert.
  - **Altman Z'':** the pure Z'' version, for non-manufacturing firms and emerging markets, without the 3.25 constant of the Emerging Market Score (which was built for emerging-market debt and depends on qualitative adjustments and a rating table we will not apply). Coefficients and zones copied from Altman (2000), with the page. X1 = (current assets − current liabilities) ÷ total assets; X2 = (profit reserves + retained earnings or accumulated losses) ÷ total assets, as a Brazilian adaptation (since Law 11,638/2007 retained profit goes to reserves), excluding capital reserves and equity valuation adjustments; X3 = EBIT ÷ total assets; X4 = consolidated book equity including non-controlling interests ÷ (current liabilities + non-current liabilities). Not computable for financial companies. A new catalog entry, financial risk family, phase `contexto_v2`, with engine v1 unchanged. A v2 worked example of its own, with the case of zero retained earnings and positive reserves, and a test that fails if X2 uses retained earnings alone.
  - **Piotroski F:** each test checked against Piotroski (2000), with the page; Brazilian adaptations flagged in the lineage and the catalog. The equity-issuance test uses the cash flow statement issuance line (frozen patterns), flagged as an adaptation; without the line, not computable.
