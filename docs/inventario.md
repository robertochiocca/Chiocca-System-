# Inventário do código dos outros projetos (Fase A do v2)

Inspeção feita em 07/11/2026 sobre os zips anexados, sem instalar nem executar nenhum dos projetos. Os três são do Roberto Chiocca, com licença MIT. Os commits vêm do comentário de cada zip (o GitHub grava ali o commit do arquivo):

| Projeto | Commit inspecionado | SHA256 do zip |
| --- | --- | --- |
| Carchuna | `a3f30ac284eb01245b022b7655bb16c4b8474cc7` | `67b76d50b9fe8dbee5c8f62600e7cab7f7bda61111263e31c39b0e8ec9bc35ee` |
| Calahonda | `47ef323440946a2552bea1ded0da59bd96e6f1a8` | `54425da6af99d21d5247ced946a5c36bcd09279d3c173ac921da1def8496afcf` |
| DireitoAberto | `102e3e2d9d70e87249d8df9215737e2d98b6358d` | `55c3799c1212a2b33834c78ed5bdf7d379a8c3d51b755733c64a82ec19269527` |

Nenhum arquivo foi trazido nesta fase. Cada um entra na fase em que for usado, com o cabeçalho de origem e o registro em [`docs/origem-do-codigo.md`](origem-do-codigo.md).

Legenda da decisão: **trazer** (o arquivo vem quase como está), **adaptar** (vem a estrutura, e o conteúdo de domínio é reescrito para dados da CVM), **adiar** (fica para o estudo 2), **descartar** (não entra).

## Carchuna

O núcleo é Python puro, sem dependências; matplotlib, pandas, FastAPI e Streamlit são extras. Quase tudo gira em torno da decomposição da margem de lojistas (`margem.py`), então quase nada vem como está: o que vale são os contratos e os princípios.

| Módulo (linhas) | O que faz | Testes | Decisão e motivo | O que muda | Fase |
| --- | --- | --- | --- | --- | --- |
| `linhagem.py` (206) | Ficha "como cheguei a este número": origem, colunas, transformações, fórmula com os valores do caso, premissas, limitações, fonte, confiança e quando foi calculado. Não recalcula nada | `test_linhagem.py` | **Adaptar.** O formato da ficha é exatamente o que o produto precisa | As colunas da planilha viram contas da DFP (documento, versão, coluna, código); o montador passa a ler a saída do motor v1 | B |
| `validade.py` (216) | Resultado com três estados (ok, indefinido, implausível), com invariantes: ok exige valor; indefinido não tem valor e exige motivo; implausível tem valor e motivo. Também `variacao_percentual`, que recusa base negativa ou zero | `test_validade_margem.py` | **Trazer** a classe e `variacao_percentual`. **Descartar** os limiares de margem, que são do domínio do lojista | O "não calculável" do motor v1 vira "indefinido" com o mesmo motivo. "Implausível" vem das conferências da Fase B e não muda nenhum sinal | B |
| `confianca.py` (153) | Nota de 0 a 100 com rubrica fixa (evidência, histórico, amostra, completude) e frase "os dados mostram" contra "hipótese" | `test_confianca.py` | **Adaptar a estrutura, descartar a pontuação.** Os pontos são do domínio de vendas e não foram validados; o plano de integração pede para não copiar pontuação arbitrária | Componentes com nome e motivo, avaliados por regras explícitas (fonte, completude, consistência, atualidade, método) e nível categórico, sem nota somada (ver contratos) | B |
| `diagnostico.py` (393) | Padrão `RegraDeteccao` → `Achado`, orquestrado por `MotorDiagnostico`; as regras são tributárias e de marketplace | `test_diagnostico.py` | **Adaptar o padrão. Descartar as regras** e a dependência do RAG jurídico | Cada sinal do motor v1 e cada indicador de contexto vira uma regra que devolve `Achado` no contrato do Chiocca | C |
| `insights.py` (731) | `detectar_fora_do_padrao`: z-score contra o histórico, com veto da cerca de IQR (quartis ± 1,5×IQR) e regra para histórico constante; o resto são análises de margem mensal | `test_insights.py` | **Trazer a detecção, descartar as análises** de margem | Séries anuais em vez de mensais: o mínimo de exercícios e a cerca são parâmetros de exibição, não regras do motor | C |
| Conferências de qualidade (`margem.py`: identidade estrutural, `reconciliar`, `conferir_plausibilidade`) | Separa identidade (que fecha por construção) de reconciliação por outro caminho e de plausibilidade | `test_conferencia_na_fronteira.py`, `test_fechamento_percentual.py` | **Adaptar o princípio**, porque as implementações são da margem do lojista | Conferências próprias da CVM: balanço que não fecha, subtotais da DRE, DFC que não reconcilia com a variação do caixa, valores implausíveis | B |
| `relatorio.py` (231) | PDF de 3 páginas com matplotlib | `test_relatorio.py` | **Descartar a implementação.** O PDF do produto usa o gerador sem dependência do DireitoAberto; o layout serve de referência | — | C |
| `margem.py`, `cenarios.py`, `rag/`, `tipos.py`, `app.py`, `api/` | Margem, Simples Nacional, cenários, RAG jurídico, ingestão de planilhas, Streamlit e API própria | — | **Descartar**: regras tributárias e de PME, como o prompt manda; a API de referência é a do DireitoAberto | — | — |

