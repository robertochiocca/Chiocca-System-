# Pré-registro do estudo 2

> **Registrado em 15/11/2026.** Redigido pelo agente com as decisões de Roberto e revisado por Roberto com o Claude (claude.ai), que aprovou o texto com os ajustes da seção 11. O commit que introduz este arquivo é o registro, e o hash dele é anotado no commit seguinte, sem mudar nenhuma regra, como no estudo 1 e no leitor. Registrar não abre o lacre: nada dos exercícios de 2024 e 2025 é baixado ou calculado antes de a parte 1 do gabarito ser congelada (seção 9).
>
> Por que isso existe: o motor v1 foi construído e medido com os exercícios de 2010 a 2023. Os de 2024 e 2025 ficaram lacrados desde o começo (`chiocca/v2/lacre.py`) justamente para um teste limpo, em dados que ninguém olhou. Decidir antes como o teste é feito é o que torna o resultado confiável.

Base: o rascunho do plano ([`docs/estudo-2-plano.md`](estudo-2-plano.md)), com os números de [`docs/estudo_2_numeros.json`](estudo_2_numeros.json), e o pré-registro do estudo 1 ([`docs/pre-registro.md`](pre-registro.md)), cujas regras de cálculo valem aqui sem mudança.

## 1. Perguntas

1. **Primária.** Com dados públicos disponíveis na época, o motor v1, sem nenhuma mudança, alertou para as irregularidades contábeis dos exercícios de 2024 e 2025 antes de elas virem a público, até 31/12/2029?
2. **Secundária.** As empresa-anos em alerta em 2024 e 2025 tiveram mais republicações relevantes no exercício seguinte do que as fora de alerta? E a regra boba do estudo 1, lado a lado?

## 2. Amostra

- **Empresas:** todas as companhias abertas com DFP de 2024 ou de 2025 na CVM, financeiras e não financeiras, incluindo as que tiverem o registro cancelado depois, com os dois grupos do estudo 1 (não financeiras: M-score, DPO e juro implícito; financeiras: peso de ganhos não recorrentes).
- **Exercícios:** 2024 e 2025. Pelos metadados do índice da CVM, 683 companhias entregaram a DFP de 2024 até o corte (30/04/2025) e 649 a de 2025 até o corte (30/04/2026). No estudo 1, cerca de 600 não financeiras foram avaliadas por ano.
- **Exclusões:** as do estudo 1, sem mudança (não financeiras sem receita no ano; empresa-anos sem versão pública até o corte; versão da época só individual quando a dos dados abertos é posterior ao corte, emenda 8).
- **Desfecho secundário:** só as não financeiras. Nas financeiras, o plano de contas da DRE é outro, e a conta 3.11 pode não ser o lucro líquido; elas entram só no descritivo.

## 3. Regra: o motor v1 sem mudança

- **Como era na época:** cada empresa-ano usa só a versão da DFP pública no corte, 30/04/2025 para 2024 e 30/04/2026 para 2025, como no estudo 1. Quando a versão dos dados abertos é posterior ao corte, a versão da época vem da rota HTML do ENET, só para o consolidado (emendas 5 e 8 do estudo 1).
- **Sinais e alertas:** os da seção 4 do pré-registro do estudo 1, com as escolhas de cálculo da seção 4.1 e as regras das emendas 1 a 11 que tratam de dados (M > −1,78; salto do DPO no decil superior do ano; juro implícito acima do CDI médio do ano mais 10 p.p.; peso de ganhos não recorrentes no decil superior do ano, nas financeiras). Os decis são calculados dentro de cada exercício, como no estudo 1. O CDI vem da série SGS 4389 do Banco Central (`data/cdi_sgs4389.csv`, que já vai até 31/12/2025).
- **Código:** o do motor v1 como está no commit de registro, o mesmo que reproduz o estudo 1 no invariante (9.474 de 9.474 empresa-anos). Os arquivos do motor e o script do estudo entram num registro de SHA-256, com um teste que acusa qualquer mudança. Nenhuma linha do motor muda neste estudo.

