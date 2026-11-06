# Sources

*English version of [`docs/fontes.md`](../fontes.md). If the two ever differ, the Portuguese file prevails.*

External facts used by the project, with URL and date consulted (rule 3 of `PROMPT.md`).

## Phase 0 · reconnaissance · consulted on 2026-11-05, from 02:12 UTC onwards (2026-11-04, 23:12 in Brasília)

All files come from CVM's Open Data Portal. They were downloaded to a temporary folder, outside the repository. "Generated on" is the date the server listing showed when consulted. CVM regenerates these files, so the hash identifies the copy used.

### Data dictionaries

| File | URL | Generated on | SHA-256 |
| --- | --- | --- | --- |
| `meta_dfp_cia_aberta_txt.zip` | https://dados.cvm.gov.br/dados/CIA_ABERTA/DOC/DFP/META/meta_dfp_cia_aberta_txt.zip | 2026-11-01 | `1c0066a38257c11c6f602a6676f00b11095bba0ffe3b4d4220fec912a466342e` |
| `meta_cad_cia_aberta.txt` | https://dados.cvm.gov.br/dados/CIA_ABERTA/CAD/META/meta_cad_cia_aberta.txt | 2026-11-04 | `3bb4c788ad8e9cefd024e4d241fcde41270116fd37fb31ad53a4a6984ab43255` |

### Listed company registry

| File | URL | Generated on | SHA-256 |
| --- | --- | --- | --- |
| `cad_cia_aberta.csv` | https://dados.cvm.gov.br/dados/CIA_ABERTA/CAD/DADOS/cad_cia_aberta.csv | 2026-11-04 | `76857def1654defbdd398f5898f2d07cebb7d3e33c93db8ee652b23dd8c9ce59` |

### Registration Form (FCA)

Source of each year's sector (Amendment 5). The 2012 file was downloaded on 2026-11-05 at 02:12 UTC; the others on the same day at 20:43 UTC (17:43 in Brasília). Both 2012 downloads gave the same hash.

Listing: https://dados.cvm.gov.br/dados/CIA_ABERTA/DOC/FCA/DADOS/ · URL of each file: `https://dados.cvm.gov.br/dados/CIA_ABERTA/DOC/FCA/DADOS/fca_cia_aberta_AAAA.zip`

| Year | Generated on | SHA-256 |
| --- | --- | --- |
| 2010 | 2024-03-04 | `9a9b933fa02c96f7cf632dbb1f7b004bb78696c81c989792b1eb60f70b001021` |
| 2011 | 2024-03-04 | `f5c7aaa2a4464b4232a05d77c288d33bca5474edd72199a9295d6fa2a34012e8` |
| 2012 | 2024-03-04 | `ba68b8e8c12b74fc56bf76a75ae582aa53e5adef1d61d940d5191c55b9be2e06` |
| 2013 | 2024-03-04 | `d62ef489d8c1208ef3d41cfd25a093b8fcb5f6b47640e59288aece45d4962cce` |
| 2014 | 2024-03-04 | `1f70b5e3a544535affb47b04a0c60a618bef872bc783e6909940d2e7dad89e3f` |
| 2015 | 2024-03-04 | `74326a566c405d703b56af257c9fade687f112f372ae68b8624719becc8215f2` |
| 2016 | 2024-03-04 | `229b2cfc8c0ac5e60083932381364bbdb6666f028422c13a1ac5f6dccc9e3e6c` |
| 2017 | 2024-03-04 | `48127cf15d8baf4d31b9544b266f9511962db158d591fc9803e335a8ab081d45` |
| 2018 | 2024-03-04 | `b20056b00927c5261ba587b668e52e4cdfe2d989e7d794491b2bb127fbd0a8cd` |
| 2019 | 2024-03-04 | `09f84e5f5485217c8b36f8379c36f718dbdcd6d6908b4e96b68861394e76fe97` |
| 2020 | 2024-12-29 | `ccf2ac081747da9ccefa50349a5494c263763d5dd8bb961565fd2ae64c264b20` |
| 2021 | 2025-12-28 | `65ba4b0225e9b2106901cdf348215933be8affba79925fc71361e2f6818c7999` |
| 2022 | 2026-11-01 | `1cf67f61d3fae38ae09e4bc333c9dada9eb30617abf4128350a23d5b0e4edeea` |
| 2023 | 2026-11-01 | `62b09231d90e9140f1fa17b36432c24e50e80eaf684ba8cdbadc74626b8956a7` |
| 2024 | 2026-11-01 | `fac9d73d0a6bd817aea969db48a71b18471f17d1a283b359f92479c22a2a25d5` |
| 2025 | 2026-11-01 | `a1923e812ae255ea195d91baf30a5771e73cf39b7a03463a139d2883a9be14b9` |
| 2026 | 2026-11-01 | `7cc2ed67a931f1056be04856fb20de2fb5184820bbadb05b82dab5dffb879c2f` |