## Calahonda

O núcleo depende de numpy, pandas e scipy; yfinance, matplotlib e Streamlit são extras.

| Módulo (linhas) | O que faz | Testes | Decisão e motivo | O que muda | Fase |
| --- | --- | --- | --- | --- | --- |
| `backtest.py` (110) | Teste de Kupiec (proporção de falhas, χ² com 1 grau de liberdade) para violações de VaR | `test_stress_backtest.py` | **Adaptar** para teste binomial exato de acertos contra a taxa de alerta, sem scipy (só `math.comb`). Só entra com a sua autorização: é uma estatística nova sobre o estudo 1, que não foi pré-registrada (ver pergunta em [`docs/plano-v2.md`](plano-v2.md)) | Saída rotulada como descritiva, calculada depois do estudo | C, se autorizado |
| `report.py` (211) | PDF de 3 páginas da carteira, com matplotlib | `test_report.py` | **Descartar**, pelo mesmo motivo do relatório da Carchuna | — | — |
| `data.py` (208), `metrics.py` (185), `ratios.py` (179) | Preços da B3 via yfinance com reserva sintética, retorno, volatilidade, drawdown, Sortino, Calmar e outros | `test_data_benchmark.py`, `test_metrics.py`, `test_ratios.py` | **Adiar** para o teste de retorno do estudo 2, como o prompt manda | — | Estudo 2 |
| `var.py`, `stress.py` | VaR e stress de carteira | `test_var.py` | **Descartar como detector**, como o prompt manda | — | — |

## DireitoAberto

O backend usa FastAPI, SQLAlchemy, pypdf e anthropic; o web usa Next.js 15 e React 19, sem biblioteca de componentes. É a referência para evidência, verificação, monitor, API e interface.