### 3.1 Dados e download

- **Já existe no ambiente:** os zips de DFP de 2024 a 2026 foram baixados em 07/11/2026, com o resto dos dados abertos do estudo 1, e estão em `data/brutos/cvm/` (fora do git), com o SHA-256 em `data/manifesto_brutos.csv`. Nenhum valor deles foi lido: o armazém só tem os exercícios de 2010 a 2023, e o lacre recusa qualquer exercício acima de 2023 (`tests/test_v2_lacre.py`). Os metadados do índice da DFP de 2024 e 2025 (quem entregou e quando) foram lidos pelo monitor e pelo rascunho do plano, sem valores.
- **Na sessão de abertura (seção 9):** os zips de DFP de 2024 e 2025 são baixados de novo, na versão da CVM do dia, com tamanho e SHA-256 no manifesto, porque o ambiente é temporário e os arquivos da CVM mudam com as reentregas. A regra da versão da época dá o mesmo resultado com os arquivos de 07/11/2026 ou com os do dia: o que mudar entre eles vem do ENET.
- **ENET, volume e ritmo:** só os documentos das empresa-anos cuja versão dos dados abertos é posterior ao corte e que têm consolidado. Pelos metadados, 139 companhias têm mais de uma versão da DFP de 2024 e 76 da de 2025: é o teto, porque parte das reentregas foi antes do corte. No estudo 1, foram 390 documentos em 14 exercícios, cerca de 28 por exercício. Espero entre 50 e 250 documentos. O ritmo é o do estudo 1 (`chiocca/enet.py`): uma requisição por vez; por documento, a página do documento (até 10 tentativas, com 2 segundos entre elas) e as 4 tabelas (BPA, BPP, DRE e DFC), com 1 segundo entre elas; até 3 novas tentativas por documento, com espera de 5, 10 e 15 segundos; identificador de cliente genérico. São cerca de 6 a 10 segundos por documento, ou de 5 a 40 minutos ao todo, e alguns MB no cache (`data/cache/enet/`, fora do git).
- **Arquivo dos dados:** os dois zips, as tabelas do ENET e o manifesto vão para um branch órfão `estudo-2-dados` neste repositório, enviado sem force push, como o `gh-pages` (autorizado por Roberto em 15/11/2026). Antes da sessão de abertura, confere-se o tamanho de cada arquivo que vai para o branch (os zips da DFP de 2024 e 2025 e, na avaliação secundária, o de 2026): o GitHub recusa arquivos acima de 100 MB, e, se algum passar de 95 MB, o agente propõe outra forma de arquivar, com o SHA-256 no manifesto, e para antes de abrir o lacre. Quem clona o repositório inteiro leva também esse branch, como o `gh-pages` (README). O SHA-256 de cada arquivo fica no manifesto do estudo, versionado no branch de desenvolvimento. Na avaliação secundária, o zip da DFP de 2026 entra no mesmo branch.

## 4. Desfechos

### 4.1 Primário: irregularidade contábil que vem a público

- Um caso do gabarito (seção 5) cujo período afetado inclui 2024 ou 2025 e cuja data pública cai até 31/12/2029. Os casos se dividem em duas partes: a parte 1, com os casos públicos até a data em que ela é congelada (o commit com o SHA-256), e a parte 2, com os que vierem a público depois dessa data e até 31/12/2029.
- **Acerto:** como no estudo 1, a empresa entrou em alerta em pelo menos um exercício do período afetado (2024 ou 2025), usando só a versão pública no corte e antes da data pública. Se a data pública cai antes de 30/04/2026, só a DFP de 2024 pode contar.
- **Antecedência:** meses entre a entrega da primeira DFP em alerta no período afetado e a data pública, como na análise da seção 5 das análises do estudo 1, agora pré-registrada.

