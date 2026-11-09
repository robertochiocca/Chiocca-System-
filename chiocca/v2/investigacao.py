"""Investigação por empresa (Fase C2, segunda parte): o JSON do contrato (`docs/contratos.md`, seção 2, Investigacao).

Uma empresa, um exercício, uma data de referência e um idioma. Monta, sem mudar nenhum valor do motor v1:
- `exercicios`: a leitura da DFP como era na data (`chiocca.v2.na_data.exercicio_na_data`);
- `achados`, por família e nunca somados: possível manipulação (motor v1, com a regra e o alerta do estudo 1, contexto,
  confiança e linhagem), risco financeiro (Altman Z'', sem zonas) e qualidade financeira (Piotroski F, "x/9");
- `mudancas` (versões conhecidas na data e reapresentação pelo comparativo do ano seguinte), `o_que_se_sabia`,
  `qualidade_dos_dados`, `parecer_e_auditor` (seção factual), `como_o_motor_foi_testado`, `limites` (texto fixo) e
  `limitacoes`.
Linguagem do projeto: alerta, não acusação. Toda saída leva o aviso fixo.

Uso: python -m chiocca.v2.investigacao <cd_cvm> <exercicio> <AAAA-MM-DD> [pt|en] [--pdf]
"""

from __future__ import annotations

import hashlib
import json
import re
import sys
from datetime import date, datetime, timezone
from typing import Any

import pandas as pd

from chiocca import base, variaveis
from chiocca.formato import decimal
from chiocca.sinais.mscore import COEFICIENTES
from chiocca.sinais.resultado import Resultado as ResultadoV1
from chiocca.sinais_amostra import CORTE_M, SPREAD_PP
from chiocca.v2 import comparativo, confianca, contexto, limites
from chiocca.v2 import conferencias as cf
from chiocca.v2.lacre import ULTIMO_EXERCICIO_LIBERADO, garantir_data_referencia, garantir_liberado
from chiocca.v2.linhagem import (
    FORMULAS,
    LIMITACOES,
    MOTOR_V1,
    ROTULOS,
    Evidencia,
    Localizador,
    aplicar_nao_preenchido,
    ficha_v1,
)
from chiocca.v2.na_data import FontesV1, corte_transversal_completo, exercicio_na_data, sinais_da_empresa
from chiocca.v2.validade import Motivo, Resultado, de_resultado_v1

