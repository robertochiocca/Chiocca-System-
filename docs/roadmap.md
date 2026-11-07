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
- Machine learning (Isolation Forest, XGBoost) só com base rotulada confiável, validação fora da amostra e comparação contra o motor v1 e a regra boba.
- Cortes por setor ou recalibrados para o Brasil, sempre com pré-registro.

## Produto, depois da Fase F

- Docker e deploy com observabilidade.
- Comparação de versões de notas explicativas entre exercícios.
- Monte Carlo e cenários de stress só como teste de robustez dos indicadores, nunca como detector.
