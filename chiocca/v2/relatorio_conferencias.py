"""Conferências de qualidade na base inteira do estudo 1, até o lacre: só números agregados, em PT e EN.

Lê a base "como era na época" da Fase 1 (data/base/, fora do git), roda `chiocca.v2.conferencias.conferir` em todas
as empresa-anos com versão da época até `ULTIMO_EXERCICIO_LIBERADO` e grava:
- docs/conferencias_numeros.json (versionado);
- docs/conferencias.md (PT) e docs/en/data-checks.md (EN), montados do JSON.
Nenhuma empresa é citada. As conferências não mudam nenhum sinal, alerta ou número do estudo 1.

Uso: python -m chiocca.v2.relatorio_conferencias
"""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path
from typing import Any

import pandas as pd

from chiocca.base import RAIZ
from chiocca.formato import inteiro, pct
from chiocca.v2 import conferencias as cf
from chiocca.v2.lacre import ULTIMO_EXERCICIO_LIBERADO, so_liberados

BASE = RAIZ / "data" / "base"
NUMEROS = RAIZ / "docs" / "conferencias_numeros.json"
DOCS = {"pt": RAIZ / "docs" / "conferencias.md", "en": RAIZ / "docs" / "en" / "data-checks.md"}
FAIXAS = (("ate_0_1", 0.001), ("ate_1", 0.01), ("ate_10", 0.10), ("acima_10", float("inf")))


def _tipo_nao_aplicavel(c: cf.Conferencia) -> str:
    texto = c.motivo.en if c.motivo else ""
    if texto.startswith("missing account"):
        return "conta_ausente"
    if texto.startswith("chart of accounts"):
        return "plano"
    return "sem_coluna"


def calcula(meta: pd.DataFrame, base: Path = BASE) -> dict[str, Any]:
    meta = so_liberados(meta)
    meta = meta[meta.status == "ok"]
    por: dict[str, Any] = {}
    falha_empresa_ano: dict[str, set[tuple[str, str]]] = defaultdict(set)
    por_ano: dict[str, dict[str, int]] = {}
    planos: dict[str, int] = defaultdict(int)
    diagnostico: dict[str, Any] = {"caixa_falhas": 0, "caixa_fecha_com_aplicacoes": 0,
                                   "ativo_zero": {cf.ULTIMO: 0, cf.PENULTIMO: 0},
                                   "identidade_falhas": 0, "identidade_lado_zero": 0}  # fmt: skip
    for ano in sorted(meta.exercicio.unique()):
        m = meta[meta.exercicio == ano]
        contas = pd.read_csv(base / f"contas_{ano}.csv.gz", dtype={"cd_cvm": str, "cd_conta": str, "ds_conta": str})
        grupos = {k: g for k, g in contas.groupby(["cd_cvm", "dt_refer"])}
        com_falha = 0
        for e in m.itertuples(index=False):
            chave = (e.cd_cvm, e.dt_refer)
            plano = e.plano if isinstance(e.plano, str) else "outro"
            planos[plano] += 1
            confs = cf.conferir(grupos[chave], plano)
            v = cf.valores(grupos[chave])
            falhou_identidade = False
            for c in confs:
                d = por.setdefault(c.id, {"tipo": c.tipo, "nome_pt": c.nome.pt, "nome_en": c.nome.en, "colunas": {}})
                x = d["colunas"].setdefault(c.coluna, {"aplicaveis": 0, "falhas": 0, "nao_aplicaveis": {},
                                                        "faixas": {f: 0 for f, _ in FAIXAS},
                                                        "falhas_por_origem": {}})  # fmt: skip
                if c.resultado == "nao_aplicavel":
                    t = _tipo_nao_aplicavel(c)
                    x["nao_aplicaveis"][t] = x["nao_aplicaveis"].get(t, 0) + 1
                    continue
                x["aplicaveis"] += 1
                if c.resultado == "falhou":
                    x["falhas"] += 1
                    origem = str(e.fonte)
                    x["falhas_por_origem"][origem] = x["falhas_por_origem"].get(origem, 0) + 1
                    rel = c.diferenca_relativa
                    if rel is not None:
                        x["faixas"][next(f for f, lim in FAIXAS if rel <= lim)] += 1
                    if c.tipo == cf.IDENTIDADE and c.coluna == cf.ULTIMO:
                        diagnostico["identidade_falhas"] += 1
                        diagnostico["identidade_lado_zero"] += int(c.esquerda == 0 or c.direita == 0)
                    if c.id == "ativo_total_positivo" and c.esquerda == 0:
                        diagnostico["ativo_zero"][c.coluna] += 1
                    if c.id == "dfc_saldo_final_no_balanco" and c.coluna == cf.ULTIMO:
                        diagnostico["caixa_falhas"] += 1
                        caixa = v.get(("BPA", cf.ULTIMO, "1.01.01"), 0.0) + v.get(("BPA", cf.ULTIMO, "1.01.02"), 0.0)
                        if c.esquerda is not None and abs(c.esquerda - caixa) <= 3 * cf.TOLERANCIA_POR_PARCELA:
                            diagnostico["caixa_fecha_com_aplicacoes"] += 1
                    if c.coluna == cf.ULTIMO:
                        falha_empresa_ano[c.tipo].add(chave)
                        falha_empresa_ano["qualquer"].add(chave)
                        falhou_identidade |= c.tipo == cf.IDENTIDADE
            com_falha += falhou_identidade
        por_ano[str(int(ano))] = {"empresa_anos": int(len(m)), "com_falha_de_identidade": com_falha}
    return {
        "ultimo_exercicio": ULTIMO_EXERCICIO_LIBERADO,
        "empresa_anos": int(len(meta)),
        "planos": dict(sorted(planos.items(), key=lambda kv: -kv[1])),
        "origens": {k: int(v) for k, v in meta.fonte.value_counts().items()},
        "conferencias": por,
        "empresa_anos_com_falha": {k: len(v) for k, v in falha_empresa_ano.items()},
        "por_ano": por_ano,
        "tolerancia_por_parcela": cf.TOLERANCIA_POR_PARCELA,
        "diagnostico": diagnostico,
    }


