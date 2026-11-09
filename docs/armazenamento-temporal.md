# Armazenamento temporal e motor v1 em qualquer data (Fases C1 e C2)

Gerado por `python -m chiocca.v2.invariante` a partir de `docs/invariante_numeros.json`. Não edite à mão: um teste compara este arquivo com a saída do script. Só números agregados; as únicas empresas citadas são as dos casos do gabarito, que são públicos.

## O armazém

- Parquet consultado pelo DuckDB (`chiocca/v2/armazem.py`), montado sem rede de `data/brutos/cvm` (conferido por hash) e do cache do ENET, em `data/armazem/`, fora do git. Exercícios de 2010 a 2023; nenhum exercício lacrado entra.
- Tabelas: `versoes` (12.372 versões de DFP, com a data de entrega), `contas` (7.550.842 linhas, dos dados abertos e de 342 documentos do ENET), `fca` (22.203 versões), `cadastro` (2.679 linhas) e `escalas` (escala original de cada demonstração dos dados abertos). O `manifesto.json` guarda o hash SHA-256 de cada arquivo de origem.
- De documento entregue depois de 31/12/2024, o armazém guarda só metadados: versão, data de entrega e a estrutura, isto é, quais demonstrações existem e o tipo (consolidado ou individual), sem nenhuma conta nem valor (decisão de 09/11/2026: a estrutura conta como metadado). Documentos entregues depois de 31/12/2024 com só a estrutura no armazém, por exercício: 2023: 14 (total: 14). O `como_era` do motor v1 usa essa estrutura da última versão para saber se há consolidado (rota do ENET, emenda 8) e para nomear a DFC do ENET; com data de referência até 31/12/2024, os valores dessa versão nunca são lidos, e um teste garante que nenhuma conta nem valor desses documentos é guardado.
- `FontesArmazem` tem a mesma interface dos arquivos brutos (`chiocca.cvm.Fontes`): o motor v1 roda sobre o armazém sem nenhuma mudança.

## Motor v1 na data

- `ExercicioNaData` (`chiocca/v2/na_data.py`): uma empresa num exercício, como era na data de referência, com a versão usada, só as versões entregues até a data, a origem (dados abertos ou ENET) e o link do documento. A data passa pelo intervalo de 30/04/2011 a 31/12/2024, e o exercício, pelo lacre.
- Corte transversal na data: as mesmas funções do estudo 1 (`como_era`, `grupos`, `sinais_amostra`), com os decis do ano recalculados só com as empresas cuja versão era pública na data.
- Quando a versão usada não é a última, o `como_era` lê a estrutura da última versão, entregue depois da data (comportamento do estudo 1, emenda 8). A linhagem registra: "estrutura lida de documento posterior à data (comportamento do estudo 1, emenda 8)". Na data de corte de cada exercício, isso aconteceu em 531 empresa-anos de 2010 a 2023.
- Camada do produto, ao lado do motor e sem mudar nenhum valor dele: a coluna `produto_nao_calculaveis` lista os sinais que o produto mostra como "não calculável" por balanço não preenchido.

## Fase C2: escala, evidências e busca no ENET

- `escala_original` da versão usada: dos dados abertos, 13.760 versões em MIL, 1.050 versões em UNIDADE. O cache do ENET guarda os valores já em reais e não registra a escala da página; nas versões do ENET, o campo fica vazio, com esse motivo na linhagem.
- Evidências do contrato: cada linha da DFP lida vira uma `Evidencia`, com id estável, documento (versão, data de entrega, origem, endereço e hash), demonstração, coluna, conta, descrição oficial, valor em reais e, com o `Localizador`, o arquivo e a linha de origem.
- Busca no ENET por comando separado (`python -m chiocca.v2.buscar_enet AAAA-MM-DD`): lista as versões que a data precisa e que não estão no armazém, baixa só essas (consolidado, exercícios liberados, entregues até 31/12/2024) e remonta o armazém. Nenhuma consulta baixa nada.

## Universo

As conferências da Fase B ([`docs/conferencias.md`](conferencias.md)) contam as 8.594 empresa-anos com a versão da época; o invariante compara todas as 9.474 empresa-anos com DFP de 2010 a 2023, inclusive as 880 sem versão da época (sem versão até o corte: 685; versão da época só com demonstração individual, sem a rota do ENET: 190; conta repetida com valores diferentes: 5), que também têm de sair iguais ao estudo 1.

## Invariante do estudo 1

Na data de corte de cada exercício, o motor v1 sobre o armazém reproduz `resultados/sinais_empresa_ano.csv` em 9.474 de 9.474 empresa-anos, com comparação exata de 54 colunas (situação, amostra, cada sinal, componente e motivo de "não calculável", cada alerta, avaliada e em alerta).

