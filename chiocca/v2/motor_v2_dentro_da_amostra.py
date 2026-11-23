"""Motor v2 congelado, dentro da amostra de desenvolvimento (pré-registro do motor v2, seções 5 e 6; pedido de
23/11/2026, item 4(b)).

Rótulo: "dentro da amostra de desenvolvimento, não é teste". Feito só depois do commit de congelamento
(`docs/motor_v2_codigo_congelado.json`): o código do v2 que roda aqui é o congelado (o SHA-256 do registro fica gravado
no JSON, e o teste do congelamento acusa qualquer mudança no código). Os exercícios são os de 2010 a 2023, os mesmos em
que o v2 foi desenvolvido, com critérios sem rótulo: nada aqui é teste. O teste do v2 é o braço dele no estudo 2
(emenda 5) e, depois, o teste prospectivo com os exercícios de 2026.

1. **Taxas de alerta e cobertura:** o v2 com as três mudanças, sobre o armazém (cada empresa na data de corte do seu
   exercício) e a DVA dos zips da DFP; por exercício e grupo, as avaliadas, as em alerta e a taxa; a cobertura de cada
   sinal ao lado da do v1; as avaliadas só pelo v2; a taxa por número de sinais calculáveis. Conferido com as
   descrições sem rótulo (`docs/motor_v2_descricoes.json`, escore pelo maior percentil): as mesmas avaliadas e os
   mesmos alertas, por grupo e por número de sinais.
2. **Acertos nos casos do estudo 1:** a regra da seção 5 do pré-registro do estudo 1 e os alarmes por acerto das
   emendas 10 e 11, pelas funções do estudo 1 (`chiocca.metricas`), com o alerta do v2 no lugar do do v1. O gabarito do
   estudo 1 (`data/gabarito_casos.csv`) é lido aqui, depois do congelamento, e nunca pelo código do v2. Só contagens,
   lado a lado com o v1 e a regra boba do estudo 1; nenhum caso nem empresa é citado.

Grava docs/motor_v2_dentro_da_amostra.json e monta docs/motor-v2-dentro-da-amostra.md e docs/en/engine-v2-in-sample.md.
Uso: python -m chiocca.v2.motor_v2_dentro_da_amostra   (precisa de data/armazem, data/brutos/cvm e resultados/)
"""

from __future__ import annotations

import hashlib
import json
import subprocess
from typing import Any, cast

import pandas as pd

from chiocca import metricas as mt
from chiocca.base import BRUTOS, RAIZ
from chiocca.cvm import Fontes
from chiocca.formato import inteiro, pct
from chiocca.sinais_amostra import AMOSTRA_FIN, AMOSTRA_NF
from chiocca.v2 import lacre
from chiocca.v2.armazem import FontesArmazem
from chiocca.v2.motor_v2 import lista, motor, registro

SAIDA = RAIZ / "docs" / "motor_v2_dentro_da_amostra.json"
DOCS = {"pt": RAIZ / "docs" / "motor-v2-dentro-da-amostra.md", "en": RAIZ / "docs" / "en" / "engine-v2-in-sample.md"}
SINAIS_ESTUDO_1 = RAIZ / "resultados" / "sinais_empresa_ano.csv"
GABARITO = RAIZ / "data" / "gabarito_casos.csv"
OBSERVACAO = RAIZ / "data" / "casos_em_observacao.csv"
DESCRICOES = RAIZ / "docs" / "motor_v2_descricoes.json"
ANOS = range(2010, lacre.ULTIMO_EXERCICIO_LIBERADO + 1)
ROTULO = {"pt": "dentro da amostra de desenvolvimento, não é teste", "en": "within the development sample, not a test"}
GRUPOS = (AMOSTRA_NF, AMOSTRA_FIN)
SINAIS = {AMOSTRA_NF: ("mscore", "dpo", "juro", "benford"), AMOSTRA_FIN: ("peso_nao_recorrente", "benford")}
CHAVE = ["exercicio", "cd_cvm", "dt_refer"]


def _git(*args: str) -> str:
    return subprocess.run(["git", *args], cwd=RAIZ, capture_output=True, text=True, check=True).stdout.strip()


def sinais_do_v2() -> pd.DataFrame:
    """O v2 congelado, com as três mudanças, de 2010 a 2023 (o armazém tem a interface das fontes)."""
    return lista.calcular(cast(Fontes, FontesArmazem()), ANOS, motor.TODAS, brutos_dva=BRUTOS)


