"""Documento da Fase 0 dos EUA (pedido de 23/11/2026, parte 3): os números saem de `docs/eua_fase0_numeros.json`,
gerado por este módulo a partir dos arquivos baixados (`data/eua/`, com o manifesto `data/eua_manifesto.csv`), e o
documento em PT e EN sai do JSON (`render`). Nenhum sinal, alerta, acerto ou ranking.

Uso: python -m chiocca.eua.fase0            (recalcula o JSON com o que está em data/eua/ e monta os documentos)
     python -m chiocca.eua.fase0 --baixar   (antes, baixa a roda do era-py e, com SEC_USER_AGENT, os arquivos da SEC)
"""

from __future__ import annotations

import json
import sys
from typing import Any

from chiocca.base import RAIZ
from chiocca.eua import fsds, rotulos, sec
from chiocca.formato import data, inteiro

SAIDA = RAIZ / "docs" / "eua_fase0_numeros.json"
DOCS = {"pt": RAIZ / "docs" / "eua-fase-0.md", "en": RAIZ / "docs" / "en" / "us-phase-0.md"}


def calcula() -> dict[str, Any]:
    manifesto = {x["arquivo"]: x for x in sec.le_manifesto()}
    roda = rotulos.RODA.relative_to(sec.DADOS).as_posix()
    if roda not in manifesto or sec.sha256(rotulos.RODA) != manifesto[roda]["sha256"]:
        raise SystemExit("a roda do era-py não confere com o manifesto: rode com --baixar")
    baixados = sorted(fsds.PASTA.glob("*.zip")) if fsds.PASTA.exists() else []
    out: dict[str, Any] = {
        "o_que_e": "Fase 0 dos EUA (pedido de 23/11/2026): só inventário e contagens, sem nenhum sinal",
        "limite": {"ultimo_ano": rotulos.ULTIMO_ANO, "trimestres_fsds": [fsds.TRIMESTRES[0], fsds.TRIMESTRES[-1]]},
        "acesso_sec": {
            "variavel": sec.VARIAVEL,
            "fsds_baixados": len(baixados),
            "fsds_previstos": len(fsds.TRIMESTRES),
        },
        "era_py": {"arquivo": roda, "sha256": manifesto[roda]["sha256"], "bytes": int(manifesto[roda]["bytes"])},
        "rotulos": rotulos.contagens(),
        "mapa": {c: list(ts) for c, ts in fsds.MAPA.items()},
        "fsds": None,
    }
    if baixados:  # com os arquivos da SEC: estrutura, 10-K por ano e cobertura das tags
        import pandas as pd

        subs = pd.concat([fsds.submissoes(z) for z in baixados], ignore_index=True)
        tabela = pd.concat(
            [fsds.cobertura_tags(z, subs[subs.trimestre == z.stem]) for z in baixados], ignore_index=True
        )
        out["fsds"] = {"estrutura_do_primeiro": fsds.estrutura(baixados[0]), "por_exercicio": fsds.resumo(subs),
                       "cobertura": fsds.cobertura_por_ano(tabela)}  # fmt: skip
    return out


