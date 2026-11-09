"""Motor v1 em qualquer data de referência (Fase C1): `ExercicioNaData` e o corte transversal na data.

Nada do motor v1 muda. Este módulo só chama o código do estudo 1 (branch `estudo-1-final`) com outra data de corte:
- `chiocca.base.como_era(fontes, cd_cvm, exercicio, corte=data_referencia)`: a versão mais recente entregue até a
  data, consolidado quando existe, ENET para versão anterior do consolidado (emendas 5 e 8);
- `chiocca.grupos`: setor do FCA entregue até a data (senão, do cadastro), plano de contas e grupo;
- `chiocca.sinais_amostra.calcula` e `alertas`: sinais e regras de alerta do pré-registro, com os decis do ano
  recalculados só com as empresas cuja versão era pública na data (contratos, seção 4).

Sem data de referência, cada empresa usa a data de corte do seu exercício, como no estudo 1; é o modo do invariante
(`chiocca.v2.invariante`). Com data de referência, ela passa por `garantir_data_referencia` (30/04/2011 a
31/12/2024), e o exercício, por `garantir_liberado` (até 2023).

A camada do produto vem ao lado, sem mudar nenhum valor do motor: a coluna `produto_nao_calculaveis` lista os sinais
que o produto mostra como "não calculável" porque usam um balanço não preenchido (ativo total zero; conferência
`ativo_total_preenchido` e `chiocca.v2.linhagem.usa_balanco`).

Fase C2:
- `escala_original` da versão usada (dados abertos); o cache do ENET guarda os valores já em reais e não registra a
  escala da página, então versões do ENET ficam sem escala, com o motivo;
- `evidencias`: cada linha da DFP lida, como `Evidencia` do contrato (id estável, documento com versão, data de
  entrega, origem, endereço e hash, demonstração, coluna, conta, valor em reais e, com um `Localizador`, o arquivo e
  a linha de origem);
- nota de linhagem `NOTA_ESTRUTURA_POSTERIOR` quando a versão usada não é a última: o `como_era` lê a estrutura da
  última versão (se há consolidado e o método da DFC), entregue depois da data (comportamento do estudo 1, emenda 8).
"""

from __future__ import annotations

import tempfile
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Any, Protocol

import pandas as pd

from chiocca import base, grupos, montar_base, sinais_amostra
from chiocca.sinais.mscore import COEFICIENTES
from chiocca.v2 import comparativo
from chiocca.v2 import conferencias as cf
from chiocca.v2.lacre import garantir_data_referencia, garantir_liberado
from chiocca.v2.linhagem import ENET_DOC, Documento, Evidencia, Localizador, id_evidencia, usa_balanco
from chiocca.v2.validade import Motivo

# Estados de `como_era` com o nome do contrato (ExercicioNaData.situacao).
SITUACAO = {
    base.OK: "ok",
    base.SEM_DOCUMENTO: "sem_documento",
    base.SEM_VERSAO_ATE_CORTE: "sem_versao_ate_a_data",
    base.INDISPONIVEL_INDIVIDUAL: "versao_indisponivel_individual",
    base.INDISPONIVEL_ENET: "versao_indisponivel_enet",
    base.PENDENTE_ENET: "versao_pendente_enet",
    base.CONTA_REPETIDA: "conta_repetida",
}
SINAIS_PRODUTO = (*COEFICIENTES, "mscore", "dpo", "juro", "lucro_sem_caixa")
NOTA_ESTRUTURA_POSTERIOR = Motivo(
    "estrutura lida de documento posterior à data (comportamento do estudo 1, emenda 8)",
    "structure read from a document filed after the date (study 1 behaviour, amendment 8)",
)
SEM_ESCALA_ENET = Motivo(
    "versão do ENET: o cache guarda os valores já em reais e não registrou a escala da página (buscas anteriores a 09/11/2026)",
    "ENET version: the cache keeps values already in reais and did not record the page's scale (fetches before 2026-11-09)",
)


