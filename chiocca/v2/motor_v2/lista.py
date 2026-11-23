"""A lista do motor v2 (emenda 5 do estudo 2, itens 1, 4 e 5; pré-registro do motor v2).

O caminho é o da lista do v1 (`chiocca.v2.estudo2.lista`), reaproveitado por importação, sem mudar nenhuma linha dele:
para cada exercício, as empresa-anos do índice da DFP na data de corte de cada uma, com os campos do estudo
(`_meta_e_contas`), os sinais do v1 (`chiocca.sinais_amostra.calcula`, que lê as contas de um CSV, como em data/base)
e, por cima, as mudanças do v2 (`motor.calcula`), com a DVA do mesmo zip da DFP. Os dados vêm dos arquivos brutos
(`chiocca.cvm.Fontes`) e do cache do ENET, os mesmos da lista do v1 (o branch `estudo-2-dados`); nada é baixado.

O arquivo segue o formato da seção 8 do estudo 2: CSV em UTF-8 com quebra de linha LF, ordenado por código CVM
(numérico), exercício e data de referência, sem data de geração; antes do cabeçalho, linhas "#" com o commit, a versão
menor do Python, o SHA-256 do requirements-lock.txt e o SHA-256 de cada arquivo de entrada. As colunas são as da lista
do v1 sem os alertas por sinal do v1 (o v2 não os tem), mais as do v2; `avaliada` e `em_alerta` são as do v2. Os
percentis e o escore vão com `CASAS_ESCORE` casas, para o arredondamento não criar empates no ranking; o resto, com as
casas da lista do v1.

Ordem: as empresa-anos de cada exercício entram no v2 na ordem do índice da DFP (a primeira linha de cada par código
CVM e data de referência no `dfp_cia_aberta_<ano>.csv` do zip arquivado no branch `estudo-2-dados`), e é essa a ordem
que desfaz os empates de quantidade de números nas faixas do Benford (`benford.py`); a ordenação por código CVM é só a
do arquivo gravado, depois do cálculo.

Lacre: cada exercício passa por `abertura.garantir_exercicio` antes de qualquer leitura. Acima de 2023, só os que o
commit da sessão do lacre da lista do v2 puser na constante do v2 (`abertura.CONSTANTE`).

Uso, na sessão do lacre da lista do v2 (separada, só com a autorização de Roberto, depois do congelamento):
  python -m chiocca.v2.motor_v2.lista                      # calcula duas vezes, confere e grava a lista
Recálculo na avaliação: no commit em que a lista foi calculada, com os mesmos arquivos, o lock e o Python 3.13,
`python -m chiocca.v2.motor_v2.lista --conferir <SHA-256>` tem de dar o mesmo arquivo, byte a byte.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import math
import sys
import tempfile
from pathlib import Path
from typing import Any, Iterable

import pandas as pd

from chiocca import base, sinais_amostra
from chiocca.cvm import Fontes
from chiocca.v2.estudo2 import lista as lista_v1
from chiocca.v2.motor_v2 import abertura, dva, motor
from chiocca.v2.motor_v2.escore import TODOS_OS_SINAIS

SAIDA = base.RAIZ / "resultados" / "motor_v2"
LISTA = SAIDA / "lista_motor_v2.csv"
TITULO = "# chiocca: lista do motor v2 (pré-registro do motor v2; emenda 5 do estudo 2)"
CASAS_ESCORE = 12

COLUNAS_V2 = [
    "marca_depreciacao_dva", "depreciacao_dva_t", "depreciacao_dva_t1", "n_numeros_benford", "desvio_benford",
    "faixa_benford", "benford", "benford_motivo", *(f"pct_{x}" for x in TODOS_OS_SINAIS), "escore",
    "n_sinais_calculaveis", "sinal_do_escore",
]  # fmt: skip
COLUNAS = [
    *(c for c in lista_v1.COLUNAS_ESTUDO_1 if c not in motor.ALERTAS_POR_SINAL_DO_V1),
    *COLUNAS_V2,
    "versao", "ultima_versao", "num_doc",
]  # fmt: skip
INTEIROS = {"n_numeros_benford", "faixa_benford", "n_sinais_calculaveis"}
BOOLEANOS = {"marca_depreciacao_dva"}
NUMEROS = {"depreciacao_dva_t", "depreciacao_dva_t1", "desvio_benford", "benford"}
DO_ESCORE = {*(f"pct_{x}" for x in TODOS_OS_SINAIS), "escore"}


def _numero(v: Any, casas: int) -> str:
    x = float(v)
    if math.isinf(x):
        return "inf" if x > 0 else "-inf"
    s = f"{x:.{casas}f}"
    return s[1:] if s.startswith("-") and s.lstrip("-0.") == "" else s  # -0.000000 vira 0.000000


def celula(coluna: str, v: Any) -> str:
    """Uma célula no formato fixo: as colunas da lista do v1 como lá (`lista_v1.celula`); as do v2 com as mesmas
    convenções (vazio para ausente, inteiros sem casas, booleanos 1 ou 0), os percentis e o escore com `CASAS_ESCORE`
    casas e os outros números com as casas do v1."""
    if coluna not in COLUNAS_V2:
        return lista_v1.celula(coluna, v)
    if lista_v1._vazio(v) or (isinstance(v, str) and v == ""):
        return ""
    if coluna in INTEIROS:
        return str(int(float(v)))
    if coluna in BOOLEANOS:
        return "1" if lista_v1._verdadeiro(v) else "0"
    if coluna in DO_ESCORE:
        return _numero(v, CASAS_ESCORE)
    if coluna in NUMEROS:
        return _numero(v, lista_v1.CASAS)
    return str(v)


def calcular(
    fontes: Fontes, exercicios: Iterable[int], mudancas: motor.Mudancas = motor.TODAS, brutos_dva: Path | None = None
) -> pd.DataFrame:
    """Sinais e alertas do v2 (ou do v1, com as mudanças desligadas) de todas as empresa-anos dos exercícios, cada uma
    na data de corte do seu exercício. `brutos_dva`: a pasta dos zips da DFP de onde vem a DVA (padrão: a das fontes).
    Todos os exercícios passam pelo lacre do v2 antes de qualquer leitura."""
    anos = [abertura.garantir_exercicio(a) for a in exercicios]
    partes = []
    for ano in anos:
        meta, contas = lista_v1._meta_e_contas(fontes, ano)
        with tempfile.TemporaryDirectory() as pasta:  # o v1 lê as contas de um CSV; o v2 lê as mesmas, de lá
            arquivo = Path(pasta) / f"contas_{ano}.csv.gz"
            contas.to_csv(arquivo, index=False)
            s = sinais_amostra.calcula(meta, Path(pasta), range(ano, ano + 1))
            lidas = pd.read_csv(arquivo, dtype={"cd_cvm": str, "cd_conta": str, "ds_conta": str})
        if not ((s.cd_cvm.values == meta.cd_cvm.values).all() and (s.dt_refer.values == meta.dt_refer.values).all()):
            raise AssertionError("sinais e empresa-anos fora de ordem")
        s["versao"] = meta.versao.values
        depreciacao = dva.depreciacao(dva.le(brutos_dva or fontes.pasta, ano)) if mudancas.depi_dva else None
        s, _ = motor.calcula(s, lidas, depreciacao, mudancas)
        s["ultima_versao"], s["num_doc"] = meta.ultima_versao.values, meta.num_doc.values
        partes.append(s)
    lista = pd.concat(partes, ignore_index=True) if partes else pd.DataFrame(columns=COLUNAS)
    ordem = lista.assign(_cd=lista.cd_cvm.astype(int)).sort_values(["_cd", "exercicio", "dt_refer"], kind="stable")
    return ordem.drop(columns="_cd").reset_index(drop=True)


def texto(lista: pd.DataFrame, commit: str, python: str, lock_sha256: str, arquivos: list[tuple[str, str]]) -> bytes:
    """O arquivo da lista do v2, em bytes, no formato da lista do v1 (cabeçalho e CSV em formato fixo)."""
    buf = io.StringIO()
    buf.write(f"{TITULO}\n# commit: {commit}\n# python: {python}\n# requirements-lock.txt: {lock_sha256}\n")
    for nome, h in arquivos:
        buf.write(f"# entrada: {nome} {h}\n")
    buf.write(f"# empresa_anos: {len(lista)}\n# pendentes_enet: {len(lista_v1.pendentes_enet(lista))}\n")
    w = csv.writer(buf, lineterminator="\n")
    w.writerow(COLUNAS)
    presentes = [c for c in COLUNAS if c in lista.columns]
    for r in lista[presentes].itertuples(index=False):
        valores = dict(zip(presentes, r))
        w.writerow([celula(c, valores.get(c)) for c in COLUNAS])
    return buf.getvalue().encode("utf-8")


def gerar(fontes: Fontes, exercicios: Iterable[int], commit: str, python: str, lock_sha256: str) -> bytes:
    anos = [abertura.garantir_exercicio(a) for a in exercicios]
    lista = calcular(fontes, anos)
    return texto(lista, commit, python, lock_sha256, lista_v1.entradas(fontes, anos, lista))


def ler(conteudo: bytes) -> pd.DataFrame:
    """A lista do v2 lida de volta, com os tipos das colunas (inteiros, booleanos e números)."""
    linhas = [x for x in conteudo.decode("utf-8").split("\n") if x and not x.startswith("#")]
    d = pd.read_csv(io.StringIO("\n".join(linhas)), dtype=str, keep_default_na=False)
    inteiros, booleanos = lista_v1.INTEIROS | INTEIROS, lista_v1.BOOLEANOS | BOOLEANOS
    numeros = lista_v1.NUMEROS | NUMEROS | DO_ESCORE
    for c in d.columns:
        vazio = d[c] == ""
        if c in inteiros:
            d[c] = pd.array([None if x == "" else int(x) for x in d[c]], dtype="Int64")
        elif c in booleanos:
            d[c] = pd.array([None if x == "" else x == "1" for x in d[c]], dtype="boolean")
        elif c in numeros:
            d[c] = d[c].where(~vazio, None).astype(float)
        else:
            d[c] = d[c].where(~vazio, None)
    return d


def main(argv: list[str] | None = None) -> int:
    a = argparse.ArgumentParser(description="Lista do motor v2 (emenda 5 do estudo 2).")
    a.add_argument("--exercicios", type=int, nargs="+", help=f"padrão: os de lacre.{abertura.CONSTANTE}")
    a.add_argument("--brutos", type=Path, default=base.BRUTOS)
    a.add_argument("--cache-enet", type=Path, default=base.CACHE_ENET)
    a.add_argument("--saida", type=Path, default=LISTA)
    a.add_argument("--conferir", help="SHA-256 esperado (recálculo): confere e não grava")
    args = a.parse_args(argv)
    anos = args.exercicios or list(abertura.exercicios_do_v2())
    if not anos:
        raise SystemExit(f"o lacre da lista do v2 está fechado: lacre.{abertura.CONSTANTE} não existe")
    anos = [abertura.garantir_exercicio(x) for x in anos]
    if sys.version_info[:2] != lista_v1.PYTHON:
        p = lista_v1.PYTHON
        raise SystemExit(f"a lista usa o Python {p[0]}.{p[1]} (seção 8 do estudo 2); este é {sys.version.split()[0]}")
    if lista_v1._git("status", "--porcelain", "--", "chiocca", "requirements-lock.txt", "data/cdi_sgs4389.csv"):
        raise SystemExit("o código tem mudança local: a lista só é calculada a partir de um commit")
    commit, lock = lista_v1._git("rev-parse", "HEAD"), lista_v1.sha256(lista_v1.LOCK)
    python = f"{lista_v1.PYTHON[0]}.{lista_v1.PYTHON[1]}"
    primeiro = gerar(Fontes(args.brutos, args.cache_enet), anos, commit, python, lock)
    segundo = gerar(Fontes(args.brutos, args.cache_enet), anos, commit, python, lock)
    h1, h2 = hashlib.sha256(primeiro).hexdigest(), hashlib.sha256(segundo).hexdigest()
    if h1 != h2:
        raise SystemExit(f"o cálculo não é determinístico: {h1} e {h2}")
    if args.conferir:
        igual = "igual" if h1 == args.conferir else "DIFERENTE"
        print(f"SHA-256 do recálculo: {h1}; esperado: {args.conferir}; {igual}")
        return 0 if h1 == args.conferir else 1
    args.saida.parent.mkdir(parents=True, exist_ok=True)
    args.saida.write_bytes(primeiro)
    print(f"lista gravada em {args.saida}: {len(primeiro)} bytes; SHA-256 {h1} (igual nas duas execuções)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
