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

Fonte do setor de cada ano (Emenda 5). O arquivo de 2012 foi baixado em 05/11/2026 às 02:12 UTC; os outros, no mesmo dia, às 20:43 UTC (17:43 em Brasília). Os dois downloads de 2012 deram o mesmo hash.

Listagem: https://dados.cvm.gov.br/dados/CIA_ABERTA/DOC/FCA/DADOS/ · URL de cada arquivo: `https://dados.cvm.gov.br/dados/CIA_ABERTA/DOC/FCA/DADOS/fca_cia_aberta_AAAA.zip`

| Ano | Gerado em | SHA-256 |
| --- | --- | --- |
| 2010 | 04/03/2024 | `9a9b933fa02c96f7cf632dbb1f7b004bb78696c81c989792b1eb60f70b001021` |
| 2011 | 04/03/2024 | `f5c7aaa2a4464b4232a05d77c288d33bca5474edd72199a9295d6fa2a34012e8` |
| 2012 | 04/03/2024 | `ba68b8e8c12b74fc56bf76a75ae582aa53e5adef1d61d940d5191c55b9be2e06` |
| 2013 | 04/03/2024 | `d62ef489d8c1208ef3d41cfd25a093b8fcb5f6b47640e59288aece45d4962cce` |
| 2014 | 04/03/2024 | `1f70b5e3a544535affb47b04a0c60a618bef872bc783e6909940d2e7dad89e3f` |
| 2015 | 04/03/2024 | `74326a566c405d703b56af257c9fade687f112f372ae68b8624719becc8215f2` |
| 2016 | 04/03/2024 | `229b2cfc8c0ac5e60083932381364bbdb6666f028422c13a1ac5f6dccc9e3e6c` |
| 2017 | 04/03/2024 | `48127cf15d8baf4d31b9544b266f9511962db158d591fc9803e335a8ab081d45` |
| 2018 | 04/03/2024 | `b20056b00927c5261ba587b668e52e4cdfe2d989e7d794491b2bb127fbd0a8cd` |
| 2019 | 04/03/2024 | `09f84e5f5485217c8b36f8379c36f718dbdcd6d6908b4e96b68861394e76fe97` |
| 2020 | 29/12/2024 | `ccf2ac081747da9ccefa50349a5494c263763d5dd8bb961565fd2ae64c264b20` |
| 2021 | 28/12/2025 | `65ba4b0225e9b2106901cdf348215933be8affba79925fc71361e2f6818c7999` |
| 2022 | 01/11/2026 | `1cf67f61d3fae38ae09e4bc333c9dada9eb30617abf4128350a23d5b0e4edeea` |
| 2023 | 01/11/2026 | `62b09231d90e9140f1fa17b36432c24e50e80eaf684ba8cdbadc74626b8956a7` |
| 2024 | 01/11/2026 | `fac9d73d0a6bd817aea969db48a71b18471f17d1a283b359f92479c22a2a25d5` |
| 2025 | 01/11/2026 | `a1923e812ae255ea195d91baf30a5771e73cf39b7a03463a139d2883a9be14b9` |
| 2026 | 01/11/2026 | `7cc2ed67a931f1056be04856fb20de2fb5184820bbadb05b82dab5dffb879c2f` |

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

## 05/11/2026 · autorizações e gabarito ampliado (depois do congelamento)

### Sistema ENET da CVM, segundo teste

- Pacotes de versões antigas, pelo `LINK_DOC` do índice da DFP: testados em 05/11/2026 às 20h–21h UTC, com curl e com `scripts/fase0/enet_teste.py`. Nenhum chegou inteiro (ver `reconhecimento.md`, parte 5.4).
- Visualização HTML de cada documento: `https://www.rad.cvm.gov.br/ENET/frmGerenciaPaginaFRE.aspx?NumeroSequencialDocumento=<n>&CodigoTipoInstituicao=2`. Respondeu com HTTP 200 nos três documentos testados.

