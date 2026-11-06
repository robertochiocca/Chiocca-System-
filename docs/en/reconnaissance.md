Pre-registration frozen at commit 6cc1d5f5d365e4923ec422d34130f5977b0ac7c3, pushed to GitHub on 2026-11-04 at 23:11:52 (Brasília time; 2026-11-05 02:11:52 UTC), before any data was downloaded.

# Reconnaissance of CVM open data (Phase 0)

*English version of [`docs/reconhecimento.md`](../reconhecimento.md). Same numbers; if the two ever differ, the Portuguese file prevails. Official CVM account and sector names are kept in Portuguese.*

Consulted on 2026-11-05, from 02:12 UTC onwards (2026-11-04, 23:12 in Brasília). File URLs and hashes are in [`sources.md`](sources.md).

**How Phase 0 was done**

- Structure only. No signal, ratio or M-score was computed. No script loaded the `VL_CONTA` column: account values never entered memory. Only exception, authorized on 2026-11-06: the ENET HTML-route test (part 7.2) loaded `VL_CONTA` only for three companies outside the ground truth and the candidates, to compare in memory, and printed only counts.
- In parts 1 to 4, all rows of these CVM codes were dropped before any analysis: 8087 (Lojas Americanas SA), 20990 (Americanas S.A.), 24180 (IRB-Brasil Resseguros) and 22837 (Drogarias Americanas SA, dropped only because its name contains "Americanas"). Americanas and IRB metadata were opened only later, with authorization, in part 5.
- The figures below are structure counts (companies, rows, presence of accounts) and come from the scripts in [`scripts/fase0/`](../../scripts/fase0/).
- Downloaded files stayed outside the repository.

## 1. What was confirmed

### 1.1 Files and years

