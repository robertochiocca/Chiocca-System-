# Pré-registro do estudo

> **Preencha e assine ANTES de baixar ou olhar qualquer dado.** O agente de código não preenche este arquivo: ele só lê. Se algum campo estiver vazio, o agente para e pergunta.
>
> Por que isso existe: depois de saber que a Americanas fraudou, é fácil escolher, sem perceber, o corte e os sinais que "teriam pego" a empresa. Decidir antes é o que torna o resultado confiável.

## 1. Pergunta

Com dados públicos disponíveis **na época**, os sinais do catálogo teriam alertado para os casos do gabarito antes de eles virem a público? Quantos alarmes falsos isso custaria?

## 2. Amostra

- Empresas: todas as companhias abertas com DFP na CVM, **financeiras e não financeiras**, **incluindo as que tiveram o registro cancelado depois**. Elas formam dois grupos, avaliados separadamente:
  - **não financeiras:** M-score, DPO e juro implícito;
  - **financeiras** (bancos, seguradoras, resseguradoras e demais instituições financeiras): peso de ganhos não recorrentes. O M-score, o DPO e o juro implícito não se aplicam a elas (o próprio artigo de 1999 exclui financeiras; não há custo das vendas nem prazo de fornecedores).
- Período de cálculo: de 2010 (ou o primeiro ano disponível nos dados abertos de DFP da CVM) a 2023.
- Exclusões (e o motivo): no grupo das não financeiras, empresas sem receita no ano (holdings puras e empresas pré-operacionais), porque vários índices dividem pela receita.
- As empresas que **nunca** republicaram ficam na amostra: sem elas não dá para medir alarme falso (é o limite do artigo de Alves e Oliveira, que só olhou empresas que republicaram).

## 3. Regra de "como era na época"

- Para cada empresa e ano, usar só a versão da demonstração que já era pública na data de corte.
- Data de corte de cada ano: 30 de abril do ano seguinte.

## 4. Sinais e regras de alerta

| Sinal | Regra de alerta | Decidido em |
| --- | --- | --- |
| mscore_beneish | M > −1,78 | 04/11/2026 |
| dpo_salto | variação do DPO (t menos t−1) no decil superior do ano | 04/11/2026 |
| juro_implicito | juro implícito > CDI médio do ano + 10 p.p. | 04/11/2026 |
| peso_nao_recorrente (só financeiras) | proporção no decil superior do ano dentro do grupo das financeiras | 04/11/2026 |

Uma empresa está "em alerta" num ano se: pelo menos um dos sinais do seu grupo disparou (três para não financeiras, um para financeiras). O lucro sem caixa aparece na ficha, mas não dispara alerta sozinho (já entra no M-score via TATA).

### 4.1 Escolhas de cálculo

Cada escolha muda os números. As opções vêm dos artigos lidos (guia de leitura do dossiê, seção 3).

| Escolha | Opções | Decisão |
| --- | --- | --- |
| Versão do TATA | fluxo de caixa (Beneish, Lee e Nichols 2013; padrão do catálogo) ou balanço (Beneish 1999) | fluxo de caixa |
| Conta faltante ou denominador zero | "não calculável" (padrão do projeto) ou valores neutros do artigo de 1999 (AQI = 1; DEPI = SGAI = 1) | "não calculável"; valores neutros só como teste de robustez |
| Valores extremos | não mexer, ou aparar os índices em 1% e 99% de cada ano, como no artigo de 1999 | não mexer |
| Depreciação e amortização numa linha só da DFC | usar o total e marcar a empresa-ano, ou deixar o DEPI não calculável | usar o total e marcar a empresa-ano |
| Juros pagos na DFC (CPC 03 deixa a empresa escolher a seção) | mover para financiamento em todas as empresas, ou usar como apresentado | mover para financiamento em todas as empresas |
| Ano de adoção do CPC 06 (R2), 2019 | excluir da avaliação, manter e marcar, ou retirar os arrendamentos dos índices | manter e marcar |
| Risco sacado informado em nota explicativa | somar à dívida no LVGI e no juro implícito, ou ignorar | ignorar no estudo principal (depende de leitura manual de nota) |

### 4.2 Previsões escritas antes dos dados

Para cada caso do gabarito: quais sinais devem disparar, quais não, e por quê. Escrever aqui impede a explicação feita depois.

