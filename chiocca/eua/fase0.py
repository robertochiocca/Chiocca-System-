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
from chiocca.eua import fsds, itens, rotulos, sec
from chiocca.formato import data, decimal, inteiro, pct

SAIDA = RAIZ / "docs" / "eua_fase0_numeros.json"
DOCS = {"pt": RAIZ / "docs" / "eua-fase-0.md", "en": RAIZ / "docs" / "en" / "us-phase-0.md"}


def _colunas_por_trimestre(estruturas: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    """Os conjuntos de colunas de sub.txt e num.txt ao longo dos trimestres, com o primeiro e o último de cada um."""
    out: list[dict[str, Any]] = []
    for t, e in estruturas.items():
        cols = {n: e[n]["colunas"] for n in ("sub.txt", "num.txt")}
        if out and out[-1]["colunas"] == cols:
            out[-1]["ate"] = t
        else:
            out.append({"de": t, "ate": t, "colunas": cols})
    return out


ULTIMO_EXERCICIO = 2024  # decisão de Roberto de 24/11/2026: exercícios dos EUA até 2024


def _no_periodo(por_ano: dict[str, Any]) -> dict[str, Any]:
    """Só os exercícios de 2009 a 2024 (um exercício declarado fora disso, numa entrega até 2025, fica de fora)."""
    return {a: v for a, v in por_ano.items() if rotulos.PRIMEIRO_ANO_XBRL <= int(a) <= ULTIMO_EXERCICIO}


def calcula_fsds(baixados: list[Any]) -> dict[str, Any]:
    """Com os arquivos da SEC: estrutura, 10-K e 10-K/A por exercício, versões públicas, cobertura das tags, AAERs com
    10-K e os 8-K com o item 4.02."""
    import pandas as pd

    estruturas = {z.stem: fsds.estrutura(z) for z in baixados}
    subs = pd.concat([fsds.submissoes(z) for z in baixados], ignore_index=True)
    tabela = pd.concat(
        [
            fsds.cobertura_tags(
                z,
                subs[subs.trimestre == z.stem],
                tags=[*fsds.TAGS, *fsds.TAGS_EXTRAS, *(t for t in fsds.TAGS_AMPLIACOES if t not in fsds.TAGS)],
                formularios=("10-K", "10-K/A"),
                receitas_anuais=True,
                tags_anuais=fsds.TAGS_AMPLIACOES,
            )
            for z in baixados
        ],
        ignore_index=True,
    )
    emendas = tabela[tabela.form == "10-K/A"]
    com_numeros = set(emendas.adsh[emendas[fsds.TAGS].any(axis=1)])
    por_exercicio = fsds.resumo(subs)
    a_fy = subs.assign(fy=pd.to_numeric(subs.fy, errors="coerce"))
    for fy, linha in por_exercicio.items():
        linha["entregas_10k_a_com_numeros"] = int(
            ((a_fy.form == "10-K/A") & (a_fy.fy == int(fy)) & a_fy.adsh.isin(com_numeros)).sum()
        )
    originais = subs[subs.form == "10-K"].dropna(subset=["ano"])
    anos_10k = {(int(c), int(a)) for c, a in zip(originais.cik, originais.ano)}
    firmas, ligacoes = rotulos.tabelas()
    primeiro_10k = originais.groupby(originais.cik.astype(int)).filed.min().to_dict()
    ultimo = estruturas[baixados[-1].stem]
    dez_k = originais.merge(tabela[tabela.form == "10-K"][["adsh", "receita"]], on="adsh", how="left")
    dez_k = dez_k.assign(sem_receita=fsds.sem_receita(dez_k.receita), spac=dez_k.sic == "6770",
                         financeira=dez_k.sic.str.match(r"^6\d{3}$") & (dez_k.sic != "6770"))  # fmt: skip
    historico: dict[int, list[tuple[str, bool, bool, bool]]] = {}
    for c, f, s_rec, s_6770, s_fin in sorted(
        zip(dez_k.cik.astype(int), dez_k.filed, dez_k.sem_receita, dez_k.spac, dez_k.financeira)
    ):
        historico.setdefault(c, []).append((f, bool(s_rec), bool(s_6770), bool(s_fin)))
    itens_8k = itens.contagens(
        itens.entregas(),
        {int(c): d for c, d in primeiro_10k.items()},
        sic_6770={int(c) for c in subs.cik[subs.sic == "6770"]},
        historico=historico,
    )
    return {
        "trimestres_baixados": len(baixados),
        "trimestres_sem_entregas": [t for t, e in estruturas.items() if e["sub.txt"]["linhas"] == 0],
        "estrutura_do_ultimo": {"trimestre": baixados[-1].stem, "arquivos": ultimo},
        "colunas_por_trimestre": _colunas_por_trimestre(estruturas),
        "linhas_por_trimestre": {t: {n: e[n]["linhas"] for n in ("sub.txt", "num.txt")} for t, e in estruturas.items()},
        "por_exercicio": _no_periodo(por_exercicio),
        "por_entrega": {
            ano: {"10k": int((g.form == "10-K").sum()), "10k_a": int((g.form == "10-K/A").sum())}
            for ano, g in subs.groupby(subs.filed.str[:4])
        },
        "versoes": _no_periodo(fsds.versoes_por_ano(subs, com_numeros)),
        "cobertura": _no_periodo(fsds.cobertura_por_ano(tabela)),
        "companhias_com_10k_por_ano_compustat": _no_periodo(
            {str(int(a)): int(n) for a, n in originais.groupby("ano").cik.nunique().items()}
        ),
        "aaer": rotulos.com_10k(firmas, ligacoes, anos_10k),
        "itens_8k": itens_8k,
        "exclusoes_10k": _no_periodo(_exclusoes_10k(dez_k)),
        "mapa_ampliado": _mapa_ampliado(dez_k, tabela, primeiro_10k, subs),
    }


# As regras do rascunho do pré-registro (seção 3.1) para a cobertura do mapa ampliado: cada conta e as tags (ou a
# derivação) que a cobrem. Só presença do valor na data de referência, como na seção 2.4; a receita é o valor anual.
REGRAS_RASCUNHO: dict[str, tuple[tuple[str, ...], ...]] = {
    "ativo_total": (("Assets",),),
    "ativo_circulante": (("AssetsCurrent",),),
    "contas_a_receber": (("AccountsReceivableNetCurrent",), ("ReceivablesNetCurrent",)),
    "imobilizado": (("PropertyPlantAndEquipmentNet",),),
    "passivo_circulante": (("LiabilitiesCurrent",),),
    "fornecedores": (("AccountsPayableCurrent",), ("AccountsPayableAndAccruedLiabilitiesCurrent",)),
    "emprestimos_cp": (("DebtCurrent",), ("LongTermDebtCurrent",), ("ShortTermBorrowings",)),
    "emprestimos_lp": (("LongTermDebtNoncurrent",), ("LongTermDebtAndCapitalLeaseObligations",)),
    "patrimonio_liquido": (
        ("StockholdersEquity",),
        ("StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest",),
    ),
    "custo_vendas": (("CostOfRevenue",), ("CostOfGoodsAndServicesSold",), ("CostOfGoodsSold",)),
    "resultado_bruto": (("GrossProfit",), ("receita", "custo_vendas")),
    "despesas_vendas_gerais_adm": (("SellingGeneralAndAdministrativeExpense",),),
    "despesas_financeiras": (("InterestExpense",),),
    "lucro_operacoes_continuadas": (("IncomeLossFromContinuingOperations",), ("NetIncomeLoss",), ("ProfitLoss",)),
    "lucro_liquido": (("NetIncomeLoss",), ("ProfitLoss",)),
    "caixa_operacional": (("NetCashProvidedByUsedInOperatingActivities",),),
    "depreciacao": (("DepreciationDepletionAndAmortization",), ("DepreciationAndAmortization",), ("Depreciation",)),
    "passivo_total": (("Liabilities",), ("LiabilitiesAndStockholdersEquity", "patrimonio_liquido")),
}
ANOS_AMOSTRA = [str(a) for a in range(2011, ULTIMO_EXERCICIO + 1)]  # a amostra do rascunho: exercícios de 2011 a 2024


def _cobre(
    linha: Any, conta: str, receita_ok: bool, regras: dict[str, tuple[tuple[str, ...], ...]] | None = None
) -> bool:
    """Se a entrega cobre a conta pelas regras do rascunho (alguma alternativa com todas as partes presentes)."""
    regras = REGRAS_RASCUNHO if regras is None else regras

    def parte(x: str) -> bool:
        if x == "receita":
            return receita_ok
        if x in regras:
            return _cobre(linha, x, receita_ok, regras)
        return bool(linha[x])

    if conta == "receita_liquida":
        return receita_ok
    return any(all(parte(x) for x in alternativa) for alternativa in regras[conta])


def _juros_e_caixa(amostra: Any) -> tuple[dict[str, Any], dict[str, tuple[tuple[str, ...], ...]]]:
    """Terceira rodada (24/11/2026), só contagens, nos 10-K da amostra: o uso de cada tag (a base e as candidatas de
    `fsds.AMPLIACOES`) por ano, pelo valor anual na data de referência; a regra gulosa da receita aplicada a cada conta;
    a cobertura antes e depois, por ano, e quantas entregas só ficam cobertas por uma tag de conceito mais largo. Devolve
    também as regras do rascunho com as tags que entraram."""
    out: dict[str, Any] = {"conceito_largo": list(fsds.CONCEITO_LARGO), "ganho_minimo": fsds.GANHO_MINIMO, "contas": {}}
    regras = dict(REGRAS_RASCUNHO)
    for conta, a in fsds.AMPLIACOES.items():
        tags = (*a["base"], *a["candidatas"])
        uso = {t: {str(fy): int(sum(t in d for d in g.anuais_extras)) for fy, g in amostra.groupby("fy")} for t in tags}
        amp = fsds.ampliar_receita(amostra.anuais_extras, base=a["base"], candidatas=a["candidatas"])
        estreitas = [t for t in amp["ordem"] if t not in fsds.CONCEITO_LARGO]
        cobertura = {
            str(fy): {"10k": len(g), "antes": int(sum(bool(set(d) & set(a["base"])) for d in g.anuais_extras)),
                      "depois": int(sum(bool(set(d) & set(amp["ordem"])) for d in g.anuais_extras)),
                      "so_conceito_largo": int(sum(bool(set(d) & set(amp["ordem"])) and not set(d) & set(estreitas)
                                                   for d in g.anuais_extras))}
            for fy, g in amostra.groupby("fy")
        }  # fmt: skip
        out["contas"][conta] = {"base": list(a["base"]), "candidatas": list(a["candidatas"]), "uso_por_ano": uso,
                                "ampliacao": amp, "cobertura_por_ano": cobertura}  # fmt: skip
        regras[conta] = tuple((t,) for t in amp["ordem"])
    return out, regras


def _mapa_ampliado(dez_k: Any, tabela: Any, primeiro_10k: dict[Any, str], subs: Any) -> dict[str, Any]:
    """Item 4 do pedido de 24/11/2026 (segunda rodada), só contagens: a ampliação do mapa da receita pela regra gulosa
    de `fsds.ampliar_receita`, a contagem de descoberta, a cobertura de cada conta pelas regras do rascunho e as
    exclusões com o mapa ampliado, nos 10-K da amostra (não financeiras, sem as SPACs, exercícios de 2011 a 2024)."""
    from collections import Counter

    originais = tabela[tabela.form == "10-K"].set_index("adsh")
    k = dez_k.set_index("adsh")
    k = k.join(originais.drop(columns=["form", "fy", "receita"]), how="left")
    for c in dict.fromkeys([*fsds.TAGS, *fsds.TAGS_EXTRAS, *fsds.TAGS_AMPLIACOES]):
        k[c] = k[c].astype("boolean").fillna(False).astype(bool)
    k["receitas_anuais"] = [d if isinstance(d, dict) else {} for d in k.receitas_anuais]
    k["anuais_extras"] = [d if isinstance(d, dict) else {} for d in k.anuais_extras]
    amostra = k[k.fy.isin(ANOS_AMOSTRA) & ~k.financeira & ~k.spac]
    amp = fsds.ampliar_receita(amostra.receitas_anuais)
    base = set(fsds.MAPA["receita_liquida"])
    sem_base = [d for d in amostra.receitas_anuais if not (set(d) & base)]
    descoberta = Counter(t for d in sem_base for t in d).most_common(15)
    k["receita_ampliada"] = [fsds.receita_ampliada(d, amp["ordem"]) for d in k.receitas_anuais]
    k["sem_receita_ampliada"] = fsds.sem_receita(k.receita_ampliada)
    amostra = k[k.fy.isin(ANOS_AMOSTRA) & ~k.financeira & ~k.spac]
    contas = ["receita_liquida", *REGRAS_RASCUNHO]
    juros_caixa, regras_novas = _juros_e_caixa(amostra)
    cobertura: dict[str, Any] = {}
    cobertura_nova: dict[str, Any] = {}
    for fy, g in amostra.groupby("fy"):
        ok = ~g.sem_receita_ampliada
        linhas = list(zip((linha for _, linha in g.iterrows()), ok))
        cobertura[str(fy)] = {"10k": len(g)} | {
            c: float(sum(_cobre(linha, c, bool(r)) for linha, r in linhas) / len(g)) for c in contas
        }
        cobertura_nova[str(fy)] = {"10k": len(g)} | {
            c: float(sum(_cobre(linha, c, bool(r), regras_novas) for linha, r in linhas) / len(g)) for c in contas
        }
    juros_caixa["cobertura_por_ano_regras_novas"] = cobertura_nova
    sem_receita = {
        str(fy): {"10k": len(g), "sem_receita_fase0": int(g.sem_receita.sum()),
                  "sem_receita_ampliada": int(g.sem_receita_ampliada.sum())}
        for fy, g in amostra.groupby("fy")
    }  # fmt: skip
    historico: dict[int, list[tuple[str, bool, bool, bool]]] = {}
    for c, f, s_rec, s_6770, s_fin in sorted(
        zip(k.cik.astype(int), k.filed, k.sem_receita_ampliada, k.spac, k.financeira)
    ):
        historico.setdefault(c, []).append((f, bool(s_rec), bool(s_6770), bool(s_fin)))
    it = itens.contagens(
        itens.entregas(),
        {int(c): d for c, d in primeiro_10k.items()},
        sic_6770={int(c) for c in subs.cik[subs.sic == "6770"]},
        historico=historico,
    )
    chaves = ("companhias_com_10k_fsds_antes", "antes_financeiras", "antes_sic_6770", "antes_sem_receita_demais",
              "antes_restantes")  # fmt: skip
    return {
        "candidatas": list(fsds.RECEITA_CANDIDATAS),
        "ganho_minimo": fsds.GANHO_MINIMO,
        "ampliacao": amp,
        "descoberta": [[t, n] for t, n in descoberta],
        "entregas_sem_as_tres_tags": len(sem_base),
        "cobertura_por_ano": cobertura,
        "sem_receita_por_ano": sem_receita,
        "exclusoes_8k": {a: {c: x[c] for c in chaves} for a, x in it.items()},
        "juros_e_caixa": juros_caixa,
    }


def _exclusoes_10k(dez_k: Any) -> dict[str, Any]:
    """Por exercício (`fy`), só contagens, com as exclusões na ordem do rascunho do pré-registro: os 10-K originais, os
    das financeiras pela SIC (6000 a 6999, sem as SPACs), os das SPACs (SIC 6770) e quantos deles a regra das sem
    receita já tira, os demais sem receita (receita ausente ou zero, a regra do estudo 1) e os que ficam."""
    out: dict[str, Any] = {}
    for fy, g in dez_k[dez_k.fy.str.isdigit()].groupby("fy"):
        out[str(fy)] = {
            "10k": len(g),
            "sem_receita": int(g.sem_receita.sum()),
            "sem_receita_financeiras": int((g.sem_receita & g.financeira).sum()),
            "sic_6770": int(g.spac.sum()),
            "sic_6770_sem_receita": int((g.spac & g.sem_receita).sum()),
            "financeiras": int(g.financeira.sum()),
            "sem_receita_demais": int((g.sem_receita & ~g.financeira & ~g.spac).sum()),
            "restantes": int((~g.sem_receita & ~g.financeira & ~g.spac).sum()),
        }
    return out


def calcula() -> dict[str, Any]:
    manifesto = {x["arquivo"]: x for x in sec.le_manifesto()}
    roda = rotulos.RODA.relative_to(sec.DADOS).as_posix()
    if roda not in manifesto or sec.sha256(rotulos.RODA) != manifesto[roda]["sha256"]:
        raise SystemExit("a roda do era-py não confere com o manifesto: rode com --baixar")
    baixados = sorted(fsds.PASTA.glob("*.zip")) if fsds.PASTA.exists() else []
    for z in baixados + ([itens.ARQUIVO] if itens.ARQUIVO.exists() else []):
        nome = z.relative_to(sec.DADOS).as_posix()
        if nome not in manifesto or int(manifesto[nome]["bytes"]) != z.stat().st_size:
            raise SystemExit(f"{nome} não confere com o manifesto")
    edgar = itens.ARQUIVO.relative_to(sec.DADOS).as_posix()
    out: dict[str, Any] = {
        "o_que_e": "Fase 0 dos EUA (pedido de 23/11/2026): só inventário e contagens, sem nenhum sinal",
        "limite": {
            "ultimo_exercicio": ULTIMO_EXERCICIO,
            "trimestres_fsds": [fsds.TRIMESTRES[0], fsds.TRIMESTRES[-1]],
            "ultima_data_8k": itens.ULTIMA_DATA,
            "ultimo_ano_indice_aaer": rotulos.ULTIMO_ANO,
        },
        "acesso_sec": {
            "variavel": sec.VARIAVEL,
            "fsds_baixados": len(baixados),
            "fsds_previstos": len(fsds.TRIMESTRES),
            "fsds_bytes": sum(z.stat().st_size for z in baixados),
            "edgar_submissions": (
                {k: manifesto[edgar][k] for k in ("bytes", "sha256", "baixado_em_utc")} if edgar in manifesto else None
            ),
        },
        "era_py": {"arquivo": roda, "sha256": manifesto[roda]["sha256"], "bytes": int(manifesto[roda]["bytes"])},
        "rotulos": rotulos.contagens(),
        "mapa": {c: list(ts) for c, ts in fsds.MAPA.items()},
        "fsds": calcula_fsds(baixados) if baixados and itens.ARQUIVO.exists() else None,
    }
    return out


ANOS = [str(a) for a in range(rotulos.PRIMEIRO_ANO_XBRL, ULTIMO_EXERCICIO + 1)]

T: dict[str, dict[str, Any]] = {
    "pt": {
        "titulo": "# Fase 0 dos EUA: reconhecimento dos dados",
        "aviso": "> **Reconhecimento, sem nenhum sinal calculado.** Objetivo: saber se dá para fazer, nos EUA, um estudo "
        "pré-registrado com os dados como eram na época, testando os sinais do v1 e do v2 do Chiocca e a regra boba contra um "
        "rótulo público de demonstrações erradas. Só inventário e contagens; nos EUA, os exercícios até 2024 (decisão de "
        "Roberto de 24/11/2026), e nada dos exercícios brasileiros de 2024 em diante; nenhum nome de pessoa "
        "física nem de companhia; nenhum valor de sinal, acerto, alerta ou ranking. A frente dos EUA fica fora do README e do "
        "produto até decisão de Roberto.",
        "s_acesso": "## 1. Acesso à SEC",
        "acesso": "A SEC pede um User-Agent com nome e contato e no máximo 10 pedidos por segundo; sem o contato, recusa o "
        "pedido (HTTP 403). Os scripts leem o User-Agent da variável de ambiente `{var}`, que nenhum arquivo versionado nem "
        "log guarda, e esperam pelo menos 0,11 segundo entre pedidos. Em 23/11/2026, com a variável definida nas "
        "configurações do ambiente, foram baixados os **{baixados} de {previstos} arquivos trimestrais** dos Financial "
        "Statement Data Sets ({gb} GB) e o histórico de entregas do EDGAR (`submissions.zip`, {gb_edgar} GB, retrato da SEC "
        "baixado em {dia_edgar}). Os arquivos ficam em `data/eua/`, fora do Git, com o tamanho e o SHA-256 de cada um em "
        "`data/eua_manifesto.csv`.",
        "acesso_pendente": "A SEC pede um User-Agent com nome e contato e no máximo 10 pedidos por segundo; sem o contato, "
        "recusa o pedido (HTTP 403). Os scripts leem o User-Agent da variável de ambiente `{var}`, que nenhum arquivo "
        "versionado nem log guarda. **{baixados} de {previstos} arquivos trimestrais da SEC foram baixados**: com a "
        "variável definida, rode `python -m chiocca.eua.fase0 --baixar`.",
        "s_fsds": "## 2. Balanços: os Financial Statement Data Sets da SEC",
        "fsds": "Os números das demonstrações em XBRL, num zip por trimestre de entrega desde 2009 (aqui, de {t0} a {t1}: "
        "os exercícios até 2024, com os 10-K entregues com atraso e as emendas de 2025). Os dois arquivos usados são "
        "`sub.txt` (uma linha por entrega: CIK, formulário, data de referência, exercício fiscal, datas de entrega e se a "
        "entrega foi emendada depois) e `num.txt` (uma linha por número: tag, taxonomia, data, trimestres cobertos, unidade "
        "e valor).",
        "versoes": "- **10-K e 10-K/A:** a entrega original e cada emenda são entregas separadas, cada uma com a sua data; "
        "`prevrpt` marca a entrega que foi emendada depois.\n- **A versão pública numa data de corte:** por companhia e "
        "exercício, a última entrega entregue até a data, entre o 10-K original e os 10-K/A com números das contas do mapa, "
        'como o "como era" do Chiocca no Brasil. Uma emenda sem esses números (só a parte III do 10-K, por exemplo) não muda '
        "a versão. O comparativo do exercício seguinte traz os números de t-1 como apresentados depois.",
        "pendente": "**Pendente (sem os arquivos da SEC):** a estrutura conferida nos arquivos, a cobertura de 10-K por ano, "
        "as emendas, os prazos de entrega e a cobertura de cada tag por ano. O código já está pronto e testado com um "
        "arquivo sintético (`chiocca/eua/fsds.py`).",
        "s_estrutura": "### 2.1 Estrutura dos arquivos",
        "estrutura": "Cada zip traz `sub.txt`, `num.txt`, `pre.txt` e `tag.txt` (texto separado por tabulação) e um "
        "`readme.htm`. As colunas usadas foram conferidas em todos os {n} trimestres antes de qualquer conta. "
        "{vazios} não tem nenhuma entrega (só os cabeçalhos): os primeiros 10-K em XBRL entram a partir de 2009q2. O "
        "último trimestre ({ultimo}):",
        "cab_estrutura": "| Arquivo | Colunas | Linhas |",
        "colunas_mudam": "As colunas mudam ao longo dos trimestres: {mudancas}. O código usa `coreg` (co-registrante) quando "
        "existe e `segments` quando existe, e em ambos os casos só conta o número da própria companhia, sem segmento.",
        "colunas_iguais": "As colunas de `sub.txt` ({n_sub}) e de `num.txt` ({n_num}) são as mesmas nos {n} trimestres. "
        "`num.txt` traz `coreg` (co-registrante) e `segments` (segmento): o código só conta o número da própria companhia, "
        "com as duas vazias.",
        "trecho_mudanca": "de {de} a {ate}, `num.txt` com {n} colunas ({extra})",
        "s_10k": "### 2.2 10-K e 10-K/A por exercício e datas de entrega",
        "txt_10k": "Por exercício fiscal declarado pela companhia (`fy`). O prazo é a diferença em dias entre a data de "
        "referência e a entrega do 10-K original. As emendas com números são os 10-K/A com alguma tag do mapa na data de "
        "referência; as demais (a maioria) só trazem a parte III ou a capa. Os exercícios declarados de 2025 em diante "
        "ficam de fora.",
        "cab_10k": "| Exercício | Companhias com 10-K | 10-K | 10-K/A | 10-K/A com números | 10-K emendados depois | Prazo mediano (dias) | Prazo, 10% a 90% (dias) | Até 90 dias |",
        "s_versao": "### 2.3 A versão pública numa data de corte",
        "txt_versao": "Por exercício, em 31 de dezembro do ano seguinte (t+1) e do outro (t+2), só cortes até 31/12/2025: quantas "
        "companhias têm uma versão pública e em quantas ela já é uma emenda com números, e não o 10-K original.",
        "cab_versao": "| Exercício | Companhias em t+1 | Emenda em t+1 | Companhias em t+2 | Emenda em t+2 |",
        "s_mapa": "### 2.4 O mapa das contas para as tags us-gaap e a cobertura por ano",
        "mapa_txt": "As contas que os sinais do v1 e do v2 usam, com as tags candidatas na ordem de preferência. Benford usa "
        "todos os números e não precisa de mapa; a DVA não existe nos EUA (a depreciação vem da DFC); nos EUA, despesas "
        "de vendas e administrativas costumam vir juntas (SG&A), e muitas companhias não apresentam o resultado bruto. As "
        "financeiras (peso de ganhos não recorrentes) ficam sem mapa nesta fase.",
        "cab_mapa": "| Conta | Tags us-gaap candidatas |",
        "cobertura_txt": "A cobertura é a fração dos 10-K originais de cada exercício com valor em dólar na data de "
        "referência, da própria companhia (sem co-registrante nem segmento), na taxonomia us-gaap. Por conta (alguma das "
        "tags candidatas):",
        "cobertura_tag_txt": "Por tag:",
        "cab_conta": "Conta",
        "cab_tag": "Tag",
        "s_rotulos": "## 3. Rótulos",
        "s_aaer": "### 3.1 Os AAERs",
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
        "sec_lista": "- **A lista pública de AAERs no site da SEC:** não foi lida diretamente; o índice do era-py é uma "
        "cópia dela, com a data da atualização.",
        "ligar": "**Como ligar cada AAER ao CIK sem a Compustat.** Até 2014, pelas empresa-anos de Bao et al. e pela "
        "ligação gvkey–CIK do era-py. Depois de 2014, não há base livre com os anos errados: o caminho é ler cada AAER "
        "no site da SEC (a companhia é parte do processo) e casar o nome com o arquivo de nomes e CIKs da SEC, guardando "
        "só a companhia e o CIK.",
        "s_402": "### 3.2 Um rótulo novo: os 8-K com o item 4.02",
        "txt_402": "Desde agosto de 2004, a companhia entrega um 8-K com o item 4.02 (*Non-Reliance on Previously Issued "
        "Financial Statements or a Related Audit Report or Completed Interim Review*) quando ela, ou o auditor, conclui que "
        "demonstrações já publicadas não devem mais ser usadas por causa de um erro; a republicação vem depois. É o mesmo "
        "conceito da republicação do estudo 2 no Brasil: a informação publicada estava errada, por erro ou de propósito, "
        "sem dizer qual. A fonte é o campo de itens (`items`) do histórico de entregas de cada companhia no EDGAR "
        "(`submissions.zip`), que lista os itens de cada 8-K; só a data, o formulário, os itens e o CIK são lidos, em "
        "memória, sem o texto do 8-K nem o nome da companhia (`chiocca/eua/itens.py`). Uma entrega de várias companhias "
        "conta uma vez nas contagens de entregas.",
        "s_contagens": "## 4. Contagens",
        "s_cont_aaer": "### 4.1 AAERs de Bao et al. com 10-K nos dados da SEC",
        "cab_cont": "| Exercício | Empresa-anos com AAER (Bao et al.) | Ligadas a um CIK | Com 10-K nos dados da SEC | Empresa-anos com 10-K (todas as companhias) |",
        "pendente_curto": "pendente",
        "total": "**Total**",
        "cont_txt": "O exercício é o da convenção da Compustat, usada por Bao et al.: o ano da data de referência, ou o "
        "anterior quando o exercício termina de janeiro a maio. Uma empresa-ano de Bao et al. tem 10-K nos dados da SEC "
        "quando algum CIK ligado ao gvkey naquele ano entregou um 10-K original com XBRL para aquele exercício. **De 2009 a "
        "2014, {fy} empresa-anos com AAER, {lig} ligadas a um CIK e {com} com 10-K nos dados da SEC**, contra cerca de "
        "{denom} companhias com 10-K por ano de 2011 a 2014, quando o XBRL já valia para todas. Contando cada caso (AAER) uma vez: **{casos} casos**, de {cias} "
        "companhias, com pelo menos um exercício afetado com 10-K de 2009 a 2014 (pelo primeiro desses exercícios: "
        "{por_ano}). Os anos mais recentes têm menos casos porque um AAER costuma sair anos depois dos fatos, e a base "
        "termina em 2014. O índice da SEC tem {n_xbrl} AAERs emitidos de 2009 a 2023, de todos os tipos (não só balanço "
        "errado).",
        "s_cont_402": "### 4.2 8-K com o item 4.02 e 10-K/A por ano de entrega",
        "cab_402": "| Ano de entrega | 8-K 4.02 | 8-K/A 4.02 | Companhias com 8-K 4.02 | Delas com SIC 6770 (SPACs) | Primeira vez desde 2009 | Com 10-K nos dados da SEC | Com 10-K nos dados da SEC antes do 8-K | 10-K (EDGAR) | 10-K/A (EDGAR) | 10-K/A com XBRL (dados da SEC) |",
        "txt_402_cont": 'Uma companhia conta uma vez por ano; "primeira vez desde 2009" conta cada companhia uma vez no '
        'período. "Com 10-K nos dados da SEC" quer dizer que o CIK tem um 10-K original nos Financial Statement Data Sets '
        'de 2009q1 a 2025q4; "antes do 8-K", que o primeiro desses 10-K foi entregue até a data do 8-K (há demonstrações em '
        "XBRL da época para comparar). **De 2009 a 30/04/2026: {n8k} 8-K com o item 4.02, de {cias} companhias-ano; {novas} "
        "companhias distintas; {com} companhias-ano com 10-K nos dados da SEC, {antes} delas com o 10-K antes do 8-K.** Os "
        "10-K/A são de todos os tipos (a maioria só completa a parte III); a última coluna conta os que estão nos dados da "
        "SEC, por ano de entrega. O pico de 2021 coincide com a declaração da equipe da SEC de 12/04/2021 sobre a "
        "contabilização de warrants das SPACs (companhias de aquisição, sem operação), seguida de muitas republicações: "
        "{spac_2021} das {cias_2021} companhias com 8-K 4.02 em 2021 têm o código SIC 6770 (blank checks) nos dados da SEC; "
        "de 2009 a 30/04/2026, {spac} companhias-ano. O ano de 2026 vai só até 30/04/2026, o fim da janela do "
        "exercício de 2024.",
        "s_decisoes": "## 5. Decisões",
        "s_decididas": "### 5.1 Decisões de Roberto (24/11/2026)",
        "decididas": [
            "**Desfecho principal: o 8-K com o item 4.02**, o mesmo conceito da republicação do estudo 2. Os AAERs de "
            "2009 a 2014 ficam só como descrição, sem teste.",
            "**Desfecho por caso:** cada episódio contado uma vez (uma companhia, um episódio de 8-K 4.02, com os 8-K e "
            "8-K/A do mesmo episódio juntos), com bootstrap por companhia, como no estudo 2. É a resposta à crítica de "
            "Walker (2021 e 2022) e de Gow (2022) a Bao et al. (2020), em que fraudes de vários anos que atravessam o "
            "treino e o teste inflam a medida; aqui os sinais são regras fixas, sem treino, e cada caso conta uma vez.",
            "**Exclusões por regra explícita:** as SPACs (código SIC 6770, blank checks, nos dados da SEC), além das sem "
            "receita (receita ausente ou zero, a regra do estudo 1). As contagens abaixo dizem quantas SPACs a regra das "
            "sem receita já tiraria; nenhum valor de sinal, acerto ou alerta.",
            "**Financeiras fora:** as companhias com SIC de 6000 a 6999, sem as SPACs, ficam fora do estudo, porque o mapa "
            "não tem as contas delas.",
            "**As tags da receita** são escolhidas só pelas contagens de cobertura, e a lista final entra no texto que for "
            "registrado.",
            "**Período:** os exercícios de 2011 a 2024 (data de referência até 31/12/2024), com os dados da SEC e os 8-K "
            "baixados de novo no dia do cálculo, porque a janela de 12 meses de todos esses exercícios já terminou (a "
            "última, em 30/04/2026). As contagens desta Fase 0 vão até lá: os 10-K entregues até 31/12/2025 e os 8-K até "
            "30/04/2026.",
            "**A semente** do bootstrap é 20270430.",
            "**Os arquivos da SEC** ficam fora do Git, com o SHA-256 no manifesto e o download por script.",
            "**Calendário com meta e reserva** (seção 5.4). Nenhum sinal americano é calculado antes do registro.",
        ],
        "txt_excl_10k": "10-K originais por exercício declarado (`fy`). A receita é o valor anual (quatro trimestres) da "
        "primeira tag de `receita_liquida` do mapa que a entrega traz. As financeiras pela SIC (6000 a 6999, sem as SPACs) "
        "aparecem à parte porque o mapa desta fase não tem a receita delas; no Brasil, a regra das sem receita vale só "
        "para as não financeiras. **A contagem das sem receita é um teto:** inclui as companhias cuja receita está em "
        "tags fora do mapa (a cobertura da conta `receita_liquida` fica entre {cob_min} e {cob_max} dos 10-K, seção 2.4); o mapa da "
        "receita é ampliado no pré-registro, antes de qualquer sinal.",
        "cab_excl_10k": "| Exercício | 10-K | Financeiras (SIC 6000 a 6999, sem as SPACs) | SPACs (SIC 6770) | SPACs já sem receita | Demais sem receita | Ficam |",
        "txt_excl_8k": "Companhias-ano com 8-K 4.02 e 10-K nos dados da SEC antes do 8-K (seção 4.2), pelo último 10-K "
        "entregue até o primeiro 8-K 4.02 do ano posterior ao primeiro 10-K da companhia (a receita e o SIC são os desse 10-K):",
        "cab_excl_8k": "| Ano de entrega | Com 10-K antes do 8-K | Financeiras | SPACs (SIC 6770) | SPACs já sem receita | Demais sem receita | Ficam |",
        "txt_excl_resumo": "**De 2009 a 30/04/2026, {total} companhias-ano com 8-K 4.02 e 10-K antes: {fin} de financeiras, "
        "{spac} de SPACs (das quais a regra das sem receita já tiraria {spac_sem}) e {sem} das demais sem receita; ficam "
        "{ficam}.** Nos 10-K dos exercícios de 2009 a 2024, a regra das sem receita tiraria {sem_10k} das {spac_10k} "
        "entregas de SPACs.",
        "s_opcoes": "### 5.2 As opções de rótulo comparadas na Fase 0",
        "cab_opcoes": "| Opção | Período | Tamanho | Custo | O que mede |",
        "opcoes": [
            (
                "AAER gratuito (Bao et al., pelo era-py)",
                "exercícios afetados até 2014; com XBRL, de 2009 a 2014",
                "{casos_aaer} casos ({ea_aaer} empresa-anos) com 10-K nos dados da SEC",
                "nenhum (a ligação gvkey–CIK não " "informa a origem)",
                "uma ação da SEC que alega demonstrações erradas: rara, grave, quase sempre com "
                "intenção alegada, e anos depois dos fatos",
            ),
            (
                "8-K com o item 4.02",
                "entregas de 2009 a 30/04/2026 (o item existe desde agosto de 2004)",
                "{cias_402} companhias distintas; {com_402} companhias-ano com 10-K nos dados da SEC",
                "nenhum (EDGAR, " "público)",
                "a própria companhia ou o auditor declara que demonstrações publicadas não valem mais por causa "
                "de um erro relevante, intencional ou não: o conceito da republicação do estudo 2",
            ),
            (
                "Base da CFRM (USC)",
                "AAERs emitidos de 1982 a 2025",
                "4.581 AAERs no total; quantos com XBRL não se " "sabe sem comprar",
                "pago (preço não publicado); termos proíbem passar a base adiante",
                "o mesmo que o AAER, " "com os anos e as contas afetadas",
            ),
            (
                "Classificação manual dos AAERs depois de 2014",
                "AAERs emitidos de 2015 a 2023",
                "{n_manual} AAERs a ler, de todos os tipos; só uma parte é de balanço errado",
                "horas de leitura, com " "regra escrita antes e leitura cega aos sinais",
                "o mesmo que o AAER, com risco de erro de classificação",
            ),
        ],
        "recomendacao": "**Recomendação do Claude (claude.ai), acolhida por Roberto em 24/11/2026:** o 8-K com o item "
        "4.02 como desfecho principal, o mesmo conceito da republicação do estudo 2, e os AAERs de 2009 a 2014 como "
        "descrição à parte, sem teste. O 8-K 4.02 é público, gratuito, cobre o período inteiro com XBRL e tem casos "
        "suficientes para medir alguma coisa; o AAER é raro demais de 2009 a 2014 para um teste e mede outra coisa (a ação "
        "da SEC).",
        "s_pendentes": "### 5.3 Para o rascunho do pré-registro",
        "rascunho": "O [rascunho do pré-registro dos EUA](pre-registro-eua-rascunho.md), de 24/11/2026, trata destes "
        "pontos; não é registro.",
        "decisoes": [
            "**Que exercício o caso afeta.** O campo de itens não diz quais demonstrações deixaram de valer. A regra é "
            "escrita antes de qualquer sinal, com a versão pública na data (seção 2.3).",
            "**O que não dá sem dados pagos.** Os anos errados dos AAERs depois de 2014 (CFRM); o gvkey e os dados da "
            "Compustat (WRDS); as republicações da Audit Analytics, que incluiriam as republicações sem 8-K 4.02 "
            '("little r"). A ligação gvkey–CIK do era-py não informa a origem.',
        ],
        "s_calendario": "### 5.4 Calendário: meta e reserva",
        "cab_cal": "| Etapa | Meta | Reserva |",
        "calendario": [
            ("Decisões de Roberto (seção 5.1).", "2026-11-24", "2026-11-24"),
            (
                "Revisão do rascunho do pré-registro pelo Claude (claude.ai) e por Roberto; nenhum sinal calculado.",
                "2026-12-15",
                "2026-12-15",
            ),
            (
                "Código do estudo escrito e testado só em dados sintéticos; a cobertura do mapa ampliado contada.",
                "2027-01-15",
                "2027-01-31",
            ),
            ("Registro do pré-registro e carimbo; código congelado.", "2027-01-31", "2027-03-31"),
            (
                "Cálculo único, depois do carimbo, com os dados da SEC e os 8-K baixados no dia.",
                "2027-02-28",
                "2027-04-30",
            ),
            ("Relatório em PT e EN, separado do estudo 2 do Brasil.", "2027-03-31", "2027-05-31"),
        ],
        "fontes": "Fontes das condições e da crítica: sites.google.com/usc.edu/aaerdataset (Buy the Data); "
        "econjwatch.org (Walker, 2021 e 2022); iangow.github.io/notes/published/bklyz.html (Gow, 2022); sec.gov (Form 8-K, "
        "item 4.02; Financial Statement Data Sets; EDGAR, submissions.zip).",
    },
    "en": {
        "titulo": "# US Phase 0: data reconnaissance",
        "aviso": "> **Reconnaissance, with no signal computed.** Goal: find out whether a pre-registered US study is feasible, "
        "with the data as they were at the time, testing Chiocca's v1 and v2 signals and the naive rule against a public "
        "label of misstated financial statements. Inventory and counts only; in the US, fiscal years through 2024 (Roberto's "
        "decision of 2026-11-24), and nothing from Brazilian fiscal years 2024 on; no names of individuals "
        "or companies; no signal value, hit, alert or ranking. The US front stays out of the README and the product until "
        "Roberto decides.",
        "s_acesso": "## 1. Access to the SEC",
        "acesso": "The SEC asks for a User-Agent with a name and contact and at most 10 requests per second; without the "
        "contact it refuses the request (HTTP 403). The scripts read the User-Agent from the environment variable `{var}`, "
        "which no versioned file or log keeps, and wait at least 0.11 second between requests. On 2026-11-23, with the "
        "variable set in the environment settings, **all {baixados} of {previstos} quarterly files** of the Financial "
        "Statement Data Sets ({gb} GB) and the EDGAR filing history (`submissions.zip`, {gb_edgar} GB, the SEC snapshot "
        "downloaded on {dia_edgar}) were downloaded. The files stay in `data/eua/`, outside Git, with each file's size and "
        "SHA-256 in `data/eua_manifesto.csv`.",
        "acesso_pendente": "The SEC asks for a User-Agent with a name and contact and at most 10 requests per second; "
        "without the contact it refuses the request (HTTP 403). The scripts read the User-Agent from the environment "
        "variable `{var}`, which no versioned file or log keeps. **{baixados} of {previstos} quarterly SEC files were "
        "downloaded**: with the variable set, run `python -m chiocca.eua.fase0 --baixar`.",
        "s_fsds": "## 2. Balance sheets: the SEC Financial Statement Data Sets",
        "fsds": "The financial statement numbers in XBRL, one zip per filing quarter since 2009 (here, from {t0} to {t1}: "
        "the fiscal years through 2024, with the late 10-Ks and the amendments of 2025). The two files used are `sub.txt` (one row per "
        "filing: CIK, form, report date, fiscal year, filing dates and whether the filing was later amended) and `num.txt` "
        "(one row per number: tag, taxonomy, date, quarters covered, unit and value).",
        "versoes": "- **10-K and 10-K/A:** the original filing and each amendment are separate filings, each with its "
        "date; `prevrpt` flags a filing that was later amended.\n- **The public version at a cutoff date:** per company "
        "and fiscal year, the last filing made by that date, between the original 10-K and the 10-K/As with numbers for "
        'the mapped accounts, like Chiocca\'s "as it was" in Brazil. An amendment without those numbers (only Part III of '
        "the 10-K, for example) does not change the version. The next year's comparative column shows the t-1 numbers as "
        "presented later.",
        "pendente": "**Pending (without the SEC files):** the structure checked on the files, 10-K coverage by year, "
        "amendments, filing lags and the coverage of each tag by year. The code is ready and tested on a synthetic file "
        "(`chiocca/eua/fsds.py`).",
        "s_estrutura": "### 2.1 File structure",
        "estrutura": "Each zip has `sub.txt`, `num.txt`, `pre.txt` and `tag.txt` (tab-separated text) and a "
        "`readme.htm`. The columns used were checked in all {n} quarters before any count. {vazios} has no filing (headers "
        "only): the first XBRL 10-Ks come in from 2009q2. The last quarter ({ultimo}):",
        "cab_estrutura": "| File | Columns | Rows |",
        "colunas_mudam": "The columns change over the quarters: {mudancas}. The code uses `coreg` (co-registrant) where it "
        "exists and `segments` where it exists, and in both cases counts only the company's own number, with no segment.",
        "colunas_iguais": "The columns of `sub.txt` ({n_sub}) and `num.txt` ({n_num}) are the same in all {n} quarters. "
        "`num.txt` has `coreg` (co-registrant) and `segments`: the code counts only the company's own number, with both "
        "empty.",
        "trecho_mudanca": "from {de} to {ate}, `num.txt` with {n} columns ({extra})",
        "s_10k": "### 2.2 10-K and 10-K/A by fiscal year and filing dates",
        "txt_10k": "By the fiscal year the company declares (`fy`). The lag is the number of days between the report date "
        "and the filing of the original 10-K. Amendments with numbers are the 10-K/As with some mapped tag at the report "
        "date; the others (most of them) carry only Part III or the cover page. Declared fiscal years from 2025 on "
        "are left out.",
        "cab_10k": "| Fiscal year | Companies with a 10-K | 10-K | 10-K/A | 10-K/A with numbers | 10-Ks later amended | Median lag (days) | Lag, 10% to 90% (days) | Within 90 days |",
        "s_versao": "### 2.3 The public version at a cutoff date",
        "txt_versao": "By fiscal year, on December 31 of the next year (t+1) and of the one after (t+2), only cutoffs "
        "through 2025-12-31: how many companies have a public version and in how many it is already an amendment with "
        "numbers, not the original 10-K.",
        "cab_versao": "| Fiscal year | Companies at t+1 | Amendment at t+1 | Companies at t+2 | Amendment at t+2 |",
        "s_mapa": "### 2.4 The map from accounts to us-gaap tags and coverage by year",
        "mapa_txt": "The accounts the v1 and v2 signals use, with candidate tags in order of preference. Benford uses all "
        "numbers and needs no map; the DVA does not exist in the US (depreciation comes from the cash flow statement); in "
        "the US, selling and administrative expenses usually come together (SG&A), and many companies do not present "
        "gross profit. Financial companies (weight of non-recurring gains) have no map in this phase.",
        "cab_mapa": "| Account | Candidate us-gaap tags |",
        "cobertura_txt": "Coverage is the share of each fiscal year's original 10-Ks with a dollar value at the report "
        "date, for the company itself (no co-registrant or segment), in the us-gaap taxonomy. By account (any of the "
        "candidate tags):",
        "cobertura_tag_txt": "By tag:",
        "cab_conta": "Account",
        "cab_tag": "Tag",
        "s_rotulos": "## 3. Labels",
        "s_aaer": "### 3.1 The AAERs",
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
        "sec_lista": "- **The public AAER list on the SEC site:** not read directly; the era-py index is a copy of it, "
        "with the refresh date.",
        "ligar": "**How to link each AAER to the CIK without Compustat.** Through 2014, through the Bao et al. "
        "company-years and the era-py gvkey–CIK link. After 2014, there is no free database with the misstated years: the "
        "path is to read each AAER on the SEC site (the company is a party) and match the name against the SEC file of "
        "names and CIKs, keeping only the company and the CIK.",
        "s_402": "### 3.2 A new label: 8-Ks with Item 4.02",
        "txt_402": "Since August 2004, a company files an 8-K with Item 4.02 (*Non-Reliance on Previously Issued Financial "
        "Statements or a Related Audit Report or Completed Interim Review*) when it, or its auditor, concludes that "
        "previously issued statements should no longer be relied upon because of an error; the restatement follows. It is "
        "the same concept as the restatement in Brazil's study 2: the published information was wrong, by error or on "
        "purpose, without saying which. The source is the items field (`items`) of each company's filing history on EDGAR "
        "(`submissions.zip`), which lists the items of each 8-K; only the date, form, items and CIK are read, in memory, "
        "with no 8-K text or company name (`chiocca/eua/itens.py`). A filing by several companies counts once in the "
        "filing counts.",
        "s_contagens": "## 4. Counts",
        "s_cont_aaer": "### 4.1 Bao et al. AAERs with a 10-K in the SEC data",
        "cab_cont": "| Fiscal year | Company-years with an AAER (Bao et al.) | Linked to a CIK | With a 10-K in the SEC data | Company-years with a 10-K (all companies) |",
        "pendente_curto": "pending",
        "total": "**Total**",
        "cont_txt": "The fiscal year follows the Compustat convention used by Bao et al.: the year of the report date, or "
        "the previous one when the fiscal year ends from January to May. A Bao et al. company-year has a 10-K in the SEC "
        "data when some CIK linked to the gvkey in that year filed an original XBRL 10-K for that fiscal year. **From 2009 "
        "to 2014, {fy} company-years with an AAER, {lig} linked to a CIK and {com} with a 10-K in the SEC data**, against "
        "about {denom} companies with a 10-K a year from 2011 to 2014, when XBRL already applied to all. Counting each case (AAER) once: **{casos} cases**, from {cias} "
        "companies, with at least one affected fiscal year with a 10-K from 2009 to 2014 (by the first such year: "
        "{por_ano}). The most recent years have fewer cases because an AAER usually comes out years after the facts, and "
        "the database ends in 2014. The SEC index has {n_xbrl} AAERs issued from 2009 to 2023, of all kinds (not only "
        "misstatements).",
        "s_cont_402": "### 4.2 8-Ks with Item 4.02 and 10-K/As by filing year",
        "cab_402": "| Filing year | 8-K 4.02 | 8-K/A 4.02 | Companies with an 8-K 4.02 | Of them with SIC 6770 (SPACs) | First time since 2009 | With a 10-K in the SEC data | With a 10-K in the SEC data before the 8-K | 10-K (EDGAR) | 10-K/A (EDGAR) | 10-K/A with XBRL (SEC data) |",
        "txt_402_cont": 'A company counts once per year; "first time since 2009" counts each company once in the period. '
        '"With a 10-K in the SEC data" means the CIK has an original 10-K in the Financial Statement Data Sets from 2009q1 '
        'to 2025q4; "before the 8-K", that the first of those 10-Ks was filed by the date of the 8-K (there are XBRL '
        "statements from the time to compare). **From 2009 to 2026-04-30: {n8k} 8-Ks with Item 4.02, from {cias} company-years; "
        "{novas} distinct companies; {com} company-years with a 10-K in the SEC data, {antes} of them with the 10-K before "
        "the 8-K.** The 10-K/As are of all kinds (most only complete Part III); the last column counts those in the SEC "
        "data, by filing year. The 2021 peak coincides with the SEC staff statement of 2021-04-12 on the accounting for "
        "SPAC warrants (acquisition companies with no operations), followed by many restatements: "
        "{spac_2021} of the {cias_2021} companies with an 8-K 4.02 in 2021 have SIC code 6770 (blank checks) in the SEC "
        "data; from 2009 to 2026-04-30, {spac} company-years. The year 2026 only goes to 2026-04-30, the end of the "
        "window of fiscal 2024.",
        "s_decisoes": "## 5. Decisions",
        "s_decididas": "### 5.1 Roberto's decisions (2026-11-24)",
        "decididas": [
            "**Main outcome: the 8-K with Item 4.02**, the same concept as study 2's restatement. The 2009 to 2014 AAERs "
            "stay as description only, with no test.",
            "**Outcome per case:** each episode counted once (one company, one 8-K 4.02 episode, with the 8-Ks and 8-K/As "
            "of the same episode together), with the bootstrap by company, as in study 2. It answers the critique by "
            "Walker (2021 and 2022) and Gow (2022) of Bao et al. (2020), where multi-year frauds spanning training and test "
            "inflate the metric; here the signals are fixed rules, with no training, and each case counts once.",
            "**Exclusions by explicit rule:** SPACs (SIC code 6770, blank checks, in the SEC data), on top of the companies "
            "without revenue (revenue missing or zero, the study 1 rule). The counts below say how many SPACs the "
            "no-revenue rule would already remove; no signal value, hit or alert.",
            "**Financial companies out:** companies with SIC 6000 to 6999, without the SPACs, stay out of the study, "
            "because the map has no accounts for them.",
            "**The revenue tags** are chosen by coverage counts only, and the final list goes into the text that is "
            "registered.",
            "**Period:** fiscal years 2011 to 2024 (report date through 2024-12-31), with the SEC data and the 8-Ks "
            "downloaded again on the day of the computation, because the 12-month window of all those fiscal years has "
            "already ended (the last one, on 2026-04-30). This Phase 0's counts go that far: 10-Ks filed through "
            "2025-12-31 and 8-Ks through 2026-04-30.",
            "**The bootstrap seed** is 20270430.",
            "**The SEC files** stay outside Git, with their SHA-256 in the manifest and the download by script.",
            "**Timeline with a target and a fallback** (section 5.4). No US signal is computed before registration.",
        ],
        "txt_excl_10k": "Original 10-Ks by declared fiscal year (`fy`). Revenue is the annual value (four quarters) of the "
        "first `receita_liquida` tag in the map that the filing has. Financial companies by SIC (6000 to 6999, without "
        "SPACs) appear separately because this phase's map has no revenue for them; in Brazil, the no-revenue rule applies "
        "to non-financial companies only. **The no-revenue count is a ceiling:** it includes companies whose revenue sits "
        "in tags outside the map (coverage of the `receita_liquida` account is between {cob_min} and {cob_max} of 10-Ks, section 2.4); "
        "the revenue map is widened in the pre-registration, before any signal.",
        "cab_excl_10k": "| Fiscal year | 10-K | Financial (SIC 6000 to 6999, without SPACs) | SPACs (SIC 6770) | SPACs already without revenue | Others without revenue | Remaining |",
        "txt_excl_8k": "Company-years with an 8-K 4.02 and a 10-K in the SEC data before the 8-K (section 4.2), by the last "
        "10-K filed by the year's first 8-K 4.02 after the company's first 10-K (revenue and SIC are those of that 10-K):",
        "cab_excl_8k": "| Filing year | With a 10-K before the 8-K | Financial | SPACs (SIC 6770) | SPACs already without revenue | Others without revenue | Remaining |",
        "txt_excl_resumo": "**From 2009 to 2026-04-30, {total} company-years with an 8-K 4.02 and a 10-K before: {fin} "
        "financial, {spac} SPACs (of which the no-revenue rule would already remove {spac_sem}) and {sem} others without "
        "revenue; {ficam} remain.** In the 10-Ks of fiscal years 2009 to 2024, the no-revenue rule would remove {sem_10k} "
        "of the {spac_10k} SPAC filings.",
        "s_opcoes": "### 5.2 The label options compared in Phase 0",
        "cab_opcoes": "| Option | Period | Size | Cost | What it measures |",
        "opcoes": [
            (
                "Free AAERs (Bao et al., through era-py)",
                "affected fiscal years through 2014; with XBRL, 2009 to 2014",
                "{casos_aaer} cases ({ea_aaer} company-years) with a 10-K in the SEC data",
                "none (the gvkey–CIK link does " "not state its source)",
                "an SEC action alleging misstated statements: rare, severe, almost always with "
                "alleged intent, and years after the facts",
            ),
            (
                "8-K with Item 4.02",
                "filings from 2009 to 2026-04-30 (the item exists since August 2004)",
                "{cias_402} distinct companies; {com_402} company-years with a 10-K in the SEC data",
                "none (EDGAR, " "public)",
                "the company or its auditor declares that published statements can no longer be relied upon "
                "because of a material error, intentional or not: the concept of study 2's restatement",
            ),
            (
                "CFRM database (USC)",
                "AAERs issued from 1982 to 2025",
                "4,581 AAERs in all; how many with XBRL is " "unknown without buying",
                "paid (price not published); terms forbid passing the data on",
                "the same as the " "AAER, with the affected years and accounts",
            ),
            (
                "Hand classification of AAERs after 2014",
                "AAERs issued from 2015 to 2023",
                "{n_manual} AAERs to read, of all kinds; only some are misstatements",
                "hours of reading, with the rule " "written beforehand and reading blind to the signals",
                "the same as the AAER, with a risk of " "classification error",
            ),
        ],
        "recomendacao": "**Recommendation from Claude (claude.ai), accepted by Roberto on 2026-11-24:** the 8-K with Item "
        "4.02 as the main outcome, the same concept as study 2's restatement, and the 2009 to 2014 AAERs as a separate "
        "description, with no test. The 8-K 4.02 is public, free, covers the whole XBRL period and has enough cases to "
        "measure something; the AAER is too rare from 2009 to 2014 for a test and measures something else (the SEC "
        "action).",
        "s_pendentes": "### 5.3 For the pre-registration draft",
        "rascunho": "The [draft US pre-registration](us-preregistration-draft.md), of 2026-11-24, takes up these points; "
        "it is not a registration.",
        "decisoes": [
            "**Which fiscal year the case affects.** The items field does not say which statements stopped being "
            "reliable. The rule is written before any signal, with the public version at the date (section 2.3).",
            "**What cannot be done without paid data.** Misstated years of AAERs after 2014 (CFRM); the gvkey and "
            "Compustat data (WRDS); Audit Analytics restatements, which would include restatements without an 8-K 4.02 "
            '("little r"). The era-py gvkey–CIK link does not state its source.',
        ],
        "s_calendario": "### 5.4 Timeline: target and fallback",
        "cab_cal": "| Step | Target | Fallback |",
        "calendario": [
            ("Roberto's decisions (section 5.1).", "2026-11-24", "2026-11-24"),
            (
                "Review of the pre-registration draft by Claude (claude.ai) and Roberto; no signal computed.",
                "2026-12-15",
                "2026-12-15",
            ),
            (
                "Study code written and tested on synthetic data only; coverage of the widened map counted.",
                "2027-01-15",
                "2027-01-31",
            ),
            ("Pre-registration registered and timestamped; code frozen.", "2027-01-31", "2027-03-31"),
            (
                "Single computation, after the timestamp, with the SEC data and the 8-Ks downloaded on the day.",
                "2027-02-28",
                "2027-04-30",
            ),
            ("Report in PT and EN, separate from Brazil's study 2.", "2027-03-31", "2027-05-31"),
        ],
        "fontes": "Sources for the conditions and the critique: sites.google.com/usc.edu/aaerdataset (Buy the Data); "
        "econjwatch.org (Walker, 2021 and 2022); iangow.github.io/notes/published/bklyz.html (Gow, 2022); sec.gov (Form "
        "8-K, Item 4.02; Financial Statement Data Sets; EDGAR, submissions.zip).",
    },
}


def _tabela(cab: str, linhas: list[list[str]], alinhamento: str) -> list[str]:
    regua = "| " + " | ".join("---" if c == "-" else "---:" for c in alinhamento) + " |"
    return [cab, regua, *("| " + " | ".join(x) + " |" for x in linhas)]


def _secao_fsds(d: dict[str, Any], lang: str) -> list[str]:
    t, i, f = T[lang], (lambda v: inteiro(int(v), lang)), d["fsds"]
    p0 = lambda x: pct(x, lang, 0)  # noqa: E731
    e = f["estrutura_do_ultimo"]
    linhas = [t["s_estrutura"], "", t["estrutura"].format(n=i(f["trimestres_baixados"]),
              vazios=", ".join(f["trimestres_sem_entregas"]), ultimo=e["trimestre"]), ""]  # fmt: skip
    linhas += _tabela(t["cab_estrutura"], [[f"`{n}`", i(len(a["colunas"])) if "colunas" in a else "—",
                                            i(a["linhas"]) if "linhas" in a else "—"]
                                           for n, a in e["arquivos"].items()], "-::")  # fmt: skip
    base = set(f["colunas_por_trimestre"][0]["colunas"]["num.txt"])
    trechos = []
    for c in f["colunas_por_trimestre"]:
        num = c["colunas"]["num.txt"]
        extra = ", ".join(f"`{x}`" for x in num if x not in base) or ", ".join(f"`{x}`" for x in num if x == "coreg")
        trechos.append(t["trecho_mudanca"].format(de=c["de"], ate=c["ate"], n=len(num), extra=extra))
    if len(f["colunas_por_trimestre"]) == 1:
        c = f["colunas_por_trimestre"][0]["colunas"]
        colunas = t["colunas_iguais"].format(n_sub=i(len(c["sub.txt"])), n_num=i(len(c["num.txt"])),
                                            n=i(f["trimestres_baixados"]))  # fmt: skip
    else:
        colunas = t["colunas_mudam"].format(mudancas="; ".join(trechos))
    linhas += ["", colunas, "", t["s_10k"], "", t["txt_10k"], ""]
    pe = f["por_exercicio"]
    linhas += _tabela(t["cab_10k"], [[a, i(pe[a]["companhias_com_10k"]), i(pe[a]["entregas_10k"]),
                                      i(pe[a]["entregas_10k_a"]), i(pe[a]["entregas_10k_a_com_numeros"]),
                                      i(pe[a]["10k_emendados_depois"]), i(pe[a]["prazo_mediano_dias"]),
                                      f"{i(pe[a]['prazo_p10_dias'])}–{i(pe[a]['prazo_p90_dias'])}",
                                      p0(pe[a]["ate_90_dias"])] for a in ANOS if a in pe], "-::::::::")  # fmt: skip
    v = f["versoes"]
    cel = lambda a, k: [i(v[a][k]["companhias"]), i(v[a][k]["emenda"])] if k in v[a] else ["—", "—"]  # noqa: E731
    linhas += ["", t["s_versao"], "", t["txt_versao"], ""]
    linhas += _tabela(t["cab_versao"], [[a, *cel(a, "t+1"), *cel(a, "t+2")] for a in ANOS if a in v], "-::::")
    cob = f["cobertura"]
    anos = [a for a in ANOS if a in cob]
    linhas += ["", t["s_mapa"], "", t["mapa_txt"], "", t["cab_mapa"], "| --- | --- |"]
    linhas += [f"| `{c}` | " + ", ".join(f"`{x}`" for x in ts) + " |" for c, ts in d["mapa"].items()]
    linhas += ["", t["cobertura_txt"], ""]
    cab = lambda nome: "| " + nome + " | " + " | ".join(anos) + " |"  # noqa: E731
    linhas += _tabela(cab(t["cab_conta"]), [[f"`{c}`", *(p0(cob[a]["contas"][c]) for a in anos)] for c in d["mapa"]],
                      "-" + ":" * len(anos))  # fmt: skip
    tags = [x for ts in d["mapa"].values() for x in ts]
    linhas += ["", t["cobertura_tag_txt"], ""]
    linhas += _tabela(cab(t["cab_tag"]), [[f"`{x}`", *(p0(cob[a]["tags"][x]) for a in anos)] for x in tags],
                      "-" + ":" * len(anos))  # fmt: skip
    return linhas + [""]


def _secao_exclusoes(f: dict[str, Any], lang: str) -> list[str]:
    """As contagens das exclusões decididas em 24/11/2026, na ordem do rascunho do pré-registro: financeiras, SPACs
    (SIC 6770) e sem receita, nos 10-K e nos 8-K 4.02."""
    t, i = T[lang], (lambda v: inteiro(int(v), lang))
    ex, it = f["exclusoes_10k"], f["itens_8k"]
    cob = [v["contas"]["receita_liquida"] for v in f["cobertura"].values()]
    linhas = ["", t["txt_excl_10k"].format(cob_min=pct(min(cob), lang, 0), cob_max=pct(max(cob), lang, 0)), ""]
    chaves = ("10k", "financeiras", "sic_6770", "sic_6770_sem_receita", "sem_receita_demais", "restantes")
    tab = [[a, *(i(x[k]) for k in chaves)] for a, x in ex.items()]
    soma = {k: sum(x[k] for x in ex.values()) for k in chaves}
    tab.append([t["total"], *(f"**{i(soma[k])}**" for k in chaves)])
    linhas += _tabela(t["cab_excl_10k"], tab, "-::::::") + ["", t["txt_excl_8k"], ""]
    chaves8 = ("companhias_com_10k_fsds_antes", "antes_financeiras", "antes_sic_6770", "antes_sic_6770_sem_receita",
               "antes_sem_receita_demais", "antes_restantes")  # fmt: skip
    tab = [[a, *(i(x[k]) for k in chaves8)] for a, x in it.items()]
    s8 = {k: sum(x[k] for x in it.values()) for k in chaves8}
    tab.append([t["total"], *(f"**{i(s8[k])}**" for k in chaves8)])
    linhas += _tabela(t["cab_excl_8k"], tab, "-::::::")
    resumo = t["txt_excl_resumo"].format(total=i(s8["companhias_com_10k_fsds_antes"]), fin=i(s8["antes_financeiras"]),
                                         spac=i(s8["antes_sic_6770"]), spac_sem=i(s8["antes_sic_6770_sem_receita"]),
                                         sem=i(s8["antes_sem_receita_demais"]), ficam=i(s8["antes_restantes"]),
                                         sem_10k=i(soma["sic_6770_sem_receita"]), spac_10k=i(soma["sic_6770"]))  # fmt: skip
    return linhas + ["", resumo, ""]


def render(d: dict[str, Any], lang: str) -> str:
    t, i = T[lang], (lambda v: inteiro(int(v), lang))
    r, b, li, f = d["rotulos"], d["rotulos"]["bao_et_al"], d["rotulos"]["ligacao_gvkey_cik"], d["fsds"]
    fy, lig = b["empresa_anos_xbrl"], b["empresa_anos_xbrl_ligadas_ao_cik"]
    a = d["acesso_sec"]
    if f is None:
        acesso = t["acesso_pendente"].format(var=a["variavel"], baixados=i(a["fsds_baixados"]),
                                             previstos=i(a["fsds_previstos"]))  # fmt: skip
    else:
        ed = a["edgar_submissions"]
        acesso = t["acesso"].format(var=a["variavel"], baixados=i(a["fsds_baixados"]), previstos=i(a["fsds_previstos"]),
                                    gb=decimal(a["fsds_bytes"] / 1e9, lang), gb_edgar=decimal(int(ed["bytes"]) / 1e9, lang),
                                    dia_edgar=data(ed["baixado_em_utc"][:10], lang))  # fmt: skip
    linhas = [t["titulo"], "", t["aviso"], "", t["s_acesso"], "", acesso, "", t["s_fsds"], "",
              t["fsds"].format(t0=d["limite"]["trimestres_fsds"][0], t1=d["limite"]["trimestres_fsds"][1]), "",
              t["versoes"], ""]  # fmt: skip
    if f is None:
        linhas += [t["pendente"], "", t["s_mapa"], "", t["mapa_txt"], "", t["cab_mapa"], "| --- | --- |"]
        linhas += [f"| `{c}` | " + ", ".join(f"`{x}`" for x in ts) + " |" for c, ts in d["mapa"].items()] + [""]
    else:
        linhas += _secao_fsds(d, lang)
    idx = r["indice_sec"]
    linhas += [t["s_rotulos"], "", t["s_aaer"], "",
               t["era"].format(v=r["pacote"]["versao"], lic=r["pacote"]["licenca"], sha=d["era_py"]["sha256"]), "",
               t["indice"].format(atual=data(r["pacote"]["indice_atualizado"], lang), n=i(idx["aaers"]),
                                  distintos=i(idx["numeros_distintos"]), a0=idx["primeiro_ano"], a1=idx["ultimo_ano"]),
               t["bao"].format(linhas=i(b["linhas"]), aaers=i(b["aaers"]), gvkeys=i(b["gvkeys"]),
                               a0=b["primeiro_ano_afetado"], a1=b["ultimo_ano_afetado"], fy=i(b["empresa_anos"]),
                               multi=i(b["aaers_de_mais_de_um_ano"])),
               t["ligacao"].format(linhas=i(li["linhas"]), gvkeys=i(li["gvkeys"]), ciks=i(li["ciks"])),
               t["cfrm"], t["sec_lista"], "", t["ligar"], "", t["s_402"], "", t["txt_402"], "",
               t["s_contagens"], "", t["s_cont_aaer"], ""]  # fmt: skip
    n_xbrl = sum(v for ano, v in idx["por_ano"].items() if int(ano) >= rotulos.PRIMEIRO_ANO_XBRL)
    n_manual = sum(v for ano, v in idx["por_ano"].items() if int(ano) > b["ultimo_ano_afetado"])
    pend = t["pendente_curto"]
    anos_aaer = list(b["empresa_anos_xbrl_por_ano"])
    if f is None:
        tab = [[ano, i(n), i(b["empresa_anos_xbrl_ligadas_por_ano"][ano]), pend, pend]
               for ano, n in b["empresa_anos_xbrl_por_ano"].items()]  # fmt: skip
        linhas += _tabela(t["cab_cont"], tab, "-::::") + [""]
        return "\n".join(linhas + [t["fontes"]]) + "\n"
    aa, den = f["aaer"], f["companhias_com_10k_por_ano_compustat"]
    tab = [[ano, i(b["empresa_anos_xbrl_por_ano"][ano]), i(b["empresa_anos_xbrl_ligadas_por_ano"][ano]),
            i(aa["empresa_anos_com_10k_por_ano"].get(ano, 0)), i(den.get(ano, 0))] for ano in anos_aaer]  # fmt: skip
    tab.append([t["total"], f"**{i(fy)}**", f"**{i(lig)}**", f"**{i(aa['empresa_anos_com_10k'])}**",
                i(sum(den.get(ano, 0) for ano in anos_aaer))])  # fmt: skip
    linhas += _tabela(t["cab_cont"], tab, "-::::")
    todas = [ano for ano in anos_aaer if int(ano) >= 2011]  # o XBRL valeu para todas as companhias a partir de 2011
    media = sum(den.get(ano, 0) for ano in todas) / len(todas)
    por_ano = ", ".join(f"{ano}: {i(n)}" for ano, n in aa["casos_com_10k_por_primeiro_ano"].items())
    linhas += ["", t["cont_txt"].format(fy=i(fy), lig=i(lig), com=i(aa["empresa_anos_com_10k"]),
                                        denom=i(round(media, -2)), casos=i(aa["casos_com_10k"]),
                                        cias=i(aa["companhias_com_10k"]), por_ano=por_ano, n_xbrl=i(n_xbrl)),
               "", t["s_cont_402"], ""]  # fmt: skip
    it, pe = f["itens_8k"], f["por_entrega"]
    tab = [[ano, i(x["8k_402"]), i(x["8k_a_402"]), i(x["companhias_8k_402"]),
            i(x["companhias_8k_402_sic_6770"]), i(x["companhias_novas_8k_402"]),
            i(x["companhias_com_10k_fsds"]), i(x["companhias_com_10k_fsds_antes"]), i(x["10k_edgar"]),
            i(x["10k_a_edgar"]), i(pe.get(ano, {}).get("10k_a", 0))] for ano, x in it.items()]  # fmt: skip
    soma = {k: sum(x[k] for x in it.values()) for k in next(iter(it.values()))}
    tab.append([t["total"], *(f"**{i(soma[k])}**" for k in ("8k_402", "8k_a_402", "companhias_8k_402",
                                                            "companhias_8k_402_sic_6770",
                                                            "companhias_novas_8k_402", "companhias_com_10k_fsds",
                                                            "companhias_com_10k_fsds_antes", "10k_edgar", "10k_a_edgar")),
                f"**{i(sum(x.get('10k_a', 0) for x in pe.values()))}**"])  # fmt: skip
    linhas += _tabela(t["cab_402"], tab, "-" + ":" * 10)
    linhas += ["", t["txt_402_cont"].format(n8k=i(soma["8k_402"]), cias=i(soma["companhias_8k_402"]),
                                            novas=i(soma["companhias_novas_8k_402"]),
                                            com=i(soma["companhias_com_10k_fsds"]),
                                            antes=i(soma["companhias_com_10k_fsds_antes"]),
                                            spac=i(soma["companhias_8k_402_sic_6770"]),
                                            spac_2021=i(it.get("2021", {}).get("companhias_8k_402_sic_6770", 0)),
                                            cias_2021=i(it.get("2021", {}).get("companhias_8k_402", 0))),
               "", t["s_decisoes"], "", t["s_decididas"], ""]  # fmt: skip
    linhas += [f"{k}. {x}" for k, x in enumerate(t["decididas"], start=1)]
    linhas += _secao_exclusoes(f, lang) + [t["s_opcoes"], ""]
    valores = {"casos_aaer": i(aa["casos_com_10k"]), "ea_aaer": i(aa["empresa_anos_com_10k"]),
               "cias_402": i(soma["companhias_novas_8k_402"]), "com_402": i(soma["companhias_com_10k_fsds"]),
               "n_manual": i(n_manual)}  # fmt: skip
    linhas += _tabela(t["cab_opcoes"], [[f"**{o}**", per, tam.format(**valores), custo, mede]
                                        for o, per, tam, custo, mede in t["opcoes"]], "-----")  # fmt: skip
    linhas += ["", t["recomendacao"], "", t["s_pendentes"], "", t["rascunho"], ""]
    linhas += [f"{k}. {x}" for k, x in enumerate(t["decisoes"], start=1)]
    linhas += ["", t["s_calendario"], "", t["cab_cal"], "| --- | --- | --- |"]
    linhas += [f"| {etapa} | {data(meta, lang)} | {data(reserva, lang)} |" for etapa, meta, reserva in t["calendario"]]
    linhas += ["", t["fontes"]]
    return "\n".join(linhas) + "\n"


def main(argv: list[str]) -> None:
    if "--baixar" in argv:
        sec.grava_manifesto([rotulos.baixar()])
        try:
            cliente = sec.Cliente()
            sec.grava_manifesto(fsds.baixar(cliente))
            sec.grava_manifesto(itens.baixar(cliente))
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
