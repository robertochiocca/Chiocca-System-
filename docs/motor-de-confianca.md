# Motor de confiança (Fase B do v2)

Quatro módulos em `chiocca/v2/`, que descrevem os números do motor v1 (estudo 1) sem mudar nenhum deles. Origem de cada arquivo em [`docs/origem-do-codigo.md`](origem-do-codigo.md); resultado das conferências na base inteira em [`docs/conferencias.md`](conferencias.md).

## Validade (`validade.py`)

- Três estados: `ok` (o número vai para a tela), `indefinido` (não existe número: o "não calculável" do motor v1, com o mesmo motivo) e `implausivel` (o número existe, mas uma conferência dos dados de entrada falhou).
- Fora de `ok`, o motivo é obrigatório nas duas línguas. `None` e `NaN` nunca servem de sinal de falta.
- A ponte com o motor v1 não muda nenhum valor: só traduz o resultado.
- Variação percentual só com base positiva; com base zero ou negativa, o resultado é `indefinido`.

## Conferências (`conferencias.py`)

- **Identidade:** ativo total = passivo total; ativo e passivo pelas suas partes; os cinco subtotais da DRE (resultado bruto, resultado antes do financeiro, antes dos tributos, operações continuadas e lucro do período); soma da DFC e saldos da DFC.
- **Reconciliação:** saldo final da DFC contra o caixa e equivalentes do balanço; saldo inicial da DFC contra o caixa do balanço anterior. Quando o saldo da DFC fecha com caixa e equivalentes mais aplicações financeiras (1.01.01 + 1.01.02), o resultado é "fecha com caixa amplo", com nota, e não conta como falha.
- **Não preenchido:** ativo total igual a zero na coluna. No produto, todo indicador que usa o balanço dessa coluna fica "não calculável", nunca calculado com zero (`linhagem.aplicar_nao_preenchido`). O valor do motor v1 não muda; muda só o que o produto mostra.
- **Sinal incomum:** ativo total negativo; nove contas de saldo negativas; receita negativa; custo e despesas de vendas e administrativas positivos. Incomum não é impossível: uma reversão de provisão maior que a despesa do ano pode deixar a despesa positiva.
- Tolerância de R$ 1.000 por parcela, só para arredondamento. Conta ausente não vira zero: "não se aplica". Os códigos por conta (todas contas fixas da CVM) valem para o plano não financeiro; nos outros planos, só ativo total = passivo total e as identidades da DFC.
- Cada conferência roda nas duas colunas da DFP (ÚLTIMO e PENÚLTIMO).

## Linhagem (`linhagem.py`)

- Para cada sinal do motor v1 de uma empresa-ano: o documento (DFP, versão, data de entrega, dados abertos ou ENET, endereço e hash do arquivo), a fórmula, os valores do caso e as evidências.
- Cada evidência é uma linha da DFP: demonstração, coluna, código, descrição oficial, valor em reais e a linha no arquivo de origem (o CSV dentro do ZIP dos dados abertos, ou o arquivo do ENET em cache).
- Transformações registradas: escala para reais, juros pagos movidos para o financiamento, depreciação pelas linhas da DFC achadas por texto, depreciação combinada, deduplicação, rota do ENET.
- O valor do sinal sai do motor v1; a ficha só descreve o caminho.

## Confiança (`confianca.py`)

- Cinco critérios, cada um `ok`, `atencao` ou `problema`, com motivo em PT e EN: fonte, completude, consistência (conferências nas demonstrações que o sinal usa: falha de identidade ou balanço não preenchido é problema; reconciliação que não fecha e sinal incomum são atenção; caixa amplo não é falha), atualidade e método (o que o estudo 1 mostrou, com os números lidos da saída do estudo).
- Nível por regra escrita, sem nota numérica: `baixa` se algum critério tem problema; `media` se algum tem atenção; senão `alta`.
- Pelo resultado do estudo 1, o critério de método fica em atenção para todo sinal do motor v1. Por isso nenhum sinal do motor v1 chega a confiança alta: é consequência direta do resultado publicado, não um ajuste.
