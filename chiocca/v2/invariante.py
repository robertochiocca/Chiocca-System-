"""Invariante do estudo 1 (Fase C1): o motor v1 sobre o armazém reproduz o estudo na data de corte de cada exercício.

Para cada exercício de 2010 a `ULTIMO_EXERCICIO_LIBERADO`, roda `chiocca.v2.na_data.corte_transversal` sobre
`FontesArmazem` sem data de referência (cada empresa na data de corte do seu exercício, como no estudo) e compara,
coluna por coluna, com `resultados/sinais_empresa_ano.csv`: situação, amostra, cada sinal e componente, cada motivo
de "não calculável", cada alerta, avaliada e em alerta. Os dois lados passam pelo mesmo CSV, e a comparação é exata.

Também roda o mesmo corte com a data de referência máxima (31/12/2024), para mostrar o motor numa data posterior:
quantas empresa-anos têm outra versão conhecida nessa data, quantas ficam pendentes do ENET e quantos alertas mudam.
Só números agregados; as únicas empresas citadas são as dos casos do gabarito (públicos), numa seção descritiva
pedida em 09/11/2026: o estado de alerta delas no corte e em 31/12/2024, quando têm outra versão nessa data.

Pedidos de 09/11/2026 também registrados: o universo (situação de cada empresa-ano na data de corte, para explicar
as 8.594 empresa-anos das conferências contra as 9.474 do invariante), os documentos só com estrutura por exercício
e quantas vezes o motor leu estrutura de documento posterior à data.

Grava docs/invariante_numeros.json (versionado) e monta docs/armazenamento-temporal.md e
docs/en/temporal-storage.md a partir dele.

Uso: python -m chiocca.v2.invariante   (precisa de data/armazem, montado por python -m chiocca.v2.armazem)
"""

from __future__ import annotations

import io
import json
from typing import Any

import pandas as pd

from chiocca import base
from chiocca.base import PENDENTE_ENET, RAIZ, SEM_VERSAO_ATE_CORTE
from chiocca.formato import data, decimal, inteiro
from chiocca.sinais.mscore import COEFICIENTES
from chiocca.v2 import comparativo
from chiocca.v2.armazem import PRIMEIRO_EXERCICIO, SO_METADADOS, FontesArmazem
from chiocca.v2.lacre import DATA_REFERENCIA_MAXIMA, ULTIMO_EXERCICIO_LIBERADO
from chiocca.v2.na_data import corte_transversal

SINAIS_ESTUDO_1 = RAIZ / "resultados" / "sinais_empresa_ano.csv"
NUMEROS = RAIZ / "docs" / "invariante_numeros.json"
DOCS = {"pt": RAIZ / "docs" / "armazenamento-temporal.md", "en": RAIZ / "docs" / "en" / "temporal-storage.md"}
CHAVE = ["exercicio", "cd_cvm", "dt_refer"]
NUMEROS_ESTUDO_1 = RAIZ / "docs" / "resultados_numeros.json"
NUMEROS_CONFERENCIAS = RAIZ / "docs" / "conferencias_numeros.json"
SINAIS = [*COEFICIENTES, "mscore", "dpo", "juro", "lucro_sem_caixa", "peso_nao_recorrente", "alavancagem"]
ALERTAS = ["alerta_mscore", "alerta_dpo", "alerta_juro", "alerta_peso_nao_recorrente"]
ORDEM_SITUACAO = [base.OK, base.SEM_VERSAO_ATE_CORTE, base.INDISPONIVEL_INDIVIDUAL, base.CONTA_REPETIDA,
                  base.SEM_DOCUMENTO, base.PENDENTE_ENET, base.INDISPONIVEL_ENET]  # fmt: skip


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


def _mudou(x: Any, y: Any) -> bool:
    if pd.isna(x) and pd.isna(y):
        return False
    if pd.isna(x) or pd.isna(y):
        return True
    return abs(float(x) - float(y)) > 1e-9 * max(1.0, abs(float(x)))


def _estado(v: Any) -> str:
    """Estado de uma coluna de alerta: em alerta, sem alerta ou não calculável."""
    return "alerta" if str(v) == "True" else "sem_alerta" if str(v) == "False" else "nao_calculavel"


