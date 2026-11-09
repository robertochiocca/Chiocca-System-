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
- **Intervalo da data de referência** (decisão de 07/11/2026): de 30/04/2011 a 31/12/2024, em `DATA_REFERENCIA_MINIMA` e `DATA_REFERENCIA_MAXIMA`, com `garantir_data_referencia`. O lacre continua por exercício: nada acima de 2023 é calculado, em nenhuma data.

## 2. Entidades

### Empresa

| Campo | Tipo | Descrição e origem |
| --- | --- | --- |
| `cd_cvm` | texto | Código CVM, sem zeros à esquerda (convenção do estudo 1) |
| `cnpj` | texto | Do índice da DFP |
| `denominacao` | texto | Da DFP do exercício (o nome muda com o tempo; a investigação mostra o da época) Implementado na C2: nome empresarial da última versão do FCA entregue até a data; o índice dos dados abertos traz o nome atual, que pode ser posterior à data (o da Americanas já trazia "em recuperação judicial") |
| `codigos_negociacao` | lista de texto | Do FCA `valor_mobiliario`, com o período de negociação de cada código, na versão entregue até a data de referência. Implementado na Fase D: tabela `valores_mobiliarios` do armazém (só versões do FCA entregues até 31/12/2024); cada código vem com o valor mobiliário, o mercado, o início e o fim da negociação e o FCA de origem (ano, versão e data de entrega), da última versão do FCA entregue até a data. Lista vazia vem com `motivo_codigos_negociacao`: nos dados abertos, o campo só vem preenchido nos FCA mais recentes, e o ano a partir do qual vem preenchido é calculado do armazém e vai no motivo |
| `setor` | texto | Setor do FCA entregue até a data de referência; sem FCA, o do cadastro (regra congelada, reconhecimento 4.1) |
| `grupo` | `financeira` ou `nao_financeira` | Regra congelada do estudo 1 (setor candidato e plano de contas) |
| `situacao_cadastro` | texto | Do cadastro atual, só como informação. Regra de 09/11/2026: é informação de hoje e não entra no bloco da empresa, que é a visão "como era"; vai na seção `informacao_de_hoje` do fim da investigação (ver "Informação de hoje" abaixo) |

### DataReferencia

Data (`AAAA-MM-DD`) informada pelo analista, de 30/04/2011 a 31/12/2024; fora desse intervalo, a consulta é recusada com o motivo. Documentos entregues depois de 31/12/2024 só têm metadados e hash registrados pelo monitor: nada é lido, resumido ou extraído deles.

### ExercicioNaData

Uma empresa num exercício, como era na data de referência. É a saída de `como_era(fontes, cd_cvm, exercicio, corte=data_referencia)`.

