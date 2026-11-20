"""Estudo 2: a avaliação secundária, à parte da lista (pré-registro do estudo 2, seções 4.2, 4.3, 6 e 7.2).

Única, numa sessão a partir de 31/05/2027, sobre a lista lacrada conferida pelo SHA-256 (o recálculo byte a byte é da
seção 8, por `chiocca.v2.estudo2.lista --conferir`). Só contagens agregadas saem daqui.

- **Republicação relevante (definição estreita, a do teste):** na DFP t+1, na versão pública no corte de t+1 (30/04/2026
  para t = 2024; 30/04/2027 para t = 2025), o comparativo de t tem diferença destacada no patrimônio líquido (BPP 2.03)
  ou no lucro líquido (DRE 3.11) em relação à versão de t usada pelo motor. "Destacada" é a regra de materialidade do
  produto, sem mudança (`chiocca.v2.comparativo.comparar`: acima da tolerância e, em valor absoluto, acima de 1% do
  ativo total da versão usada de t). Regra larga (só descritivo): qualquer diferença destacada do grupo (a).
- **Empresa-anos avaliadas:** as não financeiras avaliadas da lista com uma versão de t+1 no corte de t+1, do mesmo
  tipo; a versão de t é recalculada com os mesmos dados e tem de ser a da lista (senão, a avaliação para). As
  financeiras entram só no descritivo. A DFP de 2026 só é lida depois da segunda abertura (`abertura`).
- **Medida principal:** DR = P(republicação | em alerta) − P(republicação | fora de alerta), com os dois exercícios
  juntos; também a razão de taxas. Bootstrap por companhia: sorteiam-se companhias com reposição, cada uma com as suas
  empresa-anos; `REAMOSTRAGENS` reamostragens com a semente `SEMENTE` (`numpy.random.default_rng`); o limite inferior
  do intervalo unilateral de 95% é o percentil 5 das reamostragens com DR definida. "Associação positiva" se o limite
  ficar acima de zero.
- **Regra boba lado a lado:** o alerta do decil mais endividado de cada exercício na lista (`alerta_regra_boba`; sem
  alavancagem calculável, fora de alerta, como no estudo 1), com a mesma DR e o mesmo sorteio; a comparação é a
  diferença entre a DR do motor e a da regra boba, com o limite inferior do mesmo bootstrap pareado.
- **Métricas de ranking (secundárias deste desfecho):** precisão no topo de 1%, 5% e 10%, lift no topo (precisão ÷
  taxa geral) e NDCG@k pelas definições de Bao et al. (2020, Tabela 3): DCG@k = Σ (2^rel_i − 1) / log2(i + 1) para
  i = 1..k e NDCG@k = DCG@k ÷ DCG@k da ordem ideal, com relevância 1 para a republicação estreita; k = ⌈p × n⌉ (pelo
  menos 1) empresa-anos. Ordem do motor: número de sinais disparados, depois o M-score (maior primeiro; sem M-score,
  depois dos que têm), depois o código CVM e, para as duas empresa-anos da mesma companhia, o exercício. Regra boba:
  pela alavancagem (maior primeiro; sem ela, no fim), depois o código CVM e o exercício. Intervalos pelo mesmo
  bootstrap.

Uso: python -m chiocca.v2.estudo2.secundaria --lista resultados/estudo2/lista_estudo_2.csv --sha256 <SHA-256 da lista>
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
from collections.abc import Callable
from datetime import date
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from chiocca import base
from chiocca.cvm import Fontes
from chiocca.sinais_amostra import AMOSTRA_FIN, AMOSTRA_NF
from chiocca.v2 import comparativo
from chiocca.v2.estudo2 import abertura

SEMENTE = 20270531
REAMOSTRAGENS = 10_000
PERCENTIL_INFERIOR = 5.0  # limite inferior do intervalo unilateral de 95%
TOPOS = (0.01, 0.05, 0.10)
DATA_MINIMA = date(2027, 5, 31)
LINHAS_ESTREITAS = frozenset({("BPP", "2.03"), ("DRE", "3.11")})
SAIDA = base.RAIZ / "docs" / "estudo_2_secundaria.json"


def _sim(v: Any) -> bool:
    return False if v is None or pd.isna(v) else bool(v)


def republicacoes(fontes: Fontes, lista: pd.DataFrame) -> pd.DataFrame:
    """Para cada empresa-ano avaliada da lista (não financeiras e, para o descritivo, financeiras), a republicação
    estreita e a larga pelo comparativo da DFP t+1 na versão do corte de t+1. Nada é gravado."""
    linhas = []
    for r in lista[lista.amostra.isin([AMOSTRA_NF, AMOSTRA_FIN]) & lista.avaliada.fillna(False)].itertuples():
        t = int(r.exercicio)
        abertura.garantir_seguinte(t + 1)
        lt = base.como_era(fontes, r.cd_cvm, t, dt_refer=r.dt_refer)
        if lt.status != base.OK or lt.versao != int(r.versao) or str(lt.num_doc) != str(r.num_doc):
            raise ValueError(f"empresa-ano {r.cd_cvm}/{t}: a versão recalculada não é a da lista")
        seg = base.como_era(fontes, r.cd_cvm, t + 1)
        linha = {"exercicio": t, "cd_cvm": str(r.cd_cvm), "amostra": r.amostra, "em_alerta": _sim(r.em_alerta),
                 "alerta_regra_boba": _sim(r.alerta_regra_boba), "n_sinais": int(r.n_sinais),
                 "mscore": r.mscore, "alavancagem": r.alavancagem, "situacao_seguinte": seg.status,
                 "num_doc_seguinte": seg.num_doc, "versao_seguinte": seg.versao}  # fmt: skip
        if seg.status == base.OK and seg.tipo == lt.tipo:
            dest = {(d.demonstracao, d.cd_conta) for d in comparativo.comparar(lt, seg) if d.destacada}
            linha |= {"avaliada": True, "estreita": bool(dest & LINHAS_ESTREITAS), "larga": bool(dest)}
        else:
            linha |= {"avaliada": False, "estreita": False, "larga": False,
                      "situacao_seguinte": seg.status if seg.status != base.OK else "tipo_diferente"}  # fmt: skip
        linhas.append(linha)
    return pd.DataFrame(linhas)


def pendentes_enet(rep: pd.DataFrame) -> list[str]:
    p = rep[rep.situacao_seguinte == base.PENDENTE_ENET]
    return sorted({f"{d} {int(v)}" for d, v in zip(p.num_doc_seguinte, p.versao_seguinte)})


# ---- medidas ----


def taxas(alerta: np.ndarray, y: np.ndarray) -> dict[str, Any]:
    n1, n0 = int(alerta.sum()), int((~alerta).sum())
    y1, y0 = int((y & alerta).sum()), int((y & ~alerta).sum())
    p1 = y1 / n1 if n1 else math.nan
    p0 = y0 / n0 if n0 else math.nan
    return {"em_alerta": {"empresa_anos": n1, "republicacoes": y1, "taxa": p1},
            "fora_de_alerta": {"empresa_anos": n0, "republicacoes": y0, "taxa": p0},
            "dr": p1 - p0, "rr": p1 / p0 if p0 > 0 else math.nan}  # fmt: skip


def dr(alerta: np.ndarray, y: np.ndarray) -> float:
    return float(taxas(alerta, y)["dr"])


def ordem_do_motor(rep: pd.DataFrame) -> np.ndarray:
    """Posição de cada empresa-ano no ranking do motor (0 = topo)."""
    chave = pd.DataFrame({"n": -rep.n_sinais.astype(float), "sem_m": rep.mscore.isna(), "m": -rep.mscore.fillna(0.0),
                          "cd": rep.cd_cvm.astype(int), "ex": rep.exercicio.astype(int)})  # fmt: skip
    return _posicoes(chave.sort_values(["n", "sem_m", "m", "cd", "ex"], kind="stable").index, len(rep))


def ordem_da_regra_boba(rep: pd.DataFrame) -> np.ndarray:
    chave = pd.DataFrame({"sem_a": rep.alavancagem.isna(), "a": -rep.alavancagem.fillna(0.0),
                          "cd": rep.cd_cvm.astype(int), "ex": rep.exercicio.astype(int)})  # fmt: skip
    return _posicoes(chave.sort_values(["sem_a", "a", "cd", "ex"], kind="stable").index, len(rep))


def _posicoes(ordem: pd.Index, n: int) -> np.ndarray:
    pos = np.empty(n, dtype=np.int64)
    pos[np.asarray(ordem)] = np.arange(n)
    return pos


def topo(p: float, n: int) -> int:
    return max(1, math.ceil(p * n))


def ranking(rel_ordenada: np.ndarray, p: float) -> dict[str, float]:
    """Precisão no topo, lift e NDCG@k de uma lista já ordenada (relevância 0 ou 1)."""
    n = len(rel_ordenada)
    if n == 0:
        return {"k": 0, "precisao": math.nan, "lift": math.nan, "ndcg": math.nan}
    k = min(topo(p, n), n)
    acertos = rel_ordenada[:k].astype(float)
    precisao = float(acertos.sum() / k)
    geral = float(rel_ordenada.mean()) if n else math.nan
    descontos = 1.0 / np.log2(np.arange(2, k + 2))
    dcg = float(((2.0**acertos - 1.0) * descontos).sum())
    ideal = float(descontos[: min(k, int(rel_ordenada.sum()))].sum())
    return {"k": k, "precisao": precisao, "lift": precisao / geral if geral > 0 else math.nan,
            "ndcg": dcg / ideal if ideal > 0 else math.nan}  # fmt: skip


def _ranking_nas_linhas(idx: np.ndarray, pos: np.ndarray, y: np.ndarray, p: float) -> dict[str, float]:
    return ranking(y[idx[np.argsort(pos[idx], kind="stable")]], p)


def _estatistica_de_ranking(pos: np.ndarray, y: np.ndarray, p: float, medida: str) -> Callable[[np.ndarray], float]:
    return lambda idx: _ranking_nas_linhas(idx, pos, y, p)[medida]


def bootstrap_por_companhia(
    companhia: np.ndarray,
    estatisticas: dict[str, Callable[[np.ndarray], float]],
    reamostragens: int = REAMOSTRAGENS,
    semente: int = SEMENTE,
) -> dict[str, np.ndarray]:
    """Cada estatística recebe os índices das linhas de uma reamostragem (companhias sorteadas com reposição, cada uma
    com todas as suas empresa-anos). Todas usam o mesmo sorteio (bootstrap pareado)."""
    codigos = sorted(set(companhia.tolist()), key=int)
    linhas_por = [np.flatnonzero(companhia == c) for c in codigos]
    rng = np.random.default_rng(semente)
    out = {nome: np.empty(reamostragens) for nome in estatisticas}
    for b in range(reamostragens):
        sorteio = rng.integers(0, len(codigos), size=len(codigos))
        idx = np.concatenate([linhas_por[k] for k in sorteio])
        for nome, f in estatisticas.items():
            out[nome][b] = f(idx)
    return out


def limite_inferior(valores: np.ndarray) -> float | None:
    ok = valores[~np.isnan(valores)]
    return float(np.percentile(ok, PERCENTIL_INFERIOR)) if len(ok) else None


def _num(x: Any) -> Any:
    if isinstance(x, dict):
        return {k: _num(v) for k, v in x.items()}
    if isinstance(x, float) and (math.isnan(x) or math.isinf(x)):
        return None
    return x


def avaliar(rep: pd.DataFrame, reamostragens: int = REAMOSTRAGENS, semente: int = SEMENTE) -> dict[str, Any]:
    """As medidas da seção 7.2 sobre as não financeiras avaliadas; financeiras e regra larga só no descritivo."""
    nf = rep[(rep.amostra == AMOSTRA_NF) & rep.avaliada].reset_index(drop=True)
    y = nf.estreita.to_numpy(bool)
    motor, boba = nf.em_alerta.to_numpy(bool), nf.alerta_regra_boba.to_numpy(bool)
    pos_motor, pos_boba = ordem_do_motor(nf), ordem_da_regra_boba(nf)
    estat: dict[str, Callable[[np.ndarray], float]] = {
        "dr_motor": lambda i: dr(motor[i], y[i]), "dr_boba": lambda i: dr(boba[i], y[i]),
        "rr_motor": lambda i: float(taxas(motor[i], y[i])["rr"]),
    }  # fmt: skip
    for p in TOPOS:
        for m in ("precisao", "lift", "ndcg"):
            estat[f"{m}_{p}_motor"] = _estatistica_de_ranking(pos_motor, y, p, m)
            estat[f"{m}_{p}_boba"] = _estatistica_de_ranking(pos_boba, y, p, m)
    todas = np.arange(len(nf))
    pontual = {nome: f(todas) for nome, f in estat.items()}
    b = bootstrap_por_companhia(nf.cd_cvm.to_numpy(str), estat, reamostragens, semente)
    dif = b["dr_motor"] - b["dr_boba"]
    lim_motor, lim_dif = limite_inferior(b["dr_motor"]), limite_inferior(dif)
    rank: dict[str, Any] = {}
    for p in TOPOS:
        chave = f"{round(p * 100)}%"
        rank[chave] = {"k": topo(p, len(nf))}
        for m in ("precisao", "lift", "ndcg"):
            mm, bb = f"{m}_{p}_motor", f"{m}_{p}_boba"
            rank[chave][m] = {"motor": pontual[mm], "motor_limite_inferior_95": limite_inferior(b[mm]),
                              "regra_boba": pontual[bb], "regra_boba_limite_inferior_95": limite_inferior(b[bb]),
                              "diferenca": pontual[mm] - pontual[bb],
                              "diferenca_limite_inferior_95": limite_inferior(b[mm] - b[bb])}  # fmt: skip
    fin = rep[(rep.amostra == AMOSTRA_FIN) & rep.avaliada]
    por_ano = {str(a): taxas(g.em_alerta.to_numpy(bool), g.estreita.to_numpy(bool)) for a, g in nf.groupby("exercicio")}
    return _num({
        "empresa_anos": len(nf), "companhias": int(nf.cd_cvm.nunique()), "reamostragens": reamostragens,
        "semente": semente, "reamostragens_sem_dr": int(np.isnan(b["dr_motor"]).sum()),
        "motor": taxas(motor, y) | {"dr_limite_inferior_95": lim_motor,
                                    "rr_limite_inferior_95": limite_inferior(b["rr_motor"])},
        "resultado": ("associação positiva" if lim_motor is not None and lim_motor > 0
                      else "sem evidência de associação"),
        "regra_boba": taxas(boba, y) | {"dr_limite_inferior_95": limite_inferior(b["dr_boba"])},
        "motor_menos_regra_boba": {
            "diferenca_dr": pontual["dr_motor"] - pontual["dr_boba"], "limite_inferior_95": lim_dif,
            "resultado": "o motor separa melhor que a regra boba" if lim_dif is not None and lim_dif > 0
            else "sem vencedor declarado"},
        "ranking": rank,
        "descritivos": {"regra_larga": taxas(motor, nf.larga.to_numpy(bool)), "por_exercicio": por_ano,
                        "financeiras": taxas(fin.em_alerta.to_numpy(bool), fin.estreita.to_numpy(bool)),
                        "financeiras_regra_larga": taxas(fin.em_alerta.to_numpy(bool), fin.larga.to_numpy(bool)),
                        "nao_avaliadas_por_situacao": {str(k): int(v) for k, v in rep[~rep.avaliada]
                                                       .situacao_seguinte.value_counts().sort_index().items()}},
    })  # fmt: skip


def main(argv: list[str] | None = None) -> int:
    from chiocca.v2.estudo2 import gabarito
    from chiocca.v2.estudo2 import lista as modulo_lista

    a = argparse.ArgumentParser(description="Avaliação secundária do estudo 2 (seção 7.2), única.")
    a.add_argument("--lista", type=Path, default=modulo_lista.LISTA)
    a.add_argument("--sha256", required=True, help="o SHA-256 da lista, gravado no commit do lacre")
    a.add_argument("--brutos", type=Path, default=base.BRUTOS)
    a.add_argument("--cache-enet", type=Path, default=base.CACHE_ENET)
    a.add_argument("--pendentes", type=Path, help="só grava as versões de t+1 que vêm do ENET e para")
    a.add_argument("--saida", type=Path, default=SAIDA)
    args = a.parse_args(argv)
    if date.today() < DATA_MINIMA:
        raise SystemExit(f"a avaliação secundária é única e só começa em {DATA_MINIMA.isoformat()} (seção 6)")
    if sys.version_info[:2] != modulo_lista.PYTHON:
        raise SystemExit("o estudo usa o Python 3.13 (seção 8)")
    conteudo = args.lista.read_bytes()
    if hashlib.sha256(conteudo).hexdigest() != args.sha256:
        raise SystemExit("a lista não tem o SHA-256 gravado no commit do lacre")
    fontes = Fontes(args.brutos, args.cache_enet)
    for parte in (1, 2):  # exigência 2: em cada avaliação, conferir acertavel_principal
        arquivo = base.RAIZ / "data" / f"gabarito_estudo_2_parte_{parte}.csv"
        if arquivo.exists():
            casos = gabarito.ler_parte(arquivo)
            print(gabarito.resumo_da_conferencia(casos, gabarito.conferir_acertavel(casos, fontes.indice_dfp)))
    rep = republicacoes(fontes, modulo_lista.ler(conteudo))
    if args.pendentes:
        p = pendentes_enet(rep)
        args.pendentes.write_text("".join(f"{x}\n" for x in p), encoding="utf-8")
        print(f"versões de t+1 a buscar no ENET: {len(p)}")
        return 0
    r = avaliar(rep) | {"lista_sha256": args.sha256}
    args.saida.write_text(json.dumps(r, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"{r['resultado']}; {r['motor_menos_regra_boba']['resultado']}; gravado em {args.saida}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