def casos_com_outra_versao(
    no_corte: pd.DataFrame, na_data: pd.DataFrame, casos: list[dict[str, Any]], ano: int
) -> list[dict[str, Any]]:
    """Empresa-anos de casos do gabarito (período afetado) com outra versão na data máxima: o que mudou."""
    m = no_corte.merge(na_data, on=CHAVE, suffixes=("_corte", "_data"))
    out = []
    for c in casos:
        if not c.get("cd_cvm") or ano not in (c.get("anos_periodo") or []):
            continue
        for x in m[m.cd_cvm.astype(str) == str(c["cd_cvm"])].to_dict("records"):
            if x["status_corte"] == SEM_VERSAO_ATE_CORTE or str(x["dt_receb_corte"]) == str(x["dt_receb_data"]):
                continue
            out.append({
                "caso_id": c["caso_id"], "empresa": c["empresa"], "exercicio": ano, "data_publica": c.get("data_publica"),
                "dt_receb_corte": str(x["dt_receb_corte"])[:10], "dt_receb_data": str(x["dt_receb_data"])[:10],
                "em_alerta_corte": bool(x["em_alerta_corte"]), "em_alerta_data": bool(x["em_alerta_data"]),
                "sinais_mudaram": [s for s in SINAIS if s + "_corte" in x and _mudou(x[s + "_corte"], x[s + "_data"])],
                "alertas_mudaram": [{"alerta": a.removeprefix("alerta_"), "corte": _estado(x[a + "_corte"]),
                                     "data": _estado(x[a + "_data"])} for a in ALERTAS
                                    if a + "_corte" in x and _estado(x[a + "_corte"]) != _estado(x[a + "_data"])],
            })  # fmt: skip
    return out


def caso_comparativo(fontes: FontesArmazem, cd_cvm: str, exercicio: int, maiores: int = 10) -> dict[str, Any]:
    """Um caso do gabarito no comparativo do ano seguinte, na data máxima (descritivo)."""
    lt = base.como_era(fontes, cd_cvm, exercicio, corte=DATA_REFERENCIA_MAXIMA)  # type: ignore[arg-type]
    seg = comparativo.leitura_seguinte(fontes, cd_cvm, exercicio, DATA_REFERENCIA_MAXIMA)
    if seg is None:
        return {}
    difs = sorted(comparativo.comparar(lt, seg), key=lambda d: -abs(d.diferenca))
    return {
        "cd_cvm": cd_cvm, "exercicio": exercicio, "versao": lt.versao, "dt_receb": str(lt.dt_receb),
        "versao_seguinte": seg.versao, "dt_receb_seguinte": str(seg.dt_receb),
        "contas_comparadas": comparativo.contas_comparadas(lt, seg), "com_diferenca": len(difs),
        "maiores": [{"demonstracao": d.demonstracao, "cd_conta": d.cd_conta, "ds_conta": d.ds_conta, "valor": d.valor,
                     "valor_comparativo": d.valor_comparativo, "diferenca": d.diferenca} for d in difs[:maiores]],
    }  # fmt: skip