### 4.2 Secundário: republicação relevante

- **Republicação relevante (definição estreita, a do teste):** na DFP t+1, na versão pública no corte de t+1 (30/04/2026 para t = 2024; 30/04/2027 para t = 2025), o comparativo de t tem diferença destacada no patrimônio líquido (BPP 2.03) ou no lucro líquido (DRE 3.11) em relação à versão de t usada pelo motor. "Destacada" é a regra de materialidade do produto (`chiocca/v2/comparativo.py`): diferença acima da tolerância e, em valor absoluto, acima de 1% do ativo total da versão usada de t.
- **Regra larga (só descritivo):** diferença destacada em qualquer linha do grupo (a) do produto (ativo total, passivo circulante, passivo não circulante, patrimônio líquido, receita, lucro líquido e caixa operacional).
- **Empresa-anos avaliadas:** não financeiras com a versão de t usada pelo motor e uma versão de t+1 no corte de t+1, do mesmo tipo (consolidado ou individual).
- **Taxa esperada:** de 2013 a 2022, 4,7% das empresa-anos tiveram republicação pela definição estreita e 14,2% pela larga.

### 4.3 O comparativo de 2024 dentro da DFP de 2025 (decisão 4)

Para calcular os alertas de 2025, o motor lê a DFP de 2025, que traz o comparativo de 2024: é o dado do desfecho secundário de 2024. Regras:
- o script do estudo lê esses valores só como entrada do motor (os índices de 2025 usam o ano anterior);
- o script não grava nenhuma comparação entre versões, nem entre a versão de 2024 usada e o comparativo de 2024 da DFP de 2025;
- ninguém calcula nem olha a republicação de 2024 antes de a lista estar lacrada (seção 8);
- a comparação só é feita na avaliação secundária, pelo script dela, congelado com o resto.

## 5. Gabarito e cegueira

- **Quem escreve:** Roberto, com o Claude (claude.ai), fora deste ambiente, sem a lista e sem rodar o código, como os casos guardados do leitor. O agente deste ambiente não escolhe nem escreve casos.
- **Fontes:** (1) processos sancionadores da CVM sobre as demonstrações; (2) fatos relevantes que admitem erro ou fraude contábil; (3) determinações de refazimento ou republicação da CVM; (4) para financeiras, o Banco Central. O conteúdo do IPE entregue depois de 31/12/2024 continua sem ser lido neste ambiente: quem lê é Roberto, fora dele.
- **Campos e critério:** os do estudo 1 (`data/gabarito_casos.csv`), mais a parte (1 ou 2) e o tipo `refazimento_cvm`. `data_publica` é a primeira data pública documentada (instauração do processo, fato relevante, ofício de refazimento ou primeira notícia com fonte); o período afetado vem dos exercícios citados no documento; sem documento com os anos, o caso não é acertável. Ficam de fora os casos sem distorção nas demonstrações (só negociação com informação privilegiada ou governança). Cada caso com duas fontes, como na emenda 9 do estudo 1.
- **Parte 1:** os casos públicos até a data em que ela é congelada (o commit com o SHA-256). Escrita depois de este pré-registro ser registrado e congelada antes de abrir o lacre. Pode ser descrita logo depois do lacre, separada dos outros.
- **Parte 2:** os casos que vierem a público depois da data em que a parte 1 foi congelada e até 31/12/2029. Escrita depois de 31/12/2029 e congelada antes de a lista ser aberta para o desfecho primário.
- **Limite da cegueira:** o código e os dados são públicos, e qualquer pessoa pode recalcular a lista; o arquivo da lista fica com Roberto, sem cifra. A cegueira é de procedimento: Roberto se compromete a não abrir o arquivo nem rodar o código antes de congelar cada parte, e os critérios do gabarito são por documento. A descrição da parte 1 logo depois do lacre revela o alerta das companhias dessa parte; se uma delas tiver um caso novo na parte 2, isso fica registrado no relatório.

