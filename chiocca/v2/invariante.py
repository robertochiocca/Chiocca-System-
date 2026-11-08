"""Invariante do estudo 1 (Fase C1): o motor v1 sobre o armazém reproduz o estudo na data de corte de cada exercício.

Para cada exercício de 2010 a `ULTIMO_EXERCICIO_LIBERADO`, roda `chiocca.v2.na_data.corte_transversal` sobre
`FontesArmazem` sem data de referência (cada empresa na data de corte do seu exercício, como no estudo) e compara,
coluna por coluna, com `resultados/sinais_empresa_ano.csv`: situação, amostra, cada sinal e componente, cada motivo
de "não calculável", cada alerta, avaliada e em alerta. Os dois lados passam pelo mesmo CSV, e a comparação é exata.

Também roda o mesmo corte com a data de referência máxima (31/12/2024), para mostrar o motor numa data posterior:
quantas empresa-anos têm outra versão conhecida nessa data, quantas ficam pendentes do ENET e quantos alertas mudam.
Só números agregados; nenhuma empresa é citada.

Grava docs/invariante_numeros.json (versionado) e monta docs/armazenamento-temporal.md e
docs/en/temporal-storage.md a partir dele.

Uso: python -m chiocca.v2.invariante   (precisa de data/armazem, montado por python -m chiocca.v2.armazem)
"""

from __future__ import annotations

import io
import json
from typing import Any

import pandas as pd

from chiocca.base import PENDENTE_ENET, RAIZ, SEM_VERSAO_ATE_CORTE
from chiocca.formato import data, inteiro
from chiocca.v2.armazem import PRIMEIRO_EXERCICIO, SO_METADADOS, FontesArmazem
from chiocca.v2.lacre import DATA_REFERENCIA_MAXIMA, ULTIMO_EXERCICIO_LIBERADO
from chiocca.v2.na_data import corte_transversal

SINAIS_ESTUDO_1 = RAIZ / "resultados" / "sinais_empresa_ano.csv"
NUMEROS = RAIZ / "docs" / "invariante_numeros.json"
DOCS = {"pt": RAIZ / "docs" / "armazenamento-temporal.md", "en": RAIZ / "docs" / "en" / "temporal-storage.md"}
CHAVE = ["exercicio", "cd_cvm", "dt_refer"]


def _pelo_csv(s: pd.DataFrame, colunas: list[str]) -> pd.DataFrame:
    buf = io.StringIO()
    s[colunas].to_csv(buf, index=False)
    buf.seek(0)
    return pd.read_csv(buf, dtype={"cd_cvm": str}, low_memory=False)


def _ordena(s: pd.DataFrame) -> pd.DataFrame:
    return s.assign(**{c: s[c].astype(str) for c in CHAVE}).sort_values(CHAVE).reset_index(drop=True)


def compara(novo: pd.DataFrame, estudo: pd.DataFrame) -> dict[str, Any]:
    """Comparação exata, coluna por coluna, das empresa-anos de um exercício."""
    colunas = list(estudo.columns)
    e, n = _ordena(estudo), _ordena(_pelo_csv(novo, colunas))
    out: dict[str, Any] = {"empresa_anos_estudo": int(len(e)), "empresa_anos_v2": int(len(n))}
    if len(e) != len(n) or not (e[CHAVE].values == n[CHAVE].values).all():
        return out | {"mesmas_empresa_anos": False, "empresa_anos_iguais": 0, "colunas_com_diferenca": {}}
    iguais = pd.Series(True, index=e.index)
    difs: dict[str, int] = {}
    for c in colunas:
        x, y = e[c], n[c]
        if pd.api.types.is_numeric_dtype(x) and pd.api.types.is_numeric_dtype(y):
            ok = (x == y) | (x.isna() & y.isna())
        else:
            ok = x.astype(str).where(x.notna(), "") == y.astype(str).where(y.notna(), "")
        if not ok.all():
            difs[c] = int((~ok).sum())
        iguais &= ok
    return out | {"mesmas_empresa_anos": True, "empresa_anos_iguais": int(iguais.sum()), "colunas_com_diferenca": difs,
                  "colunas_comparadas": len(colunas)}  # fmt: skip