| Campo | Tipo | Descrição |
| --- | --- | --- |
| `cd_cvm`, `exercicio`, `dt_refer` | texto, inteiro, data | `exercicio` passa por `garantir_liberado` |
| `data_referencia` | data | A da consulta |
| `situacao` | enumeração | `ok`, `sem_documento`, `sem_versao_ate_a_data`, `versao_indisponivel_individual`, `versao_indisponivel_enet`, `versao_pendente_enet` ou `conta_repetida` (os estados de `como_era`, com o nome do contrato em `chiocca.v2.na_data.SITUACAO`) |
| `versao_usada`, `dt_receb` | inteiro, data | A versão mais recente entregue até a data de referência |
| `versoes_conhecidas` | lista de (versão, data de entrega) | Só as entregues até a data de referência: a existência de uma versão posterior é informação do futuro e não aparece |
| `tipo` | `con` ou `ind` | Consolidado quando existir; senão, individual |
| `origem` | `dados_abertos` ou `enet` | ENET só para consolidado (emenda 8) |
| `num_doc`, `link` | texto | Número sequencial do documento e endereço da página no ENET |
| `escala_original` | `MIL` ou `UNIDADE` | Os valores do contrato estão sempre em reais. Implementado na C2: a escala original da versão dos dados abertos (tabela `escalas` do armazém). Nas versões do ENET o campo fica vazio, porque o cache guarda os valores já em reais e não registra a escala da página; o motivo vai nas notas |
| `contas` | lista de `Evidencia` | As linhas da DFP usadas (ÚLTIMO para t e PENÚLTIMO para t−1). Implementado na C2 como `evidencias` (`chiocca.v2.na_data.evidencias`), com o arquivo e a linha de origem quando há `Localizador` |
| `notas` | lista de motivos (PT e EN) | Notas de linhagem do documento. Quando a versão usada não é a última, o `como_era` lê a estrutura da última versão, entregue depois da data, e a nota é "estrutura lida de documento posterior à data (comportamento do estudo 1, emenda 8)" (decisão de 09/11/2026) |

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
| `percentil_setor_ano` | Posição do valor entre as empresas do mesmo setor e grupo, no mesmo exercício, com o sinal calculável e versão pública na data de referência; traz `n`. Abaixo de um `n` mínimo (proposta: 10), fica nulo com o motivo e vale só o percentil do grupo. Na Fase E, o contexto traz também `distribuicao_setor_ano`: só a distribuição agregada do setor e ano (quantis e histograma de faixas iguais entre os percentis 5 e 95, com as contagens abaixo e acima), nunca nomes nem valores de outras empresas, e só com o mesmo `n` mínimo |
| `percentil_grupo_ano` | O mesmo dentro do grupo |
| `historico` | Série da própria empresa nos exercícios anteriores, como era na data de referência; mediana, faixa de Tukey (quartis ± 1,5 × IQR; no JSON, `faixa_tukey`) e posição do valor (dentro, acima ou abaixo da faixa), com o método escrito (detecção adaptada de `insights.py`). Mínimo de exercícios, proposta: 5. Na Fase E, traz também `serie` (a série da própria empresa, para a linha do tempo) |

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

Implementado na C2, segunda parte (`chiocca/v2/investigacao.py`, JSON; `chiocca/v2/pdf_investigacao.py`, PDF gerado só do JSON). Exemplos de referência: Americanas, exercício 2021, em 30/04/2022 e em 31/12/2024 (este com as diferenças do comparativo da DFP de 2022 como evidência destacada), em `docs/exemplos/` (PT e EN, JSON e PDF), gerados por `python -m chiocca.v2.exemplos` e conferidos pelo mesmo teste. O relatório do auditor vem da seção de pareceres dos dados abertos, que só existe para a última versão da DFP; as trocas de auditor saem do FCA, pelo código da firma na CVM, sem CPF nem pessoa física. `gerado_em` e `calculado_em` são o único campo que muda entre execuções.

