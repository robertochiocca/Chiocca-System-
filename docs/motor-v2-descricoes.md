# Motor v2: descrições sem rótulo

Gerado por `python -m chiocca.v2.motor_v2_descricoes` a partir de [`docs/motor_v2_descricoes.json`](motor_v2_descricoes.json), para o pré-registro do motor v2 ([plano](motor-v2-plano.md), seção 2). Só exercícios de 2010 a 2023 e só agregados por ano e grupo: nenhum caso, acerto ou alerta por companhia, e o gabarito não é lido. Nada de 2024 em diante foi lido, além dos metadados do índice da DFP de 2023.

## 1. DEPI pela DVA

Das 6.938 empresa-anos não financeiras, o M-score do v1 existe em 5.390. O DEPI falta em 1.321: 1.135 sem linha de depreciação na DFC; 171 por divisão por zero; 15 pelo plano de contas. Dessas, 35 têm a versão da época vindo do ENET, sem DVA. Nas demais, 1.266 têm a linha de depreciação da DVA em t e t-1, e o DEPI pela DVA fica calculável em 742. Com ele, o M-score passa a existir em mais 627 empresa-anos, de 5.390 para 6.017 (77,7% para 86,7% das não financeiras).

| Exercício | Empresa-anos | M-score no v1 | M-score com o DEPI pela DVA |
| --- | --- | --- | --- |
| 2010 | 434 | 317 (73,0%) | 378 (87,1%) |
| 2011 | 445 | 343 (77,1%) | 390 (87,6%) |
| 2012 | 440 | 334 (75,9%) | 380 (86,4%) |
| 2013 | 464 | 345 (74,4%) | 387 (83,4%) |
| 2014 | 454 | 349 (76,9%) | 384 (84,6%) |
| 2015 | 457 | 358 (78,3%) | 389 (85,1%) |
| 2016 | 451 | 349 (77,4%) | 388 (86,0%) |
| 2017 | 471 | 356 (75,6%) | 404 (85,8%) |
| 2018 | 469 | 355 (75,7%) | 396 (84,4%) |
| 2019 | 465 | 356 (76,6%) | 397 (85,4%) |
| 2020 | 556 | 425 (76,4%) | 480 (86,3%) |
| 2021 | 617 | 481 (78,0%) | 534 (86,5%) |
| 2022 | 605 | 506 (83,6%) | 552 (91,2%) |
| 2023 | 610 | 516 (84,6%) | 558 (91,5%) |

## 2. Subcontas de 3.06.02 (despesa financeira)

Nas não financeiras avaliadas pelo v1, com as subcontas de 3.06.02 diferentes de zero no exercício, reconhecidas pelo nome: variação cambial ("cambi") e arrendamento ("arrendament", "leasing" ou "direito de uso").

| Exercício | Avaliadas | Com alguma subconta | Cambial | Arrendamento | Cambial ou arrendamento |
| --- | --- | --- | --- | --- | --- |
| 2010 | 408 | 59 (14,5%) | 22 (5,4%) | 0 (0,0%) | 22 (5,4%) |
| 2011 | 427 | 75 (17,6%) | 34 (8,0%) | 1 (0,2%) | 35 (8,2%) |
| 2012 | 427 | 77 (18,0%) | 47 (11,0%) | 1 (0,2%) | 48 (11,2%) |
| 2013 | 445 | 83 (18,7%) | 46 (10,3%) | 1 (0,2%) | 47 (10,6%) |
| 2014 | 434 | 77 (17,7%) | 43 (9,9%) | 1 (0,2%) | 44 (10,1%) |
| 2015 | 441 | 82 (18,6%) | 47 (10,7%) | 1 (0,2%) | 47 (10,7%) |
| 2016 | 432 | 83 (19,2%) | 38 (8,8%) | 1 (0,2%) | 38 (8,8%) |
| 2017 | 454 | 86 (18,9%) | 48 (10,6%) | 1 (0,2%) | 48 (10,6%) |
| 2018 | 451 | 83 (18,4%) | 52 (11,5%) | 1 (0,2%) | 52 (11,5%) |
| 2019 | 450 | 87 (19,3%) | 53 (11,8%) | 7 (1,6%) | 56 (12,4%) |
| 2020 | 544 | 114 (21,0%) | 58 (10,7%) | 7 (1,3%) | 60 (11,0%) |
| 2021 | 598 | 118 (19,7%) | 62 (10,4%) | 9 (1,5%) | 64 (10,7%) |
| 2022 | 597 | 129 (21,6%) | 53 (8,9%) | 5 (0,8%) | 54 (9,0%) |
| 2023 | 602 | 126 (20,9%) | 53 (8,8%) | 1 (0,2%) | 53 (8,8%) |

