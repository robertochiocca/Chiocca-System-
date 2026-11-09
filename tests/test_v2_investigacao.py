"""Investigação (Fase C2, segunda parte): o JSON do contrato, o PDF gerado dele e o exemplo guardado da Americanas."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from chiocca.cvm import Fontes
from chiocca.v2 import armazem, comparativo, exemplos, investigacao, limites, pdf_investigacao
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
@pytest.mark.parametrize("data,lang", exemplos.PARES)
def test_exemplo_da_americanas_regenerado_igual_ao_guardado(data: str, lang: str) -> None:
    guardado = json.loads((exemplos.PASTA / f"{exemplos.nome(lang, data)}.json").read_text(encoding="utf-8"))
    novo = exemplos.gerar(lang, gerado_em=guardado["gerado_em"], data=data)
    assert novo == guardado


def test_exemplos_existem_nas_duas_linguas() -> None:
    assert exemplos.DATAS == ("2022-04-30", "2024-12-31")
    for data, lang in exemplos.PARES:
        for ext in ("json", "pdf"):
            assert (exemplos.PASTA / f"{exemplos.nome(lang, data)}.{ext}").exists()
    assert Path(exemplos.PASTA).name == "exemplos"


@pytest.mark.parametrize("lang", ["pt", "en"])
def test_segundo_exemplo_mostra_o_comparativo_de_2022_como_evidencia_destacada(lang: str) -> None:
    inv = json.loads((exemplos.PASTA / f"{exemplos.nome(lang, '2024-12-31')}.json").read_text(encoding="utf-8"))
    mud = inv["mudancas"]
    dest = mud["comparativo_destacadas"]
    assert dest and all(x["grupo"] == "a" and x["destacada"] for x in dest)
    assert all(abs(x["diferenca"]) > mud["materialidade_comparativo"]["limite"] for x in dest)
    assert {x["dt_receb_seguinte"] for x in dest} == {"2023-11-16"}  # a DFP de 2022
    texto = comparativo.TEXTO.pt if lang == "pt" else comparativo.TEXTO.en
    assert {x["texto"] for x in dest} == {texto}
    completa = mud["reapresentacao_pelo_comparativo"]
    assert len(completa) > len(dest) and {x["grupo"] for x in completa} == {"a", "b"}  # o resto fica na lista completa
    pdf = (exemplos.PASTA / f"{exemplos.nome(lang, '2024-12-31')}.pdf").read_bytes()
    assert pdf.count(b"Tj") > 0 and inv["data_referencia"] == "2024-12-31"
    primeiro = json.loads((exemplos.PASTA / f"{exemplos.nome(lang, '2022-04-30')}.json").read_text(encoding="utf-8"))
    assert primeiro["mudancas"]["comparativo_destacadas"] == []  # em 30/04/2022 a DFP de 2022 não existia


@pytest.mark.parametrize("lang", ["pt", "en"])
def test_rodizio_de_auditor_no_exemplo(lang: str) -> None:
    inv = json.loads((exemplos.PASTA / f"{exemplos.nome(lang, '2022-04-30')}.json").read_text(encoding="utf-8"))
    pa = inv["parecer_e_auditor"]
    assert pa["rodizio"]["nota"] == investigacao._m(investigacao.RODIZIO, lang)
    assert pa["rodizio"]["norma"] == "Resolução CVM nº 23/2021, arts. 31 e 31-A"
    saidas = {x["ano_fca"]: x["saidas"][0] for x in pa["trocas_de_auditor"] if x["saidas"]}  # 2011: só entrou
    assert saidas[2016]["exercicios_consecutivos"] == 5 and saidas[2016]["compativel_com_rodizio"]  # PwC 2011 a 2015
    assert saidas[2016]["norma"] == "Instrução CVM nº 308/1999"  # vigente em 2016
    assert saidas[2019]["exercicios_consecutivos"] == 3 and not saidas[2019]["compativel_com_rodizio"]
    texto = json.dumps(pa, ensure_ascii=False).lower()
    assert "alerta" not in texto.replace("não alerta", "").replace("gera_alerta", "")
    assert "alert" not in texto.replace("not an alert", "").replace("gera_alerta", "").replace("não alerta", "")


def test_saidas_do_rodizio() -> None:
    def fca(cod: str, inicio: str | None) -> dict[str, object]:
        return {"auditores": [{"auditor": f"firma {cod}", "codigo_cvm": cod, "inicio": inicio, "fim": None}]}

    dez = investigacao._saidas(fca("1", "2012-01-01"), fca("2", "2022-01-01"), {"1"}, {"2"}, "pt")[0]
    assert (dez["exercicios_consecutivos"], dez["artigo"]) == (10, "art. 31-A")
    assert dez["norma"] == "Resolução CVM nº 23/2021"  # a firma nova começou depois de 01/04/2021
    seis = investigacao._saidas(fca("1", "2012-01-01"), fca("2", "2018-06-01"), {"1"}, {"2"}, "en")[0]
    assert (seis["exercicios_consecutivos"], seis["compativel_com_rodizio"], seis["norma"]) == (6, False, None)
    sem = investigacao._saidas(fca("1", None), fca("2", "2018-06-01"), {"1"}, {"2"}, "pt")[0]
    assert sem["exercicios_consecutivos"] is None and "não traz" in sem["nota"]
    # A firma nova já constava no FCA anterior: conta pela data de fim da que saiu (fim em 26/08/2011: último é 2010).
    a = {"auditores": [{"auditor": "A", "codigo_cvm": "1", "inicio": "2009-04-02", "fim": "2011-08-26"},
                       {"auditor": "B", "codigo_cvm": "2", "inicio": "2011-08-27", "fim": None}]}  # fmt: skip
    ey = investigacao._saidas(a, fca("2", "2011-08-27"), {"1"}, set(), "pt")[0]
    assert (ey["primeiro_exercicio"], ey["ultimo_exercicio"], ey["exercicios_consecutivos"]) == (2009, 2010, 2)
