# Como reproduzir

Os comandos completos e a estrutura do repositório, que saíram do README em 21/11/2026. A instalação e os testes estão no [README](../README.md), seção "Como rodar".

## Como funciona

```
Dados abertos da CVM (DFP, todas as versões, incluindo empresas canceladas)
        ↓
Base "como era na época": a versão pública em cada data de corte
        ↓
Sinais do catálogo: M-score de Beneish e sinais adaptados ao Brasil
        ↓
Regras de alerta fixadas no pré-registro, antes de olhar os dados
        ↓
Avaliação: casos reais acertados, alarmes falsos, comparação com uma regra simples
        ↓
Ficha de alerta: qual sinal disparou, com qual número e de qual conta da DFP
```

## Dependências

O estudo 1 foi gerado com pandas 3.0.5 e numpy 2.5.3. Todas as dependências, inclusive as transitivas, estão travadas em [`requirements-lock.txt`](../requirements-lock.txt) (gerado por `scripts/gerar_lock.py`), e o CI instala a partir dele. O projeto exige Python 3.12 ou mais, porque o numpy 2.5.3 não tem distribuição para Python 3.11; o CI roda em 3.12 e 3.13. A API (Fase D) usa FastAPI, Pydantic e uvicorn, fixados no `pyproject.toml` como as demais dependências; os testes da API usam o httpx.

## Comandos

> **Aviso.** Fora dos scripts dos estudos, a montagem da base é sempre chamada com os anos de 2010 a 2023 (`python -m chiocca.montar_base 2010 2023`). Sem os anos, o script usa o padrão de 2010 a 2025 e processa exercícios lacrados; o `chiocca/montar_base.py` é congelado e não muda, e um teste confere que nenhum código não congelado nem comando documentado o chama sem os anos.

```
python -m pip install -r requirements-lock.txt && python -m pip install -e . --no-deps
python -m chiocca.dados baixar        # baixa DFP, FCA e cadastro da CVM para data/brutos/ e grava o manifesto
python -m chiocca.dados verificar     # confere os arquivos contra os hashes do manifesto
python -m chiocca.montar_base 2010 2023   # monta a base e lista as versões da época que precisam do ENET
python -m chiocca.enet data/cache/enet/pendentes.txt   # baixa essas versões (só consolidado)
python -m chiocca.montar_base 2010 2023   # monta de novo, agora com as versões do ENET
python -m chiocca.relatorio_base      # gera docs/base.md e docs/en/base.md
python -m chiocca.sinais_amostra      # sinais e alertas de todas as empresa-anos, em resultados/ (fora do git)
python -m chiocca.emenda5             # secundária da emenda 5, em resultados/
python -m chiocca.americanas          # duas leituras da Americanas, em resultados/
python -m chiocca.relatorio_resultados  # gera os resultados e o resumo, em PT e EN
python -m chiocca.ficha 20990 2021 pt  # ficha de alerta de uma empresa-ano
python -m chiocca.v2.relatorio_conferencias  # conferências de qualidade na base, até o lacre
python -m chiocca.v2.armazem          # armazém temporal em data/armazem (fora do git)
python -m chiocca.v2.buscar_enet 2024-12-31   # busca no ENET as versões que a data precisa (comando separado)
python -m chiocca.v2.invariante       # invariante do estudo 1 e corte na data máxima
python -m chiocca.dados baixar-ipe    # índices do IPE de 2010 a 2024 (fatos relevantes e comunicados; só metadados)
python -m chiocca.v2.monitor verificar   # monitor da CVM: novidades de DFP, ITR e IPE numa fila de revisão (só lista)
python -m chiocca.v2.investigacao 20990 2021 2022-04-30 pt   # investigação em JSON (com --pdf, em PDF)
python -m chiocca.v2.exemplos         # exemplos de referência em docs/exemplos/
python -m chiocca.v2.ficha_do_motor   # ficha do motor (docs/ficha-do-motor.md e docs/en/engine-card.md)
python -m chiocca.v2.api 8000         # API em http://127.0.0.1:8000/api/v1 (documentação em /api/v1/docs)
CHIOCCA_MODO_DEMONSTRACAO=1 python -m chiocca.v2.api 8000   # a mesma API no modo demonstração (só os casos do gabarito)
cd web && npm ci && npm run build && npm start   # interface em http://localhost:3000 (fala com a API em :8000)
python -m chiocca.v2.demonstracao_estatica --processos 4   # demonstração estática em web/public/demo/ (JSON e PDF, fora do git)
cd web && npm run build:estatico && npm run test:tela   # site estático em web/out/, sem API, e o teste de tela
cd web && npm run varrer:demo   # antes de publicar: todas as investigações da demonstração no navegador, PT e EN
make demo                       # na raiz: a demonstração no computador, com os exemplos de docs/exemplos/ e sem baixar nada (porta 3000; outra: make demo PORTA=8080)
python -m chiocca.v2.gh_pages PASTA_DO_GH_PAGES --varredura varredura.json   # monta o branch gh-pages (veja o módulo)
python -m pytest                      # testes sem rede
```

## Estrutura

```
catalogo_sinais.yaml      sinais: fórmula, contas da DFP, referências, fase (PT e EN)
glossario_pt_en.yaml      termos contábeis e do estudo, PT ↔ EN
data/gabarito_casos.csv   casos reais com datas, fontes, notas (PT e EN) e se são acertáveis
data/casos_em_observacao.csv  casos sem decisão final ou de fronteira (emenda 8)
data/manifesto_brutos.csv  URL, tamanho e SHA256 de cada arquivo baixado da CVM
chiocca/                  código: download, base "como era na época", sinais e avaliação
tests/                    testes sem rede, inclusive o teste de referência
docs/reconhecimento.md    reconhecimento dos dados da CVM (Fase 0) e revisão do gabarito
docs/base.md              números da base "como era na época", gerados por script
docs/resultados.md        sinais, alertas e métricas do pré-registro, gerados por script
docs/resumo.md            resumo de uma página, gerado por script
data/cdi_sgs4389.csv      CDI diário do Banco Central (SGS 4389), snapshot versionado
data/exemplo_resolvido.json  empresa fictícia com valores esperados (teste de referência)
docs/pre-registro.md      decisões do estudo, assinadas antes dos dados
PROMPT.md                 especificação de construção para o agente de código
```
