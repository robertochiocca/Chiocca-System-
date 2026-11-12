"""Exibição da seção de trechos dos documentos (Fase F1, decisões de 11/11/2026 depois da medida): título, subseções,
rótulos juntos, omitidos juntos por página, "Como o leitor foi testado", limites, texto do Formulário de Referência,
linha do motor, sem Δ e sem ponto duplo no PDF. Só exibição: os trechos do JSON ficam como o leitor congelado os
entrega."""

from __future__ import annotations

import json
import re

import pytest

from chiocca import base
from chiocca.v2 import exemplos, leitura_exibicao, pdf_investigacao

TEXTOS_TS = base.RAIZ / "web" / "lib" / "textos.ts"


def _inv(lang: str = "pt", data: str = "2024-12-31") -> dict:
    return json.loads((exemplos.PASTA / f"americanas_2021_em_{data}_{lang}.json").read_text(encoding="utf-8"))


def test_agrupa_rotulos_juntos_e_omitidos_por_pagina() -> None:
    pr = _inv()["leitura_documental"]["partes_relacionadas"]
    campos = leitura_exibicao.agrupa(pr["campos_cpc05_18"])
    cabecalho = [g for g in campos if g["texto"] == "2021 2020 2021 2020"]
    assert len(cabecalho) == 1 and cabecalho[0]["rotulos"] == ["montante", "saldos"]
    omitidos = [(g["pagina"], g["n"]) for g in campos if g["omitido"]]
    assert omitidos == [(40, sum(x["omitido"] for x in pr["campos_cpc05_18"]))]
    # nada some: cada item do JSON está numa entrada
    assert sum(g["n"] if g["omitido"] else len(g["rotulos"]) for g in campos) == len(pr["campos_cpc05_18"])
    categorias = leitura_exibicao.agrupa(pr["trechos"])
    n = sum(x["omitido"] for x in pr["trechos"])
    assert [(g["pagina"], g["n"]) for g in categorias if g["omitido"]] == [(40, n)]


def test_como_foi_testado_igual_a_saida_da_medida() -> None:
    medida = json.loads(leitura_exibicao.MEDIDA.read_text(encoding="utf-8"))
    congelado = json.loads(leitura_exibicao.CONGELADO.read_text(encoding="utf-8"))
    m = leitura_exibicao.como_foi_testado()
    t = medida["totais"]
    assert (m["casos"], m["precisao"], m["cobertura"], m["trechos_conferidos"], m["trechos_mostrados"],
            m["nomes_vazados"]) == (t["casos"], t["precisao"], t["cobertura"], t["conferidos"], t["trechos_mostrados"],
                                    t["nomes_vazados"])  # fmt: skip
    assert m["commit"] == medida["commit"][:7] == congelado["commit"][:7]
    assert leitura_exibicao.versao() == f"{congelado['leitor']} (commit {congelado['commit'][:7]})"
    for lang in ("pt", "en"):
        inv = _inv(lang)
        assert inv["como_o_leitor_foi_testado"] == m
        assert inv["limites_da_leitura"] == leitura_exibicao.limites(lang)
        assert inv["motor"]["leitor"] == leitura_exibicao.versao()
        assert "fases B a F1" in inv["motor"]["v2"]


def test_omitidos_nos_documentos_reais_na_documentacao() -> None:
    r = json.loads(leitura_exibicao.REAIS.read_text(encoding="utf-8"))
    assert r["omitidos"] == sum(x["omitidos"] for x in r["por_documento"])
    assert r["trechos"] == sum(x["trechos"] for x in r["por_documento"]) and r["documentos"] == len(r["por_documento"])
    p = leitura_exibicao.percentual_omitido()
    assert f"cerca de {p}%" in leitura_exibicao.limites("pt")[0] and f"about {p}%" in leitura_exibicao.limites("en")[0]
    pt = (base.RAIZ / "docs" / "contratos.md").read_text(encoding="utf-8")
    en = (base.RAIZ / "docs" / "en" / "contracts.md").read_text(encoding="utf-8")
    fr = f"{100 * r['omitidos'] / r['trechos']:.1f}"
    assert f"{r['omitidos']} de {r['trechos']:,}".replace(",", ".") + f" trechos ({fr.replace('.', ',')}%)" in pt
    assert f"{r['omitidos']} of {r['trechos']:,} excerpts ({fr}%)" in en
    assert f"{r['documentos']} documentos" in pt and f"{r['documentos']} documents" in en
    assert f"cerca de {p}% dos trechos" in pt and f"about {p}% of the excerpts" in en


