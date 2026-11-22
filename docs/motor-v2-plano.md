# Motor v2: rascunho do plano

Rascunho de 22/11/2026, pedido por Roberto, com as decisões dele do mesmo dia (resumo no fim). **Não é o pré-registro e não tem código do motor.** Foi escrito sem nenhum valor de exercício de 2024 em diante. Os números do estudo 1 vêm de [`docs/resultados_numeros.json`](resultados_numeros.json); os do estudo 2, de [`docs/estudo_2_numeros.json`](estudo_2_numeros.json), só metadados; as datas e as regras, do [pré-registro do estudo 2](pre-registro-estudo-2.md), que não muda nesta rodada: a emenda da seção 4 é só um rascunho. Um teste confere cada número contra os JSONs.

## Objetivo

- **Tentar o v2 no estudo 2** (decisão de Roberto, 22/11/2026), como um braço a mais na avaliação secundária (a partir de 31/05/2027), ao lado do v1 e da regra boba, pela emenda 5, que só acrescenta o braço. A análise do v1 não muda em nada: lista, registro, desfechos, métricas, semente, critérios e previsões continuam os do pré-registro.
- **Meta prospectiva:** o v2 congelado até 25/01/2027 (código e registro de SHA-256 próprio) e a lista dele para 2024 e 2025 lacrada até 31/01/2027, antes da entrega da maior parte das DFP de 2026.
- **Reserva:** se a meta não for cumprida, valem o congelamento até 31/03/2027 e o lacre até 15/04/2027, antes do corte de 30/04/2027, com o rótulo "não prospectivo", sem outra prorrogação. Se a reserva também não for cumprida, o v2 não entra no estudo 2; a avaliação do v1 segue como pré-registrada.
- **Rótulo por empresa-ano, em qualquer caso:** uma empresa-ano de 2025 conta como prospectiva para o v2 se a DFP de 2026 dela foi recebida depois do commit com o SHA-256 da lista do v2, pelo DT_RECEB do índice da CVM; com mais de uma versão, vale a primeira entrega (o menor DT_RECEB), porque uma versão anterior já teria tornado o comparativo de 2025 público. As empresa-anos de 2024 são não prospectivas nos dois braços. O braço do v2 é relatado no total e no subconjunto prospectivo.

## 1. Mudanças candidatas

Cada mudança responde a uma falha documentada do v1 nos exercícios de 2010 a 2023. A escolha final (seção 2) usa só critérios sem rótulo; os números de casos do estudo 1 são conhecidos, mas não entram na escolha.

### 1.1 Juro implícito revisto

- **Falha do v1.** O juro implícito responde sozinho por 59,8% das empresa-anos não financeiras em alerta (2.001 de 3.345). Ele alerta em 40,7% das empresa-anos em que é calculável (2.528 de 6.214), entre 31,5% e 52,1% conforme o ano. A despesa financeira (3.06.02) inclui variação cambial, juros de arrendamento e outros itens que não são juros dos empréstimos, e o corte fixo (CDI médio do ano mais 10 p.p.) não acompanha o ano.
- **Mudança, só com a DFP.** (a) Tirar da despesa financeira as subcontas de 3.06.02 cujo nome indica variação cambial ou arrendamento, quando a companhia as detalha, localizadas por texto como a depreciação na DFC do v1, com cada falha registrada; (b) trocar o corte fixo pelo corte por fração do ano (1.3).
- **Fica fora.** A versão pelas notas explicativas (item 2 da seção g do [plano do estudo 2](estudo-2-plano.md)) precisa das notas, que não estão entre as entradas (seção 3).
- **Decisão:** (b) entra pelo 1.3. (a) só entra se a descrição mostrar cobertura suficiente das subcontas, nas versões dos dados abertos e nas do ENET. Critério proposto, a fechar no pré-registro do v2: (a) entra se, em cada exercício de 2019 a 2023, pelo menos metade das empresa-anos não financeiras avaliadas detalhar 3.06.02 com pelo menos uma subconta de variação cambial ou de arrendamento reconhecível pelo nome.

### 1.2 Depreciação pela DVA