T: dict[str, dict[str, Any]] = {
    "pt": {
        "titulo": "# Conferências de qualidade dos dados da CVM (Fase B do v2)",
        "gerado": "Gerado por `python -m chiocca.v2.relatorio_conferencias` a partir de `data/base/` (fora do git), a base \"como era na época\" do estudo 1. Não edite à mão: um teste compara este arquivo com a saída do script. Só números agregados; nenhuma empresa é citada.",
        "escopo": "Empresa-anos com versão da época, de 2010 até o lacre ({ultimo}): {n}. Dados abertos: {abertos}; ENET: {enet}. Por plano de contas: {planos}.",
        "nao_muda": "As conferências descrevem os dados. Elas não mudam nenhum sinal, alerta ou número do estudo 1: um número com conferência falha só leva o estado \"implausível\" e o critério de consistência na confiança.",
        "h_tipos": "## O que cada tipo de conferência quer dizer",
        "tipos": [
            "**Identidade:** igualdade garantida pela contabilidade (ativo total = passivo total, subtotais do balanço e da DRE, soma e saldos da DFC). Falhar indica erro de preenchimento na CVM ou de leitura, não um ano ruim.",
            "**Reconciliação:** o mesmo número por outro caminho, entre demonstrações (saldo de caixa da DFC contra o caixa e equivalentes do balanço). Pode falhar por motivo legítimo, como caixa restrito, saldo bancário negativo ou ativo mantido para venda.",
            "**Plausibilidade:** valor fora do que o sinal contábil permite (ativo total não positivo, conta de saldo negativa, receita negativa, custo ou despesa com sinal de receita).",
        ],
        "regras": "Tolerância de R$ {tol} por parcela da igualdade, só para arredondamento. Conta ausente não vira zero: a conferência fica \"não se aplica\". Os códigos por conta valem para o plano não financeiro; nos outros planos, só ativo total = passivo total e as identidades da DFC, cujos códigos são fixos em todos os planos.",
        "h_resumo": "## Resumo",
        "resumo": "Empresa-anos com pelo menos uma falha no exercício (coluna ÚLTIMO): {qualquer} de {n} ({pq}). Por tipo: identidade, {ident} ({pi}); reconciliação, {recon} ({pr}); plausibilidade, {plaus} ({pp}).",
        "h_tabela": "## Resultado por conferência, no exercício (coluna ÚLTIMO)",
        "h_tabela_t1": "## Resultado por conferência, no comparativo (coluna PENÚLTIMO)",
        "col": "| Conferência | Tipo | Aplicáveis | Falhas | Parte | Diferença até 0,1% | 0,1% a 1% | 1% a 10% | Acima de 10% | Falhas em dados abertos | Falhas no ENET |",
        "faixas_nota": "As faixas medem a diferença entre os dois lados da igualdade em proporção do maior deles; não se aplicam às conferências de plausibilidade (—).",
        "diagnostico": "**Leitura das falhas mais frequentes.** Das {cf} falhas de \"saldo final da DFC = caixa e equivalentes do balanço\" no exercício, {ca} fecham quando se somam as aplicações financeiras (1.01.02) ao caixa: a empresa usa na DFC um conceito de caixa mais amplo que o da conta 1.01.01, o que é escolha de apresentação e não erro de leitura. Das falhas de \"ativo total positivo\", {zu} no exercício e {zp} no comparativo têm o ativo total igual a zero, o que indica comparativo não preenchido. Das {fi} falhas de identidade no exercício, {fz} têm um dos lados igual a zero (subtotal ou soma não preenchidos); as empresa-anos com falha de identidade estão nos exercícios {anos_falha} (tabela por exercício abaixo).",
        "h_na": "## Não se aplica, por motivo (coluna ÚLTIMO)",
        "col_na": "| Conferência | Conta ausente | Outro plano de contas | Sem a coluna |",
        "h_ano": "## Empresa-anos com falha de identidade, por exercício (coluna ÚLTIMO)",
        "col_ano": "| Exercício | Empresa-anos | Com falha de identidade | Parte |",
        "tipo": {"identidade": "identidade", "reconciliacao": "reconciliação", "plausibilidade": "plausibilidade"},
        "planos": {"nao_financeiro": "não financeiro", "banco": "banco", "seguradora": "seguradora", "outro": "não reconhecido"},
    },
    "en": {
        "titulo": "# CVM data quality checks (v2, Phase B)",
        "gerado": "Generated by `python -m chiocca.v2.relatorio_conferencias` from `data/base/` (not in git), study 1's point-in-time base. Do not edit by hand: a test compares this file with the script output. Aggregate numbers only; no company is named.",
        "escopo": "Company-years with a point-in-time version, from 2010 up to the seal ({ultimo}): {n}. Open data: {abertos}; ENET: {enet}. By chart of accounts: {planos}.",
        "nao_muda": "The checks describe the data. They change no signal, alert or number from study 1: a number with a failed check only carries the \"implausible\" state and the consistency criterion in the confidence.",
        "h_tipos": "## What each type of check means",
        "tipos": [
            "**Identity:** an equality guaranteed by the accounting (total assets = total liabilities and equity, balance sheet and income statement subtotals, cash flow sum and balances). A failure points to a filing error at the CVM or a reading error, not a bad year.",
            "**Reconciliation:** the same number through another path, across statements (cash flow closing balance against cash and cash equivalents on the balance sheet). It can fail for a legitimate reason, such as restricted cash, bank overdrafts or assets held for sale.",
            "**Plausibility:** a value outside what the accounting sign allows (non-positive total assets, a negative balance account, negative revenue, a cost or expense with the sign of income).",
        ],
        "regras": "Tolerance of R${tol} per term of the equality, for rounding only. A missing account does not become zero: the check is marked \"not applicable\". The per-account codes apply to the non-financial chart of accounts; for the other charts, only total assets = total liabilities and equity and the cash flow identities, whose codes are fixed in every chart.",
        "h_resumo": "## Summary",
        "resumo": "Company-years with at least one failure in the fiscal year (ÚLTIMO column): {qualquer} of {n} ({pq}). By type: identity, {ident} ({pi}); reconciliation, {recon} ({pr}); plausibility, {plaus} ({pp}).",
        "h_tabela": "## Result by check, for the fiscal year (ÚLTIMO column)",
        "h_tabela_t1": "## Result by check, for the prior-year column (PENÚLTIMO)",
        "col": "| Check | Type | Applicable | Failures | Share | Difference up to 0.1% | 0.1% to 1% | 1% to 10% | Above 10% | Failures in open data | Failures in ENET |",
        "faixas_nota": "The bands measure the difference between the two sides of the equality as a share of the larger one; they do not apply to plausibility checks (—).",
        "diagnostico": "**Reading the most frequent failures.** Of the {cf} failures of \"cash flow closing balance = cash and cash equivalents on the balance sheet\" in the fiscal year, {ca} close when short-term investments (1.01.02) are added to cash: the company uses a broader cash concept in the cash flow statement than account 1.01.01, which is a presentation choice and not a reading error. Of the \"positive total assets\" failures, {zu} in the fiscal year and {zp} in the prior-year column have total assets equal to zero, which points to an unfilled comparative. Of the {fi} identity failures in the fiscal year, {fz} have one side equal to zero (subtotal or sum not filled in); the company-years with an identity failure are in fiscal years {anos_falha} (table by fiscal year below).",
        "h_na": "## Not applicable, by reason (ÚLTIMO column)",
        "col_na": "| Check | Missing account | Other chart of accounts | Column missing |",
        "h_ano": "## Company-years with an identity failure, by fiscal year (ÚLTIMO column)",
        "col_ano": "| Fiscal year | Company-years | With an identity failure | Share |",
        "tipo": {"identidade": "identity", "reconciliacao": "reconciliation", "plausibilidade": "plausibility"},
        "planos": {"nao_financeiro": "non-financial", "banco": "bank", "seguradora": "insurer", "outro": "not recognized"},
    },
}  # fmt: skip


