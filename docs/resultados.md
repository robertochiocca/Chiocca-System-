# Resultados (Fase 2)

Gerado por `python -m chiocca.relatorio_resultados` a partir de `resultados/sinais_empresa_ano.csv` (fora do git), que sai de `python -m chiocca.sinais_amostra`. Não edite à mão: um teste compara este arquivo com a saída do script. Só aparecem números agregados, os casos do gabarito, que são públicos, e a tabela dos casos em observação (emenda 8). Nenhuma lista de empresas em alerta sai deste repositório.

Sinais calculados em 07/11/2026 com o código do commit `ca1256c`. O período de teste (exercícios de 2017 a 2023, pré-registro, seção 8) foi aberto em 07/11/2026, com o commit `9e8c758`, na primeira execução da amostra inteira. As regras foram aplicadas como estão no pré-registro, sem nenhum corte alternativo testado. O resultado é mostrado como saiu (seção 9).

## Números principais

- **Amostra, 2010 a 2023:** 6.938 empresa-anos de não financeiras com receita e 517 de financeiras, de 987 empresas. Ficaram de fora 1.139 empresa-anos de não financeiras sem receita (seção 2) e 880 sem versão da época (emenda 5).
- **Acerto (seção 5):** 7 de 13 casos acertáveis. Depois da exclusão das empresas sem receita, continuam acertáveis 13 de 13 (emenda 9). Contando todos os 42 casos do gabarito, são 7 de 42, com teto de 13 de 42 no estudo principal.
- **Regra boba (seção 7):** 6 de 13 casos acertáveis.
- **Alarmes por acerto (emenda 10), não financeiras, 2017 a 2023:** 624 empresas em alerta, de 758 avaliadas; (624 − 7) ÷ 7 = 88,1. Com a regra boba: 109 empresas em alerta, de 775; (109 − 6) ÷ 6 = 17,2.
- **Financeiras, 2017 a 2023:** 11 empresas em alerta, de 36 avaliadas. Alarmes por acerto não calculável: nenhum caso acertável é financeira. Com a regra boba: 13 empresas em alerta, de 46.
- Dos 7 casos acertados, 2 têm alerta no período de teste. A fórmula da emenda 10 desconta os 7 casos acertados das empresas em alerta.
- **Taxa de alerta, 2010 a 2023, somando os exercícios:** não financeiras, 3.345 empresas em alerta de 6.704 avaliadas (49,9%); financeiras, 36 de 300 (12,0%).
- **Comparação com a regra boba:** o detector acerta 7 casos e a regra boba, 6. Nas não financeiras, o detector tem 88,1 alarmes por acerto e a regra boba, 17,2: 5,1 vezes mais. O pré-registro manda pôr essa comparação no resumo.

## Regras aplicadas

- **Versão da época:** a de cada empresa-ano na data de corte, da base da Fase 1; t vem do ÚLTIMO e t−1 do PENÚLTIMO da mesma DFP (emenda 5).
- **Contas:** pelos códigos confirmados na Fase 0 (reconhecimento, parte 1.4). Depreciação e juros pagos pelos padrões de texto congelados (reconhecimento, parte 4.2), com a regra de conta-mãe e a comparação de texto da emenda 7.
- **Juros pagos:** os que estão no caixa operacional (seção 6.01) passam para o financiamento em todas as empresas; o caixa operacional ajustado entra no TATA e no lucro sem caixa (pré-registro, seção 4.1).
- **Depreciação e amortização numa linha só:** usa-se o total e a empresa-ano é marcada (seção 4.1).
- **Conta ausente, denominador zero ou receita negativa no denominador:** não calculável (seção 4.1 e emenda 10). Sem valores neutros e sem aparar extremos (seção 4.1).
- **CDI:** série 4389 do SGS do Banco Central (docs/fontes.md); CDI médio do ano = média das taxas diárias nos 12 meses que terminam na data de referência da DFP.
- **Alertas (seção 4):** M > -1,78; variação do DPO no decil superior do ano dentro das não financeiras; juro implícito > CDI médio + 10 p.p.; peso não recorrente no decil superior do ano dentro das financeiras. Não financeira em alerta = pelo menos um dos três sinais; o lucro sem caixa não dispara alerta.
- **Regra boba (emenda 7):** (ativo total − patrimônio líquido de nível mais alto) ÷ ativo total, decil superior de cada ano dentro de cada grupo.
- **Acerto (seção 5):** alerta em pelo menos um exercício do período afetado, entre 2010 e 2023, com a versão da época entregue antes da data pública. Em todos esses exercícios, a data de corte também é anterior à data pública (0 exceções).