### Decisões da CVM e fatos relevantes lidos para `data/gabarito_candidatos.csv`

Consulta em 05/11/2026. Cada caso do arquivo traz a sua fonte principal e, quando houver, uma secundária. Documentos lidos no texto integral (PDF):

| Caso | Documento | URL |
| --- | --- | --- |
| Banco Panamericano | Extrato, PAS CVM 01/2011 | https://conteudo.cvm.gov.br/export/sites/cvm/sancionadores/sancionador/anexos/2018/012011_Banco_Panamericanocx.pdf |
| Via Varejo | Fato relevante de 12/12/2019 | https://api.mziq.com/mzfilemanager/v2/d/ce9bff9f-fb19-49b9-9588-c4c6b7052c9c/ff43ced3-e5c7-a49a-f33d-57fa4a9fdb4c?origin=1 |
| Taurus | Voto, PAS CVM RJ2014/13977 | https://conteudo.cvm.gov.br/export/sites/cvm/noticias/anexos/2020/20200130_PAS_CVM_RJ2014_13977_voto_diretor_gustavo_gonzalez.pdf |
| OGX | Extrato e decisão, PAS CVM RJ2014/12838 | https://conteudo.cvm.gov.br/export/sites/cvm/sancionadores/sancionador/anexos/2018/RJ201412838__COMPLETO.pdf |
| OSX | Extrato e decisão, PAS CVM RJ2015/1421 | https://conteudo.cvm.gov.br/export/sites/cvm/sancionadores/sancionador/anexos/2018/20190625_PAS_RJ20151421.pdf |
| Metalúrgica Duque | Extrato e decisão, PAS CVM RJ2014/4077 | https://conteudo.cvm.gov.br/export/sites/cvm/sancionadores/sancionador/anexos/2018/RJ20144077__COMPLETO.pdf |
| Mundial (2016) | Extrato, PAS CVM RJ2013/6224 | https://conteudo.cvm.gov.br/export/sites/cvm/sancionadores/sancionador/anexos/2016/20160513_PAS_RJ20136224.pdf |
| Mundial (2017) e Hércules | Extrato, PAS CVM RJ2017/565 | https://conteudo.cvm.gov.br/export/sites/cvm/sancionadores/sancionador/anexos/2017/RJ2017565_Mundial_SA.pdf |
| Teka | Extrato, PAS CVM RJ2015/6229 | https://conteudo.cvm.gov.br/export/sites/cvm/sancionadores/sancionador/anexos/2018/RJ20156229_TEKA.pdf |
| IGB Eletrônica | Extrato, PAS CVM RJ2015/6280 | https://conteudo.cvm.gov.br/export/sites/cvm/sancionadores/sancionador/anexos/2018/RJ20156280_IGB_Eletronica_.pdf |
| Tecnosolo | Extrato, PAS CVM RJ2015/2651 | https://conteudo.cvm.gov.br/export/sites/cvm/sancionadores/sancionador/anexos/2017/RJ20152651_Tecnosolo_vf.pdf |
| Schlosser | Extrato, PAS CVM RJ2014/12056 | http://conteudo.cvm.gov.br/export/sites/cvm/sancionadores/sancionador/anexos/2017/RJ201412056_Cia_Industrial_Schlosser.pdf |
| Brasil Brokers | Voto, PAS CVM 19957.009415/2019-96 | https://www.gov.br/cvm/pt-br/assuntos/noticias/anexos/2021/20210316_PAS_CVM_19957_0094152019_96_SP2019_617_voto_presidente_marcelo_barbosa.pdf |
| Oi (DFs de 2014) | Extrato, PAS CVM 19957.004416/2016-00 | https://conteudo.cvm.gov.br/export/sites/cvm/sancionadores/sancionador/anexos/2023/SEI_19957004416_2016_00_1.pdf |
| Oi (DFs de 2015 e 2016), não incluído | Relatório, PAS CVM 19957.004207/2021-15 | https://www.gov.br/cvm/pt-br/assuntos/noticias/anexos/2026/20260825-pas-cvm-19957-004207-2021-15-relatorio-diretora-marina-copola.pdf |
| IRB (contabilidade de 2019), caso existente | Voto do relator, PAS CVM 19957.003588/2023-87 | https://www.gov.br/cvm/pt-br/assuntos/noticias/anexos/2026/20261006-pas-cvm-19957-003588-2023-87-diretor-igor-muniz-voto.pdf |

