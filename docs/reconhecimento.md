Pré-registro congelado no commit 6cc1d5f5d365e4923ec422d34130f5977b0ac7c3, enviado ao GitHub em 04/11/2026 às 23:11:52 (horário de Brasília; 05/11/2026 02:11:52 UTC), antes de baixar qualquer dado.

# Reconhecimento dos dados abertos da CVM (Fase 0)

Consulta feita em 05/11/2026, a partir das 02:12 UTC (04/11/2026, 23:12 em Brasília). URLs e hashes dos arquivos estão em [`fontes.md`](fontes.md).

**Como a Fase 0 foi feita**

- Só estrutura. Nenhum sinal, índice ou M-score foi calculado. A coluna `VL_CONTA` não foi carregada em nenhum script: os valores das contas não entraram na memória.
- Nas partes 1 a 4, antes de qualquer análise, todas as linhas destes códigos CVM foram removidas: 8087 (Lojas Americanas SA), 20990 (Americanas S.A.), 24180 (IRB-Brasil Resseguros) e 22837 (Drogarias Americanas SA, removida só por ter "Americanas" no nome). Os metadados de Americanas e IRB só foram abertos depois, com autorização, na parte 5.
- Os números abaixo são contagens de estrutura (empresas, linhas, presença de contas) e saem dos scripts em [`scripts/fase0/`](../scripts/fase0/).
- Os arquivos baixados ficaram fora do repositório.

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
- **Leiaute antigo, só nas demonstrações individuais (473 empresa-anos):** 3.04 Outras Despesas/Receitas Operacionais, 3.05 Resultado Operacional, 3.06 Resultado Não Operacional, **3.07 Resultado Antes Tributação/Participações**. Todas as DRE consolidadas de banco (311) seguem o leiaute com a 3.05. Os casos sem denominador caem com o tempo: 40 de 59 em 2010, 38 de 56 em 2019, 17 de 54 em 2020 e 5 de 36 em 2025.

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
3. **Emenda 2, denominador nos bancos.** No leiaute antigo dos bancos (473 empresa-anos, todas individuais), a linha "resultado antes dos tributos sobre o lucro" não existe; a mais próxima é 3.07 "Resultado Antes Tributação/Participações". Pela Emenda 2, essas empresa-anos ficam "não calculável".
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

## 4. Anexo da Emenda 5 (registrado em 05/11/2026, antes do congelamento)

A Emenda 5 manda anexar a este documento a lista exata de setores financeiros e os padrões finais de texto da DFC. Os dois ficam fixos daqui em diante: mudar qualquer um exige nova emenda. As contagens desta parte são só de estrutura e saem de `scripts/fase0/grupos.py` e `scripts/fase0/dfc.py`.

### 4.1 Quem é financeira

**Regra**, decidida por Roberto em 05/11/2026 ao fechar a lista: o setor define a candidata a financeira, e o plano de contas usado na DFP decide o grupo. A regra usa só a estrutura do arquivo, nunca valores.

1. **Setor:** o do FCA do próprio ano (`Setor_Atividade`). Se não houver FCA naquele ano, vale o do cadastro (`SETOR_ATIV`). Quando o FCA do ano tem mais de uma versão, os scripts usam a última versão do ano.
2. **Candidata a financeira:** empresa cujo setor tem um destes nomes exatos.
   - Bancos
   - Intermediação Financeira
   - Arrendamento Mercantil
   - Seguradoras e Corretoras
   - Crédito Imobiliário
   - Emp. Adm. Part. - Bancos
   - Emp. Adm. Part. - Intermediação Financeira
   - Emp. Adm. Part. - Arrendamento Mercantil
   - Emp. Adm. Part. - Seguradoras e Corretoras
   - Emp. Adm. Part. - Crédito Imobiliário
