"""Avaliador da Fase F2b (emenda 1 do pré-registro do leitor, seções 10.2 a 10.7): mede a `leitor-f1-2` e a
`leitor-f1-1` nos mesmos casos e a regra nova do assunto do IPE ao lado das regras de hoje.

- Casos do leitor: o formato da seção 6, com o campo opcional `esperado.trechos_que_nao_devem_aparecer` (10.2). As
  definições da seção 5 não mudam (unidades, correspondência, precisão, cobertura, conferência literal, nome vazado),
  e as contas são as do avaliador da f1-1 (chiocca/v2/leitor/avaliacao.py), refeitas aqui para os dois leitores. A
  `leitor-f1-1` é chamada sem mudança (chiocca.v2.leitor.ler), como manda a decisão 7 de 10.7: o avaliador antigo
  rejeita o campo novo, então é este que mede as duas.
- Um texto de `trechos_que_nao_devem_aparecer` "sai como trecho" quando está contido, sem diferença de espaços, no
  texto de algum trecho mostrado (10.7, item 4).
- Critério de troca (10.7, item 3): a f1-2 só substitui a f1-1 se atingir as quatro metas, se a precisão dela for
  pelo menos a da f1-1 e se o número de textos de cabeçalho que saem como trecho não for maior que o da f1-1.
- Casos de assunto (10.4): arquivos `assuntos_*.json`. Metas da regra nova (10.3): zero nome de pessoa (nenhum
  assunto `omitido` mostrado e nenhum texto de `nomes_proibidos` em assunto mostrado) e omissão indevida de no máximo
  0,20. Assunto vazio não entra nas contas. As regras de hoje (chiocca.v2.ipe.regra_de_omissao) são medidas ao lado,
  só para comparar. A auditoria de 400 assuntos reais (10.7, item 6) vem depois, se a regra atingir as duas metas.

Resultados com três casas decimais, somando todos os casos (média micro).
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from types import ModuleType
from typing import Any

from chiocca import base
from chiocca.v2 import ipe
from chiocca.v2.leitor import VERSAO as VERSAO_F1_1
from chiocca.v2.leitor import avaliacao as av1
from chiocca.v2.leitor import ler as ler_f1_1
from chiocca.v2.leitor.nomes import chave
from chiocca.v2.leitor.texto import confere, normaliza
from chiocca.v2.leitor_f1_2 import VERSAO, assunto
from chiocca.v2.leitor_f1_2 import ler as ler_f1_2

METAS = av1.METAS
METAS_ASSUNTO = {"nomes_vazados": 0, "omissao_indevida": 0.20}
CAMPOS_ESPERADO = av1.CAMPOS_ESPERADO | {"trechos_que_nao_devem_aparecer"}
CAMPOS_ASSUNTOS = {"id", "descricao", "assuntos", "nomes_proibidos"}
AUDITORIA = ("se aprovada nos casos: 400 assuntos reais de 2010 a 2024 que a regra nova mostra e as de hoje omitem, "
             "sorteados com a semente 20261113 e lidos (seção 10.7, item 6)")  # fmt: skip
LEITORES: dict[str, tuple[str, ModuleType]] = {"f1_2": (VERSAO, ler_f1_2), "f1_1": (VERSAO_F1_1, ler_f1_1)}


def valida(caso: dict[str, Any]) -> list[str]:
    """O formato da seção 6, com o campo opcional de 10.2 (lista de textos)."""
    esp = dict(caso.get("esperado") or {})
    extra = esp.pop("trechos_que_nao_devem_aparecer", None)
    p = av1.valida({**caso, "esperado": esp})
    if extra is not None and (not isinstance(extra, list) or not all(isinstance(x, str) and x.strip() for x in extra)):
        p.append("esperado.trechos_que_nao_devem_aparecer deve ser uma lista de textos")
    return p


def valida_assuntos(dados: dict[str, Any]) -> list[str]:
    p: list[str] = []
    if set(dados) - CAMPOS_ASSUNTOS:
        p.append(f"campos desconhecidos: {sorted(set(dados) - CAMPOS_ASSUNTOS)}")
    if not isinstance(dados.get("id"), str) or not dados["id"]:
        p.append("id ausente")
    if not isinstance(dados.get("assuntos"), list) or not dados["assuntos"]:
        p.append("assuntos ausente")
    for i, x in enumerate(dados.get("assuntos") or []):
        if (
            not isinstance(x, dict)
            or set(x) - {"assunto", "esperado", "categoria"}
            or not isinstance(x.get("assunto"), str)
        ):
            p.append(f"assunto {i}: fora do formato")
        elif x.get("esperado") not in ("omitido", "mostrado"):
            p.append(f"assunto {i}: esperado deve ser omitido ou mostrado")
        elif x.get("categoria") not in (None, "fato_relevante", "comunicado_ao_mercado"):
            p.append(f"assunto {i}: categoria desconhecida")
    if not isinstance(dados.get("nomes_proibidos"), list):
        p.append("nomes_proibidos ausente")
    return p


def avaliar_caso(caso: dict[str, Any], leitor: ModuleType) -> dict[str, Any]:
    """As contas da f1-1 (av1.avaliar_caso) para o leitor dado, mais os textos de cabeçalho que saem como trecho."""
    esp = caso["esperado"]
    pdf = av1.pdf_do_caso(caso)
    saida = leitor.ler(pdf, caso.get("parecer"), caso.get("formulario_de_referencia"), "pt")
    paginas = leitor.paginas_lidas(pdf)
    trechos = av1._trechos(saida)
    mostrados = conferidos = 0
    for t in trechos:
        if t["omitido"]:
            continue
        mostrados += 1
        fonte = (
            caso["parecer"]["texto"]
            if t["verificacao"] == "parecer"
            else (paginas[t["pagina"] - 1] if t["pagina"] and t["pagina"] <= len(paginas) else "")
        )
        conferidos += int(bool(t["conferido"]) and confere(t["texto"], fonte))
    grupos: dict[tuple[Any, ...], list[dict[str, Any]]] = {}
    for t in trechos:
        grupos.setdefault(av1._chave_unidade(t), []).append(t)
    itens = list(esp.get("itens", []))
    unidades = [{"chave": list(k), "trechos": len(ts), "corresponde": any(av1._corresponde(i, k) for i in itens)}
                for k, ts in grupos.items()]  # fmt: skip
    achados: list[dict[str, Any]] = []
    classificacoes: list[tuple[str, Any, Any]] = []
    if caso.get("notas") is not None:
        classificacoes.append(("notas", (saida.get("notas_explicativas") or {}).get("status"), esp.get("notas")))
    if caso.get("parecer") is not None:
        classificacoes.append(
            ("parecer_tipo", (saida.get("relatorio_do_auditor") or {}).get("tipo"), esp.get("parecer_tipo"))
        )
    for nome, devolvido, esperado in classificacoes:
        unidades.append({"chave": [nome, devolvido], "trechos": 0, "corresponde": devolvido == esperado})
        achados.append({"item": {"verificacao": nome, "valor": esperado}, "encontrado": devolvido == esperado})
    for item in itens:
        achado = False
        for k, ts in grupos.items():
            if not av1._corresponde(item, k):
                continue
            alvo = item.get("contem")
            if alvo is None or any(t["omitido"] or normaliza(alvo) in normaliza(t["texto"] or "") for t in ts):
                achado = True
                break
        achados.append({"item": item, "encontrado": achado})
    texto_saida = chave(json.dumps(saida, ensure_ascii=False))
    vazados = [n for n in esp.get("nomes_proibidos", []) if chave(n) and chave(n) in texto_saida]
    textos = [normaliza(t["texto"]) for t in trechos if not t["omitido"] and t["texto"]]
    cabecalhos = list(esp.get("trechos_que_nao_devem_aparecer") or [])
    saem = [c for c in cabecalhos if any(normaliza(c) in x for x in textos)]
    return {"unidades": unidades, "itens": achados, "trechos_mostrados": mostrados, "conferidos": conferidos,
            "nomes_vazados": vazados, "cabecalhos_listados": len(cabecalhos), "cabecalhos_que_saem": saem}  # fmt: skip


def _totais(resultados: list[dict[str, Any]]) -> dict[str, Any]:
    unidades = [u for r in resultados for u in r["unidades"]]
    itens = [i for r in resultados for i in r["itens"]]
    mostrados, conferidos = sum(r["trechos_mostrados"] for r in resultados), sum(r["conferidos"] for r in resultados)
    vazados = sum(len(r["nomes_vazados"]) for r in resultados)
    tot = {
        "casos": len(resultados), "unidades": len(unidades), "corretas": sum(u["corresponde"] for u in unidades),
        "itens": len(itens), "encontrados": sum(i["encontrado"] for i in itens), "trechos_mostrados": mostrados,
        "conferidos": conferidos, "nomes_vazados": vazados,
        "cabecalhos_listados": sum(r["cabecalhos_listados"] for r in resultados),
        "cabecalhos_que_saem": sum(len(r["cabecalhos_que_saem"]) for r in resultados),
    }  # fmt: skip
    tot["precisao"] = round(tot["corretas"] / tot["unidades"], 3) if tot["unidades"] else 1.0
    tot["cobertura"] = round(tot["encontrados"] / tot["itens"], 3) if tot["itens"] else 1.0
    tot["conferencia"] = round(conferidos / mostrados, 3) if mostrados else 1.0
    return tot


def _atingidas(tot: dict[str, Any]) -> dict[str, bool]:
    return {
        "precisao": tot["precisao"] >= METAS["precisao"],
        "cobertura": tot["cobertura"] >= METAS["cobertura"],
        "conferencia": tot["conferidos"] == tot["trechos_mostrados"],
        "nomes_vazados": tot["nomes_vazados"] == 0,
    }


def _hoje(texto: str) -> str:
    if not texto.strip():
        return "vazio"
    return "omitido" if ipe.regra_de_omissao(texto) else "mostrado"


def avaliar_assuntos(dados: dict[str, Any], regra: Any) -> dict[str, Any]:
    proibidos = [chave(n) for n in dados.get("nomes_proibidos", []) if chave(n)]
    out: dict[str, Any] = {"esperados_omitido": 0, "mostrados_indevidamente": [], "nomes_vazados": [],
                           "esperados_mostrado": 0, "omitidos_indevidamente": [], "vazios": 0}  # fmt: skip
    for x in dados["assuntos"]:
        devolvido = regra(x["assunto"])
        if devolvido == "vazio":
            out["vazios"] += 1
            continue
        if x["esperado"] == "omitido":
            out["esperados_omitido"] += 1
            if devolvido == "mostrado":
                out["mostrados_indevidamente"].append(x["assunto"])
        else:
            out["esperados_mostrado"] += 1
            if devolvido == "omitido":
                out["omitidos_indevidamente"].append(x["assunto"])
        if devolvido == "mostrado":
            k = chave(x["assunto"])
            out["nomes_vazados"] += [n for n in proibidos if n in k]
    return out


def _totais_assunto(resultados: list[dict[str, Any]]) -> dict[str, Any]:
    tot = {k: sum((len(r[k]) if isinstance(r[k], list) else r[k]) for r in resultados)
           for k in ("esperados_omitido", "mostrados_indevidamente", "nomes_vazados", "esperados_mostrado",
                     "omitidos_indevidamente", "vazios")}  # fmt: skip
    tot["omissao_indevida"] = (
        round(tot["omitidos_indevidamente"] / tot["esperados_mostrado"], 3) if tot["esperados_mostrado"] else 0.0
    )
    return tot


def _commit() -> str | None:
    return av1._commit()


def avaliar(pasta: Path) -> dict[str, Any]:
    """Uma medida: os casos do leitor (*.json que não começam por assuntos_) e os de assunto (assuntos_*.json)."""
    arquivos = sorted(pasta.glob("*.json"))
    if not arquivos:
        raise ValueError(f"nenhum caso em {pasta}")
    casos, conjuntos = [], []
    for arq in arquivos:
        dados = arq.read_bytes()
        conteudo = json.loads(dados.decode("utf-8"))
        sha = hashlib.sha256(dados).hexdigest()
        if arq.name.startswith("assuntos_"):
            problemas = valida_assuntos(conteudo)
            if problemas:
                raise ValueError(f"{arq.name}: " + "; ".join(problemas))
            conjuntos.append({"id": conteudo["id"], "sha256": sha,
                              "regra_nova": avaliar_assuntos(conteudo, assunto.regra),
                              "regras_de_hoje": avaliar_assuntos(conteudo, _hoje)})  # fmt: skip
        else:
            problemas = valida(conteudo)
            if problemas:
                raise ValueError(f"caso {conteudo.get('id')}: " + "; ".join(problemas))
            casos.append({"id": conteudo["id"], "sha256": sha,
                          **{nome: avaliar_caso(conteudo, mod) for nome, (_, mod) in LEITORES.items()}})  # fmt: skip
    leitor: dict[str, Any] | None = None
    troca: dict[str, Any] | None = None
    if casos:
        leitor = {}
        for nome, (versao, _) in LEITORES.items():
            tot = _totais([c[nome] for c in casos])
            leitor[nome] = {"versao": versao, "totais": tot, "atingidas": _atingidas(tot),
                            "aprovado": all(_atingidas(tot).values())}  # fmt: skip
        leitor["f1_1"]["como"] = ("leitor da leitor-f1-1 sem mudança (chiocca.v2.leitor.ler), chamado por este "
                                  "avaliador; o avaliador antigo rejeita o campo novo de esperado")  # fmt: skip
        t2, t1 = leitor["f1_2"]["totais"], leitor["f1_1"]["totais"]
        troca = {
            "quatro_metas_f1_2": leitor["f1_2"]["aprovado"],
            "precisao_f1_2_pelo_menos_f1_1": t2["precisao"] >= t1["precisao"],
            "cabecalhos_f1_2_nao_mais_que_f1_1": t2["cabecalhos_que_saem"] <= t1["cabecalhos_que_saem"],
        }
        troca["troca"] = all(troca.values())
    sujeito: dict[str, Any] | None = None
    if conjuntos:
        nova = _totais_assunto([c["regra_nova"] for c in conjuntos])
        hoje = _totais_assunto([c["regras_de_hoje"] for c in conjuntos])
        ating = {"nomes_vazados": nova["mostrados_indevidamente"] == 0 and nova["nomes_vazados"] == 0,
                 "omissao_indevida": nova["omissao_indevida"] <= METAS_ASSUNTO["omissao_indevida"]}  # fmt: skip
        sujeito = {"metas": METAS_ASSUNTO, "regra_nova": nova, "regras_de_hoje": hoje, "atingidas": ating,
                   "aprovada_nos_casos": all(ating.values()),
                   "auditoria": AUDITORIA}  # fmt: skip
    return {
        "leitor_novo": VERSAO,
        "commit": _commit(),
        "avaliado_em": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "pasta": (
            str(pasta.resolve().relative_to(base.RAIZ)) if pasta.resolve().is_relative_to(base.RAIZ) else pasta.name
        ),
        "metas": METAS,
        "leitor": leitor,
        "criterio_de_troca": troca,
        "assunto": sujeito,
        "casos": casos,
        "assuntos": conjuntos,
    }
