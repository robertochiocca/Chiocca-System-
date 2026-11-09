# Origin of the code brought from other projects

Every file brought from Carchuna, Calahonda or DireitoAberto (all by Roberto Chiocca, MIT license) goes into this table and carries at the top the origin project, the path, the commit and the sentence "adapted for the Chiocca System". No project is installed as a package.

Commits inspected in Phase A (details in [`docs/en/inventory.md`](inventory.md)):

- Carchuna: `a3f30ac284eb01245b022b7655bb16c4b8474cc7`
- Calahonda: `47ef323440946a2552bea1ded0da59bd96e6f1a8`
- DireitoAberto: `102e3e2d9d70e87249d8df9215737e2d98b6358d`

| File in Chiocca | Project | Origin path | Commit | What changed | Phase |
| --- | --- | --- | --- | --- | --- |
| `chiocca/v2/validade.py` | Carchuna | `carchuna/validade.py` | `a3f30ac284eb01245b022b7655bb16c4b8474cc7` | Three-state result class and `variacao_percentual`; float instead of Decimal, reason in PT and EN, bridge to engine v1; without the margin thresholds | B |
| `chiocca/v2/linhagem.py` | Carchuna | `carchuna/linhagem.py` | `a3f30ac284eb01245b022b7655bb16c4b8474cc7` | Sheet format; spreadsheet columns became DFP lines, with the line in the source file; new builder for engine v1 | B |
| `chiocca/v2/confianca.py` | Carchuna | `carchuna/confianca.py` | `a3f30ac284eb01245b022b7655bb16c4b8474cc7` | Only the structure of components with a reason; without the 0–100 score; new criteria and categorical level | B |
| `chiocca/v2/conferencias.py` | Carchuna | `carchuna/margem.py` | `a3f30ac284eb01245b022b7655bb16c4b8474cc7` | Only the principle (identity, reconciliation through another path and plausibility); new checks for CVM data | B |
| `.github/workflows/ci.yml` | DireitoAberto | `.github/workflows/ci.yml` | `102e3e2d9d70e87249d8df9215737e2d98b6358d` | Only the Python job, with Chiocca's commands | B |
| `chiocca/v2/pdf_simples.py` | DireitoAberto | `backend/app/leitor/pdf_simples.py` | `102e3e2d9d70e87249d8df9215737e2d98b6358d` | Removed the scanned page, the blank page and the missing font (adversarial set); added transliteration outside Windows-1252, pagination and the footer with the notice on every page | C2 |

**Not from other projects.** `tests/referencia/gerar_exemplo_resolvido.py` came from the planning conversation (claude.ai, with Claude), written before the engine, and was handed over by Roberto on 2026-11-08. Its origin is in the file's own docstring. Changes: black formatting, a type annotation required by mypy and, on 2026-11-09, by Roberto's decision, the rounding of three values (`DPO_t_dias`, `variacao_dias` and `spread_pp`) from 2 to 4 decimals, to follow commit 70d71a5; no calculation changed.
