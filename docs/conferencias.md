# Conferências de qualidade dos dados da CVM (Fase B do v2)

Gerado por `python -m chiocca.v2.relatorio_conferencias` a partir de `data/base/` (fora do git), a base "como era na época" do estudo 1. Não edite à mão: um teste compara este arquivo com a saída do script. Só números agregados; nenhuma empresa é citada.

Empresa-anos com versão da época, de 2010 até o lacre (2023): 8.594. Dados abertos: 8.253; ENET: 341. Por plano de contas: não financeiro, 8.027; banco, 526; seguradora, 32; não reconhecido, 9.

As conferências descrevem os dados. Elas não mudam nenhum sinal, alerta ou número do estudo 1: um número com conferência falha só leva o estado "implausível" e o critério de consistência na confiança.

## O que cada tipo de conferência quer dizer

- **Identidade:** igualdade garantida pela contabilidade (ativo total = passivo total, subtotais do balanço e da DRE, soma e saldos da DFC). Falhar indica erro de preenchimento na CVM ou de leitura, não um ano ruim.
- **Reconciliação:** o mesmo número por outro caminho, entre demonstrações (saldo de caixa da DFC contra o caixa e equivalentes do balanço). Pode falhar por motivo legítimo, como caixa restrito, saldo bancário negativo ou ativo mantido para venda.
- **Plausibilidade:** valor fora do que o sinal contábil permite (ativo total não positivo, conta de saldo negativa, receita negativa, custo ou despesa com sinal de receita).

Tolerância de R$ 1.000 por parcela da igualdade, só para arredondamento. Conta ausente não vira zero: a conferência fica "não se aplica". Os códigos por conta valem para o plano não financeiro; nos outros planos, só ativo total = passivo total e as identidades da DFC, cujos códigos são fixos em todos os planos.

## Resumo

Empresa-anos com pelo menos uma falha no exercício (coluna ÚLTIMO): 1.296 de 8.594 (15,1%). Por tipo: identidade, 25 (0,3%); reconciliação, 1.182 (13,8%); plausibilidade, 116 (1,3%).

## Resultado por conferência, no exercício (coluna ÚLTIMO)

| Conferência | Tipo | Aplicáveis | Falhas | Parte | Diferença até 0,1% | 0,1% a 1% | 1% a 10% | Acima de 10% | Falhas em dados abertos | Falhas no ENET |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ativo total = passivo total | identidade | 8.594 | 1 | 0,0% | 0 | 0 | 0 | 1 | 1 | 0 |
| ativo total = circulante + não circulante | identidade | 8.027 | 3 | 0,0% | 1 | 0 | 2 | 0 | 3 | 0 |
| passivo total = circulante + não circulante + patrimônio líquido | identidade | 8.027 | 1 | 0,0% | 0 | 0 | 0 | 1 | 1 | 0 |
| resultado bruto = receita + custo | identidade | 8.027 | 3 | 0,0% | 0 | 0 | 1 | 2 | 3 | 0 |
| resultado antes do financeiro = bruto + despesas e receitas operacionais | identidade | 8.027 | 3 | 0,0% | 0 | 0 | 0 | 3 | 3 | 0 |
| resultado antes dos tributos = antes do financeiro + resultado financeiro | identidade | 8.027 | 0 | 0,0% | 0 | 0 | 0 | 0 | 0 | 0 |
| operações continuadas = antes dos tributos + IR e CSLL | identidade | 8.027 | 4 | 0,0% | 0 | 0 | 0 | 4 | 4 | 0 |
| lucro do período = continuadas + descontinuadas | identidade | 8.027 | 3 | 0,0% | 0 | 0 | 0 | 3 | 3 | 0 |
| variação do caixa = operacional + investimento + financiamento + variação cambial | identidade | 8.591 | 12 | 0,1% | 1 | 2 | 0 | 9 | 10 | 2 |
| variação do caixa = saldo final − saldo inicial | identidade | 8.594 | 9 | 0,1% | 2 | 0 | 1 | 6 | 7 | 2 |
| saldo final da DFC = caixa e equivalentes do balanço | reconciliação | 8.026 | 1.025 | 12,8% | 19 | 26 | 86 | 894 | 973 | 52 |
| saldo inicial da DFC = caixa e equivalentes do balanço anterior | reconciliação | 7.947 | 1.029 | 12,9% | 16 | 18 | 72 | 923 | 977 | 52 |
| ativo total positivo | plausibilidade | 8.594 | 16 | 0,2% | — | — | — | — | 15 | 1 |
| ativo circulante (1.01) não negativa | plausibilidade | 8.027 | 0 | 0,0% | — | — | — | — | 0 | 0 |
| caixa e equivalentes (1.01.01) não negativa | plausibilidade | 8.026 | 3 | 0,0% | — | — | — | — | 3 | 0 |
| contas a receber (1.01.03) não negativa | plausibilidade | 8.027 | 0 | 0,0% | — | — | — | — | 0 | 0 |
| estoques (1.01.04) não negativa | plausibilidade | 8.027 | 0 | 0,0% | — | — | — | — | 0 | 0 |
| ativo não circulante (1.02) não negativa | plausibilidade | 8.027 | 2 | 0,0% | — | — | — | — | 2 | 0 |
| imobilizado (1.02.03) não negativa | plausibilidade | 8.027 | 0 | 0,0% | — | — | — | — | 0 | 0 |
| passivo circulante (2.01) não negativa | plausibilidade | 8.027 | 1 | 0,0% | — | — | — | — | 1 | 0 |
| fornecedores (2.01.02) não negativa | plausibilidade | 8.027 | 0 | 0,0% | — | — | — | — | 0 | 0 |
| passivo não circulante (2.02) não negativa | plausibilidade | 8.027 | 0 | 0,0% | — | — | — | — | 0 | 0 |
| receita (3.01) não negativa | plausibilidade | 8.027 | 14 | 0,2% | — | — | — | — | 13 | 1 |
| custo das vendas (3.02) não positiva | plausibilidade | 8.027 | 14 | 0,2% | — | — | — | — | 8 | 6 |
| despesas com vendas (3.04.01) não positiva | plausibilidade | 8.027 | 31 | 0,4% | — | — | — | — | 29 | 2 |
| despesas gerais e administrativas (3.04.02) não positiva | plausibilidade | 8.027 | 42 | 0,5% | — | — | — | — | 41 | 1 |