## Escolhas de implementação desta fase

O pré-registro não desce a estes detalhes. Cada um foi fixado antes de rodar a amostra, sem testar alternativa, e fica aqui para revisão.

- **Decil superior:** valor maior ou igual ao percentil 90 dos valores calculáveis do exercício e do grupo (percentil com interpolação linear, o padrão do pandas).
- **Empresa avaliada:** com pelo menos um sinal de alerta do grupo calculável. A taxa de alerta é empresas em alerta ÷ empresas avaliadas; o tamanho da amostra vem ao lado.
- **DFC pelo método direto:** os padrões de texto foram aplicados à DFC que a empresa tem. Nas 190 empresa-anos com DFC pelo método direto, não há linha de depreciação, e o M-score fica não calculável (conta ausente).
- **Não financeiras em outro plano de contas:** os códigos da Fase 0 valem para o plano não financeiro. Nas 15 empresa-anos de não financeiras no plano de banco ou não reconhecido, M-score, DPO e juro implícito ficam não calculáveis (motivo: plano de contas).
- **Juros pagos não achados:** o caixa operacional fica como apresentado. Linhas achadas na seção 6.01 (movidas) em 2.716 empresa-anos e na seção 6.03 (já no financiamento) em 1.929.
- **Casos em observação na conta de alarmes:** a empresa inteira fica fora, em todos os anos (a Oi tem caso em observação nas DFs de 2015 e 2016 e também caso no gabarito, Oi 2014, na secundária).
- **Emenda 3:** aplicada aos 20 casos do gabarito fora da análise secundária que têm código CVM e data pública; a última DFP é a da empresa-ano mais recente da amostra entregue antes da data.
- **Marca do CPC 06 (R2):** exercícios que começam em 2019 (498 empresa-anos). A marca não muda nenhum cálculo.

## Taxa de alerta por ano

**Não financeiras.** Empresas por exercício. Nas colunas dos sinais: empresa-anos com alerta ÷ empresa-anos com o sinal calculável.

| Exercício | Amostra | Avaliadas | Em alerta | Taxa | M > -1,78 | Salto do DPO | Juro implícito | Regra boba |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2010 | 434 | 408 | 202 | 49,5% | 53 / 317 | 40 / 391 | 147 / 383 | 10,1% |
| 2011 | 444 | 426 | 191 | 44,8% | 51 / 343 | 42 / 411 | 146 / 395 | 9,9% |
| 2012 | 440 | 427 | 208 | 48,7% | 49 / 334 | 40 / 396 | 154 / 394 | 10,0% |
| 2013 | 462 | 443 | 202 | 45,6% | 43 / 345 | 42 / 413 | 159 / 409 | 10,2% |
| 2014 | 454 | 434 | 190 | 43,8% | 42 / 349 | 41 / 406 | 139 / 401 | 10,1% |
| 2015 | 457 | 441 | 223 | 50,6% | 36 / 358 | 42 / 419 | 182 / 406 | 10,1% |
| 2016 | 451 | 432 | 183 | 42,4% | 31 / 349 | 41 / 409 | 138 / 392 | 10,2% |
| 2017 | 471 | 454 | 196 | 43,2% | 47 / 356 | 43 / 425 | 144 / 407 | 10,2% |
| 2018 | 469 | 451 | 234 | 51,9% | 42 / 355 | 43 / 423 | 181 / 403 | 10,0% |
| 2019 | 465 | 450 | 238 | 52,9% | 50 / 356 | 43 / 429 | 184 / 423 | 10,1% |
| 2020 | 556 | 544 | 321 | 59,0% | 74 / 425 | 52 / 514 | 264 / 507 | 10,1% |
| 2021 | 616 | 597 | 369 | 61,8% | 118 / 481 | 57 / 565 | 284 / 556 | 10,1% |
| 2022 | 604 | 596 | 320 | 53,7% | 100 / 506 | 57 / 566 | 226 / 566 | 10,1% |
| 2023 | 609 | 601 | 268 | 44,6% | 74 / 516 | 58 / 574 | 180 / 572 | 10,0% |
| **Total (soma dos exercícios)** | 6.932 | 6.704 | 3.345 | 49,9% | 810 / 5.390 | 641 / 6.341 | 2.528 / 6.214 | 10,1% |

