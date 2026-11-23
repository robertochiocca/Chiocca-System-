"""Braço do motor v2 na avaliação secundária do estudo 2 (emenda 5, itens 3 e 8; decisão de Roberto, 23/11/2026).

Só com dados fictícios: listas e republicações sintéticas, sem nenhum arquivo da CVM. As medidas reaproveitam as funções
congeladas de `chiocca/v2/estudo2/secundaria.py`; o v1 recalculado no braço tem de dar a mesma DR e o mesmo limite da
avaliação do v1, com a mesma semente e as mesmas reamostragens.
"""

from __future__ import annotations

from datetime import date
from typing import Any

import numpy as np
import pandas as pd
import pytest

from chiocca.sinais_amostra import AMOSTRA_FIN, AMOSTRA_NF
from chiocca.v2 import lacre
from chiocca.v2.estudo2 import secundaria
from chiocca.v2.motor_v2 import avaliacao

REAMOSTRAGENS = 300


def _sintetico(v2_igual_ao_v1: bool = False) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """(lista do v1, republicações do v1, lista do v2): 120 companhias não financeiras em 2024 e 2025, uma financeira,
    uma não financeira sem a DFP seguinte comparável e uma que só o v2 avalia."""
    rng = np.random.default_rng(3)
    l1, rep, l2 = [], [], []
    for c in range(1, 121):
        for ano in (2024, 2025):
            v1 = (c + ano) % 2 == 0
            v2 = v1 if v2_igual_ao_v1 else c % 5 == 0
            y = (c % 5 == 0 and (c + ano) % 3 != 0) or c % 37 == 0  # múltiplas de 5 republicam mais
            chave = {"exercicio": ano, "cd_cvm": str(c), "dt_refer": f"{ano}-12-31", "amostra": AMOSTRA_NF}
            l1.append(chave | {"avaliada": True, "em_alerta": v1})
            rep.append({"exercicio": ano, "cd_cvm": str(c), "amostra": AMOSTRA_NF, "avaliada": True, "em_alerta": v1,
                        "alerta_regra_boba": c % 7 == 0, "n_sinais": int(v1), "mscore": float(rng.normal()),
                        "alavancagem": float(rng.uniform()), "estreita": y, "larga": y or v1,
                        "situacao_seguinte": "ok"})  # fmt: skip
            l2.append(chave | {"avaliada": True, "em_alerta": v2, "escore": 0.95 if v2 else float(rng.uniform(0, 0.8))})
    extras = [  # cd, exercicio, amostra, avaliada no v1, avaliada no v2, DFP seguinte comparável
        ("999", 2024, AMOSTRA_FIN, True, True, True),
        ("998", 2025, AMOSTRA_NF, True, True, False),
        ("997", 2025, AMOSTRA_NF, False, True, True),
    ]
    for cd, ano, amostra, av1, av2, comparavel in extras:
        chave = {"exercicio": ano, "cd_cvm": cd, "dt_refer": f"{ano}-12-31", "amostra": amostra}
        l1.append(chave | {"avaliada": av1, "em_alerta": av1})
        l2.append(chave | {"avaliada": av2, "em_alerta": True, "escore": 0.99})
        if av1:
            rep.append({"exercicio": ano, "cd_cvm": cd, "amostra": amostra, "avaliada": comparavel, "em_alerta": True,
                        "alerta_regra_boba": False, "n_sinais": 1, "mscore": 0.0, "alavancagem": 0.5,
                        "estreita": True, "larga": True,
                        "situacao_seguinte": "ok" if comparavel else "sem_documento"})  # fmt: skip
    lista_1 = pd.DataFrame(l1).astype({"avaliada": "boolean", "em_alerta": "boolean"})
    lista_2 = pd.DataFrame(l2).astype({"avaliada": "boolean", "em_alerta": "boolean"})
    return lista_1, pd.DataFrame(rep), lista_2


def _braco(**k: Any) -> dict[str, Any]:
    lista_1, rep, lista_2 = _sintetico(k.pop("v2_igual_ao_v1", False))
    entregas = k.pop("entregas", {})
    commit = k.pop("commit", date(2027, 1, 20))
    return avaliacao.avaliar_braco(rep, lista_1, lista_2, entregas, commit, reamostragens=REAMOSTRAGENS, **k)


def test_v1_recalculado_igual_a_avaliacao_do_v1() -> None:
    """Mesma semente, mesmas reamostragens e as mesmas companhias: a DR e o limite do v1 são os da avaliação do v1."""
    _, rep, _ = _sintetico()
    v1 = secundaria.avaliar(rep, reamostragens=REAMOSTRAGENS)
    r = _braco()["total"]
    assert r["empresa_anos"] == v1["empresa_anos"] == 240 and r["companhias"] == v1["companhias"]
    assert (
        r["v1"]["dr"] == v1["motor"]["dr"] and r["v1"]["dr_limite_inferior_95"] == v1["motor"]["dr_limite_inferior_95"]
    )
    assert r["regra_boba"]["dr_limite_inferior_95"] == v1["regra_boba"]["dr_limite_inferior_95"]
    assert r["semente"] == secundaria.SEMENTE and secundaria.REAMOSTRAGENS == 10_000


