"""Ficha do motor, separação correção/efetividade no README e antecedência dos acertos (pedidos de 09/11/2026)."""

from __future__ import annotations

import json

import pytest

from chiocca.base import RAIZ
from chiocca.formato import decimal, inteiro, pct
from chiocca.v2 import analises_pos_estudo_1 as pos_estudo
from chiocca.v2 import ficha_do_motor, textos_readme

N = json.loads((RAIZ / "docs" / "resultados_numeros.json").read_text(encoding="utf-8"))


@pytest.mark.parametrize("lang", ["pt", "en"])
def test_ficha_igual_a_saida_do_script(lang: str) -> None:
    assert ficha_do_motor.DOCS[lang].read_text(encoding="utf-8") == ficha_do_motor.render(lang)


def test_numeros_da_ficha_vem_do_json_do_resumo() -> None:
    x = ficha_do_motor.numeros()
    assert (
        x["acerto"]["acertados"] == N["acerto"]["acertados"] and x["acerto"]["acertaveis"] == N["acerto"]["acertaveis"]
    )
    assert x["alarmes_por_acerto_nf"]["periodo_inteiro"] == N["alarmes"]["nf"]["inteiro"]["alarmes_por_acerto"]
    assert x["dados"]["empresa_anos_nao_financeiras"] == N["amostra"]["nao_financeira"]
    texto = ficha_do_motor.DOCS["pt"].read_text(encoding="utf-8")
    assert f"Acertos: {inteiro(N['acerto']['acertados'], 'pt')} de {inteiro(N['acerto']['acertaveis'], 'pt')}" in texto
    assert decimal(N["alarmes"]["nf"]["inteiro"]["alarmes_por_acerto"], "pt", 1) + " no período inteiro" in texto
    tx = N["taxa"]["nf"]
    taxa = sum(v["em_alerta"] for v in tx.values()) / sum(v["avaliadas"] for v in tx.values())
    assert f"Taxa de alerta: {pct(taxa, 'pt')}" in texto
    r = pos_estudo.calcula(N, pos_estudo.le_dados())
    assert decimal(r["variante"]["esperado"], "pt", 2) in texto and decimal(r["esperado"], "pt", 2) in texto
    for lang in ("pt", "en"):  # as limitações são as do README, com os links ajustados para docs/
        doc = ficha_do_motor.DOCS[lang].read_text(encoding="utf-8")
        assert all(s in doc for s in ficha_do_motor._limitacoes_doc(lang))
        assert len(ficha_do_motor._limitacoes_doc(lang)) == len(textos_readme.limitacoes(lang))


def test_antecedencia_dos_acertos() -> None:
    a = pos_estudo.antecedencia(N)
    acertos = [c["caso_id"] for c in N["casos"] if c["acertavel"] and c["acertado"]]
    assert [c["caso_id"] for c in a["casos"]] == acertos and len(acertos) == N["acerto"]["acertados"]
    meses = sorted(c["meses"] for c in a["casos"])
    assert a["mediana_meses"] == meses[len(meses) // 2] and (a["minimo_meses"], a["maximo_meses"]) == (
        meses[0],
        meses[-1],
    )
    ame = next(c for c in a["casos"] if c["caso_id"] == "americanas")
    assert (ame["dt_receb"], ame["data_publica"], ame["dias"]) == ("2022-02-24", "2023-01-11", 321)
    doc = (RAIZ / "docs" / "analises-pos-estudo-1.md").read_text(encoding="utf-8")
    assert (
        "## 5. Antecedência dos acertos" in doc
        and "**Análise descritiva depois do resultado, não pré-registrada.**" in doc
    )
    assert f"Mediana de {decimal(a['mediana_meses'], 'pt', 1)} meses" in doc


@pytest.mark.parametrize("lang", ["pt", "en"])
def test_readme_separa_correcao_e_efetividade(lang: str) -> None:
    readme = (RAIZ / "README.md").read_text(encoding="utf-8")
    s = textos_readme.separacao(lang)
    for chave in ("h_correcao", "correcao", "h_efetividade", "efetividade", "nao_prova"):
        assert s[chave] in readme
    assert readme.index(s["h_correcao"]) < readme.index(s["h_efetividade"]) < readme.index(s["nao_prova"])
    link = "docs/ficha-do-motor.md" if lang == "pt" else "docs/en/engine-card.md"
    assert link in s["efetividade"]