3. **Grupo:** a candidata vai para o grupo das **financeiras** se a DFP usada (consolidada quando existir; senão, individual) está no plano de contas de banco (conta 3.01 "Receitas da Intermediação Financeira" ou "Receitas de Intermediação Financeira") ou de seguradora (3.01 "Receitas das Operações" ou "Receitas das Atividades Seguradoras/Resseguradoras"). Se a DFP usa o plano não financeiro (3.01 "Receita de Venda de Bens e/ou Serviços"), a empresa-ano vai para as **não financeiras**. Isso vale também para corretoras de seguros e para as holdings da lista.
4. **Não são candidatas:** Securitização de Recebíveis, Emp. Adm. Part. - Securitização de Recebíveis, Factoring, Bolsas de Valores/Mercadorias e Futuros, Emp. Adm. Part.-Bolsas de Valores/Mercadorias e Futuros, Cooperativas e todos os outros setores.

**Como a regra divide a base:** empresa-anos de 2010 a 2025, sem Americanas e IRB, uma DFP por empresa-ano.

| | Plano de banco | Plano de seguradora | Plano não financeiro |
| --- | --- | --- | --- |
| Candidata | 565 → financeira | 27 → financeira | 258 → não financeira |
| Não candidata | 49 → não financeira | 1 → não financeira | 9.884 → não financeira |

O setor veio do FCA do ano em 10.195 empresa-anos, do cadastro em 571, e faltou em 18.

**Observação, sem proposta:** 50 empresa-anos não candidatas usam plano de banco ou de seguradora. São 30 de Securitização de Recebíveis, 16 de Emp. Adm. Part. - Sem Setor Principal, 3 sem setor e 1 de Emp. Adm. Part. - Telecomunicações. Pela regra, ficam nas não financeiras, onde os sinais usam contas que esse plano não tem e tendem a sair "não calculável".

### 4.2 Padrões finais de texto da DFC

**Como se aplicam**

- O texto comparado é o `DS_CONTA` em minúsculas, sem acento e sem espaços nas pontas.
- A linha precisa estar na seção indicada (prefixo do `CD_CONTA`), conter pelo menos um termo de cada grupo de "Contém" e nenhum termo de "Não contém".
- Os termos são trechos de palavra: "aquisic" pega "aquisição" e "aquisições".
- Se a conta-mãe e a subconta casam, conta só a mãe, como na Emenda 4, para não somar o mesmo valor duas vezes.
- Os padrões valem para a DFC pelo método indireto (`DFC_MI`). A `DFC_MD` não foi conferida.

| Linha | Seção | Contém (um termo de cada grupo) | Não contém | Uso |
| --- | --- | --- | --- | --- |
| depreciação | 6.01.01 | "deprecia" | — | DEPI, no MVP. Somam-se as linhas que casam; se alguma também contém "amortiza" ou "exaust", a empresa-ano é marcada (pré-registro 4.1 e Emenda 5) |
| juros pagos | 6.01 e 6.03 | "juros" · "pago", "pagos", "pagamento" ou "pagamentos" | "capital proprio", "recebid" | padronizar o caixa operacional (pré-registro 4.1), no MVP |
| capex | 6.02 | "aquisic", "adic", "compra" ou "investimento" · "imobilizado" ou "intangivel" | "venda", "alienac", "baixa", "recebimento" | fase 2 |
| dividendos pagos | 6.03 | "dividendo" ou "capital proprio" | "recebid" | fase 2 |
| IR e CSLL pagos | 6.01 | "imposto de renda", "ir e cs", "irpj", "ir/cs" ou "ir/csll" · "pago", "pagos", "pagamento" ou "pagamentos" | — | fase 3 |
| emissões | 6.03 | "captac", "emiss" ou "ingress" | "pagamento", "amortiza", "liquida", "resgat" | fase 2; regra da Emenda 5 |

**Cobertura:** empresa-anos do plano não financeiro com `DFC_MI`, 5.774 consolidadas e 9.716 individuais.

