# Pre-registration of the document reader (Phase F1)

Registered on 2026-11-11, before any code or measurement of the reader, with Roberto's decisions of the same date. The targets, the rule and the definitions below do not change after measuring. The case format (section 6) is the one Roberto uses to write the held-out cases.

## 1. What is measured

The extractive reader of Phase F1 (`chiocca/v2/leitor/`). It only copies excerpts from the documents, with the page, and judges nothing:

- **related parties** in the DFP explanatory notes: the categories of item 19 and the fields of item 18 of CPC 05 (R1), in the parent-company and consolidated columns when the note has them;
- the phrase **"on market terms"** (item 23), recorded as a fact, without proof;
- mentions of **reverse factoring (risco sacado) or forfaiting** in the notes, with the negative-sentence mark ("the Company has no reverse factoring operations" is a negative mention);
- the **auditor's report** of the DFP version used: the type of opinion and the excerpts of basis for qualification, emphasis of matter, material uncertainty about going concern, key audit matters and other matters.

The related-party transactions table of the Reference Form is not extraction (it is structured open data). It only enters the requirement on natural-person names.

## 2. Targets

All four are mandatory:

1. **precision** of at least 0.95;
2. **coverage** of at least 0.80;
3. **literal check** on 100% of the excerpts shown;
4. **zero natural-person names** in the output. It is a requirement, not a target: a single name showing up fails the reader.

## 3. Rule

- If any of the four fails on the held-out cases, the new section does not enter the investigation: it stays off, and the result goes into the report as it came out.
- The reader is not tuned against the held-out cases. A new attempt requires new held-out cases.
- The section is only switched on if all four are met, in a commit that records the result, the hash of the frozen reader and the SHA-256 of each held-out case.

## 4. Cases

- **Development:** written by the coding agent, in `tests/leitor/casos/desenvolvimento/`, used to build and tune the reader. The result on them is informative; it is not the measurement.
- **Held-out:** written by Roberto outside this environment, in the format of section 6. The agent freezes the reader in a commit and reports the hash. Only then does it receive the held-out cases, measure once with the frozen reader (`python -m chiocca.v2.leitor.avaliar <case folder>`) and publish the result as it came out.

## 5. Definitions

