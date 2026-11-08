"""Conferências de qualidade na base inteira do estudo 1, até o lacre: só números agregados, em PT e EN.

Lê a base "como era na época" da Fase 1 (data/base/, fora do git), roda `chiocca.v2.conferencias.conferir` em todas
as empresa-anos com versão da época até `ULTIMO_EXERCICIO_LIBERADO` e grava:
- docs/conferencias_numeros.json (versionado);
- docs/conferencias.md (PT) e docs/en/data-checks.md (EN), montados do JSON;
- resultados/identidades_com_falha.csv (fora do git): as empresa-anos com falha de identidade, com código CVM,
  versão, data de entrega e conferência que falhou, para a investigação pedida em 08/11/2026.
Nenhuma empresa é citada nos documentos. As conferências não mudam nenhum sinal, alerta ou número do estudo 1.

Uso: python -m chiocca.v2.relatorio_conferencias
"""

from __future__ import annotations

import io
import json
import zipfile
from collections import defaultdict
from pathlib import Path
from typing import Any

import pandas as pd

from chiocca.base import RAIZ
from chiocca.cvm import cd_texto
from chiocca.formato import inteiro, pct
from chiocca.v2 import conferencias as cf
from chiocca.v2.lacre import ULTIMO_EXERCICIO_LIBERADO, so_liberados

BASE = RAIZ / "data" / "base"
BRUTOS = RAIZ / "data" / "brutos" / "cvm"
SINAIS = RAIZ / "resultados" / "sinais_empresa_ano.csv"
GABARITO = RAIZ / "data" / "gabarito_casos.csv"
CSV_IDENTIDADES = RAIZ / "resultados" / "identidades_com_falha.csv"
NUMEROS = RAIZ / "docs" / "conferencias_numeros.json"
DOCS = {"pt": RAIZ / "docs" / "conferencias.md", "en": RAIZ / "docs" / "en" / "data-checks.md"}
FAIXAS = (("ate_0_1", 0.001), ("ate_1", 0.01), ("ate_10", 0.10), ("acima_10", float("inf")))
TIPOS = (cf.IDENTIDADE, cf.RECONCILIACAO, cf.NAO_PREENCHIDO, cf.SINAL_INCOMUM)


def _tipo_nao_aplicavel(c: cf.Conferencia) -> str:
    texto = c.motivo.en if c.motivo else ""
    if texto.startswith("missing account"):
        return "conta_ausente"
    if texto.startswith("chart of accounts"):
        return "plano"
    return "sem_coluna"


def _novo() -> dict[str, Any]:
    return {"aplicaveis": 0, "falhas": 0, "caixa_amplo": 0, "nao_aplicaveis": {}, "faixas": {f: 0 for f, _ in FAIXAS},
            "falhas_por_origem": {}}  # fmt: skip


