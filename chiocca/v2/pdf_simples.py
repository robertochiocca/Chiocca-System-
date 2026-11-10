# Origem: DireitoAberto (github.com/robertochiocca/direitoaberto), backend/app/leitor/pdf_simples.py, commit
# 102e3e2d9d70e87249d8df9215737e2d98b6358d. Adaptado para o Chiocca System.
# O que mudou: saíram a página digitalizada, a página sem texto e a fonte inexistente (recursos do conjunto
# adversarial do leitor); entraram a transliteração dos caracteres fora do Windows-1252, a paginação automática e o
# rodapé em todas as páginas (o aviso fixo e o número da página); em 10/11/2026, o sinal de menos pela /Differences
# da codificação e o delta, o menor-ou-igual e o maior-ou-igual pela fonte Symbol, sem transliterar.
"""Gerador mínimo de PDF com texto, sem dependências e determinístico (o mesmo conteúdo dá os mesmos bytes).

Helvetica, quebra de linha simples e texto em Windows-1252, que cobre o português. O sinal de menos (−), que a
Helvetica tem mas o Windows-1252 não, entra pela /Differences da codificação, num código que o Windows-1252 deixa sem
caractere. O delta (Δ), o menor-ou-igual (≤) e o maior-ou-igual (≥) saem na fonte Symbol (também das 14 fontes padrão
do PDF): a Helvetica embutida nos leitores mais usados (o PDFium do Chrome, por exemplo) não tem esses glifos. Os
outros caracteres fora do Windows-1252 (por exemplo "÷" e "→") são transliterados. Uma linha que começa com "#" sai
em negrito e maior (título). Cada página leva o rodapé dado, com o número da página.
"""

from __future__ import annotations

import textwrap

LARGURA, ALTURA = 595, 842  # A4 em pontos
MARGEM_X, TOPO, BASE = 50, 800, 70
COLUNAS = 96
COLUNAS_TITULO = 74  # Helvetica-Bold 11 pt na mesma largura
LINHAS_POR_PAGINA = (TOPO - BASE) // 13
TRANSLITERA = {"÷": "/", "→": "->", "σ": "sigma", "≈": "~", "′": "'", "″": "''", "✓": "v"}
# caractere -> (código livre no Windows-1252, nome do glifo na Helvetica)
GLIFOS_EXTRAS = {"−": (0x81, "minus")}
# caractere -> código na codificação própria da fonte Symbol
SIMBOLOS = {"Δ": 0x44, "≤": 0xA3, "≥": 0xB3}
CODIFICACAO = (
    b"<< /Type /Encoding /BaseEncoding /WinAnsiEncoding /Differences ["
    + b" ".join(b"%d /%s" % (codigo, nome.encode()) for codigo, nome in sorted(GLIFOS_EXTRAS.values()))
    + b"] >>"
)


def _codificar(texto: str) -> bytes:
    saida = bytearray()
    for c in texto:
        if c in GLIFOS_EXTRAS:
            saida.append(GLIFOS_EXTRAS[c][0])
            continue
        try:
            saida += c.encode("cp1252")
        except UnicodeEncodeError:
            saida += TRANSLITERA.get(c, "?").encode("cp1252")
    return bytes(saida)


def _escapar(texto: str) -> bytes:
    bruto = _codificar(texto)
    return bruto.replace(b"\\", b"\\\\").replace(b"(", b"\\(").replace(b")", b"\\)")


def quebrar(linhas: list[str]) -> list[str]:
    """Quebra as linhas longas em pedaços que cabem na largura. Título longo vira mais de uma linha de título (a fonte
    é maior e em negrito, então cabem menos caracteres); item de lista ("- ") continua com recuo."""
    saida: list[str] = []
    for linha in linhas:
        if linha.startswith("#"):
            saida += ["# " + p for p in textwrap.wrap(linha.lstrip("# "), COLUNAS_TITULO) or [""]]
            continue
        recuo = " " * (len(linha) - len(linha.lstrip(" ")))
        continuacao = recuo + ("  " if linha.lstrip(" ").startswith("- ") else "")
        pedacos = textwrap.wrap(linha.strip(), COLUNAS - len(recuo), subsequent_indent=continuacao[len(recuo) :]) or [
            ""
        ]
        saida += [recuo + p for p in pedacos]
    return saida


def paginar(linhas: list[str], por_pagina: int = LINHAS_POR_PAGINA) -> list[list[str]]:
    quebradas = quebrar(linhas)
    return [quebradas[i : i + por_pagina] for i in range(0, len(quebradas), por_pagina)] or [[]]


