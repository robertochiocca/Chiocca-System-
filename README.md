# estudo-2-dados

Branch órfão com os dados públicos da CVM usados pela lista lacrada do estudo 2 (pré-registro do estudo 2, seções 3.1 e
8, e emendas 2 e 3). Não tem código nem lista: o código fica no branch de desenvolvimento, no commit anotado em
`docs/estudo_2_lista_lacrada.json` (o do cálculo), e a lista fica com Roberto.

- `brutos/`: os zips da DFP e do FCA de 2024 e 2025 e o cadastro de companhias abertas, da CVM, baixados em 20/11/2026;
- `enet/`: as 26 tabelas do ENET das versões da época (consolidado), baixadas de novo em 20 e 21/11/2026 por
  `chiocca.enet` (7 tentativas, registradas em `docs/estudo_2_enet_tentativas.json`);
- `estudo_2_manifesto.csv`: tamanho, SHA-256, endereço e hora de cada arquivo; para as tabelas do ENET, também o
  SHA-256 da cópia de 07/11/2026 (todas idênticas);
- `contingencia/enet-2026-11-07/`: as cópias de 07/11/2026 dessas 26 tabelas, arquivadas antes do cálculo para a
  contingência da emenda 4, que não foi usada.

Recálculo (seção 8): no commit do cálculo, com Python 3.13 e o `requirements-lock.txt`, copie `brutos/` para
`data/brutos/estudo2/` e `enet/` para `data/cache/enet/` e rode
`python -m chiocca.v2.estudo2.lista --brutos data/brutos/estudo2 --conferir <SHA-256 da lista>`.