Processos lidos e descartados por não tratarem do conteúdo das DFs ou por tratarem só de atraso: RJ2014/5099 (WLM), 19957.003052/2018-02 (GPC Participações), 19957.003549/2018-12 (J&F), 19957.008462/2019-12, 19957.001933/2021-86 (Intrader DTVM), 19957.010135/2018-40 (Companhia Aurífera Brasileira), RJ2016/5786 (relatório de J.B. Duarte, sem a decisão) e a decisão 1510/19 sobre o FIDC ligado ao Banco Cruzeiro do Sul, todos no portal de processos sancionadores e decisões da CVM (`conteudo.cvm.gov.br`).

## 06/11/2026 · varredura dos processos sancionadores e teste da rota HTML do ENET (depois do congelamento v4)

### Processos sancionadores julgados (portal da CVM)

- Busca por data, ano a ano de 2010 a 2026 e página a página: `https://conteudo.cvm.gov.br/sancionadores/index.html?lastName=&dataInicio=01/01/<ano>&dataFim=31/12/<ano>&buscado=true&pasta=sancionador&contCategoriasCheck=1&filtro=todos&vimDaCategoria=/sancionadores/sancionador/&searchPage=<n>`. O portal recusa o agente padrão do Python, e por isso o script manda um User-Agent genérico.
- Depois, a página de cada processo (`https://conteudo.cvm.gov.br/sancionadores/sancionador/<ano>/...html`), com a ementa completa e os links dos PDFs.
- Consulta em 06/11/2026, por volta das 17h30–18h UTC, com `scripts/fase0/varredura_pas.py`. Resultado: 776 processos julgados de 2010 a 2025 (ver `reconhecimento.md`, parte 7.1).

### Base de dados de processos sancionadores da CVM

- `https://dados.cvm.gov.br/dados/PROCESSO/SANCIONADOR/DADOS/processo_sancionador.zip`, consultada em 06/11/2026 às 17:29 UTC. SHA256 `19e9400d0c8e77f30b1aa927c45147152cbcceffa0a6b936df9cff8e43482b42`.
- Dicionário: `https://dados.cvm.gov.br/dados/PROCESSO/SANCIONADOR/META/meta_processo_sancionador.zip`.
- 584 processos, abertos de 03/2013 em diante. A base traz número, objeto, data de abertura e fase, sem o resultado. Usada para conferir a cobertura do portal e para a `data_publica` da Fibam.

### Decisões da CVM lidas para `data/gabarito_candidatos.csv`

Fonte principal de cada linha nova ou corrigida. Em todos os casos li o extrato da sessão ou o voto (PDF).

