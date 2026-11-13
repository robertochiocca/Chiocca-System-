# Pré-registro do leitor de documentos (Fase F1)

Registrado em 11/11/2026, antes de qualquer código ou medida do leitor, com as decisões de Roberto da mesma data. As metas, a regra e as definições abaixo não mudam depois de medir. O formato dos casos (seção 6) é o que Roberto usa para escrever os casos guardados.

## 1. O que é medido

O leitor extrativo da Fase F1 (`chiocca/v2/leitor/`). Ele só copia trechos dos documentos, com a página, e não julga nada:

- **partes relacionadas** nas notas explicativas da DFP: as categorias do item 19 e os campos do item 18 do CPC 05 (R1), nas colunas controladora e consolidado quando a nota as tiver;
- a frase **"em condições de mercado"** (item 23), registrada como fato, sem prova;
- menções a **risco sacado ou forfait** nas notas, com a marca de frase negativa ("a Companhia não possui operações de risco sacado" é uma menção negativa);
- o **relatório do auditor** da versão usada da DFP: o tipo de opinião e os trechos de base para ressalva, ênfase, incerteza relevante sobre a continuidade operacional, principais assuntos de auditoria e outros assuntos.

A tabela de transações com partes relacionadas do Formulário de Referência não é extração (é dado estruturado dos dados abertos). Ela entra só na exigência de nomes de pessoa física.

## 2. Metas

As quatro são obrigatórias:

1. **precisão** de pelo menos 0,95;
2. **cobertura** de pelo menos 0,80;
3. **conferência literal** em 100% dos trechos mostrados;
4. **zero nome de pessoa física** na saída. É exigência, não meta: um único nome que apareça reprova o leitor.

## 3. Regra

- Se qualquer uma das quatro falhar nos casos guardados, a seção nova não entra na investigação: fica desligada, e o resultado vai para o relatório como saiu.
- Não se ajusta o leitor contra os casos guardados. Uma nova tentativa exige casos guardados novos.
- A seção só é ligada se as quatro forem atingidas, num commit que registra o resultado, o hash do leitor congelado e o SHA-256 de cada caso guardado.

## 4. Casos

- **Desenvolvimento:** escritos pelo agente de código, em `tests/leitor/casos/desenvolvimento/`, usados para construir e ajustar o leitor. O resultado neles é informativo; não é a medida.
- **Guardados:** escritos por Roberto fora deste ambiente, no formato da seção 6. O agente congela o leitor num commit e informa o hash. Só então recebe os casos guardados, mede uma única vez com o leitor congelado (`python -m chiocca.v2.leitor.avaliar <pasta dos casos>`) e publica o resultado como saiu.

## 5. Definições

- **Unidades devolvidas.** O leitor devolve trechos e classificações. Para contar, os trechos são agrupados pela chave (verificação, rótulo, página e, no risco sacado, a marca de frase negativa): vários trechos com a mesma chave são uma unidade. As classificações são duas: a situação da leitura das notas (`lido` ou `nao_lido`) e o tipo de opinião do auditor.
- **Correspondência.** Uma unidade corresponde a um item do gabarito quando a verificação é a mesma, o rótulo é o mesmo (se o item der rótulo), a página é a mesma (se o item der página) e, no risco sacado, a marca de frase negativa é a mesma. Uma classificação corresponde quando o valor é igual.
- **Precisão** = unidades devolvidas que correspondem a algum item ÷ unidades devolvidas.
- **Cobertura** = itens do gabarito encontrados ÷ itens do gabarito. Um item é encontrado quando alguma unidade corresponde a ele e, se o item der o texto `contem`, algum trecho dessa unidade contém esse texto (sem diferença de espaços) ou foi omitido por nome de pessoa física.
- **Conferência literal.** O texto de cada trecho mostrado, com os espaços normalizados, aparece no texto da página de onde veio (ou do relatório do auditor), também com os espaços normalizados.
- **Nome vazado.** Qualquer texto de `nomes_proibidos` (sem diferença de maiúsculas, acentos e espaços) em qualquer campo da saída do leitor, inclusive nas linhas do Formulário de Referência.
- As contas somam todos os casos (média micro). Os resultados saem com três casas decimais.

