"""Avaliação do leitor no conjunto adversarial, com as definições do pré-registro (docs/pre-registro-leitor.md,
seções 5 e 6). Mecanismo inspirado no do DireitoAberto (gabarito declarativo escrito à mão e conferência de toda
citação), reescrito para o Chiocca; nenhum código copiado.

Cada caso é um JSON. As notas viram um PDF gerado aqui, página por página (`pdf_simples`), e o leitor lê esse PDF
como leria o da CVM. As contas:
- unidades devolvidas: trechos agrupados por (verificação, rótulo, página e, no risco sacado, a marca de negação),
  mais as classificações (situação das notas e tipo de opinião do auditor);
- precisão = unidades que correspondem a algum item ÷ unidades;
- cobertura = itens encontrados ÷ itens (o trecho contém `contem`, sem diferença de espaços, ou foi omitido);
- conferência literal: cada trecho mostrado aparece no texto da página (ou do relatório), com os espaços normalizados;
- nome vazado: texto de `nomes_proibidos` (sem diferença de maiúsculas, acentos e espaços) em qualquer campo da saída.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from chiocca import base
from chiocca.v2 import pdf_simples
from chiocca.v2.leitor import VERSAO
from chiocca.v2.leitor import ler as leitor
from chiocca.v2.leitor.nomes import chave
from chiocca.v2.leitor.texto import confere, normaliza

METAS = {"precisao": 0.95, "cobertura": 0.80, "conferencia": 1.0, "nomes_vazados": 0}
VERIFICACOES = {"partes_relacionadas", "campo_cpc05_18", "condicoes_de_mercado", "risco_sacado", "parecer"}
ROTULOS = {
    "partes_relacionadas": {
        "controladora",
        "controle_conjunto_ou_influencia",
        "controladas",
        "coligadas",
        "joint_ventures",
        "pessoal_chave",
        "outras_partes",
    },
    "campo_cpc05_18": {"montante", "saldos", "termos_e_condicoes", "garantias", "provisao_pcld", "perdas_incobraveis"},
    "parecer": {"base_para_ressalva", "enfase", "incerteza_continuidade", "principais_assuntos", "outros_assuntos"},
}
TIPOS_PARECER = {"sem_ressalva", "com_ressalva", "adversa", "abstencao"}
CAMPOS_CASO = {"id", "descricao", "notas", "parecer", "formulario_de_referencia", "esperado"}
CAMPOS_ESPERADO = {"notas", "parecer_tipo", "itens", "nomes_proibidos"}
CAMPOS_ITEM = {"verificacao", "rotulo", "pagina", "negacao", "contem"}


def valida(caso: dict[str, Any]) -> list[str]:
    """Problemas de formato do caso (lista vazia se estiver no formato da seção 6 do pré-registro)."""
    p: list[str] = []
    if set(caso) - CAMPOS_CASO:
        p.append(f"campos desconhecidos: {sorted(set(caso) - CAMPOS_CASO)}")
    if not isinstance(caso.get("id"), str) or not caso["id"]:
        p.append("id ausente")
    esp = caso.get("esperado")
    if not isinstance(esp, dict):
        return p + ["esperado ausente"]
    if set(esp) - CAMPOS_ESPERADO:
        p.append(f"campos desconhecidos em esperado: {sorted(set(esp) - CAMPOS_ESPERADO)}")
    if caso.get("notas") is not None:
        n = caso["notas"]
        if not isinstance(n, dict) or not isinstance(n.get("paginas"), list) or set(n) - {"paginas", "sem_texto"}:
            p.append("notas fora do formato")
        if esp.get("notas") not in ("lido", "nao_lido"):
            p.append("esperado.notas obrigatório (lido ou nao_lido) quando há notas")
    if caso.get("parecer") is not None:
        if set(caso["parecer"]) - {"titulo", "texto"} or not isinstance(caso["parecer"].get("texto"), str):
            p.append("parecer fora do formato")
        if esp.get("parecer_tipo") not in TIPOS_PARECER:
            p.append("esperado.parecer_tipo obrigatório quando há parecer")
    for i, item in enumerate(esp.get("itens", [])):
        if set(item) - CAMPOS_ITEM or item.get("verificacao") not in VERIFICACOES:
            p.append(f"item {i}: fora do formato")
        elif item.get("rotulo") is not None and item["rotulo"] not in ROTULOS.get(item["verificacao"], set()):
            p.append(f"item {i}: rótulo desconhecido {item['rotulo']!r}")
    return p


def pdf_do_caso(caso: dict[str, Any]) -> bytes | None:
    notas = caso.get("notas")
    if notas is None:
        return None
    paginas = [pdf_simples.quebrar(list(p)) for p in notas["paginas"]]
    if notas.get("sem_texto"):
        paginas = [[] for _ in paginas]
    return pdf_simples.gerar_pdf(paginas, [[] for _ in paginas])


def _trechos(saida: dict[str, Any]) -> list[dict[str, Any]]:
    pr, rs, rel = (
        saida.get("partes_relacionadas") or {},
        saida.get("risco_sacado") or {},
        saida.get("relatorio_do_auditor") or {},
    )
    return (
        pr.get("trechos", [])
        + pr.get("campos_cpc05_18", [])
        + pr.get("condicoes_de_mercado", [])
        + rs.get("trechos", [])
        + rel.get("trechos", [])
    )


def _chave_unidade(t: dict[str, Any]) -> tuple[Any, ...]:
    return (
        t["verificacao"],
        t["rotulo"],
        t["pagina"],
        bool(t["negacao"]) if t["verificacao"] == "risco_sacado" else None,
    )


def _corresponde(item: dict[str, Any], k: tuple[Any, ...]) -> bool:
    verif, rotulo, pagina, negacao = k
    if item["verificacao"] != verif:
        return False
    if item.get("rotulo") is not None and item["rotulo"] != rotulo:
        return False
    if item.get("pagina") is not None and item["pagina"] != pagina:
        return False
    return verif != "risco_sacado" or bool(item.get("negacao", False)) == negacao


@dataclass
class Resultado:
    id: str
    sha256: str
    unidades: list[dict[str, Any]] = field(default_factory=list)
    itens: list[dict[str, Any]] = field(default_factory=list)
    mostrados: int = 0
    conferidos: int = 0
    nomes_vazados: list[str] = field(default_factory=list)

    def como_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "sha256": self.sha256,
            "unidades": self.unidades,
            "itens": self.itens,
            "trechos_mostrados": self.mostrados,
            "conferidos": self.conferidos,
            "nomes_vazados": self.nomes_vazados,
        }


def avaliar_caso(caso: dict[str, Any], sha256: str = "") -> Resultado:
    problemas = valida(caso)
    if problemas:
        raise ValueError(f"caso {caso.get('id')}: " + "; ".join(problemas))
    esp = caso["esperado"]
    pdf = pdf_do_caso(caso)
    saida = leitor.ler(pdf, caso.get("parecer"), caso.get("formulario_de_referencia"), "pt")
    paginas = leitor.paginas_lidas(pdf)
    res = Resultado(caso["id"], sha256)
    trechos = _trechos(saida)
    # conferência literal, refeita aqui contra o texto de origem (não só o campo `conferido` da saída)
    for t in trechos:
        if t["omitido"]:
            continue
        res.mostrados += 1
        fonte = (
            caso["parecer"]["texto"]
            if t["verificacao"] == "parecer"
            else (paginas[t["pagina"] - 1] if t["pagina"] and t["pagina"] <= len(paginas) else "")
        )
        res.conferidos += int(bool(t["conferido"]) and confere(t["texto"], fonte))
    # unidades e classificações
    grupos: dict[tuple[Any, ...], list[dict[str, Any]]] = {}
    for t in trechos:
        grupos.setdefault(_chave_unidade(t), []).append(t)
    itens = list(esp.get("itens", []))
    for k, ts in grupos.items():
        ok = any(_corresponde(i, k) for i in itens)
        res.unidades.append({"chave": list(k), "trechos": len(ts), "corresponde": ok})
    classificacoes: list[tuple[str, Any, Any]] = []
    if caso.get("notas") is not None:
        classificacoes.append(("notas", (saida.get("notas_explicativas") or {}).get("status"), esp.get("notas")))
    if caso.get("parecer") is not None:
        classificacoes.append(
            ("parecer_tipo", (saida.get("relatorio_do_auditor") or {}).get("tipo"), esp.get("parecer_tipo"))
        )
    for nome, devolvido, esperado in classificacoes:
        res.unidades.append({"chave": [nome, devolvido], "trechos": 0, "corresponde": devolvido == esperado})
        res.itens.append({"item": {"verificacao": nome, "valor": esperado}, "encontrado": devolvido == esperado})
    for item in itens:
        achado = False
        for k, ts in grupos.items():
            if not _corresponde(item, k):
                continue
            alvo = item.get("contem")
            if alvo is None or any(t["omitido"] or normaliza(alvo) in normaliza(t["texto"] or "") for t in ts):
                achado = True
                break
        res.itens.append({"item": item, "encontrado": achado})
    texto_saida = chave(json.dumps(saida, ensure_ascii=False))
    res.nomes_vazados = [n for n in esp.get("nomes_proibidos", []) if chave(n) and chave(n) in texto_saida]
    return res


def _commit() -> str | None:
    try:
        r = subprocess.run(["git", "rev-parse", "HEAD"], cwd=base.RAIZ, capture_output=True, text=True, check=True)
        return r.stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return None


def avaliar(pasta: Path) -> dict[str, Any]:
    arquivos = sorted(pasta.glob("*.json"))
    if not arquivos:
        raise ValueError(f"nenhum caso em {pasta}")
    resultados = []
    for arq in arquivos:
        dados = arq.read_bytes()
        resultados.append(avaliar_caso(json.loads(dados.decode("utf-8")), hashlib.sha256(dados).hexdigest()))
    unidades = [u for r in resultados for u in r.unidades]
    itens = [i for r in resultados for i in r.itens]
    mostrados, conferidos = sum(r.mostrados for r in resultados), sum(r.conferidos for r in resultados)
    vazados = sum(len(r.nomes_vazados) for r in resultados)
    tot = {
        "casos": len(resultados),
        "unidades": len(unidades),
        "corretas": sum(u["corresponde"] for u in unidades),
        "itens": len(itens),
        "encontrados": sum(i["encontrado"] for i in itens),
        "trechos_mostrados": mostrados,
        "conferidos": conferidos,
        "nomes_vazados": vazados,
    }
    tot["precisao"] = round(tot["corretas"] / tot["unidades"], 3) if tot["unidades"] else 1.0
    tot["cobertura"] = round(tot["encontrados"] / tot["itens"], 3) if tot["itens"] else 1.0
    tot["conferencia"] = round(conferidos / mostrados, 3) if mostrados else 1.0
    atingidas = {
        "precisao": tot["precisao"] >= METAS["precisao"],
        "cobertura": tot["cobertura"] >= METAS["cobertura"],
        "conferencia": conferidos == mostrados,
        "nomes_vazados": vazados == 0,
    }
    return {
        "leitor": VERSAO,
        "commit": _commit(),
        "avaliado_em": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "pasta": (
            str(pasta.resolve().relative_to(base.RAIZ)) if pasta.resolve().is_relative_to(base.RAIZ) else pasta.name
        ),
        "metas": METAS,
        "totais": tot,
        "atingidas": atingidas,
        "aprovado": all(atingidas.values()),
        "casos": [r.como_dict() for r in resultados],
    }
