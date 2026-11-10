# Análises depois do estudo 1

**Análise descritiva depois do resultado, não pré-registrada.** Autorizada por Roberto Chiocca em 07/11/2026; as seções 2 a 4 foram pedidas em 08/11/2026, e a seção 5, em 09/11/2026. Não altera o estudo 1 (branch `estudo-1-final`): lê `docs/resultados_numeros.json` e `docs/analises_pos_estudo_1_numeros.json` e é gerada por `python -m chiocca.v2.analises_pos_estudo_1`. Não edite à mão: um teste compara este arquivo com a saída do script.

## 1. Quantos acertos o acaso daria?

Para cada um dos 13 casos acertáveis, a chance de ser acertado ao acaso é 1 − produto de (1 − taxa de alerta do grupo no ano), sobre os anos do período afetado que estão nos dados, com as taxas de alerta observadas no estudo 1 (empresas em alerta ÷ empresas avaliadas). O número de acertos ao acaso segue a distribuição binomial de Poisson, calculada de forma exata, sem aproximação.

Em todos os 13 casos, os anos do período afetado nos dados são os mesmos exercícios avaliados no estudo 1.

**Resultado.** Acertos esperados ao acaso: 8,56 (desvio-padrão de 1,61). Acertos observados no estudo 1: 7 de 13. Probabilidade de 7 ou mais acertos ao acaso: 90,0%.

| Caso | Exercícios do período afetado | Taxa de alerta do grupo em cada ano | Chance ao acaso | Acertado no estudo 1 |
| --- | --- | --- | --- | --- |
| Americanas S.A. (`americanas`) | 2021 | 2021: 61,8% | 61,8% | sim |
| Metalúrgica Duque S.A. (`metalurgica_duque`) | 2010, 2011, 2012 | 2010: 49,5%; 2011: 44,8%; 2012: 48,7% | 85,7% | sim |
| Mundial S.A. - Produtos de Consumo (`mundial_2017`) | 2012, 2013, 2014, 2015 | 2012: 48,7%; 2013: 45,6%; 2014: 43,8%; 2015: 50,6% | 92,2% | sim |
| Hércules S.A. - Fábrica de Talheres (`hercules`) | 2014 | 2014: 43,8% | 43,8% | não |
| Tecnosolo Engenharia S.A. (`tecnosolo`) | 2013, 2014 | 2013: 45,6%; 2014: 43,8% | 69,4% | sim |
| Inepar Equipamentos e Montagens S.A. (`inepar_equipamentos`) | 2013 | 2013: 45,6% | 45,6% | não |
| Companhia Energética de Brasília - CEB (`ceb`) | 2011, 2012 | 2011: 44,8%; 2012: 48,7% | 71,7% | não |
| Fibam Companhia Industrial (`fibam`) | 2016, 2017 | 2016: 42,4%; 2017: 43,2% | 67,2% | sim |
| Metalgráfica Iguaçu S.A. (`metalgrafica_iguacu`) | 2010, 2011 | 2010: 49,5%; 2011: 44,8% | 72,1% | sim |
| Café Solúvel Brasília S.A. (`cafe_soluvel_brasilia`) | 2011 | 2011: 44,8% | 44,8% | não |
| Comercial Quintella Comércio e Exportação S.A. (`comercial_quintella`) | 2012, 2013 | 2012: 48,7%; 2013: 45,6% | 72,1% | não |
| Cobrasma S.A. (`cobrasma`) | 2014 | 2014: 43,8% | 43,8% | sim |
| Petróleo Brasileiro S.A. - Petrobras (`petrobras_2014`) | 2010, 2011, 2012 | 2010: 49,5%; 2011: 44,8%; 2012: 48,7% | 85,7% | não |