- **DFP:** one zip per year, `dfp_cia_aberta_AAAA.zip`, from **2010 to 2026**. The first year is **2010**; the last complete year is **2025**. The 2026 file has 9 filings, all for fiscal years that do not end on December 31.
- **Contents of each zip:** the filing index (`dfp_cia_aberta_AAAA.csv`), BPA, BPP, DRE, DRA, DFC_MD, DFC_MI, DMPL and DVA, each in a consolidated (`_con`) and an individual (`_ind`) version, plus `parecer` (auditor's report). The `composicao_capital` file is present in 2023 and 2025 but not in 2010 or 2019 (other years were not checked).
- **CVM regenerates the files.** According to the server listing, the 2010–2019 zips were generated on 2024-08-05, the 2020 zip on 2024-12-29, the 2021 zip on 2025-12-28 and the 2022–2026 zips on 2026-11-01. Content downloaded today may differ from content downloaded on another date, which is why the hashes are in `sources.md`.
- **Data dictionary:** `meta_dfp_cia_aberta_txt.zip`, with 11 files (index, BPA, BPP, DFC_MD, DFC_MI, DMPL, DRA, DRE, DVA, capital composition and auditor's report).
- **Consolidated and individual:** many companies file only individual statements.

  | DFP | Companies with an individual income statement | With a consolidated income statement | Individual only | Consolidated only |
  | --- | --- | --- | --- | --- |
  | 2012 | 652 | 361 | 298 | 7 |
  | 2019 | 663 | 382 | 284 | 3 |
  | 2023 | 725 | 472 | 258 | 5 |

- **Statement of cash flows:** most companies use the indirect method (`DFC_MI`). The direct method (`DFC_MD`) appears in 186 consolidated company-years and 367 individual company-years, from 2010 to 2025.

### 1.2 Columns

| Column | Where | Meaning (dictionary) | What the files show |
| --- | --- | --- | --- |
| `CD_CVM`, `CNPJ_CIA`, `DENOM_CIA` | all | CVM code, CNPJ (company tax ID) and company name | |
| `DT_REFER` | all | reference date of the filing | usually December 31; 0 to 21 company-years per year have another date |
| `VERSAO` | all | filing version | ranges from 1 to 9 in the index; see 1.3 |
| `DT_RECEB` | **index only** | date the filing was received (AAAA-MM-DD) | one date per version |
| `ID_DOC`, `LINK_DOC` | index only | filing identifier and download address | each version has its own; the link points to CVM's ENET system (`rad.cvm.gov.br/ENETCONSULTA/frmDownloadDocumento.aspx?CodigoInstituicao=…&NumeroSequencialDocumento=…`) |
| `CATEG_DOC` | index only | filing category | always "DFP" |
| `ORDEM_EXERC` | statements | order of the fiscal year | only two values: `ÚLTIMO` (reference year) and `PENÚLTIMO` (prior year, comparative). The dictionary does not list the values; checked in BPA, DRE and DFC_MI, consolidated and individual, from 2010 to 2025 |
| `ESCALA_MOEDA` | statements | monetary scale | `MIL` (thousands; 4,585,846 rows) and `UNIDADE` (units; 240,898 rows), in the same files. A filing never mixes two scales (0 out of 50,461). The dictionary does not list the values |
| `MOEDA` | statements | currency | only `REAL`, in the same files |
| `GRUPO_DFP` | statements | statement name and aggregation level | |
| `CD_CONTA`, `DS_CONTA` | statements | account code and description | dot hierarchy: `3.04.04` is the parent of `3.04.04.01` |
| `ST_CONTA_FIXA` | statements | whether the account is a fixed (standard) account (S/N) | present in every year, including the 2010 files |
| `DT_INI_EXERC`, `DT_FIM_EXERC` | statements | start and end of the fiscal year | `DT_INI_EXERC` does not exist in BPA or BPP |
| `COLUNA_DF` | DMPL only | statement column | |
| `VL_CONTA` | statements | account value | not read |

### 1.3 Versions: the statement files only carry the latest one

- **The index keeps every version.** Each version is one row, with its own `ID_DOC`, `LINK_DOC` and `DT_RECEB`. From 2010 to 2026 there are 10,825 filings at version 1, 2,412 at version 2, 537 at version 3 and 168 at versions 4 to 9.
- **The statements carry a single version, the latest.** From 2010 to 2025, no company-year has more than one version in BPA, DRE or the statement of cash flows. In 100% of cases, the file's version is the highest version in the index.
- **Consequence:** values of earlier versions are not in the open-data files. When a company refiled its DFP after the cut-off date, the figure in the file is not the one that was public at the cut-off date.

  Company-years with a consolidated DFP (BPA_con), excluding Americanas and IRB. The cut-off date is April 30 of the year after the file's year.

  | DFP | Company-years | Latest version received after the cut-off | Of which, version 1 received by the cut-off |
  | --- | --- | --- | --- |
  | 2010 | 370 | 139 | 70 |
  | 2011 | 367 | 117 | 63 |
  | 2012 | 361 | 89 | 41 |
  | 2013 | 352 | 67 | 32 |
  | 2014 | 345 | 78 | 27 |
  | 2015 | 340 | 65 | 32 |
  | 2016 | 337 | 72 | 34 |
  | 2017 | 337 | 64 | 27 |
  | 2018 | 337 | 73 | 35 |
  | 2019 | 383 | 127 | 24 |
  | 2020 | 439 | 95 | 25 |
  | 2021 | 464 | 63 | 28 |
  | 2022 | 475 | 80 | 52 |
  | 2023 | 473 | 66 | 36 |
  | 2024 | 465 | 52 | 26 |
  | 2025 | 438 | 30 | 10 |

  The last column counts company-years in which a version was public at the cut-off date but the file carries a later version. The difference between the last two columns is company-years with no version filed by the cut-off date.
- **Earlier versions at CVM:** I ran a test with a company outside the ground truth (DFP 2019, versions 1 and 2). Each version's `LINK_DOC` returned its own zip package, containing a `<6-digit CD_CVM><AAAAMMDD>04<2-digit version>.dfp` file, an `AnexoDocumento.xml` and a PDF. The contents of the `.dfp` file were not confirmed (see part 3).

### 1.4 Catalog account codes, for non-financial companies

The non-financial chart of accounts was identified by account 3.01, "Receita de Venda de Bens e/ou Serviços". The base is 5,937 consolidated and 10,074 individual company-years in BPA, BPP and DRE, and 5,774 and 9,715 in DFC_MI, from 2010 to 2025.

**Every catalog code was confirmed.** Each one is a fixed CVM account (`ST_CONTA_FIXA = S`), appears in 100% of the chart's company-years and has the same description from 2010 to 2025.

| Catalog variable | Code | Description at CVM |
| --- | --- | --- |
| ativo_total | 1 | Ativo Total |
| ativo_circulante | 1.01 | Ativo Circulante |
| caixa_equivalentes | 1.01.01 | Caixa e Equivalentes de Caixa |
| aplicacoes_financeiras | 1.01.02 | Aplicações Financeiras |
| contas_a_receber | 1.01.03 | Contas a Receber |
| estoques | 1.01.04 | Estoques |
| ativo_nao_circulante | 1.02 | Ativo Não Circulante |
| investimentos | 1.02.02 | Investimentos |
| imobilizado | 1.02.03 | Imobilizado |
| intangivel | 1.02.04 | Intangível |
| passivo_circulante | 2.01 | Passivo Circulante |
| fornecedores | 2.01.02 | Fornecedores |
| ir_csll_a_pagar | 2.01.03 → **2.01.03.01.01** | Obrigações Fiscais → Imposto de Renda e Contribuição Social a Pagar (see 2.2) |
| emprestimos_cp | 2.01.04 | Empréstimos e Financiamentos |
| passivo_nao_circulante | 2.02 | Passivo Não Circulante |
| emprestimos_lp | 2.02.01 | Empréstimos e Financiamentos |
| patrimonio_liquido | 2.03 | Patrimônio Líquido (individual) / Patrimônio Líquido Consolidado (consolidated) |
| receita_liquida | 3.01 | Receita de Venda de Bens e/ou Serviços |
| custo_vendas | 3.02 | Custo dos Bens e/ou Serviços Vendidos |
| resultado_bruto | 3.03 | Resultado Bruto |
| despesas_vendas | 3.04.01 | Despesas com Vendas |
| despesas_gerais_adm | 3.04.02 | Despesas Gerais e Administrativas |
| outras_receitas_operacionais | 3.04.04 | Outras Receitas Operacionais |
| ebit | 3.05 | Resultado Antes do Resultado Financeiro e dos Tributos |
| receitas_financeiras | 3.06.01 | Receitas Financeiras |
| despesas_financeiras | 3.06.02 | Despesas Financeiras |
| ir_csll_corrente | 3.08.01 | Corrente |
| lucro_operacoes_continuadas | 3.09 | Resultado Líquido das Operações Continuadas |
| lucro_liquido | 3.11 | Lucro/Prejuízo do Período (individual) / Lucro/Prejuízo Consolidado do Período (consolidated) |
| caixa_operacional | 6.01 | Caixa Líquido Atividades Operacionais (DFC_MI) |

Other useful fixed accounts, checked the same way: 2 "Passivo Total" (see 2.6), 3.07 "Resultado Antes dos Tributos sobre o Lucro", 6.01.01 "Caixa Gerado nas Operações", 6.02 and 6.03 (investing and financing cash flows). From 2010 to 2013 there are a few malformed descriptions: account 1 appears as "Ativo" in 6 company-years and as "A" in 4.

### 1.5 How to identify financial companies

- **Company registry (`cad_cia_aberta.csv`):** 2,678 rows for 2,567 CVM codes (some companies have more than one row). Useful fields:
  - `SETOR_ATIV`: sector of activity, **current only**;
  - `SIT`: ATIVO 754, CANCELADA 1,916, SUSPENSO(A) - DECISÃO ADM 8;
  - `DT_CANCEL` and `MOTIVO_CANCEL`.
- **Finance-related sectors in the registry** (number of rows): Bancos 115, Securitização de Recebíveis 141, Arrendamento Mercantil 73, Seguradoras e Corretoras 24, Intermediação Financeira 10, Crédito Imobiliário 6, Bolsas de Valores/Mercadorias e Futuros 4, Factoring 1. There are also the holding companies: "Emp. Adm. Part. - Intermediação Financeira" 16, "- Seguradoras e Corretoras" 6, "- Crédito Imobiliário" 5, "- Securitização de Recebíveis" 4, "- Arrendamento Mercantil" 2, "- Bancos" 1 and "Emp. Adm. Part.-Bolsas de Valores/Mercadorias e Futuros" 1.
- **Sector year by year:** the Registration Form (FCA, `fca_cia_aberta_geral_AAAA.csv`, 2010 to 2026) gives `Setor_Atividade` for each year, plus the day and month the fiscal year ends.
- **Delisted companies remain in the DFP open data.** Of the 661 companies in DFP 2010, 314 are delisted today; in DFP 2023, 97 of 730. In the years checked (2010, 2015, 2019 and 2023), 5 to 11 CVM codes per year appear in the DFP but not in the registry.
- **Three charts of accounts in the DFP**, identified by the description of account 3.01:

  | Chart | Description of account 3.01 | Company-years (con + ind, 2010–2025) |
  | --- | --- | --- |
  | non-financial | Receita de Venda de Bens e/ou Serviços | 16,008 |
  | bank | Receitas da (or de) Intermediação Financeira | 905 |
  | insurer | Receitas das Operações (49) or Receitas das Atividades Seguradoras/Resseguradoras (6) | 55 |

- **The registry sector and the chart of accounts do not always match.** Distinct companies from 2010 to 2025. Banks' account 3.01 has two spellings ("da" and "de"), and a company that used both is counted twice:
  - Bancos: 56 on the bank chart and 2 on the non-financial chart;
  - Arrendamento Mercantil: 13 on the bank chart;
  - Securitização de Recebíveis: 124 on the non-financial chart, 12 on the bank chart and 1 on the insurer chart;
  - Seguradoras e Corretoras: 3 on the non-financial chart and 1 on the insurer chart;
  - Emp. Adm. Part. - Seguradoras e Corretoras: 4 on the non-financial chart and 2 on the insurer chart;
  - Intermediação Financeira: 6 on the non-financial chart;
  - Emp. Adm. Part. - Intermediação Financeira: 9 on the non-financial chart;
  - Crédito Imobiliário, Bolsas and Factoring: 1 each, on the non-financial chart.

### 1.6 Amendments 2 and 4 for financial companies

The search followed Amendment 2: text in `DS_CONTA`, ignoring case and accents. Figures are company-year counts from 2010 to 2025, consolidated and individual combined.

**Bank chart (905 company-years)**

- **Numerator, "outras receitas operacionais":** found in 904. It sits in fixed account **3.04.05** (712 rows) or **3.04.06** (193 rows): there are two layouts, and in one of them 3.04.05 is "Despesas Tributárias". It also appears in non-fixed subaccounts: 3.04.05.xx (94), 3.04.06.xx (24) and 3.04.04.xx (2).
- **Text in both the parent account and a subaccount:** 113 company-years. Amendment 4's rule can be applied through the code, because the hierarchy comes from the dots. More than one row matches in 121 company-years.
- **Denominator, "resultado antes dos tributos sobre o lucro":** found in 432, in fixed account **3.05**. Missing in 473 (see 2.3).
- **Old layout, individual statements only (473 company-years):** 3.04 Outras Despesas/Receitas Operacionais, 3.05 Resultado Operacional, 3.06 Resultado Não Operacional, **3.07 Resultado Antes Tributação/Participações**. All consolidated bank income statements (311) follow the layout with 3.05. Cases without a denominator fall over time: 40 of 59 in 2010, 38 of 56 in 2019, 17 of 54 in 2020 and 5 of 36 in 2025.

**Insurer chart (55 company-years)**

- **Denominator:** fixed account **3.09** "Resultado Antes dos Tributos sobre o Lucro", in 55 of 55.
- **Numerator:** found in only 4, in non-fixed subaccounts 3.04.08.xx, under "Outras Despesas Administrativas". The chart's fixed account is **3.05 "Outras Receitas e Despesas Operacionais"** (55 of 55), which does not contain the exact text "outras receitas operacionais" (see 2.4).

**Financial-sector companies on the non-financial chart (1,395 company-years)**

- Numerator in fixed account 3.04.04 "Outras Receitas Operacionais" (100%).
- Denominator in fixed account 3.07 "Resultado Antes dos Tributos sobre o Lucro": exactly 1 row in 1,388 company-years and more than one in 7.
- Text in both the parent account and a subaccount: 131 company-years.

**Similar descriptions that Amendment 2's text does not match** (recorded, no proposal): "Outras Receitas e Despesas Operacionais" (insurers, 55 company-years), "Outras Receitas (Despesas) Operacionais" and "Outras Receitas / (Despesas) Operacionais" (bank subaccounts), "Outras Receitas Não Operacionais", and a typo ("operacioanais").

### 1.7 Statement of cash flows lines found by text, for non-financial companies (DFC_MI)

Catalog patterns and sections, with accents removed. None of these lines is a fixed account: they are subaccounts each company creates.

| Line | Catalog pattern | Found (con / ind) | Notes |
| --- | --- | --- | --- |
| depreciation | "deprecia" in 6.01.01 | 93.2% / 74.2% | In 10,724 of the 12,589 company-years with the line, it is **only combined** with amortization ("Depreciação e Amortização" and variants). Only 1,865 have a depreciation-only line |
| interest paid | "juros pagos" in 6.01 or 6.03 | 40.0% / 29.5% | Rows in 6.01 (4,702), 6.03 (1,808) and 6.02 (12): companies choose the section, as the catalog anticipated. Another 2,951 company-years have variants the pattern misses ("pagamento de juros", "pagamentos de juros") |
| capex | "aquisição de imobilizado" or "intangível" in 6.02 | 75.6% / 59.3% | 532 company-years have variants it misses ("aquisições de imobilizado", "adições ao imobilizado"). The "intangível" pattern alone may also match sales of intangible assets (not verified) |
| dividends | "dividendos" or "juros sobre o capital próprio" in 6.03 | 74.1% / 61.1% | 290 company-years only have "juros sobre capital próprio", without the "o", and are missed |
| income taxes paid | "imposto de renda e contribuição social pagos" in 6.01 | 37.1% / 28.1% | 1,190 company-years have variants it misses ("imposto de renda e contribuição social pago", "IR e CS pagos", "pagamento de imposto de renda") |
| issuances | "captação", "emissão de ações" or "debêntures" in 6.03 | 60.8% / 52.2% | "debêntures" also matches **repayment or amortization** lines for debentures, in 3,966 company-years |

Note, with no proposed change: the DVA (value added statement) has a fixed account "Depreciação, Amortização e Exaustão" (7.04.01 in most cases; 7.05.01 or 7.07.01 in other charts). It combines depreciation and amortization.

## 2. What differs from the catalog or the amendments

Recorded only. No formula, cut-off or rule was changed.

1. **Versions.** The PROMPT (Phase 1) assumes it is possible to "keep every version" and build `como_era` from open data. The statement files carry only the latest version (1.3). For company-years refiled after the cut-off, the point-in-time figure is not in the open data. Possible source: each version's package in CVM's ENET system, through the index's `LINK_DOC` (not confirmed, see 3.2).
2. **ir_csll_a_pagar.** The catalog says "2.01.03 (subconta de IR e CSLL, localizar por texto)". A fixed account exists: **2.01.03.01.01 "Imposto de Renda e Contribuição Social a Pagar"**, present in 100% of non-financial company-years, so the text search is not needed.
3. **Amendment 2, bank denominator.** In the banks' old layout (473 company-years, all individual), the line "resultado antes dos tributos sobre o lucro" does not exist; the closest is 3.07 "Resultado Antes Tributação/Participações". Under Amendment 2, these company-years are "not computable".
4. **Amendment 2, insurer numerator.** On the insurer chart, the text "outras receitas operacionais" appears in only 4 of 55 company-years. The chart's line is 3.05 "Outras Receitas e Despesas Operacionais". Under Amendment 2, the other 51 are "not computable", and the amendment itself says that if the lines do not exist, the formula changes through a new amendment before any calculation. I did not check which chart IRB uses (see 3.3).
5. **Amendment 4.** The cases it resolves exist: the text is in both the parent account and a subaccount in 113 bank company-years and in 131 company-years of financial-sector companies on the non-financial chart. Through the code, the rule can be applied.
6. **Catalog text patterns for the statement of cash flows.** They miss common variants (figures in 1.7). The "debêntures" pattern also catches repayments. These patterns live in the catalog, not in the pre-registration.
7. **Depreciation.** A depreciation-only line exists in few companies. In most, the statement of cash flows shows "depreciação e amortização" together. This is not a discrepancy: the pre-registration (4.1) already decides to use the total and flag the company-year. But the flag will apply to about 85% of the company-years in which the line is found.
8. **Naive baseline rule (section 7).** In the DFP, account 2 "Passivo Total" has account 2.03 "Patrimônio Líquido" as a subaccount: it is liabilities plus shareholders' equity, which by the accounting identity equals total assets. Read that way, the ratio "passivo total ÷ ativo total" equals 1 for every company. The bank chart has a different liability structure, not checked.
9. **Scale.** `ESCALA_MOEDA` mixes `MIL` and `UNIDADE` across companies, and the catalog does not mention it. It is not a study decision; the code has to normalize it.

## 3. What I could not confirm or needs your decision

1. **Original versions for the ground-truth years.** To know whether Americanas (2020 and 2021) and IRB (2018 and 2019) refiled their DFP after the cut-off, the index rows for those companies must be opened: only versions and filing dates, no values. Not done. I need your authorization.
2. **Contents of the old-version packages in ENET.** Both test downloads arrived truncated in all three attempts, despite an HTTP 200 response. CVM's server also once returned the error "could not be activated". I saw the file names in the package but did not open the `.dfp` file.
3. **IRB's chart of accounts.** I did not open IRB's structure. I can check only the account labels, with no values, if you authorize it.
4. **Which sectors are "financial companies".** The pre-registration says "bancos, seguradoras, resseguradoras e demais instituições financeiras". The registry has Securitização de Recebíveis, Arrendamento Mercantil, Crédito Imobiliário, Factoring, Bolsas and the "Emp. Adm. Part. - …" holding companies, and the sector does not always match the chart of accounts (1.5). It also remains to say whether the registry sector (current only) or the FCA sector for each year applies.
5. **Consolidated or individual.** Neither the pre-registration nor the PROMPT says which to use. Between 258 and 298 companies per year have only individual statements, and the banks' old layout appears only in individual statements.
6. **Where year t−1 of the ratios comes from.** At the cut-off date for year t, the figures for t−1 are in two places: as `PENÚLTIMO` in the DFP for t, possibly restated, and as `ÚLTIMO` in the DFP for t−1, the original. The pre-registration does not say which to use. This also sets the first computable year: 2010 if t−1 comes from `PENÚLTIMO` in DFP 2010; 2011 if it comes from the DFP for t−1.
7. **Fiscal years that do not end on December 31** (0 to 21 company-years per year). It is not stated how to apply "30 de abril do ano seguinte": the year after `DT_REFER` or another rule. The table in 1.3 used the file's year.
8. **Company-years with no version filed by the cut-off.** Read literally, section 3 ("usar só a versão que já era pública na data de corte") leaves them out. Please confirm.
9. **Companies with no revenue in the year** (exclusion in section 2). This depends on the value of account 3.01, so it can only be identified in Phase 1.
10. **Direct-method statement of cash flows.** I did not check account 6.01 or the text lines in `DFC_MD` (186 consolidated and 367 individual company-years).
11. **Ground-truth CVM code.** The registry has two codes linked to the Americanas case: 8087 (Lojas Americanas SA) and 20990 (Americanas S.A. - Em Recuperação Judicial). IRB is 24180. The ground truth's `cd_cvm` is still empty, and which code goes in is your decision.
12. **English version.** This document and `fontes.md` are only in Portuguese for now.

## 4. Amendment 5 appendix (recorded on 2026-11-05, before the freeze)

Amendment 5 requires this document to include the exact list of financial sectors and the final text patterns for the statement of cash flows. Both are fixed from here on: changing either requires a new amendment. The counts in this part are structure only and come from `scripts/fase0/grupos.py` and `scripts/fase0/dfc.py`.

### 4.1 Who is a financial company

**Rule**, decided by Roberto on 2026-11-05 when closing the list: the sector defines the candidate financial company, and the chart of accounts used in the DFP decides the group. The rule uses only file structure, never values.

1. **Sector:** the one in the FCA for that same year (`Setor_Atividade`). If there is no FCA for that year, the registry sector (`SETOR_ATIV`) applies. When the year's FCA has more than one version, the scripts use the year's latest version.
2. **Candidate financial company:** a company whose sector has one of these exact names.
   - Bancos
   - Intermediação Financeira
   - Arrendamento Mercantil
   - Seguradoras e Corretoras
   - Crédito Imobiliário
   - Emp. Adm. Part. - Bancos
   - Emp. Adm. Part. - Intermediação Financeira
   - Emp. Adm. Part. - Arrendamento Mercantil
   - Emp. Adm. Part. - Seguradoras e Corretoras
   - Emp. Adm. Part. - Crédito Imobiliário
3. **Group:** a candidate goes to the **financial** group if the DFP used (consolidated when available; otherwise, individual) is on the bank chart of accounts (account 3.01 "Receitas da Intermediação Financeira" or "Receitas de Intermediação Financeira") or the insurer chart (3.01 "Receitas das Operações" or "Receitas das Atividades Seguradoras/Resseguradoras"). If the DFP uses the non-financial chart (3.01 "Receita de Venda de Bens e/ou Serviços"), the company-year goes to the **non-financial** group. This also applies to insurance brokers and to the holding companies on the list.
4. **Not candidates:** Securitização de Recebíveis, Emp. Adm. Part. - Securitização de Recebíveis, Factoring, Bolsas de Valores/Mercadorias e Futuros, Emp. Adm. Part.-Bolsas de Valores/Mercadorias e Futuros, Cooperativas and all other sectors.

**How the rule splits the base:** company-years from 2010 to 2025, excluding Americanas and IRB, one DFP per company-year.

| | Bank chart | Insurer chart | Non-financial chart |
| --- | --- | --- | --- |
| Candidate | 565 → financial | 27 → financial | 258 → non-financial |
| Not a candidate | 49 → non-financial | 1 → non-financial | 9,884 → non-financial |

The sector came from that year's FCA in 10,195 company-years, from the registry in 571, and was missing in 18.

**Note, no proposal:** 50 non-candidate company-years use the bank or insurer chart. They are 30 from Securitização de Recebíveis, 16 from Emp. Adm. Part. - Sem Setor Principal, 3 with no sector and 1 from Emp. Adm. Part. - Telecomunicações. Under the rule they stay in the non-financial group, where the signals use accounts that chart does not have and tend to come out "not computable".

### 4.2 Final text patterns for the statement of cash flows

**How they apply**

- The text compared is `DS_CONTA` in lower case, without accents and with surrounding spaces trimmed.
- The line must be in the stated section (prefix of `CD_CONTA`), contain at least one term from each "Contains" group and no term from "Does not contain".
- Terms are word fragments: "aquisic" matches "aquisição" and "aquisições".
- If a parent account and a subaccount both match, only the parent counts, as in Amendment 4, so the same value is not added twice.
- The patterns apply to the indirect-method statement of cash flows (`DFC_MI`). `DFC_MD` was not checked.

| Line | Section | Contains (one term from each group) | Does not contain | Use |
| --- | --- | --- | --- | --- |
| depreciation | 6.01.01 | "deprecia" | — | DEPI, in the MVP. Matching lines are summed; if any also contains "amortiza" or "exaust", the company-year is flagged (pre-registration 4.1 and Amendment 5) |
| interest paid | 6.01 and 6.03 | "juros" · "pago", "pagos", "pagamento" or "pagamentos" | "capital proprio", "recebid" | standardize operating cash flow (pre-registration 4.1), in the MVP |
| capex | 6.02 | "aquisic", "adic", "compra" or "investimento" · "imobilizado" or "intangivel" | "venda", "alienac", "baixa", "recebimento" | phase 2 |
| dividends paid | 6.03 | "dividendo" or "capital proprio" | "recebid" | phase 2 |
| income taxes paid | 6.01 | "imposto de renda", "ir e cs", "irpj", "ir/cs" or "ir/csll" · "pago", "pagos", "pagamento" or "pagamentos" | — | phase 3 |
| issuances | 6.03 | "captac", "emiss" or "ingress" | "pagamento", "amortiza", "liquida", "resgat" | phase 2; Amendment 5 rule |

**Coverage:** non-financial company-years with `DFC_MI`, 5,774 consolidated and 9,716 individual.

| Line | Found (con / ind) | Before, with the catalog pattern (con / ind) |
| --- | --- | --- |
| depreciation | 93.2% / 74.2% | 93.2% / 74.2% |
| interest paid | 67.8% / 54.0% | 40.0% / 29.5% |
| capex | 77.3% / 60.6% | 75.6% / 59.3% |
| dividends paid | 76.1% / 62.8% | 74.1% / 61.1% |
| income taxes paid | 57.3% / 43.4% | 37.1% / 28.1% |
| issuances | 63.3% / 52.1% | 60.8% / 52.2% |

- A parent account and a subaccount never matched at the same time in these six lines.
- **Depreciation:** of the 12,589 company-years in which the line is found, 11,260 are flagged because the sum includes amortization or depletion.
- **Interest paid in 6.02:** 12 such rows appeared in Phase 0; they stay out because the section is neither 6.01 nor 6.03.
- **Issuances:** "gastos com emissão de ações" is an issuance cost, that is, an outflow, but it passes Amendment 5's rule, because "gasto" and "custo" are not among the outflow words. This happens in 2,473 company-years. Issuances are not part of the MVP.

## 5. Authorizations of 2026-11-05 and results (after the freeze)

Done after the freeze commit `99237fcb9cd52ca3a445532f1cfe9a410eef6c92` (Amendments 5 and 6), with Roberto's authorization to open only Americanas and IRB metadata. No value was read. Scripts: `autorizados.py`, `setores.py`, `emenda5.py` and `enet_teste.py`.

### 5.1 Americanas' CNPJ

- The CNPJ 00.776.574/0006-60, given in the material fact notice of 2024-07-16, **does not appear exactly** in either the registry or the DFP index from 2010 to 2026.
- That CNPJ's root (00.776.574) is the one of CVM code **20990**, Americanas S.A. - Em Recuperação Judicial, registered with CNPJ 00.776.574/0001-56. The first eight digits of a CNPJ identify the company; the ending identifies the establishment.
- The 2021 DFP was filed under code 20990 (version 1, on 2022-02-24).
- Code 8087 (Lojas Americanas SA, CNPJ 33.014.556/0001-96) was cancelled on 2021-12-10, through a merger, and has no 2021 DFP.
- The registry does not always use the /0001 ending: Via Varejo (code 6505) is registered with CNPJ 33.041.260/0652-90.
- Amendment 5 says to use the code "of the company with CNPJ 00.776.574/0006-60". By the root, it is 20990. Since the exact CNPJ is not in CVM's base, I need your confirmation before any change to the ground truth, which was not changed.

### 5.2 DFP versions from 2017 to 2022

Cut-off date under Amendment 5: last day of the fourth month after the fiscal year-end (all fiscal years below end on December 31).

| Company (code) | DFP | Versions (filing date) | Cut-off | Point-in-time version | Version in open data |
| --- | --- | --- | --- | --- | --- |
| Americanas S.A. (20990) | 2017 | 1 (2018-03-07) | 2018-04-30 | 1 | 1 |
| | 2018 | 1 (2019-03-20) | 2019-04-30 | 1 | 1 |
| | 2019 | 1 (2020-02-20), 2 (2020-02-21) | 2020-04-30 | 2 | 2 |
| | 2020 | 1 and 2 (2021-03-04) | 2021-04-30 | 2 | 2 |
| | 2021 | 1 (2022-02-24) | 2022-04-30 | 1 | 1 |
| | 2022 | 1 (2023-11-16) | 2023-04-30 | none | 1 |
| Lojas Americanas (8087) | 2017 | 1 (2018-03-07), 2 (2018-03-14) | 2018-04-30 | 2 | 2 |
| | 2018 | 1 (2019-03-20) | 2019-04-30 | 1 | 1 |
| | 2019 | 1 (2020-02-20) | 2020-04-30 | 1 | 1 |
| | 2020 | 1 (2021-03-04) | 2021-04-30 | 1 | 1 |
| IRB (24180) | 2017 | 1 (2018-02-08) | 2018-04-30 | 1 | 1 |
| | 2018 | 1 (2019-02-07), 2 and 3 (2019-03-07), 4 (2019-03-08) | 2019-04-30 | 4 | 4 |
| | 2019 | 1 (2020-02-18), 2 and 3 (2020-06-30), 4 (2020-07-07), 5 (2021-02-18) | 2020-04-30 | 1 | **5** |
| | 2020 | 1 (2021-02-18) | 2021-04-30 | 1 | 1 |
| | 2021 | 1 (2022-02-24) | 2022-04-30 | 1 | 1 |
| | 2022 | 1 (2023-03-08), 2 (2023-03-09), 3 (2023-03-21) | 2023-04-30 | 3 | 3 |

- **Americanas 2021 was not refiled.** There is a single version, filed before the cut-off; the open-data version is the point-in-time one.
- **IRB 2019 was refiled after the cut-off.** Version 1 came out on 2020-02-18, before the 2020-04-30 cut-off; versions 2 to 5 came out between 2020-06-30 and 2021-02-18. The open data carry version 5. Under Amendment 5, the point-in-time version is version 1 and must come from ENET (see 5.4). Version 1 was filed after the case's public date (2020-02-10), as Amendment 3 already records.
- **IRB 2018**, used in Amendment 3's secondary metric: all four versions were filed by the cut-off, and the open-data one (version 4) is the point-in-time version.
- **Americanas 2022:** the only version was filed after the cut-off, so there is no point-in-time version. It comes after the case's public date.

### 5.3 IRB account labels (no values)

- IRB uses the **insurer chart** (3.01 "Receitas das Operações") in every DFP from 2017 to 2022, consolidated and individual. The structure is the same every year.
- Amendment 5 denominator: 3.09 "Resultado Antes dos Tributos sobre o Lucro".
- Numerator under Amendment 5 (lines that start with "outras receitas", with Amendment 4's parent-account rule): five fixed accounts.
  - 3.01.01.02 "Outras Receitas de Seguros"
  - 3.01.02.02 "Outras Receitas de Resseguros"
  - 3.01.03.03 "Outras Receitas de Prev. Complementar"
  - 3.01.04.03 "Outras Receitas de Capitalização"
  - 3.05 "Outras Receitas e Despesas Operacionais"
- The first four sit inside operating revenue (3.01). See 5.6, item 1.
- Balance sheet: 2.01 Passivo Circulante, 2.02 Passivo Não Circulante and 2.03 Patrimônio Líquido Consolidado. Amendment 5's naive baseline rule works for IRB.

### 5.4 ENET

- **Old-version package: it does not arrive whole.** In every attempt on 2026-11-05, overnight (02:00 UTC) and in the evening (20:00–21:00 UTC), with curl and with `scripts/fase0/enet_teste.py`, always with filings of companies outside the ground truth, no package arrived whole.
  - The transfer stops at around 22 to 25 seconds ("transfer closed with outstanding read data remaining", "IncompleteRead"), or the server closes the connection without a response.
  - Resuming the download from where it stopped does not work.
  - This session's proxy recorded no failure. The cut-off seems to come from CVM's server.
- **HTML view: it arrives whole.** Each filing's lookup page (`frmGerenciaPaginaFRE.aspx`, by filing number) responds with HTTP 200, about 29 KB, and carries the menu of statements (balance sheet, income statement and others). I did not check whether each statement's tables load completely.
- **Consequence for Amendment 5:** the main rule ("buscar no ENET a versão mais recente entregue até o corte") does not work today through the package download. Before Phase 1, the HTML view still needs to be tested. If it also fails, those company-years become "versão da época indisponível" (point-in-time version unavailable). The table in part 1.3, column "Of which, version 1 received by the cut-off", gives the scale for consolidated filings. IRB 2019 is one of these cases.

### 5.5 Sector names in the registry and the FCA

- The full list, with the number of companies in each source, is in Appendix A.
- Names that appear only in the FCA: Cooperativas and "Serviços médicos" (lower-case "m"; the registry uses "Serviços Médicos").
- Names that appear only in the registry: Comércio Exterior, Emp. Adm. Participações, Outras Atividades Industriais, Serviços Diversos, Serviços Médicos and Serviços em Geral.
- The list of sectors classified as financial companies is the one in part 4.1, frozen.
- The final text patterns for the statement of cash flows are the ones in part 4.2, also frozen.

### 5.6 What, in Amendment 5, does not match the file structure

Recorded only. Any change is your amendment.

1. **"Começa com 'outras receitas'" (starts with "outras receitas") catches more lines than the two it names.**
   - On the insurer chart, it catches the four "Outras Receitas de Seguros / Resseguros / Prev. Complementar / Capitalização", which are parts of operating revenue: 49 to 55 company-years from 2010 to 2025, plus every year of IRB.
   - On the bank chart, it catches "Outras Receitas Financeiras" (3.01.03) and "Outras Receitas" (3.01.02 and 3.01.07), inside financial intermediation revenue, plus "Outras Receitas e Despesas Não Operacionais" (3.08.01) and "Outras Receitas (Despesas) Administrativas".
   - The amendment says "Vale para 'Outras Receitas Operacionais' e 'Outras Receitas e Despesas Operacionais'", and it is not clear whether that sentence restricts the rule or only gives examples. At IRB the difference is large: under the broad reading, the numerator adds part of reinsurance revenue.
2. **Case and accents.** Amendment 2 said "sem diferenciar maiúsculas e acentos" (ignoring case and accents). Amendment 5 replaces Amendment 2's text and does not repeat this. The counts used Amendment 2's normalization. Please confirm.
3. **Naive baseline rule for banks.**
   - "Contas 2.01 + 2.02" works for non-financial companies and insurers (2.01 Passivo Circulante, 2.02 Passivo Não Circulante).
   - In the banks' IFRS layouts, 2.01 and 2.02 are types of financial liabilities (for example, "Passivos Financeiros ao Valor Justo através do Resultado" and "Passivos Financeiros ao Custo Amortizado"), and shareholders' equity sits in 2.07 or 2.08. There, 2.01 + 2.02 is not "liabilities without shareholders' equity".
   - In the old layout, 2.01 and 2.02 are Passivo Circulante and "Passivo Exigível a Longo Prazo"; there is also 2.03 "Resultados de Exercícios Futuros", and shareholders' equity sits in 2.05.
4. **Americanas' CNPJ:** see 5.1.
5. **Issuances:** "gastos com emissão de ações" passes the rule (part 4.2). Issuances are not part of the MVP.
6. **Non-candidates on a financial chart:** 50 company-years stay in the non-financial group (part 4.1).
7. **FCA with more than one version in the same year:** the scripts use the year's latest version. The point-in-time rule would suggest the version in force on the cut-off date. Please say which.

### 5.7 Status of the open items in part 3

| Item in part 3 | Status |
| --- | --- |
| 1. Versions for the ground-truth years | Answered in 5.2 |
| 2. ENET packages | They do not arrive whole (5.4) |
| 3. IRB's chart of accounts | Insurer (5.3) |
| 4. Which sectors are financial companies | Amendment 5 and part 4.1 |
| 5. Consolidated or individual | Amendment 5: consolidated when available; otherwise, individual |
| 6. Year t−1 | Amendment 5: the comparative (`PENÚLTIMO`) in the DFP for t; the first computable year becomes 2010 |
| 7. Fiscal year not ending on December 31 | Amendment 5: last day of the fourth month after the fiscal year-end |
| 8. No version by the cut-off | Amendment 5: left out and counted |
| 9. Companies with no revenue | Still for Phase 1, because it depends on values |
| 10. Direct-method statement of cash flows | Not checked yet |
| 11. Ground-truth CVM code | Amendment 5; see 5.1 |
| 12. English version | Done: [`docs/en/reconnaissance.md`](reconnaissance.md) and [`docs/en/sources.md`](sources.md) |

### 5.8 Correction

In parts 1.6 and 2, the banks' old layout appeared with 474 company-years; the correct figure is 473. The earlier count added twice a company-year that had two reference dates in the same file. The number of company-years without a denominator was already 473. Part 4 did not change.

## 6. Expanded ground truth (Amendment 6): candidates for review

> First search, of 2026-11-05. The full sweep of 2026-11-06 (part 7.1) changed the list and corrected some of the exclusions below.

- **File:** [`data/gabarito_candidatos.csv`](../../data/gabarito_candidatos.csv), with the same columns as the ground truth. `verificado_por` and `verificado_em` are empty. Nothing was added to `data/gabarito_casos.csv`.
- **How I collected them:** web searches for CVM decisions and material fact notices, on 2026-11-05, and reading the text of CVM decision extracts and votes (PDF) and of the material fact notices. No DFP value was opened. CVM codes and CNPJs came from the registry.
- **Result:** 18 rows, from 16 companies (Mundial and Inepar have two proceedings each).
  - CVM decision read in the primary source (14): Banco Panamericano, Taurus, OGX, OSX, Metalúrgica Duque, Mundial (two proceedings), Hércules, Teka, IGB Eletrônica, Tecnosolo, Schlosser, Brasil Brokers and Oi (2014 financial statements).
  - Fraud confirmed by the company itself in a material fact notice (1): Via Varejo.
  - Secondary source only, to be checked (3): Inepar (two proceedings) and Companhia Docas de Imbituba.
- **Points of attention**
  - `data_publica` is filled in 6 cases. In the other 12, the exact date was not in the documents read; each one's note gives the year the proceeding was opened, taken from the case number.
  - Banco Panamericano: the affected period (2007 to 2009) predates the DFP open data, which start in 2010. In practice, the case cannot be detected.
  - Via Varejo and Docas de Imbituba: empty period, because no document read gives the fiscal years.
  - Mundial (2016 proceeding): the period runs from 2009 to 2011, partly outside Amendment 6's window.
  - New field values: `tipo_evento` = "processo_cvm"; `como_veio_a_publico` = "regulador_cvm" or "regulador_bc".
- **Not included**
  - No final decision: Oi, 2015 and 2016 financial statements (PAS 19957.004207/2021-15; the judgment began on 2026-08-25 and a director asked for more time); CVC Brasil (the company spoke of accounting errors, not fraud, and the CVM charge was made public on 2026-01-30, with no judgment); Indústrias J.B. Duarte (PAS RJ2016/5786, 2013 to 2015 financial statements, scheduled for 2021-06-22; outcome not found).
  - Facts before 2010: Brasil Telecom (2006 to 2008 financial statements, decided in 2019) and Indústrias Verolme-Ishibrás (2008 and 2009 financial statements, according to the search).
  - Sanction not about the content of the financial statements: WLM (executive pay), GPC Participações and Eucatex (voting to approve their own accounts), CSN (material fact notice), J&F (derivatives) and Recrusul (capital increase).
  - Only late filing or failure to file financial statements: Companhia Aurífera Brasileira (2021), Advanced Digital Health (2023), proceeding 19957.008462/2019-12 (2023), Inncorp (2020) and Longdis (2022). Amendment 6 speaks of "irregularidade na elaboração ou divulgação" (irregularity in preparing or disclosing). I treated late filing and failure to file as outside; if you think they belong, the list grows considerably.
  - Others: Banco Cruzeiro do Sul (only fines for price manipulation; the 2023 document concerns a receivables fund), Intrader DTVM (not a listed company), Petrobras (the sanctions over the financial statements were on auditors, not on the company or its officers), Paranapanema (no fraud or sanction found) and Laep (information disclosure and failure to file).
- **Limit:** the search was not exhaustive. A complete sweep requires going through CVM's list of decided sanctioning proceedings, year by year since 2010. I can do that before your review, if you want.
- **IRB, existing case, not changed:** in the proceeding on the 2019 accounts (PAS 19957.003588/2023-87), the rapporteur's vote of 2026-10-06 is to acquit all defendants. Fernando Passos is acquitted because the conduct was already sanctioned in another proceeding. I did not check the Board's final decision. IRB's note in the ground truth ("ainda precisa ser conferido") stays as it is until you decide.

## 7. Authorizations of 2026-11-06 and results (after freeze v4)

Done after commit `76d72e9b559f4bf3a188b9bab69f9bbbb3053407` (Amendment 7), which the `congelamento-v4` branch points to. No Americanas or IRB value was read. Scripts: `varredura_pas.py` and `enet_html.py`.

### 7.1 Sweep of CVM sanctioning proceedings (Amendment 6, criterion a)

- **Source:** the date search on the CVM portal ("Processos Sancionadores Julgados"), year by year from 2010 to 2026 and page by page; then each proceeding's page, with the full summary and the PDF links. Result: 776 proceedings decided from 2010 to 2025.
- **Portal gaps:** the search returns few proceedings in 2021 (6), 2022 (10) and 2025 (17), against 43 to 100 in neighboring years, and none in 2026. I filled in with the CVM sanctioning-proceedings dataset and the decision news releases on gov.br/cvm. The dataset has 584 proceedings, opened from 2013-03 onwards, but it only gives the number, subject, opening date and stage, not the outcome. Even so, the sweep may not be exhaustive for 2021, 2022, 2025 and 2026.
- **Screening:**
  - 195 of the 776 have an accounting-content keyword in the summary (`varredura_pas.py --filtrar`).
  - 76 of those mention no auditor and are not only about late or missing filings. I read the decision extract or the vote of each one that could fit Amendment 6.
  - Auditor cases were screened by the summary. When the summary also mentioned officers or the preparation of the financial statements, I read the extract.
- **Rule applied (Amendment 6, criterion a):** a sanction on an officer or on the company for an irregularity in preparing or disclosing the financial statements, with facts from 2010 to 2023. Left out:
  - only the auditor sanctioned;
  - acquittals only;
  - settlement (termo de compromisso);
  - late or missing filings (Amendment 7);
  - sanctions not about the content of the financial statements.
- **Result in [`data/gabarito_candidatos.csv`](../../data/gabarito_candidatos.csv):** 39 rows (there were 18). `verificado_por` and `verificado_em` remain empty. Nothing was added to `data/gabarito_casos.csv`.
  - **Inside the data period: 31 rows, from 30 companies** (Mundial has two proceedings).
    - The 14 already there: Via Varejo, Taurus, OGX, OSX, Metalúrgica Duque, Mundial (2), Hércules, Teka, IGB, Tecnosolo, Schlosser, Brasil Brokers and Oi (2014 statements). Unchanged.
    - Two corrected: Inepar (2013 statements) and Docas de Imbituba.
    - 15 new: Inepar Equipamentos e Montagens, Petrobras, Recrusul, Springer, BRAZAL, CEB, Fibam, Marina de Iracema Park, Metalgráfica Iguaçu, Sultepa (2013 statements), Café Solúvel Brasília, Comercial Quintella, Cobrasma, Bahema and Indústrias J.B. Duarte.
  - **Outside the data period (Amendment 7): 8 rows**, flagged at the start of the note: Banco Panamericano, Brasil Telecom, Sanepar, J. C. Barretto, Mendes Júnior, Sultepa (2001 to 2003 statements), Construtora Beter and Inepar (proceeding 17/2006).
  - **Empty period:** Via Varejo (already so) and Mendes Júnior (the decision gives no year).
  - **Period partly before 2010:** Metalgráfica Iguaçu (2007 to 2011) and Mundial (2009 to 2011).
  - **`data_publica`:** filled in 17 of the 39 rows, always with a date written in a document I read. The sources are:
    - a material fact notice, read directly or cited in the decision;
    - the date of the charge or of the opening cited in the decision;
    - the Data_Abertura field of the CVM dataset (Fibam).

    In the other 22, the decision read does not give those dates, and the field is empty, with no estimate.
- **Requested check (Inepar and Docas)**
  - **Inepar S.A. (7595): two proceedings on the financial statements.**
    - Proceeding 17/2006, decided on 2013-10-22: 2004 to 2008 statements. Outside the data period (row `inepar_2006`).
    - RJ2014/7072, decided on 2018-03-27: 2013-12-31 statements and 2014-03-31 quarterly report (row `inepar_2013`, now with the extract read).
    - The `inepar_2010` row was removed: no decision read sanctions 2010 statements. The IstoÉ report gives no case number, and the topics it cites (BNDES, CEMAT, tax installment programs) appear in RJ2014/7072, whose sanction covers only 2013.
    - The subsidiary Inepar Equipamentos e Montagens (17868), with its own registration, was sanctioned in RJ2014/7351 for the 2013 statements (new row).
  - **Docas de Imbituba (3174).** The proceeding on the financial statements is RJ2016/5649, decided on 2018-12-18: 2014-12-31 statements and 2015 quarterly reports.
    - SEI 19957.000817/2015-00 in the previous row concerns acts of the controlling shareholder.
    - RJ2015/6319 concerns a late filing, which stays out under Amendment 7.
- **Corrections to part 6**
  - **Petrobras.** Part 6 said the sanctions on the financial statements fell only on auditors, which is wrong. In SP2017/294 (2020-11-03), officers were fined for not running the impairment test of the Abreu e Lima refinery in the 2010 statements. The conviction for the 2012 statements, proposed by the rapporteur, did not prevail.
  - **Recrusul.** The same proceeding as the capital increase also fined two officers for omitting related-party transactions from the 2011 to 2015 statements.
  - **Indústrias J.B. Duarte.** I found the rapporteur's vote of 2021-06-22. It convicts over the 2015 consolidated statements, not 2013 to 2015. The board's final outcome was not checked, and the CSV note says so.
  - **Brasil Telecom.** The sanction covers the 2007 and 2008 statements; the 2006 officer was acquitted.
  - **Verolme-Ishibrás.** PAS 13/2014 (2019-11-05) concerns abuse of control and fiduciary duties, not the financial statements. Left out.
- **No final decision:** Oi, 2015 and 2016 statements (PAS 19957.004207/2021-15). A commissioner asked for more time on 2026-08-25, and the CVM dataset still shows the case under judgment. Under Amendment 6, a case decided after your review only enters by a new amendment.
- **Excluded after reading**
  - **All acquitted on the financial-statement charge:** CCX (RJ2015/1954) and COPEL (19957.009104/2019-27).
  - **Sanction not about the content of the financial statements:**
    - Iguaçu Café Solúvel (08/2014: diligence in the face of signs of fraud);
    - WLM (executive pay);
    - GPC Participações and Eucatex (voting on their own accounts);
    - Rima (reserves);
    - Pettenati and Aliança da Bahia;
    - Verolme;
    - insider-trading cases.
  - **Only late or missing filings (Amendment 7):** Maori, Docas de Imbituba (RJ2015/6319), Capitalpart, Intrader, Fontaine Ville, Advanced Digital Health, Companhia Aurífera Brasileira (2021), Reag, Ammo, Coteminas, TBM and proceeding 19957.008462/2019-12, among others.
  - **Other:** proceedings where only auditors were sanctioned, and proceedings about funds.
- **Borderline group, for your decision.** None of these is in the CSV.
  - What they share: sanctions over bookkeeping and corporate books (art. 100 and art. 177, caput, of Law 6,404) or false registration data, with no charge on the content of the financial statements.
  - The cases:
    - RJ2017/905 (Deluxe Motors, 2017-12-11);
    - RJ2016/891 (19957.009255/2016-32), RJ2017/628, RJ2016/9175, RJ2017/1852, RJ2016/7389 and RJ2017/17;
    - RJ2017/3508 (Drogarias Americanas, which is not Americanas S.A.);
    - Companhia Aurífera Brasileira: RJ2017/3530, RJ2017/3521, RJ2017/1069 and RJ2016/8143.
  - The question is whether "irregularity in preparing the financial statements" includes failing to keep the books. If it does, I read each one and they enter.
- **Criterion b, open question: Petrobras, 2014 statements.** The company booked in those statements a write-off of improperly capitalized costs linked to Lava Jato. I did not read the material fact notice and did not include the case under criterion b. Tell me whether to check it.
- **IRB, existing case, unchanged.** The CVM dataset shows PAS 19957.003588/2023-87 (2019 accounts) as "Finalizado" on 2026-11-04. I did not read the final decision. IRB stays as it is in the ground truth (Amendment 6).

### 7.2 ENET HTML-route test (Amendment 5)

- **Choice of companies, by a fixed rule** (`enet_html.py escolher 2023`). All conditions:
  - 2023 DFP with a single version, the same in ENET and in the open data;
  - a consolidated balance sheet and a non-financial chart of accounts (account 3.01);
  - outside the ground truth and the candidates.

  Among those that qualify, the three with the most consolidated balance-sheet rows: codes 27499, 27766 and 20125. None is on the updated candidate list.
- **Comparison.** For each company, I read the four statements (balance sheet assets and liabilities, income statement and cash flow), consolidated and individual, and compared row by row:
  - the code;
  - the description, with the Amendment 7 text comparison;
  - the first two value columns: current year against `ÚLTIMO` and prior year against `PENÚLTIMO`, with a R$0.50 tolerance after the scale ("Reais Mil").

  The script prints only counts.
- **Result: not 100%.**

| Company | Rows | Match | Do not match |
| --- | --- | --- | --- |
| 27499 | 550 | 546 | 4 |
| 27766 | 504 | 504 | 0 |
| 20125 | 669 | 669 | 0 |
| **Total** | **1,723** | **1,719** | **4** |

- **Where the differences are**
  - Consolidated: all 871 rows match for the three companies.
  - The 4 that do not match are in the individual balance-sheet liabilities of 27499, where 108 of 112 rows match. They are the prior-year column of four equity accounts: 2.03.01, 2.03.02, 2.03.02.06 and 2.03.02.07. Code, description and current year match.
  - That is exactly the column Amendment 5 uses as year t−1.
  - No account appears on one side only.
- **Interpretations that need your confirmation**
  1. **An empty HTML cell counts as 0 in the open data.** In the first run, without this rule, every difference was of this kind; with it, the 4 above remain.
  2. **Repeated rows in the open data.**
     - For the three test companies, each consolidated balance-sheet account appears 2 or 3 times in the file, with the same code, date and period. Description and value are equal across the repeats, and the comparison used one row per code.
     - The selection rule (most rows) favored these companies.
     - It is not limited to them. In the consolidated balance sheet, companies with a repeated code are 2 in 2019, 6 in 2022, 11 in 2023, 2 in 2024 and 2 in 2025; none in 2010–2018, 2020 and 2021 (ground truth excluded).
     - Outside the three test companies, I did not check whether the repeated values are equal, because that would require opening values. Phase 1 will need a rule for these rows.
- **How the route works** (for the record):
  - The filing page (`frmGerenciaPaginaFRE.aspx`) only gives the address of the tables inside a cookie session, and some sessions return a reduced page. The script tries up to ten sessions.
  - Each table comes from `frmDemonstracaoFinanceiraITR.aspx`, with the filing page as the Referer header.
  - The statement codes are 2 (balance sheet assets), 3 (liabilities), 4 (income statement) and 99 (cash flow).
  - The `Informacao` parameter picks the table: 2 for consolidated, 1 for individual. Changing `Grupo` alone is not enough.
- **Consequence, under your rule:** the HTML route was **not** registered as the means of fetching the point-in-time version (Amendment 5). IRB 2019 stays "versão da época indisponível" (point-in-time version unavailable).
- **IRB 2019, version 1 (row counts only).**
  - I ran the count when only the consolidated statements had been compared and matched 100%, before widening the test to the individual ones. I record it as a fact; under your rule, it does not change IRB 2019's status.
  - ENET confirmed the filing is version 1. The eight tables loaded with the same number of rows as version 5 in the open data:
    - consolidated: 83 (balance sheet assets), 116 (liabilities), 75 (income statement) and 34 (cash flow);
    - individual: 83, 106, 70 and 34, in the same order.
  - No value was read from the open data or printed.

### 7.3 What depends on you

1. Case-by-case review of `data/gabarito_candidatos.csv`, before anything goes into `data/gabarito_casos.csv`.
2. Borderline group (bookkeeping and corporate books): in or out.
3. `data_publica`: I used the charge date cited in the decision as "opening of the proceeding" (Amendment 6), as in part 6. For Cobrasma and Comercial Quintella, the report gives the same date (2015-07-13), from the same rapporteur; worth checking.
4. Indústrias J.B. Duarte: the board's final outcome was not checked.
5. HTML route: the two interpretations in part 7.2, empty cell as 0 and repeated rows.
6. Criterion b: whether to check Petrobras 2014.
7. Oi, 2015 and 2016 statements: no final decision; it can only enter by a new amendment.

## Appendix A. Sector names in the registry and the FCA

"Companies" counts distinct CVM codes: in the registry, by current sector; in the FCA, in any year from 2010 to 2026. Generated by `scripts/fase0/setores.py --tabela`. Sector names are the official CVM names, in Portuguese.

| Sector name | Companies in the registry | Companies in the FCA | Years in the FCA |
| --- | --- | --- | --- |
| Agricultura (Açúcar, Álcool e Cana) | 49 | 29 | 2010–2026 |
| Alimentos | 112 | 33 | 2010–2026 |
| Arrendamento Mercantil | 73 | 12 | 2010–2026 |
| Bancos | 115 | 44 | 2010–2026 |
| Bebidas e Fumo | 24 | 5 | 2010–2026 |
| Bolsas de Valores/Mercadorias e Futuros | 3 | 1 | 2010–2026 |
| Brinquedos e Lazer | 10 | 8 | 2010–2026 |
| Comunicação e Informática | 38 | 32 | 2010–2026 |
| Comércio (Atacado e Varejo) | 101 | 65 | 2010–2026 |
| Comércio Exterior | 4 | — | — |
| Construção Civil, Mat. Constr. e Decoração | 168 | 79 | 2010–2026 |
| Cooperativas | — | 1 | 2010–2010 |
| Crédito Imobiliário | 6 | 1 | 2011–2024 |
| Educação | 10 | 11 | 2010–2026 |
| Embalagens | 8 | 3 | 2010–2026 |
| Emp. Adm. Part. - Agricultura (Açúcar, Álcool e Cana) | 3 | 4 | 2010–2026 |
| Emp. Adm. Part. - Alimentos | 6 | 7 | 2010–2026 |
| Emp. Adm. Part. - Arrendamento Mercantil | 2 | 3 | 2010–2016 |
| Emp. Adm. Part. - Bancos | 1 | 2 | 2013–2026 |
| Emp. Adm. Part. - Brinquedos e Lazer | 4 | 3 | 2010–2026 |
| Emp. Adm. Part. - Comunicação e Informática | 6 | 6 | 2013–2026 |
| Emp. Adm. Part. - Comércio (Atacado e Varejo) | 18 | 17 | 2010–2026 |
| Emp. Adm. Part. - Const. Civil, Mat. Const. e Decoração | 23 | 24 | 2010–2026 |
| Emp. Adm. Part. - Crédito Imobiliário | 5 | 4 | 2012–2026 |
| Emp. Adm. Part. - Educação | 8 | 8 | 2010–2026 |
| Emp. Adm. Part. - Embalagens | 2 | 2 | 2010–2016 |
| Emp. Adm. Part. - Energia Elétrica | 49 | 50 | 2010–2026 |
| Emp. Adm. Part. - Extração Mineral | 11 | 15 | 2010–2026 |
| Emp. Adm. Part. - Farmacêutico e Higiene | 2 | 4 | 2010–2020 |
| Emp. Adm. Part. - Gráficas e Editoras | 1 | 1 | 2012–2016 |
| Emp. Adm. Part. - Hospedagem e Turismo | 5 | 4 | 2010–2026 |
| Emp. Adm. Part. - Intermediação Financeira | 15 | 10 | 2010–2026 |
| Emp. Adm. Part. - Metalurgia e Siderurgia | 7 | 7 | 2010–2026 |
| Emp. Adm. Part. - Máqs., Equip., Veíc. e Peças | 8 | 9 | 2010–2026 |
| Emp. Adm. Part. - Papel e Celulose | 1 | 2 | 2010–2026 |
| Emp. Adm. Part. - Petroquímicos e Borracha | 4 | 5 | 2010–2023 |
| Emp. Adm. Part. - Petróleo e Gás | 12 | 12 | 2010–2026 |
| Emp. Adm. Part. - Saneamento, Serv. Água e Gás | 7 | 8 | 2010–2026 |
| Emp. Adm. Part. - Securitização de Recebíveis | 4 | 7 | 2010–2024 |
| Emp. Adm. Part. - Seguradoras e Corretoras | 5 | 6 | 2010–2026 |
| Emp. Adm. Part. - Sem Setor Principal | 104 | 124 | 2010–2026 |
| Emp. Adm. Part. - Serviços Transporte e Logística | 35 | 35 | 2010–2026 |
| Emp. Adm. Part. - Serviços médicos | 7 | 5 | 2016–2026 |
| Emp. Adm. Part. - Telecomunicações | 38 | 30 | 2010–2026 |
| Emp. Adm. Part. - Têxtil e Vestuário | 5 | 6 | 2010–2025 |
| Emp. Adm. Part.-Bolsas de Valores/Mercadorias e Futuros | 1 | 2 | 2010–2011 |
| Emp. Adm. Participações | 156 | — | — |
| Energia Elétrica | 104 | 99 | 2010–2026 |
| Extração Mineral | 52 | 10 | 2010–2026 |
| Factoring | 1 | 1 | 2010–2011 |
| Farmacêutico e Higiene | 22 | 15 | 2010–2026 |
| Gráficas e Editoras | 12 | 3 | 2010–2023 |
| Hospedagem e Turismo | 28 | 12 | 2010–2026 |
| Intermediação Financeira | 9 | 11 | 2010–2026 |
| Metalurgia e Siderurgia | 136 | 32 | 2010–2026 |
| Máquinas, Equipamentos, Veículos e Peças | 176 | 40 | 2010–2026 |
| Outras Atividades Industriais | 18 | — | — |
| Papel e Celulose | 21 | 9 | 2010–2026 |
| Pesca | 4 | 1 | 2020–2020 |
| Petroquímicos e Borracha | 97 | 18 | 2010–2026 |
| Petróleo e Gás | 24 | 19 | 2010–2026 |
| Reflorestamento | 6 | 3 | 2010–2026 |
| Saneamento, Serv. Água e Gás | 37 | 36 | 2010–2026 |
| Securitização de Recebíveis | 138 | 133 | 2010–2026 |
| Seguradoras e Corretoras | 23 | 8 | 2010–2026 |
| Serviços Diversos | 18 | — | — |
| Serviços Médicos | 23 | — | — |
| Serviços Transporte e Logística | 138 | 117 | 2010–2026 |
| Serviços em Geral | 1 | — | — |
| Serviços médicos | — | 21 | 2010–2026 |
| Telecomunicações | 76 | 31 | 2010–2026 |
| Têxtil e Vestuário | 121 | 38 | 2010–2026 |
| (empty) | 6 | 3 | 2010–2021 |
