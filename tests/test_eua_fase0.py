"""Fase 0 dos EUA (pedido de 23/11/2026, parte 3): só inventário e contagens.

- Os documentos PT e EN saem do JSON versionado; os números do JSON são coerentes entre si e com o limite (nada de 2024
  em diante).
- O manifesto de SHA-256 bate com o JSON (e com a roda do era-py, quando ela está no ambiente).
- O User-Agent da SEC vem só da variável de ambiente: sem ela, nada é baixado; nenhum arquivo versionado traz um
  endereço de e-mail pessoal.
- O produto e o README não tocam a frente dos EUA; nenhuma descrição de AAER (com nomes de pessoas) entra no JSON.
- O inventário dos Financial Statement Data Sets roda num arquivo sintético no formato da SEC.
"""

from __future__ import annotations

import json
import re
import subprocess
import zipfile
from pathlib import Path
from typing import Any

import pandas as pd
import pytest

from chiocca.base import RAIZ
from chiocca.eua import fase0, fsds, rotulos, sec

D = json.loads(fase0.SAIDA.read_text(encoding="utf-8"))


@pytest.mark.parametrize("lang", ["pt", "en"])
def test_documento_igual_a_saida_do_script(lang: str) -> None:
    assert fase0.DOCS[lang].read_text(encoding="utf-8") == fase0.render(D, lang)


def test_numeros_coerentes_e_dentro_do_limite() -> None:
    r, b = D["rotulos"], D["rotulos"]["bao_et_al"]
    assert D["limite"] == {"ultimo_ano": 2023, "trimestres_fsds": ["2009q1", "2023q4"]}
    assert fsds.TRIMESTRES[-1] == "2023q4" and len(fsds.TRIMESTRES) == D["acesso_sec"]["fsds_previstos"]
    idx = r["indice_sec"]
    assert idx["ultimo_ano"] <= 2023 and max(int(a) for a in idx["por_ano"]) <= 2023
    assert sum(idx["por_ano"].values()) == idx["aaers"] >= idx["numeros_distintos"]
    assert sum(b["empresa_anos_xbrl_por_ano"].values()) == b["empresa_anos_xbrl"]
    assert sum(b["empresa_anos_xbrl_ligadas_por_ano"].values()) == b["empresa_anos_xbrl_ligadas_ao_cik"]
    assert all(b["empresa_anos_xbrl_ligadas_por_ano"][a] <= n for a, n in b["empresa_anos_xbrl_por_ano"].items())
    assert min(int(a) for a in b["empresa_anos_xbrl_por_ano"]) >= rotulos.PRIMEIRO_ANO_XBRL
    assert b["empresa_anos_xbrl"] <= b["empresa_anos"] and b["ultimo_ano_afetado"] <= 2023
    assert r["pacote"]["licenca"] == "MIT" and r["pacote"]["versao"] == rotulos.VERSAO


def test_manifesto_bate_com_o_json() -> None:
    linhas = {x["arquivo"]: x for x in sec.le_manifesto()}
    era = linhas[D["era_py"]["arquivo"]]
    assert era["sha256"] == D["era_py"]["sha256"] and int(era["bytes"]) == D["era_py"]["bytes"]
    assert list(linhas) == sorted(linhas) and all(re.fullmatch(r"[0-9a-f]{64}", x["sha256"]) for x in linhas.values())
    if rotulos.RODA.exists():
        assert sec.sha256(rotulos.RODA) == era["sha256"]


def test_sem_descricao_de_aaer_nem_nome_no_json() -> None:
    texto = fase0.SAIDA.read_text(encoding="utf-8")
    assert "aaer_desc" not in texto and "descri" not in texto.lower()


