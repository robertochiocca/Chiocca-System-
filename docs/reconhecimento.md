Pré-registro congelado no commit 6cc1d5f5d365e4923ec422d34130f5977b0ac7c3, enviado ao GitHub em 04/11/2026 às 23:11:52 (horário de Brasília; 05/11/2026 02:11:52 UTC), antes de baixar qualquer dado.

# Reconhecimento dos dados abertos da CVM (Fase 0)

Consulta feita em 05/11/2026, a partir das 02:12 UTC (04/11/2026, 23:12 em Brasília). URLs e hashes dos arquivos estão em [`fontes.md`](fontes.md).

**Como a Fase 0 foi feita**

- Só estrutura. Nenhum sinal, índice ou M-score foi calculado. A coluna `VL_CONTA` não foi carregada em nenhum script: os valores das contas não entraram na memória.
- Antes de qualquer análise, todas as linhas destes códigos CVM foram removidas: 8087 (Lojas Americanas SA), 20990 (Americanas S.A.), 24180 (IRB-Brasil Resseguros) e 22837 (Drogarias Americanas SA, removida só por ter "Americanas" no nome). Nada dessas empresas foi aberto, nem a estrutura.
- Os números abaixo são contagens de estrutura (empresas, linhas, presença de contas), saídas de scripts da Fase 0 que ficaram fora do repositório.
- Os arquivos baixados ficaram fora do repositório. Nada foi gravado em `data/`.

## 1. O que foi confirmado

### 1.1 Arquivos e anos

- **DFP:** um zip por ano, `dfp_cia_aberta_AAAA.zip`, de **2010 a 2026**. O primeiro ano é **2010**; o último completo é **2025**. O arquivo de 2026 tem 9 documentos, todos de exercícios que não terminam em 31/12.
- **Conteúdo de cada zip:** o índice de documentos (`dfp_cia_aberta_AAAA.csv`), BPA, BPP, DRE, DRA, DFC_MD, DFC_MI, DMPL e DVA, cada um em versão consolidada (`_con`) e individual (`_ind`), mais `parecer`. O arquivo `composicao_capital` está em 2023 e 2025, mas não em 2010 nem em 2019 (os outros anos não foram conferidos).
- **Os arquivos são regerados pela CVM.** Pela listagem do servidor, os zips de 2010 a 2019 foram gerados em 05/08/2024, o de 2020 em 29/12/2024, o de 2021 em 28/12/2025 e os de 2022 a 2026 em 01/11/2026. O conteúdo baixado hoje pode não ser igual ao de outra data, e por isso os hashes estão em `fontes.md`.
- **Dicionário de dados:** `meta_dfp_cia_aberta_txt.zip`, com 11 arquivos (índice, BPA, BPP, DFC_MD, DFC_MI, DMPL, DRA, DRE, DVA, composição do capital e parecer).
- **Consolidado e individual:** muitas empresas só entregam a individual.

  | DFP | Empresas com DRE individual | Com DRE consolidada | Só individual | Só consolidada |
  | --- | --- | --- | --- | --- |
  | 2012 | 652 | 361 | 298 | 7 |
  | 2019 | 663 | 382 | 284 | 3 |
  | 2023 | 725 | 472 | 258 | 5 |

- **DFC:** a maioria usa o método indireto (`DFC_MI`). O método direto (`DFC_MD`) aparece em 186 empresa-anos no consolidado e em 367 no individual, de 2010 a 2025.

### 1.2 Colunas