### DFP (Standardized Financial Statements)

Listing: https://dados.cvm.gov.br/dados/CIA_ABERTA/DOC/DFP/DADOS/ · URL of each file: `https://dados.cvm.gov.br/dados/CIA_ABERTA/DOC/DFP/DADOS/dfp_cia_aberta_AAAA.zip`

| Year | Generated on | SHA-256 |
| --- | --- | --- |
| 2010 | 2024-08-05 | `c6a9c95c2510e8a71bb583084492e9c52c3f423a3be56f1c5d2dd4f6960677ff` |
| 2011 | 2024-08-05 | `858423fba40124d7a30abea4e70248f7251e1d2c792e9fcece5a57afd3115f34` |
| 2012 | 2024-08-05 | `3aff7a726d324d29924887eed45bbc58bc30b66cd9079bafe701d55efdfe0849` |
| 2013 | 2024-08-05 | `ef379ac9aab9567434ca6d36053d8bd1f0a2a47a0c65a2e1d218259da530e224` |
| 2014 | 2024-08-05 | `b8795dba134754475a485c0f88b6542face6613bb418d261caa011d90e032f28` |
| 2015 | 2024-08-05 | `39a7001be9eaa91a6acc83831c816794df4f92441d7702b80da6c4b234352b4e` |
| 2016 | 2024-08-05 | `772f06a73c5fe80534b61365ea5d03f9d8fcce21b87823bd5c9d48699bcf71d5` |
| 2017 | 2024-08-05 | `1ff8185d61759e49b406c55c5d0b593587c2e76e9032c95f836f7fea02fc9d58` |
| 2018 | 2024-08-05 | `280dcf5acd7bdb529acc186c9a1195092a1e06cf1e33ddcdca0b11c31261296f` |
| 2019 | 2024-08-05 | `bc82a1162b44686e8953b521e3424a5938b6661ff4655f832db4ea9488296a0d` |
| 2020 | 2024-12-29 | `8fb97d1887aed1e1e2d85e54cb133baf9f65b9f46f60fa8720f09c1f7a74362e` |
| 2021 | 2025-12-28 | `64b8693b709538a0357c5179ae02231cb380d0000956ee57a873a21d4efda2e4` |
| 2022 | 2026-11-01 | `0a40fd3cf0f151e0e2f8b608426768958324308e3dfc9c462c35d5a212036c9e` |
| 2023 | 2026-11-01 | `76502c1044a51fa688a748aeca1a0325b47c670da99f2c7044e5accdad2c3cca` |
| 2024 | 2026-11-01 | `2071e7908c2d1fa945b21b3d6a982eb41b1550360f19e5185cb5eb6fbf9a8fb9` |
| 2025 | 2026-11-01 | `85f53d6aba99557ebb8a5f8b247c0610973230c1a0f97ab267da2216816a8ab6` |
| 2026 | 2026-11-01 | `0b4f99dca3b8ad5d460fcf1f324381717f8642eafa65827145b6e7280046a4c5` |

