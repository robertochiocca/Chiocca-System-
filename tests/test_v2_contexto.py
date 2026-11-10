"""Contexto (Fase C2, segunda parte): Altman Z'', Piotroski F, percentil, histórico e o PDF sem dependência."""

from __future__ import annotations

import re
from pathlib import Path

import pandas as pd
import pytest

from chiocca.base import COLUNAS
from chiocca.v2 import contexto, pdf_simples

U, P = "ÚLTIMO", "PENÚLTIMO"


def _contas(linhas: list[tuple[str, str, str, float]]) -> pd.DataFrame:
    return pd.DataFrame([(d, o, c, f"conta {c}", v) for d, o, c, v in linhas], columns=COLUNAS)


# Exemplo resolvido próprio da v2 (empresa fictícia, R$): lucros acumulados zerados e reservas de lucros positivas.
EXEMPLO_Z2 = _contas([
    ("BPA", U, "1", 1000.0), ("BPA", U, "1.01", 400.0), ("BPP", U, "2.01", 250.0), ("BPP", U, "2.02", 350.0),
    ("BPP", U, "2.03", 400.0), ("BPP", U, "2.03.04", 300.0), ("BPP", U, "2.03.05", 0.0), ("DRE", U, "3.05", 120.0),
])  # fmt: skip


def test_exemplo_resolvido_do_altman_z2() -> None:
    z = contexto.altman_z2(EXEMPLO_Z2, "nao_financeira")
    # X1 = 0,15; X2 = 0,30; X3 = 0,12; X4 = 400 ÷ 600; Z'' = 6,56·0,15 + 3,26·0,30 + 6,72·0,12 + 1,05·(2/3) = 3,4684
    assert z.componentes == pytest.approx({"X1": 0.15, "X2": 0.30, "X3": 0.12, "X4": 400 / 600})
    assert z.resultado.valor == pytest.approx(3.4684)
    assert contexto.SEM_ZONA in z.marcas and contexto.VALIDADE_Z2 in z.marcas


def test_x2_soma_reservas_de_lucros_e_nao_so_lucros_acumulados() -> None:
    z = contexto.altman_z2(EXEMPLO_Z2, "nao_financeira")
    so_acumulados = 6.56 * 0.15 + 3.26 * 0.0 + 6.72 * 0.12 + 1.05 * (400 / 600)
    assert z.resultado.valor != pytest.approx(so_acumulados)  # falha se o X2 usar só lucros acumulados


def test_z2_sem_a_constante_do_emerging_market_score_e_sem_zonas() -> None:
    fonte = (Path(contexto.__file__)).read_text(encoding="utf-8")
    assert not re.search(r"3[.,]25", fonte)  # a constante +3,25 não aparece no cálculo
    assert "zona" not in "".join(contexto.COEF_Z2)
    assert contexto.SEM_ZONA.pt == "sem zona de corte: a fonte disponível não define zonas para o Z''"


def test_z2_financeira_e_conta_ausente() -> None:
    assert contexto.altman_z2(EXEMPLO_Z2, "financeira").resultado.codigo == "nao_se_aplica"
    sem = EXEMPLO_Z2[EXEMPLO_Z2.cd_conta != "2.03.05"]
    assert contexto.altman_z2(sem, "nao_financeira").resultado.status == "indefinido"  # sem imputação


CONTAS_T = _contas([
    ("BPA", U, "1", 1100.0), ("BPA", P, "1", 1000.0), ("DRE", U, "3.09", 110.0), ("DRE", P, "3.09", 80.0),
    ("DFC_MI", U, "6.01", 150.0), ("BPP", U, "2.02.01", 0.0), ("BPP", P, "2.02.01", 0.0),
    ("BPA", U, "1.01", 500.0), ("BPA", P, "1.01", 400.0), ("BPP", U, "2.01", 250.0), ("BPP", P, "2.01", 250.0),
    ("DRE", U, "3.03", 330.0), ("DRE", P, "3.03", 280.0), ("DRE", U, "3.01", 1100.0), ("DRE", P, "3.01", 1000.0),
])  # fmt: skip
EMISSAO = pd.DataFrame([("DFC_MI", U, "6.03.01", "Captação de recursos com emissão de ações", 0.0),
                        ("DFC_MI", U, "6.03.02", "Captação de empréstimos", 500.0)], columns=COLUNAS)  # fmt: skip
