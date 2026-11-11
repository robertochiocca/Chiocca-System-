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