| Coluna | Onde | Significado (dicionário) | O que os arquivos mostram |
| --- | --- | --- | --- |
| `CD_CVM`, `CNPJ_CIA`, `DENOM_CIA` | todos | código CVM, CNPJ e nome da companhia | |
| `DT_REFER` | todos | data de referência do documento | em geral 31/12; de 0 a 21 empresa-anos por ano têm outra data |
| `VERSAO` | todos | versão do documento | no índice vai de 1 a 9; ver 1.3 |
| `DT_RECEB` | **só no índice** | data do recebimento do documento (AAAA-MM-DD) | uma data por versão |
| `ID_DOC`, `LINK_DOC` | só no índice | identificador e endereço de download do documento | cada versão tem os seus; o link aponta para o sistema ENET da CVM (`rad.cvm.gov.br/ENETCONSULTA/frmDownloadDocumento.aspx?CodigoInstituicao=…&NumeroSequencialDocumento=…`) |
| `CATEG_DOC` | só no índice | categoria do documento | sempre "DFP" |
| `ORDEM_EXERC` | demonstrações | ordem do exercício social | só dois valores: `ÚLTIMO` (exercício de referência) e `PENÚLTIMO` (exercício anterior, comparativo). O dicionário não lista os valores; conferido no BPA, na DRE e na DFC_MI, consolidados e individuais, de 2010 a 2025 |
| `ESCALA_MOEDA` | demonstrações | escala monetária | `MIL` (4.585.846 linhas) e `UNIDADE` (240.898 linhas), nos mesmos arquivos. Nunca há duas escalas no mesmo documento (0 em 50.461). O dicionário não lista os valores |
| `MOEDA` | demonstrações | moeda | só `REAL`, nos mesmos arquivos |
| `GRUPO_DFP` | demonstrações | nome e nível de agregação da demonstração | |
| `CD_CONTA`, `DS_CONTA` | demonstrações | código e descrição da conta | hierarquia por pontos: `3.04.04` é mãe de `3.04.04.01` |
| `ST_CONTA_FIXA` | demonstrações | se a conta é fixa (S/N) | presente em todos os anos, inclusive nos arquivos de 2010 |
| `DT_INI_EXERC`, `DT_FIM_EXERC` | demonstrações | início e fim do exercício | `DT_INI_EXERC` não existe no BPA nem no BPP |
| `COLUNA_DF` | só na DMPL | coluna da demonstração | |
| `VL_CONTA` | demonstrações | valor da conta | não lido |

### 1.3 Versões: os arquivos de demonstrações só trazem a última

- **O índice guarda todas as versões.** Cada versão é uma linha, com `ID_DOC`, `LINK_DOC` e `DT_RECEB` próprios. De 2010 a 2026 há 10.825 documentos na versão 1, 2.412 na versão 2, 537 na 3 e 168 entre a 4 e a 9.
- **As demonstrações trazem uma versão só, a última.** De 2010 a 2025, nenhuma empresa-ano tem mais de uma versão no BPA, na DRE ou na DFC. Em 100% dos casos, a versão do arquivo é a maior versão do índice.
- **Consequência:** os valores das versões anteriores não estão nos arquivos de dados abertos. Quando uma empresa reentregou a DFP depois da data de corte, o número que aparece no arquivo não é o que era público na data de corte.

  Empresa-anos com DFP consolidada (BPA_con), sem Americanas e IRB. A data de corte é 30/04 do ano seguinte ao do arquivo.

  | DFP | Empresa-anos | Última versão recebida depois do corte | Dessas, com versão 1 recebida até o corte |
  | --- | --- | --- | --- |
  | 2010 | 370 | 139 | 70 |
  | 2011 | 367 | 117 | 63 |
  | 2012 | 361 | 89 | 41 |
  | 2013 | 352 | 67 | 32 |
  | 2014 | 345 | 78 | 27 |
  | 2015 | 340 | 65 | 32 |
  | 2016 | 337 | 72 | 34 |
  | 2017 | 337 | 64 | 27 |
  | 2018 | 337 | 73 | 35 |
  | 2019 | 383 | 127 | 24 |
  | 2020 | 439 | 95 | 25 |
  | 2021 | 464 | 63 | 28 |
  | 2022 | 475 | 80 | 52 |
  | 2023 | 473 | 66 | 36 |
  | 2024 | 465 | 52 | 26 |
  | 2025 | 438 | 30 | 10 |

  A última coluna conta as empresa-anos em que havia uma versão pública na data de corte, mas o arquivo traz uma versão posterior. A diferença entre as duas últimas colunas são empresa-anos sem nenhuma versão entregue até a data de corte.
- **Versões antigas na CVM:** fiz um teste com uma empresa fora do gabarito (DFP 2019, versões 1 e 2). O `LINK_DOC` de cada versão devolveu um pacote zip próprio, com um arquivo `<CD_CVM com 6 dígitos><AAAAMMDD>04<versão com 2 dígitos>.dfp`, um `AnexoDocumento.xml` e um PDF. O conteúdo do `.dfp` não foi confirmado (ver parte 3).

### 1.4 Códigos de conta do catálogo, para não financeiras

O plano de contas não financeiro foi identificado pela conta 3.01, "Receita de Venda de Bens e/ou Serviços". A base são 5.937 empresa-anos consolidadas e 10.074 individuais no BPA, BPP e DRE, e 5.774 e 9.715 na DFC_MI, de 2010 a 2025.

