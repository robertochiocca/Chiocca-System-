# Estudo 2 · Parte 1 do gabarito · Registro da busca

Escrito por Roberto Chiocca, com o Claude (claude.ai), fora do ambiente do agente, sem a lista de alertas e sem rodar o código, como manda a seção 5 do pré-registro do estudo 2 (commit `79c9214714696693235ce372b82cdaa1ad73c38e`). As regras de fronteira e de qualificação usadas aqui são as da emenda 1.

## Resultado

**Nenhum caso qualificado.** Até o congelamento, nenhum caso cumpre a seção 5 com período afetado que inclua 2024 ou 2025. O arquivo `data/gabarito_estudo_2_parte_1.csv` tem só o cabeçalho. Isso está dentro do esperado: o pré-registro estima cerca de 1,6 caso até 31/12/2029, e processos sancionadores sobre o conteúdo das demonstrações costumam levar anos para serem instaurados.

## Como a busca foi feita

- **Quando:** de 15/11/2026 até o congelamento.
- **Fontes da seção 5:**
  1. processos sancionadores e decisões do Colegiado da CVM;
  2. fatos relevantes e comunicados das companhias;
  3. a lista da CVM de determinações de refazimento e republicação (pastas 2025 e 2026), conferida por Roberto no navegador;
  4. para financeiras, notícias com fonte sobre o Banco Central.
- **Termos buscados:** refazimento, republicação, reapresentação, correção de erro, CPC 23, fraude contábil, inconsistências contábeis, comitê independente, processo sancionador e demonstrações financeiras de 2024 e 2025.
- **Limite:** a busca não varreu um por um todos os fatos relevantes de 2025 e 2026. Um caso que tenha escapado entra na parte 2, marcado como "não encontrado na parte 1" (emenda 1).

## Considerados e fora

| Companhia | O que há | Por que fica fora |
| --- | --- | --- |
| Marisa Lojas S.A. | Ofício nº 242/2025/CVM/SEP/GEA-5, de 02/10/2025: refazimento das DF de 2022 a 2024 e dos ITR de 1T23 a 2T25 (provisões tributárias de controlada, ICPC 22). Em 30/12/2025, o Colegiado deu provimento ao recurso, por maioria, e afastou a determinação (Reg. 3423/25). | Determinação revertida pelo Colegiado (emenda 1, item 3). |
| Grupo Mateus S.A. | 3º ITR/25, de 14/11/2025: reapresentação de 31/12/2024, 31/12/2023 e 9M24 (estoques e custo das mercadorias, cerca de R$ 1,1 bi no total, cerca de R$ 94 mi em 2024). Comunicados de 21/11/2025 e 27/11/2025 respondem aos Ofícios nº 238 e 239/2025/CVM/SEP/GEA-2 e falam em "revisão da política contábil", sem fato relevante. | Sem fato relevante e sem admissão de erro; sem processo e sem determinação da CVM (emenda 1, item 4). Pode entrar na parte 2. |
| Aegea Saneamento e Participações S.A. | Fato relevante de 30/03/2026: adia as DF de 2025 por "ajuste de práticas contábeis e reavaliação de estimativas" e anuncia a reapresentação das DF de 2024. As DF de 2025 saíram em 10 e 11/04/2026, com 2024 reapresentado (PL consolidado de R$ 11,4 bi para R$ 6,39 bi). A companhia diz que não há indício de fraude. | O fato relevante não admite erro nem fraude (emenda 1, item 4). Pode entrar na parte 2. |
| BRB – Banco de Brasília S.A. (financeira) | Carteiras compradas do Banco Master apontadas sem lastro em 18/11/2025. A imprensa noticiou, em 23/01/2026, uma determinação do Banco Central de provisão de R$ 2,6 bi. Em comunicado de 26/01/2026, o BRB a trata como "suposta". Fato relevante de 31/03/2026: as DF de 2025 não saem no prazo. Há também processo da CVM de 2025 sobre a convocação da assembleia e o envio das DF de 2024. | Não há documento público do Banco Central nem admissão da companhia com os exercícios. O processo da CVM trata de atraso, que não entra (emenda 7 do estudo 1). Pode entrar na parte 2. A DF de 2025 não foi entregue até o corte de 30/04/2026. |
| Ambipar Participações e Empreendimentos S.A. | Processo da CVM contra dois ex-diretores de relações com investidores por não divulgar a troca de auditor. A CVM também apura as cotações. O ITR do 3T25 e as DF de 2025 foram adiados. | Divulgação e governança, sem documento que aponte distorção nas demonstrações de 2024 ou 2025. Pode entrar na parte 2. |
| REAG Capital Holding S.A. | PAS CVM 19957.011231/2025-34, com termo de acusação de 08/09/2025: DF de 2024 e ITR de 1T25 e 2T25 não elaborados no prazo. | Atraso (emenda 7 do estudo 1). |
| Cia. Tecidos Norte de Minas – Coteminas; AMMO Varejo S.A.; TBM – Têxtil Bezerra de Menezes S.A. | PAS 19957.001045/2025-97, 19957.001044/2025-42 e 19957.011123/2025-61: entrega atrasada ou não entrega de DF e ITR. | Atraso (emenda 7 do estudo 1). |
| Ybyrá Capital S.A. | Ofício nº 134/2024/CVM/SEP/GEA-5, de 13/05/2024: refazimento da DF de 2023. | Período afetado fora de 2024 e 2025. |

