# Ficha do motor

Gerada por `python -m chiocca.v2.ficha_do_motor` a partir de `docs/resultados_numeros.json` (o mesmo JSON do [resumo](resumo.md)) e da [análise descritiva depois do resultado](analises-pos-estudo-1.md). Não edite à mão: um teste compara este arquivo com a saída do script. Formato de model card.

> Sinal estatístico baseado em demonstrações públicas. Não é acusação, não é recomendação de investimento.

## Versão

- Motor: motor v1 (estudo 1), branch estudo-1-final, commit 8c9a823. O estudo 1 está congelado nesse commit; o produto usa o motor como está.
- Camada do produto: chiocca.v2 (produto, fases B a E) (contexto, confiança, linhagem, investigação, API e interface), sem mudar nenhum valor do motor.
- Pré-registro assinado em 04/11/2026, com 11 emendas ([`docs/pre-registro.md`](pre-registro.md)).

## Uso pretendido

- Apontar onde olhar nas demonstrações financeiras públicas de companhias abertas brasileiras, para análise humana.
- Cada sinal vem com a regra, o contexto (percentil no setor e no ano, histórico da própria empresa), a confiança nos dados e o lastro até a linha do documento.

## Fora de escopo

- Decisão de investimento.
- Acusação: um alerta é sinal estatístico, não prova de irregularidade.
- Decisão automática sobre pessoas ou empresas.

## Dados

- Demonstrações financeiras padronizadas (DFP) da CVM, dos dados abertos e, para versões antigas, do ENET, lidas "como eram": em cada data, só o que tinha sido entregue até ela.
- Exercícios de 2010 a 2023; os de 2024 em diante estão lacrados e reservados ao estudo 2.
- Amostra do estudo 1: 6.938 empresa-anos não financeiras e 517 financeiras; gabarito de 42 casos públicos (condenação da CVM ou fraude admitida), 13 deles acertáveis.

## Avaliação (estudo 1)

- Acertos: 7 de 13 casos acertáveis (a regra boba acertou 6); na janela de teste, 2 (regra boba: 1).
- Alarmes por acerto, não financeiras: 108,3 no período inteiro e 311,0 na janela de teste.
- Taxa de alerta: 49,9% das empresa-anos não financeiras avaliadas (48,3% incluindo as financeiras).
- Teste contra o acaso (análise descritiva depois do resultado, não pré-registrada): sem supor anos independentes, o acaso daria 7,37 acertos, e 7 ou mais com chance de 69,3%; supondo anos independentes, 8,56 acertos (90,0%). O número de acertos não superou o acaso.
- Antecedência dos acertos (mesma natureza): mediana de 19,4 meses entre a entrega da primeira DFP em alerta no período afetado e a data pública do caso, de 3,4 a 46,9 meses.

## Limitações

As mesmas da seção "Limitações" do README:

- O juro implícito responde sozinho por 59,8% das empresa-anos não financeiras em alerta (2.001 de 3.345): a despesa financeira (3.06.02) inclui variação cambial, juros de arrendamento e outros itens que não são juros dos empréstimos ([resumo](resumo.md)).
- O M-score ficou sem valor em 1.548 de 6.938 empresa-anos; em 1.306, faltou o DEPI. O motivo mais comum é a DFC sem linha de depreciação na seção 6.01.01 (1.135 empresa-anos); quando a depreciação vem somada à amortização na mesma linha, o total é usado e o DEPI é calculado ([resultados](resultados.md)).
- O corte de -1,78 do M-score vem de Beneish (1999), estimado com empresas dos EUA, e não foi recalibrado para o Brasil ([resumo](resumo.md)).
- O IRB não pode ser acertado com DFP anual (emenda 3); pegá-lo exigiria dados trimestrais (ITR) ([resumo](resumo.md)).
- Poucos casos: 13 acertáveis em 42 no gabarito, nenhum deles financeiro ([resumo](resumo.md)).
- O número de acertos não superou o acaso no teste descritivo feito depois do resultado: 7 acertos, contra 7,37 esperados sem supor anos independentes (8,56 supondo anos independentes) ([análise](analises-pos-estudo-1.md)).
- Versões antigas recuperadas pelo ENET só existem para demonstrações consolidadas: de 2010 a 2023, 190 empresa-anos com a versão da época só em demonstração individual ficaram de fora (emenda 8) ([armazenamento temporal](armazenamento-temporal.md)).
- Depois do resultado, as conferências acharam 57 empresa-anos em que um balanço não preenchido entrou no cálculo como zero; 29 alertas dependem disso. Nenhum caso do gabarito foi afetado. Detalhes na [nota posterior](analises-pos-estudo-1.md), seção 4.

## Considerações éticas

- Alerta, não acusação. Toda saída leva o aviso fixo: "Sinal estatístico baseado em demonstrações públicas. Não é acusação, não é recomendação de investimento."
- Sem ranking público: nenhuma lista de empresas ordenada por alerta, percentil ou escore, em nenhuma saída (documentos, API e interface).
- Os resultados por empresa ficam fora do git (`resultados/`); o gabarito só tem casos públicos.
- Sem dados pessoais: nem CPF nem nome de pessoa física (auditor pessoa física aparece sem nome).