## 6. Formato dos casos

Um arquivo JSON por caso, em UTF-8. As notas viram um PDF gerado no próprio teste, página por página, e o leitor lê esse PDF como leria o da CVM (nenhum PDF entra no git).

```json
{
  "id": "g01",
  "descricao": "livre; o leitor não lê este campo",
  "notas": {"paginas": [["linha 1 da página 1", "linha 2"], ["linha 1 da página 2"]], "sem_texto": false},
  "parecer": {"titulo": "Relatório do Auditor Independente - Com Ressalva", "texto": "texto corrido do relatório"},
  "formulario_de_referencia": [{"Parte_Relacionada": "Exemplo Participações S.A.", "Tipo_Pessoa": "PJ",
                                "Relacao_Emissor": "Controladora", "Objeto_Contrato": "Aluguel",
                                "Montante_Envolvido": "1000", "Saldo_Existente": "0", "Garantia_Seguro": "",
                                "Natureza_Razao_Operacao": "", "Taxa_Juros": ""}],
  "esperado": {
    "notas": "lido",
    "parecer_tipo": "com_ressalva",
    "itens": [
      {"verificacao": "partes_relacionadas", "rotulo": "controladora", "pagina": 1, "contem": "trecho esperado"},
      {"verificacao": "campo_cpc05_18", "rotulo": "garantias", "pagina": 1, "contem": "aval"},
      {"verificacao": "condicoes_de_mercado", "pagina": 1, "contem": "condições de mercado"},
      {"verificacao": "risco_sacado", "pagina": 2, "negacao": false, "contem": "risco sacado"},
      {"verificacao": "parecer", "rotulo": "base_para_ressalva", "contem": "não obtivemos"}
    ],
    "nomes_proibidos": ["Nome Fictício Completo"]
  }
}
```

- `notas`, `parecer` e `formulario_de_referencia` são opcionais (sem `notas`, não há PDF; `sem_texto: true` gera páginas sem camada de texto).
- `esperado.notas` é obrigatório quando há `notas`; `esperado.parecer_tipo`, quando há `parecer`.
- `pagina` começa em 1. Itens do parecer não têm página.
- O gabarito lista **todas** as chaves que espera: uma unidade devolvida sem item correspondente conta contra a precisão.
- Rótulos:
  - partes relacionadas (item 19): `controladora`, `controle_conjunto_ou_influencia`, `controladas`, `coligadas`, `joint_ventures`, `pessoal_chave`, `outras_partes`;
  - campos do item 18: `montante`, `saldos`, `termos_e_condicoes`, `garantias`, `provisao_pcld`, `perdas_incobraveis`;
  - seções do parecer: `base_para_ressalva`, `enfase`, `incerteza_continuidade`, `principais_assuntos`, `outros_assuntos`;
  - tipos de opinião: `sem_ressalva`, `com_ressalva`, `adversa`, `abstencao`.

## 7. Omissão de nomes de pessoa física (decisão de 11/11/2026)

Trecho com nome de pessoa física vira "trecho omitido; ver página N do documento". O detector erra para o lado de omitir. Ele marca o trecho quando houver:

- pronome de tratamento (Sr., Sra., Srs., Sras., Dr., Dra.);
- CPF;
- sequência de duas ou mais palavras com inicial maiúscula (podendo ter "de", "da", "do", "das", "dos" ou "e" no meio) que não termina em marca de empresa (S.A., S/A, Ltda., Participações, Holding e outras) e não está na lista de exceções (nomes de companhias do cadastro da CVM e termos contábeis e institucionais).

No Formulário de Referência, o nome da parte só aparece quando a tabela diz pessoa jurídica e o detector não o marca; nos outros casos, "parte relacionada (nome omitido)". Os campos de texto da tabela passam pelo mesmo detector.

