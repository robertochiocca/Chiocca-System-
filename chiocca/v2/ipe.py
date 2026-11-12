"""Fatos relevantes e comunicados ao mercado entregues à CVM até a data (Fase F2a, decisões de 12/11/2026).

Fonte: data/brutos/cvm/ipe_cia_aberta_<ano>.zip, os dados abertos do IPE de 2010 a 2024 (python -m chiocca.dados
baixar-ipe), arquivo ipe_cia_aberta_<ano>.csv: uma linha por documento entregue, com a data de entrega, a categoria,
o assunto, o protocolo de entrega, a versão e o link do documento no ENET. O arquivo de cada ano traz o que foi
entregue nesse ano. Só os metadados entram: o conteúdo dos documentos não é baixado, lido nem resumido.

Regras:
- só as categorias "Fato Relevante" e "Comunicado ao Mercado";
- só o entregue até a data de referência, e nunca depois de 31/12/2024 (o lacre do produto); os documentos entregues em
  2024 entram para datas de 2024, como as DFP entregues em 2024: a lista não calcula nada, e o lacre é por exercício;
- um item por documento entregue, identificado pelo link do ENET (numProtocolo, numSequencia e numVersao): um
  protocolo de entrega pode trazer mais de um documento (o fato relevante em português e em inglês, por exemplo), as
  linhas repetidas do mesmo documento contam uma vez, e de 2010 a 2014 o arquivo não traz o protocolo de entrega (o
  link traz). A reapresentação é outra entrega, com outro protocolo e a sua versão; os dados não ligam a reapresentação
  ao documento original, então cada entrega aparece, com a versão;
- o assunto passa pelo detector de nomes do leitor (chiocca.v2.leitor.nomes, o mesmo código, sem mudança): se marcar,
  vira "assunto omitido (possível nome de pessoa); ver o documento na CVM";
- ordem fixa: fatos relevantes primeiro, depois comunicados; em cada grupo, da entrega mais recente para a mais
  antiga (empate pelo identificador do documento). Nenhuma palavra do assunto é destacada, contada ou usada para
  alerta, nota ou ordenação; a única contagem é a de documentos por categoria;
- linhagem: cada item com a fonte (arquivo do IPE, ano e SHA-256 do arquivo), a data de entrega e o identificador do
  documento.

Sem arquivo do IPE, ou sem documento da companhia até a data, a lista sai vazia com o mesmo motivo (o comando
python -m chiocca.dados verificar confere os arquivos contra o manifesto).
"""

from __future__ import annotations

import hashlib
import io
import re
import zipfile
from datetime import date
from functools import lru_cache
from pathlib import Path
from typing import Any

import pandas as pd

from chiocca import base
from chiocca.v2.lacre import DATA_REFERENCIA_MAXIMA
from chiocca.v2.leitor import nomes

PRIMEIRO_ANO, ULTIMO_ANO = 2010, 2024  # o de 2025 em diante não entra (só o monitor olha os metadados)
CATEGORIAS = {"Fato Relevante": "fato_relevante", "Comunicado ao Mercado": "comunicado_ao_mercado"}
ORDEM_CATEGORIA = {"fato_relevante": 0, "comunicado_ao_mercado": 1}
COLUNAS = ["Codigo_CVM", "Categoria", "Assunto", "Data_Entrega", "Protocolo_Entrega", "Versao", "Link_Download"]
_LINK = re.compile(r"numProtocolo=(\d+)&numSequencia=(\d+)&numVersao=(\d+)")
TEXTOS = {
    "pt": {
        "omitido": "assunto omitido (possível nome de pessoa); ver o documento na CVM",
        "nota": "Fatos relevantes e comunicados ao mercado entregues à CVM até a data, pelos dados abertos do IPE "
        "(desde 2010): data de entrega, categoria, assunto e link. O conteúdo dos documentos não é baixado, lido nem "
        "resumido, e a lista não gera alerta, nota nem ordenação.",
        "sem_itens": "Nenhum fato relevante ou comunicado ao mercado entregue até a data nos dados abertos do IPE "
        "(desde 2010).",
    },
    "en": {
        "omitido": "subject omitted (possible person's name); see the document at the CVM",
        "nota": "Material facts and market notices filed with the CVM by the date, from the IPE open data (since "
        "2010): filing date, category, subject (as filed, in Portuguese) and link. The content of the documents "
        "is not downloaded, read or summarized, and the list generates no alert, score or ranking.",
        "sem_itens": "No material fact or market notice filed by the date in the IPE open data (since 2010).",
    },
}


