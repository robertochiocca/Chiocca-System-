"""Motor v2 congelado, dentro da amostra de desenvolvimento (pedido de 23/11/2026, item 4(b)).

Os documentos saem do JSON versionado; o rótulo "dentro da amostra de desenvolvimento, não é teste" está no JSON e no
topo dos dois documentos; só agregados de 2010 a 2023; os números foram calculados com o código congelado (o SHA-256 do
registro gravado é o do registro atual); o v2 congelado dá as mesmas avaliadas e os mesmos alertas das descrições sem
rótulo; o v1 e a regra boba são os do estudo 1.
"""

from __future__ import annotations

import hashlib
import json
import re

import pytest

from chiocca.base import RAIZ
from chiocca.sinais_amostra import AMOSTRA_FIN, AMOSTRA_NF
from chiocca.v2 import motor_v2_dentro_da_amostra as da
from chiocca.v2.motor_v2 import registro

D = json.loads(da.SAIDA.read_text(encoding="utf-8"))
ESTUDO_1 = json.loads((RAIZ / "docs" / "resultados_numeros.json").read_text(encoding="utf-8"))
DESCRICOES = json.loads(da.DESCRICOES.read_text(encoding="utf-8"))


@pytest.mark.parametrize("lang", ["pt", "en"])
def test_documento_igual_a_saida_do_script(lang: str) -> None:
    assert da.DOCS[lang].read_text(encoding="utf-8") == da.render(D, lang)


@pytest.mark.parametrize("lang", ["pt", "en"])
def test_rotulo_no_json_e_no_topo_dos_documentos(lang: str) -> None:
    assert D["rotulo"] == "dentro da amostra de desenvolvimento, não é teste"
    doc = da.DOCS[lang].read_text(encoding="utf-8")
    citacao = doc.split("\n")[2]
    assert citacao.startswith("> **") and da.ROTULO[lang].lower() in citacao.lower()


def test_calculado_com_o_codigo_congelado() -> None:
    assert D["registro_sha256"] == hashlib.sha256(registro.REGISTRO.read_bytes()).hexdigest()
    assert D["congelado_em"] == registro.CONGELADO_EM and D["codigo_sem_alteracao_local"] is True
    assert re.fullmatch(r"[0-9a-f]{40}", D["commit"])


def test_so_agregados_de_2010_a_2023() -> None:
    assert D["anos"] == [2010, 2023]
    texto = da.SAIDA.read_text(encoding="utf-8")
    assert '"cd_cvm"' not in texto and "caso_id" not in texto and "denominacao" not in texto
    for lado in D["acertos_estudo_1"].values():  # só contagens, sem a lista dos casos
        assert set(lado) == {"acertaveis", "acertados", "acertados_teste", "alarmes", "secundaria", "taxa"}
    for g in (AMOSTRA_NF, AMOSTRA_FIN):
        assert list(D["taxas"][g]["por_ano"]) == [str(a) for a in range(2010, 2024)]


def test_igual_as_descricoes_sem_rotulo() -> None:
    assert D["igual_as_descricoes"] == {AMOSTRA_NF: True, AMOSTRA_FIN: True}
    d = DESCRICOES["escore_por_numero_de_sinais"]["grupos"]
    for g in (AMOSTRA_NF, AMOSTRA_FIN):
        assert D["taxas"][g]["avaliadas"] == d[g]["maximo"]["avaliadas"]
        assert D["taxas"][g]["em_alerta"] == d[g]["maximo"]["alertas"]
        assert D["por_numero_de_sinais"][g] == d[g]["maximo"]["por_k"]
    assert D["cobertura"][AMOSTRA_NF]["v2"]["mscore"] == DESCRICOES["depi_dva"]["mscore_v2"]
    assert D["cobertura"][AMOSTRA_NF]["v1"]["mscore"] == DESCRICOES["depi_dva"]["mscore_v1"]
    c = D["cobertura"][AMOSTRA_NF]
    fora = c["descricoes"]["depi_pela_dva_fora_do_plano_nao_financeiro"]
    assert (
        c["depreciacao_pela_dva"] + fora == c["descricoes"]["depi_pela_dva"] == DESCRICOES["depi_dva"]["depi_pela_dva"]
    )
    assert c["descricoes"]["mscore_v2"] == c["v2"]["mscore"]


def test_somas_e_taxas_consistentes() -> None:
    for g in (AMOSTRA_NF, AMOSTRA_FIN):
        t = D["taxas"][g]
        assert t["avaliadas"] == sum(v["avaliadas"] for v in t["por_ano"].values())
        assert t["em_alerta"] == sum(v["em_alerta"] for v in t["por_ano"].values())
        taxas = [v["em_alerta"] / v["avaliadas"] for v in t["por_ano"].values()]
        assert t["menor_taxa_anual"] == min(taxas) and t["maior_taxa_anual"] == max(taxas)
        assert t["avaliadas"] == sum(v["empresa_anos"] for v in D["por_numero_de_sinais"][g].values())


def test_cobertura_consistente() -> None:
    for g in (AMOSTRA_NF, AMOSTRA_FIN):
        c = D["cobertura"][g]
        assert D["taxas"][g]["avaliadas"] == c["avaliadas_v1"] - c["avaliadas_pelo_v1_e_nao_pelo_v2"] + c[
            "avaliadas_so_pelo_v2"]  # fmt: skip
        assert c["v2"]["benford"] <= c["empresa_anos"] and all(c["v2"][s] >= n for s, n in c["v1"].items())


def test_v1_e_regra_boba_sao_os_do_estudo_1() -> None:
    a, e = D["acertos_estudo_1"], ESTUDO_1["acerto"]
    assert a["v1"]["acertaveis"] == a["v2"]["acertaveis"] == a["regra_boba"]["acertaveis"] == e["acertaveis"]
    assert a["v1"]["acertados"] == e["acertados"] and a["v1"]["acertados_teste"] == e["acertados_teste"]
    assert a["regra_boba"]["acertados"] == e["acertados_boba"]
    assert a["regra_boba"]["acertados_teste"] == e["acertados_boba_teste"]
    assert a["v1"]["alarmes"]["nf"] == ESTUDO_1["alarmes"]["nf"]
    assert a["regra_boba"]["alarmes"]["nf"] == ESTUDO_1["alarmes"]["nf_boba"]