Por origem da versão: dados abertos, 1.226 de 6.399 com alguma subconta e 635 com cambial ou arrendamento; ENET, 53 de 311 com alguma subconta e 33 com cambial ou arrendamento.

**Critério proposto no plano** (a fechar no pré-registro): a mudança 1.1 (a) entra se, em cada exercício de 2019 a 2023, pelo menos 50% das não financeiras avaliadas tiverem uma subconta de variação cambial ou de arrendamento. Resultado desta descrição: **não atende** (2019: não atende; 2020: não atende; 2021: não atende; 2022: não atende; 2023: não atende).

## 3. Quantidade de números por empresa-ano

Números diferentes de zero na coluna do exercício de BPA, BPP, DRE e DFC da versão usada, os quatro demonstrativos que existem nos dados abertos e no ENET. Empresa-anos sem nenhum número na base: 0.

| Conjunto | Empresa-anos | Mínimo | P5 | P25 | Mediana | P75 | P95 | Máximo |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| não financeiras | 6.938 | 23 | 63 | 113 | 135 | 154 | 183 | 258 |
| financeiras | 517 | 39 | 69 | 94 | 114 | 137 | 179 | 202 |
| dados abertos | 7.123 | 23 | 63 | 111 | 134 | 153 | 183 | 258 |
| ENET | 332 | 43 | 92 | 120 | 139 | 157 | 187 | 224 |

Mediana por exercício: 2010: 130; 2011: 131; 2012: 132; 2013: 132; 2014: 132; 2015: 134; 2016: 133; 2017: 133; 2018: 130; 2019: 136; 2020: 137; 2021: 138; 2022: 140; 2023: 139.

## 4. Opções da fração (plano, 1.3)

O desvio de Benford entra numa versão provisória: o desvio médio absoluto do primeiro dígito, dividido pela média do desvio na mesma faixa de quantidade de números (quintis dentro do ano e do grupo). O juro implícito usa a fórmula do v1. A taxa é sobre as empresa-anos com pelo menos um sinal do v2 calculável. (i): o decil superior em cada sinal; (ii): os 10% do ano com o maior percentil entre os sinais calculáveis. As contagens são por empresa-ano (linha da base); o estudo 1 conta companhias distintas por exercício, e a diferença vem de companhias com duas DFP no mesmo exercício: 6 linhas a mais nas não financeiras e 0 nas financeiras.

### Não financeiras

| Exercício | Avaliáveis pelo v2 | Taxa do v1 | Opção (i): união | Opção (ii) |
| --- | --- | --- | --- | --- |
| 2010 | 434 | 49,5% | 32,7% | 10,1% |
| 2011 | 445 | 45,0% | 30,8% | 10,1% |
| 2012 | 440 | 48,7% | 29,5% | 10,0% |
| 2013 | 464 | 45,4% | 31,0% | 10,1% |
| 2014 | 454 | 43,8% | 31,9% | 10,1% |
| 2015 | 457 | 50,6% | 31,7% | 10,1% |
| 2016 | 451 | 42,4% | 32,8% | 10,2% |
| 2017 | 471 | 43,2% | 30,1% | 10,2% |
| 2018 | 469 | 51,9% | 31,3% | 10,0% |
| 2019 | 465 | 52,9% | 30,5% | 10,1% |
| 2020 | 556 | 59,0% | 32,4% | 10,1% |
| 2021 | 617 | 61,7% | 30,6% | 10,0% |
| 2022 | 605 | 53,8% | 32,1% | 10,1% |
| 2023 | 610 | 44,5% | 32,8% | 10,0% |
| Total | 6.938 | 49,9% | 31,5% | 10,1% |

Opção (i), de 2010 a 2023: 2.185 de 6.938 empresa-anos em alerta (31,5%). Por número de sinais no topo: 1: 1.821; 2: 337; 3: 27; 4: 0. Pares de sinais no topo ao mesmo tempo: M-score (DEPI pela DVA quando falta na DFC) e salto do DPO, 88; M-score (DEPI pela DVA quando falta na DFC) e juro implícito (fórmula do v1), 85; M-score (DEPI pela DVA quando falta na DFC) e desvio de Benford ajustado (provisório), 59; salto do DPO e juro implícito (fórmula do v1), 77; salto do DPO e desvio de Benford ajustado (provisório), 54; juro implícito (fórmula do v1) e desvio de Benford ajustado (provisório), 55. Alertas de cada sinal: M-score (DEPI pela DVA quando falta na DFC), 606 de 6.017; salto do DPO, 641 de 6.341; juro implícito (fórmula do v1), 629 de 6.214; desvio de Benford ajustado (provisório), 700 de 6.938.