- **Falha do v1.** O M-score ficou sem valor em 1.548 de 6.938 empresa-anos; em 1.306, faltou o DEPI. O motivo mais comum é a DFC sem linha de depreciação na seção 6.01.01 (1.135 empresa-anos).
- **Mudança.** Quando a DFC não traz a depreciação, usar a conta fixa "Depreciação, Amortização e Exaustão" da DVA (7.04.01 na maioria dos planos; 7.05.01 ou 7.07.01 em outros, [reconhecimento](reconhecimento.md)). Ela junta depreciação e amortização: vale a regra que o v1 já usa para a linha combinada da DFC (usar o total e marcar a empresa-ano). A DFC continua em primeiro lugar, e o v2 fica igual ao v1 onde o v1 já calcula o DEPI.
- **Limite.** A DVA está nos zips da DFP, mas os 26 documentos do ENET do estudo 2 trazem só BPA, BPP, DRE e DFC. Nas empresa-anos cuja versão da época vem do ENET, não há a DVA daquela versão; usar a DVA de uma versão posterior quebraria a regra "como era na época". Nelas, o DEPI fica como no v1.

### 1.3 Cortes sem rótulo

- **Falha do v1.** Os cortes fixos dão frações muito diferentes e instáveis entre os sinais e os anos: o M-score acima de -1,78 alerta 15,0% das empresa-anos em que é calculável (810 de 5.390), entre 8,9% e 24,5% conforme o ano; o juro implícito, 40,7% (entre 31,5% e 52,1%); o salto do DPO, no decil superior, 10,1% (641 de 6.341). O corte de -1,78 vem de Beneish (1999), com empresas dos EUA, e não foi recalibrado para o Brasil. A taxa de alerta das não financeiras foi de 49,9% (3.345 de 6.704).
- **Mudança.** Cada sinal alerta uma fração fixa das empresa-anos do ano em que é calculável, dentro de cada grupo (não financeiras e financeiras), como o DPO e a regra boba já fazem. O corte sai só da distribuição do sinal no ano, sem o gabarito.
- **A fração: duas opções, descritas só com exercícios até 2023, por ano e grupo.** (i) O decil superior em cada sinal, com a taxa da união resultante (empresa-anos com pelo menos um alerta) e a sobreposição entre os sinais. (ii) O alerta nos 10% do ano, dentro do grupo, com as empresa-anos ordenadas pelo maior percentil entre os sinais calculáveis, a mesma taxa da regra boba, com quantas vezes cada sinal define esse máximo. A escolha fica no pré-registro do v2, só com essas descrições. Recomendação provisória: (ii), porque fixa a taxa de alerta na da regra boba e torna a comparação com ela direta.

### 1.4 Desvio de Benford ajustado

- **Origem.** O item 9 da seção g do [plano do estudo 2](estudo-2-plano.md), a partir do AB-score de Chakrabarty et al. (2025), em versão sem rótulo ([referências](referencias.md)).
- **Falha do v1 que ele responde.** A cobertura: o M-score ficou sem valor em 1.548 de 6.938 empresa-anos (22,3%), e o desvio de Benford dá para calcular em quase todas.
- **O quê.** O desvio médio absoluto da distribuição do primeiro dígito dos números da versão usada da DFP, normalizado dentro do ano por faixas de quantidade de números (o `B_Input` do artigo) e pelo ano (o `B_Year`); alerta no decil superior do ano, dentro de cada grupo. Os coeficientes do artigo, estimados com AAER dos EUA, não são usados.
- **Escolha de entrada.** Só os números de BPA, BPP, DRE e DFC, os quatro demonstrativos que existem tanto nos zips da DFP quanto nos documentos do ENET: assim, toda empresa-ano é medida sobre o mesmo conjunto de demonstrativos, venha a versão de onde vier.
- **Antes de decidir:** descrever, só com exercícios até 2023, a distribuição da quantidade de números por empresa-ano, que define as faixas. No artigo, sozinho, ele alerta demais: entra como sinal complementar, com a mesma fração dos outros.
- **Decisão:** entra também nas financeiras, dentro do grupo. Ele não depende do plano de contas, e hoje as financeiras têm um sinal só.

### 1.5 Accruals discricionários

