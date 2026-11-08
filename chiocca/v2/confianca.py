# Origem da estrutura: Carchuna (github.com/robertochiocca/carchuna), carchuna/confianca.py, commit
# a3f30ac284eb01245b022b7655bb16c4b8474cc7. Adaptado para o Chiocca System.
# O que mudou: a nota de 0 a 100 e os pontos da rubrica de vendas não vieram (não foram validados, e o plano de
# integração pede para não copiar pontuação arbitrária). Ficou a ideia de componentes com nome e motivo, agora
# critérios com resultado categórico e um nível por regra escrita.
"""Confiança nos dados de um sinal: cinco critérios com motivo, e um nível por regra escrita, sem nota numérica.

Critérios:
- **fonte**: dados abertos ou ENET, consolidado ou individual;
- **completude**: as contas de que o sinal precisa estão na DFP? (não calculável, depreciação combinada, juros
  pagos não achados);
- **consistencia**: conferências de qualidade (`chiocca.v2.conferencias`) nas demonstrações que o sinal usa: falha de
  identidade ou balanço não preenchido é problema; reconciliação que não fecha e sinal contábil incomum são atenção;
  "fecha com caixa amplo" não é falha;
- **atualidade**: entregue até a data de corte do exercício? reapresentada até a data de referência?
- **metodo**: o que o estudo 1 mostrou sobre o motor (números lidos de `docs/resultados_numeros.json`).

Cada critério dá `ok`, `atencao` ou `problema`. Nível: `baixa` se algum critério tem problema; `media` se algum tem
atenção; senão `alta`. A confiança descreve os dados e o método; não muda nenhum sinal nem alerta do motor v1.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any

from chiocca.base import RAIZ
from chiocca.formato import decimal, inteiro, pct
from chiocca.sinais.mscore import COEFICIENTES
from chiocca.v2.conferencias import IDENTIDADE, NAO_PREENCHIDO, RECONCILIACAO, SINAL_INCOMUM, Conferencia
from chiocca.v2.linhagem import Documento
from chiocca.v2.validade import Motivo, Resultado

OK, ATENCAO, PROBLEMA = "ok", "atencao", "problema"
NUMEROS_ESTUDO_1 = RAIZ / "docs" / "resultados_numeros.json"
# Demonstrações que cada sinal do motor v1 usa (para a consistência).
DEMONSTRACOES = {
    "DSRI": {"BPA", "DRE"}, "GMI": {"DRE"}, "AQI": {"BPA"}, "SGI": {"DRE"}, "DEPI": {"BPA", "DFC"},
    "SGAI": {"DRE"}, "TATA": {"BPA", "DRE", "DFC"}, "LVGI": {"BPA", "BPP"}, "mscore": {"BPA", "BPP", "DRE", "DFC"},
    "dpo": {"BPP", "DRE"}, "juro": {"BPP", "DRE"}, "lucro_sem_caixa": {"BPA", "DRE", "DFC"},
    "peso_nao_recorrente": {"DRE"},
}  # fmt: skip
USA_DEPRECIACAO = {"DEPI", "mscore"}
USA_CAIXA_OPERACIONAL = {"TATA", "mscore", "lucro_sem_caixa"}
SINAIS_V1 = set(COEFICIENTES) | {"mscore", "dpo", "juro", "lucro_sem_caixa", "peso_nao_recorrente"}


@dataclass(frozen=True)
class Criterio:
    nome: str
    resultado: str
    motivo: Motivo


@dataclass(frozen=True)
class Confianca:
    nivel: str
    criterios: tuple[Criterio, ...]


@lru_cache(maxsize=2)
def evidencia_estudo_1(caminho: Path = NUMEROS_ESTUDO_1) -> dict[str, Any]:
    """Os números do estudo 1 que entram no critério de método, lidos da saída versionada do estudo."""
    n = json.loads(Path(caminho).read_text(encoding="utf-8"))
    taxa = n["taxa"]["nf"]
    juro = n["por_sinal"]["nf"]["alerta_juro"]
    return {
        "acertados": n["acerto"]["acertados"],
        "acertaveis": n["acerto"]["acertaveis"],
        "alarmes_inteiro": n["alarmes"]["nf"]["inteiro"]["alarmes_por_acerto"],
        "taxa_alerta": sum(v["em_alerta"] for v in taxa.values()) / sum(v["avaliadas"] for v in taxa.values()),
        "juro_frequencia": sum(v["alertas"] for v in juro.values()) / sum(v["calculaveis"] for v in juro.values()),
    }


def _fonte(doc: Documento) -> Criterio:
    if doc.tipo_demonstracao == "ind":
        return Criterio(
            "fonte",
            ATENCAO,
            Motivo(
                "só demonstração individual: as controladas entram por equivalência patrimonial, sem consolidação",
                "individual statements only: subsidiaries enter through the equity method, without consolidation",
            ),
        )
    if doc.origem == "enet":
        return Criterio(
            "fonte",
            OK,
            Motivo(
                "consolidado; versão da época lida no ENET (rota aceita na emenda 8, só para consolidado)",
                "consolidated; point-in-time version read from ENET (route accepted in amendment 8, consolidated only)",
            ),
        )
    return Criterio("fonte", OK, Motivo("consolidado, dados abertos da CVM", "consolidated, CVM open data"))  # fmt: skip


def _completude(sinal: str, validade: Resultado, depreciacao_combinada: bool, juros_em_6_01: bool) -> Criterio:
    if validade.status == "indefinido":
        assert validade.motivo is not None
        return Criterio("completude", PROBLEMA, Motivo(f"o sinal não é calculável: {validade.motivo.pt}",
                                                       f"the signal is not computable: {validade.motivo.en}"))  # fmt: skip
    avisos = []
    if sinal in USA_DEPRECIACAO and depreciacao_combinada:
        avisos.append(Motivo("depreciação somada com amortização ou exaustão (usado o total)",
                             "depreciation combined with amortization or depletion (total used)"))  # fmt: skip
    if sinal in USA_CAIXA_OPERACIONAL and not juros_em_6_01:
        avisos.append(Motivo("sem linha de juros pagos na seção 6.01: caixa operacional como apresentado",
                             "no interest-paid line in section 6.01: operating cash flow as reported"))  # fmt: skip
    if avisos:
        return Criterio("completude", ATENCAO, Motivo("; ".join(a.pt for a in avisos), "; ".join(a.en for a in avisos)))
    return Criterio("completude", OK, Motivo("todas as contas de que o sinal precisa estão na DFP",
                                             "every account the signal needs is in the DFP"))  # fmt: skip


def _consistencia(sinal: str, conferencias: list[Conferencia]) -> Criterio:
    usadas = DEMONSTRACOES.get(sinal, set())
    relevantes = [c for c in conferencias if c.resultado != "nao_aplicavel" and (c.demonstracoes & usadas)]
    graves = [c for c in relevantes if c.resultado == "falhou" and c.tipo in (IDENTIDADE, NAO_PREENCHIDO)]
    avisos = [c for c in relevantes if c.resultado == "falhou" and c.tipo == RECONCILIACAO]
    incomuns = [c for c in relevantes if c.resultado == "falhou" and c.tipo == SINAL_INCOMUM]

    def lista(cs: list[Conferencia], lang: str) -> str:
        nomes = dict.fromkeys(f"{c.nome.pt if lang == 'pt' else c.nome.en} ({c.coluna})" for c in cs)
        return "; ".join(nomes)

    if graves:
        return Criterio("consistencia", PROBLEMA, Motivo("conferência falhou: " + lista(graves, "pt"),
                                                         "check failed: " + lista(graves, "en")))  # fmt: skip
    if avisos:
        return Criterio("consistencia", ATENCAO, Motivo(
            "reconciliação não fechou (pode ter explicação legítima, como caixa restrito): " + lista(avisos, "pt"),
            "reconciliation did not close (it may have a legitimate explanation, such as restricted cash): "
            + lista(avisos, "en")))  # fmt: skip
    if incomuns:
        return Criterio("consistencia", ATENCAO, Motivo(
            "sinal contábil incomum (pode ter explicação legítima, como reversão de provisão): " + lista(incomuns, "pt"),
            "unusual accounting sign (it may have a legitimate explanation, such as a provision reversal): "
            + lista(incomuns, "en")))  # fmt: skip
    if not relevantes:
        return Criterio("consistencia", ATENCAO, Motivo("nenhuma conferência se aplica às demonstrações usadas",
                                                        "no check applies to the statements used"))  # fmt: skip
    return Criterio("consistencia", OK, Motivo(
        f"{len(relevantes)} conferências aplicáveis, nenhuma falha",
        f"{len(relevantes)} applicable checks, no failure"))  # fmt: skip


def _atualidade(doc: Documento, data_corte: str, versoes_conhecidas: int) -> Criterio:
    avisos = []
    if doc.dt_receb and doc.dt_receb[:10] > data_corte[:10]:
        avisos.append(
            Motivo("entregue depois da data de corte do exercício", "filed after the fiscal year's cut-off date")
        )
    if versoes_conhecidas > 1:
        avisos.append(Motivo(f"{versoes_conhecidas} versões entregues até a data de referência (reapresentação)",
                             f"{versoes_conhecidas} versions filed by the reference date (restatement)"))  # fmt: skip
    if avisos:
        return Criterio("atualidade", ATENCAO, Motivo("; ".join(a.pt for a in avisos), "; ".join(a.en for a in avisos)))
    return Criterio("atualidade", OK, Motivo("entregue até a data de corte, sem reapresentação conhecida na data",
                                             "filed by the cut-off date, with no restatement known on the date"))  # fmt: skip


def _metodo(sinal: str, estudo: dict[str, Any]) -> Criterio:
    if sinal not in SINAIS_V1:
        return Criterio("metodo", ATENCAO, Motivo("indicador de contexto, não validado no Brasil por este projeto",
                                                  "context indicator, not validated in Brazil by this project"))  # fmt: skip

    def txt(lang: str) -> str:
        a, n = inteiro(estudo["acertados"], lang), inteiro(estudo["acertaveis"], lang)
        x, t = decimal(estudo["alarmes_inteiro"], lang, 1), pct(estudo["taxa_alerta"], lang)
        if lang == "pt":
            s = f"no estudo 1, o motor v1 acertou {a} de {n} casos acertáveis, com {x} alarmes por acerto no período inteiro e taxa de alerta de {t}"
            if sinal == "juro":
                s += f"; o juro implícito disparou em {pct(estudo['juro_frequencia'], lang)} das empresa-anos em que era calculável"
            return s
        s = f"in study 1, engine v1 detected {a} of {n} detectable cases, with {x} false alarms per detected case over the whole period and an alert rate of {t}"
        if sinal == "juro":
            s += f"; the implied interest rate fired in {pct(estudo['juro_frequencia'], lang)} of the company-years where it was computable"
        return s

    return Criterio("metodo", ATENCAO, Motivo(txt("pt"), txt("en")))


def avaliar(
    sinal: str,
    validade: Resultado,
    conferencias: list[Conferencia],
    doc: Documento,
    data_corte: str,
    versoes_conhecidas: int = 1,
    depreciacao_combinada: bool = False,
    juros_em_6_01: bool = True,
    estudo: dict[str, Any] | None = None,
) -> Confianca:
    criterios = (
        _fonte(doc),
        _completude(sinal, validade, depreciacao_combinada, juros_em_6_01),
        _consistencia(sinal, conferencias),
        _atualidade(doc, data_corte, versoes_conhecidas),
        _metodo(sinal, estudo if estudo is not None else evidencia_estudo_1()),
    )
    resultados = {c.resultado for c in criterios}
    nivel = "baixa" if PROBLEMA in resultados else "media" if ATENCAO in resultados else "alta"
    return Confianca(nivel, criterios)
