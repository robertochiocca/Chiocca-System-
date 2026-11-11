"""API (Fase D): testes de contrato sem rede, com o armazém montado da fixture (`mundo_c1`).

Conferem que as rotas espelham o JSON do contrato, com os mesmos números do motor, as mesmas validações (data de
referência de 30/04/2011 a 31/12/2024 e exercício até 2023) e a regra de 09/11/2026: nenhuma rota lista empresas
ordenadas por alerta, percentil ou escore; a busca é só por nome, código CVM ou CNPJ, em ordem alfabética.
"""

from __future__ import annotations

import json
import socket
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import pandas as pd
import pytest
from fastapi.routing import APIRoute
from fastapi.testclient import TestClient

from chiocca import base
from chiocca.cvm import Fontes
from chiocca.v2 import api, armazem, exemplos, investigacao, modelos, pdf_investigacao
from tests.test_base import mundo  # noqa: F401  (fixture)
from tests.test_v2_armazem import mundo_c1  # noqa: F401  (fixture)

V1 = api.PREFIXO
D = "2022-04-30"


@pytest.fixture
def sem_rede(monkeypatch: pytest.MonkeyPatch) -> None:
    def recusa(*_: Any, **__: Any) -> None:
        raise AssertionError("a API não pode acessar a rede")

    monkeypatch.setattr(socket.socket, "connect", recusa)
    monkeypatch.setattr(socket, "create_connection", recusa)


@pytest.fixture
def cliente(mundo_c1: tuple[Fontes, armazem.FontesArmazem], sem_rede: None) -> Iterator[TestClient]:  # noqa: F811
    _, arm = mundo_c1
    with TestClient(api.criar_app(lambda: arm)) as c:
        yield c


def _sem_carimbos(x: Any) -> Any:
    if isinstance(x, dict):
        return {k: _sem_carimbos(v) for k, v in x.items() if k not in ("gerado_em", "calculado_em")}
    if isinstance(x, list):
        return [_sem_carimbos(v) for v in x]
    return x


def test_saude(cliente: TestClient) -> None:
    r = cliente.get(f"{V1}/saude").json()
    assert (r["status"], r["ultimo_exercicio_liberado"]) == ("ok", 2023)
    assert (r["data_referencia_minima"], r["data_referencia_maxima"]) == ("2011-04-30", "2024-12-31")
    assert r["aviso"] == investigacao.AVISO and "valores_mobiliarios" in r["armazem"]["linhas"]


def test_busca_por_nome_codigo_cvm_e_cnpj(cliente: TestClient) -> None:
    nome = cliente.get(f"{V1}/empresas", params={"busca": "empresa 1", "data_referencia": D}).json()
    assert nome["criterio"] == "nome" and nome["ordem"] == "denominacao" and nome["data_referencia"] == D
    nomes = [x["denominacao"] for x in nome["resultados"]]
    assert nomes == sorted(nomes) and "EMPRESA 100" in nomes  # ordem alfabética, nunca por sinal
    cd = cliente.get(f"{V1}/empresas", params={"busca": "000100", "data_referencia": D}).json()
    assert cd["criterio"] == "cd_cvm" and [x["cd_cvm"] for x in cd["resultados"]] == ["100"]
    cnpj = cliente.get(f"{V1}/empresas", params={"busca": "00.000.100/0001-00", "data_referencia": D}).json()
    assert cnpj["criterio"] == "cnpj" and [x["cd_cvm"] for x in cnpj["resultados"]] == ["100"]
    a = cd["resultados"][0]
    assert set(a) == set(modelos.EmpresaResumo.model_fields)  # nenhum sinal, alerta, percentil ou escore
    assert [c["codigo"] for c in a["codigos_negociacao"]] == ["EMP1003"]
    curta = cliente.get(f"{V1}/empresas", params={"busca": "em"})
    assert curta.status_code == 422 and curta.json()["erro"] == "busca_invalida"
    assert cliente.get(f"{V1}/empresas").status_code == 422  # sem busca não há lista de empresas


def test_nenhuma_rota_ordena_empresas_por_sinal(cliente: TestClient) -> None:
    proibidos = {"ordem", "ordenar", "ordenacao", "order", "order_by", "sort", "sort_by", "rank", "ranking", "top"}
    rotas = [r for r in cliente.app.routes if isinstance(r, APIRoute)]  # type: ignore[attr-defined]
    assert rotas and all(r.methods == {"GET"} for r in rotas)
    for r in rotas:
        parametros = {p.alias for p in r.dependant.query_params} | {p.alias for p in r.dependant.path_params}
        assert not parametros & proibidos, r.path
        assert not any(x in r.path for x in ("ranking", "top", "alertas", "maiores", "piores", "percentis")), r.path
    openapi = json.dumps(cliente.get(f"{V1}/openapi.json").json()).lower()
    assert '"name": "sort"' not in openapi and '"name": "ordem"' not in openapi
    base = cliente.get(f"{V1}/empresas", params={"busca": "empresa", "data_referencia": D}).json()["resultados"]
    pedido = cliente.get(f"{V1}/empresas", params={"busca": "empresa", "data_referencia": D, "ordenar": "alerta"})
    assert pedido.json()["resultados"] == base  # parâmetro desconhecido não muda a ordem alfabética
    regra = Path(api.__file__).parents[2] / "docs" / "contratos.md"
    assert (
        "nenhum endpoint lista empresas ordenadas por alerta, percentil ou escore" in regra.read_text("utf-8").lower()
    )


