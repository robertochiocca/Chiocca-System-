"""Estudo 2: as partes do gabarito (pré-registro do estudo 2, seções 4.1, 5 e 7.1, e emenda 1).

- `ler_parte`: lê uma parte (UTF-8, cabeçalho de `data/gabarito_casos.csv` mais a coluna `parte`) e aceita o arquivo só
  com o cabeçalho: a parte 1 deste estudo não tem casos, e a descrição logo depois do lacre registra "parte 1: nenhum
  caso". O arquivo congelado só é lido, nunca alterado.
- `conferir_acertavel`: na abertura e em cada avaliação, confere `acertavel_principal` contra os metadados do índice da
  DFP: há, num exercício do período afetado (2024 ou 2025), versão entregue até o corte e antes da `data_publica`? Toda
  divergência é relatada; nada no arquivo muda. No cálculo vale a regra da seção 4.1 (`avaliar_caso`), não a coluna.
- `avaliar_caso` e `descrever_parte`: a regra da seção 4.1 sobre a lista lacrada. Acerto: a empresa entrou em alerta em
  pelo menos um exercício do período afetado, na amostra do seu grupo, com a versão usada (a pública no corte) entregue
  antes da data pública, como no estudo 1 (`chiocca.metricas`); se a data pública cai antes de 30/04/2026, só a DFP de
  2024 pode contar. Antecedência: meses entre a entrega da primeira DFP em alerta e a data pública (dias × 12/365,25,
  como nas análises do estudo 1). A chance de cada total ao acaso (cada caso com a taxa de alerta do seu grupo no
  exercício) é só descritiva (seção 7.1).

Uso: python -m chiocca.v2.estudo2.gabarito [--parte 1] [--lista resultados/estudo2/lista_estudo_2.csv]
"""

from __future__ import annotations

import argparse
import csv
import io
import json
from collections.abc import Callable
from datetime import date
from pathlib import Path
from typing import Any

import pandas as pd

from chiocca import base
from chiocca.corte import data_corte
from chiocca.sinais_amostra import AMOSTRA_FIN, AMOSTRA_NF
from chiocca.v2.estudo2 import abertura

GABARITO_ESTUDO_1 = base.RAIZ / "data" / "gabarito_casos.csv"
PARTE_1 = base.RAIZ / "data" / "gabarito_estudo_2_parte_1.csv"
EXERCICIOS = (2024, 2025)
DATA_MINIMA_2025 = "2026-04-30"  # seção 4.1: com a data pública antes disso, só a DFP de 2024 pode contar
MESES_POR_DIA = 12 / 365.25
AMOSTRAS = (AMOSTRA_NF, AMOSTRA_FIN)
ALERTAS = ("alerta_mscore", "alerta_dpo", "alerta_juro", "alerta_peso_nao_recorrente")


def colunas() -> list[str]:
    with GABARITO_ESTUDO_1.open(encoding="utf-8", newline="") as f:
        return [*next(csv.reader(f)), "parte"]


def ler_parte(caminho: Path) -> list[dict[str, str]]:
    """Os casos de uma parte; o arquivo só com o cabeçalho dá a lista vazia."""
    linhas = list(csv.reader(io.StringIO(Path(caminho).read_bytes().decode("utf-8"), newline="")))
    esperadas = colunas()
    if not linhas or linhas[0] != esperadas:
        raise ValueError(f"{caminho}: cabeçalho diferente do formato da parte (gabarito do estudo 1 mais 'parte')")
    casos = []
    for k, linha in enumerate(linhas[1:], start=2):
        if not linha:
            continue
        if len(linha) != len(esperadas):
            raise ValueError(f"{caminho}, linha {k}: {len(linha)} colunas, esperadas {len(esperadas)}")
        casos.append(dict(zip(esperadas, linha)))
    return casos


def _sim(v: Any) -> bool:
    return False if v is None or pd.isna(v) else bool(v)


def anos_do_caso(caso: dict[str, str]) -> list[int]:
    """Exercícios do período afetado dentro de 2024 e 2025."""
    try:
        ini, fim = int(caso["periodo_afetado_inicio"]), int(caso["periodo_afetado_fim"])
    except (KeyError, ValueError):
        return []
    return [a for a in EXERCICIOS if ini <= a <= fim]


