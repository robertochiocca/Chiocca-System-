"""Base "como era na época" (PROMPT.md, Fase 1; pré-registro, seção 3 e emendas 5, 7 e 8).

Função central: como_era(fontes, cd_cvm, exercicio, data_corte) devolve as contas da versão da DFP que era
pública na data de corte:
1. versões do documento pelo índice da DFP, cada uma com a data de recebimento (DT_RECEB);
2. a versão da época é a mais recente entregue até a data de corte; sem nenhuma, a empresa-ano fica fora
   ("sem_versao_ate_corte", emenda 5);
3. se a versão da época é a última, as contas vêm dos dados abertos: consolidado quando existir; senão,
   individual (emenda 5);
4. se a versão da época é anterior à dos dados abertos, ela vem do ENET, só para o consolidado (emenda 8);
   empresa só com individual fica "versao_da_epoca_indisponivel" e falha do ENET também (emenda 5);
5. conta repetida na mesma demonstração: valores iguais, fica uma; valores diferentes, a empresa-ano fica
   "nao_calculavel_conta_repetida" (emenda 8).

Cada leitura traz as duas colunas da DFP do ano: ÚLTIMO (o exercício) e PENÚLTIMO (o comparativo, usado
como t-1 pela emenda 5). As duas leituras de um exercício (PROMPT.md) são o ÚLTIMO da DFP do ano e o
PENÚLTIMO da DFP do ano seguinte, cada uma na versão da sua data de corte (duas_leituras).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

import pandas as pd

from chiocca import enet
from chiocca.corte import data_corte
from chiocca.cvm import Fontes

RAIZ = Path(__file__).resolve().parents[1]
BRUTOS = RAIZ / "data" / "brutos" / "cvm"
CACHE_ENET = RAIZ / "data" / "cache" / "enet"

OK = "ok"
SEM_DOCUMENTO = "sem_documento"
SEM_VERSAO_ATE_CORTE = "sem_versao_ate_corte"
INDISPONIVEL_INDIVIDUAL = "versao_da_epoca_indisponivel_individual"
INDISPONIVEL_ENET = "versao_da_epoca_indisponivel_enet"
PENDENTE_ENET = "versao_da_epoca_pendente_enet"
CONTA_REPETIDA = "nao_calculavel_conta_repetida"
COLUNAS = ["demonstracao", "ordem", "cd_conta", "ds_conta", "valor"]


@dataclass
class Leitura:
    cd_cvm: str
    dt_refer: str | None
    data_corte: date | None
    status: str
    versao: int | None = None
    dt_receb: date | None = None
    ultima_versao: int | None = None
    tipo: str | None = None
    fonte: str | None = None
    num_doc: str | None = None
    repetidas_iguais: int = 0
    contas: pd.DataFrame = field(default_factory=lambda: pd.DataFrame(columns=COLUNAS))

    def valores(self, ordem: str = "ÚLTIMO") -> dict[tuple[str, str], float]:
        """(demonstracao, cd_conta) -> valor, para uma coluna da DFP."""
        c = self.contas[self.contas.ordem == ordem]
        return {(d, k): float(v) for d, k, v in zip(c.demonstracao, c.cd_conta, c.valor)}


def _deduplica(contas: pd.DataFrame) -> tuple[pd.DataFrame, int, bool]:
    """Emenda 8: repetidas com valores iguais ficam uma; valores diferentes tornam a empresa-ano não calculável."""
    chave = ["demonstracao", "ordem", "cd_conta"]
    repetidas = contas[contas.duplicated(chave, keep=False)]
    if repetidas.empty:
        return contas, 0, False
    diferentes = bool((repetidas.groupby(chave).valor.nunique() > 1).any())
    n_iguais = int(contas.duplicated(chave).sum())
    return contas.drop_duplicates(chave).reset_index(drop=True), n_iguais, diferentes


def _metodo_dfc(abertas: pd.DataFrame) -> str:
    return (
        "DFC_MD"
        if (abertas.demonstracao == "DFC_MD").any() and not (abertas.demonstracao == "DFC_MI").any()
        else "DFC_MI"
    )


def como_era(
    fontes: Fontes,
    cd_cvm: str,
    exercicio: int,
    corte: date | None = None,
    dt_refer: str | None = None,
    rede: bool = False,
) -> Leitura:
    """Contas da DFP do exercício na versão pública na data de corte (padrão: a do pré-registro)."""
    cd_cvm = str(cd_cvm).lstrip("0") or "0"
    idx = fontes.indice_dfp(exercicio)
    docs = idx[idx.cd_cvm == cd_cvm]
    if dt_refer is not None:
        docs = docs[docs.DT_REFER == dt_refer]
    if docs.empty:
        return Leitura(cd_cvm, dt_refer, corte, SEM_DOCUMENTO)
    dt_refer = str(docs.DT_REFER.max())
    docs = docs[docs.DT_REFER == dt_refer]
    corte = corte or data_corte(dt_refer)
    # Mesma versão listada duas vezes com datas diferentes: vale a data mais tardia (menos informação no corte).
    versoes = docs.groupby("versao").agg(dt_receb=("dt_receb", "max"), num_doc=("num_doc", "last")).reset_index()
    ultima = int(versoes.versao.max())
    validas = versoes[versoes.dt_receb <= corte]
    base = Leitura(cd_cvm, dt_refer, corte, SEM_VERSAO_ATE_CORTE, ultima_versao=ultima)
    if validas.empty:
        return base
    v = validas.sort_values("versao").iloc[-1]
    base.versao, base.dt_receb, base.num_doc = int(v.versao), v.dt_receb, str(v.num_doc)
    abertas = fontes.contas_abertas(exercicio)
    con = abertas.get((cd_cvm, dt_refer, "con"))
    ind = abertas.get((cd_cvm, dt_refer, "ind"))
    if base.versao == ultima:
        escolhida, base.tipo = (con, "con") if con is not None else (ind, "ind")
        if escolhida is None:
            base.status = SEM_DOCUMENTO
            return base
        contas = escolhida[COLUNAS].copy()
        base.fonte = "dados_abertos"
    else:
        if con is None:
            base.status = INDISPONIVEL_INDIVIDUAL
            return base
        cache = fontes.cache_enet
        contas_enet = enet.le_cache(cache, base.num_doc)
        if contas_enet is None and rede:
            try:
                contas_enet = enet.baixa_para_cache(cache, base.num_doc, base.versao)
            except enet.FalhaENET:
                base.status = INDISPONIVEL_ENET
                return base
        if contas_enet is None:
            base.status = PENDENTE_ENET
            return base
        if contas_enet.empty:  # a versão da época não tinha consolidado
            base.status = INDISPONIVEL_INDIVIDUAL
            return base
        contas = contas_enet[COLUNAS].copy()
        contas.loc[contas.demonstracao == "DFC", "demonstracao"] = _metodo_dfc(con)
        base.tipo, base.fonte = "con", "enet"
    contas, base.repetidas_iguais, diferentes = _deduplica(contas.reset_index(drop=True))
    base.contas = contas
    base.status = CONTA_REPETIDA if diferentes else OK
    return base


def duas_leituras(fontes: Fontes, cd_cvm: str, exercicio: int, rede: bool = False) -> pd.DataFrame:
    """Original (ÚLTIMO da DFP de t) e reapresentado (PENÚLTIMO da DFP de t+1), cada um na sua data de corte."""
    a = como_era(fontes, cd_cvm, exercicio, rede=rede)
    b = como_era(fontes, cd_cvm, exercicio + 1, rede=rede)
    if a.status != OK or b.status != OK or a.tipo != b.tipo:
        return pd.DataFrame(columns=["demonstracao", "cd_conta", "ds_conta", "original", "reapresentado"])
    o = a.contas[a.contas.ordem == "ÚLTIMO"][["demonstracao", "cd_conta", "ds_conta", "valor"]]
    r = b.contas[b.contas.ordem == "PENÚLTIMO"][["demonstracao", "cd_conta", "valor"]]
    juntas = o.merge(r, on=["demonstracao", "cd_conta"], how="outer", suffixes=("_o", "_r"))
    return juntas.rename(columns={"valor_o": "original", "valor_r": "reapresentado"})
