<div align="center">

# Chiocca System

**Alertas de manipulação contábil em companhias abertas brasileiras, calculados só com o que era público na época.**

**Accounting-manipulation alerts for Brazilian listed companies, computed only from what was public at the time.**

[Português](#português) · [English](#english)

*Projeto bilíngue: todo o conteúdo existe completo em português e em inglês.*
*Bilingual project: all content is complete in both Portuguese and English.*

</div>

---

## Português

> **Projeto de estudo e portfólio. Não é acusação nem recomendação de investimento.** O sistema emite alertas estatísticos a partir de demonstrações públicas. Um alerta diz onde olhar, não que houve fraude.

### O problema

Fraudes contábeis grandes costumam deixar rastro nos números antes de virem a público. A pergunta deste projeto é quanto desse rastro dá para ver de fora, só com dados abertos, e a que custo:

> *Com os dados que eram públicos na época, sinais simples teriam alertado para casos reais de manipulação antes de eles virem a público? E quantos alarmes falsos isso custaria?*

O "na época" é o ponto central. A base de dados abertos da CVM é atualizada quando uma empresa reapresenta suas demonstrações. Quem baixa hoje o balanço de 2021 da Americanas pode receber o número já corrigido: o lucro de R$ 544 milhões daquele ano virou prejuízo de R$ 6,2 bilhões na reapresentação ([demonstrações de 2022](https://api.mziq.com/mzfilemanager/v2/d/347dba24-05d2-479e-a775-2ea8677c50f2/a0a24676-9552-a96e-80b1-b5c6a7a90e46?origin=1)). Testar um detector com o número corrigido é "prever" a fraude olhando a resposta. Aqui, cada cálculo usa só a versão que já era pública na data de corte.

### Como funciona

```
Dados abertos da CVM (DFP, todas as versões, incluindo empresas canceladas)
        ↓
Base "como era na época": a versão pública em cada data de corte
        ↓
Sinais do catálogo: M-score de Beneish e sinais adaptados ao Brasil
        ↓
Regras de alerta fixadas no pré-registro, antes de olhar os dados
        ↓
Avaliação: casos reais acertados, alarmes falsos, comparação com uma regra simples
        ↓
Ficha de alerta: qual sinal disparou, com qual número e de qual conta da DFP
```

### Sinais da primeira versão

- **M-score de Beneish:** oito índices que comparam um ano com o anterior.
- **Salto no prazo de fornecedores:** dívida com banco registrada como "fornecedores" alonga o prazo de pagamento. Foi o mecanismo do risco sacado na Americanas.
- **Juro implícito:** despesa financeira alta demais para a dívida declarada pode indicar financiamento fora da linha de empréstimos.
- **Lucro que não vira caixa:** a diferença entre lucro e caixa operacional.

Fórmulas, contas da DFP e referências de cada sinal, inclusive os das próximas fases, estão em [`catalogo_sinais.yaml`](catalogo_sinais.yaml). O código lê esse arquivo, que é a fonte única dos sinais, com nome e descrição nos dois idiomas.

### Casos de referência

O gabarito ([`data/gabarito_casos.csv`](data/gabarito_casos.csv)) guarda casos reais, cada um com o período afetado, a data em que veio a público e a fonte. Começa com dois:

- **Americanas (2023):** revelado por dentro. O Comitê Independente confirmou contratos fictícios de verba de propaganda e operações de risco sacado lançadas em "fornecedores" ([fato relevante de 16/07/2024](https://api.mziq.com/mzfilemanager/v2/d/347dba24-05d2-479e-a775-2ea8677c50f2/fbd1eb14-1e3f-f8ef-ecc5-f49db62d1b04?origin=1)).
- **IRB Brasil (2020):** revelado de fora, pela tese de uma gestora de que o lucro recorrente era menor que o contábil ([InfoMoney](https://www.infomoney.com.br/?p=1397142)). Como é resseguradora, fica fora do M-score, que não se aplica a empresas financeiras.

### Princípios

1. **Como era na época.** Nenhum cálculo usa informação posterior à data de corte.
2. **Pré-registro.** Pontos de corte e regras de alerta são decididos e assinados em [`docs/pre-registro.md`](docs/pre-registro.md) antes de qualquer dado. Mudar uma regra depois exige um pré-registro novo.
3. **Nenhum número digitado à mão.** Todo resultado publicado sai de script, e um teste falha se o documento divergir.
4. **Alerta, não acusação.** O repositório publica só números agregados e os casos do gabarito, que já são públicos. Nenhuma lista de empresas em alerta é divulgada.
5. **Resultado ruim também é resultado.** Se o detector não ganhar de uma regra simples, isso vai para o resumo.
6. **Bilíngue de verdade.** Resultados, resumos e fichas de alerta saem do mesmo cálculo em português e em inglês, com teste de números idênticos. A terminologia segue o [`glossario_pt_en.yaml`](glossario_pt_en.yaml).

### Estado do projeto

**Fase 0: fundação.** Ainda não há código de cálculo.

| Implementado | Roadmap |
| --- | --- |
| Catálogo de 16 sinais, em PT e EN, com fórmulas e referências | Base "como era na época" com os dados da CVM |
| Gabarito inicial com 2 casos e fontes, notas em PT e EN | Sinais da primeira versão, com testes |
| Glossário PT↔EN dos termos contábeis e do estudo | Avaliação conforme o pré-registro |
| Pré-registro do estudo | Ficha de alerta e resumo de uma página, em PT e EN |
| Exemplo resolvido com valores esperados (teste de referência) | |
| Especificação para o agente de código ([`PROMPT.md`](PROMPT.md)) | Próximas fases: auditoria, ganhos não recorrentes, rendimento do caixa, dividendos sem caixa, F-score e teste de retorno das ações |

### Estrutura

```
catalogo_sinais.yaml      sinais: fórmula, contas da DFP, referências, fase (PT e EN)
glossario_pt_en.yaml      termos contábeis e do estudo, PT ↔ EN
data/gabarito_casos.csv   casos reais com datas, fontes e notas (PT e EN)
data/exemplo_resolvido.json  empresa fictícia com valores esperados (teste de referência)
docs/pre-registro.md      decisões do estudo, assinadas antes dos dados
PROMPT.md                 especificação de construção para o agente de código
```

### Referências

- Beneish, M. D. (1999). [The Detection of Earnings Manipulation](https://rpc.cfainstitute.org/research/financial-analysts-journal/1999/the-detection-of-earnings-manipulation). *Financial Analysts Journal*.
- Beneish, M. D., Lee, C. M. C. e Nichols, C. (2013). [Earnings Manipulation and Expected Returns](https://papers.ssrn.com/abstract=2241717). *Financial Analysts Journal*.
- Dechow, P., Ge, W., Larson, C. e Sloan, R. (2011). [Predicting Material Accounting Misstatements](https://www.thecaq.org/wp-content/uploads/2018/03/Dechow-et-al-2011-Contemporary_Accounting_Research.pdf). *Contemporary Accounting Research*.
- Schilit, H., Perler, J. e Engelhart, Y. (2018). [Financial Shenanigans](https://www.mheducation.com/highered/mhp/product/financial-shenanigans-fourth-edition-how-detect-accounting-gimmicks-fraud-financial-reports.html), 4ª ed. McGraw Hill.
- Alves, M. C. D. e Oliveira, K. V. [Inconsistências em demonstrações contábeis: setor elétrico pelo M-score de Beneish](https://congressousp.fipecafi.org/Arquivos/45/Anais/5700%20.pdf). Congresso USP.

---

## English

> **Study and portfolio project. Not an accusation and not investment advice.** The system issues statistical alerts from public financial statements. An alert says where to look, not that fraud occurred.

### The problem

Large accounting frauds tend to leave traces in the numbers before they come to light. This project asks how much of that trace is visible from the outside, using only open data, and at what cost:

> *Using only data that was public at the time, would simple signals have flagged real manipulation cases before they came to light? And how many false alarms would that cost?*

"At the time" is the core idea. The CVM (Brazil's securities regulator) updates its open-data base when a company restates its financial statements. Downloading Americanas' 2021 balance sheet today may return the already-corrected figure: that year's R$544 million profit became a R$6.2 billion loss in the restatement ([2022 financial statements](https://api.mziq.com/mzfilemanager/v2/d/347dba24-05d2-479e-a775-2ea8677c50f2/a0a24676-9552-a96e-80b1-b5c6a7a90e46?origin=1), in Portuguese). Testing a detector on restated numbers means "predicting" the fraud with the answer in hand. Here, every calculation uses only the filing version that was public at each cut-off date.

### How it works

```
CVM open data (DFP annual filings, every version, including delisted companies)
        ↓
Point-in-time base: the version that was public at each cut-off date
        ↓
Catalog signals: Beneish M-score and Brazil-specific signals
        ↓
Alert rules fixed in the pre-registration, before looking at the data
        ↓
Evaluation: real cases detected, false alarms, comparison with a naive rule
        ↓
Alert sheet: which signal fired, with which figure, from which DFP account
```

### First-version signals

- **Beneish M-score:** eight indices that compare one year with the previous one.
- **Jump in days payable outstanding:** bank debt booked as trade payables stretches the payment period. It was the *risco sacado* (supplier finance) mechanism in the Americanas case.
- **Implied interest:** finance costs too high for the reported debt may point to financing outside the borrowings line.
- **Earnings not backed by cash:** the gap between net income and operating cash flow.

Formulas, DFP accounts and references for each signal, including later phases, are in [`catalogo_sinais.yaml`](catalogo_sinais.yaml). The code reads that file, the single source of signals, with names and descriptions in both languages.

### Reference cases

The ground truth ([`data/gabarito_casos.csv`](data/gabarito_casos.csv)) holds real cases, each with the affected period, the date it became public and the source. It starts with two:

- **Americanas (2023):** revealed from the inside. The Independent Committee confirmed fictitious cooperative advertising allowances and supplier-finance operations booked as trade payables ([material fact notice of 2024-07-16](https://api.mziq.com/mzfilemanager/v2/d/347dba24-05d2-479e-a775-2ea8677c50f2/fbd1eb14-1e3f-f8ef-ecc5-f49db62d1b04?origin=1), in Portuguese).
- **IRB Brasil (2020):** revealed from the outside, by an asset manager's thesis that recurring profit was lower than reported profit ([InfoMoney](https://www.infomoney.com.br/?p=1397142), in Portuguese). As a reinsurer, it is excluded from the M-score, which does not apply to financial companies.

### Principles

1. **Point-in-time.** No calculation uses information published after the cut-off date.
2. **Pre-registration.** Cut-offs and alert rules are decided and signed in [`docs/pre-registro.md`](docs/pre-registro.md) before any data is touched. Changing a rule afterwards requires a new pre-registration.
3. **No hand-typed numbers.** Every published result comes from a script, and a test fails if a document diverges.
4. **Alert, not accusation.** The repository publishes only aggregate figures and the reference cases, which are already public. No list of flagged companies is released.
5. **A bad result is still a result.** If the detector does not beat a naive rule, that goes into the summary.
6. **Truly bilingual.** Results, summaries and alert sheets come from the same calculation in Portuguese and English, with a test that the numbers match. Terminology follows [`glossario_pt_en.yaml`](glossario_pt_en.yaml).

### Project status

**Phase 0: foundation.** There is no calculation code yet.

| Done | Roadmap |
| --- | --- |
| Catalog of 16 signals, in PT and EN, with formulas and references | Point-in-time base from CVM data |
| Initial ground truth with 2 sourced cases, notes in PT and EN | First-version signals, with tests |
| PT↔EN glossary of accounting and study terms | Evaluation as set in the pre-registration |
| Study pre-registration | Alert sheet and one-page summary, in PT and EN |
| Worked example with expected values (reference test) | |
| Build specification for the coding agent ([`PROMPT.md`](PROMPT.md)) | Next phases: auditor signals, non-recurring gains, cash yield, dividends above free cash flow, F-score and stock-return test |

### Structure

```
catalogo_sinais.yaml      signals: formula, DFP accounts, references, phase (PT and EN)
glossario_pt_en.yaml      accounting and study terms, PT ↔ EN
data/gabarito_casos.csv   real cases with dates, sources and notes (PT and EN)
data/exemplo_resolvido.json  fictitious company with expected values (reference test)
docs/pre-registro.md      study decisions, signed before the data
PROMPT.md                 build specification for the coding agent
```

### References

- Beneish, M. D. (1999). [The Detection of Earnings Manipulation](https://rpc.cfainstitute.org/research/financial-analysts-journal/1999/the-detection-of-earnings-manipulation). *Financial Analysts Journal*.
- Beneish, M. D., Lee, C. M. C. and Nichols, C. (2013). [Earnings Manipulation and Expected Returns](https://papers.ssrn.com/abstract=2241717). *Financial Analysts Journal*.
- Dechow, P., Ge, W., Larson, C. and Sloan, R. (2011). [Predicting Material Accounting Misstatements](https://www.thecaq.org/wp-content/uploads/2018/03/Dechow-et-al-2011-Contemporary_Accounting_Research.pdf). *Contemporary Accounting Research*.
- Schilit, H., Perler, J. and Engelhart, Y. (2018). [Financial Shenanigans](https://www.mheducation.com/highered/mhp/product/financial-shenanigans-fourth-edition-how-detect-accounting-gimmicks-fraud-financial-reports.html), 4th ed. McGraw Hill.
- Alves, M. C. D. and Oliveira, K. V. [Inconsistências em demonstrações contábeis: setor elétrico pelo M-score de Beneish](https://congressousp.fipecafi.org/Arquivos/45/Anais/5700%20.pdf) (in Portuguese). USP Congress.

---

Roberto Chiocca · [MIT](LICENSE)
