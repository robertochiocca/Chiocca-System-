"""Notas explicativas (PDF) e relatório do auditor (texto) de uma DFP no ENET da CVM, com cache fora do git.

Rotas, confirmadas em 11/11/2026 (docs/fontes.md):
- a página do documento, frmGerenciaPaginaFRE.aspx?NumeroSequencialDocumento=<n>&CodigoTipoInstituicao=2, numa sessão
  com cookie; algumas sessões devolvem página reduzida (sem o menu), e então a sessão é refeita;
- o grupo é escolhido por postback do ASP.NET (__EVENTTARGET=cmbGrupo): "Notas Explicativas" (valor PDF|<código>) e
  "Pareceres e Declarações"; a resposta traz o endereço frmExibirArquivoFRE.aspx do conteúdo;
- as notas vêm como PDF em base64 no campo hdnConteudoArquivo (é o mesmo arquivo do pacote do documento: mesmo
  SHA-256 na Americanas, exercício 2021); o relatório do auditor vem como texto, com o tipo no título do item
  ("Relatório do Auditor Independente - Sem Ressalva").

Regras de acesso (decisão de 11/11/2026): uma requisição por vez, com intervalo mínimo entre elas; novas tentativas
com espera crescente (2, 4, 8 e 16 segundos); integridade de cada download (tamanho igual ao anunciado; o PDF começa
com %PDF-, tem %%EOF no fim e abre no pypdf com páginas; o texto do relatório tem título e corpo); cache em
data/cache/enet_documentos/<NumeroSequencialDocumento>/ (fora do git), com o SHA-256 e a hora do download; identificador
de cliente genérico.
"""

from __future__ import annotations

import base64
import binascii
import hashlib
import html
import http.client
import http.cookiejar
import io
import json
import re
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pypdf

from chiocca import base

ENET = "https://www.rad.cvm.gov.br/ENET/"
AGENTE = "Mozilla/5.0 (compatible; leitor-documentos-publicos/1.0)"
INTERVALO = 2.0  # segundos entre o fim de uma requisição e o início da seguinte
ESPERAS = (2, 4, 8, 16)
CACHE = base.RAIZ / "data" / "cache" / "enet_documentos"

_trava = threading.Lock()
_ultima = [0.0]


class FalhaDocumento(Exception):
    """O ENET não entregou o conteúdo (ou entregou incompleto) depois das tentativas."""


class SemConteudo(Exception):
    """O documento não tem o grupo pedido (por exemplo, DFP sem notas explicativas anexadas)."""


def _abre() -> urllib.request.OpenerDirector:
    op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
    op.addheaders = [("User-Agent", AGENTE)]
    return op


def _pede(op: urllib.request.OpenerDirector, url: str, dados: bytes | None = None, referer: str | None = None) -> bytes:
    """Uma requisição por vez, com o intervalo mínimo; recusa corpo menor que o tamanho anunciado."""
    with _trava:
        espera = INTERVALO - (time.monotonic() - _ultima[0])
        if espera > 0:
            time.sleep(espera)
        try:
            cabecalhos = {"Referer": referer} if referer else {}
            if dados is not None:
                cabecalhos["Content-Type"] = "application/x-www-form-urlencoded"
            with op.open(urllib.request.Request(url, data=dados, headers=cabecalhos), timeout=180) as r:
                corpo = bytes(r.read())
                anunciado = r.headers.get("Content-Length")
            if anunciado is not None and int(anunciado) != len(corpo):
                raise FalhaDocumento(f"download incompleto: {len(corpo)} de {anunciado} bytes")
            return corpo
        finally:
            _ultima[0] = time.monotonic()