- **Dá para fazer só com a DFP?** Sim, em parte. O Jones modificado usa os accruals totais, a variação da receita e das contas a receber, o imobilizado e o ativo de t-1, todos na DFP de t (colunas de t e t-1). Precisa também do setor, e o cadastro da CVM traz só o setor atual (`SETOR_ATIV`); o setor de cada ano está no FCA.
- **Decisão: fica fora do v2.** (1) A regressão por setor e ano pede pelo menos 10 empresas por célula, e o estudo 1 avaliou de 408 a 601 não financeiras por ano: com uma divisão por setor, muitas células ficam abaixo de 10, e a escolha da classificação e do tratamento das células pequenas seria um parâmetro livre, sem critério sem rótulo claro; (2) os accruals totais já estão no M-score (o TATA); (3) o prazo até 31/03/2027 não comporta mais um modelo com estimação. Fica para uma versão seguinte, com pré-registro próprio.

### 1.6 F-score de Dechow e outros (2011)

- **Dá para fazer só com a DFP?** Não com as entradas do estudo 2. O modelo 1 usa a variação do ROA e a variação das vendas a caixa, que pedem saldos de t-2 (o ativo médio de t-1 e as contas a receber de t-2). A DFP de t traz só t e t-1; para 2024, o t-2 estaria na DFP de 2023, que não está no branch `estudo-2-dados` (seção 3).
- **Decisão: fica fora do v2.** Além da entrada que falta, os coeficientes foram estimados com AAER dos EUA, o mesmo problema do corte de -1,78, e a maior parte da informação (accruals, contas a receber) já está no M-score.

### 1.7 Fora desta versão

- **ITR (dados trimestrais):** não estão entre as entradas do estudo 2, e o caso que os motivou (IRB, que não pode ser acertado com DFP anual) é financeiro e depende de dados trimestrais de 2024 e 2025 que nunca foram baixados.
- **Aprendizado supervisionado:** precisa de rótulos para treinar, e a regra da seção 2 proíbe usar o gabarito para escolher ou ajustar qualquer coisa; com 13 casos acertáveis no estudo 1, também não haveria com o que treinar.

### 1.8 O que não muda

O DPO e o peso de ganhos não recorrentes ficam como no v1, só com o corte por fração do ano (o DPO já é o decil superior). O M-score continua com os coeficientes de Beneish; muda o corte (1.3) e o DEPI (1.2). A empresa-ano fica em alerta se pelo menos um sinal estiver no topo, como no v1.

## 2. Regra de desenvolvimento

- **Só exercícios até 2023.** O lacre do produto continua em 2023 e 31/12/2024: o código do v2 é escrito e medido com `ULTIMO_EXERCICIO_LIBERADO = 2023`. Nenhum dado de 2024 em diante é lido antes da sessão do lacre do v2.
- **Escolhas só por critérios sem rótulo:** cobertura (fração das empresa-anos em que o sinal é calculável), taxa de alerta (de cada sinal e da união), estabilidade (variação da taxa entre os anos e persistência do alerta na mesma companhia) e testes de correção (exemplo calculado à mão para cada mudança; com todas as mudanças desligadas, o v2 reproduz o v1 nas 9.474 empresa-anos do invariante).
- **O gabarito do estudo 1 não é usado** para escolher nem ajustar nada. O código de desenvolvimento do v2 não lê `data/gabarito_casos.csv` nem importa as métricas do estudo 1; um teste confere.
- **Os acertos do v2 nos casos do estudo 1** aparecem só depois do congelamento, como descrição dentro da amostra, com o rótulo "dentro da amostra de desenvolvimento, não é teste". Nenhum acerto, caso ou alerta por companhia do gabarito é calculado ou mostrado antes disso; as descrições são só agregados por ano e grupo.
- **As escolhas ficam no pré-registro do v2**, antes de qualquer código: a lista fechada de mudanças, a regra sem rótulo que decide cada uma (por exemplo, "entra se a cobertura passar de X%") e a ordem do ranking. Entre o pré-registro e o congelamento, só implementação e testes, sem escolha livre.
- **Descrições sem rótulo, antes do pré-registro (até 10/12/2026),** só com exercícios até 2023: a cobertura do DEPI pela DVA; a cobertura das subcontas de 3.06.02, nos dados abertos e nas versões do ENET; a distribuição da quantidade de números por empresa-ano em BPA, BPP, DRE e DFC; as taxas das opções (i) e (ii) da fração (1.3); e, só com metadados, a distribuição das datas de entrega da DFP de 2023 (recebidas em 2024), para estimar quantas empresa-anos de 2025 ficariam prospectivas com o lacre em 31/01/2027.

