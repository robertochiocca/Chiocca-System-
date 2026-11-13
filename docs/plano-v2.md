# Plano do Chiocca System v2: fases B a F

Proposta da Fase A. Cada fase termina com código e testes passando, documentação em PT e EN, hash do commit e `git ls-remote`. Depois para e espera a sua autorização por escrito.

As estimativas são ordens de grandeza para comparar as fases (linhas de código novo, sem contar testes, e número de testes), não promessas.

## Organização do código

- `chiocca/v2/`: o produto em Python. Não altera nenhum módulo do estudo 1; só os chama.
- `web/`: a interface em Next.js (Fase E).
- Cada arquivo trazido de outro projeto leva no topo o projeto de origem, o caminho, o commit e "adaptado para o Chiocca System", e entra em [`docs/origem-do-codigo.md`](origem-do-codigo.md).
- Dependências novas só quando a fase precisar: DuckDB (C), FastAPI e Pydantic (D), Node e Next.js (E), leitor de PDF (F).

## Fase B: motor de confiança

- `validade.py`: estados ok, indefinido e implausível (classe e `variacao_percentual` da Carchuna), com a ponte para o "não calculável" do motor v1.
- `conferencias.py`: conferências dos dados da CVM, com tolerância e evidências: balanço que não fecha (ativo contra passivo mais patrimônio líquido), subtotais da DRE, DFC que não reconcilia com a variação do caixa no balanço e valores implausíveis (por exemplo, ativo total negativo ou nulo).
- `linhagem.py`: a ficha "como cheguei a este número" para cada sinal do motor v1, até a linha da DFP (dados abertos ou ENET), com as transformações do estudo 1 (escala, juros pagos, deduplicação, padrões de texto da DFC).
- `confianca.py`: os cinco critérios e o nível categórico, sem nota.
- Relatório agregado, PT e EN: quantas empresa-anos até 2023 falham em cada conferência. Só números agregados.
- CI no GitHub Actions: ruff, black, mypy e pytest (adaptado do DireitoAberto). O repositório ainda não tem CI.
- Tamanho: cerca de 900 linhas e 45 testes.

## Fase C: investigação por empresa

- Armazenamento temporal: DuckDB sobre Parquet com versões, contas, FCA e cadastro até o lacre, montado de `data/brutos` e `data/cache/enet`.
- `ExercicioNaData` em qualquer data de referência e o corte transversal na mesma data (decis do motor v1 e percentis).
- Teste do invariante: na data de corte de cada exercício, os sinais e alertas coincidem com os do estudo 1.
- Contexto: percentil no setor e no grupo, histórico com a cerca de IQR (detecção da Carchuna).
- Famílias de risco financeiro (Altman Z'') e qualidade financeira (Piotroski F), com as fórmulas e as páginas em `docs/contratos.md` (seção 3) e as obras em `docs/referencias.md`. Só contexto descritivo.
- "O que mudou", "o que se sabia na data", explicações alternativas e limitações, com um catálogo de textos PT e EN que cita fontes.
- Saídas em JSON e PDF, nas duas línguas.
- Testes de ponta a ponta: Americanas em 31/03/2022 e uma empresa sem nenhum caso no gabarito.
- Tamanho: cerca de 2.200 linhas e 60 testes. É a fase maior; se você preferir, ela se divide em C1 (armazenamento temporal e motor v1 na data) e C2 (famílias, contexto e saídas), com parada entre as duas.

## Fase D: API

- FastAPI em `/api/v1`: `saude`, busca de empresas (nome, código CVM, CNPJ ou código de negociação), investigação por empresa e data, linhagem de cada número e PDF.
- Contratos em Pydantic, gerados do mesmo modelo da Fase C; testes da API com os mesmos números do motor.
- Recusa de exercício acima do lacre e de data fora do intervalo, com o motivo; limite de tamanho de requisição.
- Tamanho: cerca de 600 linhas e 30 testes.
- **Decisão de Roberto, 09/11/2026:** Fase D autorizada. Os endpoints espelham o JSON do contrato, com as mesmas validações (data de 30/04/2011 a 31/12/2024; exercício até 2023). Nenhum endpoint lista empresas ordenadas por alerta, percentil ou escore; a busca é só por nome, código CVM ou CNPJ (o código de negociação sai da busca e fica só como informação da empresa). Testes de contrato sem rede.
- **Concluída em 09/11/2026:** `chiocca/v2/api.py`, `chiocca/v2/modelos.py` e `chiocca/v2/busca.py`, com o campo `codigos_negociacao` (tabela `valores_mobiliarios` do armazém); rotas e regras em [`docs/contratos.md`](contratos.md), seção 6; testes em `tests/test_v2_api.py`.

