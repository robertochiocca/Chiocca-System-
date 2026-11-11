"""A seção "Notas explicativas" da investigação (Fase F1): busca os documentos (cache do ENET e dados abertos do
Formulário de Referência), roda o leitor e acrescenta os metadados de cada documento.

O interruptor `LIGADO` começa desligado. Pelo pré-registro (docs/pre-registro-leitor.md), a seção só entra na
investigação se o leitor congelado atingir as quatro metas nos casos guardados, num commit que registra o resultado;
um teste confere que o interruptor só fica ligado com esse resultado aprovado em docs/leitor_medida.json.

Só o documento da versão usada na investigação é lido (a versão pública na data de referência); nada entregue depois
de 31/12/2024 nem de exercício acima de 2023, como o resto da investigação.
"""

from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Any

from chiocca.v2.leitor import enet_documentos, formulario, ler

LIGADO = True  # ligada em 11/11/2026: as quatro metas atingidas nos casos guardados (docs/leitor_medida.json)

TEXTOS: dict[str, dict[str, str]] = {
    "pt": {"fora_do_cache": "documento ainda não baixado do ENET", "sem_notas": "a DFP não tem notas explicativas no ENET",
           "sem_relatorio": "a DFP não tem relatório do auditor no ENET", "falha": "o ENET não entregou o documento",
           "sem_documento": "sem número de documento da DFP"},
    "en": {"fora_do_cache": "document not yet downloaded from ENET", "sem_notas": "the DFP has no explanatory notes on ENET",
           "sem_relatorio": "the DFP has no auditor's report on ENET", "falha": "ENET did not deliver the document",
           "sem_documento": "no DFP document number"},
}  # fmt: skip


def _busca(f: Any, num_doc: str, rede: bool, pasta: Path) -> tuple[Any, dict[str, Any], str | None]:
    try:
        conteudo, meta = f(num_doc, pasta=pasta, rede=rede)
    except enet_documentos.FalhaDocumento:
        return None, {}, "falha"
    if meta.get("fora_do_cache"):
        return None, meta, "fora_do_cache"
    if meta.get("sem_conteudo"):
        return None, meta, "sem_conteudo"
    return conteudo, meta, None


def secao(num_doc: str | None, versao: int | None, dt_receb: str | None, cd_cvm: str, exercicio: int,
          data_referencia: date, lang: str, rede: bool = False, pasta: Path = enet_documentos.CACHE,
          brutos: Path | None = None) -> dict[str, Any]:  # fmt: skip
    t = TEXTOS[lang]
    notas: Any = None
    relatorio: Any = None
    meta_n: dict[str, Any] = {}
    meta_r: dict[str, Any] = {}
    motivo_n: str | None
    motivo_r: str | None
    if not num_doc:
        motivo_n = motivo_r = t["sem_documento"]
    else:
        notas, meta_n, mn = _busca(enet_documentos.notas, num_doc, rede, pasta)
        relatorio, meta_r, mr = _busca(enet_documentos.relatorio_do_auditor, num_doc, rede, pasta)
        motivo_n = None if mn is None else t["sem_notas"] if mn == "sem_conteudo" else t[mn]
        motivo_r = None if mr is None else t["sem_relatorio"] if mr == "sem_conteudo" else t[mr]
    out = ler.ler(notas, {"titulo": meta_r.get("titulo"), "texto": relatorio} if relatorio else None, None, lang,
                  motivo_n, motivo_r)  # fmt: skip
    out["documento"] = {
        "tipo": "DFP", "num_doc": num_doc, "versao": versao, "dt_receb": dt_receb, "origem": "enet",
        "notas": {k: meta_n.get(k) for k in ("url", "sha256", "bytes", "paginas", "baixado_em_utc")} if notas else None,
        "relatorio": {k: meta_r.get(k) for k in ("url", "titulo", "sha256", "baixado_em_utc")} if relatorio else None,
    }  # fmt: skip
    out["formulario_de_referencia"] = formulario.transacoes(cd_cvm, exercicio, data_referencia, lang, brutos)
    return out
