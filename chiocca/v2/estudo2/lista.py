"""Estudo 2: o cálculo da lista lacrada (pré-registro do estudo 2, seções 3, 4.3, 8 e 9).

O motor v1 sem nenhuma mudança, pelo caminho do estudo 1: para cada exercício, as empresa-anos do índice da DFP com
`chiocca.base.como_era` (cada empresa na data de corte do seu exercício: 30/04/2025 para 2024 e 30/04/2026 para 2025,
para quem fecha em 31/12), o grupo por `chiocca.grupos`, os mesmos campos de `chiocca.montar_base.monta` e, depois,
`chiocca.sinais_amostra.calcula` e `alertas`, com os decis dentro de cada exercício. Os dados vêm dos arquivos brutos
(`chiocca.cvm.Fontes`: DFP e FCA do exercício e o cadastro) e do cache do ENET, como no estudo 1; o armazém do produto
não é usado, e o script não importa nenhum módulo do produto além do lacre.

O arquivo (seção 8): CSV em UTF-8 com quebra de linha LF, ordenado por código CVM (numérico), exercício e data de
referência, números com `CASAS` casas fixas, sem data de geração. Antes do cabeçalho das colunas, linhas começadas por
"#" com o commit do código, a versão menor do Python, o SHA-256 do requirements-lock.txt e o SHA-256 de cada arquivo de
entrada (os zips da DFP e do FCA de cada exercício, o cadastro, a série do CDI e cada tabela do ENET lida). Depois,
uma linha por empresa-ano do índice da DFP (as avaliadas e também as fora da amostra, com a situação), com as colunas
de `resultados/sinais_empresa_ano.csv` do estudo 1 (sinais, componentes, motivos de "não calculável" e alertas), mais
a versão usada, a última versão, o documento e o número de sinais disparados.

Decisão 4 (seção 4.3): o comparativo de 2024 dentro da DFP de 2025 é lido só como entrada do motor (a coluna PENÚLTIMO
dos índices de 2025). Este script não grava nenhuma comparação entre versões; a comparação é só da avaliação
secundária (`chiocca.v2.estudo2.secundaria`).

Lacre: cada exercício passa por `abertura.garantir_exercicio` antes de qualquer leitura. Acima de 2023, só os que o
commit de abertura puser em `lacre.ESTUDO_2_EXERCICIOS`.

Uso, na sessão de abertura, depois do commit que abre o lacre e do download (seção 3.1):
  python -m chiocca.v2.estudo2.lista --pendentes resultados/estudo2/pendentes_enet.txt
  python -m chiocca.enet resultados/estudo2/pendentes_enet.txt        # versões da época do ENET, no ritmo do estudo 1
  python -m chiocca.v2.estudo2.lista                                   # calcula duas vezes, confere e grava a lista
Recálculo na avaliação: no commit em que a lista foi calculada (git checkout), com os arquivos do branch
`estudo-2-dados`, o lock e o Python 3.13, `python -m chiocca.v2.estudo2.lista --conferir <SHA-256>` tem de dar o
mesmo arquivo, byte a byte.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import math
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Iterable

import pandas as pd

from chiocca import base, cdi, enet, grupos, montar_base, sinais_amostra
from chiocca.cvm import Fontes
from chiocca.sinais.mscore import COEFICIENTES
from chiocca.v2.estudo2 import abertura

SAIDA = base.RAIZ / "resultados" / "estudo2"
LISTA = SAIDA / "lista_estudo_2.csv"
LOCK = base.RAIZ / "requirements-lock.txt"
PYTHON = (3, 13)  # seção 8: o recálculo usa a mesma versão menor do Python
CASAS = 6
TITULO = "# chiocca: lista do estudo 2 (pré-registro do estudo 2, seção 8)"

COLUNAS_ESTUDO_1 = [
    "exercicio", "cd_cvm", "dt_refer", "grupo", "plano", "tipo", "fonte", "dt_receb", "data_corte", "status",
    "amostra", "marca_cpc06", "alavancagem", "alavancagem_motivo", "peso_nao_recorrente",
    "peso_nao_recorrente_motivo", "metodo_dfc", "marca_depreciacao_combinada", "juros_pagos_linhas_6_01",
    "juros_pagos_linhas_6_03", "sem_penultimo", *[x for c in COEFICIENTES for x in (c, f"{c}_motivo")], "mscore",
    "mscore_motivo", "dpo", "dpo_motivo", "cdi_medio", "juro_implicito", "juro", "juro_motivo", "lucro_sem_caixa",
    "lucro_sem_caixa_motivo", "alerta_mscore", "alerta_dpo", "alerta_juro", "alerta_peso_nao_recorrente",
    "alerta_regra_boba", "avaliada", "em_alerta",
]  # fmt: skip
COLUNAS = [*COLUNAS_ESTUDO_1, "versao", "ultima_versao", "num_doc", "n_sinais"]
INTEIROS = {"exercicio", "juros_pagos_linhas_6_01", "juros_pagos_linhas_6_03", "versao", "ultima_versao", "n_sinais"}
BOOLEANOS = {"marca_cpc06", "marca_depreciacao_combinada", "sem_penultimo", "alerta_mscore", "alerta_dpo",
             "alerta_juro", "alerta_peso_nao_recorrente", "alerta_regra_boba", "avaliada", "em_alerta"}  # fmt: skip
NUMEROS = {"alavancagem", "peso_nao_recorrente", *COEFICIENTES, "mscore", "dpo", "cdi_medio", "juro_implicito", "juro",
           "lucro_sem_caixa"}  # fmt: skip
DATAS = {"dt_receb", "data_corte"}
ALERTAS_NF = ("alerta_mscore", "alerta_dpo", "alerta_juro")
ALERTA_FIN = "alerta_peso_nao_recorrente"


def _vazio(v: Any) -> bool:
    if v is None or v is pd.NA or v is pd.NaT:
        return True
    try:
        return bool(pd.isna(v))
    except (TypeError, ValueError):
        return False


def _verdadeiro(v: Any) -> bool:
    return v.strip().lower() in ("true", "1") if isinstance(v, str) else bool(v)


def celula(coluna: str, v: Any) -> str:
    """Uma célula no formato fixo: vazio para ausente; inteiros sem casas; booleanos 1 ou 0; números com `CASAS`
    casas (sem "-0"); datas ISO; o resto como texto."""
    if _vazio(v) or (isinstance(v, str) and v == ""):
        return ""
    if coluna in INTEIROS:
        return str(int(float(v)))
    if coluna in BOOLEANOS:
        return "1" if _verdadeiro(v) else "0"
    if coluna in NUMEROS:
        x = float(v)
        if math.isinf(x):
            return "inf" if x > 0 else "-inf"
        s = f"{x:.{CASAS}f}"
        return s[1:] if s.startswith("-") and s.lstrip("-0.") == "" else s  # -0.000000 vira 0.000000
    if coluna in DATAS:
        return str(v)[:10]
    return str(v)


def _meta_e_contas(fontes: Fontes, exercicio: int) -> tuple[pd.DataFrame, pd.DataFrame]:
    """As empresa-anos do exercício na data de corte de cada uma, com os campos de `chiocca.montar_base.monta`, e as
    contas das que têm versão da época (o mesmo laço do estudo 1, sem gravar nada em data/)."""
    sit = montar_base.situacao_cadastro(fontes)
    idx = fontes.indice_dfp(exercicio)
    pares = idx[["cd_cvm", "DT_REFER", "CNPJ_CIA", "DENOM_CIA"]].drop_duplicates(["cd_cvm", "DT_REFER"])
    linhas: list[dict[str, Any]] = []
    partes = []
    for p in pares.itertuples():
        leitura = base.como_era(fontes, p.cd_cvm, exercicio, dt_refer=p.DT_REFER)
        st, origem = (
            grupos.setor(fontes, p.cd_cvm, exercicio, leitura.data_corte) if leitura.data_corte else (None, "nenhum")
        )
        ok = leitura.status == base.OK
        plano = grupos.plano_de_contas(grupos.descricao_301(leitura.contas)) if ok else None
        rec = montar_base.receita(leitura.contas) if ok else None
        linhas.append({
            "exercicio": exercicio, "cd_cvm": p.cd_cvm, "dt_refer": p.DT_REFER, "cnpj": p.CNPJ_CIA,
            "denominacao": p.DENOM_CIA, "data_corte": leitura.data_corte, "status": leitura.status,
            "versao": leitura.versao, "dt_receb": leitura.dt_receb, "ultima_versao": leitura.ultima_versao,
            "tipo": leitura.tipo, "fonte": leitura.fonte, "num_doc": leitura.num_doc,
            "repetidas_iguais": leitura.repetidas_iguais, "setor": st, "origem_setor": origem, "plano": plano,
            "grupo": grupos.grupo(st, plano) if plano else None,
            "sem_receita": (rec is None or rec == 0) if ok else None,
            "situacao_cadastro": sit.get(p.cd_cvm, "fora_do_cadastro"),
        })  # fmt: skip
        if ok:
            c = leitura.contas.copy()
            c.insert(0, "dt_refer", leitura.dt_refer)
            c.insert(0, "cd_cvm", leitura.cd_cvm)
            partes.append(c)
    vazias = pd.DataFrame(columns=["cd_cvm", "dt_refer", *base.COLUNAS])
    return pd.DataFrame(linhas), pd.concat(partes, ignore_index=True) if partes else vazias


def _n_sinais(s: pd.DataFrame) -> pd.Series:
    """Sinais de alerta disparados na empresa-ano (os do grupo); vazio fora da amostra."""
    nf = sum(s[c].astype("boolean").fillna(False).astype(int) for c in ALERTAS_NF)
    fin = s[ALERTA_FIN].astype("boolean").fillna(False).astype(int)
    n = pd.Series(pd.NA, index=s.index, dtype="Int64")
    n[s.amostra == sinais_amostra.AMOSTRA_NF] = nf[s.amostra == sinais_amostra.AMOSTRA_NF]
    n[s.amostra == sinais_amostra.AMOSTRA_FIN] = fin[s.amostra == sinais_amostra.AMOSTRA_FIN]
    return n


def calcular(fontes: Fontes, exercicios: Iterable[int]) -> pd.DataFrame:
    """Sinais e alertas do motor v1 de todas as empresa-anos dos exercícios, cada uma na data de corte do seu
    exercício. Todos os exercícios passam pelo lacre antes de qualquer leitura."""
    anos = [abertura.garantir_exercicio(a) for a in exercicios]
    partes = []
    for ano in anos:
        meta, contas = _meta_e_contas(fontes, ano)
        with tempfile.TemporaryDirectory() as pasta:  # o motor v1 lê as contas de um CSV, como em data/base
            contas.to_csv(Path(pasta) / f"contas_{ano}.csv.gz", index=False)
            s = sinais_amostra.calcula(meta, Path(pasta), range(ano, ano + 1))
        for col in ("mscore", "dpo", "juro", "peso_nao_recorrente", "alavancagem"):  # grupo sem nenhuma empresa
            if col not in s.columns:
                s[col] = float("nan")
        s, _ = sinais_amostra.alertas(s)
        if not ((s.cd_cvm.values == meta.cd_cvm.values).all() and (s.dt_refer.values == meta.dt_refer.values).all()):
            raise AssertionError("sinais e empresa-anos fora de ordem")
        for col in ("versao", "ultima_versao", "num_doc"):
            s[col] = meta[col].values
        partes.append(s)
    lista = pd.concat(partes, ignore_index=True) if partes else pd.DataFrame(columns=COLUNAS)
    lista["n_sinais"] = _n_sinais(lista)
    ordem = lista.assign(_cd=lista.cd_cvm.astype(int)).sort_values(["_cd", "exercicio", "dt_refer"], kind="stable")
    return ordem.drop(columns="_cd").reset_index(drop=True)


def pendentes_enet(lista: pd.DataFrame) -> list[str]:
    """Versões da época que precisam vir do ENET, no formato de `python -m chiocca.enet`: "documento versão"."""
    p = lista[lista.status == base.PENDENTE_ENET]
    return sorted({f"{d} {int(v)}" for d, v in zip(p.num_doc, p.versao)}, key=lambda x: [int(y) for y in x.split()])


def sha256(caminho: Path) -> str:
    return hashlib.sha256(Path(caminho).read_bytes()).hexdigest()


def entradas(fontes: Fontes, exercicios: Iterable[int], lista: pd.DataFrame) -> list[tuple[str, str]]:
    """(nome, SHA-256) de cada arquivo de entrada, com nomes relativos (o cabeçalho não depende da máquina)."""
    out = []
    for ano in sorted(set(exercicios)):
        for nome in (f"dfp_cia_aberta_{ano}.zip", f"fca_cia_aberta_{ano}.zip"):
            out.append((nome, sha256(fontes.pasta / nome)))
    out.append(("cad_cia_aberta.csv", sha256(fontes.pasta / "cad_cia_aberta.csv")))
    out.append(("data/cdi_sgs4389.csv", sha256(cdi.SNAPSHOT)))
    anteriores = lista[lista.versao.notna() & (lista.versao != lista.ultima_versao) & lista.num_doc.notna()]
    for doc in sorted({str(d) for d in anteriores.num_doc}, key=int):
        p = enet.caminho_cache(fontes.cache_enet, doc)
        if p.exists():
            out.append((f"enet/{p.name}", sha256(p)))
    return out


def texto(lista: pd.DataFrame, commit: str, python: str, lock_sha256: str, arquivos: list[tuple[str, str]]) -> bytes:
    """O arquivo da lista, em bytes: cabeçalho com commit, Python, lock e entradas; depois, o CSV em formato fixo."""
    buf = io.StringIO()
    buf.write(f"{TITULO}\n# commit: {commit}\n# python: {python}\n# requirements-lock.txt: {lock_sha256}\n")
    for nome, h in arquivos:
        buf.write(f"# entrada: {nome} {h}\n")
    buf.write(f"# empresa_anos: {len(lista)}\n# pendentes_enet: {len(pendentes_enet(lista))}\n")
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
    return texto(lista, commit, python, lock_sha256, entradas(fontes, anos, lista))


def ler(conteudo: bytes) -> pd.DataFrame:
    """A lista lida de volta: exercício e versões como inteiros, booleanos como booleanos, números como float."""
    linhas = [x for x in conteudo.decode("utf-8").split("\n") if x and not x.startswith("#")]
    d = pd.read_csv(io.StringIO("\n".join(linhas)), dtype=str, keep_default_na=False)
    for c in d.columns:
        vazio = d[c] == ""
        if c in INTEIROS:
            d[c] = pd.array([None if x == "" else int(x) for x in d[c]], dtype="Int64")
        elif c in BOOLEANOS:
            d[c] = pd.array([None if x == "" else x == "1" for x in d[c]], dtype="boolean")
        elif c in NUMEROS:
            d[c] = d[c].where(~vazio, None).astype(float)
        else:
            d[c] = d[c].where(~vazio, None)
    return d


def _git(*args: str) -> str:
    return subprocess.run(["git", *args], cwd=base.RAIZ, capture_output=True, text=True, check=True).stdout.strip()


def main(argv: list[str] | None = None) -> int:
    from chiocca.v2.estudo2 import gabarito

    a = argparse.ArgumentParser(description="Lista lacrada do estudo 2 (pré-registro do estudo 2, seções 8 e 9).")
    a.add_argument("--exercicios", type=int, nargs="+", help="padrão: os de lacre.ESTUDO_2_EXERCICIOS")
    a.add_argument("--brutos", type=Path, default=base.BRUTOS)
    a.add_argument("--cache-enet", type=Path, default=base.CACHE_ENET)
    a.add_argument("--saida", type=Path, default=LISTA)
    a.add_argument("--pendentes", type=Path, help="só grava as versões da época que vêm do ENET e para")
    a.add_argument("--conferir", help="SHA-256 esperado (recálculo): confere e não grava")
    args = a.parse_args(argv)
    anos = args.exercicios or list(abertura.exercicios_do_estudo())
    if not anos:
        raise SystemExit("o lacre do estudo 2 está fechado: lacre.ESTUDO_2_EXERCICIOS não existe")
    anos = [abertura.garantir_exercicio(x) for x in anos]
    if sys.version_info[:2] != PYTHON:
        raise SystemExit(f"o estudo usa o Python {PYTHON[0]}.{PYTHON[1]} (seção 8); este é {sys.version.split()[0]}")
    if _git("status", "--porcelain", "--", "chiocca", "requirements-lock.txt", "data/cdi_sgs4389.csv"):
        raise SystemExit("o código tem mudança local: a lista só é calculada a partir de um commit")
    casos = gabarito.ler_parte(gabarito.PARTE_1)  # seção 9 e exigência 2: conferir acertavel_principal na abertura
    print(gabarito.resumo_da_conferencia(casos, gabarito.conferir_acertavel(casos, Fontes(args.brutos).indice_dfp)))
    if args.pendentes:
        lista = calcular(Fontes(args.brutos, args.cache_enet), anos)
        p = pendentes_enet(lista)
        args.pendentes.parent.mkdir(parents=True, exist_ok=True)
        args.pendentes.write_text("".join(f"{x}\n" for x in p), encoding="utf-8")
        print(f"empresa-anos: {len(lista)}; versões da época a buscar no ENET: {len(p)}")
        return 0
    commit, python, lock = _git("rev-parse", "HEAD"), f"{PYTHON[0]}.{PYTHON[1]}", sha256(LOCK)
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
