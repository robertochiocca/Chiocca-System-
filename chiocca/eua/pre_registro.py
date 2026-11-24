"""Pré-registro do estudo dos EUA, registrado em 24/11/2026, antes de qualquer sinal americano calculado, com as
decisões de Roberto (Fase 0, seção 5.1) e os três ajustes da revisão final (seção 14 do texto). Os números citados da
Fase 0 saem de `docs/eua_fase0_numeros.json` (`render`); o resto do texto são regras e datas. Um teste confere que os
documentos em PT e EN são a saída deste módulo, e o carimbo (`docs/carimbos/eua-registro.txt`) guarda o SHA-256 do
texto em PT como está no commit de registro. Os arquivos do antigo rascunho viram um aviso (`AVISOS`).

Uso: python -m chiocca.eua.pre_registro
"""

from __future__ import annotations

import json
from typing import Any

from chiocca.base import RAIZ
from chiocca.eua import fase0, fsds
from chiocca.formato import inteiro, pct

DOCS = {"pt": RAIZ / "docs" / "pre-registro-eua.md", "en": RAIZ / "docs" / "en" / "us-preregistration.md"}
RASCUNHOS = {
    "pt": RAIZ / "docs" / "pre-registro-eua-rascunho.md",
    "en": RAIZ / "docs" / "en" / "us-preregistration-draft.md",
}
AVISOS = {
    "pt": "# Rascunho do pré-registro do estudo dos EUA\n\n> Este rascunho foi registrado em 24/11/2026. O texto em vigor é "
    "o [pré-registro do estudo dos EUA](pre-registro-eua.md); o histórico do rascunho fica no Git.\n",
    "en": "# Draft pre-registration of the US study\n\n> This draft was registered on 2026-11-24. The text in force is the "
    "[US study pre-registration](us-preregistration.md); the draft's history stays in Git.\n",
}
COMMIT_DE_REGISTRO: str | None = "a527b9eca9ab0f087b04f1c97ed737bc63188456"  # anotado no commit seguinte ao de registro
ANOTACAO = {
    "pt": "- Hash do commit de registro: `{c}` (anotado no commit seguinte, sem mudar nenhuma regra acima).\n",
    "en": "- Hash of the registration commit: `{c}` (noted in the next commit, without changing any rule above).\n",
}
PRIMEIRO, ULTIMO = 2011, 2024  # exercícios da amostra (ano da data de referência), decisão de 24/11/2026
SEMENTE = 20270430

