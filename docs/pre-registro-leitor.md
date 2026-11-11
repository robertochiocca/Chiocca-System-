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
