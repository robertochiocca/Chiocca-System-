"""Rascunho do plano do estudo 2 (docs/estudo-2-plano.md e docs/en/study-2-plan.md): os números vêm de
docs/estudo_2_numeros.json, que não guarda nada além de contagens e não usa nenhum valor de conta de 2024 em diante;
as contas que dependem só do gabarito do estudo 1 são refeitas aqui."""

from __future__ import annotations

import json

from chiocca import base
from chiocca.v2 import estudo2_numeros as e2

NUMEROS = json.loads(e2.DESTINO.read_text(encoding="utf-8"))
PT = (base.RAIZ / "docs" / "estudo-2-plano.md").read_text(encoding="utf-8")
EN = (base.RAIZ / "docs" / "en" / "study-2-plan.md").read_text(encoding="utf-8")


def _br(x: int) -> str:
    return f"{x:,}".replace(",", ".")


def test_contas_do_gabarito_iguais_ao_json() -> None:
    assert e2.atrasos() == NUMEROS["atrasos"]
    assert e2.limiares() == NUMEROS["limiares"]
    assert e2.esperados() == NUMEROS["esperados"]
    assert e2.persistencia() == NUMEROS["persistencia"]
    assert e2.derivados(NUMEROS) == NUMEROS["derivados"]


def test_so_contagens_dos_metadados_de_2024_e_2025() -> None:
    for ano, x in NUMEROS["entregas_dfp"].items():
        assert set(x) == {"companhias", "ate_o_corte", "com_mais_de_uma_versao"}, ano
        assert all(isinstance(v, int) for v in x.values())
    anos = {int(a) for a in NUMEROS["republicacoes"]["por_exercicio"]}
    assert max(anos) + 1 <= 2023  # o comparativo seguinte fica dentro do lacre


def test_limiares_com_metade_em_alerta() -> None:
    por_k = {x["casos"]: x for x in NUMEROS["limiares"]}
    assert all(por_k[k]["acertos_minimos"] is None for k in (1, 2, 3, 4))
    assert (por_k[5]["acertos_minimos"], por_k[8]["acertos_minimos"], por_k[13]["acertos_minimos"]) == (5, 7, 10)


def test_numeros_do_json_nos_dois_documentos() -> None:
    assert "**Não é o pré-registro.**" in PT and "**It is not the pre-registration.**" in EN
    e = NUMEROS["entregas_dfp"]
    for ano in ("2023", "2024", "2025"):
        assert f"{e[ano]['companhias']} " in PT and f"{e[ano]['companhias']} " in EN
        assert f"{e[ano]['ate_o_corte']} " in PT and f"{e[ano]['ate_o_corte']} " in EN
    rep = NUMEROS["republicacoes"]["total"]
    assert f"{_br(rep['destacada'])} de {_br(rep['comparadas'])} empresa-anos" in PT
    assert f"{rep['destacada']:,} of {rep['comparadas']:,} company-years" in EN
    at = NUMEROS["atrasos"]["acertaveis"]
    assert f"{at['mediana']:.1f}".replace(".", ",") + " meses na mediana" in PT
    assert f"{at['mediana']:.1f} months at the median" in EN
    ps = NUMEROS["derivados"]["poder_secundario"]["pl_ou_lucro"]["por_razao"]
    assert f"1,5 é de {ps['1.5']['poder']:.2f}".replace("0.", "0,") in PT and f"1.5 is {ps['1.5']['poder']:.2f}" in EN
    esp = NUMEROS["esperados"]["por_data"]["2029-12-31"]["media"]
    assert f"{esp:.1f}".replace(".", ",") + " até 31/12/2029" in PT and f"{esp:.1f} by 2029-12-31" in EN


def test_pre_registro_do_estudo_2_com_os_numeros_do_json() -> None:
    """O pré-registro do estudo 2 usa os mesmos números do JSON e do estudo 1, e é assinado por Roberto."""
    pt = (base.RAIZ / "docs" / "pre-registro-estudo-2.md").read_text(encoding="utf-8")
    en = (base.RAIZ / "docs" / "en" / "study-2-preregistration.md").read_text(encoding="utf-8")
    assert "**Registrado em 15/11/2026.**" in pt and "**Registered on 2026-11-15.**" in en
    assert (
        "Assinado por: Roberto Chiocca · Data: 15/11/2026" in pt
        and "Signed by: Roberto Chiocca · Date: 2026-11-15" in en
    )
    assert "revisado por Roberto com o Claude (claude.ai)" in pt and "reviewed by Roberto with Claude (claude.ai)" in en
    e = NUMEROS["entregas_dfp"]
    assert f"{e['2024']['ate_o_corte']} companhias entregaram a DFP de 2024" in pt
    assert f"{e['2024']['ate_o_corte']} companies filed the 2024 DFP" in en
    assert f"{e['2025']['ate_o_corte']} a de 2025" in pt and f"{e['2025']['ate_o_corte']} the 2025 one" in en
    v24, v25 = e["2024"]["com_mais_de_uma_versao"], e["2025"]["com_mais_de_uma_versao"]
    assert f"{v24} companhias têm mais de uma versão da DFP de 2024 e {v25} da de 2025" in pt
    assert f"{v24} companies have more than one version of the 2024 DFP and {v25} of the 2025 one" in en
    d = NUMEROS["derivados"]
    tx = f"{100 * d['taxas_2013_2022']['pl_ou_lucro']:.1f}"
    assert f"{tx.replace('.', ',')}% das empresa-anos tiveram republicação" in pt and f"{tx}% of company-years" in en
    ps = d["poder_secundario"]["pl_ou_lucro"]["por_razao"]
    assert f"{ps['1.5']['poder']:.2f}".replace(".", ",") + " para uma razão de taxas de 1,5" in pt
    assert f"{ps['2.0']['poder']:.2f} for 2.0" in en
    esp = NUMEROS["esperados"]["por_data"]["2029-12-31"]["media"]
    assert f"cerca de {esp:.1f}".replace(".", ",") + " até 31/12/2029" in pt and f"about {esp:.1f} by 2029-12-31" in en
    base_md = (base.RAIZ / "docs" / "base.md").read_text(encoding="utf-8")
    assert "Documentos pedidos ao ENET: 390." in base_md and "390 documentos em 14 exercícios" in pt