def arquivo(ano: int, brutos: Path | None = None) -> Path:
    return (brutos or base.BRUTOS) / f"ipe_cia_aberta_{ano}.zip"


@lru_cache(maxsize=32)
def _sha256(caminho: str, tamanho: int, mtime: float) -> str:
    h = hashlib.sha256()
    with open(caminho, "rb") as f:
        for bloco in iter(lambda: f.read(1 << 20), b""):
            h.update(bloco)
    return h.hexdigest()


@lru_cache(maxsize=32)
def _ano(caminho: str, tamanho: int, mtime: float) -> pd.DataFrame:
    """As linhas de fato relevante e comunicado ao mercado de um arquivo do IPE (cache pelo caminho, tamanho e data)."""
    with zipfile.ZipFile(caminho) as z:
        nome = next(n for n in z.namelist() if n.endswith(".csv"))
        bruto = z.read(nome).decode("latin1")
    tab = pd.read_csv(io.StringIO(bruto), sep=";", dtype=str, keep_default_na=False, usecols=COLUNAS)
    tab = tab[tab["Categoria"].isin(list(CATEGORIAS))].copy()
    tab["cd_cvm"] = tab["Codigo_CVM"].str.strip().str.lstrip("0")
    tab["versao"] = pd.to_numeric(tab["Versao"], errors="coerce").astype("Int64")
    colunas = zip(tab["Link_Download"], tab["Categoria"], tab["Assunto"], tab["Data_Entrega"], strict=True)
    tab["id_documento"] = [id_documento(link, cat, ass, ent) for link, cat, ass, ent in colunas]
    return tab.drop_duplicates("id_documento")  # linhas repetidas do mesmo documento contam uma vez


def id_documento(link: str, categoria: str = "", assunto_: str = "", entrega: str = "") -> str:
    """O documento no ENET, pelo link (numProtocolo, numSequencia e numVersao); sem link reconhecível, hash da linha."""
    m = _LINK.search(link or "")
    if m:
        return "-".join(m.groups())
    return "linha-" + hashlib.sha256("|".join([link, categoria, assunto_, entrega]).encode("utf-8")).hexdigest()[:16]


def _tabelas(brutos: Path | None) -> list[tuple[int, Path, pd.DataFrame]]:
    out = []
    for ano in range(PRIMEIRO_ANO, ULTIMO_ANO + 1):
        p = arquivo(ano, brutos)
        if p.exists():
            st = p.stat()
            out.append((ano, p, _ano(str(p), st.st_size, st.st_mtime)))
    return out


def _fonte(ano: int, p: Path) -> dict[str, Any]:
    st = p.stat()
    return {"arquivo": p.name, "ano": ano, "sha256": _sha256(str(p), st.st_size, st.st_mtime)}


def assunto(texto: str, lang: str) -> tuple[str, bool]:
    """O assunto como vai para a tela: omitido se o detector de nomes do leitor marcar."""
    t = texto.strip()
    if nomes.tem_nome_de_pessoa(t):
        return TEXTOS[lang]["omitido"], True
    return t, False