T: dict[str, dict[str, Any]] = {
    "pt": {
        "titulo": "# Fase 0 dos EUA: reconhecimento dos dados",
        "aviso": "> **Reconhecimento, sem nenhum sinal calculado.** Objetivo: saber se dá para fazer, nos EUA, um estudo "
        "pré-registrado com os dados como eram na época, testando os sinais do v1 e do v2 do Chiocca e a regra boba contra os "
        "AAERs (Accounting and Auditing Enforcement Releases) da SEC. Só inventário e contagens; nada de 2024 em diante; "
        "nenhum nome de pessoa física. A frente dos EUA fica fora do README e do produto até decisão de Roberto.",
        "s_acesso": "## 1. Acesso à SEC",
        "acesso": "A SEC pede um User-Agent com nome e contato e no máximo 10 pedidos por segundo; sem o contato, recusa o "
        "pedido (HTTP 403, conferido nesta sessão). Os scripts leem o User-Agent da variável de ambiente `{var}`, que nenhum "
        "arquivo versionado nem log guarda. Nesta sessão a variável não estava definida, e a ferramenta de privacidade do "
        "ambiente não deixa o agente escrever o contato num comando: **{baixados} de {previstos} arquivos trimestrais da SEC "
        "foram baixados**. Para completar a Fase 0, Roberto define `{var}` nas configurações do ambiente (variável de "
        "ambiente) e uma sessão nova roda `python -m chiocca.eua.fase0 --baixar`.",
        "s_fsds": "## 2. Balanços: os Financial Statement Data Sets da SEC",
        "fsds": "Os números das demonstrações em XBRL, num zip por trimestre de entrega desde 2009 (aqui, de {t0} a {t1}: "
        "os 10-K dos exercícios de 2023, quase todos entregues em 2024, ficam de fora). Os dois arquivos usados são "
        "`sub.txt` (uma linha por entrega: CIK, formulário, data de referência, exercício fiscal, datas de entrega e se a "
        "entrega foi emendada depois) e `num.txt` (uma linha por número: tag, taxonomia, data, trimestres cobertos, unidade "
        "e valor).",
        "versoes": "- **10-K e 10-K/A:** a entrega original e cada emenda são entregas separadas, cada uma com a sua data; "
        "`prevrpt` marca a entrega que foi emendada depois.\n- **A versão pública numa data de corte:** por companhia e "
        'exercício, a última entrega (original ou emenda com números em XBRL) entregue até a data, como o "como era" '
        "do Chiocca no Brasil; o comparativo do exercício seguinte traz os números de t-1 como apresentados depois.",
        "pendente": "**Pendente (sem os arquivos da SEC):** a estrutura conferida nos arquivos, a cobertura de 10-K por ano, "
        "as emendas, os prazos de entrega e a cobertura de cada tag por ano. O código já está pronto e testado com um "
        "arquivo sintético (`chiocca/eua/fsds.py`).",
        "s_mapa": "### O mapa das contas para as tags us-gaap (proposta)",
        "mapa_txt": "As contas que os sinais do v1 e do v2 usam, com as tags candidatas na ordem de preferência. Benford usa "
        "todos os números e não precisa de mapa; a DVA não existe nos EUA (a depreciação vem da DFC); nos EUA, despesas "
        "de vendas e administrativas costumam vir juntas (SG&A), e muitas companhias não apresentam o resultado bruto. As "
        "financeiras (peso de ganhos não recorrentes) ficam sem mapa nesta fase.",
        "cab_mapa": "| Conta | Tags us-gaap candidatas |",
        "s_rotulos": "## 3. Rótulos: os AAERs",
        "era": "**era-py {v}** (PyPI, de Ian Gow, os dados do livro *Empirical Research in Accounting: Tools and Methods*): "
        "licença do pacote {lic}; as tabelas não trazem licença própria, e a origem da ligação gvkey–CIK não é informada. "
        "Por isso nada delas é copiado para o repositório: a roda fica em `data/eua/`, com o SHA-256 no manifesto "
        "(`{sha}`).",
        "indice": "- **O índice de AAERs da SEC** (`aaer_dates`, atualizado pelo autor até {atual}): número, data, "
        "descrição e ano. Até 2023, {n} AAERs ({distintos} números distintos), de {a0} a {a1}. A descrição traz nomes de "
        "companhias e de pessoas físicas e não é lida aqui.",
        "bao": "- **As empresa-anos de Bao et al. (2020)** (`aaer_firm_year`): {linhas} linhas, {aaers} AAERs e {gvkeys} "
        "companhias, identificadas pelo gvkey (Compustat), com o primeiro e o último ano afetados, de {a0} a {a1}: "
        "{fy} empresa-anos com balanço errado alegado. {multi} dos AAERs afetam mais de um ano.",
        "ligacao": "- **A ligação gvkey–CIK** (`gvkey_ciks`): {linhas} ligações, {gvkeys} gvkeys e {ciks} CIKs, com as "
        "datas de cada ligação. Com ela, cada empresa-ano de Bao et al. se liga ao CIK da SEC sem a Compustat.",
        "cfrm": "- **A base da CFRM (Berkeley), usada por Dechow et al. (2011):** hoje vendida pelo site da USC (página "
        '"Buy the Data", pagamento pelo cashnet; o preço não aparece no texto da página); os termos proíbem passar a base '
        "a terceiros, exceto coautores; cobre 4.581 AAERs emitidos de 17/05/1982 a 31/12/2025, com o nome e os "
        "identificadores da companhia, as contas afetadas e os anos e trimestres errados (a página não diz quais "
        "identificadores). Só as condições de acesso foram lidas.",
        "sec_lista": "- **A lista pública de AAERs no site da SEC:** não foi lida diretamente (o site exige o User-Agent "
        "com contato); o índice do era-py é uma cópia dela, com a data da atualização.",
        "ligar": "**Como ligar cada AAER ao CIK sem a Compustat.** Até 2014, pelas empresa-anos de Bao et al. e pela "
        "ligação gvkey–CIK do era-py. Depois de 2014, não há base livre com os anos errados: o caminho é ler cada AAER "
        "no site da SEC (a companhia é parte do processo) e casar o nome com o arquivo de nomes e CIKs da SEC (`cik-lookup-data.txt`, a "
        "conferir quando o acesso estiver configurado), guardando só a companhia e o CIK.",
        "s_contagens": "## 4. Contagens",
        "cab_cont": "| Exercício | Empresa-anos com AAER (Bao et al.) | Ligadas a um CIK | Com 10-K nos dados da SEC | Empresa-anos com 10-K |",
        "pendente_curto": "pendente",
        "cont_txt": "Nos exercícios com XBRL (de 2009 a 2014, o fim dos anos afetados de Bao et al.): {fy} empresa-anos "
        "com AAER, das quais {lig} se ligam a um CIK. Os anos mais recentes têm menos casos porque um AAER costuma sair "
        "anos depois da fraude, e a base termina em 2014. O índice da SEC tem {n_xbrl} AAERs emitidos de 2009 a 2023, de "
        "todos os tipos (não só balanço errado).",
        "s_decisoes": "## 5. Decisões para Roberto",
        "decisoes": [
            "**Período possível.** Balanços em XBRL desde 2009 (todas as companhias desde 2011). Com rótulos livres, os anos "
            "afetados vão só até 2014: a interseção é de 2009 a 2014. Para ir além de 2014, comprar a base da CFRM (até "
            "2025) ou classificar os AAERs da SEC à mão.",
            "**Tamanho esperado.** {fy} empresa-anos com AAER nos exercícios com XBRL, {lig} ligadas a um CIK, contra "
            "os 10-K de cada ano (o número sai dos arquivos da SEC). Com fraudes de vários anos "
            "contadas uma vez, o número de casos é menor ainda: o poder será baixo, como no estudo 1.",
            "**O que não dá sem dados pagos.** Os anos errados depois de 2014 (CFRM); o gvkey e os dados da Compustat "
            "(WRDS); as republicações da Audit Analytics. A ligação gvkey–CIK do era-py não informa a origem.",
            "**Fraudes de vários anos.** Walker (2021) mostrou que, em Bao et al. (2020), fraudes que atravessam o período "
            "de treino e o de teste inflam a medida; a errata (JAR, 2022) reconheceu um erro de código que deixou cerca de "
            "10% desses casos sem recodificar, Walker (2022) criticou a errata, e Gow (2022) discutiu se o artigo deveria "
            "ser retratado. Proposta: o desfecho por caso (uma fraude, uma vez), como o acerto do estudo 1, com o "
            "bootstrap por companhia, como no estudo 2; os sinais são regras fixas, sem treino.",
        ],
        "s_calendario": "### Rascunho de calendário até maio de 2027",
        "cab_cal": "| Até | Etapa |",
        "calendario": [
            (
                "2026-12-15",
                "Roberto define o User-Agent; a Fase 0 termina com os arquivos da SEC (estrutura, 10-K por ano, cobertura das tags).",
            ),
            ("2027-01-15", "Decisão dos rótulos (até 2014, ou comprar a CFRM, ou classificar à mão) e do período."),
            ("2027-02-28", "Rascunho do pré-registro dos EUA: amostra, desfecho por caso, métricas e regra boba."),
            ("2027-03-31", "Revisão de Roberto, registro e carimbo; código congelado."),
            ("2027-05-31", "Cálculo único e relatório, separado do estudo 2 do Brasil."),
        ],
        "fontes": "Fontes das condições e da crítica: sites.google.com/usc.edu/aaerdataset (Buy the Data); "
        "econjwatch.org (Walker, 2021 e 2022); iangow.github.io/notes/published/bklyz.html (Gow, 2022).",
    },
    "en": {
        "titulo": "# US Phase 0: data reconnaissance",
        "aviso": "> **Reconnaissance, with no signal computed.** Goal: find out whether a pre-registered US study is feasible, "
        "with the data as they were at the time, testing Chiocca's v1 and v2 signals and the naive rule against the SEC's "
        "AAERs (Accounting and Auditing Enforcement Releases). Inventory and counts only; nothing from 2024 on; no names of "
        "individuals. The US front stays out of the README and the product until Roberto decides.",
        "s_acesso": "## 1. Access to the SEC",
        "acesso": "The SEC asks for a User-Agent with a name and contact and at most 10 requests per second; without the "
        "contact it refuses the request (HTTP 403, checked in this session). The scripts read the User-Agent from the "
        "environment variable `{var}`, which no versioned file or log keeps. In this session the variable was not set, and "
        "the environment's privacy tool does not let the agent write the contact into a command: **{baixados} of "
        "{previstos} quarterly SEC files were downloaded**. To finish Phase 0, Roberto sets `{var}` in the environment "
        "settings (environment variable) and a new session runs `python -m chiocca.eua.fase0 --baixar`.",
        "s_fsds": "## 2. Balance sheets: the SEC Financial Statement Data Sets",
        "fsds": "The financial statement numbers in XBRL, one zip per filing quarter since 2009 (here, from {t0} to {t1}: "
        "the 10-Ks for fiscal 2023, almost all filed in 2024, are left out). The two files used are `sub.txt` (one row per "
        "filing: CIK, form, report date, fiscal year, filing dates and whether the filing was later amended) and `num.txt` "
        "(one row per number: tag, taxonomy, date, quarters covered, unit and value).",
        "versoes": "- **10-K and 10-K/A:** the original filing and each amendment are separate filings, each with its "
        "date; `prevrpt` flags a filing that was later amended.\n- **The public version at a cutoff date:** per company "
        "and fiscal year, the last filing (original or amendment with XBRL numbers) filed by that date, like Chiocca's "
        '"as it was" in Brazil; the next year\'s comparative column shows the t-1 numbers as presented later.',
        "pendente": "**Pending (without the SEC files):** the structure checked on the files, 10-K coverage by year, "
        "amendments, filing lags and the coverage of each tag by year. The code is ready and tested on a synthetic file "
        "(`chiocca/eua/fsds.py`).",
        "s_mapa": "### The map from accounts to us-gaap tags (proposal)",
        "mapa_txt": "The accounts the v1 and v2 signals use, with candidate tags in order of preference. Benford uses all "
        "numbers and needs no map; the DVA does not exist in the US (depreciation comes from the cash flow statement); in "
        "the US, selling and administrative expenses usually come together (SG&A), and many companies do not present "
        "gross profit. Financial companies (weight of non-recurring gains) have no map in this phase.",
        "cab_mapa": "| Account | Candidate us-gaap tags |",
        "s_rotulos": "## 3. Labels: the AAERs",
        "era": "**era-py {v}** (PyPI, by Ian Gow, the data for the book *Empirical Research in Accounting: Tools and "
        "Methods*): package license {lic}; the tables carry no license of their own, and the source of the gvkey–CIK link "
        "is not stated. So nothing from them is copied into the repository: the wheel stays in `data/eua/`, with its "
        "SHA-256 in the manifest (`{sha}`).",
        "indice": "- **The SEC AAER index** (`aaer_dates`, refreshed by the author through {atual}): number, date, "
        "description and year. Through 2023, {n} AAERs ({distintos} distinct numbers), from {a0} to {a1}. The description "
        "carries names of companies and individuals and is not read here.",
        "bao": "- **The Bao et al. (2020) company-years** (`aaer_firm_year`): {linhas} rows, {aaers} AAERs and {gvkeys} "
        "companies, identified by gvkey (Compustat), with the first and last affected years, from {a0} to {a1}: {fy} "
        "company-years with an alleged misstatement. {multi} of the AAERs affect more than one year.",
        "ligacao": "- **The gvkey–CIK link** (`gvkey_ciks`): {linhas} links, {gvkeys} gvkeys and {ciks} CIKs, with the "
        "dates of each link. With it, each Bao et al. company-year links to the SEC CIK without Compustat.",
        "cfrm": '- **The CFRM (Berkeley) database, used by Dechow et al. (2011):** now sold through the USC site ("Buy the '
        'Data" page, payment through cashnet; the price does not appear in the page text); the terms forbid passing the '
        "data to third parties, except co-authors; it covers 4,581 AAERs issued from 1982-05-17 to 2025-12-31, with the "
        "company's name and identifiers, the affected accounts and the misstated years and quarters (the page does not "
        "say which identifiers). Only the access conditions were read.",
        "sec_lista": "- **The public AAER list on the SEC site:** not read directly (the site requires the User-Agent "
        "with a contact); the era-py index is a copy of it, with the refresh date.",
        "ligar": "**How to link each AAER to the CIK without Compustat.** Through 2014, through the Bao et al. "
        "company-years and the era-py gvkey–CIK link. After 2014, there is no free database with the misstated years: the "
        "path is to read each AAER on the SEC site (the company is a party) and match the name against the SEC file of "
        "names and CIKs (`cik-lookup-data.txt`, to be checked once access is set up), keeping only the company and the CIK.",
        "s_contagens": "## 4. Counts",
        "cab_cont": "| Fiscal year | Company-years with an AAER (Bao et al.) | Linked to a CIK | With a 10-K in the SEC data | Company-years with a 10-K |",
        "pendente_curto": "pending",
        "cont_txt": "In the fiscal years with XBRL (2009 to 2014, the end of the Bao et al. affected years): {fy} "
        "company-years with an AAER, of which {lig} link to a CIK. The most recent years have fewer cases because an "
        "AAER usually comes out years after the fraud, and the database ends in 2014. The SEC index has {n_xbrl} "
        "AAERs issued from 2009 to 2023, of all kinds (not only misstatements).",
        "s_decisoes": "## 5. Decisions for Roberto",
        "decisoes": [
            "**Possible period.** XBRL balance sheets since 2009 (all companies since 2011). With free labels, the affected "
            "years only go to 2014: the overlap is 2009 to 2014. To go beyond 2014, buy the CFRM database (through 2025) or "
            "classify the SEC AAERs by hand.",
            "**Expected size.** {fy} company-years with an AAER in the XBRL fiscal years, {lig} linked to a CIK, against "
            "the 10-Ks of each year (the number comes from the SEC files). With multi-year frauds counted once, "
            "the number of cases is smaller still: power will be low, as in study 1.",
            "**What cannot be done without paid data.** Misstated years after 2014 (CFRM); the gvkey and Compustat data "
            "(WRDS); Audit Analytics restatements. The era-py gvkey–CIK link does not state its source.",
            "**Multi-year frauds.** Walker (2021) showed that, in Bao et al. (2020), frauds spanning the training and test "
            "periods inflate the metric; the erratum (JAR, 2022) acknowledged a code error that left about 10% of these "
            "cases unrecoded, Walker (2022) criticized the erratum, and Gow (2022) discussed whether the paper should be "
            "retracted. Proposal: the outcome per case (one fraud, counted once), like the study 1 detection, with the "
            "bootstrap by company, as in study 2; the signals are fixed rules, with no training.",
        ],
        "s_calendario": "### Draft timeline through May 2027",
        "cab_cal": "| By | Step |",
        "calendario": [
            (
                "2026-12-15",
                "Roberto sets the User-Agent; Phase 0 ends with the SEC files (structure, 10-Ks by year, tag coverage).",
            ),
            ("2027-01-15", "Decision on labels (through 2014, buy the CFRM, or classify by hand) and on the period."),
            ("2027-02-28", "Draft of the US pre-registration: sample, outcome per case, metrics and naive rule."),
            ("2027-03-31", "Roberto's review, registration and timestamp; code frozen."),
            ("2027-05-31", "Single computation and report, separate from Brazil's study 2."),
        ],
        "fontes": "Sources for the conditions and the critique: sites.google.com/usc.edu/aaerdataset (Buy the Data); "
        "econjwatch.org (Walker, 2021 and 2022); iangow.github.io/notes/published/bklyz.html (Gow, 2022).",
    },
}