| Caso | Processo | URL |
| --- | --- | --- |
| `inepar_2013` | PAS CVM RJ2014/7072 | https://conteudo.cvm.gov.br/export/sites/cvm/sancionadores/sancionador/anexos/2018/RJ20147072_INEPAR.pdf |
| `docas_imbituba` | PAS CVM RJ2016/5649 (SEI 19957.003408/2016-38) | https://conteudo.cvm.gov.br/export/sites/cvm/sancionadores/sancionador/anexos/2018/RJ20165649__Completo.pdf |
| `inepar_equipamentos` | PAS CVM RJ2014/7351 | https://conteudo.cvm.gov.br/export/sites/cvm/sancionadores/sancionador/anexos/2018/RJ20147351__Completo.pdf |
| `petrobras` | PAS CVM SP2017/294 (SEI 19957.005789/2017-71) | https://conteudo.cvm.gov.br/export/sites/cvm/sancionadores/sancionador/anexos/2020/SEI_19957005789_2017_71.pdf |
| `recrusul` | PAS CVM SEI 19957.007552/2016-43 (RJ2016/7929) | https://conteudo.cvm.gov.br/export/sites/cvm/sancionadores/sancionador/anexos/2020/SEI_19957007552_2016_43.pdf |
| `springer` | PAS CVM SEI 19957.010686/2017-22 (RJ2017/5122) | https://conteudo.cvm.gov.br/export/sites/cvm/sancionadores/sancionador/anexos/2020/SEI_19957010686_2017_22.pdf |
| `brazal` | PAS CVM RJ2015/13326 | https://conteudo.cvm.gov.br/export/sites/cvm/sancionadores/sancionador/anexos/2018/RJ201513326COMPLETO.pdf |
| `ceb` | PAS CVM SEI 19957.009292/2017-21 | https://conteudo.cvm.gov.br/export/sites/cvm/sancionadores/sancionador/anexos/2021/SEI_19957009292_2017_21.pdf |
| `fibam` | PAS CVM SEI 19957.009140/2018-18 | https://www.gov.br/cvm/pt-br/assuntos/noticias/anexos/2022/20220621_PAS_CVM_19957_009140_2018_18_voto_diretor_alexandre_rangel.pdf |
| `marina_iracema` | PAS CVM RJ2014/918 | https://conteudo.cvm.gov.br/export/sites/cvm/sancionadores/sancionador/anexos/2014/20141104_PAS_RJ2014918.pdf |
| `metalgrafica_iguacu` | PAS CVM RJ2012/15235 | https://conteudo.cvm.gov.br/export/sites/cvm/sancionadores/sancionador/anexos/2016/20160322_PAS_RJ201215235.pdf |
| `sultepa_2013` | PAS CVM RJ2015/1823 | https://conteudo.cvm.gov.br/export/sites/cvm/sancionadores/sancionador/anexos/2016/20160802_PAS_RJ20151823.pdf |
| `cafe_soluvel_brasilia` | PAS CVM RJ2014/1442 | https://conteudo.cvm.gov.br/export/sites/cvm/sancionadores/sancionador/anexos/2015/20150602_PAS_RJ20141442.pdf |
| `comercial_quintella` | PAS CVM RJ2015/4456 | https://conteudo.cvm.gov.br/export/sites/cvm/sancionadores/sancionador/anexos/2017/RJ20154456_Comercial_Quintella.pdf |
| `cobrasma` | PAS CVM RJ2016/2159 | https://conteudo.cvm.gov.br/export/sites/cvm/sancionadores/sancionador/anexos/2017/RJ20162159_Cobrasma.pdf |
| `bahema` | PAS CVM SP2017/493 | https://conteudo.cvm.gov.br/export/sites/cvm/sancionadores/sancionador/anexos/2018/SP2017-493.pdf |
| `jb_duarte` | PAS CVM SEI 19957.003864/2016-88 (RJ2016/5786) | https://www.gov.br/cvm/pt-br/assuntos/noticias/anexos/2021/20210622_PAS_CVM_SEI_19957_003864_2016_88_voto_diretor_alexandre_rangel.pdf |
| `brasil_telecom` | PAS CVM 03/2011 | https://conteudo.cvm.gov.br/export/sites/cvm/sancionadores/sancionador/anexos/2018/03-2011.pdf |
| `sanepar` | PAS CVM 08/2012 | https://conteudo.cvm.gov.br/export/sites/cvm/sancionadores/sancionador/anexos/2014/20141216_PAS_082012.pdf |
| `jc_barretto` | PAS CVM RJ2013/1402 | https://conteudo.cvm.gov.br/export/sites/cvm/sancionadores/sancionador/anexos/2014/20140722_PAS_RJ20131402.pdf |
| `mendes_junior` | PAS CVM 14/2009 | https://conteudo.cvm.gov.br/export/sites/cvm/sancionadores/sancionador/anexos/2015/20150811_PAS_142009.pdf |
| `sultepa_2003` | PAS CVM 16/2010 | https://conteudo.cvm.gov.br/export/sites/cvm/sancionadores/sancionador/anexos/2018/162010__COMPLETO.pdf |
| `beter` | PAS CVM RJ2010/14248 | https://conteudo.cvm.gov.br/export/sites/cvm/sancionadores/sancionador/anexos/2012/20121030_PAS_RJ201014248.pdf |
| `inepar_2006` | Processo Sancionador CVM 17/2006 | https://conteudo.cvm.gov.br/export/sites/cvm/sancionadores/sancionador/anexos/2013/20131022_PAS_172006.pdf |