| Acertos ao acaso | Probabilidade | Probabilidade de pelo menos esse número |
| --- | --- | --- |
| 0 | 0,0% | 100,0% |
| 1 | 0,0% | 100,0% |
| 2 | 0,0% | 100,0% |
| 3 | 0,1% | 100,0% |
| 4 | 0,6% | 99,9% |
| 5 | 2,4% | 99,3% |
| 6 | 7,0% | 97,0% |
| 7 | 14,9% | 90,0% |
| 8 | 22,5% | 75,0% |
| 9 | 24,0% | 52,5% |
| 10 | 17,5% | 28,5% |
| 11 | 8,3% | 11,0% |
| 12 | 2,3% | 2,6% |
| 13 | 0,3% | 0,3% |

**Premissas e o que elas fazem com o resultado.**

- Independência entre os anos de um mesmo caso. Se os alertas se repetem na mesma empresa, essa premissa exagera o acaso: a chance de pelo menos um alerta em vários anos é menor que a calculada com anos independentes. Por isso, 8,56 é um teto para os acertos esperados ao acaso. A seção 2 mede a repetição, e a seção 3 refaz a conta sem essa premissa.
- Independência entre os casos.
- Cada caso tem a taxa de alerta média do seu grupo no ano. As empresas do gabarito podem ser diferentes da média (por exemplo, menores ou mais endividadas), e a taxa delas, ao acaso, pode ser maior ou menor que a média; a direção do efeito não é conhecida.
- As taxas são as do próprio estudo 1, que incluem as empresas do gabarito.
- Esta conta não substitui as métricas pré-registradas (acerto e alarmes por acerto), e não foi decidida antes de ver o resultado.

## 2. Os alertas se repetem na mesma empresa?

Persistência: entre as empresa-anos em alerta cuja empresa também foi avaliada no ano anterior, no mesmo grupo, a fração que também estava em alerta no ano anterior. A comparação é com a taxa geral de alerta (empresa-anos em alerta ÷ empresa-anos avaliadas, 2010 a 2023). Cada empresa conta uma vez por exercício, como nas taxas do estudo 1.

| Grupo | Em alerta, com o ano anterior avaliado | Também em alerta no ano anterior | Persistência | Taxa geral de alerta |
| --- | --- | --- | --- | --- |
| Não financeiras | 2.775 | 2.047 | 73,8% | 49,9% |
| Financeiras | 30 | 14 | 46,7% | 12,0% |
| Total | 2.805 | 2.061 | 73,5% | 48,3% |

**Resultado.** Nas não financeiras, 73,8% das empresa-anos em alerta também estavam em alerta no ano anterior, contra taxa de alerta de 49,9% das empresa-anos não financeiras avaliadas. Os alertas se repetem na mesma empresa, e a premissa de independência entre os anos da seção 1 exagera o acaso.

## 3. Variante sem a premissa de independência entre os anos

Para cada caso, a chance ao acaso é a fração das empresas do mesmo grupo, com dados em todos os anos do período afetado, que tiveram pelo menos um alerta nesses anos. "Com dados" quer dizer avaliada no estudo 1 (pelo menos um sinal de alerta calculável) em cada um desses anos. A repetição dos alertas na mesma empresa entra na conta como aconteceu. O número de acertos ao acaso segue de novo a distribuição binomial de Poisson exata.

**Resultado.** Acertos esperados ao acaso: 7,37 (desvio-padrão de 1,75), contra 8,56 na seção 1. Acertos observados no estudo 1: 7 de 13. Probabilidade de 7 ou mais acertos ao acaso: 69,3%, contra 90,0% na seção 1.

