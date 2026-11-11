"""Textos do catálogo para a interface (Fase E2, 10/11/2026): o bloco `leitura_simples` de catalogo_sinais.yaml (o
que cada sinal mede e por que importa, em linguagem simples, PT e EN, e uma linha por componente do M-score e do
Z''), com os nomes do catálogo, nas chaves que a investigação usa (`sinal`). Grava web/lib/catalogo.json; um teste
confere que o arquivo está em dia com o catálogo.

Uso: python -m chiocca.v2.catalogo_web
"""

from __future__ import annotations

import json
from typing import Any

import yaml

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


def gerar() -> dict[str, Any]:
    cat = yaml.safe_load(CATALOGO.read_text(encoding="utf-8"))
    entradas = {s["id"]: s for s in cat["sinais"]}
    leitura = cat["leitura_simples"]
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
