# Notas de procedimento do estudo dos EUA, antes do cálculo único

> Escritas em 24/11/2026, depois do congelamento do código do estudo (commit `dd9b662e1f2d52355722b6fe102d7e5515782115`) e antes do cálculo único, que só começa com a autorização de Roberto, depois do PR e da release do congelamento. Estas notas não mudam o [pré-registro do estudo dos EUA](pre-registro-eua.md) nem o código congelado: registram as quatro regras de implementação que o texto registrado não detalha e que já estão no código, cada uma com o motivo, e as leituras de formato feitas nos arquivos reais da SEC. Nenhum sinal americano foi calculado. Alerta, não acusação.

## 1. Onde as regras estão

- **O código congelado:** `chiocca/eua/estudo.py`, com o SHA-256 `6440c49a6ede796e51f2b6c3d7e1c2b63201bd939afe1507feb87c652b0f4ffa` no [registro de congelamento](eua_codigo_congelado.json), gravado no commit `dd9b662e1f2d52355722b6fe102d7e5515782115`. As regras abaixo são as do docstring desse arquivo, com o mesmo número.
- **As outras regras:** as de (i) a (vi) estão no exemplo calculado à mão (`tests/referencia/gerar_exemplo_eua.py`) e no mapa das contas (`chiocca/eua/mapa.py`); a (iii), a versão pública no corte, e a (v), a ordem de entrada, também estão no docstring de `estudo.py`. As de (vii) a (x) só existem no código do estudo.

## 2. As regras de (vii) a (x), cada uma com o motivo

### (vii) Janelas que se cruzam

- **Regra:** a empresa-ano é positiva se um episódio se abre depois do corte dela e até o último dia do mesmo mês do ano seguinte (os 12 meses da seção 5). Se as janelas de duas empresa-anos da mesma companhia se cruzam, o episódio fica com a de corte mais recente antes da abertura dele. As janelas são as das não financeiras da amostra; um episódio fora de todas elas entra só na descrição (`desfecho` e `fim_da_janela`).
- **Motivo:** a seção 5 diz que as janelas de exercícios seguidos não se sobrepõem, o que vale quando os exercícios terminam a 12 meses um do outro. Quando uma companhia muda a data de fim do exercício e entrega dois 10-K a menos de 12 meses um do outro, as janelas se cruzam. Ficar com o corte mais recente dá o episódio às demonstrações públicas mais novas na data do 8-K que o abre e mantém a regra registrada de que cada episódio cai em no máximo uma empresa-ano. O fim da janela no último dia do mês vem de o corte ser sempre o último dia de um mês (seção 3.3); para o exercício de 2024, ele cai em 30/04/2026, a data da seção 5.

### (viii) Os exercícios de 2009 e 2010, só para os AAERs

- **Regra:** os sinais e os alertas também são calculados nos exercícios de 2009 e 2010, só para a descrição dos AAERs (seção 8). Esses exercícios não entram nas medidas, nas exclusões nem nas descritivas por exercício, que são de 2011 a 2024, como na seção 4 (`EXERCICIOS_CALCULADOS` e `aaers`).
- **Motivo:** a seção 8 conta os casos de Bao et al. com anos afetados de 2009 a 2014, com a versão pública no corte, e lembra que em 2009 e 2010 só as companhias maiores entregavam em XBRL. Para saber se o v1, o v2 e a regra boba alertaram nesses anos, é preciso calcular o grupo inteiro de cada exercício, porque o decil do DPO, o da regra boba e os percentis do v2 são dentro do exercício. Como os grupos são por exercício, calcular 2009 e 2010 não muda nenhum resultado de 2011 a 2024.

### (ix) A exclusão "sem nenhum sinal calculável"