def test_medidas_so_nas_empresa_anos_que_o_v1_avalia() -> None:
    """A financeira, a sem DFP seguinte comparável e a que só o v2 avalia ficam fora das medidas."""
    lista_1, rep, lista_2 = _sintetico()
    r = _braco()
    assert r["total"]["empresa_anos"] == 240 and r["total"]["v2"]["em_alerta"]["empresa_anos"] == 48
    so = avaliacao.linhas_so_do_v2(lista_1, lista_2)
    assert so.cd_cvm.tolist() == ["997"] and (so.n_sinais == 0).all()
    assert r["descritivos"]["financeiras"]["em_alerta"]["empresa_anos"] == 1
    rep_so = pd.DataFrame([{"exercicio": 2025, "cd_cvm": "997", "amostra": AMOSTRA_NF, "avaliada": True,
                            "em_alerta": True, "estreita": False}])  # fmt: skip
    d = _braco(rep_so_v2=rep_so)["descritivos"]["so_o_v2_avalia"]
    assert d["empresa_anos"] == 1 and d["em_alerta"]["empresa_anos"] == 1


def test_criterios_da_emenda_5() -> None:
    r = _braco()["total"]
    assert r["resultado"] == "associação positiva" and r["v2"]["dr"] > 0
    assert r["v2_menos_v1"]["resultado"] == "o v2 separa melhor que o v1" and r["v2_menos_v1"]["limite_inferior_95"] > 0
    assert r["v2_menos_regra_boba"]["resultado"] == "o v2 separa melhor que a regra boba"
    igual = _braco(v2_igual_ao_v1=True)["total"]["v2_menos_v1"]
    assert igual["diferenca_dr"] == 0 and igual["limite_inferior_95"] == 0
    assert igual["resultado"] == "sem vencedor declarado"


def test_ranking_pela_ordem_do_v2() -> None:
    """O escore do v2 põe no topo as companhias múltiplas de 5, as que mais republicam."""
    r = _braco()["total"]["ranking"]
    assert set(r) == {"1%", "5%", "10%"} and r["10%"]["k"] == 24
    assert r["10%"]["precisao"]["v2"] > r["10%"]["precisao"]["regra_boba"]
    assert r["1%"]["precisao"]["v2"] >= 0.5


def test_subconjunto_prospectivo_pela_primeira_entrega_da_dfp_de_2026() -> None:
    """2025 com a primeira entrega da DFP de 2026 estritamente depois do dia do commit; o mesmo dia não conta; 2024
    nunca conta."""
    commit = date(2027, 1, 20)
    entregas = {str(c): date(2027, 1, 21) if c <= 60 else date(2027, 1, 20) for c in range(1, 121)}
    r = _braco(entregas=entregas, commit=commit)["prospectivo"]
    assert r["empresa_anos_de_2025"] == 120 and r["empresa_anos"] == 60 and r["companhias"] == 60
    _, rep, _ = _sintetico()
    nf = rep[(rep.amostra == AMOSTRA_NF) & rep.avaliada]
    pro = avaliacao.prospectiva(nf, entregas, commit)
    assert not pro[nf.exercicio.to_numpy() == 2024].any() and int(pro.sum()) == 60
    vazio = _braco(entregas={}, commit=commit)["prospectivo"]
    assert vazio["empresa_anos"] == 0 and vazio["empresa_anos_de_2025"] == 120


def test_rotulo_nao_prospectivo_so_com_a_reserva() -> None:
    assert avaliacao.rotulos(date(2027, 1, 31)) == [] and avaliacao.rotulos(date(2026, 12, 15)) == []
    assert avaliacao.rotulos(date(2027, 4, 2)) == ["não prospectivo"]
    assert _braco(commit=date(2027, 4, 2))["rotulos"] == ["não prospectivo"]


def test_republicacoes_e_lista_do_v1_na_mesma_ordem() -> None:
    lista_1, rep, lista_2 = _sintetico()
    com = avaliacao.com_dt_refer(rep, lista_1)
    assert (com.dt_refer == com.exercicio.astype(str) + "-12-31").all()
    with pytest.raises(ValueError):
        avaliacao.com_dt_refer(rep.iloc[::-1], lista_1)
    with pytest.raises(ValueError):
        avaliacao.com_o_v2(com, lista_2[lista_2.cd_cvm != "1"])


class FontesProibidas:
    def __getattr__(self, nome: str) -> Any:
        raise AssertionError(f"leitura de dados antes do lacre: {nome}")


def test_dfp_de_2026_so_depois_da_segunda_abertura() -> None:
    assert not hasattr(lacre, "ESTUDO_2_SEGUNDA_ABERTURA")
    with pytest.raises(lacre.ExercicioLacrado):
        avaliacao.primeira_entrega(FontesProibidas())  # type: ignore[arg-type]


def test_avaliacao_so_a_partir_de_31_05_2027() -> None:
    assert date.today() < secundaria.DATA_MINIMA
    with pytest.raises(SystemExit, match="2027-05-31"):
        avaliacao.main(["--sha256-v1", "0", "--sha256-v2", "0", "--commit-lista-v2", "HEAD"])


def test_data_do_commit_no_horario_de_brasilia() -> None:
    d = avaliacao.data_do_commit("HEAD")
    assert isinstance(d, date) and d <= date.today()
