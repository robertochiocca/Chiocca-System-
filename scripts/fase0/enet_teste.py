"""Teste de download de versões antigas no ENET da CVM (só formato, nenhum valor).

Pega a versão 1 de algumas empresa-anos da DFP que têm mais de uma versão (fora do gabarito),
baixa o pacote pelo LINK_DOC, confere se o zip chega inteiro e lista só os nomes dos arquivos.
Testa também a visualização HTML do documento (frmGerenciaPaginaFRE.aspx), só status e tamanho.
"""

from __future__ import annotations

import io
import re
import sys
import urllib.request
import zipfile

from comum import excluidos, ler_dfp, sem_excluidos

HTML = "https://www.rad.cvm.gov.br/ENET/frmGerenciaPaginaFRE.aspx?NumeroSequencialDocumento={n}&CodigoTipoInstituicao=2"


def baixar(url: str) -> tuple[int, bytes, str]:
    try:
        with urllib.request.urlopen(url, timeout=240) as r:
            return r.status, r.read(), ""
    except Exception as e:  # o servidor costuma cortar a transferência
        return 0, b"", f"{type(e).__name__}: {e}"


def main(ano: int = 2019, n_docs: int = 3) -> None:
    idx = sem_excluidos(ler_dfp(ano, ""), excluidos())
    idx["VERSAO"] = idx.VERSAO.astype(int)
    multi = idx.groupby(["CD_CVM", "DT_REFER"]).filter(lambda g: len(g) > 1)
    alvos = multi[multi.VERSAO == 1].drop_duplicates("CD_CVM").head(n_docs)
    for i, r in enumerate(alvos.itertuples(), 1):
        status, dados, erro = baixar(r.LINK_DOC)
        try:
            nomes = zipfile.ZipFile(io.BytesIO(dados)).namelist()
            inteiro = "inteiro"
        except zipfile.BadZipFile:
            nomes, inteiro = [], "incompleto ou não é zip"
        print(f"doc {i}: HTTP {status} | {len(dados)} bytes | {inteiro} | {nomes} {erro}")
        n = re.search(r"NumeroSequencialDocumento=(\d+)", r.LINK_DOC)
        if n:
            s, h, e = baixar(HTML.format(n=n.group(1)))
            print(f"  visualização HTML: HTTP {s} | {len(h)} bytes {e}")


if __name__ == "__main__":
    main(*(int(a) for a in sys.argv[1:3]))