| Campo | Descrição |
| --- | --- |
| `empresa`, `data_referencia`, `idioma` | — |
| `exercicios` | Lista de `ExercicioNaData`, todos liberados |
| `achados` | Agrupados por família e **nunca somados** entre famílias. Cada achado traz `unidade` (dias no DPO, p.p. no juro menos CDI, "índice" nos componentes e nas demais razões, "sinais de 9" no Piotroski F), e todo valor mostrado leva a unidade. Componentes do M-score: `componente_de = "mscore"` e a regra "Componente do M-score; não tem regra própria". Títulos de sinal e itens de lista com inicial maiúscula (09/11/2026) |
| `mudancas` | O que mudou em relação aos exercícios anteriores e às versões anteriores conhecidas na data (reapresentações), com evidências. Na C2: `comparativo_destacadas` (só as diferenças destacadas pela regra de materialidade da seção 4), `reapresentacao_pelo_comparativo` (lista completa, com o grupo de cada diferença) e `materialidade_comparativo` (linhas-chave, limite relativo, ativo total e limite) |
| `o_que_se_sabia` | Documentos públicos na data de referência (DFP, ITR e, na Fase F, fatos relevantes), com data de entrega |
| `qualidade_dos_dados` | Conferências e confiança |
| `parecer_e_auditor` | Seção factual (Fase C2): tipo do parecer, trecho do texto da DFP conferido literalmente, auditor e trocas de auditor pelo FCA. Não é família de sinais e não gera nota nem alerta. Rodízio (regra de 09/11/2026): nota fixa `rodizio` sobre a Resolução CVM nº 23/2021, arts. 31 (cinco exercícios sociais consecutivos, com intervalo mínimo de três para a recontratação) e 31-A (até dez, com Comitê de Auditoria Estatutário e auditor pessoa jurídica), em vigor desde 01/04/2021 (art. 41), que revogou a Instrução CVM nº 308/1999 (art. 40, I), de regra equivalente nos seus arts. 31 e 31-A; texto conferido na CVM em 09/11/2026. Trocas (acabamento de 09/11/2026): uma linha por troca real, comparando as firmas pelo código na CVM, com um nome canônico por código, também nos auditores por FCA: a grafia mais frequente nos FCA entregues até a data, de todas as companhias, entre as que já vêm em capitalização normal (no empate, a mais recente); se só houver grafias em maiúsculas, a mais frequente recebe capitalização normal, mantendo siglas como KPMG, BDO e S.S. (pedido de 09/11/2026; é só exibição, a comparação continua pelo código); quando a nova firma aparece no FCA ao lado da que sai, a troca é uma só, com `transicao_fca` ("transição: duas firmas no FCA de AAAA"); firma acrescentada ou retirada sem par é uma linha com o outro lado vazio. Auditor pessoa física (CPF no campo do auditor) não tem o nome guardado: aparece como "auditor pessoa física (nome omitido)". Em cada troca, `saida` traz os exercícios consecutivos da firma que saiu, pelas datas de início e fim no FCA (audita o exercício quem está contratado no fim dele); quando a troca coincide com o fim do prazo (cinco ou dez exercícios), a nota diz que a troca é compatível com o rodízio, citando a norma vigente quando a firma nova começou. Troca de auditor é fato, não alerta |
| `informacao_de_hoje` | **Informação de hoje (fora da data de referência)** (regra de 09/11/2026): o que vem de dados de hoje, e não do que era público na data, não entra na visão "como era". Fica numa seção separada no fim, com esse título: hoje, a situação no cadastro de companhias abertas da CVM, com a fonte. No PDF, é a última seção antes do anexo |
| `como_o_motor_foi_testado` | Ligação para o resultado do estudo 1, como saiu ([`docs/resumo.md`](resumo.md)) |
| `limitacoes` | Gerais e do caso |
| `motor`, `gerado_em`, `aviso` | Versão do motor, data e hora, aviso fixo |

## 3. Famílias de sinais, sem soma entre elas

| Família | Sinais | Papel | Fonte | Gera alerta? |
| --- | --- | --- | --- | --- |
| Possível manipulação | Motor v1 (estudo 1): os oito componentes do M-score e o M, o salto do DPO, o juro implícito, o lucro sem caixa (só contexto, como no estudo) e, nas financeiras, o peso não recorrente | Alerta do motor v1, sempre com o contexto e com o resultado do estudo 1 ao lado | Pré-registro, seção 4, e emendas 1 a 11 | Sim, pela regra do estudo 1, sem mudança |
| Risco financeiro | Altman Z'' puro, para empresas não industriais e mercados emergentes, sem a constante do Emerging Market Score e sem zonas | Contexto descritivo | Altman (2000), "Predicting Financial Distress of Companies: Revisiting the Z-Score and ZETA Models", p. 27, em `referencias/` ([`docs/referencias.md`](referencias.md)) | Não |
| Qualidade financeira | Piotroski F (2000), nove testes binários | Contexto descritivo | Piotroski (2000), Journal of Accounting Research, pp. 7-10, em `referencias/` ([`docs/referencias.md`](referencias.md)) | Não |

