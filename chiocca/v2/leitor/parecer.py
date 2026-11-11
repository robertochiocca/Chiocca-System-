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

_M = r"(?=\s+[A-ZÀ-Ý0-9\"“(])"  # o título é seguido de frase que começa com maiúscula
SECOES: list[tuple[str, str]] = [
    ("base_para_ressalva", r"Base para (?:opini[ãa]o com ressalvas?|opini[ãa]o adversa|abstenç[ãa]o de opini[ãa]o)"),
    ("incerteza_continuidade", r"Incerteza (?:relevante|significativa) (?:relacionada (?:com|à) a? ?)?"
                               r"continuidade operacional"),
    ("enfase", r"(?:Parágrafos? de [êÊ]nfases?|Ênfases?)(?: [-–—] [^.]{0,80}?)?"),
    ("principais_assuntos", r"Principais [Aa]ssuntos de [Aa]uditoria(?: [-–—] PAA| \(PAA\))?"),
    ("outros_assuntos", r"Outros [Aa]ssuntos(?: [-–—] [^.]{0,80}?)?"),
]  # fmt: skip
# Títulos que só encerram a seção anterior.
FIM = (r"Opini[ãa]o(?: com ressalvas?| adversa)?|Abstenç[ãa]o de opini[ãa]o|Base para (?:a )?opini[ãa]o|"
       r"Outras informações que acompanham|Responsabilidades? da (?:administração|diretoria)|"
       r"Responsabilidades? do auditor|Responsabilidades dos auditores|"
       r"Valores correspondentes|Auditoria dos valores correspondentes")  # fmt: skip
TIPOS_NO_TITULO = [("com_ressalva", r"com ressalva"), ("adversa", r"advers[oa]"), ("abstencao", r"absten[çc][ãa]o"),
                   ("sem_ressalva", r"sem ressalva")]  # fmt: skip


def tipo(titulo: str | None, texto: str) -> str | None:
    t = (titulo or "").lower()
    for valor, padrao in TIPOS_NO_TITULO:
        if re.search(padrao, t):
            return valor
    if re.search(r"Opini[ãa]o com ressalva" + _M, texto):
        return "com_ressalva"
    if re.search(r"Opini[ãa]o adversa" + _M, texto):
        return "adversa"
    if re.search(r"Abstenç[ãa]o de opini[ãa]o" + _M, texto):
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
    return tipo(titulo, t), trechos
