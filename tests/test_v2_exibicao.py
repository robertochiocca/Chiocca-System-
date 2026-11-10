"""Exibição da v2 (pedido de 10/11/2026): sinal de menos (−) nos números negativos da tela e do PDF, sem mudar o
estudo 1; rótulos do Piotroski F iguais na tela e no PDF; glifos do PDF."""

from __future__ import annotations

import json
import re

import pytest

from chiocca import formato
from chiocca.v2 import contexto, exemplos, exibicao, pdf_investigacao, pdf_simples

MENOS = "−"
HIFEN_COMO_SINAL = re.compile(r"(?<![\w.,\-−/])-(?=\d)")


def test_sinal_de_menos_so_onde_o_hifen_e_sinal() -> None:
    assert (
        exibicao.com_sinal_de_menos("M > -1,78 (pré-registro, seção 4)") == f"M > {MENOS}1,78 (pré-registro, seção 4)"
    )
    assert (
        exibicao.com_sinal_de_menos("-0,240; (-3); de -5,212 a 0,647")
        == f"{MENOS}0,240; ({MENOS}3); de {MENOS}5,212 a 0,647"
    )
    intactos = "2024-12-31, 2010-2023, t-1, p. 7-10, pré-registro, DFC_MI 6.01"
    assert exibicao.com_sinal_de_menos(intactos) == intactos
    assert exibicao.decimal(-1.78, "pt", 2) == f"{MENOS}1,78" and exibicao.pct(-0.125, "en") == f"{MENOS}12.5%"


def test_estudo_1_continua_com_hifen() -> None:
    assert formato.decimal(-1.78, "pt", 2) == "-1,78"  # chiocca/formato.py e os documentos do estudo 1 não mudam


def test_literais_e_evidencias_ficam_como_vieram() -> None:
    inv = {"regra": "M > -1,78", "achados": [{"trecho": "lucro de -3", "texto": "valor -3"}],
           "evidencias": {"x": {"ds_conta": "(-) Custo -1"}}, "codigo": "a:-1"}  # fmt: skip
    out = exibicao.textos_com_sinal_de_menos(inv)
    assert out["regra"] == f"M > {MENOS}1,78" and out["achados"][0] == {
        "trecho": "lucro de -3",
        "texto": f"valor {MENOS}3",
    }
    assert out["evidencias"] == inv["evidencias"] and out["codigo"] == "a:-1"


def _textos_de_exibicao(x: object, chave: str | None = None) -> list[str]:
    if chave in exibicao.LITERAIS or chave == "evidencias":
        return []
    if isinstance(x, str):
        return [x]
    if isinstance(x, dict):
        return [s for k, v in x.items() for s in _textos_de_exibicao(v, k)]
    if isinstance(x, list):
        return [s for v in x for s in _textos_de_exibicao(v, chave)]
    return []


@pytest.mark.parametrize("nome", exemplos.NOMES)
def test_exemplos_sem_hifen_como_sinal_no_json_e_no_pdf(nome: str) -> None:
    inv = json.loads((exemplos.PASTA / f"{nome}.json").read_text(encoding="utf-8"))
    assert [s for s in _textos_de_exibicao(inv) if HIFEN_COMO_SINAL.search(s)] == []
    assert [linha for linha in pdf_investigacao.linhas(inv) if HIFEN_COMO_SINAL.search(linha)] == []
    regra = inv["achados"]["possivel_manipulacao"][0]["regra"]
    assert regra.startswith(f"M > {MENOS}1") and f"M > {MENOS}1" in "\n".join(pdf_investigacao.linhas(inv))


def test_pdf_com_sinal_de_menos_e_simbolos() -> None:
    pdf = pdf_simples.gerar_pdf([["M > −1,78 · ΔROA ≤ 3 ≥ 2"]], [["rodapé"]])
    assert b"/Differences [129 /minus]" in pdf and b"/BaseFont /Symbol" in pdf
    assert b"(M > \x811,78 \xb7 ) Tj" in pdf  # o sinal de menos no código livre 0x81 da Helvetica
    assert b"/F3 9 Tf\n(D) Tj" in pdf and b"(\xa3) Tj" in pdf and b"(\xb3) Tj" in pdf  # Δ, ≤ e ≥ na Symbol
    assert pdf == pdf_simples.gerar_pdf([["M > −1,78 · ΔROA ≤ 3 ≥ 2"]], [["rodapé"]])  # determinístico


def test_rotulos_do_piotroski_iguais_na_tela_e_no_pdf() -> None:
    ts = (exemplos.PASTA.parents[1] / "web" / "lib" / "textos.ts").read_text(encoding="utf-8")
    blocos = re.findall(r"sinais_f_rotulos: \{(.*?)\}", ts, flags=re.S)
    assert len(blocos) == 2  # PT e EN
    for k, bloco in enumerate(blocos):
        tela = {a.strip('"'): b for a, b in re.findall(r'^\s*("?[^\s:"]+"?): "([^"]+)",', bloco, flags=re.M)}
        assert tela == {s: r[k] for s, r in contexto.ROTULOS_F.items()}
    assert set(contexto.ROTULOS_F) == set(contexto.SINAIS_F)
    for pt, en in contexto.ROTULOS_F.values():  # nome legível com a sigla do artigo entre parênteses
        assert re.fullmatch(r"[A-ZÀ-Ú][^()]+ \(Δ?[A-Z_]+\)", pt) and re.fullmatch(r"[A-Z][^()]+ \(Δ?[A-Z_]+\)", en)
