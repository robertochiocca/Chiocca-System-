# Estudo 2: rascunho do plano

Rascunho de 15/11/2026, pedido por Roberto, para decisão. **Não é o pré-registro.** Foi escrito antes de qualquer código do estudo 2 e sem tocar em nenhum valor de exercício de 2024 em diante. Os números vêm de [`docs/estudo_2_numeros.json`](estudo_2_numeros.json), gerado por `python -m chiocca.v2.estudo2_numeros`: dos exercícios de 2024 e 2025, só metadados (quantas companhias entregaram a DFP e quando, lidos do índice de cada arquivo da CVM, sem baixar as demonstrações); o resto vem do estudo 1 e dos exercícios de 2010 a 2022, dentro do lacre.

O que já está decidido e não muda aqui: o lacre (`ULTIMO_EXERCICIO_LIBERADO = 2023` e data máxima de 31/12/2024), o monitor só com metadados para o que foi entregue depois de 31/12/2024, o motor v1 sem mudança como primeiro teste (roadmap), nenhuma lista pública ordenada por alerta e "alerta, não acusação".

Cada seção traz as opções, o que cada uma permite concluir e a minha recomendação. A lista das decisões está no fim.

## a. Desenho

**Opção A, prospectiva (a proposta de Roberto).** Depois do pré-registro e do commit que abre o lacre, o motor v1 sem mudança calcula os alertas dos exercícios de 2024 e 2025 numa data fixa. A lista fica lacrada (só o SHA-256 vai para o git) e é comparada, numa data de avaliação definida no pré-registro, com os casos que vieram a público até lá.

**Opção B, retrospectiva, só com os casos já públicos hoje.** O mesmo cálculo, comparado só com os casos públicos na data do pré-registro.

**Opção C, a A com uma divisão pré-registrada.** Os casos que já eram públicos na data do lacre e os que vierem a público depois dele são contados juntos e também separados.

| | A, prospectiva | B, só casos públicos hoje | C, A com a divisão |
| --- | --- | --- | --- |
| Casos acertáveis esperados (taxa média) | 1,6 até 31/12/2029 | 0,9 hoje | os mesmos da A |
| Quando sai o resultado | na data de avaliação (anos) | logo depois da abertura | os dois momentos |
| Risco de contaminação | baixo: o gabarito dos casos novos é escrito depois | maior: Roberto e o Claude podem já conhecer casos de 2024 e 2025 | a parte de antes do lacre fica separada |
| O que permite concluir | se o alerta veio antes de o caso virar público, sem nenhuma escolha feita depois | o mesmo, com menos casos e com o gabarito escrito sabendo o que já é público | as duas coisas, sem misturar |

O motor não muda, então conhecer casos antigos não ajusta o motor; o risco da opção B está no gabarito (que casos entram e com que período), não no cálculo.

**Data fixa do cálculo.** Proponho a regra do estudo 1: cada exercício na versão da DFP pública no corte (último dia do quarto mês depois do exercício), 30/04/2025 para 2024 e 30/04/2026 para 2025, com as versões do ENET. As duas datas já passaram, e o cálculo é reprodutível. A alternativa, uma data só para os dois exercícios, usaria para 2024 versões reentregues depois do corte e quebraria a comparação com o estudo 1.

**Recomendação: C**, com o cálculo nas datas de corte do estudo 1 e uma data de avaliação única para o desfecho primário, sem olhar antes (seção c). O desfecho secundário tem data própria, mais cedo, e publica só contagens agregadas (seção b).

## b. Desfecho

**Primário: irregularidade contábil que vem a público**, como no estudo 1: processo sancionador da CVM sobre as demonstrações, fraude ou erro admitido em fato relevante, ou determinação de refazimento. No estudo 1, o tempo entre o fim do período afetado e a data pública foi de 12,4 meses na mediana nos 13 casos acertáveis (de 4,3 a 56,9) e de 18,2 meses nos 36 casos com período e data (de -24,4 a 118,1; o mínimo negativo é um caso que veio a público antes do fim do período afetado); 92% desses casos ficaram públicos em até 60 meses. A mediana de 19,4 meses do estudo 1 é outra medida: vai da entrega da primeira DFP em alerta até a data pública, só nos 7 acertos. **Permite concluir:** se o motor alertou antes de a irregularidade vir a público, que é a pergunta do produto. Com poucos casos, é uma conferência descritiva, não um teste estatístico (seção c).