| Linha | Achada (con / ind) | Antes, com o padrão do catálogo (con / ind) |
| --- | --- | --- |
| depreciação | 93,2% / 74,2% | 93,2% / 74,2% |
| juros pagos | 67,8% / 54,0% | 40,0% / 29,5% |
| capex | 77,3% / 60,6% | 75,6% / 59,3% |
| dividendos pagos | 76,1% / 62,8% | 74,1% / 61,1% |
| IR e CSLL pagos | 57,3% / 43,4% | 37,1% / 28,1% |
| emissões | 63,3% / 52,1% | 60,8% / 52,2% |

- A conta-mãe e a subconta nunca casaram ao mesmo tempo nessas seis linhas.
- **Depreciação:** de 12.589 empresa-anos em que a linha é achada, 11.260 ficam marcadas porque a soma inclui amortização ou exaustão.
- **Juros pagos em 6.02:** na Fase 0 apareceram 12 linhas assim, que ficam fora porque a seção não é 6.01 nem 6.03.
- **Emissões:** "gastos com emissão de ações" é um custo de emissão, ou seja, uma saída, mas passa pela regra da Emenda 5, porque "gasto" e "custo" não estão entre as palavras de saída. Isso acontece em 2.473 empresa-anos. Emissões não entram no MVP.

## 5. Autorizações de 05/11/2026 e resultados (depois do congelamento)

Feito depois do commit de congelamento `99237fcb9cd52ca3a445532f1cfe9a410eef6c92` (Emendas 5 e 6), com autorização de Roberto para abrir só metadados de Americanas e IRB. Nenhum valor foi lido. Scripts: `autorizados.py`, `setores.py`, `emenda5.py` e `enet_teste.py`.

### 5.1 CNPJ da Americanas

- O CNPJ 00.776.574/0006-60, informado no fato relevante de 16/07/2024, **não aparece exato** nem no cadastro nem no índice da DFP de 2010 a 2026.
- A raiz desse CNPJ (00.776.574) é a do código CVM **20990**, Americanas S.A. - Em Recuperação Judicial, cadastrada com o CNPJ 00.776.574/0001-56. Os oito primeiros dígitos do CNPJ identificam a empresa; o final indica o estabelecimento.
- A DFP de 2021 foi entregue com o código 20990 (versão 1, em 24/02/2022).
- O código 8087 (Lojas Americanas SA, CNPJ 33.014.556/0001-96) foi cancelado em 10/12/2021, por incorporação, e não tem DFP de 2021.
- O cadastro nem sempre usa o final /0001: a Via Varejo (código 6505) está cadastrada com o CNPJ 33.041.260/0652-90.
- A Emenda 5 manda usar o código "da empresa com o CNPJ 00.776.574/0006-60". Pela raiz, é o 20990. Como o CNPJ exato não está na base da CVM, preciso da sua confirmação antes de qualquer mudança no gabarito, que não foi alterado.

### 5.2 Versões das DFPs de 2017 a 2022

Data de corte pela Emenda 5: último dia do quarto mês depois do fim do exercício (todos os exercícios abaixo terminam em 31/12).

| Empresa (código) | DFP | Versões (data de entrega) | Corte | Versão da época | Versão nos dados abertos |
| --- | --- | --- | --- | --- | --- |
| Americanas S.A. (20990) | 2017 | 1 (07/03/2018) | 30/04/2018 | 1 | 1 |
| | 2018 | 1 (20/03/2019) | 30/04/2019 | 1 | 1 |
| | 2019 | 1 (20/02/2020), 2 (21/02/2020) | 30/04/2020 | 2 | 2 |
| | 2020 | 1 e 2 (04/03/2021) | 30/04/2021 | 2 | 2 |
| | 2021 | 1 (24/02/2022) | 30/04/2022 | 1 | 1 |
| | 2022 | 1 (16/11/2023) | 30/04/2023 | nenhuma | 1 |
| Lojas Americanas (8087) | 2017 | 1 (07/03/2018), 2 (14/03/2018) | 30/04/2018 | 2 | 2 |
| | 2018 | 1 (20/03/2019) | 30/04/2019 | 1 | 1 |
| | 2019 | 1 (20/02/2020) | 30/04/2020 | 1 | 1 |
| | 2020 | 1 (04/03/2021) | 30/04/2021 | 1 | 1 |
| IRB (24180) | 2017 | 1 (08/02/2018) | 30/04/2018 | 1 | 1 |
| | 2018 | 1 (07/02/2019), 2 e 3 (07/03/2019), 4 (08/03/2019) | 30/04/2019 | 4 | 4 |
| | 2019 | 1 (18/02/2020), 2 e 3 (30/06/2020), 4 (07/07/2020), 5 (18/02/2021) | 30/04/2020 | 1 | **5** |
| | 2020 | 1 (18/02/2021) | 30/04/2021 | 1 | 1 |
| | 2021 | 1 (24/02/2022) | 30/04/2022 | 1 | 1 |
| | 2022 | 1 (08/03/2023), 2 (09/03/2023), 3 (21/03/2023) | 30/04/2023 | 3 | 3 |

