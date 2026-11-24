"""Notas de procedimento do estudo dos EUA, antes do cálculo único (pedido de 24/11/2026, sexta rodada, item 1).

Os documentos em PT e EN são a saída de `chiocca.eua.notas`; os números das leituras de formato saem de
`docs/eua_leituras_de_formato.json` e conferem com a Fase 0; as regras descritas são as do código congelado, que as
notas não mudam.
"""

from __future__ import annotations

import json

import pytest

from chiocca.base import RAIZ
from chiocca.eua import estudo, fsds, notas

LEITURAS, REGISTRO = notas.ler()


@pytest.mark.parametrize("lang", ["pt", "en"])
def test_documento_igual_a_saida_do_modulo(lang: str) -> None:
    assert notas.DOCS[lang].read_text(encoding="utf-8") == notas.render(LEITURAS, REGISTRO, lang)


def test_leituras_coerentes_e_iguais_as_da_fase_0() -> None:
    z, v, c = LEITURAS["nomes_nos_zips"], LEITURAS["trimestre_sem_entregas"], LEITURAS["contagem_de_linhas"]
    assert (z["de"], z["ate"], z["zips"], z["com_sub_num_pre"]) == (
        fsds.TRIMESTRES[0], fsds.TRIMESTRES[-1], len(fsds.TRIMESTRES), len(fsds.TRIMESTRES))  # fmt: skip
    for x in c["arquivos"].values():
        assert x["linhas"] == x["lidas_sem_aspas"] == x["lidas_com_o_padrao"] > 0
    assert set(v["linhas_de_dados"].values()) == {0}
    fase0 = json.loads((RAIZ / "docs" / "eua_fase0_numeros.json").read_text(encoding="utf-8"))["fsds"]
    assert v["trimestre"] in fase0["trimestres_sem_entregas"]
    por_trimestre = fase0["linhas_por_trimestre"]
    for arquivo in ("sub.txt", "num.txt"):
        assert c["arquivos"][arquivo]["linhas"] == por_trimestre[c["trimestre"]][arquivo]
        assert v["linhas_de_dados"][arquivo] == por_trimestre[v["trimestre"]][arquivo]
    assert "value" not in {x for cs in c["colunas_carregadas"].values() for x in cs}  # nenhum valor lido


def test_notas_apontam_o_congelamento_e_as_regras_do_codigo() -> None:
    assert notas.COMMIT_DO_CONGELAMENTO.startswith("dd9b662") and len(notas.COMMIT_DO_CONGELAMENTO) == 40
    assert "chiocca/eua/notas.py" not in REGISTRO["codigo"]  # fora do fecho do estudo: as notas não mudam o código
    for lang, aviso in (("pt", "Nenhum valor foi lido"), ("en", "No value was read")):
        texto = notas.DOCS[lang].read_text(encoding="utf-8")
        assert notas.COMMIT_DO_CONGELAMENTO in texto and REGISTRO["codigo"]["chiocca/eua/estudo.py"] in texto
        assert aviso in texto and all(f"### ({r})" in texto for r in ("vii", "viii", "ix", "x"))
    doc = estudo.__doc__ or ""
    assert all(f"\n({r})" in doc for r in ("vii", "viii", "ix", "x"))
    assert estudo.PRIMEIRO_ANO_DO_ITEM == 2004 and estudo.EXERCICIOS_CALCULADOS.start == 2009
    assert (estudo.EXERCICIOS.start, estudo.EXERCICIOS.stop - 1) == (2011, 2024)


def test_pre_registro_nao_muda() -> None:
    texto = (RAIZ / "docs" / "pre-registro-eua.md").read_text(encoding="utf-8")
    assert "notas-de-procedimento" not in texto and "procedure-notes" not in texto