**Secundário: republicação relevante do exercício t no comparativo da DFP t+1**, pela regra de materialidade do produto (diferença do grupo (a), totais e linhas-chave, acima de 1% do ativo total da versão usada). De 2010 a 2022, 1.407 de 8.084 empresa-anos (17,4%) tiveram diferença destacada; de 2013 a 2022, a taxa foi de 14,2% ao ano. Essa regra inclui reclassificações e mudanças de perímetro, que não indicam erro. Uma definição mais estreita, a diferença destacada no patrimônio líquido ou no lucro líquido, ocorreu em 439 empresa-anos de 2010 a 2022 (5,4%), com taxa de 4,7% de 2013 a 2022. O desfecho aparece cedo: o de 2024 já está no comparativo da DFP de 2025 (entregue em 2026), e o de 2025 estará no da DFP de 2026 (até 30/04/2027). **Permite concluir:** se o alerta está associado a uma republicação relevante depois, isto é, à qualidade ou à instabilidade da informação contábil; não permite falar em fraude. Tamanho, setor, dificuldade financeira e mudanças de perímetro confundem a associação, por isso a comparação é com a regra boba do estudo 1 (decil mais endividado), lado a lado.

Para o exercício de 2024, o desfecho secundário já existe: o pré-registro precisa proibir ler o comparativo da DFP de 2025 antes de a lista estar lacrada.

**Recomendação:** primário como no estudo 1, com a determinação de refazimento da CVM incluída; secundário pela definição estreita (patrimônio líquido ou lucro), com a regra larga do produto só como descritivo, avaliado depois de 30/04/2027 e publicado só em contagens agregadas. A definição estreita tem menos eventos e menos poder (seção c), mas mede melhor o que interessa; a larga tem mais poder e mais ruído.

## c. Poder

**Quantas empresa-anos.** Pelos metadados, 709 companhias entregaram a DFP de 2024 (683 com a primeira entrega até 30/04/2025) e 671 a de 2025 até agora (649 até 30/04/2026); a de 2023 teve 732 (701 até 30/04/2024). No estudo 1, cerca de 600 não financeiras por ano foram avaliadas (597, 596 e 601 de 2021 a 2023). Espero perto de 1.200 empresa-anos para os dois exercícios.

**Quantos casos acertáveis esperar.** A conta usa três taxas de casos acertáveis por exercício, tiradas do gabarito do estudo 1: baixa, 0,25 (o observado de 2016 a 2023, ainda incompleto, porque casos recentes podem não ter vindo a público); média, 0,93 (2010 a 2023); alta, 2,2 (2011 a 2015). Multiplica cada taxa pela fração dos casos do estudo 1 que já estavam públicos com o mesmo atraso.

| Data de avaliação | Fração pública (2024; 2025) | Esperados, taxa baixa | média | alta |
| --- | --- | --- | --- | --- |
| 15/11/2026 (hoje) | 0,61; 0,33 | 0,2 | 0,9 | 2,1 |
| 31/12/2027 | 0,67; 0,61 | 0,3 | 1,2 | 2,8 |
| 31/12/2028 | 0,81; 0,67 | 0,4 | 1,4 | 3,2 |
| 31/12/2029 | 0,92; 0,81 | 0,4 | 1,6 | 3,8 |
| 31/12/2030 | 0,97; 0,92 | 0,5 | 1,8 | 4,2 |

**Quantos acertos distinguem do acaso.** Com a taxa de alerta de cerca de 50% do estudo 1, cada caso é acertado ao acaso com chance de 0,5. Com até 4 casos, nenhum resultado distingue do acaso com 5% de significância: 4 de 4 acontece ao acaso em 6,25% das vezes.

| Casos acertáveis | Acertos necessários | Chance ao acaso | Poder se a taxa real fosse 0,75 | se fosse 0,9 |
| --- | --- | --- | --- | --- |
| 1 | nenhum resultado basta | 0,5000 | 0 | 0 |
| 2 | nenhum resultado basta | 0,2500 | 0 | 0 |
| 3 | nenhum resultado basta | 0,1250 | 0 | 0 |
| 4 | nenhum resultado basta | 0,0625 | 0 | 0 |
| 5 | 5 | 0,0312 | 0,237 | 0,590 |
| 6 | 6 | 0,0156 | 0,178 | 0,531 |
| 8 | 7 | 0,0352 | 0,367 | 0,813 |
| 10 | 9 | 0,0107 | 0,244 | 0,736 |
| 13 | 10 | 0,0461 | 0,584 | 0,966 |
| 15 | 12 | 0,0176 | 0,461 | 0,944 |
| 20 | 15 | 0,0207 | 0,617 | 0,989 |
| 30 | 20 | 0,0494 | 0,894 | 1,000 |