def na_data_maxima(no_corte: pd.DataFrame, na_data: pd.DataFrame) -> dict[str, int]:
    """O mesmo exercício visto na data máxima, contra a data de corte: só contagens."""
    a, b = _ordena(no_corte), _ordena(na_data)
    m = a.merge(b, on=CHAVE, suffixes=("_corte", "_data"))
    receb = m.dt_receb_corte.astype(str) != m.dt_receb_data.astype(str)
    ambos = m.avaliada_corte.astype(bool) & m.avaliada_data.astype(bool)
    em_c, em_d = m.em_alerta_corte.astype(bool), m.em_alerta_data.astype(bool)
    return {
        "empresa_anos": int(len(m)),
        "com_versao_no_corte": int((m.status_corte != SEM_VERSAO_ATE_CORTE).sum()),
        "outra_versao_na_data": int((receb & (m.status_corte != SEM_VERSAO_ATE_CORTE)).sum()),
        "pendentes_enet_na_data": int((m.status_data == PENDENTE_ENET).sum()),
        "avaliadas_nas_duas_datas": int(ambos.sum()),
        "entram_em_alerta": int((ambos & ~em_c & em_d).sum()),
        "saem_do_alerta": int((ambos & em_c & ~em_d).sum()),
    }


def calcula(fontes: FontesArmazem, estudo: pd.DataFrame, anos: range) -> dict[str, Any]:
    out: dict[str, Any] = {"exercicios": {}, "data_maxima": {}}
    for ano in anos:
        no_corte, _ = corte_transversal(fontes, ano)
        out["exercicios"][str(ano)] = compara(no_corte, estudo[estudo.exercicio == ano])
        na_data, _ = corte_transversal(fontes, ano, DATA_REFERENCIA_MAXIMA)
        out["data_maxima"][str(ano)] = na_data_maxima(no_corte, na_data)
        print(ano, out["exercicios"][str(ano)]["empresa_anos_iguais"], flush=True)
    origens = fontes.consulta(
        "SELECT origem, count(*) AS n, count(DISTINCT cd_cvm || dt_refer) AS docs FROM contas GROUP BY origem"
    )
    out["armazem"] = {
        "linhas": fontes.manifesto["linhas"],
        "documentos_enet": fontes.manifesto["documentos_enet"],
        "documentos_so_metadados": int(origens.loc[origens.origem == SO_METADADOS, "docs"].sum()),
        "exercicios": fontes.manifesto["exercicios"],
    }
    out["ultimo_exercicio_liberado"] = ULTIMO_EXERCICIO_LIBERADO
    out["data_referencia_maxima"] = str(DATA_REFERENCIA_MAXIMA)
    return out


