# Origem: Carchuna (github.com/robertochiocca/carchuna), carchuna/linhagem.py, commit
# a3f30ac284eb01245b022b7655bb16c4b8474cc7. Adaptado para o Chiocca System.
# O que mudou: as colunas de planilha viraram linhas da DFP da CVM (documento, versão, demonstração, coluna e conta),
# com a localização no arquivo de origem; textos em PT e EN; o montador lê o motor v1 do estudo 1.
"""Linhagem: "como cheguei a este número?", para cada sinal do motor v1 (estudo 1) numa empresa-ano.

Para cada número, uma ficha com:
- o **documento** (DFP, versão, data de entrega, dados abertos ou ENET, endereço e hash do arquivo);
- as **evidências**: cada linha da DFP usada, com demonstração, coluna (ÚLTIMO = t, PENÚLTIMO = t−1), código,
  descrição oficial, valor em reais e a linha do arquivo de origem;
- a **fórmula** e os valores do caso;
- as **transformações** feitas na leitura (escala, juros pagos movidos para o financiamento, padrões de texto da
  DFC, deduplicação), as **premissas** e as **limitações**;
- o **motor** e a função que calcularam, e quando.

A ficha não recalcula nada: o valor do sinal sai do motor v1 (`chiocca.sinais.*`), que fica como está. Ela só
descreve o caminho e aponta as evidências.
"""

from __future__ import annotations

import hashlib
import io
import zipfile
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from typing import Any

import pandas as pd

from chiocca import variaveis
from chiocca.cvm import cd_texto
from chiocca.sinais import dpo, juro_implicito, lucro_sem_caixa, mscore, peso_nao_recorrente
from chiocca.sinais.resultado import Resultado as ResultadoV1
from chiocca.v2.validade import Motivo

MOTOR_V1 = "motor v1 (estudo 1), branch estudo-1-final, commit 8c9a823"
ENET_DOC = (
    "https://www.rad.cvm.gov.br/ENET/frmGerenciaPaginaFRE.aspx?NumeroSequencialDocumento={}&CodigoTipoInstituicao=2"
)
T, T1 = variaveis.ULTIMO, variaveis.PENULTIMO


@dataclass(frozen=True)
class Documento:
    tipo: str  # "DFP"
    cd_cvm: str
    exercicio: int
    dt_refer: str
    num_doc: str | None
    versao: int | None
    dt_receb: str | None
    origem: str  # dados_abertos ou enet
    tipo_demonstracao: str  # con ou ind
    url: str | None = None
    sha256: str | None = None


@dataclass(frozen=True)
class Evidencia:
    id: str
    documento: Documento
    demonstracao: str
    coluna: str
    cd_conta: str
    ds_conta: str
    valor: float
    localizacao: dict[str, Any] | None = None


@dataclass(frozen=True)
class Linhagem:
    sinal: str
    rotulo: Motivo
    valor: float | None
    motivo_v1: str | None
    formula: Motivo
    valores: tuple[tuple[str, str, float | None], ...]  # (variável, coluna, valor)
    entradas: tuple[str, ...]  # ids das evidências
    transformacoes: tuple[Motivo, ...]
    premissas: tuple[Motivo, ...]
    limitacoes: tuple[Motivo, ...]
    motor: str
    codigo: str
    calculado_em: str


@dataclass
class Ficha:
    documento: Documento
    evidencias: dict[str, Evidencia] = field(default_factory=dict)
    linhagens: dict[str, Linhagem] = field(default_factory=dict)