PT = """# Pré-registro do estudo dos EUA

> **Registrado em 24/11/2026.** Redigido pelo agente com as decisões de Roberto ([Fase 0, seção 5.1](eua-fase-0.md)) e revisado por Roberto com o Claude (claude.ai), que aprovou o registro com os três ajustes da seção 14. O commit que introduz este arquivo é o registro, e o hash dele é anotado no commit seguinte, sem mudar nenhuma regra, como no estudo 2 e no motor v2. Nenhum sinal americano foi calculado antes do registro. A frente dos EUA fica fora do README e do produto. Alerta, não acusação: um 8-K com o item 4.02 é uma declaração de que demonstrações publicadas não valem mais, não uma acusação de fraude; nenhum alerta por companhia é publicado.

Base: a [Fase 0 dos EUA](eua-fase-0.md), com os números de [`docs/eua_fase0_numeros.json`](eua_fase0_numeros.json), e os pré-registros do [estudo 1](pre-registro.md), do [estudo 2](pre-registro-estudo-2.md) e do [motor v2](pre-registro-motor-v2.md), cujas regras valem aqui com só as adaptações da seção 3.

## 1. Pergunta

Com os 10-K como eram na época, os alertas do motor v1 e do motor v2, congelados no Brasil, e a regra boba separam as empresa-anos seguidas de um 8-K com o item 4.02 nos 12 meses depois do corte das que não foram? E o v2 separa melhor que o v1?

**Rótulo: retrospectivo.** Os dados de {primeiro} a 30/04/2026 já são públicos, e as contagens de 8-K 4.02 por ano já apareceram na Fase 0, sem nenhuma ligação com sinal. O teste é limpo porque as regras são fixas (sem treino), foram escritas e congeladas no Brasil, e este texto é registrado antes de qualquer sinal americano.

## 2. Os sinais: o v1 e o v2 congelados

- **v1:** as regras da seção 4 do pré-registro do estudo 1, com as emendas, no código registrado em [`docs/estudo_2_codigo_congelado.json`](estudo_2_codigo_congelado.json): M-score acima de -1,78; salto do DPO no decil superior do exercício; juro implícito acima da taxa de referência média do ano mais 10 p.p.; alerta quando pelo menos um sinal dispara.
- **v2:** as regras do pré-registro do motor v2, no código registrado em [`docs/motor_v2_codigo_congelado.json`](motor_v2_codigo_congelado.json): percentis do M-score, do salto do DPO, do juro implícito e do desvio de Benford padronizado, dentro do exercício e do grupo; escore igual ao maior percentil; alerta quando o escore fica no quantil de 90% ou acima.
- **O código:** as funções de sinal dos dois registros são chamadas sem mudar nenhuma linha. O script dos EUA só monta as entradas de cada empresa-ano a partir do XBRL e aplica as adaptações da seção 3. Só o grupo das não financeiras (seção 4).

## 3. As adaptações (as únicas), cada uma com o motivo

### 3.1 O mapa das contas para as tags us-gaap

Valores da própria companhia (sem co-registrante nem segmento), em dólar, na taxonomia us-gaap: o balanço na data de referência; o resultado e o fluxo de caixa do exercício (quatro trimestres). O ano anterior (t-1) vem do mesmo 10-K, como a coluna do exercício anterior da DFP. Conta faltante ou denominador zero: "não calculável", como no v1, sem imputação. O sinal das despesas segue a convenção da DFP (negativo), e o código do v1 já usa o valor absoluto onde precisa.

| Conta | Tags e regra | Motivo |
| --- | --- | --- |
| `ativo_total`, `ativo_circulante`, `contas_a_receber`, `imobilizado`, `passivo_circulante`, `patrimonio_liquido`, `depreciacao`, `custo_vendas`, `lucro_liquido` | as da proposta da Fase 0, na ordem de preferência | o mesmo conceito da conta da DFP |
| `caixa_operacional` | {ordem_caixa}, nessa ordem (seção 3.1.3) | a variante só de operações continuadas cobre os 10-K que não trazem o total; exclui o caixa das operações descontinuadas |
| `receita_liquida` | {ordem_receita}, nessa ordem: as três da Fase 0 e as que a regra da seção 3.1.1 escolheu | com as três tags, a receita cobre de {rec_min} a {rec_max} dos 10-K de {primeiro} a {ultimo}, e a regra das sem receita tiraria companhias que têm receita em outra tag |
| `resultado_bruto` | `GrossProfit`; se ausente, receita menos custo das vendas | na DFP a linha 3.03 é obrigatória; no US GAAP o lucro bruto é opcional (cobertura de {bruto_min} a {bruto_max}) |
| `despesas_vendas` + `despesas_gerais_adm` | `SellingGeneralAndAdministrativeExpense`, que já junta as duas | o v1 soma as duas contas; no US GAAP elas vêm juntas |
| `lucro_operacoes_continuadas` | `IncomeLossFromContinuingOperations`; se ausente, o lucro líquido menos `IncomeLossFromDiscontinuedOperationsNetOfTax`, quando houver | a conta 3.09 é depois dos impostos; a tag antes dos impostos da proposta da Fase 0 sai, por ser outro conceito |
| `emprestimos_cp` | `DebtCurrent`; se ausente, a soma de `LongTermDebtCurrent` e `ShortTermBorrowings` presentes | no US GAAP a dívida de curto prazo pode vir em linhas separadas |
| `emprestimos_lp` | `LongTermDebtNoncurrent`; se ausente, `LongTermDebtAndCapitalLeaseObligations` | o mesmo conceito, com a segunda tag como reserva |
| `despesas_financeiras` | {ordem_juros}, nessa ordem (seção 3.1.3); as marcadas com (*) são de conceito mais largo e entram com a marca | limite registrado: a despesa financeira da DFP inclui variação cambial e outros encargos; as tags americanas são de juros |
| `fornecedores` | `AccountsPayableCurrent`; se ausente, `AccountsPayableAndAccruedLiabilitiesCurrent`, com a marca de que inclui provisões | a segunda tag é mais larga |
| `passivo_total` (regra boba) | `Liabilities`; se ausente, `LiabilitiesAndStockholdersEquity` menos o patrimônio líquido com minoritários | a regra boba usa passivo total ÷ ativo total, e muitas companhias não apresentam o total do passivo |

O desvio de Benford usa os valores diferentes de zero do exercício na demonstração do balanço, do resultado e do fluxo de caixa do 10-K (pela coluna `stmt` de `pre.txt`: BS, IS e CF), o equivalente americano de BPA, BPP, DRE e DFC, com o mínimo de 20 números do v2. A DVA não existe nos EUA: o DEPI do v2 é o do v1, pela depreciação do fluxo de caixa. A cobertura de cada conta com as regras acima está na seção 3.1.2 (só contagens).

### 3.1.1 A ampliação da receita, só pela cobertura

Decisão de Roberto de 24/11/2026: as tags da receita são escolhidas só pelas contagens de cobertura, e a lista final entra no texto registrado. A lista de candidatas e a regra foram escritas no código (`RECEITA_CANDIDATAS` e `ampliar_receita`, em `chiocca/eua/fsds.py`) antes de qualquer contagem: só tags us-gaap de receita total, sem componentes, custos ou saldos. Partindo das três tags da Fase 0, entra a cada passo a candidata que cobre mais 10-K da amostra ainda sem receita (não financeiras, sem as SPACs, exercícios de {primeiro} a {ultimo}: {n_am} 10-K), se o ganho for de pelo menos {ganho_min} dessas entregas. O valor é o anual (quatro trimestres) na data de referência.

{tabela_receita}

Entraram {n_escolhidas} tags. **A lista final da receita, nesta ordem de preferência: {ordem_receita}.**

Contagem de descoberta, só para transparência: entre os {sem_tres} 10-K da amostra sem nenhuma das três tags da Fase 0, as 15 tags us-gaap mais frequentes com "Revenue" ou "Sales" no nome (valor anual na data de referência). Nenhuma tag fora das candidatas entra, mesmo que pareça de receita total: as listas de candidatas escritas antes da contagem são as finais (ajuste de Roberto de 24/11/2026).

{tabela_descoberta}

### 3.1.2 A cobertura do mapa ampliado

A fração dos 10-K da amostra com cada conta pelas regras da seção 3.1: presença do valor na data de referência, como na seção 2.4 da Fase 0, e, para a receita, o valor anual diferente de zero. No conjunto de {primeiro} a {ultimo}, e o menor e o maior ano. Só contagens.

{tabela_cobertura}

Com o mapa ampliado, a regra das sem receita tira {sem_amp} dos {n_am} 10-K da amostra, contra {sem_f0} com as três tags da Fase 0. A despesa financeira e o caixa operacional já estão com as tags da seção 3.1.3.

### 3.1.3 A ampliação da despesa financeira e do caixa operacional

Pedido de Roberto de 24/11/2026: a mesma regra da receita para as duas contas que perdiam cobertura. As candidatas de cada conta foram escritas no código (`AMPLIACOES` e `CONCEITO_LARGO`, em `chiocca/eua/fsds.py`) antes de qualquer contagem, todas do mesmo conceito contábil: juros da dívida; caixa líquido das atividades operacionais, inclusive a variante só de operações continuadas. As de conceito mais largo (`InterestAndDebtExpense`, juros e outros encargos da dívida, e `InterestCostsIncurred`, que inclui os juros capitalizados) entram com uma marca, como a de fornecedores. Ficam fora os juros líquidos de receita de juros e os juros pagos (outros conceitos) e as tags de componentes. Entram pela ordem de maior ganho, com pelo menos {ganho_min} dos 10-K da amostra, pelo valor anual (quatro trimestres) na data de referência. Nenhuma tag fora das candidatas entra: as listas escritas antes da contagem são as finais.

**Antes, o uso de cada tag por ano** (fração dos 10-K da amostra com o valor anual da tag), para ver se as quedas vêm de troca de tag na taxonomia:

{tabela_uso}

{leitura_uso}

{tabela_juros_caixa}

{resumo_juros_caixa}

### 3.2 A taxa que substitui o CDI

A Effective Federal Funds Rate, série diária DFF do FRED (Federal Reserve Bank of St. Louis), cuja fonte é a publicação H.15 do Federal Reserve: pública, gratuita e sem chave. Como `chiocca.cdi.medio`, a média das taxas diárias nos 12 meses que terminam no fim do exercício, com o mesmo corte de 10 p.p. Motivo: é a taxa do overnight interbancário dos EUA, o papel do CDI no Brasil. Limite registrado: a DFF anualiza em base de 360 dias corridos e o CDI em base de 252 dias úteis. O arquivo da série entra no repositório, como `data/cdi_sgs4389.csv`, com o SHA-256 no manifesto.

### 3.3 A data de corte

A mesma regra do estudo 1 (emenda 5, `chiocca.corte.data_corte`): o último dia do quarto mês depois do fim do exercício. Motivo: o prazo do 10-K é de 60, 75 ou 90 dias, conforme o porte, e, de {primeiro} a {ultimo}, o décimo de 10-K entregues mais tarde saiu até {p90} dias depois da data de referência (seção 2.2 da Fase 0). A versão usada é a pública no corte: a última entrega até a data entre o 10-K original e os 10-K/A com números das contas (seção 2.3 da Fase 0). A companhia sem 10-K com XBRL até o corte fica fora daquele exercício, como no Brasil.

### 3.4 O que não se adapta

As financeiras ficam fora (decisão de Roberto de 24/11/2026): o mapa não tem as contas delas, e por isso o grupo das financeiras e o peso de ganhos não recorrentes não existem neste estudo. A DVA (seção 3.1). O leitor de documentos.

## 4. Amostra e exclusões

- **Universo:** os 10-K originais dos Financial Statement Data Sets com data de referência de {primeiro} a {ultimo} (o exercício é o ano da data de referência, como na DFP). {primeiro}, porque o XBRL vale para todas as companhias a partir dos períodos depois de 15/06/2011; {ultimo}, porque a janela de 12 meses desse exercício já terminou, em 30/04/2026 (decisão de Roberto de 24/11/2026).
- **Exclusões, nesta ordem, cada uma contada no relatório:** (1) sem versão pública com XBRL até o corte; (2) as financeiras pela SIC, de 6000 a 6999, exceto 6770 (seção 3.4); (3) as SPACs, SIC 6770, regra explícita decidida por Roberto em 24/11/2026; (4) as sem receita (receita ausente ou zero, a regra do estudo 1, pelo mapa ampliado); (5) as sem nenhum sinal calculável. A SIC e a receita são as da versão usada.
- **O tamanho, pela Fase 0 (exercício declarado, mapa da Fase 0):** de {primeiro} a {ultimo}, {n10k} 10-K originais: {fin} de financeiras, {spac} de SPACs ({spac_sem} delas já sem receita) e {sem_dem} das demais sem receita pelo mapa da Fase 0; ficam {ficam10k}. Com o mapa ampliado (seção 3.1.2), as demais sem receita são {sem_amp}, e ficam {ficam_amp10k}.

## 5. O desfecho: o 8-K com o item 4.02, por caso

- **Episódio (o caso):** o primeiro 8-K de uma companhia com o item 4.02 no campo de itens do EDGAR abre um episódio; todo 8-K ou 8-K/A com o item 4.02 da mesma companhia nos 365 dias seguintes pertence a ele; depois disso, um novo 8-K 4.02 abre outro episódio. Cada episódio conta uma vez, a resposta à crítica de Walker e de Gow a Bao et al. (Fase 0, seção 5.1).
- **Janela:** a empresa-ano t é positiva se um episódio se abre depois do corte de t e até 12 meses depois dele. As janelas de exercícios seguidos da mesma companhia não se sobrepõem, e cada episódio cai em no máximo uma empresa-ano. Os episódios fora de qualquer empresa-ano da amostra entram só na descrição.
- **Fonte:** o campo de itens do histórico de entregas do EDGAR (`submissions.zip`), baixado de novo no dia do cálculo, com o SHA-256 no manifesto, e só os 8-K entregues até 30/04/2026, o fim da janela do exercício de {ultimo}.
- **O tamanho, pela Fase 0:** de 2009 a 30/04/2026, {antes} companhias-ano com 8-K 4.02 e 10-K nos dados da SEC antes do 8-K: {antes_fin} de financeiras, {antes_spac} de SPACs e {antes_sem} das demais sem receita pelo mapa da Fase 0; ficam {antes_ficam}, de {ficam_min} a {ficam_max} por ano de entrega de 2012 a 2025. Com o mapa ampliado, ficam {antes_ficam_amp}, de {ficam_amp_min} a {ficam_amp_max} por ano.
- **Limites:** o item 4.02 não diz quais demonstrações deixaram de valer: o desfecho é uma declaração de não confiabilidade nos 12 meses seguintes, sem garantia de que trata do exercício t. As republicações sem 8-K ("little r") ficam de fora. Nada disso é chamado de fraude.

## 6. Métricas: as do estudo 2

- **Medida principal:** a diferença de risco DR = P(positiva | em alerta) − P(positiva | fora de alerta), nas empresa-anos avaliadas pelo v1, com todos os exercícios juntos; também a razão de taxas.
- **Bootstrap por companhia:** sorteiam-se companhias com reposição, cada uma com todas as suas empresa-anos; 10.000 reamostragens, com a semente {semente} (decisão de Roberto de 24/11/2026); o intervalo é o percentil unilateral de 95%. As funções são `taxas`, `dr`, `bootstrap_por_companhia` e `limite_inferior` de `chiocca/v2/estudo2/secundaria.py`, chamadas sem mudar nenhuma linha.
- **Resultado:** "associação positiva" se o limite inferior do intervalo unilateral de 95% da DR ficar acima de zero; senão, "sem evidência de associação".
- **Regra boba lado a lado:** o decil mais endividado (passivo total ÷ ativo total) de cada exercício, como no estudo 1, com a mesma DR e o bootstrap pareado (as mesmas reamostragens): "o motor separa melhor que a regra boba" só se o limite inferior da diferença ficar acima de zero.
- **O v2 pareado com o v1:** como na emenda 5 do estudo 2. O alerta do v2 sai de todas as empresa-anos que o v2 avalia; as medidas são calculadas nas empresa-anos avaliadas pelo v1; "o v2 separa melhor que o v1" só se o limite inferior da diferença pareada ficar acima de zero; senão, sem vencedor declarado.
- **Descritivas:** as métricas de ranking do estudo 2 (precisão e lift no topo de 1%, 5% e 10% e NDCG@k), cada exercício separado e os AAERs (seção 8). Só agregados: nenhuma lista de companhias por alerta.

## 7. O exemplo calculado à mão

Antes de qualquer código do estudo, um exemplo calculado à mão, num script separado (`tests/referencia/gerar_exemplo_eua.py`), fora do pacote `chiocca` e sem importá-lo, como os exemplos do estudo 1 e do motor v2, com aritmética exata nas bordas:

- **Um 10-K fictício em XBRL:** linhas no formato de `sub.txt`, `num.txt` e `pre.txt`, com valores escolhidos, de um grupo pequeno de companhias fictícias não financeiras, no exercício e no anterior, de modo que cada regra do mapa das contas (seção 3.1) apareça pelo menos uma vez: a primeira tag de cada conta e as reservas (a receita por uma tag da ampliação, o lucro bruto derivado, o lucro das operações continuadas pelo lucro líquido, a dívida de curto prazo pela soma, a despesa financeira por uma tag da ampliação e por `InterestAndDebtExpense`, com a marca, o caixa operacional pela variante das operações continuadas, fornecedores pela tag mais larga, com a marca, e o passivo total pela diferença); números de co-registrante, de segmento, em outra moeda e de outra data, que não podem entrar; e uma conta faltante, que deixa um sinal não calculável.
- **A versão pública no corte (seção 3.3):** o 10-K original e emendas com números das contas, uma entregue até o corte, que vira a versão usada, e outra depois do corte, que não entra, e uma emenda sem esses números, que não muda a versão.
- **Os sinais do v1 e do v2 (seção 2):** os oito componentes e o M-score, o salto do DPO, o juro implícito contra uma taxa de referência fictícia, o desvio de Benford, os percentis, o escore e os alertas do v1, do v2 e da regra boba, num grupo pequeno o bastante para conferir à mão.
- **A conferência:** o código do estudo tem de reproduzir os valores do script, com um teste, e o script entra no registro de SHA-256 do estudo, no congelamento (seção 10). Limite, como no motor v2: as duas implementações partem do mesmo texto; a conferência pega erro de implementação, não erro no texto.

## 8. Os AAERs de 2009 a 2014: descrição à parte

Para os {casos} casos de Bao et al. ({ea} empresa-anos) com 10-K nos dados da SEC (Fase 0, seção 4.1): quantos casos o v1, o v2 e a regra boba alertaram em pelo menos um exercício afetado, com a versão pública no corte. Só contagens, sem teste e sem lista. Em 2009 e 2010, só as companhias maiores entregavam em XBRL.

## 9. Previsões escritas antes dos dados

Revistas em 24/11/2026 para o período novo ({primeiro} a {ultimo}) e o mapa ampliado, e de novo depois da ampliação da despesa financeira e do caixa operacional (seção 3.1.3). Nenhuma faixa mudou; o motivo de cada uma vem ao lado.

1. **Taxa de alerta do v1:** entre 25% e 45% das não financeiras avaliadas em cada exercício. Motivo: o M-score acima de -1,78 marca parte relevante das companhias americanas, e o decil do DPO soma 10%; o juro implícito dispara menos que no Brasil, porque a despesa de juros americana não inclui variação cambial. **Sem ajuste:** o período novo acrescenta exercícios de juros altos (2022 a 2024), em que o juro implícito dispara menos (o corte sobe com a taxa de referência), mas o M-score e o DPO não dependem dos juros, e a faixa já cobre essa variação. **Sem ajuste depois da seção 3.1.3:** com mais juros e mais caixa operacional calculáveis, o juro implícito e o M-score passam a ser calculados em mais empresa-anos (o juro implícito, sobretudo em {df_ano}), o que pode subir um pouco a taxa de alerta nesses anos, dentro da faixa.
2. **Taxa de alerta do v2:** entre 10,0% e 11,0% em cada exercício. **Sem ajuste:** vem da construção do decil, com qualquer cobertura.
3. **Taxa do desfecho:** entre 1,5% e 4% das empresa-anos avaliadas. **Sem ajuste:** com o mapa ampliado, ficam {antes_ficam_amp} companhias-ano com 8-K 4.02 e 10-K antes (seção 5), de {ficam_amp_min} a {ficam_amp_max} por ano de entrega, contra cerca de {media_am} 10-K da amostra por exercício antes da regra das sem receita: perto de 2% a 3%.
4. **DR do v1:** positiva, com razão de taxas entre 1,1 e 1,5, e "associação positiva" mais provável que não. **Sem ajuste:** a amostra maior só reforça o poder.
5. **DR do v2:** positiva, com razão de taxas entre 1,2 e 2,0, e "associação positiva". **Sem ajuste.**
6. **O v2 pareado com o v1:** diferença positiva, com o limite inferior acima de zero ("o v2 separa melhor que o v1"). Motivo: o grupo em alerta do v2 é menor e mais extremo. **Sem ajuste.**
7. **O v2 contra a regra boba:** sem vencedor declarado. Motivo: o endividamento também se associa a republicações, pela dificuldade financeira. **Sem ajuste.**
8. **AAERs:** dos {casos} casos, entre 30% e 60% em alerta no v1 e entre 10% e 30% no v2 em pelo menos um exercício afetado. **Sem ajuste:** a descrição dos AAERs não depende do período da amostra.

## 10. Ordem e calendário: meta e reserva

A ordem é fixa: (1) o registro deste texto; (2) o exemplo calculado à mão (seção 7), antes de qualquer código do estudo; (3) o código do estudo, testado só em dados sintéticos e no exemplo à mão, sem nenhum sinal calculado em dados reais; (4) o congelamento, com o registro de SHA-256 do código e do script do exemplo; (5) só então o cálculo único, com os dados da SEC e os 8-K baixados de novo no dia; (6) o relatório.

| Etapa | Meta | Reserva |
| --- | --- | --- |
| Registro deste texto e carimbo. | 05/12/2026 | 31/01/2027 |
| Exemplo à mão, código testado só em dados sintéticos e no exemplo, e congelamento. | 15/01/2027 | 31/03/2027 |
| Cálculo único, depois do congelamento. | 31/01/2027 | 30/04/2027 |
| Relatório em PT e EN, separado do estudo 2 do Brasil. | 28/02/2027 | 31/05/2027 |

A reserva mantém as datas da reserva da versão revisada (31/01/2027, 31/03/2027, 30/04/2027 e 31/05/2027), na ordem nova.

## 11. Decisões de Roberto de 24/11/2026

(a) As financeiras ficam fora (seção 3.4); (b) as tags da receita são escolhidas só pelas contagens de cobertura, e a lista final está na seção 3.1.1; (c) a amostra vai até o exercício de {ultimo}, com os dados da SEC e os 8-K baixados de novo no dia do cálculo; (d) a semente é {semente}; (e) os arquivos da SEC ficam fora do Git, com o SHA-256 no manifesto e o download por script; (f) a despesa financeira e o caixa operacional pela mesma regra da receita (seção 3.1.3); (g) nenhuma tag fora das candidatas entra (seções 3.1.1 e 3.1.3); (h) o exemplo calculado à mão (seção 7); (i) a ordem e o calendário, com meta e reserva (seção 10).

O exercício é o ano da data de referência, como na DFP; as contagens da Fase 0 usam o exercício declarado pela companhia (`fy`), e a diferença entre os dois é pequena.

## 12. O que fica de fora

As financeiras, a DVA e o leitor (seção 3.4); qualquer lista ou ordem de companhias por alerta; qualquer recomendação de investimento; e, até decisão de Roberto, a frente dos EUA no README e no produto.

## 13. Registro

- Data: 24/11/2026.
- Commit: o que introduz esta versão com este nome. O hash é anotado aqui no commit seguinte, sem mudar nenhuma regra acima.
{anotacao}- Carimbo de tempo, como no estudo 2 e no motor v2: `docs/carimbos/eua-registro.txt`, com o hash do commit de registro e o SHA-256 deste arquivo em PT, como está no commit de registro, carimbado com o OpenTimestamps; o `.ots` vai para o repositório, e o `ots upgrade` é feito depois da confirmação no Bitcoin.
- Congelamento: o código do estudo e o script do exemplo da seção 7 entram num registro de SHA-256 próprio do estudo, antes do cálculo único (seção 10).

## 14. Revisão de Roberto (24/11/2026)

Roberto leu o texto inteiro, com a revisão do Claude (claude.ai), e aprovou o registro com três ajustes. O texto lido foi o do commit `8c529c7fd215e268304570296a1aaf5332e0acb2`; os ajustes entraram no commit `08d15363cbe7191bfe2a661e86f88fafa1228f8d`, antes do registro, sem mudar nenhuma outra regra.

1. **Tags fora das candidatas:** nenhuma entra; as listas de candidatas escritas antes da contagem são as finais (seções 3.1.1 e 3.1.3).
2. **O exemplo calculado à mão (seção 7):** um 10-K fictício em XBRL, com valores escolhidos, passando pelo mapa das contas (inclusive as reservas e as marcas), pela versão pública no corte e pelos sinais do v1 e do v2, num script separado, escrito antes do código do estudo; o código tem de reproduzir os valores, e o script entra no registro de SHA-256 do estudo.
3. **A ordem e o calendário (seção 10):** primeiro o registro do texto; depois o código, testado só em dados sintéticos e no exemplo à mão; o congelamento; e só então o cálculo único; com meta e reserva.
"""

