# Chiocca System v2 data contracts

Phase A proposal, for your approval. Only the seal (section 1) is already in the code; the rest is specification. Field names stay in Portuguese, as in the rest of the repository; user-facing text comes in PT and EN.

## 0. What the contracts guarantee

- **Engine v1 (study 1) as it is.** v2 calls `chiocca.base.como_era`, `chiocca.variaveis` and `chiocca.sinais.*` from the `estudo-1-final` branch (`8c9a823`) and changes no rule, cut-off or code in those modules.
- **Reference date on every query.** Every answer says "as of YYYY-MM-DD" and uses only what had been filed with the CVM by that date.
- **Seal.** No fiscal year above `ULTIMO_EXERCICIO_LIBERADO` is read, computed, displayed or summarized.
- **Backing.** Every number points to a document, version, filing date, statement, column and account; every sentence about a document carries the excerpt, checked literally.
- **A signal is not an accusation.** No field, label or text says "fraud", recommends buying or selling, or ranks companies by risk. Every output carries the notice: PT "Sinal estatístico baseado em demonstrações públicas. Não é acusação, não é recomendação de investimento."; EN "Statistical signal based on public financial statements. Not an accusation, not investment advice."
- **No binary verdict.** Every signal comes with context (percentile within the sector and year, the company's own history and confidence in the data).

## 1. Seal (already implemented)

- `chiocca/v2/lacre.py`: `ULTIMO_EXERCICIO_LIBERADO = 2023`, in a single place, in the code. Changing it requires a commit.
- `garantir_liberado(exercicio)` raises `ExercicioLacrado`; `so_liberados(tabela)` filters before any computation.
- The test `tests/test_v2_lacre.py` checks the limit, the refusal and that the reused engine v1 computation stops at 2023.
- **Reference date range** (decision of 2026-11-07): from 2011-04-30 to 2024-12-31, in `DATA_REFERENCIA_MINIMA` and `DATA_REFERENCIA_MAXIMA`, with `garantir_data_referencia`. The seal stays by fiscal year: nothing above 2023 is computed, on any date.

## 2. Entities

### Empresa (company)

| Field | Type | Description and origin |
| --- | --- | --- |
| `cd_cvm` | text | CVM code, without leading zeros (study 1 convention) |
| `cnpj` | text | From the DFP index |
| `denominacao` | text | From the fiscal year's DFP (names change over time; the investigation shows the one at the time) |
| `codigos_negociacao` | list of text | From the FCA `valor_mobiliario`, with each code's trading period, in the version filed by the reference date |
| `setor` | text | Sector from the FCA filed by the reference date; with no FCA, the one in the registry (frozen rule, reconnaissance 4.1) |
| `grupo` | `financeira` or `nao_financeira` | Study 1 frozen rule (candidate sector and chart of accounts) |
| `situacao_cadastro` | text | From the current registry, for information only |

### DataReferencia (reference date)

Date (`YYYY-MM-DD`) entered by the analyst, from 2011-04-30 to 2024-12-31; outside that range, the query is refused with the reason. Documents filed after 2024-12-31 only have metadata and hash recorded by the monitor: nothing is read, summarized or extracted from them.

### ExercicioNaData (fiscal year as of the date)

A company in a fiscal year, as it stood on the reference date. It is the output of `como_era(fontes, cd_cvm, exercicio, corte=data_referencia)`.

| Field | Type | Description |
| --- | --- | --- |
| `cd_cvm`, `exercicio`, `dt_refer` | text, integer, date | `exercicio` goes through `garantir_liberado` |
| `data_referencia` | date | The query's |
| `situacao` | enumeration | `ok`, `sem_versao_ate_a_data`, `versao_indisponivel_individual`, `versao_pendente_enet` or `conta_repetida` (the states of `como_era`) |
| `versao_usada`, `dt_receb` | integer, date | The most recent version filed by the reference date |
| `versoes_conhecidas` | list of (version, filing date) | Only those filed by the reference date: the existence of a later version is information from the future and does not appear |
| `tipo` | `con` or `ind` | Consolidated when it exists; otherwise individual |
| `origem` | `dados_abertos` or `enet` | ENET only for consolidated statements (amendment 8) |
| `num_doc`, `link` | text | Document sequence number and ENET page address |
| `escala_original` | `MIL` or `UNIDADE` | Contract values are always in reais |
| `contas` | list of `Evidencia` | The DFP lines used (ÚLTIMO for t and PENÚLTIMO for t−1) |

### Evidencia (evidence)

The unit of backing. Every number and every quotation points to one or more pieces of evidence.

| Field | Type | Description |
| --- | --- | --- |
| `id` | text | Stable: hash of document, version, statement, column and account (or page and excerpt) |
| `documento` | object | `tipo` (DFP, ITR, FCA, IPE), `num_doc`, `versao`, `dt_receb`, `origem` (`dados_abertos`, `enet` or `pdf`), `url`, `sha256` of the file the line was read from |
| `demonstracao`, `coluna` | text | BPA, BPP, DRE, DFC_MI, DFC_MD, DVA or parecer (auditor's report); ÚLTIMO (fiscal year t) or PENÚLTIMO (t−1) |
| `cd_conta`, `ds_conta` | text | Official code and description, as in the file (the official text stays in PT; the EN version only adds the glossary term alongside) |
| `valor` | number | In reais, after scaling; the transformation appears in the lineage |
| `localizacao` | object | For CSV: file and line; for PDF: page and sheet |
| `trecho` | text or null | Only for text documents: the quoted excerpt |
| `conferida` | boolean | For an excerpt, true only if it exists literally on the page (the reader's check) |

### Validade (validity)

The state of each number, adapted from `validade.py` (Carchuna).

| State | Value | When |
| --- | --- | --- |
| `ok` | present | The number can go on screen |
| `indefinido` (undefined) | absent | No number exists: this is engine v1's "not computable", with the same reason (missing account, zero denominator, negative revenue, chart of accounts) |
| `implausivel` (implausible) | present | The arithmetic worked, but a Phase B quality check failed on the input. The state travels with the number and **changes no engine v1 signal** |

A reason is mandatory outside `ok`, in PT and EN. `None` and `NaN` are never used to signal absence.

### Conferencia (check)

CVM data quality check (Phase B): `id`, `nome` (PT and EN), `resultado` (`ok`, `falhou` or `nao_aplicavel`), `valores_comparados` (evidence), `tolerancia` and `detalhe`. Identities, such as assets equal to liabilities plus equity, are kept apart from reconciliations through another path (for example, the cash flow statement against the change in cash on the balance sheet), as in Carchuna.

### Confianca (confidence)

Adapted from the structure of `confianca.py` (Carchuna), **with no numeric score**: the integration plan says not to copy arbitrary scores.

| Field | Description |
| --- | --- |
| `criterios` | List with `fonte` (open data or ENET, consolidated or individual), `completude` (accounts the signal needs), `consistencia` (Phase B checks), `atualidade` (filed by the fiscal year's cut-off, restated later?) and `metodo` (what study 1 showed about the signal) |
| each criterion | `resultado` (`ok`, `atencao` or `problema`) and `motivo` in PT and EN |
| `nivel` | `baixa` (low) if any criterion has a problem; `media` (medium) if any needs attention; otherwise `alta` (high). A written rule, with no sum |

### Contexto (context)

| Field | Description |
| --- | --- |
| `percentil_setor_ano` | Position of the value among companies in the same sector and group, in the same fiscal year, with the signal computable and a version public on the reference date; it carries `n`. Below a minimum `n` (proposal: 10), it is null with the reason and only the group percentile applies |
| `percentil_grupo_ano` | The same within the group |
| `historico` | The company's own series over previous fiscal years, as it stood on the reference date; median, IQR fence and the value's position (inside or outside the fence), with the method written out (detection adapted from `insights.py`). Minimum number of fiscal years, proposal: 5 |

Percentiles and history are display, not rules: they create no alert and do not change engine v1.

### Achado (finding)

| Field | Description |
| --- | --- |
| `id` | Stable |
| `familia` | `possivel_manipulacao` (possible manipulation), `risco_financeiro` (financial risk) or `qualidade_financeira` (financial quality) (section 3) |
| `sinal` | Signal code (for example `mscore`, `DSRI`, `dpo`, `juro`, `lucro_sem_caixa`, `peso_nao_recorrente`, `altman_z2`, `piotroski_f`) |
| `exercicio` | Released by the seal |
| `valor` | With `Validade` |
| `regra` | Only in the possible-manipulation family: the pre-registered rule (for example, M > −1.78), with the reference |
| `alerta_v1` | True or false only in that family, by the study 1 rule; null in the others, which never alert |
| `contexto` | `Contexto` |
| `confianca` | `Confianca` |
| `explicacao` | What the signal measures, in PT and EN, from the catalog |
| `explicacoes_alternativas` | Legitimate reasons for the value (for example, a merger, a change in commercial terms, exchange differences in finance costs), each with a source; when there is a company document, with a checked excerpt |
| `limitacoes` | Of the signal and of the case (for example, a direct-method cash flow statement with no depreciation line) |
| `linhagem` | `Linhagem` |
| `natureza` | Nature of each sentence: `calculado` (computed), `trecho_literal` (literal excerpt), `resumo` (summary), `inferencia` (inference) or `hipotese` (hypothesis) (taxonomy adapted from `proveniencia.py`, DireitoAberto) |

### Linhagem (lineage)

The "how I got to this number" sheet, adapted from `linhagem.py` (Carchuna). It recomputes nothing: it describes the path the engine already took.

| Field | Description |
| --- | --- |
| `numero` | Name, label in PT and EN, value |
| `formula` | Formula text with the case's values |
| `entradas` | Evidence ids, each clickable down to the DFP line |
| `transformacoes` | Scaling to reais, interest paid moved to financing, de-duplication of repeated accounts, cash flow text patterns |
| `premissas`, `limitacoes` | Text in PT and EN |
| `motor` | "engine v1 (study 1)", with commit `8c9a823`, or the v2 module for the context indicators |
| `codigo` | Module and function that computed it |
| `calculado_em` | Date and time |

### Investigacao (investigation)

| Field | Description |
| --- | --- |
| `empresa`, `data_referencia`, `idioma` | — |
| `exercicios` | List of `ExercicioNaData`, all released |
| `achados` | Grouped by family and **never summed** across families |
| `mudancas` | What changed relative to previous fiscal years and to earlier versions known on the date (restatements), with evidence |
| `o_que_se_sabia` | Documents public on the reference date (DFP, ITR and, in Phase F, material fact notices), with filing dates |
| `qualidade_dos_dados` | Checks and confidence |
| `parecer_e_auditor` | Factual section (Phase C2): type of auditor's report, an excerpt of the DFP text checked literally, the auditor and auditor changes from the FCA. It is not a signal family and produces no score or alert |
| `como_o_motor_foi_testado` | Link to the study 1 result, as it came out ([`docs/summary.md`](../summary.md)) |
| `limitacoes` | General and case-specific |
| `motor`, `gerado_em`, `aviso` | Engine version, date and time, fixed notice |

## 3. Signal families, never summed together

| Family | Signals | Role | Source | Alerts? |
| --- | --- | --- | --- | --- |
| Possible manipulation | Engine v1 (study 1): the eight M-score components and M, the DPO jump, the implied interest rate, accruals (context only, as in the study) and, for financial companies, the non-recurring weight | Engine v1 alert, always with context and with the study 1 result alongside | Pre-registration, section 4, and amendments 1 to 11 | Yes, by the study 1 rule, unchanged |
| Financial risk | Pure Altman Z'', for non-manufacturing firms and emerging markets, without the Emerging Market Score constant and without zones | Descriptive context | Altman (2000), "Predicting Financial Distress of Companies: Revisiting the Z-Score and ZETA Models", p. 27, in `referencias/` ([`docs/en/references.md`](references.md)) | No |
| Financial quality | Piotroski F (2000), nine binary tests | Descriptive context | Piotroski (2000), Journal of Accounting Research, pp. 7-10, in `referencias/` ([`docs/en/references.md`](references.md)) | No |

- The DPO jump and the implied interest rate stay in the possible-manipulation family, as in engine v1 (decision of 2026-11-07). Mandatory alternative explanations in the finding, with a source when available: for the implied interest rate, expensive debt, exchange differences and lease interest inside finance costs; for DPO, bargaining power with suppliers and a change in purchase mix.
- **Altman Z''** (decision of 2026-11-07; specification of 2026-11-08, with the pages provided by Roberto and the PDF in `referencias/`). Financial risk family, context only:
  - formula (Altman 2000, p. 27): Z'' = 6.56·X1 + 3.26·X2 + 6.72·X3 + 1.05·X4, with X1 = (1.01 − 2.01) ÷ 1; X2 = (2.03.04 + 2.03.05) ÷ 1; X3 = 3.05 ÷ 1; X4 = 2.03 ÷ (2.01 + 2.02). The codes are from the non-financial chart of accounts (1 = total assets; 3.05 = operating profit before finance result and taxes; 2.03 = consolidated equity, including non-controlling interests);
  - X2 is a **Brazilian adaptation**: since Law 11,638/2007, a Brazilian corporation does not close the year with a positive balance in retained earnings, because retained profit goes to profit reserves (2.03.04) and the remaining balance stays in retained earnings or accumulated losses (2.03.05). Fixed accounts, to be confirmed and located by text if they vary. Capital reserves and equity valuation adjustments are excluded. The adaptation flag goes in the lineage and in the catalog;
  - no +3.25 constant and no rating table (pp. 27-29). A test fails if 3.25 appears in the Z'' calculation;
  - no zones for Z''. The 1.23 and 2.90 zones (p. 26) belong to Z' and are not used. The page shows the value, the sector and year percentile and the phrase "no cut-off zone: the available source does not define zones for Z''". **This changes the decision of 2026-11-07**, which planned to show the original article's zones;
  - the percentile is point-in-time: only DFPs public on the reference date enter. If the sector has fewer than 10 companies, the percentile uses the non-financial universe, flagged;
  - financial companies: "does not apply";
  - validity note, always next to the value: "coefficients estimated outside Brazil; bankruptcy models lose validity over time (Pereira and Martins 2015, p. 25)";
  - a new catalog entry, financial risk family, phase `contexto_v2`, name and description in PT and EN; no engine v1 entry changes;
  - a v2 worked example of its own (not study 1's `data/exemplo_resolvido.json`), with the case of zero retained earnings and positive reserves, and a test that fails if X2 uses retained earnings alone;
  - do not: use the Z' zones for Z'' or the Altman, Baidya and Dias (1979) coefficients as a yardstick.
- **Piotroski F** (decision of 2026-11-07; specification of 2026-11-08, with the pages provided by Roberto and the PDF in `referencias/`). Financial quality family, context only. Nine binary signals (Piotroski 2000, pp. 7-10), with opening TA = total assets of t−1 and average TA = mean of total assets of t and t−1:
  1. ROA > 0, with ROA = 3.09 ÷ opening TA;
  2. CFO > 0, with CFO = 6.01 (as reported) ÷ opening TA;
  3. ΔROA > 0;
  4. ACCRUAL: CFO ÷ opening TA > ROA;
  5. ΔLEVER < 0, with leverage = 2.02.01 ÷ average TA. Zero long-term debt in both years: signal 0, with the flag "no long-term debt in either year" in the lineage (Roberto's decision, 2026-11-08). The article only defines "fell = 1, rose = 0" (p. 8) and does not define a tie; the 0 for a tie is the project's choice. The implementation report counts the cases;
  6. ΔLIQUID > 0, with liquidity = 1.01 ÷ 2.01;
  7. EQ_OFFER: 1 if no shares were issued in the year, from the cash flow statement's issuance line found by text (frozen patterns in part 4.2 of the reconnaissance), with the account codes recorded; flagged as an adaptation; without the line, "not computable";
  8. ΔMARGIN > 0, with margin = 3.03 ÷ 3.01;
  9. ΔTURN > 0, with turnover = 3.01 ÷ opening TA.
  - t−1 values come from the prior-year column of the DFP of t; t−2 values, from the DFP of t−1 in the version public on the reference date. Both origins go in the lineage;
  - the page shows "F = x/9 (y computable)"; a missing component is not imputed;
  - financial companies: "does not apply";
  - the family name is "financial quality", not "earnings quality";
  - a new catalog entry, financial quality family, phase `contexto_v2`.
- **"Limits" section of the investigation page** (fixed text, 2026-11-08). The text comes from `chiocca.v2.limites`, with the numbers read from the study 1 output, and a test checks it matches this one:
  - No alert is not a clean bill of health. In Dechow, Sloan and Sweeney (1995), the most powerful accruals model rejected 'no manipulation' for only 28.1% of 32 companies sanctioned by the SEC (Table 7, p. 32).
  - In study 1, 49.9% of evaluated non-financial company-years (48.3% including financial companies) were in alert, and the number of detections did not beat chance in a descriptive test done after the result: 7 detections in 13 detectable cases, against 7.37 expected by chance without assuming independent years (8.56 assuming independent years).
  - Risk models use numbers that may be manipulated (Pereira and Martins 2015, p. 29). That is why the three families are not added up.
- The catalog already has an `fscore_dechow` (Dechow and others, 2011), which measures something else (likelihood of a restatement) and is a catalog phase 2 signal. It does not come in at this stage, and the names are not confused.

## 4. Reference date, versions and cross-section

- **Version:** for each company and fiscal year, the most recent one filed by the reference date (`como_era` with `corte = data_referencia`). Consolidated when it exists; otherwise individual. Earlier versions come from ENET, consolidated only. t−1 comes from the PENÚLTIMO column of the same DFP.
- **Cross-section:** engine v1's deciles (DPO jump and non-recurring weight) and the context percentiles are recomputed with the companies whose version was public on the reference date. It is the same study 1 rule, applied to the information of that date.
- **Testable invariant:** with the reference date equal to the fiscal year's cut-off date, engine v1's signals and alerts match those of study 1 (`resultados/sinais_empresa_ano.csv`). This test comes in Phase C.
- **Storage:** DuckDB over Parquet, built from `data/brutos` (already checked by hash) and `data/cache/enet`. Tables: `versoes` (metadata of every DFP version up to the seal), `contas` (per available version), `fca` and `cadastro`. A version that is not stored comes out as `versao_pendente_enet`. Fetching from ENET happens through a separate command, never inside an API query (question 9 in the plan).

## 5. Outputs

- **JSON:** the contract above, with Pydantic in Phase D and the same numbers as the engine.
- **PDF:** text and tables, in both languages, generated without dependencies (adapted from `pdf_simples.py`, DireitoAberto), with the fixed notice on every page.
- No list of companies ranked by risk, in any output.