**Todos os códigos do catálogo foram confirmados.** Cada um é conta fixa da CVM (`ST_CONTA_FIXA = S`), aparece em 100% das empresa-anos do plano e tem a mesma descrição de 2010 a 2025.

| Variável do catálogo | Código | Descrição na CVM |
| --- | --- | --- |
| ativo_total | 1 | Ativo Total |
| ativo_circulante | 1.01 | Ativo Circulante |
| caixa_equivalentes | 1.01.01 | Caixa e Equivalentes de Caixa |
| aplicacoes_financeiras | 1.01.02 | Aplicações Financeiras |
| contas_a_receber | 1.01.03 | Contas a Receber |
| estoques | 1.01.04 | Estoques |
| ativo_nao_circulante | 1.02 | Ativo Não Circulante |
| investimentos | 1.02.02 | Investimentos |
| imobilizado | 1.02.03 | Imobilizado |
| intangivel | 1.02.04 | Intangível |
| passivo_circulante | 2.01 | Passivo Circulante |
| fornecedores | 2.01.02 | Fornecedores |
| ir_csll_a_pagar | 2.01.03 → **2.01.03.01.01** | Obrigações Fiscais → Imposto de Renda e Contribuição Social a Pagar (ver 2.2) |
| emprestimos_cp | 2.01.04 | Empréstimos e Financiamentos |
| passivo_nao_circulante | 2.02 | Passivo Não Circulante |
| emprestimos_lp | 2.02.01 | Empréstimos e Financiamentos |
| patrimonio_liquido | 2.03 | Patrimônio Líquido (individual) / Patrimônio Líquido Consolidado (consolidado) |
| receita_liquida | 3.01 | Receita de Venda de Bens e/ou Serviços |
| custo_vendas | 3.02 | Custo dos Bens e/ou Serviços Vendidos |
| resultado_bruto | 3.03 | Resultado Bruto |
| despesas_vendas | 3.04.01 | Despesas com Vendas |
| despesas_gerais_adm | 3.04.02 | Despesas Gerais e Administrativas |
| outras_receitas_operacionais | 3.04.04 | Outras Receitas Operacionais |
| ebit | 3.05 | Resultado Antes do Resultado Financeiro e dos Tributos |
| receitas_financeiras | 3.06.01 | Receitas Financeiras |
| despesas_financeiras | 3.06.02 | Despesas Financeiras |
| ir_csll_corrente | 3.08.01 | Corrente |
| lucro_operacoes_continuadas | 3.09 | Resultado Líquido das Operações Continuadas |
| lucro_liquido | 3.11 | Lucro/Prejuízo do Período (individual) / Lucro/Prejuízo Consolidado do Período (consolidado) |
| caixa_operacional | 6.01 | Caixa Líquido Atividades Operacionais (DFC_MI) |

Outras contas fixas úteis, conferidas do mesmo jeito: 2 "Passivo Total" (ver 2.6), 3.07 "Resultado Antes dos Tributos sobre o Lucro", 6.01.01 "Caixa Gerado nas Operações", 6.02 e 6.03 (caixa de investimento e de financiamento). De 2010 a 2013 há poucas descrições malformadas: a conta 1 aparece como "Ativo" em 6 empresa-anos e como "A" em 4.

### 1.5 Como identificar financeiras

- **Cadastro (`cad_cia_aberta.csv`):** 2.678 linhas para 2.567 códigos CVM (algumas empresas têm mais de uma linha). Campos úteis:
  - `SETOR_ATIV`: setor de atividade, **só o atual**;
  - `SIT`: ATIVO 754, CANCELADA 1.916, SUSPENSO(A) - DECISÃO ADM 8;
  - `DT_CANCEL` e `MOTIVO_CANCEL`.