AVISO = {
    "pt": "Sinal estatístico baseado em demonstrações públicas. Não é acusação, não é recomendação de investimento.",
    "en": "Statistical signal based on public financial statements. Not an accusation, not investment advice.",
}
MOTOR_V2 = "chiocca.v2 (Fase C2)"
SINAIS_NF = ["mscore", *COEFICIENTES, "dpo", "juro", "lucro_sem_caixa"]
ALERTA = {
    "mscore": "alerta_mscore",
    "dpo": "alerta_dpo",
    "juro": "alerta_juro",
    "peso_nao_recorrente": "alerta_peso_nao_recorrente",
}
ANOS_HISTORICO = 5
# Rodízio de auditor (pedido de 09/11/2026), conferido no texto publicado pela CVM em 09/11/2026: Resolução CVM nº 23,
# de 25/02/2021, arts. 31 e 31-A, em vigor desde 01/04/2021 (art. 41); revogou a Instrução CVM nº 308/1999 (art. 40, I),
# que tinha a regra equivalente nos seus arts. 31 e 31-A. Troca de auditor é fato, não alerta.
RODIZIO_FONTE = "https://conteudo.cvm.gov.br/export/sites/cvm/legislacao/resolucoes/anexos/001/resol023.pdf"
RODIZIO_PRAZOS = {
    5: "art. 31",
    10: "art. 31-A",
}  # fim do prazo: cinco exercícios; até dez com CAE e auditor pessoa jurídica
RODIZIO_VIGENCIA = "2021-04-01"
RODIZIO_NORMAS = {True: "Resolução CVM nº 23/2021", False: "Instrução CVM nº 308/1999"}
RODIZIO_NORMAS_EN = {
    "Resolução CVM nº 23/2021": "CVM Resolution No. 23/2021",
    "Instrução CVM nº 308/1999": "CVM Instruction No. 308/1999",
}
RODIZIO = Motivo(
    "Rodízio de auditor: pela Resolução CVM nº 23/2021, art. 31, o mesmo auditor independente não pode prestar serviços a um mesmo cliente por mais de cinco exercícios sociais consecutivos, com intervalo mínimo de três exercícios sociais para a recontratação; pelo art. 31-A, o prazo é de até dez exercícios sociais consecutivos quando a companhia tem Comitê de Auditoria Estatutário em funcionamento permanente e o auditor é pessoa jurídica. A Resolução está em vigor desde 01/04/2021 (art. 41); antes, a regra equivalente estava nos arts. 31 e 31-A da Instrução CVM nº 308/1999, revogada pela Resolução (art. 40, I). Troca de auditor é fato, não alerta.",
    "Auditor rotation: under CVM Resolution No. 23/2021, art. 31, the same independent auditor may not serve the same client for more than five consecutive fiscal years, with a minimum interval of three fiscal years before being hired again; under art. 31-A, the term is up to ten consecutive fiscal years when the company has a statutory audit committee in permanent operation and the auditor is a firm. The Resolution has been in force since 2021-04-01 (art. 41); before that, the equivalent rule was in arts. 31 and 31-A of CVM Instruction No. 308/1999, revoked by the Resolution (art. 40, I). A change of auditor is a fact, not an alert.",
)
ALTERNATIVAS = {
    "juro": Motivo("dívida cara, variação cambial e juros de arrendamento dentro da despesa financeira (decisão de 07/11/2026)",
                   "expensive debt, exchange differences and lease interest inside finance costs (decision of 2026-11-07)"),
    "dpo": Motivo("poder de negociação com fornecedores e mudança de mix de compras (decisão de 07/11/2026)",
                  "bargaining power with suppliers and a change in purchase mix (decision of 2026-11-07)"),
}  # fmt: skip
# Explicações documentadas de casos do gabarito, com a fonte (natureza: resumo de documento já citado no estudo 1).
NOTAS_DE_CASO = {
    ("20990", 2021): Motivo(
        "Em 2021 a B2W (código CVM 20990) recebeu as operações da Lojas Americanas por cisão parcial (assembleia de 10/06/2021); o comparativo de 2020 é só da B2W, e parte do SGI vem dessa troca de perímetro (docs/resultados.md, seção da Americanas).",
        "In 2021, B2W (CVM code 20990) received the Lojas Americanas operations through a partial spin-off (shareholders' meeting of 2021-06-10); the 2020 comparative is B2W alone, and part of SGI comes from this change of perimeter (docs/en/results.md, Americanas section).",
    ),
}
TEXTOS = {
    "pt": {
        "regra_mscore": "M > {corte} (pré-registro, seção 4)",
        "regra_dpo": "variação do DPO no decil superior do ano entre as não financeiras (≥ percentil 90 dos calculáveis na data: {lim} dias)",
        "regra_juro": "juro implícito acima do CDI médio do ano + {spread} p.p. (pré-registro, seção 4)",
        "regra_pnr": "peso não recorrente no decil superior do ano entre as financeiras (≥ percentil 90 dos calculáveis na data: {lim})",
        "sem_alerta": "não dispara alerta",
        "fallback_setor": "percentil no universo das não financeiras: o setor tem menos de 10 empresas com o valor",
        "parecer_enet": "a seção de pareceres dos dados abertos é só da última versão da DFP; a versão usada veio do ENET",
        "parecer_ausente": "a versão usada não tem a seção de pareceres nos dados abertos",
        "sem_trecho": "não foi achado trecho de opinião no texto",
        "o_que_se_sabia_nota": "DFP e FCA entregues à CVM até a data de referência; ITR e fatos relevantes entram em fases seguintes.",
        "rodizio_prazo": "A firma que saiu auditou {n} exercícios sociais consecutivos ({a} a {b}), pelas datas de início e fim no FCA.",
        "rodizio_compativel": "A troca coincide com o fim do prazo de {n} exercícios e é compatível com o rodízio ({art} da {norma}, vigente quando a firma nova começou).",
        "rodizio_sem_prazo": "O FCA não traz as datas necessárias para contar os exercícios da firma que saiu.",
        "materialidade": "Destacadas: diferenças em totais e linhas-chave (ativo total, passivo circulante, passivo não circulante, patrimônio líquido, receita líquida, lucro líquido e caixa operacional) acima de 1% do ativo total da versão usada. As demais diferenças (reclassificações entre linhas e diferenças menores) ficam na lista completa.",
        "contexto_nao_validado": "indicadores de contexto (Altman Z'' e Piotroski F) não foram validados no Brasil por este projeto e não geram alerta",
        "produto": "no produto, este sinal fica não calculável: usa um balanço não preenchido (ativo total zero)",
    },
    "en": {
        "regra_mscore": "M > {corte} (pre-registration, section 4)",
        "regra_dpo": "DPO change in the year's top decile among non-financial companies (≥ 90th percentile of computable values on the date: {lim} days)",
        "regra_juro": "implied interest rate above the year's average CDI rate + {spread} p.p. (pre-registration, section 4)",
        "regra_pnr": "non-recurring weight in the year's top decile among financial companies (≥ 90th percentile of computable values on the date: {lim})",
        "sem_alerta": "does not trigger alerts",
        "fallback_setor": "percentile in the non-financial universe: the sector has fewer than 10 companies with a value",
        "parecer_enet": "the open-data opinions section is only for the latest DFP version; the version used came from ENET",
        "parecer_ausente": "the version used has no opinions section in open data",
        "sem_trecho": "no opinion excerpt was found in the text",
        "o_que_se_sabia_nota": "DFP and FCA filed with the CVM by the reference date; ITR and material facts come in later phases.",
        "rodizio_prazo": "The outgoing firm audited {n} consecutive fiscal years ({a} to {b}), by the start and end dates in the FCA.",
        "rodizio_compativel": "The change coincides with the end of the {n}-fiscal-year term and is compatible with the rotation rule ({art} of {norma}, in force when the new firm started).",
        "rodizio_sem_prazo": "The FCA does not have the dates needed to count the outgoing firm's fiscal years.",
        "materialidade": "Highlighted: differences in totals and key lines (total assets, current liabilities, non-current liabilities, equity, net revenue, net income and operating cash flow) above 1% of total assets of the version used. The other differences (reclassifications between lines and smaller differences) stay in the full list.",
        "contexto_nao_validado": "context indicators (Altman Z'' and Piotroski F) were not validated in Brazil by this project and do not trigger alerts",
        "produto": "in the product, this signal is not computable: it uses an unfilled balance sheet (zero total assets)",
    },
}  # fmt: skip