- O salto do DPO e o juro implícito ficam na família de possível manipulação, como no motor v1 (decisão de 07/11/2026). Explicações alternativas obrigatórias no Achado, com fonte quando houver: no juro implícito, dívida cara, variação cambial e juros de arrendamento dentro da despesa financeira; no DPO, poder de negociação com fornecedores e mudança de mix de compras.
- **Altman Z''** (decisão de 07/11/2026; especificação de 08/11/2026, com as páginas informadas por Roberto e o PDF em `referencias/`). Família risco financeiro, só contexto:
  - fórmula (Altman 2000, p. 27): Z'' = 6,56·X1 + 3,26·X2 + 6,72·X3 + 1,05·X4, com X1 = (1.01 − 2.01) ÷ 1; X2 = (2.03.04 + 2.03.05) ÷ 1; X3 = 3.05 ÷ 1; X4 = 2.03 ÷ (2.01 + 2.02). Os códigos são do plano das não financeiras (1 = ativo total; 3.05 = resultado antes do resultado financeiro e dos tributos; 2.03 = patrimônio líquido consolidado, com não controladores);
  - X2 é **adaptação brasileira**: desde a Lei 11.638/2007, a S.A. não fecha o ano com saldo positivo em lucros acumulados, porque o lucro retido vai para as reservas de lucros (2.03.04) e o saldo restante fica em lucros ou prejuízos acumulados (2.03.05). Contas fixas, a confirmar e localizar por texto se variarem. Reservas de capital e ajustes de avaliação patrimonial não entram. A marca de adaptação vai na linhagem e no catálogo;
  - sem a constante +3,25 e sem a tabela de rating (pp. 27-29). Um teste falha se 3,25 aparecer no cálculo do Z'';
  - sem zonas para o Z''. As zonas 1,23 e 2,90 (p. 26) são do Z' e não se usam. A página mostra o valor, o percentil no setor e no ano e a frase "sem zona de corte: a fonte disponível não define zonas para o Z''". **Isto muda a decisão de 07/11/2026**, que previa mostrar as zonas do artigo original;
  - o percentil segue o "como era": só entram as DFPs públicas na data de referência. Se o setor tiver menos de 10 empresas, o percentil usa o universo das não financeiras, com marca;
  - financeiras: "não se aplica";
  - nota de validade, sempre ao lado do valor: "coeficientes estimados fora do Brasil; modelos de falência perdem validade com o tempo (Pereira e Martins 2015, p. 25)";
  - entrada nova no catálogo, família risco financeiro, fase `contexto_v2`, nome e descrição em PT e EN; nenhuma entrada do motor v1 muda;
  - exemplo resolvido próprio da v2 (não o `data/exemplo_resolvido.json` do estudo 1), com o caso de lucros acumulados zerados e reservas positivas, e um teste que falha se o X2 usar só lucros acumulados;
  - não fazer: usar as zonas do Z' no Z'' ou os coeficientes de Altman, Baidya e Dias (1979) como régua.
- **Piotroski F** (decisão de 07/11/2026; especificação de 08/11/2026, com as páginas informadas por Roberto e o PDF em `referencias/`). Família qualidade financeira, só contexto. Nove sinais binários (Piotroski 2000, pp. 7-10), com AT início = ativo total de t−1 e AT médio = média do ativo total de t e t−1:
  1. ROA > 0, com ROA = 3.09 ÷ AT início;
  2. CFO > 0, com CFO = 6.01 (como apresentado) ÷ AT início;
  3. ΔROA > 0;
  4. ACCRUAL: CFO ÷ AT início > ROA;
  5. ΔLEVER < 0, com alavancagem = 2.02.01 ÷ AT médio. Dívida de longo prazo zero nos dois anos: sinal 0, com a marca "sem dívida de longo prazo nos dois anos" na linhagem (decisão de Roberto, 08/11/2026). O artigo só define "caiu = 1, subiu = 0" (p. 8) e não define o empate; o 0 no empate é escolha do projeto. O relatório da implementação conta os casos;
  6. ΔLIQUID > 0, com liquidez = 1.01 ÷ 2.01;
  7. EQ_OFFER: 1 se não houve emissão de ações no ano, pela linha de emissão da DFC achada por texto (padrões congelados da parte 4.2 do reconhecimento), com os códigos de conta registrados; sem a linha, "não calculável". Implementado na C2: entre as linhas do padrão congelado, só as de ações ou capital (palavra inteira), porque o padrão também pega captação de empréstimos; soma positiva é emissão (0), soma zero é não emissão (1); sem linha ou com soma negativa, não calculável. Rótulo (corrigido em 09/11/2026): contar só linhas de ações ou capital é a definição do próprio artigo ("did not issue common equity", p. 9), não uma adaptação. A adaptação, marcada no resultado, é só esta: ações preferenciais também contam, porque no Brasil são capital próprio, e a linha é identificada por texto na DFC;
  8. ΔMARGIN > 0, com margem = 3.03 ÷ 3.01;
  9. ΔTURN > 0, com giro = 3.01 ÷ AT início.
  - os valores de t−1 vêm do comparativo da DFP de t; os de t−2, da DFP de t−1 na versão pública na data de referência. As duas origens ficam na Linhagem;
  - a página mostra "F = x/9 (y calculáveis)"; componente que falta não é imputado;
  - financeiras: "não se aplica";
  - o nome da família é "qualidade financeira", não "qualidade do lucro";
  - entrada nova no catálogo, família qualidade financeira, fase `contexto_v2`.
