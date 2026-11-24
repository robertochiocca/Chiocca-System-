# Rascunho do pré-registro do estudo dos EUA

> **Rascunho, não é registro.** Escrito em 24/11/2026 pelo agente, com as decisões de Roberto da mesma data ([Fase 0, seção 5.1](eua-fase-0.md)), antes de qualquer sinal americano calculado. Nada aqui vale até Roberto revisar e o texto ser registrado (o commit que o introduz como registro e o hash anotado no commit seguinte), até 31/03/2027. A frente dos EUA fica fora do README e do produto. Alerta, não acusação: um 8-K com o item 4.02 é uma declaração de que demonstrações publicadas não valem mais, não uma acusação de fraude; nenhum alerta por companhia é publicado.

Base: a [Fase 0 dos EUA](eua-fase-0.md), com os números de [`docs/eua_fase0_numeros.json`](eua_fase0_numeros.json), e os pré-registros do [estudo 1](pre-registro.md), do [estudo 2](pre-registro-estudo-2.md) e do [motor v2](pre-registro-motor-v2.md), cujas regras valem aqui com só as adaptações da seção 3.

## 1. Pergunta

Com os 10-K como eram na época, os alertas do motor v1 e do motor v2, congelados no Brasil, e a regra boba separam as empresa-anos seguidas de um 8-K com o item 4.02 nos 12 meses depois do corte das que não foram? E o v2 separa melhor que o v1?

**Rótulo: retrospectivo.** Os dados de 2011 a 2023 já são públicos, e as contagens de 8-K 4.02 por ano já apareceram na Fase 0, sem nenhuma ligação com sinal. O teste é limpo porque as regras são fixas (sem treino), foram escritas e congeladas no Brasil, e este texto é registrado antes de qualquer sinal americano.

## 2. Os sinais: o v1 e o v2 congelados

- **v1:** as regras da seção 4 do pré-registro do estudo 1, com as emendas, no código registrado em [`docs/estudo_2_codigo_congelado.json`](estudo_2_codigo_congelado.json): M-score acima de -1,78; salto do DPO no decil superior do exercício; juro implícito acima da taxa de referência média do ano mais 10 p.p.; alerta quando pelo menos um sinal dispara.
- **v2:** as regras do pré-registro do motor v2, no código registrado em [`docs/motor_v2_codigo_congelado.json`](motor_v2_codigo_congelado.json): percentis do M-score, do salto do DPO, do juro implícito e do desvio de Benford padronizado, dentro do exercício e do grupo; escore igual ao maior percentil; alerta quando o escore fica no quantil de 90% ou acima.
- **O código:** as funções de sinal dos dois registros são chamadas sem mudar nenhuma linha. O script dos EUA só monta as entradas de cada empresa-ano a partir do XBRL e aplica as adaptações da seção 3. Só o grupo das não financeiras (seção 4).

## 3. As adaptações (as únicas), cada uma com o motivo

### 3.1 O mapa das contas para as tags us-gaap

Valores da própria companhia (sem co-registrante nem segmento), em dólar, na taxonomia us-gaap: o balanço na data de referência; o resultado e o fluxo de caixa do exercício (quatro trimestres). O ano anterior (t-1) vem do mesmo 10-K, como a coluna do exercício anterior da DFP. Conta faltante ou denominador zero: "não calculável", como no v1, sem imputação. O sinal das despesas segue a convenção da DFP (negativo), e o código do v1 já usa o valor absoluto onde precisa.