**Financeiras.**

| Exercício | Amostra | Avaliadas | Em alerta | Taxa | Regra boba |
| --- | --- | --- | --- | --- | --- |
| 2010 | 33 | 13 | 2 | 15,4% | 12,1% |
| 2011 | 40 | 19 | 2 | 10,5% | 10,0% |
| 2012 | 42 | 21 | 3 | 14,3% | 11,9% |
| 2013 | 42 | 22 | 3 | 13,6% | 11,9% |
| 2014 | 42 | 22 | 3 | 13,6% | 11,9% |
| 2015 | 41 | 22 | 3 | 13,6% | 12,2% |
| 2016 | 38 | 19 | 2 | 10,5% | 10,5% |
| 2017 | 38 | 20 | 2 | 10,0% | 10,5% |
| 2018 | 37 | 20 | 2 | 10,0% | 10,8% |
| 2019 | 33 | 18 | 2 | 11,1% | 12,1% |
| 2020 | 33 | 25 | 3 | 12,0% | 12,1% |
| 2021 | 34 | 26 | 3 | 11,5% | 11,8% |
| 2022 | 34 | 28 | 3 | 10,7% | 11,8% |
| 2023 | 30 | 25 | 3 | 12,0% | 10,0% |
| **Total (soma dos exercícios)** | 517 | 300 | 36 | 12,0% | 11,4% |

## Casos acertáveis, caso a caso

Os 13 casos acertáveis do gabarito (emendas 8 e 9). Exercícios avaliados: na amostra, com versão da época entregue antes da data pública e com pelo menos um sinal calculável.

| Caso | Código CVM | Período afetado nos dados | Data pública | Exercícios avaliados | Exercícios em alerta | Fora da conta | Acertado | Regra boba |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Americanas S.A. (`americanas`) | 20990 | 2021 | 11/01/2023 | 2021 | 2021 | — | sim | não |
| Metalúrgica Duque S.A. (`metalurgica_duque`) | 8648 | 2010, 2011, 2012 | 06/08/2014 | 2010, 2011, 2012 | 2010, 2011, 2012 | — | sim | não |
| Mundial S.A. - Produtos de Consumo (`mundial_2017`) | 5312 | 2012, 2013, 2014, 2015 | 06/03/2017 | 2012, 2013, 2014, 2015 | 2012, 2013, 2014, 2015 | — | sim | sim |
| Hércules S.A. - Fábrica de Talheres (`hercules`) | 6629 | 2014 | 06/03/2017 | 2014 | — | — | não | sim |
| Tecnosolo Engenharia S.A. (`tecnosolo`) | 11207 | 2013, 2014 | 12/05/2015 | 2013, 2014 | 2013, 2014 | — | sim | não |
| Inepar Equipamentos e Montagens S.A. (`inepar_equipamentos`) | 17868 | 2013 | 19/09/2014 | 2013 | — | — | não | não |
| Companhia Energética de Brasília - CEB (`ceb`) | 14451 | 2011, 2012 | 29/09/2017 | 2011, 2012 | — | — | não | não |
| Fibam Companhia Industrial (`fibam`) | 6017 | 2016, 2017 | 08/11/2018 | 2016, 2017 | 2016, 2017 | — | sim | sim |
| Metalgráfica Iguaçu S.A. (`metalgrafica_iguacu`) | 8605 | 2010, 2011 | 20/12/2012 | 2010, 2011 | 2010, 2011 | — | sim | não |
| Café Solúvel Brasília S.A. (`cafe_soluvel_brasilia`) | 2062 | 2011 | 15/09/2012 | 2011 | — | — | não | sim |
| Comercial Quintella Comércio e Exportação S.A. (`comercial_quintella`) | 15652 | 2012, 2013 | 13/07/2015 | 2012, 2013 | — | — | não | sim |
| Cobrasma S.A. (`cobrasma`) | 4448 | 2014 | 13/07/2015 | 2014 | 2014 | — | sim | sim |
| Petróleo Brasileiro S.A. - Petrobras (`petrobras_2014`) | 9512 | 2010, 2011, 2012 | 10/10/2014 | 2010, 2011, 2012 | — | — | não | não |

