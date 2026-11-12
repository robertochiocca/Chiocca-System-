"""PDF da investigação, gerado só do JSON (`chiocca.v2.investigacao`): texto e tabelas, nas duas línguas.

O PDF não recalcula nada: cada número sai do JSON, formatado no idioma dele. Toda página leva o aviso fixo e o número
da página (`chiocca.v2.pdf_simples`, gerador sem dependência e determinístico: o mesmo JSON dá os mesmos bytes).
"""

from __future__ import annotations

import re
from typing import Any

from chiocca.formato import data
from chiocca.v2 import leitura_exibicao
from chiocca.v2.contexto import ROTULOS_F
from chiocca.v2.exibicao import com_sinal_de_menos, decimal, inteiro, pct
from chiocca.v2.pdf_simples import gerar_pdf, paginar

T: dict[str, dict[str, Any]] = {
    "pt": {
        "titulo": "# Investigação: {nome} (código CVM {cd}), exercício {ex}, como era em {data}",
        "empresa": "# Empresa", "setor": "Setor: {s} (origem: {o}); grupo: {g}.",
        "negociacao": "Códigos de negociação (FCA de {a}, versão {v}, entregue em {r}): {c}.", "negociacao_item": "{c} ({vm}, {m}, desde {i})",
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
        "hist_txt": "mediana {m}; faixa de Tukey (1,5 × IQR): de {a} a {b}; valor {p} da faixa ({u}{n} exercícios)",
        "posicoes": {"dentro": "dentro", "acima": "acima", "abaixo": "abaixo"},
        "componentes": "Componentes", "sinais_f": "Sinais", "indices": "índices",
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
        "auditores": "Auditor no FCA de {a}: {f}.", "trocas": "Trocas de auditor (uma linha por troca, nome canônico pelo código da firma na CVM):",
        "sem_trocas": "Trocas de auditor: nenhuma nos FCA entregues até a data.",
        "troca": "{a}: {de} → {para}{tr}.", "transicao": " (transição: duas firmas no FCA de {x})",
        "so_entrada": "{a}: entrada de {para}, sem saída de outra firma.", "so_saida": "{a}: saída de {de}, sem entrada de outra firma.",
        "hoje": "Situação no cadastro: {s}. Fonte: {f}.",
        "hoje_nome": "Nome no cadastro de hoje: {n}.",
        "nome_anterior": "Antes de {a}, a companhia se chamava {n}.",
        "testado": "# Como o motor foi testado",
        "testado_txt": "No estudo 1, o motor v1 acertou {a} de {n} casos acertáveis, com {x} alarmes por acerto no período inteiro e taxa de alerta de {t} nas empresa-anos não financeiras avaliadas ({doc}).",
        "limites": "# Limites", "limitacoes": "# Limitações", "motor": "# Motor",
        "motor_txt": "{m}. Gerado em {g}.", "pagina": "Página {i} de {n}",
        "evidencias": "Evidências no JSON: {n} linhas da DFP, cada uma com documento, versão, data de entrega, conta e localização.",
        "codigos": {"nao_financeira": "não financeira", "financeira": "financeira", "dados_abertos": "dados abertos", "enet": "ENET",
                    "DFC_MI": "DFC (método indireto)", "DFC_MD": "DFC (método direto)",
                    "con": "consolidado", "ind": "individual", "alta": "alta", "media": "média", "baixa": "baixa", "fca": "FCA",
                    "cadastro": "cadastro"},
        "pareceres": {},
    },
    "en": {
        "titulo": "# Investigation: {nome} (CVM code {cd}), fiscal year {ex}, as it was on {data}",
        "empresa": "# Company", "setor": "Sector: {s} (origin: {o}); group: {g}.",
        "negociacao": "Trading codes ({a} FCA, version {v}, filed on {r}): {c}.", "negociacao_item": "{c} ({vm}, {m}, since {i})",
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
        "hist_txt": "median {m}; Tukey range (1.5 × IQR): from {a} to {b}; value {p} the range ({u}{n} fiscal years)",
        "posicoes": {"dentro": "inside", "acima": "above", "abaixo": "below"},
        "componentes": "Components", "sinais_f": "Signals", "indices": "indices",
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
        "auditores": "Auditor in the {a} FCA: {f}.", "trocas": "Auditor changes (one line per change, canonical name by the firm's CVM code):",
        "sem_trocas": "Auditor changes: none in the FCAs filed by the date.",
        "troca": "{a}: {de} → {para}{tr}.", "transicao": " (transition: two firms in the {x} FCA)",
        "so_entrada": "{a}: entry of {para}, with no other firm leaving.", "so_saida": "{a}: exit of {de}, with no other firm entering.",
        "hoje": "Registry status: {s}. Source: {f}.",
        "hoje_nome": "Name in today's registry: {n}.",
        "nome_anterior": "Before {a}, the company was called {n}.",
        "testado": "# How the engine was tested",
        "testado_txt": "In study 1, engine v1 detected {a} of {n} detectable cases, with {x} false alarms per detected case over the whole period and an alert rate of {t} among evaluated non-financial company-years ({doc}).",
        "limites": "# Limits", "limitacoes": "# Limitations", "motor": "# Engine",
        "motor_txt": "{m}. Generated at {g}.", "pagina": "Page {i} of {n}",
        "evidencias": "Evidence in the JSON: {n} DFP lines, each with document, version, filing date, account and location.",
        "codigos": {"nao_financeira": "non-financial", "financeira": "financial", "dados_abertos": "open data", "enet": "ENET",
                    "DFC_MI": "DFC (indirect method)", "DFC_MD": "DFC (direct method)",
                    "con": "consolidated", "ind": "individual", "alta": "high", "media": "medium", "baixa": "low", "fca": "FCA",
                    "cadastro": "registry"},
        "pareceres": {"Sem Ressalva": "Sem Ressalva (unqualified)", "Com Ressalva": "Com Ressalva (qualified)",
                      "Adverso": "Adverso (adverse)", "Negativa de Opinião": "Negativa de Opinião (disclaimer of opinion)"},
    },
}  # fmt: skip