def calcula(meta: pd.DataFrame, base: Path = BASE) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """Números agregados e a lista das empresa-anos com falha de identidade (esta, só para resultados/)."""
    meta = so_liberados(meta)
    meta = meta[meta.status == "ok"]
    por: dict[str, Any] = {}
    antes: dict[str, set[tuple[str, str]]] = defaultdict(set)  # caixa amplo contado como falha
    depois: dict[str, set[tuple[str, str]]] = defaultdict(set)
    por_ano: dict[str, dict[str, int]] = {}
    planos: dict[str, int] = defaultdict(int)
    diag = {"identidade_falhas": 0, "identidade_lado_zero": 0}
    identidades: list[dict[str, Any]] = []
    for ano in sorted(meta.exercicio.unique()):
        m = meta[meta.exercicio == ano]
        contas = pd.read_csv(base / f"contas_{ano}.csv.gz", dtype={"cd_cvm": str, "cd_conta": str, "ds_conta": str})
        grupos = {k: g for k, g in contas.groupby(["cd_cvm", "dt_refer"])}
        com_falha = 0
        for e in m.itertuples(index=False):
            chave = (e.cd_cvm, e.dt_refer)
            plano = e.plano if isinstance(e.plano, str) else "outro"
            planos[plano] += 1
            falhas_identidade: list[cf.Conferencia] = []
            for c in cf.conferir(grupos[chave], plano):
                d = por.setdefault(c.id, {"tipo": c.tipo, "nome_pt": c.nome.pt, "nome_en": c.nome.en, "colunas": {}})
                x = d["colunas"].setdefault(c.coluna, _novo())
                if c.resultado == "nao_aplicavel":
                    t = _tipo_nao_aplicavel(c)
                    x["nao_aplicaveis"][t] = x["nao_aplicaveis"].get(t, 0) + 1
                    continue
                x["aplicaveis"] += 1
                if c.resultado == cf.FECHA_CAIXA_AMPLO:
                    x["caixa_amplo"] += 1
                    if c.coluna == cf.ULTIMO:
                        antes[c.tipo].add(chave)
                        antes["qualquer"].add(chave)
                    continue
                if c.resultado != "falhou":
                    continue
                x["falhas"] += 1
                o = str(e.fonte)
                x["falhas_por_origem"][o] = x["falhas_por_origem"].get(o, 0) + 1
                rel = c.diferenca_relativa
                if rel is not None and c.tipo in (cf.IDENTIDADE, cf.RECONCILIACAO):
                    x["faixas"][next(f for f, lim in FAIXAS if rel <= lim)] += 1
                if c.coluna == cf.ULTIMO:
                    for alvo in (antes, depois):
                        alvo[c.tipo].add(chave)
                        alvo["qualquer"].add(chave)
                    if c.tipo == cf.IDENTIDADE:
                        falhas_identidade.append(c)
                        diag["identidade_falhas"] += 1
                        diag["identidade_lado_zero"] += int(c.esquerda == 0 or c.direita == 0)
            if falhas_identidade:
                com_falha += 1
                identidades.append({
                    "exercicio": int(ano), "cd_cvm": e.cd_cvm, "dt_refer": e.dt_refer, "versao": int(e.versao),
                    "ultima_versao": int(e.ultima_versao), "dt_receb": str(e.dt_receb), "fonte": e.fonte, "tipo": e.tipo,
                    "conferencias": ";".join(c.id for c in falhas_identidade),
                    "contas": ";".join(sorted({f"{dm} {cd}" for c in falhas_identidade for dm, cd, _ in c.contas})),
                    "lado_zero": any(c.esquerda == 0 or c.direita == 0 for c in falhas_identidade),
                })  # fmt: skip
        por_ano[str(int(ano))] = {"empresa_anos": int(len(m)), "com_falha_de_identidade": com_falha}
    n = {
        "ultimo_exercicio": ULTIMO_EXERCICIO_LIBERADO,
        "empresa_anos": int(len(meta)),
        "planos": dict(sorted(planos.items(), key=lambda kv: -kv[1])),
        "origens": {k: int(v) for k, v in meta.fonte.value_counts().items()},
        "conferencias": por,
        "com_falha_antes": {k: len(v) for k, v in antes.items()},
        "com_falha_depois": {k: len(v) for k, v in depois.items()},
        "por_ano": por_ano,
        "tolerancia_por_parcela": cf.TOLERANCIA_POR_PARCELA,
        "diagnostico": diag,
    }
    return n, identidades


