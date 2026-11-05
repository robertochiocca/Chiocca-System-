# Pré-registro do estudo

> **Preencha e assine ANTES de baixar ou olhar qualquer dado.** O agente de código não preenche este arquivo: ele só lê. Se algum campo estiver vazio, o agente para e pergunta.
>
> Por que isso existe: depois de saber que a Americanas fraudou, é fácil escolher, sem perceber, o corte e os sinais que "teriam pego" a empresa. Decidir antes é o que torna o resultado confiável.

## 1. Pergunta

Com dados públicos disponíveis **na época**, os sinais do catálogo teriam alertado para os casos do gabarito antes de eles virem a público? Quantos alarmes falsos isso custaria?

## 2. Amostra

- Empresas: todas as companhias abertas **não financeiras** com DFP na CVM, **incluindo as que tiveram o registro cancelado depois**.
- Período de cálculo: de ______ a ______.
- Exclusões além das financeiras (e o motivo): ______
- As empresas que **nunca** republicaram ficam na amostra: sem elas não dá para medir alarme falso (é o limite do artigo de Alves e Oliveira, que só olhou empresas que republicaram).

## 3. Regra de "como era na época"

- Para cada empresa e ano, usar só a versão da demonstração que já era pública na data de corte.
- Data de corte de cada ano: ______ (exemplo: 30 de abril do ano seguinte).

## 4. Sinais e regras de alerta

| Sinal | Regra de alerta | Decidido em |
| --- | --- | --- |
| mscore_beneish | M > ______ (escolha −1,78 ou −2,22) | ______ |
| dpo_salto | ______ | ______ |
| juro_implicito | ______ | ______ |

Uma empresa está "em alerta" num ano se: ______ (exemplo: pelo menos um sinal disparou).

### 4.1 Escolhas de cálculo

Cada escolha muda os números. As opções vêm dos artigos lidos (guia de leitura do dossiê, seção 3).

| Escolha | Opções | Decisão |
| --- | --- | --- |
| Versão do TATA | fluxo de caixa (Beneish, Lee e Nichols 2013; padrão do catálogo) ou balanço (Beneish 1999) | ______ |
| Conta faltante ou denominador zero | "não calculável" (padrão do projeto) ou valores neutros do artigo de 1999 (AQI = 1; DEPI = SGAI = 1) | ______ |
| Valores extremos | não mexer, ou aparar os índices em 1% e 99% de cada ano, como no artigo de 1999 | ______ |
| Depreciação e amortização numa linha só da DFC | usar o total e marcar a empresa-ano, ou deixar o DEPI não calculável | ______ |
| Juros pagos na DFC (CPC 03 deixa a empresa escolher a seção) | mover para financiamento em todas as empresas, ou usar como apresentado | ______ |
| Ano de adoção do CPC 06 (R2), 2019 | excluir da avaliação, manter e marcar, ou retirar os arrendamentos dos índices | ______ |
| Risco sacado informado em nota explicativa | somar à dívida no LVGI e no juro implícito, ou ignorar | ______ |

### 4.2 Previsões escritas antes dos dados

Para cada caso do gabarito: quais sinais devem disparar, quais não, e por quê. Escrever aqui impede a explicação feita depois.

- Americanas: ______ (ponto de partida: a VPC fictícia aumentou a margem, então o GMI tende a não disparar; DPO e juro implícito podem não disparar porque os lançamentos ficaram dentro de Fornecedores; AQI, TATA e rendimento do caixa são os candidatos)
- IRB: ______ (fora do M-score por ser resseguradora; o sinal relevante é o peso de ganhos não recorrentes)

## 5. O que conta como acerto

Um caso do gabarito é **acertado** se a empresa entrou em alerta em pelo menos um ano do período afetado, usando só dados públicos antes da `data_publica`.

## 6. Métricas

- Taxa de alerta: fração das empresas em alerta por ano.
- Casos acertados ÷ casos do gabarito.
- Alarmes por acerto: empresas em alerta para cada caso acertado.

## 7. Regra boba de comparação

Se o detector não ganhar desta regra, isso é resultado e vai para o resumo: ______ (exemplo: sinalizar o decil mais endividado de cada ano).

## 8. Divisão no tempo

- Período em que posso ajustar as regras: até ______.
- Período de teste, que não abro até o fim: de ______ a ______.

## 9. Se o resultado for ruim

O estudo é publicado do mesmo jeito, com o resultado que deu.

---

Assinado por: ______ · Data: ______
