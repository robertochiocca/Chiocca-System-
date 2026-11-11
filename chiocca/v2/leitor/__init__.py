"""Leitor extrativo de documentos da CVM (Fase F1, decisões de Roberto de 11/11/2026).

Copia trechos das notas explicativas e do relatório do auditor da DFP, com a página, e lê a tabela de transações com
partes relacionadas do Formulário de Referência. Não julga nada, não gera alerta, nota nem ordenação. Cada trecho
mostrado passa pela conferência literal (aparece no texto da página de onde veio); trecho com nome de pessoa física
vira "trecho omitido; ver página N do documento". A medida do leitor segue o pré-registro de
docs/pre-registro-leitor.md: a seção só entra na investigação se as quatro metas forem atingidas nos casos guardados.

Módulos: `texto` (texto de cada página do PDF e conferência literal), `nomes` (detector de nome de pessoa física),
`partes_relacionadas`, `risco_sacado`, `parecer` (relatório do auditor), `formulario` (tabela do Formulário de
Referência), `ler` (junta tudo), `enet_documentos` (acesso ao ENET), `secao` (a seção da investigação), `avaliacao`
(conjunto adversarial) e os comandos `avaliar` e `baixar`.
"""

VERSAO = "leitor-f1-1"
