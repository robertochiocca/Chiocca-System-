"""Menções a risco sacado, forfait e operações parecidas com fornecedores nas notas explicativas.

Procura os termos em todo o documento (parágrafos e linhas de tabela) e marca a frase negativa: "a Companhia não
possui operações de risco sacado" é uma menção negativa (negação antes do termo, na mesma frase). Sem menção, a seção
diz que o leitor não encontrou menção; ausência de menção não prova ausência da operação.
"""

from __future__ import annotations

import re

from chiocca.v2.leitor.trechos import Trecho, segmentos

TERMOS = re.compile(
    r"risco[\s-]sacado|\bforfait(?:ing)?\b|\bconfirming\b|conv[êe]nios? (?:com|de|junto a) fornecedores|"
    r"financiamentos? (?:a|de|com|junto a) fornecedores|"
    r"opera[çc][õo]es? de (?:antecipa[çc][ãa]o|cess[ãa]o) (?:de|a) (?:pagamentos? (?:a|de) )?fornecedores|"
    r"cess[ãa]o de (?:cr[ée]ditos|receb[íi]veis|t[íi]tulos) (?:pelos|por|de) fornecedores|"
    r"supplier financ\w*|reverse factoring|fornecedores?\s*[-–—(]?\s*conv[êe]nios?\b|"
    r"antecipa[çc][ãa]o (?:de pagamentos? )?(?:a|de|aos|dos) fornecedores|supply chain financ\w*|"
    r"financiamento (?:à|da) cadeia de (?:suprimentos|fornecedores)|desconto de (?:duplicatas|t[íi]tulos) (?:de|dos) "
    r"fornecedores"
)
NEGACAO = re.compile(r"\b(?:não|nem|nenhum|nenhuma|inexist\w*|ausência de|sem)\b")
_FRASE = re.compile(r"(?<=[.;!?])\s+")


def _negativa(segmento_busca: str, inicio: int) -> bool:
    """Negação antes do termo, na mesma frase."""
    comeco = 0
    for m in _FRASE.finditer(segmento_busca[:inicio]):
        comeco = m.end()
    return bool(NEGACAO.search(segmento_busca[comeco:inicio]))


def ler(paginas: list[str]) -> list[Trecho]:
    trechos = []
    for p, texto in enumerate(paginas):
        for seg in segmentos(texto, p + 1):
            b = seg.busca
            achados = list(TERMOS.finditer(b))
            if not achados:
                continue
            negacoes = {_negativa(b, m.start()) for m in achados}
            # um trecho por segmento; se houver menção afirmativa e negativa no mesmo segmento, vale a afirmativa
            trechos.append(Trecho("risco_sacado", None, seg.pagina, seg.texto, negacao=negacoes == {True}))
    return trechos


def termos_encontrados(trechos: list[Trecho]) -> list[str]:
    vistos: list[str] = []
    for t in trechos:
        for m in TERMOS.finditer(t.texto.lower()):
            termo = re.sub(r"\s+", " ", m.group(0))
            if termo not in vistos:
                vistos.append(termo)
    return vistos