As faixas medem a diferença entre os dois lados da igualdade em proporção do maior deles; não se aplicam às conferências de plausibilidade (—).

**Leitura das falhas mais frequentes.** Das 1.025 falhas de "saldo final da DFC = caixa e equivalentes do balanço" no exercício, 692 fecham quando se somam as aplicações financeiras (1.01.02) ao caixa: a empresa usa na DFC um conceito de caixa mais amplo que o da conta 1.01.01, o que é escolha de apresentação e não erro de leitura. Das falhas de "ativo total positivo", 16 no exercício e 88 no comparativo têm o ativo total igual a zero, o que indica comparativo não preenchido. Das 39 falhas de identidade no exercício, 14 têm um dos lados igual a zero (subtotal ou soma não preenchidos); as empresa-anos com falha de identidade estão nos exercícios 2021, 2022 (tabela por exercício abaixo).

## Resultado por conferência, no comparativo (coluna PENÚLTIMO)

| Conferência | Tipo | Aplicáveis | Falhas | Parte | Diferença até 0,1% | 0,1% a 1% | 1% a 10% | Acima de 10% | Falhas em dados abertos | Falhas no ENET |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ativo total = passivo total | identidade | 8.507 | 0 | 0,0% | 0 | 0 | 0 | 0 | 0 | 0 |
| ativo total = circulante + não circulante | identidade | 7.948 | 1 | 0,0% | 0 | 0 | 1 | 0 | 1 | 0 |
| passivo total = circulante + não circulante + patrimônio líquido | identidade | 7.948 | 0 | 0,0% | 0 | 0 | 0 | 0 | 0 | 0 |
| resultado bruto = receita + custo | identidade | 7.948 | 0 | 0,0% | 0 | 0 | 0 | 0 | 0 | 0 |
| resultado antes do financeiro = bruto + despesas e receitas operacionais | identidade | 7.948 | 0 | 0,0% | 0 | 0 | 0 | 0 | 0 | 0 |
| resultado antes dos tributos = antes do financeiro + resultado financeiro | identidade | 7.948 | 0 | 0,0% | 0 | 0 | 0 | 0 | 0 | 0 |
| operações continuadas = antes dos tributos + IR e CSLL | identidade | 7.948 | 2 | 0,0% | 0 | 0 | 0 | 2 | 2 | 0 |
| lucro do período = continuadas + descontinuadas | identidade | 7.948 | 2 | 0,0% | 0 | 0 | 0 | 2 | 2 | 0 |
| variação do caixa = operacional + investimento + financiamento + variação cambial | identidade | 8.504 | 6 | 0,1% | 0 | 0 | 0 | 6 | 5 | 1 |
| variação do caixa = saldo final − saldo inicial | identidade | 8.507 | 5 | 0,1% | 1 | 0 | 0 | 4 | 4 | 1 |
| saldo final da DFC = caixa e equivalentes do balanço | reconciliação | 7.947 | 1.006 | 12,7% | 17 | 22 | 86 | 881 | 956 | 50 |
| ativo total positivo | plausibilidade | 8.507 | 88 | 1,0% | — | — | — | — | 82 | 6 |
| ativo circulante (1.01) não negativa | plausibilidade | 7.948 | 0 | 0,0% | — | — | — | — | 0 | 0 |
| caixa e equivalentes (1.01.01) não negativa | plausibilidade | 7.947 | 1 | 0,0% | — | — | — | — | 0 | 1 |
| contas a receber (1.01.03) não negativa | plausibilidade | 7.948 | 0 | 0,0% | — | — | — | — | 0 | 0 |
| estoques (1.01.04) não negativa | plausibilidade | 7.948 | 0 | 0,0% | — | — | — | — | 0 | 0 |
| ativo não circulante (1.02) não negativa | plausibilidade | 7.948 | 1 | 0,0% | — | — | — | — | 1 | 0 |
| imobilizado (1.02.03) não negativa | plausibilidade | 7.948 | 0 | 0,0% | — | — | — | — | 0 | 0 |
| passivo circulante (2.01) não negativa | plausibilidade | 7.948 | 0 | 0,0% | — | — | — | — | 0 | 0 |
| fornecedores (2.01.02) não negativa | plausibilidade | 7.948 | 0 | 0,0% | — | — | — | — | 0 | 0 |
| passivo não circulante (2.02) não negativa | plausibilidade | 7.948 | 3 | 0,0% | — | — | — | — | 3 | 0 |
| receita (3.01) não negativa | plausibilidade | 7.948 | 11 | 0,1% | — | — | — | — | 9 | 2 |
| custo das vendas (3.02) não positiva | plausibilidade | 7.948 | 11 | 0,1% | — | — | — | — | 6 | 5 |
| despesas com vendas (3.04.01) não positiva | plausibilidade | 7.948 | 29 | 0,4% | — | — | — | — | 29 | 0 |
| despesas gerais e administrativas (3.04.02) não positiva | plausibilidade | 7.948 | 30 | 0,4% | — | — | — | — | 29 | 1 |

