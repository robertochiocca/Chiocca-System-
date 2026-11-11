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
| `denominacao` | text | From the fiscal year's DFP (names change over time; the investigation shows the one at the time) Implemented in C2: company name from the latest FCA version filed by the date; the open-data index carries the current name, which may be later than the date (Americanas' already said "em recuperação judicial") |
| `codigos_negociacao` | list of text | From the FCA `valor_mobiliario`, with each code's trading period, in the version filed by the reference date. Implemented in Phase D: the store's `valores_mobiliarios` table (only FCA versions filed by 2024-12-31); each code comes with the security, the market, the trading start and end dates and the source FCA (year, version and filing date), from the latest FCA version filed by the date. An empty list comes with `motivo_codigos_negociacao`: in the open data, the field is filled only in the more recent FCAs, and the year from which it is filled is computed from the store and goes in the reason |
| `setor` | text | Sector from the FCA filed by the reference date; with no FCA, the one in the registry (frozen rule, reconnaissance 4.1) |
| `grupo` | `financeira` or `nao_financeira` | Study 1 frozen rule (candidate sector and chart of accounts) |
| `situacao_cadastro` | text | From the current registry, for information only. Rule of 2026-11-09: it is today's information and is not in the company block, which is the "as it was" view; it goes in the `informacao_de_hoje` section at the end of the investigation (see "Today's information" below) |

### DataReferencia (reference date)

Date (`YYYY-MM-DD`) entered by the analyst, from 2011-04-30 to 2024-12-31; outside that range, the query is refused with the reason. Documents filed after 2024-12-31 only have metadata and hash recorded by the monitor: nothing is read, summarized or extracted from them.

### ExercicioNaData (fiscal year as of the date)

A company in a fiscal year, as it stood on the reference date. It is the output of `como_era(fontes, cd_cvm, exercicio, corte=data_referencia)`.

