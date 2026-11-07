# Contratos de dados do Chiocca System v2

Proposta da Fase A, para sua aprovação. Só o lacre (seção 1) já está no código; o resto é especificação. Os nomes de campo ficam em português, como no resto do repositório; os textos ao usuário vêm em PT e EN.

## 0. O que os contratos garantem

- **Motor v1 (estudo 1) como está.** O v2 chama `chiocca.base.como_era`, `chiocca.variaveis` e `chiocca.sinais.*` do branch `estudo-1-final` (`8c9a823`) e não altera regra, corte nem código desses módulos.
- **Data de referência em toda consulta.** Toda resposta diz "como era em DD/MM/AAAA" e só usa o que tinha sido entregue à CVM até aquela data.
- **Lacre.** Nenhum exercício acima de `ULTIMO_EXERCICIO_LIBERADO` é lido, calculado, exibido ou resumido.
- **Lastro.** Todo número aponta para documento, versão, data de entrega, demonstração, coluna e conta; toda frase sobre documento traz o trecho conferido literalmente.
- **Sinal não é acusação.** Nenhum campo, rótulo ou texto diz "fraude", recomenda compra ou venda, ou ordena empresas por risco. Toda saída leva o aviso: PT "Sinal estatístico baseado em demonstrações públicas. Não é acusação, não é recomendação de investimento."; EN "Statistical signal based on public financial statements. Not an accusation, not investment advice."
- **Sem veredito binário.** Todo sinal vem com contexto (percentil no setor e no ano, histórico da própria empresa e confiança nos dados).

## 1. Lacre (já implementado)

- `chiocca/v2/lacre.py`: `ULTIMO_EXERCICIO_LIBERADO = 2023`, num lugar só, no código. Mudar exige um commit.
- `garantir_liberado(exercicio)` levanta `ExercicioLacrado`; `so_liberados(tabela)` filtra antes de qualquer cálculo.
- O teste `tests/test_v2_lacre.py` garante o limite, a recusa e que o cálculo do motor v1 reaproveitado para em 2023.
- **Data de referência máxima: decisão sua** (pergunta 1 do [plano](plano-v2.md)). Proposta: 31/12/2024. Assim nenhuma DFP de exercício lacrado chega a ser lida, e o filtro por exercício continua valendo para quem fecha o exercício no meio do ano.

## 2. Entidades

### Empresa

| Campo | Tipo | Descrição e origem |
| --- | --- | --- |
| `cd_cvm` | texto | Código CVM, sem zeros à esquerda (convenção do estudo 1) |
| `cnpj` | texto | Do índice da DFP |
| `denominacao` | texto | Da DFP do exercício (o nome muda com o tempo; a investigação mostra o da época) |
| `codigos_negociacao` | lista de texto | Do FCA `valor_mobiliario`, com o período de negociação de cada código, na versão entregue até a data de referência |
| `setor` | texto | Setor do FCA entregue até a data de referência; sem FCA, o do cadastro (regra congelada, reconhecimento 4.1) |
| `grupo` | `financeira` ou `nao_financeira` | Regra congelada do estudo 1 (setor candidato e plano de contas) |
| `situacao_cadastro` | texto | Do cadastro atual, só como informação |

### DataReferencia

Data (`AAAA-MM-DD`) informada pelo analista. Vale dentro do intervalo [data mínima, data máxima] que você decidir; fora dele, a consulta é recusada com o motivo.

### ExercicioNaData

Uma empresa num exercício, como era na data de referência. É a saída de `como_era(fontes, cd_cvm, exercicio, corte=data_referencia)`.

