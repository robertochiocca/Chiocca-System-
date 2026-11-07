"""Os documentos de resultados saem do script e têm os mesmos números em PT e EN (regra 2 e paridade do PROMPT)."""

from __future__ import annotations

import json
import re

import pytest

from chiocca import relatorio_resultados as rr
from chiocca import textos_resultados as tr

pytestmark = pytest.mark.skipif(not rr.NUMEROS.exists(), reason="docs/resultados_numeros.json ainda não gerado")


def _numeros() -> dict:
    return json.loads(rr.NUMEROS.read_text(encoding="utf-8"))


@pytest.mark.parametrize("lang", ["pt", "en"])
def test_documento_igual_a_saida_do_script(lang: str) -> None:
    assert rr.DOCS[lang].read_text(encoding="utf-8") == tr.render(_numeros(), lang)


def _extrai(texto: str, lang: str) -> list[float]:
    # Identificadores não são quantidades: código de conta entre parênteses (2.01.02), seção ou parte de documento
    # (seção 4.1, parte 1.4) e identificadores de caso em código (`mundial_2017`).
    texto = re.sub(r"`[^`]*`", " ", texto)
    texto = re.sub(r"\(\d+(?:\.\d+)+\)", " ", texto)
    texto = re.sub(r"\b(seção|seções|section|sections|parte|part)\s+\d+(?:\.\d+)+", r"\1", texto)
    if lang == "pt":
        texto = re.sub(r"(\d{2})/(\d{2})/(\d{4})", r"\3 \2 \1", texto)
        brutos = re.findall(r"\d[\d.]*(?:,\d+)?", texto)
        return sorted(float(x.replace(".", "").replace(",", ".")) for x in brutos)
    texto = re.sub(r"(\d{4})-(\d{2})-(\d{2})", r"\1 \2 \3", texto)
    brutos = re.findall(r"\d[\d,]*(?:\.\d+)?", texto)
    return sorted(float(x.replace(",", "")) for x in brutos)


def test_mesmos_numeros_nos_dois_idiomas() -> None:
    pt = _extrai(rr.DOCS["pt"].read_text(encoding="utf-8"), "pt")
    en = _extrai(rr.DOCS["en"].read_text(encoding="utf-8"), "en")
    assert pt == en


def test_catalogo_de_mensagens_completo() -> None:
    assert tr.T["pt"].keys() == tr.T["en"].keys()
    iguais = {"nc"}  # "n.c." é a mesma abreviação nos dois idiomas
    for chave, pt in tr.T["pt"].items():
        en = tr.T["en"][chave]
        if isinstance(pt, (list, dict)):
            assert len(pt) == len(en), chave
            continue
        assert pt.strip() and en.strip(), chave
        if chave not in iguais:
            assert pt != en, chave
    for tabela in (tr.CONTAS, tr.PECAS, tr.TIPOS, tr.PLANOS, tr.SINAIS):
        for pt, en in tabela.values():
            assert pt.strip() and en.strip()


def test_documentos_sem_linguagem_de_acusacao() -> None:
    for caminho in rr.DOCS.values():
        texto = caminho.read_text(encoding="utf-8").lower()
        assert "fraude" not in texto and "fraud" not in texto and "suspeit" not in texto and "suspect" not in texto


@pytest.mark.parametrize(
    "motivo,pt,en",
    [
        ("conta_ausente:fornecedores", "conta ausente: fornecedores (2.01.02)",
         "missing account: trade payables (2.01.02)"),
        ("divisao_por_zero:DPO custo t-1", "denominador zero: DPO, custo das vendas de t−1",
         "zero denominator: DPO, t−1 cost of sales"),
        ("plano_de_contas:banco", "plano de contas de banco", "bank chart of accounts"),
        ("componente:DEPI", "componente não calculável: DEPI", "component not computable: DEPI"),
    ],
)  # fmt: skip
def test_motivos_nos_dois_idiomas(motivo: str, pt: str, en: str) -> None:
    assert tr.motivo(motivo, "pt") == pt and tr.motivo(motivo, "en") == en