- **Setores ligados a finanças no cadastro** (número de linhas): Bancos 115, Securitização de Recebíveis 141, Arrendamento Mercantil 73, Seguradoras e Corretoras 24, Intermediação Financeira 10, Crédito Imobiliário 6, Bolsas de Valores/Mercadorias e Futuros 4, Factoring 1. Há também as holdings: "Emp. Adm. Part. - Intermediação Financeira" 16, "- Seguradoras e Corretoras" 6, "- Crédito Imobiliário" 5, "- Securitização de Recebíveis" 4, "- Arrendamento Mercantil" 2, "- Bancos" 1 e "Emp. Adm. Part.-Bolsas de Valores/Mercadorias e Futuros" 1.
- **Setor ano a ano:** o Formulário Cadastral (FCA, `fca_cia_aberta_geral_AAAA.csv`, de 2010 a 2026) traz `Setor_Atividade` em cada ano, além do dia e do mês de encerramento do exercício social.
- **Empresas canceladas continuam nos dados abertos da DFP.** Das 661 empresas da DFP 2010, 314 estão canceladas hoje; na DFP 2023, 97 de 730. Nos anos conferidos (2010, 2015, 2019 e 2023), de 5 a 11 códigos CVM por ano aparecem na DFP mas não no cadastro.
- **Três planos de contas na DFP**, identificados pela descrição da conta 3.01:

  | Plano | Descrição da conta 3.01 | Empresa-anos (con + ind, 2010–2025) |
  | --- | --- | --- |
  | não financeiro | Receita de Venda de Bens e/ou Serviços | 16.008 |
  | banco | Receitas da (ou de) Intermediação Financeira | 905 |
  | seguradora | Receitas das Operações (49) ou Receitas das Atividades Seguradoras/Resseguradoras (6) | 55 |

- **O setor do cadastro e o plano de contas nem sempre batem.** Empresas distintas de 2010 a 2025. A conta 3.01 dos bancos tem duas grafias ("da" e "de"), e uma empresa que usou as duas é contada duas vezes:
  - Bancos: 56 no plano de banco e 2 no não financeiro;
  - Arrendamento Mercantil: 13 no plano de banco;
  - Securitização de Recebíveis: 124 no não financeiro, 12 no de banco e 1 no de seguradora;
  - Seguradoras e Corretoras: 3 no não financeiro e 1 no de seguradora;
  - Emp. Adm. Part. - Seguradoras e Corretoras: 4 no não financeiro e 2 no de seguradora;
  - Intermediação Financeira: 6 no não financeiro;
  - Emp. Adm. Part. - Intermediação Financeira: 9 no não financeiro;
  - Crédito Imobiliário, Bolsas e Factoring: 1 cada, no não financeiro.

### 1.6 Emendas 2 e 4 nas financeiras

A busca foi feita como a Emenda 2 manda: texto em `DS_CONTA`, sem diferenciar maiúsculas e acentos. Os números são contagens de empresa-anos de 2010 a 2025, somando consolidado e individual.

**Plano de banco (905 empresa-anos)**

- **Numerador, "outras receitas operacionais":** achado em 904. Está na conta fixa **3.04.05** (712 linhas) ou **3.04.06** (193 linhas): há dois leiautes, e num deles a 3.04.05 é "Despesas Tributárias". Aparece também em subcontas não fixas: 3.04.05.xx (94), 3.04.06.xx (24) e 3.04.04.xx (2).
- **Texto ao mesmo tempo na conta-mãe e na subconta:** 113 empresa-anos. A regra da Emenda 4 é aplicável pelo código, porque a hierarquia vem dos pontos. Há mais de uma linha casada em 121 empresa-anos.
- **Denominador, "resultado antes dos tributos sobre o lucro":** achado em 432, na conta fixa **3.05**. Não aparece em 473 (ver 2.3).
- **Leiaute antigo, só nas demonstrações individuais (474 empresa-anos):** 3.04 Outras Despesas/Receitas Operacionais, 3.05 Resultado Operacional, 3.06 Resultado Não Operacional, **3.07 Resultado Antes Tributação/Participações**. Todas as DRE consolidadas de banco (311) seguem o leiaute com a 3.05. Os casos sem denominador caem com o tempo: 40 de 59 em 2010, 38 de 56 em 2019, 17 de 54 em 2020 e 5 de 36 em 2025.

**Plano de seguradora (55 empresa-anos)**

- **Denominador:** conta fixa **3.09** "Resultado Antes dos Tributos sobre o Lucro", em 55 de 55.
- **Numerador:** achado só em 4, em subcontas não fixas 3.04.08.xx, debaixo de "Outras Despesas Administrativas". A conta fixa do plano é **3.05 "Outras Receitas e Despesas Operacionais"** (55 de 55), que não contém o texto exato "outras receitas operacionais" (ver 2.4).

**Empresas de setor financeiro no plano não financeiro (1.395 empresa-anos)**

- Numerador na conta fixa 3.04.04 "Outras Receitas Operacionais" (100%).
- Denominador na conta fixa 3.07 "Resultado Antes dos Tributos sobre o Lucro": exatamente 1 linha em 1.388 empresa-anos e mais de uma em 7.
- Texto na conta-mãe e na subconta: 131 empresa-anos.

