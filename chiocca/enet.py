"""Rota HTML do ENET da CVM para a versão da época, só para demonstrações consolidadas (emendas 5 e 8).

Os arquivos de dados abertos só trazem a última versão de cada DFP. Quando a última versão foi entregue
depois da data de corte, a versão vigente no corte vem da visualização HTML do documento no ENET:
- a página do documento (frmGerenciaPaginaFRE.aspx) dá o endereço das tabelas dentro de uma sessão com
  cookie; algumas sessões devolvem página reduzida, e por isso há novas tentativas;
- cada tabela vem de frmDemonstracaoFinanceiraITR.aspx, com a página do documento como Referer;
- Demonstracao: 2 BPA, 3 BPP, 4 DRE, 99 DFC; Informacao=2 é o consolidado (emenda 8: só consolidado);
- célula vazia vale 0 (emenda 8); "Reais Mil" multiplica por 1.000.
O teste de 06/11/2026 (docs/reconhecimento.md, 7.2) bateu 871 de 871 linhas no consolidado.

As tabelas baixadas ficam em data/cache/enet/<NumeroSequencialDocumento>_con.csv (fora do git). Um arquivo
só com o cabeçalho quer dizer que o documento não tem demonstração consolidada.

Uso: python -m chiocca.enet <arquivo com um NumeroSequencialDocumento por linha>
"""

from __future__ import annotations

import html
import http.cookiejar
import re
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

import pandas as pd

ENET = "https://www.rad.cvm.gov.br/ENET/"
AGENTE = "Mozilla/5.0 (compatible; chiocca-system/0.1)"
PADRAO_TABELAS = re.compile(r"frmDemonstracaoFinanceiraITR\.aspx\?[^\x27\"]*?Hash=[A-Za-z0-9]+")
QUADROS = {
    "BPA": (2, "Balan%c3%a7o+Patrimonial+Ativo"),
    "BPP": (3, "Balan%c3%a7o+Patrimonial+Passivo"),
    "DRE": (4, "Demonstra%c3%a7%c3%a3o+do+Resultado"),
    "DFC": (99, "Demonstra%c3%a7%c3%a3o+do+Fluxo+de+Caixa"),
}
COLUNAS = ["demonstracao", "ordem", "cd_conta", "ds_conta", "valor"]
ORDENS = ("ÚLTIMO", "PENÚLTIMO")  # 1ª e 2ª colunas de valor da DFP; a 3ª (antepenúltimo) não é usada


class FalhaENET(Exception):
    pass


def _limpa(s: str) -> str:
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", s))).strip()


def numero(celula: str) -> float | None:
    s = _limpa(celula).replace("\xa0", "")
    if s in ("", "-"):
        return None
    negativo = s.startswith("(") and s.endswith(")")
    s = s.strip("()").replace(".", "").replace(",", ".")
    try:
        v = float(s)
    except ValueError:
        return None
    return -v if negativo else v


def parse_tabela(pagina: str, demonstracao: str) -> pd.DataFrame:
    """Linhas da tabela HTML de uma demonstração, com célula vazia = 0 (emenda 8) e escala em reais."""
    mil = "Reais Mil" in _limpa(pagina)
    linhas = []
    for tr in re.findall(r"<tr[^>]*>(.*?)</tr>", pagina, re.DOTALL | re.IGNORECASE)[1:]:
        tds = re.findall(r"<td[^>]*>(.*?)</td>", tr, re.DOTALL | re.IGNORECASE)
        if len(tds) < 4:
            continue
        conta, descricao = _limpa(tds[0]), _limpa(tds[1])
        for ordem, celula in zip(ORDENS, tds[2:4]):
            v = numero(celula)
            linhas.append((demonstracao, ordem, conta, descricao, (0.0 if v is None else v) * (1000 if mil else 1)))
    return pd.DataFrame(linhas, columns=COLUNAS)