| Conta | Tags e regra | Motivo |
| --- | --- | --- |
| `ativo_total`, `ativo_circulante`, `contas_a_receber`, `imobilizado`, `passivo_circulante`, `patrimonio_liquido`, `caixa_operacional`, `depreciacao`, `custo_vendas`, `lucro_liquido` | as da proposta da Fase 0, na ordem de preferência | o mesmo conceito da conta da DFP |
| `receita_liquida` | as três da Fase 0 e as tags que a ampliação acrescentar antes do registro, escolhidas só pela cobertura (contagens) | a receita cobre de 66% a 73% dos 10-K de 2011 a 2021 com as três tags; sem a ampliação, a regra das sem receita tiraria companhias que têm receita |
| `resultado_bruto` | `GrossProfit`; se ausente, receita menos custo das vendas | na DFP a linha 3.03 é obrigatória; no US GAAP o lucro bruto é opcional (cobertura de 35% a 37%) |
| `despesas_vendas` + `despesas_gerais_adm` | `SellingGeneralAndAdministrativeExpense`, que já junta as duas | o v1 soma as duas contas; no US GAAP elas vêm juntas |
| `lucro_operacoes_continuadas` | `IncomeLossFromContinuingOperations`; se ausente, o lucro líquido menos `IncomeLossFromDiscontinuedOperationsNetOfTax`, quando houver | a conta 3.09 é depois dos impostos; a tag antes dos impostos da proposta da Fase 0 sai, por ser outro conceito |
| `emprestimos_cp` | `DebtCurrent`; se ausente, a soma de `LongTermDebtCurrent` e `ShortTermBorrowings` presentes | no US GAAP a dívida de curto prazo pode vir em linhas separadas |
| `emprestimos_lp` | `LongTermDebtNoncurrent`; se ausente, `LongTermDebtAndCapitalLeaseObligations` | o mesmo conceito, com a segunda tag como reserva |
| `despesas_financeiras` | `InterestExpense` | limite registrado: a despesa financeira da DFP inclui variação cambial e outros encargos; a tag americana é só de juros |
| `fornecedores` | `AccountsPayableCurrent`; se ausente, `AccountsPayableAndAccruedLiabilitiesCurrent`, com a marca de que inclui provisões | a segunda tag é mais larga |
| `passivo_total` (regra boba) | `Liabilities`; se ausente, `LiabilitiesAndStockholdersEquity` menos o patrimônio líquido com minoritários | a regra boba usa passivo total ÷ ativo total, e muitas companhias não apresentam o total do passivo |

O desvio de Benford usa os valores diferentes de zero do exercício na demonstração do balanço, do resultado e do fluxo de caixa do 10-K (pela coluna `stmt` de `pre.txt`: BS, IS e CF), o equivalente americano de BPA, BPP, DRE e DFC, com o mínimo de 20 números do v2. A DVA não existe nos EUA: o DEPI do v2 é o do v1, pela depreciação do fluxo de caixa. Antes do registro, a cobertura de cada conta com as regras acima é contada (só contagens) e entra no texto registrado.

### 3.2 A taxa que substitui o CDI

A Effective Federal Funds Rate, série diária DFF do FRED (Federal Reserve Bank of St. Louis), cuja fonte é a publicação H.15 do Federal Reserve: pública, gratuita e sem chave. Como `chiocca.cdi.medio`, a média das taxas diárias nos 12 meses que terminam no fim do exercício, com o mesmo corte de 10 p.p. Motivo: é a taxa do overnight interbancário dos EUA, o papel do CDI no Brasil. Limite registrado: a DFF anualiza em base de 360 dias corridos e o CDI em base de 252 dias úteis. O arquivo da série entra no repositório, como `data/cdi_sgs4389.csv`, com o SHA-256 no manifesto.

### 3.3 A data de corte

A mesma regra do estudo 1 (emenda 5, `chiocca.corte.data_corte`): o último dia do quarto mês depois do fim do exercício. Motivo: o prazo do 10-K é de 60, 75 ou 90 dias, conforme o porte, e, de 2011 a 2021, o décimo de 10-K entregues mais tarde saiu até 107 dias depois da data de referência (seção 2.2 da Fase 0). A versão usada é a pública no corte: a última entrega até a data entre o 10-K original e os 10-K/A com números das contas (seção 2.3 da Fase 0). A companhia sem 10-K com XBRL até o corte fica fora daquele exercício, como no Brasil.

### 3.4 O que não se adapta

As financeiras: o mapa não tem as contas delas, e por isso o grupo das financeiras e o peso de ganhos não recorrentes não existem neste estudo. A DVA (seção 3.1). O leitor de documentos.

## 4. Amostra e exclusões