Opção (ii): 700 de 6.938 empresa-anos em alerta (10,1%). Sinal que define o maior percentil entre as alertadas (com empate, conta para cada um): M-score (DEPI pela DVA quando falta na DFC), 160; salto do DPO, 174; juro implícito (fórmula do v1), 168; desvio de Benford ajustado (provisório), 198; alertas com empate no maior percentil: 0.

Empresa-anos que só o v2 consegue avaliar (nenhum sinal do v1 calculável): 228.

### Financeiras

| Exercício | Avaliáveis pelo v2 | Taxa do v1 | Opção (i): união | Opção (ii) |
| --- | --- | --- | --- | --- |
| 2010 | 33 | 15,4% | 18,2% | 12,1% |
| 2011 | 40 | 10,5% | 15,0% | 10,0% |
| 2012 | 42 | 14,3% | 19,0% | 11,9% |
| 2013 | 42 | 13,6% | 16,7% | 11,9% |
| 2014 | 42 | 13,6% | 19,0% | 11,9% |
| 2015 | 41 | 13,6% | 17,1% | 12,2% |
| 2016 | 38 | 10,5% | 15,8% | 13,2% |
| 2017 | 38 | 10,0% | 15,8% | 10,5% |
| 2018 | 37 | 10,0% | 16,2% | 10,8% |
| 2019 | 33 | 11,1% | 18,2% | 12,1% |
| 2020 | 33 | 12,0% | 21,2% | 12,1% |
| 2021 | 34 | 11,5% | 20,6% | 11,8% |
| 2022 | 34 | 10,7% | 20,6% | 11,8% |
| 2023 | 30 | 12,0% | 16,7% | 10,0% |
| Total | 517 | 12,0% | 17,8% | 11,6% |

Opção (i), de 2010 a 2023: 92 de 517 empresa-anos em alerta (17,8%). Por número de sinais no topo: 1: 89; 2: 3. Pares de sinais no topo ao mesmo tempo: peso de ganhos não recorrentes e desvio de Benford ajustado (provisório), 3. Alertas de cada sinal: peso de ganhos não recorrentes, 36 de 300; desvio de Benford ajustado (provisório), 59 de 517.

Opção (ii): 60 de 517 empresa-anos em alerta (11,6%). Sinal que define o maior percentil entre as alertadas (com empate, conta para cada um): peso de ganhos não recorrentes, 25; desvio de Benford ajustado (provisório), 35; alertas com empate no maior percentil: 0.

Empresa-anos que só o v2 consegue avaliar (nenhum sinal do v1 calculável): 217.

## 5. Datas de entrega da DFP de 2023 (só metadados)

Primeira entrega (o menor DT_RECEB do índice) da DFP de 2023 com data de referência 31/12/2023, por companhia: 721 companhias, 690 até o corte de 30/04/2024 e 31 depois. Das entregues até o corte, 690 (100,0%) foram depois de 25/01/2024 e 681 (98,7%) depois de 31/01/2024, o análogo de 2024 das datas da meta (25/01/2027 e 31/01/2027).

Estimativa para o rótulo prospectivo: das 557 não financeiras avaliadas em 2022 (referência em 31/12/2022) com a DFP de 2023 entregue até o corte, 550 (98,7%) tiveram a primeira entrega depois de 31/01/2024, e 557 (100,0%) depois de 25/01/2024. Com o mesmo padrão em 2027 e o lacre em 31/01/2027, essa seria a fração prospectiva das empresa-anos de 2025; as datas da semana não coincidem entre os anos.

| Semana | Primeiras entregas | Acumulado até o corte |
| --- | --- | --- |
| 01/01/2024 a 07/01/2024 | 0 | 0,0% |
| 08/01/2024 a 14/01/2024 | 0 | 0,0% |
| 15/01/2024 a 21/01/2024 | 0 | 0,0% |
| 22/01/2024 a 28/01/2024 | 1 | 0,1% |
| 29/01/2024 a 04/02/2024 | 13 | 2,0% |
| 05/02/2024 a 11/02/2024 | 46 | 8,7% |
| 12/02/2024 a 18/02/2024 | 1 | 8,8% |
| 19/02/2024 a 25/02/2024 | 38 | 14,3% |
| 26/02/2024 a 03/03/2024 | 61 | 23,2% |
| 04/03/2024 a 10/03/2024 | 62 | 32,2% |
| 11/03/2024 a 17/03/2024 | 109 | 48,0% |
| 18/03/2024 a 24/03/2024 | 108 | 63,6% |
| 25/03/2024 a 31/03/2024 | 197 | 92,2% |
| 01/04/2024 a 07/04/2024 | 36 | 97,4% |
| 08/04/2024 a 14/04/2024 | 8 | 98,6% |
| 15/04/2024 a 21/04/2024 | 5 | 99,3% |
| 22/04/2024 a 28/04/2024 | 4 | 99,9% |
| 29/04/2024 a 30/04/2024 | 1 | 100,0% |
