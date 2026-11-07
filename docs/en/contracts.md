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
- **Maximum reference date: your decision** (question 1 in the [plan](plan-v2.md)). Proposal: 2024-12-31. That way no DFP of a sealed fiscal year is ever read, and the fiscal-year filter still applies to companies whose fiscal year ends mid-year.

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

Date (`YYYY-MM-DD`) entered by the analyst. It is valid within the [minimum date, maximum date] range you decide; outside it, the query is refused with the reason.

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
| `como_o_motor_foi_testado` | Link to the study 1 result, as it came out ([`docs/summary.md`](../summary.md)) |
| `limitacoes` | General and case-specific |
| `motor`, `gerado_em`, `aviso` | Engine version, date and time, fixed notice |

## 3. Signal families, never summed together

| Family | Signals | Role | Source | Alerts? |
| --- | --- | --- | --- | --- |
| Possible manipulation | Engine v1 (study 1): the eight M-score components and M, the DPO jump, the implied interest rate, accruals (context only, as in the study) and, for financial companies, the non-recurring weight | Engine v1 alert, always with context and with the study 1 result alongside | Pre-registration, section 4, and amendments 1 to 11 | Yes, by the study 1 rule, unchanged |
| Financial risk | Altman Z'' (1995 emerging-markets version) | Descriptive context | Altman, Hartzell and Peck (1995), to be checked against the primary source before implementation | No |
| Financial quality | Piotroski F (2000), nine binary tests | Descriptive context | Piotroski (2000), Journal of Accounting Research, to be checked against the primary source before implementation | No |

- The DPO jump and the implied interest rate stay in the possible-manipulation family because, in engine v1, they are part of the same detector (pre-registration, section 4); separating them would change the "in alert" rule. Question 3 in the plan.
- **Altman Z''**: the coefficients, the emerging-markets constant and the zones will be transcribed from the primary source and recorded in `docs/en/sources.md` before implementation, as the backing rule requires. Proposed mapping of the variables to CVM accounts, to be checked: working capital (1.01 − 2.01) ÷ total assets (1); retained earnings (2.03.04 + 2.03.05) ÷ total assets; EBIT (3.05) ÷ total assets; shareholders' equity (2.03) ÷ total liabilities (2.01 + 2.02). Known limits: calibrated outside Brazil; in Brazil, the year's profits are largely distributed or moved to reserves, which affects the retained-earnings variable; it does not apply to financial companies. The source's zones appear as "zones from the original article", never as a verdict.
- **Piotroski F**: the nine tests (profitability, operating cash flow, change in profitability, accruals, leverage, liquidity, equity issuance, gross margin and asset turnover) will be checked against the primary source. Equity issuance depends on `composicao_capital`, which only exists in recent years. For the years without it, the mapping (issuance lines in the cash flow statement, by the frozen pattern in part 4.2 of the reconnaissance, or the change in share capital 2.03.01) will be proposed in Phase C.
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