- **Regra:** a última exclusão da seção 4, "sem nenhum sinal calculável", conta as não financeiras que nem o v1 nem o v2 avaliam. As medidas são calculadas nas avaliadas pelo v1; as que só o v2 avalia (nenhum sinal do v1, mas o desvio de Benford) ficam à parte, só contadas, com a taxa do desfecho.
- **Motivo:** a seção 4 não diz de qual motor é o sinal, e o v2 tem um sinal que o v1 não tem, o desvio de Benford. A seção 6 já fixa as medidas nas avaliadas pelo v1 e o alerta do v2 calculado entre todas as que o v2 avalia, como no estudo do Brasil. Contar como excluída só a empresa-ano que nenhum dos dois avalia não tira do cálculo do v2 nenhuma que ele avalia, e o relatório mostra as duas contagens.

### (x) Os 8-K desde 2004

- **Regra:** os episódios partem de todos os 8-K e 8-K/A com o item 4.02 do histórico de entregas do EDGAR desde 2004, até 30/04/2026 (`PRIMEIRO_ANO_DO_ITEM`). As contagens da Fase 0 continuam desde 2009: o padrão de `chiocca.eua.itens.entregas` não mudou.
- **Motivo:** a seção 5 abre o episódio no primeiro 8-K da companhia com o item 4.02. Lendo só desde 2009, um 8-K de 2009 que pertence a um episódio aberto antes abriria um episódio novo e, numa sequência de 8-K a menos de 365 dias uns dos outros, poderia mudar a data de abertura dos episódios seguintes. O item 4.02 existe desde 23/08/2004, quando entraram em vigor as regras novas do 8-K.

## 3. As leituras de formato nos arquivos reais da SEC

Em 24/11/2026, durante a escrita do código e antes do congelamento, para conferir que o leitor do estudo (`chiocca.eua.estudo.le_trimestre`) aceita os arquivos como vêm da SEC. **Nenhum valor foi lido:** a coluna `value` de `num.txt` não foi carregada; nada além de nomes de arquivo, linhas de cabeçalho e contagens de linhas foi impresso; nenhum sinal, conta ou alerta foi calculado. Os números abaixo saem de [`docs/eua_leituras_de_formato.json`](eua_leituras_de_formato.json).

1. **Os nomes dos arquivos em cada zip:** nos 68 trimestres, de 2009T1 a 2025T4, os 68 têm `sub.txt`, `num.txt` e `pre.txt`.
2. **O trimestre sem entregas (2009T1):** a linha de cabeçalho dos três arquivos e o número de linhas de dados, como na Fase 0: `sub.txt` 0; `num.txt` 0; `pre.txt` 0.
3. **A contagem de linhas (2016T1):** em cada arquivo, o número de linhas contra o número de linhas lidas pelo pandas sem tratamento de aspas (`quoting=3`, como o leitor do estudo lê `num.txt` e `pre.txt`) e com o tratamento padrão, carregando só colunas de identificação (`sub.txt`: `adsh`; `num.txt`: `adsh`, `tag`; `pre.txt`: `adsh`, `plabel`). As três contagens bateram em cada arquivo; as de `sub.txt` e `num.txt` são as da Fase 0.

| Arquivo | Linhas | Lidas sem aspas | Lidas com o padrão |
| --- | ---: | ---: | ---: |
| `sub.txt` | 6.532 | 6.532 | 6.532 |
| `num.txt` | 3.174.261 | 3.174.261 | 3.174.261 |
| `pre.txt` | 729.483 | 729.483 | 729.483 |

Também foi olhado o tamanho em disco das pastas baixadas, para estimar a memória do cálculo; a escala foi medida num trimestre sintético, gerado no formato da SEC, não nos arquivos reais. O arquivo do histórico de entregas do EDGAR, com os 8-K, não foi aberto nesta etapa.

## 4. O que vem depois

O cálculo único (`python -m chiocca.eua.estudo --calculo-unico --baixar`), só com a autorização de Roberto, depois do PR e da release do congelamento (meta de 31/01/2027; reserva de 30/04/2027). Antes de ler qualquer dado, ele confere o registro de congelamento e recusa os arquivos da SEC que não foram baixados de novo no dia. Só agregados vão para o resultado versionado; nenhuma lista de companhias por alerta é publicada.