def conta_pela_regra_4_1(exercicio: int, data_publica: str) -> bool:
    return int(exercicio) != 2025 or data_publica >= DATA_MINIMA_2025


def _cd(caso: dict[str, str]) -> str:
    return caso.get("cd_cvm", "").strip().lstrip("0")


def versao_no_corte(indice: pd.DataFrame, cd_cvm: str) -> tuple[int, date] | None:
    """A versão pública no corte pelo índice da DFP (só metadados), com a mesma regra do `como_era`."""
    docs = indice[indice.cd_cvm == cd_cvm]
    if docs.empty:
        return None
    dt_refer = str(docs.DT_REFER.max())
    docs = docs[docs.DT_REFER == dt_refer]
    receb = docs.groupby("versao").dt_receb.max()  # mesma versão listada duas vezes: vale a data mais tardia
    validas = receb[receb <= data_corte(dt_refer)]
    if validas.empty:
        return None
    v = int(validas.index.max())
    return v, validas.loc[v]


def conferir_acertavel(casos: list[dict[str, str]], indice: Callable[[int], pd.DataFrame]) -> list[dict[str, Any]]:
    """Para cada caso, acertável pelos metadados do índice (versão entregue até o corte e antes da data pública, num
    exercício do período afetado) contra `acertavel_principal`; `divergente` marca toda diferença."""
    out = []
    for c in casos:
        cd, dp = _cd(c), c.get("data_publica", "").strip()
        pelo_indice = []
        for ano in anos_do_caso(c) if cd and dp else []:
            v = versao_no_corte(indice(abertura.garantir_exercicio(ano)), cd)
            if v is not None and str(v[1]) < dp:
                pelo_indice.append(ano)
        no_arquivo = c.get("acertavel_principal", "").strip() == "sim"
        out.append({
            "caso_id": c.get("caso_id"), "parte": c.get("parte"), "acertavel_principal": c.get("acertavel_principal"),
            "acertavel_pelo_indice": bool(pelo_indice), "exercicios_pelo_indice": pelo_indice,
            "exercicios_pela_regra_4_1": [a for a in pelo_indice if conta_pela_regra_4_1(a, dp)],
            "divergente": no_arquivo != bool(pelo_indice),
        })  # fmt: skip
    return out


def resumo_da_conferencia(casos: list[dict[str, str]], conferencia: list[dict[str, Any]]) -> str:
    partes = sorted({c.get("parte", "") for c in casos})
    if not casos:
        return "conferência de acertavel_principal: nenhum caso na parte; nenhuma divergência"
    div = [c for c in conferencia if c["divergente"]]
    texto = (
        f"conferência de acertavel_principal (parte {', '.join(partes)}): {len(casos)} casos, {len(div)} divergências"
    )
    return texto + "".join(
        f"\n- {c['caso_id']}: no arquivo {c['acertavel_principal']}; pelo índice "
        f"{'sim' if c['acertavel_pelo_indice'] else 'não'} (exercícios {c['exercicios_pelo_indice']})"
        for c in div
    )


def avaliar_caso(caso: dict[str, str], lista: pd.DataFrame) -> dict[str, Any]:
    """A regra da seção 4.1 para um caso, sobre a lista lida por `chiocca.v2.estudo2.lista.ler`."""
    cd, dp, anos = _cd(caso), caso.get("data_publica", "").strip(), anos_do_caso(caso)
    linhas = lista[(lista.cd_cvm == cd) & lista.exercicio.isin(anos)] if cd and dp else lista.iloc[0:0]
    detalhe, fora = [], []
    for ano in anos:
        r = linhas[linhas.exercicio == ano]
        if r.empty:
            fora.append([ano, "sem_dfp"])
            continue
        motivos = []
        for _, x in r.iterrows():  # em geral uma linha; duas se o exercício tiver duas datas de referência
            receb = None if pd.isna(x.dt_receb) else str(x.dt_receb)[:10]
            if x.amostra not in AMOSTRAS:
                motivos.append(str(x.amostra))
            elif receb is None or not receb < dp:
                motivos.append("depois_da_data")
            elif not conta_pela_regra_4_1(ano, dp):
                motivos.append("regra_4_1")
            else:
                sinais = [a.removeprefix("alerta_") for a in ALERTAS if a in x.index and _sim(x[a])]
                detalhe.append({"exercicio": ano, "amostra": str(x.amostra), "dt_receb": receb, "sinais": sinais,
                                "avaliada": _sim(x.avaliada), "em_alerta": _sim(x.em_alerta)})  # fmt: skip
        if not any(d["exercicio"] == ano for d in detalhe):
            fora.append([ano, motivos[0]])
    em_alerta = [d for d in detalhe if d["em_alerta"]]
    primeira = min(em_alerta, key=lambda d: (d["dt_receb"], d["exercicio"])) if em_alerta else None
    dias = (date.fromisoformat(dp) - date.fromisoformat(str(primeira["dt_receb"]))).days if primeira else None
    return {
        "caso_id": caso.get("caso_id"), "parte": caso.get("parte"), "acertavel": bool(detalhe),
        "acertado": bool(em_alerta), "exercicios_que_contam": detalhe, "exercicios_fora": fora,
        "antecedencia_meses": None if dias is None else dias * MESES_POR_DIA,
    }  # fmt: skip