def _m(m: Motivo | None, lang: str) -> str | None:
    return None if m is None else (m.pt if lang == "pt" else m.en)


def _num(v: Any) -> float | None:
    return None if v is None or pd.isna(v) else float(v)


def _res(r: Resultado, lang: str) -> dict[str, Any]:
    return {"valor": r.valor, "status": r.status, "motivo": _m(r.motivo, lang), "codigo": r.codigo}


def _ev(e: Evidencia) -> dict[str, Any]:
    d = e.documento
    return {"id": e.id, "documento": {"tipo": d.tipo, "num_doc": d.num_doc, "versao": d.versao, "dt_receb": d.dt_receb,
                                       "origem": d.origem, "tipo_demonstracao": d.tipo_demonstracao, "url": d.url,
                                       "sha256": d.sha256},
            "demonstracao": e.demonstracao, "coluna": e.coluna, "cd_conta": e.cd_conta, "ds_conta": e.ds_conta,
            "valor": e.valor, "localizacao": e.localizacao}  # fmt: skip


def _id(*partes: Any) -> str:
    return hashlib.sha256("|".join(str(p) for p in partes).encode()).hexdigest()[:16]


def _percentis(valor: float | None, ref: pd.DataFrame, coluna: str, setor: str | None) -> dict[str, Any]:
    if valor is None:
        return {"percentil_setor_ano": None, "percentil_grupo_ano": None}
    grupo = contexto.percentil(valor, list(ref[coluna]))
    no_setor = (
        contexto.percentil(valor, list(ref.loc[ref.setor == setor, coluna])) if setor else grupo | {"valor": None}
    )
    return {"percentil_setor_ano": no_setor, "percentil_grupo_ano": grupo}


def _jm(d: dict[str, Any], lang: str) -> dict[str, Any]:
    """Troca os `Motivo` de um dicionário de contexto pelo texto no idioma."""
    return {
        k: (_m(v, lang) if isinstance(v, Motivo) else _jm(v, lang) if isinstance(v, dict) else v) for k, v in d.items()
    }