**Sinais por exercício.** M: valor do M-score (alerta se > -1,78). DPO: variação do prazo de pagamento, em dias (alerta no decil superior do ano). Juro: juro implícito menos CDI médio, em p.p. (alerta se > 10). n.c. = não calculável, com os componentes que faltaram. Em negrito, o sinal que disparou.

| Caso | Exercício | M | DPO | Juro − CDI | Em alerta | Regra boba |
| --- | --- | --- | --- | --- | --- | --- |
| `americanas` | 2021 | **-0,24** | -6,8 | 9,4 | sim | não |
| `metalurgica_duque` | 2010 | **-1,07** | 5,5 | **11,4** | sim | não |
| `metalurgica_duque` | 2011 | -1,87 | 28,0 | **11,9** | sim | não |
| `metalurgica_duque` | 2012 | -3,07 | -17,0 | **23,2** | sim | não |
| `mundial_2017` | 2012 | -2,48 | -0,4 | **28,7** | sim | sim |
| `mundial_2017` | 2013 | -2,49 | -12,9 | **38,3** | sim | sim |
| `mundial_2017` | 2014 | -3,04 | -3,4 | **30,0** | sim | sim |
| `mundial_2017` | 2015 | -2,81 | -0,2 | **33,0** | sim | sim |
| `hercules` | 2014 | n.c. (DEPI) | n.c. | -3,6 | não | sim |
| `tecnosolo` | 2013 | n.c. (DEPI) | **157,2** | -7,5 | sim | não |
| `tecnosolo` | 2014 | n.c. (DEPI) | **363,9** | -9,2 | sim | não |
| `inepar_equipamentos` | 2013 | -3,84 | 1,2 | 5,3 | não | não |
| `ceb` | 2011 | n.c. (DEPI) | 0,3 | 9,3 | não | não |
| `ceb` | 2012 | n.c. (DEPI) | -5,8 | 9,3 | não | não |
| `fibam` | 2016 | n.c. (DEPI) | **30,8** | 5,8 | sim | sim |
| `fibam` | 2017 | n.c. (DEPI) | 26,2 | **16,4** | sim | sim |
| `metalgrafica_iguacu` | 2010 | n.c. (DEPI) | -8,7 | **12,0** | sim | não |
| `metalgrafica_iguacu` | 2011 | n.c. (DEPI) | -25,3 | **23,5** | sim | não |
| `cafe_soluvel_brasilia` | 2011 | n.c. (DEPI) | -46,1 | -1,6 | não | sim |
| `comercial_quintella` | 2012 | -29,47 | -136,6 | -8,4 | não | sim |
| `comercial_quintella` | 2013 | -36,81 | 0,0 | -8,0 | não | sim |
| `cobrasma` | 2014 | n.c. (DEPI) | **2.725,3** | 5,8 | sim | sim |
| `petrobras_2014` | 2010 | -1,94 | -11,6 | -6,8 | não | não |
| `petrobras_2014` | 2011 | -2,46 | 1,9 | -6,9 | não | não |
| `petrobras_2014` | 2012 | -2,59 | -5,7 | -2,2 | não | não |

## Alarmes por acerto e regra boba (2017 a 2023)

Emenda 10: (empresas em alerta − casos acertados) ÷ casos acertados, com empresas distintas que tiveram pelo menos um alerta no período de teste. As 13 empresas dos casos em observação ficam fora. Casos acertados: os do estudo principal, em qualquer exercício do período afetado.

| Grupo | Regra | Empresas avaliadas | Empresas em alerta | Casos acertados | Alarmes por acerto |
| --- | --- | --- | --- | --- | --- |
| Não financeiras | Sinais | 758 | 624 | 7 | 88,1 |
| Não financeiras | Regra boba | 775 | 109 | 6 | 17,2 |
| Financeiras | Sinais | 36 | 11 | 0 | não calculável |
| Financeiras | Regra boba | 46 | 13 | 0 | não calculável |

## Previsões do pré-registro (seção 4.2)

