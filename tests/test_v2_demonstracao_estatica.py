"""Demonstração estática (pedido de 10/11/2026): os arquivos pré-gerados são iguais à saída da API para as mesmas
entradas. Com o armazém da fixture (sem rede, roda no CI) e, quando a demonstração real foi gerada localmente, com
uma amostra dela."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pytest
from fastapi.testclient import TestClient

from chiocca import base
from chiocca.cvm import Fontes
from chiocca.v2 import api, armazem, demonstracao, demonstracao_estatica, pdf_investigacao
from chiocca.v2.linhagem import Localizador
from tests.test_base import mundo  # noqa: F401  (fixture)
from tests.test_v2_api import sem_rede  # noqa: F401  (fixture)
from tests.test_v2_armazem import mundo_c1  # noqa: F401  (fixture)

sem_carimbos = demonstracao_estatica._sem_carimbos


def test_plano_com_as_datas_do_caso(mundo_c1: tuple[Fontes, armazem.FontesArmazem]) -> None:  # noqa: F811
    _, arm = mundo_c1
    colunas = ["caso_id", "cd_cvm", "periodo_afetado_inicio", "periodo_afetado_fim"]
    gab = pd.DataFrame([("x", "100", "2021", "2021"), ("y", "200", None, None)], columns=colunas)
    p = demonstracao_estatica.plano(arm, {"100", "200"}, gab)
    # período afetado 2021 e o exercício anterior (2020): as datas de corte de cada um e 31/12/2024
    assert p["100"] == {"2021-04-30": [2020], "2022-04-30": [2020, 2021], "2024-12-31": [2020, 2021]}
    # sem período informado: só 31/12/2024, com o último exercício entregue até lá
    assert list(p["200"]) == ["2024-12-31"] and len(p["200"]["2024-12-31"]) == 1


def _gabarito_da_fixture() -> pd.DataFrame:
    colunas = ["caso_id", "empresa", "cd_cvm", "tipo_evento", "periodo_afetado_inicio", "periodo_afetado_fim",
               "data_publica", "fonte_principal_url"]  # fmt: skip
    gab = pd.DataFrame([("x", "Empresa Cem S.A.", "100", "processo_cvm", "2021", "2021", "2023-01-11",
                         "https://exemplo.org/caso")], columns=colunas)  # fmt: skip
    return gab.assign(cd=gab.cd_cvm)


def test_arquivos_estaticos_iguais_a_saida_da_api(
    mundo_c1: tuple[Fontes, armazem.FontesArmazem],  # noqa: F811
    sem_rede: None,  # noqa: F811
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    _, arm = mundo_c1
    monkeypatch.setattr(api, "empresas_da_demonstracao", lambda: {"100"})
    monkeypatch.setattr(demonstracao, "gabarito", _gabarito_da_fixture)
    demo = tmp_path / "demo"  # o tmp_path também guarda o armazém da fixture
    m = demonstracao_estatica.gerar(demo, fabrica=lambda: arm)
    assert m["arquivos"] == len(list(demo.rglob("*.*")))
    with TestClient(api.criar_app(lambda: arm, modo_demonstracao=True)) as c:
        indice = json.loads((demo / "indice.json").read_text(encoding="utf-8"))
        assert indice == c.get("/api/v1/demonstracao").json()  # o índice é a própria rota da demonstração
        plano = {e["cd_cvm"]: e["datas"] for e in indice["empresas"]}
        assert plano == {"100": {"2021-04-30": [2020], "2022-04-30": [2020, 2021], "2024-12-31": [2020, 2021]}}
        assert m["investigacoes"] == 5
        for data, exs in plano["100"].items():
            for lang in ("pt", "en"):
                q = {"data_referencia": data, "idioma": lang}
                empresa = json.loads((demo / f"empresas/100/{data}/{lang}.json").read_text(encoding="utf-8"))
                assert empresa == c.get("/api/v1/empresas/100", params=q).json()
                for ex in exs:
                    pasta = demo / f"investigacoes/100/{ex}/{data}"
                    arquivo = json.loads((pasta / f"{lang}.json").read_text(encoding="utf-8"))
                    da_api = c.get(f"/api/v1/investigacoes/100/{ex}", params=q).json()
                    assert sem_carimbos(arquivo) == sem_carimbos(da_api)
                    assert (pasta / f"{lang}.pdf").read_bytes() == pdf_investigacao.gerar(arquivo)  # o PDF sai do JSON
        testado = json.loads((demo / "como-o-motor-foi-testado.json").read_text(encoding="utf-8"))
        assert testado == c.get("/api/v1/como-o-motor-foi-testado").json()
    (e,) = indice["empresas"]
    assert e["rotulos_datas"] == {"2021-04-30": "exercicio_anterior", "2022-04-30": "periodo_afetado",
                                  "2024-12-31": "depois_da_revelacao"}  # fmt: skip
    assert e["data_inicial"] == "2022-04-30" and e["casos"][0]["tipo_evento"] == ["processo_cvm"]
    texto = json.dumps(indice)
    assert e["nome_do_caso"] == "Empresa Cem S.A."
    assert indice["ordem"] == "nome_do_caso" and "alerta" not in texto and "percentil" not in texto  # sem sinal
    assert "notas" not in texto  # as notas do gabarito citam pessoas e não saem


def test_rotulos_das_datas() -> None:
    casos = [{"periodo_afetado": [2015, 2016], "data_publica": "2018-03-01"}]
    ex = {"2015-04-30": 2014, "2016-04-30": 2015, "2017-04-30": 2016}
    datas = [*ex, "2024-12-31"]
    assert demonstracao.rotulos_das_datas(datas, ex, casos) == {
        "2015-04-30": "exercicio_anterior", "2016-04-30": "periodo_afetado", "2017-04-30": "periodo_afetado",
        "2024-12-31": "depois_da_revelacao"}  # fmt: skip
    sem_data = [{"periodo_afetado": None, "data_publica": None}]
    assert demonstracao.rotulos_das_datas(["2024-12-31"], {}, sem_data) == {"2024-12-31": "data_maxima"}


DEMO = demonstracao_estatica.DESTINO


@pytest.mark.skipif(
    not (DEMO / "manifesto.json").exists() or not (armazem.PASTA / "manifesto.json").exists(),
    reason="precisa da demonstração gerada (web/public/demo) e de data/armazem (fora do git)",
)
def test_amostra_da_demonstracao_real_igual_a_api() -> None:
    indice = json.loads((DEMO / "indice.json").read_text(encoding="utf-8"))
    entradas = [(e["cd_cvm"], d, exs[-1]) for e in indice["empresas"] for d, exs in e["datas"].items()]
    amostra = [entradas[0], entradas[len(entradas) // 2], entradas[-1]]  # três entradas fixas, sem sorteio
    fa = armazem.FontesArmazem()
    loc = Localizador(base.BRUTOS, fa.cache_enet, base.RAIZ / "data" / "manifesto_brutos.csv")
    with TestClient(api.criar_app(lambda: fa, loc, modo_demonstracao=True)) as c:
        for cd, data, ex in amostra:
            for lang in ("pt", "en"):
                pasta = DEMO / f"investigacoes/{cd}/{ex}/{data}"
                arquivo = json.loads((pasta / f"{lang}.json").read_text(encoding="utf-8"))
                q = {"data_referencia": data, "idioma": lang}
                da_api = c.get(f"/api/v1/investigacoes/{cd}/{ex}", params=q).json()
                assert sem_carimbos(arquivo) == sem_carimbos(da_api)
                assert (pasta / f"{lang}.pdf").read_bytes() == pdf_investigacao.gerar(arquivo)


@pytest.mark.skipif(not (DEMO / "manifesto.json").exists(), reason="precisa da demonstração gerada (web/public/demo)")
def test_demonstracao_real_sem_codigo_interno_nem_hifen_como_sinal_no_pdf() -> None:
    from tests.test_v2_exibicao import HIFEN_COMO_SINAL, sem_trechos_literais
    from tests.test_v2_investigacao import codigos_no_pdf

    achados = {}
    for arquivo in sorted((DEMO / "investigacoes").rglob("*.json")):
        inv = json.loads(arquivo.read_text(encoding="utf-8"))
        problemas = sorted(codigos_no_pdf(inv)) + [
            x for x in pdf_investigacao.linhas(inv) if HIFEN_COMO_SINAL.search(sem_trechos_literais(x))
        ]
        if problemas:
            achados[str(arquivo.relative_to(DEMO))] = problemas
    assert achados == {}