def gerar(
    fontes: FontesV1,
    cd_cvm: str,
    exercicio: int,
    data_referencia: date | str,
    lang: str = "pt",
    localizador: Localizador | None = None,
    gerado_em: str | None = None,
) -> dict[str, Any]:
    garantir_liberado(exercicio)
    d = garantir_data_referencia(data_referencia)
    cd_cvm = str(cd_cvm).lstrip("0") or "0"
    gerado_em = gerado_em or datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    t = TEXTOS[lang]
    e = exercicio_na_data(fontes, cd_cvm, exercicio, d, localizador=localizador)
    s, limiares, contas_todas, meta = corte_transversal_completo(fontes, exercicio, d)
    s = s.merge(meta[["cd_cvm", "dt_refer", "setor"]], on=["cd_cvm", "dt_refer"], how="left")
    linha_s = s[(s.cd_cvm == cd_cvm) & (s.dt_refer == e.dt_refer)]
    linha_m = meta[(meta.cd_cvm == cd_cvm) & (meta.dt_refer == e.dt_refer)]
    if linha_s.empty or linha_m.empty:
        raise ValueError(f"empresa {cd_cvm} sem DFP do exercício {exercicio}")
    r, mt = linha_s.iloc[0], linha_m.iloc[0]
    grupo, setor, amostra = mt.grupo, mt.setor if isinstance(mt.setor, str) else None, r.amostra
    out: dict[str, Any] = {
        "empresa": _empresa(fontes, cd_cvm, d, mt, setor, grupo, lang),
        "data_referencia": d.isoformat(), "idioma": lang,
        "exercicios": [{"exercicio": exercicio, "dt_refer": e.dt_refer, "situacao": e.situacao, "versao_usada": e.versao_usada,
                        "dt_receb": None if e.dt_receb is None else str(e.dt_receb),
                        "versoes_conhecidas": [{"versao": v, "dt_receb": str(x)} for v, x in e.versoes_conhecidas],
                        "tipo": e.tipo, "origem": e.origem, "num_doc": e.num_doc, "link": e.link,
                        "escala_original": e.escala_original, "notas": [_m(n, lang) for n in e.notas],
                        "amostra_estudo_1": amostra}],
    }  # fmt: skip
    if e.situacao != "ok" or e.documento is None:
        out["achados"] = {}
        return _fecha(out, e, lang, gerado_em, d, fontes, exercicio, cd_cvm, {}, [])
    evid: dict[str, Evidencia] = {}
    por_chave = {(x.demonstracao[:3] if x.demonstracao.startswith("DFC") else x.demonstracao, x.coluna, x.cd_conta): x
                 for x in e.evidencias}  # fmt: skip
    conferencias = cf.conferir(e.contas, mt.plano if isinstance(mt.plano, str) else "outro")
    nao_preenchidas = cf.colunas_nao_preenchidas(conferencias)
    leitura_t = variaveis.le_ordem(e.contas, variaveis.ULTIMO)
    ficha = ficha_v1(e.contas, e.documento, "financeira" if amostra == "financeira" else "nao_financeira", gerado_em,
                     _num(r.get("cdi_medio")), localizador, int(mt.repetidas_iguais or 0))  # fmt: skip
    evid |= ficha.evidencias
    historico_s, historico_contas = _historico(fontes, cd_cvm, exercicio, d)
    ref = s[s.amostra == amostra]
    achados: dict[str, list[dict[str, Any]]] = {
        "possivel_manipulacao": [],
        "risco_financeiro": [],
        "qualidade_financeira": [],
    }
    sinais = ["peso_nao_recorrente"] if amostra == "financeira" else SINAIS_NF if amostra == "nao_financeira" else []
    for sinal in sinais:
        valor = _num(r.get(sinal))
        res = de_resultado_v1(
            ResultadoV1(valor, None if valor is not None else str(r.get(f"{sinal}_motivo") or "nao_calculado"))
        )
        produto = aplicar_nao_preenchido(sinal, res, nao_preenchidas)
        conf = confianca.avaliar(sinal, res, conferencias, e.documento, str(r.data_corte), len(e.versoes_conhecidas),
                                 leitura_t.depreciacao_combinada, bool(leitura_t.juros_pagos_em_6_01))  # fmt: skip
        lin = ficha.linhagens.get(sinal)
        serie = {a: _num(h.get(sinal)) for a, h in historico_s.items()}
        achados["possivel_manipulacao"].append({
            "id": _id(cd_cvm, exercicio, d, sinal), "familia": "possivel_manipulacao", "sinal": sinal, "exercicio": exercicio,
            "rotulo": _m(Motivo(*ROTULOS[sinal]), lang), "valor": _res(res, lang),
            "valor_no_produto": _res(produto, lang) if produto != res else None,
            "regra": _regra(sinal, t, limiares, exercicio, lang), "alerta_v1": _alerta(r, sinal),
            "contexto": _jm(_percentis(valor, ref, sinal, setor) | {"historico": contexto.historico(serie, valor)}, lang),
            "confianca": {"nivel": conf.nivel, "criterios": [{"nome": c.nome, "resultado": c.resultado, "motivo": _m(c.motivo, lang)}
                                                             for c in conf.criterios]},
            "explicacao": _m(Motivo(*FORMULAS[sinal]), lang) if sinal in FORMULAS else None,
            "explicacoes_alternativas": [_m(x, lang) for x in [ALTERNATIVAS.get(sinal), NOTAS_DE_CASO.get((cd_cvm, exercicio))
                                                               if sinal in ("mscore", "SGI") else None] if x],
            "limitacoes": [_m(x, lang) for x in LIMITACOES.get(sinal, ())] + ([t["produto"]] if produto != res else []),
            "linhagem": _linhagem(lin, lang) if lin else None,
            "natureza": {"valor": "calculado", "regra": "calculado", "explicacao": "resumo", "explicacoes_alternativas": "hipotese"},
        })  # fmt: skip
    z = contexto.altman_z2(e.contas, grupo)
    z_ref = _z2_universo(contas_todas, meta)
    z_ctx: dict[str, Any] = {"percentil_setor_ano": None, "percentil_grupo_ano": None}
    if z.resultado.ok and z.resultado.valor is not None:
        no_setor = (
            contexto.percentil(z.resultado.valor, list(z_ref.loc[z_ref.setor == setor, "z2"]))
            if setor
            else {"valor": None}
        )
        universo = contexto.percentil(z.resultado.valor, list(z_ref.z2))
        z_ctx = {"percentil_setor_ano": no_setor if no_setor["valor"] is not None else universo | {"marca": t["fallback_setor"]},
                 "percentil_grupo_ano": universo}  # fmt: skip
    z_hist = {a: contexto.altman_z2(c, grupo).resultado.valor for a, c in historico_contas.items()}
    achados["risco_financeiro"].append(_achado_contexto("altman_z2", z, cd_cvm, exercicio, d, lang, por_chave, evid,
                                                        z_ctx | {"historico": contexto.historico(z_hist, z.resultado.valor)}))  # fmt: skip
    anterior = base.como_era(fontes, cd_cvm, exercicio - 1, corte=d) if exercicio - 1 >= 2010 else None  # type: ignore[arg-type]
    contas_t1 = anterior.contas if anterior is not None and anterior.status == base.OK else None
    f = contexto.piotroski_f(e.contas, contas_t1, grupo)
    achados["qualidade_financeira"].append(
        _achado_contexto("piotroski_f", f, cd_cvm, exercicio, d, lang, por_chave, evid, None)
    )
    out["achados"] = achados
    return _fecha(out, e, lang, gerado_em, d, fontes, exercicio, cd_cvm, evid, conferencias)