| Campo | Tipo | Descrição |
| --- | --- | --- |
| `cd_cvm`, `exercicio`, `dt_refer` | texto, inteiro, data | `exercicio` passa por `garantir_liberado` |
| `data_referencia` | data | A da consulta |
| `situacao` | enumeração | `ok`, `sem_versao_ate_a_data`, `versao_indisponivel_individual`, `versao_pendente_enet` ou `conta_repetida` (os estados de `como_era`) |
| `versao_usada`, `dt_receb` | inteiro, data | A versão mais recente entregue até a data de referência |
| `versoes_conhecidas` | lista de (versão, data de entrega) | Só as entregues até a data de referência: a existência de uma versão posterior é informação do futuro e não aparece |
| `tipo` | `con` ou `ind` | Consolidado quando existir; senão, individual |
| `origem` | `dados_abertos` ou `enet` | ENET só para consolidado (emenda 8) |
| `num_doc`, `link` | texto | Número sequencial do documento e endereço da página no ENET |
| `escala_original` | `MIL` ou `UNIDADE` | Os valores do contrato estão sempre em reais |
| `contas` | lista de `Evidencia` | As linhas da DFP usadas (ÚLTIMO para t e PENÚLTIMO para t−1) |

### Evidencia

A unidade de lastro. Todo número e toda citação apontam para uma ou mais evidências.

| Campo | Tipo | Descrição |
| --- | --- | --- |
| `id` | texto | Estável: hash de documento, versão, demonstração, coluna e conta (ou página e trecho) |
| `documento` | objeto | `tipo` (DFP, ITR, FCA, IPE), `num_doc`, `versao`, `dt_receb`, `origem` (`dados_abertos`, `enet` ou `pdf`), `url`, `sha256` do arquivo de onde a linha foi lida |
| `demonstracao`, `coluna` | texto | BPA, BPP, DRE, DFC_MI, DFC_MD, DVA ou parecer; ÚLTIMO (exercício t) ou PENÚLTIMO (t−1) |
| `cd_conta`, `ds_conta` | texto | Código e descrição oficiais, como estão no arquivo (o texto oficial fica em PT; a versão EN só leva o termo do glossário ao lado) |
| `valor` | número | Em reais, depois da escala; a transformação aparece na linhagem |
| `localizacao` | objeto | Para CSV: arquivo e linha; para PDF: página e folha |
| `trecho` | texto ou nulo | Só para documentos de texto: o trecho citado |
| `conferida` | booleano | Para trecho, verdadeiro só se ele existe literalmente na página (conferência do leitor) |

### Validade

O estado de cada número, adaptado de `validade.py` (Carchuna).

| Estado | Valor | Quando |
| --- | --- | --- |
| `ok` | presente | O número pode ir para a tela |
| `indefinido` | ausente | Não existe número: é o "não calculável" do motor v1, com o mesmo motivo (conta ausente, denominador zero, receita negativa, plano de contas) |
| `implausivel` | presente | A conta fechou, mas uma conferência de qualidade da Fase B falhou na entrada. O estado acompanha o número e **não muda nenhum sinal** do motor v1 |

Motivo obrigatório fora de `ok`, em PT e EN. `None` e `NaN` nunca são usados como sinal de falta.

### Conferencia

Conferência de qualidade dos dados da CVM (Fase B): `id`, `nome` (PT e EN), `resultado` (`ok`, `falhou` ou `nao_aplicavel`), `valores_comparados` (evidências), `tolerancia` e `detalhe`. As identidades, como o ativo igual ao passivo mais o patrimônio líquido, são separadas das reconciliações por outro caminho (por exemplo, DFC contra a variação do caixa no balanço), como na Carchuna.

### Confianca

Adaptada da estrutura de `confianca.py` (Carchuna), **sem nota numérica**: o plano de integração pede para não copiar pontuação arbitrária.

| Campo | Descrição |
| --- | --- |
| `criterios` | Lista com `fonte` (dados abertos ou ENET, consolidado ou individual), `completude` (contas de que o sinal precisa), `consistencia` (conferências da Fase B), `atualidade` (entregue até o corte do exercício, reapresentada depois?) e `metodo` (o que o estudo 1 mostrou sobre o sinal) |
| cada critério | `resultado` (`ok`, `atencao` ou `problema`) e `motivo` em PT e EN |
| `nivel` | `baixa` se algum critério tem problema; `media` se algum tem atenção; senão `alta`. Regra escrita, sem soma |

### Contexto

