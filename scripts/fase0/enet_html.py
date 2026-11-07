"""Teste da rota HTML do ENET (Emenda 5): compara, linha a linha, as tabelas HTML de um documento
com os dados abertos da DFP da mesma versão. Imprime só contagens, nunca valores.

Uso:
  python enet_html.py escolher <ano>                   # lista as empresas do teste pela regra (só estrutura)
  python enet_html.py comparar <CD_CVM> <ano> [<CD_CVM> <ano> ...]
  python enet_html.py contar <CD_CVM> <ano> <versao>   # só conta linhas (ex.: IRB 2019 versão 1)
"""

from __future__ import annotations

import html
import http.cookiejar
import io
import re
import sys
import time
import urllib.parse
import urllib.request
import zipfile

import pandas as pd
from comum import RAW, cd, excluidos, ler_dfp, norm, tipo_plano

ENET = "https://www.rad.cvm.gov.br/ENET/"
UA = "Mozilla/5.0 (compatible; chiocca-system/0.1)"
PAT = re.compile(r"frmDemonstracaoFinanceiraITR\.aspx\?[^\x27\"]*?Hash=[A-Za-z0-9]+")
QUADROS = {  # código da demonstração no ENET -> (nome no ENET, arquivos dos dados abertos)
    2: ("Balan%c3%a7o+Patrimonial+Ativo", ["BPA"]),
    3: ("Balan%c3%a7o+Patrimonial+Passivo", ["BPP"]),
    4: ("Demonstra%c3%a7%c3%a3o+do+Resultado", ["DRE"]),
    99: ("Demonstra%c3%a7%c3%a3o+do+Fluxo+de+Caixa", ["DFC_MI", "DFC_MD"]),
}


def texto(s: str) -> str:
    """Comparação de texto da Emenda 7: sem maiúsculas, acentos nem espaços repetidos."""
    return re.sub(r"\s+", " ", norm(html.unescape(re.sub(r"<[^>]+>", " ", s))))


def numero(s: str) -> float | None:
    s = html.unescape(re.sub(r"<[^>]+>", "", s)).strip().replace("\xa0", "")
    if s in ("", "-"):
        return None
    neg = s.startswith("(") and s.endswith(")")
    s = s.strip("()").replace(".", "").replace(",", ".")
    try:
        v = float(s)
    except ValueError:
        return None
    return -v if neg else v


def sessao(num_doc: str) -> tuple[urllib.request.OpenerDirector, str, str, str]:
    """Abre sessões até a página principal trazer o endereço das tabelas (algumas sessões não trazem)."""
    menu = f"{ENET}frmGerenciaPaginaFRE.aspx?NumeroSequencialDocumento={num_doc}&CodigoTipoInstituicao=2"
    for _ in range(10):
        op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
        op.addheaders = [("User-Agent", UA)]
        t = op.open(menu, timeout=90).read().decode("utf-8", errors="replace")
        m = PAT.search(t)
        if m:
            base = urllib.parse.quote(html.unescape(m.group(0)), safe=":/?&=%+|")  # nomes com acento e espaço
            versao = re.search(r"Versao=(\d+)", base).group(1)
            return op, menu, base, versao
        time.sleep(2)
    raise RuntimeError("página principal sem o endereço das tabelas")


def tabela(op, menu: str, base: str, dem: int, grupo: str) -> list[tuple[str, str, list[float | None]]]:
    url = ENET + re.sub(
        r"Demonstracao=\d+", f"Demonstracao={dem}", re.sub(r"Quadro=[^&]+", f"Quadro={QUADROS[dem][0]}", base)
    )
    url = re.sub(r"Grupo=[^&]+", f"Grupo={grupo}", url)
    url = re.sub(
        r"Informacao=\d+", "Informacao=" + ("1" if grupo == "DFs+Individuais" else "2"), url
    )  # 1 individual, 2 consolidada
    p = (
        op.open(urllib.request.Request(url, headers={"Referer": menu}), timeout=90)
        .read()
        .decode("utf-8", errors="replace")
    )
    escala_mil = "Reais Mil" in html.unescape(re.sub(r"<[^>]+>", " ", p))
    linhas = []
    for tr in re.findall(r"<tr[^>]*>(.*?)</tr>", p, re.S | re.I)[1:]:
        tds = re.findall(r"<td[^>]*>(.*?)</td>", tr, re.S | re.I)
        if len(tds) >= 4:
            vals = [numero(x) for x in tds[2:]]
            linhas.append(
                (
                    texto(tds[0]),
                    texto(tds[1]),
                    [v * (1000 if escala_mil else 1) if v is not None else None for v in vals],
                )
            )
    return linhas


