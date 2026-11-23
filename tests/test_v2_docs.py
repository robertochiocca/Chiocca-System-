"""Documentos do v2 escritos à mão: cada um tem o par em inglês, com os mesmos números (paridade do PROMPT.md)."""

from __future__ import annotations

import json
import posixpath
import re
import subprocess
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
    ("docs/pre-registro-leitor.md", "docs/en/reader-preregistration.md"),
    ("docs/estudo-2-plano.md", "docs/en/study-2-plan.md"),
    ("docs/pre-registro-estudo-2.md", "docs/en/study-2-preregistration.md"),
    ("README.md", "README.en.md"),
    ("docs/historico.md", "docs/en/history.md"),
    ("docs/como-reproduzir.md", "docs/en/how-to-reproduce.md"),
    ("docs/motor-v2-plano.md", "docs/en/engine-v2-plan.md"),
    ("docs/motor-v2-descricoes.md", "docs/en/engine-v2-descriptions.md"),
    ("docs/motor-v2-dentro-da-amostra.md", "docs/en/engine-v2-in-sample.md"),
    ("docs/pre-registro-motor-v2.md", "docs/en/engine-v2-preregistration.md"),
    ("docs/estudo-2-emenda-5-rascunho.md", "docs/en/study-2-amendment-5-draft.md"),
]
README = {"pt": "README.md", "en": "README.en.md"}
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
    pt = (RAIZ / README["pt"]).read_text(encoding="utf-8")
    en = (RAIZ / README["en"]).read_text(encoding="utf-8")
    for lang, readme, frase in (
        ("pt", pt, "O invariante do estudo 1 ({i} de {e} empresa-anos iguais ao estudo) roda localmente"),
        ("en", en, "The study 1 invariant ({i} of {e} company-years equal to the study) runs locally"),
    ):
        assert frase.format(i=inteiro(iguais, lang), e=inteiro(estudo, lang)) in readme
    total = armazem + len(FASE_2)
    assert (
        f"pula {total} testes: {armazem} dependem do armazém" in pt and f"e {len(FASE_2)} são valores da fase 2" in pt
    )
    assert f"skips {total} tests: {armazem} depend on the store" in en and f"and {len(FASE_2)} are phase 2 values" in en
    assert len(exemplos.PARES) == 4 and "regeneração dos 4 exemplos" in pt and "regeneration of the 4 examples" in en


def test_readme_demonstracao_com_o_numero_de_companhias_do_modo_demonstracao() -> None:
    from chiocca.v2.api import empresas_da_demonstracao

    n = len(empresas_da_demonstracao())
    casos = (
        ("pt", "## Em 30 segundos\n", "## Demonstração\n", f"as {n} companhias do gabarito"),
        ("en", "## In 30 seconds\n", "## Demo\n", f"the {n} ground-truth companies"),
    )
    for lingua, h_topo, h_demo, companhias in casos:
        readme = (RAIZ / README[lingua]).read_text(encoding="utf-8")
        topo = readme.split(h_topo, 1)[1].split("\n## ", 1)[0]
        demo = readme.split(h_demo, 1)[1].split("\n## ", 1)[0]
        assert "https://robertochiocca.github.io/Chiocca-System-/" in demo and companhias in demo
        assert "https://robertochiocca.github.io/Chiocca-System-/" in topo
        # as capturas de npm run capturas -- --readme, na língua do README, no topo: computador e celular
        assert re.findall(r'src="(docs/imagens/[^"]+)"', readme) == [
            f"docs/imagens/demonstracao-computador-{lingua}.png",
            f"docs/imagens/demonstracao-celular-{lingua}.png",
        ]
        assert re.findall(r'src="(docs/imagens/[^"]+)"', topo) == re.findall(r'src="(docs/imagens/[^"]+)"', readme)


@pytest.mark.parametrize("lang", ["pt", "en"])
def test_readme_topo_de_30_segundos(lang: str) -> None:
    """Pedido de 21/11/2026: o topo traz os números do estudo 1 e o estado do estudo 2, gerados, e o README tem
    no máximo 1.500 palavras; o histórico das fases fica em docs/historico.md."""
    from chiocca.v2 import textos_readme

    readme = (RAIZ / README[lang]).read_text(encoding="utf-8")
    topo = readme.split("## Em 30 segundos\n" if lang == "pt" else "## In 30 seconds\n", 1)[1].split("\n## ", 1)[0]
    t = textos_readme.topo(lang)
    assert t["estudo_1"] in topo and t["estudo_2"] in topo and t["stack"] in topo
    assert len(readme.split()) <= 1500
    historico = "docs/historico.md" if lang == "pt" else "docs/en/history.md"
    assert f"]({historico})" in readme
    aviso = (
        ("Alerta, não acusação.", "não é recomendação de investimento")
        if lang == "pt"
        else ("Alert, not accusation.", "is not investment advice")
    )
    assert all(a in readme for a in aviso)