Outras fontes usadas:
- Petrobras, resultado final (só 2010): https://istoedinheiro.com.br/cvm-condena-ex-diretores-da-petrobras-nos-casos-da-refinaria-abreu-lima-e-comperj
- Fibam: https://www.gov.br/cvm/pt-br/assuntos/noticias/2022/cvm-julga-processos-envolvendo-fibam-companhia-industrial e a manifestação de voto da diretora Flávia Perlingeiro (https://www.gov.br/cvm/pt-br/assuntos/noticias/anexos/2022/20220621_PAS_CVM_19957_009140_2018_18_manifestacao_de_voto_diretora_flavia_perlingeiro.pdf).
- J.B. Duarte, relatório: https://www.gov.br/cvm/pt-br/assuntos/noticias/anexos/2021/20210622_PAS_CVM_SEI_19957_003864_2016_88_relatorio_diretor_alexandre_rangel.pdf
- Verolme-Ishibrás, descartado: https://conteudo.cvm.gov.br/sancionadores/sancionador/2019/20191105-PAS-13-2014.html
- Código CVM e CNPJ vieram do cadastro de companhias abertas. A J.B. Duarte (hoje Blue Tech Solutions EQI S.A.) veio do FCA de 2012, 2015 e 2016 e do cadastro. A J. C. Barretto Fertilizantes não foi achada no cadastro nem no FCA.

### Sistema ENET da CVM, rota HTML

- Página do documento: `https://www.rad.cvm.gov.br/ENET/frmGerenciaPaginaFRE.aspx?NumeroSequencialDocumento=<n>&CodigoTipoInstituicao=2`, aberta numa sessão com cookie.
- Tabelas: `https://www.rad.cvm.gov.br/ENET/frmDemonstracaoFinanceiraITR.aspx?...`, com o endereço tirado da página do documento e o Referer dessa página.
- Parâmetros: `Demonstracao` (2 BPA, 3 BPP, 4 DRE, 99 DFC) e `Informacao` (2 consolidado, 1 individual).
- Consulta em 06/11/2026, por volta das 17h50 UTC, com `scripts/fase0/enet_html.py`. Documentos das DFPs de 2023 dos códigos 27499, 27766 e 20125, e da DFP de 2019 do IRB (24180), versão 1, só para contagem de linhas.

## 07/11/2026 · Fase 1: download e base "como era na época"