def binomial_de_poisson(probabilidades: list[float]) -> list[float]:
    """P(K = k) da soma de Bernoullis independentes (a mesma conta das análises do estudo 1)."""
    pmf = [1.0]
    for p in probabilidades:
        nova = [0.0] * (len(pmf) + 1)
        for k, q in enumerate(pmf):
            nova[k] += q * (1 - p)
            nova[k + 1] += q * p
        pmf = nova
    return pmf


def taxa_de_alerta(lista: pd.DataFrame, exercicio: int, amostra: str) -> float | None:
    g = lista[(lista.exercicio == exercicio) & (lista.amostra == amostra) & lista.avaliada.fillna(False)]
    return None if g.empty else float(g.em_alerta.fillna(False).mean())


def descrever_parte(casos: list[dict[str, str]], lista: pd.DataFrame | None, parte: int) -> dict[str, Any]:
    """A descrição de uma parte (seção 7.1): cada caso pela regra da seção 4.1, os totais e a chance do total ao acaso,
    só como descrição. Sem casos, "parte N: nenhum caso", sem ler a lista."""
    if not casos:
        return {"parte": parte, "casos": 0, "acertaveis": 0, "acertados": 0, "texto": f"parte {parte}: nenhum caso"}
    if lista is None:
        raise ValueError("a parte tem casos: a descrição precisa da lista")
    avaliados = [avaliar_caso(c, lista) for c in casos]
    acertaveis = [a for a in avaliados if a["acertavel"]]
    ps = []
    for a in acertaveis:
        nao = 1.0
        for d in a["exercicios_que_contam"]:
            nao *= 1 - (taxa_de_alerta(lista, d["exercicio"], d["amostra"]) or 0.0)
        ps.append(1 - nao)
    acertados = sum(a["acertado"] for a in acertaveis)
    pmf = binomial_de_poisson(ps)
    return {
        "parte": parte, "casos": len(casos), "acertaveis": len(acertaveis), "acertados": acertados,
        "chance_de_ao_menos_esse_total_ao_acaso": float(sum(pmf[acertados:])), "por_caso": avaliados,
        "texto": f"parte {parte}: {len(casos)} casos, {len(acertaveis)} acertáveis, {acertados} acertados",
    }  # fmt: skip


def main(argv: list[str] | None = None) -> int:
    from chiocca.v2.estudo2 import lista as modulo_lista

    a = argparse.ArgumentParser(description="Parte do gabarito do estudo 2: conferência e descrição (seção 7.1).")
    a.add_argument("--parte", type=int, default=1)
    a.add_argument("--arquivo", type=Path, help="padrão: data/gabarito_estudo_2_parte_<parte>.csv")
    a.add_argument("--lista", type=Path, help="a lista lacrada (só se a parte tiver casos)")
    a.add_argument("--brutos", type=Path, default=base.BRUTOS)
    args = a.parse_args(argv)
    from chiocca.cvm import Fontes

    arquivo = args.arquivo or base.RAIZ / "data" / f"gabarito_estudo_2_parte_{args.parte}.csv"
    casos = ler_parte(arquivo)
    print(resumo_da_conferencia(casos, conferir_acertavel(casos, Fontes(args.brutos).indice_dfp)))
    lista = modulo_lista.ler(args.lista.read_bytes()) if casos and args.lista else None
    print(json.dumps(descrever_parte(casos, lista, args.parte), ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