## 8. O que fica de fora

Julgamento de qualquer tipo, alerta, nota ou ordenação; prova de omissão (ausência de menção não prova ausência); reconhecimento de texto em imagem (página sem camada de texto é "não lida"); notas de ITR; documentos entregues depois de 31/12/2024 e exercícios de 2024 em diante; transformar tabelas em números; versões antigas do Formulário de Referência; LLM (fora da Fase F).

## 9. Registro

- Data: 11/11/2026.
- Commit: o que introduz este arquivo. O hash é anotado aqui no commit seguinte, sem mudar nenhuma regra acima.
- Hash do commit do registro: `0e3eebc30a8dc26ded921ea0439a06cf34f207f5`.

## 10. Emenda 1: leitor-f1-2 e a regra própria para o assunto do IPE (13/11/2026)

Registrada em 13/11/2026, antes de qualquer código da `leitor-f1-2` ou da regra do assunto, com o pedido de Roberto da mesma data. As seções 1 a 9 continuam valendo para a `leitor-f1-1` e não mudam; esta emenda vale para a nova tentativa. Nada abaixo muda depois de medir.

### 10.1 O que muda no leitor (`leitor-f1-2`)

Os quatro ajustes registrados no plano, e só eles:

1. **Quem controla a Companhia:** "a Companhia é controlada por X" e "a Companhia é controlada em conjunto por X e Y" passam a ser `controladora` e `controle_conjunto_ou_influencia`, e não menção a `controladas` ou a `joint_ventures`.
2. **A própria Companhia:** "a Companhia, na qualidade de controladora, ..." fala da própria Companhia e não conta como `controladora` (item 19 a do CPC 05).
3. **Montante e prazo em frase:** frases como "somou R$ … no exercício" e "as compras totalizaram R$ …" contam como `montante`, e "o contrato vence em 2030" ou "com vencimento em 30 dias" como `termos_e_condicoes`.
4. **Cabeçalho de tabela:** linhas de cabeçalho (anos como "2021 2020 2021 2020", títulos de coluna como "Controladora Consolidado" ou "A receber (a pagar) Receita (despesa)"), inclusive em várias linhas, não saem como trecho.

O detector de nomes de pessoa física (seção 7) não fica mais permissivo na `leitor-f1-2`: qualquer mudança nele só pode omitir mais.

**Casos de desenvolvimento novos**, escritos pelo agente em `tests/leitor/casos/desenvolvimento/` (os 28 atuais continuam), com tabelas no formato real das notas: cabeçalho em várias linhas, colunas de controladora e consolidado, dois exercícios, linhas de total, valores entre parênteses e notas de rodapé (i), (ii). Pelo menos 12 casos novos, com pelo menos 8 com tabela.

### 10.2 Metas do leitor e regra

- As mesmas quatro da seção 2, com as definições da seção 5: precisão de pelo menos 0,95; cobertura de pelo menos 0,80; conferência literal em 100% dos trechos mostrados; zero nome de pessoa física (exigência).
- Se a `leitor-f1-2` atingir as quatro nos casos guardados novos, ela substitui a `leitor-f1-1` na seção de trechos, num commit que registra o resultado, o hash do leitor congelado e o SHA-256 de cada caso. Se falhar em qualquer uma, a seção continua com a `leitor-f1-1`, já aprovada, e o resultado vai para o relatório como saiu.
- **Medida informativa do cabeçalho:** cada caso pode trazer `esperado.trechos_que_nao_devem_aparecer` (por exemplo, as linhas de cabeçalho da tabela). Conta-se quantos desses textos saem como trecho. É informativo: não muda a precisão, a cobertura nem a regra.
- **Comparação informativa:** a `leitor-f1-1` também é medida nos casos guardados novos, só para comparar.

### 10.3 Regra própria para o assunto do IPE