def _empresa(fontes: Any, cd_cvm: str, d: date, mt: Any, setor: str | None, grupo: str, lang: str) -> dict[str, Any]:
    """O nome da época vem do FCA entregue até a data; o índice dos dados abertos traz o nome atual."""
    from chiocca.v2.busca import codigos

    nome = fontes.nome_na_data(cd_cvm, d) if hasattr(fontes, "nome_na_data") else None
    origem = "fca" if nome else "indice_dfp"
    cods, motivo = codigos(fontes, cd_cvm, d)
    return {"cd_cvm": cd_cvm, "cnpj": mt.cnpj, "denominacao": nome or mt.denominacao, "origem_denominacao": origem,
            "setor": setor, "origem_setor": mt.origem_setor, "grupo": grupo,
            "situacao_cadastro_atual": mt.situacao_cadastro, "codigos_negociacao": cods,
            "motivo_codigos_negociacao": motivo}  # fmt: skip


def _alerta(r: pd.Series, sinal: str) -> bool | None:
    col = ALERTA.get(sinal)
    if col is None:
        return None
    v = r.get(col)
    return None if v is None or pd.isna(v) else bool(v)


def _regra(sinal: str, t: dict[str, str], limiares: pd.DataFrame, exercicio: int, lang: str) -> str | None:
    def lim(nome: str, grupo: str) -> str:
        x = limiares[
            (limiares.exercicio == exercicio) & (limiares.sinal == nome) & (limiares.grupo == grupo)
        ].limite_p90
        return (
            "—"
            if x.empty or pd.isna(x.iloc[0])
            else decimal(float(x.iloc[0]), lang, 3 if nome == "peso_nao_recorrente" else 1)
        )

    if sinal == "mscore":
        return t["regra_mscore"].format(corte=decimal(CORTE_M, lang, 2))
    if sinal == "dpo":
        return t["regra_dpo"].format(lim=lim("dpo", "nao_financeira"))
    if sinal == "juro":
        return t["regra_juro"].format(spread=decimal(SPREAD_PP, lang, 0))
    if sinal == "peso_nao_recorrente":
        return t["regra_pnr"].format(lim=lim("peso_nao_recorrente", "financeira"))
    return None


def _linhagem(lin: Any, lang: str) -> dict[str, Any]:
    return {"numero": {"nome": lin.sinal, "rotulo": _m(lin.rotulo, lang), "valor": lin.valor, "motivo_v1": lin.motivo_v1},
            "formula": _m(lin.formula, lang), "valores": [list(v) for v in lin.valores], "entradas": list(lin.entradas),
            "transformacoes": [_m(x, lang) for x in lin.transformacoes], "premissas": [_m(x, lang) for x in lin.premissas],
            "limitacoes": [_m(x, lang) for x in lin.limitacoes], "motor": lin.motor, "codigo": lin.codigo,
            "calculado_em": lin.calculado_em}  # fmt: skip


def _historico(
    fontes: FontesV1, cd_cvm: str, exercicio: int, d: date
) -> tuple[dict[int, pd.Series], dict[int, pd.DataFrame]]:
    sinais: dict[int, pd.Series] = {}
    contas: dict[int, pd.DataFrame] = {}
    for ano in range(max(2010, exercicio - ANOS_HISTORICO), exercicio):
        s, c, meta = sinais_da_empresa(fontes, cd_cvm, ano, d)
        if s.empty or meta.status.iloc[0] != base.OK:
            continue
        sinais[ano] = s.iloc[0]
        contas[ano] = c[c.dt_refer == meta.dt_refer.iloc[0]]
    return sinais, contas


