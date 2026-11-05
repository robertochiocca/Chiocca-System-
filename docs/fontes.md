# Fontes

Fatos externos usados pelo projeto, com URL e data da consulta (regra 3 do `PROMPT.md`).

## Fase 0 · reconhecimento · consulta em 05/11/2026, das 02:12 UTC em diante (04/11/2026, 23:12 em Brasília)

Todos os arquivos vêm do Portal de Dados Abertos da CVM. Foram baixados para uma pasta temporária, fora do repositório. "Gerado em" é a data que a listagem do servidor mostrava na consulta. A CVM regera esses arquivos, e por isso o hash identifica a cópia usada.

### Dicionários de dados

| Arquivo | URL | Gerado em | SHA-256 |
| --- | --- | --- | --- |
| `meta_dfp_cia_aberta_txt.zip` | https://dados.cvm.gov.br/dados/CIA_ABERTA/DOC/DFP/META/meta_dfp_cia_aberta_txt.zip | 01/11/2026 | `1c0066a38257c11c6f602a6676f00b11095bba0ffe3b4d4220fec912a466342e` |
| `meta_cad_cia_aberta.txt` | https://dados.cvm.gov.br/dados/CIA_ABERTA/CAD/META/meta_cad_cia_aberta.txt | 04/11/2026 | `3bb4c788ad8e9cefd024e4d241fcde41270116fd37fb31ad53a4a6984ab43255` |

### Cadastro de companhias abertas

| Arquivo | URL | Gerado em | SHA-256 |
| --- | --- | --- | --- |
| `cad_cia_aberta.csv` | https://dados.cvm.gov.br/dados/CIA_ABERTA/CAD/DADOS/cad_cia_aberta.csv | 04/11/2026 | `76857def1654defbdd398f5898f2d07cebb7d3e33c93db8ee652b23dd8c9ce59` |

### Formulário Cadastral (FCA)

Só a estrutura foi conferida, em um ano. Listagem: https://dados.cvm.gov.br/dados/CIA_ABERTA/DOC/FCA/DADOS/ (arquivos de 2010 a 2026).

| Arquivo | URL | SHA-256 |
| --- | --- | --- |
| `fca_cia_aberta_2012.zip` | https://dados.cvm.gov.br/dados/CIA_ABERTA/DOC/FCA/DADOS/fca_cia_aberta_2012.zip | `ba68b8e8c12b74fc56bf76a75ae582aa53e5adef1d61d940d5191c55b9be2e06` |

### DFP (Demonstrações Financeiras Padronizadas)

Listagem: https://dados.cvm.gov.br/dados/CIA_ABERTA/DOC/DFP/DADOS/ · URL de cada arquivo: `https://dados.cvm.gov.br/dados/CIA_ABERTA/DOC/DFP/DADOS/dfp_cia_aberta_AAAA.zip`

| Ano | Gerado em | SHA-256 |
| --- | --- | --- |
| 2010 | 05/08/2024 | `c6a9c95c2510e8a71bb583084492e9c52c3f423a3be56f1c5d2dd4f6960677ff` |
| 2011 | 05/08/2024 | `858423fba40124d7a30abea4e70248f7251e1d2c792e9fcece5a57afd3115f34` |
| 2012 | 05/08/2024 | `3aff7a726d324d29924887eed45bbc58bc30b66cd9079bafe701d55efdfe0849` |
| 2013 | 05/08/2024 | `ef379ac9aab9567434ca6d36053d8bd1f0a2a47a0c65a2e1d218259da530e224` |
| 2014 | 05/08/2024 | `b8795dba134754475a485c0f88b6542face6613bb418d261caa011d90e032f28` |
| 2015 | 05/08/2024 | `39a7001be9eaa91a6acc83831c816794df4f92441d7702b80da6c4b234352b4e` |
| 2016 | 05/08/2024 | `772f06a73c5fe80534b61365ea5d03f9d8fcce21b87823bd5c9d48699bcf71d5` |
| 2017 | 05/08/2024 | `1ff8185d61759e49b406c55c5d0b593587c2e76e9032c95f836f7fea02fc9d58` |
| 2018 | 05/08/2024 | `280dcf5acd7bdb529acc186c9a1195092a1e06cf1e33ddcdca0b11c31261296f` |
| 2019 | 05/08/2024 | `bc82a1162b44686e8953b521e3424a5938b6661ff4655f832db4ea9488296a0d` |
| 2020 | 29/12/2024 | `8fb97d1887aed1e1e2d85e54cb133baf9f65b9f46f60fa8720f09c1f7a74362e` |
| 2021 | 28/12/2025 | `64b8693b709538a0357c5179ae02231cb380d0000956ee57a873a21d4efda2e4` |
| 2022 | 01/11/2026 | `0a40fd3cf0f151e0e2f8b608426768958324308e3dfc9c462c35d5a212036c9e` |
| 2023 | 01/11/2026 | `76502c1044a51fa688a748aeca1a0325b47c670da99f2c7044e5accdad2c3cca` |
| 2024 | 01/11/2026 | `2071e7908c2d1fa945b21b3d6a982eb41b1550360f19e5185cb5eb6fbf9a8fb9` |
| 2025 | 01/11/2026 | `85f53d6aba99557ebb8a5f8b247c0610973230c1a0f97ab267da2216816a8ab6` |
| 2026 | 01/11/2026 | `0b4f99dca3b8ad5d460fcf1f324381717f8642eafa65827145b6e7280046a4c5` |

### Sistema ENET da CVM (versões de cada documento)

- Formato do link, tirado da coluna `LINK_DOC` do índice da DFP: `http://www.rad.cvm.gov.br/ENETCONSULTA/frmDownloadDocumento.aspx?CodigoInstituicao=<n>&NumeroSequencialDocumento=<n>`.
- Teste de download feito em 05/11/2026 com uma empresa fora do gabarito (DFP 2019, versões 1 e 2). Os dois downloads chegaram cortados nas três tentativas, e o conteúdo do `.dfp` não foi confirmado (ver `reconhecimento.md`, parte 3).
