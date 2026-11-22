# Pré-registro do motor v2 (rascunho)

> **Rascunho de 22/11/2026, para revisão de Roberto e do Claude (claude.ai). Ainda não é registro.** O registro será o commit que introduzir a versão aprovada, com outro nome de arquivo ou sem a palavra "rascunho", até 20/12/2026, com o hash anotado no commit seguinte, sem mudar nenhuma regra, como no estudo 1, no leitor e no estudo 2. A emenda 5 ao estudo 2, que acrescenta o braço do v2, está ao lado, também em rascunho: [`docs/estudo-2-emenda-5-rascunho.md`](estudo-2-emenda-5-rascunho.md).
>
> Base: o [plano do motor v2](motor-v2-plano.md), com as decisões de Roberto de 22/11/2026, e as [descrições sem rótulo](motor-v2-descricoes.md), só com exercícios até 2023. Nenhum valor de exercício de 2024 em diante foi lido; das DFP de 2024 em diante, só metadados.

## 1. O que é o v2

O motor v2 é o motor v1 com três mudanças, cada uma ligada a uma falha documentada do v1 no estudo 1: (1) o DEPI pela DVA quando a DFC não dá o DEPI; (2) o desvio de Benford padronizado como sinal novo, nos dois grupos; (3) o alerta pelo escore, nos 10% do ano dentro do grupo, no lugar dos cortes fixos. Todo o resto é o do v1: a base "como era na época", as amostras, as exclusões, os grupos e as fórmulas dos sinais que já existiam. O v2 é avaliado como um braço a mais na avaliação secundária do estudo 2 (emenda 5) e, depois, num teste prospectivo próprio com os exercícios de 2026, com pré-registro próprio. O produto continua com o v1; a troca para o v2 é uma decisão separada, depois da avaliação de 2027.

## 2. Amostra, grupos e versão usada

Como no v1 (pré-registro do estudo 1, seções 2 e 3, e emendas): as companhias abertas com DFP, em dois grupos, não financeiras e financeiras; as mesmas exclusões; cada empresa-ano com a versão da DFP pública no corte, e, quando a versão dos dados abertos é posterior ao corte, a versão da época pela rota do ENET, só para o consolidado.

## 3. Sinais por grupo

| Grupo | Sinais do escore |
| --- | --- |
| Não financeiras | M-score (com o DEPI pela DVA), salto do DPO, juro implícito, desvio de Benford padronizado |
| Financeiras | peso de ganhos não recorrentes, desvio de Benford padronizado |

O lucro que não vira caixa continua na ficha, fora do escore, como no v1 (pré-registro do estudo 1, seção 4: ele já entra no M-score pelo TATA). Em todos os sinais, valor maior quer dizer mais incomum.

### 3.1 M-score, com o DEPI pela DVA

- **Fórmula (Beneish, 1999), como no v1:** M = -4,84 + 0,920 DSRI + 0,528 GMI + 0,404 AQI + 0,892 SGI + 0,115 DEPI - 0,172 SGAI + 4,679 TATA - 0,327 LVGI, com os componentes e as escolhas de cálculo do v1 (catálogo de sinais; pré-registro do estudo 1, seção 4.1). O corte de -1,78 deixa de existir: o M entra no escore pelo percentil (seção 4).
- **DEPI:** taxa de t-1 ÷ taxa de t, com taxa = depreciação ÷ (depreciação + imobilizado).
- **A depreciação, nesta ordem:** (1) a da DFC, como no v1 (subcontas de 6.01.01 cujo nome contém "deprecia"; a linha que junta depreciação e amortização entra pelo total, com a marca); (2) se o DEPI do v1 não é calculável e a versão usada é a dos dados abertos, a da DVA: a conta 7.04.01, 7.05.01 ou 7.07.01 cujo nome contém "deprecia", nessa ordem de preferência, do mesmo tipo (consolidado ou individual) e da mesma DFP, nas colunas de t e t-1, em valor absoluto, com a marca "depreciação pela DVA". Nas versões do ENET, que não trazem a DVA, o DEPI fica como no v1.
- **Cobertura nas descrições (2010 a 2023):** o M-score passa de 5.390 para 6.017 das 6.938 empresa-anos não financeiras.

