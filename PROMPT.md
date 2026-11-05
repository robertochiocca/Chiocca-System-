# Prompt: Chiocca System, detector de alertas contábeis (versão mínima)

*Bilingual project: every deliverable in Brazilian Portuguese and English.*

> **Como usar este pacote**
> 1. Crie o repositório `Chiocca-System` e copie para ele todos os arquivos do pacote: `README.md`, `LICENSE`, este `PROMPT.md`, `catalogo_sinais.yaml`, `glossario_pt_en.yaml`, `data/gabarito_casos.csv`, `data/exemplo_resolvido.json`, `docs/pre-registro.md` e `.gitignore`.
> 2. Coloque os PDFs dos livros e artigos da trilha (*Financial Shenanigans* e os demais) em `referencias/` **no seu computador**. O `.gitignore` já impede que eles vão para o GitHub: os livros têm direitos autorais e não podem ser publicados.
> 3. **Preencha e assine `docs/pre-registro.md` antes de rodar o agente.**
> 4. Cole tudo abaixo da linha no agente de código, com o repositório aberto.

---

Você vai construir a **versão mínima de um detector de alertas contábeis** para companhias abertas brasileiras, usando os dados abertos da CVM.

O objetivo não é acusar ninguém. O objetivo é um **estudo reproduzível** que responde: *com os dados que eram públicos na época, sinais simples teriam alertado para casos reais de manipulação antes de eles virem a público, e quantos alarmes falsos isso custaria?*

## Arquivos que já existem (leia todos antes de escrever código)

- **`catalogo_sinais.yaml`:** fonte única de verdade dos sinais. Para cada um, traz a fórmula, as contas da DFP, o capítulo e a página do livro e a fase (`mvp`, `fase_2`, `fase_3`, `manual`). Nesta tarefa, implemente **só os sinais `mvp`**: `mscore_beneish`, `dpo_salto`, `juro_implicito` e `lucro_sem_caixa`.
- **`data/gabarito_casos.csv`:** os casos reais com `data_publica` e período afetado. Traz dois casos iniciais (Americanas e IRB) com fontes.
- **`data/exemplo_resolvido.json`:** empresa fictícia com as entradas e os valores esperados de cada componente do M-score e de cada sinal da primeira versão, mais um exemplo de contagem da avaliação. Também traz valores de sinais da fase 2 (TATA na versão de balanço, rendimento do caixa, dividendos sem caixa, F-score): ficam como referência futura e não entram nesta tarefa. É o teste de referência: o código tem que reproduzir todos os valores dentro da tolerância do arquivo, inclusive o lado do corte do M-score. **Nunca altere um valor esperado para o teste passar;** se achar um erro no arquivo, pare e me mostre.
- **`docs/pre-registro.md`:** as decisões do estudo (corte, regras de alerta, divisão no tempo), tomadas pelo Roberto **antes** de qualquer dado. **Você lê e obedece; nunca preenche nem altera.**
- **`glossario_pt_en.yaml`:** os termos contábeis e do estudo em português e inglês. É a referência de tradução de todo texto gerado.
- **`referencias/` (local, fora do git):** o PDF de *Financial Shenanigans* (Schilit, Perler e Engelhart, 4ª ed., 2018) e os demais livros e artigos da trilha (Beneish, Dechow, Assaf Neto, Manual FIPECAFI, *Money Men*, Einhorn, McLean e Elkind, Benford). Use-os para entender cada sinal. As páginas no catálogo são do arquivo PDF; o guia de leitura do dossiê diz capítulo e página de cada assunto. **Não copie trechos do livro para o repositório:** cite capítulo e página na docstring e explique com suas palavras.

## Projeto bilíngue (PT-BR + EN) · Bilingual project

> **This is a bilingual project. Brazilian Portuguese and English are both first-class languages: every user-facing output must be complete, correct and natural in both.**

