"""Junta o leitor: notas explicativas (partes relacionadas e risco sacado), relatório do auditor e a tabela do
Formulário de Referência, na forma da seção da investigação. É função pura (sem rede): recebe os conteúdos.

Cada trecho sai com a conferência literal contra o texto da página (ou do relatório) e, se tiver nome de pessoa
física, como "trecho omitido; ver página N do documento" (docs/pre-registro-leitor.md, seção 7).
"""

from __future__ import annotations

from typing import Any

from chiocca.v2.leitor import VERSAO, parecer, partes_relacionadas, risco_sacado
from chiocca.v2.leitor.formulario import linha as linha_do_formulario
from chiocca.v2.leitor.texto import Paginas, paginas_do_pdf
from chiocca.v2.leitor.trechos import Trecho

TEXTOS: dict[str, dict[str, Any]] = {
    "pt": {
        "nota": "Trechos copiados dos documentos, com a página, e a tabela do Formulário de Referência. Não é família "
                "de sinais: não gera alerta, nota nem ordenação. Ausência de menção não prova ausência.",
        "condicoes": "A frase sobre condições de mercado é registrada como fato, sem prova (CPC 05 (R1), item 23).",
        "sem_nota": "O leitor não encontrou nota com \"partes relacionadas\" no título.",
        "risco_ausente": "O leitor não encontrou menção a risco sacado, forfait ou convênio com fornecedores nas notas "
                         "desta DFP. Ausência de menção não prova ausência da operação.",
        "nao_lido": {"sem_camada_de_texto": "PDF sem camada de texto (sem reconhecimento de texto em imagem)",
                     "pdf_invalido": "PDF que o leitor não abre", "pdf_sem_paginas": "PDF sem páginas",
                     "arquivo_grande_demais": "arquivo grande demais", "paginas_demais": "páginas demais"},
    },
    "en": {
        "nota": "Excerpts copied from the documents, with the page, and the Reference Form table. It is not a signal "
                "family: it generates no alert, score or ranking. Absence of mention does not prove absence.",
        "condicoes": "The sentence about market terms is recorded as a fact, without proof (CPC 05 (R1), item 23).",
        "sem_nota": "The reader found no note with \"partes relacionadas\" (related parties) in the title.",
        "risco_ausente": "The reader found no mention of reverse factoring (risco sacado), forfaiting or supplier "
                         "agreements in the notes of this DFP. Absence of mention does not prove absence of the "
                         "operation.",
        "nao_lido": {"sem_camada_de_texto": "PDF with no text layer (no text recognition in images)",
                     "pdf_invalido": "PDF the reader cannot open", "pdf_sem_paginas": "PDF with no pages",
                     "arquivo_grande_demais": "file too large", "paginas_demais": "too many pages"},
    },
}  # fmt: skip


def _nao_lido(motivo: str | None, lang: str) -> tuple[dict[str, Any], dict[str, Any]]:
    pr = {"status": "nao_lido", "motivo": motivo, "nota": None, "colunas": [], "trechos": [], "campos_cpc05_18": [],
          "condicoes_de_mercado": [], "nota_condicoes": TEXTOS[lang]["condicoes"]}  # fmt: skip
    return pr, {"status": "nao_lido", "motivo": motivo, "encontrado": None, "termos": [], "trechos": [], "nota": None}


def _mostraveis(trechos: list[Trecho], fonte: dict[int, str], lang: str) -> list[dict[str, Any]]:
    """Saída dos trechos; o que não confere com o texto da página não sai (a conferência literal é exigência)."""
    saida = [x.saida(fonte[x.pagina or 0], lang) for x in trechos]
    return [x for x in saida if x["conferido"]]