def taxas(s2: pd.DataFrame) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for g in GRUPOS:
        x = s2[s2.amostra == g]
        por_ano = {str(a): {"empresa_anos": int((x.exercicio == a).sum()),
                            "avaliadas": int((x.avaliada & (x.exercicio == a)).sum()),
                            "em_alerta": int((x.em_alerta & (x.exercicio == a)).sum())} for a in ANOS}  # fmt: skip
        ta = [v["em_alerta"] / v["avaliadas"] for v in por_ano.values() if v["avaliadas"]]
        out[g] = {"por_ano": por_ano, "empresa_anos": len(x), "avaliadas": int(x.avaliada.sum()),
                  "em_alerta": int(x.em_alerta.sum()), "menor_taxa_anual": min(ta), "maior_taxa_anual": max(ta)}  # fmt: skip
    return out


def cobertura(s2: pd.DataFrame, s1: pd.DataFrame) -> dict[str, Any]:
    v1_avaliadas = set(map(tuple, s1.loc[s1.avaliada.astype("boolean").fillna(False), CHAVE].astype(str).to_numpy()))
    out: dict[str, Any] = {}
    for g in GRUPOS:
        x, y = s2[s2.amostra == g], s1[s1.amostra == g]
        chaves = list(map(tuple, x[CHAVE].astype(str).to_numpy()))
        so_v2 = sum(bool(av) and k not in v1_avaliadas for av, k in zip(x.avaliada, chaves))
        v2_avaliadas = {k for av, k in zip(x.avaliada, chaves) if bool(av)}
        v1_do_grupo = set(map(tuple, y.loc[y.avaliada.astype("boolean").fillna(False), CHAVE].astype(str).to_numpy()))
        out[g] = {
            "empresa_anos": len(x),
            "v2": {s: int(x[s].notna().sum()) for s in SINAIS[g]},
            "v1": {s: int(y[s].notna().sum()) for s in SINAIS[g] if s in y.columns},
            "avaliadas_v1": int(y.avaliada.astype("boolean").fillna(False).sum()),
            "avaliadas_so_pelo_v2": int(so_v2),
            "avaliadas_pelo_v1_e_nao_pelo_v2": len(v1_do_grupo - v2_avaliadas),
        }
    out[AMOSTRA_NF]["depreciacao_pela_dva"] = int(s2.marca_depreciacao_dva.fillna(False).astype(bool).sum())
    desc = json.loads(DESCRICOES.read_text(encoding="utf-8"))["depi_dva"]
    out[AMOSTRA_NF]["descricoes"] = {"depi_pela_dva": desc["depi_pela_dva"], "mscore_v2": desc["mscore_v2"],
                                     "depi_pela_dva_fora_do_plano_nao_financeiro": depi_das_descricoes_fora_do_plano(s2)}  # fmt: skip
    return out


def depi_das_descricoes_fora_do_plano(s2: pd.DataFrame) -> int:
    """Quantas empresa-anos as descrições sem rótulo contaram com o DEPI pela DVA entre as não financeiras fora do plano
    de contas não financeiro (bancos e outros), em que o v1 não calcula o M-score e o v2, como o v1, não aplica a DVA;
    pela mesma conta das descrições (`chiocca.v2.motor_v2_descricoes`)."""
    from chiocca.v2 import motor_v2_descricoes as md

    x = s2[(s2.amostra == AMOSTRA_NF) & (s2.plano != motor.PLANO_NAO_FINANCEIRO) & (s2.fonte == motor.DADOS_ABERTOS)]
    n = 0
    for ano, g in x.groupby("exercicio"):
        b = md._por_empresa_ano_da_base(int(ano))[["cd_cvm", "dt_refer", "imob_t", "imob_t1"]]
        m = g[["cd_cvm", "dt_refer", "tipo"]].merge(md._dva(int(ano)), on=["cd_cvm", "dt_refer", "tipo"])
        m = m.merge(b, on=["cd_cvm", "dt_refer"])
        n += sum(md.depi_pela_dva(*r) == md.depi_pela_dva(*r) for r in m[["dep_t", "dep_t1", "imob_t", "imob_t1"]]
                 .itertuples(index=False))  # fmt: skip
    return int(n)