def _trechos(texto: str) -> list[tuple[bool, str]]:
    """O texto em trechos seguidos: (True, símbolos da fonte Symbol) ou (False, texto da Helvetica)."""
    trechos: list[tuple[bool, str]] = []
    for c in texto:
        simbolo = c in SIMBOLOS
        if trechos and trechos[-1][0] == simbolo:
            trechos[-1] = (simbolo, trechos[-1][1] + c)
        else:
            trechos.append((simbolo, c))
    return trechos


def _mostrar(texto: str, fonte: bytes, tamanho: bytes) -> list[bytes]:
    """Operadores que mostram o texto na posição atual, trocando para a Symbol nos trechos de símbolo e voltando."""
    partes = [b"/" + fonte + b" " + tamanho + b" Tf"]
    for simbolo, trecho in _trechos(texto):
        if simbolo:
            partes += [b"/F3 " + tamanho + b" Tf", b"(" + bytes(SIMBOLOS[c] for c in trecho) + b") Tj",
                       b"/" + fonte + b" " + tamanho + b" Tf"]  # fmt: skip
        else:
            partes.append(b"(" + _escapar(trecho) + b") Tj")
    return partes


def _conteudo_pagina(linhas: list[str], rodape: list[str]) -> bytes:
    partes = [b"BT", b"13 TL", f"{MARGEM_X} {TOPO} Td".encode()]
    for linha in linhas:
        partes.append(b"T*")  # próxima linha
        if linha.startswith("#"):
            partes += _mostrar(linha.lstrip("# "), b"F2", b"11")
        else:
            partes += _mostrar(linha, b"F1", b"9")
    partes.append(b"ET")
    y = BASE - 20
    for texto in rodape:
        partes += [b"BT", f"{MARGEM_X} {y} Td".encode(), *_mostrar(texto, b"F1", b"7.5"), b"ET"]
        y -= 10
    return b"\n".join(partes)


def gerar_pdf(paginas: list[list[str]], rodapes: list[list[str]]) -> bytes:
    """Monta o PDF: `paginas[i]` são as linhas da página i, e `rodapes[i]`, as linhas do rodapé dela."""
    objetos: list[bytes] = []

    def novo(corpo: bytes) -> int:
        objetos.append(corpo)
        return len(objetos)

    codificacao = novo(CODIFICACAO)
    fonte = novo(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica /Encoding %d 0 R >>" % codificacao)
    negrito = novo(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold /Encoding %d 0 R >>" % codificacao)
    simbolo = novo(b"<< /Type /Font /Subtype /Type1 /BaseFont /Symbol >>")
    raiz_paginas = novo(b"")  # preenchido depois que as páginas existirem
    ids_paginas = []
    for linhas, rodape in zip(paginas, rodapes, strict=True):
        conteudo = _conteudo_pagina(linhas, rodape)
        fluxo = novo(b"<< /Length %d >>\nstream\n" % len(conteudo) + conteudo + b"\nendstream")
        ids_paginas.append(novo(
            b"<< /Type /Page /Parent %d 0 R /MediaBox [0 0 %d %d] "
            b"/Resources << /Font << /F1 %d 0 R /F2 %d 0 R /F3 %d 0 R >> >> /Contents %d 0 R >>"
            % (raiz_paginas, LARGURA, ALTURA, fonte, negrito, simbolo, fluxo)
        ))  # fmt: skip
    filhos = b" ".join(b"%d 0 R" % i for i in ids_paginas)
    objetos[raiz_paginas - 1] = b"<< /Type /Pages /Kids [%s] /Count %d >>" % (filhos, len(ids_paginas))
    catalogo = novo(b"<< /Type /Catalog /Pages %d 0 R >>" % raiz_paginas)

    saida = bytearray(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
    posicoes = []
    for numero, corpo in enumerate(objetos, 1):
        posicoes.append(len(saida))
        saida += b"%d 0 obj\n" % numero + corpo + b"\nendobj\n"
    xref = len(saida)
    saida += b"xref\n0 %d\n0000000000 65535 f \n" % (len(objetos) + 1)
    for pos in posicoes:
        saida += b"%010d 00000 n \n" % pos
    saida += b"trailer\n<< /Size %d /Root %d 0 R >>\nstartxref\n%d\n%%%%EOF\n" % (len(objetos) + 1, catalogo, xref)
    return bytes(saida)