| Caso | Exercícios do período afetado | Empresas avaliadas em todos esses anos | Com pelo menos um alerta | Chance ao acaso | Acertado no estudo 1 |
| --- | --- | --- | --- | --- | --- |
| Americanas S.A. (`americanas`) | 2021 | 597 | 369 | 61,8% | sim |
| Metalúrgica Duque S.A. (`metalurgica_duque`) | 2010, 2011, 2012 | 328 | 222 | 67,7% | sim |
| Mundial S.A. - Produtos de Consumo (`mundial_2017`) | 2012, 2013, 2014, 2015 | 345 | 260 | 75,4% | sim |
| Hércules S.A. - Fábrica de Talheres (`hercules`) | 2014 | 434 | 190 | 43,8% | não |
| Tecnosolo Engenharia S.A. (`tecnosolo`) | 2013, 2014 | 399 | 224 | 56,1% | sim |
| Inepar Equipamentos e Montagens S.A. (`inepar_equipamentos`) | 2013 | 443 | 202 | 45,6% | não |
| Companhia Energética de Brasília - CEB (`ceb`) | 2011, 2012 | 380 | 229 | 60,3% | não |
| Fibam Companhia Industrial (`fibam`) | 2016, 2017 | 408 | 220 | 53,9% | sim |
| Metalgráfica Iguaçu S.A. (`metalgrafica_iguacu`) | 2010, 2011 | 365 | 214 | 58,6% | sim |
| Café Solúvel Brasília S.A. (`cafe_soluvel_brasilia`) | 2011 | 426 | 191 | 44,8% | não |
| Comercial Quintella Comércio e Exportação S.A. (`comercial_quintella`) | 2012, 2013 | 402 | 232 | 57,7% | não |
| Cobrasma S.A. (`cobrasma`) | 2014 | 434 | 190 | 43,8% | sim |
| Petróleo Brasileiro S.A. - Petrobras (`petrobras_2014`) | 2010, 2011, 2012 | 328 | 222 | 67,7% | não |

| Acertos ao acaso | Probabilidade | Probabilidade de pelo menos esse número |
| --- | --- | --- |
| 0 | 0,0% | 100,0% |
| 1 | 0,0% | 100,0% |
| 2 | 0,2% | 100,0% |
| 3 | 1,1% | 99,8% |
| 4 | 3,7% | 98,7% |
| 5 | 9,2% | 94,9% |
| 6 | 16,4% | 85,8% |
| 7 | 21,8% | 69,3% |
| 8 | 21,3% | 47,6% |
| 9 | 15,3% | 26,3% |
| 10 | 7,8% | 11,0% |
| 11 | 2,7% | 3,3% |
| 12 | 0,5% | 0,6% |
| 13 | 0,1% | 0,1% |

**Premissas e o que elas fazem com o resultado.**

- Independência entre os casos, como na seção 1.
- Só entram as empresas avaliadas em todos os anos do período afetado. Empresas que entraram ou saíram no meio do período ficam fora, e a taxa de alerta delas pode ser diferente.
- As frações incluem as empresas do gabarito: em 13 dos 13 casos, a própria empresa do caso está entre as contadas.
- Esta conta também não substitui as métricas pré-registradas, e não foi decidida antes de ver o resultado.

## 4. Nota posterior: balanços não preenchidos no estudo 1

**Nota posterior, de 08/11/2026.** Verificação pedida na resposta à Fase B (item 1c). Não muda o estudo 1: só relata.

A conferência "não preenchido" da v2 (`chiocca.v2.conferencias`) achou 104 colunas de balanço com ativo total zero na base do estudo 1: 16 na coluna do exercício (ÚLTIMO) e 88 no comparativo (PENÚLTIMO), em 93 empresa-anos. Dessas empresa-anos, 57 estão na amostra de não financeiras, 2 na de financeiras e 34 fora da amostra. Em 78 das colunas, o balanço inteiro está zerado; nas outras 26, só o total.

Critério: um cálculo do estudo 1 usou zero como valor quando o sinal tem valor no estudo 1 e pelo menos uma conta de balanço que ele usa, numa dessas colunas, vale zero.

**Resultado: sim.** Em 57 empresa-anos, pelo menos um cálculo do estudo 1 usou como valor um zero de balanço de uma dessas colunas.

| Sinal | Empresa-anos calculadas com zero | Alertas desse sinal nessas empresa-anos |
| --- | --- | --- |
| DSRI, índice de dias de recebimento | 1 | componente do M-score: não dispara alerta sozinho |
| DEPI, índice de depreciação | 2 | componente do M-score: não dispara alerta sozinho |
| salto do prazo de pagamento a fornecedores (DPO) | 2 | 0 |
| juro implícito menos CDI médio | 49 | 29 |
| lucro sem caixa (accruals sobre o ativo médio) | 56 | só contexto: não dispara alerta |

