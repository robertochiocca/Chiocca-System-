"""Varredura dos processos sancionadores julgados no portal da CVM (Emenda 6, critério a).

Percorre a busca por data do portal (conteudo.cvm.gov.br/sancionadores), ano a ano e página
a página, e grava uma linha por processo: número, ementa (como aparece na lista), data,
tipo e link. Só documentos públicos; nenhum dado da DFP.
Uso: python varredura_pas.py <pasta_saida> [ano_inicial] [ano_final]   # lista: pas_julgados.csv
     python varredura_pas.py --detalhes <pasta_saida>                 # ementa completa e PDFs: pas_detalhes.csv
     python varredura_pas.py --filtrar <pasta_saida>                  # triagem por palavra-chave: pas_filtrados.csv
"""

from __future__ import annotations

import csv
import html
import re
import sys
import time
import unicodedata
import urllib.parse
import urllib.request
from pathlib import Path

BASE = "https://conteudo.cvm.gov.br"
UA = {"User-Agent": "Mozilla/5.0 (compatible; chiocca-system/0.1)"}  # o portal recusa o agente padrão do urllib
ARTIGO = re.compile(
    r'<article>\s*<h3><a href="(?P<href>[^"]+)" title="(?P<id>[^"]*)">.*?</a></h3>\s*'
    r'<div class="contentDesc">(?P<ementa>.*?)</div>.*?<b>Data:</b>\s*(?P<data>[0-9/]+).*?'
    r"<b>Tipo:</b>\s*(?P<tipo>[^<]+)</p>",
    re.S,
)


def pagina(ano: int, n: int) -> str:
    q = {
        "lastName": "",
        "dataInicio": f"01/01/{ano}",
        "dataFim": f"31/12/{ano}",
        "buscado": "true",
        "pasta": "sancionador",
        "contCategoriasCheck": "1",
        "filtro": "todos",
        "vimDaCategoria": "/sancionadores/sancionador/",
        "searchPage": str(n),
    }
    url = f"{BASE}/sancionadores/index.html?{urllib.parse.urlencode(q)}"
    for tentativa in range(4):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=120) as r:
                return r.read().decode("utf-8", errors="replace")
        except Exception:
            time.sleep(2 ** (tentativa + 1))
    raise RuntimeError(f"falha ao ler {ano} página {n}")


def limpa(s: str) -> str:
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", s))).strip()


def main(saida: str, ano_ini: int = 2010, ano_fim: int = 2026) -> None:
    linhas = []
    for ano in range(ano_ini, ano_fim + 1):
        t = pagina(ano, 1)
        total = re.search(r"(\d+)\s+resultados encontrados", t)
        paginas = re.search(r"Páginas\s+\d+/(\d+)", t)
        n_pag = int(paginas.group(1)) if paginas else 1
        for n in range(1, n_pag + 1):
            if n > 1:
                time.sleep(0.5)
                t = pagina(ano, n)
            for m in ARTIGO.finditer(t):
                linhas.append(
                    {
                        "ano_busca": ano,
                        "id": m["id"].strip(),
                        "data": m["data"],
                        "tipo": limpa(m["tipo"]),
                        "ementa_lista": limpa(m["ementa"]),
                        "url": BASE + m["href"],
                    }
                )
        print(
            ano, "resultados:", total.group(1) if total else "?", "| páginas:", n_pag, "| lidos até agora:", len(linhas)
        )
    Path(saida).mkdir(parents=True, exist_ok=True)
    with open(Path(saida) / "pas_julgados.csv", "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(linhas[0]))
        w.writeheader()
        w.writerows(linhas)


def ler(url: str) -> str:
    for tentativa in range(4):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=120) as r:
                return r.read().decode("utf-8", errors="replace")
        except Exception:
            time.sleep(2 ** (tentativa + 1))
    return ""


def ementa(pagina_html: str) -> str:
    """Ementa completa da página do processo. Páginas novas usam "Ementa:"; as antigas, "Ementa" seguido
    do texto até "Extrato da Sessão de Julgamento" ou "Voltar ao topo"."""
    txt = limpa(pagina_html)
    i = txt.find("Ementa:")
    if i >= 0:
        fim = txt.find("Data decisão CVM", i)
        return txt[i + len("Ementa:") : fim if fim > 0 else i + 3000].strip()
    i = txt.rfind("Ementa ")
    if i < 0:
        return ""
    fins = [j for j in (txt.find("Extrato da Sessão", i), txt.find("Voltar ao topo", i)) if j > 0]
    return txt[i + len("Ementa ") : min(fins) if fins else i + 3000].strip()


