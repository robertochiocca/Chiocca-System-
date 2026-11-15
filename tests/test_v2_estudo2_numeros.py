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