def render(n: dict[str, Any], lang: str) -> str:
    t = T[lang]

    def i(x: int) -> str:
        return inteiro(x, lang)

    def p(a: int, b: int) -> str:
        return pct(a / b, lang) if b else "—"

    total = n["empresa_anos"]
    planos = "; ".join(f"{t['planos'].get(k, k)}, {i(v)}" for k, v in n["planos"].items())
    linhas = [t["titulo"], "", t["gerado"], "",
              t["escopo"].format(ultimo=n["ultimo_exercicio"], n=i(total), abertos=i(n["origens"].get("dados_abertos", 0)),
                                 enet=i(n["origens"].get("enet", 0)), planos=planos),
              "", t["nao_muda"], "", t["h_tipos"], ""] + ["- " + x for x in t["tipos"]]  # fmt: skip
    linhas += ["", t["regras"].format(tol=i(int(n["tolerancia_por_parcela"]))), "", t["h_resumo"], ""]
    f = n["empresa_anos_com_falha"]
    linhas.append(t["resumo"].format(
        qualquer=i(f.get("qualquer", 0)), n=i(total), pq=p(f.get("qualquer", 0), total),
        ident=i(f.get("identidade", 0)), pi=p(f.get("identidade", 0), total),
        recon=i(f.get("reconciliacao", 0)), pr=p(f.get("reconciliacao", 0), total),
        plaus=i(f.get("plausibilidade", 0)), pp=p(f.get("plausibilidade", 0), total)))  # fmt: skip
    for coluna, titulo in ((cf.ULTIMO, t["h_tabela"]), (cf.PENULTIMO, t["h_tabela_t1"])):
        linhas += ["", titulo, "", t["col"], "|" + " --- |" * 11]
        for d in n["conferencias"].values():
            x = d["colunas"].get(coluna)
            if x is None:
                continue
            nome = d["nome_pt"] if lang == "pt" else d["nome_en"]
            if d["tipo"] == cf.PLAUSIBILIDADE:
                faixas = ["—"] * 4
            else:
                faixas = [i(x["faixas"][k]) for k, _ in FAIXAS]
            o = x["falhas_por_origem"]
            linhas.append(f"| {nome} | {t['tipo'][d['tipo']]} | {i(x['aplicaveis'])} | {i(x['falhas'])} | "
                          f"{p(x['falhas'], x['aplicaveis'])} | " + " | ".join(faixas)
                          + f" | {i(o.get('dados_abertos', 0))} | {i(o.get('enet', 0))} |")  # fmt: skip
        if coluna == cf.ULTIMO:
            dg = n["diagnostico"]
            linhas += ["", t["faixas_nota"], "", t["diagnostico"].format(
                cf=i(dg["caixa_falhas"]), ca=i(dg["caixa_fecha_com_aplicacoes"]), zu=i(dg["ativo_zero"][cf.ULTIMO]),
                zp=i(dg["ativo_zero"][cf.PENULTIMO]), fi=i(dg["identidade_falhas"]),
                fz=i(dg["identidade_lado_zero"]),
                anos_falha=", ".join(a for a, v in n["por_ano"].items() if v["com_falha_de_identidade"]) or "—")]  # fmt: skip
    linhas += ["", t["h_na"], "", t["col_na"], "| --- | --- | --- | --- |"]
    for d in n["conferencias"].values():
        x = d["colunas"].get(cf.ULTIMO)
        if x is None or not x["nao_aplicaveis"]:
            continue
        na = x["nao_aplicaveis"]
        nome = d["nome_pt"] if lang == "pt" else d["nome_en"]
        linhas.append(
            f"| {nome} | {i(na.get('conta_ausente', 0))} | {i(na.get('plano', 0))} | {i(na.get('sem_coluna', 0))} |"
        )
    linhas += ["", t["h_ano"], "", t["col_ano"], "| --- | --- | --- | --- |"]
    for ano, v in n["por_ano"].items():
        linhas.append(f"| {ano} | {i(v['empresa_anos'])} | {i(v['com_falha_de_identidade'])} | "
                      f"{p(v['com_falha_de_identidade'], v['empresa_anos'])} |")  # fmt: skip
    return "\n".join(linhas) + "\n"


def escreve_docs(n: dict[str, Any]) -> None:
    for lang, caminho in DOCS.items():
        caminho.write_text(render(n, lang), encoding="utf-8")


def main() -> None:
    meta = pd.read_csv(BASE / "empresa_ano.csv", dtype={"cd_cvm": str, "num_doc": str})
    n = calcula(meta)
    NUMEROS.write_text(json.dumps(n, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    escreve_docs(json.loads(NUMEROS.read_text(encoding="utf-8")))


if __name__ == "__main__":
    main()