- **Seção "Limites" da página de investigação** (texto fixo, 08/11/2026). O texto sai de `chiocca.v2.limites`, com os números lidos da saída do estudo 1, e um teste confere que é igual ao daqui:
  - Não ter alerta não é atestado. Em Dechow, Sloan e Sweeney (1995), o modelo de accruals com mais poder rejeitou 'sem manipulação' em só 28,1% de 32 empresas punidas pela SEC (Tabela 7, p. 32).
  - No estudo 1, 49,9% das empresa-anos não financeiras avaliadas (48,3% incluindo as financeiras) ficaram em alerta, e o número de acertos não superou o acaso num teste descritivo feito depois do resultado: 7 acertos em 13 casos acertáveis, contra 7,37 esperados ao acaso sem supor anos independentes (8,56 supondo anos independentes).
  - Os modelos de risco usam números que podem estar manipulados (Pereira e Martins 2015, p. 29). Por isso as três famílias não se somam.
- O catálogo já tem um `fscore_dechow` (Dechow e outros, 2011), que mede outra coisa (probabilidade de reapresentação) e é sinal da fase 2 do catálogo. Ele não entra nesta etapa, e os nomes não se confundem.

## 4. Data de referência, versões e corte transversal

- **Versão:** para cada empresa e exercício, a mais recente entregue até a data de referência (`como_era` com `corte = data_referencia`). Consolidado quando existir; senão, individual. Versões anteriores vêm do ENET, só no consolidado. O t−1 vem do PENÚLTIMO da mesma DFP.
- **Corte transversal:** os decis do motor v1 (salto do DPO e peso não recorrente) e os percentis de contexto são recalculados com as empresas cuja versão era pública na data de referência. É a mesma regra do estudo 1, aplicada à informação daquela data.
- **Reapresentação pelo comparativo** (regra de 09/11/2026, registrada antes da implementação; não muda nenhum cálculo nem alerta do motor v1):
  - quando, na data de referência, já existe a DFP do exercício seguinte (versão pública na data, pelo `como_era`), cada conta do exercício t na versão usada (coluna ÚLTIMO) é comparada com a coluna PENÚLTIMO da DFP de t+1;
  - a comparação é pela mesma demonstração (a DFC pelo prefixo, porque o método pode mudar) e pelo mesmo código de conta, no mesmo tipo (consolidado com consolidado, individual com individual). Conta que só existe numa das colunas não entra, porque o plano de contas pode mudar;
  - tolerância: R$ 1.000 por conta, a mesma das conferências (`TOLERANCIA_POR_PARCELA`). Diferença acima disso vai para a investigação como evidência, com o texto neutro "valor diferente no comparativo do ano seguinte (reapresentação ou reclassificação)", as duas versões, as duas datas de entrega, os dois valores e a diferença;
  - não se aplica quando a DFP de t+1 não tem versão pública na data, quando uma das duas leituras não tem situação ok ou quando os tipos diferem. Pelo lacre, t+1 vai até 2023: o exercício de 2023 não tem comparação.