def calcula(fontes: FontesArmazem, estudo: pd.DataFrame, anos: range) -> dict[str, Any]:
    casos = json.loads(NUMEROS_ESTUDO_1.read_text(encoding="utf-8"))["casos"]
    out: dict[str, Any] = {"exercicios": {}, "data_maxima": {}, "casos_com_outra_versao": []}
    for ano in anos:
        no_corte, _ = corte_transversal(fontes, ano)
        r = compara(no_corte, estudo[estudo.exercicio == ano])
        r["situacao"] = {k: int(v) for k, v in no_corte.status.value_counts().items()}
        r["estrutura_de_documento_posterior"] = int(no_corte.estrutura_de_documento_posterior.sum())
        out["exercicios"][str(ano)] = r
        na_data, _ = corte_transversal(fontes, ano, DATA_REFERENCIA_MAXIMA)
        out["data_maxima"][str(ano)] = na_data_maxima(no_corte, na_data)
        out["casos_com_outra_versao"] += casos_com_outra_versao(no_corte, na_data, casos, ano)
        print(ano, r["empresa_anos_iguais"], flush=True)
    so_meta = fontes.consulta(
        "SELECT exercicio, count(DISTINCT cd_cvm || dt_refer) AS docs FROM contas WHERE origem = ? "
        "GROUP BY exercicio ORDER BY exercicio",
        [SO_METADADOS],
    )
    escalas = fontes.consulta(
        "SELECT escala, count(*) AS n FROM (SELECT DISTINCT exercicio, cd_cvm, dt_refer, versao, tipo, escala "
        "FROM escalas) GROUP BY escala ORDER BY escala"
    )
    out["armazem"] = {
        "linhas": fontes.manifesto["linhas"],
        "documentos_enet": fontes.manifesto["documentos_enet"],
        "documentos_so_metadados": int(so_meta.docs.sum()),
        "so_metadados_por_exercicio": {str(int(a)): int(n) for a, n in zip(so_meta.exercicio, so_meta.docs)},
        "versoes_por_escala": {str(e): int(n) for e, n in zip(escalas.escala, escalas.n)},
        "exercicios": fontes.manifesto["exercicios"],
    }
    out["comparativo"] = {"tolerancia": comparativo.TOLERANCIA,
                          "por_exercicio": comparativo.contagem(fontes, DATA_REFERENCIA_MAXIMA, anos),
                          "americanas_2021": caso_comparativo(fontes, "20990", 2021)}  # fmt: skip
    out["empresa_anos_conferencias"] = json.loads(NUMEROS_CONFERENCIAS.read_text(encoding="utf-8"))["empresa_anos"]
    out["ultimo_exercicio_liberado"] = ULTIMO_EXERCICIO_LIBERADO
    out["data_referencia_maxima"] = str(DATA_REFERENCIA_MAXIMA)
    return out


def situacao_total(n: dict[str, Any]) -> dict[str, int]:
    tot: dict[str, int] = {}
    for v in n["exercicios"].values():
        for k, x in v.get("situacao", {}).items():
            tot[k] = tot.get(k, 0) + x
    return tot


def frase_so_metadados(n: dict[str, Any], lang: str) -> str:
    """Contagem por exercício dos documentos só com estrutura no armazém (para os contratos e este documento)."""
    a = n["armazem"]
    por = "; ".join(f"{ano}: {inteiro(k, lang)}" for ano, k in a["so_metadados_por_exercicio"].items())
    total = inteiro(a["documentos_so_metadados"], lang)
    if lang == "pt":
        return f"Documentos entregues depois de {data(n['data_referencia_maxima'], 'pt')} com só a estrutura no armazém, por exercício: {por} (total: {total})."
    return f"Documents filed after {data(n['data_referencia_maxima'], 'en')} with only their structure in the store, by fiscal year: {por} (total: {total})."