- **Dados abertos da CVM:** DFP anual de 2010 a 2026, FCA de 2010 a 2026, cadastro de companhias abertas e os dicionários da DFP, do FCA e do cadastro, baixados por `python -m chiocca.dados baixar` em 07/11/2026. URL, tamanho, SHA256 e hora de cada arquivo estão em [`data/manifesto_brutos.csv`](../data/manifesto_brutos.csv). Em relação ao download da Fase 0 (05/11/2026), só o cadastro mudou.
- **Dicionário do FCA:** `https://dados.cvm.gov.br/dados/CIA_ABERTA/DOC/FCA/META/fca_cia_aberta.zip`.
- **ENET, rota HTML (só consolidado, emenda 8):** `https://www.rad.cvm.gov.br/ENET/frmGerenciaPaginaFRE.aspx?NumeroSequencialDocumento=<n>&CodigoTipoInstituicao=2` e as tabelas em `frmDemonstracaoFinanceiraITR.aspx`, consultadas em 07/11/2026 por `python -m chiocca.enet`. A lista de documentos fica em `data/cache/enet/pendentes.txt` e as tabelas em `data/cache/enet/` (fora do git). Quantos documentos e o resultado estão em [`base.md`](base.md).

## 07/11/2026 · Fase 2: CDI para o juro implícito

- **Série:** Banco Central do Brasil, SGS, código **4389**, "Taxa de juros - CDI anualizada base 252", diária, em % a.a.
- **URL:** `https://api.bcb.gov.br/dados/serie/bcdata.sgs.4389/dados?formato=json&dataInicial=01/01/2009&dataFinal=31/12/2025`, em blocos de cinco anos, consultada em 07/11/2026 às 04:46 UTC por `python -m chiocca.cdi`.
- **Snapshot versionado:** [`data/cdi_sgs4389.csv`](../data/cdi_sgs4389.csv), 4.269 dias de 02/01/2009 a 31/12/2025, SHA256 `aecfe83578f6850c42fc9fd9d945916f9103c56b5a09d524bfc38fd557ad5dcb`.
- **Conferência da série:** a página de metadados do SGS (`www3.bcb.gov.br/sgspub/consultarmetadados/...hdOidSerieMetadados=4389`) devolveu erro 502 nas três tentativas de 07/11/2026. A identificação foi conferida nos próprios dados: em 05/01/2015, a série 4389 vale 11,57% a.a., igual à série 12 (CDI, % a.d.) anualizada em 252 dias úteis, e diferente da Selic anualizada (série 1178, 11,65% a.a.).
- **Uso:** "CDI médio do ano" é a média simples das taxas diárias nos 12 meses que terminam na data de referência da DFP (`chiocca/cdi.py`).

## 07/11/2026 · Explicação depois do resultado: incorporação da Lojas Americanas pela B2W

Usado só na análise descritiva (a) de [`docs/resultados.md`](resultados.md), feita depois de ver os resultados e rotulada como "explicação depois do resultado, não teste".

- **Índice IPE da CVM de 2021:** `https://dados.cvm.gov.br/dados/CIA_ABERTA/DOC/IPE/DADOS/ipe_cia_aberta_2021.zip`, consultado em 07/11/2026. SHA256 `b5ad4dcc2c0376027a23ed372469feaea11bf0dfd7ac75e2bbe99fd6b8f78ee7`. Os documentos abaixo vêm do ENET, pelo `Link_Download` das linhas do código CVM 20990 (B2W – Companhia Digital, CNPJ 00.776.574/0006-60, depois Americanas S.A.).
- **Fato relevante de 19/02/2021** (protocolo 833599), potencial combinação operacional dos negócios de Lojas Americanas e B2W. SHA256 `b908c6b35f161c86fc632faf0e4750fed6813be06c4cae7d1591c359cce1e877`.
- **Fato relevante de 28/04/2021** (protocolo 858751, versão 2): protocolo da cisão parcial da Lojas Americanas com versão do acervo cindido para a B2W; "todos os ativos operacionais de Lojas Americanas e passivos a eles relacionados" vertidos pelo valor contábil de 31/12/2020, e "as variações patrimoniais relativas aos elementos que compõem o Acervo Cindido, apuradas a partir da mesma data base", apropriadas pela B2W. SHA256 `298cc4babae20cc142626d33ad1b01ec38ba17b3f87b1a4a58802d32eabbd638`.
- **Ata da assembleia geral extraordinária da B2W de 10/06/2021** (protocolo 875411): aprova a cisão parcial com incorporação do acervo cindido, efetivada "linha a linha", e a nova denominação "americanas s.a."; as novas ações "participarão integralmente dos resultados do exercício social em curso". SHA256 `fbd901da26543fe9d1aeee4e829ac88fd2ec7db8c28da31d70a883ba1bb71b7c`.
- **Números usados:** as DFPs de 2020 e 2021 do código 20990 e a DFP de 2020 do código 8087, da base "como era na época" (Fase 1). Para as duas leituras, a DFP de 2022 do código 20990 (versão 1, entregue em 16/11/2023), dos dados abertos já listados no manifesto.