**Americanas.** Previsão: o M-score dispara em pelo menos um ano antes de 2023, puxado por TATA e AQI e não pelo GMI; DPO e juro implícito não disparam. Resultado no exercício de 2021: M = -0,24 (alerta); DPO sem alerta; juro implícito sem alerta. Componentes e contribuições (coeficiente × índice; M = -4,84 + soma):

| Componente | Índice | Contribuição |
| --- | --- | --- |
| DSRI | 1,70 | 1,57 |
| GMI | 0,95 | 0,50 |
| AQI | 1,21 | 0,49 |
| SGI | 2,24 | 2,00 |
| DEPI | 3,40 | 0,39 |
| SGAI | 1,01 | -0,17 |
| TATA | 0,03 | 0,14 |
| LVGI | 0,98 | -0,32 |

**IRB.** Previsão: o sinal não dispara antes da data pública. A DFP de 2019 foi entregue em 18/02/2020, depois de 10/02/2020; a última antes da data é a de 2018. Peso não recorrente em 2018: 0,053 (limite do decil superior do ano nas financeiras: 1,024); sem alerta. Por isso o IRB não pode ser acertado (emenda 3).

## Análises secundárias (rotuladas; fora da conta principal)

- **Emenda 1, Americanas:** alerta em algum exercício até 2021 com DFP entregue antes de 11/01/2023? sim. Exercícios em alerta: 2010, 2011, 2012, 2013, 2014, 2015, 2016, 2017, 2019, 2020, 2021. Regra boba: sim.
- **Emenda 3, alerta na última DFP publicada antes da data pública** (mede alerta antecipado, não acerto): 10 de 16 casos com DFP na amostra antes da data; regra boba, 6. Casos sem DFP na amostra antes da data: 4.

| Caso | Data pública | Última DFP antes da data | Em alerta | Regra boba |
| --- | --- | --- | --- | --- |
| Americanas S.A. (`americanas`) | 11/01/2023 | 2021 | sim | não |
| IRB-Brasil Resseguros S.A. (`irb`) | 10/02/2020 | 2018 | não | não |
| Via Varejo S.A. (hoje Grupo Casas Bahia S.A.) (`via_varejo`) | 13/11/2019 | 2018 | não | não |
| Metalúrgica Duque S.A. (`metalurgica_duque`) | 06/08/2014 | 2012 | sim | não |
| Mundial S.A. - Produtos de Consumo (`mundial_2017`) | 06/03/2017 | 2015 | sim | sim |
| Hércules S.A. - Fábrica de Talheres (`hercules`) | 06/03/2017 | 2014 | não | sim |
| Tecnosolo Engenharia S.A. (`tecnosolo`) | 12/05/2015 | 2014 | sim | não |
| Inepar Equipamentos e Montagens S.A. (`inepar_equipamentos`) | 19/09/2014 | 2013 | não | não |
| Companhia Energética de Brasília - CEB (`ceb`) | 29/09/2017 | 2016 | sim | não |
| Fibam Companhia Industrial (`fibam`) | 08/11/2018 | 2017 | sim | sim |
| Metalgráfica Iguaçu S.A. (`metalgrafica_iguacu`) | 20/12/2012 | 2011 | sim | não |
| Construtora Sultepa S.A. (`sultepa_2013`) | 02/03/2015 | 2011 | sim | não |
| Café Solúvel Brasília S.A. (`cafe_soluvel_brasilia`) | 15/09/2012 | 2011 | não | sim |
| Comercial Quintella Comércio e Exportação S.A. (`comercial_quintella`) | 13/07/2015 | 2014 | sim | sim |
| Cobrasma S.A. (`cobrasma`) | 13/07/2015 | 2014 | sim | sim |
| Petróleo Brasileiro S.A. - Petrobras (`petrobras_2014`) | 10/10/2014 | 2013 | não | não |

- **Emenda 9, partes 2a e 2b:** mesma regra de acerto, com a primeira data pública documentada. Parte 2a: 2 de 4 casos acertados (3 com exercício na amostra antes da data); regra boba, 0. Parte 2b, teto otimista: 7 de 13 (11 com exercício na amostra antes da data); regra boba, 5.