## 3. Entradas

A lista do v2 roda só sobre o que já está no branch `estudo-2-dados` e sobre o CDI versionado, os mesmos arquivos da lista do v1, conferidos pelo SHA-256 do manifesto do estudo ([`data/estudo_2_manifesto.csv`](../data/estudo_2_manifesto.csv)). Nenhum arquivo é baixado.

| Entrada | O que traz |
| --- | --- |
| zips da DFP de 2024 e 2025 | BPA, BPP, DRE, DRA, DFC, DMPL e DVA, consolidados e individuais, mais o índice e o parecer |
| zips do FCA de 2024 e 2025 e o cadastro | dados cadastrais, com o setor |
| 26 documentos do ENET | só BPA, BPP, DRE e DFC consolidados, das empresa-anos cuja versão dos dados abertos é posterior ao corte |
| `data/cdi_sgs4389.csv` | o CDI da série SGS 4389, até 31/12/2025 |

| Mudança | Precisa de outra entrada? | Situação |
| --- | --- | --- |
| Juro implícito, subcontas e corte por fração | não | candidata |
| Juro implícito pelas notas explicativas | sim (notas) | fora |
| DEPI pela DVA | não (a DVA está nos zips); nas empresa-anos do ENET, fica como no v1 | candidata |
| Cortes sem rótulo | não | candidata |
| Desvio de Benford ajustado | não (só BPA, BPP, DRE e DFC) | candidata |
| Accruals discricionários | não (DFP e cadastro ou FCA) | fora por recomendação (1.5) |
| F-score | sim (saldos de t-2, da DFP de t-1) | fora |
| ITR | sim | fora |
| Aprendizado supervisionado | sim (rótulos) | fora |

No desenvolvimento, as entradas são as do estudo 1 (os dados abertos de 2010 a 2023, conferidos pelo manifesto dos brutos, e o mesmo CDI).

## 4. Rascunho do texto da emenda ao estudo 2

Rascunho com as decisões de Roberto; não é registrado nesta rodada. Será a emenda 5: a emenda 4 foi reservada para a contingência do ENET e não foi usada nem registrada, e o texto da emenda 5 diz isso.