EN = """# US study pre-registration

> **Registered on 2026-11-24.** Written by the agent with Roberto's decisions ([Phase 0, section 5.1](us-phase-0.md)) and reviewed by Roberto with Claude (claude.ai), who approved the registration with the three adjustments in section 14. The commit that introduces this file is the registration, and its hash is noted in the next commit, without changing any rule, as in study 2 and engine v2. No US signal was computed before registration. The US front stays out of the README and the product. Alert, not accusation: an 8-K with Item 4.02 is a statement that published financial statements can no longer be relied upon, not an accusation of fraud; no alert by company is published.

Basis: [US Phase 0](us-phase-0.md), with the numbers in [`docs/eua_fase0_numeros.json`](../eua_fase0_numeros.json), and the pre-registrations of [study 1](../pre-registro.md), [study 2](study-2-preregistration.md) and [engine v2](engine-v2-preregistration.md), whose rules hold here with only the adaptations in section 3.

## 1. Question

With the 10-Ks as they were at the time, do the alerts of engine v1 and engine v2, frozen in Brazil, and the naive rule separate the company-years followed by an 8-K with Item 4.02 within 12 months after the cut-off from those that were not? And does v2 separate better than v1?

**Label: retrospective.** The data from {primeiro} to 2026-04-30 are already public, and the counts of 8-K 4.02 by year already appeared in Phase 0, with no link to any signal. The test is clean because the rules are fixed (no training), were written and frozen in Brazil, and this text is registered before any US signal.

## 2. The signals: v1 and v2, frozen

- **v1:** the rules in section 4 of the study 1 pre-registration, with the amendments, in the code registered in [`docs/estudo_2_codigo_congelado.json`](../estudo_2_codigo_congelado.json): M-score above -1.78; DPO jump in the top decile of the fiscal year; implied interest above the year's average reference rate plus 10 p.p.; alert when at least one signal fires.
- **v2:** the rules of the engine v2 pre-registration, in the code registered in [`docs/motor_v2_codigo_congelado.json`](../motor_v2_codigo_congelado.json): percentiles of the M-score, the DPO jump, implied interest and the standardized Benford deviation, within the fiscal year and the group; score equal to the highest percentile; alert when the score is at or above the 90% quantile.
- **The code:** the signal functions of both registries are called without changing a line. The US script only builds each company-year's inputs from XBRL and applies the adaptations in section 3. Only the non-financial group (section 4).

## 3. The adaptations (the only ones), each with its reason

### 3.1 The map from accounts to us-gaap tags

The company's own values (no co-registrant or segment), in dollars, in the us-gaap taxonomy: the balance sheet at the report date; the income statement and cash flow for the fiscal year (four quarters). The prior year (t-1) comes from the same 10-K, like the DFP's prior-year column. Missing account or zero denominator: "not computable", as in v1, with no imputation. Expense signs follow the DFP convention (negative), and the v1 code already uses the absolute value where it needs to.

| Account | Tags and rule | Reason |
| --- | --- | --- |
| `ativo_total`, `ativo_circulante`, `contas_a_receber`, `imobilizado`, `passivo_circulante`, `patrimonio_liquido`, `depreciacao`, `custo_vendas`, `lucro_liquido` | those of the Phase 0 proposal, in order of preference | the same concept as the DFP account |
| `caixa_operacional` | {ordem_caixa}, in this order (section 3.1.3) | the continuing-operations variant covers the 10-Ks that do not report the total; it excludes discontinued-operations cash flows |
| `receita_liquida` | {ordem_receita}, in this order: the three Phase 0 tags and those the rule in section 3.1.1 chose | with the three tags, revenue covers {rec_min} to {rec_max} of the {primeiro} to {ultimo} 10-Ks, and the no-revenue rule would remove companies that have revenue in another tag |
| `resultado_bruto` | `GrossProfit`; if missing, revenue minus cost of sales | in the DFP line 3.03 is mandatory; under US GAAP gross profit is optional (coverage of {bruto_min} to {bruto_max}) |
| `despesas_vendas` + `despesas_gerais_adm` | `SellingGeneralAndAdministrativeExpense`, which already joins both | v1 adds the two accounts; under US GAAP they come together |
| `lucro_operacoes_continuadas` | `IncomeLossFromContinuingOperations`; if missing, net income minus `IncomeLossFromDiscontinuedOperationsNetOfTax`, when present | account 3.09 is after taxes; the pre-tax tag of the Phase 0 proposal is dropped, being a different concept |
| `emprestimos_cp` | `DebtCurrent`; if missing, the sum of `LongTermDebtCurrent` and `ShortTermBorrowings` present | under US GAAP short-term debt may come in separate lines |
| `emprestimos_lp` | `LongTermDebtNoncurrent`; if missing, `LongTermDebtAndCapitalLeaseObligations` | the same concept, with the second tag as a fallback |
| `despesas_financeiras` | {ordem_juros}, in this order (section 3.1.3); those marked (*) have a wider concept and enter with the flag | recorded limitation: the DFP's financial expense includes FX variation and other charges; the US tags are interest |
| `fornecedores` | `AccountsPayableCurrent`; if missing, `AccountsPayableAndAccruedLiabilitiesCurrent`, flagged as including accruals | the second tag is wider |
| `passivo_total` (naive rule) | `Liabilities`; if missing, `LiabilitiesAndStockholdersEquity` minus equity including noncontrolling interest | the naive rule uses total liabilities ÷ total assets, and many companies do not present total liabilities |

The Benford deviation uses the fiscal year's nonzero values in the 10-K's balance sheet, income statement and cash flow statement (by the `stmt` column of `pre.txt`: BS, IS and CF), the US equivalent of BPA, BPP, DRE and DFC, with v2's minimum of 20 numbers. The DVA does not exist in the US: v2's DEPI is v1's, from cash-flow depreciation. The coverage of each account under the rules above is in section 3.1.2 (counts only).

### 3.1.1 The revenue widening, by coverage only

Roberto's decision of 2026-11-24: the revenue tags are chosen by coverage counts only, and the final list goes into the registered text. The candidate list and the rule were written in the code (`RECEITA_CANDIDATAS` and `ampliar_receita`, in `chiocca/eua/fsds.py`) before any count: only us-gaap tags for total revenue, with no components, costs or balances. Starting from the three Phase 0 tags, at each step the candidate that covers the most sample 10-Ks still without revenue enters (non-financial, without SPACs, fiscal years {primeiro} to {ultimo}: {n_am} 10-Ks), if the gain is at least {ganho_min} of those filings. The value is the annual one (four quarters) at the report date.

{tabela_receita}

{n_escolhidas} tags entered. **The final revenue list, in this order of preference: {ordem_receita}.**

Discovery count, for transparency only: among the {sem_tres} sample 10-Ks with none of the three Phase 0 tags, the 15 most frequent us-gaap tags with "Revenue" or "Sales" in the name (annual value at the report date). No tag outside the candidates enters, even if it looks like total revenue: the candidate lists written before the count are final (Roberto's adjustment of 2026-11-24).

{tabela_descoberta}

### 3.1.2 Coverage of the widened map

The share of sample 10-Ks with each account under the rules in section 3.1: presence of the value at the report date, as in Phase 0 section 2.4, and, for revenue, a nonzero annual value. Over {primeiro} to {ultimo} as a whole, and the lowest and highest year. Counts only.

{tabela_cobertura}

With the widened map, the no-revenue rule removes {sem_amp} of the {n_am} sample 10-Ks, against {sem_f0} with the three Phase 0 tags. Financial expense and operating cash flow already use the tags of section 3.1.3.

### 3.1.3 Widening financial expense and operating cash flow

Roberto's request of 2026-11-24: the same rule as for revenue, for the two accounts that were losing coverage. Each account's candidates were written in the code (`AMPLIACOES` and `CONCEITO_LARGO`, in `chiocca/eua/fsds.py`) before any count, all of the same accounting concept: interest on debt; net cash from operating activities, including the continuing-operations-only variant. Those with a wider concept (`InterestAndDebtExpense`, interest and other debt charges, and `InterestCostsIncurred`, which includes capitalized interest) enter with a flag, like the accounts payable one. Net interest (net of interest income) and interest paid (other concepts) and component tags are left out. They enter in order of largest gain, with at least {ganho_min} of the sample 10-Ks, by the annual value (four quarters) at the report date. No tag outside the candidates enters: the lists written before the count are final.

**First, the use of each tag by year** (share of sample 10-Ks with the tag's annual value), to see whether the drops come from a tag change in the taxonomy:

{tabela_uso}

{leitura_uso}

{tabela_juros_caixa}

{resumo_juros_caixa}

### 3.2 The rate that replaces the CDI

The Effective Federal Funds Rate, daily series DFF on FRED (Federal Reserve Bank of St. Louis), sourced from the Federal Reserve's H.15 release: public, free and with no key. Like `chiocca.cdi.medio`, the average of the daily rates over the 12 months ending at the fiscal year end, with the same 10 p.p. cut-off. Reason: it is the US overnight interbank rate, the CDI's role in Brazil. Recorded limitation: DFF annualizes on a 360 calendar-day basis and the CDI on a 252 business-day basis. The series file goes into the repository, like `data/cdi_sgs4389.csv`, with its SHA-256 in the manifest.

### 3.3 The cut-off date

The same rule as study 1 (amendment 5, `chiocca.corte.data_corte`): the last day of the fourth month after the fiscal year end. Reason: the 10-K deadline is 60, 75 or 90 days, depending on size, and, from {primeiro} to {ultimo}, the latest-filed tenth of 10-Ks came out up to {p90} days after the report date (Phase 0, section 2.2). The version used is the one public at the cut-off: the last filing by that date between the original 10-K and the 10-K/As with account numbers (Phase 0, section 2.3). A company with no XBRL 10-K by the cut-off is out for that fiscal year, as in Brazil.

### 3.4 What is not adapted

Financial companies stay out (Roberto's decision of 2026-11-24): the map has no accounts for them, so the financial group and the weight of non-recurring gains do not exist in this study. The DVA (section 3.1). The document reader.

## 4. Sample and exclusions

- **Universe:** the original 10-Ks in the Financial Statement Data Sets with a report date from {primeiro} to {ultimo} (the fiscal year is the year of the report date, as in the DFP). {primeiro}, because XBRL applies to all companies from periods after 2011-06-15; {ultimo}, because the 12-month window of that fiscal year has already ended, on 2026-04-30 (Roberto's decision of 2026-11-24).
- **Exclusions, in this order, each counted in the report:** (1) no public XBRL version by the cut-off; (2) financial companies by SIC, 6000 to 6999, except 6770 (section 3.4); (3) SPACs, SIC 6770, an explicit rule decided by Roberto on 2026-11-24; (4) companies without revenue (revenue missing or zero, the study 1 rule, by the widened map); (5) those with no computable signal. SIC and revenue are those of the version used.
- **The size, from Phase 0 (declared fiscal year, Phase 0 map):** from {primeiro} to {ultimo}, {n10k} original 10-Ks: {fin} financial, {spac} SPACs ({spac_sem} of them already without revenue) and {sem_dem} others without revenue by the Phase 0 map; {ficam10k} remain. With the widened map (section 3.1.2), the others without revenue are {sem_amp}, and {ficam_amp10k} remain.

## 5. The outcome: the 8-K with Item 4.02, per case

- **Episode (the case):** a company's first 8-K with Item 4.02 in the EDGAR items field opens an episode; every 8-K or 8-K/A with Item 4.02 from the same company within the next 365 days belongs to it; after that, a new 8-K 4.02 opens another episode. Each episode counts once, the answer to Walker's and Gow's critique of Bao et al. (Phase 0, section 5.1).
- **Window:** company-year t is positive if an episode opens after the cut-off of t and within 12 months of it. The windows of consecutive fiscal years of the same company do not overlap, and each episode falls into at most one company-year. Episodes outside any sample company-year enter the description only.
- **Source:** the items field of the EDGAR filing history (`submissions.zip`), downloaded again on the day of the computation, with its SHA-256 in the manifest, and only the 8-Ks filed through 2026-04-30, the end of the window of fiscal {ultimo}.
- **The size, from Phase 0:** from 2009 to 2026-04-30, {antes} company-years with an 8-K 4.02 and a 10-K in the SEC data before the 8-K: {antes_fin} financial, {antes_spac} SPACs and {antes_sem} others without revenue by the Phase 0 map; {antes_ficam} remain, from {ficam_min} to {ficam_max} a year by filing year from 2012 to 2025. With the widened map, {antes_ficam_amp} remain, from {ficam_amp_min} to {ficam_amp_max} a year.
- **Limitations:** Item 4.02 does not say which statements stopped being reliable: the outcome is a non-reliance statement within the next 12 months, with no guarantee that it concerns fiscal year t. Restatements without an 8-K ("little r") are left out. None of this is called fraud.

## 6. Metrics: those of study 2

- **Main measure:** the risk difference DR = P(positive | alert) − P(positive | no alert), on the company-years evaluated by v1, with all fiscal years together; also the rate ratio.
- **Bootstrap by company:** companies are drawn with replacement, each with all its company-years; 10,000 resamples, with seed {semente} (Roberto's decision of 2026-11-24); the interval is the one-sided 95% percentile. The functions are `taxas`, `dr`, `bootstrap_por_companhia` and `limite_inferior` from `chiocca/v2/estudo2/secundaria.py`, called without changing a line.
- **Result:** "positive association" if the lower bound of the one-sided 95% interval of the DR is above zero; otherwise, "no evidence of association".
- **Naive rule side by side:** the most leveraged decile (total liabilities ÷ total assets) of each fiscal year, as in study 1, with the same DR and the paired bootstrap (the same resamples): "the engine separates better than the naive rule" only if the lower bound of the difference is above zero.
- **v2 paired with v1:** as in study 2's amendment 5. v2's alert comes from all company-years v2 evaluates; the measures are computed on the company-years evaluated by v1; "v2 separates better than v1" only if the lower bound of the paired difference is above zero; otherwise, no winner declared.
- **Descriptive:** study 2's ranking metrics (precision and lift at the top 1%, 5% and 10% and NDCG@k), each fiscal year separately and the AAERs (section 8). Aggregates only: no list of companies by alert.

## 7. The hand-computed example

Before any study code, a hand-computed example, in a separate script (`tests/referencia/gerar_exemplo_eua.py`), outside the `chiocca` package and without importing it, like the study 1 and engine v2 examples, with exact arithmetic at the boundaries:

- **A fictitious XBRL 10-K:** rows in the format of `sub.txt`, `num.txt` and `pre.txt`, with chosen values, for a small group of fictitious non-financial companies, in the fiscal year and the previous one, so that each rule of the account map (section 3.1) appears at least once: the first tag of each account and the fallbacks (revenue through a widening tag, derived gross profit, income from continuing operations through net income, short-term debt by the sum, financial expense through a widening tag and through `InterestAndDebtExpense`, with the flag, operating cash flow through the continuing-operations variant, accounts payable through the wider tag, with the flag, and total liabilities by the difference); co-registrant, segment, other-currency and other-date numbers, which must not enter; and a missing account, which leaves a signal not computable.
- **The public version at the cut-off (section 3.3):** the original 10-K and amendments with account numbers, one filed by the cut-off, which becomes the version used, and another after the cut-off, which does not enter, and an amendment without those numbers, which does not change the version.
- **The v1 and v2 signals (section 2):** the eight components and the M-score, the DPO jump, implied interest against a fictitious reference rate, the Benford deviation, the percentiles, the score and the alerts of v1, v2 and the naive rule, in a group small enough to check by hand.
- **The check:** the study code must reproduce the script's values, with a test, and the script goes into the study's SHA-256 registry at the freeze (section 10). Limitation, as in engine v2: both implementations start from the same text; the check catches implementation errors, not errors in the text.

## 8. The 2009 to 2014 AAERs: a separate description

For the {casos} Bao et al. cases ({ea} company-years) with a 10-K in the SEC data (Phase 0, section 4.1): how many cases v1, v2 and the naive rule alerted in at least one affected fiscal year, with the version public at the cut-off. Counts only, with no test and no list. In 2009 and 2010, only the largest companies filed in XBRL.

## 9. Predictions written before the data

Revised on 2026-11-24 for the new period ({primeiro} to {ultimo}) and the widened map, and again after widening financial expense and operating cash flow (section 3.1.3). No range changed; the reason for each is given next to it.

1. **v1 alert rate:** between 25% and 45% of the evaluated non-financial companies in each fiscal year. Reason: the M-score above -1.78 flags a relevant share of US companies, and the DPO decile adds 10%; implied interest fires less than in Brazil, because US interest expense does not include FX variation. **No adjustment:** the new period adds high-rate fiscal years (2022 to 2024), in which implied interest fires less (the cut-off rises with the reference rate), but the M-score and the DPO do not depend on rates, and the range already covers that variation. **No adjustment after section 3.1.3:** with more interest and more operating cash flow available, implied interest and the M-score are computed in more company-years (implied interest above all in {df_ano}), which may raise the alert rate a little in those years, within the range.
2. **v2 alert rate:** between 10.0% and 11.0% in each fiscal year. **No adjustment:** it comes from the construction of the decile, whatever the coverage.
3. **Outcome rate:** between 1.5% and 4% of the evaluated company-years. **No adjustment:** with the widened map, {antes_ficam_amp} company-years with an 8-K 4.02 and a 10-K before remain (section 5), from {ficam_amp_min} to {ficam_amp_max} a year by filing year, against about {media_am} sample 10-Ks per fiscal year before the no-revenue rule: about 2% to 3%.
4. **v1 DR:** positive, with a rate ratio between 1.1 and 1.5, and "positive association" more likely than not. **No adjustment:** the larger sample only adds power.
5. **v2 DR:** positive, with a rate ratio between 1.2 and 2.0, and "positive association". **No adjustment.**
6. **v2 paired with v1:** a positive difference, with the lower bound above zero ("v2 separates better than v1"). Reason: v2's alert group is smaller and more extreme. **No adjustment.**
7. **v2 against the naive rule:** no winner declared. Reason: leverage is also associated with restatements, through financial distress. **No adjustment.**
8. **AAERs:** of the {casos} cases, between 30% and 60% in alert under v1 and between 10% and 30% under v2 in at least one affected fiscal year. **No adjustment:** the AAER description does not depend on the sample period.

## 10. Order and timeline: target and fallback

The order is fixed: (1) registration of this text; (2) the hand-computed example (section 7), before any study code; (3) the study code, tested only on synthetic data and on the hand-computed example, with no signal computed on real data; (4) the freeze, with the SHA-256 registry of the code and of the example script; (5) only then the single computation, with the SEC data and the 8-Ks downloaded again on the day; (6) the report.

| Step | Target | Fallback |
| --- | --- | --- |
| Registration of this text and timestamp. | 2026-12-05 | 2027-01-31 |
| Hand-computed example, code tested only on synthetic data and on the example, and freeze. | 2027-01-15 | 2027-03-31 |
| Single computation, after the freeze. | 2027-01-31 | 2027-04-30 |
| Report in PT and EN, separate from Brazil's study 2. | 2027-02-28 | 2027-05-31 |

The fallback keeps the dates of the reviewed version's fallback (2027-01-31, 2027-03-31, 2027-04-30 and 2027-05-31), in the new order.

## 11. Roberto's decisions of 2026-11-24

(a) Financial companies stay out (section 3.4); (b) the revenue tags are chosen by coverage counts only, and the final list is in section 3.1.1; (c) the sample goes to fiscal {ultimo}, with the SEC data and the 8-Ks downloaded again on the day of the computation; (d) the seed is {semente}; (e) the SEC files stay outside Git, with their SHA-256 in the manifest and the download by script; (f) financial expense and operating cash flow by the same rule as revenue (section 3.1.3); (g) no tag outside the candidates enters (sections 3.1.1 and 3.1.3); (h) the hand-computed example (section 7); (i) the order and the timeline, with a target and a fallback (section 10).

The fiscal year is the year of the report date, as in the DFP; Phase 0 counts use the fiscal year declared by the company (`fy`), and the difference between the two is small.

## 12. What is left out

Financial companies, the DVA and the reader (section 3.4); any list or ordering of companies by alert; any investment recommendation; and, until Roberto decides, the US front in the README and the product.

## 13. Registration

- Date: 2026-11-24.
- Commit: the one that introduces this version under this name. Its hash is noted here in the next commit, without changing any rule above.
{anotacao}- Timestamp, as in study 2 and engine v2: `docs/carimbos/eua-registro.txt`, with the hash of the registration commit and the SHA-256 of this file in PT, as it is in the registration commit, stamped with OpenTimestamps; the `.ots` goes into the repository, and `ots upgrade` is run after confirmation on Bitcoin.
- Freeze: the study code and the script of the section 7 example go into a SHA-256 registry of the study's own, before the single computation (section 10).

## 14. Roberto's review (2026-11-24)

Roberto read the whole text, with Claude's (claude.ai) review, and approved the registration with three adjustments. The text read was the one in commit `8c529c7fd215e268304570296a1aaf5332e0acb2`; the adjustments went in with commit `08d15363cbe7191bfe2a661e86f88fafa1228f8d`, before registration, without changing any other rule.

1. **Tags outside the candidates:** none enters; the candidate lists written before the count are final (sections 3.1.1 and 3.1.3).
2. **The hand-computed example (section 7):** a fictitious XBRL 10-K, with chosen values, going through the account map (including the fallbacks and the flags), the public version at the cut-off and the v1 and v2 signals, in a separate script, written before the study code; the code must reproduce the values, and the script goes into the study's SHA-256 registry.
3. **The order and the timeline (section 10):** first the registration of the text; then the code, tested only on synthetic data and on the hand-computed example; the freeze; and only then the single computation; with a target and a fallback.
"""

