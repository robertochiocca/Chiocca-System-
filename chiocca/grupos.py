"""Grupo de cada empresa-ano: financeiras ou não financeiras (docs/reconhecimento.md, 4.1, congelado).

Regra decidida por Roberto em 05/11/2026 (emenda 5 e anexo 4.1), com a versão do FCA da emenda 7:
1. Setor: o do FCA do próprio ano, na versão mais recente entregue até a data de corte (emenda 7). Sem FCA
   do ano até o corte, vale o setor do cadastro.
2. Candidata a financeira: setor com um dos dez nomes exatos de SETORES_CANDIDATOS.
3. Grupo: a candidata é financeira se a DFP usada (consolidada quando existir; senão, individual) está no
   plano de contas de banco ou de seguradora, pela descrição da conta 3.01. No plano não financeiro, a
   empresa-ano fica nas não financeiras. Não candidatas ficam sempre nas não financeiras.
"""

from __future__ import annotations

from datetime import date

import pandas as pd

from chiocca.cvm import Fontes
from chiocca.texto import normaliza

SETORES_CANDIDATOS = frozenset(
    {
        "Bancos",
        "Intermediação Financeira",
        "Arrendamento Mercantil",
        "Seguradoras e Corretoras",
        "Crédito Imobiliário",
        "Emp. Adm. Part. - Bancos",
        "Emp. Adm. Part. - Intermediação Financeira",
        "Emp. Adm. Part. - Arrendamento Mercantil",
        "Emp. Adm. Part. - Seguradoras e Corretoras",
        "Emp. Adm. Part. - Crédito Imobiliário",
    }
)
FINANCEIRA = "financeira"
NAO_FINANCEIRA = "nao_financeira"


def plano_de_contas(descricao_301: object) -> str:
    """Plano pela descrição da conta 3.01 da DRE (reconhecimento, 1.5)."""
    p = normaliza(descricao_301) if isinstance(descricao_301, str) else ""
    if "intermediacao financeira" in p:
        return "banco"
    if p in ("receitas das operacoes", "receitas das atividades seguradoras/resseguradoras"):
        return "seguradora"
    if p.startswith("receita de venda de bens"):
        return "nao_financeiro"
    return "outro"


def setor(fontes: Fontes, cd_cvm: str, ano: int, corte: date) -> tuple[str | None, str]:
    """Setor e de onde veio ('fca' ou 'cadastro'; 'nenhum' se faltar)."""
    f = fontes.fca(ano)
    f = f[(f.cd_cvm == cd_cvm) & (f.dt_receb <= corte)]
    if not f.empty:
        linha = f.sort_values(["versao", "dt_receb"]).iloc[-1]
        if isinstance(linha.setor, str) and linha.setor:
            return linha.setor, "fca"
    cad = fontes.cadastro()
    s = cad.loc[cad.cd_cvm == cd_cvm, "SETOR_ATIV"].dropna()
    if not s.empty:
        return str(s.value_counts().index[0]), "cadastro"
    return None, "nenhum"


def grupo(setor_atividade: str | None, plano: str) -> str:
    if setor_atividade in SETORES_CANDIDATOS and plano in ("banco", "seguradora"):
        return FINANCEIRA
    return NAO_FINANCEIRA


def descricao_301(contas: pd.DataFrame) -> str | None:
    d = contas[(contas.demonstracao == "DRE") & (contas.ordem == "ÚLTIMO") & (contas.cd_conta == "3.01")]
    return None if d.empty else str(d.ds_conta.iloc[0])