Uma regra nova, só para o assunto dos fatos relevantes e comunicados (seção 9 dos contratos), congelada no mesmo commit da `leitor-f1-2` e medida nos mesmos casos guardados, em arquivos próprios (10.4). Ela pode usar o detector de nomes do leitor e regras próprias para assunto (por exemplo, para siglas, nomes de companhias fora do cadastro, títulos em inglês e assunto em maiúsculas). Duas metas:

1. **Zero nome de pessoa (exigência):** nenhum assunto marcado `omitido` no gabarito aparece, e nenhum texto de `nomes_proibidos` (sem diferença de maiúsculas, acentos e espaços) aparece em assunto mostrado. Um único caso reprova a regra.
2. **Omissão indevida de no máximo 0,20:** assuntos marcados `mostrado` no gabarito que a regra omite ÷ assuntos marcados `mostrado`. Proposta de 0,20 (pelo menos 80% dos assuntos sem nome aparecem): as regras conservadoras de hoje omitem 60,2% de todos os assuntos de 2010 a 2024, e na amostra de 12/11/2026 quase nenhum dos omitidos pelas regras novas tinha nome.

- Se a regra atingir as duas, substitui as regras conservadoras de hoje (detector, maiúsculas e palavra maiúscula fora do começo), num commit que registra o resultado. Se falhar em qualquer uma, ficam as regras de hoje.
- O assunto vazio continua com o aviso e não entra nas contas.
- **Comparação informativa:** as regras de hoje também são medidas nos mesmos casos de assunto.
- A regra do assunto e a `leitor-f1-2` são decididas separadamente: cada uma passa ou falha nas suas metas.

### 10.4 Formato dos casos de assunto

Um arquivo JSON por conjunto, em UTF-8, com nome começando por `assuntos_` (por exemplo, `assuntos_a01.json`), na mesma pasta dos casos do leitor:

```json
{
  "id": "a01",
  "descricao": "livre; a regra não lê este campo",
  "assuntos": [
    {"assunto": "Renúncia do Diretor Fulano Exemplar de Tal", "esperado": "omitido"},
    {"assunto": "Renúncia do diretor Exemplar", "esperado": "omitido"},
    {"assunto": "AUMENTO DE CAPITAL APROVADO", "esperado": "mostrado"},
    {"assunto": "Petrobras sobre venda da refinaria RLAM", "esperado": "mostrado"},
    {"assunto": "Resultados do 3T23 - Versão em inglês", "esperado": "mostrado", "categoria": "comunicado_ao_mercado"}
  ],
  "nomes_proibidos": ["Fulano Exemplar de Tal", "Exemplar"]
}
```

- `esperado` é `omitido` (o assunto tem nome de pessoa) ou `mostrado` (não tem). `categoria` é opcional (`fato_relevante` ou `comunicado_ao_mercado`); a regra pode não usá-la.
- `nomes_proibidos` lista cada nome de pessoa dos assuntos `omitido` do arquivo, inteiro e nas partes que identificam a pessoa (um sobrenome sozinho, por exemplo).
- Os nomes de pessoa são inventados: nenhum nome real de pessoa física entra no repositório. Nomes de companhias, lugares, siglas e produtos podem ser reais.
- Sugestão para os guardados: pelo menos 300 assuntos, com pelo menos 60 com nome, em formas variadas (nome completo, sobrenome sozinho, todo em maiúsculas, depois de dois-pontos, com pronome de tratamento, com iniciais, em assunto em inglês, nome que coincide com palavra comum ou com nome de companhia), e pelo menos 200 sem nome, parecidos com os reais (iniciais maiúsculas, siglas, companhias dentro e fora do cadastro, lugares, meses como "Maio/2017", produtos, títulos em inglês).
- Casos de desenvolvimento de assunto, escritos pelo agente: pelo menos 150 assuntos, no mesmo formato.

### 10.5 Casos e procedimento