## Fase E: interface

- Next.js (estrutura e componentes adaptados do DireitoAberto): busca, seletor de data de referência limitado ao lacre, página da investigação, linha do tempo dos sinais, evidência clicável, comparação com pares do setor (agregada, sem ranking), exportação em PDF e a página "Como o motor foi testado" com o resumo do estudo 1.
- Modo escuro, celular, PT e EN; aviso fixo em todas as telas.
- CI com build e checagem de tipos do web. O deploy (Vercel, Render ou outro) é decisão sua nesta fase.
- Tamanho: cerca de 2.000 linhas de TypeScript e testes de build e de contrato com a API.
- **Decisão de Roberto, 09/11/2026:** Fase E autorizada, com as regras da API, comparação com o setor só agregada, data até 31/12/2024 e exercício até 2023, "Informação de hoje" separada, aviso fixo, PT e EN, modo escuro e celular, página "Como o motor foi testado" do mesmo JSON do resumo, CI com build, tipos, testes de contrato e npm audit, e nenhum deploy: só um modo demonstração ligado por configuração.
- **Concluída em 09/11/2026:** `web/` (Next.js 16.4.3, React 19.2.9, TypeScript 5.9.3; o Next 15 trazia um postcss com vulnerabilidade alta no `npm audit`), regras em [`docs/contratos.md`](contratos.md), seção 7; modo demonstração na API (`CHIOCCA_MODO_DEMONSTRACAO`). O deploy espera a escolha de Roberto.
- **Resposta à Fase E, 10/11/2026:** ajustes da interface (rótulos no lugar de códigos, menu do celular, aviso de diferença destacada, faixa de Tukey, caminhos como links), com teste de tela; demonstração estática gerada por script (`chiocca/v2/demonstracao_estatica.py`), deploy preferido de Roberto, que publica depois de ver o relatório.
- **Segunda rodada, 10/11/2026:** rótulos dos sinais do Piotroski F, sinal de menos na exibição da v2 (tela e PDF) e publicação no GitHub Pages pelo branch gerado `gh-pages` ([`docs/contratos.md`](contratos.md), seção 7).
- **Fase E2, experiência e explicação (autorizada em 10/11/2026):** cabeçalho, página inicial, empresa, investigação com resumo, índice e cartões explicados, "Como o motor foi testado" como página de explicação, celular, acessibilidade com axe e capturas para revisão ([`docs/contratos.md`](contratos.md), seção 7).

## Fase F: inteligência documental v0