- **Materialidade das diferenças do comparativo** (regra de 09/11/2026, registrada antes da implementação; não muda nenhum cálculo nem alerta do motor v1, e nada aqui vira sinal de alerta):
  - as diferenças acima da tolerância se separam em dois grupos. Grupo (a), totais e linhas-chave: ativo total (BPA 1), passivo circulante (BPP 2.01), passivo não circulante (BPP 2.02), patrimônio líquido (BPP 2.03), receita líquida (DRE 3.01), lucro líquido (DRE 3.11) e caixa operacional (DFC 6.01), com os mesmos códigos do motor v1 (`chiocca/variaveis.py`). Grupo (b), reclassificações: diferenças nas demais linhas, que não mudam os totais; quando um total também muda, a diferença dele aparece no grupo (a);
  - destacada: diferença do grupo (a) com valor absoluto acima de 1% do ativo total (BPA 1, coluna ÚLTIMO) da versão usada de t. Sem ativo total positivo na versão usada, nada é destacado;
  - a investigação mostra em destaque só as diferenças destacadas, com o mesmo texto neutro; todas as diferenças (as dos dois grupos, com o grupo de cada uma) ficam na lista completa de evidências;
  - nas financeiras, o plano de contas da DRE é outro, e os códigos 3.01 e 3.11 podem ser outras linhas; o rótulo mostrado é sempre a descrição da própria conta;
  - descritivo: quantas empresa-anos têm diferença destacada em 31/12/2024, em [`docs/armazenamento-temporal.md`](armazenamento-temporal.md), gerado pelo `chiocca/v2/invariante.py`.
- **Invariante testável:** com a data de referência igual à data de corte do exercício, os sinais e alertas do motor v1 coincidem com os do estudo 1 (`resultados/sinais_empresa_ano.csv`). Implementado na C1 (`chiocca/v2/invariante.py`), com o resultado em [`docs/armazenamento-temporal.md`](armazenamento-temporal.md).
- **Armazenamento:** DuckDB sobre Parquet, montado a partir de `data/brutos` (já conferido por hash) e de `data/cache/enet`. Tabelas: `versoes` (metadados de todas as versões de DFP até o lacre), `contas` (por versão disponível), `fca` e `cadastro`. Uma versão que não está armazenada sai como `versao_pendente_enet`. A busca no ENET acontece por comando separado, nunca dentro de uma consulta da API (pergunta 9 do plano). Implementado na C1 (`chiocca/v2/armazem.py`), com uma regra a mais: de documento entregue depois de 31/12/2024, o armazém guarda só metadados e a estrutura (quais demonstrações existem), sem nenhuma conta nem valor; o `como_era` usa essa estrutura da última versão para decidir a rota do ENET (emenda 8). Decisão de 09/11/2026: a estrutura conta como metadado; um teste garante que nenhuma conta nem valor desses documentos é guardado, e, quando o motor numa data usa estrutura lida de documento entregue depois dessa data, a linhagem registra "estrutura lida de documento posterior à data (comportamento do estudo 1, emenda 8)". Documentos entregues depois de 31/12/2024 com só a estrutura no armazém, por exercício: 2023: 14 (total: 14). Busca no ENET por comando separado: `python -m chiocca.v2.buscar_enet` (C2).

## 5. Saídas

- **JSON:** o contrato acima, com Pydantic na Fase D e os mesmos números do motor.
- **PDF:** texto e tabelas, nas duas línguas, gerado sem dependência (adaptado de `pdf_simples.py`, DireitoAberto), com o aviso fixo em todas as páginas.
- Nenhuma lista de empresas ordenada por risco, em nenhuma saída.

## 6. API (Fase D)