| Módulo (linhas) | O que faz | Testes | Decisão e motivo | O que muda | Fase |
| --- | --- | --- | --- | --- | --- |
| `corpus/proveniencia.py` (526) | Natureza de cada texto (literal, consolidado, resumo explicativo, interpretação, não conferido), hash e cobertura por sequências de 8 palavras | `test_proveniencia.py` | **Adaptar a taxonomia**, que separa fato, resumo e inferência. **Descartar** o resto, ligado ao corpus jurídico | Natureza de cada frase da investigação: número calculado, trecho literal conferido, resumo, inferência ou hipótese | C e F |
| `monitor/registro.py` (290) | Registro de versões com fila de revisão: linha de base, pendente, aceita, rejeitada e superada; snapshots com hash, diário de decisões, trava de arquivo, contador de revisão e reversão sem apagar histórico | `test_monitor.py`, `test_monitor_operacao.py` | **Trazer**: é genérico e já resolve concorrência e reversão | Fontes da CVM (índices de DFP, ITR e IPE) em vez de páginas do Planalto | F |
| `monitor/comparar.py` (293), `eventos.py` (63) | Comparação de normas artigo por artigo e tradução em eventos jurídicos | `test_monitor.py` | **Descartar a lógica**, que é jurídica. **Adaptar a ideia** de classificação conservadora | Classificação da CVM: DFP nova, nova versão (reapresentação), ITR novo, fato relevante novo, coleta suspeita | F |
| `monitor/coleta.py` (209) | Coleta educada: novas tentativas com espera, `Retry-After`, sem insistir em 403 e 404, hash sobre o texto | `test_monitor_operacao.py` | **Adaptar** para os downloads da CVM, junto com `chiocca/dados.py` | Endereços e formatos da CVM | F |
| `leitor/verificacao.py` (79) | Conferência literal de citação contra a página, tolerando só espaços, quebras de linha e hifenização; vale também para texto de LLM | `test_leitor.py` | **Trazer** | O modelo de documento do Chiocca (páginas de PDF e linhas de CSV da CVM) | F |
| `leitor/extracao.py` (531), `documentos.py` | Extração de texto de PDF com guardas de tamanho e tempo (pypdf) | `test_leitor.py`, `test_documentos.py` | **Adaptar o mínimo** na Fase F; a dependência (pypdf ou `pdftotext`) é decisão daquela fase | Fatos relevantes e notas explicativas | F |
| `leitor/pdf_simples.py` (128) | Gerador de PDF sem dependência: Helvetica, texto em Windows-1252, determinístico | `test_leitor_conjunto.py` | **Trazer** para o PDF da investigação e para o conjunto adversarial | Transliterar os caracteres fora do Windows-1252 (por exemplo, "−", "≥" e "÷") | C e F |
| `leitor/avaliacao.py` (222), `conjunto_adversarial.py` (433) | Avaliação com gabarito declarativo escrito à mão e conferência implícita de toda citação; documentos fictícios que reproduzem falhas conhecidas | `test_leitor_conjunto.py` | **Adaptar o mecanismo**; os documentos e gabaritos são novos, com fatos relevantes e notas fictícios | Verificações do Chiocca: partes relacionadas, risco sacado ou forfait, troca de auditor, ressalvas e garantias | F |
| `validacao.py` (208) | Estado de validação de cada resposta por verificações determinísticas, nenhuma dada pelo próprio LLM | `test_validacao.py` | **Adaptar o padrão**; as verificações são jurídicas | Alimenta a confiança e o estado das frases geradas | B e F |
| `main.py` (803) | API FastAPI em `/api/v1`, limite de corpo, limitação de requisições, autenticação, banco e LLM | `test_api.py` e outros | **Adaptar a estrutura** (roteador `/api/v1`, `/saude`, limite de corpo, tratamento de erro). **Descartar** autenticação, banco, feedback e rotas jurídicas | Rotas do Chiocca, com Pydantic nos contratos | D |
| `web/` (Next.js 15, React 19, TypeScript) | App router, componentes, `lib/api.ts`, CSS próprio e `vercel.json` | `test_frontend_estatico.py` | **Adaptar a estrutura e os componentes** que servirem | Páginas do Chiocca, PT e EN, modo escuro e celular | E |
| `.github/workflows/ci.yml` | Lint, tipos, testes em duas versões do Python, build do web e auditoria de dependências | — | **Adaptar** | Comandos do Chiocca (ruff, black, mypy, pytest) | B |
| Corpus jurídico, jurisprudência, embeddings, busca semântica, autenticação, feedback, `render.yaml` | — | — | **Descartar** nesta etapa. O deploy é decisão da Fase E | — | — |

## Fatos dos dados da CVM que pesam nos contratos

Conferidos só na estrutura dos arquivos já baixados (sem valores, sem sinais e sem exercícios acima do lacre):

- O ZIP da DFP traz `parecer` (tipo e texto do relatório do auditor) em todos os anos conferidos, e `composicao_capital` (quantidade de ações) só nos anos recentes: está em 2023 e falta em 2010 e 2015.
- O FCA traz `auditor` (histórico de auditores, com datas de início e fim) e `valor_mobiliario` (códigos de negociação na B3, com datas). Servem para a troca de auditor e para buscar empresa por código de negociação.
- No plano não financeiro, 2.03.04 "Reservas de Lucros" e 2.03.05 "Lucros/Prejuízos Acumulados" são contas fixas.
