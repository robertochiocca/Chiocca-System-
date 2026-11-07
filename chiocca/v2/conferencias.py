# Origem do princípio: Carchuna (github.com/robertochiocca/carchuna), carchuna/margem.py (identidade estrutural,
# reconciliar e conferir_plausibilidade), commit a3f30ac284eb01245b022b7655bb16c4b8474cc7. Adaptado para o Chiocca
# System. O que mudou: as conferências são novas, para as demonstrações da CVM; da Carchuna veio a separação entre
# identidade, reconciliação por outro caminho e plausibilidade.
"""Conferências de qualidade dos dados da CVM, para cada empresa-ano, sem mudar nenhum sinal do motor v1.

Três tipos, que dizem coisas diferentes:

- **identidade**: igualdade que a contabilidade garante por construção (ativo total = passivo total; subtotais da
  DRE; soma da DFC). Falhar quer dizer erro de preenchimento na CVM ou de leitura, não um ano ruim;
- **reconciliação**: o mesmo número chegando por outro caminho, entre demonstrações (saldo de caixa da DFC contra o
  caixa e equivalentes do balanço). Pode falhar por motivo legítimo (caixa restrito, saldo bancário negativo,
  ativo mantido para venda): o resultado é um aviso, não uma acusação de erro;
- **plausibilidade**: valores fora do que o sinal contábil permite (ativo total não positivo, conta de saldo que
  não pode ser negativa, receita negativa, custo ou despesa com sinal de receita).

Regras:
- os códigos de conta usados são contas fixas da CVM, conferidas no plano não financeiro (reconhecimento, parte 1.4,
  e conferência da Fase B em `docs/conferencias.md`). Nos outros planos, as conferências por código ficam "não se
  aplica", menos ativo total = passivo total e as identidades da DFC, cujos códigos são fixos em todos os planos;
- conta ausente não vira zero: a conferência fica "não se aplica", com a conta que faltou;
- tolerância: R$ 1.000 por parcela da igualdade (uma unidade da escala mais grossa da DFP, R$ mil), só para
  arredondamento.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import pandas as pd

from chiocca.v2.validade import Motivo

ULTIMO, PENULTIMO = "ÚLTIMO", "PENÚLTIMO"
TOLERANCIA_POR_PARCELA = 1000.0
NAO_FINANCEIRO = "nao_financeiro"
IDENTIDADE, RECONCILIACAO, PLAUSIBILIDADE = "identidade", "reconciliacao", "plausibilidade"


@dataclass(frozen=True)
class Termo:
    demonstracao: str  # BPA, BPP, DRE ou DFC (método indireto ou direto)
    cd_conta: str
    sinal: int = 1
    ordem: str | None = None  # None: a coluna da conferência


@dataclass(frozen=True)
class Definicao:
    id: str
    tipo: str
    nome: Motivo
    esquerda: tuple[Termo, ...]
    direita: tuple[Termo, ...]
    so_nao_financeiro: bool = True
    colunas: tuple[str, ...] = (ULTIMO, PENULTIMO)


@dataclass(frozen=True)
class Conferencia:
    id: str
    tipo: str
    nome: Motivo
    coluna: str
    resultado: str  # ok, falhou ou nao_aplicavel
    esquerda: float | None = None
    direita: float | None = None
    tolerancia: float | None = None
    motivo: Motivo | None = None
    contas: tuple[tuple[str, str, str], ...] = field(default_factory=tuple)  # (demonstração, código, coluna)

    @property
    def diferenca(self) -> float | None:
        return None if self.esquerda is None or self.direita is None else self.esquerda - self.direita

    @property
    def diferenca_relativa(self) -> float | None:
        d = self.diferenca
        if d is None or self.esquerda is None or self.direita is None:
            return None
        return abs(d) / max(abs(self.esquerda), abs(self.direita), 1.0)

    @property
    def demonstracoes(self) -> frozenset[str]:
        return frozenset(c[0] for c in self.contas)


def _t(dem: str, *codigos: str, sinal: int = 1, ordem: str | None = None) -> tuple[Termo, ...]:
    return tuple(Termo(dem, c, sinal, ordem) for c in codigos)


DEFINICOES: tuple[Definicao, ...] = (
    Definicao("ativo_igual_passivo", IDENTIDADE, Motivo("ativo total = passivo total", "total assets = total liabilities and equity"),
              _t("BPA", "1"), _t("BPP", "2"), so_nao_financeiro=False),
    Definicao("ativo_partes", IDENTIDADE, Motivo("ativo total = circulante + não circulante", "total assets = current + non-current"),
              _t("BPA", "1"), _t("BPA", "1.01", "1.02")),
    Definicao("passivo_partes", IDENTIDADE,
              Motivo("passivo total = circulante + não circulante + patrimônio líquido",
                     "total liabilities and equity = current + non-current + equity"),
              _t("BPP", "2"), _t("BPP", "2.01", "2.02", "2.03")),
    Definicao("dre_resultado_bruto", IDENTIDADE, Motivo("resultado bruto = receita + custo", "gross profit = revenue + cost of sales"),
              _t("DRE", "3.03"), _t("DRE", "3.01", "3.02")),
    Definicao("dre_ebit", IDENTIDADE,
              Motivo("resultado antes do financeiro = bruto + despesas e receitas operacionais",
                     "operating profit = gross profit + operating expenses and income"),
              _t("DRE", "3.05"), _t("DRE", "3.03", "3.04")),
    Definicao("dre_antes_tributos", IDENTIDADE,
              Motivo("resultado antes dos tributos = antes do financeiro + resultado financeiro",
                     "profit before taxes = operating profit + finance result"),
              _t("DRE", "3.07"), _t("DRE", "3.05", "3.06")),
    Definicao("dre_continuadas", IDENTIDADE,
              Motivo("operações continuadas = antes dos tributos + IR e CSLL",
                     "continuing operations = profit before taxes + income taxes"),
              _t("DRE", "3.09"), _t("DRE", "3.07", "3.08")),
    Definicao("dre_lucro", IDENTIDADE,
              Motivo("lucro do período = continuadas + descontinuadas", "profit for the period = continuing + discontinued"),
              _t("DRE", "3.11"), _t("DRE", "3.09", "3.10")),
    Definicao("dfc_soma", IDENTIDADE,
              Motivo("variação do caixa = operacional + investimento + financiamento + variação cambial",
                     "change in cash = operating + investing + financing + exchange differences"),
              _t("DFC", "6.05"), _t("DFC", "6.01", "6.02", "6.03", "6.04"), so_nao_financeiro=False),
    Definicao("dfc_saldos", IDENTIDADE,
              Motivo("variação do caixa = saldo final − saldo inicial", "change in cash = closing − opening balance"),
              _t("DFC", "6.05"), _t("DFC", "6.05.02") + _t("DFC", "6.05.01", sinal=-1), so_nao_financeiro=False),
    Definicao("dfc_saldo_final_no_balanco", RECONCILIACAO,
              Motivo("saldo final da DFC = caixa e equivalentes do balanço",
                     "cash flow closing balance = cash and cash equivalents on the balance sheet"),
              _t("DFC", "6.05.02"), _t("BPA", "1.01.01")),
    Definicao("dfc_saldo_inicial_no_balanco", RECONCILIACAO,
              Motivo("saldo inicial da DFC = caixa e equivalentes do balanço anterior",
                     "cash flow opening balance = cash and cash equivalents on the prior balance sheet"),
              _t("DFC", "6.05.01", ordem=ULTIMO), _t("BPA", "1.01.01", ordem=PENULTIMO), colunas=(ULTIMO,)),
)  # fmt: skip

# Contas de saldo que não podem ser negativas (plano não financeiro) e sinais esperados da DRE.
SALDO_NAO_NEGATIVO = (("BPA", "1.01"), ("BPA", "1.01.01"), ("BPA", "1.01.03"), ("BPA", "1.01.04"), ("BPA", "1.02"),
                      ("BPA", "1.02.03"), ("BPP", "2.01"), ("BPP", "2.01.02"), ("BPP", "2.02"))  # fmt: skip
SINAL_DRE = (
    ("3.01", 1),
    ("3.02", -1),
    ("3.04.01", -1),
    ("3.04.02", -1),
)  # 1: não pode ser negativa; −1: não pode ser positiva
NOMES_CONTAS = {
    "1.01": ("ativo circulante", "current assets"), "1.01.01": ("caixa e equivalentes", "cash and cash equivalents"),
    "1.01.03": ("contas a receber", "trade receivables"), "1.01.04": ("estoques", "inventories"),
    "1.02": ("ativo não circulante", "non-current assets"), "1.02.03": ("imobilizado", "property, plant and equipment"),
    "2.01": ("passivo circulante", "current liabilities"), "2.01.02": ("fornecedores", "trade payables"),
    "2.02": ("passivo não circulante", "non-current liabilities"), "3.01": ("receita", "net revenue"),
    "3.02": ("custo das vendas", "cost of sales"), "3.04.01": ("despesas com vendas", "selling expenses"),
    "3.04.02": ("despesas gerais e administrativas", "general and administrative expenses"),
}  # fmt: skip


def valores(contas: pd.DataFrame) -> dict[tuple[str, str, str], float]:
    """(demonstração, coluna, código) -> valor, com DFC_MI e DFC_MD juntas como DFC."""
    dem = contas.demonstracao.astype(str).where(~contas.demonstracao.astype(str).str.startswith("DFC"), "DFC")
    return {(d, o, c): float(v) for d, o, c, v in zip(dem, contas.ordem, contas.cd_conta, contas.valor)}


def _nao_aplicavel(d: Definicao, coluna: str, pt: str, en: str) -> Conferencia:
    return Conferencia(d.id, d.tipo, d.nome, coluna, "nao_aplicavel", motivo=Motivo(pt, en))


def _igualdade(d: Definicao, coluna: str, v: dict[tuple[str, str, str], float]) -> Conferencia:
    lados: list[float] = []
    usadas: list[tuple[str, str, str]] = []
    faltando: list[str] = []
    for termos in (d.esquerda, d.direita):
        soma = 0.0
        for t in termos:
            ordem = t.ordem or coluna
            chave = (t.demonstracao, ordem, t.cd_conta)
            usadas.append((t.demonstracao, t.cd_conta, ordem))
            if chave not in v:
                faltando.append(f"{t.demonstracao} {t.cd_conta}")
            else:
                soma += t.sinal * v[chave]
        lados.append(soma)
    if faltando:
        return _nao_aplicavel(
            d, coluna, "conta ausente: " + ", ".join(faltando), "missing account: " + ", ".join(faltando)
        )
    tol = TOLERANCIA_POR_PARCELA * (len(d.esquerda) + len(d.direita))
    ok = abs(lados[0] - lados[1]) <= tol
    motivo = None if ok else Motivo(f"diferença acima da tolerância de R$ {tol:,.0f}".replace(",", "."),
                                    f"difference above the tolerance of R${tol:,.0f}")  # fmt: skip
    return Conferencia(d.id, d.tipo, d.nome, coluna, "ok" if ok else "falhou", lados[0], lados[1], tol, motivo,
                       tuple(usadas))  # fmt: skip


def _tem_coluna(v: dict[tuple[str, str, str], float], coluna: str) -> bool:
    return any(o == coluna for _, o, _ in v)


def conferir(contas: pd.DataFrame, plano: str | None) -> list[Conferencia]:
    """Todas as conferências de uma empresa-ano (as linhas da sua DFP da época, nas duas colunas)."""
    v = valores(contas)
    out: list[Conferencia] = []
    nao_fin = plano == NAO_FINANCEIRO
    for d in DEFINICOES:
        for coluna in d.colunas:
            if not _tem_coluna(v, coluna):
                out.append(_nao_aplicavel(d, coluna, "a DFP não tem essa coluna", "the DFP does not have this column"))
            elif d.so_nao_financeiro and not nao_fin:
                out.append(_nao_aplicavel(d, coluna, f"plano de contas {plano}: códigos não conferidos",
                                          f"chart of accounts {plano}: codes not checked"))  # fmt: skip
            else:
                out.append(_igualdade(d, coluna, v))
    for coluna in (ULTIMO, PENULTIMO):
        if not _tem_coluna(v, coluna):
            continue
        at = v.get(("BPA", coluna, "1"))
        nome_at = Motivo("ativo total positivo", "positive total assets")
        if at is None:
            out.append(Conferencia("ativo_total_positivo", PLAUSIBILIDADE, nome_at, coluna, "nao_aplicavel",
                                   motivo=Motivo("conta ausente: BPA 1", "missing account: BPA 1")))  # fmt: skip
        else:
            ok = at > 0
            out.append(Conferencia("ativo_total_positivo", PLAUSIBILIDADE, nome_at, coluna, "ok" if ok else "falhou", at,
                                   None, None, None if ok else Motivo("ativo total não positivo", "total assets not positive"),
                                   (("BPA", "1", coluna),)))  # fmt: skip
        if not nao_fin:
            continue
        for dem, cod in SALDO_NAO_NEGATIVO:
            out.append(_sinal(f"saldo_negativo:{cod}", dem, cod, coluna, v, 1))
        for cod, sinal in SINAL_DRE:
            out.append(_sinal(f"sinal_dre:{cod}", "DRE", cod, coluna, v, sinal))
    return out


def _sinal(id_: str, dem: str, cod: str, coluna: str, v: dict[tuple[str, str, str], float], sinal: int) -> Conferencia:
    pt, en = NOMES_CONTAS[cod]
    if sinal > 0:
        nome = Motivo(f"{pt} ({cod}) não negativa", f"{en} ({cod}) not negative")
        erro = Motivo(f"{pt} ({cod}) negativa", f"{en} ({cod}) negative")
    else:
        nome = Motivo(f"{pt} ({cod}) não positiva", f"{en} ({cod}) not positive")
        erro = Motivo(f"{pt} ({cod}) com sinal de receita", f"{en} ({cod}) with the sign of income")
    x = v.get((dem, coluna, cod))
    if x is None:
        return Conferencia(id_, PLAUSIBILIDADE, nome, coluna, "nao_aplicavel",
                           motivo=Motivo(f"conta ausente: {dem} {cod}", f"missing account: {dem} {cod}"))  # fmt: skip
    ok = x >= 0 if sinal > 0 else x <= 0
    return Conferencia(id_, PLAUSIBILIDADE, nome, coluna, "ok" if ok else "falhou", x, None, None,
                       None if ok else erro, ((dem, cod, coluna),))  # fmt: skip


def falhas(conferencias: list[Conferencia], tipo: str | None = None) -> list[Conferencia]:
    return [c for c in conferencias if c.resultado == "falhou" and (tipo is None or c.tipo == tipo)]