Se o período afetado de um caso cobre os dois exercícios, a chance de pelo menos um alerta ao acaso sobe para 0,75 com anos independentes e para 0,87 com a persistência do estudo 1 (73,8% das empresa-anos em alerta também estavam em alerta no ano anterior), e a barreira fica mais alta.

**O que o teste permite concluir.** Até 2030, o esperado é de 2 casos acertáveis ou menos na taxa média: o desfecho primário não distingue o motor do acaso. Ele serve como conferência descritiva, caso a caso, com a antecedência de cada acerto. Um resultado como 0 de 3 é informativo, mas fraco. O desfecho secundário tem mais poder: com 1.200 empresa-anos, metade em alerta e a taxa média de republicação estreita de 4,7%, o poder para uma razão de taxas de 1,5 é de 0,45 e, para 2,0, de 0,82; pela regra larga (14,2%), de 0,88 e 1,00. A conta supõe empresa-anos independentes; com dois exercícios por companhia, o poder real é menor.

**Recomendação:** desfecho primário avaliado em 31/12/2029 (60 e 48 meses depois dos exercícios, quando 92% e 81% dos casos do estudo 1 já eram públicos), descrito caso a caso, sem teste contra o acaso como critério principal; o teste estatístico fica no desfecho secundário.

## d. Guarda da lista lacrada

**O arquivo.** Um CSV em formato fixo (UTF-8, quebras de linha LF, ordenado por código CVM e exercício), com todas as empresa-anos avaliadas, em alerta ou não, e os sinais de cada uma; no cabeçalho, o commit do código e o SHA-256 de cada arquivo da CVM usado. Ter todas as empresa-anos evita discussão depois sobre quem foi avaliado.

**A prova de que não mudou (opções).**
1. O SHA-256 num commit enviado ao GitHub. O GitHub registra a hora do envio e do CI nesse commit, fora do meu ambiente. A data do commit sozinha não prova nada, porque pode ser escrita à mão.
2. Um carimbo de tempo independente do hash (OpenTimestamps, gratuito, ou uma autoridade de carimbo de tempo RFC 3161).
3. Recalcular a lista na avaliação: o motor é determinístico, e a lista sai do código congelado e dos arquivos da CVM do manifesto (as versões no corte vêm do ENET). Para não depender da CVM mudar os arquivos, os zips usados ficam arquivados, com o SHA-256 no manifesto.

**Onde fica o arquivo.** Cifrado com a chave pública de Roberto (age ou GPG); só a chave pública entra no repositório. O arquivo cifrado vai para dois lugares que Roberto controla (por exemplo, um repositório privado e um drive), e a cópia em texto é apagada do ambiente, que é temporário. A chave privada nunca entra no ambiente.

**O limite.** O código e os dados são públicos: qualquer pessoa, inclusive quem escreve o gabarito, pode recalcular a lista. O lacre impede mudar a lista, não impede descobrir. A cegueira do gabarito é de procedimento: quem o escreve se compromete a não rodar o código, e os critérios do gabarito são objetivos, por documento.

**Recomendação:** as opções 1 e 3, mais o OpenTimestamps (opção 2), que custa pouco; o arquivo cifrado com Roberto, em dois lugares; os zips arquivados.

## e. Gabarito

**Fontes.** (1) Processos sancionadores da CVM sobre as demonstrações (normas contábeis e informação financeira), com a data da instauração ou do primeiro documento público; (2) fatos relevantes que admitem erro ou fraude contábil (o conteúdo do IPE entregue depois de 31/12/2024 continua sem ser lido no meu ambiente; quem lê é Roberto, fora dele); (3) determinações de refazimento ou republicação da CVM; (4) para financeiras, o Banco Central.

**Critério**, como no estudo 1: `data_publica` é a primeira data pública documentada; o período afetado vem dos exercícios citados na decisão ou no fato relevante; caso sem documento com os anos não conta como acertável. Acertável: o período afetado inclui 2024 ou 2025, a DFP desse exercício era pública no corte e antes da data pública, e a empresa-ano está na amostra. Ficam de fora os casos sem distorção nas demonstrações (só negociação com informação privilegiada ou governança). Cada caso com duas fontes, como na emenda 9 do estudo 1.

**Cegueira.** Concordo com a proposta: Roberto escreve o gabarito com o Claude (claude.ai), fora deste ambiente, sem acesso à lista e sem rodar o código, como os casos guardados do leitor. Recomendo duas partes: a parte 1, com os casos já públicos na data do lacre, escrita e congelada (SHA-256 num commit) antes de abrir o lacre; a parte 2, com os casos que vierem a público até a data de avaliação, escrita depois dela e congelada antes de abrir a lista.