| Field | Type | Description |
| --- | --- | --- |
| `cd_cvm`, `exercicio`, `dt_refer` | text, integer, date | `exercicio` goes through `garantir_liberado` |
| `data_referencia` | date | The query's |
| `situacao` | enumeration | `ok`, `sem_documento`, `sem_versao_ate_a_data`, `versao_indisponivel_individual`, `versao_indisponivel_enet`, `versao_pendente_enet` or `conta_repetida` (the states of `como_era`, with the contract name in `chiocca.v2.na_data.SITUACAO`) |
| `versao_usada`, `dt_receb` | integer, date | The most recent version filed by the reference date |
| `versoes_conhecidas` | list of (version, filing date) | Only those filed by the reference date: the existence of a later version is information from the future and does not appear |
| `tipo` | `con` or `ind` | Consolidated when it exists; otherwise individual |
| `origem` | `dados_abertos` or `enet` | ENET only for consolidated statements (amendment 8) |
| `num_doc`, `link` | text | Document sequence number and ENET page address |
| `escala_original` | `MIL` or `UNIDADE` | Contract values are always in reais. Implemented in C2: the original scale of the open-data version (the store's `escalas` table). For ENET versions the field is empty, because the cache keeps values already in reais and does not record the page's scale; the reason goes in the notes |
| `contas` | list of `Evidencia` | The DFP lines used (ÚLTIMO for t and PENÚLTIMO for t−1). Implemented in C2 as `evidencias` (`chiocca.v2.na_data.evidencias`), with the source file and line when a `Localizador` is given |
| `notas` | list of reasons (PT and EN) | Lineage notes on the document. When the version used is not the latest, `como_era` reads the structure of the latest version, filed after the date, and the note is "structure read from a document filed after the date (study 1 behaviour, amendment 8)" (decision of 2026-11-09) |

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
| `percentil_setor_ano` | Position of the value among companies in the same sector and group, in the same fiscal year, with the signal computable and a version public on the reference date; it carries `n`. Below a minimum `n` (proposal: 10), it is null with the reason and only the group percentile applies. In Phase E, the context also carries `distribuicao_setor_ano`: only the aggregate distribution of the sector and year (quantiles and an equal-width histogram between the 5th and 95th percentiles, with the counts below and above), never names or values of other companies, and only with the same minimum `n` |
| `percentil_grupo_ano` | The same within the group |
| `historico` | The company's own series over previous fiscal years, as it stood on the reference date; median, Tukey range (quartiles ± 1.5 × IQR; in the JSON, `faixa_tukey`) and the value's position (inside, above or below the range), with the method written out (detection adapted from `insights.py`). Minimum number of fiscal years, proposal: 5. In Phase E, it also carries `serie` (the company's own series, for the timeline) |

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

Implemented in C2, second part (`chiocca/v2/investigacao.py`, JSON; `chiocca/v2/pdf_investigacao.py`, PDF generated only from the JSON). Reference examples: Americanas, fiscal year 2021, on 2022-04-30 and on 2024-12-31 (the latter with the differences in the comparative of the 2022 DFP as highlighted evidence), in `docs/exemplos/` (PT and EN, JSON and PDF), generated by `python -m chiocca.v2.exemplos` and checked by the same test. The auditor's report comes from the open-data opinions section, which exists only for the latest DFP version; auditor changes come from the FCA, by the firm's CVM code, with no CPF and no natural person. `gerado_em` and `calculado_em` are the only fields that change between runs.

| Field | Description |
| --- | --- |
| `empresa`, `data_referencia`, `idioma` | — |
| `exercicios` | List of `ExercicioNaData`, all released |
| `achados` | Grouped by family and **never summed** across families. Each finding carries `unidade` (days for the DPO, p.p. for interest minus CDI, "index" for the components and the other ratios, "signals out of 9" for the Piotroski F), and every value shown carries its unit. M-score components: `componente_de = "mscore"` and the rule "M-score component; it has no rule of its own". Signal titles and list items start with a capital letter (2026-11-09) |
| `mudancas` | What changed relative to previous fiscal years and to earlier versions known on the date (restatements), with evidence. In C2: `comparativo_destacadas` (only the differences highlighted by the materiality rule in section 4), `reapresentacao_pelo_comparativo` (full list, with each difference's group) and `materialidade_comparativo` (key lines, relative threshold, total assets and threshold) |
| `o_que_se_sabia` | Documents public on the reference date (DFP, ITR and, in Phase F, material fact notices), with filing dates |
| `qualidade_dos_dados` | Checks and confidence |
| `parecer_e_auditor` | Factual section (Phase C2): type of auditor's report, an excerpt of the DFP text checked literally, the auditor and auditor changes from the FCA. It is not a signal family and produces no score or alert. Rotation (rule of 2026-11-09): fixed note `rodizio` on CVM Resolution No. 23/2021, arts. 31 (five consecutive fiscal years, with a minimum interval of three before being hired again) and 31-A (up to ten, with a statutory audit committee and a firm as auditor), in force since 2021-04-01 (art. 41), which revoked CVM Instruction No. 308/1999 (art. 40, I), with an equivalent rule in its arts. 31 and 31-A; text checked at the CVM on 2026-11-09. Changes (finishing of 2026-11-09): one line per real change, comparing firms by their CVM code, with one canonical name per code, also in the auditors by FCA: the most frequent spelling in the FCAs filed by the date, across all companies, among those already in normal capitalization (on a tie, the most recent); if there are only upper-case spellings, the most frequent gets normal capitalization, keeping acronyms such as KPMG, BDO and S.S. (request of 2026-11-09; display only, the comparison is still by code); when the new firm appears in the FCA next to the outgoing one, it is a single change, with `transicao_fca` ("transition: two firms in the YYYY FCA"); a firm added or removed with no counterpart is a line with the other side empty. An individual auditor (CPF in the auditor field) has no name stored: it shows as "individual auditor (name omitted)". For each change, `saida` gives the outgoing firm's consecutive fiscal years, from the start and end dates in the FCA (whoever is engaged at a fiscal year's end audits it); when the change coincides with the end of the term (five or ten fiscal years), the note says the change is compatible with the rotation rule, citing the rule in force when the new firm started. A change of auditor is a fact, not an alert |
| `informacao_de_hoje` | **Today's information (outside the reference date)** (rule of 2026-11-09): what comes from today's data, and not from what was public on the date, stays out of the "as it was" view. It goes in a separate section at the end, with that title: for now, the status in the CVM registry of listed companies, with the source. In the PDF, it is the last section before the annex |
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
  7. EQ_OFFER: 1 if no shares were issued in the year, from the cash flow statement's issuance line found by text (frozen patterns in part 4.2 of the reconnaissance), with the account codes recorded; without the line, "not computable". Implemented in C2: among the frozen-pattern lines, only those about shares or capital (whole word), because the pattern also catches borrowing; a positive sum is an issuance (0), a zero sum is no issuance (1); with no line or a negative sum, not computable. Label (corrected on 09/11/2026): counting only share or capital lines is the article's own definition ("did not issue common equity", p. 9), not an adaptation. The adaptation, flagged in the result, is only this: preferred shares also count, because in Brazil they are equity, and the line is identified by text in the cash flow statement;
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
- **Restatement through the comparative** (rule of 2026-11-09, recorded before implementation; it changes no engine v1 calculation or alert):
  - when, on the reference date, the next fiscal year's DFP already exists (version public on the date, by `como_era`), each account of fiscal year t in the version used (ÚLTIMO column) is compared with the PENÚLTIMO column of the DFP of t+1;
  - the comparison is by the same statement (the cash flow statement by prefix, because the method may change) and the same account code, in the same type (consolidated with consolidated, individual with individual). An account that exists in only one of the columns is left out, because the chart of accounts may change;
  - tolerance: R$1,000 per account, the same as in the data checks (`TOLERANCIA_POR_PARCELA`). A difference above that goes into the investigation as evidence, with the neutral text "different value in the following year's comparative (restatement or reclassification)", both versions, both filing dates, both values and the difference;
  - it does not apply when the DFP of t+1 has no version public on the date, when either reading is not ok or when the types differ. Because of the seal, t+1 goes up to 2023: fiscal year 2023 has no comparison.
- **Materiality of comparative differences** (rule of 2026-11-09, recorded before implementation; it changes no engine v1 calculation or alert, and nothing here becomes an alert signal):
  - differences above the tolerance are split into two groups. Group (a), totals and key lines: total assets (BPA 1), current liabilities (BPP 2.01), non-current liabilities (BPP 2.02), equity (BPP 2.03), net revenue (DRE 3.01), net income (DRE 3.11) and operating cash flow (DFC 6.01), with the same codes as engine v1 (`chiocca/variaveis.py`). Group (b), reclassifications: differences in the other lines, which do not change the totals; when a total also changes, its difference appears in group (a);
  - highlighted: a group (a) difference whose absolute value is above 1% of total assets (BPA 1, ÚLTIMO column) of the version of t used. Without positive total assets in the version used, nothing is highlighted;
  - the investigation highlights only the highlighted differences, with the same neutral text; every difference (from both groups, with the group of each) stays in the full list of evidence;
  - for financial companies, the income statement chart of accounts is different, and codes 3.01 and 3.11 may be other lines; the label shown is always the account's own description;
  - descriptive: how many company-years have a highlighted difference on 2024-12-31, in [`docs/en/temporal-storage.md`](temporal-storage.md), generated by `chiocca/v2/invariante.py`.
- **Testable invariant:** with the reference date equal to the fiscal year's cut-off date, engine v1's signals and alerts match those of study 1 (`resultados/sinais_empresa_ano.csv`). Implemented in C1 (`chiocca/v2/invariante.py`), with the result in [`docs/en/temporal-storage.md`](temporal-storage.md).
- **Storage:** DuckDB over Parquet, built from `data/brutos` (already checked by hash) and `data/cache/enet`. Tables: `versoes` (metadata of every DFP version up to the seal), `contas` (per available version), `fca` and `cadastro`. A version that is not stored comes out as `versao_pendente_enet`. Fetching from ENET happens through a separate command, never inside an API query (question 9 in the plan). Implemented in C1 (`chiocca/v2/armazem.py`), with one more rule: for documents filed after 2024-12-31, the store keeps only metadata and the structure (which statements exist), with no account and no value; `como_era` uses that structure of the latest version to decide the ENET route (amendment 8). Decision of 2026-11-09: the structure counts as metadata; a test ensures no account or value of these documents is stored, and, when the engine on a date uses structure read from a document filed after that date, the lineage records "structure read from a document filed after the date (study 1 behaviour, amendment 8)". Documents filed after 2024-12-31 with only their structure in the store, by fiscal year: 2023: 14 (total: 14). ENET fetching through a separate command: `python -m chiocca.v2.buscar_enet` (C2).

## 5. Outputs

- **JSON:** the contract above, with Pydantic in Phase D and the same numbers as the engine.
- **PDF:** text and tables, in both languages, generated without dependencies (adapted from `pdf_simples.py`, DireitoAberto), with the fixed notice on every page.
- No list of companies ranked by risk, in any output.

## 6. API (Phase D)

Implemented in `chiocca/v2/api.py` (FastAPI), with the Pydantic contracts in `chiocca/v2/modelos.py`, from the same model as the Phase C JSON: the API recomputes nothing, validates the JSON of `chiocca.v2.investigacao.gerar` against the model (unknown fields are rejected) and returns the same numbers as the engine. Every route is GET, under `/api/v1`, and every response carries the reference date and the fixed notice.

| Route | Response |
| --- | --- |
| `/saude` | Seal, date range, the store's fiscal years and rows, engine versions |
| `/empresas?busca=&data_referencia=&limite=` | Company search (`BuscaEmpresas`): only by name (3 characters or more, accent- and case-insensitive), CVM code (up to 6 digits) or CNPJ (14 digits, with or without punctuation); up to 50 results |
| `/empresas/{cd_cvm}?data_referencia=` | The company on the date (`Empresa`, with the name of the time, sector, group and trading codes) and the fiscal years with a DFP filed by the date |
| `/empresas/{cd_cvm}/exercicios/{exercicio}?data_referencia=` | `ExercicioNaData` with the evidence (the DFP lines in the version used) |
| `/investigacoes/{cd_cvm}/{exercicio}?data_referencia=&idioma=` | `Investigacao`, the same JSON as in section 2 |
| `/investigacoes/{cd_cvm}/{exercicio}/pdf?…` | The PDF generated only from that JSON |
| `/investigacoes/{cd_cvm}/{exercicio}/linhagem/{sinal}?…` | The lineage of one number, with the evidence it cites |
| `/como-o-motor-foi-testado` | Study 1 figures, from the same JSON as the summary (the same as in the [engine card](engine-card.md)), with the lead time of the detections (Phase E) |

- **Validations:** the same as in the contract. Reference date from 2011-04-30 to 2024-12-31 (with no date, the maximum) and fiscal year up to 2023 (seal); otherwise the refusal (422) carries the reason (`data_fora_do_intervalo`, `exercicio_lacrado`). Company or fiscal year with no DFP filed by the date: 404 with the reason. A request with a query string above 2,048 characters (414) or a body above 16,384 bytes (413) is refused.
- **Rule of 2026-11-09:** no endpoint lists companies ranked by alert, percentile or score. Search is only by name, CVM code or CNPJ (not by trading code, which appears only as company information), the list of companies comes only from the search, always in alphabetical order of the name, and the search result carries no signal. No route accepts a sorting parameter. A test (`tests/test_v2_api.py`) checks the routes, the parameters, the OpenAPI schema and the search order.
- **Name of the time in the search:** the name shown and the names searched are those of the FCA filed by the date; with no FCA, the DFP index name, flagged in `origem_denominacao`. So a company is not found by a name it only had after the date.
- **No network:** the API reads only the store; a missing version comes out as `versao_pendente_enet` (ENET fetching is the separate C2 command). The contract tests run with the fixture store and the network blocked.
- **Demo mode** (Phase E, turned on by `CHIOCCA_MODO_DEMONSTRACAO=1`): the search and the per-company routes only accept the companies of the ground-truth cases (`data/gabarito_casos.csv`, which under the pre-registration rule only has CVM convictions or admitted fraud), without the cases under observation; the others are refused (403, `fora_do_modo_demonstracao`) with the reason. `/saude` says whether the mode is on. Pattern inspired by FraudShield (MIT), with no copied code.
- **Usage:** `python -m chiocca.v2.api [port]` (uvicorn on 127.0.0.1; interactive documentation at `/api/v1/docs`).

## 7. Interface (Phase E)

Implemented in `web/` (Next.js, React and TypeScript, with no component library), with the rules of 2026-11-09:

- **The same rules as the API.** No list of companies ranked by alert, percentile or score; search is only by name, CVM code or CNPJ, and results appear in the API's order (alphabetical). A web test checks that no screen reorders lists and that there is no ranking route.
- **Sector peer comparison is aggregate only:** percentiles and the `distribuicao_setor_ano` histogram. Never names of other companies next to values or alerts; the charts receive no name, code or CNPJ.
- **Date selector** limited to 2011-04-30–2024-12-31 and fiscal years up to 2023 (the same limits as `chiocca/v2/lacre.py`, checked by a test). "Today's information" stays separate, at the end, as in the PDF.
- **Fixed notice on every screen** (in the sticky top bar), PT and EN, dark mode and mobile.
- **"How the engine was tested"**: the figures come from the `/como-o-motor-foi-testado` route, which reads them from the same JSON as the summary; link to the engine card and the lead time of the detections.
- **Contract:** every API response goes through `web/lib/contrato.mjs` before reaching the screen. The web tests (`npm test`, no network) run these functions over the examples in `docs/exemplos/` and over the API responses stored in `web/tests/contrato/`, which a Python test (`tests/test_v2_contrato_web.py`) checks against the current API.
- **Demo mode:** the API's (section 6); the interface shows a notice when it is on.
- **Labels, not codes (2026-11-10):** document origin, statement type, `DFC_MI`/`DFC_MD`, the CVM file column (`ÚLTIMO`/`PENÚLTIMO`) and the signal identifier appear on screen as labels, in both languages ("dados abertos · consolidado", "open data · consolidated"). The same holds for the PDF and for the engine v1 reasons that study 1's text catalog does not translate (M-score component not computable, "not computed"), which get text in the v2 layer (`chiocca/v2/validade.py`), without touching study 1; the code stays in the `codigo` field. The screen test checks, in PT and EN, that no identifier with an underscore appears outside links and file names, and a Python test checks the PDF text; an article acronym only appears in parentheses right after the readable name, as in the M-score indices ("No equity issuance (EQ_OFFER)"); on its own, it counts as a code (decision of 2026-11-10, which removed the `EQ_OFFER` exception). Before publishing, `npm run varrer:demo` opens every investigation of the generated demo in the browser, in both languages, with the same check.
- **Highlighted-difference notice:** when the comparative in the following year's DFP has a highlighted difference ("Changes" section), the investigation shows a notice right below the title, with the number of accounts, the DFP and the filing date, and a link to the section; neutral wording, no adjectives.
- **Tukey range** with the unit only once: "from *a* to *b* (*unit*)".
- **Piotroski F signals:** a readable name with the article's acronym in parentheses, as in the M-score indices, on screen and in the PDF, in PT and EN (`chiocca/v2/contexto.py`, `ROTULOS_F`; the screen uses the same ones, checked by a test). The screen lists the nine signals, as the PDF does.
- **Minus sign (2026-11-10):** in the v2 display (screen and PDF), a negative number uses the minus sign (−), including in rules ("M > −1.78"). The investigation texts go through `chiocca/v2/exibicao.py` (except literal data: the auditor's report excerpt, the account name as it came from the CVM and the evidence) and the PDF formats numbers with its functions. In the PDF, the minus sign goes in through the Helvetica encoding, and delta, less-or-equal and greater-or-equal through the Symbol font, because the Helvetica built into the most used readers lacks those glyphs. Study 1 files and texts do not change (`chiocca/formato.py` keeps the hyphen). Tests in Python (JSON and PDF) and on screen.
- **Repository paths** cited in the texts (`docs/…`, `chiocca/…`) become links to the file on GitHub; the screen test checks that every link points to a file that exists.
- **Mobile menu:** a full-screen panel with a solid background, over all the content; it closes on navigation, on a tap outside the items and with Esc; the theme button has an accessible label, naming the theme it switches to ("Tema escuro"/"Tema claro", "Dark theme"/"Light theme").
- **Static demo (2026-11-10):** the demo-mode investigations generated by a script (`python -m chiocca.v2.demonstracao_estatica`), so the interface can be published as a static site, with no API running. Companies: those of demo mode. Dates for each company: the cut-off date of each fiscal year of the case's affected period, the one of the previous fiscal year and 2024-12-31; on each date, the fiscal years of that set whose DFP had been filed by then. The files are the API's own output, called in process: the investigation in JSON and PDF in both languages, the company on the date and "how the engine was tested", plus an `indice.json` in alphabetical order (names known up to 2024-12-31, for search, and the dates). The interface reads the files with the same `web/lib/contrato.mjs` functions it uses with the API; in static mode the date selector only offers the generated dates and the screen says so. A Python test (`tests/test_v2_demonstracao_estatica.py`) checks that the files equal the API output for the same inputs (without the timestamps; the PDF byte for byte). The files live in `web/public/demo/`, outside git (PDFs do not enter the repository); the static build is `npm run build:estatico`, with `NEXT_PUBLIC_BASE_PATH` to publish under a subfolder. The full product keeps running locally with the API.
- **Publication on GitHub Pages (Roberto's decision, 2026-11-10):** the demo is generated from the final commit of the development branch and the exported site, with `NEXT_PUBLIC_BASE_PATH=/Chiocca-System-`, goes to the orphan `gh-pages` branch, assembled by `python -m chiocca.v2.gh_pages`. The `gh-pages` branch holds only the generated site, with a `.nojekyll` at the root (without it, GitHub Pages ignores the `_next` folder) and a `manifesto.json` with the source commit, the commands used, the date and the hash (SHA-256) of every file. Before pushing, `npm run varrer:demo` runs on the exported site, and the assembly refuses a sweep with problems. **Exception to the no-PDF-in-Git rule:** only `gh-pages`, which is generated (besides `docs/exemplos/`, authorized earlier). Updates go in as normal commits on `gh-pages`, with no force push. The address is https://robertochiocca.github.io/Chiocca-System-/; Roberto turns Pages on.
- **Phase E2, experience and explanation (authorized on 2026-11-10):**
  - *Header:* language "PT | EN" side by side (`aria-pressed`), theme with an icon and an accessible label; only the notice is fixed, on a compact line; the demo strip sits at the top of the page; the footer links to the repository and the engine card. On mobile, the menu is a full-screen dialog with "Language: Português | English" and "Theme: Light | Dark" and the notice at the foot.
  - *New API data (and static demo):* the `/api/v1/demonstracao` route (`chiocca/v2/demonstracao.py`) returns the demo-mode companies in alphabetical order, with the ground-truth case (type, public date, affected period and source; never the notes, which name people), the dates with labels ("previous fiscal year", "case's affected period", "after it came to light"), the starting date (that of the first fiscal year of the affected period) and the home-page highlights, taken from the examples in `docs/exemplos/`; it is the static demo's `indice.json`, and the generation plan comes from it. The company block gains `nomes_anteriores` (the FCA names, by reference year, as filed); "Today's information" gains today's name, the only place where it appears; "How the engine was tested" gains the four study 1 rules with their cut-offs, the limits and the pre-registration link. None of these carries a signal result, and the web contract rejects any signal field in the demo route.
  - *Home page:* what Chiocca does and what "as it was on a date" means, the demo note, the search (nothing ranked by alert), "Start here" (at the time, afterwards and how the engine was tested, with the numbers from the JSONs) and the demo companies in alphabetical order, with the case and the public date, the first 10 and a button to see them all.
  - *Company and investigation header:* breadcrumb, name on the date, "Fiscal year YYYY · as it was on YYYY-MM-DD", name history, dates as buttons with labels and, in the investigation, "Export as PDF" and "Document at the CVM".
  - *Investigation:* a summary at the top with four cards (possible manipulation with a badge and what fired and stayed below the cut-off; financial risk and financial quality, context only; the ground-truth case, in light blue, with "inside/outside the affected period"), the sentence that the families do not add up and "How to read this page"; an "On this page" index (on mobile, a row of buttons); sections with a subtitle; a signal card with what it measures and why it matters (the `leitura_simples` block of `catalogo_sinais.yaml`, added in v2, generated into `web/lib/catalogo.json` with a test), value, study 1 rule, badge, percentiles and "Show details"; the M-score expanded, with the grid of the 8 components (percentile bar and the tag for the company's own range); Z'' with readable components; F with the nine signals in text ("yes", "no", "not computable"); in "Changes", when the following DFP did not exist on the date, the link to the same investigation on the last date. Badges: "Alert" in amber, "No alert" in neutral gray (never green: no alert is not a clean bill), "Context only" in light blue.
  - *Help:* the texts of the "?" icons live in a single PT and EN glossary (`web/lib/glossario.ts`).
  - *Accessibility:* AA contrast in both themes, visible focus, touch targets of 44 px or more, real buttons and scrolling tables reachable by keyboard; the screen test runs axe (`@axe-core/playwright`) in both languages and both themes, with zero serious or critical violations.
  - *Screenshots:* `npm run capturas` produces the home page, the company, the investigation (top and details open), the mobile menu and "How the engine was tested", on computer and phone, in PT and EN, in light and dark themes; in CI, they become an artifact of the web job.
  - *Finishing touches (2026-11-11):* amber is reserved for the "Alert" badge: the "Above the company's own range" tag becomes light blue, like "Context only" (a CSS test and a screen test, in both themes). In the summary's risk and quality cards, a small uppercase label ("Financial risk · context only", "Financial quality · context only"), the big number on its own line (Z'' and F) and a short line below (the sector percentile with the number of companies; the computable signals), with no badge repeating "context only". A single-year affected period shows no range ("2021") and the case type starts with a capital letter ("Admitted fraud", "CVM conviction"). The home page list shows the company's name in the ground truth (the investigation title keeps the FCA name on the date), in alphabetical order by it (`ordem: "nome_do_caso"` in the demo route), with the affected period; a case that ends before 2010 gets, in the list and on the company page, the tag "Case before the start of the data (2010): only fiscal years from 2010 onward can be seen". A case with no public date in the ground truth is left out of the demo (Sanepar, Construtora Beter and Mendes Júnior leave); the number of companies comes from the JSON, in texts, tests and the README. On a phone, the fixed notice is a short line ("Statistical signal. Not an accusation or advice.") with "Learn more", which leads to the full text in the footer; it stays on one line in any font and width ("Learn more" always whole; if the sentence does not fit, its end becomes "…"), and the screen test checks one line, no horizontal scroll (390 and 320 px) and no index heading under it. On the company page, the card with the CVM code, CNPJ and sector sits right below the title, before the dates, and the ground-truth case comes before the list of fiscal years.
- **CI:** type checking, contract and rule tests, build, static build with a screen test in a real browser (Playwright and Chromium; test data assembled from `docs/exemplos/`) and `npm audit --audit-level=high`. Nothing is published.