## 6. Datas

| Etapa | Quando |
| --- | --- |
| Registro deste pré-registro (commit e hash) | depois da revisão de Roberto |
| Parte 1 do gabarito congelada | depois do registro, antes da abertura |
| Abertura do lacre, cálculo e lacre da lista (seções 8 e 9) | numa sessão só, depois da parte 1 |
| Descrição da parte 1 | logo depois do lacre |
| Avaliação secundária, única | numa sessão a partir de 31/05/2027, depois de as DFP de 2026 estarem entregues no corte de 30/04/2027 |
| Gabarito da parte 2 congelado | a partir de 01/01/2030 |
| Avaliação primária | depois da parte 2, com os casos públicos até 31/12/2029 |

Nada é olhado antes dessas datas: nenhuma prévia do desfecho primário e nenhuma conta do secundário antes da avaliação única.

## 7. Testes, métricas e o que conta como resultado

### 7.1 Primário (descritivo)

- Para cada caso acertável: acertado ou não, quais sinais dispararam, em que exercício, e a antecedência.
- Totais: acertos de casos acertáveis, nas partes 1 (casos públicos até o congelamento dela) e 2 (os públicos depois dele e até 31/12/2029), juntas e separadas, e a taxa de alerta de cada exercício.
- A chance de cada total ao acaso (cada caso acertado com a taxa de alerta do seu grupo no exercício) é relatada só como descrição. Com o número esperado de casos (cerca de 1,6 até 31/12/2029 na taxa média do estudo 1), nenhum teste contra o acaso é critério de resultado. As métricas de ranking ficam só descritivas.

### 7.2 Secundário (o teste)

- **Medida principal:** a diferença de risco DR = P(republicação estreita | em alerta) − P(republicação estreita | fora de alerta), nas não financeiras avaliadas dos dois exercícios juntos; também a razão de taxas.
- **As duas empresa-anos de cada companhia:** bootstrap por companhia. Sorteiam-se companhias com reposição, cada uma com as suas empresa-anos de 2024 e 2025; 10.000 reamostragens, com a semente 20270531. O intervalo é o percentil unilateral de 95%.
- **Resultado:** "associação positiva" se o limite inferior do intervalo unilateral de 95% da DR ficar acima de zero; senão, "sem evidência de associação". Com 1.200 empresa-anos e a taxa de 4,7%, o poder aproximado é de 0,45 para uma razão de taxas de 1,5 e de 0,82 para 2,0 (supondo empresa-anos independentes; com o bootstrap por companhia, é menor).
- **Regra boba lado a lado:** o decil mais endividado (passivo total ÷ ativo total) de cada exercício, como no estudo 1, com a mesma DR e o mesmo bootstrap. A comparação é a diferença entre a DR do motor e a da regra boba, com bootstrap pareado (as mesmas reamostragens): "o motor separa melhor que a regra boba" só se o limite inferior do intervalo unilateral de 95% ficar acima de zero; senão, sem vencedor declarado.
- **Métricas de ranking (secundárias deste desfecho):** precisão no topo de 1%, 5% e 10%, lift no topo (precisão no topo ÷ taxa geral) e NDCG@k (k = 1%, 5% e 10% das empresa-anos), com relevância 1 para republicação estreita, reimplementadas em Python pelas definições de Bao et al. (2020, Tabela 3) e conferidas com um exemplo calculado à mão, como no roadmap. Ordem do ranking: número de sinais disparados, depois o M-score (maior primeiro; sem M-score, depois dos que têm), depois o código CVM. Intervalos pelo mesmo bootstrap por companhia; o motor e a regra boba (ordenada pelo endividamento) no mesmo sorteio.
- **Descritivos:** a regra larga do produto, as financeiras e cada exercício separado.

### 7.3 Previsões escritas antes dos dados