def _z2_universo(contas: pd.DataFrame, meta: pd.DataFrame) -> pd.DataFrame:
    """Z'' de todas as não financeiras com versão pública na data (para o percentil)."""
    ok = meta[(meta.status == base.OK) & (meta.grupo == "nao_financeira")]
    linhas = []
    por = {k: g for k, g in contas.groupby(["cd_cvm", "dt_refer"])}
    for m in ok.itertuples(index=False):
        g = por.get((m.cd_cvm, m.dt_refer))
        if g is None:
            continue
        z = contexto.altman_z2(g, m.grupo).resultado
        if z.ok:
            linhas.append({"cd_cvm": m.cd_cvm, "setor": m.setor, "z2": z.valor})
    return pd.DataFrame(linhas, columns=["cd_cvm", "setor", "z2"])


def _achado_contexto(sinal: str, ind: contexto.Indicador, cd_cvm: str, exercicio: int, d: date, lang: str,
                     por_chave: dict[tuple[str, str, str], Evidencia], evid: dict[str, Evidencia],
                     ctx: dict[str, Any] | None) -> dict[str, Any]:  # fmt: skip
    ids = []
    for dem, cod, col in ind.contas:
        x = por_chave.get((dem[:3] if dem.startswith("DFC") else dem, col, cod))
        if x is not None:
            evid[x.id] = x
            ids.append(x.id)
    familia = "risco_financeiro" if sinal == "altman_z2" else "qualidade_financeira"
    rotulo = {"altman_z2": ("Altman Z'' (risco financeiro, só contexto)", "Altman Z'' (financial risk, context only)"),
              "piotroski_f": ("Piotroski F (qualidade financeira, só contexto)", "Piotroski F (financial quality, context only)")}[sinal]  # fmt: skip
    componentes = dict(ind.componentes)
    texto = ind.texto
    if sinal == "piotroski_f" and texto and lang == "en":
        texto = texto.replace("calculáveis", "computable")
    return {
        "id": _id(cd_cvm, exercicio, d, sinal), "familia": familia, "sinal": sinal, "exercicio": exercicio,
        "rotulo": rotulo[0 if lang == "pt" else 1], "valor": _res(ind.resultado, lang), "texto": texto,
        "componentes": componentes, "regra": None, "alerta_v1": None,
        "contexto": _jm(ctx, lang) if ctx else None, "marcas": [_m(x, lang) for x in ind.marcas],
        "linhagem": {"entradas": ids, "motor": MOTOR_V2, "codigo": f"chiocca.v2.contexto.{sinal}",
                     "origens": ["DFP de t, coluna ÚLTIMO", "DFP de t, coluna PENÚLTIMO (t−1)"]
                     + (["DFP de t−1 na data, coluna PENÚLTIMO (t−2)"] if sinal == "piotroski_f" else [])},
        "natureza": {"valor": "calculado"},
    }  # fmt: skip


def _parecer_e_auditor(fontes: Any, e: Any, exercicio: int, cd_cvm: str, d: date, lang: str) -> dict[str, Any]:
    t = TEXTOS[lang]
    out: dict[str, Any] = {"natureza": "trecho_literal", "gera_alerta": False}
    if e.origem != "dados_abertos" or not hasattr(fontes, "parecer"):
        out["relatorio_do_auditor"] = {"motivo": t["parecer_enet"] if e.origem == "enet" else t["parecer_ausente"]}
    else:
        p = fontes.parecer(exercicio, cd_cvm, str(e.dt_refer), int(e.versao_usada))
        aud = p[p.tp_parecer_decl.astype(str).str.startswith("Relatório do Auditor")]
        if aud.empty:
            out["relatorio_do_auditor"] = {"motivo": t["parecer_ausente"]}
        else:
            texto = " ".join(str(x) for x in aud.texto)
            # A frase de opinião, até o ponto seguido de espaço e maiúscula (não corta em "S.A.").
            m = re.search(r"(Em nossa opini[aã]o.{0,600}?\.)(?=\s+[A-ZÁÉÍÓÚÂÊÔÃÕÇ]|\s*$)", texto)
            trecho = m.group(1) if m else None
            out["relatorio_do_auditor"] = {
                "tipo": sorted(set(str(x) for x in aud.tp_relat_aud.dropna())),
                "trecho": trecho, "conferido": bool(trecho and trecho in texto), "motivo": None if trecho else t["sem_trecho"],
                "localizacao": {"arquivo": str(aud.arquivo.iloc[0]), "linhas": [int(x) for x in aud.linha_arquivo]},
            }  # fmt: skip
    if hasattr(fontes, "auditores"):
        au = fontes.auditores(cd_cvm, d)
        ultimas = au.sort_values(["ano", "versao"]).groupby("ano").tail(10)
        firmas: list[dict[str, Any]] = []
        for ano, g in ultimas.groupby("ano"):
            g = g[g.versao == g.versao.max()]
            firmas.append({"ano_fca": int(ano), "dt_receb": str(g.dt_receb.iloc[0])[:10],
                           "auditores": [{"auditor": str(x.auditor), "codigo_cvm": str(x.codigo_cvm_auditor),
                                          "inicio": None if pd.isna(x.inicio) else str(x.inicio),
                                          "fim": None if pd.isna(x.fim) else str(x.fim)} for x in g.itertuples(index=False)]})  # fmt: skip
        trocas = []
        for a, b in zip(firmas, firmas[1:]):  # troca pelo código da firma na CVM, não pela grafia do nome
            de = {x["codigo_cvm"]: x["auditor"] for x in a["auditores"]}
            para = {x["codigo_cvm"]: x["auditor"] for x in b["auditores"]}
            if set(de) != set(para):
                trocas.append({"ano_fca": b["ano_fca"], "de": sorted(de.values()), "para": sorted(para.values()),
                               "saidas": _saidas(a, b, set(de) - set(para), set(para) - set(de), lang)})  # fmt: skip
        out["auditores_no_fca"] = firmas
        out["trocas_de_auditor"] = trocas
        out["rodizio"] = {"nota": _m(RODIZIO, lang), "norma": "Resolução CVM nº 23/2021, arts. 31 e 31-A",
                          "fonte": RODIZIO_FONTE, "conferida_em": "2026-11-09"}  # fmt: skip
    return out