### CVM's ENET system (versions of each filing)

- Link format, taken from the `LINK_DOC` column of the DFP index: `http://www.rad.cvm.gov.br/ENETCONSULTA/frmDownloadDocumento.aspx?CodigoInstituicao=<n>&NumeroSequencialDocumento=<n>`.
- Download test run on 2026-11-05 with a company outside the ground truth (DFP 2019, versions 1 and 2). Both downloads arrived truncated in all three attempts, and the contents of the `.dfp` file were not confirmed (see `reconnaissance.md`, part 3).

## 2026-11-05 · authorizations and expanded ground truth (after the freeze)

### CVM's ENET system, second test

- Old-version packages, through the DFP index's `LINK_DOC`: tested on 2026-11-05 at 20:00–21:00 UTC, with curl and with `scripts/fase0/enet_teste.py`. None arrived whole (see `reconnaissance.md`, part 5.4).
- HTML view of each filing: `https://www.rad.cvm.gov.br/ENET/frmGerenciaPaginaFRE.aspx?NumeroSequencialDocumento=<n>&CodigoTipoInstituicao=2`. It responded with HTTP 200 for all three filings tested.

### CVM decisions and material fact notices read for `data/gabarito_candidatos.csv`

Consulted on 2026-11-05. Each case in the file carries its main source and, where available, a secondary one. Documents read in full text (PDF):

| Case | Document | URL |
| --- | --- | --- |
| Banco Panamericano | Decision extract, PAS CVM 01/2011 | https://conteudo.cvm.gov.br/export/sites/cvm/sancionadores/sancionador/anexos/2018/012011_Banco_Panamericanocx.pdf |
| Via Varejo | Material fact notice of 2019-12-12 | https://api.mziq.com/mzfilemanager/v2/d/ce9bff9f-fb19-49b9-9588-c4c6b7052c9c/ff43ced3-e5c7-a49a-f33d-57fa4a9fdb4c?origin=1 |
| Taurus | Vote, PAS CVM RJ2014/13977 | https://conteudo.cvm.gov.br/export/sites/cvm/noticias/anexos/2020/20200130_PAS_CVM_RJ2014_13977_voto_diretor_gustavo_gonzalez.pdf |
| OGX | Decision extract, PAS CVM RJ2014/12838 | https://conteudo.cvm.gov.br/export/sites/cvm/sancionadores/sancionador/anexos/2018/RJ201412838__COMPLETO.pdf |
| OSX | Decision extract, PAS CVM RJ2015/1421 | https://conteudo.cvm.gov.br/export/sites/cvm/sancionadores/sancionador/anexos/2018/20190625_PAS_RJ20151421.pdf |
| Metalúrgica Duque | Decision extract, PAS CVM RJ2014/4077 | https://conteudo.cvm.gov.br/export/sites/cvm/sancionadores/sancionador/anexos/2018/RJ20144077__COMPLETO.pdf |
| Mundial (2016) | Decision extract, PAS CVM RJ2013/6224 | https://conteudo.cvm.gov.br/export/sites/cvm/sancionadores/sancionador/anexos/2016/20160513_PAS_RJ20136224.pdf |
| Mundial (2017) and Hércules | Decision extract, PAS CVM RJ2017/565 | https://conteudo.cvm.gov.br/export/sites/cvm/sancionadores/sancionador/anexos/2017/RJ2017565_Mundial_SA.pdf |
| Teka | Decision extract, PAS CVM RJ2015/6229 | https://conteudo.cvm.gov.br/export/sites/cvm/sancionadores/sancionador/anexos/2018/RJ20156229_TEKA.pdf |
| IGB Eletrônica | Decision extract, PAS CVM RJ2015/6280 | https://conteudo.cvm.gov.br/export/sites/cvm/sancionadores/sancionador/anexos/2018/RJ20156280_IGB_Eletronica_.pdf |
| Tecnosolo | Decision extract, PAS CVM RJ2015/2651 | https://conteudo.cvm.gov.br/export/sites/cvm/sancionadores/sancionador/anexos/2017/RJ20152651_Tecnosolo_vf.pdf |
| Schlosser | Decision extract, PAS CVM RJ2014/12056 | http://conteudo.cvm.gov.br/export/sites/cvm/sancionadores/sancionador/anexos/2017/RJ201412056_Cia_Industrial_Schlosser.pdf |
| Brasil Brokers | Vote, PAS CVM 19957.009415/2019-96 | https://www.gov.br/cvm/pt-br/assuntos/noticias/anexos/2021/20210316_PAS_CVM_19957_0094152019_96_SP2019_617_voto_presidente_marcelo_barbosa.pdf |
| Oi (2014 financial statements) | Decision extract, PAS CVM 19957.004416/2016-00 | https://conteudo.cvm.gov.br/export/sites/cvm/sancionadores/sancionador/anexos/2023/SEI_19957004416_2016_00_1.pdf |
| Oi (2015 and 2016 financial statements), not included | Report, PAS CVM 19957.004207/2021-15 | https://www.gov.br/cvm/pt-br/assuntos/noticias/anexos/2026/20260825-pas-cvm-19957-004207-2021-15-relatorio-diretora-marina-copola.pdf |
| IRB (2019 accounts), existing case | Rapporteur's vote, PAS CVM 19957.003588/2023-87 | https://www.gov.br/cvm/pt-br/assuntos/noticias/anexos/2026/20261006-pas-cvm-19957-003588-2023-87-diretor-igor-muniz-voto.pdf |