## Não se aplica, por motivo (coluna ÚLTIMO)

| Conferência | Conta ausente | Outro plano de contas | Sem a coluna |
| --- | --- | --- | --- |
| ativo total = circulante + não circulante | 0 | 567 | 0 |
| passivo total = circulante + não circulante + patrimônio líquido | 0 | 567 | 0 |
| resultado bruto = receita + custo | 0 | 567 | 0 |
| resultado antes do financeiro = bruto + despesas e receitas operacionais | 0 | 567 | 0 |
| resultado antes dos tributos = antes do financeiro + resultado financeiro | 0 | 567 | 0 |
| operações continuadas = antes dos tributos + IR e CSLL | 0 | 567 | 0 |
| lucro do período = continuadas + descontinuadas | 0 | 567 | 0 |
| variação do caixa = operacional + investimento + financiamento + variação cambial | 3 | 0 | 0 |
| saldo final da DFC = caixa e equivalentes do balanço | 1 | 567 | 0 |
| saldo inicial da DFC = caixa e equivalentes do balanço anterior | 80 | 567 | 0 |
| caixa e equivalentes (1.01.01) não negativa | 1 | 0 | 0 |

## Empresa-anos com falha de identidade, por exercício (coluna ÚLTIMO)

| Exercício | Empresa-anos | Com falha de identidade | Parte |
| --- | --- | --- | --- |
| 2010 | 569 | 0 | 0,0% |
| 2011 | 603 | 0 | 0,0% |
| 2012 | 595 | 0 | 0,0% |
| 2013 | 602 | 0 | 0,0% |
| 2014 | 586 | 0 | 0,0% |
| 2015 | 589 | 0 | 0,0% |
| 2016 | 572 | 0 | 0,0% |
| 2017 | 586 | 0 | 0,0% |
| 2018 | 576 | 0 | 0,0% |
| 2019 | 557 | 0 | 0,0% |
| 2020 | 650 | 0 | 0,0% |
| 2021 | 727 | 15 | 2,1% |
| 2022 | 692 | 10 | 1,4% |
| 2023 | 690 | 0 | 0,0% |