- **Americanas 2021 não foi reentregue.** Há uma versão só, entregue antes do corte; a versão dos dados abertos é a da época.
- **IRB 2019 foi reentregue depois do corte.** A versão 1 saiu em 18/02/2020, antes do corte de 30/04/2020; as versões 2 a 5 saíram entre 30/06/2020 e 18/02/2021. Os dados abertos trazem a versão 5. Pela Emenda 5, a versão da época é a 1 e precisa vir do ENET (ver 5.4). A versão 1 foi entregue depois da data pública do caso (10/02/2020), como a Emenda 3 já registra.
- **IRB 2018**, usado na métrica secundária da Emenda 3: as quatro versões foram entregues até o corte, e a dos dados abertos (versão 4) é a da época.
- **Americanas 2022:** a única versão foi entregue depois do corte, então não há versão da época. É posterior à data pública do caso.

### 5.3 Rótulos de contas do IRB (sem valores)

- O IRB usa o **plano de seguradora** (3.01 "Receitas das Operações") em todas as DFPs de 2017 a 2022, consolidadas e individuais. A estrutura é a mesma em todos os anos.
- Denominador da Emenda 5: 3.09 "Resultado Antes dos Tributos sobre o Lucro".
- Numerador pela Emenda 5 (linhas que começam com "outras receitas", com a regra de conta-mãe da Emenda 4): cinco contas fixas.
  - 3.01.01.02 "Outras Receitas de Seguros"
  - 3.01.02.02 "Outras Receitas de Resseguros"
  - 3.01.03.03 "Outras Receitas de Prev. Complementar"
  - 3.01.04.03 "Outras Receitas de Capitalização"
  - 3.05 "Outras Receitas e Despesas Operacionais"
- As quatro primeiras ficam dentro da receita das operações (3.01). Ver 5.6, item 1.
- Balanço: 2.01 Passivo Circulante, 2.02 Passivo Não Circulante e 2.03 Patrimônio Líquido Consolidado. A regra boba da Emenda 5 funciona para o IRB.

### 5.4 ENET

- **Pacote de versões antigas: não chega inteiro.** Em todas as tentativas de 05/11/2026, de madrugada (02h UTC) e à noite (20h–21h UTC), com curl e com `scripts/fase0/enet_teste.py`, sempre com documentos de empresas fora do gabarito, nenhum pacote chegou inteiro.
  - A transferência para por volta de 22 a 25 segundos ("transfer closed with outstanding read data remaining", "IncompleteRead"), ou o servidor fecha a conexão sem resposta.
  - Retomar o download do ponto onde parou não funciona.
  - O proxy desta sessão não registrou falha. O corte parece vir do servidor da CVM.
- **Visualização HTML: chega inteira.** A página de consulta de cada documento (`frmGerenciaPaginaFRE.aspx`, pelo número do documento) responde com HTTP 200, cerca de 29 KB, e traz o menu das demonstrações (balanço, DRE e outras). Não conferi se as tabelas de cada demonstração carregam completas.
- **Consequência para a Emenda 5:** a regra principal ("buscar no ENET a versão mais recente entregue até o corte") não funciona hoje pelo download do pacote. Antes da Fase 1, falta testar a visualização HTML. Se ela também falhar, essas empresa-anos ficam "versão da época indisponível". A tabela da parte 1.3, coluna "Dessas, com versão 1 recebida até o corte", dá a escala no consolidado. O IRB 2019 é um desses casos.