ROTULOS = {
    "DSRI": ("DSRI, índice de dias de recebimento", "DSRI, days' sales in receivables index"),
    "GMI": ("GMI, índice de margem bruta", "GMI, gross margin index"),
    "AQI": ("AQI, índice de qualidade do ativo", "AQI, asset quality index"),
    "SGI": ("SGI, índice de crescimento da receita", "SGI, sales growth index"),
    "DEPI": ("DEPI, índice de depreciação", "DEPI, depreciation index"),
    "SGAI": ("SGAI, índice de despesas de vendas e administrativas", "SGAI, SG&A expenses index"),
    "TATA": ("TATA, accruals totais sobre o ativo", "TATA, total accruals to total assets"),
    "LVGI": ("LVGI, índice de alavancagem", "LVGI, leverage index"),
    "mscore": ("M-score de Beneish", "Beneish M-score"),
    "dpo": ("salto do prazo de pagamento a fornecedores (DPO)", "DPO jump"),
    "juro": ("juro implícito menos CDI médio", "implied interest rate minus average CDI"),
    "lucro_sem_caixa": ("lucro sem caixa (accruals sobre o ativo médio)", "accruals to average total assets"),
    "peso_nao_recorrente": ("peso não recorrente (financeiras)", "non-recurring weight (financial companies)"),
}
FORMULAS = {
    "DSRI": ("(contas a receber ÷ receita) de t ÷ (contas a receber ÷ receita) de t−1",
             "(trade receivables ÷ revenue) in t ÷ (trade receivables ÷ revenue) in t−1"),
    "GMI": ("margem bruta de t−1 ÷ margem bruta de t, com margem = resultado bruto ÷ receita",
            "gross margin in t−1 ÷ gross margin in t, with margin = gross profit ÷ revenue"),
    "AQI": ("[1 − (ativo circulante + imobilizado) ÷ ativo total] de t ÷ o mesmo de t−1",
            "[1 − (current assets + PP&E) ÷ total assets] in t ÷ the same in t−1"),
    "SGI": ("receita de t ÷ receita de t−1", "revenue in t ÷ revenue in t−1"),
    "DEPI": ("taxa de depreciação de t−1 ÷ taxa de t, com taxa = depreciação ÷ (depreciação + imobilizado)",
             "depreciation rate in t−1 ÷ rate in t, with rate = depreciation ÷ (depreciation + PP&E)"),
    "SGAI": ("[(|despesas com vendas| + |despesas gerais e administrativas|) ÷ receita] de t ÷ o mesmo de t−1",
             "[(|selling expenses| + |G&A expenses|) ÷ revenue] in t ÷ the same in t−1"),
    "TATA": ("(resultado das operações continuadas − caixa operacional) ÷ ativo total, em t",
             "(profit from continuing operations − operating cash flow) ÷ total assets, in t"),
    "LVGI": ("[(passivo circulante + empréstimos de longo prazo) ÷ ativo total] de t ÷ o mesmo de t−1",
             "[(current liabilities + long-term borrowings) ÷ total assets] in t ÷ the same in t−1"),
    "mscore": ("−4,84 + 0,920 DSRI + 0,528 GMI + 0,404 AQI + 0,892 SGI + 0,115 DEPI − 0,172 SGAI + 4,679 TATA − 0,327 LVGI",
               "−4.84 + 0.920 DSRI + 0.528 GMI + 0.404 AQI + 0.892 SGI + 0.115 DEPI − 0.172 SGAI + 4.679 TATA − 0.327 LVGI"),
    "dpo": ("fornecedores ÷ |custo das vendas| × 365, em t, menos o mesmo em t−1",
            "trade payables ÷ |cost of sales| × 365, in t, minus the same in t−1"),
    "juro": ("|despesas financeiras de t| ÷ média dos empréstimos (curto + longo prazo) de t e t−1, menos o CDI médio, em pontos percentuais",
             "|finance costs in t| ÷ average borrowings (current + non-current) in t and t−1, minus the average CDI rate, in percentage points"),
    "lucro_sem_caixa": ("(lucro líquido − caixa operacional) ÷ média do ativo total de t e t−1",
                        "(net income − operating cash flow) ÷ average total assets in t and t−1"),
    "peso_nao_recorrente": ('máx(0, soma das linhas "outras receitas operacionais" no nível mais alto) ÷ |resultado antes dos tributos|',
                            'max(0, sum of the top-level "outras receitas operacionais" lines) ÷ |income before taxes|'),
}  # fmt: skip
ENTRADAS: dict[str, list[tuple[str, str]]] = {
    "DSRI": [("contas_a_receber", T), ("receita_liquida", T), ("contas_a_receber", T1), ("receita_liquida", T1)],
    "GMI": [("resultado_bruto", T), ("receita_liquida", T), ("resultado_bruto", T1), ("receita_liquida", T1)],
    "AQI": [("ativo_circulante", T), ("imobilizado", T), ("ativo_total", T), ("ativo_circulante", T1),
            ("imobilizado", T1), ("ativo_total", T1)],
    "SGI": [("receita_liquida", T), ("receita_liquida", T1)],
    "DEPI": [("depreciacao", T), ("imobilizado", T), ("depreciacao", T1), ("imobilizado", T1)],
    "SGAI": [("despesas_vendas", T), ("despesas_gerais_adm", T), ("receita_liquida", T), ("despesas_vendas", T1),
             ("despesas_gerais_adm", T1), ("receita_liquida", T1)],
    "TATA": [("lucro_operacoes_continuadas", T), ("caixa_operacional", T), ("ativo_total", T)],
    "LVGI": [("passivo_circulante", T), ("emprestimos_lp", T), ("ativo_total", T), ("passivo_circulante", T1),
             ("emprestimos_lp", T1), ("ativo_total", T1)],
    "dpo": [("fornecedores", T), ("custo_vendas", T), ("fornecedores", T1), ("custo_vendas", T1)],
    "juro": [("despesas_financeiras", T), ("emprestimos_cp", T), ("emprestimos_lp", T), ("emprestimos_cp", T1),
             ("emprestimos_lp", T1)],
    "lucro_sem_caixa": [("lucro_liquido", T), ("caixa_operacional", T), ("ativo_total", T), ("ativo_total", T1)],
}  # fmt: skip
CODIGO = {c: f"chiocca.sinais.mscore.{c.lower()}" for c in mscore.COEFICIENTES} | {
    "mscore": "chiocca.sinais.mscore.calcula", "dpo": "chiocca.sinais.dpo.variacao",
    "juro": "chiocca.sinais.juro_implicito.juro", "lucro_sem_caixa": "chiocca.sinais.lucro_sem_caixa.accruals",
    "peso_nao_recorrente": "chiocca.sinais.peso_nao_recorrente.financeiras",
}  # fmt: skip
PREMISSAS = (
    Motivo("versão da DFP pública na data de corte (como era na época)", "DFP version public on the cut-off date (point-in-time)"),
    Motivo("t−1 vem do comparativo (PENÚLTIMO) da mesma DFP (emenda 5)", "t−1 comes from the prior-year column (PENÚLTIMO) of the same DFP (amendment 5)"),
    Motivo("consolidado quando existe; senão, individual (emenda 5)", "consolidated when available; otherwise individual (amendment 5)"),
)  # fmt: skip
LIMITACOES = {
    "DEPI": (Motivo("a depreciação vem de linhas da DFC achadas por texto; na DFC pelo método direto não há essa linha",
                    "depreciation comes from cash flow lines found by text; a direct-method statement has no such line"),),
    "TATA": (Motivo("caixa operacional sem os juros pagos que estavam na seção 6.01 (pré-registro, seção 4.1)",
                    "operating cash flow excluding interest paid that was in section 6.01 (pre-registration, section 4.1)"),),
    "dpo": (Motivo("risco sacado informado só em nota explicativa não entra (pré-registro, seção 4.1)",
                   "risco sacado (supplier finance) disclosed only in the notes is not included (pre-registration, section 4.1)"),),
    "juro": (Motivo("a despesa financeira inclui variação cambial, juros de arrendamento e outros itens que não são juros dos empréstimos",
                    "finance costs include exchange differences, lease interest and other items that are not interest on borrowings"),),
    "lucro_sem_caixa": (Motivo("só aparece como contexto: não dispara alerta (pré-registro, seção 4)",
                               "context only: it does not trigger alerts (pre-registration, section 4)"),),
}  # fmt: skip
ROTULOS_VARIAVEIS = {
    "contas_a_receber": ("contas a receber", "trade receivables"), "receita_liquida": ("receita", "revenue"),
    "resultado_bruto": ("resultado bruto", "gross profit"), "ativo_circulante": ("ativo circulante", "current assets"),
    "imobilizado": ("imobilizado", "property, plant and equipment"), "ativo_total": ("ativo total", "total assets"),
    "depreciacao": ("depreciação (DFC)", "depreciation (cash flow statement)"),
    "despesas_vendas": ("despesas com vendas", "selling expenses"),
    "despesas_gerais_adm": ("despesas gerais e administrativas", "general and administrative expenses"),
    "lucro_operacoes_continuadas": ("resultado das operações continuadas", "profit from continuing operations"),
    "caixa_operacional": ("caixa operacional sem juros pagos", "operating cash flow excluding interest paid"),
    "passivo_circulante": ("passivo circulante", "current liabilities"), "emprestimos_lp": ("empréstimos de longo prazo", "long-term borrowings"),
    "emprestimos_cp": ("empréstimos de curto prazo", "short-term borrowings"), "fornecedores": ("fornecedores", "trade payables"),
    "custo_vendas": ("custo das vendas", "cost of sales"), "despesas_financeiras": ("despesas financeiras", "finance costs"),
    "lucro_liquido": ("lucro líquido", "net income"),
}  # fmt: skip