- Monitor da CVM: o registro de versões do DireitoAberto, com fila de revisão e reversão, adaptado aos índices de DFP, ITR e IPE. Hash e classificação de cada novidade (DFP nova, reapresentação, ITR, fato relevante), sem calcular sinais acima do lacre. Uma pessoa decide; nada muda os dados sozinho.
- Leitor extrativo de fatos relevantes, notas explicativas e do `parecer` da DFP: partes relacionadas, risco sacado ou forfait, troca de auditor (FCA `auditor`), ressalvas e garantias. Cada trecho vem com página e conferência literal.
- Conjunto adversarial próprio, com documentos fictícios e gabarito, medido como no DireitoAberto.
- LLM só opcional, com toda citação passando pela mesma conferência. Sem chave, tudo funciona em modo extrativo.
- Tamanho: cerca de 1.800 linhas e 50 testes.
- **Plano aprovado por Roberto em 11/11/2026, em duas partes, com parada entre elas:**
  - *F1:* leitor extrativo das notas explicativas da DFP (partes relacionadas pelos itens 18 e 19 do CPC 05, lendo também as colunas da controladora; risco sacado ou forfait), do relatório do auditor da versão usada e da tabela de partes relacionadas do Formulário de Referência; o núcleo do conjunto adversarial; pypdf com versão fixa no lock. Pré-registro da medida em [`docs/pre-registro-leitor.md`](pre-registro-leitor.md), antes de qualquer código; casos guardados escritos por Roberto com o Claude (claude.ai), fora deste ambiente e sem acesso ao código de detecção do leitor (para o formato e as convenções, foram lidos o pré-registro, `avaliacao.py`, `pdf_simples.py` e os casos de desenvolvimento), medidos uma vez com o leitor congelado (limite: o leitor e os casos foram escritos por instâncias do mesmo modelo, em ambientes separados; a separação é de informação, não de autor); abaixo da meta, a seção fica desligada. Contrato em [`docs/contratos.md`](contratos.md), seção 8.
  - *F2:* monitor da CVM (só metadados e hash para documentos depois de 31/12/2024), a lista de fatos relevantes e comunicados entregues até a data (data de entrega, categoria, assunto e link, sem leitura do conteúdo) na seção "O que se sabia na data" e o conjunto adversarial ampliado, medido de novo.
  - *Leitor congelado em 11/11/2026* no commit `c99c9538c90f9574f372dddee03bf17757929220` (`leitor-f1-1`), com o SHA-256 de cada arquivo em [`docs/leitor_congelado.json`](leitor_congelado.json) e um teste que falha se algum mudar. Aguarda os casos guardados.
  - *Medida nos casos guardados em 11/11/2026:* uma única vez, sobre o leitor congelado; precisão de 0,962, cobertura de 0,962, conferência literal em 132 de 132 trechos e nenhum nome vazado. As quatro metas foram atingidas e a seção foi ligada ([`docs/contratos.md`](contratos.md), seção 8).
  - *Exibição, 11/11/2026, depois da medida (sem mudar o leitor nem os trechos do JSON):* título "Trechos dos documentos (copiados; não gera alerta)", com as subseções Notas explicativas, Relatório do auditor e Formulário de Referência; rótulos juntos no mesmo trecho; omitidos da mesma página numa linha só; "Como o leitor foi testado" e os limites na seção; o leitor na linha "Motor"; sem Δ no PDF.
  - *Próxima versão do leitor (`leitor-f1-2`), só registrada, sem código:* separar "a Companhia é controlada (em conjunto) por" das menções a controladas e joint ventures; não contar "na qualidade de controladora" quando fala da própria Companhia; reconhecer frases de montante ("somou R$ … no exercício") e de prazo ("vence em …"); tirar o ruído de cabeçalho de tabela (anos e títulos de coluna que saem como trecho). Exige emenda ao pré-registro atual, com as mesmas metas, e casos guardados novos, escritos por Roberto com tabelas no formato real. Até lá, vale a medida de `leitor-f1-1`.
  - *F2a, 12/11/2026:* a lista de fatos relevantes e comunicados ao mercado (IPE) em "O que se sabia na data", só com metadados, e o monitor da CVM, com fila de revisão ([`docs/contratos.md`](contratos.md), seção 9). Os documentos entregues em 2024 entram na lista para datas de 2024, como as DFP entregues em 2024: a lista não calcula nada, e o lacre é por exercício. Nada entregue depois de 31/12/2024 aparece em investigação, demonstração ou resposta da API; o monitor guarda desses documentos só metadados e hash, sem o assunto. Ajustes aprovados em 12/11/2026, antes de publicar: o detector do leitor fica sem mudança e só entram regras que omitem mais (assunto todo em maiúsculas; palavra com inicial maiúscula fora do começo e fora das exceções); assunto vazio com aviso; versões e documentos repetidos numa linha só, com um link para cada um, e contagens em documentos; aviso nos links de 2010 a 2014; investigações da demonstração sem carimbo de hora, com a data da geração só no manifesto. Uma regra própria para o assunto só entra medida, na F2b.
  - *F2b:* emenda 1 ao pré-registro registrada em 13/11/2026, antes de qualquer código ([`docs/pre-registro-leitor.md`](pre-registro-leitor.md), seção 10): `leitor-f1-2` com as mesmas quatro metas e a regra própria para o assunto do IPE, com zero nome de pessoa e omissão indevida de no máximo 0,20. Decisões de Roberto antes de qualquer código na seção 10.7. Congeladas em 13/11/2026 no commit `dd688dadf9a1f0bc43b4ba1d02fd2f5ad0c0d0db` ([`docs/leitor_congelado_f1_2.json`](leitor_congelado_f1_2.json), com o SHA-256 de cada arquivo e o teste que acusa mudança): a `leitor-f1-2` fica num pacote próprio (`chiocca/v2/leitor_f1_2/`), ao lado da `leitor-f1-1`, que não muda e continua na seção, nos exemplos e na demonstração; a regra do assunto também fica ao lado das regras de hoje até a medida e a auditoria. A medida usa o avaliador novo (`python -m chiocca.v2.leitor_f1_2.avaliar <pasta>`), que mede as duas versões do leitor e os arquivos `assuntos_`; o comando da `leitor-f1-1` faz parte dos arquivos congelados dela e não muda. O resultado nos casos de desenvolvimento, informativo, está em [`docs/leitor_desenvolvimento_f1_2.json`](leitor_desenvolvimento_f1_2.json). Notas de procedimento antes da medida, com o comando e o hash do congelamento, na seção 10.8. **Medida em 13/11/2026**, uma única vez, nos 22 casos guardados novos e nos 4 arquivos de assunto (335 assuntos) escritos por Roberto depois do congelamento ([`docs/leitor_medida_f1_2.json`](leitor_medida_f1_2.json), como saiu): a `leitor-f1-2` atingiu as quatro metas e o critério de troca saiu verdadeiro, e a regra do assunto atingiu as duas metas e passou na auditoria de 400 assuntos reais ([`docs/assunto_auditoria.json`](assunto_auditoria.json)). Desde então a seção de trechos usa a `leitor-f1-2` e a lista do IPE usa a regra nova ([`docs/contratos.md`](contratos.md), seções 8 e 9). Decisão de Roberto depois da medida (13/11/2026): a troca fica, com o critério aplicado como registrado (três casas, no avaliador congelado antes da medida); a precisão empatou em 0,973 (sem arredondar, 0,9732 contra 0,9735; as duas versões com 3 unidades sem item), a cobertura foi de 0,915 contra 0,924 e os cabeçalhos que saem, 1 contra 14. **Lição:** em comparações futuras entre versões, o critério conta unidades sem item e itens encontrados, não proporções arredondadas.
  - *Próxima versão do leitor (`leitor-f1-3`), só registrada, sem código:* as linhas da tabela herdam o rótulo do cabeçalho em várias linhas (saldos e montante perdidos nos casos guardados h08, h09 e h10); frase com dois números não vira linha de tabela (frases cortadas no h06 e no h12); título e cabeçalho que viram um só parágrafo (h04); as variações que ficaram de fora ("subsidiária integral de", "na condição de controladora", "controle compartilhado", "vai até", "será quitado em"); e os erros conhecidos ("Encargos sociais" como termo, "% da receita" e "garante"). Para a regra do assunto: lugares com nome de pessoa pública e companhias do cadastro com nome de pessoa. Como nas versões anteriores: emenda ao pré-registro antes de qualquer código, casos de desenvolvimento novos, congelamento com hash e casos guardados novos.
  - *F2b, só depois da resposta à F2a:* o `leitor-f1-2` (o "conjunto adversarial ampliado, medido de novo"), com emenda ao pré-registro antes de qualquer código, as mesmas metas, casos de desenvolvimento novos com tabelas no formato real, congelamento com hash e casos guardados novos escritos por Roberto depois do congelamento; se a `leitor-f1-2` falhar, a seção continua com a `leitor-f1-1`. Os 20 casos guardados da `leitor-f1-1` já são públicos: medir a nova versão neles é só informativo.
  - *Decisões:* nomes de pessoa física viram "trecho omitido; ver página N do documento", com o detector errando para o lado de omitir; do Formulário de Referência, só a última versão entregue até a data; LLM fora da Fase F (no roadmap); acesso ao ENET uma requisição por vez, com intervalo, tentativas, integridade e cache fora do git.

