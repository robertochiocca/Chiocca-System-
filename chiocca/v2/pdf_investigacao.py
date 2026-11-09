"""PDF da investigação, gerado só do JSON (`chiocca.v2.investigacao`): texto e tabelas, nas duas línguas.

O PDF não recalcula nada: cada número sai do JSON, formatado no idioma dele. Toda página leva o aviso fixo e o número
da página (`chiocca.v2.pdf_simples`, gerador sem dependência e determinístico: o mesmo JSON dá os mesmos bytes).
"""

from __future__ import annotations

from typing import Any

from chiocca.formato import data, decimal, inteiro, pct
from chiocca.v2.pdf_simples import gerar_pdf, paginar

T: dict[str, dict[str, Any]] = {
    "pt": {
        "titulo": "# Investigação: {nome} (código CVM {cd}), exercício {ex}, como era em {data}",
        "empresa": "# Empresa", "setor": "Setor: {s} (origem: {o}); grupo: {g}; situação no cadastro atual: {c}.",
        "documento": "# Documento usado",
        "doc": "DFP de {ex}, versão {v}, entregue em {r}; origem: {o}; tipo: {t}; escala original: {e}.",
        "versoes": "Versões conhecidas na data: {v}.", "link": "Documento na CVM: {l}",
        "manipulacao": "# Possível manipulação (motor v1, estudo 1)",
        "risco": "# Risco financeiro (só contexto)", "qualidade": "# Qualidade financeira (só contexto)",
        "valor": "Valor", "alerta": "Alerta pela regra do estudo 1", "regra": "Regra",
        "sim": "sim", "nao": "não", "nao_dispara": "não dispara alerta",
        "pct_setor": "Percentil no setor e ano", "pct_grupo": "Percentil no grupo e ano",
        "historico": "Histórico da própria empresa", "confianca": "Confiança nos dados",
        "alternativas": "Explicações alternativas", "no_produto": "No produto",
        "hist_txt": "mediana {m}; cerca de IQR de {a} a {b}; valor {p} da cerca ({n} exercícios)",
        "posicoes": {"dentro": "dentro", "acima": "acima", "abaixo": "abaixo"},
        "componentes": "Componentes", "sinais_f": "Sinais",
        "mudancas": "# Mudanças",
        "destacadas": "Destacadas no comparativo do ano seguinte: {n} (limite de R$ {lim} milhões, 1% do ativo total da versão usada). Valores em R$ milhões:",
        "destacada_linha": "{dem} {cod} {ds}: {v} na versão usada (v{ver}, entregue em {dt}); {c} no comparativo da DFP seguinte (v{vers}, entregue em {dts}); diferença de {dif}. {txt}.",
        "sem_destacadas": "Destacadas no comparativo do ano seguinte: nenhuma.",
        "comparativo": "Lista completa: {n} contas acima da tolerância de R$ {tol} (grupo a, totais e linhas-chave: {a}; grupo b, reclassificações: {b}), no anexo ao final.",
        "anexo": "# Anexo: lista completa das diferenças do comparativo do ano seguinte (R$ milhões)",
        "comparativo_linha": "({g}) {dem} {cod} {ds}: {v} na versão usada, {c} no comparativo (diferença de {dif})",
        "sem_comparativo": "Reapresentação pelo comparativo do ano seguinte: nenhuma diferença acima da tolerância, ou a DFP do ano seguinte ainda não existia na data.",
        "sabia": "# O que se sabia na data", "qualidade_dados": "# Qualidade dos dados",
        "conferencias": "{n} conferências aplicáveis; {f} com falha.",
        "parecer": "# Parecer e auditor (seção factual; não gera alerta)",
        "tipo_parecer": "Relatório do auditor: {t}.", "trecho": "Trecho conferido literalmente: \"{t}\"",
        "auditores": "Auditor no FCA de {a}: {f}.", "trocas": "Trocas de auditor: {t}.", "sem_trocas": "Trocas de auditor: nenhuma nos FCA entregues até a data.",
        "testado": "# Como o motor foi testado",
        "testado_txt": "No estudo 1, o motor v1 acertou {a} de {n} casos acertáveis, com {x} alarmes por acerto no período inteiro e taxa de alerta de {t} nas empresa-anos não financeiras avaliadas ({doc}).",
        "limites": "# Limites", "limitacoes": "# Limitações", "motor": "# Motor",
        "motor_txt": "{v1}; {v2}. Gerado em {g}.", "pagina": "Página {i} de {n}",
        "evidencias": "Evidências no JSON: {n} linhas da DFP, cada uma com documento, versão, data de entrega, conta e localização.",
        "codigos": {"nao_financeira": "não financeira", "financeira": "financeira", "dados_abertos": "dados abertos", "enet": "ENET",
                    "con": "consolidado", "ind": "individual", "alta": "alta", "media": "média", "baixa": "baixa", "fca": "FCA",
                    "cadastro": "cadastro"},
        "pareceres": {},
    },
    "en": {
        "titulo": "# Investigation: {nome} (CVM code {cd}), fiscal year {ex}, as it was on {data}",
        "empresa": "# Company", "setor": "Sector: {s} (origin: {o}); group: {g}; current registry status: {c}.",
        "documento": "# Document used",
        "doc": "{ex} DFP, version {v}, filed on {r}; origin: {o}; type: {t}; original scale: {e}.",
        "versoes": "Versions known on the date: {v}.", "link": "Document at the CVM: {l}",
        "manipulacao": "# Possible manipulation (engine v1, study 1)",
        "risco": "# Financial risk (context only)", "qualidade": "# Financial quality (context only)",
        "valor": "Value", "alerta": "Alert by the study 1 rule", "regra": "Rule",
        "sim": "yes", "nao": "no", "nao_dispara": "does not trigger alerts",
        "pct_setor": "Percentile in sector and year", "pct_grupo": "Percentile in group and year",
        "historico": "The company's own history", "confianca": "Confidence in the data",
        "alternativas": "Alternative explanations", "no_produto": "In the product",
        "hist_txt": "median {m}; IQR fence from {a} to {b}; value {p} the fence ({n} fiscal years)",
        "posicoes": {"dentro": "inside", "acima": "above", "abaixo": "below"},
        "componentes": "Components", "sinais_f": "Signals",
        "mudancas": "# Changes",
        "destacadas": "Highlighted in the following year's comparative: {n} (threshold of R${lim} million, 1% of total assets of the version used). Values in R$ million:",
        "destacada_linha": "{dem} {cod} {ds}: {v} in the version used (v{ver}, filed on {dt}); {c} in the next DFP's comparative (v{vers}, filed on {dts}); difference of {dif}. {txt}.",
        "sem_destacadas": "Highlighted in the following year's comparative: none.",
        "comparativo": "Full list: {n} accounts above the R${tol} tolerance (group a, totals and key lines: {a}; group b, reclassifications: {b}), in the annex at the end.",
        "anexo": "# Annex: full list of differences in the following year's comparative (R$ million)",
        "comparativo_linha": "({g}) {dem} {cod} {ds}: {v} in the version used, {c} in the comparative (difference of {dif})",
        "sem_comparativo": "Restatement through the following year's comparative: no difference above the tolerance, or the next year's DFP did not exist yet on the date.",
        "sabia": "# What was known on the date", "qualidade_dados": "# Data quality",
        "conferencias": "{n} applicable checks; {f} failed.",
        "parecer": "# Auditor's report and auditor (factual section; no alert)",
        "tipo_parecer": "Auditor's report: {t}.", "trecho": "Excerpt checked literally: \"{t}\"",
        "auditores": "Auditor in the {a} FCA: {f}.", "trocas": "Auditor changes: {t}.", "sem_trocas": "Auditor changes: none in the FCAs filed by the date.",
        "testado": "# How the engine was tested",
        "testado_txt": "In study 1, engine v1 detected {a} of {n} detectable cases, with {x} false alarms per detected case over the whole period and an alert rate of {t} among evaluated non-financial company-years ({doc}).",
        "limites": "# Limits", "limitacoes": "# Limitations", "motor": "# Engine",
        "motor_txt": "{v1}; {v2}. Generated at {g}.", "pagina": "Page {i} of {n}",
        "evidencias": "Evidence in the JSON: {n} DFP lines, each with document, version, filing date, account and location.",
        "codigos": {"nao_financeira": "non-financial", "financeira": "financial", "dados_abertos": "open data", "enet": "ENET",
                    "con": "consolidated", "ind": "individual", "alta": "high", "media": "medium", "baixa": "low", "fca": "FCA",
                    "cadastro": "registry"},
        "pareceres": {"Sem Ressalva": "Sem Ressalva (unqualified)", "Com Ressalva": "Com Ressalva (qualified)",
                      "Adverso": "Adverso (adverse)", "Negativa de Opinião": "Negativa de Opinião (disclaimer of opinion)"},
    },
}  # fmt: skip