T: dict[str, dict[str, Any]] = {
    "pt": {
        "titulo": "# Armazenamento temporal e motor v1 em qualquer data (Fases C1 e C2)",
        "gerado": "Gerado por `python -m chiocca.v2.invariante` a partir de `docs/invariante_numeros.json`. Não edite à mão: um teste compara este arquivo com a saída do script. Só números agregados; as únicas empresas citadas são as dos casos do gabarito, que são públicos.",
        "h_armazem": "## O armazém",
        "armazem": [
            "Parquet consultado pelo DuckDB (`chiocca/v2/armazem.py`), montado sem rede de `data/brutos/cvm` (conferido por hash) e do cache do ENET, em `data/armazem/`, fora do git. Exercícios de {ini} a {fim}; nenhum exercício lacrado entra.",
            "Tabelas: `versoes` ({versoes} versões de DFP, com a data de entrega), `contas` ({contas} linhas, dos dados abertos e de {enet} documentos do ENET), `fca` ({fca} versões), `cadastro` ({cadastro} linhas) e `escalas` (escala original de cada demonstração dos dados abertos). O `manifesto.json` guarda o hash SHA-256 de cada arquivo de origem.",
            "De documento entregue depois de {maxima}, o armazém guarda só metadados: versão, data de entrega e a estrutura, isto é, quais demonstrações existem e o tipo (consolidado ou individual), sem nenhuma conta nem valor (decisão de 09/11/2026: a estrutura conta como metadado). {so_meta_frase} O `como_era` do motor v1 usa essa estrutura da última versão para saber se há consolidado (rota do ENET, emenda 8) e para nomear a DFC do ENET; com data de referência até {maxima}, os valores dessa versão nunca são lidos, e um teste garante que nenhuma conta nem valor desses documentos é guardado.",
            "`FontesArmazem` tem a mesma interface dos arquivos brutos (`chiocca.cvm.Fontes`): o motor v1 roda sobre o armazém sem nenhuma mudança.",
        ],
        "h_motor": "## Motor v1 na data",
        "motor": [
            "`ExercicioNaData` (`chiocca/v2/na_data.py`): uma empresa num exercício, como era na data de referência, com a versão usada, só as versões entregues até a data, a origem (dados abertos ou ENET) e o link do documento. A data passa pelo intervalo de {minima} a {maxima}, e o exercício, pelo lacre.",
            "Corte transversal na data: as mesmas funções do estudo 1 (`como_era`, `grupos`, `sinais_amostra`), com os decis do ano recalculados só com as empresas cuja versão era pública na data.",
            "Quando a versão usada não é a última, o `como_era` lê a estrutura da última versão, entregue depois da data (comportamento do estudo 1, emenda 8). A linhagem registra: \"estrutura lida de documento posterior à data (comportamento do estudo 1, emenda 8)\". Na data de corte de cada exercício, isso aconteceu em {posterior} empresa-anos de 2010 a 2023.",
            "Camada do produto, ao lado do motor e sem mudar nenhum valor dele: a coluna `produto_nao_calculaveis` lista os sinais que o produto mostra como \"não calculável\" por balanço não preenchido.",
        ],
        "h_c2": "## Fase C2: escala, evidências e busca no ENET",
        "c2": [
            "`escala_original` da versão usada: dos dados abertos, {escalas}. O cache do ENET guarda os valores já em reais e não registra a escala da página; nas versões do ENET, o campo fica vazio, com esse motivo na linhagem.",
            "Evidências do contrato: cada linha da DFP lida vira uma `Evidencia`, com id estável, documento (versão, data de entrega, origem, endereço e hash), demonstração, coluna, conta, descrição oficial, valor em reais e, com o `Localizador`, o arquivo e a linha de origem.",
            "Busca no ENET por comando separado (`python -m chiocca.v2.buscar_enet AAAA-MM-DD`): lista as versões que a data precisa e que não estão no armazém, baixa só essas (consolidado, exercícios liberados, entregues até {maxima}) e remonta o armazém. Nenhuma consulta baixa nada.",
        ],
        "h_universo": "## Universo",
        "universo": "As conferências da Fase B ([`docs/conferencias.md`](conferencias.md)) contam as {conferencias} empresa-anos com a versão da época; o invariante compara todas as {total} empresa-anos com DFP de 2010 a 2023, inclusive as {fora} sem versão da época ({lista}), que também têm de sair iguais ao estudo 1.",
        "situacoes": {base.SEM_VERSAO_ATE_CORTE: "sem versão até o corte", base.INDISPONIVEL_INDIVIDUAL: "versão da época só com demonstração individual, sem a rota do ENET",
                      base.CONTA_REPETIDA: "conta repetida com valores diferentes", base.SEM_DOCUMENTO: "sem documento",
                      base.PENDENTE_ENET: "pendente do ENET", base.INDISPONIVEL_ENET: "falha do ENET"},
        "h_invariante": "## Invariante do estudo 1",
        "invariante": "Na data de corte de cada exercício, o motor v1 sobre o armazém reproduz `resultados/sinais_empresa_ano.csv` em {iguais} de {total} empresa-anos, com comparação exata de {colunas} colunas (situação, amostra, cada sinal, componente e motivo de \"não calculável\", cada alerta, avaliada e em alerta).",
        "col_invariante": "| Exercício | Empresa-anos no estudo 1 | Empresa-anos no armazém | Iguais em todas as colunas | Colunas com diferença |",
        "nenhuma": "nenhuma",
        "h_data": "## O mesmo exercício visto em {maxima}",
        "data": "Com a data de referência em {maxima}, cada exercício usa a versão mais recente entregue até essa data. Contagens contra a data de corte:",
        "col_data": "| Exercício | Com versão na data de corte | Outra versão conhecida em {maxima} | Pendentes do ENET em {maxima} | Avaliadas nas duas datas | Entram em alerta | Saem do alerta |",
        "pendentes": "\"Pendente do ENET\" é a versão da data que não está no armazém; a busca no ENET é um comando separado e nunca acontece dentro de uma consulta (pergunta 9 do plano).",
        "h_casos": "## Casos do gabarito com outra versão em {maxima}",
        "rotulo_casos": "**Análise descritiva, não pré-registrada.** O estudo 1 não muda. Empresa-anos do período afetado de casos do gabarito que, em {maxima}, tinham outra versão da DFP entregue depois da data de corte; o estado de alerta nas duas datas e os sinais cujo valor mudou.",
        "col_casos": "| Caso | Exercício | Data pública do caso | Versão do corte (entrega) | Versão em {maxima} (entrega) | Em alerta no corte | Em alerta em {maxima} | Sinais com outro valor (ou outra calculabilidade) | Alertas que mudaram (corte → {maxima}) |",
        "sem_casos": "Nenhuma empresa-ano de caso do gabarito tinha outra versão em {maxima}.",
        "sim": "sim",
        "nao": "não",
        "nenhum": "nenhum",
        "estados": {"alerta": "em alerta", "sem_alerta": "sem alerta", "nao_calculavel": "não calculável"},
        "h_comparativo": "## Reapresentação pelo comparativo do ano seguinte em {maxima}",
        "rotulo_comparativo": "**Análise descritiva.** O estudo 1 e o motor v1 não mudam. Regra de 09/11/2026 (`docs/contratos.md`, seção 4): quando a DFP de t+1 já é pública na data, cada conta de t na versão usada é comparada com a coluna PENÚLTIMO de t+1 (mesma demonstração, mesmo código, mesmo tipo); diferença acima de R$ {tol} por conta vai para a investigação como evidência, com o texto \"valor diferente no comparativo do ano seguinte (reapresentação ou reclassificação)\". Pelo lacre, o exercício de 2023 não tem comparação.",
        "resultado_comparativo": "Em {maxima}, {com} de {comp} empresa-anos comparáveis (de {ini} a {fim}) têm pelo menos uma conta com diferença acima da tolerância.",
        "col_comparativo": "| Exercício | Empresa-anos comparáveis | Com alguma diferença |",
        "h_americanas": "**Americanas S.A. (`americanas`), exercício {ex}.** A DFP de {ex} tem uma única versão, entregue em {receb}; a reapresentação veio no comparativo da DFP de {ex1}, entregue em {receb1}, e não numa versão nova da DFP de {ex}. Por isso a Americanas não está entre as empresa-anos com outra versão em {maxima}. Das {comp} contas comparáveis, {com} têm diferença acima da tolerância; as {n} maiores, em R$ milhões:",
        "col_americanas": "| Demonstração | Conta | Descrição | DFP de {ex} (entregue em {receb}) | Comparativo da DFP de {ex1} (entregue em {receb1}) | Diferença |",
        "h_uso": "## Como reproduzir",
        "uso": ["python -m chiocca.v2.armazem      # monta data/armazem a partir de data/brutos/cvm e data/cache/enet",
                "python -m chiocca.v2.buscar_enet 2024-12-31 --listar   # versões que a data precisa e não estão no armazém",
                "python -m chiocca.v2.invariante   # invariante e corte na data máxima; grava este documento"],
    },
    "en": {
        "titulo": "# Temporal storage and engine v1 on any date (Phases C1 and C2)",
        "gerado": "Generated by `python -m chiocca.v2.invariante` from `docs/invariante_numeros.json`. Do not edit by hand: a test compares this file with the script output. Aggregate numbers only; the only companies named are those of the ground-truth cases, which are public.",
        "h_armazem": "## The store",
        "armazem": [
            "Parquet queried through DuckDB (`chiocca/v2/armazem.py`), built offline from `data/brutos/cvm` (checked by hash) and the ENET cache, in `data/armazem/`, outside git. Fiscal years {ini} to {fim}; no sealed fiscal year goes in.",
            "Tables: `versoes` ({versoes} DFP versions, with the filing date), `contas` ({contas} rows, from open data and from {enet} ENET documents), `fca` ({fca} versions), `cadastro` ({cadastro} rows) and `escalas` (original scale of each open-data statement). `manifesto.json` keeps the SHA-256 hash of every source file.",
            "For documents filed after {maxima}, the store keeps metadata only: version, filing date and the structure, that is, which statements exist and their type (consolidated or individual), with no account and no value (decision of 2026-11-09: the structure counts as metadata). {so_meta_frase} Engine v1's `como_era` uses this structure of the latest version to know whether a consolidated statement exists (the ENET route, amendment 8) and to name the ENET cash flow statement; with a reference date up to {maxima}, that version's values are never read, and a test ensures no account or value of these documents is stored.",
            "`FontesArmazem` has the same interface as the raw files (`chiocca.cvm.Fontes`): engine v1 runs on the store without any change.",
        ],
        "h_motor": "## Engine v1 on the date",
        "motor": [
            "`ExercicioNaData` (`chiocca/v2/na_data.py`): one company in one fiscal year, as it was on the reference date, with the version used, only the versions filed by the date, the origin (open data or ENET) and the document link. The date goes through the {minima} to {maxima} range, and the fiscal year through the seal.",
            "Cross-section on the date: the same study 1 functions (`como_era`, `grupos`, `sinais_amostra`), with the year's deciles recomputed only with the companies whose version was public on the date.",
            "When the version used is not the latest, `como_era` reads the structure of the latest version, filed after the date (study 1 behaviour, amendment 8). The lineage records: \"structure read from a document filed after the date (study 1 behaviour, amendment 8)\". On each fiscal year's cut-off date, this happened in {posterior} company-years from 2010 to 2023.",
            "Product layer, next to the engine and without changing any of its values: the `produto_nao_calculaveis` column lists the signals the product shows as \"not computable\" because of an unfilled balance sheet.",
        ],
        "h_c2": "## Phase C2: scale, evidence and ENET fetching",
        "c2": [
            "`escala_original` of the version used: from open data, {escalas}. The ENET cache keeps values already in reais and does not record the page's scale; for ENET versions, the field is empty, with that reason in the lineage.",
            "Contract evidence: each DFP line read becomes an `Evidencia`, with a stable id, document (version, filing date, origin, address and hash), statement, column, account, official description, value in reais and, with the `Localizador`, the source file and line.",
            "ENET fetching through a separate command (`python -m chiocca.v2.buscar_enet YYYY-MM-DD`): it lists the versions the date needs that are not in the store, fetches only those (consolidated, released fiscal years, filed by {maxima}) and rebuilds the store. No query fetches anything.",
        ],
        "h_universo": "## Universe",
        "universo": "The Phase B data checks ([`docs/en/data-checks.md`](data-checks.md)) count the {conferencias} company-years with the point-in-time version; the invariant compares all {total} company-years with a DFP from 2010 to 2023, including the {fora} without a point-in-time version ({lista}), which must also match study 1.",
        "situacoes": {base.SEM_VERSAO_ATE_CORTE: "no version by the cut-off", base.INDISPONIVEL_INDIVIDUAL: "point-in-time version with individual statements only, without the ENET route",
                      base.CONTA_REPETIDA: "repeated account with different values", base.SEM_DOCUMENTO: "no document",
                      base.PENDENTE_ENET: "pending from ENET", base.INDISPONIVEL_ENET: "ENET failure"},
        "h_invariante": "## Study 1 invariant",
        "invariante": "On each fiscal year's cut-off date, engine v1 on the store reproduces `resultados/sinais_empresa_ano.csv` in {iguais} of {total} company-years, with an exact comparison of {colunas} columns (status, sample, each signal, component and \"not computable\" reason, each alert, evaluated and in alert).",
        "col_invariante": "| Fiscal year | Company-years in study 1 | Company-years in the store | Equal in every column | Columns with a difference |",
        "nenhuma": "none",
        "h_data": "## The same fiscal year seen on {maxima}",
        "data": "With the reference date on {maxima}, each fiscal year uses the latest version filed by that date. Counts against the cut-off date:",
        "col_data": "| Fiscal year | With a version on the cut-off date | Another version known on {maxima} | Pending from ENET on {maxima} | Evaluated on both dates | Enter alert | Leave alert |",
        "pendentes": "\"Pending from ENET\" is the version of the date that is not in the store; fetching from ENET is a separate command and never happens inside a query (plan question 9).",
        "h_casos": "## Ground-truth cases with another version on {maxima}",
        "rotulo_casos": "**Descriptive analysis, not pre-registered.** Study 1 does not change. Company-years in the affected period of ground-truth cases that, on {maxima}, had another DFP version filed after the cut-off date; the alert state on both dates and the signals whose value changed.",
        "col_casos": "| Case | Fiscal year | Case public date | Cut-off version (filed) | Version on {maxima} (filed) | In alert at cut-off | In alert on {maxima} | Signals with another value (or computability) | Alerts that changed (cut-off → {maxima}) |",
        "sem_casos": "No ground-truth case company-year had another version on {maxima}.",
        "sim": "yes",
        "nao": "no",
        "nenhum": "none",
        "estados": {"alerta": "in alert", "sem_alerta": "no alert", "nao_calculavel": "not computable"},
        "h_comparativo": "## Restatement through the following year's comparative on {maxima}",
        "rotulo_comparativo": "**Descriptive analysis.** Study 1 and engine v1 do not change. Rule of 2026-11-09 (`docs/en/contracts.md`, section 4): when the DFP of t+1 is already public on the date, each account of t in the version used is compared with the PENÚLTIMO column of t+1 (same statement, same code, same type); a difference above R${tol} per account goes into the investigation as evidence, with the text \"different value in the following year's comparative (restatement or reclassification)\". Because of the seal, fiscal year 2023 has no comparison.",
        "resultado_comparativo": "On {maxima}, {com} of {comp} comparable company-years (from {ini} to {fim}) have at least one account with a difference above the tolerance.",
        "col_comparativo": "| Fiscal year | Comparable company-years | With some difference |",
        "h_americanas": "**Americanas S.A. (`americanas`), fiscal year {ex}.** The {ex} DFP has a single version, filed on {receb}; the restatement came in the comparative of the {ex1} DFP, filed on {receb1}, not in a new version of the {ex} DFP. That is why Americanas is not among the company-years with another version on {maxima}. Of the {comp} comparable accounts, {com} have a difference above the tolerance; the {n} largest, in R$ million:",
        "col_americanas": "| Statement | Account | Description | {ex} DFP (filed on {receb}) | Comparative in the {ex1} DFP (filed on {receb1}) | Difference |",
        "h_uso": "## How to reproduce",
        "uso": ["python -m chiocca.v2.armazem      # builds data/armazem from data/brutos/cvm and data/cache/enet",
                "python -m chiocca.v2.buscar_enet 2024-12-31 --listar   # versions the date needs that are not in the store",
                "python -m chiocca.v2.invariante   # invariant and cross-section on the maximum date; writes this document"],
    },
}  # fmt: skip