### 3.2 Salto do DPO, juro implícito e peso de ganhos não recorrentes

- **Salto do DPO:** como no v1, DPO de t menos DPO de t-1, com DPO = fornecedores ÷ |custo das vendas| × 365.
- **Juro implícito:** como no v1, |despesa financeira| ÷ média dos empréstimos de curto e longo prazo de t e t-1, menos o CDI médio do ano (SGS 4389). Dentro de um ano, a ordem é a mesma da taxa implícita. As subcontas de 3.06.02 não entram: aparecem em 8,8% a 12,4% das não financeiras avaliadas de 2019 a 2023, abaixo do critério de 50% escrito antes da descrição.
- **Peso de ganhos não recorrentes (financeiras):** como no v1.

### 3.3 Desvio de Benford padronizado

- **Os números:** os valores diferentes de zero na coluna do exercício de BPA, BPP, DRE e DFC da versão usada, os quatro demonstrativos que existem nos dados abertos e no ENET. De cada um, o primeiro dígito significativo de |valor|.
- **O desvio:** o desvio médio absoluto entre a frequência de cada dígito de 1 a 9 e a lei de Benford, log10(1 + 1/d), somado e dividido por 9.
- **As faixas:** os quintis da quantidade de números, dentro do exercício e do grupo, entre as empresa-anos com pelo menos 20 números (`qcut` do pandas sobre `rank(method="first")`, 5 faixas).
- **A padronização (a do artigo de Chakrabarty et al., 2025):** (desvio - média do desvio na faixa) ÷ desvio-padrão do desvio na faixa (amostral, n - 1). Os coeficientes do artigo, estimados com AAER dos EUA, não são usados.
- **Calculável** se a empresa-ano tem pelo menos 20 números (nenhuma empresa-ano de 2010 a 2023 tem menos de 23) e a faixa tem desvio-padrão maior que zero.
- **Nas descrições (2010 a 2023):** o topo do desvio padronizado fica entre 18,0% e 21,3% em cada quintil de quantidade de números nas não financeiras; ele não se concentra nas empresas com poucos números.

## 4. Escore, alerta e ranking

- **Percentil de cada sinal:** dentro do exercício e do grupo, entre as empresa-anos com o sinal calculável, pelo `rank(pct=True)` do pandas (empates recebem a média das posições).
- **Escore:** o maior percentil entre os sinais calculáveis da empresa-ano. Foi escolhido, contra esse maior percentil elevado ao número de sinais calculáveis, pela descrição sem rótulo da seção 7 das descrições, com o critério escrito por Roberto antes de rodar (fica a versão com a menor das maiores distâncias entre a taxa por número de sinais calculáveis e a taxa do grupo; em empate, o maior percentil simples): a maior distância foi de 6,8 p.p. com o maior percentil e de 12,9 p.p. com a versão elevada ao número de sinais.
- **Avaliada:** a empresa-ano com pelo menos um sinal calculável.
- **Alerta:** escore maior ou igual ao quantil de 90% do escore entre as avaliadas do exercício e do grupo, pelo `quantile(0.9)` do pandas, com interpolação linear, como o decil do v1. A taxa fica perto de 10% por construção; empates no limite podem levá-la um pouco acima.
- **Ranking das métricas de ranking do estudo 2:** o escore, do maior para o menor, e as empresa-anos sem escore depois; desempate pelo código CVM, em ordem crescente, e, entre as duas empresa-anos da mesma companhia, pelo exercício, em ordem crescente (emenda 2, item 3(b), do estudo 2).
- **Ficha:** cada sinal com o valor, o percentil e qual define o escore; o lucro que não vira caixa aparece sem entrar no escore.
- **Características conhecidas, sem correção.** (1) A taxa de alerta varia com o número de sinais calculáveis: nas não financeiras de 2010 a 2023, 7,0% com um sinal, 16,9% com dois, 14,5% com três e 9,1% com quatro. (2) O topo se concentra nas empresas com poucos números: 32,0% dos alertas no quintil com menos números e 11,1% no quintil com mais, nas não financeiras. Isso vem do M-score, do DPO e do juro implícito, não do Benford: sem o Benford, o primeiro quintil teria 31,5% dos alertas, e o topo do Benford padronizado fica entre 18,0% e 21,3% em cada quintil. No relatório de 2027, a distribuição dos alertas do v2 por quintil de quantidade de números entra só agregada, como descrição.

