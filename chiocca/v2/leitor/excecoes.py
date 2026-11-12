"""Gera data/leitor/companhias_cadastro.txt: os nomes das companhias do cadastro da CVM, na forma de comparação do
detector de nomes (sem acento, sem pontuação, sem a situação e sem as marcas de empresa do fim), uma por linha.

É a lista de exceções de nomes de companhias da regra de 11/11/2026 (docs/pre-registro-leitor.md, seção 7). Fica
versionada para o detector se comportar igual no CI (que não tem os dados brutos) e aqui. Só entram nomes com duas
ou mais palavras: o detector só olha sequências de duas ou mais.

Uso: python -m chiocca.v2.leitor.excecoes
"""

from __future__ import annotations

import pandas as pd

from chiocca import base
from chiocca.dados import MANIFESTO, sha256
from chiocca.v2.leitor.nomes import ARQUIVO_COMPANHIAS, _sem_marcas


def gerar() -> list[str]:
    cad = pd.read_csv(base.BRUTOS / "cad_cia_aberta.csv", sep=";", encoding="latin1", dtype=str)
    nomes = {_sem_marcas(n) for col in ("DENOM_SOCIAL", "DENOM_COMERC") for n in cad[col].dropna()}
    return sorted(n for n in nomes if len(n.split()) >= 2)


def main() -> None:
    origem = base.BRUTOS / "cad_cia_aberta.csv"
    manifesto = pd.read_csv(MANIFESTO, dtype=str)
    registrado = manifesto.loc[manifesto.arquivo == "cad_cia_aberta.csv", "sha256"].iloc[0]
    atual = sha256(origem)
    if atual != registrado:
        raise SystemExit("cad_cia_aberta.csv diferente do manifesto: rode python -m chiocca.dados verificar")
    nomes = gerar()
    ARQUIVO_COMPANHIAS.parent.mkdir(parents=True, exist_ok=True)
    cabecalho = ["# Gerado por python -m chiocca.v2.leitor.excecoes a partir de data/brutos/cvm/cad_cia_aberta.csv",
                 f"# SHA256 da origem (data/manifesto_brutos.csv): {atual}", f"# {len(nomes)} nomes"]  # fmt: skip
    ARQUIVO_COMPANHIAS.write_text("\n".join(cabecalho + nomes) + "\n", encoding="utf-8")
    print(f"{len(nomes)} nomes em {ARQUIVO_COMPANHIAS}")


if __name__ == "__main__":
    main()
