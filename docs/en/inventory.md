# Inventory of code from the other projects (v2, Phase A)

Inspection done on 2026-11-07 on the attached zips, without installing or running any of the projects. All three belong to Roberto Chiocca and are MIT-licensed. The commits come from each zip's comment (GitHub writes the archive's commit there):

| Project | Commit inspected | Zip SHA256 |
| --- | --- | --- |
| Carchuna | `a3f30ac284eb01245b022b7655bb16c4b8474cc7` | `67b76d50b9fe8dbee5c8f62600e7cab7f7bda61111263e31c39b0e8ec9bc35ee` |
| Calahonda | `47ef323440946a2552bea1ded0da59bd96e6f1a8` | `54425da6af99d21d5247ced946a5c36bcd09279d3c173ac921da1def8496afcf` |
| DireitoAberto | `102e3e2d9d70e87249d8df9215737e2d98b6358d` | `55c3799c1212a2b33834c78ed5bdf7d379a8c3d51b755733c64a82ec19269527` |

No file was brought in this phase. Each one comes in the phase where it is used, with the origin header and an entry in [`docs/en/code-origin.md`](code-origin.md).

Decision key: **bring** (the file comes nearly as is), **adapt** (the structure comes, and the domain content is rewritten for CVM data), **defer** (left for study 2), **discard** (does not come in).

## Carchuna

The core is pure Python, with no dependencies; matplotlib, pandas, FastAPI and Streamlit are extras. Almost everything revolves around the decomposition of a merchant's margin (`margem.py`), so almost nothing comes as is: what matters are the contracts and the principles.