class Localizador:
    """Acha a linha de cada conta no arquivo de origem: o CSV dos dados abertos (dentro do ZIP) ou o cache do ENET."""

    def __init__(self, pasta_brutos: Path, cache_enet: Path, manifesto: Path | None = None) -> None:
        self.pasta_brutos, self.cache_enet = Path(pasta_brutos), Path(cache_enet)
        self._hash: dict[str, str] = {}
        if manifesto is not None and Path(manifesto).exists():
            m = pd.read_csv(manifesto, dtype=str)
            self._hash = dict(zip(m.arquivo, m.sha256))
            self._url = dict(zip(m.arquivo, m.url))
        else:
            self._url = {}
        self._linhas = lru_cache(maxsize=4)(self._indice_aberto)

    def _indice_aberto(self, ano: int, arquivo: str) -> dict[tuple[str, str, int, str, str], tuple[int, str]]:
        with zipfile.ZipFile(self.pasta_brutos / f"dfp_cia_aberta_{ano}.zip") as z:
            d = pd.read_csv(io.BytesIO(z.read(arquivo)), sep=";", encoding="latin1", dtype=str)
        chaves = zip(cd_texto(d.CD_CVM), d.DT_REFER, d.VERSAO.astype(int), d.ORDEM_EXERC, d.CD_CONTA)
        return {k: (i + 2, e) for i, (k, e) in enumerate(zip(chaves, d.ESCALA_MOEDA))}

    def documento_aberto(self, ano: int) -> tuple[str | None, str | None]:
        nome = f"dfp_cia_aberta_{ano}.zip"
        return self._url.get(nome), self._hash.get(nome)

    def sha256_enet(self, num_doc: str) -> str | None:
        p = self.cache_enet / f"{num_doc}_con.csv"
        return hashlib.sha256(p.read_bytes()).hexdigest() if p.exists() else None

    def localizar(self, doc: Documento, demonstracao: str, coluna: str, cd_conta: str) -> dict[str, Any] | None:
        if doc.origem == "enet" and doc.num_doc:
            p = self.cache_enet / f"{doc.num_doc}_con.csv"
            if not p.exists():
                return None
            c = pd.read_csv(p, dtype=str, keep_default_na=False)
            dem = "DFC" if demonstracao.startswith("DFC") else demonstracao
            achou = c.index[(c.demonstracao == dem) & (c.ordem == coluna) & (c.cd_conta == cd_conta)]
            return {"arquivo": f"data/cache/enet/{p.name}", "linha": int(achou[0]) + 2} if len(achou) else None
        arquivo = f"dfp_cia_aberta_{demonstracao}_{doc.tipo_demonstracao}_{doc.exercicio}.csv"
        try:
            indice = self._linhas(doc.exercicio, arquivo)
        except (FileNotFoundError, KeyError):
            return None
        achado = indice.get((doc.cd_cvm, doc.dt_refer, int(doc.versao or 0), coluna, cd_conta))
        if achado is None:
            return None
        return {"arquivo": f"dfp_cia_aberta_{doc.exercicio}.zip/{arquivo}", "linha": achado[0], "escala": achado[1]}


