"""Exibição da seção de trechos dos documentos (Fase F1), no PDF e na tela (web/lib/trechos.mjs agrupa do mesmo jeito).

Só exibição: o JSON da investigação continua com um item por trecho, como o leitor em uso entrega (a leitor-f1-2 desde
13/11/2026, chiocca/v2/leitura_secao.py; antes, a leitor-f1-1);
nenhum trecho sai, entra ou muda de rótulo. Decisões de 11/11/2026, depois da medida:
- trecho mostrado com mais de um rótulo aparece uma vez, com os rótulos juntos;
- os trechos omitidos da mesma página viram uma linha só, sem contagem (no relatório do auditor, que não tem página,
  idem); a contagem saiu em 12/11/2026, porque podia contar o mesmo trecho duas vezes;
- a investigação traz "Como o leitor foi testado" (da saída da medida que pôs o leitor em uso na seção,
  docs/leitor_medida_f1_2.json), a versão do leitor (da mesma saída: o leitor e o commit do congelamento) e os limites
  da seção (o número dos documentos reais vem de docs/leitor_documentos_reais.json, gerado por python -m
  chiocca.v2.leitura_real; o dos cabeçalhos, da mesma medida).
"""

from __future__ import annotations

import json
from typing import Any

from chiocca import base

DOCS = base.RAIZ / "docs"
MEDIDA = DOCS / "leitor_medida_f1_2.json"  # a medida da emenda 1, que pôs a leitor-f1-2 na seção em 13/11/2026
CONGELADO = DOCS / "leitor_congelado_f1_2.json"
MEDIDA_F1_1 = DOCS / "leitor_medida.json"  # a medida da leitor-f1-1 (11/11/2026), que ligou a seção
REAIS = DOCS / "leitor_documentos_reais.json"

LIMITES = {
    "pt": [
        "Em documentos reais, cerca de {p}% dos trechos saem omitidos pelo detector de nomes, inclusive nomes de "
        "empresas fora do cadastro.",
        "Em tabelas, uma linha de cabeçalho (anos, títulos de coluna) ainda pode sair como trecho: na medida do "
        "leitor, {c} de {n} textos de cabeçalho dos casos guardados saíram como trecho.",
    ],
    "en": [
        "In real documents, about {p}% of the excerpts come out omitted by the name detector, including names of "
        "companies outside the registry.",
        "In tables, a header line (years, column titles) may still come out as an excerpt: in the reader's "
        "measurement, {c} of {n} header texts of the held-out cases came out as excerpts.",
    ],
}


def _json(caminho: Any) -> dict[str, Any]:
    return json.loads(caminho.read_text(encoding="utf-8"))  # type: ignore[no-any-return]


def _totais() -> dict[str, Any]:
    return _json(MEDIDA)["leitor"]["f1_2"]["totais"]  # type: ignore[no-any-return]


def versao() -> str:
    """'leitor-f1-2 (commit dd688da)': o leitor congelado que gera a seção, com o commit do congelamento medido."""
    m = _json(MEDIDA)
    return f"{m['leitor_novo']} (commit {m['commit'][:7]})"


def como_foi_testado() -> dict[str, Any]:
    """Os números da medida única do leitor em uso nos casos guardados, como saíram (docs/leitor_medida_f1_2.json)."""
    m = _json(MEDIDA)
    t = _totais()
    return {"documento": "docs/leitor_medida_f1_2.json", "leitor": m["leitor_novo"], "commit": m["commit"][:7],
            "casos": t["casos"], "precisao": t["precisao"], "cobertura": t["cobertura"],
            "trechos_mostrados": t["trechos_mostrados"], "trechos_conferidos": t["conferidos"],
            "nomes_vazados": t["nomes_vazados"]}  # fmt: skip


def percentual_omitido() -> int:
    r = _json(REAIS)
    return round(100 * r["omitidos"] / r["trechos"])


def limites(lang: str) -> list[str]:
    p, t = percentual_omitido(), _totais()
    return [x.format(p=p, c=t["cabecalhos_que_saem"], n=t["cabecalhos_listados"]) for x in LIMITES[lang]]


def agrupa(trechos: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Os trechos de um bloco, na ordem do JSON, para mostrar: o mesmo texto da mesma página (e a mesma marca de menção
    negativa) uma vez só, com os rótulos juntos; os omitidos da mesma página numa entrada só, com `n` = quantos itens
    omitidos o JSON tem nessa página (um trecho omitido com dois rótulos é um item por rótulo: o texto omitido não fica
    no JSON, então não dá para juntar os rótulos dele)."""
    out: list[dict[str, Any]] = []
    onde: dict[tuple[Any, ...], int] = {}
    for x in trechos:
        chave = ("omitido", x["pagina"]) if x["omitido"] else ("texto", x["texto"], x["pagina"], x.get("negacao"))
        if chave in onde:
            g = out[onde[chave]]
            g["n"] += 1
            if x.get("rotulo") and x["rotulo"] not in g["rotulos"]:
                g["rotulos"].append(x["rotulo"])
            g["cortado"] = g["cortado"] or bool(x.get("cortado"))
            continue
        onde[chave] = len(out)
        rotulos = [x["rotulo"]] if x.get("rotulo") else []
        out.append({"omitido": x["omitido"], "pagina": x["pagina"], "texto": x["texto"], "negacao": x.get("negacao"),
                    "cortado": bool(x.get("cortado")), "rotulos": rotulos, "n": 1})  # fmt: skip
    return out