| Exercício | Empresa-anos no estudo 1 | Empresa-anos no armazém | Iguais em todas as colunas | Colunas com diferença |
| --- | --- | --- | --- | --- |
| 2010 | 663 | 663 | 663 | nenhuma |
| 2011 | 684 | 684 | 684 | nenhuma |
| 2012 | 662 | 662 | 662 | nenhuma |
| 2013 | 652 | 652 | 652 | nenhuma |
| 2014 | 652 | 652 | 652 | nenhuma |
| 2015 | 633 | 633 | 633 | nenhuma |
| 2016 | 626 | 626 | 626 | nenhuma |
| 2017 | 632 | 632 | 632 | nenhuma |
| 2018 | 631 | 631 | 631 | nenhuma |
| 2019 | 671 | 671 | 671 | nenhuma |
| 2020 | 733 | 733 | 733 | nenhuma |
| 2021 | 771 | 771 | 771 | nenhuma |
| 2022 | 731 | 731 | 731 | nenhuma |
| 2023 | 733 | 733 | 733 | nenhuma |

## O mesmo exercício visto em 31/12/2024

Com a data de referência em 31/12/2024, cada exercício usa a versão mais recente entregue até essa data. Contagens contra a data de corte:

| Exercício | Com versão na data de corte | Outra versão conhecida em 31/12/2024 | Pendentes do ENET em 31/12/2024 | Avaliadas nas duas datas | Entram em alerta | Saem do alerta |
| --- | --- | --- | --- | --- | --- | --- |
| 2010 | 594 | 71 | 0 | 421 | 0 | 2 |
| 2011 | 625 | 63 | 0 | 446 | 0 | 2 |
| 2012 | 614 | 41 | 0 | 448 | 1 | 3 |
| 2013 | 616 | 34 | 0 | 467 | 0 | 2 |
| 2014 | 601 | 27 | 0 | 456 | 0 | 4 |
| 2015 | 600 | 32 | 0 | 463 | 0 | 1 |
| 2016 | 586 | 34 | 0 | 451 | 1 | 1 |
| 2017 | 594 | 27 | 0 | 474 | 1 | 2 |
| 2018 | 593 | 35 | 0 | 471 | 2 | 3 |
| 2019 | 567 | 25 | 0 | 468 | 0 | 1 |
| 2020 | 661 | 25 | 0 | 569 | 0 | 0 |
| 2021 | 734 | 28 | 0 | 624 | 1 | 3 |
| 2022 | 702 | 53 | 0 | 625 | 2 | 2 |
| 2023 | 702 | 29 | 0 | 627 | 1 | 0 |

"Pendente do ENET" é a versão da data que não está no armazém; a busca no ENET é um comando separado e nunca acontece dentro de uma consulta (pergunta 9 do plano).

## Casos do gabarito com outra versão em 31/12/2024

**Análise descritiva, não pré-registrada.** O estudo 1 não muda. Empresa-anos do período afetado de casos do gabarito que, em 31/12/2024, tinham outra versão da DFP entregue depois da data de corte; o estado de alerta nas duas datas e os sinais cujo valor mudou.

| Caso | Exercício | Data pública do caso | Versão do corte (entrega) | Versão em 31/12/2024 (entrega) | Em alerta no corte | Em alerta em 31/12/2024 | Sinais com outro valor (ou outra calculabilidade) | Alertas que mudaram (corte → 31/12/2024) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| IGB Eletrônica S.A. (`igb`) | 2011 | 30/01/2018 | 13/04/2012 | 26/11/2013 | não | não | nenhum | nenhum |
| Marina de Iracema Park S.A. (`marina_iracema`) | 2011 | 04/11/2014 | 03/04/2012 | 12/11/2012 | não | não | DSRI, GMI, AQI, SGI, SGAI, TATA, LVGI, dpo, juro, lucro_sem_caixa, alavancagem | dpo: não calculável → sem alerta; juro: não calculável → sem alerta |
| Café Solúvel Brasília S.A. (`cafe_soluvel_brasilia`) | 2011 | 15/09/2012 | 27/04/2012 | 25/10/2012 | não | não | nenhum | nenhum |
| Forjas Taurus S.A. (hoje Taurus Armas S.A.) (`taurus`) | 2012 | 14/08/2013 | 24/04/2013 | 28/03/2014 | sim | sim | DSRI, GMI, AQI, DEPI, SGAI, TATA, LVGI, mscore, dpo, lucro_sem_caixa, alavancagem | nenhum |
| IGB Eletrônica S.A. (`igb`) | 2012 | 30/01/2018 | 24/04/2013 | 27/11/2013 | não | não | nenhum | nenhum |
| BRAZAL - Brasil Alimentos S.A. (`brazal`) | 2012 | 02/07/2019 | 12/04/2013 | 10/05/2013 | não | não | nenhum | nenhum |
| Comercial Quintella Comércio e Exportação S.A. (`comercial_quintella`) | 2012 | 13/07/2015 | 12/04/2013 | 02/09/2016 | não | não | TATA, LVGI, mscore, lucro_sem_caixa, alavancagem | nenhum |
| Comercial Quintella Comércio e Exportação S.A. (`comercial_quintella`) | 2013 | 13/07/2015 | 31/03/2014 | 02/09/2016 | não | não | AQI, SGAI, TATA, LVGI, mscore, lucro_sem_caixa, alavancagem | nenhum |
| IRB-Brasil Resseguros S.A. (`irb`) | 2019 | 10/02/2020 | 18/02/2020 | 18/02/2021 | não | não | peso_nao_recorrente, alavancagem | nenhum |