## Perguntas e decisões

1. **Data de referência máxima e mínima.** Proposta: máxima em 31/12/2024 e mínima em 30/04/2011, a primeira data de corte com DFP de 2010.
   - **Decisão de Roberto, 07/11/2026:** de 30/04/2011 a 31/12/2024. O lacre segue por exercício: nada acima de 2023 é calculado, em nenhuma data.
2. **Documentos entregues depois da data máxima** (fatos relevantes, ITR, comunicados). Proposta: o monitor registra só metadados e hash, sem ler nem resumir. Um fato relevante de 2024 ou depois pode revelar casos que o estudo 2 vai testar.
   - **Decisão de Roberto, 07/11/2026:** o monitor registra só metadados e hash, sem ler, resumir ou extrair nada.
3. **Salto do DPO e juro implícito na família de possível manipulação**, como no motor v1. Proposta: sim, porque separá-los mudaria a regra "em alerta" do estudo 1.
   - **Decisão de Roberto, 07/11/2026:** ficam na família de manipulação; o invariante da Fase C continua valendo. Explicações alternativas no Achado, com fonte quando houver: no juro implícito, dívida cara, variação cambial e juros de arrendamento dentro da despesa financeira; no DPO, poder de negociação com fornecedores e mudança de mix de compras.
4. **Confiança categórica, sem nota numérica.** Proposta: sim.
   - **Aceita por padrão em 07/11/2026.**
5. **PDF sem dependência** (gerador do DireitoAberto, só texto e tabelas) agora, em vez de matplotlib. Proposta: sim; gráficos ficam na interface.
   - **Aceita por padrão em 07/11/2026.**