T = {"pt": PT, "en": EN}


CONTAS_COBERTURA = ("receita_liquida", "ativo_total", "ativo_circulante", "contas_a_receber", "imobilizado",
                    "passivo_circulante", "fornecedores", "emprestimos_cp", "emprestimos_lp", "patrimonio_liquido",
                    "custo_vendas", "resultado_bruto", "despesas_vendas_gerais_adm", "despesas_financeiras",
                    "lucro_operacoes_continuadas", "lucro_liquido", "caixa_operacional", "depreciacao",
                    "passivo_total")  # fmt: skip
CABECALHOS = {
    "pt": {"receita": "| Candidata | Ganho no primeiro passo | Entrou | Ganho quando entrou |", "sim": "sim", "nao": "não",
           "descoberta": "| Tag | 10-K sem as três tags com ela | Candidata |", "cobertura": "| Conta | {primeiro} a {ultimo} | Menor ano | Maior ano |"},
    "en": {"receita": "| Candidate | Gain at the first step | Entered | Gain when it entered |", "sim": "yes", "nao": "no",
           "descoberta": "| Tag | 10-Ks without the three tags with it | Candidate |", "cobertura": "| Account | {primeiro} to {ultimo} | Lowest year | Highest year |"},
}  # fmt: skip


def _tabelas(m: dict[str, Any], lang: str) -> dict[str, str]:
    """As tabelas da ampliação da receita, da descoberta e da cobertura, do JSON da Fase 0."""
    c, i = CABECALHOS[lang], (lambda v: inteiro(int(v), lang))
    p1 = lambda x: pct(x, lang, 1)  # noqa: E731
    amp = m["ampliacao"]
    linhas = [c["receita"], "| --- | ---: | --- | ---: |"]
    for t in m["candidatas"]:
        entrou = t in amp["escolhidas"]
        linhas.append(f"| `{t}` | {i(amp['ganho_no_primeiro_passo'].get(t, 0))} | {c['sim'] if entrou else c['nao']} | "
                      f"{i(amp['ganhos'][t]) if entrou else '—'} |")  # fmt: skip
    descoberta = [c["descoberta"], "| --- | ---: | --- |"]
    descoberta += [f"| `{t}` | {i(n)} | {c['sim'] if t in m['candidatas'] or t in fsds.MAPA['receita_liquida'] else c['nao']} |"
                   for t, n in m["descoberta"]]  # fmt: skip
    anos = [str(a) for a in range(PRIMEIRO, ULTIMO + 1)]
    cob = m["juros_e_caixa"]["cobertura_por_ano_regras_novas"]
    n = sum(cob[a]["10k"] for a in anos)
    cobertura = [c["cobertura"].format(primeiro=PRIMEIRO, ultimo=ULTIMO), "| --- | ---: | ---: | ---: |"]
    for conta in CONTAS_COBERTURA:
        conjunto = sum(cob[a][conta] * cob[a]["10k"] for a in anos) / n
        cobertura.append(f"| `{conta}` | {p1(conjunto)} | {p1(min(cob[a][conta] for a in anos))} | "
                         f"{p1(max(cob[a][conta] for a in anos))} |")  # fmt: skip
    return {"tabela_receita": "\n".join(linhas), "tabela_descoberta": "\n".join(descoberta),
            "tabela_cobertura": "\n".join(cobertura)}  # fmt: skip