- **Universo:** os 10-K originais dos Financial Statement Data Sets com data de referência de 2011 a 2021 (o exercício é o ano da data de referência, como na DFP). 2011, porque o XBRL vale para todas as companhias a partir dos períodos depois de 15/06/2011; 2021, porque a janela do desfecho do exercício seguinte passaria de 31/12/2023, o limite dos dados da Fase 0.
- **Exclusões, nesta ordem, cada uma contada no relatório:** (1) sem versão pública com XBRL até o corte; (2) as financeiras pela SIC, de 6000 a 6999, exceto 6770 (seção 3.4); (3) as SPACs, SIC 6770, regra explícita decidida por Roberto em 24/11/2026; (4) as sem receita (receita ausente ou zero, a regra do estudo 1, pelo mapa ampliado); (5) as sem nenhum sinal calculável. A SIC e a receita são as da versão usada.
- **O tamanho, pela Fase 0 (exercício declarado, mapa da Fase 0):** de 2011 a 2021, 69.225 10-K originais; a regra das sem receita tiraria no máximo 26.715 (um teto, porque o mapa da receita ainda não foi ampliado), 8.632 deles de financeiras; as SPACs são 2.224, das quais 2.103 já sem receita.

## 5. O desfecho: o 8-K com o item 4.02, por caso

- **Episódio (o caso):** o primeiro 8-K de uma companhia com o item 4.02 no campo de itens do EDGAR abre um episódio; todo 8-K ou 8-K/A com o item 4.02 da mesma companhia nos 365 dias seguintes pertence a ele; depois disso, um novo 8-K 4.02 abre outro episódio. Cada episódio conta uma vez, a resposta à crítica de Walker e de Gow a Bao et al. (Fase 0, seção 5.1).
- **Janela:** a empresa-ano t é positiva se um episódio se abre depois do corte de t e até 12 meses depois dele. As janelas de exercícios seguidos da mesma companhia não se sobrepõem, e cada episódio cai em no máximo uma empresa-ano. Os episódios fora de qualquer empresa-ano da amostra entram só na descrição.
- **Fonte:** o campo de itens do histórico de entregas do EDGAR (`submissions.zip`), baixado de novo no dia do cálculo, com o SHA-256 no manifesto, e só os 8-K entregues até 31/12/2023.
- **O tamanho, pela Fase 0:** de 2009 a 2023, 2.029 companhias-ano com 8-K 4.02 e 10-K nos dados da SEC antes do 8-K; 332 delas de SPACs e 975 sem receita pelo mapa da Fase 0; ficam 1.048 depois das duas regras, de 54 a 127 por ano de 2012 a 2023.
- **Limites:** o item 4.02 não diz quais demonstrações deixaram de valer: o desfecho é uma declaração de não confiabilidade nos 12 meses seguintes, sem garantia de que trata do exercício t. As republicações sem 8-K ("little r") ficam de fora. Nada disso é chamado de fraude.

## 6. Métricas: as do estudo 2

- **Medida principal:** a diferença de risco DR = P(positiva | em alerta) − P(positiva | fora de alerta), nas empresa-anos avaliadas pelo v1, com todos os exercícios juntos; também a razão de taxas.
- **Bootstrap por companhia:** sorteiam-se companhias com reposição, cada uma com todas as suas empresa-anos; 10.000 reamostragens, com a semente 20270430; o intervalo é o percentil unilateral de 95%. As funções são `taxas`, `dr`, `bootstrap_por_companhia` e `limite_inferior` de `chiocca/v2/estudo2/secundaria.py`, chamadas sem mudar nenhuma linha.
- **Resultado:** "associação positiva" se o limite inferior do intervalo unilateral de 95% da DR ficar acima de zero; senão, "sem evidência de associação".
- **Regra boba lado a lado:** o decil mais endividado (passivo total ÷ ativo total) de cada exercício, como no estudo 1, com a mesma DR e o bootstrap pareado (as mesmas reamostragens): "o motor separa melhor que a regra boba" só se o limite inferior da diferença ficar acima de zero.
- **O v2 pareado com o v1:** como na emenda 5 do estudo 2. O alerta do v2 sai de todas as empresa-anos que o v2 avalia; as medidas são calculadas nas empresa-anos avaliadas pelo v1; "o v2 separa melhor que o v1" só se o limite inferior da diferença pareada ficar acima de zero; senão, sem vencedor declarado.
- **Descritivas:** as métricas de ranking do estudo 2 (precisão e lift no topo de 1%, 5% e 10% e NDCG@k), cada exercício separado e os AAERs (seção 7). Só agregados: nenhuma lista de companhias por alerta.