## f. Abertura do lacre

**O que precisa estar pronto antes, nesta ordem.**
1. O pré-registro do estudo 2 num commit, com o hash anotado no commit seguinte, como no estudo 1 e no leitor.
2. A parte 1 do gabarito congelada (SHA-256 num commit).
3. A chave pública de Roberto no repositório; o formato da lista e o script que a calcula e lacra, congelados com o SHA-256 de cada arquivo e um teste que acusa mudança; o motor v1 sem mudança (o invariante passa, e os arquivos do motor entram no registro de hashes).
4. Só então baixar as DFP de 2024 e 2025 (e as versões do ENET nos cortes), com o SHA-256 de cada arquivo no manifesto.

**O commit que abre o lacre (opções).**
- **Global:** `ULTIMO_EXERCICIO_LIBERADO` de 2023 para 2025 e a data máxima para 30/04/2026. É simples, mas abre também o produto: a API e a demonstração passariam a mostrar 2024 e 2025, e uma demonstração regerada mostraria alertas desses anos para as companhias do gabarito, o que publicaria parte da lista antes da avaliação.
- **Só para o estudo (recomendada):** uma constante própria do estudo em `chiocca/v2/lacre.py` (por exemplo, `ESTUDO_2_EXERCICIOS = (2024, 2025)`), lida só pelo script congelado do estudo. O produto continua com 2023 e 31/12/2024 até a avaliação, e a regra do monitor (só metadados depois de 31/12/2024) continua para o produto. O teste do lacre passa a conferir que nada além do script do estudo lê 2024 e 2025.

Depois do commit, na mesma sessão: calcular a lista, gravar o SHA-256 num commit, cifrar o arquivo para Roberto, entregar o arquivo cifrado e apagar a cópia em texto. Nada mais de 2024 e 2025 é calculado até as datas de avaliação.

## g. Melhorias depois do teste limpo

Cada uma com pré-registro próprio, comparada com o motor v1 sem mudança e com a regra boba, e avaliada em dados que não serviram para desenvolvê-la (exercícios de 2026 em diante ou casos guardados novos). Ordem recomendada:

1. **Métricas, sem mudar o motor:** antecedência pré-registrada, lift e precisão no topo, NDCG@k, bootstrap pareado por empresa, intervalo de 24 meses e a regra para casos de vários anos. Recomendo que já entrem no pré-registro do teste limpo, como métricas secundárias.
2. **Juro implícito:** separar da despesa financeira a variação cambial e os juros de arrendamento, pelas notas. É a maior fonte de alertas do estudo 1 (59,8% das empresa-anos em alerta).
3. **DEPI pela DVA:** o M-score ficou sem valor em 1.548 de 6.938 empresa-anos, e em 7 dos 13 casos acertáveis.
4. **Accruals discricionários** (Jones modificado e modelo de margem, com pelo menos 10 empresas por setor e ano), Dechow e Dichev com defasagem e lucro logo acima de zero.
5. **F-score de Dechow e outros (2011).**
6. **Cortes recalibrados para o Brasil ou por setor.**
7. **Dados trimestrais (ITR)**, para casos como o do IRB.
8. **Aprendizado supervisionado**, só exploratório.

## Decisões de Roberto (resumo)

| Decisão | Opções | Minha recomendação |
| --- | --- | --- |
| Desenho | A, B ou C | C, com o cálculo nas datas de corte do estudo 1 |
| Desfecho primário | como no estudo 1, com ou sem refazimento | como no estudo 1, com a determinação de refazimento |
| Desfecho secundário | regra larga do produto ou definição estreita | definição estreita (patrimônio líquido ou lucro), a larga como descritivo |
| Data de avaliação do primário | 31/12/2027 a 31/12/2030 | 31/12/2029, sem olhar antes |
| Data do secundário | depois de 30/04/2027 | depois de 30/04/2027, só contagens agregadas |
| Guarda da lista | hash, carimbo de tempo, arquivo cifrado, recálculo | hash, OpenTimestamps, arquivo cifrado com Roberto e recálculo |
| Gabarito | quem escreve e quando | Roberto com o Claude, fora do ambiente, em duas partes |
| Abertura do lacre | global ou só para o estudo | só para o estudo |
| Melhorias | ordem e quando | métricas no próprio teste limpo; depois juro implícito e DEPI |