**Descrições parecidas que o texto da Emenda 2 não pega** (registro, sem proposta): "Outras Receitas e Despesas Operacionais" (seguradoras, 55 empresa-anos), "Outras Receitas (Despesas) Operacionais" e "Outras Receitas / (Despesas) Operacionais" (subcontas em bancos), "Outras Receitas Não Operacionais", e um erro de digitação ("operacioanais").

### 1.7 Linhas da DFC achadas por texto, para não financeiras (DFC_MI)

Padrões e seções do catálogo, com o texto sem acento. Nenhuma dessas linhas é conta fixa: são subcontas criadas por cada empresa.

| Linha | Padrão do catálogo | Achada (con / ind) | Observações |
| --- | --- | --- | --- |
| depreciação | "deprecia" em 6.01.01 | 93,2% / 74,2% | Em 10.724 das 12.589 empresa-anos com a linha, ela é **só combinada** com amortização ("Depreciação e Amortização" e variantes). Só 1.865 têm uma linha só de depreciação |
| juros pagos | "juros pagos" em 6.01 ou 6.03 | 40,0% / 29,5% | Linhas em 6.01 (4.702), 6.03 (1.808) e 6.02 (12): as empresas escolhem a seção, como o catálogo previa. Outras 2.951 empresa-anos têm variantes que o padrão não pega ("pagamento de juros", "pagamentos de juros") |
| capex | "aquisição de imobilizado" ou "intangível" em 6.02 | 75,6% / 59,3% | 532 empresa-anos têm variantes não pegas ("aquisições de imobilizado", "adições ao imobilizado"). O padrão "intangível" sozinho também pode pegar venda de intangível (não verificado) |
| dividendos | "dividendos" ou "juros sobre o capital próprio" em 6.03 | 74,1% / 61,1% | 290 empresa-anos têm só "juros sobre capital próprio", sem o "o", e não são pegas |
| IR e CSLL pagos | "imposto de renda e contribuição social pagos" em 6.01 | 37,1% / 28,1% | 1.190 empresa-anos têm variantes não pegas ("imposto de renda e contribuição social pago", "IR e CS pagos", "pagamento de imposto de renda") |
| emissões | "captação", "emissão de ações" ou "debêntures" em 6.03 | 60,8% / 52,2% | "debêntures" também pega linhas de **pagamento ou amortização** de debêntures, em 3.966 empresa-anos |

Observação, sem proposta de mudança: a DVA tem uma conta fixa "Depreciação, Amortização e Exaustão" (7.04.01 na maioria; 7.05.01 ou 7.07.01 em outros planos). Ela junta depreciação e amortização.

## 2. O que é diferente do catálogo ou das emendas

Só registro. Nenhuma fórmula, corte ou regra foi mudada.

1. **Versões.** O PROMPT (Fase 1) supõe que dá para "guardar todas as versões" e montar `como_era` com os dados abertos. Os arquivos de demonstrações só trazem a última versão (1.3). Para as empresa-anos reentregues depois do corte, o número "como era na época" não está nos dados abertos. Fonte possível: o pacote de cada versão no ENET da CVM, pelo `LINK_DOC` do índice (não confirmado, ver 3.2).
2. **ir_csll_a_pagar.** O catálogo diz "2.01.03 (subconta de IR e CSLL, localizar por texto)". Existe conta fixa: **2.01.03.01.01 "Imposto de Renda e Contribuição Social a Pagar"**, presente em 100% das empresa-anos do plano não financeiro, então a busca por texto não é necessária.
3. **Emenda 2, denominador nos bancos.** No leiaute antigo dos bancos (474 empresa-anos, todas individuais), a linha "resultado antes dos tributos sobre o lucro" não existe; a mais próxima é 3.07 "Resultado Antes Tributação/Participações". Pela Emenda 2, essas empresa-anos ficam "não calculável".
4. **Emenda 2, numerador nas seguradoras.** No plano de seguradora, o texto "outras receitas operacionais" só aparece em 4 de 55 empresa-anos. A linha do plano é 3.05 "Outras Receitas e Despesas Operacionais". Pela Emenda 2, as outras 51 ficam "não calculável", e a própria emenda diz que, se as linhas não existirem, a fórmula muda por nova emenda antes de qualquer cálculo. Não verifiquei qual plano o IRB usa (ver 3.3).
5. **Emenda 4.** Os casos que ela resolve existem: o texto está ao mesmo tempo na conta-mãe e na subconta em 113 empresa-anos de banco e em 131 de empresas de setor financeiro no plano não financeiro. Pelo código, a regra é aplicável.
6. **Padrões de texto da DFC no catálogo.** Deixam de pegar variantes comuns (números em 1.7). O padrão "debêntures" pega também pagamentos. Esses padrões estão no catálogo, não no pré-registro.
7. **Depreciação.** A linha só de depreciação existe em poucas empresas. Na maioria, a DFC traz "depreciação e amortização" juntas. Não é divergência: o pré-registro (4.1) já decide usar o total e marcar a empresa-ano. Mas a marca vai valer para cerca de 85% das empresa-anos em que a linha é achada.
8. **Regra boba (seção 7).** Na DFP, a conta 2 "Passivo Total" tem como subconta a 2.03 "Patrimônio Líquido": é a soma do passivo com o patrimônio líquido, que pela identidade contábil é igual ao Ativo Total. Lida assim, a razão "passivo total ÷ ativo total" vale 1 para todas as empresas. O plano de banco tem outra estrutura de passivo, não conferida.
9. **Escala.** `ESCALA_MOEDA` mistura `MIL` e `UNIDADE` entre empresas, e o catálogo não fala disso. Não é decisão do estudo; o código precisa normalizar.

