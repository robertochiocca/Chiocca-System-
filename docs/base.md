# Base "como era na época" (Fase 1)

Gerado por `python -m chiocca.relatorio_base` a partir de `data/base/empresa_ano.csv` (fora do git). Não edite à mão: um teste compara este arquivo com a saída do script.

Base montada em 07/11/2026, com os arquivos brutos conferidos contra `data/manifesto_brutos.csv`. Exercícios de 2010 a 2025. Nenhum sinal foi calculado nesta fase.

## Regras aplicadas

- **Versão da época:** a mais recente entregue até a data de corte, que é o último dia do quarto mês depois do fim do exercício (pré-registro, seção 3, e emenda 5).
- **Consolidado quando existir; senão, individual** (emenda 5).
- **Versão da época anterior à dos dados abertos:** vem da visualização HTML do ENET, só para o consolidado (emenda 8). Célula vazia vale 0.
- **Conta repetida na mesma demonstração:** com valores iguais, fica uma; com valores diferentes, a empresa-ano fica não calculável (emenda 8).
- **Grupos:** regra congelada da parte 4.1 do reconhecimento, com o FCA na versão entregue até o corte (emenda 7).
- **Duas leituras de cada exercício:** o original (ÚLTIMO na DFP do ano) e o reapresentado (PENÚLTIMO na DFP do ano seguinte), cada um na versão da sua data de corte.

## Empresa-anos por exercício e situação

| Exercício | Empresa-anos | Ok, dados abertos | Ok, ENET | Sem versão até o corte | Versão da época indisponível (só individual) | Versão da época indisponível (falha do ENET) | Pendente no ENET | Conta repetida com valores diferentes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2010 | 663 | 523 | 46 | 69 | 25 | 0 | 0 | 0 |
| 2011 | 684 | 562 | 41 | 59 | 22 | 0 | 0 | 0 |
| 2012 | 662 | 573 | 22 | 48 | 19 | 0 | 0 | 0 |
| 2013 | 652 | 582 | 20 | 36 | 14 | 0 | 0 | 0 |
| 2014 | 652 | 574 | 12 | 51 | 15 | 0 | 0 | 0 |
| 2015 | 633 | 568 | 21 | 33 | 11 | 0 | 0 | 0 |
| 2016 | 626 | 552 | 20 | 40 | 14 | 0 | 0 | 0 |
| 2017 | 632 | 567 | 19 | 38 | 8 | 0 | 0 | 0 |
| 2018 | 631 | 558 | 18 | 38 | 17 | 0 | 0 | 0 |
| 2019 | 671 | 541 | 16 | 104 | 9 | 0 | 0 | 1 |
| 2020 | 733 | 636 | 14 | 72 | 11 | 0 | 0 | 0 |
| 2021 | 771 | 706 | 21 | 37 | 7 | 0 | 0 | 0 |
| 2022 | 731 | 648 | 44 | 29 | 9 | 0 | 0 | 1 |
| 2023 | 733 | 663 | 27 | 31 | 9 | 0 | 0 | 3 |
| 2024 | 709 | 655 | 20 | 26 | 8 | 0 | 0 | 0 |
| 2025 | 669 | 639 | 5 | 20 | 5 | 0 | 0 | 0 |
| **Total** | **10.852** | **9.547** | **366** | **731** | **203** | **0** | **0** | **5** |

## O que ficou de fora ("não calculável" nesta fase)

- **Sem versão até o corte:** 731 empresa-anos. A primeira versão da DFP foi entregue depois da data de corte; pela emenda 5, a empresa-ano fica de fora naquele ano e é contada aqui.
- **Versão da época indisponível, só individual:** 203 empresa-anos. A versão dos dados abertos é posterior ao corte e a empresa não tem consolidado (ou a versão da época não tinha), então a rota do ENET não se aplica (emenda 8).
- **Versão da época indisponível, falha do ENET:** 0 empresa-anos (emenda 5).
- **Pendente no ENET:** 0 empresa-anos ainda sem a tabela baixada.
- **Conta repetida com valores diferentes:** 5 empresa-anos (emenda 8). Em todos, a repetição acontece no mesmo período, não em períodos diferentes.
- **Sem receita:** 1.228 empresa-anos do grupo das não financeiras, com a conta 3.01 ausente ou igual a zero. Saem da amostra das não financeiras (pré-registro, seção 2, e emenda 9).

## Grupos e amostra

- Empresa-anos com versão da época disponível: 9.913, de 1.223 empresas.
- **Financeiras:** 572. **Não financeiras:** 9.341, das quais 8.113 com receita.
- Plano de contas não reconhecido pela conta 3.01: 9 empresa-anos (ficam nas não financeiras).
- Empresa-anos em que uma conta repetida com valores iguais foi deduplicada: 22.
- Origem do setor (todas as empresa-anos): FCA 10.084, cadastro 744, sem setor 24.
- Situação no cadastro de hoje, entre as empresa-anos disponíveis: ativo 6.950, cancelado 2.763, suspenso por decisão administrativa 90, fora do cadastro 110. As empresas com registro cancelado continuam na base.

## Duas leituras

Empresa-anos com o exercício seguinte também disponível, no mesmo tipo de demonstração (exercícios até 2024): 8.361. Nelas dá para comparar o número original com o reapresentado.

## Rota do ENET

Documentos pedidos ao ENET: 390. Sem demonstração consolidada na versão da época: 24. Empresa-anos que entraram na base pelo ENET: 366; com ativo total (conta 1): 366; com receita (conta 3.01): 366; com caixa operacional (conta 6.01): 366. Versões antigas que mostram só a coluna do exercício, sem o comparativo (PENÚLTIMO): 2; nelas, o que depende de t-1 vai sair não calculável.

## Casos acertáveis do gabarito na base (sem valores)

| Caso | Anos do período afetado nos dados | Anos com versão da época | Desses, pelo ENET |
| --- | --- | --- | --- |
| americanas | 2021 | 1 de 1 | 0 |
| metalurgica_duque | 2010–2012 | 3 de 3 | 0 |
| mundial_2017 | 2012–2015 | 4 de 4 | 0 |
| hercules | 2014 | 1 de 1 | 0 |
| tecnosolo | 2013–2014 | 2 de 2 | 0 |
| inepar_equipamentos | 2013 | 1 de 1 | 0 |
| ceb | 2011–2012 | 2 de 2 | 0 |
| fibam | 2016–2017 | 2 de 2 | 0 |
| metalgrafica_iguacu | 2010–2011 | 2 de 2 | 0 |
| cafe_soluvel_brasilia | 2011 | 1 de 1 | 1 |
| comercial_quintella | 2012–2013 | 2 de 2 | 2 |
| cobrasma | 2014 | 1 de 1 | 0 |
| petrobras_2014 | 2010–2012 | 3 de 3 | 0 |

IRB, exercício de 2019 (não acertável pela emenda 3): situação `ok`, fonte `enet`.