## 5. Regra de desenvolvimento

- **Só exercícios até 2023.** O código do v2 é escrito e medido com o lacre do produto em 2023 e 31/12/2024. Nenhum dado de 2024 em diante é lido antes da sessão do lacre da lista do v2.
- **Só critérios sem rótulo:** cobertura, taxa de alerta, estabilidade entre os anos e testes de correção. As escolhas deste pré-registro foram feitas assim, com as descrições.
- **O gabarito não é usado** para escolher nem ajustar nada. O código do v2 não lê `data/gabarito_casos.csv` nem importa as métricas do estudo 1; um teste confere.
- **Os acertos do v2 nos casos do estudo 1** só depois do congelamento, como descrição dentro da amostra, com o rótulo "dentro da amostra de desenvolvimento, não é teste". Nenhum acerto, caso ou alerta por companhia do gabarito é calculado ou mostrado antes disso.

## 6. Congelamento

- **Registro de SHA-256 próprio** (`docs/motor_v2_codigo_congelado.json`), com um teste que acusa qualquer mudança. O registro do v1 (`docs/estudo_2_codigo_congelado.json`) não muda.
- **Exemplo calculado à mão por script separado,** escrito antes do código do v2, como o exemplo resolvido do estudo 1: (a) o Benford, numa tabela fictícia de empresa-anos, com os dígitos, o desvio, as faixas e a padronização; (b) o DEPI pela DVA, numa empresa-ano fictícia sem depreciação na DFC. O v2 tem de reproduzir os valores do script.
- **Invariante:** com as três mudanças desligadas (o DEPI só pela DFC, sem o Benford e com as regras de alerta do v1), o v2 reproduz o v1 nas 9.474 empresa-anos do invariante do estudo 1.
- **Descrição do v2 congelado, dentro da amostra:** as taxas de alerta e a cobertura de 2010 a 2023 e, só então, os acertos nos casos do estudo 1, rotulados.

## 7. Previsões escritas antes dos dados (braço do v2 no estudo 2)

1. **Taxa de alerta:** entre 10,0% e 11,0% das não financeiras avaliadas em cada exercício e entre 10% e 14% das financeiras. Motivo: o alerta é o decil superior do escore; empates no limite e grupos pequenos puxam a taxa um pouco para cima. Nas descrições de 2010 a 2023, com o Benford padronizado, a taxa foi de 10,1% nas não financeiras e de 11,6% nas financeiras.
2. **DR do v2:** positiva, com razão de taxas entre 1,0 e 2,0, e "sem evidência de associação" como resultado mais provável. Motivo: com cerca de 1.200 empresa-anos avaliadas e 10% em alerta, são cerca de 120 empresa-anos em alerta, e, na taxa de 4,7%, cerca de 6 republicações seriam esperadas entre elas sem associação nenhuma. Supondo empresa-anos independentes, o poder aproximado do teste unilateral é de 0,25 para uma razão de taxas de 1,5, de 0,53 para 2,0 e de 0,76 para 2,5; com o bootstrap por companhia, é menor. Os sinais medem accruals, prazos e financiamento, que só em parte acabam em republicação.
3. **Diferença pareada v2 menos v1 (DR):** sem vencedor declarado. Motivo: o v1 alerta perto de metade das empresa-anos (a previsão do estudo 2 é de 40% a 60%) e o v2, 10%; as duas DR vêm de grupos em alerta de tamanhos muito diferentes, e o intervalo da diferença fica largo.
4. **v2 contra a regra boba:** sem vencedor declarado. Motivo: os dois alertam 10% das empresa-anos, os grupos em alerta são pequenos, e o endividamento da regra boba também se relaciona com dificuldade financeira, que pode levar a republicações.
5. **Subconjunto prospectivo:** com a meta cumprida, a maior parte das empresa-anos de 2025 fica prospectiva. Motivo: nas descrições, 98,7% das primeiras entregas da DFP de 2023 até o corte foram depois de 31/01/2024.