- Juro implícito: em 49 empresa-anos, a dívida (curto mais longo prazo) é zero numa das colunas. A dívida média de t e t−1 fica na metade da dívida do outro ano, e o juro implícito fica no dobro do que daria com a dívida desse outro ano.
- Empresa-anos em alerta no estudo 1 só por sinais calculados com zero: 29. Empresa-anos avaliadas só por sinais calculados com zero: 50.
- Salto do DPO: 2 valores calculados com zero entraram no limite do decil superior do ano. Sem eles, nenhum alerta de DPO de outra empresa-ano mudaria.
- Gabarito: nenhuma dessas empresa-anos está no período afetado de um caso. Os 7 acertos do estudo 1 não mudam.

**Sem as 57 empresa-anos afetadas** (mesmo rótulo: análise descritiva depois do resultado, não pré-registrada; o estudo 1 não muda). Taxa de alerta e alarmes por acerto recalculados pelas funções do estudo 1 (`chiocca.metricas`), sem essas empresa-anos:

| Não financeiras | Estudo 1 | Sem as 57 empresa-anos afetadas |
| --- | --- | --- |
| Taxa de alerta das empresa-anos avaliadas | 49,9% (3.345 de 6.704) | 49,8% (3.316 de 6.654) |
| Alarmes por acerto, período de teste (2017–2023) | 311,0 | 309,5 |
| Alarmes por acerto, período inteiro (2010–2023) | 108,3 | 108,0 |
| Casos acertados | 7 de 13 | 7 de 13 |

Recalcular os alertas pelas regras do estudo 1, com os limites do decil sem essas empresa-anos, dá os mesmos números.

No produto, a regra é outra: indicador que depende de balanço não preenchido fica "não calculável", nunca calculado com zero (`chiocca.v2.linhagem.aplicar_nao_preenchido`). A lista das empresa-anos fica em `resultados/nao_preenchidas_estudo_1.csv`, fora do git.

## 5. Antecedência dos acertos

**Análise descritiva depois do resultado, não pré-registrada.** Pedida por Roberto Chiocca em 09/11/2026. O estudo 1 não muda. Para cada um dos 7 acertos, o tempo entre a entrega da primeira DFP do período afetado que deixou a empresa em alerta (entre as entregues antes da data pública, que são as que contam para o acerto) e a data pública do caso, em meses (dias × 12 ÷ 365,25). Lido de `docs/resultados_numeros.json`.

| Caso | Primeira DFP em alerta no período afetado | Entregue em | Data pública | Meses de antecedência |
| --- | --- | --- | --- | --- |
| Americanas S.A. (`americanas`) | 2021 | 24/02/2022 | 11/01/2023 | 10,5 |
| Metalúrgica Duque S.A. (`metalurgica_duque`) | 2010 | 22/03/2011 | 06/08/2014 | 40,5 |
| Mundial S.A. - Produtos de Consumo (`mundial_2017`) | 2012 | 09/04/2013 | 06/03/2017 | 46,9 |
| Tecnosolo Engenharia S.A. (`tecnosolo`) | 2013 | 07/04/2014 | 12/05/2015 | 13,1 |
| Fibam Companhia Industrial (`fibam`) | 2016 | 27/03/2017 | 08/11/2018 | 19,4 |
| Metalgráfica Iguaçu S.A. (`metalgrafica_iguacu`) | 2010 | 25/03/2011 | 20/12/2012 | 20,9 |
| Cobrasma S.A. (`cobrasma`) | 2014 | 30/03/2015 | 13/07/2015 | 3,4 |

Mediana de 19,4 meses, de 3,4 a 46,9 meses. Antecedência não é métrica do pré-registro do estudo 1; no estudo 2, ela entra como métrica pré-registrada (roadmap).
