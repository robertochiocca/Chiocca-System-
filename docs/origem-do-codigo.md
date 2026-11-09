# Origem do código trazido de outros projetos

Todo arquivo trazido da Carchuna, da Calahonda ou do DireitoAberto (todos de Roberto Chiocca, licença MIT) entra nesta tabela e leva no topo o projeto de origem, o caminho, o commit e a frase "adaptado para o Chiocca System". Nenhum projeto é instalado como pacote.

Commits inspecionados na Fase A (detalhes em [`docs/inventario.md`](inventario.md)):

- Carchuna: `a3f30ac284eb01245b022b7655bb16c4b8474cc7`
- Calahonda: `47ef323440946a2552bea1ded0da59bd96e6f1a8`
- DireitoAberto: `102e3e2d9d70e87249d8df9215737e2d98b6358d`

| Arquivo no Chiocca | Projeto | Caminho de origem | Commit | O que mudou | Fase |
| --- | --- | --- | --- | --- | --- |
| `chiocca/v2/validade.py` | Carchuna | `carchuna/validade.py` | `a3f30ac284eb01245b022b7655bb16c4b8474cc7` | Classe de resultado com três estados e `variacao_percentual`; float em vez de Decimal, motivo em PT e EN, ponte para o motor v1; sem os limiares de margem | B |
| `chiocca/v2/linhagem.py` | Carchuna | `carchuna/linhagem.py` | `a3f30ac284eb01245b022b7655bb16c4b8474cc7` | Formato da ficha; colunas de planilha viraram linhas da DFP, com a linha do arquivo de origem; montador novo para o motor v1 | B |
| `chiocca/v2/confianca.py` | Carchuna | `carchuna/confianca.py` | `a3f30ac284eb01245b022b7655bb16c4b8474cc7` | Só a estrutura de componentes com motivo; sem a nota de 0 a 100; critérios e nível categórico novos | B |
| `chiocca/v2/conferencias.py` | Carchuna | `carchuna/margem.py` | `a3f30ac284eb01245b022b7655bb16c4b8474cc7` | Só o princípio (identidade, reconciliação por outro caminho e plausibilidade); conferências novas para a CVM | B |
| `.github/workflows/ci.yml` | DireitoAberto | `.github/workflows/ci.yml` | `102e3e2d9d70e87249d8df9215737e2d98b6358d` | Só o job de Python, com os comandos do Chiocca | B |
| `chiocca/v2/pdf_simples.py` | DireitoAberto | `backend/app/leitor/pdf_simples.py` | `102e3e2d9d70e87249d8df9215737e2d98b6358d` | Saíram a página digitalizada, a página sem texto e a fonte inexistente (conjunto adversarial); entraram a transliteração fora do Windows-1252, a paginação e o rodapé com o aviso em todas as páginas | C2 |

**Fora de outros projetos.** `tests/referencia/gerar_exemplo_resolvido.py` veio da conversa de planejamento (claude.ai, com o Claude), escrito antes do motor, e foi entregue por Roberto em 08/11/2026. A origem está no docstring do próprio arquivo. Mudanças: a formatação do black, uma anotação de tipo pedida pelo mypy e, em 09/11/2026, por decisão de Roberto, o arredondamento de três valores (`DPO_t_dias`, `variacao_dias` e `spread_pp`) de 2 para 4 casas, para seguir o commit 70d71a5; nenhuma conta mudou.

**Fase D.** Nenhum arquivo veio de outro projeto: `chiocca/v2/api.py`, `chiocca/v2/modelos.py`, `chiocca/v2/busca.py` e `tests/test_v2_api.py` foram escritos para o Chiocca System. FastAPI, Pydantic, uvicorn e httpx são dependências instaladas, fixadas no `pyproject.toml` e no `requirements-lock.txt`, não código copiado.