def _com_tentativas(f: Any, *args: Any) -> Any:
    erro: Exception | None = None
    for i in range(len(ESPERAS) + 1):
        try:
            return f(*args)
        except SemConteudo:
            raise
        except urllib.error.HTTPError as e:
            if e.code < 500 and e.code != 429:
                raise FalhaDocumento(f"HTTP {e.code}") from e
            erro = e
        except (OSError, http.client.HTTPException, FalhaDocumento, binascii.Error, ValueError) as e:
            erro = e
        if i < len(ESPERAS):
            time.sleep(ESPERAS[i])
    raise FalhaDocumento(str(erro))


def _opcoes(pagina: str, nome: str) -> list[tuple[str, str]]:
    m = re.search(rf'<select name="{nome}"[^>]*>(.*?)</select>', pagina, re.S)
    if not m:
        return []
    return [
        (html.unescape(v), html.unescape(t).strip())
        for v, t in re.findall(r'<option[^>]*value="([^"]*)"[^>]*>([^<]*)</option>', m.group(1))
    ]


def _conteudo_do_grupo(num_doc: str, comeco_do_grupo: str, comeco_do_quadro: str | None) -> tuple[str, str, str]:
    """(endereço, título do item, página) do conteúdo de um grupo do documento, numa sessão nova."""
    op = _abre()
    menu = f"{ENET}frmGerenciaPaginaFRE.aspx?NumeroSequencialDocumento={num_doc}&CodigoTipoInstituicao=2"
    pagina = _pede(op, menu).decode("utf-8", "replace")
    grupos = _opcoes(pagina, "cmbGrupo")
    if not grupos:
        raise FalhaDocumento("página do documento sem o menu (sessão reduzida)")
    escolhido = [v for v, t in grupos if t.lower().startswith(comeco_do_grupo.lower())]
    if not escolhido:
        raise SemConteudo(f"documento {num_doc} sem o grupo {comeco_do_grupo!r}")
    campos = {
        k: html.unescape(v)
        for k, v in re.findall(r'<input type="hidden" name="([^"]+)" id="[^"]*" value="([^"]*)"', pagina)
    }
    quadros = _opcoes(pagina, "cmbQuadro")
    campos |= {
        "__EVENTTARGET": "cmbGrupo",
        "__EVENTARGUMENT": "",
        "cmbGrupo": escolhido[0],
        "cmbQuadro": quadros[0][0] if quadros else "",
    }
    resposta = _pede(op, menu, urllib.parse.urlencode(campos).encode(), referer=menu).decode("utf-8", "replace")
    alvo = re.search(r"(frmExibirArquivoFRE\.aspx\?[^\"' <]+)", resposta)
    if not alvo:
        raise FalhaDocumento("resposta do grupo sem o endereço do conteúdo")
    url = html.unescape(alvo.group(1))
    titulo = next(t for v, t in grupos if v == escolhido[0])
    if comeco_do_quadro is not None:
        itens = [(v, t) for v, t in _opcoes(resposta, "cmbQuadro") if t.lower().startswith(comeco_do_quadro.lower())]
        if not itens:
            raise SemConteudo(f"documento {num_doc} sem o item {comeco_do_quadro!r}")
        codigo = itens[0][0].split("|")[-1]
        url = re.sub(r"CodigoQuadro=\d+", f"CodigoQuadro={codigo}", url)
        titulo = itens[0][1]
    conteudo = _pede(op, ENET + url, referer=menu).decode("utf-8", "replace")
    return ENET + url, titulo, conteudo


def confere_pdf(conteudo: bytes) -> int:
    """Integridade do PDF: assinatura, fim de arquivo e páginas no pypdf. Devolve o número de páginas."""
    if not conteudo.startswith(b"%PDF-"):
        raise FalhaDocumento("o conteúdo não é PDF")
    if b"%%EOF" not in conteudo[-2048:]:
        raise FalhaDocumento("PDF sem %%EOF no fim (download cortado?)")
    paginas = len(pypdf.PdfReader(io.BytesIO(conteudo)).pages)
    if paginas < 1:
        raise FalhaDocumento("PDF sem páginas")
    return paginas


