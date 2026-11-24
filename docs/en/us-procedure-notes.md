# US study procedure notes, before the single computation

> Written on 2026-11-24, after the freeze of the study code (commit `dd9b662e1f2d52355722b6fe102d7e5515782115`) and before the single computation, which starts only with Roberto's authorization, after the PR and the freeze release. These notes change neither the [US study pre-registration](us-preregistration.md) nor the frozen code: they record the four implementation rules that the registered text does not detail and that are already in the code, each with its reason, and the format reads done on the real SEC files. No US signal was computed. A flag, not an accusation.

## 1. Where the rules are

- **The frozen code:** `chiocca/eua/estudo.py`, with SHA-256 `6440c49a6ede796e51f2b6c3d7e1c2b63201bd939afe1507feb87c652b0f4ffa` in the [freeze registry](../eua_codigo_congelado.json), written in commit `dd9b662e1f2d52355722b6fe102d7e5515782115`. The rules below are the ones in that file's docstring, with the same number.
- **The other rules:** (i) to (vi) are in the hand-computed example (`tests/referencia/gerar_exemplo_eua.py`) and in the account map (`chiocca/eua/mapa.py`); (iii), the public version at the cut-off, and (v), the entry order, are also in the docstring of `estudo.py`. Rules (vii) to (x) exist only in the study code.

## 2. Rules (vii) to (x), each with its reason

### (vii) Overlapping windows

- **Rule:** a company-year is positive if an episode opens after its cut-off and up to the last day of the same month of the following year (the 12 months of section 5). If the windows of two company-years of the same company overlap, the episode goes to the one with the latest cut-off before the episode opens. The windows are those of the sample's non-financial companies; an episode outside all of them goes only into the description (`desfecho` and `fim_da_janela`).
- **Reason:** section 5 says the windows of consecutive fiscal years do not overlap, which holds when fiscal years end 12 months apart. When a company changes its fiscal year-end and files two 10-Ks less than 12 months apart, the windows overlap. Keeping the latest cut-off gives the episode to the newest public statements on the date of the 8-K that opens it and keeps the registered rule that each episode falls in at most one company-year. The window ending on the last day of the month follows from the cut-off always being the last day of a month (section 3.3); for fiscal year 2024 it falls on 2026-04-30, the date in section 5.

### (viii) Fiscal years 2009 and 2010, for the AAERs only

- **Rule:** signals and alerts are also computed for fiscal years 2009 and 2010, only for the AAER description (section 8). These fiscal years do not enter the measures, the exclusions or the per-year descriptives, which cover 2011 to 2024, as in section 4 (`EXERCICIOS_CALCULADOS` and `aaers`).
- **Reason:** section 8 counts the Bao et al. cases with affected years from 2009 to 2014, with the public version at the cut-off, and notes that in 2009 and 2010 only the larger companies filed in XBRL. To know whether v1, v2 and the naive rule flagged those years, the whole group of each fiscal year must be computed, because the DPO decile, the naive-rule decile and the v2 percentiles are within the fiscal year. Since the groups are per fiscal year, computing 2009 and 2010 changes no result from 2011 to 2024.

### (ix) The "no computable signal" exclusion

- **Rule:** the last exclusion of section 4, "no computable signal", counts the non-financial companies that neither v1 nor v2 evaluates. The measures are computed on those evaluated by v1; those that only v2 evaluates (no v1 signal, but the Benford deviation) are kept apart, only counted, with the outcome rate.
- **Reason:** section 4 does not say which engine the signal belongs to, and v2 has a signal v1 lacks, the Benford deviation. Section 6 already fixes the measures on the company-years evaluated by v1 and the v2 alert computed among all those v2 evaluates, as in the Brazilian study. Counting as excluded only the company-year that neither evaluates removes from the v2 computation none that it evaluates, and the report shows both counts.

### (x) The 8-Ks since 2004

- **Rule:** the episodes come from all 8-K and 8-K/A filings with Item 4.02 in the EDGAR filing history since 2004, up to 2026-04-30 (`PRIMEIRO_ANO_DO_ITEM`). The Phase 0 counts still start in 2009: the default of `chiocca.eua.itens.entregas` did not change.
- **Reason:** section 5 opens the episode at the company's first 8-K with Item 4.02. Reading only from 2009, a 2009 8-K that belongs to an episode opened earlier would open a new episode and, in a sequence of 8-Ks less than 365 days apart, could shift the opening date of the following episodes. Item 4.02 exists since 2004-08-23, when the new 8-K rules took effect.

## 3. The format reads on the real SEC files

On 2026-11-24, while the code was being written and before the freeze, to check that the study reader (`chiocca.eua.estudo.le_trimestre`) accepts the files as the SEC ships them. **No value was read:** the `value` column of `num.txt` was not loaded; nothing beyond file names, header lines and line counts was printed; no signal, account or alert was computed. The numbers below come from [`docs/eua_leituras_de_formato.json`](../eua_leituras_de_formato.json).

1. **The file names in each zip:** in the 68 quarters, from 2009Q1 to 2025Q4, all 68 have `sub.txt`, `num.txt` and `pre.txt`.
2. **The quarter with no filings (2009Q1):** the header line of the three files and the number of data lines, as in Phase 0: `sub.txt` 0; `num.txt` 0; `pre.txt` 0.
3. **The line count (2016Q1):** in each file, the number of lines against the number of rows read by pandas without quote handling (`quoting=3`, as the study reader reads `num.txt` and `pre.txt`) and with the default handling, loading only identification columns (`sub.txt`: `adsh`; `num.txt`: `adsh`, `tag`; `pre.txt`: `adsh`, `plabel`). The three counts matched in each file; those of `sub.txt` and `num.txt` are the Phase 0 ones.

| File | Lines | Read without quotes | Read with the default |
| --- | ---: | ---: | ---: |
| `sub.txt` | 6,532 | 6,532 | 6,532 |
| `num.txt` | 3,174,261 | 3,174,261 | 3,174,261 |
| `pre.txt` | 729,483 | 729,483 | 729,483 |

The disk size of the downloaded folders was also looked at, to estimate the memory of the computation; the scale was measured on a synthetic quarter, generated in the SEC format, not on the real files. The EDGAR filing-history file, with the 8-Ks, was not opened at this stage.

## 4. What comes next

The single computation (`python -m chiocca.eua.estudo --calculo-unico --baixar`), only with Roberto's authorization, after the PR and the freeze release (target 2027-01-31; fallback 2027-04-30). Before reading any data, it checks the freeze registry and refuses SEC files that were not downloaded again on the day. Only aggregates go into the versioned result; no list of companies by alert is published.