TEXTOS_JC = {
    "pt": {"cab_res": "| Conta | Candidata | Conceito mais largo | Ganho no primeiro passo | Entrou | Ganho quando entrou |",
           "sim": "sim", "nao": "não", "conta_tag": "| Conta | Tag | ",
           "resumo": "Pelo valor anual, a cobertura da despesa financeira passa de {j_antes} para {j_depois} no conjunto de "
                     "{primeiro} a {ultimo} e, em {df_ano}, de {j_ano_antes} para {j_ano_depois}; {j_largo} entregas ficam "
                     "cobertas só por uma tag de conceito mais largo, com a marca. A do caixa operacional passa de {c_antes} "
                     "para {c_depois} e, em {co_ano}, de {c_ano_antes} para {c_ano_depois}. Uma parte das companhias não tem "
                     "dívida nem despesa de juros, e por isso a despesa financeira não chega perto de 100%.",
           "leitura": "Leitura: em {df_ano}, o uso de `InterestExpense` cai para {ie_ano} e o de `InterestExpenseNonoperating` "
                      "sobe de {nop_antes} no ano anterior para {nop_ano}; de {co_ini} a {co_fim}, a variante só de operações "
                      "continuadas chega a {cc_max} dos 10-K, no ano em que o total cai para {nc_min}. As quedas vêm de troca "
                      "de tag, não de falta do dado."},
    "en": {"cab_res": "| Account | Candidate | Wider concept | Gain at the first step | Entered | Gain when it entered |",
           "sim": "yes", "nao": "no", "conta_tag": "| Account | Tag | ",
           "resumo": "By the annual value, financial expense coverage goes from {j_antes} to {j_depois} over {primeiro} to "
                     "{ultimo} and, in {df_ano}, from {j_ano_antes} to {j_ano_depois}; {j_largo} filings are covered only by "
                     "a wider-concept tag, with the flag. Operating cash flow goes from {c_antes} to {c_depois} and, in "
                     "{co_ano}, from {c_ano_antes} to {c_ano_depois}. Some companies have no debt and no interest expense, "
                     "so financial expense does not come close to 100%.",
           "leitura": "Reading: in {df_ano}, the use of `InterestExpense` falls to {ie_ano} and that of "
                      "`InterestExpenseNonoperating` rises from {nop_antes} in the previous year to {nop_ano}; from {co_ini} "
                      "to {co_fim}, the continuing-operations-only variant reaches {cc_max} of the 10-Ks, in the year the "
                      "total falls to {nc_min}. The drops come from a tag change, not from missing data."},
}  # fmt: skip