Proceedings read and set aside because they do not concern the content of the financial statements or concern only late filing: RJ2014/5099 (WLM), 19957.003052/2018-02 (GPC Participações), 19957.003549/2018-12 (J&F), 19957.008462/2019-12, 19957.001933/2021-86 (Intrader DTVM), 19957.010135/2018-40 (Companhia Aurífera Brasileira), RJ2016/5786 (J.B. Duarte report, without the decision) and decision 1510/19 on the receivables fund linked to Banco Cruzeiro do Sul, all on CVM's sanctioning-proceedings and decisions portal (`conteudo.cvm.gov.br`).

## 2026-11-06 · sweep of sanctioning proceedings and ENET HTML-route test (after freeze v4)

### Decided sanctioning proceedings (CVM portal)

- Date search, year by year from 2010 to 2026 and page by page: `https://conteudo.cvm.gov.br/sancionadores/index.html?lastName=&dataInicio=01/01/<year>&dataFim=31/12/<year>&buscado=true&pasta=sancionador&contCategoriasCheck=1&filtro=todos&vimDaCategoria=/sancionadores/sancionador/&searchPage=<n>`. The portal refuses Python's default agent, so the script sends a generic User-Agent.
- Then each proceeding's page (`https://conteudo.cvm.gov.br/sancionadores/sancionador/<year>/...html`), with the full summary and the PDF links.
- Consulted on 2026-11-06, around 17:30–18:00 UTC, with `scripts/fase0/varredura_pas.py`. Result: 776 proceedings decided from 2010 to 2025 (see `reconnaissance.md`, part 7.1).

### CVM sanctioning-proceedings dataset

- `https://dados.cvm.gov.br/dados/PROCESSO/SANCIONADOR/DADOS/processo_sancionador.zip`, consulted on 2026-11-06 at 17:29 UTC. SHA256 `19e9400d0c8e77f30b1aa927c45147152cbcceffa0a6b936df9cff8e43482b42`.
- Dictionary: `https://dados.cvm.gov.br/dados/PROCESSO/SANCIONADOR/META/meta_processo_sancionador.zip`.
- 584 proceedings, opened from 2013-03 onwards. The dataset gives number, subject, opening date and stage, not the outcome. Used to check the portal's coverage and for Fibam's `data_publica`.

### CVM decisions read for `data/gabarito_candidatos.csv`