def test_topo_do_estudo_2_bate_com_o_lacre_e_o_carimbo() -> None:
    """Pedido de 22/11/2026: o topo diz que só o SHA-256 da lista é público e que ele está carimbado no Bitcoin. O
    registro traz o SHA-256 e o carimbo da lista tem uma atestação do Bitcoin (a etiqueta do OpenTimestamps para
    BitcoinBlockHeaderAttestation)."""
    lacre = json.loads((RAIZ / "docs/estudo_2_lista_lacrada.json").read_text(encoding="utf-8"))
    assert re.fullmatch(r"[0-9a-f]{64}", lacre["sha256"])
    ots = (RAIZ / "docs/carimbos/estudo-2-lista.txt.ots").read_bytes()
    assert bytes.fromhex("0588960d73d71901") in ots


def test_regra_boba_do_topo_igual_a_do_pre_registro() -> None:
    """O topo descreve a regra boba como na seção 7 do pré-registro: o decil mais endividado de cada ano, dentro de
    cada grupo; o 10% sai da constante do código (sinais_amostra.PERCENTIL)."""
    from chiocca import sinais_amostra
    from chiocca.v2 import textos_readme

    pre = (RAIZ / "docs/pre-registro.md").read_text(encoding="utf-8")
    assert "sinalizar o decil mais endividado (passivo total ÷ ativo total) de cada ano, dentro de cada grupo" in pre
    assert sinais_amostra.PERCENTIL == 0.9
    assert "alertar os 10% mais endividados de cada ano, dentro de cada grupo" in textos_readme.topo("pt")["estudo_1"]
    assert "flag the 10% most indebted firms each year, within each group" in textos_readme.topo("en")["estudo_1"]


def test_datas_do_topo_iguais_as_do_script_do_estudo_2() -> None:
    """O produto não importa o script do estudo; o teste confere a data da avaliação secundária contra ele."""
    from chiocca.v2 import textos_readme
    from chiocca.v2.estudo2 import secundaria

    assert textos_readme.DATA_AVALIACAO_SECUNDARIA == secundaria.DATA_MINIMA.isoformat()
    pre_registro = (RAIZ / "docs/pre-registro-estudo-2.md").read_text(encoding="utf-8")
    assert "31/05/2027" in pre_registro and "01/01/2030" in pre_registro


def _imagens_citadas(md: str) -> list[str]:
    """Imagens citadas num Markdown: ![alt](caminho) e <img src="caminho">."""
    return re.findall(r"!\[[^\]]*\]\(\s*<?([^)\s>]+)", md) + re.findall(r"<img\b[^>]*\bsrc=[\"']([^\"']+)", md)


def test_imagens_citadas_nos_readmes_existem_no_repositorio() -> None:
    """Toda imagem citada num README do repositório é um arquivo versionado (não basta existir no disco)."""
    versionados = set(subprocess.run(["git", "ls-files", "-z"], cwd=RAIZ, capture_output=True, check=True,
                                     text=True).stdout.split("\0"))  # fmt: skip
    readmes = sorted(p for p in versionados if re.search(r"(^|/)readme[^/]*\.md$", p, re.IGNORECASE))
    assert "README.md" in readmes and "README.en.md" in readmes
    citadas = []
    for readme in readmes:
        for alvo in _imagens_citadas((RAIZ / readme).read_text(encoding="utf-8")):
            assert not re.match(r"^[a-z]+:", alvo, re.IGNORECASE), f"{readme}: imagem fora do repositório: {alvo}"
            caminho = posixpath.normpath(posixpath.join(posixpath.dirname(readme), alvo.split("#")[0]))
            assert caminho in versionados, f"{readme}: {alvo} não está no repositório"
            citadas.append(caminho)
    assert len(citadas) >= 4  # as quatro do README: computador e celular, em PT e EN


def test_imagens_citadas_reconhece_markdown_e_html() -> None:
    md = '![a](docs/x.png "título") texto <img width="9" src="docs/y.png" alt="b"> e [link](docs/z.md)'
    assert _imagens_citadas(md) == ["docs/x.png", "docs/y.png"]


def test_readme_lucro_sem_caixa_sem_alerta_sozinho() -> None:
    """Pedido de 22/11/2026: a seção de sinais diz que o lucro que não vira caixa aparece na ficha, mas não dispara
    alerta sozinho, como na seção 4 do pré-registro do estudo 1."""
    pre = (RAIZ / "docs/pre-registro.md").read_text(encoding="utf-8")
    secao_4 = pre.split("## 4. Sinais e regras de alerta", 1)[1].split("\n## 5.", 1)[0]
    assert "O lucro sem caixa aparece na ficha, mas não dispara alerta sozinho" in secao_4
    pt = (RAIZ / README["pt"]).read_text(encoding="utf-8")
    en = (RAIZ / README["en"]).read_text(encoding="utf-8")
    assert "O lucro que não vira caixa aparece na ficha, mas não dispara alerta sozinho" in pt
    assert "Earnings not backed by cash appear on the alert sheet but do not trigger an alert on their own" in en
    assert all("](docs/pre-registro.md), section 4" in x or "](docs/pre-registro.md), seção 4" in x for x in (pt, en))