### 5.5 Nomes de setor do cadastro e do FCA

- A lista completa, com o número de empresas em cada fonte, está no Anexo A.
- Nomes que só aparecem no FCA: Cooperativas e "Serviços médicos" (com "m" minúsculo; o cadastro usa "Serviços Médicos").
- Nomes que só aparecem no cadastro: Comércio Exterior, Emp. Adm. Participações, Outras Atividades Industriais, Serviços Diversos, Serviços Médicos e Serviços em Geral.
- A lista de setores classificados como financeiras é a da parte 4.1, congelada.
- Os padrões de texto finais da DFC são os da parte 4.2, também congelados.

### 5.6 O que, na Emenda 5, não bate com a estrutura

Só registro. Qualquer mudança é emenda sua.

1. **"Começa com 'outras receitas'" pega mais linhas do que as duas citadas.**
   - No plano de seguradora, pega as quatro "Outras Receitas de Seguros / Resseguros / Prev. Complementar / Capitalização", que são partes da receita das operações: 49 a 55 empresa-anos de 2010 a 2025, além de todos os anos do IRB.
   - No plano de banco, pega "Outras Receitas Financeiras" (3.01.03) e "Outras Receitas" (3.01.02 e 3.01.07), dentro da receita de intermediação, além de "Outras Receitas e Despesas Não Operacionais" (3.08.01) e "Outras Receitas (Despesas) Administrativas".
   - A emenda diz "Vale para 'Outras Receitas Operacionais' e 'Outras Receitas e Despesas Operacionais'", e não está claro se a frase restringe a regra ou só dá exemplos. No IRB a diferença é grande: com a leitura ampla, o numerador soma parte da receita de resseguros.
2. **Maiúsculas e acentos.** A Emenda 2 dizia "sem diferenciar maiúsculas e acentos". A Emenda 5 substitui o texto da Emenda 2 e não repete isso. As contagens usaram a mesma normalização da Emenda 2. Confirme.
3. **Regra boba nos bancos.**
   - "Contas 2.01 + 2.02" funciona nas não financeiras e nas seguradoras (2.01 Passivo Circulante, 2.02 Passivo Não Circulante).
   - Nos leiautes IFRS de banco, 2.01 e 2.02 são tipos de passivo financeiro (por exemplo, "Passivos Financeiros ao Valor Justo através do Resultado" e "Passivos Financeiros ao Custo Amortizado"), e o patrimônio líquido fica em 2.07 ou 2.08. Ali, 2.01 + 2.02 não é "passivo sem o patrimônio líquido".
   - No leiaute antigo, 2.01 e 2.02 são Passivo Circulante e "Passivo Exigível a Longo Prazo"; há ainda 2.03 "Resultados de Exercícios Futuros", e o patrimônio líquido fica em 2.05.
4. **CNPJ da Americanas:** ver 5.1.
5. **Emissões:** "gastos com emissão de ações" passa pela regra (parte 4.2). Emissões não entram no MVP.
6. **Não candidatas com plano financeiro:** 50 empresa-anos ficam nas não financeiras (parte 4.1).
7. **FCA com mais de uma versão no mesmo ano:** os scripts usam a última versão do ano. A regra "como era na época" sugeriria a versão vigente na data de corte. Diga qual.

### 5.7 Situação das pendências da parte 3