| Campo | Descrição |
| --- | --- |
| `percentil_setor_ano` | Posição do valor entre as empresas do mesmo setor e grupo, no mesmo exercício, com o sinal calculável e versão pública na data de referência; traz `n`. Abaixo de um `n` mínimo (proposta: 10), fica nulo com o motivo e vale só o percentil do grupo |
| `percentil_grupo_ano` | O mesmo dentro do grupo |
| `historico` | Série da própria empresa nos exercícios anteriores, como era na data de referência; mediana, cerca de IQR e posição do valor (dentro ou fora da cerca), com o método escrito (detecção adaptada de `insights.py`). Mínimo de exercícios, proposta: 5 |

Percentis e histórico são exibição, não regra: não criam alerta e não mudam o motor v1.

### Achado

| Campo | Descrição |
| --- | --- |
| `id` | Estável |
| `familia` | `possivel_manipulacao`, `risco_financeiro` ou `qualidade_financeira` (seção 3) |
| `sinal` | Código do sinal (por exemplo `mscore`, `DSRI`, `dpo`, `juro`, `lucro_sem_caixa`, `peso_nao_recorrente`, `altman_z2`, `piotroski_f`) |
| `exercicio` | Liberado pelo lacre |
| `valor` | Com `Validade` |
| `regra` | Só na família de possível manipulação: a regra do pré-registro (por exemplo, M > −1,78), com a referência |
| `alerta_v1` | Verdadeiro ou falso só nessa família, pela regra do estudo 1; nulo nas outras, que nunca alertam |
| `contexto` | `Contexto` |
| `confianca` | `Confianca` |
| `explicacao` | O que o sinal mede, em PT e EN, do catálogo |
| `explicacoes_alternativas` | Razões legítimas para o valor (por exemplo, fusão, mudança de prazo comercial, variação cambial na despesa financeira), cada uma com fonte; quando houver documento da empresa, com trecho conferido |
| `limitacoes` | Do sinal e do caso (por exemplo, DFC pelo método direto sem linha de depreciação) |
| `linhagem` | `Linhagem` |
| `natureza` | Natureza de cada frase: `calculado`, `trecho_literal`, `resumo`, `inferencia` ou `hipotese` (taxonomia adaptada de `proveniencia.py`, DireitoAberto) |

### Linhagem

A ficha "como cheguei a este número", adaptada de `linhagem.py` (Carchuna). Ela não recalcula nada: descreve o caminho que o motor já percorreu.

| Campo | Descrição |
| --- | --- |
| `numero` | Nome, rótulo em PT e EN, valor |
| `formula` | Texto da fórmula com os valores do caso |
| `entradas` | Ids das evidências, cada uma clicável até a linha da DFP |
| `transformacoes` | Escala para reais, juros pagos movidos para o financiamento, deduplicação de conta repetida, padrões de texto da DFC |
| `premissas`, `limitacoes` | Texto em PT e EN |
| `motor` | "motor v1 (estudo 1)", com o commit `8c9a823`, ou o módulo do v2 para os indicadores de contexto |
| `codigo` | Módulo e função que calcularam |
| `calculado_em` | Data e hora |

### Investigacao

| Campo | Descrição |
| --- | --- |
| `empresa`, `data_referencia`, `idioma` | — |
| `exercicios` | Lista de `ExercicioNaData`, todos liberados |
| `achados` | Agrupados por família e **nunca somados** entre famílias |
| `mudancas` | O que mudou em relação aos exercícios anteriores e às versões anteriores conhecidas na data (reapresentações), com evidências |
| `o_que_se_sabia` | Documentos públicos na data de referência (DFP, ITR e, na Fase F, fatos relevantes), com data de entrega |
| `qualidade_dos_dados` | Conferências e confiança |
| `como_o_motor_foi_testado` | Ligação para o resultado do estudo 1, como saiu ([`docs/resumo.md`](resumo.md)) |
| `limitacoes` | Gerais e do caso |
| `motor`, `gerado_em`, `aviso` | Versão do motor, data e hora, aviso fixo |

## 3. Famílias de sinais, sem soma entre elas

