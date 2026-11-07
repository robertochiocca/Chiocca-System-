"""Peso de ganhos não recorrentes no resultado (sinal `peso_nao_recorrente` do catálogo, fase mvp).

O que mede: quanto do resultado vem de ganhos pontuais apresentados como se fossem do negócio, inclusive
reversões de provisão. No estudo principal vale só para o grupo das financeiras (pré-registro, Emenda 2,
substituída na fórmula pela Emenda 5, com o alcance da Emenda 7 e a regra de conta-mãe da Emenda 4).

Livro: Financial Shenanigans, 4ª ed., capítulos 5 e 9 (pp. 69-80 e 123-141 do PDF do catálogo).

Financeiras (estudo principal), linhas da DRE achadas por texto em DS_CONTA, com a comparação da Emenda
7 (sem maiúsculas, acentos nem espaços repetidos):
- numerador = máx(0, soma das linhas cujo texto começa com "outras receitas operacionais" ou com
  "outras receitas e despesas operacionais"), contando cada valor uma vez no nível mais alto em que o
  texto aparece (Emenda 4);
- denominador = |linha cujo texto começa com "resultado antes dos tributos"|;
- sem uma das duas linhas, "não calculável" (Emenda 5).

Não financeiras (proxy do catálogo, fora do estudo principal): outras_receitas_operacionais_t / |ebit_t|.
"""

from __future__ import annotations

from typing import Iterable, Mapping

from chiocca.sinais.resultado import CONTA_AUSENTE, NaoCalculavel, Resultado, conta, divide
from chiocca.texto import normaliza

Valores = Mapping[str, float | None]
PREFIXOS_NUMERADOR = ("outras receitas operacionais", "outras receitas e despesas operacionais")
PREFIXO_DENOMINADOR = "resultado antes dos tributos"


def proxy_nao_financeiras(t: Valores) -> Resultado:
    try:
        return Resultado(divide(conta(t, "outras_receitas_operacionais"), abs(conta(t, "ebit")), "ebit"))
    except NaoCalculavel as e:
        return Resultado(None, f"{e.motivo}:{e.detalhe}")


def _e_filha(codigo: str, mae: str) -> bool:
    return codigo.startswith(mae + ".")


def financeiras(linhas_dre: Iterable[tuple[str, str, float]]) -> Resultado:
    """linhas_dre: (CD_CONTA, DS_CONTA, valor) de uma DRE, exercício t."""
    linhas = [(c, normaliza(d), v) for c, d, v in linhas_dre]
    casadas = [(c, v) for c, d, v in linhas if d.startswith(PREFIXOS_NUMERADOR)]
    if not casadas:
        return Resultado(None, f"{CONTA_AUSENTE}:numerador")
    codigos = [c for c, _ in casadas]
    # Emenda 4: entra só a linha cuja conta-mãe não casou também (pelo código: 3.04.04 é mãe de 3.04.04.01).
    topo = [(c, v) for c, v in casadas if not any(_e_filha(c, outra) for outra in codigos if outra != c)]
    numerador = max(0.0, sum(v for _, v in topo))
    denominadores = [v for _, d, v in linhas if d.startswith(PREFIXO_DENOMINADOR)]
    if not denominadores:
        return Resultado(None, f"{CONTA_AUSENTE}:denominador")
    if len(denominadores) > 1:
        return Resultado(None, "denominador_ambiguo")
    if denominadores[0] == 0:
        return Resultado(None, "divisao_por_zero:denominador")
    return Resultado(numerador / abs(denominadores[0]))