Português e inglês têm o mesmo peso neste projeto. "Eficiência máxima nos dois idiomas" quer dizer:

1. **Paridade completa.** Tudo o que um usuário, leitor ou recrutador vê existe inteiro nos dois idiomas: README, documentação, estudos e relatórios, interface, saídas da API e mensagens ao usuário final. A versão em inglês não é resumo da portuguesa, nem o contrário.
2. **Texto nativo, não tradução literal.** Cada versão é escrita como um profissional da área escreveria naquele idioma, com a terminologia usada no mercado.
3. **Uma fonte de números, dois textos.** Números, tabelas e gráficos são calculados uma vez. Só o texto muda por idioma, e ele vem de catálogos de mensagens (`pt`/`en`) ou de templates. Nenhuma frase traduzida fica solta no meio da lógica.
4. **Formatação por idioma, numa função só, testada.**
   - PT: `R$ 1.234,56`, `12,5%`, `31/12/2025`.
   - EN: `R$1,234.56` (a moeda continua sendo o real), `12.5%`, `2025-12-31`.
5. **Glossário PT↔EN versionado.** Cada termo técnico tem uma tradução só, usada em todo lugar. Termos sem equivalente (Simples Nacional, DAS, risco sacado, fato relevante) ficam no original e ganham uma explicação curta na primeira vez que aparecem em inglês.
6. **Fonte oficial não se traduz como se fosse oficial.** Leis, normas e demonstrações financeiras brasileiras existem em português. O texto oficial fica em PT, e qualquer versão em inglês leva o rótulo "unofficial translation".
7. **Testes de paridade no CI:**
   - toda chave de mensagem existe nos dois idiomas;
   - nenhum texto fica em branco ou idêntico ao do outro idioma, exceto os de uma lista de exceções (nomes próprios, siglas);
   - cada documento PT tem seu par EN com **os mesmos números**: um teste extrai os números dos dois e compara;
   - interface e relatórios montam nos dois idiomas.
8. **Código.** Identificadores, docstrings e mensagens de commit seguem a convenção que o repositório já usa. Não renomeie nada por causa do bilinguismo.

### O que isso significa neste projeto

- **Catálogo:** cada sinal já traz `nome_en` e `o_que_mede_en` ao lado do português. A tabela de sinais da documentação é gerada nos dois idiomas a partir dele. Sinal novo só entra com os dois idiomas.
- **Glossário:** `glossario_pt_en.yaml`, que já está no pacote, é a fonte dos termos contábeis (CPC↔IFRS). Todo texto gerado usa só esses termos.
- **Nomes de contas da DFP:** o nome oficial é o da CVM, em português. Na saída em inglês, use o termo do glossário com o código da conta entre parênteses. Exemplo: *Trade payables (2.01.02)*.
- **Resultados e resumo:** `docs/resultados.md` e `docs/en/results.md`; `docs/resumo.md` e `docs/summary.md`. Todos saem do mesmo script, com teste de números idênticos.
- **Ficha de alerta:** aceita `lang="pt"` ou `lang="en"`, com a frase fixa nos dois idiomas (Fase 4).
- **Pré-registro:** o original assinado é o português. Gere `docs/en/pre-registration.md` com o rótulo "Translation of the signed Portuguese original". Um teste confere que cortes, datas e regras são idênticos aos do original.
- **README:** as seções PT e EN completas, com o mesmo conteúdo. Atualize as duas a cada fase.

## Regras da casa (valem para tudo)