def test_user_agent_so_da_variavel(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv(sec.VARIAVEL, raising=False)
    with pytest.raises(sec.SemUserAgent):
        sec.agente()
    with pytest.raises(sec.SemUserAgent):
        fsds.baixar(sec.Cliente(), ["2010q1"])
    monkeypatch.setenv(sec.VARIAVEL, "Nome sem contato")
    with pytest.raises(sec.SemUserAgent):
        sec.agente()
    monkeypatch.setenv(sec.VARIAVEL, "Projeto Exemplo contato@exemplo.org")
    cliente = sec.Cliente()
    assert "exemplo" not in repr(cliente) and sec.INTERVALO >= 0.1  # no máximo 10 pedidos por segundo


def test_nenhum_arquivo_versionado_com_email_pessoal() -> None:
    arquivos = subprocess.run(["git", "ls-files"], cwd=RAIZ, capture_output=True, text=True, check=True).stdout.split()
    padrao = re.compile(r"[\w.+-]+@(gmail|hotmail|outlook|yahoo)\.com")
    for a in arquivos:
        p = RAIZ / a
        if p.suffix in {".png", ".pdf", ".zip", ".gz", ".ots", ".parquet", ".whl"} or not p.is_file():
            continue
        assert not padrao.search(p.read_text(encoding="utf-8", errors="ignore")), a


def test_fora_do_produto_e_do_readme() -> None:
    importa = re.compile(r"chiocca\.eua(?![\w])|from chiocca import [^\n]*\beua\b")
    for p in sorted((RAIZ / "chiocca").rglob("*.py")):
        caminho = p.relative_to(RAIZ).as_posix()
        if not caminho.startswith("chiocca/eua/"):
            assert not importa.search(p.read_text(encoding="utf-8")), caminho
    for readme in ("README.md", "README.en.md"):
        texto = (RAIZ / readme).read_text(encoding="utf-8")
        assert "eua-fase-0" not in texto and "us-phase-0" not in texto and "AAER" not in texto
        assert "pre-registro-eua" not in texto and "us-preregistration" not in texto


def test_nada_de_2024_em_diante() -> None:
    class Falso:
        def baixar(self, url: str, destino: Path) -> dict[str, Any]:
            raise AssertionError("não devia baixar")

    with pytest.raises(ValueError, match="2024"):
        fsds.baixar(Falso(), ["2024q1"])  # type: ignore[arg-type]


# ---- inventário dos Financial Statement Data Sets, num arquivo sintético ----

SUB = (
    "adsh\tcik\tname\tsic\tform\tperiod\tfy\tfp\tfiled\tprevrpt\n"
    "0001\t100\tALFA CORP\t2834\t10-K\t20201231\t2020\tFY\t20210301\t1\n"
    "0002\t200\tBETA INC\t6770\t10-K\t20201231\t2020\tFY\t20210315\t0\n"
    "0003\t100\tALFA CORP\t2834\t10-K/A\t20201231\t2020\tFY\t20210601\t0\n"
    "0004\t300\tGAMA CO\t\t10-Q\t20210331\t2021\tQ1\t20210510\t0\n"
)
NUM = (
    "adsh\ttag\tversion\tcoreg\tddate\tqtrs\tuom\tvalue\tfootnote\n"
    "0001\tAssets\tus-gaap/2020\t\t20201231\t0\tUSD\t1000\t\n"
    "0001\tRevenues\tus-gaap/2020\t\t20201231\t4\tUSD\t500\t\n"
    "0001\tAssets\tus-gaap/2020\t\t20191231\t0\tUSD\t900\t\n"
    "0002\tAssets\tus-gaap/2020\tSUB\t20201231\t0\tUSD\t50\t\n"
    "0002\tSalesRevenueNet\tus-gaap/2020\t\t20201231\t4\tUSD\t70\t\n"
    "0002\tAssets\tus-gaap/2020\t\t20201231\t0\tEUR\t60\t\n"
    "0003\tAssets\tus-gaap/2020\t\t20201231\t0\tUSD\t1100\t\n"
    "0004\tAssets\tus-gaap/2020\t\t20210331\t0\tUSD\t10\t\n"
)


def _zip(tmp_path: Path, sub: str = SUB) -> Path:
    z = tmp_path / "2021q1.zip"
    with zipfile.ZipFile(z, "w") as f:
        f.writestr("sub.txt", sub)
        f.writestr("num.txt", NUM)
        f.writestr("readme.htm", "<html></html>")
    return z


def test_estrutura_e_submissoes(tmp_path: Path) -> None:
    z = _zip(tmp_path)
    e = fsds.estrutura(z)
    assert e["sub.txt"]["linhas"] == 4 and e["num.txt"]["linhas"] == 8 and e["sub.txt"]["colunas"][0] == "adsh"
    assert "readme.htm" in e and "colunas" not in e["readme.htm"]
    s = fsds.submissoes(z)
    assert sorted(s.form) == ["10-K", "10-K", "10-K/A"] and set(s.trimestre) == {"2021q1"}
    r = fsds.resumo(s)
    assert r == {"2020": {"companhias_com_10k": 2, "entregas_10k": 2, "entregas_10k_a": 1, "10k_emendados_depois": 1,
                          "prazo_mediano_dias": 67.0, "prazo_p10_dias": 61.4, "prazo_p90_dias": 72.6,
                          "ate_90_dias": 1.0}}  # fmt: skip


def test_cobertura_das_tags_so_da_companhia_em_dolar_na_data(tmp_path: Path) -> None:
    z = _zip(tmp_path)
    t = fsds.cobertura_tags(z, fsds.submissoes(z)).set_index("adsh")
    assert list(t.index) == ["0001", "0002"]  # só os 10-K originais
    assert bool(t.at["0001", "Assets"]) and bool(t.at["0001", "Revenues"])
    assert not bool(t.at["0002", "Assets"])  # co-registrante e outra moeda não contam
    assert bool(t.at["0002", "SalesRevenueNet"])
    c = fsds.cobertura_por_ano(t.reset_index())["2020"]
    assert c["10k"] == 2 and c["contas"]["ativo_total"] == 0.5 and c["contas"]["receita_liquida"] == 1.0
    assert c["tags"]["Revenues"] == 0.5


def test_coluna_ausente_e_recusada(tmp_path: Path) -> None:
    z = _zip(tmp_path, SUB.replace("prevrpt", "outra"))
    with pytest.raises(fsds.ColunaAusente, match="prevrpt"):
        fsds.submissoes(z)


def test_anos_afetados_e_ligacao_ao_cik() -> None:
    from datetime import date

    f = pd.DataFrame({"p_aaer": ["1", "2"], "gvkey": ["A", "B"], "min_year": [2009, 2012], "max_year": [2010, 2012]})
    fy = rotulos.anos_afetados(f)
    assert fy.values.tolist() == [["A", 2009], ["A", 2010], ["B", 2012]]
    ligacoes = pd.DataFrame({"gvkey": ["A", "B"], "cik": [1, 2], "first_date": [date(2010, 3, 1), date(2013, 1, 1)],
                             "last_date": [date(2020, 1, 1), date(2020, 1, 1)]})  # fmt: skip
    assert rotulos.ligadas_ao_cik(fy, ligacoes).tolist() == [False, True, False]


# ---- 8-K com o item 4.02, num submissions.zip sintético ----


def _submissions(tmp_path: Path) -> Path:
    def bloco(linhas: list[tuple[str, str, str, str]]) -> dict[str, list[str]]:
        return {"accessionNumber": [x[0] for x in linhas], "filingDate": [x[1] for x in linhas],
                "form": [x[2] for x in linhas], "items": [x[3] for x in linhas]}  # fmt: skip

    z = tmp_path / "submissions.zip"
    with zipfile.ZipFile(z, "w") as f:
        f.writestr("CIK0000000100.json", json.dumps({"cik": "100", "filings": {"recent": bloco([
            ("a1", "2012-03-01", "8-K", "4.02,9.01"),
            ("a2", "2012-05-01", "8-K/A", "4.02"),
            ("a3", "2011-03-01", "10-K", ""),
            ("a4", "2024-02-01", "8-K", "4.02"),  # depois de 2023: fora
            ("a5", "2012-06-01", "10-K/A", ""),
        ])}}))  # fmt: skip
        f.writestr("CIK0000000100-submissions-001.json", json.dumps(bloco([
            ("a0", "2010-01-05", "8-K", "4.02"),
            ("b0", "2010-02-05", "8-K", "2.02,4.021"),  # não é 4.02
        ])))  # fmt: skip
        f.writestr("CIK0000000200.json", json.dumps({"cik": "200", "filings": {"recent": bloco([
            ("c1", "2012-07-01", "8-K", " 4.02"),
            ("c2", "2012-08-01", "8-K", "4.02"),
        ])}}))  # fmt: skip
    return z


def test_8k_402_por_ano(tmp_path: Path) -> None:
    from chiocca.eua import itens

    assert itens.tem_item("4.02,9.01") and itens.tem_item(" 4.02") and not itens.tem_item("4.021,2.02")
    linhas = list(itens.entregas(_submissions(tmp_path)))
    assert {x["adsh"] for x in linhas} == {"a0", "a1", "a2", "a3", "a5", "b0", "c1", "c2"}
    c = itens.contagens(linhas, {100: "20110301"}, sic_6770={200})
    assert c["2010"]["8k_402"] == 1 and c["2010"]["companhias_com_10k_fsds_antes"] == 0
    assert c["2012"] == {"8k_402": 3, "8k_a_402": 1, "companhias_8k_402": 2, "companhias_8k_402_sic_6770": 1,
                         "companhias_novas_8k_402": 1,
                         "companhias_com_10k_fsds": 1, "companhias_com_10k_fsds_antes": 1, "10k_edgar": 0,
                         "10k_a_edgar": 1}  # fmt: skip
    assert c["2011"]["10k_edgar"] == 1 and "2024" not in c


def test_versao_publica_e_aaers_com_10k(tmp_path: Path) -> None:
    z = _zip(tmp_path)
    s = fsds.submissoes(z)
    assert list(s.ano) == [2020, 2020, 2020]
    v = fsds.versao_publica(s, {"0003"}, "20210701").set_index("cik")
    assert v.at["100", "form"] == "10-K/A" and v.at["200", "form"] == "10-K"
    assert fsds.versao_publica(s, set(), "20210701").set_index("cik").at["100", "form"] == "10-K"  # emenda sem números
    assert fsds.versao_publica(s, {"0003"}, "20210305").cik.tolist() == ["100"]
    t = fsds.cobertura_tags(z, s, formularios=("10-K", "10-K/A"))
    assert sorted(t.form) == ["10-K", "10-K", "10-K/A"] and fsds.cobertura_por_ano(t)["2020"]["10k"] == 2
    from datetime import date

    f = pd.DataFrame({"p_aaer": ["1", "2"], "gvkey": ["A", "B"], "min_year": [2008, 2012], "max_year": [2010, 2012]})
    ligacoes = pd.DataFrame({"gvkey": ["A", "B"], "cik": [1, 2], "first_date": [date(2000, 1, 1)] * 2,
                             "last_date": [date(2020, 1, 1)] * 2})  # fmt: skip
    r = rotulos.com_10k(f, ligacoes, {(1, 2010), (1, 2008)})
    assert r["empresa_anos_com_10k_por_ano"] == {"2009": 0, "2010": 1, "2012": 0}
    assert r["casos_com_10k"] == 1 and r["casos_com_10k_por_primeiro_ano"] == {"2010": 1}


def test_numeros_da_sec_coerentes_e_dentro_do_limite() -> None:
    f = D["fsds"]
    assert f is not None and D["acesso_sec"]["fsds_baixados"] == D["acesso_sec"]["fsds_previstos"] == 60
    assert f["trimestres_baixados"] == 60 and f["trimestres_sem_entregas"] == ["2009q1"]
    for chave in ("por_exercicio", "versoes", "cobertura", "companhias_com_10k_por_ano_compustat"):
        assert all(2009 <= int(a) <= 2023 for a in f[chave]), chave
    assert all(2009 <= int(a) <= 2023 for a in f["itens_8k"]) and all(2009 <= int(a) <= 2023 for a in f["por_entrega"])
    for a, x in f["itens_8k"].items():
        assert x["companhias_com_10k_fsds_antes"] <= x["companhias_com_10k_fsds"] <= x["companhias_8k_402"]
        assert x["companhias_8k_402"] <= x["8k_402"] and x["companhias_novas_8k_402"] <= x["companhias_8k_402"]
        assert x["companhias_8k_402_sic_6770"] <= x["companhias_8k_402"]
        assert f["por_entrega"][a]["10k_a"] <= x["10k_a_edgar"]  # os 10-K/A com XBRL estão entre os do EDGAR
    for a, x in f["por_exercicio"].items():
        assert x["entregas_10k_a_com_numeros"] <= x["entregas_10k_a"] and x["companhias_com_10k"] <= x["entregas_10k"]
        assert x["prazo_p10_dias"] <= x["prazo_mediano_dias"] <= x["prazo_p90_dias"]
    for a, v in f["versoes"].items():
        assert all(k["emenda"] <= k["companhias"] for k in v.values()) and all(int(a) + int(k[2]) <= 2023 for k in v)
    for a, c in f["cobertura"].items():
        assert set(c["contas"]) == set(fsds.MAPA) and all(
            0 <= x <= 1 for x in [*c["contas"].values(), *c["tags"].values()]
        )
    for a, x in f["exclusoes_10k"].items():  # decisões de 24/11/2026: só contagens
        assert 2009 <= int(a) <= 2023 and x["10k"] == f["por_exercicio"][a]["entregas_10k"]
        assert x["sic_6770_sem_receita"] <= min(x["sic_6770"], x["sem_receita"]) and x["sem_receita"] <= x["10k"]
        assert x["sem_receita_financeiras"] <= x["sem_receita"]
    for a, x in f["itens_8k"].items():
        assert x["antes_sic_6770_sem_receita"] <= min(x["antes_sic_6770"], x["antes_sem_receita"])
        assert x["antes_restantes"] == x["companhias_com_10k_fsds_antes"] - x["antes_sem_receita"] - (
            x["antes_sic_6770"] - x["antes_sic_6770_sem_receita"]
        )
    aa, b = f["aaer"], D["rotulos"]["bao_et_al"]
    assert sum(aa["empresa_anos_com_10k_por_ano"].values()) == aa["empresa_anos_com_10k"]
    assert all(aa["empresa_anos_com_10k_por_ano"][a] <= n for a, n in b["empresa_anos_xbrl_ligadas_por_ano"].items())
    assert sum(aa["casos_com_10k_por_primeiro_ano"].values()) == aa["casos_com_10k"] <= aa["empresa_anos_com_10k"]


def test_manifesto_tem_os_arquivos_da_sec() -> None:
    linhas = {x["arquivo"]: x for x in sec.le_manifesto()}
    assert all(f"fsds/{t}.zip" in linhas for t in fsds.TRIMESTRES) and "edgar/submissions.zip" in linhas
    ed = D["acesso_sec"]["edgar_submissions"]
    assert ed["sha256"] == linhas["edgar/submissions.zip"]["sha256"]
    assert D["acesso_sec"]["fsds_bytes"] == sum(int(linhas[f"fsds/{t}.zip"]["bytes"]) for t in fsds.TRIMESTRES)


def test_receita_e_regra_das_sem_receita(tmp_path: Path) -> None:
    z = _zip(tmp_path)
    t = fsds.cobertura_tags(z, fsds.submissoes(z), formularios=("10-K", "10-K/A")).set_index("adsh")
    assert t.at["0001", "receita"] == 500.0 and t.at["0002", "receita"] == 70.0  # anual (quatro trimestres)
    assert pd.isna(t.at["0003", "receita"])  # a emenda só traz o ativo
    assert fsds.sem_receita(pd.Series([None, 0.0, 10.0])).tolist() == [True, True, False]


def test_exclusoes_dos_8k_pelo_ultimo_10k_antes() -> None:
    from chiocca.eua import itens

    linhas = [
        {"cik": 1, "adsh": "x1", "data": "2021-05-01", "form": "8-K", "itens": "4.02"},
        {"cik": 1, "adsh": "x2", "data": "2021-09-01", "form": "8-K", "itens": "4.02"},
        {"cik": 2, "adsh": "y1", "data": "2021-06-01", "form": "8-K", "itens": "4.02"},
        {"cik": 3, "adsh": "z1", "data": "2021-07-01", "form": "8-K", "itens": "4.02"},
        {"cik": 4, "adsh": "w1", "data": "2021-02-01", "form": "8-K", "itens": "4.02"},  # antes do 1º 10-K dela
        {"cik": 4, "adsh": "w2", "data": "2021-10-01", "form": "8-K", "itens": "4.02"},  # depois: este conta
    ]
    historico = {
        1: [("20200301", False, True), ("20210801", True, True)],  # SPAC; o 10-K de agosto vem depois do 1º 8-K
        2: [("20210301", True, False)],  # sem receita
        3: [("20210301", False, False)],  # fica
        4: [("20210301", False, False)],  # fica, pelo 8-K de outubro
    }
    primeiros = {1: "20200301", 2: "20210301", 3: "20210301", 4: "20210301"}
    c = itens.contagens(linhas, primeiros, {1}, historico)["2021"]
    assert c["companhias_com_10k_fsds_antes"] == 4
    assert (c["antes_sem_receita"], c["antes_sic_6770"], c["antes_sic_6770_sem_receita"], c["antes_restantes"]) == (
        1, 1, 0, 2,
    )  # fmt: skip


# ---- rascunho do pré-registro dos EUA (pedido de 24/11/2026, item 4) ----


@pytest.mark.parametrize("lang", ["pt", "en"])
def test_rascunho_igual_a_saida_do_script(lang: str) -> None:
    from chiocca.eua import rascunho

    texto = rascunho.DOCS[lang].read_text(encoding="utf-8")
    assert texto == rascunho.render(D, lang)
    assert ("Rascunho, não é registro" if lang == "pt" else "Draft, not a registration") in texto
    assert not re.search(r"[\w.+-]+@[\w-]+\.[\w.]+", texto)  # nenhum e-mail
    for proibido in ("fraude comprovada", "proven fraud", "recomendação de compra", "buy recommendation"):
        assert proibido not in texto.lower(), proibido


def test_rascunho_antes_de_qualquer_sinal_americano() -> None:
    """Nenhum módulo da frente dos EUA importa as funções de sinal ou o motor antes do registro."""
    for p in sorted((RAIZ / "chiocca" / "eua").glob("*.py")):
        texto = p.read_text(encoding="utf-8")
        assert not re.search(r"chiocca\.sinais|chiocca\.v2\.motor_v2|from chiocca import sinais", texto), p.name