def render(d: dict[str, Any], lang: str) -> str:
    t, i = T[lang], (lambda v: inteiro(int(v), lang))
    r, b, li = d["rotulos"], d["rotulos"]["bao_et_al"], d["rotulos"]["ligacao_gvkey_cik"]
    fy, lig = b["empresa_anos_xbrl"], b["empresa_anos_xbrl_ligadas_ao_cik"]
    pend = t["pendente_curto"]
    linhas = [t["titulo"], "", t["aviso"], "", t["s_acesso"], "",
              t["acesso"].format(var=d["acesso_sec"]["variavel"], baixados=i(d["acesso_sec"]["fsds_baixados"]),
                                 previstos=i(d["acesso_sec"]["fsds_previstos"])),
              "", t["s_fsds"], "", t["fsds"].format(t0=d["limite"]["trimestres_fsds"][0], t1=d["limite"]["trimestres_fsds"][1]),
              "", t["versoes"], ""]  # fmt: skip
    if d["fsds"] is None:
        linhas += [t["pendente"], ""]
    linhas += [t["s_mapa"], "", t["mapa_txt"], "", t["cab_mapa"], "| --- | --- |"]
    linhas += [f"| `{c}` | " + ", ".join(f"`{x}`" for x in ts) + " |" for c, ts in d["mapa"].items()]
    idx = r["indice_sec"]
    linhas += ["", t["s_rotulos"], "",
               t["era"].format(v=r["pacote"]["versao"], lic=r["pacote"]["licenca"], sha=d["era_py"]["sha256"]), "",
               t["indice"].format(atual=data(r["pacote"]["indice_atualizado"], lang), n=i(idx["aaers"]),
                                  distintos=i(idx["numeros_distintos"]), a0=idx["primeiro_ano"], a1=idx["ultimo_ano"]),
               t["bao"].format(linhas=i(b["linhas"]), aaers=i(b["aaers"]), gvkeys=i(b["gvkeys"]),
                               a0=b["primeiro_ano_afetado"], a1=b["ultimo_ano_afetado"], fy=i(b["empresa_anos"]),
                               multi=i(b["aaers_de_mais_de_um_ano"])),
               t["ligacao"].format(linhas=i(li["linhas"]), gvkeys=i(li["gvkeys"]), ciks=i(li["ciks"])),
               t["cfrm"], t["sec_lista"], "", t["ligar"], "", t["s_contagens"], "", t["cab_cont"],
               "| --- | ---: | ---: | ---: | ---: |"]  # fmt: skip
    for ano, n in b["empresa_anos_xbrl_por_ano"].items():
        linhas.append(f"| {ano} | {i(n)} | {i(b['empresa_anos_xbrl_ligadas_por_ano'][ano])} | {pend} | {pend} |")
    n_xbrl = sum(v for a, v in idx["por_ano"].items() if int(a) >= rotulos.PRIMEIRO_ANO_XBRL)
    linhas += ["", t["cont_txt"].format(fy=i(fy), lig=i(lig), n_xbrl=i(n_xbrl)), "", t["s_decisoes"], ""]
    linhas += [f"{k}. " + x.format(fy=i(fy), lig=i(lig)) for k, x in enumerate(t["decisoes"], start=1)]
    linhas += ["", t["s_calendario"], "", t["cab_cal"], "| --- | --- |"]
    linhas += [f"| {data(dia, lang)} | {etapa} |" for dia, etapa in t["calendario"]]
    linhas += ["", t["fontes"]]
    return "\n".join(linhas) + "\n"


def main(argv: list[str]) -> None:
    if "--baixar" in argv:
        sec.grava_manifesto([rotulos.baixar()])
        try:
            sec.grava_manifesto(fsds.baixar(sec.Cliente()))
        except sec.SemUserAgent as e:
            print(f"arquivos da SEC não baixados: {e}")
    d = calcula()
    SAIDA.write_text(json.dumps(d, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    for lang, caminho in DOCS.items():
        caminho.write_text(render(d, lang), encoding="utf-8")
    print(
        f"gravado em {SAIDA}; FSDS baixados: {d['acesso_sec']['fsds_baixados']} de {d['acesso_sec']['fsds_previstos']}"
    )


if __name__ == "__main__":
    main(sys.argv[1:])
