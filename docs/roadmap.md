# Roadmap: ideias fora desta etapa

Anotadas para depois, sem compromisso. Nada aqui entra no produto v2 sem autorização, e nada muda o estudo 1.

## Estudo 2 (com os exercícios de 2024 em diante, hoje lacrados)

- Rodar o motor v1 sem mudança nos exercícios lacrados, como teste limpo, antes de qualquer melhoria.
- DEPI sem linha de depreciação na DFC: a DVA tem uma conta fixa "Depreciação, Amortização e Exaustão" (reconhecimento, parte 1.7), que pode resolver os casos de DFC pelo método direto. Exige novo pré-registro.
- Juro implícito: separar da despesa financeira a variação cambial e os juros de arrendamento, pelas notas explicativas, antes de comparar com o CDI.
- Dados trimestrais (ITR), para casos como o do IRB.
- Teste de retorno das ações, com `data.py`, `metrics.py` e `ratios.py` da Calahonda.
- F-score de Dechow e outros (2011), que já está no catálogo como sinal da fase 2.
- Validar no Brasil os indicadores de contexto (Altman Z'' e Piotroski F) antes de qualquer uso como alerta.
- Aprendizado supervisionado só exploratório: 13 casos acertáveis não bastam para treinar e validar um modelo, e nenhum texto do projeto afirma que machine learning ganha do logit. Qualquer modelo (Isolation Forest, XGBoost) só com base rotulada confiável, validação fora da amostra e comparação contra o motor v1 e a regra boba.
- Cortes por setor ou recalibrados para o Brasil, sempre com pré-registro.

Registrado em 08/11/2026, para o pré-registro novo do estudo 2, antes de abrir os exercícios de 2024 em diante:

- Accruals discricionários por setor e ano, pelo Jones modificado e pelo modelo de margem, com pelo menos 10 empresas por setor-ano (Peasnell, Pope e Young 2000, pp. 11 e 15). O Quadro 03 de Paulo (2007, p. 168) serve de lista de conferência.
- Dechow e Dichev (2002) só com defasagem, porque o modelo usa o caixa de t+1.
- Lucro logo acima de zero ou do lucro do ano anterior (Martinez 2001, pp. 72-80).
- Métricas de ranking: precisão no topo de 1%, 5% e 10% e NDCG@k, reimplementadas em Python a partir das definições de Bao et al. (2020, Tabela 3, p. 21) e conferidas contra o `evaluate.m` do JarFraud/FraudDetection, sem copiar código (o repositório não tem arquivo de licença), com testes que reproduzem um exemplo pequeno calculado à mão (correção de 09/11/2026).
- Lift no topo da lista, junto com a precisão no topo e o NDCG@k (09/11/2026).
- Intervalos de confiança por bootstrap pareado: motor e regra boba comparados nas mesmas reamostragens, com reamostragem por empresa, porque os alertas se repetem (73,8% das empresa-anos não financeiras em alerta também estavam em alerta no ano anterior; [análises](analises-pos-estudo-1.md), seção 2). Adaptado do `evaluate.py` do FraudShield (ARMAND-cod-eng/fraud-detection-ensemble, MIT), com cabeçalho de origem e registro em [`docs/origem-do-codigo.md`](origem-do-codigo.md); o arquivo e o commit exatos são conferidos na hora de adaptar (09/11/2026).
- Antecedência do alerta como métrica pré-registrada: no estudo 1 ela só existe como análise descritiva depois do resultado ([análises](analises-pos-estudo-1.md), seção 5) (09/11/2026).
- Intervalo de 24 meses entre o período de calibração e o de teste.
- Regra no pré-registro para casos que se estendem por vários anos, com teste automático para ano de dados faltando e para identificador de caso trocado: foi o erro que Walker apontou em 2021 em Bao et al. (2020) e que o erratum de 2022 reconheceu.

## Produto: indicadores de contexto (registrado em 08/11/2026)

Só contexto, sem alerta, e só depois de especificados no plano:

- Accruals ÷ ativo médio, com percentil (Sloan 1996, p. 6).
- SMTH1 = −σ(lucro ÷ AT) ÷ σ(CFO ÷ AT) em 5 anos, exigindo 5 DFPs públicas na data de referência (Gonçalves et al. 2024, pp. 10-11).

## Fase F: leitor de partes relacionadas (registrado em 08/11/2026)

- Campos do item 18 do CPC 05 (R1), organizados pelas categorias do item 19.
- Ler também a nota da controladora, porque a consolidação elimina as transações dentro do grupo (Gonçalves et al. 2024, p. 9).
- A frase "em condições de mercado" é registrada como fato, sem prova (item 23).
- Antes de começar a Fase F: verificar se os dados abertos do Formulário de Referência têm uma tabela estruturada de transações com partes relacionadas. Só verificar e relatar.

## Não fazer

- Não copiar o CSV do JarFraud/FraudDetection para o repositório: é derivado da Compustat.
- Não usar as zonas do Z' no Z'' nem os coeficientes de 1979 como régua.

## Revisar quando o Starlette mudar (registrado em 09/11/2026)

- Os testes da API usam o `TestClient` com o httpx, e o Starlette avisa que essa combinação está obsoleta e sugere o `httpx2`. O aviso fica como está; revisar quando o Starlette mudar (nova versão fixada no lock ou fim do suporte ao httpx).

## Produto, depois da Fase F

- Docker e deploy com observabilidade.
- Comparação de versões de notas explicativas entre exercícios.
- Monte Carlo e cenários de stress só como teste de robustez dos indicadores, nunca como detector.
