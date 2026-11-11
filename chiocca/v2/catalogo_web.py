"""Textos do catálogo para a interface (Fase E2, 10/11/2026): o bloco `leitura_simples` de catalogo_sinais.yaml (o
que cada sinal mede e por que importa, em linguagem simples, PT e EN, e uma linha por componente do M-score e do
Z''), com os nomes do catálogo, nas chaves que a investigação usa (`sinal`). Grava web/lib/catalogo.json; um teste
confere que o arquivo está em dia com o catálogo.

Sem dependência nova: o PyYAML não é dependência do projeto. O bloco `leitura_simples` usa só mapas e textos entre
aspas duplas numa linha, e é lido aqui por um leitor estrito desse formato, que recusa qualquer outra coisa; os
nomes vêm das linhas `nome:` e `nome_en:` de cada sinal. Um teste confere, quando o PyYAML está instalado, que o
resultado é o mesmo da leitura completa do YAML.

Uso: python -m chiocca.v2.catalogo_web
"""

from __future__ import annotations

import json
import re
from typing import Any

from chiocca import base

CATALOGO = base.RAIZ / "catalogo_sinais.yaml"
DESTINO = base.RAIZ / "web" / "lib" / "catalogo.json"
# sinal na investigação -> id no catálogo
SINAIS = {
    "mscore": "mscore_beneish",
    "dpo": "dpo_salto",
    "juro": "juro_implicito",
    "lucro_sem_caixa": "lucro_sem_caixa",
    "peso_nao_recorrente": "peso_nao_recorrente",
    "altman_z2": "altman_z2",
    "piotroski_f": "piotroski_f",
}


_CHAVE = re.compile(r"^( *)([A-Za-z0-9_]+):(?: (\".*\"))?$")


def ler_leitura_simples(texto: str) -> dict[str, Any]:
    """O bloco `leitura_simples` (mapas e textos entre aspas duplas numa linha); recusa qualquer outro formato."""
    linhas = texto.split("\n")
    inicio = linhas.index("leitura_simples:")
    raiz: dict[str, Any] = {}
    pilha: list[tuple[int, dict[str, Any]]] = [(0, raiz)]  # (recuo dos filhos, mapa)
    for n, linha in enumerate(linhas[inicio + 1 :], inicio + 2):
        if not linha.strip() or linha.lstrip().startswith("#"):
            continue
        if not linha.startswith(" "):
            break  # fim do bloco
        m = _CHAVE.match(linha)
        if not m:
            raise ValueError(f"catalogo_sinais.yaml, linha {n}: fora do formato do bloco leitura_simples")
        recuo, chave, valor = len(m.group(1)), m.group(2), m.group(3)
        while len(pilha) > 1 and recuo < pilha[-1][0]:  # volta ao mapa do recuo da linha
            pilha.pop()
        if recuo != pilha[-1][0] and pilha[-1][0] != 0:
            raise ValueError(f"catalogo_sinais.yaml, linha {n}: recuo inesperado")
        atual = pilha[-1][1]
        if valor is None:
            atual[chave] = {}
            pilha.append((recuo + 2, atual[chave]))
        else:
            atual[chave] = json.loads(valor)
    return raiz


def nomes_dos_sinais(texto: str) -> dict[str, dict[str, str]]:
    """`nome` e `nome_en` de cada sinal, das linhas `nome: "..."` do bloco de cada `- id:`."""
    out: dict[str, dict[str, str]] = {}
    atual: dict[str, str] | None = None
    for linha in texto.split("\n"):
        if m := re.match(r"^  - id: (\S+)$", linha):
            atual = out.setdefault(m.group(1), {})
        elif atual is not None and (m := re.match(r'^    (nome|nome_en): (".*")$', linha)):
            atual[m.group(1)] = json.loads(m.group(2))
    return out


def gerar() -> dict[str, Any]:
    texto = CATALOGO.read_text(encoding="utf-8")
    entradas = nomes_dos_sinais(texto)
    leitura = ler_leitura_simples(texto)
    sinais: dict[str, Any] = {}
    componentes: dict[str, Any] = {}
    for sinal, id_ in SINAIS.items():
        e, x = entradas[id_], leitura[id_]
        sinais[sinal] = {
            "pt": {"nome": e["nome"].strip(), "o_que_mede": x["o_que_mede"], "por_que": x["por_que"]},
            "en": {"nome": e["nome_en"].strip(), "o_que_mede": x["o_que_mede_en"], "por_que": x["por_que_en"]},
        }
        for k, v in (x.get("componentes") or {}).items():
            componentes[k] = {"pt": v["pt"], "en": v["en"]}
    return {"gerado_por": "python -m chiocca.v2.catalogo_web", "sinais": sinais, "componentes": componentes}


def texto() -> str:
    return json.dumps(gerar(), ensure_ascii=False, indent=1) + "\n"


def main() -> None:
    DESTINO.write_text(texto(), encoding="utf-8")
    print(DESTINO)


if __name__ == "__main__":
    main()
