"""A seção "Trechos dos documentos" da investigação com o leitor em uso: a `leitor-f1-2` desde 13/11/2026.

Pela emenda 1 do pré-registro do leitor (docs/pre-registro-leitor.md, seção 10, e as decisões de 10.7), a `leitor-f1-2`
substitui a `leitor-f1-1` na seção porque o critério de troca saiu verdadeiro na medida única nos casos guardados
novos (docs/leitor_medida_f1_2.json): as quatro metas, a precisão (com três casas) pelo menos a da `leitor-f1-1` e não
mais textos de cabeçalho saindo como trecho. Um teste confere que a seção só usa a `leitor-f1-2` com esse resultado.

Os arquivos da `leitor-f1-1` não mudam (chiocca/v2/leitor/, congelados): esta seção é a de chiocca/v2/leitor/secao.py
(mesma busca dos documentos, mesmos textos e mesmo Formulário de Referência), com o leitor da `leitor-f1-2`
(chiocca/v2/leitor_f1_2/ler.py, congelado no commit dd688da). O interruptor continua o da `leitor-f1-1` (`LIGADO`).
"""

from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Any

from chiocca.v2.leitor import enet_documentos, formulario
from chiocca.v2.leitor import secao as secao_f1_1
from chiocca.v2.leitor_f1_2 import VERSAO as LEITOR
from chiocca.v2.leitor_f1_2 import ler

LIGADO = secao_f1_1.LIGADO
TEXTOS = secao_f1_1.TEXTOS
__all__ = ["LEITOR", "LIGADO", "TEXTOS", "secao"]


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
        notas, meta_n, mn = secao_f1_1._busca(enet_documentos.notas, num_doc, rede, pasta)
        relatorio, meta_r, mr = secao_f1_1._busca(enet_documentos.relatorio_do_auditor, num_doc, rede, pasta)
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