| Item da parte 3 | Situação |
| --- | --- |
| 1. Versões dos anos do gabarito | Respondido em 5.2 |
| 2. Pacotes do ENET | Não chegam inteiros (5.4) |
| 3. Plano de contas do IRB | Seguradora (5.3) |
| 4. Quais setores são financeiras | Emenda 5 e parte 4.1 |
| 5. Consolidado ou individual | Emenda 5: consolidado quando existir; senão, individual |
| 6. Ano t−1 | Emenda 5: comparativo (`PENÚLTIMO`) da DFP de t; o primeiro ano calculável passa a ser 2010 |
| 7. Exercício fora de 31/12 | Emenda 5: último dia do quarto mês depois do fim do exercício |
| 8. Sem versão até o corte | Emenda 5: fica de fora e é contada |
| 9. Empresas sem receita | Continua para a Fase 1, porque depende de valor |
| 10. DFC pelo método direto | Ainda não conferida |
| 11. Código CVM do gabarito | Emenda 5; ver 5.1 |
| 12. Versão em inglês | Feita: [`docs/en/reconnaissance.md`](en/reconnaissance.md) e [`docs/en/sources.md`](en/sources.md) |

### 5.8 Correção

Nas partes 1.6 e 2, o leiaute antigo dos bancos aparecia com 474 empresa-anos; o número certo é 473. A contagem anterior somava duas vezes uma empresa-ano que tinha duas datas de referência no mesmo arquivo. O número de empresa-anos sem denominador já era 473. A parte 4 não mudou.

## 6. Gabarito ampliado (Emenda 6): candidatos para revisão

- **Arquivo:** [`data/gabarito_candidatos.csv`](../data/gabarito_candidatos.csv), com as mesmas colunas do gabarito. `verificado_por` e `verificado_em` ficam vazios. Nada entrou em `data/gabarito_casos.csv`.
- **Como coletei:** buscas na web por decisões da CVM e fatos relevantes, em 05/11/2026, e leitura do texto dos extratos e votos da CVM (PDF) e dos fatos relevantes. Nenhum valor de DFP foi aberto. Código CVM e CNPJ vieram do cadastro.
- **Resultado:** 18 linhas, de 16 empresas (Mundial e Inepar têm dois processos cada).
  - Decisão da CVM lida na fonte primária (14): Banco Panamericano, Taurus, OGX, OSX, Metalúrgica Duque, Mundial (dois processos), Hércules, Teka, IGB Eletrônica, Tecnosolo, Schlosser, Brasil Brokers e Oi (DFs de 2014).
  - Fraude confirmada pela própria companhia em fato relevante (1): Via Varejo.
  - Só fonte secundária, a conferir (3): Inepar (dois processos) e Companhia Docas de Imbituba.
- **Pontos de atenção**
  - `data_publica` está preenchida em 6 casos. Nos outros 12, a data exata não estava nos documentos lidos; a nota de cada um traz o ano de instauração, tirado do número do processo.
  - Banco Panamericano: o período afetado (2007 a 2009) é anterior aos dados abertos da DFP, que começam em 2010. Na prática, o caso não é acertável.
  - Via Varejo e Docas de Imbituba: período vazio, porque nenhum documento lido dá os exercícios.
  - Mundial (processo de 2016): o período vai de 2009 a 2011, em parte fora da janela da Emenda 6.
  - Valores novos nos campos: `tipo_evento` = "processo_cvm"; `como_veio_a_publico` = "regulador_cvm" ou "regulador_bc".
- **Não entraram**
  - Sem decisão final: Oi, DFs de 2015 e 2016 (PAS 19957.004207/2021-15; o julgamento começou em 25/08/2026 e teve pedido de vista); CVC Brasil (a companhia falou em erros contábeis, não em fraude, e a acusação da CVM foi revelada em 30/01/2026, sem julgamento); Indústrias J.B. Duarte (PAS RJ2016/5786, DFs de 2013 a 2015, pautado para 22/06/2021; resultado não encontrado).
  - Fatos anteriores a 2010: Brasil Telecom (DFs de 2006 a 2008, julgado em 2019) e Indústrias Verolme-Ishibrás (DFs de 2008 e 2009, segundo a busca).
  - Condenação que não trata do conteúdo das DFs: WLM (remuneração), GPC Participações e Eucatex (voto na aprovação das próprias contas), CSN (fato relevante), J&F (derivativos) e Recrusul (aumento de capital).
  - Só atraso ou falta de entrega das DFs: Companhia Aurífera Brasileira (2021), Advanced Digital Health (2023), processo 19957.008462/2019-12 (2023), Inncorp (2020) e Longdis (2022). A Emenda 6 fala em "irregularidade na elaboração ou divulgação". Tratei atraso e falta de entrega como fora; se você entender que entram, a lista cresce bastante.
  - Outros: Banco Cruzeiro do Sul (só multas por manipulação de preço; o documento de 2023 trata de um FIDC), Intrader DTVM (não é companhia aberta), Petrobras (as condenações sobre as DFs foram de auditores, não da companhia nem de seus administradores), Paranapanema (sem fraude nem condenação encontradas) e Laep (divulgação de informações e falta de entrega).
