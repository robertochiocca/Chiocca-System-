# Fase 0 dos EUA: reconhecimento dos dados

> **Reconhecimento, sem nenhum sinal calculado.** Objetivo: saber se dá para fazer, nos EUA, um estudo pré-registrado com os dados como eram na época, testando os sinais do v1 e do v2 do Chiocca e a regra boba contra os AAERs (Accounting and Auditing Enforcement Releases) da SEC. Só inventário e contagens; nada de 2024 em diante; nenhum nome de pessoa física. A frente dos EUA fica fora do README e do produto até decisão de Roberto.

## 1. Acesso à SEC

A SEC pede um User-Agent com nome e contato e no máximo 10 pedidos por segundo; sem o contato, recusa o pedido (HTTP 403, conferido nesta sessão). Os scripts leem o User-Agent da variável de ambiente `SEC_USER_AGENT`, que nenhum arquivo versionado nem log guarda. Nesta sessão a variável não estava definida, e a ferramenta de privacidade do ambiente não deixa o agente escrever o contato num comando: **0 de 60 arquivos trimestrais da SEC foram baixados**. Para completar a Fase 0, Roberto define `SEC_USER_AGENT` nas configurações do ambiente (variável de ambiente) e uma sessão nova roda `python -m chiocca.eua.fase0 --baixar`.

## 2. Balanços: os Financial Statement Data Sets da SEC

Os números das demonstrações em XBRL, num zip por trimestre de entrega desde 2009 (aqui, de 2009q1 a 2023q4: os 10-K dos exercícios de 2023, quase todos entregues em 2024, ficam de fora). Os dois arquivos usados são `sub.txt` (uma linha por entrega: CIK, formulário, data de referência, exercício fiscal, datas de entrega e se a entrega foi emendada depois) e `num.txt` (uma linha por número: tag, taxonomia, data, trimestres cobertos, unidade e valor).

- **10-K e 10-K/A:** a entrega original e cada emenda são entregas separadas, cada uma com a sua data; `prevrpt` marca a entrega que foi emendada depois.
- **A versão pública numa data de corte:** por companhia e exercício, a última entrega (original ou emenda com números em XBRL) entregue até a data, como o "como era" do Chiocca no Brasil; o comparativo do exercício seguinte traz os números de t-1 como apresentados depois.

**Pendente (sem os arquivos da SEC):** a estrutura conferida nos arquivos, a cobertura de 10-K por ano, as emendas, os prazos de entrega e a cobertura de cada tag por ano. O código já está pronto e testado com um arquivo sintético (`chiocca/eua/fsds.py`).

### O mapa das contas para as tags us-gaap (proposta)

As contas que os sinais do v1 e do v2 usam, com as tags candidatas na ordem de preferência. Benford usa todos os números e não precisa de mapa; a DVA não existe nos EUA (a depreciação vem da DFC); nos EUA, despesas de vendas e administrativas costumam vir juntas (SG&A), e muitas companhias não apresentam o resultado bruto. As financeiras (peso de ganhos não recorrentes) ficam sem mapa nesta fase.

| Conta | Tags us-gaap candidatas |
| --- | --- |
| `ativo_total` | `Assets` |
| `ativo_circulante` | `AssetsCurrent` |
| `contas_a_receber` | `AccountsReceivableNetCurrent`, `ReceivablesNetCurrent` |
| `imobilizado` | `PropertyPlantAndEquipmentNet` |
| `passivo_circulante` | `LiabilitiesCurrent` |
| `fornecedores` | `AccountsPayableCurrent`, `AccountsPayableAndAccruedLiabilitiesCurrent` |
| `emprestimos_cp` | `DebtCurrent`, `LongTermDebtCurrent`, `ShortTermBorrowings` |
| `emprestimos_lp` | `LongTermDebtNoncurrent`, `LongTermDebtAndCapitalLeaseObligations` |
| `patrimonio_liquido` | `StockholdersEquity`, `StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest` |
| `receita_liquida` | `Revenues`, `RevenueFromContractWithCustomerExcludingAssessedTax`, `SalesRevenueNet` |
| `custo_vendas` | `CostOfRevenue`, `CostOfGoodsAndServicesSold`, `CostOfGoodsSold` |
| `resultado_bruto` | `GrossProfit` |
| `despesas_vendas_gerais_adm` | `SellingGeneralAndAdministrativeExpense` |
| `despesas_financeiras` | `InterestExpense` |
| `lucro_operacoes_continuadas` | `IncomeLossFromContinuingOperations`, `IncomeLossFromContinuingOperationsBeforeIncomeTaxesExtraordinaryItemsNoncontrollingInterest` |
| `lucro_liquido` | `NetIncomeLoss`, `ProfitLoss` |
| `caixa_operacional` | `NetCashProvidedByUsedInOperatingActivities` |
| `depreciacao` | `DepreciationDepletionAndAmortization`, `DepreciationAndAmortization`, `Depreciation` |
| `juros_pagos` | `InterestPaidNet`, `InterestPaid` |

## 3. Rótulos: os AAERs

**era-py 0.0.37** (PyPI, de Ian Gow, os dados do livro *Empirical Research in Accounting: Tools and Methods*): licença do pacote MIT; as tabelas não trazem licença própria, e a origem da ligação gvkey–CIK não é informada. Por isso nada delas é copiado para o repositório: a roda fica em `data/eua/`, com o SHA-256 no manifesto (`5f79fc223a17af9147b65a9a24f918355fc8a31f9341cd7fed8c0267b3591c0c`).