T: dict[str, dict[str, Any]] = {
    "pt": {
        "titulo": "# Armazenamento temporal e motor v1 em qualquer data (Fase C1)",
        "gerado": "Gerado por `python -m chiocca.v2.invariante` a partir de `docs/invariante_numeros.json`. Não edite à mão: um teste compara este arquivo com a saída do script. Só números agregados; nenhuma empresa é citada.",
        "h_armazem": "## O armazém",
        "armazem": [
            "Parquet consultado pelo DuckDB (`chiocca/v2/armazem.py`), montado sem rede de `data/brutos/cvm` (conferido por hash) e do cache do ENET, em `data/armazem/`, fora do git. Exercícios de {ini} a {fim}; nenhum exercício lacrado entra.",
            "Tabelas: `versoes` ({versoes} versões de DFP, com a data de entrega), `contas` ({contas} linhas, dos dados abertos e de {enet} documentos do ENET), `fca` ({fca} versões) e `cadastro` ({cadastro} linhas). O `manifesto.json` guarda o hash SHA-256 de cada arquivo de origem.",
            "De documento entregue depois de {maxima}, o armazém guarda só metadados: versão, data de entrega e quais demonstrações existem, sem nenhuma conta nem valor ({so_meta} documentos). O `como_era` do motor v1 usa essa estrutura da última versão para saber se há consolidado (rota do ENET, emenda 8) e para nomear a DFC do ENET; com data de referência até {maxima}, os valores dessa versão nunca são lidos.",
            "`FontesArmazem` tem a mesma interface dos arquivos brutos (`chiocca.cvm.Fontes`): o motor v1 roda sobre o armazém sem nenhuma mudança.",
        ],
        "h_motor": "## Motor v1 na data",
        "motor": [
            "`ExercicioNaData` (`chiocca/v2/na_data.py`): uma empresa num exercício, como era na data de referência, com a versão usada, só as versões entregues até a data, a origem (dados abertos ou ENET) e o link do documento. A data passa pelo intervalo de {minima} a {maxima}, e o exercício, pelo lacre.",
            "Corte transversal na data: as mesmas funções do estudo 1 (`como_era`, `grupos`, `sinais_amostra`), com os decis do ano recalculados só com as empresas cuja versão era pública na data.",
            "Camada do produto, ao lado do motor e sem mudar nenhum valor dele: a coluna `produto_nao_calculaveis` lista os sinais que o produto mostra como \"não calculável\" por balanço não preenchido.",
        ],
        "h_invariante": "## Invariante do estudo 1",
        "invariante": "Na data de corte de cada exercício, o motor v1 sobre o armazém reproduz `resultados/sinais_empresa_ano.csv` em {iguais} de {total} empresa-anos, com comparação exata de {colunas} colunas (situação, amostra, cada sinal, componente e motivo de \"não calculável\", cada alerta, avaliada e em alerta).",
        "col_invariante": "| Exercício | Empresa-anos no estudo 1 | Empresa-anos no armazém | Iguais em todas as colunas | Colunas com diferença |",
        "nenhuma": "nenhuma",
        "h_data": "## O mesmo exercício visto em {maxima}",
        "data": "Com a data de referência em {maxima}, cada exercício usa a versão mais recente entregue até essa data. Contagens contra a data de corte, sem nenhuma empresa citada:",
        "col_data": "| Exercício | Com versão na data de corte | Outra versão conhecida em {maxima} | Pendentes do ENET em {maxima} | Avaliadas nas duas datas | Entram em alerta | Saem do alerta |",
        "pendentes": "\"Pendente do ENET\" é a versão da data que não está no armazém; a busca no ENET é um comando separado e nunca acontece dentro de uma consulta (pergunta 9 do plano).",
        "h_uso": "## Como reproduzir",
        "uso": ["python -m chiocca.v2.armazem      # monta data/armazem a partir de data/brutos/cvm e data/cache/enet",
                "python -m chiocca.v2.invariante   # invariante e corte na data máxima; grava este documento"],
    },
    "en": {
        "titulo": "# Temporal storage and engine v1 on any date (Phase C1)",
        "gerado": "Generated by `python -m chiocca.v2.invariante` from `docs/invariante_numeros.json`. Do not edit by hand: a test compares this file with the script output. Aggregate numbers only; no company is named.",
        "h_armazem": "## The store",
        "armazem": [
            "Parquet queried through DuckDB (`chiocca/v2/armazem.py`), built offline from `data/brutos/cvm` (checked by hash) and the ENET cache, in `data/armazem/`, outside git. Fiscal years {ini} to {fim}; no sealed fiscal year goes in.",
            "Tables: `versoes` ({versoes} DFP versions, with the filing date), `contas` ({contas} rows, from open data and from {enet} ENET documents), `fca` ({fca} versions) and `cadastro` ({cadastro} rows). `manifesto.json` keeps the SHA-256 hash of every source file.",
            "For documents filed after {maxima}, the store keeps metadata only: version, filing date and which statements exist, with no account and no value ({so_meta} documents). Engine v1's `como_era` uses this structure of the latest version to know whether a consolidated statement exists (the ENET route, amendment 8) and to name the ENET cash flow statement; with a reference date up to {maxima}, that version's values are never read.",
            "`FontesArmazem` has the same interface as the raw files (`chiocca.cvm.Fontes`): engine v1 runs on the store without any change.",
        ],
        "h_motor": "## Engine v1 on the date",
        "motor": [
            "`ExercicioNaData` (`chiocca/v2/na_data.py`): one company in one fiscal year, as it was on the reference date, with the version used, only the versions filed by the date, the origin (open data or ENET) and the document link. The date goes through the {minima} to {maxima} range, and the fiscal year through the seal.",
            "Cross-section on the date: the same study 1 functions (`como_era`, `grupos`, `sinais_amostra`), with the year's deciles recomputed only with the companies whose version was public on the date.",
            "Product layer, next to the engine and without changing any of its values: the `produto_nao_calculaveis` column lists the signals the product shows as \"not computable\" because of an unfilled balance sheet.",
        ],
        "h_invariante": "## Study 1 invariant",
        "invariante": "On each fiscal year's cut-off date, engine v1 on the store reproduces `resultados/sinais_empresa_ano.csv` in {iguais} of {total} company-years, with an exact comparison of {colunas} columns (status, sample, each signal, component and \"not computable\" reason, each alert, evaluated and in alert).",
        "col_invariante": "| Fiscal year | Company-years in study 1 | Company-years in the store | Equal in every column | Columns with a difference |",
        "nenhuma": "none",
        "h_data": "## The same fiscal year seen on {maxima}",
        "data": "With the reference date on {maxima}, each fiscal year uses the latest version filed by that date. Counts against the cut-off date, with no company named:",
        "col_data": "| Fiscal year | With a version on the cut-off date | Another version known on {maxima} | Pending from ENET on {maxima} | Evaluated on both dates | Enter alert | Leave alert |",
        "pendentes": "\"Pending from ENET\" is the version of the date that is not in the store; fetching from ENET is a separate command and never happens inside a query (plan question 9).",
        "h_uso": "## How to reproduce",
        "uso": ["python -m chiocca.v2.armazem      # builds data/armazem from data/brutos/cvm and data/cache/enet",
                "python -m chiocca.v2.invariante   # invariant and cross-section on the maximum date; writes this document"],
    },
}  # fmt: skip