| Module (lines) | What it does | Tests | Decision and reason | What changes | Phase |
| --- | --- | --- | --- | --- | --- |
| `linhagem.py` (206) | "How I got to this number" sheet: origin, columns, transformations, formula with the case's values, assumptions, limitations, source, confidence and when it was computed. It recomputes nothing | `test_linhagem.py` | **Adapt.** The sheet format is exactly what the product needs | Spreadsheet columns become DFP accounts (document, version, column, code); the builder reads the output of engine v1 | B |
| `validade.py` (216) | Result with three states (ok, undefined, implausible), with invariants: ok requires a value; undefined has no value and requires a reason; implausible has a value and a reason. Also `variacao_percentual`, which refuses a negative or zero base | `test_validade_margem.py` | **Bring** the class and `variacao_percentual`. **Discard** the margin thresholds, which belong to the merchant domain | Engine v1's "not computable" becomes "undefined" with the same reason. "Implausible" comes from the Phase B checks and changes no signal | B |
| `confianca.py` (153) | 0–100 score with a fixed rubric (evidence, history, sample, completeness) and a "the data show" versus "hypothesis" sentence | `test_confianca.py` | **Adapt the structure, discard the scoring.** The points belong to the sales domain and were not validated; the integration plan says not to copy arbitrary scores | Components with a name and a reason, assessed by explicit rules (source, completeness, consistency, timeliness, method) and a categorical level, with no summed score (see the contracts) | B |
| `diagnostico.py` (393) | `RegraDeteccao` → `Achado` pattern, orchestrated by `MotorDiagnostico`; the rules are about taxes and marketplaces | `test_diagnostico.py` | **Adapt the pattern. Discard the rules** and the dependency on the legal RAG | Each engine v1 signal and each context indicator becomes a rule that returns an `Achado` (finding) in the Chiocca contract | C |
| `insights.py` (731) | `detectar_fora_do_padrao`: z-score against the history, with an IQR-fence veto (quartiles ± 1.5×IQR) and a rule for a constant history; the rest are monthly-margin analyses | `test_insights.py` | **Bring the detection, discard the analyses** of margin | Annual instead of monthly series: the minimum number of fiscal years and the fence are display parameters, not engine rules | C |
| Quality checks (`margem.py`: structural identity, `reconciliar`, `conferir_plausibilidade`) | Separates identity (which holds by construction) from reconciliation through another path and from plausibility | `test_conferencia_na_fronteira.py`, `test_fechamento_percentual.py` | **Adapt the principle**, because the implementations belong to the merchant margin | CVM-specific checks: balance sheet that does not balance, income statement subtotals, cash flow statement that does not reconcile with the change in cash, implausible values | B |
| `relatorio.py` (231) | 3-page PDF with matplotlib | `test_relatorio.py` | **Discard the implementation.** The product PDF uses DireitoAberto's dependency-free generator; the layout serves as a reference | — | C |
| `margem.py`, `cenarios.py`, `rag/`, `tipos.py`, `app.py`, `api/` | Margin, Simples Nacional (Brazil's simplified small-business tax regime), scenarios, legal RAG, spreadsheet ingestion, Streamlit and its own API | — | **Discard**: tax and small-business rules, as the prompt says; the reference API is DireitoAberto's | — | — |

## Calahonda

The core depends on numpy, pandas and scipy; yfinance, matplotlib and Streamlit are extras.

| Module (lines) | What it does | Tests | Decision and reason | What changes | Phase |
| --- | --- | --- | --- | --- | --- |
| `backtest.py` (110) | Kupiec test (proportion of failures, χ² with 1 degree of freedom) for VaR violations | `test_stress_backtest.py` | **Adapt** into an exact binomial test of detections against the alert rate, without scipy (only `math.comb`). It comes in only with your authorization: it is a new statistic on study 1 that was not pre-registered (see the question in [`docs/en/plan-v2.md`](plan-v2.md)) | Output labeled as descriptive, computed after the study | C, if authorized |
| `report.py` (211) | 3-page portfolio PDF, with matplotlib | `test_report.py` | **Discard**, for the same reason as Carchuna's report | — | — |
| `data.py` (208), `metrics.py` (185), `ratios.py` (179) | B3 prices via yfinance with a synthetic fallback, return, volatility, drawdown, Sortino, Calmar and others | `test_data_benchmark.py`, `test_metrics.py`, `test_ratios.py` | **Defer** to the study 2 return test, as the prompt says | — | Study 2 |
| `var.py`, `stress.py` | Portfolio VaR and stress | `test_var.py` | **Discard as a detector**, as the prompt says | — | — |

## DireitoAberto

The backend uses FastAPI, SQLAlchemy, pypdf and anthropic; the web app uses Next.js 15 and React 19, with no component library. It is the reference for evidence, verification, monitor, API and interface.

| Module (lines) | What it does | Tests | Decision and reason | What changes | Phase |
| --- | --- | --- | --- | --- | --- |
| `corpus/proveniencia.py` (526) | Nature of each text (literal, consolidated, explanatory summary, interpretation, not checked), hash and coverage by sequences of 8 words | `test_proveniencia.py` | **Adapt the taxonomy**, which separates fact, summary and inference. **Discard** the rest, tied to the legal corpus | Nature of each sentence in the investigation: computed number, checked literal excerpt, summary, inference or hypothesis | C and F |
| `monitor/registro.py` (290) | Version registry with a review queue: baseline, pending, accepted, rejected and superseded; hashed snapshots, decision log, file lock, revision counter and reversal without deleting history | `test_monitor.py`, `test_monitor_operacao.py` | **Bring**: it is generic and already handles concurrency and reversal | CVM sources (DFP, ITR and IPE indexes) instead of Planalto pages | F |
| `monitor/comparar.py` (293), `eventos.py` (63) | Article-by-article comparison of laws and translation into legal events | `test_monitor.py` | **Discard the logic**, which is legal. **Adapt the idea** of conservative classification | CVM classification: new DFP, new version (restatement), new ITR, new material fact notice, suspicious collection | F |
| `monitor/coleta.py` (209) | Polite collection: retries with backoff, `Retry-After`, no retrying on 403 and 404, hash over the text | `test_monitor_operacao.py` | **Adapt** for the CVM downloads, together with `chiocca/dados.py` | CVM addresses and formats | F |
| `leitor/verificacao.py` (79) | Literal check of a quotation against the page, tolerating only spaces, line breaks and end-of-line hyphenation; also applies to LLM text | `test_leitor.py` | **Bring** | The Chiocca document model (PDF pages and CVM CSV lines) | F |
| `leitor/extracao.py` (531), `documentos.py` | PDF text extraction with size and time guards (pypdf) | `test_leitor.py`, `test_documentos.py` | **Adapt the minimum** in Phase F; the dependency (pypdf or `pdftotext`) is a decision for that phase | Material fact notices and notes to the financial statements | F |
| `leitor/pdf_simples.py` (128) | Dependency-free PDF generator: Helvetica, Windows-1252 text, deterministic | `test_leitor_conjunto.py` | **Bring** for the investigation PDF and for the adversarial set | Transliterate characters outside Windows-1252 (for example "−", "≥" and "÷") | C and F |
| `leitor/avaliacao.py` (222), `conjunto_adversarial.py` (433) | Evaluation against a hand-written declarative answer key, with an implicit check of every quotation; fictitious documents that reproduce known failures | `test_leitor_conjunto.py` | **Adapt the mechanism**; the documents and answer keys are new, with fictitious material fact notices and notes | Chiocca checks: related parties, risco sacado (supplier finance) or forfait, auditor change, qualified opinions and guarantees | F |
| `validacao.py` (208) | Validation state of each answer by deterministic checks, none of them given by the LLM itself | `test_validacao.py` | **Adapt the pattern**; the checks are legal | Feeds the confidence and the state of generated sentences | B and F |
| `main.py` (803) | FastAPI API under `/api/v1`, body limit, rate limiting, authentication, database and LLM | `test_api.py` and others | **Adapt the structure** (`/api/v1` router, `/saude`, body limit, error handling). **Discard** authentication, database, feedback and legal routes | Chiocca routes, with Pydantic on the contracts | D |
| `web/` (Next.js 15, React 19, TypeScript) | App router, components, `lib/api.ts`, its own CSS and `vercel.json` | `test_frontend_estatico.py` | **Adapt the structure and the components** that fit | Chiocca pages, PT and EN, dark mode and mobile | E |
| `.github/workflows/ci.yml` | Lint, types, tests on two Python versions, web build and dependency audit | — | **Adapt** | Chiocca commands (ruff, black, mypy, pytest) | B |
| Legal corpus, case law, embeddings, semantic search, authentication, feedback, `render.yaml` | — | — | **Discard** in this stage. Deployment is a Phase E decision | — | — |

## CVM data facts that bear on the contracts

Checked only on the structure of the files already downloaded (no values, no signals and no fiscal year above the seal):

- The DFP zip has `parecer` (type and text of the auditor's report) in every year checked, and `composicao_capital` (number of shares) only in recent years: it is in 2023 and missing in 2010 and 2015.
- The FCA has `auditor` (auditor history, with start and end dates) and `valor_mobiliario` (B3 trading codes, with dates). They serve the auditor change and searching a company by trading code.
- In the non-financial chart of accounts, 2.03.04 "Reservas de Lucros" (profit reserves) and 2.03.05 "Lucros/Prejuízos Acumulados" (retained earnings or accumulated losses) are fixed accounts.