6. **Teste binomial sobre o estudo 1** (adaptado do Kupiec da Calahonda). É uma estatística nova, não pré-registrada. Proposta: só com a sua autorização, e rotulada como descritiva, calculada depois do estudo.
   - **Decisão de Roberto, 07/11/2026:** autorizado, como "análise descritiva depois do resultado, não pré-registrada", com a distribuição binomial de Poisson exata e sem scipy. A probabilidade de cada caso acertável ser acertado ao acaso é 1 − produto de (1 − taxa de alerta do grupo no ano) sobre os anos do período afetado, com as taxas observadas no estudo 1. Resultado em [`docs/analises-pos-estudo-1.md`](analises-pos-estudo-1.md), sem alterar nenhum arquivo do estudo 1.
7. **Parâmetros de exibição:** `n` mínimo de 10 empresas para o percentil no setor e 5 exercícios para o histórico. Não são regras do motor e não criam alerta.
   - **Aceita por padrão em 07/11/2026.**
8. **Organização:** pacote `chiocca/v2/` e interface em `web/`.
   - **Aceita por padrão em 07/11/2026.**
9. **Busca no ENET** de versões que não estão no armazenamento. Proposta: só por comando separado; a API responde `versao_pendente_enet` e nunca baixa nada dentro de uma consulta.
   - **Aceita por padrão em 07/11/2026.**
10. **Altman Z'' e Piotroski F:** a fonte primária (artigo ou livro) precisa estar acessível para transcrever as fórmulas. Se você tiver os PDFs, eles entram em `referencias/` (fora do git); senão, busco as fontes publicadas e registro em `docs/fontes.md`.
    - **Decisão de Roberto, 07/11/2026:** os PDFs de Altman (2000), "Predicting Financial Distress of Companies: Revisiting the Z-Score and ZETA Models", e de Piotroski (2000), Journal of Accounting Research, vão para `referencias/`. Nenhum coeficiente ou teste entra antes de conferido neles, com a página.
    - **08/11/2026:** fórmulas e páginas informadas por Roberto e registradas em `docs/contratos.md`, seção 3; obras em `docs/referencias.md`.

## Fase C dividida (decisão de Roberto, 07/11/2026)

- **C1:** armazenamento temporal, motor v1 em qualquer data e o invariante do estudo 1. Para.
  - **Concluída em 08/11/2026:** `chiocca/v2/armazem.py`, `chiocca/v2/na_data.py` e `chiocca/v2/invariante.py`, com o resultado em [`docs/armazenamento-temporal.md`](armazenamento-temporal.md).
  - **Primeira parte da C2, autorizada em 09/11/2026 e concluída:** `escala_original`, as contas da leitura numa data convertidas em evidências do contrato e o comando separado de busca no ENET (`chiocca/v2/buscar_enet.py`). O restante da C2 abaixo (contexto, Altman Z'', Piotroski F, parecer e auditor, seção "Limites" na página, JSON e PDF) foi autorizado em 09/11/2026 como "C2, segunda parte" e está concluído: `chiocca/v2/contexto.py`, `investigacao.py`, `pdf_simples.py`, `pdf_investigacao.py` e o exemplo da Americanas em `docs/exemplos/`.
- **C2:** contexto, Altman Z'', Piotroski F, JSON e PDF. Acréscimos:
  - **Parecer e auditor:** seção factual na Investigacao, com o tipo do parecer, trecho do texto da DFP conferido literalmente, auditor e trocas de auditor pelo FCA. Não é família de sinais e não gera nota nem alerta.
  - **Altman Z'':** especificação de 08/11/2026 em `docs/contratos.md`, seção 3: fórmula da p. 27 do Altman (2000), X2 como adaptação brasileira, sem a constante +3,25 e sem tabela de rating (teste falha se 3,25 aparecer), sem zonas (as de 1,23 e 2,90 são do Z'), percentil no setor e no ano pelo "como era" (universo das não financeiras se o setor tiver menos de 10 empresas), "não se aplica" em financeiras e nota de validade. Exemplo resolvido próprio da v2, com teste que falha se o X2 usar só lucros acumulados.
  - **Piotroski F:** especificação de 08/11/2026 em `docs/contratos.md`, seção 3: os nove sinais das pp. 7-10, com AT início = ativo total de t−1, t−2 da DFP de t−1 na versão pública na data, "F = x/9 (y calculáveis)" sem imputar componente, "não se aplica" em financeiras, regra e contagem dos casos de dívida de longo prazo zero nos dois anos, e EQ_OFFER pela linha de emissão da DFC, com os códigos registrados.
  - **Seção "Limites":** texto fixo de `chiocca.v2.limites` na página de investigação, em PT e EN (`docs/contratos.md`, seção 3).
  - **Não fazer:** usar as zonas do Z' no Z'' ou os coeficientes de 1979 como régua.