1. Esta emenda é registrada antes de qualquer código da `leitor-f1-2` e da regra do assunto.
2. O agente desenvolve com os casos de desenvolvimento (10.1 e 10.4). Os 20 casos guardados da `leitor-f1-1` agora são públicos: a medida neles é só informativa e não decide nada.
3. O agente congela a `leitor-f1-2` e a regra do assunto num commit, com o SHA-256 de cada arquivo num registro próprio e um teste que falha se algum mudar, e informa o hash.
4. Só então Roberto escreve os casos guardados novos (casos do leitor no formato da seção 6, com o campo opcional de 10.2, e casos de assunto no formato de 10.4) e os entrega. Sugestão: pelo menos 20 casos do leitor, com pelo menos 8 com tabela no formato real.
5. A medida é feita uma única vez, com o código congelado (`python -m chiocca.v2.leitor.avaliar <pasta dos casos>`, que passa a ler também os arquivos `assuntos_`), e publicada como saiu. Não se ajusta nada contra os casos guardados; uma nova tentativa exige casos guardados novos.
6. Resultados com três casas decimais, somando todos os casos (média micro).

### 10.6 Registro da emenda

- Data: 13/11/2026.
- Commit: o que introduz esta seção. O hash é anotado aqui no commit seguinte, sem mudar nenhuma regra acima.
- Hash do commit da emenda: `2fcdbc18752b693510c76cda12acd4f53af055ee`.

### 10.7 Decisões de Roberto sobre a emenda (13/11/2026, antes de qualquer código)

1. Os três acréscimos informativos de 10.2 e 10.3 ficam.
2. **Desenvolvimento ao lado, não por cima.** Os arquivos congelados da `leitor-f1-1` não mudam: a `leitor-f1-2` é feita ao lado (um módulo próprio ou uma versão selecionável), e o teste de hashes da `leitor-f1-1` continua valendo. Até a medida aprovar a `leitor-f1-2`, a seção, os exemplos e a demonstração continuam com a `leitor-f1-1`. O mesmo vale para o assunto: até a regra nova ser aprovada, ficam as regras conservadoras de hoje.
3. **Critério de troca da `leitor-f1-2`.** Além das quatro metas, a `leitor-f1-2` só substitui a `leitor-f1-1` se, nos mesmos casos guardados novos: (a) a precisão da `leitor-f1-2` for pelo menos a da `leitor-f1-1`; (b) o número de textos de `trechos_que_nao_devem_aparecer` que saem como trecho na `leitor-f1-2` não for maior que na `leitor-f1-1`. Senão, fica a `leitor-f1-1`, e o resultado vai para o relatório como saiu.
4. **Definição.** Um texto de `trechos_que_nao_devem_aparecer` "sai como trecho" quando está contido, sem diferença de espaços, no texto de algum trecho mostrado.
5. **Detector de nomes.** Um teste roda o detector da `leitor-f1-2` e o da `leitor-f1-1` sobre todos os casos públicos (os de desenvolvimento e os 20 guardados antigos) e sobre os trechos reais dos 96 documentos da demonstração. O teste falha se algum trecho omitido pela `leitor-f1-1` deixar de ser omitido.
6. **Auditoria em dados reais da regra do assunto, antes de ligar.** Se a regra atingir as duas metas nos casos guardados, sorteiam-se (semente 20261113) 400 assuntos de 2010 a 2024 que a regra nova mostra e as regras de hoje omitem. O agente lê os 400. Se algum tiver nome de pessoa física, a regra não entra e ficam as regras de hoje. As contagens são relatadas sem escrever os nomes.
7. **Comparação da `leitor-f1-1` nos casos novos.** O avaliador antigo rejeita o campo novo de `esperado`. A `leitor-f1-1` é medida com o avaliador novo, que chama o leitor da `leitor-f1-1` sem mudança, e o relatório diz como foi feito.

- Hash do commit destas decisões: `c7232b6e751bb0e6e5675e606873869a7be0583c` (anotado no commit seguinte, sem mudar nenhuma regra acima).