| Caso | Parte | Período afetado nos dados | Data pública | Exercícios avaliados | Exercícios em alerta | Fora da conta | Acertado | Regra boba |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Forjas Taurus S.A. (hoje Taurus Armas S.A.) (`taurus`) | 2a | 2012 | 14/08/2013 | 2012 | 2012 | — | sim | não |
| OGX Petróleo e Gás Participações S.A. (depois Dommo Energia S.A.) (`ogx`) | 2a | 2012 | 01/07/2013 | — | — | 2012: sem receita | não | não |
| OSX Brasil S.A. (`osx`) | 2a | 2012 | 01/07/2013 | 2012 | 2012 | — | sim | não |
| Oi S.A. (`oi_2014`) | 2a | 2014 | 30/06/2016 | 2014 | — | — | não | não |
| Mundial S.A. - Produtos de Consumo (`mundial_2016`) | 2b | 2010, 2011 | 13/05/2016 | 2010, 2011 | 2010, 2011 | — | sim | não |
| Teka Tecelagem Kuehnrich S.A. (`teka`) | 2b | 2012, 2013, 2014 | 20/03/2018 | 2012, 2013, 2014 | 2012, 2013, 2014 | — | sim | sim |
| IGB Eletrônica S.A. (`igb`) | 2b | 2011, 2012 | 30/01/2018 | 2012 | — | 2011: sem receita | não | sim |
| Cia Industrial Schlosser S.A. (`schlosser`) | 2b | 2012, 2013 | 12/12/2017 | 2012, 2013 | 2012 | — | sim | sim |
| Brasil Brokers Participações S.A. (hoje Nexpe Participações S.A.) (`brasil_brokers`) | 2b | 2018 | 16/03/2021 | 2018 | — | — | não | não |
| Inepar S.A. Indústria e Construções (`inepar_2013`) | 2b | 2013 | 27/03/2018 | 2013 | 2013 | — | sim | sim |
| Companhia Docas de Imbituba (`docas_imbituba`) | 2b | 2014 | 18/12/2018 | 2014 | 2014 | — | sim | não |
| Petróleo Brasileiro S.A. - Petrobras (`petrobras_2010`) | 2b | 2010 | 03/11/2020 | 2010 | — | — | não | não |
| Recrusul S.A. (`recrusul`) | 2b | 2011, 2012, 2013, 2014, 2015 | 29/09/2020 | 2011, 2012, 2013 | 2011, 2012, 2013 | 2014: sem versão da época; 2015: sem versão da época | sim | sim |
| Springer S.A. (`springer`) | 2b | 2014, 2015, 2016 | 07/07/2020 | 2014, 2015, 2016 | 2014, 2015, 2016 | — | sim | não |
| BRAZAL - Brasil Alimentos S.A. (`brazal`) | 2b | 2012, 2013 | 02/07/2019 | — | — | 2012: sem versão da época; 2013: sem versão da época | não | não |
| Marina de Iracema Park S.A. (`marina_iracema`) | 2b | 2010, 2011, 2012 | 04/11/2014 | 2010, 2012 | — | 2011: sem versão da época | não | não |
| Bahema S.A. (hoje Bioma Educação S.A.) (`bahema`) | 2b | 2011, 2012, 2013, 2014, 2015 | 24/09/2019 | — | — | 2011: sem receita; 2012: sem receita; 2013: sem receita; 2014: sem receita; 2015: sem receita | não | não |

## Casos em observação (emenda 8)

Fora das métricas de acerto e de alarme. A tabela mostra se houve alerta em exercício com DFP entregue antes da data do caso: a abertura do processo, para a Oi, que ainda não tem decisão; o julgamento, para as companhias do grupo de fronteira.