## 3. O que não consegui confirmar ou precisa de decisão sua

1. **Versões originais dos anos do gabarito.** Para saber se a Americanas (2020 e 2021) e o IRB (2018 e 2019) reentregaram a DFP depois do corte, é preciso abrir as linhas do índice dessas empresas: só versões e datas de entrega, sem valores. Não fiz. Preciso da sua autorização.
2. **Conteúdo dos pacotes de versões antigas no ENET.** Os dois downloads de teste chegaram cortados nas três tentativas, apesar da resposta HTTP 200. O servidor da CVM também devolveu uma vez o erro "could not be activated". Vi os nomes dos arquivos do pacote, mas não abri o `.dfp`.
3. **Plano de contas do IRB.** Não abri a estrutura do IRB. Posso conferir só os rótulos das contas, sem valores, se você autorizar.
4. **Quais setores são "financeiras".** O pré-registro diz "bancos, seguradoras, resseguradoras e demais instituições financeiras". O cadastro tem Securitização de Recebíveis, Arrendamento Mercantil, Crédito Imobiliário, Factoring, Bolsas e as holdings "Emp. Adm. Part. - …", e o setor nem sempre bate com o plano de contas (1.5). Também falta dizer se vale o setor do cadastro (só o atual) ou o do FCA de cada ano.
5. **Consolidado ou individual.** Nem o pré-registro nem o PROMPT dizem qual usar. De 258 a 298 empresas por ano só têm a individual, e o leiaute antigo dos bancos só aparece na individual.
6. **De onde vem o ano t−1 dos índices.** Na data de corte do ano t, os números de t−1 estão em dois lugares: como `PENÚLTIMO` na DFP de t, possivelmente reapresentados, e como `ÚLTIMO` na DFP de t−1, o original. O pré-registro não diz qual usar. Isso também define o primeiro ano calculável: 2010 se t−1 vier do `PENÚLTIMO` da DFP 2010; 2011 se vier da DFP de t−1.
7. **Exercício que não termina em 31/12** (de 0 a 21 empresa-anos por ano). Não está dito como aplicar "30 de abril do ano seguinte": seguinte ao ano de `DT_REFER` ou outra regra. A tabela de 1.3 usou o ano do arquivo.
8. **Empresa-ano sem nenhuma versão entregue até o corte.** Pela letra da seção 3 ("usar só a versão que já era pública na data de corte"), ela fica de fora. Confirme se é isso.
9. **Empresas sem receita no ano** (exclusão da seção 2). Depende do valor da conta 3.01, então só dá para identificar na Fase 1.
10. **DFC pelo método direto.** Não conferi a conta 6.01 nem as linhas por texto na `DFC_MD` (186 empresa-anos consolidadas e 367 individuais).
11. **Código CVM do gabarito.** O cadastro tem dois códigos ligados ao caso Americanas: 8087 (Lojas Americanas SA) e 20990 (Americanas S.A. - Em Recuperação Judicial). O IRB é 24180. O `cd_cvm` do gabarito continua vazio, e qual código entra é decisão sua.
12. **Versão em inglês.** Este documento e o `fontes.md` estão só em português por enquanto.