## 7. Os AAERs de 2009 a 2014: descrição à parte

Para os 25 casos de Bao et al. (47 empresa-anos) com 10-K nos dados da SEC (Fase 0, seção 4.1): quantos casos o v1, o v2 e a regra boba alertaram em pelo menos um exercício afetado, com a versão pública no corte. Só contagens, sem teste e sem lista. Em 2009 e 2010, só as companhias maiores entregavam em XBRL.

## 8. Previsões escritas antes dos dados

1. **Taxa de alerta do v1:** entre 25% e 45% das não financeiras avaliadas em cada exercício. Motivo: o M-score acima de -1,78 marca parte relevante das companhias americanas, e o decil do DPO soma 10%; o juro implícito dispara menos que no Brasil, porque a despesa de juros americana não inclui variação cambial.
2. **Taxa de alerta do v2:** entre 10,0% e 11,0% em cada exercício, pela construção do decil.
3. **Taxa do desfecho:** entre 1,5% e 4% das empresa-anos avaliadas. Motivo: as contagens da seção 5, cerca de uma centena de companhias-ano por ano, contra alguns milhares de avaliadas.
4. **DR do v1:** positiva, com razão de taxas entre 1,1 e 1,5, e "associação positiva" mais provável que não, pelo tamanho da amostra.
5. **DR do v2:** positiva, com razão de taxas entre 1,2 e 2,0, e "associação positiva".
6. **O v2 pareado com o v1:** diferença positiva, com o limite inferior acima de zero ("o v2 separa melhor que o v1"). Motivo: o grupo em alerta do v2 é menor e mais extremo.
7. **O v2 contra a regra boba:** sem vencedor declarado. Motivo: o endividamento também se associa a republicações, pela dificuldade financeira.
8. **AAERs:** dos 25 casos, entre 30% e 60% em alerta no v1 e entre 10% e 30% no v2 em pelo menos um exercício afetado.

## 9. Calendário até maio de 2027

| Até | Etapa |
| --- | --- |
| 24/11/2026 | Decisões de Roberto: o rótulo, o desfecho por caso e as exclusões. Este rascunho. |
| 15/12/2026 | Revisão de Roberto deste rascunho; nenhum sinal calculado. |
| 31/01/2027 | Código do estudo escrito e testado só em dados sintéticos; a cobertura do mapa ampliado contada (só contagens); nenhum sinal americano calculado. |
| 31/03/2027 | Registro do pré-registro e carimbo; código congelado com registro de SHA-256. |
| 30/04/2027 | Cálculo único, depois do carimbo, com os arquivos da SEC baixados de novo no dia. |
| 31/05/2027 | Relatório em PT e EN, separado do estudo 2 do Brasil. |

## 10. Pontos em aberto para Roberto, antes do registro

1. A exclusão das financeiras (seção 3.4).
2. As tags da ampliação da receita e as derivações da seção 3.1, escolhidas pela cobertura.
3. O fim da amostra em 2021, com os dados até 31/12/2023, ou um limite mais tarde para os dados dos EUA (o lacre do Brasil não trata deles; o limite de 2023 veio do pedido da Fase 0).
4. A semente (20270430, a data do cálculo único).
5. O arquivo dos dados: os arquivos da SEC passam de 6 GB e ficam fora do Git, com o SHA-256 no manifesto e o download por script.

## 11. O que fica de fora

As financeiras, a DVA e o leitor (seção 3.4); qualquer lista ou ordem de companhias por alerta; qualquer recomendação de investimento; e, até decisão de Roberto, a frente dos EUA no README e no produto.
