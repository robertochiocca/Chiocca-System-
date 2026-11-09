"""Documentos do v2 escritos à mão: cada um tem o par em inglês, com os mesmos números (paridade do PROMPT.md)."""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[1]
PARES = [
    ("docs/inventario.md", "docs/en/inventory.md"),
    ("docs/contratos.md", "docs/en/contracts.md"),
    ("docs/plano-v2.md", "docs/en/plan-v2.md"),
    ("docs/origem-do-codigo.md", "docs/en/code-origin.md"),
    ("docs/roadmap.md", "docs/en/roadmap.md"),
    ("docs/motor-de-confianca.md", "docs/en/trust-engine.md"),
    ("docs/referencias.md", "docs/en/references.md"),
    ("docs/armazenamento-temporal.md", "docs/en/temporal-storage.md"),
]
AVISO_PT = "Sinal estatístico baseado em demonstrações públicas. Não é acusação, não é recomendação de investimento."
AVISO_EN = "Statistical signal based on public financial statements. Not an accusation, not investment advice."


def numeros(texto: str, lang: str) -> list[float]:
    """Números de um texto, depois de levar o formato PT (1.234,5 e 31/12/2025) ao formato EN."""
    texto = re.sub(r"`[^`\n]*`", " ", texto)  # identificadores e hashes em código
    texto = re.sub(r"\]\([^)\s]*\)", "]", texto)  # destinos de links (URLs, DOIs e caminhos)
    if lang == "pt":
        texto = re.sub(r"(\d{2})/(\d{2})/(\d{4})", r"\3 \2 \1", texto)
        texto = re.sub(r"(?<=\d)\.(?=\d{3}\b)", "", texto)  # separador de milhar
        texto = re.sub(r"(?<=\d),(?=\d)", ".", texto)  # vírgula decimal
    else:
        texto = re.sub(r"(\d{4})-(\d{2})-(\d{2})", r"\1 \2 \3", texto)
        texto = re.sub(r"(?<=\d),(?=\d{3}\b)", "", texto)
    return sorted(float(x) for x in re.findall(r"\d+(?:\.\d+)?", texto))


@pytest.mark.parametrize("pt,en", PARES)
def test_par_em_ingles_com_os_mesmos_numeros(pt: str, en: str) -> None:
    texto_pt = (RAIZ / pt).read_text(encoding="utf-8")
    texto_en = (RAIZ / en).read_text(encoding="utf-8")
    assert numeros(texto_pt, "pt") == numeros(texto_en, "en")


def test_aviso_fixo_nos_contratos() -> None:
    assert AVISO_PT in (RAIZ / "docs/contratos.md").read_text(encoding="utf-8")
    assert AVISO_EN in (RAIZ / "docs/en/contracts.md").read_text(encoding="utf-8")


def test_numeros_no_formato_de_cada_lingua() -> None:
    assert numeros("2.200 linhas, 0,053 e 31/12/2024", "pt") == numeros("2,200 lines, 0.053 and 2024-12-31", "en")


def test_referencias_sem_pdf_no_git_e_com_licenca() -> None:
    assert "referencias/" in (RAIZ / ".gitignore").read_text(encoding="utf-8").splitlines()
    for caminho in ("docs/referencias.md", "docs/en/references.md"):
        linhas = [
            x
            for x in (RAIZ / caminho).read_text(encoding="utf-8").splitlines()
            if x.startswith("| ") and "---" not in x
        ]
        assert len(linhas) > 1 and all(x.count(" | ") == 4 for x in linhas)  # obra, uso, páginas, DOI ou link, licença
    import subprocess

    versionados = subprocess.run(["git", "ls-files"], cwd=RAIZ, capture_output=True, text=True, check=True).stdout
    # Nenhum PDF de referência entra no Git. A exceção são os exemplos gerados por script em docs/exemplos/ (pedido de
    # 09/11/2026), que um teste regenera, byte a byte, a partir do JSON guardado.
    pdfs = [f for f in versionados.splitlines() if f.lower().endswith(".pdf")]
    assert all(f.startswith("docs/exemplos/") for f in pdfs), pdfs


@pytest.mark.parametrize("lang,caminho", [("pt", "docs/contratos.md"), ("en", "docs/en/contracts.md")])
def test_limites_nos_contratos_iguais_ao_texto_do_produto(lang: str, caminho: str) -> None:
    from chiocca.v2 import limites

    texto = (RAIZ / caminho).read_text(encoding="utf-8")
    for paragrafo in limites.textos(lang):
        assert f"  - {paragrafo}" in texto


def test_nao_fazer_no_roadmap() -> None:
    texto = (RAIZ / "docs/roadmap.md").read_text(encoding="utf-8")
    assert "Não copiar o CSV do JarFraud/FraudDetection para o repositório: é derivado da Compustat." in texto
    assert "Não usar as zonas do Z' no Z'' nem os coeficientes de 1979 como régua." in texto


def test_readme_invariante_e_testes_pulados_no_ci() -> None:
    """Os números da frase do README saem do invariante e da contagem dos testes que o CI pula (09/11/2026)."""
    from chiocca.formato import inteiro
    from chiocca.v2 import exemplos
    from tests.test_referencia import FASE_2

    n = json.loads((RAIZ / "docs" / "invariante_numeros.json").read_text(encoding="utf-8"))
    iguais = sum(v["empresa_anos_iguais"] for v in n["exercicios"].values())
    estudo = sum(v["empresa_anos_estudo"] for v in n["exercicios"].values())
    armazem = len(exemplos.PARES) + 1  # a regeneração dos exemplos e o invariante de 2021
    readme = (RAIZ / "README.md").read_text(encoding="utf-8")
    for lang, frase in (
        ("pt", "O invariante do estudo 1 ({i} de {e} empresa-anos iguais ao estudo) roda localmente"),
        ("en", "The study 1 invariant ({i} of {e} company-years equal to the study) runs locally"),
    ):
        assert frase.format(i=inteiro(iguais, lang), e=inteiro(estudo, lang)) in readme
    total = armazem + len(FASE_2)
    assert (
        f"pula {total} testes: {armazem} dependem do armazém" in readme
        and f"e {len(FASE_2)} são valores da fase 2" in readme
    )
    assert (
        f"skips {total} tests: {armazem} depend on the store" in readme
        and f"and {len(FASE_2)} are phase 2 values" in readme
    )
    assert (
        len(exemplos.PARES) == 4
        and "regeneração dos 4 exemplos" in readme
        and "regeneration of the 4 examples" in readme
    )