> **Emenda 5 · (data) · braço do motor v2 na avaliação secundária (antes de qualquer valor de 2024 ou 2025 calculado pelo v2)**
>
> A emenda 4 foi reservada para a contingência do ENET (as tabelas de 07/11/2026 que não pudessem ser baixadas de novo) e não foi usada nem registrada: as 26 tabelas foram baixadas de novo, todas idênticas.
>
> 1. **Braço novo.** O motor v2, congelado com um registro de SHA-256 próprio (sem mudar `docs/estudo_2_codigo_congelado.json`), calcula a lista dos exercícios de 2024 e 2025 sobre os mesmos arquivos de entrada da lista do v1 (o branch `estudo-2-dados`, conferido pelo SHA-256 do manifesto, e `data/cdi_sgs4389.csv`). Nenhum arquivo é baixado. Meta: congelado até 25/01/2027 e lista lacrada até 31/01/2027. Reserva, se a meta não for cumprida: congelado até 31/03/2027 e lista lacrada até 15/04/2027, com o rótulo "não prospectivo". Sem a reserva cumprida, o braço não existe, sem outra prorrogação.
> 2. **O que não muda.** Tudo o que este pré-registro diz do v1: a lista lacrada, o registro, os desfechos, as métricas, a semente, os critérios, as datas e as previsões da seção 7.3. O relatório traz primeiro o v1, exatamente como pré-registrado, e depois o braço do v2.
> 3. **Métricas do braço.** As da seção 7.2, com a mesma semente (20270531) e as mesmas 10.000 reamostragens por companhia, pelas funções congeladas de `chiocca/v2/estudo2/secundaria.py`, sem mudar nenhuma linha. A comparação pareada usa as empresa-anos avaliadas pelo v1: como o sorteio depende só da semente e do conjunto de companhias, as reamostragens são as mesmas do v1. As empresa-anos que só o v2 consegue avaliar (por exemplo, pelo desvio de Benford) são relatadas à parte, só como descrição. Comparações: a DR do v2, com o mesmo critério de "associação positiva"; a diferença entre o v2 e a regra boba, pareada; a diferença entre o v2 e o v1, pareada: "o v2 separa melhor que o v1" só se o limite inferior do intervalo unilateral de 95% ficar acima de zero; senão, sem vencedor declarado. As métricas de ranking da seção 7.2 usam a ordem do v2 definida no pré-registro dele. As previsões do v2 são escritas no pré-registro dele, antes do congelamento.
> 4. **Abertura do lacre só para o script do v2.** Uma constante própria no bloco do estudo de `chiocca/v2/lacre.py` (o bloco fica fora do hash do registro do v1), lida só pelo script do v2. `ULTIMO_EXERCICIO_LIBERADO` continua 2023, e a data máxima do produto continua 31/12/2024. O teste que restringe as constantes do estudo passa a aceitar o script do v2, e só ele.
> 5. **Lacre e carimbo.** Como na seção 8: o mesmo formato de arquivo, duas execuções com o mesmo SHA-256, o SHA-256 num commit enviado ao GitHub, o carimbo do OpenTimestamps (e o `ots upgrade` depois da confirmação), o arquivo para Roberto sem cifra e a cópia apagada do ambiente na mesma sessão. Na avaliação, o recálculo byte a byte é a prova.
> 6. **Roberto sem abrir a lista.** Como na seção 5: Roberto não abre o arquivo do v2 nem roda o código dele antes de congelar a parte 2 do gabarito, porque o braço do v2 também tem o descritivo do desfecho primário (item 7). Na avaliação secundária, a lista do v2 é recalculada pelo script, e só saem as medidas agregadas da seção 7.2; o agente não descreve nenhum alerta do v2 por companhia.
> 7. **Casos da parte 2 públicos antes do lacre do v2.** Para o braço do v2, a parte 2 se divide pela data do commit com o SHA-256 da lista do v2: a parte 2a, com os casos cujo documento qualificador (emenda 1, item 1) é público entre o congelamento da parte 1 (19/11/2026) e esse commit, e a parte 2b, com os públicos depois dele e até 31/12/2029. No desfecho primário (descritivo), os acertos do v2 são relatados separados nas partes 2a e 2b; a comparação com o v1 usa só a 2b, e a 2a vem com o rótulo "público antes do lacre do v2". Para o v1, nada muda: a parte 2 continua inteira.
> 8. **Rótulo prospectivo por empresa-ano.** Uma empresa-ano de 2025 conta como prospectiva para o v2 se a primeira entrega da DFP de 2026 dela (o menor DT_RECEB do índice da CVM) é posterior ao commit com o SHA-256 da lista do v2. As de 2024 são não prospectivas nos dois braços: as republicações de 2024 (na DFP de 2025, corte de 30/04/2026) eram públicas antes deste plano. O braço do v2 é relatado no total e no subconjunto prospectivo; se valer a reserva, o braço inteiro leva também o rótulo "não prospectivo".

## 5. Calendário