class FontesV1(Protocol):
    """A interface que o motor v1 lê: `chiocca.cvm.Fontes` ou `chiocca.v2.armazem.FontesArmazem`."""

    cache_enet: Path

    def indice_dfp(self, ano: int) -> pd.DataFrame: ...
    def contas_abertas(self, ano: int) -> dict[tuple[str, str, str], pd.DataFrame]: ...
    def fca(self, ano: int) -> pd.DataFrame: ...
    def cadastro(self) -> pd.DataFrame: ...


@dataclass
class ExercicioNaData:
    """Uma empresa num exercício, como era na data de referência (contratos, seção 2)."""

    cd_cvm: str
    exercicio: int
    dt_refer: str | None
    data_referencia: date | None
    situacao: str
    versao_usada: int | None
    dt_receb: date | None
    versoes_conhecidas: tuple[tuple[int, date], ...]
    tipo: str | None
    origem: str | None
    num_doc: str | None
    link: str | None
    contas: pd.DataFrame = field(repr=False)
    status_motor: str = ""
    escala_original: str | None = None
    documento: Documento | None = None
    evidencias: tuple[Evidencia, ...] = field(default=(), repr=False)
    diferencas_comparativo: tuple[comparativo.DiferencaComparativo, ...] = field(default=(), repr=False)
    notas: tuple[Motivo, ...] = ()


def estrutura_posterior(leitura: base.Leitura, docs: pd.DataFrame) -> bool:
    """O `como_era` leu a estrutura da última versão, entregue depois da data? (a versão usada não é a última)"""
    if leitura.versao is None or leitura.ultima_versao is None or leitura.versao == leitura.ultima_versao:
        return False
    receb = docs.loc[docs.versao == leitura.ultima_versao, "dt_receb"]
    return bool(not receb.empty and leitura.data_corte is not None and receb.max() > leitura.data_corte)


def _documento(e: ExercicioNaData, localizador: Localizador | None) -> Documento:
    url = sha = None
    if e.origem == "enet" and e.num_doc:
        url = ENET_DOC.format(e.num_doc)
        sha = localizador.sha256_enet(e.num_doc) if localizador else None
    elif localizador:
        url, sha = localizador.documento_aberto(e.exercicio)
    receb = None if e.dt_receb is None else str(e.dt_receb)
    return Documento("DFP", e.cd_cvm, e.exercicio, str(e.dt_refer), e.num_doc, e.versao_usada, receb, str(e.origem),
                     str(e.tipo), url, sha, e.notas)  # fmt: skip


def evidencias(contas: pd.DataFrame, doc: Documento, localizador: Localizador | None = None) -> tuple[Evidencia, ...]:
    """Cada linha da DFP lida, como `Evidencia` do contrato (seção 2)."""
    out: dict[str, Evidencia] = {}
    for linha in contas.itertuples(index=False):
        dem, col, cod = str(linha.demonstracao), str(linha.ordem), str(linha.cd_conta)
        eid = id_evidencia(doc, dem, col, cod)
        if eid in out:
            continue
        loc = localizador.localizar(doc, dem, col, cod) if localizador else None
        out[eid] = Evidencia(eid, doc, dem, col, cod, str(linha.ds_conta), float(linha.valor), loc)
    return tuple(out.values())