| Caso | Código CVM | Data | Período | Exercícios com DFP antes da data | Na amostra | Sem receita | Em alerta |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Oi S.A. | 11312 | 17/05/2021 | 2015–2016 | 2015, 2016 | 2015, 2016 | — | 2015 |
| Deluxe Motors S.A. | 23191 | 11/12/2017 | — | — | — | — | — |
| Intellectual Services S.A. - Gestão de Ativos do Conhecimento | 23043 | 11/12/2017 | — | 2012 | — | 2012 | — |
| Ativos Brasileiros S.A. | 22918 | 13/03/2018 | — | 2012 | — | 2012 | — |
| Intermultimodal S.A. Operadora de Plataformas Internacionais de Logística Multimodal | 23086 | 19/06/2018 | — | 2012 | — | 2012 | — |
| Loucos por Futebol S.A. | 23027 | 19/06/2018 | — | 2012 | — | 2012 | — |
| Companhia Ferrífera Brasileira S.A. | 23124 | 19/06/2018 | — | 2012 | — | 2012 | — |
| EOX Energia Eólica S.A. | 23078 | 19/06/2018 | — | 2012 | — | — | — |
| Drogarias Americanas S.A. | 22837 | 19/02/2019 | — | 2012 | — | 2012 | — |
| Atletas Brasileiros S.A. | 22934 | 30/07/2019 | — | 2012, 2013, 2016 | 2013 | 2012, 2016 | — |
| Tecno Waste S.A. (Tekno Waste S.A. na decisão) | 23051 | 30/07/2019 | — | 2012 | — | 2012 | — |
| Ekoparking S.A. | 22896 | 30/07/2019 | — | 2012 | — | 2012 | — |
| Companhia Aurífera Brasileira S.A. | 22870 | 30/07/2019 | — | 2012, 2013, 2014, 2015 | — | 2012, 2013, 2014, 2015 | — |

## Não calculável, por sinal e motivo

Empresa-anos da amostra de cada grupo, de 2010 a 2023. No M-score, uma empresa-ano entra uma vez em cada componente que faltou. Em 20 empresa-anos de não financeiras, a DFP da época não traz nenhuma conta no comparativo (PENÚLTIMO): tudo o que depende de t−1 fica não calculável, e o motivo mostra a primeira conta procurada.

| Sinal | Empresa-anos | Calculáveis | Não calculáveis |
| --- | --- | --- | --- |
| M-score (M) | 6.938 | 5.390 | 1.548 |
| DSRI | 6.938 | 6.524 | 414 |
| GMI | 6.938 | 6.712 | 226 |
| AQI | 6.938 | 6.600 | 338 |
| SGI | 6.938 | 6.739 | 199 |
| DEPI | 6.938 | 5.617 | 1.321 |
| SGAI | 6.938 | 6.638 | 300 |
| TATA | 6.938 | 6.920 | 18 |
| LVGI | 6.938 | 6.825 | 113 |
| Variação do DPO | 6.938 | 6.341 | 597 |
| Juro implícito | 6.938 | 6.214 | 724 |
| Lucro sem caixa (só na ficha) | 6.938 | 6.902 | 36 |
| Peso não recorrente (financeiras) | 517 | 300 | 217 |
| Regra boba, não financeiras | 6.938 | 6.935 | 3 |
| Regra boba, financeiras | 517 | 517 | 0 |