def _id(doc: Documento, demonstracao: str, coluna: str, cd_conta: str) -> str:
    chave = f"{doc.cd_cvm}|{doc.num_doc}|{doc.versao}|{demonstracao}|{coluna}|{cd_conta}"
    return hashlib.sha256(chave.encode()).hexdigest()[:16]


def _linhas(contas: pd.DataFrame, coluna: str, codigos: tuple[str, ...], demonstracao: str) -> pd.DataFrame:
    dem = contas.demonstracao.astype(str)
    alvo = dem.str.startswith("DFC") if demonstracao == "DFC" else dem == demonstracao
    return contas[alvo & (contas.ordem == coluna) & contas.cd_conta.isin(codigos)]


def _resultados_v1(t: dict, t1: dict, contas: pd.DataFrame, cdi_medio: float | None) -> dict[str, ResultadoV1]:
    m = mscore.calcula(t, t1)
    r: dict[str, ResultadoV1] = dict(m.componentes) | {"mscore": m.m}
    r["dpo"] = dpo.variacao(t, t1)
    j = juro_implicito.juro(t, t1)
    if j.valor is None:
        r["juro"] = j
    elif cdi_medio is None:
        r["juro"] = ResultadoV1(None, "cdi_ausente")
    else:
        r["juro"] = ResultadoV1(juro_implicito.spread_pp(j.valor, cdi_medio))
    r["lucro_sem_caixa"] = lucro_sem_caixa.accruals(t, t1)
    return r


