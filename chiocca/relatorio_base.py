"""Relatório da base "como era na época" (Fase 1), gerado nos dois idiomas a partir dos mesmos números.

Números: calculados uma vez de data/base/empresa_ano.csv e gravados em docs/base_numeros.json (versionado).
Textos: docs/base.md (PT) e docs/en/base.md (EN), montados do JSON com os modelos de TEXTOS. Um teste
confere que os dois documentos são iguais ao que este módulo gera e que têm os mesmos números.

Uso: python -m chiocca.relatorio_base
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

from chiocca import base
from chiocca.formato import data, inteiro

RAIZ = base.RAIZ
NUMEROS = RAIZ / "docs" / "base_numeros.json"
DOCS = {"pt": RAIZ / "docs" / "base.md", "en": RAIZ / "docs" / "en" / "base.md"}
STATUS = [
    ("ok_abertos", "ok", "dados_abertos"),
    ("ok_enet", "ok", "enet"),
    ("sem_versao", base.SEM_VERSAO_ATE_CORTE, None),
    ("indisp_individual", base.INDISPONIVEL_INDIVIDUAL, None),
    ("indisp_enet", base.INDISPONIVEL_ENET, None),
    ("pendente_enet", base.PENDENTE_ENET, None),
    ("conta_repetida", base.CONTA_REPETIDA, None),
]


def _status(linha: pd.Series) -> str:
    for chave, status, fonte in STATUS:
        if linha.status == status and (fonte is None or linha.fonte == fonte):
            return chave
    return "outro"


def chaves_enet(meta: pd.DataFrame, pasta_base: Path) -> dict[str, int]:
    """Empresa-anos vindas do ENET com as contas-chave: ativo total (1), receita (3.01) e caixa operacional (6.01)."""
    enet_ok = meta[(meta.status == base.OK) & (meta.fonte == "enet")]
    conta = {"empresa_anos": int(len(enet_ok)), "com_1": 0, "com_301": 0, "com_601": 0}
    for ano, g in enet_ok.groupby("exercicio"):
        c = pd.read_csv(pasta_base / f"contas_{ano}.csv.gz", dtype={"cd_cvm": str, "cd_conta": str})
        c = c[c.ordem == "ÚLTIMO"].merge(g[["cd_cvm", "dt_refer"]], on=["cd_cvm", "dt_refer"])
        for chave, dem, codigo in (("com_1", "BPA", "1"), ("com_301", "DRE", "3.01"), ("com_601", None, "6.01")):
            sel = c[(c.cd_conta == codigo) & ((c.demonstracao == dem) if dem else c.demonstracao.str.startswith("DFC"))]
            conta[chave] += int(sel[["cd_cvm", "dt_refer"]].drop_duplicates().shape[0])
    return conta


def numeros(
    meta: pd.DataFrame,
    gabarito: pd.DataFrame,
    cache_enet: Path,
    data_montagem: str,
    chaves: dict[str, int] | None = None,
) -> dict[str, Any]:
    meta = meta.copy()
    meta["situacao"] = meta.apply(_status, axis=1)
    ok = meta[meta.status == base.OK]
    por_ano = {}
    for ano, g in meta.groupby("exercicio"):
        c = g.situacao.value_counts()
        por_ano[str(ano)] = {"total": int(len(g))} | {k: int(c.get(k, 0)) for k, _, _ in STATUS}
    nf = ok[ok.grupo == "nao_financeira"]
    sem_receita = nf.sem_receita.astype(str).str.lower() == "true"
    # Duas leituras: exercício t e t+1 com versão da época disponível e o mesmo tipo (consolidado ou individual).
    tipos = {(cd, int(ano)): tipo for cd, ano, tipo in zip(ok.cd_cvm, ok.exercicio, ok.tipo)}
    pares = sum(1 for (cd, ano), tipo in tipos.items() if ano <= 2024 and tipos.get((cd, ano + 1)) == tipo)
    pedidos = [linha.split()[0] for linha in (cache_enet / "pendentes.txt").read_text().split("\n") if linha.strip()]
    vazios = sum(
        1 for n in pedidos if (p := cache_enet / f"{n}_con.csv").exists() and len(p.read_text().split("\n")) <= 2
    )
    casos = []
    for caso in gabarito[gabarito.acertavel_principal == "sim"].itertuples():
        ini, fim = max(int(caso.periodo_afetado_inicio), 2010), min(int(caso.periodo_afetado_fim), 2023)
        linhas = meta[(meta.cd_cvm == str(caso.cd_cvm)) & meta.exercicio.between(ini, fim)]
        bons = linhas[linhas.status == base.OK]
        casos.append(
            {
                "caso": caso.caso_id,
                "anos": f"{ini}–{fim}" if ini != fim else str(ini),
                "n_anos": fim - ini + 1,
                "anos_ok": int(bons.exercicio.nunique()),
                "enet": int((bons.fonte == "enet").sum()),
            }
        )
    irb = meta[(meta.cd_cvm == "24180") & (meta.exercicio == 2019)]
    return {
        "data_montagem": data_montagem,
        "anos": [int(min(meta.exercicio)), int(max(meta.exercicio))],
        "por_ano": por_ano,
        "total": {"total": int(len(meta))} | {k: int((meta.situacao == k).sum()) for k, _, _ in STATUS},
        "empresas": int(meta.cd_cvm.nunique()),
        "ok": int(len(ok)),
        "financeiras": int((ok.grupo == "financeira").sum()),
        "nao_financeiras": int(len(nf)),
        "sem_receita": int(sem_receita.sum()),
        "nao_financeiras_com_receita": int((~sem_receita).sum()),
        "plano_outro": int((ok.plano == "outro").sum()),
        "repetidas_iguais": int((ok.repetidas_iguais.astype(int) > 0).sum()),
        "origem_setor": {k: int(v) for k, v in meta.origem_setor.value_counts().items()},
        "cadastro_ok": {k: int(v) for k, v in ok.situacao_cadastro.value_counts().items()},
        "duas_leituras": int(pares),
        "enet": {"pedidos": len(pedidos), "sem_consolidado": int(vazios)} | (chaves or {}),
        "casos_acertaveis": casos,
        "irb_2019": (
            {"status": str(irb.status.iloc[0]), "fonte": str(irb.fonte.iloc[0]) if pd.notna(irb.fonte.iloc[0]) else "—"}
            if len(irb)
            else {}
        ),
    }


TEXTOS: dict[str, dict[str, str]] = {
    "pt": {
        "titulo": '# Base "como era na época" (Fase 1)',
        "aviso": "Gerado por `python -m chiocca.relatorio_base` a partir de `data/base/empresa_ano.csv` (fora do git). "
        "Não edite à mão: um teste compara este arquivo com a saída do script.",
        "montagem": "Base montada em {data}, com os arquivos brutos conferidos contra `data/manifesto_brutos.csv`. "
        "Exercícios de {ini} a {fim}. Nenhum sinal foi calculado nesta fase.",
        "regras_t": "## Regras aplicadas",
        "regras": "- **Versão da época:** a mais recente entregue até a data de corte, que é o último dia do quarto mês "
        "depois do fim do exercício (pré-registro, seção 3, e emenda 5).\n"
        "- **Consolidado quando existir; senão, individual** (emenda 5).\n"
        "- **Versão da época anterior à dos dados abertos:** vem da visualização HTML do ENET, só para o consolidado "
        "(emenda 8). Célula vazia vale 0.\n"
        "- **Conta repetida na mesma demonstração:** com valores iguais, fica uma; com valores diferentes, a "
        "empresa-ano fica não calculável (emenda 8).\n"
        "- **Grupos:** regra congelada da parte 4.1 do reconhecimento, com o FCA na versão entregue até o corte "
        "(emenda 7).\n"
        "- **Duas leituras de cada exercício:** o original (ÚLTIMO na DFP do ano) e o reapresentado (PENÚLTIMO na "
        "DFP do ano seguinte), cada um na versão da sua data de corte.",
        "tabela_t": "## Empresa-anos por exercício e situação",
        "cab": "| Exercício | Empresa-anos | Ok, dados abertos | Ok, ENET | Sem versão até o corte | "
        "Versão da época indisponível (só individual) | Versão da época indisponível (falha do ENET) | "
        "Pendente no ENET | Conta repetida com valores diferentes |",
        "total": "Total",
        "fora_t": '## O que ficou de fora ("não calculável" nesta fase)',
        "fora": "- **Sem versão até o corte:** {sem_versao} empresa-anos. A primeira versão da DFP foi entregue depois da "
        "data de corte; pela emenda 5, a empresa-ano fica de fora naquele ano e é contada aqui.\n"
        "- **Versão da época indisponível, só individual:** {indisp_individual} empresa-anos. A versão dos dados abertos "
        "é posterior ao corte e a empresa não tem consolidado (ou a versão da época não tinha), então a rota do ENET "
        "não se aplica (emenda 8).\n"
        "- **Versão da época indisponível, falha do ENET:** {indisp_enet} empresa-anos (emenda 5).\n"
        "- **Pendente no ENET:** {pendente_enet} empresa-anos ainda sem a tabela baixada.\n"
        "- **Conta repetida com valores diferentes:** {conta_repetida} empresa-anos (emenda 8). Em todos, a repetição "
        "acontece no mesmo período, não em períodos diferentes.\n"
        "- **Sem receita:** {sem_receita} empresa-anos do grupo das não financeiras, com a conta 3.01 ausente ou igual a "
        "zero. Saem da amostra das não financeiras (pré-registro, seção 2, e emenda 9).",
        "grupos_t": "## Grupos e amostra",
        "grupos": "- Empresa-anos com versão da época disponível: {ok}, de {empresas} empresas.\n"
        "- **Financeiras:** {financeiras}. **Não financeiras:** {nao_financeiras}, das quais {com_receita} com "
        "receita.\n"
        "- Plano de contas não reconhecido pela conta 3.01: {plano_outro} empresa-anos (ficam nas não financeiras).\n"
        "- Empresa-anos em que uma conta repetida com valores iguais foi deduplicada: {repetidas_iguais}.\n"
        "- Origem do setor (todas as empresa-anos): FCA {fca}, cadastro {cadastro}, sem setor {nenhum}.\n"
        "- Situação no cadastro de hoje, entre as empresa-anos disponíveis: {cadastro_ok}. As empresas com registro "
        "cancelado continuam na base.",
        "duas_t": "## Duas leituras",
        "duas": "Empresa-anos com o exercício seguinte também disponível, no mesmo tipo de demonstração (exercícios até "
        "2024): {duas}. Nelas dá para comparar o número original com o reapresentado.",
        "enet_t": "## Rota do ENET",
        "enet": "Documentos pedidos ao ENET: {pedidos}. Sem demonstração consolidada na versão da época: {sem_con}. "
        "Empresa-anos que entraram na base pelo ENET: {n_enet}; com ativo total (conta 1): {c1}; com receita "
        "(conta 3.01): {c301}; com caixa operacional (conta 6.01): {c601}.",
        "casos_t": "## Casos acertáveis do gabarito na base (sem valores)",
        "casos_cab": "| Caso | Anos do período afetado nos dados | Anos com versão da época | Desses, pelo ENET |",
        "irb": "IRB, exercício de 2019 (não acertável pela emenda 3): situação `{status}`, fonte `{fonte}`.",
    },
    "en": {
        "titulo": "# Point-in-time base (Phase 1)",
        "aviso": "Generated by `python -m chiocca.relatorio_base` from `data/base/empresa_ano.csv` (outside git). "
        "Do not edit by hand: a test compares this file with the script output.",
        "montagem": "Base built on {data}, with the raw files checked against `data/manifesto_brutos.csv`. "
        "Fiscal years {ini} to {fim}. No signal was computed in this phase.",
        "regras_t": "## Rules applied",
        "regras": "- **Point-in-time version:** the latest one filed by the cut-off date, the last day of the fourth "
        "month after the fiscal year-end (pre-registration, section 3, and amendment 5).\n"
        "- **Consolidated statements when available; otherwise, individual** (amendment 5).\n"
        "- **Point-in-time version older than the open-data one:** taken from the ENET HTML view, for consolidated "
        "statements only (amendment 8). An empty cell counts as 0.\n"
        "- **Repeated account in the same statement:** with equal values, one is kept; with different values, the "
        "company-year is not computable (amendment 8).\n"
        "- **Groups:** frozen rule of part 4.1 of the reconnaissance, with the FCA version filed by the cut-off "
        "(amendment 7).\n"
        "- **Two readings of each fiscal year:** the original (ÚLTIMO in that year's DFP) and the restated one "
        "(PENÚLTIMO in the next year's DFP), each in the version of its own cut-off date.",
        "tabela_t": "## Company-years by fiscal year and status",
        "cab": "| Fiscal year | Company-years | Ok, open data | Ok, ENET | No version by the cut-off | "
        "Point-in-time version unavailable (individual only) | Point-in-time version unavailable (ENET failure) | "
        "Pending in ENET | Repeated account with different values |",
        "total": "Total",
        "fora_t": '## What was left out ("not computable" in this phase)',
        "fora": "- **No version by the cut-off:** {sem_versao} company-years. The first DFP version was filed after the "
        "cut-off date; under amendment 5, the company-year is left out that year and counted here.\n"
        "- **Point-in-time version unavailable, individual only:** {indisp_individual} company-years. The open-data "
        "version postdates the cut-off and the company has no consolidated statements (or the point-in-time version "
        "had none), so the ENET route does not apply (amendment 8).\n"
        "- **Point-in-time version unavailable, ENET failure:** {indisp_enet} company-years (amendment 5).\n"
        "- **Pending in ENET:** {pendente_enet} company-years whose table has not been downloaded yet.\n"
        "- **Repeated account with different values:** {conta_repetida} company-years (amendment 8). In all of them "
        "the repetition happens within the same period, not across periods.\n"
        "- **No revenue:** {sem_receita} company-years in the non-financial group, with account 3.01 missing or equal "
        "to zero. They leave the non-financial sample (pre-registration, section 2, and amendment 9).",
        "grupos_t": "## Groups and sample",
        "grupos": "- Company-years with the point-in-time version available: {ok}, from {empresas} companies.\n"
        "- **Financial companies:** {financeiras}. **Non-financial companies:** {nao_financeiras}, of which "
        "{com_receita} with revenue.\n"
        "- Chart of accounts not recognized from account 3.01: {plano_outro} company-years (kept with the "
        "non-financial companies).\n"
        "- Company-years where a repeated account with equal values was deduplicated: {repetidas_iguais}.\n"
        "- Source of the sector (all company-years): FCA {fca}, registry {cadastro}, no sector {nenhum}.\n"
        "- Status in today's registry, among available company-years: {cadastro_ok}. Delisted companies (registration "
        "cancelled) stay in the base.",
        "duas_t": "## Two readings",
        "duas": "Company-years whose next fiscal year is also available, in the same type of statement (fiscal years "
        "up to 2024): {duas}. For these, the original figure can be compared with the restated one.",
        "enet_t": "## ENET route",
        "enet": "Filings requested from ENET: {pedidos}. With no consolidated statements in the point-in-time version: "
        "{sem_con}. Company-years that entered the base via ENET: {n_enet}; with total assets (account 1): {c1}; with "
        "revenue (account 3.01): {c301}; with operating cash flow (account 6.01): {c601}.",
        "casos_t": "## Detectable ground-truth cases in the base (no values)",
        "casos_cab": "| Case | Affected years in the data | Years with the point-in-time version | Of which via ENET |",
        "irb": "IRB, fiscal year 2019 (not detectable under amendment 3): status `{status}`, source `{fonte}`.",
    },
}
SITUACOES = {
    "pt": {"ATIVO": "ativo", "CANCELADA": "cancelado", "fora_do_cadastro": "fora do cadastro"},
    "en": {"ATIVO": "active", "CANCELADA": "cancelled", "fora_do_cadastro": "not in the registry"},
}


def render(n: dict[str, Any], lang: str) -> str:
    t = TEXTOS[lang]

    def i(x: int) -> str:
        return inteiro(x, lang)

    colunas = ["total"] + [k for k, _, _ in STATUS]
    tabela = [t["cab"], "|" + " --- |" * (len(colunas) + 1)]
    for ano, c in n["por_ano"].items():
        tabela.append(f"| {ano} | " + " | ".join(i(c[k]) for k in colunas) + " |")
    tabela.append(f"| **{t['total']}** | " + " | ".join(f"**{i(n['total'][k])}**" for k in colunas) + " |")
    cad = ", ".join(f"{SITUACOES[lang].get(k, k)} {i(v)}" for k, v in sorted(n["cadastro_ok"].items()))
    casos = [t["casos_cab"], "| --- | --- | --- | --- |"]
    casos += [f"| {c['caso']} | {c['anos']} | {i(c['anos_ok'])} de {i(c['n_anos'])} | {i(c['enet'])} |"
              if lang == "pt" else
              f"| {c['caso']} | {c['anos']} | {i(c['anos_ok'])} of {i(c['n_anos'])} | {i(c['enet'])} |"
              for c in n["casos_acertaveis"]]  # fmt: skip
    partes = [
        t["titulo"],
        t["aviso"],
        t["montagem"].format(data=data(n["data_montagem"], lang), ini=n["anos"][0], fim=n["anos"][1]),
        t["regras_t"],
        t["regras"],
        t["tabela_t"],
        "\n".join(tabela),
        t["fora_t"],
        t["fora"].format(**{k: i(v) for k, v in n["total"].items()}, sem_receita=i(n["sem_receita"])),
        t["grupos_t"],
        t["grupos"].format(
            ok=i(n["ok"]),
            empresas=i(n["empresas"]),
            financeiras=i(n["financeiras"]),
            nao_financeiras=i(n["nao_financeiras"]),
            com_receita=i(n["nao_financeiras_com_receita"]),
            plano_outro=i(n["plano_outro"]),
            repetidas_iguais=i(n["repetidas_iguais"]),
            fca=i(n["origem_setor"].get("fca", 0)),
            cadastro=i(n["origem_setor"].get("cadastro", 0)),
            nenhum=i(n["origem_setor"].get("nenhum", 0)),
            cadastro_ok=cad,
        ),
        t["duas_t"],
        t["duas"].format(duas=i(n["duas_leituras"])),
        t["enet_t"],
        t["enet"].format(
            pedidos=i(n["enet"]["pedidos"]),
            sem_con=i(n["enet"]["sem_consolidado"]),
            n_enet=i(n["enet"].get("empresa_anos", 0)),
            c1=i(n["enet"].get("com_1", 0)),
            c301=i(n["enet"].get("com_301", 0)),
            c601=i(n["enet"].get("com_601", 0)),
        ),
        t["casos_t"],
        "\n".join(casos),
    ]
    if n.get("irb_2019"):
        partes.append(t["irb"].format(**n["irb_2019"]))
    return "\n\n".join(partes) + "\n"


def main() -> None:
    meta = pd.read_csv(RAIZ / "data" / "base" / "empresa_ano.csv", dtype={"cd_cvm": str})
    gab = pd.read_csv(RAIZ / "data" / "gabarito_casos.csv", dtype=str)
    hoje = datetime.now(timezone.utc).date().isoformat()
    n = numeros(meta, gab, base.CACHE_ENET, hoje, chaves_enet(meta, RAIZ / "data" / "base"))
    NUMEROS.write_text(json.dumps(n, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    for lang, caminho in DOCS.items():
        caminho.write_text(render(n, lang), encoding="utf-8")


if __name__ == "__main__":
    main()