## 11/11/2026 · Fase F1: notas explicativas, relatório do auditor e Formulário de Referência

- **Notas explicativas (ENET):** não estão nos dados abertos da DFP. Vêm do ENET, na página do documento (`https://www.rad.cvm.gov.br/ENET/frmGerenciaPaginaFRE.aspx?NumeroSequencialDocumento=<n>&CodigoTipoInstituicao=2`), pelo grupo "Notas Explicativas" (postback do ASP.NET), que devolve `frmExibirArquivoFRE.aspx` com o PDF anexado pela companhia em base64. É o mesmo arquivo do pacote do documento (`frmDownloadDocumento.aspx`): mesmo SHA256 (`a8a14bde47a708a265bcf406a3916b006777f96fa80609bf6055e6714c807f6f`) na DFP de 2021 da Americanas (documento 112049). O pacote, de 10 MB, veio cortado pelo servidor nas três tentativas de 11/11/2026; por isso a rota é a da página do documento.
- **Relatório do auditor (ENET):** o grupo "Pareceres e Declarações" da mesma página traz o texto de cada versão, com o tipo no título do item ("Relatório do Auditor Independente - Sem Ressalva").
- **Formulário de Referência (dados abertos):** `https://dados.cvm.gov.br/dados/CIA_ABERTA/DOC/FRE/DADOS/fre_cia_aberta_<ano>.zip`, de 2010 a 2024, baixados por `python -m chiocca.dados baixar-fre` em 11/11/2026, com tamanho e SHA256 no manifesto (`data/manifesto_brutos.csv`). O arquivo `fre_cia_aberta_transacao_parte_relacionada_<ano>.csv` só tem a última versão de cada companhia no ano; aspas soltas dentro dos campos impedem a leitura com aspas, e toda linha física tem o número de campos do cabeçalho.
- **Cadastro para as exceções de nomes:** `data/leitor/companhias_cadastro.txt`, gerado de `cad_cia_aberta.csv` (o SHA256 do manifesto vai no cabeçalho do arquivo).

## 12/11/2026 · Fase F2a: fatos relevantes, comunicados e monitor

- **IPE (dados abertos):** `https://dados.cvm.gov.br/dados/CIA_ABERTA/DOC/IPE/DADOS/ipe_cia_aberta_<ano>.zip`, de 2010 a 2024, baixados por `python -m chiocca.dados baixar-ipe` em 12/11/2026, com tamanho e SHA256 no manifesto (`data/manifesto_brutos.csv`). Cada arquivo tem `ipe_cia_aberta_<ano>.csv`, com uma linha por entrega (protocolo e versão) feita no ano: código CVM sem zeros à esquerda, categoria, tipo, assunto, data de entrega, protocolo, versão e link do documento no ENET. Só esses metadados são usados; o conteúdo dos documentos não é baixado.
- **Índices de DFP e ITR para o monitor:** `dfp_cia_aberta_<ano>.csv` e `itr_cia_aberta_<ano>.csv`, lidos por faixas de bytes (HTTP Range) de dentro de `https://dados.cvm.gov.br/dados/CIA_ABERTA/DOC/<DFP|ITR>/DADOS/<dfp|itr>_cia_aberta_<ano>.zip`; o servidor respondeu com `accept-ranges: bytes` em 12/11/2026.