def doc_da_versao(cd_cvm: str, ano: int, versao: int | None) -> tuple[str, int, str]:
    idx = ler_dfp(ano, "")
    idx = idx[cd(idx.CD_CVM) == cd_cvm].copy()
    idx["VERSAO"] = idx.VERSAO.astype(int)
    linha = idx[idx.VERSAO == (versao or idx.VERSAO.max())].iloc[0]
    return re.search(r"NumeroSequencialDocumento=(\d+)", linha.LINK_DOC).group(1), int(linha.VERSAO), linha.DT_REFER


def ler_com_valores(ano: int, nome: str, cd_cvm: str) -> pd.DataFrame:
    """Único leitor que carrega VL_CONTA, autorizado só para as empresas do teste do ENET (fora do
    gabarito e dos candidatos). Os valores ficam na memória para a comparação e nunca são impressos."""
    arq = f"dfp_cia_aberta_{nome}_{ano}.csv"
    with zipfile.ZipFile(RAW / f"dfp_cia_aberta_{ano}.zip") as z:
        if arq not in z.namelist():
            return pd.DataFrame()
        d = pd.read_csv(io.BytesIO(z.read(arq)), sep=";", encoding="latin1", dtype=str)
    return d[cd(d.CD_CVM) == cd_cvm]


def abertos(cd_cvm: str, ano: int, arquivos: list[str], tipo: str) -> pd.DataFrame:
    for a in arquivos:
        d = ler_com_valores(ano, f"{a}_{tipo}", cd_cvm)
        if len(d):
            d = d.copy()
            d["valor"] = d.VL_CONTA.astype(float) * d.ESCALA_MOEDA.map({"MIL": 1000.0, "UNIDADE": 1.0})
            return d
    return pd.DataFrame()


def comparar(cd_cvm: str, ano: int) -> None:
    num, versao_aberta, _ = doc_da_versao(cd_cvm, ano, None)
    op, menu, base, versao_enet = sessao(num)
    print(f"empresa {cd_cvm}, DFP {ano}: versão nos dados abertos {versao_aberta} | versão no ENET {versao_enet}")
    tot = {"linhas": 0, "batem": 0, "nao_batem": 0, "so_nos_abertos": 0}
    tipos = [t for t in ("con", "ind") if len(abertos(cd_cvm, ano, ["BPA"], t))]
    for tipo, dem, arquivos in [(t, d, q[1]) for t in tipos for d, q in QUADROS.items()]:
        grupo = "DFs+Consolidadas" if tipo == "con" else "DFs+Individuais"
        h = tabela(op, menu, base, dem, grupo)
        a = abertos(cd_cvm, ano, arquivos, tipo)
        ult = {r.CD_CONTA: (texto(r.DS_CONTA), r.valor) for r in a[a.ORDEM_EXERC == "ÚLTIMO"].itertuples()}
        pen = {r.CD_CONTA: r.valor for r in a[a.ORDEM_EXERC == "PENÚLTIMO"].itertuples()}
        bate = vazio_zero = 0
        for conta, desc, vals in h:
            # célula vazia no HTML corresponde a 0 nos dados abertos (achado do primeiro teste)
            v1 = 0.0 if vals[0] is None else vals[0]
            v2 = 0.0 if len(vals) < 2 or vals[1] is None else vals[1]
            vazio_zero += (vals[0] is None) or (len(vals) > 1 and vals[1] is None)
            ok = conta in ult and ult[conta][0] == desc
            ok = ok and abs(v1 - ult[conta][1]) < 0.5
            ok = ok and (conta not in pen or abs(v2 - pen[conta]) < 0.5)
            bate += ok
        so_abertos = len(set(ult) - {c for c, _, _ in h})
        print(
            f"  {tipo} demonstração {dem}: linhas {len(h)} | batem {bate} | não batem {len(h) - bate} | só nos dados abertos {so_abertos}"
            f" | linhas com célula vazia no HTML (tratada como 0): {vazio_zero}"
        )
        tot["linhas"] += len(h)
        tot["batem"] += bate
        tot["nao_batem"] += len(h) - bate
        tot["so_nos_abertos"] += so_abertos
        time.sleep(1)
    print(f"  total: {tot}")