def por_numero_de_sinais(s2: pd.DataFrame) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for g in GRUPOS:
        x = s2[(s2.amostra == g) & s2.avaliada]
        out[g] = {str(int(k)): {"empresa_anos": len(v), "alertas": int(v.em_alerta.sum())}
                  for k, v in x.groupby("n_sinais_calculaveis")}  # fmt: skip
    return out


def confere_descricoes(t: dict[str, Any], k: dict[str, Any]) -> dict[str, bool]:
    """As avaliadas e os alertas do v2 congelado contra as descrições sem rótulo (escore pelo maior percentil)."""
    d = json.loads(DESCRICOES.read_text(encoding="utf-8"))["escore_por_numero_de_sinais"]["grupos"]
    return {g: d[g]["maximo"]["avaliadas"] == t[g]["avaliadas"] and d[g]["maximo"]["alertas"] == t[g]["em_alerta"]
            and d[g]["maximo"]["por_k"] == k[g] for g in GRUPOS}  # fmt: skip


def _pacote(a: dict[str, Any]) -> dict[str, Any]:
    """Só as contagens de `metricas.avaliacao` (sem os casos)."""
    return {"acertaveis": a["acertaveis"], "acertados": a["acertados"], "acertados_teste": a["acertados_teste"],
            "alarmes": a["alarmes"], "secundaria": a["secundaria"], "taxa": a["taxa"]}  # fmt: skip


def acertos(s2: pd.DataFrame, s1: pd.DataFrame) -> dict[str, Any]:
    gab = pd.read_csv(GABARITO, dtype={"cd_cvm": str})
    fora = set(pd.read_csv(OBSERVACAO, dtype={"cd_cvm": str}).cd_cvm.dropna().astype(str))
    v2, v1 = mt.prepara(s2), mt.prepara(s1)
    return {
        "v2": _pacote(mt.avaliacao(v2, gab, fora, mt.ALERTA_SINAIS, "avaliada")),
        "v1": _pacote(mt.avaliacao(v1, gab, fora, mt.ALERTA_SINAIS, "avaliada")),
        "regra_boba": _pacote(mt.avaliacao(v1, gab, fora, mt.ALERTA_BOBA, "boba_avaliada")),
    }


def calcula(s2: pd.DataFrame | None = None) -> dict[str, Any]:
    s1 = lacre.so_liberados(pd.read_csv(SINAIS_ESTUDO_1, dtype={"cd_cvm": str}, low_memory=False))
    s2 = sinais_do_v2() if s2 is None else s2
    assert set(s2.exercicio) <= set(ANOS)
    t, k = taxas(s2), por_numero_de_sinais(s2)
    return {
        "rotulo": ROTULO["pt"],
        "anos": [ANOS[0], ANOS[-1]],
        "commit": _git("rev-parse", "HEAD"),
        "codigo_sem_alteracao_local": _git("status", "--porcelain", "--untracked-files=no", "--", "chiocca") == "",
        "registro_sha256": hashlib.sha256(registro.REGISTRO.read_bytes()).hexdigest(),
        "congelado_em": json.loads(registro.REGISTRO.read_text(encoding="utf-8"))["congelado_em"],
        "taxas": t,
        "cobertura": cobertura(s2, s1),
        "por_numero_de_sinais": k,
        "igual_as_descricoes": confere_descricoes(t, k),
        "acertos_estudo_1": acertos(s2, s1),
    }


# ---- documento ----