def render(n: dict[str, Any], lang: str) -> str:
    from chiocca.v2.lacre import DATA_REFERENCIA_MINIMA

    t = T[lang]
    i = lambda x: inteiro(x, lang)  # noqa: E731
    a, li = n["armazem"], n["armazem"]["linhas"]
    maxima, minima = data(n["data_referencia_maxima"], lang), data(str(DATA_REFERENCIA_MINIMA), lang)
    ex = n["exercicios"]
    posterior = sum(v.get("estrutura_de_documento_posterior", 0) for v in ex.values())
    linhas = [t["titulo"], "", t["gerado"], "", t["h_armazem"], ""]
    linhas += ["- " + x.format(ini=min(a["exercicios"]), fim=max(a["exercicios"]), versoes=i(li["versoes"]),
                               contas=i(li["contas"]), enet=i(a["documentos_enet"]), fca=i(li["fca"]),
                               cadastro=i(li["cadastro"]), maxima=maxima, so_meta_frase=frase_so_metadados(n, lang))
               for x in t["armazem"]]  # fmt: skip
    linhas += ["", t["h_motor"], ""]
    linhas += ["- " + x.format(minima=minima, maxima=maxima, posterior=i(posterior)) for x in t["motor"]]
    escalas = ", ".join(
        f"{i(k)} {'versões em' if lang == 'pt' else 'versions in'} {e}" for e, k in a["versoes_por_escala"].items()
    )
    linhas += ["", t["h_c2"], ""] + ["- " + x.format(escalas=escalas, maxima=maxima) for x in t["c2"]]
    sit = situacao_total(n)
    total = sum(v["empresa_anos_estudo"] for v in ex.values())
    if sit.get(base.OK) != n["empresa_anos_conferencias"]:
        raise ValueError("as empresa-anos com versão da época não batem com as das conferências")
    fora = [k for k in ORDEM_SITUACAO if k != base.OK and sit.get(k)]
    lista = "; ".join(f"{t['situacoes'][k]}: {i(sit[k])}" for k in fora)
    linhas += ["", t["h_universo"], "", t["universo"].format(conferencias=i(n["empresa_anos_conferencias"]), total=i(total),
                                                              fora=i(sum(sit[k] for k in fora)), lista=lista)]  # fmt: skip
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
    linhas += [
        "",
        t["pendentes"],
        "",
        t["h_casos"].format(maxima=maxima),
        "",
        t["rotulo_casos"].format(maxima=maxima),
        "",
    ]
    casos = n.get("casos_com_outra_versao", [])
    if casos:
        linhas += [t["col_casos"].format(maxima=maxima), "| --- | --- | --- | --- | --- | --- | --- | --- | --- |"]
        for c in casos:
            sn = lambda v: t["sim"] if v else t["nao"]  # noqa: E731
            sinais = ", ".join(c["sinais_mudaram"]) or t["nenhum"]
            alertas = "; ".join(f"{m['alerta']}: {t['estados'][m['corte']]} → {t['estados'][m['data']]}"
                                for m in c["alertas_mudaram"]) or t["nenhum"]  # fmt: skip
            pub = data(c["data_publica"], lang) if c.get("data_publica") else "—"
            linhas.append(f"| {c['empresa']} (`{c['caso_id']}`) | {c['exercicio']} | {pub} | {data(c['dt_receb_corte'], lang)} | "
                          f"{data(c['dt_receb_data'], lang)} | {sn(c['em_alerta_corte'])} | {sn(c['em_alerta_data'])} | {sinais} | {alertas} |")  # fmt: skip
    else:
        linhas.append(t["sem_casos"].format(maxima=maxima))
    linhas += _comparativo(n, t, lang, maxima)
    linhas += ["", t["h_uso"], "", "```"] + t["uso"] + ["```"]
    return "\n".join(linhas) + "\n"