def _c(codigo: Any, t: dict[str, Any]) -> str:
    """Código do JSON em texto do idioma (grupo, origem, tipo, nível de confiança)."""
    return str(t["codigos"].get(codigo, codigo)) if codigo is not None else "—"


def _f(v: Any, lang: str, casas: int = 3) -> str:
    return "—" if v is None else decimal(float(v), lang, casas)


def _valor(r: dict[str, Any], lang: str) -> str:
    return _f(r["valor"], lang) if r["status"] == "ok" else str(r["motivo"])


def _pct(p: dict[str, Any] | None, lang: str) -> str:
    if not p:
        return "—"
    if p.get("valor") is None:
        return str(p.get("motivo") or "—")
    txt = f"{decimal(p['valor'], lang, 0)} (n = {inteiro(p['n'], lang)})"
    return f"{txt}; {p['marca']}" if p.get("marca") else txt


def _hist(h: dict[str, Any] | None, t: dict[str, Any], lang: str) -> str:
    if not h:
        return "—"
    if h.get("motivo"):
        return str(h["motivo"])
    a, b = h["cerca"]
    return t["hist_txt"].format(m=_f(h["mediana"], lang), a=_f(a, lang), b=_f(b, lang), p=t["posicoes"][h["posicao"]],
                                n=inteiro(len(h["exercicios"]), lang))  # fmt: skip