1. **"Como era na época."** Todo cálculo de um ano usa só a versão da demonstração que já era pública na data de corte do pré-registro. A base da CVM é atualizada com as reapresentações: usar o número corrigido para "prever" a fraude é olhar o futuro. Escreva um teste que prova isso com uma reapresentação simulada.
2. **Nenhum número digitado à mão** em README, resumo ou docs. Tudo sai de script, e um teste falha se o documento divergir da saída. A tabela de sinais da documentação é **gerada** a partir do `catalogo_sinais.yaml`.
3. **Fato externo só com fonte conferida.** Exemplos: códigos de conta, campos da base, série do CDI. Registre em `docs/fontes.md` com URL e data da consulta. Os códigos de conta do catálogo foram escritos de memória e estão marcados "a confirmar".
4. **Testes sem rede.** Use fixtures pequenas no formato dos arquivos da CVM, com procedência descrita. O download real fica num comando separado.
5. **Dado faltante não vira zero.** Um sinal que não pode ser calculado devolve "não calculável" com o motivo (conta ausente, divisão por zero, empresa financeira). Esses casos são contados no relatório.
6. **Linguagem.** O sistema emite **"alerta"** (*alert*), nunca "fraude" nem "suspeita" (*fraud*, *suspect*). Não gera recomendação de compra ou venda. Nenhuma lista pública de empresas em alerta sai deste repositório: os resultados por empresa ficam em `resultados/` (fora do git) e o resumo publica só números agregados e os casos do gabarito, que já são públicos.
7. **Campos humanos.** Você nunca preenche `verificado_por` e `verificado_em` no gabarito. Pode acrescentar casos candidatos com fonte, mas deixa esses dois campos vazios e lista os candidatos no relatório final.
8. Python 3.11+, pandas e numpy. `ruff`, `black` e `mypy` no CI. Um commit por passo, mensagem em português.

## Fase 0: reconhecimento (sem código de sinal ainda)

1. **Confira o pré-registro.** Se `docs/pre-registro.md` tiver qualquer campo `______` vazio ou faltar a assinatura, **pare e me avise**. Não proponha valores.
2. **Confira os dados abertos da CVM.** Baixe o dicionário de dados da DFP e confirme:
   - as colunas `VERSAO` e `ORDEM_EXERC` (os valores `ÚLTIMO` e `PENÚLTIMO`);
   - se existe data de recebimento do documento, e em qual arquivo;
   - os códigos de conta do catálogo, um por um;
   - como empresas com registro cancelado e o setor de atividade aparecem no cadastro de companhias abertas.
3. Escreva `docs/reconhecimento.md` com o que confirmou, o que mudou em relação ao catálogo e o que não conseguiu confirmar. **Pare e me mostre antes da Fase 1.**

## Fase 1: base "como era na época"

- **Download** da DFP anual de todos os anos disponíveis e do cadastro, incluindo empresas canceladas, para `data/brutos/` (fora do git). Inclua um script de verificação com hash dos arquivos.
- **Guarde todas as versões** de cada demonstração. Função central: `como_era(cd_cvm, exercicio, data_corte)`, que devolve as contas da versão pública naquela data.
- **Duas leituras de cada ano.** O valor original vem do ano como `ÚLTIMO` na DFP daquele ano, versão vigente na data de corte. O valor reapresentado aparece como `PENÚLTIMO` na DFP do ano seguinte. Guarde os dois: a diferença entre eles é o que o estudo mede.
- **Financeiras de fora:** identifique bancos, seguradoras e resseguradoras pelo setor no cadastro e marque-as como excluídas. Elas ficam fora do M-score.
- **Testes:**
  - fixture de uma empresa fictícia que reapresenta o exercício anterior;
  - a função devolve o número original antes da reapresentação e o corrigido depois dela;
  - empresa cancelada continua na base.

## Fase 2: os sinais `mvp`

- Um módulo por sinal, lendo fórmula e contas do catálogo.
- Cada função tem uma docstring com:
  - o que o sinal mede, com suas palavras;
  - a referência acadêmica;
  - o capítulo e a página do livro;
  - as contas usadas;
  - a convenção de sinal (na DFP, despesas vêm negativas).