def lista(cd_cvm: str, data_referencia: date, lang: str, brutos: Path | None = None) -> dict[str, Any]:
    """Os fatos relevantes e comunicados ao mercado da companhia entregues até a data, com a linhagem de cada item."""
    t = TEXTOS[lang]
    limite = min(data_referencia, DATA_REFERENCIA_MAXIMA).isoformat()
    cd = str(cd_cvm).strip().lstrip("0")
    itens: list[dict[str, Any]] = []
    vistos: set[str] = set()
    for ano, p, tab in _tabelas(brutos):
        if str(ano) > limite[:4]:
            continue
        sel = tab[(tab["cd_cvm"] == cd) & (tab["Data_Entrega"] <= limite)]
        if sel.empty:
            continue
        fonte = _fonte(ano, p)
        for r in sel.itertuples(index=False):
            if r.id_documento in vistos:
                continue
            vistos.add(r.id_documento)
            texto, omitido = assunto(r.Assunto, lang)
            itens.append({"categoria": CATEGORIAS[r.Categoria], "categoria_cvm": r.Categoria,
                          "data_entrega": r.Data_Entrega.strip(), "assunto": texto, "assunto_omitido": omitido,
                          "link": r.Link_Download.strip() or None, "id_documento": r.id_documento,
                          "protocolo": r.Protocolo_Entrega.strip() or None,
                          "versao": None if pd.isna(r.versao) else int(r.versao), "fonte": fonte})  # fmt: skip
    itens.sort(key=lambda x: x["id_documento"], reverse=True)
    itens.sort(key=lambda x: x["data_entrega"], reverse=True)
    itens.sort(key=lambda x: ORDEM_CATEGORIA[x["categoria"]])
    contagem = {c: sum(x["categoria"] == c for x in itens) for c in ORDEM_CATEGORIA}
    return {"origem": "dados_abertos", "conjunto": "IPE", "desde": f"{PRIMEIRO_ANO}-01-01", "ate": limite,
            "nota": t["nota"], "motivo": None if itens else t["sem_itens"], "contagem": contagem,
            "gera_alerta": False, "itens": itens}  # fmt: skip


NUMEROS = base.RAIZ / "docs" / "ipe_numeros.json"


def contar(brutos: Path | None = None) -> dict[str, Any]:
    """Quantos assuntos o detector de nomes omite, em todos os fatos relevantes e comunicados de 2010 a 2024 (um por
    documento entregue), para a documentação: python -m chiocca.v2.ipe grava docs/ipe_numeros.json."""
    docs: dict[str, tuple[str, str]] = {}
    arquivos = []
    for ano, p, tab in _tabelas(brutos):
        arquivos.append(_fonte(ano, p))
        for r in tab.itertuples(index=False):
            docs.setdefault(r.id_documento, (r.Categoria, r.Assunto))
    por_categoria = {}
    for nome, c in CATEGORIAS.items():
        assuntos = [x[1] for x in docs.values() if x[0] == nome]
        omitidos = sum(nomes.tem_nome_de_pessoa(a.strip()) for a in assuntos)
        por_categoria[c] = {"documentos": len(assuntos), "assuntos_omitidos": omitidos}
    total = sum(x["documentos"] for x in por_categoria.values())
    omit = sum(x["assuntos_omitidos"] for x in por_categoria.values())
    return {"gerado_por": "python -m chiocca.v2.ipe", "o_que_e": "assuntos omitidos pelo detector de nomes do leitor "
            "(leitor-f1-1, sem mudança) em todos os fatos relevantes e comunicados ao mercado dos dados abertos do IPE "
            "de 2010 a 2024, um por documento entregue (pelo link do ENET)", "arquivos": arquivos, "documentos": total,
            "assuntos_omitidos": omit, "fracao_omitidos": round(omit / total, 3) if total else None,
            "por_categoria": por_categoria}  # fmt: skip


if __name__ == "__main__":
    import json

    r = contar()
    NUMEROS.write_text(json.dumps(r, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in r.items() if k != "arquivos"}, ensure_ascii=False, indent=1))