- Taxa de alerta das não financeiras entre 40% e 60% em cada exercício, puxada pelo juro implícito, como no estudo 1 (taxa de 49,9%, com 59,8% das empresa-anos em alerta vindas do juro implícito).
- No secundário, espero DR positiva, mas pequena: o juro implícito dispara por causa de variação cambial e arrendamentos, que não têm relação direta com republicação. Em número: razão de taxas entre 1,0 e 1,5 (empresa-anos em alerta contra fora de alerta).

### 7.4 Se o resultado for ruim

O estudo é publicado do mesmo jeito, com o resultado que deu, nas datas da seção 6.

## 8. Guarda da lista lacrada

- **O arquivo:** um CSV em formato fixo (UTF-8, quebra de linha LF, ordenado por código CVM e exercício, números com casas fixas, sem data de geração no conteúdo), com todas as empresa-anos avaliadas, em alerta ou não, os sinais e os valores de cada sinal; no cabeçalho, o commit do código e o SHA-256 de cada arquivo de entrada.
- **A prova:** o SHA-256 do arquivo num commit enviado ao GitHub, e o recálculo na avaliação: o motor é determinístico, e o script congelado, com os arquivos do branch `estudo-2-dados` e as versões do lock (pandas 3.0.5, numpy 2.5.3), tem de gerar o mesmo arquivo, byte a byte. Um teste da sessão de abertura roda o script duas vezes e confere que o SHA-256 é o mesmo. O registro do estudo anota também a versão do Python (3.13.x) e o SHA-256 do `requirements-lock.txt`, e o recálculo usa a mesma versão menor do Python (3.13).
- **Carimbo de tempo:** o ambiente alcança os calendários do OpenTimestamps (conferido em 15/11/2026). Na sessão de abertura, o agente carimba o arquivo de hashes (o SHA-256 da lista e do manifesto) com o `opentimestamps-client` e põe o `.ots` no repositório; numa sessão seguinte, depois da confirmação no Bitcoin, o `.ots` é atualizado (`ots upgrade`). Se os calendários não responderem no dia, Roberto carimba o arquivo de hashes pelo site opentimestamps.org e devolve o `.ots`.
- **Onde fica o arquivo da lista:** vem para Roberto, sem cifra, pelo envio de arquivo da sessão; ele guarda em dois lugares privados (um repositório privado e o Drive). A cópia é apagada do ambiente na mesma sessão. Sem chave age ou GPG: o recálculo é a prova principal.

## 9. Abertura do lacre

**Antes, nesta ordem:**
1. Este pré-registro registrado: commit, com o hash anotado no commit seguinte.
2. Parte 1 do gabarito congelada (SHA-256 num commit).
3. O script do estudo (cálculo da lista e, à parte, o da avaliação secundária) e o registro de SHA-256 dos arquivos do motor e do script, com o teste que acusa mudança; o invariante do estudo 1 passando.

**O commit que abre o lacre, só para o estudo:** uma constante própria em `chiocca/v2/lacre.py` (por exemplo, `ESTUDO_2_EXERCICIOS = (2024, 2025)` e os cortes de cada um), lida só pelo script do estudo. `ULTIMO_EXERCICIO_LIBERADO` continua 2023, e a data máxima do produto continua 31/12/2024: a interface, a API, a demonstração e o monitor (só metadados depois de 31/12/2024) não mudam. Um teste confere que só o script do estudo usa a constante e lê 2024 e 2025. Na avaliação secundária, uma segunda abertura, também só para o estudo, deixa o script dela ler da DFP de 2026 só o comparativo de 2025.

**Na mesma sessão, depois do commit:** baixar os dados (seção 3.1), calcular a lista, conferir o recálculo, gravar o SHA-256 num commit, carimbar, enviar o arquivo para Roberto, apagar a cópia e arquivar os dados no branch `estudo-2-dados`. Nada mais de 2024 e 2025 é calculado até as datas da seção 6.

## 10. O que fica de fora