def ler_notas(pdf: bytes | None, lang: str, motivo_sem_pdf: str | None = None
              ) -> tuple[dict[str, Any], dict[str, Any], Paginas | None]:  # fmt: skip
    """(partes relacionadas, risco sacado, páginas) a partir do PDF das notas."""
    t = TEXTOS[lang]
    if pdf is None:
        vazio_pr, vazio_rs = _nao_lido(motivo_sem_pdf, lang)
        return vazio_pr, vazio_rs, None
    pag = paginas_do_pdf(pdf)
    if pag.status != "lido":
        vazio_pr, vazio_rs = _nao_lido(t["nao_lido"].get(pag.motivo or "", pag.motivo), lang)
        return vazio_pr, vazio_rs, pag
    nota, trechos = partes_relacionadas.ler(pag.paginas)
    fonte = {p + 1: texto for p, texto in enumerate(pag.paginas)}
    pr: dict[str, Any] = {
        "status": "lido", "motivo": None if nota else t["sem_nota"],
        "nota": None if nota is None else {"titulo": nota.titulo, "paginas": [nota.pagina_inicio, nota.pagina_fim]},
        "colunas": partes_relacionadas.colunas(nota) if nota else [],
        "trechos": _mostraveis([x for x in trechos if x.verificacao == "partes_relacionadas"], fonte, lang),
        "campos_cpc05_18": _mostraveis([x for x in trechos if x.verificacao == "campo_cpc05_18"], fonte, lang),
        "condicoes_de_mercado": _mostraveis([x for x in trechos if x.verificacao == "condicoes_de_mercado"], fonte, lang),
        "nota_condicoes": t["condicoes"],
    }  # fmt: skip
    rs = risco_sacado.ler(pag.paginas)
    risco: dict[str, Any] = {
        "status": "lido", "encontrado": bool(rs), "termos": risco_sacado.termos_encontrados(rs),
        "trechos": _mostraveis(rs, fonte, lang), "nota": None if rs else t["risco_ausente"],
    }  # fmt: skip
    return pr, risco, pag


def ler_relatorio(titulo: str | None, texto: str | None, lang: str, motivo: str | None = None) -> dict[str, Any]:
    if texto is None:
        return {"status": "nao_lido", "motivo": motivo, "titulo": None, "tipo": None, "trechos": []}
    tipo, trechos = parecer.ler(titulo, texto)
    return {"status": "lido", "motivo": None, "titulo": titulo, "tipo": tipo,
            "trechos": _mostraveis(trechos, {0: texto}, lang)}  # fmt: skip


def ler(pdf_notas: bytes | None, relatorio: dict[str, Any] | None, formulario: list[dict[str, Any]] | None,
        lang: str = "pt", motivo_sem_notas: str | None = None, motivo_sem_relatorio: str | None = None
        ) -> dict[str, Any]:  # fmt: skip
    """A leitura dos conteúdos dados, sem os metadados dos documentos (que a seção acrescenta)."""
    pr, risco, pag = ler_notas(pdf_notas, lang, motivo_sem_notas)
    rel = ler_relatorio(relatorio.get("titulo") if relatorio else None, relatorio.get("texto") if relatorio else None,
                        lang, motivo_sem_relatorio)  # fmt: skip
    out: dict[str, Any] = {
        "natureza": "trecho_literal", "gera_alerta": False, "leitor": VERSAO,
        "extrator": pag.extrator if pag else None, "nota": TEXTOS[lang]["nota"],
        "notas_explicativas": {"status": pag.status if pag else "nao_lido", "paginas": len(pag.paginas) if pag else 0},
        "partes_relacionadas": pr, "risco_sacado": risco, "relatorio_do_auditor": rel,
        "formulario_de_referencia": {"status": "disponivel" if formulario else "sem_linhas", "motivo": None,
                                     "linhas": [linha_do_formulario(r, lang) for r in formulario or []]},
    }  # fmt: skip
    return out


def paginas_lidas(pdf_notas: bytes | None) -> list[str]:
    """Texto de cada página, para a conferência literal na avaliação."""
    return paginas_do_pdf(pdf_notas).paginas if pdf_notas else []