def _c(codigo: Any, t: dict[str, Any]) -> str:
    """Código do JSON em texto do idioma (grupo, origem, tipo, demonstração, nível de confiança)."""
    return str(t["codigos"].get(codigo, codigo)) if codigo is not None else "—"


def _f(v: Any, lang: str, casas: int = 3) -> str:
    return "—" if v is None else decimal(float(v), lang, casas)


INDICE = ("índice", "index")


def _n(v: Any, unidade: str, lang: str) -> str:
    """Número com a unidade: dias (1 casa), p.p. (2 casas); índice (3 casas) leva a unidade no fim da linha."""
    if v is None:
        return "—"
    if unidade in INDICE:
        return decimal(float(v), lang, 3)
    return f"{decimal(float(v), lang, 1 if unidade in ('dias', 'days') else 2)} {unidade}"


def _sufixo(unidade: str) -> str:
    return f" ({unidade})" if unidade in INDICE else ""


def _valor(r: dict[str, Any], lang: str, unidade: str = "índice") -> str:
    return _n(r["valor"], unidade, lang) + _sufixo(unidade) if r["status"] == "ok" else str(r["motivo"])


def _pct(p: dict[str, Any] | None, lang: str) -> str:
    if not p:
        return "—"
    if p.get("valor") is None:
        return str(p.get("motivo") or "—")
    txt = f"{decimal(p['valor'], lang, 0)} (n = {inteiro(p['n'], lang)})"
    return f"{txt}; {p['marca']}" if p.get("marca") else txt


def _hist(h: dict[str, Any] | None, t: dict[str, Any], lang: str, unidade: str) -> str:
    if not h:
        return "—"
    if h.get("motivo"):
        return str(h["motivo"])
    a, b = h["faixa_tukey"]
    u = f"{unidade}; " if unidade in INDICE else ""
    return t["hist_txt"].format(m=_n(h["mediana"], unidade, lang), a=_n(a, unidade, lang), b=_n(b, unidade, lang),
                                p=t["posicoes"][h["posicao"]], u=u, n=inteiro(len(h["exercicios"]), lang))  # fmt: skip


