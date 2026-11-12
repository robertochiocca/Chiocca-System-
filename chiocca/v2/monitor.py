"""Monitor da CVM (Fase F2a; decisões de 07/11/2026 e 12/11/2026): compara os índices dos dados abertos de DFP, ITR e
IPE com o que está armazenado e registra cada novidade numa fila de revisão, com metadados e hash. A fila só lista:
uma pessoa decide o que fazer, e nada muda os dados sozinho (o monitor não escreve em data/brutos nem no armazém).

    python -m chiocca.v2.monitor verificar [--tipos DFP,ITR,IPE] [--anos 2010-2026]
    python -m chiocca.v2.monitor listar

O que é lido, uma requisição por vez, com intervalo e novas tentativas:
- IPE: o arquivo do ano (ipe_cia_aberta_<ano>.zip), que só tem os metadados de cada documento; o conteúdo dos
  documentos nunca é baixado;
- DFP e ITR: só o índice de cada arquivo (dfp_cia_aberta_<ano>.csv ou itr_cia_aberta_<ano>.csv: companhia, data de
  referência, versão, data de entrega, identificador e link), lido por faixas de bytes (HTTP Range) de dentro do zip
  remoto, com o CRC32 conferido; as demonstrações não são baixadas.

O que é guardado, em data/monitor/ (fora do git):
- fila.jsonl: uma linha por novidade (documento novo no índice, alterado ou removido), com tipo, arquivo, chave,
  companhia, data de entrega, categoria, link, hash dos metadados (SHA-256 da linha do índice) e situação "a_revisar";
- indices/<tipo>_<ano>.json: o estado de cada índice na última verificação, só chave e hash (sem o texto do assunto).
Documento entregue depois de 31/12/2024 fica só com metadados e hash (decisão de 07/11/2026): nada é baixado, lido,
resumido ou extraído, e o assunto (IPE) não é guardado nem mostrado; só entra no hash.

O armazenado de partida é o índice dos arquivos em data/brutos/cvm (DFP e IPE de 2010 a 2024). Sem arquivo armazenado
nem verificação anterior (ITR, IPE de 2025 em diante), a primeira verificação registra só uma linha de base (quantos
documentos e o hash do índice); as seguintes registram cada novidade.
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
import struct
import sys
import time
import urllib.error
import urllib.request
import zipfile
import zlib
from collections.abc import Callable
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

from chiocca import base
from chiocca.dados import AGENTE, BASE
from chiocca.v2 import ipe
from chiocca.v2.lacre import DATA_REFERENCIA_MAXIMA

PASTA = base.RAIZ / "data" / "monitor"
INTERVALO = 1.0  # segundos entre requisições
LIMITE = DATA_REFERENCIA_MAXIMA.isoformat()
TIPOS = ("DFP", "ITR", "IPE")
PRIMEIRO_ANO = {"DFP": 2010, "ITR": 2011, "IPE": 2010}

LerFaixa = Callable[[int, int], bytes]  # (início, fim inclusive) -> bytes


def nome_arquivo(tipo: str, ano: int) -> str:
    return f"{tipo.lower()}_cia_aberta_{ano}.zip"


def url(tipo: str, ano: int) -> str:
    return f"{BASE}/DOC/{tipo}/DADOS/{nome_arquivo(tipo, ano)}"


def membro_indice(tipo: str, ano: int) -> str:
    return f"{tipo.lower()}_cia_aberta_{ano}.csv"


# ---- leitura de um só arquivo de dentro de um zip remoto, por faixas de bytes ----


class ZipRemotoInvalido(Exception):
    pass


def membro_remoto(ler: LerFaixa, tamanho: int, membro: str) -> bytes:
    """Os bytes de um arquivo de dentro do zip, lendo só o diretório central e o próprio arquivo (sem zip64)."""
    fim = ler(max(0, tamanho - 65_557), tamanho - 1)
    i = fim.rfind(b"PK\x05\x06")
    if i < 0:
        raise ZipRemotoInvalido("fim do diretório central não achado")
    _, _, _, _, _, tam_cd, ini_cd, _ = struct.unpack("<IHHHHIIH", fim[i : i + 22])
    if 0xFFFFFFFF in (tam_cd, ini_cd):
        raise ZipRemotoInvalido("zip64 não suportado")
    cd = ler(ini_cd, ini_cd + tam_cd - 1)
    p = 0
    while p + 46 <= len(cd):
        if cd[p : p + 4] != b"PK\x01\x02":
            raise ZipRemotoInvalido("diretório central inválido")
        metodo, crc, tam_comp, n_nome, n_extra, n_coment, ini_local = (
            struct.unpack("<H", cd[p + 10 : p + 12])[0],
            *struct.unpack("<I", cd[p + 16 : p + 20]),
            *struct.unpack("<I", cd[p + 20 : p + 24]),
            *struct.unpack("<HHH", cd[p + 28 : p + 34]),
            *struct.unpack("<I", cd[p + 42 : p + 46]),
        )
        nome = cd[p + 46 : p + 46 + n_nome].decode("cp437")
        if nome == membro:
            cab = ler(ini_local, ini_local + 29)
            if cab[:4] != b"PK\x03\x04":
                raise ZipRemotoInvalido("cabeçalho local inválido")
            n_nome_l, n_extra_l = struct.unpack("<HH", cab[26:30])
            ini_dados = ini_local + 30 + n_nome_l + n_extra_l
            dados = ler(ini_dados, ini_dados + tam_comp - 1) if tam_comp else b""
            if metodo == 8:
                saida = zlib.decompress(dados, -15)
            elif metodo == 0:
                saida = dados
            else:
                raise ZipRemotoInvalido(f"método de compressão {metodo} não suportado")
            if zlib.crc32(saida) & 0xFFFFFFFF != crc:
                raise ZipRemotoInvalido("CRC32 não confere")
            return saida
        p += 46 + n_nome + n_extra + n_coment
    raise ZipRemotoInvalido(f"{membro} não está no zip")


def _pede(req: urllib.request.Request) -> tuple[int, dict[str, str], bytes]:
    for tentativa in range(5):
        try:
            with urllib.request.urlopen(req, timeout=300) as r:
                return r.status, dict(r.headers), bytes(r.read())
        except urllib.error.HTTPError as e:
            if e.code < 500 or tentativa == 4:
                raise
        except OSError:
            if tentativa == 4:
                raise
        time.sleep(2 ** (tentativa + 1))
    raise RuntimeError(req.full_url)


def _rede_faixas(endereco: str) -> tuple[LerFaixa, int]:
    time.sleep(INTERVALO)
    _, cab, _ = _pede(urllib.request.Request(endereco, method="HEAD", headers={"User-Agent": AGENTE}))
    tamanho = int(cab.get("Content-Length") or cab.get("content-length") or 0)

    def ler(inicio: int, fim: int) -> bytes:
        time.sleep(INTERVALO)
        req = urllib.request.Request(endereco, headers={"User-Agent": AGENTE, "Range": f"bytes={inicio}-{fim}"})
        status, _, dados = _pede(req)
        if status != 206 or len(dados) != fim - inicio + 1:
            raise ZipRemotoInvalido("o servidor não devolveu a faixa pedida (sem suporte a Range)")
        return dados

    return ler, tamanho


def _rede_arquivo(endereco: str) -> bytes:
    time.sleep(INTERVALO)
    return _pede(urllib.request.Request(endereco, headers={"User-Agent": AGENTE}))[2]


# ---- índices ----


def _linhas(csv_bytes: bytes) -> list[dict[str, str]]:
    return list(csv.DictReader(io.StringIO(csv_bytes.decode("latin1")), delimiter=";"))


def chave(tipo: str, r: dict[str, str]) -> str:
    """A identidade de um documento no índice: no IPE, o link do ENET (numProtocolo, numSequencia e numVersao; de 2010 a
    2014 o protocolo de entrega vem vazio, e um protocolo pode ter mais de um documento); em DFP e ITR, companhia, data
    de referência, versão e identificador."""
    if tipo == "IPE":
        return ipe.id_documento(r["Link_Download"].strip(), r["Categoria"], r["Assunto"], r["Data_Entrega"])
    return f"{r['CD_CVM'].strip()}|{r['DT_REFER'].strip()}|{r['VERSAO'].strip()}|{r['ID_DOC'].strip()}"


def chaves(tipo: str, linhas: list[dict[str, str]]) -> list[str]:
    """As chaves das linhas de um índice; a chave vazia, ou repetida com conteúdo diferente, vira o hash da linha (aí
    não há "alterado", só "novo" e "removido")."""
    base_ = [chave(tipo, r) for r in linhas]
    hashes = [hash_metadados(r) for r in linhas]
    por: dict[str, set[str]] = {}
    for k, h in zip(base_, hashes, strict=True):
        por.setdefault(k, set()).add(h)
    return [k if k and len(por[k]) == 1 else f"linha-{h}" for k, h in zip(base_, hashes, strict=True)]


def hash_metadados(r: dict[str, str]) -> str:
    return hashlib.sha256(json.dumps(r, ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()


def data_entrega(tipo: str, r: dict[str, str]) -> str:
    return (r.get("Data_Entrega") if tipo == "IPE" else r.get("DT_RECEB")) or ""


def registro(tipo: str, ano: int, r: dict[str, str], evento: str, k: str | None = None) -> dict[str, Any]:
    """A linha da fila: só metadados e hash; o assunto do IPE só até 31/12/2024."""
    entrega = data_entrega(tipo, r).strip()
    depois = not entrega or entrega > LIMITE
    out: dict[str, Any] = {"evento": evento, "tipo": tipo, "arquivo": nome_arquivo(tipo, ano), "ano_arquivo": ano,
                           "chave": k or chave(tipo, r), "data_entrega": entrega or None,
                           "depois_de_31_12_2024": depois, "hash_metadados": hash_metadados(r)}  # fmt: skip
    if tipo == "IPE":
        out |= {"cd_cvm": r["Codigo_CVM"].strip(), "companhia": r["Nome_Companhia"].strip(),
                "categoria": r["Categoria"].strip(), "tipo_documento": r["Tipo"].strip(),
                "data_referencia_documento": r["Data_Referencia"].strip(), "protocolo": r["Protocolo_Entrega"].strip(),
                "versao": r["Versao"].strip(), "link": r["Link_Download"].strip()}  # fmt: skip
        if not depois:
            out["assunto"] = r["Assunto"].strip()
    else:
        out |= {"cd_cvm": r["CD_CVM"].strip(), "companhia": r["DENOM_CIA"].strip(), "categoria": r["CATEG_DOC"].strip(),
                "data_referencia_documento": r["DT_REFER"].strip(), "versao": r["VERSAO"].strip(),
                "id_doc": r["ID_DOC"].strip(), "link": r["LINK_DOC"].strip()}  # fmt: skip
    return out


def indice_atual(tipo: str, ano: int, faixas: Callable[[str], tuple[LerFaixa, int]] = _rede_faixas,
                 arquivo_inteiro: Callable[[str], bytes] = _rede_arquivo) -> bytes:  # fmt: skip
    """Os bytes do índice de agora nos dados abertos: o IPE inteiro (só metadados); de DFP e ITR, só o índice."""
    if tipo == "IPE":
        with zipfile.ZipFile(io.BytesIO(arquivo_inteiro(url(tipo, ano)))) as z:
            return z.read(membro_indice(tipo, ano))
    ler, tamanho = faixas(url(tipo, ano))
    return membro_remoto(ler, tamanho, membro_indice(tipo, ano))


def estado_armazenado(tipo: str, ano: int, pasta: Path, brutos: Path) -> dict[str, str] | None:
    """chave -> hash do armazenado: a última verificação do monitor ou, na primeira vez, o arquivo dos brutos."""
    salvo = pasta / "indices" / f"{tipo.lower()}_{ano}.json"
    if salvo.exists():
        return json.loads(salvo.read_text(encoding="utf-8"))["hashes"]  # type: ignore[no-any-return]
    local = brutos / nome_arquivo(tipo, ano)
    if local.exists():
        with zipfile.ZipFile(local) as z:
            linhas = _linhas(z.read(membro_indice(tipo, ano)))
            return dict(zip(chaves(tipo, linhas), (hash_metadados(r) for r in linhas), strict=True))
    return None


def _id(x: dict[str, Any]) -> tuple[str, str, str, str]:
    """A identidade de uma novidade, para não pôr a mesma duas vezes na fila."""
    return x["arquivo"], x.get("chave") or "", x["evento"], x.get("hash_metadados") or x.get("hash_indice", "")


def _ja_na_fila(fila: Path) -> set[tuple[str, str, str, str]]:
    if not fila.exists():
        return set()
    return {_id(json.loads(linha)) for linha in fila.read_text(encoding="utf-8").splitlines()}


def comparar(tipo: str, ano: int, atual: bytes, armazenado: dict[str, str] | None) -> list[dict[str, Any]]:
    """As novidades de um índice: documentos novos, alterados e removidos; sem armazenado, uma linha de base."""
    linhas = _linhas(atual)
    if armazenado is None:
        return [{"evento": "linha_de_base", "tipo": tipo, "arquivo": nome_arquivo(tipo, ano), "ano_arquivo": ano,
                 "documentos": len(linhas), "hash_indice": hashlib.sha256(atual).hexdigest()}]  # fmt: skip
    out = []
    vistas = set()
    for r, k in zip(linhas, chaves(tipo, linhas), strict=True):
        if k in vistas:  # linha repetida igual
            continue
        vistas.add(k)
        if k not in armazenado:
            out.append(registro(tipo, ano, r, "novo", k))
        elif armazenado[k] != hash_metadados(r):
            out.append(registro(tipo, ano, r, "alterado", k) | {"hash_anterior": armazenado[k]})
    for k in sorted(set(armazenado) - vistas):
        out.append({"evento": "removido_do_indice", "tipo": tipo, "arquivo": nome_arquivo(tipo, ano),
                    "ano_arquivo": ano, "chave": k, "hash_metadados": armazenado[k]})  # fmt: skip
    return out


def verificar(tipos: tuple[str, ...] = TIPOS, anos: range | None = None, pasta: Path = PASTA,
              brutos: Path | None = None, buscar: Callable[[str, int], bytes] = indice_atual,
              agora: Callable[[], str] | None = None) -> dict[str, Any]:  # fmt: skip
    """Uma verificação: lê cada índice, compara com o armazenado, acrescenta as novidades à fila e guarda o estado."""
    brutos = brutos or base.BRUTOS
    (pasta / "indices").mkdir(parents=True, exist_ok=True)
    fila = pasta / "fila.jsonl"
    ja = _ja_na_fila(fila)
    quando = (agora or (lambda: datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")))()
    resumo: dict[str, Any] = {"verificado_em": quando, "novidades": 0, "por_arquivo": {}, "erros": {}}
    ultimo = date.today().year
    for tipo in tipos:
        for ano in anos or range(PRIMEIRO_ANO[tipo], ultimo + 1):
            nome = nome_arquivo(tipo, ano)
            try:
                atual = buscar(tipo, ano)
            except (OSError, ZipRemotoInvalido, KeyError, zipfile.BadZipFile) as e:
                resumo["erros"][nome] = str(e)[:200]
                continue
            novidades = comparar(tipo, ano, atual, estado_armazenado(tipo, ano, pasta, brutos))
            novas = [x for x in novidades if _id(x) not in ja]
            with fila.open("a", encoding="utf-8") as f:
                for x in novas:
                    linha = x | {"registrado_em": quando, "situacao": "a_revisar"}
                    f.write(json.dumps(linha, ensure_ascii=False) + "\n")
            linhas = _linhas(atual)
            estado = dict(zip(chaves(tipo, linhas), (hash_metadados(r) for r in linhas), strict=True))
            (pasta / "indices" / f"{tipo.lower()}_{ano}.json").write_text(
                json.dumps({"arquivo": nome, "verificado_em": quando, "hash_indice": hashlib.sha256(atual).hexdigest(),
                            "documentos": len(estado), "hashes": estado}, ensure_ascii=False) + "\n",
                encoding="utf-8")  # fmt: skip
            resumo["por_arquivo"][nome] = len(novas)
            resumo["novidades"] += len(novas)
    return resumo


def listar(pasta: Path = PASTA) -> dict[str, Any]:
    """O resumo da fila: quantas novidades por tipo, evento e situação, e as datas de entrega (nada é lido dos
    documentos)."""
    fila = pasta / "fila.jsonl"
    linhas = [json.loads(x) for x in fila.read_text(encoding="utf-8").splitlines()] if fila.exists() else []
    contagem: dict[str, int] = {}
    for x in linhas:
        depois = " · depois de 31/12/2024" if x.get("depois_de_31_12_2024") else ""
        k = f"{x['tipo']} · {x['evento']} · {x['situacao']}{depois}"
        contagem[k] = contagem.get(k, 0) + 1
    return {"fila": str(fila), "linhas": len(linhas), "contagem": dict(sorted(contagem.items()))}


def _anos(texto: str) -> range:
    a, _, b = texto.partition("-")
    return range(int(a), int(b or a) + 1)


def main(argv: list[str]) -> None:
    if not argv or argv[0] not in ("verificar", "listar"):
        print(__doc__)
        sys.exit(2)
    if argv[0] == "listar":
        print(json.dumps(listar(), ensure_ascii=False, indent=1))
        return
    tipos = tuple(argv[argv.index("--tipos") + 1].split(",")) if "--tipos" in argv else TIPOS
    anos = _anos(argv[argv.index("--anos") + 1]) if "--anos" in argv else None
    print(json.dumps(verificar(tipos, anos), ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main(sys.argv[1:])
