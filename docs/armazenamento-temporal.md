# Armazenamento temporal e motor v1 em qualquer data (Fase C1)

Gerado por `python -m chiocca.v2.invariante` a partir de `docs/invariante_numeros.json`. Não edite à mão: um teste compara este arquivo com a saída do script. Só números agregados; nenhuma empresa é citada.

## O armazém

- Parquet consultado pelo DuckDB (`chiocca/v2/armazem.py`), montado sem rede de `data/brutos/cvm` (conferido por hash) e do cache do ENET, em `data/armazem/`, fora do git. Exercícios de 2010 a 2023; nenhum exercício lacrado entra.
- Tabelas: `versoes` (12.372 versões de DFP, com a data de entrega), `contas` (7.550.288 linhas, dos dados abertos e de 341 documentos do ENET), `fca` (22.203 versões) e `cadastro` (2.679 linhas). O `manifesto.json` guarda o hash SHA-256 de cada arquivo de origem.
- De documento entregue depois de 31/12/2024, o armazém guarda só metadados: versão, data de entrega e quais demonstrações existem, sem nenhuma conta nem valor (14 documentos). O `como_era` do motor v1 usa essa estrutura da última versão para saber se há consolidado (rota do ENET, emenda 8) e para nomear a DFC do ENET; com data de referência até 31/12/2024, os valores dessa versão nunca são lidos.
- `FontesArmazem` tem a mesma interface dos arquivos brutos (`chiocca.cvm.Fontes`): o motor v1 roda sobre o armazém sem nenhuma mudança.

## Motor v1 na data

- `ExercicioNaData` (`chiocca/v2/na_data.py`): uma empresa num exercício, como era na data de referência, com a versão usada, só as versões entregues até a data, a origem (dados abertos ou ENET) e o link do documento. A data passa pelo intervalo de 30/04/2011 a 31/12/2024, e o exercício, pelo lacre.
- Corte transversal na data: as mesmas funções do estudo 1 (`como_era`, `grupos`, `sinais_amostra`), com os decis do ano recalculados só com as empresas cuja versão era pública na data.
- Camada do produto, ao lado do motor e sem mudar nenhum valor dele: a coluna `produto_nao_calculaveis` lista os sinais que o produto mostra como "não calculável" por balanço não preenchido.

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

Com a data de referência em 31/12/2024, cada exercício usa a versão mais recente entregue até essa data. Contagens contra a data de corte, sem nenhuma empresa citada:

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
| 2023 | 702 | 29 | 1 | 627 | 1 | 0 |

"Pendente do ENET" é a versão da data que não está no armazém; a busca no ENET é um comando separado e nunca acontece dentro de uma consulta (pergunta 9 do plano).

## Como reproduzir

```
python -m chiocca.v2.armazem      # monta data/armazem a partir de data/brutos/cvm e data/cache/enet
python -m chiocca.v2.invariante   # invariante e corte na data máxima; grava este documento
```