def _maiusculas(linhas: list[str]) -> list[str]:
    """Itens de lista com inicial maiúscula (pedido de 09/11/2026)."""
    out = []
    for x in linhas:
        corpo = x.lstrip()
        if corpo.startswith("- ") and len(corpo) > 2:
            recuo = x[: len(x) - len(corpo)]
            x = f"{recuo}- {corpo[2:3].upper()}{corpo[3:]}"
        out.append(x)
    return out


def linhas(inv: dict[str, Any]) -> list[str]:
    lang = inv["idioma"]
    t = T[lang]
    emp, ex = inv["empresa"], inv["exercicios"][0]
    out = [t["titulo"].format(nome=emp["denominacao"], cd=emp["cd_cvm"], ex=ex["exercicio"], data=data(inv["data_referencia"], lang)),
           inv["aviso"], "", t["empresa"],
           t["setor"].format(s=emp["setor"] or "—", o=_c(emp["origem_setor"], t), g=_c(emp["grupo"], t)),
           *[t["nome_anterior"].format(a=x["ate_ano"], n=x["nome"]) for x in reversed(emp.get("nomes_anteriores", []))],
           *_codigos(emp, t, lang), "", t["documento"],
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
        u = a["unidade"]
        out += ["", f"{a['rotulo']}", f"  {t['valor']}: {_valor(a['valor'], lang, u)}"]  # o rótulo, sem o código
        if a.get("componente_de"):  # componente do M-score: não tem regra nem alerta próprios
            out.append(f"  {a['regra']}")
        else:
            out.append(f"  {t['alerta']}: {alerta}")
            if a.get("regra"):
                out.append(f"  {t['regra']}: {a['regra']}")
        if a.get("valor_no_produto"):
            out.append(f"  {t['no_produto']}: {_valor(a['valor_no_produto'], lang, u)}")
        c = a.get("contexto") or {}
        out += [f"  {t['pct_setor']}: {_pct(c.get('percentil_setor_ano'), lang)}", f"  {t['pct_grupo']}: {_pct(c.get('percentil_grupo_ano'), lang)}",
                f"  {t['historico']}: {_hist(c.get('historico'), t, lang, u)}", f"  {t['confianca']}: {_c(a['confianca']['nivel'], t)}"]  # fmt: skip
        out += [f"  {t['alternativas']}: {x}" for x in a.get("explicacoes_alternativas", [])]
    for chave, titulo in (("risco_financeiro", "risco"), ("qualidade_financeira", "qualidade")):
        out += ["", t[titulo]]
        for a in ach.get(chave, []):
            out += ["", f"{a['rotulo']}", f"  {t['valor']}: {a['texto'] or _valor(a['valor'], lang, a['unidade'])}"]
            comp = a.get("componentes") or {}
            if a["sinal"] == "altman_z2" and comp:
                out.append(
                    f"  {t['componentes']}: "
                    + "; ".join(f"{k} = {_f(v, lang)}" for k, v in comp.items())
                    + f" ({t['indices']})"
                )
            if a["sinal"] == "piotroski_f" and comp.get("sinais"):
                k = 0 if lang == "pt" else 1
                out.append(f"  {t['sinais_f']}:")
                out += [f"    - {ROTULOS_F[s][k] if s in ROTULOS_F else s}: {'—' if v is None else v}"
                        for s, v in comp["sinais"].items()]  # fmt: skip
            c = a.get("contexto") or {}
            if c:
                out += [f"  {t['pct_setor']}: {_pct(c.get('percentil_setor_ano'), lang)}",
                        f"  {t['historico']}: {_hist(c.get('historico'), t, lang, a['unidade'])}"]  # fmt: skip
            out += [f"  - {m}" for m in a.get("marcas", [])]
    mud = inv.get("mudancas", {})
    out += ["", t["mudancas"]]
    difs = mud.get("reapresentacao_pelo_comparativo", [])
    mat = mud.get("materialidade_comparativo") or {}
    if difs:
        dest = mud.get("comparativo_destacadas", [])
        if dest:
            out.append(t["destacadas"].format(n=inteiro(len(dest), lang), lim=_f(mat["limite"] / 1e6, lang, 1)))
            out += ["  " + t["destacada_linha"].format(dem=_c(x["demonstracao"], t), cod=x["cd_conta"], ds=x["ds_conta"],
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
        out.append(t["trocas"] if trocas else t["sem_trocas"])
        out += [f"- {_troca(x, t)}" for x in trocas]
    if pa.get("rodizio"):
        out.append(pa["rodizio"]["nota"])
    if inv.get("leitura_documental"):  # Fase F1: só com o leitor aprovado nos casos guardados
        out += _leitura(inv, lang)
    mt = inv.get("como_o_motor_foi_testado", {})
    if mt:
        out += ["", t["testado"], t["testado_txt"].format(a=inteiro(mt["acertados"], lang), n=inteiro(mt["acertaveis"], lang),
                                                          x=_f(mt["alarmes_por_acerto_periodo_inteiro"], lang, 1),
                                                          t=pct(mt["taxa_de_alerta_nao_financeiras"], lang), doc=mt["documento"])]  # fmt: skip
    out += ["", t["limites"]] + [f"- {x}" for x in inv.get("limites", [])]
    out += ["", t["limitacoes"]] + [f"- {x}" for x in inv.get("limitacoes", [])]
    out += ["", t["evidencias"].format(n=inteiro(len(inv.get("evidencias", {})), lang))]
    motor = "; ".join(x for x in (inv["motor"]["v1"], inv["motor"]["v2"], inv["motor"].get("leitor")) if x)
    out += ["", t["motor"], t["motor_txt"].format(m=motor, g=inv["gerado_em"])]
    hoje = inv.get("informacao_de_hoje")
    if hoje:  # fora da visão "como era": seção separada no fim
        out += ["", f"# {hoje['titulo']}", t["hoje"].format(s=hoje["situacao_cadastro"] or "—", f=hoje["fonte"])]
        if hoje.get("denominacao"):
            out.append(t["hoje_nome"].format(n=hoje["denominacao"]))
    if difs:
        out += ["", t["anexo"]]
        out += [t["comparativo_linha"].format(g=x["grupo"], dem=_c(x["demonstracao"], t), cod=x["cd_conta"], ds=x["ds_conta"],
                                              v=_f(x["valor"] / 1e6, lang, 1), c=_f(x["valor_comparativo"] / 1e6, lang, 1),
                                              dif=_f(x["diferenca"] / 1e6, lang, 1)) for x in difs]  # fmt: skip
    return _sem_delta(_sem_ponto_duplo(_maiusculas(out)))


_DELTA = re.compile(r"\s*\(Δ[A-Z_]+\)")
_PONTO_DUPLO = re.compile(r"(?<!\.)\.\.$")


def _sem_delta(linhas: list[str]) -> list[str]:
    """Sem o Δ no PDF (pedido de 11/11/2026): a fonte Symbol não vai embutida e cada leitor de PDF a substitui de um
    jeito, e o Δ saía em branco. Sai a sigla entre parênteses: "Variação do ROA (ΔROA)" vira "Variação do ROA". A tela
    mantém o Δ. Os trechos copiados dos documentos (entre aspas) ficam como vieram."""
    return [x if "“" in x else _DELTA.sub("", x) for x in linhas]


def _sem_ponto_duplo(linhas: list[str]) -> list[str]:
    """Frase que termina num nome com ponto ("AMERICANAS S.A.") não ganha outro ponto."""
    return [x if "“" in x else _PONTO_DUPLO.sub(".", x) for x in linhas]


LEITURA: dict[str, dict[str, Any]] = {
    "pt": {"titulo": "# Trechos dos documentos (copiados; não gera alerta)", "notas": "Notas explicativas",
           "partes": "Notas explicativas · Partes relacionadas", "nota": "Nota: {t} (páginas {a} a {b})",
           "campos": "Campos do item 18 do CPC 05 (R1)", "condicoes": "Condições de mercado",
           "risco": "Notas explicativas · Risco sacado e forfait", "relatorio": "Relatório do auditor",
           "tipo": "Tipo de opinião: {t}", "formulario": "Formulário de Referência", "pagina": "p. {p}",
           "negativa": "menção negativa", "cortado": "cortado no fim da frase", "original": "",
           "omitidos": "Trecho omitido; ver página {p} do documento", "omitidos_sem_pagina": "Trecho omitido; ver o "
           "relatório do auditor no documento", "n_trechos": " ({n} trechos)",
           "testado": "Como o leitor foi testado: {n} casos guardados, medida única com o leitor congelado ({c}): "
                      "precisão {p}, cobertura {cob}, conferência literal em {a} de {b} trechos, {nomes} ({doc}).",
           "sem_nomes": "nenhum nome de pessoa física", "com_nomes": "{n} nomes de pessoa física",
           "limites": "Limites desta seção:",
           "fre": {"sem_linhas": "O Formulário de Referência não traz transações com partes relacionadas na tabela.",
                   "nao_disponivel_na_data": "O Formulário de Referência deste exercício não estava disponível na data.",
                   "sem_formulario": "Não há Formulário de Referência deste exercício nos dados abertos."},
           "fre_doc": "Formulário de {a}, versão {v}, entregue em {d}.",
           "linhagem": "É a única versão disponível nos dados abertos; as versões anteriores não estão lá."},
    "en": {"titulo": "# Document excerpts (copied; no alert)", "notas": "Explanatory notes",
           "partes": "Explanatory notes · Related parties", "nota": "Note: {t} (pages {a} to {b})",
           "campos": "Fields of item 18 of CPC 05 (R1)", "condicoes": "Market terms",
           "risco": "Explanatory notes · Reverse factoring and forfaiting", "relatorio": "Auditor's report",
           "tipo": "Type of opinion: {t}", "formulario": "Reference Form", "pagina": "p. {p}",
           "negativa": "negative mention", "cortado": "cut at the end of a sentence",
           "original": "original excerpt in Portuguese",
           "omitidos": "Excerpt omitted; see page {p} of the document", "omitidos_sem_pagina": "Excerpt omitted; see "
           "the auditor's report in the document", "n_trechos": " ({n} excerpts)",
           "testado": "How the reader was tested: {n} held-out cases, a single measurement with the frozen reader ({c}): "
                      "precision {p}, coverage {cob}, literal check on {a} of {b} excerpts, {nomes} ({doc}).",
           "sem_nomes": "no natural-person name", "com_nomes": "{n} natural-person names",
           "limites": "Limits of this section:",
           "fre": {"sem_linhas": "The Reference Form lists no related-party transactions in the table.",
                   "nao_disponivel_na_data": "The Reference Form for this fiscal year was not available on the date.",
                   "sem_formulario": "There is no Reference Form for this fiscal year in the open data."},
           "fre_doc": "Form of {a}, version {v}, filed on {d}.",
           "linhagem": "It is the only version available in the open data; earlier versions are not there."},
}  # fmt: skip
ROTULOS_LEITURA = {
    "pt": {"controladora": "controladora", "controle_conjunto_ou_influencia": "controle conjunto ou influência significativa",
           "controladas": "controladas", "coligadas": "coligadas", "joint_ventures": "joint ventures",
           "pessoal_chave": "pessoal-chave da administração", "outras_partes": "outras partes relacionadas",
           "montante": "montante das transações", "saldos": "saldos", "termos_e_condicoes": "termos e condições",
           "garantias": "garantias", "provisao_pcld": "provisão para créditos de liquidação duvidosa",
           "perdas_incobraveis": "dívidas incobráveis", "base_para_ressalva": "base para a opinião", "enfase": "ênfase",
           "incerteza_continuidade": "incerteza sobre a continuidade operacional",
           "principais_assuntos": "principais assuntos de auditoria", "outros_assuntos": "outros assuntos"},
    "en": {"controladora": "parent company", "controle_conjunto_ou_influencia": "joint control or significant influence",
           "controladas": "subsidiaries", "coligadas": "associates", "joint_ventures": "joint ventures",
           "pessoal_chave": "key management personnel", "outras_partes": "other related parties",
           "montante": "amount of the transactions", "saldos": "balances", "termos_e_condicoes": "terms and conditions",
           "garantias": "guarantees", "provisao_pcld": "allowance for doubtful debts", "perdas_incobraveis": "bad debts",
           "base_para_ressalva": "basis for the opinion", "enfase": "emphasis of matter",
           "incerteza_continuidade": "material uncertainty related to going concern",
           "principais_assuntos": "key audit matters", "outros_assuntos": "other matters"},
}  # fmt: skip
TIPOS_OPINIAO = {"pt": {"sem_ressalva": "sem ressalva", "com_ressalva": "com ressalva", "adversa": "adversa",
                        "abstencao": "abstenção de opinião"},
                 "en": {"sem_ressalva": "unqualified", "com_ressalva": "qualified", "adversa": "adverse",
                        "abstencao": "disclaimer of opinion"}}  # fmt: skip


def frase(x: str) -> str:
    """Texto de motivo como frase: inicial maiúscula e ponto no fim."""
    x = x.strip()
    return x[:1].upper() + x[1:] + ("" if x.endswith((".", "!", "?")) else ".") if x else x


def _trechos(xs: list[dict[str, Any]], t: dict[str, Any], lang: str) -> list[str]:
    """Os trechos de um bloco, agrupados para mostrar (chiocca/v2/leitura_exibicao.py): rótulos juntos no mesmo trecho;
    omitidos da mesma página numa linha só, com a contagem."""
    out = []
    for g in leitura_exibicao.agrupa(xs):
        if g["omitido"]:
            linha = t["omitidos"].format(p=g["pagina"]) if g["pagina"] is not None else t["omitidos_sem_pagina"]
            out.append(f"- {linha}" + (t["n_trechos"].format(n=inteiro(g["n"], lang)) if g["n"] > 1 else ""))
            continue
        onde = [t["pagina"].format(p=g["pagina"])] if g["pagina"] is not None else []
        marcas = (onde + ([t["negativa"]] if g["negacao"] else []) + ([t["cortado"]] if g["cortado"] else [])
                  + ([t["original"]] if t["original"] else []))  # fmt: skip
        rotulos = "; ".join(ROTULOS_LEITURA[lang].get(r, r) for r in g["rotulos"])
        prefixo = f"[{rotulos}] " if rotulos else ""
        out.append(f"- {prefixo}“{g['texto']}”" + (f" ({', '.join(marcas)})" if marcas else ""))
    return out


def _testado(mt: dict[str, Any], t: dict[str, Any], lang: str) -> str:
    nomes = t["sem_nomes"] if mt["nomes_vazados"] == 0 else t["com_nomes"].format(n=inteiro(mt["nomes_vazados"], lang))
    return t["testado"].format(n=inteiro(mt["casos"], lang), c=mt["commit"], p=decimal(mt["precisao"], lang, 3),
                               cob=decimal(mt["cobertura"], lang, 3), a=inteiro(mt["trechos_conferidos"], lang),
                               b=inteiro(mt["trechos_mostrados"], lang), nomes=nomes, doc=mt["documento"])  # fmt: skip


def _leitura(inv: dict[str, Any], lang: str) -> list[str]:
    """A seção de trechos dos documentos no PDF: só fato, os trechos como vieram (literais), sem selo nem alerta."""
    t = LEITURA[lang]
    ld = inv["leitura_documental"]
    pr, rs, rel, fre = (
        ld["partes_relacionadas"],
        ld["risco_sacado"],
        ld["relatorio_do_auditor"],
        ld["formulario_de_referencia"],
    )
    out = ["", t["titulo"], ld["nota"]]
    if inv.get("como_o_leitor_foi_testado"):
        out.append(_testado(inv["como_o_leitor_foi_testado"], t, lang))
    out += ["", t["partes"]]
    if pr.get("motivo"):
        out.append(frase(pr["motivo"]))
    if pr.get("nota"):
        out.append(t["nota"].format(t=pr["nota"]["titulo"], a=pr["nota"]["paginas"][0], b=pr["nota"]["paginas"][1]))
    out += _trechos(pr["trechos"], t, lang)
    if pr["campos_cpc05_18"]:
        out += [t["campos"]] + _trechos(pr["campos_cpc05_18"], t, lang)
    if pr["condicoes_de_mercado"]:
        out += [t["condicoes"]] + _trechos(pr["condicoes_de_mercado"], t, lang) + [pr["nota_condicoes"]]
    out += ["", t["risco"]] + ([frase(rs["motivo"])] if rs.get("motivo") else []) + _trechos(rs["trechos"], t, lang)
    if rs.get("nota"):
        out.append(rs["nota"])
    out += ["", t["relatorio"]] + ([frase(rel["motivo"])] if rel.get("motivo") else [])
    if rel.get("tipo"):
        out.append(t["tipo"].format(t=TIPOS_OPINIAO[lang].get(rel["tipo"], rel["tipo"])))
    out += _trechos(rel["trechos"], t, lang)
    out += ["", t["formulario"]]
    doc = fre.get("documento") or {}
    if doc.get("versao") is not None and fre["status"] in ("disponivel", "sem_linhas"):
        out.append(t["fre_doc"].format(a=fre["ano_formulario"], v=doc["versao"], d=data(doc["dt_receb"], lang)))
    texto_fre = (
        [t["fre"][fre["status"]]]
        if fre["status"] in t["fre"]
        else ([frase(fre["motivo"])] if fre.get("motivo") else [])
    )
    if doc.get("linhagem"):
        texto_fre.append(t["linhagem"])
    if texto_fre:
        out.append(" ".join(texto_fre))
    # montante e saldo vêm do arquivo da CVM com hífen no lugar do sinal de menos: na exibição, o sinal de menos
    out += [f"- {x['parte']} · {x['relacao'] or '—'} · {x['objeto'] or '—'} · "
            f"{com_sinal_de_menos(x['montante'] or '—')} · {com_sinal_de_menos(x['saldo'] or '—')}"
            for x in fre["linhas"]]  # fmt: skip
    if inv.get("limites_da_leitura"):
        out += ["", t["limites"]] + [f"- {x}" for x in inv["limites_da_leitura"]]
    return out


def _troca(x: dict[str, Any], t: dict[str, Any]) -> str:
    if x["de"] is None:
        linha = t["so_entrada"].format(a=x["ano_fca"], para=x["para"])
    elif x["para"] is None:
        linha = t["so_saida"].format(a=x["ano_fca"], de=x["de"])
    else:
        tr = t["transicao"].format(x=x["transicao_fca"]) if x["transicao_fca"] else ""
        linha = t["troca"].format(a=x["ano_fca"], de=x["de"], para=x["para"], tr=tr)
    return f"{linha} {x['saida']['nota']}" if x.get("saida") else linha


def _codigos(emp: dict[str, Any], t: dict[str, Any], lang: str) -> list[str]:
    cods = emp.get("codigos_negociacao") or []
    if not cods:
        return [emp["motivo_codigos_negociacao"]] if emp.get("motivo_codigos_negociacao") else []
    f = cods[0]["fca"]
    lista = "; ".join(t["negociacao_item"].format(c=x["codigo"], vm=x["valor_mobiliario"] or "—", m=x["mercado"] or "—",
                                         i=data(x["inicio_negociacao"], lang) if x["inicio_negociacao"] else "—")
                      for x in cods)  # fmt: skip
    return [t["negociacao"].format(a=f["ano"], v=f["versao"], r=data(f["dt_receb"], lang), c=lista)]


def gerar(inv: dict[str, Any]) -> bytes:
    t = T[inv["idioma"]]
    paginas = paginar(linhas(inv))
    n = len(paginas)
    rodapes = [[inv["aviso"], t["pagina"].format(i=i, n=n)] for i in range(1, n + 1)]
    return gerar_pdf(paginas, rodapes)
