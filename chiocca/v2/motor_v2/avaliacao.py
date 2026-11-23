"""Braço do motor v2 na avaliação secundária do estudo 2 (emenda 5 do estudo 2, itens 1, 3, 6 e 8).

Na mesma sessão da avaliação secundária do v1 (a partir de 31/05/2027, o v1 primeiro), sobre as duas listas lacradas,
conferidas pelo SHA-256 (o recálculo byte a byte é de cada script de lista, com `--conferir`). Só contagens agregadas
saem daqui; nenhum alerta do v2 por companhia é descrito (item 6).

- **Empresa-anos medidas (item 3):** só as que a seção 7.2 avalia para o v1, as não financeiras avaliadas da lista do
  v1 com a DFP de t+1 comparável (`secundaria.republicacoes`, sem mudança). O desfecho (a republicação estreita) é o
  mesmo nos dois braços. O alerta do v2 vem da lista do v2 inteira: o limite de 90% do escore foi calculado, na lista,
  entre todas as empresa-anos que o v2 avalia. As que só o v2 avalia ficam à parte, só como descrição.
- **Medidas:** as da seção 7.2, pelas funções congeladas de `chiocca/v2/estudo2/secundaria.py`, sem mudar nenhuma
  linha: a DR e a razão de taxas do v2, com o critério de "associação positiva"; a diferença pareada entre o v2 e a
  regra boba; a diferença pareada entre o v2 e o v1 ("o v2 separa melhor que o v1" só se o limite inferior do intervalo
  unilateral de 95% ficar acima de zero; senão, sem vencedor declarado); as métricas de ranking pela ordem do v2 (o
  escore, do maior para o menor, com o desempate da emenda 2, item 3(b): `escore.posicoes_no_ranking`). O bootstrap é
  `secundaria.bootstrap_por_companhia`, com a mesma semente e as mesmas reamostragens: com o mesmo conjunto de
  companhias, os sorteios são os do v1, e o v1 recalculado aqui tem de dar a mesma DR e o mesmo limite da avaliação do
  v1 (`docs/estudo_2_secundaria.json`).
- **Subconjunto prospectivo (item 8):** as empresa-anos de 2025 cuja primeira entrega da DFP de 2026 (o menor
  DT_RECEB da companhia no índice da CVM do exercício de 2026) é posterior ao commit com o SHA-256 da lista do v2. A
  data do commit é o dia no horário de Brasília (UTC-3), e "posterior" é estritamente depois desse dia. As mesmas
  medidas, com as mesmas funções e a mesma semente, sobre as companhias do subconjunto. As de 2024 são não
  prospectivas nos dois braços.
- **Rótulo "não prospectivo":** se o commit da lista do v2 é posterior a 31/01/2027 (vale a reserva do calendário), o
  braço inteiro leva também o rótulo.
- **Partes 2a e 2b (item 7):** ficam para o código da avaliação primária, escrito junto com o do v1 antes do
  congelamento da parte 2 (decisão de Roberto, 23/11/2026).

Uso, na sessão da avaliação secundária, depois da do v1:
  python -m chiocca.v2.motor_v2.avaliacao --lista-v1 <lista do v1> --sha256-v1 <SHA-256> \
      --lista-v2 <lista do v2> --sha256-v2 <SHA-256> --commit-lista-v2 <commit com o SHA-256 da lista do v2>
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from collections.abc import Callable
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from chiocca import base
from chiocca.cvm import Fontes
from chiocca.sinais_amostra import AMOSTRA_FIN, AMOSTRA_NF
from chiocca.v2.estudo2 import abertura as abertura_do_estudo
from chiocca.v2.estudo2 import lista as lista_v1
from chiocca.v2.estudo2 import secundaria
from chiocca.v2.motor_v2 import escore
from chiocca.v2.motor_v2 import lista as lista_v2

SAIDA = base.RAIZ / "docs" / "estudo_2_braco_v2.json"
CHAVE = ["exercicio", "cd_cvm", "dt_refer"]
EXERCICIO_PROSPECTIVO = 2025
DFP_SEGUINTE = 2026
DATA_META_DO_LACRE = date(2027, 1, 31)
BRASILIA = timezone(timedelta(hours=-3))  # sem horário de verão desde 2019
NAO_PROSPECTIVO = "não prospectivo"
BRACOS = ("v2", "v1", "boba")


def com_dt_refer(rep: pd.DataFrame, lista: pd.DataFrame) -> pd.DataFrame:
    """A data de referência em cada linha das republicações do v1: `secundaria.republicacoes` percorre, em ordem, as
    linhas da lista do v1 com o mesmo filtro usado aqui."""
    linhas = lista[lista.amostra.isin([AMOSTRA_NF, AMOSTRA_FIN]) & lista.avaliada.fillna(False)]
    if len(linhas) != len(rep) or not (
        (linhas.cd_cvm.astype(str).to_numpy() == rep.cd_cvm.astype(str).to_numpy()).all()
        and (linhas.exercicio.astype(int).to_numpy() == rep.exercicio.astype(int).to_numpy()).all()
    ):
        raise ValueError("as republicações não correspondem às linhas avaliadas da lista do v1")
    return rep.assign(dt_refer=linhas.dt_refer.astype(str).to_numpy())


def com_o_v2(rep: pd.DataFrame, lista: pd.DataFrame) -> pd.DataFrame:
    """O alerta, o escore e a avaliação do v2 de cada empresa-ano das republicações do v1, pela chave da empresa-ano."""
    v2 = lista[CHAVE + ["em_alerta", "escore", "avaliada"]].rename(
        columns={"em_alerta": "em_alerta_v2", "escore": "escore_v2", "avaliada": "avaliada_v2"}
    )
    v2 = v2.assign(exercicio=v2.exercicio.astype(int), cd_cvm=v2.cd_cvm.astype(str), dt_refer=v2.dt_refer.astype(str))
    r = rep.assign(exercicio=rep.exercicio.astype(int), cd_cvm=rep.cd_cvm.astype(str))
    juntos = r.merge(v2, on=CHAVE, how="left", validate="one_to_one", indicator=True)
    if (juntos._merge != "both").any():
        raise ValueError("empresa-ano da lista do v1 sem linha na lista do v2")
    juntos["em_alerta_v2"] = juntos.em_alerta_v2.astype("boolean").fillna(False).astype(bool)
    return juntos.drop(columns="_merge")


def _dr_nas_linhas(alerta: np.ndarray, y: np.ndarray) -> Callable[[np.ndarray], float]:
    return lambda i: secundaria.dr(alerta[i], y[i])


def medidas(nf: pd.DataFrame, reamostragens: int = secundaria.REAMOSTRAGENS, semente: int = secundaria.SEMENTE) -> dict:
    """As medidas da seção 7.2 para o v2, lado a lado com o v1 e a regra boba, num conjunto de não financeiras avaliadas
    (o bootstrap é um só, pareado entre os três)."""
    nf = nf.reset_index(drop=True)
    if nf.empty:
        return {"empresa_anos": 0, "companhias": 0}
    y = nf.estreita.to_numpy(bool)
    alerta = {"v2": nf.em_alerta_v2.to_numpy(bool), "v1": nf.em_alerta.to_numpy(bool),
              "boba": nf.alerta_regra_boba.to_numpy(bool)}  # fmt: skip
    posicao = {"v2": escore.posicoes_no_ranking(nf.rename(columns={"escore_v2": "escore"})),
               "v1": secundaria.ordem_do_motor(nf), "boba": secundaria.ordem_da_regra_boba(nf)}  # fmt: skip
    estat: dict[str, Callable[[np.ndarray], float]] = {
        "rr_v2": lambda i: float(secundaria.taxas(alerta["v2"][i], y[i])["rr"])
    }
    for braco in BRACOS:
        estat[f"dr_{braco}"] = _dr_nas_linhas(alerta[braco], y)
        for p in secundaria.TOPOS:
            for m in ("precisao", "lift", "ndcg"):
                estat[f"{m}_{p}_{braco}"] = secundaria._estatistica_de_ranking(posicao[braco], y, p, m)
    pontual = {nome: f(np.arange(len(nf))) for nome, f in estat.items()}
    b = secundaria.bootstrap_por_companhia(nf.cd_cvm.to_numpy(str), estat, reamostragens, semente)
    lim = secundaria.limite_inferior
    lim_v2, lim_boba, lim_v1 = lim(b["dr_v2"]), lim(b["dr_v2"] - b["dr_boba"]), lim(b["dr_v2"] - b["dr_v1"])
    rank: dict[str, Any] = {}
    for p in secundaria.TOPOS:
        chave = f"{round(p * 100)}%"
        rank[chave] = {"k": secundaria.topo(p, len(nf))}
        for m in ("precisao", "lift", "ndcg"):
            v2, v1, bo = f"{m}_{p}_v2", f"{m}_{p}_v1", f"{m}_{p}_boba"
            rank[chave][m] = {
                "v2": pontual[v2], "v2_limite_inferior_95": lim(b[v2]),
                "regra_boba": pontual[bo], "v1": pontual[v1],
                "v2_menos_regra_boba": pontual[v2] - pontual[bo],
                "v2_menos_regra_boba_limite_inferior_95": lim(b[v2] - b[bo]),
                "v2_menos_v1": pontual[v2] - pontual[v1], "v2_menos_v1_limite_inferior_95": lim(b[v2] - b[v1]),
            }  # fmt: skip
    por_ano = {str(a): secundaria.taxas(g.em_alerta_v2.to_numpy(bool), g.estreita.to_numpy(bool))
               for a, g in nf.groupby("exercicio")}  # fmt: skip
    return secundaria._num({
        "empresa_anos": len(nf), "companhias": int(nf.cd_cvm.nunique()), "reamostragens": reamostragens,
        "semente": semente, "reamostragens_sem_dr": int(np.isnan(b["dr_v2"]).sum()),
        "v2": secundaria.taxas(alerta["v2"], y) | {"dr_limite_inferior_95": lim_v2,
                                                   "rr_limite_inferior_95": lim(b["rr_v2"])},
        "resultado": "associação positiva" if lim_v2 is not None and lim_v2 > 0 else "sem evidência de associação",
        "regra_boba": secundaria.taxas(alerta["boba"], y) | {"dr_limite_inferior_95": lim(b["dr_boba"])},
        "v1": secundaria.taxas(alerta["v1"], y) | {"dr_limite_inferior_95": lim(b["dr_v1"])},
        "v2_menos_regra_boba": {
            "diferenca_dr": pontual["dr_v2"] - pontual["dr_boba"], "limite_inferior_95": lim_boba,
            "resultado": "o v2 separa melhor que a regra boba" if lim_boba is not None and lim_boba > 0
            else "sem vencedor declarado"},
        "v2_menos_v1": {
            "diferenca_dr": pontual["dr_v2"] - pontual["dr_v1"], "limite_inferior_95": lim_v1,
            "resultado": "o v2 separa melhor que o v1" if lim_v1 is not None and lim_v1 > 0
            else "sem vencedor declarado"},
        "ranking": rank,
        "por_exercicio": por_ano,
    })  # fmt: skip


def data_do_commit(commit: str) -> date:
    """O dia do commit (a data de quem fez o commit, no git) no horário de Brasília."""
    iso = subprocess.run(["git", "show", "-s", "--format=%cI", commit], cwd=base.RAIZ, capture_output=True, text=True,
                         check=True).stdout.strip()  # fmt: skip
    return datetime.fromisoformat(iso).astimezone(BRASILIA).date()


def primeira_entrega(fontes: Fontes, exercicio: int = DFP_SEGUINTE) -> dict[str, date]:
    """O menor DT_RECEB de cada companhia no índice da DFP do exercício (só depois da segunda abertura do estudo)."""
    abertura_do_estudo.garantir_seguinte(exercicio)
    idx = fontes.indice_dfp(exercicio)
    return {str(c): d for c, d in idx.groupby("cd_cvm").dt_receb.min().items()}


def prospectiva(rep: pd.DataFrame, entregas: dict[str, date], commit: date) -> np.ndarray:
    """Empresa-anos de 2025 com a primeira entrega da DFP de 2026 estritamente depois do dia do commit."""
    return np.array([int(a) == EXERCICIO_PROSPECTIVO and c in entregas and entregas[c] > commit
                     for a, c in zip(rep.exercicio, rep.cd_cvm.astype(str))], dtype=bool)  # fmt: skip


def rotulos(commit: date) -> list[str]:
    return [NAO_PROSPECTIVO] if commit > DATA_META_DO_LACRE else []


def linhas_so_do_v2(lista_1: pd.DataFrame, lista_2: pd.DataFrame) -> pd.DataFrame:
    """As empresa-anos dos dois grupos que só o v2 avalia, com as colunas que `secundaria.republicacoes` lê (o número
    de sinais do v1 não existe nelas e fica 0; só a descrição as usa)."""
    v1 = set(zip(*(lista_1.loc[lista_1.avaliada.fillna(False), c].astype(str) for c in CHAVE)))
    grupos = lista_2.amostra.isin([AMOSTRA_NF, AMOSTRA_FIN]) & lista_2.avaliada.fillna(False)
    so = lista_2[grupos & np.array([k not in v1 for k in zip(*(lista_2[c].astype(str) for c in CHAVE))], dtype=bool)]
    return so.assign(n_sinais=0)


def descricao_so_do_v2(rep: pd.DataFrame) -> dict[str, Any]:
    """Só descrição: as empresa-anos que só o v2 avalia, com o alerta do v2 e a republicação estreita."""
    nf = rep[(rep.amostra == AMOSTRA_NF) & rep.avaliada] if not rep.empty else rep
    if nf.empty:
        return {"empresa_anos": 0}
    return secundaria._num(secundaria.taxas(nf.em_alerta.to_numpy(bool), nf.estreita.to_numpy(bool))
                           | {"empresa_anos": len(nf)})  # fmt: skip


def avaliar_braco(
    rep_v1: pd.DataFrame,
    lista_1: pd.DataFrame,
    lista_2: pd.DataFrame,
    entregas: dict[str, date],
    commit: date,
    rep_so_v2: pd.DataFrame | None = None,
    reamostragens: int = secundaria.REAMOSTRAGENS,
    semente: int = secundaria.SEMENTE,
) -> dict[str, Any]:
    """O braço do v2: o total e o subconjunto prospectivo, só nas empresa-anos que a seção 7.2 avalia para o v1."""
    rep = com_o_v2(com_dt_refer(rep_v1, lista_1), lista_2)
    nf = rep[(rep.amostra == AMOSTRA_NF) & rep.avaliada.astype(bool)].reset_index(drop=True)
    pro = prospectiva(nf, entregas, commit)
    fin = rep[(rep.amostra == AMOSTRA_FIN) & rep.avaliada.astype(bool)]
    return secundaria._num({
        "rotulos": rotulos(commit), "data_do_commit_da_lista_v2": commit.isoformat(),
        "total": medidas(nf, reamostragens, semente),
        "prospectivo": {"empresa_anos_de_2025": int((nf.exercicio == EXERCICIO_PROSPECTIVO).sum())}
        | medidas(nf[pro], reamostragens, semente),
        "descritivos": {
            "financeiras": secundaria.taxas(fin.em_alerta_v2.to_numpy(bool), fin.estreita.to_numpy(bool)),
            "regra_larga": secundaria.taxas(nf.em_alerta_v2.to_numpy(bool), nf.larga.to_numpy(bool)),
            "so_o_v2_avalia": descricao_so_do_v2(rep_so_v2) if rep_so_v2 is not None else None,
        },
    })  # fmt: skip


def main(argv: list[str] | None = None) -> int:
    a = argparse.ArgumentParser(description="Braço do motor v2 na avaliação secundária do estudo 2 (emenda 5).")
    a.add_argument("--lista-v1", type=Path, default=lista_v1.LISTA)
    a.add_argument("--sha256-v1", required=True)
    a.add_argument("--lista-v2", type=Path, default=lista_v2.LISTA)
    a.add_argument("--sha256-v2", required=True)
    a.add_argument("--commit-lista-v2", required=True, help="o commit com o SHA-256 da lista do v2")
    a.add_argument("--brutos", type=Path, default=base.BRUTOS)
    a.add_argument("--cache-enet", type=Path, default=base.CACHE_ENET)
    a.add_argument("--saida", type=Path, default=SAIDA)
    args = a.parse_args(argv)
    if date.today() < secundaria.DATA_MINIMA:
        raise SystemExit(f"a avaliação secundária só começa em {secundaria.DATA_MINIMA.isoformat()}")
    if sys.version_info[:2] != lista_v1.PYTHON:
        raise SystemExit("o estudo usa o Python 3.13 (seção 8)")
    v1_feito = json.loads(secundaria.SAIDA.read_text(encoding="utf-8")) if secundaria.SAIDA.exists() else {}
    if v1_feito.get("lista_sha256") != args.sha256_v1:
        raise SystemExit("a avaliação do v1 vem primeiro, na mesma sessão (emenda 5, calendário)")
    conteudos = {}
    for nome, caminho, sha in (("v1", args.lista_v1, args.sha256_v1), ("v2", args.lista_v2, args.sha256_v2)):
        conteudos[nome] = caminho.read_bytes()
        if hashlib.sha256(conteudos[nome]).hexdigest() != sha:
            raise SystemExit(f"a lista do {nome} não tem o SHA-256 gravado no commit do lacre")
    lista_1, lista_2 = lista_v1.ler(conteudos["v1"]), lista_v2.ler(conteudos["v2"])
    fontes = Fontes(args.brutos, args.cache_enet)
    rep_v1 = secundaria.republicacoes(fontes, lista_1)
    rep_so_v2 = secundaria.republicacoes(fontes, linhas_so_do_v2(lista_1, lista_2))
    if secundaria.pendentes_enet(rep_v1) or secundaria.pendentes_enet(rep_so_v2):
        raise SystemExit("há versões de t+1 pendentes do ENET: busque-as antes (secundaria --pendentes)")
    r = avaliar_braco(rep_v1, lista_1, lista_2, primeira_entrega(fontes), data_do_commit(args.commit_lista_v2),
                      rep_so_v2)  # fmt: skip
    v1 = r["total"]["v1"]
    feito = v1_feito["motor"]
    r["v1_igual_a_avaliacao_do_v1"] = (
        v1["dr"] == feito["dr"] and v1["dr_limite_inferior_95"] == feito["dr_limite_inferior_95"]
    )
    r |= {"lista_v1_sha256": args.sha256_v1, "lista_v2_sha256": args.sha256_v2}
    args.saida.write_text(json.dumps(r, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"{r['total']['resultado']}; {r['total']['v2_menos_v1']['resultado']}; gravado em {args.saida}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