def test_empresa_na_data(cliente: TestClient) -> None:
    r = cliente.get(f"{V1}/empresas/100", params={"data_referencia": D}).json()
    assert r["empresa"]["cd_cvm"] == "100" and r["exercicios"] == [2020, 2021]
    assert [c["codigo"] for c in r["empresa"]["codigos_negociacao"]] == ["EMP1003"]
    antes = cliente.get(f"{V1}/empresas/100", params={"data_referencia": "2021-04-30"}).json()["empresa"]
    assert antes["codigos_negociacao"] == [] and "FCA" in antes["motivo_codigos_negociacao"]  # FCA entregue depois
    assert cliente.get(f"{V1}/empresas/999999").status_code == 404


def test_validacoes_de_data_e_lacre(cliente: TestClient) -> None:
    for rota in ("investigacoes/100/2024", "empresas/100/exercicios/2024"):
        r = cliente.get(f"{V1}/{rota}", params={"data_referencia": D})
        assert r.status_code == 422 and r.json()["erro"] == "exercicio_lacrado" and "2023" in r.json()["motivo"]
    for data in ("2011-04-29", "2025-01-01"):
        r = cliente.get(f"{V1}/investigacoes/100/2020", params={"data_referencia": data})
        assert r.status_code == 422 and r.json()["erro"] == "data_fora_do_intervalo"
        assert r.json()["aviso"] == investigacao.AVISO
    assert (
        cliente.get(f"{V1}/empresas", params={"busca": "empresa", "data_referencia": "2025-01-01"}).status_code == 422
    )
    assert cliente.get(f"{V1}/investigacoes/100/2020", params={"idioma": "es"}).status_code == 422
    assert cliente.get(f"{V1}/investigacoes/100/2009").status_code == 422
    assert cliente.post(f"{V1}/saude").status_code == 405


def test_limite_de_tamanho_da_requisicao(cliente: TestClient) -> None:
    assert cliente.get(f"{V1}/empresas", params={"busca": "x" * (api.LIMITE_QUERY + 1)}).status_code == 414
    r = cliente.request("GET", f"{V1}/saude", content=b"x" * (api.LIMITE_CORPO + 1))
    assert r.status_code == 413 and r.json()["erro"] == "requisicao_grande"


def test_exercicio_na_data_com_evidencias(cliente: TestClient) -> None:
    r = cliente.get(f"{V1}/empresas/100/exercicios/2020", params={"data_referencia": D}).json()
    ex = r["exercicio"]
    assert (ex["exercicio"], ex["versao_usada"], ex["situacao"]) == (2020, 2, "ok")
    assert [v["versao"] for v in ex["versoes_conhecidas"]] == [1, 2]
    antes = cliente.get(f"{V1}/empresas/100/exercicios/2020", params={"data_referencia": "2021-04-30"}).json()
    assert antes["exercicio"]["versao_usada"] == 1  # a versão 2 ainda não existia
    assert r["evidencias"] and all(e["documento"]["versao"] == 2 for e in r["evidencias"])
    assert cliente.get(f"{V1}/empresas/100/exercicios/2023", params={"data_referencia": D}).status_code == 404


@pytest.mark.parametrize("idioma", ["pt", "en"])
def test_investigacao_espelha_o_json_do_motor(
    cliente: TestClient, mundo_c1: tuple[Fontes, armazem.FontesArmazem], idioma: str  # noqa: F811
) -> None:
    _, arm = mundo_c1
    r = cliente.get(f"{V1}/investigacoes/100/2020", params={"data_referencia": D, "idioma": idioma})
    assert r.status_code == 200
    via_api = r.json()
    direto = investigacao.gerar(arm, "100", 2020, D, idioma)
    assert _sem_carimbos(via_api) == _sem_carimbos(json.loads(json.dumps(direto)))  # os mesmos números do motor
    modelos.Investigacao.model_validate(via_api)
    pdf = cliente.get(f"{V1}/investigacoes/100/2020/pdf", params={"data_referencia": D, "idioma": idioma})
    assert pdf.headers["content-type"] == "application/pdf"
    assert pdf.content == pdf_investigacao.gerar(via_api)  # o PDF sai só do JSON (o mesmo, guardado no cache)
    lin = cliente.get(f"{V1}/investigacoes/100/2020/linhagem/piotroski_f", params={"data_referencia": D}).json()
    assert lin["achado"]["sinal"] == "piotroski_f" and lin["achado"]["alerta_v1"] is None
    assert set(lin["evidencias"]) == set(lin["achado"]["linhagem"]["entradas"]) & set(via_api["evidencias"])
    assert cliente.get(f"{V1}/investigacoes/100/2020/linhagem/inexistente").status_code == 404
    texto = json.dumps(via_api, ensure_ascii=False).lower()
    assert "fraude" not in texto and "fraud" not in texto