def ficha_v1(
    contas: pd.DataFrame,
    doc: Documento,
    grupo: str,
    calculado_em: str,
    cdi_medio: float | None = None,
    localizador: Localizador | None = None,
    repetidas_iguais: int = 0,
) -> Ficha:
    """Linhagem de cada sinal do motor v1 de uma empresa-ano (contas no formato de data/base/contas_<ano>.csv.gz)."""
    ficha = Ficha(doc)

    def evidencia(linha: Any) -> str:
        dem = str(linha.demonstracao)
        eid = _id(doc, dem, str(linha.ordem), str(linha.cd_conta))
        if eid not in ficha.evidencias:
            loc = localizador.localizar(doc, dem, str(linha.ordem), str(linha.cd_conta)) if localizador else None
            ficha.evidencias[eid] = Evidencia(eid, doc, dem, str(linha.ordem), str(linha.cd_conta), str(linha.ds_conta),
                                              float(linha.valor), loc)  # fmt: skip
        return eid

    base = [Motivo("valores convertidos para reais pela escala da DFP (MIL ou UNIDADE)",
                   "values converted to reais by the DFP scale (MIL or UNIDADE)")]  # fmt: skip
    if doc.origem == "enet":
        base.append(Motivo("versão da época lida no ENET, só consolidado; célula vazia vale 0 (emenda 8)",
                           "point-in-time version read from ENET, consolidated only; an empty cell counts as 0 (amendment 8)"))  # fmt: skip
    if repetidas_iguais:
        base.append(Motivo(f"{repetidas_iguais} conta(s) repetida(s) com valores iguais deduplicada(s) (emenda 8)",
                           f"{repetidas_iguais} repeated account(s) with equal values de-duplicated (amendment 8)"))  # fmt: skip

    if grupo == "financeira":
        r = peso_nao_recorrente.financeiras(variaveis.linhas_dre(contas))
        dre = contas[(contas.demonstracao == "DRE") & (contas.ordem == T)]
        prefixos = (*peso_nao_recorrente.PREFIXOS_NUMERADOR, peso_nao_recorrente.PREFIXO_DENOMINADOR)
        from chiocca.texto import normaliza

        usadas = dre[dre.ds_conta.map(lambda s: normaliza(s).startswith(prefixos))]
        ids_fin = tuple(evidencia(x) for x in usadas.itertuples())
        ficha.linhagens["peso_nao_recorrente"] = _montar("peso_nao_recorrente", r, (), ids_fin, tuple(base),
                                                        calculado_em)  # fmt: skip
        return ficha

    t, t1 = variaveis.le_ordem(contas, T), variaveis.le_ordem(contas, T1)
    resultados = _resultados_v1(t.valores, t1.valores, contas, cdi_medio)
    leituras = {T: t, T1: t1}
    for sinal in (*mscore.COEFICIENTES, "mscore", "dpo", "juro", "lucro_sem_caixa"):
        ids: list[str] = []
        valores: list[tuple[str, str, float | None]] = []
        transf = list(base)
        if sinal == "mscore":
            valores = [(c, "", resultados[c].valor) for c in mscore.COEFICIENTES]
            for c in mscore.COEFICIENTES:
                ids += list(ficha.linhagens[c].entradas)
        for var, col in ENTRADAS.get(sinal, []):
            valores.append((var, col, leituras[col].valores.get(var)))
            ids += _ids_variavel(var, col, contas, leituras[col], evidencia, transf)
        if sinal == "juro":
            valores.append(("cdi_medio", "", cdi_medio))
            transf.append(Motivo("CDI médio do ano: média das taxas diárias da série 4389 do SGS do Banco Central nos 12 meses até a data de referência da DFP",
                                 "average CDI rate: mean of the daily rates of Banco Central SGS series 4389 over the 12 months up to the DFP reference date"))  # fmt: skip
        ficha.linhagens[sinal] = _montar(sinal, resultados[sinal], tuple(valores), tuple(dict.fromkeys(ids)),
                                         tuple(dict.fromkeys(transf)), calculado_em)  # fmt: skip
    return ficha