- **M-score:** os oito componentes calculados e guardados separadamente, porque a ficha de alerta precisa mostrar qual deles pesou. A depreciação não tem código fixo: busque por texto na DFC e conte as falhas.
- **Juro implícito:** precisa da média anual do CDI. Se o repositório da Calahonda já tiver o módulo de CDI com procedência, reaproveite. Senão, crie um snapshot da série do SGS do Banco Central, confirmando o número da série e registrando a fonte.
- **Testes:** o teste de referência com `data/exemplo_resolvido.json` vem primeiro; depois, cada componente conferido à mão; propriedades (por exemplo, o DSRI sobe quando os recebíveis crescem mais que a receita); casos não calculáveis.

## Fase 3: avaliação, exatamente como o pré-registro manda

- Calcule os sinais de todas as empresas não financeiras em todos os anos, sempre com `como_era`.
- Aplique as regras de alerta **do pré-registro, sem ajuste**.
- **Métricas:**
  - taxa de alerta por ano;
  - casos do gabarito acertados, com alerta antes da `data_publica`;
  - alarmes por acerto;
  - resultado da regra boba do pré-registro, lado a lado.
- **Divisão no tempo:** o período de teste só é aberto uma vez, no fim. Registre a data e o commit em que foi aberto.
- **Duas leituras da Americanas:** rode os sinais nos números originais e nos reapresentados e mostre a diferença componente por componente.
- **O IRB não entra no M-score** (é resseguradora). No relatório, explique por quê e aponte o sinal da `fase_2` que se aplica a ele.
- Saídas geradas por script em `resultados/` (fora do git) e `docs/resultados.md` e `docs/en/results.md` agregados, com um teste que confere cada número dos dois contra o script.

## Fase 4: ficha de alerta

Para qualquer empresa e ano, `ficha(cd_cvm, exercicio, lang="pt")` gera um texto curto (com `lang="en"`, em inglês) com:

- os sinais que dispararam e os que não dispararam;
- o valor de cada componente, a conta da DFP de origem e o link do documento na CVM;
- a frase fixa:
  - PT: "Alerta estatístico baseado em demonstrações públicas. Não é acusação, não é recomendação de investimento."
  - EN: "Statistical alert based on public financial statements. Not an accusation, not investment advice."

## Fase 5: resumo de uma página, em português e inglês

`docs/resumo.md` (PT) e `docs/summary.md` (EN), gerados a partir dos resultados, com o mesmo conteúdo nos dois idiomas:

- pergunta;
- dados;
- método (citando o pré-registro);
- resultado;
- o que não funcionou;
- limitações, entre elas: poucos casos no gabarito, sinais calibrados nos EUA, despesa financeira ruidosa e o fato de a fraude da Americanas ter sido revelada por dentro.

Nenhum adjetivo sem número ao lado.

## Fora do escopo (não faça)

- Sinais das fases `fase_2`, `fase_3` e `manual`.
- Machine learning: com poucos casos, o modelo decora o gabarito.
- Dashboard, API ou app.
- LLM lendo documentos.
- Teste de retorno das ações.
- Publicar nomes de empresas em alerta fora do gabarito.

Se algo disso parecer necessário, escreva em `docs/roadmap.md` e siga.

## Quando parar e me perguntar

- Pré-registro incompleto ou sem assinatura.
- Fim da Fase 0.
- A base da CVM não guarda as versões originais de algum ano do gabarito. Diga quais e proponha onde buscar; não substitua pelo número corrigido.
- Vontade de mudar uma fórmula ou regra de alerta depois de ver dados. Isso só acontece com um pré-registro novo assinado por mim.
- Antes de qualquer dependência além de pandas e numpy no núcleo.

## Entrega final

Relatório curto com:

- o que foi feito em cada fase;
- os códigos de conta confirmados e os corrigidos;
- quantas empresas e anos entraram na base, e quantos ficaram de fora e por quê;
- o resultado da Fase 3 em três frases com números, em PT e em EN;
- a comparação com a regra boba;
- os casos candidatos ao gabarito que você encontrou, com fonte, para eu verificar;
- o que não foi feito e por quê.
