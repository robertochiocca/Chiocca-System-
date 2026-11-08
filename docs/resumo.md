# Resumo · Chiocca System

Gerado por `python -m chiocca.relatorio_resultados` a partir de `docs/resultados_numeros.json`. Detalhes, tabelas e fontes em [`docs/resultados.md`](resultados.md). Alerta estatístico baseado em demonstrações públicas. Não é acusação, não é recomendação de investimento.

**Pergunta.**
Com dados públicos disponíveis na época, os sinais do catálogo teriam alertado para os casos do gabarito antes de eles virem a público? Quantos alarmes falsos isso custaria?

**Desenho.**

- Pré-registro assinado em 04/11/2026, com 11 emendas; só a última foi escrita depois dos resultados, e ela muda apenas a métrica de alarmes.
- Todas as companhias abertas com DFP na CVM, de 2010 a 2023, inclusive as canceladas: 6.938 empresa-anos de não financeiras com receita e 517 de financeiras, de 987 empresas.
- "Como era na época": cada empresa-ano usa a versão da DFP pública na data de corte (último dia do quarto mês depois do exercício); versões reentregues depois vêm do ENET da CVM.
- Não financeiras: M-score (alerta se M > -1,78), salto do DPO (decil superior do ano) e juro implícito (acima do CDI médio + 10 p.p.). Financeiras: peso de ganhos não recorrentes (decil superior do ano).
- Gabarito: 42 casos, dos quais 13 acertáveis no estudo principal. Período de teste, 2017 a 2023, aberto uma vez, em 07/11/2026.

**Resultado.**

- Acerto: 7 de 13 casos acertáveis (7 de 42 no gabarito inteiro).
- Alarmes por acerto nas não financeiras (emenda 11): 311,0 no período de teste, com 2 acertos por alerta dentro dele, e 108,3 no período inteiro. Taxa de alerta: 49,9% das empresa-anos não financeiras avaliadas (48,3% incluindo as financeiras).
- Financeiras: nenhum caso acertável. O IRB não teve alerta na DFP de 2018 (0,053, contra limite de 1,024).

**Regra boba lado a lado** (decil mais endividado de cada ano e grupo; sem vencedor declarado, emenda 11):

| Não financeiras | Sinais | Regra boba |
| --- | --- | --- |
| Casos acertados (de 13) | 7 | 6 |
| Acertos por alerta em 2017–2023 | 2 | 1 |
| Alarmes por acerto, período de teste | 311,0 | 108,0 |
| Alarmes por acerto, período inteiro | 108,3 | 26,8 |
| Taxa de alerta das empresa-anos avaliadas, 2010–2023 | 49,9% | 10,1% |

**Depois do resultado (análise descritiva, não pré-registrada).** Com anos independentes, o acaso daria 8,56 acertos em média, e 7 ou mais com chance de 90,0%. Como os alertas se repetem na mesma empresa (73,8% das empresa-anos em alerta das não financeiras também estavam em alerta no ano anterior, contra taxa de alerta de 49,9% das empresa-anos não financeiras avaliadas), esse número é um teto. Com a chance de cada caso medida nas empresas do mesmo grupo, sem supor anos independentes, o acaso daria 7,37 acertos, e 7 ou mais com chance de 69,3%. Detalhes em [`docs/analises-pos-estudo-1.md`](analises-pos-estudo-1.md).

**O que deu errado e por quê.**

- O juro implícito sozinho responde por 59,8% das empresa-anos em alerta (2.001 de 3.345). A despesa financeira (3.06.02) inclui, por definição, variação cambial, juros de arrendamento e outros itens que não são juros dos empréstimos (2.01.04 e 2.02.01); essa decomposição não foi medida. Sem ele, a taxa de alerta das empresa-anos não financeiras avaliadas seria 20,0%, e não 49,9%.
- O M-score ficou sem valor em 1.548 de 6.938 empresa-anos; em 1.306, faltou o DEPI. Em 7 dos 13 casos acertáveis o M não existiu porque a DFC não tem linha de depreciação (2 deles com DFC pelo método direto). Com valores neutros, o acerto seria 8 de 13.
- Só 2 dos 7 acertos têm alerta no período de teste: em 11 dos 13 casos acertáveis, o período afetado termina antes de 2017.
- A emenda 10 punha numerador e acertos em janelas diferentes (88,1 alarmes por acerto); a emenda 11 corrigiu isso depois dos resultados, e as duas versões estão no relatório.

**Previsões do pré-registro (seção 4.2).**

- Acertaram: o M-score da Americanas disparou antes de 2023, com M = -0,24 em 2021; o DPO, com -6,8 dias, e o juro implícito, com 9,4 p.p. acima do CDI, não dispararam; o GMI ficou em 0,95, abaixo de 1; o IRB não teve alerta antes da data pública.
- Erraram: o M da Americanas não foi puxado por TATA e AQI, com contribuições de 0,14 e 0,49, e sim por SGI e DSRI, com 2,00 e 1,57, as duas maiores contribuições.

**Americanas: parte do alerta de 2021 vem da fusão.**

Em 2021 a B2W (código CVM 20990) recebeu as operações da Lojas Americanas por cisão parcial (assembleia de 10/06/2021). O comparativo de 2020 é só da B2W: a receita foi de R$ 10.124 milhões para R$ 22.696 milhões, e o SGI de 2,24 vem dessa troca de perímetro. Com a Lojas Americanas consolidada de 2020 como base, o SGI cai para 1,07 (contribuição de 0,95, contra 2,00), e o M continua acima do corte, em -0,96, puxado por DSRI e AQI, com índices de 1,96 e 1,71. Na leitura reapresentada da DFP de 2022, o M também fica acima do corte, em -0,90. Essa explicação foi feita depois do resultado e não é teste.

**Limitações.**

- Poucos casos: 13 acertáveis em 42 no gabarito, nenhum deles financeiro; o teto do estudo principal é 13 de 42.
- O IRB não pode ser acertado com DFP anual (emenda 3); pegá-lo exigiria dados trimestrais (ITR).
- Sinais calibrados nos EUA: o corte de -1,78 vem de Beneish (1999) e não foi recalibrado para o Brasil.
- Despesa financeira (3.06.02) que não separa os juros dos empréstimos: o juro implícito dispara em 40,7% das empresa-anos em que é calculável.
- DFC pelo método direto sem linha de depreciação em 190 empresa-anos, com M não calculável (limitação aceita na emenda 11).
- O caso da Americanas veio a público por dentro, pelo fato relevante da própria companhia de 11/01/2023, e não por um sinal das demonstrações.
- A emenda 11 foi escrita depois de ver os resultados; a versão anterior da métrica continua no relatório.
