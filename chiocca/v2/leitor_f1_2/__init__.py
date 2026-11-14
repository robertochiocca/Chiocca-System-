"""Leitor de documentos, segunda versão (`leitor-f1-2`), e a regra própria para o assunto do IPE (Fase F2b).

Feita ao lado da `leitor-f1-1` (decisão de Roberto de 13/11/2026, docs/pre-registro-leitor.md, seção 10.7): os
arquivos congelados de chiocca/v2/leitor/ não mudam, e a seção, os exemplos e a demonstração continuam com a f1-1 até
a medida aprovar a f1-2. O mesmo vale para o assunto: até a regra nova ser aprovada, ficam as regras conservadoras de
chiocca/v2/ipe.py.

O que muda (só os quatro ajustes da emenda 1, seção 10.1), em `partes_relacionadas`:
1. "a Companhia é controlada (em conjunto) por" é `controladora` (ou `controle_conjunto_ou_influencia`), não menção a
   controladas ou a joint ventures;
2. "a Companhia, na qualidade de controladora, ..." fala da própria Companhia e não conta como `controladora`;
3. montante e prazo escritos em frase ("somou R$ ... no exercício", "vence em 2030");
4. linhas de cabeçalho de tabela (anos, datas, títulos de coluna, inclusive em várias linhas) não saem como trecho.
O resto vem da f1-1 sem mudança: texto e conferência literal, segmentos, detector de nomes, risco sacado, relatório do
auditor e Formulário de Referência.

Módulos: `partes_relacionadas`, `ler`, `assunto` (regra do assunto do IPE), `avaliacao` e o comando `avaliar`.
"""

VERSAO = "leitor-f1-2"
