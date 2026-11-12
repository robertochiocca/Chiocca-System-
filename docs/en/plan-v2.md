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
- Financial risk (Altman Z'') and financial quality (Piotroski F) families, with the formulas and pages in `docs/en/contracts.md` (section 3) and the works in `docs/en/references.md`. Descriptive context only.
- "What changed", "what was known on the date", alternative explanations and limitations, with a PT and EN text catalog that cites sources.
- JSON and PDF outputs, in both languages.
- End-to-end tests: Americanas on 2022-03-31 and a company with no ground-truth case.
- Size: about 2,200 lines and 60 tests. It is the largest phase; if you prefer, it splits into C1 (temporal storage and engine v1 on the date) and C2 (families, context and outputs), with a stop between them.

## Phase D: API

- FastAPI under `/api/v1`: `saude` (health), company search (name, CVM code, CNPJ or trading code), investigation by company and date, lineage of each number and PDF.
- Pydantic contracts, generated from the same model as Phase C; API tests with the same numbers as the engine.
- Refusal of fiscal years above the seal and of dates outside the range, with the reason; request size limit.
- Size: about 600 lines and 30 tests.
- **Roberto's decision, 2026-11-09:** Phase D authorized. Endpoints mirror the contract JSON, with the same validations (date from 2011-04-30 to 2024-12-31; fiscal year up to 2023). No endpoint lists companies ranked by alert, percentile or score; search is only by name, CVM code or CNPJ (the trading code is not searchable and stays only as company information). Contract tests without network.
- **Completed on 2026-11-09:** `chiocca/v2/api.py`, `chiocca/v2/modelos.py` and `chiocca/v2/busca.py`, with the `codigos_negociacao` field (the store's `valores_mobiliarios` table); routes and rules in [`docs/en/contracts.md`](contracts.md), section 6; tests in `tests/test_v2_api.py`.

## Phase E: interface

- Next.js (structure and components adapted from DireitoAberto): search, reference-date picker limited by the seal, investigation page, signal timeline, clickable evidence, comparison with sector peers (aggregate, no ranking), PDF export and the "How the engine was tested" page with the study 1 summary.
- Dark mode, mobile, PT and EN; fixed notice on every screen.
- CI with web build and type checking. Deployment (Vercel, Render or other) is your decision in this phase.
- Size: about 2,000 lines of TypeScript and build and API-contract tests.
- **Roberto's decision, 2026-11-09:** Phase E authorized, with the API rules, aggregate-only sector comparison, dates up to 2024-12-31 and fiscal years up to 2023, "Today's information" kept separate, fixed notice, PT and EN, dark mode and mobile, a "How the engine was tested" page from the same JSON as the summary, CI with build, types, contract tests and npm audit, and no deploy: only a demo mode turned on by configuration.
- **Completed on 2026-11-09:** `web/` (Next.js 16.4.3, React 19.2.9, TypeScript 5.9.3; Next 15 shipped a postcss with a high vulnerability in `npm audit`), rules in [`docs/en/contracts.md`](contracts.md), section 7; demo mode in the API (`CHIOCCA_MODO_DEMONSTRACAO`). The deploy awaits Roberto's choice.
- **Response to Phase E, 2026-11-10:** interface adjustments (labels instead of codes, mobile menu, highlighted-difference notice, Tukey range, paths as links), with a screen test; static demo generated by a script (`chiocca/v2/demonstracao_estatica.py`), Roberto's preferred deploy; Roberto publishes it after seeing the report.
- **Second round, 2026-11-10:** labels for the Piotroski F signals, the minus sign in the v2 display (screen and PDF) and publication on GitHub Pages through the generated `gh-pages` branch ([`docs/en/contracts.md`](contracts.md), section 7).
- **Phase E2, experience and explanation (authorized on 2026-11-10):** header, home page, company, investigation with a summary, index and explained cards, "How the engine was tested" as the explanation page, mobile, accessibility with axe and screenshots for review ([`docs/en/contracts.md`](contracts.md), section 7).

## Phase F: document intelligence v0

- CVM monitor: DireitoAberto's version registry, with a review queue and reversal, adapted to the DFP, ITR and IPE indexes. Hash and classification of each new item (new DFP, restatement, ITR, material fact notice), without computing signals above the seal. A person decides; nothing changes the data on its own.
- Extractive reader of material fact notices, notes to the financial statements and the DFP `parecer` (auditor's report): related parties, risco sacado (supplier finance) or forfait, auditor change (FCA `auditor`), qualified opinions and guarantees. Each excerpt comes with its page and a literal check.
- Its own adversarial set, with fictitious documents and an answer key, measured as in DireitoAberto.
- LLM optional only, with every quotation going through the same check. Without a key, everything works in extractive mode.
- Size: about 1,800 lines and 50 tests.
- **Plan approved by Roberto on 2026-11-11, in two parts, with a stop between them:**
  - *F1:* extractive reader of the DFP explanatory notes (related parties under items 18 and 19 of CPC 05, also reading the parent-company columns; reverse factoring or forfaiting), of the auditor's report of the version used and of the Reference Form related-party table; the core of the adversarial set; pypdf pinned in the lock. Pre-registration of the measurement in [`docs/en/reader-preregistration.md`](reader-preregistration.md), before any code; held-out cases written by Roberto with Claude (claude.ai), outside this environment and without access to the reader's detection code (for the format and conventions, the pre-registration, `avaliacao.py`, `pdf_simples.py` and the development cases were read), measured once with the frozen reader (limit: the reader and the cases were written by instances of the same model, in separate environments; the separation is of information, not of author); below the target, the section stays off. Contract in [`docs/en/contracts.md`](contracts.md), section 8.
  - *F2:* CVM monitor (only metadata and hash for documents after 2024-12-31), the list of material facts and notices filed by the date (filing date, category, subject and link, without reading the content) in the "What was known on the date" section and the expanded adversarial set, measured again.
  - *Reader frozen on 2026-11-11* at commit `c99c9538c90f9574f372dddee03bf17757929220` (`leitor-f1-1`), with the SHA-256 of each file in [`docs/leitor_congelado.json`](../leitor_congelado.json) and a test that fails if any changes. Awaiting the held-out cases.
  - *Measurement on the held-out cases on 2026-11-11:* once, on the frozen reader; precision of 0.962, coverage of 0.962, literal check on 132 of 132 excerpts and no leaked name. The four targets were met and the section was switched on ([`docs/en/contracts.md`](contracts.md), section 8).
  - *Display, 2026-11-11, after the measurement (without changing the reader or the JSON excerpts):* title "Document excerpts (copied; no alert)", with the subsections Explanatory notes, Auditor's report and Reference Form; labels together on the same excerpt; omitted excerpts of the same page on a single line; "How the reader was tested" and the limits in the section; the reader in the "Engine" line; no Δ in the PDF.
  - *Next reader version (`leitor-f1-2`), only recorded, no code:* tell "the Company is (jointly) controlled by" apart from mentions of subsidiaries and joint ventures; do not count "na qualidade de controladora" ("as parent company") when it refers to the Company itself; recognize amount sentences ("somou R$ … no exercício", "totalled R$ … in the year") and term sentences ("vence em …", "expires in …"); remove table-header noise (years and column titles that come out as excerpts). It requires an amendment to the current pre-registration, with the same targets, and new held-out cases, written by Roberto with tables in the real format. Until then, the `leitor-f1-1` measurement stands.
  - *F2a, 2026-11-12:* the list of material facts and market notices (IPE) in "What was known on the date", metadata only, and the CVM monitor, with a review queue ([`docs/en/contracts.md`](contracts.md), section 9). Documents filed in 2024 enter the list for 2024 dates, like the DFPs filed in 2024: the list computes nothing, and the seal is by fiscal year. Nothing filed after 2024-12-31 appears in an investigation, the demo or an API response; for those documents the monitor keeps only metadata and hash, without the subject. Adjustments approved on 2026-11-12, before publishing: the reader's detector stays unchanged and only rules that omit more come in (subject all in capitals; capitalized word outside the start and outside the exceptions); empty subject with a notice; versions and repeated documents on a single line, with a link to each, and counts in documents; a notice on the 2010–2014 links; demo investigations without a timestamp, with the generation date only in the manifest. A subject-specific rule only comes in measured, in F2b.
  - *F2b, only after the reply to F2a:* `leitor-f1-2` (the "expanded adversarial set, measured again"), with an amendment to the pre-registration before any code, the same targets, new development cases with tables in the real format, a freeze with hash and new held-out cases written by Roberto after the freeze; if `leitor-f1-2` fails, the section keeps `leitor-f1-1`. The 20 held-out cases of `leitor-f1-1` are now public: measuring the new version on them is informative only.
  - *Decisions:* natural-person names become "trecho omitido; ver página N do documento" ("excerpt omitted; see page N of the document"), with the detector erring on the side of omitting; from the Reference Form, only the last version filed by the date; LLM outside Phase F (on the roadmap); ENET access one request at a time, with interval, retries, integrity and a cache outside git.

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
    - **2026-11-08:** formulas and pages provided by Roberto and recorded in `docs/en/contracts.md`, section 3; works in `docs/en/references.md`.

## Phase C split (Roberto's decision, 2026-11-07)

- **C1:** temporal storage, engine v1 on any date and the study 1 invariant. Stop.
  - **Completed on 2026-11-08:** `chiocca/v2/armazem.py`, `chiocca/v2/na_data.py` and `chiocca/v2/invariante.py`, with the result in [`docs/en/temporal-storage.md`](temporal-storage.md).
  - **First part of C2, authorized on 2026-11-09 and completed:** `escala_original`, the accounts read on a date converted into contract evidence, and the separate ENET fetching command (`chiocca/v2/buscar_enet.py`). The rest of C2 below (context, Altman Z'', Piotroski F, auditor's report and auditor, the "Limits" section on the page, JSON and PDF) was authorized on 2026-11-09 as "C2, second part" and is complete: `chiocca/v2/contexto.py`, `investigacao.py`, `pdf_simples.py`, `pdf_investigacao.py` and the Americanas example in `docs/exemplos/`.
- **C2:** context, Altman Z'', Piotroski F, JSON and PDF. Additions:
  - **Auditor's report and auditor:** a factual section in the investigation, with the type of report, an excerpt of the DFP text checked literally, the auditor and auditor changes from the FCA. It is not a signal family and produces no score or alert.
  - **Altman Z'':** specification of 2026-11-08 in `docs/en/contracts.md`, section 3: formula from p. 27 of Altman (2000), X2 as a Brazilian adaptation, no +3.25 constant and no rating table (a test fails if 3.25 appears), no zones (the 1.23 and 2.90 zones belong to Z'), point-in-time sector and year percentile (non-financial universe if the sector has fewer than 10 companies), "does not apply" for financial companies and a validity note. A v2 worked example of its own, with a test that fails if X2 uses retained earnings alone.
  - **Piotroski F:** specification of 2026-11-08 in `docs/en/contracts.md`, section 3: the nine signals from pp. 7-10, with opening TA = total assets of t−1, t−2 from the DFP of t−1 in the version public on the date, "F = x/9 (y computable)" without imputing a component, "does not apply" for financial companies, a rule and a count for zero long-term debt in both years, and EQ_OFFER from the cash flow statement's issuance line, with the codes recorded.
  - **"Limits" section:** fixed text from `chiocca.v2.limites` on the investigation page, in PT and EN (`docs/en/contracts.md`, section 3).
  - **Do not:** use the Z' zones for Z'' or the 1979 coefficients as a yardstick.
