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
        "vazio": "sem assunto nos dados abertos; ver o documento na CVM",
        "nota": "Fatos relevantes e comunicados ao mercado entregues à CVM até a data, pelos dados abertos do IPE "
        "(desde 2010): data de entrega, categoria, assunto e link. O conteúdo dos documentos não é baixado, lido nem "
        "resumido, e a lista não gera alerta, nota nem ordenação. As contagens são de documentos: versões, "
        "reapresentações e versões em inglês contam separadamente; na lista, as versões do mesmo documento e os "
        "documentos com a mesma data, categoria e assunto aparecem numa linha só, com um link para cada um.",
        "sem_itens": "Nenhum fato relevante ou comunicado ao mercado entregue até a data nos dados abertos do IPE "
        "(desde 2010).",
    },
    "en": {
        "omitido": "subject omitted (possible person's name); see the document at the CVM",
        "vazio": "no subject in the open data; see the document at the CVM",
        "nota": "Material facts and market notices filed with the CVM by the date, from the IPE open data (since "
        "2010): filing date, category, subject (as filed, in Portuguese) and link. The content of the documents "
        "is not downloaded, read or summarized, and the list generates no alert, score or ranking. The counts are "
        "of documents: versions, resubmissions and English versions count separately; in the list, versions of the "
        "same document and documents with the same date, category and subject appear on a single line, with a link "
        "to each one.",
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


def _maiusculas(texto: str) -> bool:
    """Assunto escrito todo em maiúsculas (toda letra com caixa está em maiúscula)."""
    letras = [c for c in texto if c.lower() != c.upper()]
    return bool(letras) and all(c.isupper() for c in letras)


def _corridas(tokens: list[str]) -> list[tuple[int, list[str]]]:
    """As sequências de palavras com inicial maiúscula (com conectores no meio), como no detector, mas de qualquer
    tamanho, com a posição da primeira palavra."""
    out, i = [], 0
    while i < len(tokens):
        if not nomes._palavra_de_nome(tokens[i]):
            i += 1
            continue
        palavras, k = [tokens[i]], i + 1
        while k < len(tokens) and not nomes._fim_de_frase(palavras[-1]):
            conector = nomes._limpo(tokens[k]).lower() in nomes.CONECTORES
            if conector and k + 1 < len(tokens) and nomes._palavra_de_nome(tokens[k + 1]):
                palavras += [tokens[k], tokens[k + 1]]
                k += 2
            elif nomes._palavra_de_nome(tokens[k]):
                palavras.append(tokens[k])
                k += 1
            else:
                break
            if nomes._marca(palavras[-1]):  # a marca de empresa encerra a sequência, como no detector
                break
        out.append((i, palavras))
        i = k
    return out


def _palavra_maiuscula_no_meio(texto: str) -> bool:
    """Uma palavra com inicial maiúscula fora do começo do assunto que não está nas exceções do detector (vocabulário,
    lugares e companhias do cadastro): um sobrenome sozinho escapa da regra de duas palavras do detector. A sequência
    de palavras maiúsculas que é exceção inteira ("São Paulo", uma companhia do cadastro) não conta; a primeira palavra
    do assunto não conta (cada parte separada por "||" é um assunto); depois de pontuação, conta. Siglas também
    contam."""
    for parte in texto.split("||"):
        tokens = nomes._TOKEN.findall(parte)
        for inicio, palavras in _corridas(tokens):
            nucleo = [w for w in palavras if nomes._limpo(w).lower() not in nomes.CONECTORES]
            fim = inicio + len(palavras)
            seguinte = tokens[fim] if fim < len(tokens) else None
            if nomes._marca(nucleo[-1]) or nomes._marca(seguinte):  # nome de empresa, como no detector
                continue
            anterior = tokens[inicio - 1] if inicio > 0 else ""
            com_anterior = [anterior, *palavras] if anterior[:1].isupper() else palavras  # "São Paulo": "São" é função
            if nomes._excecao(palavras) or nomes._excecao(com_anterior) or all(nomes._excecao([w]) for w in nucleo):
                continue
            if inicio == 0 and len(nucleo) == 1:
                continue
            return True
    return False


def regra_de_omissao(texto: str) -> str | None:
    """Por que o assunto sai omitido, ou None se pode ser mostrado. Primeiro o detector de nomes do leitor (sem
    mudança); depois as regras mais conservadoras de 12/11/2026, que só omitem mais: assunto todo em maiúsculas e
    palavra com inicial maiúscula no meio da frase fora das exceções."""
    if nomes.tem_nome_de_pessoa(texto):
        return "detector"
    if _maiusculas(texto):
        return "maiusculas"
    if _palavra_maiuscula_no_meio(texto):
        return "palavra_maiuscula"
    return None


def assunto(texto: str, lang: str) -> tuple[str, bool, bool]:
    """O assunto como vai para a tela: (texto, omitido, vazio). Vazio nos dados abertos vira um aviso; com possível
    nome de pessoa (pelas regras acima), omitido."""
    t = texto.strip()
    if not t:
        return TEXTOS[lang]["vazio"], False, True
    if regra_de_omissao(t):
        return TEXTOS[lang]["omitido"], True, False
    return t, False, False


def protocolo_base(protocolo: str) -> str | None:
    """O protocolo de entrega sem os dois dígitos da versão ("020990IPE13012023" + "01"/"02" + "04493912-11"): as
    versões do mesmo documento costumam ter o mesmo protocolo-base."""
    m = re.fullmatch(r"(\d{6}IPE\d{8})\d{2}(\d+-\d+)", protocolo.strip())
    return f"{m.group(1)}·{m.group(2)}" if m else None


def link_antigo(link: str | None) -> bool:
    """Link dos dados abertos de 2010 a 2014 (numSequencia=0 e numVersao=0): na conferência de 12/11/2026, 4 de 5 não
    entregaram o documento."""
    m = _LINK.search(link or "")
    return m is not None and m.group(2) == "0" and m.group(3) == "0"


def _agrupa(itens: list[dict[str, Any]], originais: list[str]) -> list[int]:
    """O grupo de cada item, para mostrar numa linha só: as versões do mesmo documento (mesmo protocolo-base) e os
    documentos com a mesma data, categoria e assunto original (comparado aqui, na geração; o JSON não guarda o assunto
    omitido). Grupos numerados na ordem da lista."""
    pai = list(range(len(itens)))

    def raiz(i: int) -> int:
        while pai[i] != i:
            pai[i] = pai[pai[i]]
            i = pai[i]
        return i

    def junta(a: int, b: int) -> None:
        ra, rb = raiz(a), raiz(b)
        if ra != rb:
            pai[max(ra, rb)] = min(ra, rb)

    vistos: dict[tuple[str, ...], int] = {}
    for i, (x, original) in enumerate(zip(itens, originais, strict=True)):
        chaves: list[tuple[str, ...]] = []
        base_ = protocolo_base(x["protocolo"] or "")
        if base_:
            chaves.append(("protocolo", x["categoria"], base_))
        if original.strip():
            chaves.append(("assunto", x["categoria"], x["data_entrega"], original.strip()))
        for k in chaves:
            if k in vistos:
                junta(vistos[k], i)
            else:
                vistos[k] = i
    numeros: dict[int, int] = {}
    return [numeros.setdefault(raiz(i), len(numeros) + 1) for i in range(len(itens))]


def lista(cd_cvm: str, data_referencia: date, lang: str, brutos: Path | None = None) -> dict[str, Any]:
    """Os fatos relevantes e comunicados ao mercado da companhia entregues até a data, com a linhagem de cada item."""
    t = TEXTOS[lang]
    limite = min(data_referencia, DATA_REFERENCIA_MAXIMA).isoformat()
    cd = str(cd_cvm).strip().lstrip("0")
    linhas: list[tuple[dict[str, Any], str]] = []
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
            texto, omitido, vazio = assunto(r.Assunto, lang)
            link = r.Link_Download.strip() or None
            linhas.append(({"categoria": CATEGORIAS[r.Categoria], "categoria_cvm": r.Categoria,
                            "data_entrega": r.Data_Entrega.strip(), "assunto": texto, "assunto_omitido": omitido,
                            "assunto_vazio": vazio, "link": link, "link_pode_nao_abrir": link_antigo(link),
                            "id_documento": r.id_documento, "protocolo": r.Protocolo_Entrega.strip() or None,
                            "versao": None if pd.isna(r.versao) else int(r.versao), "grupo": 0, "fonte": fonte},
                           r.Assunto))  # fmt: skip
    linhas.sort(key=lambda x: x[0]["id_documento"], reverse=True)
    linhas.sort(key=lambda x: x[0]["data_entrega"], reverse=True)
    linhas.sort(key=lambda x: ORDEM_CATEGORIA[x[0]["categoria"]])
    itens = [x for x, _ in linhas]
    for x, g in zip(itens, _agrupa(itens, [o for _, o in linhas]), strict=True):
        x["grupo"] = g
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
            docs.setdefault(r.id_documento, (r.Categoria, r.Assunto.strip()))
    por_categoria = {}
    for nome, c in CATEGORIAS.items():
        assuntos = [x[1] for x in docs.values() if x[0] == nome]
        regras = [regra_de_omissao(a) if a else "vazio" for a in assuntos]
        por_categoria[c] = {"documentos": len(assuntos), "assuntos_vazios": regras.count("vazio"),
                            "assuntos_omitidos": sum(r not in (None, "vazio") for r in regras),
                            "omitidos_pelo_detector": regras.count("detector"),
                            "omitidos_por_maiusculas": regras.count("maiusculas"),
                            "omitidos_por_palavra_maiuscula": regras.count("palavra_maiuscula"),
                            "assuntos_mostrados": regras.count(None)}  # fmt: skip
    tot = {k: sum(x[k] for x in por_categoria.values()) for k in next(iter(por_categoria.values()))}
    return {"gerado_por": "python -m chiocca.v2.ipe", "o_que_e": "assuntos dos fatos relevantes e comunicados ao "
            "mercado dos dados abertos do IPE de 2010 a 2024, um por documento entregue (pelo link do ENET): vazios, "
            "omitidos (pelo detector de nomes do leitor, sem mudança, e pelas regras mais conservadoras de 12/11/2026: "
            "todo em maiúsculas e palavra com inicial maiúscula no meio da frase fora das exceções) e mostrados",
            "arquivos": arquivos, **tot,
            "fracao_omitidos": round(tot["assuntos_omitidos"] / tot["documentos"], 3) if tot["documentos"] else None,
            "por_categoria": por_categoria}  # fmt: skip


if __name__ == "__main__":
    import json

    r = contar()
    NUMEROS.write_text(json.dumps(r, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in r.items() if k != "arquivos"}, ensure_ascii=False, indent=1))