def exercicio_na_data(
    fontes: FontesV1,
    cd_cvm: str,
    exercicio: int,
    data_referencia: date | str,
    dt_refer: str | None = None,
    localizador: Localizador | None = None,
) -> ExercicioNaData:
    garantir_liberado(exercicio)
    d = garantir_data_referencia(data_referencia)
    leitura = base.como_era(fontes, cd_cvm, exercicio, corte=d, dt_refer=dt_refer)  # type: ignore[arg-type]
    idx = fontes.indice_dfp(exercicio)
    docs = idx[(idx.cd_cvm == leitura.cd_cvm) & (idx.DT_REFER == leitura.dt_refer)]
    por_versao = docs.groupby("versao").agg(dt_receb=("dt_receb", "max"), link=("LINK_DOC", "last")).reset_index()
    conhecidas = por_versao[por_versao.dt_receb <= d].sort_values("versao")
    link = None
    if leitura.versao is not None:
        lk = conhecidas.loc[conhecidas.versao == leitura.versao, "link"]
        link = None if lk.empty else str(lk.iloc[0])
    notas: tuple[Motivo, ...] = (NOTA_ESTRUTURA_POSTERIOR,) if estrutura_posterior(leitura, docs) else ()
    escala = None
    ler_escala = getattr(fontes, "escala", None)  # só o armazém tem a escala original
    if leitura.fonte is not None and leitura.versao is not None and ler_escala is not None:
        escala = ler_escala(exercicio, leitura.cd_cvm, str(leitura.dt_refer), leitura.versao, str(leitura.tipo))
    if leitura.fonte == "enet" and escala is None:
        notas += (SEM_ESCALA_ENET,)
    e = ExercicioNaData(
        cd_cvm=leitura.cd_cvm, exercicio=exercicio, dt_refer=leitura.dt_refer, data_referencia=d,
        situacao=SITUACAO.get(leitura.status, leitura.status), versao_usada=leitura.versao, dt_receb=leitura.dt_receb,
        versoes_conhecidas=tuple((int(v), r) for v, r in zip(conhecidas.versao, conhecidas.dt_receb)),
        tipo=leitura.tipo, origem=leitura.fonte, num_doc=leitura.num_doc, link=link, contas=leitura.contas,
        status_motor=leitura.status, escala_original=escala, notas=notas,
    )  # fmt: skip
    if leitura.fonte is not None:
        e.documento = _documento(e, localizador)
        e.evidencias = evidencias(leitura.contas, e.documento, localizador)
        e.diferencas_comparativo = comparativo.diferencas(fontes, leitura, exercicio, d)
    return e


def nao_calculaveis_no_produto(contas: pd.DataFrame, plano: str | None) -> list[str]:
    """Sinais do motor v1 que o produto mostra como "não calculável" por balanço não preenchido."""
    colunas = cf.colunas_nao_preenchidas(cf.conferir(contas, plano if isinstance(plano, str) else "outro"))
    return [s for s in SINAIS_PRODUTO if any(usa_balanco(s, c) for c in colunas)]