## Fontes dos casos considerados

- Marisa: https://www.gov.br/cvm/pt-br/assuntos/regulados/consultas-por-participante/companhias/determinacao-de-refazimento-republicacao-de-dfs-e-itrs/2025/marisa-lojas-s-a/@@download/file ; https://conteudo.cvm.gov.br/decisoes/2025/20251230_R1/20251230_D3423.html
- Grupo Mateus: https://api.mziq.com/mzfilemanager/v2/d/8ea287f8-ae0a-4b88-b20b-80c1f1b86a1e/77674adc-0532-7710-bb30-3bdcbd77a736?origin=1 ; https://api.mziq.com/mzfilemanager/v2/d/8ea287f8-ae0a-4b88-b20b-80c1f1b86a1e/238cfebe-ba86-3d87-ab6a-a1f626e2ab0e?origin=1
- Aegea: https://www.rededivulgacao.com.br/2026/03/30/aegea-fato-relevante-postergacao-divulgacao-dfs/ ; https://dinheiroportal.com/ultimas-noticias/com-atraso-aegea-divulga-balanco-de-2025-faz-ajuste-de-2024-e-corta-r-5-bilhoes-no-patrimonio/
- BRB: https://ri.brb.com.br/upload/files/4027_Comunicado-ao-Mercado-Esclarecimentos-Jornal-Fol_260126_202856.pdf ; https://www.infomoney.com.br/mercados/bc-manda-brb-provisionar-r-26-bi-para-cobrir-fraude-do-master-diz-jornal/ ; https://agenciabrasil.ebc.com.br/economia/noticia/2026-03/brb-confirma-que-nao-divulgara-balanco-de-2025-no-prazo
- Ambipar: https://timesbrasil.com.br/empresas-e-negocios/por-que-a-cvm-decidiu-processar-ex-executivos-da-ambipar/ ; https://investidor10.com.br/noticias/ambipar-ambp3-adia-balanco-do-3t25-em-meio-a-rj-e-transicao-de-diretoria-116700/
- REAG: PAS CVM 19957.011231/2025-34, voto publicado nas notícias da CVM em 29/09/2026 (o endereço do arquivo traz nome de pessoa física e por isso não é reproduzido aqui).
- Coteminas, AMMO e TBM: https://www.gov.br/cvm/pt-br/assuntos/noticias/anexos/2026/20250511-pas-cvm-19957-001045-2025-97-relatorio-da-area-tecnica.pdf ; https://www.gov.br/cvm/pt-br/assuntos/noticias/anexos/2026/20260713-pas-cvm-19957-001044-2025-42-relatorio-area-tecnica.pdf ; https://www.gov.br/cvm/pt-br/assuntos/noticias/anexos/2026/20260601-pas-cvm-19957-011123-2025-61-relatorio-area-tecnica.pdf
- Ybyrá: https://www.gov.br/cvm/pt-br/assuntos/regulados/consultas-por-participante/companhias/determinacao-de-refazimento-republicacao-de-dfs-e-itrs/2024/ybyra-capital-s-a

## Podem entrar na parte 2

Grupo Mateus, Aegea, BRB e Ambipar. Estar nesta lista não é acusação nem indica alerta: só registra fatos públicos que, no congelamento, não cumprem a seção 5. Nenhum alerta delas é descrito ou publicado por estarem aqui (emenda 1, item 5). Se um documento que qualifica o caso sair depois do congelamento, o caso entra na parte 2, e a `data_publica` continua sendo a primeira data pública documentada (emenda 1, item 1). Nos quatro casos, essa data é anterior a 30/04/2026, então só a DFP de 2024 pode contar (seção 4.1).