T: dict[str, dict[str, Any]] = {
    "pt": {
        "titulo": "Motor v2 congelado: dentro da amostra de desenvolvimento",
        "aviso": "**Dentro da amostra de desenvolvimento, não é teste.** O v2 foi congelado em {data} "
        "([registro de SHA-256](motor_v2_codigo_congelado.json)), e só depois disso estes números foram calculados, "
        "com o código congelado, nos exercícios de {ini} a {fim}, os mesmos em que o v2 foi desenvolvido. Nada aqui "
        "é evidência de que o v2 funciona: o teste dele é o braço do v2 na avaliação secundária do estudo 2 (emenda 5) "
        "e, depois, o teste prospectivo com os exercícios de 2026. Só números agregados; nenhuma empresa é citada.",
        "s1": "## 1. Taxa de alerta",
        "s1_txt": "O v2 com as três mudanças, cada empresa na data de corte do seu exercício. Alerta: escore no quantil "
        "de 90% do exercício e do grupo; avaliada: pelo menos um sinal calculável.",
        "cab1": "| Exercício | Não financeiras avaliadas | Em alerta | Taxa | Financeiras avaliadas | Em alerta | Taxa |",
        "total": "Total",
        "s1_fim": "A taxa anual fica entre {nf_min} e {nf_max} nas não financeiras e entre {fin_min} e {fin_max} nas "
        "financeiras. As avaliadas e os alertas, por grupo e por número de sinais calculáveis, são os mesmos das "
        "[descrições sem rótulo](motor-v2-descricoes.md) feitas antes do pré-registro: {igual}.",
        "sim": "sim, nos dois grupos",
        "nao": "não",
        "s2": "## 2. Cobertura dos sinais",
        "cab2": "| Grupo | Sinal | Calculável no v1 | Calculável no v2 |",
        "sinal": {
            "mscore": "M-score",
            "dpo": "salto do DPO",
            "juro": "juro implícito",
            "benford": "desvio de Benford padronizado",
            "peso_nao_recorrente": "peso de ganhos não recorrentes",
        },
        "grupo": {AMOSTRA_NF: "Não financeiras", AMOSTRA_FIN: "Financeiras"},
        "nao_existe": "não existe no v1",
        "s2_fim": "O DEPI pela DVA entra em {dva} empresa-anos. As descrições sem rótulo contaram {desc}: as {fora} a "
        "mais são não financeiras fora do plano de contas não financeiro (bancos e outros), em que o v1 não calcula o "
        "M-score e o v2, como o v1, não aplica a DVA; o M-score cobre as mesmas {m} empresa-anos nos dois cálculos. O v2 avalia {so_nf} não financeiras e {so_fin} "
        "financeiras que o v1 não avaliava (por exemplo, só pelo Benford); das {av1_nf} não financeiras avaliadas pelo "
        "v1, o v2 {avalia_nf}.",
        "todas": "avalia todas",
        "faltam": "deixa de avaliar {n}",
        "s3": "## 3. Taxa de alerta por número de sinais calculáveis",
        "s3_txt": "A característica conhecida da seção 4 do pré-registro do v2, sem correção:",
        "cab3": "| Grupo | Sinais calculáveis | Avaliadas | Em alerta | Taxa |",
        "s4": "## 4. Acertos nos casos do estudo 1 (dentro da amostra, não é teste)",
        "s4_txt": "A regra da seção 5 do pré-registro do estudo 1 e os alarmes por acerto das emendas 10 e 11, com o "
        "alerta do v2 no lugar do do v1, pelas mesmas funções do estudo 1. O v2 foi desenvolvido sem o gabarito, mas "
        "nos mesmos exercícios e com os mesmos casos à vista: os acertos abaixo não são teste.",
        "cab4": "| | v2 congelado | v1 (estudo 1) | Regra boba (estudo 1) |",
        "acertaveis": "Casos acertáveis",
        "acertados": "Casos acertados, de 2010 a 2023",
        "acertados_teste": "Casos acertados com alerta de 2017 a 2023",
        "empresas_teste": "Não financeiras distintas em alerta, de 2017 a 2023",
        "alarmes_teste": "Alarmes por acerto, de 2017 a 2023 (não financeiras)",
        "empresas_inteiro": "Não financeiras distintas em alerta, de 2010 a 2023",
        "alarmes_inteiro": "Alarmes por acerto, de 2010 a 2023 (não financeiras)",
        "indefinido": "sem acerto",
    },
    "en": {
        "titulo": "Engine v2 frozen: within the development sample",
        "aviso": "**Within the development sample, not a test.** Engine v2 was frozen on {data} "
        "([SHA-256 registry](../motor_v2_codigo_congelado.json)), and only after that were these numbers computed, "
        "with the frozen code, on fiscal years {ini} to {fim}, the same ones in which v2 was developed. Nothing here "
        "is evidence that v2 works: its test is the v2 arm in the secondary evaluation of study 2 (amendment 5) and, "
        "later, the prospective test with fiscal year 2026. Aggregate numbers only; no company is named.",
        "s1": "## 1. Alert rate",
        "s1_txt": "Engine v2 with the three changes, each company at the cutoff date of its fiscal year. Alert: score "
        "at the 90% quantile of the fiscal year and group; evaluated: at least one computable signal.",
        "cab1": "| Fiscal year | Non-financial evaluated | On alert | Rate | Financial evaluated | On alert | Rate |",
        "total": "Total",
        "s1_fim": "The yearly rate stays between {nf_min} and {nf_max} for non-financial companies and between "
        "{fin_min} and {fin_max} for financial ones. The evaluated company-years and the alerts, by group and by "
        "number of computable signals, are the same as in the [label-free descriptions](engine-v2-descriptions.md) "
        "made before the pre-registration: {igual}.",
        "sim": "yes, in both groups",
        "nao": "no",
        "s2": "## 2. Signal coverage",
        "cab2": "| Group | Signal | Computable in v1 | Computable in v2 |",
        "sinal": {
            "mscore": "M-score",
            "dpo": "DPO jump",
            "juro": "implied interest",
            "benford": "standardized Benford deviation",
            "peso_nao_recorrente": "weight of non-recurring gains",
        },
        "grupo": {AMOSTRA_NF: "Non-financial", AMOSTRA_FIN: "Financial"},
        "nao_existe": "does not exist in v1",
        "s2_fim": "DEPI from the DVA applies to {dva} company-years. The label-free descriptions counted {desc}: the "
        "{fora} extra ones are non-financial company-years outside the non-financial chart of accounts (banks and "
        "others), where v1 does not compute the M-score and v2, like v1, does not apply the DVA; the M-score covers "
        "the same {m} company-years in both computations. Engine v2 evaluates {so_nf} non-financial and "
        "{so_fin} financial company-years that v1 did not evaluate (for example, only through Benford); of the "
        "{av1_nf} non-financial company-years evaluated by v1, v2 {avalia_nf}.",
        "todas": "evaluates all",
        "faltam": "no longer evaluates {n}",
        "s3": "## 3. Alert rate by number of computable signals",
        "s3_txt": "The known characteristic in section 4 of the v2 pre-registration, uncorrected:",
        "cab3": "| Group | Computable signals | Evaluated | On alert | Rate |",
        "s4": "## 4. Hits on the study 1 cases (within the sample, not a test)",
        "s4_txt": "The rule in section 5 of the study 1 pre-registration and the alarms per hit of amendments 10 and "
        "11, with the v2 alert in place of the v1 alert, through the same study 1 functions. Engine v2 was developed "
        "without the answer key, but on the same fiscal years and with the same cases in view: the hits below are not "
        "a test.",
        "cab4": "| | v2 frozen | v1 (study 1) | Naive rule (study 1) |",
        "acertaveis": "Hittable cases",
        "acertados": "Cases hit, 2010 to 2023",
        "acertados_teste": "Cases hit with an alert in 2017 to 2023",
        "empresas_teste": "Distinct non-financial companies on alert, 2017 to 2023",
        "alarmes_teste": "Alarms per hit, 2017 to 2023 (non-financial)",
        "empresas_inteiro": "Distinct non-financial companies on alert, 2010 to 2023",
        "alarmes_inteiro": "Alarms per hit, 2010 to 2023 (non-financial)",
        "indefinido": "no hit",
    },
}