@pytest.mark.parametrize("lang", ["pt", "en"])
def test_pdf_da_secao(lang: str) -> None:
    inv = _inv(lang)
    ls = pdf_investigacao.linhas(inv)
    t = pdf_investigacao.LEITURA[lang]
    assert t["titulo"] in ls
    assert ("# Trechos dos documentos (copiados; não gera alerta)" if lang == "pt"
            else "# Document excerpts (copied; no alert)") in ls  # fmt: skip
    assert f"- {t['omitidos'].format(p=40)}" in ls and not any(re.search(r"\(\d+ (trechos|excerpts)\)", x) for x in ls)
    rotulos = "; ".join(pdf_investigacao.ROTULOS_LEITURA[lang][r] for r in ("montante", "saldos"))
    fim = ")" if lang == "pt" else ", original excerpt in Portuguese)"
    assert f"- [{rotulos}] “2021 2020 2021 2020” (p. 40{fim}" in ls
    fre = ("O Formulário de Referência não traz transações com partes relacionadas na tabela. É a única versão "
           "disponível nos dados abertos; as versões anteriores não estão lá." if lang == "pt" else
           "The Reference Form lists no related-party transactions in the table. It is the only version available in "
           "the open data; earlier versions are not there.")  # fmt: skip
    assert fre in ls
    assert any(x.startswith("Como o leitor foi testado: 20 casos guardados" if lang == "pt"
                            else "How the reader was tested: 20 held-out cases") for x in ls)  # fmt: skip
    i = ls.index(t["limites"])
    assert ls[i + 1 : i + 3] == [f"- {x}" for x in inv["limites_da_leitura"]]
    motor = ls[ls.index("# Motor" if lang == "pt" else "# Engine") + 1]
    assert "fases B a F1" in motor and "leitor-f1-1 (commit c99c953)" in motor


@pytest.mark.parametrize("data", ["2022-04-30", "2024-12-31"])
@pytest.mark.parametrize("lang", ["pt", "en"])
def test_pdf_sem_delta_e_sem_ponto_duplo(lang: str, data: str) -> None:
    ls = pdf_investigacao.linhas(_inv(lang, data))
    assert [x for x in ls if "Δ" in x and "“" not in x] == []
    assert [x for x in ls if re.search(r"(?<!\.)\.\.(?=\s|$)", x) and "“" not in x] == []
    assert ("Variação do ROA: " if lang == "pt" else "Change in ROA: ") in "\n".join(ls)
    if data == "2024-12-31":  # em 30/04/2022 o nome ainda era AMERICANAS S.A.
        assert ("Antes de 2023, a companhia se chamava AMERICANAS S.A." if lang == "pt"
                else "Before 2023, the company was called AMERICANAS S.A.") in ls  # fmt: skip


def _bloco_ts(chave: str) -> list[dict[str, str]]:
    ts = TEXTOS_TS.read_text(encoding="utf-8")
    blocos = re.findall(chave + r": \{(.*?)\}", ts, flags=re.S)
    assert len(blocos) == 2  # PT e EN
    return [dict(re.findall(r'(\w+): "([^"]+)"', b)) for b in blocos]


def test_textos_iguais_na_tela_e_no_pdf() -> None:
    for k, lang in enumerate(("pt", "en")):
        assert _bloco_ts("rotulos_leitura")[k] == pdf_investigacao.ROTULOS_LEITURA[lang]
        assert _bloco_ts("leitura_fre")[k] == pdf_investigacao.LEITURA[lang]["fre"]
        ts = TEXTOS_TS.read_text(encoding="utf-8")
        t = pdf_investigacao.LEITURA[lang]
        for chave_ts, chave_pdf in (("sec_trechos", "titulo"), ("leitura_linhagem", "linhagem"),
                                    ("leitura_fre_doc", "fre_doc"), ("leitura_omitidos", "omitidos"),
                                    ("leitura_omitidos_sem_pagina", "omitidos_sem_pagina")):  # fmt: skip
            valores = re.findall(rf'{chave_ts}: "([^"]+)"', ts)
            assert valores[k] == t[chave_pdf].removeprefix("# "), chave_ts


def test_sem_ponto_duplo_no_meio_e_no_fim_da_linha() -> None:
    linhas = ["- 2011: — -> Ernst & Young Auditores Independentes S.S.. A firma que saiu.",
              "Antes de 2023, a companhia se chamava AMERICANAS S.A..", "Reticências... ficam.",
              "- [saldos] “Trecho literal S.A.. fica como veio” (p. 1)"]  # fmt: skip
    assert pdf_investigacao._sem_ponto_duplo(linhas) == [
        "- 2011: — -> Ernst & Young Auditores Independentes S.S. A firma que saiu.",
        "Antes de 2023, a companhia se chamava AMERICANAS S.A.", "Reticências... ficam.",
        "- [saldos] “Trecho literal S.A.. fica como veio” (p. 1)"]  # fmt: skip
