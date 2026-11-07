"""M-score de Beneish, oito variáveis (sinal `mscore_beneish` do catálogo, fase mvp).

O que mede: oito índices que comparam o ano t com o ano t-1. Juntos, estimam a chance de o lucro ter
sido manipulado: recebíveis crescendo mais que a receita (DSRI), margem caindo (GMI), ativos de
qualidade duvidosa (AQI), crescimento forte (SGI), depreciação desacelerando (DEPI), despesas de venda
e administrativas (SGAI), lucro sem caixa (TATA) e alavancagem (LVGI).

Referência acadêmica: Beneish (1999), Financial Analysts Journal 55(5); Beneish, Lee e Nichols (2013),
Financial Analysts Journal 69(2) (TATA pela versão do fluxo de caixa, escolhida no pré-registro, 4.1).
Livro: Schilit, Perler e Engelhart, Financial Shenanigans, 4ª ed., capítulos 3, 4, 6, 7 e 12. O livro
não traz a fórmula; cada componente corresponde a uma família de truques descrita nesses capítulos.

Contas (códigos confirmados na Fase 0, docs/reconhecimento.md 1.4): contas_a_receber 1.01.03,
receita_liquida 3.01, resultado_bruto 3.03, ativo_circulante 1.01, imobilizado 1.02.03, ativo_total 1,
depreciacao (DFC, por texto em 6.01.01), despesas_vendas 3.04.01, despesas_gerais_adm 3.04.02,
lucro_operacoes_continuadas 3.09, caixa_operacional 6.01, passivo_circulante 2.01, emprestimos_lp 2.02.01.

Convenção de sinal: na DFP, despesas vêm negativas. O SGAI usa o valor absoluto das despesas; a
depreciação entra positiva, como na DFC indireta.

Conta faltante ou denominador zero: "não calculável" (pré-registro, 4.1). Os valores neutros do artigo
de 1999 ficam só para o teste de robustez. Receita negativa: a empresa-ano fica na amostra, e os índices que
dividem pela receita (DSRI, GMI, SGI e SGAI) ficam "não calculável" quando a receita do denominador é ≤ 0
(emenda 10).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping

from chiocca.sinais.resultado import NaoCalculavel, Resultado, conta, divide, divide_por_positivo

Valores = Mapping[str, float | None]

INTERCEPTO = -4.84
COEFICIENTES: dict[str, float] = {
    "DSRI": 0.920,
    "GMI": 0.528,
    "AQI": 0.404,
    "SGI": 0.892,
    "DEPI": 0.115,
    "SGAI": -0.172,
    "TATA": 4.679,
    "LVGI": -0.327,
}


def dsri(t: Valores, t1: Valores) -> float:
    a = divide_por_positivo(conta(t, "contas_a_receber"), conta(t, "receita_liquida"), "DSRI receita t")
    b = divide_por_positivo(conta(t1, "contas_a_receber"), conta(t1, "receita_liquida"), "DSRI receita t-1")
    return divide(a, b, "DSRI t-1")


def gmi(t: Valores, t1: Valores) -> float:
    margem_t = divide_por_positivo(conta(t, "resultado_bruto"), conta(t, "receita_liquida"), "GMI receita t")
    margem_t1 = divide_por_positivo(conta(t1, "resultado_bruto"), conta(t1, "receita_liquida"), "GMI receita t-1")
    return divide(margem_t1, margem_t, "GMI margem t")


def _qualidade_ativo(v: Valores, rotulo: str) -> float:
    ativo = conta(v, "ativo_total")
    return 1 - divide(conta(v, "ativo_circulante") + conta(v, "imobilizado"), ativo, f"AQI ativo {rotulo}")


def aqi(t: Valores, t1: Valores) -> float:
    return divide(_qualidade_ativo(t, "t"), _qualidade_ativo(t1, "t-1"), "AQI t-1")


def sgi(t: Valores, t1: Valores) -> float:
    return divide_por_positivo(conta(t, "receita_liquida"), conta(t1, "receita_liquida"), "SGI receita t-1")


def _taxa_depreciacao(v: Valores, rotulo: str) -> float:
    dep = abs(conta(v, "depreciacao"))
    return divide(dep, dep + conta(v, "imobilizado"), f"DEPI base {rotulo}")


def depi(t: Valores, t1: Valores) -> float:
    return divide(_taxa_depreciacao(t1, "t-1"), _taxa_depreciacao(t, "t"), "DEPI taxa t")


def _peso_sga(v: Valores, rotulo: str) -> float:
    sga = abs(conta(v, "despesas_vendas")) + abs(conta(v, "despesas_gerais_adm"))
    return divide_por_positivo(sga, conta(v, "receita_liquida"), f"SGAI receita {rotulo}")


def sgai(t: Valores, t1: Valores) -> float:
    return divide(_peso_sga(t, "t"), _peso_sga(t1, "t-1"), "SGAI t-1")


def tata(t: Valores, t1: Valores) -> float:  # noqa: ARG001 - t1 mantido pela assinatura comum
    numerador = conta(t, "lucro_operacoes_continuadas") - conta(t, "caixa_operacional")
    return divide(numerador, conta(t, "ativo_total"), "TATA ativo t")


def _alavancagem(v: Valores, rotulo: str) -> float:
    divida = conta(v, "passivo_circulante") + conta(v, "emprestimos_lp")
    return divide(divida, conta(v, "ativo_total"), f"LVGI ativo {rotulo}")


def lvgi(t: Valores, t1: Valores) -> float:
    return divide(_alavancagem(t, "t"), _alavancagem(t1, "t-1"), "LVGI t-1")


FUNCOES = {"DSRI": dsri, "GMI": gmi, "AQI": aqi, "SGI": sgi, "DEPI": depi, "SGAI": sgai, "TATA": tata, "LVGI": lvgi}


@dataclass(frozen=True)
class MScore:
    """Os oito componentes guardados separadamente (a ficha de alerta mostra qual pesou)."""

    componentes: dict[str, Resultado] = field(default_factory=dict)
    m: Resultado = field(default_factory=lambda: Resultado(None, "nao_calculado"))

    def contribuicao(self, nome: str) -> float | None:
        r = self.componentes[nome]
        return None if r.valor is None else COEFICIENTES[nome] * r.valor


def calcula(t: Valores, t1: Valores) -> MScore:
    """Calcula cada componente; o M só existe se os oito forem calculáveis."""
    componentes: dict[str, Resultado] = {}
    for nome, funcao in FUNCOES.items():
        try:
            componentes[nome] = Resultado(funcao(t, t1))
        except NaoCalculavel as e:
            componentes[nome] = Resultado(None, f"{e.motivo}:{e.detalhe}")
    faltando = [n for n, r in componentes.items() if r.valor is None]
    if faltando:
        return MScore(componentes, Resultado(None, "componente_nao_calculavel:" + ",".join(faltando)))
    m = INTERCEPTO + sum(COEFICIENTES[n] * r.valor for n, r in componentes.items() if r.valor is not None)
    return MScore(componentes, Resultado(m))
