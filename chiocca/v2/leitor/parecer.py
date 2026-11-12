"""Relatório do auditor da versão usada da DFP (texto do grupo "Pareceres e Declarações" do ENET).

O tipo de opinião sai do título oficial do item no ENET ("Relatório do Auditor Independente - Sem Ressalva", "- Com
Ressalva", "- Adverso", "- Abstenção de Opinião"); sem tipo no título, sai dos títulos de seção do texto ("Opinião com
ressalva", "Opinião adversa", "Abstenção de opinião"; só "Opinião", sem ressalva). As seções são achadas pelos títulos
no texto corrido (o ENET entrega o relatório sem quebras de linha): cada uma vai do título até o título seguinte, e o
trecho é cortado no fim da última frase antes de 1.200 caracteres (o começo continua literal).
"""

from __future__ import annotations

import re

from chiocca.v2.leitor.texto import normaliza
from chiocca.v2.leitor.trechos import Trecho, corta

# o título é seguido de frase que começa com maiúscula ou de lista ("a)", "i)"), às vezes depois de " ." ou ":"
_M = r"(?=\s*[.:]?\s+(?:[A-ZÀ-Ý0-9\"“(]|[a-z]{1,4}\)))"
# complemento que alguns títulos trazem: "Opinião com ressalva sobre as demonstrações contábeis individuais e consolidadas"
_Q = r"(?i:(?: sobre as demonstrações(?: (?:financeiras|contábeis))?(?: individuais(?: e consolidadas)?| consolidadas)?)?)"
SECOES: list[tuple[str, str]] = [
    ("base_para_ressalva", r"Base para (?:a )?(?i:opini[ãa]o com ressalvas?|opini[ãa]o adversa|abstenç[ãa]o de opini[ãa]o|"
                           r"conclus[ãa]o com ressalvas?)" + _Q + r"(?: [-–—] [^.]{0,80}?)?"),
    ("incerteza_continuidade", r"Incerteza (?:relevante|significativa) (?:relacionada (?:com|à) a? ?)?"
                               r"continuidade operacional"),
    ("enfase", r"(?:Parágrafos? de [êÊ]nfases?|Ênfases?)(?: [-–—] [^.]{0,80}?)?"),
    ("principais_assuntos", r"Principais [Aa]ssuntos de [Aa]uditoria(?: [-–—] PAA| \(PAA\))?"),
    ("outros_assuntos", r"Outros [Aa]ssuntos(?: [-–—] [^.]{0,80}?)?"),
]  # fmt: skip
# Títulos que só encerram a seção anterior.
FIM = (r"Opini[ãa]o(?: com ressalvas?| adversa)?" + _Q + r"|Abstenç[ãa]o de opini[ãa]o" + _Q + r"|Base para (?:a )?opini[ãa]o" + _Q + r"|"
       r"Outras informações que acompanham|Responsabilidades? da (?:administração|diretoria)|"
       r"Responsabilidades? do auditor|Responsabilidades dos auditores|"
       r"Valores correspondentes|Auditoria dos valores correspondentes")  # fmt: skip
TIPOS_NO_TITULO = [("com_ressalva", r"com ressalva"), ("adversa", r"advers[oa]"), ("abstencao", r"absten[çc][ãa]o"),
                   ("abstencao", r"negativa de opini[ãa]o"),
                   ("sem_ressalva", r"sem ressalva")]  # fmt: skip


def tipo(titulo: str | None, texto: str) -> str | None:
    t = (titulo or "").lower()
    for valor, padrao in TIPOS_NO_TITULO:
        if re.search(padrao, t):
            return valor
    if re.search(r"Opini[ãa]o com ressalva" + _Q + _M, texto):
        return "com_ressalva"
    if re.search(r"Opini[ãa]o adversa" + _Q + _M, texto):
        return "adversa"
    if re.search(r"Abstenç[ãa]o de opini[ãa]o" + _Q + _M, texto):
        return "abstencao"
    if re.search(r"Opini[ãa]o" + _M, texto) or "Em nossa opinião" in texto:
        return "sem_ressalva"
    return None


def ler(titulo: str | None, texto: str) -> tuple[str | None, list[Trecho]]:
    t = normaliza(texto)
    marcos: list[tuple[int, int, str | None]] = []  # (início do título, fim do título, seção ou None)
    for secao, padrao in SECOES:
        for m in re.finditer(padrao + _M, t):
            marcos.append((m.start(), m.end(), secao))
    for m in re.finditer(r"(?:" + FIM + r")" + _M, t):
        if not any(a <= m.start() < b for a, b, _ in marcos):
            marcos.append((m.start(), m.end(), None))
    marcos.sort()
    trechos: list[Trecho] = []
    for k, (inicio, fim_titulo, rotulo) in enumerate(marcos):
        if rotulo is None:
            continue
        fim = marcos[k + 1][0] if k + 1 < len(marcos) else len(t)
        corpo = t[inicio:fim].strip()
        if len(corpo) - (fim_titulo - inicio) < 20:  # título sem texto
            continue
        texto_trecho, cortado = corta(corpo)
        trechos.append(Trecho("parecer", rotulo, None, texto_trecho, cortado=cortado))
    tp = tipo(titulo, t)
    if tp in ("com_ressalva", "adversa", "abstencao") and not any(x.rotulo == "base_para_ressalva" for x in trechos):
        antigo = _base_no_formato_antigo(t)
        if antigo:
            texto_trecho, cortado = corta(antigo)
            trechos.insert(0, Trecho("parecer", "base_para_ressalva", None, texto_trecho, cortado=cortado))
    return tp, trechos


def _base_no_formato_antigo(t: str) -> str | None:
    """Relatório no formato antigo, sem o título "Base para opinião com ressalva": o parágrafo da ressalva fica entre
    "...para fundamentar nossa opinião." e o título "Opinião"."""
    m = re.search(
        r"fundamentar (?:a )?nossa opini[ãa]o(?: com ressalvas?| adversa)?\.\s+(.{40,2500}?)\s+Opini[ãa]o" + _M, t
    )
    return m.group(1).strip() if m else None