Implementada em `chiocca/v2/api.py` (FastAPI), com os contratos em Pydantic em `chiocca/v2/modelos.py`, do mesmo modelo do JSON da Fase C: a API não recalcula nada, valida o JSON de `chiocca.v2.investigacao.gerar` contra o modelo (campos desconhecidos são recusados) e devolve os mesmos números do motor. Todas as rotas são GET, sob `/api/v1`, e toda resposta traz a data de referência e o aviso fixo.

| Rota | Resposta |
| --- | --- |
| `/saude` | Lacre, intervalo de datas, exercícios e linhas do armazém, versões do motor |
| `/empresas?busca=&data_referencia=&limite=` | Busca de empresas (`BuscaEmpresas`): só por nome (3 caracteres ou mais, sem acento e sem diferença de maiúsculas), código CVM (até 6 dígitos) ou CNPJ (14 dígitos, com ou sem pontuação); até 50 resultados |
| `/empresas/{cd_cvm}?data_referencia=` | A empresa na data (`Empresa`, com o nome da época, setor, grupo e códigos de negociação) e os exercícios com DFP entregue até a data |
| `/empresas/{cd_cvm}/exercicios/{exercicio}?data_referencia=` | `ExercicioNaData` com as evidências (as linhas da DFP na versão usada) |
| `/investigacoes/{cd_cvm}/{exercicio}?data_referencia=&idioma=` | `Investigacao`, o mesmo JSON da seção 2 |
| `/investigacoes/{cd_cvm}/{exercicio}/pdf?…` | O PDF gerado só desse JSON |
| `/investigacoes/{cd_cvm}/{exercicio}/linhagem/{sinal}?…` | A linhagem de um número, com as evidências que ela cita |
| `/como-o-motor-foi-testado` | Os números do estudo 1, do mesmo JSON do resumo (os mesmos da [ficha do motor](ficha-do-motor.md)), com a antecedência dos acertos (Fase E) |

- **Validações:** as mesmas do contrato. Data de referência de 30/04/2011 a 31/12/2024 (sem data, a máxima) e exercício até 2023 (lacre); fora disso, a recusa (422) traz o motivo (`data_fora_do_intervalo`, `exercicio_lacrado`). Empresa ou exercício sem DFP entregue até a data: 404 com o motivo. Requisição com query string acima de 2.048 caracteres (414) ou com corpo acima de 16.384 bytes (413) é recusada.
- **Regra de 09/11/2026:** nenhum endpoint lista empresas ordenadas por alerta, percentil ou escore. A busca é só por nome, código CVM ou CNPJ (não por código de negociação, que só aparece como informação da empresa), a lista de empresas só sai da busca, sempre em ordem alfabética da denominação, e o resultado da busca não traz nenhum sinal. Nenhuma rota aceita parâmetro de ordenação. Um teste (`tests/test_v2_api.py`) confere as rotas, os parâmetros, o esquema OpenAPI e a ordem da busca.
- **Nome da época na busca:** o nome mostrado e os nomes pesquisados são os do FCA entregue até a data; sem FCA, o do índice da DFP, marcado em `origem_denominacao`. Assim, uma empresa não é achada por um nome que só teve depois da data.
- **Sem rede:** a API lê só o armazém; versão que falta sai como `versao_pendente_enet` (a busca no ENET é o comando separado da C2). Os testes de contrato rodam com o armazém da fixture e com a rede bloqueada.
- **Modo demonstração** (Fase E, ligado por `CHIOCCA_MODO_DEMONSTRACAO=1`): a busca e as rotas por empresa só aceitam as companhias dos casos do gabarito (`data/gabarito_casos.csv`, que pela regra do pré-registro só tem condenação da CVM ou fraude admitida), sem os casos em observação; as outras são recusadas (403, `fora_do_modo_demonstracao`) com o motivo. `/saude` diz se o modo está ligado. Padrão inspirado no FraudShield (MIT), sem código copiado.
- **Uso:** `python -m chiocca.v2.api [porta]` (uvicorn em 127.0.0.1; documentação interativa em `/api/v1/docs`).