| Família | Sinais | Papel | Fonte | Gera alerta? |
| --- | --- | --- | --- | --- |
| Possível manipulação | Motor v1 (estudo 1): os oito componentes do M-score e o M, o salto do DPO, o juro implícito, o lucro sem caixa (só contexto, como no estudo) e, nas financeiras, o peso não recorrente | Alerta do motor v1, sempre com o contexto e com o resultado do estudo 1 ao lado | Pré-registro, seção 4, e emendas 1 a 11 | Sim, pela regra do estudo 1, sem mudança |
| Risco financeiro | Altman Z'' (versão de 1995 para mercados emergentes) | Contexto descritivo | Altman, Hartzell e Peck (1995), a conferir na fonte primária antes de implementar | Não |
| Qualidade financeira | Piotroski F (2000), nove testes binários | Contexto descritivo | Piotroski (2000), Journal of Accounting Research, a conferir na fonte primária antes de implementar | Não |

- O salto do DPO e o juro implícito ficam na família de possível manipulação porque, no motor v1, fazem parte do mesmo detector (pré-registro, seção 4); separá-los mudaria a regra "em alerta". Pergunta 3 do plano.
- **Altman Z''**: os coeficientes, a constante de mercados emergentes e as faixas serão transcritos da fonte primária e registrados em `docs/fontes.md` antes da implementação, como manda a regra de lastro. Proposta de mapeamento das variáveis para as contas da CVM, a conferir: capital de giro (1.01 − 2.01) ÷ ativo total (1); lucros retidos (2.03.04 + 2.03.05) ÷ ativo total; EBIT (3.05) ÷ ativo total; patrimônio líquido (2.03) ÷ passivo exigível (2.01 + 2.02). Limites conhecidos: calibrado fora do Brasil; no Brasil os lucros do exercício são em grande parte distribuídos ou levados a reservas, o que afeta a variável de lucros retidos; não se aplica a financeiras. As faixas da fonte aparecem como "faixas do artigo original", nunca como veredito.
- **Piotroski F**: os nove testes (rentabilidade, caixa operacional, variação da rentabilidade, accruals, alavancagem, liquidez, emissão de ações, margem bruta e giro do ativo) serão conferidos na fonte primária. A emissão de ações depende de `composicao_capital`, que só existe nos anos recentes. Para os anos sem ele, o mapeamento (linhas de emissão na DFC, pelo padrão congelado da parte 4.2 do reconhecimento, ou variação do capital social 2.03.01) será proposto na Fase C.
- O catálogo já tem um `fscore_dechow` (Dechow e outros, 2011), que mede outra coisa (probabilidade de reapresentação) e é sinal da fase 2 do catálogo. Ele não entra nesta etapa, e os nomes não se confundem.

## 4. Data de referência, versões e corte transversal

- **Versão:** para cada empresa e exercício, a mais recente entregue até a data de referência (`como_era` com `corte = data_referencia`). Consolidado quando existir; senão, individual. Versões anteriores vêm do ENET, só no consolidado. O t−1 vem do PENÚLTIMO da mesma DFP.
- **Corte transversal:** os decis do motor v1 (salto do DPO e peso não recorrente) e os percentis de contexto são recalculados com as empresas cuja versão era pública na data de referência. É a mesma regra do estudo 1, aplicada à informação daquela data.
- **Invariante testável:** com a data de referência igual à data de corte do exercício, os sinais e alertas do motor v1 coincidem com os do estudo 1 (`resultados/sinais_empresa_ano.csv`). Esse teste entra na Fase C.
- **Armazenamento:** DuckDB sobre Parquet, montado a partir de `data/brutos` (já conferido por hash) e de `data/cache/enet`. Tabelas: `versoes` (metadados de todas as versões de DFP até o lacre), `contas` (por versão disponível), `fca` e `cadastro`. Uma versão que não está armazenada sai como `versao_pendente_enet`. A busca no ENET acontece por comando separado, nunca dentro de uma consulta da API (pergunta 9 do plano).

## 5. Saídas

- **JSON:** o contrato acima, com Pydantic na Fase D e os mesmos números do motor.
- **PDF:** texto e tabelas, nas duas línguas, gerado sem dependência (adaptado de `pdf_simples.py`, DireitoAberto), com o aviso fixo em todas as páginas.
- Nenhuma lista de empresas ordenada por risco, em nenhuma saída.
