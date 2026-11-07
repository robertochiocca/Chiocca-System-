"""Liga as fórmulas dos sinais às contas da base "como era na época" (PROMPT.md, Fase 2).

Uma empresa-ano chega aqui como as linhas da sua DFP da época (data/base/contas_<ano>.csv.gz: demonstração,
ordem, código, descrição e valor em reais). Daqui saem os valores com os nomes que os módulos de sinais usam.

- **t e t−1:** t vem da coluna ÚLTIMO e t−1 do comparativo PENÚLTIMO da mesma DFP (emenda 5).
- **Contas por código:** os códigos confirmados na Fase 0 (docs/reconhecimento.md, 1.4), que valem para o
  plano de contas não financeiro (conta 3.01 "Receita de Venda de Bens e/ou Serviços"). Conta ausente fica
  ausente (None) e nunca vira zero.
- **Linhas da DFC por texto:** padrões congelados na parte 4.2 do reconhecimento (anexo da emenda 5), com a
  comparação da emenda 7 (sem maiúsculas, acentos nem espaços repetidos):
  - depreciação: seção 6.01.01, contém "deprecia"; somam-se as linhas, e a empresa-ano é marcada se alguma
    também contém "amortiza" ou "exaust" (pré-registro 4.1: usar o total e marcar);
  - juros pagos: seções 6.01 e 6.03, contém "juros" e um de "pago", "pagos", "pagamento", "pagamentos", e não
    contém "capital proprio" nem "recebid". Os que estão em 6.01 saem do caixa operacional (pré-registro 4.1:
    mover para financiamento em todas as empresas); os que já estão em 6.03 não mudam nada;
  - se a conta-mãe e a subconta casam, conta só a mãe (como na emenda 4).
  Os padrões são aplicados à DFC que a empresa-ano tem, pelo método indireto (DFC_MI) ou direto (DFC_MD).
- **Regra boba (emenda 7):** alavancagem = (ativo total − patrimônio líquido) / ativo total, com o patrimônio
  líquido na linha de nível mais alto cuja descrição começa com "patrimonio liquido" (a consolidada, que inclui
  os não controladores). Vale para os dois grupos.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import pandas as pd

from chiocca.sinais.resultado import CONTA_AUSENTE, Resultado
from chiocca.texto import normaliza

ULTIMO, PENULTIMO = "ÚLTIMO", "PENÚLTIMO"

# Nome usado nos sinais -> (demonstração, código), reconhecimento 1.4.
CONTAS: dict[str, tuple[str, str]] = {
    "ativo_total": ("BPA", "1"),
    "ativo_circulante": ("BPA", "1.01"),
    "caixa_equivalentes": ("BPA", "1.01.01"),
    "aplicacoes_financeiras": ("BPA", "1.01.02"),
    "contas_a_receber": ("BPA", "1.01.03"),
    "estoques": ("BPA", "1.01.04"),
    "ativo_nao_circulante": ("BPA", "1.02"),
    "investimentos": ("BPA", "1.02.02"),
    "imobilizado": ("BPA", "1.02.03"),
    "intangivel": ("BPA", "1.02.04"),
    "passivo_circulante": ("BPP", "2.01"),
    "fornecedores": ("BPP", "2.01.02"),
    "ir_csll_a_pagar": ("BPP", "2.01.03.01.01"),
    "emprestimos_cp": ("BPP", "2.01.04"),
    "passivo_nao_circulante": ("BPP", "2.02"),
    "emprestimos_lp": ("BPP", "2.02.01"),
    "patrimonio_liquido": ("BPP", "2.03"),
    "receita_liquida": ("DRE", "3.01"),
    "custo_vendas": ("DRE", "3.02"),
    "resultado_bruto": ("DRE", "3.03"),
    "despesas_vendas": ("DRE", "3.04.01"),
    "despesas_gerais_adm": ("DRE", "3.04.02"),
    "outras_receitas_operacionais": ("DRE", "3.04.04"),
    "ebit": ("DRE", "3.05"),
    "receitas_financeiras": ("DRE", "3.06.01"),
    "despesas_financeiras": ("DRE", "3.06.02"),
    "ir_csll_corrente": ("DRE", "3.08.01"),
    "lucro_operacoes_continuadas": ("DRE", "3.09"),
    "lucro_liquido": ("DRE", "3.11"),
    "caixa_operacional_apresentado": ("DFC", "6.01"),
}


@dataclass(frozen=True)
class Padrao:
    """Padrão de texto da DFC (reconhecimento 4.2): um termo de cada grupo de `contem`, nenhum de `nao_contem`."""

    secoes: tuple[str, ...]
    contem: tuple[tuple[str, ...], ...]
    nao_contem: tuple[str, ...] = ()


DEPRECIACAO = Padrao(secoes=("6.01.01",), contem=(("deprecia",),))
JUROS_PAGOS = Padrao(
    secoes=("6.01", "6.03"),
    contem=(("juros",), ("pago", "pagos", "pagamento", "pagamentos")),
    nao_contem=("capital proprio", "recebid"),
)
MARCA_DEPRECIACAO = ("amortiza", "exaust")
PREFIXO_PL = "patrimonio liquido"


def na_secao(codigo: str, secoes: tuple[str, ...]) -> bool:
    return any(codigo == s or codigo.startswith(s + ".") for s in secoes)


def casa(descricao: str, padrao: Padrao) -> bool:
    d = normaliza(descricao)
    return all(any(t in d for t in grupo) for grupo in padrao.contem) and not any(t in d for t in padrao.nao_contem)


def so_no_topo(codigos: list[str]) -> list[str]:
    """Tira as linhas cuja conta-mãe (em qualquer nível acima) também casou."""
    return [c for c in codigos if not any(c.startswith(outra + ".") for outra in codigos if outra != c)]


@dataclass(frozen=True)
class LinhasDFC:
    soma: float | None  # None quando nenhuma linha casa
    codigos: tuple[str, ...] = ()
    descricoes: tuple[str, ...] = ()

    def contem(self, termos: tuple[str, ...]) -> bool:
        return any(t in normaliza(d) for d in self.descricoes for t in termos)


def linhas_dfc(dfc: pd.DataFrame, padrao: Padrao, secoes: tuple[str, ...] | None = None) -> LinhasDFC:
    """Linhas de uma DFC (uma ordem só) que casam com o padrão; `secoes` restringe a parte delas."""
    alvo = padrao.secoes if secoes is None else secoes
    mascara = [na_secao(c, padrao.secoes) and casa(d, padrao) for c, d in zip(dfc.cd_conta, dfc.ds_conta)]
    casadas = dfc[pd.Series(mascara, index=dfc.index, dtype=bool)]
    topo = set(so_no_topo(list(casadas.cd_conta)))
    escolhidas = casadas[
        pd.Series([c in topo and na_secao(c, alvo) for c in casadas.cd_conta], index=casadas.index, dtype=bool)
    ]
    if escolhidas.empty:
        return LinhasDFC(None)
    return LinhasDFC(float(escolhidas.valor.sum()), tuple(escolhidas.cd_conta), tuple(escolhidas.ds_conta))


@dataclass
class Leitura:
    """Valores de uma ordem (t ou t−1) e as marcas da Fase 2."""

    valores: dict[str, float | None] = field(default_factory=dict)
    depreciacao_combinada: bool = False
    juros_pagos_em_6_01: tuple[str, ...] = ()
    juros_pagos_em_6_03: tuple[str, ...] = ()


def metodo_dfc(contas: pd.DataFrame) -> str | None:
    metodos = sorted(set(d for d in contas.demonstracao if str(d).startswith("DFC")))
    if len(metodos) > 1:
        raise ValueError(f"empresa-ano com mais de uma DFC: {metodos}")
    return metodos[0] if metodos else None


def le_ordem(contas: pd.DataFrame, ordem: str) -> Leitura:
    """Valores de uma empresa-ano numa ordem (ÚLTIMO = t, PENÚLTIMO = t−1), plano não financeiro."""
    linhas = contas[contas.ordem == ordem]
    dem = linhas.demonstracao.where(~linhas.demonstracao.astype(str).str.startswith("DFC"), "DFC")
    por_codigo = {(d, c): float(v) for d, c, v in zip(dem, linhas.cd_conta, linhas.valor)}
    leitura = Leitura({nome: por_codigo.get(chave) for nome, chave in CONTAS.items()})
    dfc = linhas[dem == "DFC"]
    dep = linhas_dfc(dfc, DEPRECIACAO)
    leitura.valores["depreciacao"] = dep.soma
    leitura.depreciacao_combinada = dep.contem(MARCA_DEPRECIACAO)
    jop = linhas_dfc(dfc, JUROS_PAGOS, secoes=("6.01",))
    jfi = linhas_dfc(dfc, JUROS_PAGOS, secoes=("6.03",))
    leitura.juros_pagos_em_6_01, leitura.juros_pagos_em_6_03 = jop.codigos, jfi.codigos
    leitura.valores["juros_pagos_em_6_01"] = jop.soma
    cfo = leitura.valores["caixa_operacional_apresentado"]
    # Pré-registro 4.1: juros pagos vão para o financiamento; os que estavam em 6.01 saem do caixa operacional.
    leitura.valores["caixa_operacional"] = None if cfo is None else cfo - (jop.soma or 0.0)
    return leitura


def linhas_dre(contas: pd.DataFrame, ordem: str = ULTIMO) -> list[tuple[str, str, float]]:
    d = contas[(contas.demonstracao == "DRE") & (contas.ordem == ordem)]
    return list(zip(d.cd_conta, d.ds_conta, d.valor.astype(float)))


def alavancagem(contas: pd.DataFrame, ordem: str = ULTIMO) -> Resultado:
    """Regra boba (emenda 7): (ativo total − patrimônio líquido de nível mais alto) / ativo total."""
    linhas = contas[contas.ordem == ordem]
    ativo = linhas[(linhas.demonstracao == "BPA") & (linhas.cd_conta == "1")]
    if ativo.empty:
        return Resultado(None, f"{CONTA_AUSENTE}:ativo_total")
    pl = linhas[(linhas.demonstracao == "BPP") & linhas.ds_conta.map(lambda s: normaliza(s).startswith(PREFIXO_PL))]
    if pl.empty:
        return Resultado(None, f"{CONTA_AUSENTE}:patrimonio_liquido")
    nivel = pl.cd_conta.str.count(r"\.")
    topo = pl[nivel == nivel.min()]
    if len(topo) > 1:
        return Resultado(None, "patrimonio_liquido_ambiguo")
    at = float(ativo.valor.iloc[0])
    if at == 0:
        return Resultado(None, "divisao_por_zero:ativo_total")
    return Resultado((at - float(topo.valor.iloc[0])) / at)
