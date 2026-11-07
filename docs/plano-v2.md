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
- Famílias de risco financeiro (Altman Z'') e qualidade financeira (Piotroski F), depois de transcrever as fórmulas da fonte primária para `docs/fontes.md`. Só contexto descritivo.
- "O que mudou", "o que se sabia na data", explicações alternativas e limitações, com um catálogo de textos PT e EN que cita fontes.
- Saídas em JSON e PDF, nas duas línguas.
- Testes de ponta a ponta: Americanas em 31/03/2022 e uma empresa sem nenhum caso no gabarito.
- Tamanho: cerca de 2.200 linhas e 60 testes. É a fase maior; se você preferir, ela se divide em C1 (armazenamento temporal e motor v1 na data) e C2 (famílias, contexto e saídas), com parada entre as duas.

## Fase D: API

- FastAPI em `/api/v1`: `saude`, busca de empresas (nome, código CVM, CNPJ ou código de negociação), investigação por empresa e data, linhagem de cada número e PDF.
- Contratos em Pydantic, gerados do mesmo modelo da Fase C; testes da API com os mesmos números do motor.
- Recusa de exercício acima do lacre e de data fora do intervalo, com o motivo; limite de tamanho de requisição.
- Tamanho: cerca de 600 linhas e 30 testes.

## Fase E: interface

- Next.js (estrutura e componentes adaptados do DireitoAberto): busca, seletor de data de referência limitado ao lacre, página da investigação, linha do tempo dos sinais, evidência clicável, comparação com pares do setor (agregada, sem ranking), exportação em PDF e a página "Como o motor foi testado" com o resumo do estudo 1.
- Modo escuro, celular, PT e EN; aviso fixo em todas as telas.
- CI com build e checagem de tipos do web. O deploy (Vercel, Render ou outro) é decisão sua nesta fase.
- Tamanho: cerca de 2.000 linhas de TypeScript e testes de build e de contrato com a API.

## Fase F: inteligência documental v0

- Monitor da CVM: o registro de versões do DireitoAberto, com fila de revisão e reversão, adaptado aos índices de DFP, ITR e IPE. Hash e classificação de cada novidade (DFP nova, reapresentação, ITR, fato relevante), sem calcular sinais acima do lacre. Uma pessoa decide; nada muda os dados sozinho.
- Leitor extrativo de fatos relevantes, notas explicativas e do `parecer` da DFP: partes relacionadas, risco sacado ou forfait, troca de auditor (FCA `auditor`), ressalvas e garantias. Cada trecho vem com página e conferência literal.
- Conjunto adversarial próprio, com documentos fictícios e gabarito, medido como no DireitoAberto.
- LLM só opcional, com toda citação passando pela mesma conferência. Sem chave, tudo funciona em modo extrativo.
- Tamanho: cerca de 1.800 linhas e 50 testes.

## Perguntas para você decidir

1. **Data de referência máxima e mínima.** Proposta: máxima em 31/12/2024 e mínima em 30/04/2011, a primeira data de corte com DFP de 2010.
2. **Documentos entregues depois da data máxima** (fatos relevantes, ITR, comunicados). Proposta: o monitor registra só metadados e hash, sem ler nem resumir. Um fato relevante de 2024 ou depois pode revelar casos que o estudo 2 vai testar.
3. **Salto do DPO e juro implícito na família de possível manipulação**, como no motor v1. Proposta: sim, porque separá-los mudaria a regra "em alerta" do estudo 1.
4. **Confiança categórica, sem nota numérica.** Proposta: sim.
5. **PDF sem dependência** (gerador do DireitoAberto, só texto e tabelas) agora, em vez de matplotlib. Proposta: sim; gráficos ficam na interface.
6. **Teste binomial sobre o estudo 1** (adaptado do Kupiec da Calahonda). É uma estatística nova, não pré-registrada. Proposta: só com a sua autorização, e rotulada como descritiva, calculada depois do estudo.
7. **Parâmetros de exibição:** `n` mínimo de 10 empresas para o percentil no setor e 5 exercícios para o histórico. Não são regras do motor e não criam alerta.
8. **Organização:** pacote `chiocca/v2/` e interface em `web/`.
9. **Busca no ENET** de versões que não estão no armazenamento. Proposta: só por comando separado; a API responde `versao_pendente_enet` e nunca baixa nada dentro de uma consulta.
10. **Altman Z'' e Piotroski F:** a fonte primária (artigo ou livro) precisa estar acessível para transcrever as fórmulas. Se você tiver os PDFs, eles entram em `referencias/` (fora do git); senão, busco as fontes publicadas e registro em `docs/fontes.md`.