## Reapresentação pelo comparativo do ano seguinte em 31/12/2024

**Análise descritiva.** O estudo 1 e o motor v1 não mudam. Regra de 09/11/2026 (`docs/contratos.md`, seção 4): quando a DFP de t+1 já é pública na data, cada conta de t na versão usada é comparada com a coluna PENÚLTIMO de t+1 (mesma demonstração, mesmo código, mesmo tipo); diferença acima de R$ 1.000 por conta vai para a investigação como evidência, com o texto "valor diferente no comparativo do ano seguinte (reapresentação ou reclassificação)". Pelo lacre, o exercício de 2023 não tem comparação.

Em 31/12/2024, 5.747 de 8.084 empresa-anos comparáveis (de 2010 a 2022) têm pelo menos uma conta com diferença acima da tolerância.

| Exercício | Empresa-anos comparáveis | Com alguma diferença |
| --- | --- | --- |
| 2010 | 606 | 470 |
| 2011 | 627 | 464 |
| 2012 | 606 | 444 |
| 2013 | 603 | 366 |
| 2014 | 605 | 391 |
| 2015 | 588 | 392 |
| 2016 | 592 | 361 |
| 2017 | 585 | 541 |
| 2018 | 581 | 423 |
| 2019 | 629 | 506 |
| 2020 | 687 | 446 |
| 2021 | 694 | 473 |
| 2022 | 681 | 470 |

**Americanas S.A. (`americanas`), exercício 2021.** A DFP de 2021 tem uma única versão, entregue em 24/02/2022; a reapresentação veio no comparativo da DFP de 2022, entregue em 16/11/2023, e não numa versão nova da DFP de 2021. Por isso a Americanas não está entre as empresa-anos com outra versão em 31/12/2024. Das 280 contas comparáveis, 126 têm diferença acima da tolerância; as 10 maiores, em R$ milhões:

| Demonstração | Conta | Descrição | DFP de 2021 (entregue em 24/02/2022) | Comparativo da DFP de 2022 (entregue em 16/11/2023) | Diferença |
| --- | --- | --- | --- | --- | --- |
| BPP | 2.01 | Passivo Circulante | 13.336,9 | 43.013,1 | 29.676,3 |
| BPP | 2.03 | Patrimônio Líquido Consolidado | 15.911,0 | -12.621,9 | -28.532,9 |
| BPP | 2.03.05 | Lucros/Prejuízos Acumulados | 0,0 | -28.405,0 | -28.405,0 |
| BPP | 2.01.05 | Outras Obrigações | 2.973,3 | 17.246,2 | 14.272,9 |
| BPP | 2.01.05.02 | Outros | 2.961,6 | 17.234,5 | 14.272,9 |
| BPP | 2.01.04 | Empréstimos e Financiamentos | 1.052,9 | 13.719,7 | 12.666,8 |
| BPP | 2.02.01 | Empréstimos e Financiamentos | 11.287,8 | 0,0 | -11.287,8 |
| BPP | 2.01.04.01 | Empréstimos e Financiamentos | 946,2 | 11.571,0 | 10.624,8 |
| BPP | 2.02.01.01 | Empréstimos e Financiamentos | 9.245,9 | 0,0 | -9.245,9 |
| BPP | 2.02 | Passivo Não Circulante | 15.271,0 | 7.127,0 | -8.144,0 |

## Como reproduzir

```
python -m chiocca.v2.armazem      # monta data/armazem a partir de data/brutos/cvm e data/cache/enet
python -m chiocca.v2.buscar_enet 2024-12-31 --listar   # versões que a data precisa e não estão no armazém
python -m chiocca.v2.invariante   # invariante e corte na data máxima; grava este documento
```
