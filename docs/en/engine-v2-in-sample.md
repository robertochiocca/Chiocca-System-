# Engine v2 frozen: within the development sample

> **Within the development sample, not a test.** Engine v2 was frozen on 2026-11-23 ([SHA-256 registry](../motor_v2_codigo_congelado.json)), and only after that were these numbers computed, with the frozen code, on fiscal years 2010 to 2023, the same ones in which v2 was developed. Nothing here is evidence that v2 works: its test is the v2 arm in the secondary evaluation of study 2 (amendment 5) and, later, the prospective test with fiscal year 2026. Aggregate numbers only; no company is named.

## 1. Alert rate

Engine v2 with the three changes, each company at the cutoff date of its fiscal year. Alert: score at the 90% quantile of the fiscal year and group; evaluated: at least one computable signal.

| Fiscal year | Non-financial evaluated | On alert | Rate | Financial evaluated | On alert | Rate |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 2010 | 434 | 44 | 10.1% | 33 | 4 | 12.1% |
| 2011 | 445 | 45 | 10.1% | 40 | 4 | 10.0% |
| 2012 | 440 | 44 | 10.0% | 42 | 5 | 11.9% |
| 2013 | 464 | 47 | 10.1% | 42 | 5 | 11.9% |
| 2014 | 454 | 46 | 10.1% | 42 | 5 | 11.9% |
| 2015 | 457 | 46 | 10.1% | 41 | 5 | 12.2% |
| 2016 | 451 | 46 | 10.2% | 38 | 5 | 13.2% |
| 2017 | 471 | 48 | 10.2% | 38 | 4 | 10.5% |
| 2018 | 469 | 47 | 10.0% | 37 | 4 | 10.8% |
| 2019 | 465 | 47 | 10.1% | 33 | 4 | 12.1% |
| 2020 | 556 | 56 | 10.1% | 33 | 4 | 12.1% |
| 2021 | 617 | 62 | 10.0% | 34 | 4 | 11.8% |
| 2022 | 605 | 61 | 10.1% | 34 | 4 | 11.8% |
| 2023 | 610 | 61 | 10.0% | 30 | 3 | 10.0% |
| Total | 6,938 | 700 | 10.1% | 517 | 60 | 11.6% |

The yearly rate stays between 10.0% and 10.2% for non-financial companies and between 10.0% and 13.2% for financial ones. The evaluated company-years and the alerts, by group and by number of computable signals, are the same as in the [label-free descriptions](engine-v2-descriptions.md) made before the pre-registration: yes, in both groups.

## 2. Signal coverage

| Group | Signal | Computable in v1 | Computable in v2 |
| --- | --- | ---: | ---: |
| Non-financial | M-score | 5,390 | 6,017 |
| Non-financial | DPO jump | 6,341 | 6,341 |
| Non-financial | implied interest | 6,214 | 6,214 |
| Non-financial | standardized Benford deviation | does not exist in v1 | 6,938 |
| Financial | weight of non-recurring gains | 300 | 300 |
| Financial | standardized Benford deviation | does not exist in v1 | 517 |

DEPI from the DVA applies to 735 company-years. The label-free descriptions counted 742: the 7 extra ones are non-financial company-years outside the non-financial chart of accounts (banks and others), where v1 does not compute the M-score and v2, like v1, does not apply the DVA; the M-score covers the same 6,017 company-years in both computations. Engine v2 evaluates 228 non-financial and 217 financial company-years that v1 did not evaluate (for example, only through Benford); of the 6,710 non-financial company-years evaluated by v1, v2 evaluates all.

## 3. Alert rate by number of computable signals

The known characteristic in section 4 of the v2 pre-registration, uncorrected:

| Group | Computable signals | Evaluated | On alert | Rate |
| --- | ---: | ---: | ---: | ---: |
| Non-financial | 1 | 215 | 15 | 7.0% |
| Non-financial | 2 | 426 | 72 | 16.9% |
| Non-financial | 3 | 745 | 108 | 14.5% |
| Non-financial | 4 | 5,552 | 505 | 9.1% |
| Financial | 1 | 217 | 17 | 7.8% |
| Financial | 2 | 300 | 43 | 14.3% |

## 4. Hits on the study 1 cases (within the sample, not a test)

The rule in section 5 of the study 1 pre-registration and the alarms per hit of amendments 10 and 11, with the v2 alert in place of the v1 alert, through the same study 1 functions. Engine v2 was developed without the answer key, but on the same fiscal years and with the same cases in view: the hits below are not a test.

| | v2 frozen | v1 (study 1) | Naive rule (study 1) |
| --- | ---: | ---: | ---: |
| Hittable cases | 13 | 13 | 13 |
| Cases hit, 2010 to 2023 | 3 | 7 | 6 |
| Cases hit with an alert in 2017 to 2023 | 0 | 2 | 1 |
| Distinct non-financial companies on alert, 2017 to 2023 | 231 | 624 | 109 |
| Alarms per hit, 2017 to 2023 (non-financial) | no hit | 311 | 108 |
| Distinct non-financial companies on alert, 2010 to 2023 | 366 | 765 | 167 |
| Alarms per hit, 2010 to 2023 (non-financial) | 121 | 108 | 27 |
