"""Investigação (Fase C2, segunda parte): o JSON do contrato, o PDF gerado dele e o exemplo guardado da Americanas."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd
import pytest

from chiocca.cvm import Fontes
from chiocca.v2 import armazem, comparativo, exemplos, investigacao, limites, pdf_investigacao
from tests.test_base import mundo  # noqa: F401  (fixture)
from tests.test_v2_armazem import mundo_c1  # noqa: F401  (fixture)

CAMPOS = {"empresa", "data_referencia", "idioma", "exercicios", "achados", "mudancas", "o_que_se_sabia",
          "qualidade_dos_dados", "parecer_e_auditor", "como_o_motor_foi_testado", "limites", "limitacoes", "evidencias",
          "motor", "informacao_de_hoje", "gerado_em", "aviso"}  # fmt: skip


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
def test_rodizio_e_trocas_de_auditor_no_exemplo(lang: str) -> None:
    inv = json.loads((exemplos.PASTA / f"{exemplos.nome(lang, '2024-12-31')}.json").read_text(encoding="utf-8"))
    pa = inv["parecer_e_auditor"]
    assert pa["rodizio"]["nota"] == investigacao._m(investigacao.RODIZIO, lang)
    assert pa["rodizio"]["norma"] == "Resolução CVM nº 23/2021, arts. 31 e 31-A"
    trocas = [(x["ano_fca"], x["codigo_de"], x["codigo_para"], x["transicao_fca"]) for x in pa["trocas_de_auditor"]]
    assert trocas == [
        (2011, "004715", "002879", 2011),
        (2016, "002879", "004189", None),
        (2019, "004189", "002879", None),
        (2023, "002879", "010324", None),
    ]  # uma linha por troca real
    nomes: dict[str, set[str]] = {}
    for f in pa["auditores_no_fca"]:
        for a in f["auditores"]:
            nomes.setdefault(a["codigo_cvm"], set()).add(a["auditor"])
    assert all(len(v) == 1 for v in nomes.values())  # um nome canônico por código, sem variantes de grafia
    exibidos = {n for v in nomes.values() for n in v} | {
        x[k] for x in pa["trocas_de_auditor"] for k in ("de", "para") if x[k]
    }
    assert not any(n.isupper() for n in exibidos)  # capitalização normal, só para exibição (pedido de 09/11/2026)
    assert "PricewaterhouseCoopers Auditores Independentes" in exibidos and "KPMG Auditores Independentes" in exibidos
    s = {x["ano_fca"]: x["saida"] for x in pa["trocas_de_auditor"]}
    assert s[2016]["exercicios_consecutivos"] == 5 and s[2016]["compativel_com_rodizio"]  # PwC 2011 a 2015
    assert s[2016]["norma"] == "Instrução CVM nº 308/1999"  # vigente em 2016
    assert s[2019]["exercicios_consecutivos"] == 3 and not s[2019]["compativel_com_rodizio"]
    texto = json.dumps(pa, ensure_ascii=False).lower()
    assert "alerta" not in texto.replace("não alerta", "").replace("gera_alerta", "")
    assert "alert" not in texto.replace("not an alert", "").replace("gera_alerta", "").replace("não alerta", "")
    pdf = pdf_investigacao.linhas(inv)
    transicao = {"pt": "(transição: duas firmas no FCA de 2011)", "en": "(transition: two firms in the 2011 FCA)"}[lang]
    assert sum(transicao in x for x in pdf) == 1


def _fca(ano: int, *firmas: tuple[str, str | None, str | None]) -> dict[str, Any]:
    return {"ano_fca": ano, "dt_receb": f"{ano}-05-01",
            "auditores": [{"auditor": f"firma {c}", "codigo_cvm": c, "pessoa_fisica": False, "inicio": i, "fim": f}
                          for c, i, f in firmas]}  # fmt: skip


def test_trocas_e_prazo_do_rodizio() -> None:
    dez = investigacao._trocas([_fca(2021, ("1", "2012-01-01", None)), _fca(2022, ("2", "2022-01-01", None))], "pt")
    assert [(x["de"], x["para"], x["transicao_fca"]) for x in dez] == [("firma 1", "firma 2", None)]
    assert (dez[0]["saida"]["exercicios_consecutivos"], dez[0]["saida"]["artigo"]) == (10, "art. 31-A")
    assert dez[0]["saida"]["norma"] == "Resolução CVM nº 23/2021"  # a firma nova começou depois de 01/04/2021
    seis = investigacao._trocas([_fca(2017, ("1", "2012-01-01", None)), _fca(2018, ("2", "2018-06-01", None))], "en")
    assert (seis[0]["saida"]["exercicios_consecutivos"], seis[0]["saida"]["compativel_com_rodizio"]) == (6, False)
    sem = investigacao._trocas([_fca(2017, ("1", None, None)), _fca(2018, ("2", "2018-06-01", None))], "pt")
    assert sem[0]["saida"]["exercicios_consecutivos"] is None and "não traz" in sem[0]["saida"]["nota"]
    # Transição: a nova aparece ao lado da que sai (fim em 26/08/2011: o último exercício da que sai é 2010).
    tr = investigacao._trocas([_fca(2010, ("1", "2009-04-02", None)), _fca(2011, ("1", "2009-04-02", "2011-08-26"),
                               ("2", "2011-08-27", None)), _fca(2012, ("2", "2011-08-27", None))], "pt")  # fmt: skip
    assert [(x["ano_fca"], x["codigo_de"], x["codigo_para"], x["transicao_fca"]) for x in tr] == [
        (2011, "1", "2", 2011)
    ]
    assert (tr[0]["saida"]["primeiro_exercicio"], tr[0]["saida"]["ultimo_exercicio"]) == (2009, 2010)
    # Firma acrescentada e depois retirada (auditoria conjunta): entrada e saída sem par, cada uma numa linha.
    conj = investigacao._trocas([_fca(2015, ("1", "2015-01-01", None)), _fca(2016, ("1", "2015-01-01", None),
                                 ("2", "2016-01-01", None)), _fca(2017, ("1", "2015-01-01", None)),
                                 _fca(2018, ("1", "2015-01-01", None))], "pt")  # fmt: skip
    assert [(x["ano_fca"], x["de"], x["para"]) for x in conj] == [(2016, None, "firma 2"), (2017, "firma 2", None)]


def test_auditor_pessoa_fisica_sem_nome() -> None:
    linha = pd.Series(
        {"auditor": None, "codigo_cvm_auditor": "999", "pessoa_fisica": True, "inicio": None, "fim": None}
    )
    x = investigacao._auditor(type("L", (), linha.to_dict())(), {"999": "nome de alguém"}, investigacao.TEXTOS["pt"])
    assert x["auditor"] == "auditor pessoa física (nome omitido)" and x["pessoa_fisica"]


@pytest.mark.parametrize("nome", exemplos.NOMES)
def test_acabamento_da_investigacao(nome: str) -> None:
    """Pedidos de 09/11/2026: faixa de Tukey, informação de hoje fora da empresa, unidades, maiúsculas e componentes."""
    inv = json.loads((exemplos.PASTA / f"{nome}.json").read_text(encoding="utf-8"))
    lang = inv["idioma"]
    assert "situacao_cadastro_atual" not in inv["empresa"]
    assert inv["informacao_de_hoje"]["titulo"] == investigacao.TEXTOS[lang]["hoje_titulo"]
    unidades = {a["sinal"]: a["unidade"] for lista in inv["achados"].values() for a in lista}
    assert unidades["dpo"] == ("dias" if lang == "pt" else "days") and unidades["juro"] == "p.p."
    assert unidades["DSRI"] == unidades["altman_z2"] == ("índice" if lang == "pt" else "index")
    for a in inv["achados"]["possivel_manipulacao"]:
        assert a["rotulo"][:1].isupper()
        if a["sinal"] in investigacao.COEFICIENTES:
            assert a["componente_de"] == "mscore" and a["regra"] == investigacao.TEXTOS[lang]["regra_componente"]
        itens = a["limitacoes"] + a["explicacoes_alternativas"]
        assert all(x[:1] == x[:1].upper() for x in itens)
    assert all(x[:1] == x[:1].upper() for x in inv["limitacoes"] + inv["exercicios"][0]["notas"])
    linhas = pdf_investigacao.linhas(inv)
    texto = "\n".join(linhas)
    assert "cerca" not in texto.lower() and "fence" not in texto.lower()
    assert ("faixa de Tukey (1,5 × IQR): de " if lang == "pt" else "Tukey range (1.5 × IQR): from ") in texto
    assert texto.count(investigacao.TEXTOS[lang]["regra_componente"]) == len(investigacao.COEFICIENTES)
    assert all(x.lstrip()[2:3] == x.lstrip()[2:3].upper() for x in linhas if x.lstrip().startswith("- "))
    titulo = f"# {inv['informacao_de_hoje']['titulo']}"
    assert titulo in linhas and linhas.index(titulo) > linhas.index(pdf_investigacao.T[lang]["motor"])
    assert (" dias" if lang == "pt" else " days") in texto and " p.p." in texto


@pytest.mark.skipif(not (armazem.PASTA / "manifesto.json").exists(), reason="precisa de data/armazem (fora do git)")
def test_ponta_a_ponta_com_empresa_fora_do_gabarito(tmp_path: Path) -> None:
    """Plano da Fase C: teste de ponta a ponta com uma empresa sem nenhum caso no gabarito (nem em observação).

    A empresa é escolhida por regra, não por nome: a de menor código CVM, não financeira, com a DFP de 2021 em
    situação ok em 30/04/2022. O resultado não é publicado em docs/ (fica só no diretório temporário do teste)."""
    from chiocca.v2 import modelos
    from chiocca.v2.na_data import _meta

    raiz = Path(armazem.__file__).parents[2]
    fora = set(pd.read_csv(raiz / "data" / "gabarito_casos.csv", dtype=str).cd_cvm.dropna())
    fora |= set(pd.read_csv(raiz / "data" / "casos_em_observacao.csv", dtype=str).cd_cvm.dropna())
    fa = armazem.FontesArmazem()
    d = "2022-04-30"
    candidatos = fa.consulta(
        "SELECT DISTINCT cd_cvm FROM versoes WHERE exercicio = 2021 AND CAST(dt_receb AS DATE) <= ?", [d]
    ).cd_cvm
    escolhida = None
    for cd in sorted((str(c) for c in candidatos if str(c) not in fora), key=int):
        meta, _ = _meta(fa, 2021, pd.Timestamp(d).date(), so={cd})
        if not meta.empty and (meta.status == "ok").any() and (meta.grupo == "nao_financeira").any():
            escolhida = cd
            break
    assert escolhida is not None and escolhida not in fora
    for lang in ("pt", "en"):
        inv = investigacao.gerar(fa, escolhida, 2021, d, lang)
        modelos.Investigacao.model_validate(inv)  # o contrato vale para qualquer empresa, não só para os casos
        assert inv["aviso"] == investigacao.AVISO[lang] and inv["exercicios"][0]["situacao"] == "ok"
        assert len(inv["achados"]["possivel_manipulacao"]) > 1 and inv["achados"]["risco_financeiro"]
        assert all(a["unidade"] for lista in inv["achados"].values() for a in lista)
        texto = json.dumps(inv, ensure_ascii=False).lower()
        assert "fraude" not in texto and "fraud" not in texto and "suspeit" not in texto
        pdf = pdf_investigacao.gerar(inv)
        assert pdf.startswith(b"%PDF-1.4") and pdf.count(investigacao.AVISO[lang].encode("latin-1")[:20]) > 0
        (tmp_path / f"investigacao_{lang}.pdf").write_bytes(pdf)  # nada vai para docs/
    assert not list((raiz / "docs" / "exemplos").glob(f"*{escolhida}*"))


def test_capitalizacao_dos_nomes_de_firmas() -> None:
    from chiocca.v2.armazem import capitalizacao

    assert (
        capitalizacao("BDO RCS AUDITORES INDEPENDENTES - SOCIEDADE SIMPLES")
        == "BDO RCS Auditores Independentes - Sociedade Simples"
    )
    assert capitalizacao("ERNST & YOUNG AUDITORES INDEPENDENTES S.S.") == "Ernst & Young Auditores Independentes S.S."
    assert capitalizacao("KPMG AUDITORES INDEPENDENTES LTDA") == "KPMG Auditores Independentes Ltda."
    assert (
        capitalizacao("GRANT THORNTON AUDITORES INDEPENDENTES DO BRASIL")
        == "Grant Thornton Auditores Independentes do Brasil"
    )