CONTAS_T1 = _contas([("BPA", P, "1", 900.0)])


def test_piotroski_f_com_os_nove_sinais() -> None:
    f = contexto.piotroski_f(pd.concat([CONTAS_T, EMISSAO]), CONTAS_T1, "nao_financeira")
    s = f.componentes["sinais"]
    assert s == {
        "ROA": 1,
        "CFO": 1,
        "ΔROA": 1,
        "ACCRUAL": 1,
        "ΔLEVER": 0,
        "ΔLIQUID": 1,
        "EQ_OFFER": 1,
        "ΔMARGIN": 1,
        "ΔTURN": 0,
    }
    assert f.texto == "F = 7/9 (9 calculáveis)" and f.resultado.valor == 7.0
    assert contexto.DIVIDA_ZERO in f.marcas  # dívida de longo prazo zero nos dois anos: 0, com marca
    assert f.componentes["codigos_emissao"] == ["6.03.01"]  # captação de empréstimos não é emissão de ações


def test_piotroski_sem_t2_e_sem_linha_de_emissao() -> None:
    f = contexto.piotroski_f(CONTAS_T, None, "nao_financeira")
    s = f.componentes["sinais"]
    assert s["ΔROA"] is None and s["ΔTURN"] is None and s["EQ_OFFER"] is None  # não imputa o que falta
    assert f.texto == "F = 5/9 (5 calculáveis)"
    com_emissao = pd.concat([CONTAS_T, EMISSAO.assign(valor=[300.0, 0.0])])
    assert contexto.piotroski_f(com_emissao, None, "nao_financeira").componentes["sinais"]["EQ_OFFER"] == 0
    assert contexto.piotroski_f(CONTAS_T, None, "financeira").resultado.codigo == "nao_se_aplica"


def test_percentil_e_historico() -> None:
    assert contexto.percentil(5.0, [float(x) for x in range(1, 11)])["valor"] == pytest.approx(45.0)
    assert contexto.percentil(5.0, [float(x) for x in range(1, 10)])["valor"] is None  # menos de 10
    h = contexto.historico({2015: 1.0, 2016: 2.0, 2017: 3.0, 2018: 4.0, 2019: 5.0}, 20.0)
    assert (h["mediana"], h["q1"], h["q3"], h["faixa_tukey"], h["posicao"]) == (3.0, 2.0, 4.0, [-1.0, 7.0], "acima")
    assert contexto.historico({2018: 4.0, 2019: 5.0, 2017: None}, 4.5)["motivo"] is not None


def test_pdf_determinista_com_rodape_em_todas_as_paginas() -> None:
    linhas = ["# Título com − e ≥", *[f"linha {i} → texto" for i in range(200)]]
    paginas = pdf_simples.paginar(linhas)
    rodapes = [["Aviso fixo", f"Página {i}"] for i in range(1, len(paginas) + 1)]
    a, b = pdf_simples.gerar_pdf(paginas, rodapes), pdf_simples.gerar_pdf(paginas, rodapes)
    assert a == b and a.startswith(b"%PDF-1.4") and len(paginas) > 1
    assert a.count(b"(Aviso fixo) Tj") == len(paginas)
    # sinal de menos na Helvetica (código 0x81 da /Differences), "≥" na Symbol, "→" transliterado (10/11/2026)
    assert b"(T\xedtulo com \x81 e ) Tj" in a and b"/F3 11 Tf\n(\xb3) Tj" in a and b"->" in a


def test_coeficientes_do_z2_iguais_ao_catalogo() -> None:
    catalogo = (Path(contexto.__file__).parents[2] / "catalogo_sinais.yaml").read_text(encoding="utf-8")
    bloco = catalogo[catalogo.index("- id: altman_z2") :]
    formula = re.search(r'formula: "Z\'\' = ([^"]+)"', bloco)
    assert formula
    termos = {k: float(c) for c, k in re.findall(r"([0-9.]+)\*(X\d)", formula.group(1))}
    assert termos == contexto.COEF_Z2
    assert "fase: contexto_v2" in bloco[: bloco.index("- id: piotroski_f")]