@pytest.mark.parametrize("nome", exemplos.NOMES)
def test_exemplos_guardados_seguem_o_modelo(nome: str) -> None:
    inv = json.loads((exemplos.PASTA / f"{nome}.json").read_text(encoding="utf-8"))
    m = modelos.Investigacao.model_validate(inv)
    assert m.model_dump(mode="json", exclude_unset=True) == inv  # o modelo espelha o JSON, campo por campo


def test_modelo_recusa_o_que_o_contrato_recusa() -> None:
    inv = json.loads((exemplos.PASTA / f"{exemplos.NOMES[0]}.json").read_text(encoding="utf-8"))
    for mexe in (
        lambda x: x.update(aviso="outro"),
        lambda x: x.update(data_referencia="2025-01-01"),
        lambda x: x["exercicios"][0].update(exercicio=2024),
        lambda x: x.update(ranking=[]),
        lambda x: x["achados"]["risco_financeiro"][0].update(alerta_v1=True),
    ):
        copia = json.loads(json.dumps(inv))
        mexe(copia)
        with pytest.raises(ValueError):
            modelos.Investigacao.model_validate(copia)


def test_como_o_motor_foi_testado_vem_do_json_do_resumo(cliente: TestClient) -> None:
    from chiocca.v2 import ficha_do_motor

    r = cliente.get(f"{V1}/como-o-motor-foi-testado").json()
    x = ficha_do_motor.numeros()
    assert r["acerto"] == x["acerto"] and r["alarmes_por_acerto_nf"] == x["alarmes_por_acerto_nf"]
    assert r["antecedencia"]["mediana_meses"] == x["antecedencia"]["mediana_meses"]
    assert r["documentos"]["pt"]["ficha_do_motor"] == "docs/ficha-do-motor.md" and r["aviso"] == investigacao.AVISO


def test_modo_demonstracao(
    mundo_c1: tuple[Fontes, armazem.FontesArmazem], sem_rede: None, monkeypatch: pytest.MonkeyPatch  # noqa: F811
) -> None:
    _, arm = mundo_c1
    assert "100" not in api.empresas_da_demonstracao()  # a empresa da fixture não está no gabarito
    gabarito = api.empresas_da_demonstracao()
    assert "20990" in gabarito and "22837" not in gabarito  # Americanas entra; caso em observação não entra
    # caso sem data pública no gabarito não entra (decisão de 11/11/2026): Sanepar, Construtora Beter, Mendes Júnior
    assert not {"18627", "4758", "4782"} & gabarito
    gab = pd.read_csv(base.RAIZ / "data" / "gabarito_casos.csv", dtype=str)
    com_data = {str(c).lstrip("0") for c in gab[gab.data_publica.notna()].cd_cvm.dropna()}
    assert gabarito <= com_data  # toda companhia da demonstração tem caso com data pública
    with TestClient(api.criar_app(lambda: arm, modo_demonstracao=True)) as c:
        assert c.get(f"{V1}/saude").json()["modo_demonstracao"] is True
        assert c.get(f"{V1}/empresas", params={"busca": "empresa", "data_referencia": D}).json()["resultados"] == []
        for rota in ("empresas/100", "empresas/100/exercicios/2020", "investigacoes/100/2020",
                     "investigacoes/100/2020/pdf", "investigacoes/100/2020/linhagem/mscore"):  # fmt: skip
            r = c.get(f"{V1}/{rota}", params={"data_referencia": D})
            assert r.status_code == 403 and r.json()["erro"] == "fora_do_modo_demonstracao", rota
    monkeypatch.setattr(api, "empresas_da_demonstracao", lambda: {"100"})
    with TestClient(api.criar_app(lambda: arm, modo_demonstracao=True)) as c:
        nomes = [
            x["cd_cvm"]
            for x in c.get(f"{V1}/empresas", params={"busca": "empresa", "data_referencia": D}).json()["resultados"]
        ]
        assert nomes == ["100"]
        assert c.get(f"{V1}/investigacoes/100/2020", params={"data_referencia": D}).status_code == 200
    monkeypatch.setenv("CHIOCCA_MODO_DEMONSTRACAO", "1")
    assert api.modo_demonstracao_do_ambiente()
    monkeypatch.setenv("CHIOCCA_MODO_DEMONSTRACAO", "0")
    assert not api.modo_demonstracao_do_ambiente()
