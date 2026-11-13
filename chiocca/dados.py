"""Download dos dados abertos da CVM para data/brutos/cvm (fora do git) e verificação por hash.

Arquivos: DFP anual de todos os anos disponíveis (2010 a 2026), FCA dos mesmos anos (setor de cada ano,
emenda 5), cadastro de companhias abertas (inclui as canceladas) e os dicionários de dados.

O manifesto versionado (data/manifesto_brutos.csv) guarda URL, tamanho, SHA256 e hora do download de cada
arquivo. A CVM regera os arquivos (docs/reconhecimento.md, 1.1): um download novo pode ter outro hash, e por
isso o manifesto só muda quando `baixar` roda de novo, e o commit registra a troca.

Formulário de Referência (Fase F1, 11/11/2026): os arquivos de 2010 a 2024 (o de 2024 traz o exercício de 2023; o de
2025 já é do exercício lacrado) entram por um comando próprio, que só acrescenta as linhas deles ao manifesto e não
baixa de novo nem troca as linhas dos outros arquivos (a base do invariante não muda).

Fatos relevantes e comunicados (Fase F2a, 12/11/2026): os índices do IPE de 2010 a 2024 (só metadados de cada
documento entregue no ano: data de entrega, categoria, assunto, protocolo e link; o conteúdo dos documentos não é
baixado) entram por um comando próprio, como o Formulário de Referência. O de 2025 em diante não é baixado aqui: só o
monitor (chiocca.v2.monitor) olha os metadados, sem guardar o assunto.

Uso:
  python -m chiocca.dados baixar      # baixa tudo e reescreve o manifesto
  python -m chiocca.dados baixar-fre  # baixa só o Formulário de Referência de 2010 a 2024 e acrescenta ao manifesto
  python -m chiocca.dados baixar-ipe  # baixa só os índices do IPE de 2010 a 2024 e acrescenta ao manifesto
  python -m chiocca.dados verificar   # confere os arquivos locais contra o manifesto (sem rede)
"""

from __future__ import annotations

import csv
import hashlib
import os
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
BRUTOS = Path(os.environ.get("CHIOCCA_CVM_RAW", RAIZ / "data" / "brutos" / "cvm"))
MANIFESTO = RAIZ / "data" / "manifesto_brutos.csv"
BASE = "https://dados.cvm.gov.br/dados/CIA_ABERTA"
ANOS = range(2010, 2027)
AGENTE = "Mozilla/5.0 (compatible; chiocca-system/0.1)"


def urls() -> list[str]:
    return (
        [
            f"{BASE}/DOC/DFP/META/meta_dfp_cia_aberta_txt.zip",
            f"{BASE}/DOC/FCA/META/fca_cia_aberta.zip",
            f"{BASE}/CAD/DADOS/cad_cia_aberta.csv",
            f"{BASE}/CAD/META/meta_cad_cia_aberta.txt",
        ]
        + [f"{BASE}/DOC/DFP/DADOS/dfp_cia_aberta_{a}.zip" for a in ANOS]
        + [f"{BASE}/DOC/FCA/DADOS/fca_cia_aberta_{a}.zip" for a in ANOS]
    )


def urls_fre() -> list[str]:
    return [f"{BASE}/DOC/FRE/DADOS/fre_cia_aberta_{a}.zip" for a in range(2010, 2025)]


def urls_ipe() -> list[str]:
    return [f"{BASE}/DOC/IPE/DADOS/ipe_cia_aberta_{a}.zip" for a in range(2010, 2025)]


def sha256(caminho: Path) -> str:
    h = hashlib.sha256()
    with caminho.open("rb") as f:
        for bloco in iter(lambda: f.read(1 << 20), b""):
            h.update(bloco)
    return h.hexdigest()


def _baixa(url: str) -> bytes:
    for tentativa in range(5):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": AGENTE})
            with urllib.request.urlopen(req, timeout=600) as r:
                return bytes(r.read())
        except urllib.error.HTTPError as e:
            if e.code < 500 or tentativa == 4:
                raise
            time.sleep(2 ** (tentativa + 1))
        except OSError:
            if tentativa == 4:
                raise
            time.sleep(2 ** (tentativa + 1))
    raise RuntimeError(url)


def _le_manifesto() -> list[dict[str, str]]:
    if not MANIFESTO.exists():
        return []
    with MANIFESTO.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def _grava_manifesto(linhas: list[dict[str, object]]) -> None:
    with MANIFESTO.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["arquivo", "url", "bytes", "sha256", "baixado_em_utc"], lineterminator="\n")
        w.writeheader()
        w.writerows(linhas)


def baixar_fre(lista: list[str] | None = None) -> None:
    """Baixa só o Formulário de Referência (2010 a 2024), ou os arquivos da lista dada, e troca ou acrescenta as linhas
    deles no manifesto; as linhas dos outros arquivos ficam como estão."""
    BRUTOS.mkdir(parents=True, exist_ok=True)
    novas: dict[str, dict[str, object]] = {}
    for url in lista if lista is not None else urls_fre():
        nome = url.rsplit("/", 1)[1]
        dados = _baixa(url)
        (BRUTOS / nome).write_bytes(dados)
        quando = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        novas[nome] = {"arquivo": nome, "url": url, "bytes": len(dados), "sha256": hashlib.sha256(dados).hexdigest(),
                       "baixado_em_utc": quando}  # fmt: skip
        print(nome, len(dados))
        time.sleep(1)
    linhas: list[dict[str, object]] = [dict(x) for x in _le_manifesto() if x["arquivo"] not in novas]
    _grava_manifesto(linhas + list(novas.values()))


def baixar() -> None:
    BRUTOS.mkdir(parents=True, exist_ok=True)
    proprios = {u.rsplit("/", 1)[1] for u in urls()}
    outros: list[dict[str, object]] = [dict(x) for x in _le_manifesto() if x["arquivo"] not in proprios]
    linhas: list[dict[str, object]] = []
    for url in urls():
        nome = url.rsplit("/", 1)[1]
        dados = _baixa(url)
        (BRUTOS / nome).write_bytes(dados)
        quando = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        linhas.append(
            {
                "arquivo": nome,
                "url": url,
                "bytes": len(dados),
                "sha256": hashlib.sha256(dados).hexdigest(),
                "baixado_em_utc": quando,
            }
        )
        print(nome, len(dados))
    _grava_manifesto(linhas + outros)  # as linhas do Formulário de Referência (baixar-fre) ficam


def verificar(pasta: Path = BRUTOS, manifesto: Path = MANIFESTO) -> list[str]:
    """Devolve a lista de problemas (vazia se tudo bate)."""
    problemas = []
    with manifesto.open(encoding="utf-8", newline="") as f:
        for linha in csv.DictReader(f):
            caminho = pasta / linha["arquivo"]
            if not caminho.exists():
                problemas.append(f"faltando: {linha['arquivo']}")
            elif sha256(caminho) != linha["sha256"]:
                problemas.append(f"hash diferente: {linha['arquivo']}")
    return problemas


if __name__ == "__main__":
    if sys.argv[1:] == ["baixar"]:
        baixar()
    elif sys.argv[1:] == ["baixar-fre"]:
        baixar_fre()
    elif sys.argv[1:] == ["baixar-ipe"]:
        baixar_fre(urls_ipe())  # mesmo caminho: só acrescenta ou troca as linhas do IPE no manifesto
    elif sys.argv[1:] == ["verificar"]:
        p = verificar()
        print("\n".join(p) if p else "todos os arquivos batem com o manifesto")
        sys.exit(1 if p else 0)
    else:
        print(__doc__)
        sys.exit(2)