def _ids_variavel(var: str, col: str, contas: pd.DataFrame, leitura: variaveis.Leitura, evidencia: Any,
                  transf: list[Motivo]) -> list[str]:  # fmt: skip
    if var == "depreciacao":
        dfc = contas[contas.demonstracao.astype(str).str.startswith("DFC") & (contas.ordem == col)]
        dep = variaveis.linhas_dfc(dfc, variaveis.DEPRECIACAO)
        transf.append(Motivo('depreciação: soma das linhas da seção 6.01.01 que contêm "deprecia" (reconhecimento, parte 4.2)',
                             'depreciation: sum of the section 6.01.01 lines containing "deprecia" (reconnaissance, part 4.2)'))  # fmt: skip
        if leitura.depreciacao_combinada:
            transf.append(Motivo("depreciação somada com amortização ou exaustão na mesma linha: usado o total, empresa-ano marcada",
                                 "depreciation combined with amortization or depletion in the same line: total used, company-year flagged"))  # fmt: skip
        return [evidencia(x) for x in _linhas(contas, col, dep.codigos, "DFC").itertuples()]
    if var == "caixa_operacional":
        ids = [evidencia(x) for x in _linhas(contas, col, ("6.01",), "DFC").itertuples()]
        if leitura.juros_pagos_em_6_01:
            ids += [evidencia(x) for x in _linhas(contas, col, leitura.juros_pagos_em_6_01, "DFC").itertuples()]
            transf.append(Motivo("juros pagos que estavam na seção 6.01 movidos para o financiamento (pré-registro, seção 4.1)",
                                 "interest paid that was in section 6.01 moved to financing (pre-registration, section 4.1)"))  # fmt: skip
        else:
            transf.append(Motivo("nenhuma linha de juros pagos na seção 6.01: caixa operacional como apresentado",
                                 "no interest-paid line in section 6.01: operating cash flow as reported"))  # fmt: skip
        return ids
    dem, cod = variaveis.CONTAS[var]
    return [evidencia(x) for x in _linhas(contas, col, (cod,), dem).itertuples()]


def _montar(sinal: str, r: ResultadoV1, valores: tuple[tuple[str, str, float | None], ...], ids: tuple[str, ...],
            transf: tuple[Motivo, ...], calculado_em: str) -> Linhagem:  # fmt: skip
    pt, en = ROTULOS[sinal]
    fpt, fen = FORMULAS[sinal]
    return Linhagem(sinal, Motivo(pt, en), r.valor, r.motivo, Motivo(fpt, fen), valores, ids, transf, PREMISSAS,
                    LIMITACOES.get(sinal, ()), MOTOR_V1, CODIGO[sinal], calculado_em)  # fmt: skip


def documento_da_base(meta: Any, localizador: Localizador | None = None) -> Documento:
    """Documento a partir de uma linha de data/base/empresa_ano.csv (base da Fase 1 do estudo 1)."""
    num = None if pd.isna(meta.num_doc) else str(meta.num_doc).split(".")[0]
    origem = str(meta.fonte)
    url = sha = None
    if origem == "enet" and num:
        url = ENET_DOC.format(num)
        sha = localizador.sha256_enet(num) if localizador else None
    elif localizador:
        url, sha = localizador.documento_aberto(int(meta.exercicio))
    return Documento("DFP", str(meta.cd_cvm), int(meta.exercicio), str(meta.dt_refer), num,
                     None if pd.isna(meta.versao) else int(meta.versao), None if pd.isna(meta.dt_receb) else str(meta.dt_receb),
                     origem, str(meta.tipo), url, sha)  # fmt: skip