def _meta(
    fontes: FontesV1, exercicio: int, corte: date | None, so: set[str] | None = None
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """As empresa-anos do exercício na data, com os mesmos campos de `chiocca.montar_base.monta` (`so`: só essas)."""
    sit = montar_base.situacao_cadastro(fontes)  # type: ignore[arg-type]
    idx = fontes.indice_dfp(exercicio)
    pares = idx[["cd_cvm", "DT_REFER", "CNPJ_CIA", "DENOM_CIA"]].drop_duplicates(["cd_cvm", "DT_REFER"])
    if so is not None:
        pares = pares[pares.cd_cvm.isin(so)]
    linhas: list[dict[str, Any]] = []
    partes = []
    for p in pares.itertuples():
        leitura = base.como_era(fontes, p.cd_cvm, exercicio, corte=corte, dt_refer=p.DT_REFER)  # type: ignore[arg-type]
        st, origem = (
            grupos.setor(fontes, p.cd_cvm, exercicio, leitura.data_corte)  # type: ignore[arg-type]
            if leitura.data_corte
            else (None, "nenhum")
        )
        ok = leitura.status == base.OK
        plano = grupos.plano_de_contas(grupos.descricao_301(leitura.contas)) if ok else None
        rec = montar_base.receita(leitura.contas) if ok else None
        linhas.append({
            "exercicio": exercicio, "cd_cvm": p.cd_cvm, "dt_refer": p.DT_REFER, "cnpj": p.CNPJ_CIA,
            "denominacao": p.DENOM_CIA, "data_corte": leitura.data_corte, "status": leitura.status,
            "versao": leitura.versao, "dt_receb": leitura.dt_receb, "ultima_versao": leitura.ultima_versao,
            "tipo": leitura.tipo, "fonte": leitura.fonte, "num_doc": leitura.num_doc,
            "repetidas_iguais": leitura.repetidas_iguais, "setor": st, "origem_setor": origem, "plano": plano,
            "grupo": grupos.grupo(st, plano) if plano else None,
            "sem_receita": (rec is None or rec == 0) if ok else None,
            "situacao_cadastro": sit.get(p.cd_cvm, "fora_do_cadastro"),
            "produto_nao_calculaveis": ";".join(nao_calculaveis_no_produto(leitura.contas, plano)) if ok else "",
            "estrutura_de_documento_posterior": estrutura_posterior(
                leitura, idx[(idx.cd_cvm == p.cd_cvm) & (idx.DT_REFER == p.DT_REFER)]),
        })  # fmt: skip
        if ok:
            c = leitura.contas.copy()
            c.insert(0, "dt_refer", leitura.dt_refer)
            c.insert(0, "cd_cvm", leitura.cd_cvm)
            partes.append(c)
    contas = (
        pd.concat(partes, ignore_index=True) if partes else pd.DataFrame(columns=["cd_cvm", "dt_refer", *base.COLUNAS])
    )
    return pd.DataFrame(linhas), contas


def corte_transversal(
    fontes: FontesV1, exercicio: int, data_referencia: date | str | None = None
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Sinais e alertas do motor v1 de todas as empresas do exercício, como eram na data de referência.

    Devolve (sinais, limiares): `sinais` tem as colunas de `resultados/sinais_empresa_ano.csv` mais
    `produto_nao_calculaveis`; `limiares` tem o limite do decil superior de cada sinal e grupo na data.
    """
    s, limiares, _, _ = corte_transversal_completo(fontes, exercicio, data_referencia)
    return s, limiares


def _sinais(meta: pd.DataFrame, contas: pd.DataFrame, exercicio: int) -> pd.DataFrame:
    # Mesmo caminho do estudo 1: as contas passam por um CSV como em data/base, e o motor v1 lê de lá.
    with tempfile.TemporaryDirectory() as pasta:
        contas.to_csv(Path(pasta) / f"contas_{exercicio}.csv.gz", index=False)
        s = sinais_amostra.calcula(meta, Path(pasta), range(exercicio, exercicio + 1))
    # Numa data em que um grupo não tem nenhuma empresa, a coluna do sinal dele não existe; as regras precisam dela.
    for col in ("mscore", "dpo", "juro", "peso_nao_recorrente", "alavancagem"):
        if col not in s.columns:
            s[col] = float("nan")
    return s


def corte_transversal_completo(
    fontes: FontesV1, exercicio: int, data_referencia: date | str | None = None
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """O corte transversal com as contas e o meta de cada empresa-ano (para a investigação): (sinais, limiares,
    contas, meta). Os sinais e alertas são os mesmos de `corte_transversal`."""
    garantir_liberado(exercicio)
    corte = garantir_data_referencia(data_referencia) if data_referencia is not None else None
    meta, contas = _meta(fontes, exercicio, corte)
    s = _sinais(meta, contas, exercicio)
    s, limiares = sinais_amostra.alertas(s)
    s["produto_nao_calculaveis"] = meta.produto_nao_calculaveis.values
    s["estrutura_de_documento_posterior"] = meta.estrutura_de_documento_posterior.values
    s.insert(1, "data_referencia", corte)
    return s, limiares, contas, meta


def sinais_da_empresa(
    fontes: FontesV1, cd_cvm: str, exercicio: int, data_referencia: date
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Valores dos sinais do motor v1 de uma empresa num exercício, na data (sem alertas: os decis precisam do
    corte inteiro). Para o histórico da investigação. Devolve (sinais, contas, meta)."""
    garantir_liberado(exercicio)
    meta, contas = _meta(fontes, exercicio, data_referencia, so={str(cd_cvm)})
    if meta.empty:
        return pd.DataFrame(), contas, meta
    return _sinais(meta, contas, exercicio), contas, meta