def escolher(ano: int, n: int = 6) -> None:
    """Regra do teste: DFP do ano com uma versão só, BPA consolidado, plano de não financeira, fora do
    gabarito e dos candidatos; ordena pelo número de linhas do BPA consolidado (exercício ÚLTIMO)."""
    fora = set(excluidos())
    for arq in ("data/gabarito_casos.csv", "data/gabarito_candidatos.csv"):
        fora |= {c for c in pd.read_csv(arq, dtype=str).cd_cvm.dropna()}
    idx = ler_dfp(ano, "", ["CD_CVM", "VERSAO"])
    uma = {c for c, v in idx.groupby(cd(idx.CD_CVM)).VERSAO.agg(lambda s: tuple(sorted(set(s)))).items() if v == ("1",)}
    dre = ler_dfp(ano, "DRE_con", ["CD_CVM", "ORDEM_EXERC", "CD_CONTA", "DS_CONTA"])
    dre = dre[(dre.ORDEM_EXERC == "ÚLTIMO") & (dre.CD_CONTA == "3.01")]
    nao_fin = {c for c, d in zip(cd(dre.CD_CVM), dre.DS_CONTA) if tipo_plano(d) == "nao_financeiro"}
    bpa = ler_dfp(ano, "BPA_con", ["CD_CVM", "ORDEM_EXERC", "CD_CONTA"])
    bpa = bpa[bpa.ORDEM_EXERC == "ÚLTIMO"]
    linhas = bpa.groupby(cd(bpa.CD_CVM)).size()
    ok = linhas[[c in uma and c in nao_fin and c not in fora for c in linhas.index]]
    print(
        "candidatos ao teste (código | linhas no BPA consolidado):",
        list(ok.sort_values(ascending=False).head(n).items()),
    )


def contar(cd_cvm: str, ano: int, versao: int) -> None:
    num, v, _ = doc_da_versao(cd_cvm, ano, versao)
    op, menu, base, versao_enet = sessao(num)
    print(f"empresa {cd_cvm}, DFP {ano}: versão pedida {v} | versão no ENET {versao_enet}")
    for grupo, tipo in (("DFs+Consolidadas", "con"), ("DFs+Individuais", "ind")):
        for dem, (_, arquivos) in QUADROS.items():
            h = tabela(op, menu, base, dem, grupo)
            n_abertos = 0
            for arq in arquivos:  # só estrutura: sem VL_CONTA
                e = ler_dfp(ano, f"{arq}_{tipo}", ["CD_CVM", "ORDEM_EXERC", "CD_CONTA"])
                e = e[(cd(e.CD_CVM) == cd_cvm) & (e.ORDEM_EXERC == "ÚLTIMO")]
                if len(e):
                    n_abertos = len(e)
                    break
            sem_valor = sum(1 for _, _, vals in h if vals and vals[0] is None)
            print(
                f"  {grupo} demonstração {dem}: linhas no ENET {len(h)} (sem valor na 1ª coluna: {sem_valor}) | "
                f"linhas nos dados abertos (versão mais recente): {n_abertos}"
            )
            time.sleep(1)


if __name__ == "__main__":
    if sys.argv[1] == "escolher":
        escolher(int(sys.argv[2]))
    elif sys.argv[1] == "comparar":
        args = sys.argv[2:]
        for i in range(0, len(args), 2):
            comparar(args[i], int(args[i + 1]))
    else:
        contar(sys.argv[2], int(sys.argv[3]), int(sys.argv[4]))
