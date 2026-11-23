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


def test_nada_de_2024_em_diante() -> None:
    class Falso:
        def baixar(self, url: str, destino: Path) -> dict[str, Any]:
            raise AssertionError("não devia baixar")

    with pytest.raises(ValueError, match="2024"):
        fsds.baixar(Falso(), ["2024q1"])  # type: ignore[arg-type]


# ---- inventário dos Financial Statement Data Sets, num arquivo sintético ----

SUB = (
    "adsh\tcik\tname\tform\tperiod\tfy\tfp\tfiled\tprevrpt\n"
    "0001\t100\tALFA CORP\t10-K\t20201231\t2020\tFY\t20210301\t1\n"
    "0002\t200\tBETA INC\t10-K\t20201231\t2020\tFY\t20210315\t0\n"
    "0003\t100\tALFA CORP\t10-K/A\t20201231\t2020\tFY\t20210601\t0\n"
    "0004\t300\tGAMA CO\t10-Q\t20210331\t2021\tQ1\t20210510\t0\n"
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
                          "prazo_mediano_dias": 67.0}}  # fmt: skip


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