- Qualquer mudança no motor v1: as melhorias (juro implícito, DEPI pela DVA, accruals discricionários, F-score, cortes recalibrados, ITR, aprendizado supervisionado) entram depois, na ordem do rascunho do plano, cada uma com pré-registro próprio e avaliada em dados que não serviram para desenvolvê-la.
- Usar os exercícios de 2024 e 2025 para desenvolver ou ajustar qualquer coisa.
- Lista pública de empresas em alerta, ou qualquer ordem por alerta, percentil ou escore. Publica-se só o descrito na seção 7: casos do gabarito e contagens agregadas.
- Abrir o produto para 2024 e 2025 antes da avaliação primária.
- Ler neste ambiente o conteúdo dos documentos do IPE entregues depois de 31/12/2024.
- Testes contra o acaso no desfecho primário como critério de resultado.

## 11. Revisão de Roberto (15/11/2026)

Roberto leu o rascunho inteiro (commit `549b7611a4260fa7325a9da70d0be3449fb7e15c`) e aprovou, com estas respostas e ajustes, já incorporados acima:

1. Desfecho secundário só nas não financeiras: de acordo.
2. Ordem do ranking (número de sinais, M-score, código CVM): de acordo.
3. Semente 20270531 e 10.000 reamostragens: de acordo.
4. Avaliação secundária a partir de 31/05/2027: de acordo.
5. Branch órfão `estudo-2-dados`: autorizado, enviado sem force push, com a conferência do tamanho de cada arquivo antes da abertura (seção 3.1) e o aviso no README.
6. Previsões da seção 7.3: de acordo, com a previsão em número da razão de taxas.

Ajustes: a fronteira entre as partes do gabarito pela data de congelamento da parte 1 (seções 4.1, 5 e 7.1); a versão do Python e o SHA-256 do lock no registro do estudo (seção 8); o cabeçalho com a autoria do texto; a assinatura.

## 12. Registro

- Data: 15/11/2026.
- Commit: o que introduz este arquivo com este nome. O hash é anotado aqui no commit seguinte, sem mudar nenhuma regra acima.
- Hash do commit de registro: `79c9214714696693235ce372b82cdaa1ad73c38e` (anotado no commit seguinte, sem mudar nenhuma regra acima).

---

Assinado por: Roberto Chiocca · Data: 15/11/2026

## 13. Emendas

### Emenda 1 · 19/11/2026 · fronteira entre as partes do gabarito e qualificação dos casos (antes da abertura do lacre, sem nenhum valor de 2024 ou 2025 e sem nenhum alerta)

1. Um caso pertence à parte em que se torna público o primeiro documento que o qualifica pela seção 5: processo da CVM sobre as demonstrações, fato relevante que admite erro ou fraude contábil, determinação de refazimento ou republicação da CVM ou, nas financeiras, o Banco Central. A data_publica continua sendo a primeira data pública documentada, mesmo que anterior a esse documento.
2. A busca da parte 2 cobre todo o período, do registro deste pré-registro até 31/12/2029. Um caso cujo documento qualificador é anterior ao congelamento da parte 1, mas que a busca da parte 1 não encontrou, entra na parte 2 marcado como "não encontrado na parte 1" e é relatado à parte.
3. Uma determinação de refazimento ou republicação revertida pelo Colegiado da CVM não qualifica o caso. Se mantida, qualifica normalmente.
4. Pela fonte (2), só qualifica um fato relevante que admite erro ou fraude nas demonstrações. Uma reapresentação descrita como mudança de política contábil ou de estimativa, sem admissão de erro, não qualifica; reapresentações assim são tratadas só pelo desfecho secundário (seção 4.2), pela regra mecânica dele.
5. Casos que não qualificam no congelamento, mas podem qualificar depois, ficam listados no registro da busca como "podem entrar na parte 2". Estar na lista não é acusação; nenhum alerta deles é descrito ou publicado por estarem nela, e a lista não entra em nenhuma métrica.
