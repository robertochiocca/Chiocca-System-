"""Baixa os arquivos da Fase 0 para CHIOCCA_CVM_RAW e grava SHA256SUMS.

DFP de 2010 a 2026, dicionário da DFP, cadastro de companhias abertas e seu dicionário,
e FCA de 2010 a 2026. Os arquivos ficam fora do git (data/brutos/ por padrão).
"""

from __future__ import annotations

import hashlib
import urllib.request

from comum import ANOS_DFP, RAW

BASE = "https://dados.cvm.gov.br/dados/CIA_ABERTA"
URLS = (
    [
        f"{BASE}/DOC/DFP/META/meta_dfp_cia_aberta_txt.zip",
        f"{BASE}/CAD/DADOS/cad_cia_aberta.csv",
        f"{BASE}/CAD/META/meta_cad_cia_aberta.txt",
    ]
    + [f"{BASE}/DOC/DFP/DADOS/dfp_cia_aberta_{a}.zip" for a in ANOS_DFP]
    + [f"{BASE}/DOC/FCA/DADOS/fca_cia_aberta_{a}.zip" for a in ANOS_DFP]
)


def main() -> None:
    RAW.mkdir(parents=True, exist_ok=True)
    linhas = []
    for url in URLS:
        destino = RAW / url.rsplit("/", 1)[1]
        with urllib.request.urlopen(url, timeout=300) as r:
            dados = r.read()
        destino.write_bytes(dados)
        linhas.append(f"{hashlib.sha256(dados).hexdigest()}  {destino.name}")
        print(destino.name, len(dados))
    (RAW / "SHA256SUMS").write_text("\n".join(linhas) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