def _juros_e_caixa(jc: dict[str, Any], lang: str) -> dict[str, str]:
    """As tabelas e as frases da seção 3.1.3, do JSON da Fase 0 (só contagens)."""
    t, i = TEXTOS_JC[lang], (lambda v: inteiro(int(v), lang))
    p1 = lambda x: pct(x, lang, 1)  # noqa: E731
    anos = [str(a) for a in range(PRIMEIRO, ULTIMO + 1)]
    juros, caixa = jc["contas"]["despesas_financeiras"], jc["contas"]["caixa_operacional"]
    n = {a: juros["cobertura_por_ano"][a]["10k"] for a in anos}
    uso = [t["conta_tag"] + " | ".join(anos) + " |", "| --- | --- | " + " | ".join("---:" for _ in anos) + " |"]
    for conta, x in (("despesas_financeiras", juros), ("caixa_operacional", caixa)):
        for tag in (*x["base"], *x["candidatas"]):
            uso.append(
                f"| `{conta}` | `{tag}` | " + " | ".join(p1(x["uso_por_ano"][tag][a] / n[a]) for a in anos) + " |"
            )
    res = [t["cab_res"], "| --- | --- | --- | ---: | --- | ---: |"]
    for conta, x in (("despesas_financeiras", juros), ("caixa_operacional", caixa)):
        amp = x["ampliacao"]
        for tag in x["candidatas"]:
            entrou = tag in amp["escolhidas"]
            res.append(f"| `{conta}` | `{tag}` | {t['sim'] if tag in jc['conceito_largo'] else t['nao']} | "
                       f"{i(amp['ganho_no_primeiro_passo'].get(tag, 0))} | {t['sim'] if entrou else t['nao']} | "
                       f"{i(amp['ganhos'][tag]) if entrou else '—'} |")  # fmt: skip

    def frac(x: dict[str, Any], chave: str, ano: str | None = None) -> str:
        c = x["cobertura_por_ano"]
        if ano:
            return p1(c[ano][chave] / c[ano]["10k"])
        return p1(sum(c[a][chave] for a in anos) / sum(c[a]["10k"] for a in anos))

    df_ano = min(anos, key=lambda a: juros["cobertura_por_ano"][a]["antes"] / n[a])
    co_ano = min(anos, key=lambda a: caixa["cobertura_por_ano"][a]["antes"] / n[a])
    nc = caixa["base"][0]
    cc = caixa["candidatas"][0]
    co_baixos = [a for a in anos if caixa["uso_por_ano"][nc][a] / n[a] < 0.8]
    anterior = str(int(df_ano) - 1)
    v = {"primeiro": str(PRIMEIRO), "ultimo": str(ULTIMO), "df_ano": df_ano, "co_ano": co_ano,
         "j_antes": frac(juros, "antes"), "j_depois": frac(juros, "depois"), "j_ano_antes": frac(juros, "antes", df_ano),
         "j_ano_depois": frac(juros, "depois", df_ano), "j_largo": i(sum(juros["cobertura_por_ano"][a]["so_conceito_largo"] for a in anos)),
         "c_antes": frac(caixa, "antes"), "c_depois": frac(caixa, "depois"), "c_ano_antes": frac(caixa, "antes", co_ano),
         "c_ano_depois": frac(caixa, "depois", co_ano),
         "ie_ano": p1(juros["uso_por_ano"]["InterestExpense"][df_ano] / n[df_ano]),
         "nop_antes": p1(juros["uso_por_ano"]["InterestExpenseNonoperating"].get(anterior, 0) / n.get(anterior, 1)),
         "nop_ano": p1(juros["uso_por_ano"]["InterestExpenseNonoperating"][df_ano] / n[df_ano]),
         "co_ini": min(co_baixos) if co_baixos else co_ano, "co_fim": max(co_baixos) if co_baixos else co_ano,
         "cc_max": p1(max(caixa["uso_por_ano"][cc][a] / n[a] for a in anos)),
         "nc_min": p1(min(caixa["uso_por_ano"][nc][a] / n[a] for a in anos))}  # fmt: skip
    marca = lambda tag: f"`{tag}`" + (" (*)" if tag in jc["conceito_largo"] else "")  # noqa: E731
    return {"tabela_uso": "\n".join(uso), "tabela_juros_caixa": "\n".join(res),
            "resumo_juros_caixa": t["resumo"].format(**v), "leitura_uso": t["leitura"].format(**v),
            "ordem_juros": ", ".join(marca(x) for x in juros["ampliacao"]["ordem"]),
            "ordem_caixa": ", ".join(f"`{x}`" for x in caixa["ampliacao"]["ordem"])}  # fmt: skip