def detalhes(saida: str) -> None:
    """Segunda etapa: lê a página de cada processo e grava a ementa completa e os links dos PDFs."""
    pasta = Path(saida)
    anterior = pasta / "pas_detalhes.csv"
    fonte = anterior if anterior.exists() else pasta / "pas_julgados.csv"  # retoma, refazendo só os vazios
    with open(fonte, encoding="utf-8") as f:
        casos = list(csv.DictReader(f))
    for c in casos:
        if c.get("ementa_completa"):
            continue
        t = ler(c["url"])
        c["ementa_completa"] = ementa(t)
        c["pdfs"] = " ".join(dict.fromkeys(BASE + h for h in re.findall(r'href="(/export/[^"]+\.pdf)"', t)))
        time.sleep(0.4)
    with open(pasta / "pas_detalhes.csv", "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(casos[0]))
        w.writeheader()
        w.writerows(casos)
    print("detalhes:", len(casos), "| sem ementa:", sum(1 for c in casos if not c["ementa_completa"]))


# Terceira etapa: triagem por palavra-chave na ementa (sem acento, minúsculas). Só separa para leitura;
# a decisão de cada caso vem da leitura do extrato ou do voto.
CONTEUDO = re.compile(
    r"demonstrac\w* (financeir|contab)|informac\w* (financeir|contab|trimestr)|\bitrs?\b|\bdfs?\b|normas contab|"
    r"pronunciamento|\bcpc\b|principios contab|praticas contab|escriturac|registros? contab|lancamentos? contab|"
    r"fraude|contabil|contabeis|balanc|art\.? ?17[67]\b|refazimento|republicac|reapresentac|impairment|"
    r"recuperabilidade|fidedign"
)
AUDITOR = re.compile(r"auditor|auditoria")
ATRASO = re.compile(
    r"nao elabora|nao envi|atraso|intempestiv|nao entreg|nao divulg|falta de (apresentacao|envio|entrega)"
)
CONTEUDO_DF = re.compile(
    r"desacordo|inobservancia|irregularidades? (contab|na elaborac)|normas contab|pronunciamento|\bcpc\b|fraude|"
    r"fidedign|superavalia|subavalia"
)
CONDENA = re.compile(r"multa|inabilita|advertencia|condena")


def sem_acento(s: str) -> str:
    s = unicodedata.normalize("NFKD", s)
    return re.sub(r"\s+", " ", "".join(c for c in s if not unicodedata.combining(c)).lower())


def filtrar(saida: str) -> None:
    """Grava pas_filtrados.csv: processos com palavra de conteúdo contábil na ementa, com três marcas
    (auditor, só atraso ou falta de entrega, alguma condenação) para orientar a leitura."""
    pasta = Path(saida)
    with open(pasta / "pas_detalhes.csv", encoding="utf-8") as f:
        casos = list(csv.DictReader(f))
    sel = []
    for c in casos:
        t = sem_acento(c["ementa_completa"])
        if not CONTEUDO.search(t):
            continue
        c["auditor"] = bool(AUDITOR.search(t))
        c["so_atraso"] = bool(ATRASO.search(t)) and not CONTEUDO_DF.search(t)
        c["condena"] = bool(CONDENA.search(t))
        sel.append(c)
    with open(pasta / "pas_filtrados.csv", "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(sel[0]))
        w.writeheader()
        w.writerows(sel)
    ler_primeiro = sum(1 for c in sel if not c["auditor"] and not c["so_atraso"])
    print(f"total {len(casos)} | com conteúdo contábil {len(sel)} | sem auditor e sem só atraso {ler_primeiro}")


if __name__ == "__main__":
    if sys.argv[1] == "--detalhes":
        detalhes(sys.argv[2])
    elif sys.argv[1] == "--filtrar":
        filtrar(sys.argv[2])
    else:
        main(sys.argv[1], *(int(a) for a in sys.argv[2:4]))
