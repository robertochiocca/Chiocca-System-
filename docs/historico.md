# Histórico do projeto

O que saiu do README em 21/11/2026: o histórico das fases, do estudo 1 à lista lacrada do estudo 2, e a tabela do que está feito e do que está no roadmap. O estado atual, em 30 segundos, está no [README](../README.md).

## Estudo 1 (2010 a 2023)

**Estudo da primeira versão concluído.** O resumo de uma página está em [`docs/resumo.md`](resumo.md), e os números completos, inclusive o caso a caso do gabarito, a regra boba lado a lado, as análises secundárias e a robustez, em [`docs/resultados.md`](resultados.md). Qualquer mudança de regra ou estudo novo depende de autorização.

O gabarito ([`data/gabarito_casos.csv`](../data/gabarito_casos.csv)) guarda casos reais, cada um com o período afetado, a data em que veio a público, a fonte e se o caso é acertável na análise principal. Ele foi ampliado pelas emendas 6 a 9 do pré-registro com processos sancionadores da CVM; casos sem decisão final ficam em [`data/casos_em_observacao.csv`](../data/casos_em_observacao.csv). Os dois casos de partida:

- **Americanas (2023):** revelado por dentro. O Comitê Independente confirmou contratos fictícios de verba de propaganda e operações de risco sacado lançadas em "fornecedores" ([fato relevante de 16/07/2024](https://api.mziq.com/mzfilemanager/v2/d/347dba24-05d2-479e-a775-2ea8677c50f2/fbd1eb14-1e3f-f8ef-ecc5-f49db62d1b04?origin=1)).
- **IRB Brasil (2020):** revelado de fora, pela tese de uma gestora de que o lucro recorrente era menor que o contábil ([InfoMoney](https://www.infomoney.com.br/?p=1397142)). Como é resseguradora, fica fora do M-score, que não se aplica a empresas financeiras, e é avaliado pelo peso de ganhos não recorrentes.

## Produto v2

**Chiocca v2, do estudo ao produto (em andamento).** O estudo 1 está congelado no branch `estudo-1-final`, e o produto usa o motor v1 como está. Fase A concluída: inventário do código da Carchuna, da Calahonda e do DireitoAberto ([`docs/inventario.md`](inventario.md)), contratos de dados ([`docs/contratos.md`](contratos.md)), plano das fases B a F ([`docs/plano-v2.md`](plano-v2.md)) e lacre dos exercícios de 2024 em diante (`chiocca/v2/lacre.py`), reservados ao estudo 2. Fase B concluída: validade, conferências dos dados da CVM, linhagem e confiança ([`docs/motor-de-confianca.md`](motor-de-confianca.md)), com o resultado das conferências na base inteira em [`docs/conferencias.md`](conferencias.md), e CI no GitHub Actions. Fase C1 concluída: armazenamento temporal (DuckDB sobre Parquet), motor v1 em qualquer data de referência e o invariante do estudo 1 ([`docs/armazenamento-temporal.md`](armazenamento-temporal.md)). Fase C2 concluída: escala original, evidências do contrato, busca no ENET por comando separado, contexto (percentis, histórico, Altman Z'' e Piotroski F, sem alerta), parecer e auditor, a seção "Limites" e a investigação em JSON e PDF, com dois exemplos da Americanas (exercício 2021, em 30/04/2022 e em 31/12/2024) em [`docs/exemplos/`](exemplos/). Fase D concluída: API em FastAPI (`/api/v1`), com contratos em Pydantic, busca só por nome, código CVM ou CNPJ, em ordem alfabética, e nenhuma lista de empresas ordenada por alerta, percentil ou escore ([`docs/contratos.md`](contratos.md), seção 6). Fase E concluída: interface em `web/` (Next.js), em PT e EN, com modo escuro e celular, aviso fixo em todas as telas, comparação com o setor só agregada e a página "Como o motor foi testado" ([`docs/contratos.md`](contratos.md), seção 7); modo demonstração ligado por configuração. Demonstração estática preparada: as investigações do modo demonstração geradas por script, em JSON e PDF, para a interface rodar como site estático, sem API (seção 7 dos contratos). Fase F1 em andamento: leitor extrativo das notas explicativas, do relatório do auditor e do Formulário de Referência, só com trechos copiados e conferidos literalmente, sem alerta, com a medida pré-registrada antes do código ([`docs/pre-registro-leitor.md`](pre-registro-leitor.md)); a seção "Trechos dos documentos" foi ligada em 11/11/2026, depois de o leitor congelado atingir as quatro metas nos 20 casos guardados ([`docs/contratos.md`](contratos.md), seção 8). Fase F2a em andamento: fatos relevantes e comunicados ao mercado entregues até a data, só com os metadados do IPE, em "O que se sabia na data", e o monitor da CVM, que só lista as novidades para revisão ([`docs/contratos.md`](contratos.md), seção 9). Fase F2b: pela emenda 1 do pré-registro do leitor, a segunda versão do leitor (`leitor-f1-2`) e uma regra própria para o assunto dos fatos relevantes foram congeladas e medidas uma única vez em casos guardados novos; as duas passaram, e desde 13/11/2026 a seção de trechos usa a `leitor-f1-2` e a lista usa a regra nova ([`docs/contratos.md`](contratos.md), seções 8 e 9). A demonstração estática está publicada no GitHub Pages desde 10/11/2026; o deploy com API ao vivo foi adiado (decisão de Roberto de 15/11/2026, [`plano-v2.md`](plano-v2.md)).

## Estudo 2 (2024 e 2025)

O pré-registro do estudo 2 ([`pre-registro-estudo-2.md`](pre-registro-estudo-2.md)) foi registrado em 15/11/2026 (commit `79c9214714696693235ce372b82cdaa1ad73c38e`), com três emendas antes da lista. A parte 1 do gabarito foi congelada em 19/11/2026, sem nenhum caso. O lacre foi aberto só para o script do estudo em 20/11/2026 (commit `f45469872316c1068703e11837e1a2cce70db4ae`), e a lista foi lacrada em 21/11/2026: o SHA-256 está em [`estudo_2_lista_lacrada.json`](estudo_2_lista_lacrada.json), com o carimbo OpenTimestamps em [`carimbos/estudo-2-lista.txt`](carimbos/estudo-2-lista.txt), e o arquivo ficou com Roberto. A avaliação secundária é a partir de 31/05/2027 e a principal, a partir de 01/01/2030. Os passos estão no [plano](plano-v2.md), seção "Depois da Fase F".

## Feito e roadmap

| Implementado | Roadmap |
| --- | --- |
| Catálogo de 16 sinais, em PT e EN, com fórmulas e referências | Dados trimestrais (ITR), necessários para alcançar o IRB |
| Gabarito ampliado e casos em observação, com fontes e notas em PT e EN | |
| Reconhecimento dos dados da CVM ([`docs/reconhecimento.md`](reconhecimento.md)) | |
| Download com verificação por hash e base "como era na época" ([`docs/base.md`](base.md)) | |
| Fórmulas dos sinais da primeira versão, conferidas pelo teste de referência | |
| Sinais e alertas na amostra inteira e métricas do pré-registro ([`docs/resultados.md`](resultados.md)) | |
| CDI do Banco Central (SGS 4389) com fonte registrada ([`docs/fontes.md`](fontes.md)) | |
| Duas leituras da Americanas, robustez com valores neutros, secundária da emenda 5 e análise descritiva rotulada | |
| Ficha de alerta em PT e EN (`python -m chiocca.ficha`) e resumo de uma página ([`docs/resumo.md`](resumo.md)) | |
| Glossário PT↔EN dos termos contábeis e do estudo | |
| Pré-registro do estudo 1 e do estudo 2 | Avaliação secundária do estudo 2 (a partir de 31/05/2027) e principal (a partir de 01/01/2030) |
| Exemplo resolvido com valores esperados (teste de referência) | |
| Produto v2 (fases A a F): armazém temporal, investigação, API, interface, demonstração no GitHub Pages e leitor de documentos | |
| Estudo 2: pré-registro, emendas, parte 1 do gabarito e lista lacrada ([`estudo_2_lista_lacrada.json`](estudo_2_lista_lacrada.json)) | |
| Especificação para o agente de código ([`PROMPT.md`](../PROMPT.md)) | Próximas fases: auditoria, ganhos não recorrentes a partir das notas explicativas, rendimento do caixa, dividendos sem caixa, F-score e teste de retorno das ações |