def valores(d: dict[str, Any], lang: str) -> dict[str, str]:
    """Os números da Fase 0 citados no pré-registro, formatados para a língua."""
    f, i = d["fsds"], (lambda v: inteiro(int(v), lang))
    p0 = lambda x: pct(x, lang, 0)  # noqa: E731
    anos = [str(a) for a in range(PRIMEIRO, ULTIMO + 1)]
    ex, it, cob, pe = f["exclusoes_10k"], f["itens_8k"], f["cobertura"], f["por_exercicio"]
    soma = lambda k: sum(ex[a][k] for a in anos)  # noqa: E731
    rec = [cob[a]["contas"]["receita_liquida"] for a in anos]
    bruto = [cob[a]["contas"]["resultado_bruto"] for a in anos]
    ficam = [it[str(a)]["antes_restantes"] for a in range(2012, 2026)]
    tot = lambda k: sum(x[k] for x in it.values())  # noqa: E731
    m = f["mapa_ampliado"]
    sr, e8 = m["sem_receita_por_ano"], m["exclusoes_8k"]
    n_am = sum(sr[a]["10k"] for a in anos)
    sem_amp = sum(sr[a]["sem_receita_ampliada"] for a in anos)
    ficam_amp = [e8[str(a)]["antes_restantes"] for a in range(2012, 2026)]
    cob_am = m["cobertura_por_ano"]  # a cobertura antes da terceira rodada (o ano da queda dos juros)
    df_ano = min(anos, key=lambda a: cob_am[a]["despesas_financeiras"])
    co_ano = min(anos, key=lambda a: cob_am[a]["caixa_operacional"])
    co_baixos = [a for a in anos if cob_am[a]["caixa_operacional"] < 0.8]
    return {
        "primeiro": str(PRIMEIRO), "ultimo": str(ULTIMO), "semente": str(SEMENTE),
        "rec_min": p0(min(rec)), "rec_max": p0(max(rec)), "bruto_min": p0(min(bruto)), "bruto_max": p0(max(bruto)),
        "p90": i(max(pe[a]["prazo_p90_dias"] for a in anos)),
        "n10k": i(soma("10k")), "fin": i(soma("financeiras")), "spac": i(soma("sic_6770")),
        "spac_sem": i(soma("sic_6770_sem_receita")), "sem_dem": i(soma("sem_receita_demais")),
        "ficam10k": i(soma("restantes")),
        "antes": i(tot("companhias_com_10k_fsds_antes")), "antes_fin": i(tot("antes_financeiras")),
        "antes_spac": i(tot("antes_sic_6770")), "antes_sem": i(tot("antes_sem_receita_demais")),
        "antes_ficam": i(tot("antes_restantes")),
        "ficam_min": i(min(ficam)), "ficam_max": i(max(ficam)),
        "casos": i(f["aaer"]["casos_com_10k"]), "ea": i(f["aaer"]["empresa_anos_com_10k"]),
        "ordem_receita": ", ".join(f"`{t}`" for t in m["ampliacao"]["ordem"]),
        "n_escolhidas": i(len(m["ampliacao"]["escolhidas"])), "ganho_min": pct(m["ganho_minimo"], lang, 1),
        "n_am": i(n_am), "sem_tres": i(m["entregas_sem_as_tres_tags"]),
        "sem_amp": i(sem_amp), "sem_f0": i(sum(sr[a]["sem_receita_fase0"] for a in anos)),
        "ficam_amp10k": i(n_am - sem_amp), "media_am": i(round(n_am / len(anos), -2)),
        "antes_ficam_amp": i(sum(x["antes_restantes"] for x in e8.values())),
        "ficam_amp_min": i(min(ficam_amp)), "ficam_amp_max": i(max(ficam_amp)),
        "df_min": pct(cob_am[df_ano]["despesas_financeiras"], lang, 1), "df_ano": df_ano,
        "co_min": pct(cob_am[co_ano]["caixa_operacional"], lang, 1), "co_ano": co_ano,
        "co_ini": min(co_baixos), "co_fim": max(co_baixos),
        **_tabelas(m, lang),
        **_juros_e_caixa(m["juros_e_caixa"], lang),
    }  # fmt: skip


def render(d: dict[str, Any], lang: str) -> str:
    anotacao = ANOTACAO[lang].format(c=COMMIT_DE_REGISTRO) if COMMIT_DE_REGISTRO else ""
    return T[lang].format(**valores(d, lang), anotacao=anotacao)


def main() -> None:
    d = json.loads(fase0.SAIDA.read_text(encoding="utf-8"))
    for lang, caminho in DOCS.items():
        caminho.write_text(render(d, lang), encoding="utf-8")
        RASCUNHOS[lang].write_text(AVISOS[lang], encoding="utf-8")
    print("gravado:", ", ".join(str(c.relative_to(RAIZ)) for c in (*DOCS.values(), *RASCUNHOS.values())))


if __name__ == "__main__":
    main()