def linhas(inv: dict[str, Any]) -> list[str]:
    lang = inv["idioma"]
    t = T[lang]
    emp, ex = inv["empresa"], inv["exercicios"][0]
    out = [t["titulo"].format(nome=emp["denominacao"], cd=emp["cd_cvm"], ex=ex["exercicio"], data=data(inv["data_referencia"], lang)),
           inv["aviso"], "", t["empresa"],
           t["setor"].format(s=emp["setor"] or "—", o=_c(emp["origem_setor"], t), g=_c(emp["grupo"], t), c=emp["situacao_cadastro_atual"]),
           "", t["documento"],
           t["doc"].format(ex=ex["exercicio"], v=ex["versao_usada"], r=data(ex["dt_receb"], lang) if ex["dt_receb"] else "—",
                           o=_c(ex["origem"], t), t=_c(ex["tipo"], t), e=ex["escala_original"] or "—"),
           t["versoes"].format(v="; ".join(f"{x['versao']} ({data(x['dt_receb'], lang)})" for x in ex["versoes_conhecidas"]) or "—")]  # fmt: skip
    if ex.get("link"):
        out.append(t["link"].format(l=ex["link"]))
    out += [f"- {n}" for n in ex["notas"]]
    ach = inv.get("achados", {})
    out += ["", t["manipulacao"]]
    for a in ach.get("possivel_manipulacao", []):
        alerta = t["nao_dispara"] if a["alerta_v1"] is None else t["sim"] if a["alerta_v1"] else t["nao"]
        out += [
            "",
            f"{a['rotulo']} ({a['sinal']})",
            f"  {t['valor']}: {_valor(a['valor'], lang)}",
            f"  {t['alerta']}: {alerta}",
        ]
        if a.get("regra"):
            out.append(f"  {t['regra']}: {a['regra']}")
        if a.get("valor_no_produto"):
            out.append(f"  {t['no_produto']}: {_valor(a['valor_no_produto'], lang)}")
        c = a.get("contexto") or {}
        out += [f"  {t['pct_setor']}: {_pct(c.get('percentil_setor_ano'), lang)}", f"  {t['pct_grupo']}: {_pct(c.get('percentil_grupo_ano'), lang)}",
                f"  {t['historico']}: {_hist(c.get('historico'), t, lang)}", f"  {t['confianca']}: {_c(a['confianca']['nivel'], t)}"]  # fmt: skip
        out += [f"  {t['alternativas']}: {x}" for x in a.get("explicacoes_alternativas", [])]
    for chave, titulo in (("risco_financeiro", "risco"), ("qualidade_financeira", "qualidade")):
        out += ["", t[titulo]]
        for a in ach.get(chave, []):
            out += ["", f"{a['rotulo']}", f"  {t['valor']}: {a['texto'] or _valor(a['valor'], lang)}"]
            comp = a.get("componentes") or {}
            if a["sinal"] == "altman_z2" and comp:
                out.append(f"  {t['componentes']}: " + "; ".join(f"{k} = {_f(v, lang)}" for k, v in comp.items()))
            if a["sinal"] == "piotroski_f" and comp.get("sinais"):
                out.append(
                    f"  {t['sinais_f']}: "
                    + "; ".join(f"{k} = {'—' if v is None else v}" for k, v in comp["sinais"].items())
                )
            c = a.get("contexto") or {}
            if c:
                out += [f"  {t['pct_setor']}: {_pct(c.get('percentil_setor_ano'), lang)}",
                        f"  {t['historico']}: {_hist(c.get('historico'), t, lang)}"]  # fmt: skip
            out += [f"  - {m}" for m in a.get("marcas", [])]
    mud = inv.get("mudancas", {})
    out += ["", t["mudancas"]]
    difs = mud.get("reapresentacao_pelo_comparativo", [])
    mat = mud.get("materialidade_comparativo") or {}
    if difs:
        dest = mud.get("comparativo_destacadas", [])
        if dest:
            out.append(t["destacadas"].format(n=inteiro(len(dest), lang), lim=_f(mat["limite"] / 1e6, lang, 1)))
            out += ["  " + t["destacada_linha"].format(dem=x["demonstracao"], cod=x["cd_conta"], ds=x["ds_conta"],
                                                       v=_f(x["valor"] / 1e6, lang, 1), ver=x["versao"], dt=data(x["dt_receb"], lang),
                                                       c=_f(x["valor_comparativo"] / 1e6, lang, 1), vers=x["versao_seguinte"],
                                                       dts=data(x["dt_receb_seguinte"], lang), dif=_f(x["diferenca"] / 1e6, lang, 1),
                                                       txt=x["texto"][:1].upper() + x["texto"][1:])
                    for x in dest]  # fmt: skip
        else:
            out.append(t["sem_destacadas"])
        out.append(mat.get("texto", ""))
        out.append(t["comparativo"].format(n=inteiro(len(difs), lang), tol=inteiro(int(mud["tolerancia_comparativo"]), lang),
                                           a=inteiro(sum(x["grupo"] == "a" for x in difs), lang),
                                           b=inteiro(sum(x["grupo"] == "b" for x in difs), lang)))  # fmt: skip
    else:
        out.append(t["sem_comparativo"])
    sabia = inv.get("o_que_se_sabia", {})
    out += ["", t["sabia"]] + [
        f"- {x['tipo']} {x['exercicio']}, v{x['versao']}: {data(x['dt_receb'], lang)}"
        for x in sabia.get("documentos", [])
    ]
    out.append(sabia.get("nota", ""))
    confs = [c for c in inv.get("qualidade_dos_dados", {}).get("conferencias", []) if c["resultado"] != "nao_aplicavel"]
    falhas = [c for c in confs if c["resultado"] == "falhou"]
    out += [
        "",
        t["qualidade_dados"],
        t["conferencias"].format(n=inteiro(len(confs), lang), f=inteiro(len(falhas), lang)),
    ]
    out += [f"- {c['nome']} ({c['coluna']}): {c['motivo'] or ''}" for c in falhas]
    pa = inv.get("parecer_e_auditor") or {}
    out += ["", t["parecer"]]
    rel = pa.get("relatorio_do_auditor") or {}
    if rel.get("tipo"):
        out.append(t["tipo_parecer"].format(t=", ".join(t["pareceres"].get(x, x) for x in rel["tipo"])))
    if rel.get("trecho"):
        out.append(t["trecho"].format(t=rel["trecho"]))
    if rel.get("motivo"):
        out.append(str(rel["motivo"]))
    for f in pa.get("auditores_no_fca", [])[-3:]:
        out.append(t["auditores"].format(a=f["ano_fca"], f=", ".join(x["auditor"] for x in f["auditores"])))
    trocas = pa.get("trocas_de_auditor")
    if trocas is not None:
        out.append(t["trocas"].format(t="; ".join(f"{x['ano_fca']}: {', '.join(x['de'])} -> {', '.join(x['para'])}" for x in trocas))
                   if trocas else t["sem_trocas"])  # fmt: skip
        out += [f"  {x['ano_fca']}: {s['nota']}" for x in trocas for s in x.get("saidas", [])]
    if pa.get("rodizio"):
        out.append(pa["rodizio"]["nota"])
    mt = inv.get("como_o_motor_foi_testado", {})
    if mt:
        out += ["", t["testado"], t["testado_txt"].format(a=inteiro(mt["acertados"], lang), n=inteiro(mt["acertaveis"], lang),
                                                          x=_f(mt["alarmes_por_acerto_periodo_inteiro"], lang, 1),
                                                          t=pct(mt["taxa_de_alerta_nao_financeiras"], lang), doc=mt["documento"])]  # fmt: skip
    out += ["", t["limites"]] + [f"- {x}" for x in inv.get("limites", [])]
    out += ["", t["limitacoes"]] + [f"- {x}" for x in inv.get("limitacoes", [])]
    out += ["", t["evidencias"].format(n=inteiro(len(inv.get("evidencias", {})), lang))]
    out += ["", t["motor"], t["motor_txt"].format(v1=inv["motor"]["v1"], v2=inv["motor"]["v2"], g=inv["gerado_em"])]
    if difs:
        out += ["", t["anexo"]]
        out += [t["comparativo_linha"].format(g=x["grupo"], dem=x["demonstracao"], cod=x["cd_conta"], ds=x["ds_conta"],
                                              v=_f(x["valor"] / 1e6, lang, 1), c=_f(x["valor_comparativo"] / 1e6, lang, 1),
                                              dif=_f(x["diferenca"] / 1e6, lang, 1)) for x in difs]  # fmt: skip
    return out


def gerar(inv: dict[str, Any]) -> bytes:
    t = T[inv["idioma"]]
    paginas = paginar(linhas(inv))
    n = len(paginas)
    rodapes = [[inv["aviso"], t["pagina"].format(i=i, n=n)] for i in range(1, n + 1)]
    return gerar_pdf(paginas, rodapes)
