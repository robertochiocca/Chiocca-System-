# Análises depois do estudo 1

**Análise descritiva depois do resultado, não pré-registrada.** Autorizada por Roberto Chiocca em 07/11/2026. Não altera o estudo 1 (branch `estudo-1-final`): lê `docs/resultados_numeros.json` e é gerada por `python -m chiocca.v2.analises_pos_estudo_1`. Não edite à mão: um teste compara este arquivo com a saída do script.

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

- Independência entre os anos de um mesmo caso: a chance de alerta num ano não depende do ano anterior. Se os alertas se repetem na mesma empresa de um ano para outro (isso não foi medido aqui), a chance real de pelo menos um alerta em vários anos é menor que a calculada, e a probabilidade acima superestima o acaso.
- Independência entre os casos.
- Cada caso tem a taxa de alerta média do seu grupo no ano. As empresas do gabarito podem ser diferentes da média (por exemplo, menores ou mais endividadas), e a taxa delas, ao acaso, pode ser maior ou menor que a média; a direção do efeito não é conhecida.
- As taxas são as do próprio estudo 1, que incluem as empresas do gabarito.
- Esta conta não substitui as métricas pré-registradas (acerto e alarmes por acerto), e não foi decidida antes de ver o resultado.