| Sinal | Motivo | Empresa-anos |
| --- | --- | --- |
| M-score (M) | componente não calculável: DEPI | 1.306 |
| M-score (M) | componente não calculável: DSRI | 399 |
| M-score (M) | componente não calculável: AQI | 323 |
| M-score (M) | componente não calculável: SGAI | 285 |
| M-score (M) | componente não calculável: GMI | 211 |
| M-score (M) | componente não calculável: SGI | 184 |
| M-score (M) | componente não calculável: LVGI | 98 |
| M-score (M) | plano de contas de banco | 11 |
| M-score (M) | plano de contas não reconhecido | 4 |
| M-score (M) | componente não calculável: TATA | 3 |
| DSRI | denominador zero: DSRI, índice de t−1 igual a zero | 202 |
| DSRI | denominador zero: DSRI, receita de t−1 | 153 |
| DSRI | conta ausente: contas a receber (1.01.03) | 20 |
| DSRI | receita negativa no denominador: DSRI, receita de t | 14 |
| DSRI | plano de contas de banco | 11 |
| DSRI | receita negativa no denominador: DSRI, receita de t−1 | 10 |
| DSRI | plano de contas não reconhecido | 4 |
| GMI | denominador zero: GMI, receita de t−1 | 153 |
| GMI | conta ausente: resultado bruto (3.03) | 20 |
| GMI | receita negativa no denominador: GMI, receita de t | 14 |
| GMI | denominador zero: GMI, margem bruta de t | 14 |
| GMI | plano de contas de banco | 11 |
| GMI | receita negativa no denominador: GMI, receita de t−1 | 10 |
| GMI | plano de contas não reconhecido | 4 |
| AQI | denominador zero: AQI, índice de t−1 igual a zero | 246 |
| AQI | denominador zero: AQI, ativo total de t−1 | 54 |
| AQI | conta ausente: ativo total (conta 1) | 20 |
| AQI | plano de contas de banco | 11 |
| AQI | plano de contas não reconhecido | 4 |
| AQI | denominador zero: AQI, ativo total de t | 3 |
| SGI | denominador zero: SGI, receita de t−1 | 153 |
| SGI | conta ausente: receita líquida (3.01) | 20 |
| SGI | receita negativa no denominador: SGI, receita de t−1 | 11 |
| SGI | plano de contas de banco | 11 |
| SGI | plano de contas não reconhecido | 4 |
| DEPI | conta ausente: depreciação, linhas da DFC na seção 6.01.01 | 1.135 |
| DEPI | denominador zero: DEPI, depreciação + imobilizado de t−1 | 117 |
| DEPI | denominador zero: DEPI, taxa de depreciação de t | 46 |
| DEPI | plano de contas de banco | 11 |
| DEPI | denominador zero: DEPI, depreciação + imobilizado de t | 8 |
| DEPI | plano de contas não reconhecido | 4 |
| SGAI | denominador zero: SGAI, receita de t−1 | 153 |
| SGAI | denominador zero: SGAI, índice de t−1 igual a zero | 88 |
| SGAI | conta ausente: despesas com vendas (3.04.01) | 20 |
| SGAI | receita negativa no denominador: SGAI, receita de t | 14 |
| SGAI | plano de contas de banco | 11 |
| SGAI | receita negativa no denominador: SGAI, receita de t−1 | 10 |
| SGAI | plano de contas não reconhecido | 4 |
| TATA | plano de contas de banco | 11 |
| TATA | plano de contas não reconhecido | 4 |
| TATA | denominador zero: TATA, ativo total de t | 3 |
| LVGI | denominador zero: LVGI, ativo total de t−1 | 54 |
| LVGI | denominador zero: LVGI, índice de t−1 igual a zero | 21 |
| LVGI | conta ausente: passivo circulante (2.01) | 20 |
| LVGI | plano de contas de banco | 11 |
| LVGI | plano de contas não reconhecido | 4 |
| LVGI | denominador zero: LVGI, ativo total de t | 3 |
| Variação do DPO | denominador zero: DPO, custo das vendas de t | 433 |
| Variação do DPO | denominador zero: DPO, custo das vendas de t−1 | 132 |
| Variação do DPO | conta ausente: fornecedores (2.01.02) | 17 |
| Variação do DPO | plano de contas de banco | 11 |
| Variação do DPO | plano de contas não reconhecido | 4 |
| Juro implícito | denominador zero: dívida média (sem empréstimos em t e t−1) | 689 |
| Juro implícito | conta ausente: empréstimos e financiamentos de curto prazo (2.01.04) | 20 |
| Juro implícito | plano de contas de banco | 11 |
| Juro implícito | plano de contas não reconhecido | 4 |
| Lucro sem caixa (só na ficha) | conta ausente: ativo total (conta 1) | 20 |
| Lucro sem caixa (só na ficha) | plano de contas de banco | 11 |
| Lucro sem caixa (só na ficha) | plano de contas não reconhecido | 4 |
| Lucro sem caixa (só na ficha) | denominador zero: ativo total médio | 1 |
| Peso não recorrente (financeiras) | conta ausente: linha "resultado antes dos tributos" | 215 |
| Peso não recorrente (financeiras) | conta ausente: linha "outras receitas operacionais" | 1 |
| Peso não recorrente (financeiras) | denominador zero: linha "resultado antes dos tributos" | 1 |
| Regra boba, não financeiras | denominador zero: ativo total | 3 |

## Marcas

Depreciação somada com amortização ou exaustão: 5.184 empresa-anos de não financeiras. Exercícios marcados pelo CPC 06 (R2): 498. DFC pelo método direto: 190.

## O que não foi feito nesta fase

- As duas leituras da Americanas (números originais e reapresentados, componente por componente), o teste de robustez com valores neutros (pré-registro, seção 4.1) e a análise secundária da emenda 5 (empresa-anos com versão da época indisponível, pela versão disponível): ficam para a fase seguinte.
- Ficha de alerta (Fase 4) e resumo de uma página (Fase 5).