def _baixa_notas(num_doc: str) -> tuple[bytes, dict[str, Any]]:
    url, titulo, pagina = _conteudo_do_grupo(num_doc, "Notas Explicativas", None)
    m = re.search(r'hdnConteudoArquivo"[^>]*value="([^"]+)"', pagina)
    if not m:
        raise FalhaDocumento("página das notas sem o PDF")
    pdf = base64.b64decode(m.group(1), validate=True)
    paginas = confere_pdf(pdf)
    return pdf, {"url": url, "titulo": titulo, "paginas": paginas}


def texto_do_relatorio(pagina: str) -> tuple[str, str]:
    """(título, texto) da página do relatório do auditor no ENET."""
    t = re.search(r"<h2[^>]*>(.*?)</h2>", pagina, re.S)
    corpo = re.search(r"<div style='white-space: pre-line;'>(.*?)</div>", pagina, re.S)
    if not t or not corpo:
        raise FalhaDocumento("página do relatório sem título ou sem texto")
    texto = html.unescape(re.sub(r"<br\s*/?>", "\n", corpo.group(1)))
    texto = re.sub(r"<[^>]+>", " ", texto)
    titulo = re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", t.group(1)))).strip()
    if len(texto.strip()) < 200:
        raise FalhaDocumento("relatório do auditor curto demais")
    return titulo, texto


def _baixa_relatorio(num_doc: str) -> tuple[bytes, dict[str, Any]]:
    url, _, pagina = _conteudo_do_grupo(num_doc, "Pareceres e Declarações", "Relatório")
    titulo, texto = texto_do_relatorio(pagina)
    return texto.encode("utf-8"), {"url": url, "titulo": titulo}


def _cache(num_doc: str, nome: str, baixa: Any, pasta: Path) -> tuple[bytes | None, dict[str, Any]]:
    """Conteúdo do cache, se houver; senão baixa (com tentativas), confere e grava. Grupo ausente fica registrado."""
    destino = pasta / str(num_doc)
    meta_arq = destino / f"{nome}.json"
    if meta_arq.exists():
        meta = json.loads(meta_arq.read_text(encoding="utf-8"))
        if meta.get("sem_conteudo"):
            return None, meta
        dados = (destino / meta["arquivo"]).read_bytes()
        if hashlib.sha256(dados).hexdigest() == meta["sha256"]:
            return dados, meta
    destino.mkdir(parents=True, exist_ok=True)
    quando = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    try:
        dados, meta = _com_tentativas(baixa, str(num_doc))
    except SemConteudo as e:
        meta = {"sem_conteudo": True, "motivo": str(e), "baixado_em_utc": quando}
        meta_arq.write_text(json.dumps(meta, ensure_ascii=False, indent=1), encoding="utf-8")
        return None, meta
    arquivo = f"{nome}.pdf" if dados.startswith(b"%PDF-") else f"{nome}.txt"
    (destino / arquivo).write_bytes(dados)
    meta |= {
        "arquivo": arquivo,
        "bytes": len(dados),
        "sha256": hashlib.sha256(dados).hexdigest(),
        "baixado_em_utc": quando,
        "num_doc": str(num_doc),
    }
    meta_arq.write_text(json.dumps(meta, ensure_ascii=False, indent=1), encoding="utf-8")
    return dados, meta


def notas(num_doc: str, pasta: Path = CACHE, rede: bool = True) -> tuple[bytes | None, dict[str, Any]]:
    if not rede and not (pasta / str(num_doc) / "notas.json").exists():
        return None, {"fora_do_cache": True}
    return _cache(num_doc, "notas", _baixa_notas, pasta)


def relatorio_do_auditor(num_doc: str, pasta: Path = CACHE, rede: bool = True) -> tuple[str | None, dict[str, Any]]:
    if not rede and not (pasta / str(num_doc) / "relatorio.json").exists():
        return None, {"fora_do_cache": True}
    dados, meta = _cache(num_doc, "relatorio", _baixa_relatorio, pasta)
    return (dados.decode("utf-8") if dados is not None else None), meta