def investiga_identidades(
    identidades: list[dict[str, Any]], base: Path = BASE, brutos: Path = BRUTOS, sinais: Path = SINAIS,
    gabarito: Path = GABARITO,
) -> dict[str, Any]:  # fmt: skip
    """Investigação curta das falhas de identidade (pedido de 08/11/2026): só contagens, nenhuma empresa citada."""
    d = pd.DataFrame(identidades)
    out: dict[str, Any] = {"empresa_anos": int(len(d))}
    if d.empty:
        return out | {"causa": "nao_determinada"}
    out["por_ano"] = {str(k): int(v) for k, v in d.exercicio.value_counts().sort_index().items()}
    out["primeira_versao"] = int((d.versao == 1).sum())
    out["versao_posterior"] = int((d.versao > 1).sum())
    out["reapresentadas_depois"] = int((d.ultima_versao > d.versao).sum())
    out["por_origem"] = {str(k): int(v) for k, v in d.fonte.value_counts().items()}
    out["por_tipo"] = {str(k): int(v) for k, v in d.tipo.value_counts().items()}
    out["lado_zero"] = int(d.lado_zero.sum())
    out["receb_min"], out["receb_max"] = str(d.dt_receb.min())[:10], str(d.dt_receb.max())[:10]
    # A leitura confere com o arquivo bruto? (só dados abertos; o ENET já foi conferido linha a linha na emenda 8)
    comparadas = iguais = 0
    abertos = d[d.fonte == "dados_abertos"]
    if brutos.exists():
        for ano, g in abertos.groupby("exercicio"):
            contas = pd.read_csv(base / f"contas_{ano}.csv.gz", dtype={"cd_cvm": str, "cd_conta": str})
            with zipfile.ZipFile(brutos / f"dfp_cia_aberta_{ano}.zip") as z:
                cache: dict[str, pd.DataFrame] = {}
                for e in g.itertuples(index=False):
                    b = contas[
                        (contas.cd_cvm == e.cd_cvm) & (contas.dt_refer == e.dt_refer) & (contas.ordem == cf.ULTIMO)
                    ]
                    for item in e.contas.split(";"):
                        dem, cod = item.split(" ")
                        for dd in (["DFC_MI", "DFC_MD"] if dem == "DFC" else [dem]):
                            arq = f"dfp_cia_aberta_{dd}_{e.tipo}_{ano}.csv"
                            if arq not in cache:
                                cache[arq] = pd.read_csv(io.BytesIO(z.read(arq)), sep=";", encoding="latin1", dtype=str)
                            r = cache[arq]
                            sel = r[(cd_texto(r.CD_CVM) == e.cd_cvm) & (r.DT_REFER == e.dt_refer)
                                    & (r.VERSAO.astype(int) == e.versao) & (r.ORDEM_EXERC == cf.ULTIMO) & (r.CD_CONTA == cod)]  # fmt: skip
                            if sel.empty:
                                continue
                            v = float(sel.VL_CONTA.iloc[0]) * {"MIL": 1000.0, "UNIDADE": 1.0}[sel.ESCALA_MOEDA.iloc[0]]
                            vb = b[b.demonstracao.astype(str).str.startswith(dem) & (b.cd_conta == cod)].valor
                            comparadas += 1
                            iguais += int(len(vb) == 1 and abs(float(vb.iloc[0]) - v) < 1)
        cabecalhos = set()
        for ano in range(min(d.exercicio) - 2, min(max(d.exercicio) + 1, ULTIMO_EXERCICIO_LIBERADO) + 1):
            p = brutos / f"dfp_cia_aberta_{ano}.zip"
            if p.exists():
                with zipfile.ZipFile(p) as z:
                    cab = pd.read_csv(io.BytesIO(z.read(f"dfp_cia_aberta_DRE_con_{ano}.csv")), sep=";",
                                      encoding="latin1", dtype=str, nrows=1).columns  # fmt: skip
                cabecalhos.add(tuple(cab))
        out["mesmo_formato_de_arquivo"] = len(cabecalhos) == 1
    out["linhas_comparadas_com_o_bruto"], out["linhas_iguais_ao_bruto"] = comparadas, iguais
    if gabarito.exists():
        gab = pd.read_csv(gabarito, dtype={"cd_cvm": str})
        anos_gab = set()
        for c in gab.itertuples(index=False):
            if pd.notna(c.cd_cvm) and pd.notna(c.periodo_afetado_inicio):
                anos_gab |= {
                    (str(c.cd_cvm), a) for a in range(int(c.periodo_afetado_inicio), int(c.periodo_afetado_fim) + 1)
                }
        out["empresas_do_gabarito"] = int(d.cd_cvm.isin(set(gab.cd_cvm.dropna().astype(str))).sum())
        out["anos_afetados_do_gabarito"] = int(sum((c, a) in anos_gab for c, a in zip(d.cd_cvm, d.exercicio)))
    if sinais.exists():
        s = pd.read_csv(sinais, dtype={"cd_cvm": str}, low_memory=False)
        s = s.merge(d[["cd_cvm", "dt_refer"]], on=["cd_cvm", "dt_refer"])
        out["na_amostra_do_estudo_1"] = int(s.amostra.isin(["nao_financeira", "financeira"]).sum())
        out["em_alerta_no_estudo_1"] = int(s.em_alerta.astype(str).eq("True").sum())
    explicada = out.get("versao_posterior", 0) == len(d) or not out.get("mesmo_formato_de_arquivo", True)
    out["causa"] = "versao_ou_formato" if explicada else "nao_determinada"
    return out