def _comparativo(n: dict[str, Any], t: dict[str, Any], lang: str, maxima: str) -> list[str]:
    c = n.get("comparativo")
    if not c:
        return []
    i = lambda x: inteiro(x, lang)  # noqa: E731
    por = c["por_exercicio"]
    linhas = [
        "",
        t["h_comparativo"].format(maxima=maxima),
        "",
        t["rotulo_comparativo"].format(tol=i(int(c["tolerancia"]))),
        "",
    ]
    linhas += [t["resultado_comparativo"].format(maxima=maxima, com=i(sum(v["com_diferenca"] for v in por.values())),
                                                 comp=i(sum(v["comparadas"] for v in por.values())), ini=min(por), fim=max(por)), ""]  # fmt: skip
    linhas += [t["col_comparativo"], "| --- | --- | --- |"]
    linhas += [f"| {ano} | {i(v['comparadas'])} | {i(v['com_diferenca'])} |" for ano, v in por.items()]
    a = c.get("americanas_2021")
    if a:
        fmt = dict(
            ex=a["exercicio"],
            ex1=a["exercicio"] + 1,
            receb=data(a["dt_receb"], lang),
            receb1=data(a["dt_receb_seguinte"], lang),
        )
        linhas += ["", t["h_americanas"].format(maxima=maxima, comp=i(a["contas_comparadas"]), com=i(a["com_diferenca"]),
                                                n=i(len(a["maiores"])), **fmt), ""]  # fmt: skip
        linhas += [t["col_americanas"].format(**fmt), "| --- | --- | --- | --- | --- | --- |"]
        m = lambda v: decimal(v / 1e6, lang, 1)  # noqa: E731
        linhas += [f"| {d['demonstracao']} | {d['cd_conta']} | {d['ds_conta']} | {m(d['valor'])} | {m(d['valor_comparativo'])} | {m(d['diferenca'])} |"
                   for d in a["maiores"]]  # fmt: skip
    return linhas


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