def _saidas(
    a: dict[str, Any], b: dict[str, Any], sairam: set[str], entraram: set[str], lang: str
) -> list[dict[str, Any]]:
    """Exercícios sociais consecutivos da firma que saiu, pelas datas do FCA: do ano do início dela ao último exercício
    que terminou com ela contratada (pela data de fim, quando o FCA traz; senão, o ano anterior ao início da firma que
    entrou). Quando a troca coincide com o fim do prazo (cinco exercícios, art. 31; dez, art. 31-A), a nota diz que é
    compatível com o rodízio, citando a norma vigente quando a firma nova começou."""
    t = TEXTOS[lang]
    out = []
    for x in a["auditores"]:
        if x["codigo_cvm"] not in sairam:
            continue
        primeiro = int(x["inicio"][:4]) if x["inicio"] else None
        # Quem entrou: a firma nova nesta troca ou, se ela já constava no FCA anterior, a que começou depois da que saiu.
        inicios_novos = [y["inicio"] for y in b["auditores"] if y["inicio"] and (y["codigo_cvm"] in entraram or
                         (x["inicio"] is not None and y["inicio"] > x["inicio"]))]  # fmt: skip
        if x["fim"]:  # a data de fim no FCA, quando existe: o último exercício é o que termina até ela
            ultimo: int | None = int(x["fim"][:4]) - (0 if x["fim"][5:10] == "12-31" else 1)
        else:
            ultimo = int(min(inicios_novos)[:4]) - 1 if inicios_novos else None
        n = ultimo - primeiro + 1 if primeiro is not None and ultimo is not None and ultimo >= primeiro else None
        artigo = RODIZIO_PRAZOS.get(n) if n is not None else None
        # A norma vigente na data em que a firma nova começou: a Resolução desde 01/04/2021; antes, a Instrução 308.
        norma = None if not inicios_novos else RODIZIO_NORMAS[min(inicios_novos) >= RODIZIO_VIGENCIA]
        if n is None:
            nota = t["rodizio_sem_prazo"]
        else:
            nota = t["rodizio_prazo"].format(n=n, a=primeiro, b=ultimo)
            if artigo:
                nome_norma = RODIZIO_NORMAS_EN.get(str(norma), str(norma)) if lang == "en" else norma
                nota += " " + t["rodizio_compativel"].format(n=n, art=artigo, norma=nome_norma)
        out.append({"auditor": x["auditor"], "codigo_cvm": x["codigo_cvm"], "primeiro_exercicio": primeiro,
                    "ultimo_exercicio": ultimo, "exercicios_consecutivos": n, "compativel_com_rodizio": artigo is not None,
                    "artigo": artigo, "norma": norma if artigo else None, "nota": nota})  # fmt: skip
    return out