T: dict[str, dict[str, Any]] = {
    "pt": {
        "titulo": "# Conferências de qualidade dos dados da CVM (Fase B do v2)",
        "gerado": "Gerado por `python -m chiocca.v2.relatorio_conferencias` a partir de `data/base/` (fora do git), a base \"como era na época\" do estudo 1. Não edite à mão: um teste compara este arquivo com a saída do script. Só números agregados; nenhuma empresa é citada.",
        "escopo": "Empresa-anos com versão da época, de 2010 até o lacre ({ultimo}): {n}. Dados abertos: {abertos}; ENET: {enet}. Por plano de contas: {planos}.",
        "nao_muda": "As conferências descrevem os dados. Elas não mudam nenhum sinal, alerta ou número do estudo 1.",
        "h_tipos": "## O que cada tipo de conferência quer dizer",
        "tipos": [
            "**Identidade:** igualdade garantida pela contabilidade (ativo total = passivo total, subtotais do balanço e da DRE, soma e saldos da DFC). Falhar indica erro de preenchimento na CVM ou de leitura, não um ano ruim.",
            "**Reconciliação:** o mesmo número por outro caminho, entre demonstrações (saldo de caixa da DFC contra o caixa e equivalentes do balanço). Quando o saldo da DFC fecha com caixa e equivalentes mais aplicações financeiras (1.01.01 + 1.01.02), o resultado é \"fecha com caixa amplo\": a DFC usa um conceito de caixa mais amplo, o que é escolha de apresentação e não conta como falha.",
            "**Não preenchido:** ativo total igual a zero na coluna. No produto, os indicadores que dependem desse balanço ficam \"não calculável\", nunca calculados com zero.",
            "**Sinal incomum:** sinal contábil incomum (ativo total negativo, conta de saldo negativa, receita negativa, custo ou despesa com sinal de receita). Incomum não é impossível: uma reversão de provisão maior que a despesa do ano, por exemplo, pode deixar a despesa positiva.",
        ],
        "regras": "Tolerância de R$ {tol} por parcela da igualdade, só para arredondamento. Conta ausente não vira zero: a conferência fica \"não se aplica\". Os códigos por conta valem para o plano não financeiro; nos outros planos, só ativo total = passivo total e as identidades da DFC, cujos códigos são fixos em todos os planos.",
        "h_resumo": "## Resumo: antes e depois do caixa amplo",
        "col_resumo": "| Empresa-anos com falha no exercício (coluna ÚLTIMO) | Antes | Depois |",
        "linhas_resumo": {"identidade": "Identidade", "reconciliacao": "Reconciliação", "nao_preenchido": "Não preenchido",
                          "sinal_incomum": "Sinal incomum", "qualquer": "Qualquer tipo"},
        "resumo_nota": "\"Antes\" conta como falha a reconciliação que fecha com caixa amplo; \"depois\", não. As outras conferências não mudam. Parte sobre {n} empresa-anos.",
        "h_caixa": "## Reconciliação do caixa: antes e depois",
        "col_caixa": "| Conferência | Coluna | Aplicáveis | Falhas antes | Fecha com caixa amplo | Falhas depois |",
        "h_tabela": "## Resultado por conferência, no exercício (coluna ÚLTIMO)",
        "h_tabela_t1": "## Resultado por conferência, no comparativo (coluna PENÚLTIMO)",
        "col": "| Conferência | Tipo | Aplicáveis | Falhas | Parte | Fecha com caixa amplo | Diferença até 0,1% | 0,1% a 1% | 1% a 10% | Acima de 10% | Falhas em dados abertos | Falhas no ENET |",
        "faixas_nota": "As faixas medem a diferença entre os dois lados da igualdade em proporção do maior deles; não se aplicam a \"não preenchido\" nem a \"sinal incomum\" (—).",
        "diagnostico": "Das {fi} falhas de identidade no exercício, {fz} têm um dos lados igual a zero (subtotal ou soma não preenchidos).",
        "h_investigacao": "## Investigação das falhas de identidade",
        "investigacao": [
            "Empresa-anos com falha de identidade no exercício: {n}, nos exercícios {anos}. A lista (código CVM, versão, data de entrega e conferência) fica em `resultados/identidades_com_falha.csv`, fora do git, gerada pelo mesmo script.",
            "Versão: {v1} são a primeira versão entregue e {vp} são versões posteriores; {reap} foram reapresentadas depois. Entregas entre {rmin} e {rmax}. Por origem: {origens}. Por tipo: {tipos}.",
            "Leitura: {iguais} de {comparadas} linhas das contas envolvidas, nos dados abertos, são iguais às do arquivo bruto da CVM; a base lê o que foi entregue. Formato do arquivo dos dados abertos: {formato}.",
            "Gabarito e estudo 1: {gab} empresa-anos são de empresas do gabarito, {gab_anos} delas em ano de período afetado; {amostra} estavam na amostra do estudo 1, e {alerta} estavam em alerta.",
            "**Causa: {causa}.**",
        ],
        "formato_igual": "o mesmo em todos os anos conferidos",
        "formato_diferente": "mudou entre os anos conferidos",
        "causa": {"nao_determinada": "não determinada", "versao_ou_formato": "ligada à versão ou ao formato do arquivo"},
        "h_na": "## Não se aplica, por motivo (coluna ÚLTIMO)",
        "col_na": "| Conferência | Conta ausente | Outro plano de contas | Sem a coluna |",
        "h_ano": "## Empresa-anos com falha de identidade, por exercício (coluna ÚLTIMO)",
        "col_ano": "| Exercício | Empresa-anos | Com falha de identidade | Parte |",
        "tipo": {"identidade": "identidade", "reconciliacao": "reconciliação", "nao_preenchido": "não preenchido",
                 "sinal_incomum": "sinal incomum"},
        "planos": {"nao_financeiro": "não financeiro", "banco": "banco", "seguradora": "seguradora", "outro": "não reconhecido"},
        "origem": {"dados_abertos": "dados abertos", "enet": "ENET"},
        "tipo_dem": {"con": "consolidado", "ind": "individual"},
    },
    "en": {
        "titulo": "# CVM data quality checks (v2, Phase B)",
        "gerado": "Generated by `python -m chiocca.v2.relatorio_conferencias` from `data/base/` (not in git), study 1's point-in-time base. Do not edit by hand: a test compares this file with the script output. Aggregate numbers only; no company is named.",
        "escopo": "Company-years with a point-in-time version, from 2010 up to the seal ({ultimo}): {n}. Open data: {abertos}; ENET: {enet}. By chart of accounts: {planos}.",
        "nao_muda": "The checks describe the data. They change no signal, alert or number from study 1.",
        "h_tipos": "## What each type of check means",
        "tipos": [
            "**Identity:** an equality guaranteed by the accounting (total assets = total liabilities and equity, balance sheet and income statement subtotals, cash flow sum and balances). A failure points to a filing error at the CVM or a reading error, not a bad year.",
            "**Reconciliation:** the same number through another path, across statements (cash flow closing balance against cash and cash equivalents on the balance sheet). When the cash flow balance closes with cash and cash equivalents plus short-term investments (1.01.01 + 1.01.02), the result is \"closes with broad cash\": the cash flow statement uses a broader cash concept, which is a presentation choice and does not count as a failure.",
            "**Not filled in:** total assets equal to zero in the column. In the product, the indicators that depend on that balance sheet are \"not computable\", never computed with zero.",
            "**Unusual sign:** an unusual accounting sign (negative total assets, a negative balance account, negative revenue, a cost or expense with the sign of income). Unusual is not impossible: a provision reversal larger than the year's expense, for example, can leave the expense positive.",
        ],
        "regras": "Tolerance of R${tol} per term of the equality, for rounding only. A missing account does not become zero: the check is marked \"not applicable\". The per-account codes apply to the non-financial chart of accounts; for the other charts, only total assets = total liabilities and equity and the cash flow identities, whose codes are fixed in every chart.",
        "h_resumo": "## Summary: before and after broad cash",
        "col_resumo": "| Company-years with a failure in the fiscal year (ÚLTIMO column) | Before | After |",
        "linhas_resumo": {"identidade": "Identity", "reconciliacao": "Reconciliation", "nao_preenchido": "Not filled in",
                          "sinal_incomum": "Unusual sign", "qualquer": "Any type"},
        "resumo_nota": "\"Before\" counts a reconciliation that closes with broad cash as a failure; \"after\" does not. The other checks do not change. Share of {n} company-years.",
        "h_caixa": "## Cash reconciliation: before and after",
        "col_caixa": "| Check | Column | Applicable | Failures before | Closes with broad cash | Failures after |",
        "h_tabela": "## Result by check, for the fiscal year (ÚLTIMO column)",
        "h_tabela_t1": "## Result by check, for the prior-year column (PENÚLTIMO)",
        "col": "| Check | Type | Applicable | Failures | Share | Closes with broad cash | Difference up to 0.1% | 0.1% to 1% | 1% to 10% | Above 10% | Failures in open data | Failures in ENET |",
        "faixas_nota": "The bands measure the difference between the two sides of the equality as a share of the larger one; they do not apply to \"not filled in\" or \"unusual sign\" (—).",
        "diagnostico": "Of the {fi} identity failures in the fiscal year, {fz} have one side equal to zero (subtotal or sum not filled in).",
        "h_investigacao": "## Investigation of the identity failures",
        "investigacao": [
            "Company-years with an identity failure in the fiscal year: {n}, in fiscal years {anos}. The list (CVM code, version, filing date and check) is in `resultados/identidades_com_falha.csv`, not in git, generated by the same script.",
            "Version: {v1} are the first version filed and {vp} are later versions; {reap} were restated afterwards. Filed between {rmin} and {rmax}. By source: {origens}. By type: {tipos}.",
            "Reading: {iguais} of {comparadas} lines of the accounts involved, in the open data, equal the lines in the raw CVM file; the base reads what was filed. Open data file format: {formato}.",
            "Ground truth and study 1: {gab} company-years belong to ground-truth companies, {gab_anos} of them in a year of the affected period; {amostra} were in the study 1 sample, and {alerta} were in alert.",
            "**Cause: {causa}.**",
        ],
        "formato_igual": "the same in every year checked",
        "formato_diferente": "changed across the years checked",
        "causa": {"nao_determinada": "not determined", "versao_ou_formato": "tied to the version or the file format"},
        "h_na": "## Not applicable, by reason (ÚLTIMO column)",
        "col_na": "| Check | Missing account | Other chart of accounts | Column missing |",
        "h_ano": "## Company-years with an identity failure, by fiscal year (ÚLTIMO column)",
        "col_ano": "| Fiscal year | Company-years | With an identity failure | Share |",
        "tipo": {"identidade": "identity", "reconciliacao": "reconciliation", "nao_preenchido": "not filled in",
                 "sinal_incomum": "unusual sign"},
        "planos": {"nao_financeiro": "non-financial", "banco": "bank", "seguradora": "insurer", "outro": "not recognized"},
        "origem": {"dados_abertos": "open data", "enet": "ENET"},
        "tipo_dem": {"con": "consolidated", "ind": "individual"},
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
    linhas += ["", t["regras"].format(tol=i(int(n["tolerancia_por_parcela"]))), ""]
    linhas += [t["h_resumo"], "", t["col_resumo"], "| --- | --- | --- |"]
    for k in (*TIPOS, "qualquer"):
        a, d = n["com_falha_antes"].get(k, 0), n["com_falha_depois"].get(k, 0)
        linhas.append(f"| {t['linhas_resumo'][k]} | {i(a)} ({p(a, total)}) | {i(d)} ({p(d, total)}) |")
    linhas += [
        "",
        t["resumo_nota"].format(n=i(total)),
        "",
        t["h_caixa"],
        "",
        t["col_caixa"],
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for d in n["conferencias"].values():
        if d["tipo"] != cf.RECONCILIACAO:
            continue
        for coluna, x in d["colunas"].items():
            nome = d["nome_pt"] if lang == "pt" else d["nome_en"]
            linhas.append(f"| {nome} | {coluna} | {i(x['aplicaveis'])} | {i(x['falhas'] + x['caixa_amplo'])} | "
                          f"{i(x['caixa_amplo'])} | {i(x['falhas'])} |")  # fmt: skip
    for coluna, titulo in ((cf.ULTIMO, t["h_tabela"]), (cf.PENULTIMO, t["h_tabela_t1"])):
        linhas += ["", titulo, "", t["col"], "|" + " --- |" * 12]
        for d in n["conferencias"].values():
            x = d["colunas"].get(coluna)
            if x is None:
                continue
            nome = d["nome_pt"] if lang == "pt" else d["nome_en"]
            igualdade = d["tipo"] in (cf.IDENTIDADE, cf.RECONCILIACAO)
            faixas = [i(x["faixas"][k]) for k, _ in FAIXAS] if igualdade else ["—"] * 4
            amplo = i(x["caixa_amplo"]) if d["tipo"] == cf.RECONCILIACAO else "—"
            o = x["falhas_por_origem"]
            linhas.append(f"| {nome} | {t['tipo'][d['tipo']]} | {i(x['aplicaveis'])} | {i(x['falhas'])} | "
                          f"{p(x['falhas'], x['aplicaveis'])} | {amplo} | " + " | ".join(faixas)
                          + f" | {i(o.get('dados_abertos', 0))} | {i(o.get('enet', 0))} |")  # fmt: skip
        if coluna == cf.ULTIMO:
            dg = n["diagnostico"]
            linhas += ["", t["faixas_nota"], "", t["diagnostico"].format(fi=i(dg["identidade_falhas"]),
                                                                      fz=i(dg["identidade_lado_zero"]))]  # fmt: skip
    inv = n.get("investigacao_identidades")
    if inv and inv.get("empresa_anos"):
        anos = ", ".join(inv["por_ano"])
        origens = "; ".join(f"{t['origem'].get(k, k)}, {i(v)}" for k, v in inv["por_origem"].items())
        tipos = "; ".join(f"{t['tipo_dem'].get(k, k)}, {i(v)}" for k, v in inv["por_tipo"].items())
        formato = t["formato_igual"] if inv.get("mesmo_formato_de_arquivo", True) else t["formato_diferente"]
        from chiocca.formato import data

        campos = dict(n=i(inv["empresa_anos"]), anos=anos, v1=i(inv["primeira_versao"]), vp=i(inv["versao_posterior"]),
                      reap=i(inv["reapresentadas_depois"]), rmin=data(inv["receb_min"], lang), rmax=data(inv["receb_max"], lang),
                      origens=origens, tipos=tipos, iguais=i(inv["linhas_iguais_ao_bruto"]),
                      comparadas=i(inv["linhas_comparadas_com_o_bruto"]), formato=formato,
                      gab=i(inv.get("empresas_do_gabarito", 0)), gab_anos=i(inv.get("anos_afetados_do_gabarito", 0)),
                      amostra=i(inv.get("na_amostra_do_estudo_1", 0)), alerta=i(inv.get("em_alerta_no_estudo_1", 0)),
                      causa=t["causa"][inv["causa"]])  # fmt: skip
        linhas += ["", t["h_investigacao"], ""] + ["- " + x.format(**campos) for x in t["investigacao"]]
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
    n, identidades = calcula(meta)
    n["investigacao_identidades"] = investiga_identidades(identidades)
    CSV_IDENTIDADES.parent.mkdir(exist_ok=True)
    pd.DataFrame(identidades).to_csv(CSV_IDENTIDADES, index=False)
    NUMEROS.write_text(json.dumps(n, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    escreve_docs(json.loads(NUMEROS.read_text(encoding="utf-8")))


if __name__ == "__main__":
    main()