| Etapa | Data-limite | Se atrasar |
| --- | --- | --- |
| Este rascunho e as decisões de Roberto | 22/11/2026 | — |
| Descrições sem rótulo, só com exercícios até 2023 (seção 2) | 10/12/2026 | A mudança cuja descrição não estiver pronta no pré-registro do v2 não entra. |
| Pré-registro do motor v2 (lista fechada de mudanças, critério de cobertura do 1.1 (a), opção da fração, regras sem rótulo, ordem do ranking, previsões) e emenda 5 ao estudo 2, registrados | 20/12/2026 | As datas da meta e da reserva não mudam. Sem o pré-registro e a emenda registrados antes da sessão do lacre, o v2 não entra. |
| Meta: v2 congelado (código, registro de SHA-256, exemplo calculado à mão, invariante do v1 com as mudanças desligadas) | 25/01/2027 | Vale a reserva. |
| Meta: sessão do lacre (abertura só para o script do v2, conferência dos SHA-256 das entradas, cálculo duas vezes, SHA-256 num commit, carimbo, arquivo para Roberto, cópia apagada) | 31/01/2027 | Vale a reserva. |
| Reserva: v2 congelado | 31/03/2027 | Não entra, sem outra prorrogação. |
| Reserva: sessão do lacre, com o rótulo "não prospectivo" | de 01/04/2027 a 15/04/2027 | Não entra, sem outra prorrogação. Se os calendários do OpenTimestamps não responderem, Roberto carimba pelo site, como na seção 8 do pré-registro; o commit com o SHA-256 vale como lacre. |
| Corte da DFP de 2026 | 30/04/2027 | data do pré-registro, não muda |
| `ots upgrade` do carimbo da lista do v2 | depois da confirmação no Bitcoin | sem efeito no estudo |
| Avaliação secundária única, os dois braços na mesma sessão (o v1 primeiro, como pré-registrado) | a partir de 31/05/2027 | "A partir de": a data pode passar sem efeito em nenhum braço. |

## 6. Riscos e próximo passo

- **Prospectivo só em parte.** Mesmo com a meta, as empresa-anos de 2024 são não prospectivas, e as de 2025 só contam como prospectivas pela data de entrega da DFP de 2026 (seção "Objetivo"). Por isso as escolhas ficam fechadas no pré-registro do v2 (20/12/2026), e o agente não lê nenhum dado de 2024 em diante no desenvolvimento. A descrição das datas de entrega da DFP de 2023 estima o tamanho do subconjunto prospectivo.
- **Pouco tempo.** Para a meta, de 20/12/2026 a 25/01/2027 há cerca de cinco semanas para implementar três mudanças e os testes; para a reserva, cerca de quatorze semanas. Se alguma mudança não estiver pronta, ela sai e o v2 congela sem ela; o v2 não espera.
- **Próximo passo, depois deste estudo: um teste prospectivo próprio do v2** (decisão de Roberto, 22/11/2026): uma lista dos exercícios de 2026 (DFP de 2026, depois do corte de 30/04/2027), lacrada antes de qualquer republicação dela ser pública, com a republicação na DFP de 2027 (corte de 30/04/2028) como desfecho, com pré-registro próprio depois. Por ora, fica só neste plano.

## Decisões de Roberto (22/11/2026)

| Decisão | O que ficou decidido |
| --- | --- |
| 1. Tentar o v2 no estudo 2 | sim |
| 2. Calendário | meta prospectiva (congelado até 25/01/2027, lacre até 31/01/2027) e reserva (31/03/2027 e 15/04/2027, com o rótulo "não prospectivo"), sem outra prorrogação; rótulo prospectivo por empresa-ano de 2025, pelo DT_RECEB da DFP de 2026; 2024 não prospectivo nos dois braços; descrições até 10/12/2026; pré-registro do v2 e emenda até 20/12/2026 |
| 3. Mudanças | 1.2, 1.3 e 1.4; 1.1 (b) pelo 1.3; 1.1 (a) só com cobertura suficiente das subcontas, pelo critério proposto e fechado no pré-registro; 1.5 e 1.6 fora |
| 4. Fração do corte | descrever as opções (i) e (ii) só com exercícios até 2023; a escolha fica no pré-registro, só com essas descrições; recomendação provisória: (ii) |
| 5. Benford nas financeiras | sim, dentro do grupo |
| 6. Emenda | emenda 5; o texto registra que a emenda 4 foi reservada para a contingência do ENET e não foi usada nem registrada |
| 7. Conjunto avaliado | a comparação pareada usa as empresa-anos avaliadas pelo v1; as que só o v2 avalia ficam à parte, só como descrição |
| 8. Acertos do v2 nos casos do estudo 1 | só depois do congelamento, como descrição dentro da amostra; nada por companhia do gabarito antes disso |
| 9. Teste prospectivo próprio do v2, com os exercícios de 2026 | sim, com pré-registro próprio depois; por ora, só no plano |