def _data(iso: str, lang: str) -> str:
    a, m, d = iso.split("-")
    return f"{d}/{m}/{a}" if lang == "pt" else iso


def render(d: dict[str, Any], lang: str) -> str:
    t = T[lang]
    i = lambda n: inteiro(int(n), lang)  # noqa: E731
    p = lambda x: pct(x, lang)  # noqa: E731
    tx, cob, k, ac = d["taxas"], d["cobertura"], d["por_numero_de_sinais"], d["acertos_estudo_1"]
    nf, fin = tx[AMOSTRA_NF], tx[AMOSTRA_FIN]
    linhas = [f"# {t['titulo']}", "", "> " + t["aviso"].format(data=_data(d["congelado_em"], lang), ini=d["anos"][0],
                                                                fim=d["anos"][1]), "", t["s1"], "", t["s1_txt"], "",
              t["cab1"], "| --- | ---: | ---: | ---: | ---: | ---: | ---: |"]  # fmt: skip
    for a in nf["por_ano"]:
        x, y = nf["por_ano"][a], fin["por_ano"][a]
        linhas.append(f"| {a} | {i(x['avaliadas'])} | {i(x['em_alerta'])} | {p(x['em_alerta'] / x['avaliadas'])} | "
                      f"{i(y['avaliadas'])} | {i(y['em_alerta'])} | {p(y['em_alerta'] / y['avaliadas'])} |")  # fmt: skip
    linhas.append(f"| {t['total']} | {i(nf['avaliadas'])} | {i(nf['em_alerta'])} | {p(nf['em_alerta'] / nf['avaliadas'])}"
                  f" | {i(fin['avaliadas'])} | {i(fin['em_alerta'])} | {p(fin['em_alerta'] / fin['avaliadas'])} |")  # fmt: skip
    igual = t["sim"] if all(d["igual_as_descricoes"].values()) else t["nao"]
    linhas += ["", t["s1_fim"].format(nf_min=p(nf["menor_taxa_anual"]), nf_max=p(nf["maior_taxa_anual"]),
                                      fin_min=p(fin["menor_taxa_anual"]), fin_max=p(fin["maior_taxa_anual"]), igual=igual),
               "", t["s2"], "", t["cab2"], "| --- | --- | ---: | ---: |"]  # fmt: skip
    for g in GRUPOS:
        c = cob[g]
        for s in SINAIS[g]:
            v1 = i(c["v1"][s]) if s in c["v1"] else t["nao_existe"]
            linhas.append(f"| {t['grupo'][g]} | {t['sinal'][s]} | {v1} | {i(c['v2'][s])} |")
    dsc = cob[AMOSTRA_NF]["descricoes"]
    linhas += ["", t["s2_fim"].format(dva=i(cob[AMOSTRA_NF]["depreciacao_pela_dva"]), desc=i(dsc["depi_pela_dva"]),
                                      fora=i(dsc["depi_pela_dva_fora_do_plano_nao_financeiro"]),
                                      m=i(cob[AMOSTRA_NF]["v2"]["mscore"]),
                                      so_nf=i(cob[AMOSTRA_NF]["avaliadas_so_pelo_v2"]),
                                      so_fin=i(cob[AMOSTRA_FIN]["avaliadas_so_pelo_v2"]),
                                      av1_nf=i(cob[AMOSTRA_NF]["avaliadas_v1"]),
                                      avalia_nf=t["todas"] if not cob[AMOSTRA_NF]["avaliadas_pelo_v1_e_nao_pelo_v2"]
                                      else t["faltam"].format(n=i(cob[AMOSTRA_NF]["avaliadas_pelo_v1_e_nao_pelo_v2"]))),
               "", t["s3"], "", t["s3_txt"], "", t["cab3"], "| --- | ---: | ---: | ---: | ---: |"]  # fmt: skip
    for g in GRUPOS:
        for n, v in k[g].items():
            linhas.append(f"| {t['grupo'][g]} | {n} | {i(v['empresa_anos'])} | {i(v['alertas'])} | "
                          f"{p(v['alertas'] / v['empresa_anos'])} |")  # fmt: skip
    linhas += ["", t["s4"], "", t["s4_txt"], "", t["cab4"], "| --- | ---: | ---: | ---: |"]
    lados = (ac["v2"], ac["v1"], ac["regra_boba"])

    def alarme(x: dict[str, Any]) -> str:
        v = x["alarmes_por_acerto"]
        return t["indefinido"] if v is None else inteiro(round(v), lang)

    def linha(rotulo: str, f: Any) -> str:
        return f"| {rotulo} | " + " | ".join(f(x) for x in lados) + " |"

    linhas += [
        linha(t["acertaveis"], lambda x: i(x["acertaveis"])),
        linha(t["acertados"], lambda x: i(x["acertados"])),
        linha(t["acertados_teste"], lambda x: i(x["acertados_teste"])),
        linha(t["empresas_teste"], lambda x: i(x["alarmes"]["nf"]["teste"]["empresas_em_alerta"])),
        linha(t["alarmes_teste"], lambda x: alarme(x["alarmes"]["nf"]["teste"])),
        linha(t["empresas_inteiro"], lambda x: i(x["alarmes"]["nf"]["inteiro"]["empresas_em_alerta"])),
        linha(t["alarmes_inteiro"], lambda x: alarme(x["alarmes"]["nf"]["inteiro"])),
    ]
    return "\n".join(linhas) + "\n"


def main() -> None:
    d = calcula()
    SAIDA.write_text(json.dumps(d, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    for lang, caminho in DOCS.items():
        caminho.write_text(render(d, lang), encoding="utf-8")
    print(json.dumps({"taxas": {g: (v["avaliadas"], v["em_alerta"]) for g, v in d["taxas"].items()},
                      "igual_as_descricoes": d["igual_as_descricoes"]}, ensure_ascii=False))  # fmt: skip


if __name__ == "__main__":
    main()