## 8. Rótulo prospectivo, partes 2a e 2b e Roberto sem abrir a lista

- **Rótulo prospectivo por empresa-ano:** uma empresa-ano de 2025 é prospectiva para o v2 se a primeira entrega da DFP de 2026 dela (o menor DT_RECEB do índice da CVM) é posterior ao commit com o SHA-256 da lista do v2. As de 2024 são não prospectivas nos dois braços. O braço do v2 é relatado no total e no subconjunto prospectivo; se valer a reserva do calendário, o braço inteiro leva também o rótulo "não prospectivo".
- **Partes 2a e 2b:** para o braço do v2, a parte 2 do gabarito do estudo 2 se divide pela data desse commit: a 2a, com os casos cujo documento qualificador (emenda 1, item 1, do estudo 2) é público entre o congelamento da parte 1 (19/11/2026) e o commit; a 2b, com os públicos depois dele e até 31/12/2029. A comparação com o v1 no descritivo do primário usa só a 2b; a 2a vem com o rótulo "público antes do lacre do v2". Para o v1, nada muda.
- **Roberto sem abrir a lista:** Roberto não abre o arquivo da lista do v2 nem roda o código dele antes de congelar a parte 2 do gabarito. Na avaliação secundária, a lista é recalculada pelo script, e só saem medidas agregadas; o agente não descreve nenhum alerta do v2 por companhia.

## 9. Calendário

| Etapa | Data-limite | Se atrasar |
| --- | --- | --- |
| Registro deste pré-registro e da emenda 5 ao estudo 2, com o carimbo do OpenTimestamps | 20/12/2026 | As datas abaixo não mudam. Sem os dois registrados antes da sessão do lacre, o v2 não entra no estudo 2. |
| Meta: v2 congelado (registro de SHA-256, exemplo à mão, invariante) | 25/01/2027 | Vale a reserva. |
| Meta: sessão do lacre da lista do v2 | 31/01/2027 | Vale a reserva. |
| Reserva: v2 congelado | 31/03/2027 | Não entra, sem outra prorrogação. |
| Reserva: sessão do lacre, com o rótulo "não prospectivo" | de 01/04/2027 a 15/04/2027 | Não entra, sem outra prorrogação. |
| Corte da DFP de 2026 | 30/04/2027 | data do pré-registro do estudo 2, não muda |
| Avaliação secundária, os dois braços na mesma sessão (o v1 primeiro) | a partir de 31/05/2027 | "A partir de": a data pode passar. |
| Teste prospectivo próprio do v2, com os exercícios de 2026 | depois, com pré-registro próprio | — |

## 10. O que fica de fora

As subcontas de 3.06.02 no juro implícito; os accruals discricionários e o F-score de Dechow e outros (2011), pelos motivos do plano; os dados trimestrais (ITR); o aprendizado supervisionado; qualquer dado de 2024 em diante no desenvolvimento; qualquer mudança no motor v1 ou no registro dele.

## 11. Registro

- Data: a preencher no registro.
- Commit: o que introduzir a versão aprovada. O hash é anotado no commit seguinte, sem mudar nenhuma regra acima.
- Carimbo de tempo, como no estudo 2: um arquivo em `docs/carimbos/` com o hash do commit de registro deste pré-registro e o da emenda 5 ao estudo 2, e o SHA-256 dos dois arquivos registrados, carimbado com o OpenTimestamps; o `.ots` vai para o repositório, e o `ots upgrade` é feito depois da confirmação no Bitcoin. Se os calendários não responderem, Roberto carimba pelo site opentimestamps.org e devolve o `.ots`.