- Americanas: espero que o M-score dispare em pelo menos um ano antes de 2023, puxado por TATA e AQI, e não pelo GMI (a VPC fictícia aumentou a margem). Espero que DPO e juro implícito **não** disparem, porque os lançamentos ficaram dentro de Fornecedores e os juros não passaram pela despesa financeira.
- IRB: entra no grupo das financeiras. Espero que o sinal **não** dispare antes da data pública: os ganhos lançados fora de período estão nos ITRs de 2019, e a DFP de 2019 só saiu depois de 10/02/2020. Com dados anuais, a última DFP antes da data pública é a de 2018. Se não disparar, o resultado mostra que pegar o caso exigiria dados trimestrais (ITR), o que fica para uma fase seguinte.

## 5. O que conta como acerto

Um caso do gabarito é **acertado** se a empresa entrou em alerta em pelo menos um ano do período afetado, usando só dados públicos antes da `data_publica`.

## 6. Métricas

- Taxa de alerta: fração das empresas em alerta por ano.
- Casos acertados ÷ casos do gabarito.
- Alarmes por acerto: empresas em alerta para cada caso acertado.

## 7. Regra boba de comparação

Se o detector não ganhar desta regra, isso é resultado e vai para o resumo: sinalizar o decil mais endividado (passivo total ÷ ativo total) de cada ano, dentro de cada grupo.

## 8. Divisão no tempo

- Período em que posso ajustar as regras: até o exercício de 2016.
- Período de teste, que não abro até o fim: de 2017 a 2023.
- Limite assumido: os casos do gabarito caem todos no período de teste. No período de ajuste só dá para calibrar o alarme falso, não o acerto.

## 9. Se o resultado for ruim

O estudo é publicado do mesmo jeito, com o resultado que deu.

---

Assinado por: Roberto Chiocca · Data: 04/11/2026

## Emendas

Qualquer mudança entra aqui, com data, o que mudou e por quê; o texto acima não é editado.

### Emenda 1 · 04/11/2026 · período afetado da Americanas (antes de qualquer dado)

- **Fonte:** release de resultados de 2022 da Americanas. Ele reapresenta 2021 ano a ano e diz que todos os efeitos da fraude ocorridos antes de 31/12/2020 foram ajustados no saldo de abertura de 01/01/2021, **sem separar por ano**. O fato relevante de 16/07/2024 confirma a fraude, mas não dá anos.
- **Regra principal:** período afetado = **2021**, único exercício com efeito documentado ano a ano. Fica registrado no gabarito antes da Fase 1.
- **Análise secundária, rotulada como tal:** acerto se houver alerta em qualquer exercício até 2021 cuja DFP saiu antes de 11/01/2023. Ela é reportada à parte e nunca substitui a principal.
- Se um documento oficial posterior der os anos (relatório do comitê, processo da CVM), isso vira nova emenda, feita antes de abrir o período de teste.

### Emenda 2 · 04/11/2026 · fórmula do peso_nao_recorrente para financeiras

- O catálogo e o PROMPT já marcam o sinal como `mvp` para financeiras.
- Bancos e seguradoras usam outro plano de contas na DFP, então os códigos 3.04.04 e 3.05 não valem para eles. A fórmula para financeiras fica definida pelo **texto** da conta, não pelo código:
  - **numerador:** soma das linhas da DRE cujo `DS_CONTA` contém "outras receitas operacionais" (sem diferenciar maiúsculas e acentos), só a parte positiva;
  - **denominador:** valor absoluto da linha "resultado antes dos tributos sobre o lucro";
  - se alguma das duas não for encontrada, o sinal fica "não calculável" e a falha entra no relatório.
- Na Fase 0, o agente só **confirma** se essas linhas existem nos arquivos e registra os códigos. Se não existirem, a fórmula muda por nova emenda antes de qualquer cálculo.

### Emenda 3 · 04/11/2026 · teto de acerto e métrica secundária

- Com a regra da seção 5, o IRB não pode ser acertado: o período afetado é 2019 e a DFP de 2019 saiu depois da data pública (10/02/2020). O máximo possível no estudo principal é **1 acerto em 2 casos**, e isso vai escrito no resumo.
- **Métrica secundária, rotulada como tal:** alerta na última DFP publicada antes da data pública, mesmo fora do período afetado (no IRB, a DFP de 2018). Ela mede alerta antecipado, não acerto, e não entra na conta principal.