def render(n: dict[str, Any], lang: str) -> str:
    from chiocca.v2.lacre import DATA_REFERENCIA_MINIMA

    t = T[lang]
    i = lambda x: inteiro(x, lang)  # noqa: E731
    a, li = n["armazem"], n["armazem"]["linhas"]
    maxima, minima = data(n["data_referencia_maxima"], lang), data(str(DATA_REFERENCIA_MINIMA), lang)
    linhas = [t["titulo"], "", t["gerado"], "", t["h_armazem"], ""]
    linhas += ["- " + x.format(ini=min(a["exercicios"]), fim=max(a["exercicios"]), versoes=i(li["versoes"]),
                               contas=i(li["contas"]), enet=i(a["documentos_enet"]), fca=i(li["fca"]),
                               cadastro=i(li["cadastro"]), maxima=maxima, so_meta=i(a["documentos_so_metadados"]))
               for x in t["armazem"]]  # fmt: skip
    linhas += ["", t["h_motor"], ""] + ["- " + x.format(minima=minima, maxima=maxima) for x in t["motor"]]
    ex = n["exercicios"]
    total = sum(v["empresa_anos_estudo"] for v in ex.values())
    iguais = sum(v["empresa_anos_iguais"] for v in ex.values())
    colunas = max((v.get("colunas_comparadas", 0) for v in ex.values()), default=0)
    linhas += [
        "",
        t["h_invariante"],
        "",
        t["invariante"].format(iguais=i(iguais), total=i(total), colunas=i(colunas)),
        "",
    ]
    linhas += [t["col_invariante"], "| --- | --- | --- | --- | --- |"]
    for ano, v in ex.items():
        difs = "; ".join(f"`{c}` ({i(k)})" for c, k in v["colunas_com_diferenca"].items()) or t["nenhuma"]
        linhas.append(
            f"| {ano} | {i(v['empresa_anos_estudo'])} | {i(v['empresa_anos_v2'])} | {i(v['empresa_anos_iguais'])} | {difs} |"
        )
    linhas += ["", t["h_data"].format(maxima=maxima), "", t["data"].format(maxima=maxima), ""]
    linhas += [t["col_data"].format(maxima=maxima), "| --- | --- | --- | --- | --- | --- | --- |"]
    for ano, v in n["data_maxima"].items():
        linhas.append(f"| {ano} | {i(v['com_versao_no_corte'])} | {i(v['outra_versao_na_data'])} | {i(v['pendentes_enet_na_data'])} | "
                      f"{i(v['avaliadas_nas_duas_datas'])} | {i(v['entram_em_alerta'])} | {i(v['saem_do_alerta'])} |")  # fmt: skip
    linhas += ["", t["pendentes"], "", t["h_uso"], "", "```"] + t["uso"] + ["```"]
    return "\n".join(linhas) + "\n"


def escreve_docs(n: dict[str, Any]) -> None:
    for lang, caminho in DOCS.items():
        caminho.write_text(render(n, lang), encoding="utf-8")


def main() -> None:
    estudo = pd.read_csv(SINAIS_ESTUDO_1, dtype={"cd_cvm": str}, low_memory=False)
    n = calcula(FontesArmazem(), estudo, range(PRIMEIRO_EXERCICIO, ULTIMO_EXERCICIO_LIBERADO + 1))
    NUMEROS.write_text(json.dumps(n, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    escreve_docs(json.loads(NUMEROS.read_text(encoding="utf-8")))


if __name__ == "__main__":
    main()