- **Returned units.** The reader returns excerpts and classifications. For counting, excerpts are grouped by key (check, label, page and, for reverse factoring, the negative-sentence mark): several excerpts with the same key are one unit. There are two classifications: the reading status of the notes (`lido` or `nao_lido`) and the auditor's type of opinion.
- **Match.** A unit matches a ground-truth item when the check is the same, the label is the same (if the item gives a label), the page is the same (if the item gives a page) and, for reverse factoring, the negative-sentence mark is the same. A classification matches when the value is equal.
- **Precision** = returned units matching some item ÷ returned units.
- **Coverage** = ground-truth items found ÷ ground-truth items. An item is found when some unit matches it and, if the item gives the text `contem`, some excerpt of that unit contains that text (ignoring whitespace differences) or was omitted for a natural-person name.
- **Literal check.** The text of each excerpt shown, with whitespace normalized, appears in the text of the page it came from (or of the auditor's report), also with whitespace normalized.
- **Leaked name.** Any text of `nomes_proibidos` (ignoring case, accents and whitespace) in any field of the reader's output, including the Reference Form rows.
- Counts add up all cases (micro average). Results are given with three decimal places.

## 6. Case format

One JSON file per case, in UTF-8. The notes become a PDF generated in the test itself, page by page, and the reader reads that PDF as it would read the CVM one (no PDF enters git).

```json
{
  "id": "g01",
  "descricao": "free text; the reader does not read this field",
  "notas": {"paginas": [["line 1 of page 1", "line 2"], ["line 1 of page 2"]], "sem_texto": false},
  "parecer": {"titulo": "Relatório do Auditor Independente - Com Ressalva", "texto": "running text of the report"},
  "formulario_de_referencia": [{"Parte_Relacionada": "Exemplo Participações S.A.", "Tipo_Pessoa": "PJ",
                                "Relacao_Emissor": "Controladora", "Objeto_Contrato": "Aluguel",
                                "Montante_Envolvido": "1000", "Saldo_Existente": "0", "Garantia_Seguro": "",
                                "Natureza_Razao_Operacao": "", "Taxa_Juros": ""}],
  "esperado": {
    "notas": "lido",
    "parecer_tipo": "com_ressalva",
    "itens": [
      {"verificacao": "partes_relacionadas", "rotulo": "controladora", "pagina": 1, "contem": "trecho esperado"},
      {"verificacao": "campo_cpc05_18", "rotulo": "garantias", "pagina": 1, "contem": "aval"},
      {"verificacao": "condicoes_de_mercado", "pagina": 1, "contem": "condições de mercado"},
      {"verificacao": "risco_sacado", "pagina": 2, "negacao": false, "contem": "risco sacado"},
      {"verificacao": "parecer", "rotulo": "base_para_ressalva", "contem": "não obtivemos"}
    ],
    "nomes_proibidos": ["Nome Fictício Completo"]
  }
}
```

- `notas`, `parecer` and `formulario_de_referencia` are optional (without `notas` there is no PDF; `sem_texto: true` generates pages with no text layer).
- `esperado.notas` is mandatory when there are `notas`; `esperado.parecer_tipo`, when there is a `parecer`.
- `pagina` starts at 1. Auditor's report items have no page.
- The ground truth lists **all** the keys it expects: a returned unit with no matching item counts against precision.
- Labels:
  - related parties (item 19): `controladora`, `controle_conjunto_ou_influencia`, `controladas`, `coligadas`, `joint_ventures`, `pessoal_chave`, `outras_partes`;
  - item 18 fields: `montante`, `saldos`, `termos_e_condicoes`, `garantias`, `provisao_pcld`, `perdas_incobraveis`;
  - auditor's report sections: `base_para_ressalva`, `enfase`, `incerteza_continuidade`, `principais_assuntos`, `outros_assuntos`;
  - opinion types: `sem_ressalva`, `com_ressalva`, `adversa`, `abstencao`.

## 7. Omission of natural-person names (decision of 2026-11-11)

An excerpt with a natural-person name becomes "trecho omitido; ver página N do documento" ("excerpt omitted; see page N of the document"). The detector errs on the side of omitting. It flags the excerpt when there is:

- a courtesy title (Sr., Sra., Srs., Sras., Dr., Dra.);
- a CPF number;
- a sequence of two or more capitalized words (possibly with "de", "da", "do", "das", "dos" or "e" in between) that does not end in a company marker (S.A., S/A, Ltda., Participações, Holding and others) and is not on the exception list (company names from the CVM registry and accounting and institutional terms).

In the Reference Form, the party's name only shows when the table says legal entity and the detector does not flag it; otherwise, "parte relacionada (nome omitido)" ("related party (name omitted)"). The table's text fields go through the same detector.

## 8. What is left out

Any kind of judgment, alert, score or ranking; proof of omission (absence of mention does not prove absence); text recognition in images (a page with no text layer is "not read"); ITR notes; documents filed after 2024-12-31 and fiscal years from 2024 onward; turning tables into numbers; older versions of the Reference Form; LLM (outside Phase F).

## 9. Registration

- Date: 2026-11-11.
- Commit: the one that introduces this file. The hash is noted here in the next commit, without changing any rule above.
- Hash of the registration commit: `0e3eebc30a8dc26ded921ea0439a06cf34f207f5`.

## 10. Amendment 1: leitor-f1-2 and the IPE subject rule (2026-11-13)

Registered on 2026-11-13, before any code of `leitor-f1-2` or of the subject rule, with Roberto's request of the same date. Sections 1 to 9 still apply to `leitor-f1-1` and do not change; this amendment applies to the new attempt. Nothing below changes after measuring.

### 10.1 What changes in the reader (`leitor-f1-2`)

The four adjustments recorded in the plan, and only those:

1. **Who controls the Company:** "the Company is controlled by X" and "the Company is jointly controlled by X and Y" become `controladora` and `controle_conjunto_ou_influencia`, not a mention of `controladas` or `joint_ventures`.
2. **The Company itself:** "the Company, as parent company, ..." refers to the Company itself and does not count as `controladora` (CPC 05 item 19 a).
3. **Amount and term in a sentence:** sentences such as "somou R$ … no exercício" and "as compras totalizaram R$ …" ("totalled R$ … in the year", "purchases totalled R$ …") count as `montante`, and "the contract expires in 2030" or "due in 30 days" as `termos_e_condicoes`.
4. **Table headers:** header lines (years such as "2021 2020 2021 2020", column titles such as "Controladora Consolidado" or "A receber (a pagar) Receita (despesa)"), including multi-line ones, do not come out as excerpts.

The natural-person name detector (section 7) does not become more permissive in `leitor-f1-2`: any change to it can only omit more.

**New development cases**, written by the agent in `tests/leitor/casos/desenvolvimento/` (the current 28 remain), with tables in the real format of the notes: multi-line headers, parent-company and consolidated columns, two fiscal years, total lines, values in parentheses and footnotes (i), (ii). At least 12 new cases, at least 8 of them with a table.

### 10.2 Reader targets and rule

- The same four as in section 2, with the definitions of section 5: precision of at least 0.95; coverage of at least 0.80; literal check on 100% of the excerpts shown; zero natural-person names (a requirement).
- If `leitor-f1-2` meets all four on the new held-out cases, it replaces `leitor-f1-1` in the excerpts section, in a commit that records the result, the frozen reader hash and each case's SHA-256. If it fails any of them, the section keeps `leitor-f1-1`, already approved, and the result goes into the report as it came out.
- **Informative header measure:** each case may carry `esperado.trechos_que_nao_devem_aparecer` (for example, the table header lines). The number of these texts that come out as excerpts is counted. It is informative: it changes neither precision, coverage nor the rule.
- **Informative comparison:** `leitor-f1-1` is also measured on the new held-out cases, for comparison only.

### 10.3 Subject-specific rule for the IPE

A new rule, only for the subject of material facts and notices (contracts section 9), frozen in the same commit as `leitor-f1-2` and measured on the same held-out cases, in files of its own (10.4). It may use the reader's name detector and subject-specific rules (for example, for acronyms, company names outside the registry, English titles and all-caps subjects). Two targets:

1. **Zero person names (a requirement):** no subject marked `omitido` in the ground truth is shown, and no text of `nomes_proibidos` (ignoring case, accents and spaces) appears in a shown subject. A single case fails the rule.
2. **Undue omission of at most 0.20:** subjects marked `mostrado` in the ground truth that the rule omits ÷ subjects marked `mostrado`. Proposed value 0.20 (at least 80% of name-free subjects shown): today's conservative rules omit 60.2% of all subjects from 2010 to 2024, and in the 2026-11-12 sample almost none of those omitted by the new rules had a name.

- If the rule meets both, it replaces today's conservative rules (detector, all caps and capitalized word outside the start), in a commit that records the result. If it fails either, today's rules stay.
- An empty subject keeps its notice and does not enter the counts.
- **Informative comparison:** today's rules are also measured on the same subject cases.
- The subject rule and `leitor-f1-2` are decided separately: each passes or fails on its own targets.

### 10.4 Format of the subject cases

One JSON file per set, in UTF-8, with a name starting with `assuntos_` (for example, `assuntos_a01.json`), in the same folder as the reader cases:

```json
{
  "id": "a01",
  "descricao": "free text; the rule does not read this field",
  "assuntos": [
    {"assunto": "Renúncia do Diretor Fulano Exemplar de Tal", "esperado": "omitido"},
    {"assunto": "Renúncia do diretor Exemplar", "esperado": "omitido"},
    {"assunto": "AUMENTO DE CAPITAL APROVADO", "esperado": "mostrado"},
    {"assunto": "Petrobras sobre venda da refinaria RLAM", "esperado": "mostrado"},
    {"assunto": "Resultados do 3T23 - Versão em inglês", "esperado": "mostrado", "categoria": "comunicado_ao_mercado"}
  ],
  "nomes_proibidos": ["Fulano Exemplar de Tal", "Exemplar"]
}
```

- `esperado` is `omitido` (the subject has a person's name) or `mostrado` (it does not). `categoria` is optional (`fato_relevante` or `comunicado_ao_mercado`); the rule may ignore it.
- `nomes_proibidos` lists each person's name in the file's `omitido` subjects, in full and in the parts that identify the person (a lone surname, for example).
- Person names are invented: no real natural-person name enters the repository. Names of companies, places, acronyms and products may be real.
- Suggestion for the held-out cases: at least 300 subjects, at least 60 with a name, in varied forms (full name, lone surname, all caps, after a colon, with a courtesy title, with initials, in an English subject, a name that matches a common word or a company name), and at least 200 without a name, similar to the real ones (title case, acronyms, companies in and outside the registry, places, months such as "Maio/2017", products, English titles).
- Subject development cases, written by the agent: at least 150 subjects, in the same format.

### 10.5 Cases and procedure

1. This amendment is registered before any code of `leitor-f1-2` and of the subject rule.
2. The agent develops with the development cases (10.1 and 10.4). The 20 held-out cases of `leitor-f1-1` are now public: measuring on them is informative only and decides nothing.
3. The agent freezes `leitor-f1-2` and the subject rule in a commit, with each file's SHA-256 in a record of its own and a test that fails if any changes, and reports the hash.
4. Only then does Roberto write the new held-out cases (reader cases in the section 6 format, with the optional field of 10.2, and subject cases in the 10.4 format) and hand them over. Suggestion: at least 20 reader cases, at least 8 of them with a table in the real format.
5. The measurement is made once, with the frozen code (`python -m chiocca.v2.leitor.avaliar <case folder>`, which will also read the `assuntos_` files), and published as it came out. Nothing is adjusted against the held-out cases; a new attempt requires new held-out cases.
6. Results with three decimal places, summing all cases (micro average).

### 10.6 Amendment record

- Date: 2026-11-13.
- Commit: the one that introduces this section. The hash is recorded here in the next commit, without changing any rule above.