Main source of each new or corrected row. In every case I read the session summary or the vote (PDF).

| Case | Proceeding | URL |
| --- | --- | --- |
| `inepar_2013` | CVM proceeding RJ2014/7072 | https://conteudo.cvm.gov.br/export/sites/cvm/sancionadores/sancionador/anexos/2018/RJ20147072_INEPAR.pdf |
| `docas_imbituba` | CVM proceeding RJ2016/5649 (SEI 19957.003408/2016-38) | https://conteudo.cvm.gov.br/export/sites/cvm/sancionadores/sancionador/anexos/2018/RJ20165649__Completo.pdf |
| `inepar_equipamentos` | CVM proceeding RJ2014/7351 | https://conteudo.cvm.gov.br/export/sites/cvm/sancionadores/sancionador/anexos/2018/RJ20147351__Completo.pdf |
| `petrobras` | CVM proceeding SP2017/294 (SEI 19957.005789/2017-71) | https://conteudo.cvm.gov.br/export/sites/cvm/sancionadores/sancionador/anexos/2020/SEI_19957005789_2017_71.pdf |
| `recrusul` | CVM proceeding SEI 19957.007552/2016-43 (RJ2016/7929) | https://conteudo.cvm.gov.br/export/sites/cvm/sancionadores/sancionador/anexos/2020/SEI_19957007552_2016_43.pdf |
| `springer` | CVM proceeding SEI 19957.010686/2017-22 (RJ2017/5122) | https://conteudo.cvm.gov.br/export/sites/cvm/sancionadores/sancionador/anexos/2020/SEI_19957010686_2017_22.pdf |
| `brazal` | CVM proceeding RJ2015/13326 | https://conteudo.cvm.gov.br/export/sites/cvm/sancionadores/sancionador/anexos/2018/RJ201513326COMPLETO.pdf |
| `ceb` | CVM proceeding SEI 19957.009292/2017-21 | https://conteudo.cvm.gov.br/export/sites/cvm/sancionadores/sancionador/anexos/2021/SEI_19957009292_2017_21.pdf |
| `fibam` | CVM proceeding SEI 19957.009140/2018-18 | https://www.gov.br/cvm/pt-br/assuntos/noticias/anexos/2022/20220621_PAS_CVM_19957_009140_2018_18_voto_diretor_alexandre_rangel.pdf |
| `marina_iracema` | CVM proceeding RJ2014/918 | https://conteudo.cvm.gov.br/export/sites/cvm/sancionadores/sancionador/anexos/2014/20141104_PAS_RJ2014918.pdf |
| `metalgrafica_iguacu` | CVM proceeding RJ2012/15235 | https://conteudo.cvm.gov.br/export/sites/cvm/sancionadores/sancionador/anexos/2016/20160322_PAS_RJ201215235.pdf |
| `sultepa_2013` | CVM proceeding RJ2015/1823 | https://conteudo.cvm.gov.br/export/sites/cvm/sancionadores/sancionador/anexos/2016/20160802_PAS_RJ20151823.pdf |
| `cafe_soluvel_brasilia` | CVM proceeding RJ2014/1442 | https://conteudo.cvm.gov.br/export/sites/cvm/sancionadores/sancionador/anexos/2015/20150602_PAS_RJ20141442.pdf |
| `comercial_quintella` | CVM proceeding RJ2015/4456 | https://conteudo.cvm.gov.br/export/sites/cvm/sancionadores/sancionador/anexos/2017/RJ20154456_Comercial_Quintella.pdf |
| `cobrasma` | CVM proceeding RJ2016/2159 | https://conteudo.cvm.gov.br/export/sites/cvm/sancionadores/sancionador/anexos/2017/RJ20162159_Cobrasma.pdf |
| `bahema` | CVM proceeding SP2017/493 | https://conteudo.cvm.gov.br/export/sites/cvm/sancionadores/sancionador/anexos/2018/SP2017-493.pdf |
| `jb_duarte` | CVM proceeding SEI 19957.003864/2016-88 (RJ2016/5786) | https://www.gov.br/cvm/pt-br/assuntos/noticias/anexos/2021/20210622_PAS_CVM_SEI_19957_003864_2016_88_voto_diretor_alexandre_rangel.pdf |
| `brasil_telecom` | CVM proceeding 03/2011 | https://conteudo.cvm.gov.br/export/sites/cvm/sancionadores/sancionador/anexos/2018/03-2011.pdf |
| `sanepar` | CVM proceeding 08/2012 | https://conteudo.cvm.gov.br/export/sites/cvm/sancionadores/sancionador/anexos/2014/20141216_PAS_082012.pdf |
| `jc_barretto` | CVM proceeding RJ2013/1402 | https://conteudo.cvm.gov.br/export/sites/cvm/sancionadores/sancionador/anexos/2014/20140722_PAS_RJ20131402.pdf |
| `mendes_junior` | CVM proceeding 14/2009 | https://conteudo.cvm.gov.br/export/sites/cvm/sancionadores/sancionador/anexos/2015/20150811_PAS_142009.pdf |
| `sultepa_2003` | CVM proceeding 16/2010 | https://conteudo.cvm.gov.br/export/sites/cvm/sancionadores/sancionador/anexos/2018/162010__COMPLETO.pdf |
| `beter` | CVM proceeding RJ2010/14248 | https://conteudo.cvm.gov.br/export/sites/cvm/sancionadores/sancionador/anexos/2012/20121030_PAS_RJ201014248.pdf |
| `inepar_2006` | CVM sanctioning proceeding 17/2006 | https://conteudo.cvm.gov.br/export/sites/cvm/sancionadores/sancionador/anexos/2013/20131022_PAS_172006.pdf |