- **O índice de AAERs da SEC** (`aaer_dates`, atualizado pelo autor até 08/10/2026): número, data, descrição e ano. Até 2023, 3.277 AAERs (3.248 números distintos), de 1999 a 2023. A descrição traz nomes de companhias e de pessoas físicas e não é lida aqui.
- **As empresa-anos de Bao et al. (2020)** (`aaer_firm_year`): 415 linhas, 412 AAERs e 402 companhias, identificadas pelo gvkey (Compustat), com o primeiro e o último ano afetados, de 1990 a 2014: 990 empresa-anos com balanço errado alegado. 233 dos AAERs afetam mais de um ano.
- **A ligação gvkey–CIK** (`gvkey_ciks`): 49.089 ligações, 29.099 gvkeys e 27.708 CIKs, com as datas de cada ligação. Com ela, cada empresa-ano de Bao et al. se liga ao CIK da SEC sem a Compustat.
- **A base da CFRM (Berkeley), usada por Dechow et al. (2011):** hoje vendida pelo site da USC (página "Buy the Data", pagamento pelo cashnet; o preço não aparece no texto da página); os termos proíbem passar a base a terceiros, exceto coautores; cobre 4.581 AAERs emitidos de 17/05/1982 a 31/12/2025, com o nome e os identificadores da companhia, as contas afetadas e os anos e trimestres errados (a página não diz quais identificadores). Só as condições de acesso foram lidas.
- **A lista pública de AAERs no site da SEC:** não foi lida diretamente (o site exige o User-Agent com contato); o índice do era-py é uma cópia dela, com a data da atualização.

**Como ligar cada AAER ao CIK sem a Compustat.** Até 2014, pelas empresa-anos de Bao et al. e pela ligação gvkey–CIK do era-py. Depois de 2014, não há base livre com os anos errados: o caminho é ler cada AAER no site da SEC (a companhia é parte do processo) e casar o nome com o arquivo de nomes e CIKs da SEC (`cik-lookup-data.txt`, a conferir quando o acesso estiver configurado), guardando só a companhia e o CIK.

## 4. Contagens

| Exercício | Empresa-anos com AAER (Bao et al.) | Ligadas a um CIK | Com 10-K nos dados da SEC | Empresa-anos com 10-K |
| --- | ---: | ---: | ---: | ---: |
| 2009 | 31 | 30 | pendente | pendente |
| 2010 | 26 | 24 | pendente | pendente |
| 2011 | 22 | 22 | pendente | pendente |
| 2012 | 19 | 19 | pendente | pendente |
| 2013 | 11 | 11 | pendente | pendente |
| 2014 | 4 | 4 | pendente | pendente |

Nos exercícios com XBRL (de 2009 a 2014, o fim dos anos afetados de Bao et al.): 113 empresa-anos com AAER, das quais 110 se ligam a um CIK. Os anos mais recentes têm menos casos porque um AAER costuma sair anos depois da fraude, e a base termina em 2014. O índice da SEC tem 1.572 AAERs emitidos de 2009 a 2023, de todos os tipos (não só balanço errado).

## 5. Decisões para Roberto

1. **Período possível.** Balanços em XBRL desde 2009 (todas as companhias desde 2011). Com rótulos livres, os anos afetados vão só até 2014: a interseção é de 2009 a 2014. Para ir além de 2014, comprar a base da CFRM (até 2025) ou classificar os AAERs da SEC à mão.
2. **Tamanho esperado.** 113 empresa-anos com AAER nos exercícios com XBRL, 110 ligadas a um CIK, contra os 10-K de cada ano (o número sai dos arquivos da SEC). Com fraudes de vários anos contadas uma vez, o número de casos é menor ainda: o poder será baixo, como no estudo 1.
3. **O que não dá sem dados pagos.** Os anos errados depois de 2014 (CFRM); o gvkey e os dados da Compustat (WRDS); as republicações da Audit Analytics. A ligação gvkey–CIK do era-py não informa a origem.
4. **Fraudes de vários anos.** Walker (2021) mostrou que, em Bao et al. (2020), fraudes que atravessam o período de treino e o de teste inflam a medida; a errata (JAR, 2022) reconheceu um erro de código que deixou cerca de 10% desses casos sem recodificar, Walker (2022) criticou a errata, e Gow (2022) discutiu se o artigo deveria ser retratado. Proposta: o desfecho por caso (uma fraude, uma vez), como o acerto do estudo 1, com o bootstrap por companhia, como no estudo 2; os sinais são regras fixas, sem treino.

### Rascunho de calendário até maio de 2027

| Até | Etapa |
| --- | --- |
| 15/12/2026 | Roberto define o User-Agent; a Fase 0 termina com os arquivos da SEC (estrutura, 10-K por ano, cobertura das tags). |
| 15/01/2027 | Decisão dos rótulos (até 2014, ou comprar a CFRM, ou classificar à mão) e do período. |
| 28/02/2027 | Rascunho do pré-registro dos EUA: amostra, desfecho por caso, métricas e regra boba. |
| 31/03/2027 | Revisão de Roberto, registro e carimbo; código congelado. |
| 31/05/2027 | Cálculo único e relatório, separado do estudo 2 do Brasil. |

Fontes das condições e da crítica: sites.google.com/usc.edu/aaerdataset (Buy the Data); econjwatch.org (Walker, 2021 e 2022); iangow.github.io/notes/published/bklyz.html (Gow, 2022).
