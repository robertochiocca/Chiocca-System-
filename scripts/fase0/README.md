# Scripts da Fase 0 · Phase 0 scripts

**PT.** Reconhecimento da estrutura dos dados abertos da CVM. Nenhum script lê a coluna `VL_CONTA`. As contagens de estrutura removem Americanas e IRB antes de qualquer análise; só `autorizados.py` olha os metadados dessas duas empresas, autorizados por Roberto em 05/11/2026: versões e datas de entrega das DFPs de 2017 a 2022 e rótulos das contas do IRB. Os números de `docs/reconhecimento.md` saem destes scripts.

**EN.** Reconnaissance of the structure of CVM open data. No script reads the `VL_CONTA` column. The structure counts drop Americanas and IRB before any analysis; only `autorizados.py` looks at those two companies' metadata, authorized by Roberto on 2026-11-05: filing versions and receipt dates of the 2017–2022 DFPs and IRB's account labels. The figures in `docs/reconhecimento.md` come from these scripts.

```
# na raiz do repositório · from the repository root
export CHIOCCA_CVM_RAW=data/brutos/cvm        # arquivos baixados, fora do git · downloads, outside git
python scripts/fase0/baixar.py                # DFP, FCA, cadastro e dicionários + SHA256SUMS
python scripts/fase0/estrutura.py             # partes 1 e 2 do reconhecimento (seções: versoes, dominios, ...)
python scripts/fase0/setores.py               # nomes de setor do cadastro e do FCA
python scripts/fase0/grupos.py                # regra de financeiras da Emenda 5 (parte 4.1)
python scripts/fase0/dfc.py                   # padrões finais da DFC (parte 4.2)
python scripts/fase0/emenda5.py               # linhas da Emenda 5 nas financeiras e contas 2.01/2.02
python scripts/fase0/autorizados.py           # metadados autorizados de Americanas e IRB (parte 5)
python scripts/fase0/enet_teste.py 2019 3     # teste de download no ENET (parte 5)
```