Other sources used:
- Petrobras, final outcome (2010 only): https://istoedinheiro.com.br/cvm-condena-ex-diretores-da-petrobras-nos-casos-da-refinaria-abreu-lima-e-comperj
- Fibam: https://www.gov.br/cvm/pt-br/assuntos/noticias/2022/cvm-julga-processos-envolvendo-fibam-companhia-industrial and commissioner Flávia Perlingeiro's separate vote (https://www.gov.br/cvm/pt-br/assuntos/noticias/anexos/2022/20220621_PAS_CVM_19957_009140_2018_18_manifestacao_de_voto_diretora_flavia_perlingeiro.pdf).
- J.B. Duarte, report: https://www.gov.br/cvm/pt-br/assuntos/noticias/anexos/2021/20210622_PAS_CVM_SEI_19957_003864_2016_88_relatorio_diretor_alexandre_rangel.pdf
- Verolme-Ishibrás, set aside: https://conteudo.cvm.gov.br/sancionadores/sancionador/2019/20191105-PAS-13-2014.html
- CVM codes and CNPJs came from the listed-company registry. J.B. Duarte (now Blue Tech Solutions EQI S.A.) came from the 2012, 2015 and 2016 FCA and the registry. J. C. Barretto Fertilizantes was not found in the registry or the FCA.

### CVM's ENET system, HTML route

- Filing page: `https://www.rad.cvm.gov.br/ENET/frmGerenciaPaginaFRE.aspx?NumeroSequencialDocumento=<n>&CodigoTipoInstituicao=2`, opened in a cookie session.
- Tables: `https://www.rad.cvm.gov.br/ENET/frmDemonstracaoFinanceiraITR.aspx?...`, with the address taken from the filing page and that page as the Referer.
- Parameters: `Demonstracao` (2 balance sheet assets, 3 liabilities, 4 income statement, 99 cash flow) and `Informacao` (2 consolidated, 1 individual).
- Consulted on 2026-11-06, around 17:50 UTC, with `scripts/fase0/enet_html.py`. Filings of the 2023 DFPs of codes 27499, 27766 and 20125, and IRB's (24180) 2019 DFP, version 1, for row counts only.
