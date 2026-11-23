# Motor v2 congelado: dentro da amostra de desenvolvimento

> **Dentro da amostra de desenvolvimento, não é teste.** O v2 foi congelado em 23/11/2026 ([registro de SHA-256](motor_v2_codigo_congelado.json)), e só depois disso estes números foram calculados, com o código congelado, nos exercícios de 2010 a 2023, os mesmos em que o v2 foi desenvolvido. Nada aqui é evidência de que o v2 funciona: o teste dele é o braço do v2 na avaliação secundária do estudo 2 (emenda 5) e, depois, o teste prospectivo com os exercícios de 2026. Só números agregados; nenhuma empresa é citada.

## 1. Taxa de alerta

O v2 com as três mudanças, cada empresa na data de corte do seu exercício. Alerta: escore no quantil de 90% do exercício e do grupo; avaliada: pelo menos um sinal calculável.

| Exercício | Não financeiras avaliadas | Em alerta | Taxa | Financeiras avaliadas | Em alerta | Taxa |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 2010 | 434 | 44 | 10,1% | 33 | 4 | 12,1% |
| 2011 | 445 | 45 | 10,1% | 40 | 4 | 10,0% |
| 2012 | 440 | 44 | 10,0% | 42 | 5 | 11,9% |
| 2013 | 464 | 47 | 10,1% | 42 | 5 | 11,9% |
| 2014 | 454 | 46 | 10,1% | 42 | 5 | 11,9% |
| 2015 | 457 | 46 | 10,1% | 41 | 5 | 12,2% |
| 2016 | 451 | 46 | 10,2% | 38 | 5 | 13,2% |
| 2017 | 471 | 48 | 10,2% | 38 | 4 | 10,5% |
| 2018 | 469 | 47 | 10,0% | 37 | 4 | 10,8% |
| 2019 | 465 | 47 | 10,1% | 33 | 4 | 12,1% |
| 2020 | 556 | 56 | 10,1% | 33 | 4 | 12,1% |
| 2021 | 617 | 62 | 10,0% | 34 | 4 | 11,8% |
| 2022 | 605 | 61 | 10,1% | 34 | 4 | 11,8% |
| 2023 | 610 | 61 | 10,0% | 30 | 3 | 10,0% |
| Total | 6.938 | 700 | 10,1% | 517 | 60 | 11,6% |

A taxa anual fica entre 10,0% e 10,2% nas não financeiras e entre 10,0% e 13,2% nas financeiras. As avaliadas e os alertas, por grupo e por número de sinais calculáveis, são os mesmos das [descrições sem rótulo](motor-v2-descricoes.md) feitas antes do pré-registro: sim, nos dois grupos.

## 2. Cobertura dos sinais

| Grupo | Sinal | Calculável no v1 | Calculável no v2 |
| --- | --- | ---: | ---: |
| Não financeiras | M-score | 5.390 | 6.017 |
| Não financeiras | salto do DPO | 6.341 | 6.341 |
| Não financeiras | juro implícito | 6.214 | 6.214 |
| Não financeiras | desvio de Benford padronizado | não existe no v1 | 6.938 |
| Financeiras | peso de ganhos não recorrentes | 300 | 300 |
| Financeiras | desvio de Benford padronizado | não existe no v1 | 517 |

O DEPI pela DVA entra em 735 empresa-anos. As descrições sem rótulo contaram 742: as 7 a mais são não financeiras fora do plano de contas não financeiro (bancos e outros), em que o v1 não calcula o M-score e o v2, como o v1, não aplica a DVA; o M-score cobre as mesmas 6.017 empresa-anos nos dois cálculos. O v2 avalia 228 não financeiras e 217 financeiras que o v1 não avaliava (por exemplo, só pelo Benford); das 6.710 não financeiras avaliadas pelo v1, o v2 avalia todas.

## 3. Taxa de alerta por número de sinais calculáveis

A característica conhecida da seção 4 do pré-registro do v2, sem correção:

| Grupo | Sinais calculáveis | Avaliadas | Em alerta | Taxa |
| --- | ---: | ---: | ---: | ---: |
| Não financeiras | 1 | 215 | 15 | 7,0% |
| Não financeiras | 2 | 426 | 72 | 16,9% |
| Não financeiras | 3 | 745 | 108 | 14,5% |
| Não financeiras | 4 | 5.552 | 505 | 9,1% |
| Financeiras | 1 | 217 | 17 | 7,8% |
| Financeiras | 2 | 300 | 43 | 14,3% |

## 4. Acertos nos casos do estudo 1 (dentro da amostra, não é teste)

A regra da seção 5 do pré-registro do estudo 1 e os alarmes por acerto das emendas 10 e 11, com o alerta do v2 no lugar do do v1, pelas mesmas funções do estudo 1. O v2 foi desenvolvido sem o gabarito, mas nos mesmos exercícios e com os mesmos casos à vista: os acertos abaixo não são teste.

| | v2 congelado | v1 (estudo 1) | Regra boba (estudo 1) |
| --- | ---: | ---: | ---: |
| Casos acertáveis | 13 | 13 | 13 |
| Casos acertados, de 2010 a 2023 | 3 | 7 | 6 |
| Casos acertados com alerta de 2017 a 2023 | 0 | 2 | 1 |
| Não financeiras distintas em alerta, de 2017 a 2023 | 231 | 624 | 109 |
| Alarmes por acerto, de 2017 a 2023 (não financeiras) | sem acerto | 311 | 108 |
| Não financeiras distintas em alerta, de 2010 a 2023 | 366 | 765 | 167 |
| Alarmes por acerto, de 2010 a 2023 (não financeiras) | 121 | 108 | 27 |
