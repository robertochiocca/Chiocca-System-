# Origem: DireitoAberto (github.com/robertochiocca/direitoaberto), backend/app/leitor/pdf_simples.py, commit
# 102e3e2d9d70e87249d8df9215737e2d98b6358d. Adaptado para o Chiocca System.
# O que mudou: saíram a página digitalizada, a página sem texto e a fonte inexistente (recursos do conjunto
# adversarial do leitor); entraram a transliteração dos caracteres fora do Windows-1252, a paginação automática e o
# rodapé em todas as páginas (o aviso fixo e o número da página).
"""Gerador mínimo de PDF com texto, sem dependências e determinístico (o mesmo conteúdo dá os mesmos bytes).

Uma fonte (Helvetica), quebra de linha simples e texto em Windows-1252, que cobre o português. Caracteres fora do
Windows-1252 (por exemplo "−", "≥", "÷", "→" e "Δ") são transliterados. Uma linha que começa com "#" sai em negrito e
maior (título). Cada página leva o rodapé dado, com o número da página.
"""

from __future__ import annotations

import textwrap

LARGURA, ALTURA = 595, 842  # A4 em pontos
MARGEM_X, TOPO, BASE = 50, 800, 70
COLUNAS = 96
LINHAS_POR_PAGINA = (TOPO - BASE) // 13
TRANSLITERA = {"−": "-", "≥": ">=", "≤": "<=", "÷": "/", "→": "->", "Δ": "Delta ", "σ": "sigma", "≈": "~", "′": "'",
               "″": "''", "✓": "v"}  # fmt: skip


def _cp1252(texto: str) -> str:
    saida = []
    for c in texto:
        try:
            c.encode("cp1252")
            saida.append(c)
        except UnicodeEncodeError:
            saida.append(TRANSLITERA.get(c, "?"))
    return "".join(saida)


def _escapar(texto: str) -> bytes:
    bruto = _cp1252(texto).encode("cp1252")
    return bruto.replace(b"\\", b"\\\\").replace(b"(", b"\\(").replace(b")", b"\\)")


def quebrar(linhas: list[str]) -> list[str]:
    """Quebra as linhas longas em pedaços que cabem na largura (títulos ficam inteiros)."""
    saida: list[str] = []
    for linha in linhas:
        if linha.startswith("#"):
            saida.append(linha)
            continue
        recuo = " " * (len(linha) - len(linha.lstrip(" ")))
        pedacos = textwrap.wrap(linha.strip(), COLUNAS - len(recuo)) or [""]
        saida += [recuo + p for p in pedacos]
    return saida


def paginar(linhas: list[str], por_pagina: int = LINHAS_POR_PAGINA) -> list[list[str]]:
    quebradas = quebrar(linhas)
    return [quebradas[i : i + por_pagina] for i in range(0, len(quebradas), por_pagina)] or [[]]


def _conteudo_pagina(linhas: list[str], rodape: list[str]) -> bytes:
    partes = [b"BT", b"13 TL", f"{MARGEM_X} {TOPO} Td".encode()]
    for linha in linhas:
        if linha.startswith("#"):
            partes += [b"/F2 11 Tf", b"(" + _escapar(linha.lstrip("# ")) + b") '", b"/F1 9 Tf"]
        else:
            partes += [b"/F1 9 Tf", b"(" + _escapar(linha) + b") '"]
    partes.append(b"ET")
    y = BASE - 20
    for texto in rodape:
        partes += [b"BT /F1 7.5 Tf", f"{MARGEM_X} {y} Td".encode(), b"(" + _escapar(texto) + b") Tj ET"]
        y -= 10
    return b"\n".join(partes)


def gerar_pdf(paginas: list[list[str]], rodapes: list[list[str]]) -> bytes:
    """Monta o PDF: `paginas[i]` são as linhas da página i, e `rodapes[i]`, as linhas do rodapé dela."""
    objetos: list[bytes] = []

    def novo(corpo: bytes) -> int:
        objetos.append(corpo)
        return len(objetos)

    fonte = novo(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica /Encoding /WinAnsiEncoding >>")
    negrito = novo(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold /Encoding /WinAnsiEncoding >>")
    raiz_paginas = novo(b"")  # preenchido depois que as páginas existirem
    ids_paginas = []
    for linhas, rodape in zip(paginas, rodapes, strict=True):
        conteudo = _conteudo_pagina(linhas, rodape)
        fluxo = novo(b"<< /Length %d >>\nstream\n" % len(conteudo) + conteudo + b"\nendstream")
        ids_paginas.append(novo(
            b"<< /Type /Page /Parent %d 0 R /MediaBox [0 0 %d %d] "
            b"/Resources << /Font << /F1 %d 0 R /F2 %d 0 R >> >> /Contents %d 0 R >>"
            % (raiz_paginas, LARGURA, ALTURA, fonte, negrito, fluxo)
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