- **Limite:** a busca não foi exaustiva. Uma varredura completa exige percorrer, ano a ano desde 2010, a lista de processos sancionadores julgados no site da CVM. Posso fazer isso antes da sua revisão, se você quiser.
- **IRB, caso existente, não alterado:** no processo sobre a contabilidade de 2019 (PAS 19957.003588/2023-87), o voto do relator, de 06/10/2026, é pela absolvição de todos os acusados. Fernando Passos é absolvido porque a conduta já foi punida em outro processo. Não conferi a decisão final do Colegiado. A nota do IRB no gabarito ("ainda precisa ser conferido") fica como está até você decidir.

## Anexo A. Nomes de setor no cadastro e no FCA

"Empresas" conta códigos CVM distintos: no cadastro, pelo setor atual; no FCA, por qualquer ano de 2010 a 2026. Gerado por `scripts/fase0/setores.py --tabela`.

| Nome do setor | Empresas no cadastro | Empresas no FCA | Anos no FCA |
| --- | --- | --- | --- |
| Agricultura (Açúcar, Álcool e Cana) | 49 | 29 | 2010–2026 |
| Alimentos | 112 | 33 | 2010–2026 |
| Arrendamento Mercantil | 73 | 12 | 2010–2026 |
| Bancos | 115 | 44 | 2010–2026 |
| Bebidas e Fumo | 24 | 5 | 2010–2026 |
| Bolsas de Valores/Mercadorias e Futuros | 3 | 1 | 2010–2026 |
| Brinquedos e Lazer | 10 | 8 | 2010–2026 |
| Comunicação e Informática | 38 | 32 | 2010–2026 |
| Comércio (Atacado e Varejo) | 101 | 65 | 2010–2026 |
| Comércio Exterior | 4 | — | — |
| Construção Civil, Mat. Constr. e Decoração | 168 | 79 | 2010–2026 |
| Cooperativas | — | 1 | 2010–2010 |
| Crédito Imobiliário | 6 | 1 | 2011–2024 |
| Educação | 10 | 11 | 2010–2026 |
| Embalagens | 8 | 3 | 2010–2026 |
| Emp. Adm. Part. - Agricultura (Açúcar, Álcool e Cana) | 3 | 4 | 2010–2026 |
| Emp. Adm. Part. - Alimentos | 6 | 7 | 2010–2026 |
| Emp. Adm. Part. - Arrendamento Mercantil | 2 | 3 | 2010–2016 |
| Emp. Adm. Part. - Bancos | 1 | 2 | 2013–2026 |
| Emp. Adm. Part. - Brinquedos e Lazer | 4 | 3 | 2010–2026 |
| Emp. Adm. Part. - Comunicação e Informática | 6 | 6 | 2013–2026 |
| Emp. Adm. Part. - Comércio (Atacado e Varejo) | 18 | 17 | 2010–2026 |
| Emp. Adm. Part. - Const. Civil, Mat. Const. e Decoração | 23 | 24 | 2010–2026 |
| Emp. Adm. Part. - Crédito Imobiliário | 5 | 4 | 2012–2026 |
| Emp. Adm. Part. - Educação | 8 | 8 | 2010–2026 |
| Emp. Adm. Part. - Embalagens | 2 | 2 | 2010–2016 |
| Emp. Adm. Part. - Energia Elétrica | 49 | 50 | 2010–2026 |
| Emp. Adm. Part. - Extração Mineral | 11 | 15 | 2010–2026 |
| Emp. Adm. Part. - Farmacêutico e Higiene | 2 | 4 | 2010–2020 |
| Emp. Adm. Part. - Gráficas e Editoras | 1 | 1 | 2012–2016 |
| Emp. Adm. Part. - Hospedagem e Turismo | 5 | 4 | 2010–2026 |
| Emp. Adm. Part. - Intermediação Financeira | 15 | 10 | 2010–2026 |
| Emp. Adm. Part. - Metalurgia e Siderurgia | 7 | 7 | 2010–2026 |
| Emp. Adm. Part. - Máqs., Equip., Veíc. e Peças | 8 | 9 | 2010–2026 |
| Emp. Adm. Part. - Papel e Celulose | 1 | 2 | 2010–2026 |
| Emp. Adm. Part. - Petroquímicos e Borracha | 4 | 5 | 2010–2023 |
| Emp. Adm. Part. - Petróleo e Gás | 12 | 12 | 2010–2026 |
| Emp. Adm. Part. - Saneamento, Serv. Água e Gás | 7 | 8 | 2010–2026 |
| Emp. Adm. Part. - Securitização de Recebíveis | 4 | 7 | 2010–2024 |
| Emp. Adm. Part. - Seguradoras e Corretoras | 5 | 6 | 2010–2026 |
| Emp. Adm. Part. - Sem Setor Principal | 104 | 124 | 2010–2026 |
| Emp. Adm. Part. - Serviços Transporte e Logística | 35 | 35 | 2010–2026 |
| Emp. Adm. Part. - Serviços médicos | 7 | 5 | 2016–2026 |
| Emp. Adm. Part. - Telecomunicações | 38 | 30 | 2010–2026 |
| Emp. Adm. Part. - Têxtil e Vestuário | 5 | 6 | 2010–2025 |
| Emp. Adm. Part.-Bolsas de Valores/Mercadorias e Futuros | 1 | 2 | 2010–2011 |
| Emp. Adm. Participações | 156 | — | — |
| Energia Elétrica | 104 | 99 | 2010–2026 |
| Extração Mineral | 52 | 10 | 2010–2026 |
| Factoring | 1 | 1 | 2010–2011 |
| Farmacêutico e Higiene | 22 | 15 | 2010–2026 |
| Gráficas e Editoras | 12 | 3 | 2010–2023 |
| Hospedagem e Turismo | 28 | 12 | 2010–2026 |
| Intermediação Financeira | 9 | 11 | 2010–2026 |
| Metalurgia e Siderurgia | 136 | 32 | 2010–2026 |
| Máquinas, Equipamentos, Veículos e Peças | 176 | 40 | 2010–2026 |
| Outras Atividades Industriais | 18 | — | — |
| Papel e Celulose | 21 | 9 | 2010–2026 |
| Pesca | 4 | 1 | 2020–2020 |
| Petroquímicos e Borracha | 97 | 18 | 2010–2026 |
| Petróleo e Gás | 24 | 19 | 2010–2026 |
| Reflorestamento | 6 | 3 | 2010–2026 |
| Saneamento, Serv. Água e Gás | 37 | 36 | 2010–2026 |
| Securitização de Recebíveis | 138 | 133 | 2010–2026 |
| Seguradoras e Corretoras | 23 | 8 | 2010–2026 |
| Serviços Diversos | 18 | — | — |
| Serviços Médicos | 23 | — | — |
| Serviços Transporte e Logística | 138 | 117 | 2010–2026 |
| Serviços em Geral | 1 | — | — |
| Serviços médicos | — | 21 | 2010–2026 |
| Telecomunicações | 76 | 31 | 2010–2026 |
| Têxtil e Vestuário | 121 | 38 | 2010–2026 |
| (vazio) | 6 | 3 | 2010–2021 |
