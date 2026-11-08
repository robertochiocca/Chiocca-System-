# Trust engine (v2, Phase B)

Four modules in `chiocca/v2/` that describe the numbers of engine v1 (study 1) without changing any of them. Origin of each file in [`docs/en/code-origin.md`](code-origin.md); result of the checks on the whole base in [`docs/en/data-checks.md`](data-checks.md).

## Validity (`validade.py`)

- Three states: `ok` (the number goes on screen), `indefinido` (undefined: there is no number; engine v1's "not computable", with the same reason) and `implausivel` (implausible: the number exists, but a check on the input data failed).
- Outside `ok`, a reason is mandatory in both languages. `None` and `NaN` are never used to signal absence.
- The bridge to engine v1 changes no value: it only translates the result.
- Percentage change only with a positive base; with a zero or negative base, the result is `indefinido`.

## Checks (`conferencias.py`)

- **Identity:** total assets = total liabilities and equity; assets and liabilities by their parts; the five income statement subtotals (gross profit, operating profit, profit before taxes, continuing operations and profit for the period); cash flow sum and cash flow balances.
- **Reconciliation:** cash flow closing balance against cash and cash equivalents on the balance sheet; cash flow opening balance against cash on the prior balance sheet. When the cash flow balance closes with cash and cash equivalents plus short-term investments (1.01.01 + 1.01.02), the result is "closes with broad cash", with a note, and does not count as a failure.
- **Not filled in:** total assets equal to zero in the column. In the product, every indicator that uses that column's balance sheet is "not computable", never computed with zero (`linhagem.aplicar_nao_preenchido`). Engine v1's value does not change; only what the product shows does.
- **Unusual sign:** negative total assets; nine negative balance accounts; negative revenue; positive cost of sales and selling and administrative expenses. Unusual is not impossible: a provision reversal larger than the year's expense can leave the expense positive.
- Tolerance of R$1,000 per term, for rounding only. A missing account does not become zero: "not applicable". The per-account codes (all CVM fixed accounts) apply to the non-financial chart of accounts; for the other charts, only total assets = total liabilities and equity and the cash flow identities.
- Each check runs on both DFP columns (ÚLTIMO and PENÚLTIMO).

## Lineage (`linhagem.py`)

- For each engine v1 signal of a company-year: the document (DFP, version, filing date, open data or ENET, address and file hash), the formula, the case's values and the evidence.
- Each piece of evidence is a DFP line: statement, column, code, official description, value in reais and the line in the source file (the CSV inside the open data ZIP, or the cached ENET file).
- Transformations recorded: scaling to reais, interest paid moved to financing, depreciation from cash flow lines found by text, combined depreciation, de-duplication, ENET route.
- The signal value comes from engine v1; the sheet only describes the path.

## Confidence (`confianca.py`)

- Five criteria, each `ok`, `atencao` (attention) or `problema` (problem), with a reason in PT and EN: source, completeness, consistency (checks on the statements the signal uses: an identity failure or an unfilled balance sheet is a problem; a reconciliation that does not close and an unusual sign need attention; broad cash is not a failure), timeliness and method (what study 1 showed, with the numbers read from the study output).
- Level by a written rule, with no numeric score: `baixa` (low) if any criterion has a problem; `media` (medium) if any needs attention; otherwise `alta` (high).
- Given the study 1 result, the method criterion is at attention for every engine v1 signal. That is why no engine v1 signal reaches high confidence: it is a direct consequence of the published result, not an adjustment.
