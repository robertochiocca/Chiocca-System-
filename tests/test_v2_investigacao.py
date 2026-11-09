"""Investigação (Fase C2, segunda parte): o JSON do contrato, o PDF gerado dele e o exemplo guardado da Americanas."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from chiocca.cvm import Fontes
from chiocca.v2 import armazem, exemplos, investigacao, limites, pdf_investigacao
from tests.test_base import mundo  # noqa: F401  (fixture)
from tests.test_v2_armazem import mundo_c1  # noqa: F401  (fixture)

CAMPOS = {"empresa", "data_referencia", "idioma", "exercicios", "achados", "mudancas", "o_que_se_sabia",
          "qualidade_dos_dados", "parecer_e_auditor", "como_o_motor_foi_testado", "limites", "limitacoes", "evidencias",
          "motor", "gerado_em", "aviso"}  # fmt: skip


@pytest.mark.parametrize("lang", ["pt", "en"])
def test_investigacao_segue_o_contrato(mundo_c1: tuple[Fontes, armazem.FontesArmazem], lang: str) -> None:  # noqa: F811
    _, arm = mundo_c1
    inv = investigacao.gerar(arm, "100", 2020, "2022-04-30", lang, gerado_em="2026-11-09T00:00:00+00:00")
    assert set(inv) == CAMPOS
    assert inv["aviso"] == investigacao.AVISO[lang] and inv["limites"] == limites.textos(lang)
    assert set(inv["achados"]) == {"possivel_manipulacao", "risco_financeiro", "qualidade_financeira"}
    f = inv["achados"]["qualidade_financeira"][0]
    assert f["sinal"] == "piotroski_f" and f["alerta_v1"] is None and "/9 (" in (f["texto"] or "")
    z = inv["achados"]["risco_financeiro"][0]
    assert z["sinal"] == "altman_z2" and z["alerta_v1"] is None and z["regra"] is None
    assert inv["mudancas"]["reapresentacao_pelo_comparativo"]  # a DFP de 2021 já tinha sido entregue
    texto = json.dumps(inv, ensure_ascii=False).lower()
    assert "fraude" not in texto and "fraud" not in texto and "suspeit" not in texto and "suspect" not in texto
    pdf = pdf_investigacao.gerar(inv)
    assert pdf == pdf_investigacao.gerar(json.loads(json.dumps(inv)))  # o PDF sai só do JSON, sempre igual
    assert pdf.startswith(b"%PDF-1.4")


@pytest.mark.parametrize("nome", exemplos.NOMES)
def test_pdf_do_exemplo_regenerado_do_json(nome: str) -> None:
    inv = json.loads((exemplos.PASTA / f"{nome}.json").read_text(encoding="utf-8"))
    assert (exemplos.PASTA / f"{nome}.pdf").read_bytes() == pdf_investigacao.gerar(inv)
    assert inv["aviso"] == investigacao.AVISO[inv["idioma"]]


@pytest.mark.skipif(not (armazem.PASTA / "manifesto.json").exists(), reason="precisa de data/armazem (fora do git)")
@pytest.mark.parametrize("lang", ["pt", "en"])
def test_exemplo_da_americanas_regenerado_igual_ao_guardado(lang: str) -> None:
    guardado = json.loads((exemplos.PASTA / f"{exemplos.nome(lang)}.json").read_text(encoding="utf-8"))
    novo = exemplos.gerar(lang, gerado_em=guardado["gerado_em"])
    assert novo == guardado


def test_exemplos_existem_nas_duas_linguas() -> None:
    for lang in ("pt", "en"):
        for ext in ("json", "pdf"):
            assert (exemplos.PASTA / f"{exemplos.nome(lang)}.{ext}").exists()
    assert Path(exemplos.PASTA).name == "exemplos"