def _fecha(out: dict[str, Any], e: Any, lang: str, gerado_em: str, d: date, fontes: Any, exercicio: int, cd_cvm: str,
           evid: dict[str, Evidencia], conferencias: list[Any]) -> dict[str, Any]:  # fmt: skip
    t = TEXTOS[lang]

    def dif(x: comparativo.DiferencaComparativo) -> dict[str, Any]:
        return {"texto": _m(x.texto, lang), "demonstracao": x.demonstracao, "cd_conta": x.cd_conta, "ds_conta": x.ds_conta,
                "valor": x.valor, "valor_comparativo": x.valor_comparativo, "diferenca": x.diferenca, "grupo": x.grupo,
                "destacada": x.destacada, "versao": x.versao, "dt_receb": x.dt_receb, "versao_seguinte": x.versao_seguinte,
                "dt_receb_seguinte": x.dt_receb_seguinte}  # fmt: skip

    # Destaque só do grupo (a) acima de 1% do ativo total; a lista completa (grupos a e b) fica logo abaixo.
    ordenadas = sorted(e.diferencas_comparativo, key=lambda x: (x.grupo, -abs(x.diferenca), x.demonstracao, x.cd_conta))
    contas_e = (
        e.contas
        if isinstance(e.contas, pd.DataFrame) and "cd_conta" in e.contas
        else pd.DataFrame(columns=base.COLUNAS)
    )
    out["mudancas"] = {
        "versoes_conhecidas": [{"versao": v, "dt_receb": str(x), "usada": v == e.versao_usada} for v, x in e.versoes_conhecidas],
        "comparativo_destacadas": [dif(x) for x in ordenadas if x.destacada],
        "reapresentacao_pelo_comparativo": [dif(x) for x in ordenadas],
        "tolerancia_comparativo": comparativo.TOLERANCIA,
        "materialidade_comparativo": {
            "linhas_chave": [{"demonstracao": dem, "cd_conta": cod} for dem, cod in comparativo.LINHAS_CHAVE],
            "limite_relativo": comparativo.MATERIALIDADE, "ativo_total": comparativo.ativo_total(contas_e),
            "limite": comparativo.limite_destaque(contas_e), "texto": t["materialidade"]},
    }  # fmt: skip
    docs = []
    for ano in range(max(2010, exercicio - ANOS_HISTORICO), min(exercicio + 1, ULTIMO_EXERCICIO_LIBERADO) + 1):
        idx = fontes.indice_dfp(ano)
        for x in idx[(idx.cd_cvm == cd_cvm) & (idx.dt_receb <= d)].drop_duplicates(["versao"]).itertuples(index=False):
            docs.append(
                {
                    "tipo": "DFP",
                    "exercicio": ano,
                    "versao": int(x.versao),
                    "dt_receb": str(x.dt_receb),
                    "num_doc": x.num_doc,
                }
            )
    fca = fontes.fca(exercicio)
    docs += [{"tipo": "FCA", "exercicio": exercicio, "versao": int(x.versao), "dt_receb": str(x.dt_receb), "num_doc": None}
             for x in fca[(fca.cd_cvm == cd_cvm) & (fca.dt_receb <= d)].itertuples(index=False)]  # fmt: skip
    out["o_que_se_sabia"] = {"documentos": sorted(docs, key=lambda x: (x["dt_receb"], x["tipo"], x["exercicio"])),
                             "nota": t["o_que_se_sabia_nota"]}  # fmt: skip
    out["qualidade_dos_dados"] = {"conferencias": [
        {"id": c.id, "tipo": c.tipo, "nome": _m(c.nome, lang), "coluna": c.coluna, "resultado": c.resultado,
         "motivo": _m(c.motivo, lang)} for c in conferencias]}  # fmt: skip
    out["parecer_e_auditor"] = _parecer_e_auditor(fontes, e, exercicio, cd_cvm, d, lang) if e.situacao == "ok" else None
    est = confianca.evidencia_estudo_1()
    out["como_o_motor_foi_testado"] = {"documento": "docs/resumo.md" if lang == "pt" else "docs/summary.md",
                                       "acertados": est["acertados"], "acertaveis": est["acertaveis"],
                                       "alarmes_por_acerto_periodo_inteiro": est["alarmes_inteiro"],
                                       "taxa_de_alerta_nao_financeiras": est["taxa_alerta"]}  # fmt: skip
    out["limites"] = limites.textos(lang)
    out["limitacoes"] = [_m(n, lang) for n in e.notas] + [t["contexto_nao_validado"]]
    out["evidencias"] = {k: _ev(v) for k, v in sorted(evid.items())}
    out["motor"] = {"v1": MOTOR_V1, "v2": MOTOR_V2}
    out["gerado_em"] = gerado_em
    out["aviso"] = AVISO[lang]
    return out


def main(argv: list[str]) -> None:
    from chiocca.v2 import pdf_investigacao
    from chiocca.v2.armazem import FontesArmazem

    pdf = "--pdf" in argv
    args = [a for a in argv if a != "--pdf"]
    cd, ano, data_ref = args[0], int(args[1]), args[2]
    lang = args[3] if len(args) > 3 else "pt"
    fa = FontesArmazem()
    loc = Localizador(base.BRUTOS, fa.cache_enet, base.RAIZ / "data" / "manifesto_brutos.csv")
    inv = gerar(fa, cd, ano, data_ref, lang, loc)
    texto = json.dumps(inv, ensure_ascii=False, indent=1)
    if pdf:
        sys.stdout.buffer.write(pdf_investigacao.gerar(inv))
    else:
        print(texto)


if __name__ == "__main__":
    main(sys.argv[1:])