def _sessao(num_doc: str) -> tuple[urllib.request.OpenerDirector, str, str, str, bool]:
    menu = f"{ENET}frmGerenciaPaginaFRE.aspx?NumeroSequencialDocumento={num_doc}&CodigoTipoInstituicao=2"
    for _ in range(10):
        op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
        op.addheaders = [("User-Agent", AGENTE)]
        pagina = op.open(menu, timeout=90).read().decode("utf-8", errors="replace")
        m = PADRAO_TABELAS.search(pagina)
        if m:
            base = urllib.parse.quote(html.unescape(m.group(0)), safe=":/?&=%+|")
            v = re.search(r"Versao=(\d+)", base)
            tem_con = bool(re.search(r"<option[^>]*>\s*DFs Consolidadas\s*</option>", pagina))
            return op, menu, base, (v.group(1) if v else ""), tem_con
        time.sleep(2)
    raise FalhaENET(f"página do documento {num_doc} sem o endereço das tabelas")


def baixa_consolidado(num_doc: str, versao_esperada: int) -> pd.DataFrame:
    op, menu, base, versao, tem_con = _sessao(num_doc)
    if versao and int(versao) != versao_esperada:
        raise FalhaENET(f"documento {num_doc}: ENET mostra a versão {versao}, esperada {versao_esperada}")
    if not tem_con:
        return pd.DataFrame(columns=COLUNAS)
    partes = []
    for dem, (codigo, quadro) in QUADROS.items():
        url = ENET + re.sub(
            r"Demonstracao=\d+", f"Demonstracao={codigo}", re.sub(r"Quadro=[^&]+", f"Quadro={quadro}", base)
        )
        url = re.sub(r"Grupo=[^&]+", "Grupo=DFs+Consolidadas", url)
        url = re.sub(r"Informacao=\d+", "Informacao=2", url)
        pagina = op.open(urllib.request.Request(url, headers={"Referer": menu}), timeout=90).read()
        t = parse_tabela(pagina.decode("utf-8", errors="replace"), dem)
        if t.empty:
            raise FalhaENET(f"documento {num_doc}: tabela {dem} vazia")
        partes.append(t)
        time.sleep(1)
    return pd.concat(partes, ignore_index=True)


def caminho_cache(cache: Path, num_doc: str) -> Path:
    return cache / f"{num_doc}_con.csv"


def le_cache(cache: Path, num_doc: str) -> pd.DataFrame | None:
    p = caminho_cache(cache, num_doc)
    if not p.exists():
        return None
    return pd.read_csv(p, dtype={"cd_conta": str, "ds_conta": str}, keep_default_na=False, na_values=[])


def baixa_para_cache(cache: Path, num_doc: str, versao: int, tentativas: int = 3) -> pd.DataFrame:
    cache.mkdir(parents=True, exist_ok=True)
    erro: Exception | None = None
    for i in range(tentativas):
        try:
            d = baixa_consolidado(num_doc, versao)
            d.to_csv(caminho_cache(cache, num_doc), index=False)
            return d
        except (OSError, FalhaENET) as e:
            erro = e
            time.sleep(5 * (i + 1))
    raise FalhaENET(f"documento {num_doc}: {erro}")


if __name__ == "__main__":
    from chiocca.base import CACHE_ENET

    falhas = []
    pedidos = [linha.split() for linha in Path(sys.argv[1]).read_text().split("\n") if linha.strip()]
    for k, (num, ver) in enumerate(pedidos, 1):
        if le_cache(CACHE_ENET, num) is not None:
            continue
        try:
            baixa_para_cache(CACHE_ENET, num, int(ver))
        except FalhaENET as e:
            falhas.append(f"{num}\t{e}")
        print(f"{k}/{len(pedidos)}", flush=True)
    (CACHE_ENET / ("falhas_" + Path(sys.argv[1]).stem + ".txt")).write_text(
        "\n".join(falhas) + ("\n" if falhas else ""), encoding="utf-8"
    )
    print("falhas:", len(falhas))
