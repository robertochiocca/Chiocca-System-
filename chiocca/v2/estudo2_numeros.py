"""Números do rascunho do plano do estudo 2 (docs/estudo-2-plano.md e docs/en/study-2-plan.md), sem nenhum valor de
conta de exercício de 2024 em diante.

    python -m chiocca.v2.estudo2_numeros   # grava docs/estudo_2_numeros.json (precisa de rede e do armazém)

- Entregas de DFP de 2023, 2024 e 2025: só os metadados do índice de cada arquivo da CVM (companhia, versão e data de
  entrega), lidos de dentro do zip remoto por faixas de bytes, como no monitor (chiocca.v2.monitor.indice_atual); as
  demonstrações não são baixadas. Nada do índice é guardado além das contagens.
- Atraso entre o fim do período afetado e a data pública, nos casos do gabarito do estudo 1 (data/gabarito_casos.csv).
- Poder: quantos acertos distinguem do acaso, com a taxa de alerta de cerca de 50% do estudo 1, e quantos casos
  acertáveis esperar em cada data de avaliação possível, para três taxas de casos por exercício.
- Republicações relevantes no comparativo da DFP seguinte, pela regra de materialidade do produto
  (chiocca.v2.comparativo), nos exercícios de 2010 a 2022 (comparativo até a DFP de 2023, dentro do lacre), separadas
  pelas linhas que mudam.
"""

from __future__ import annotations

import collections
import csv
import json
import sys
from datetime import date
from math import comb
from pathlib import Path
from typing import Any

from chiocca import base

DESTINO = base.RAIZ / "docs" / "estudo_2_numeros.json"
GABARITO = base.RAIZ / "data" / "gabarito_casos.csv"
TAXA_DE_ALERTA = 0.5  # cerca de 49,9% das empresa-anos não financeiras avaliadas no estudo 1 (docs/resumo.md)
ALFA = 0.05
DATAS_DE_AVALIACAO = ("2027-12-31", "2028-12-31", "2029-12-31", "2030-12-31")
HOJE = "2026-11-15"  # data do rascunho
TAXAS_DE_CASOS = {"baixa": 0.25, "media": 0.93, "alta": 2.2}
MESES = 30.4375


def _meses(a: date, b: date) -> float:
    return (b - a).days / MESES


def atrasos(gabarito: Path = GABARITO) -> dict[str, Any]:
    """Meses entre 31/12 do último ano do período afetado e a data pública, nos casos com os dois campos."""
    todos, acertaveis = [], []
    por_ano: collections.Counter[int] = collections.Counter()
    for r in csv.DictReader(gabarito.open(encoding="utf-8")):
        if not (r["data_publica"] and r["periodo_afetado_fim"]):
            continue
        fim = int(r["periodo_afetado_fim"])
        m = _meses(date(fim, 12, 31), date.fromisoformat(r["data_publica"]))
        todos.append(m)
        if r["acertavel_principal"] == "sim":
            acertaveis.append(m)
            por_ano[fim] += 1

    def resumo(xs: list[float]) -> dict[str, Any]:
        s = sorted(xs)
        mediana = (s[len(s) // 2] if len(s) % 2 else (s[len(s) // 2 - 1] + s[len(s) // 2]) / 2) if s else None
        fracao = {str(L): round(sum(x <= L for x in s) / len(s), 2) for L in (12, 24, 36, 48, 60, 72)}
        return {"casos": len(s), "mediana": round(mediana, 1) if mediana is not None else None,
                "minimo": round(s[0], 1), "maximo": round(s[-1], 1), "fracao_ate": fracao}  # fmt: skip

    anos = sorted(por_ano)
    return {"todos": resumo(todos), "acertaveis": resumo(acertaveis),
            "acertaveis_por_ano_final": {str(a): por_ano[a] for a in anos},
            "taxa_acertaveis_2011_2015": round(sum(por_ano[a] for a in range(2011, 2016)) / 5, 2),
            "taxa_acertaveis_2016_2023": round(sum(por_ano[a] for a in range(2016, 2024)) / 8, 2),
            "taxa_acertaveis_2010_2023": round(sum(por_ano.values()) / 14, 2)}  # fmt: skip


def _cauda(k: int, x: int, p: float) -> float:
    return sum(comb(k, i) * p**i * (1 - p) ** (k - i) for i in range(x, k + 1))


def limiares(p: float = TAXA_DE_ALERTA, alfa: float = ALFA) -> list[dict[str, Any]]:
    """Para k casos acertáveis, o menor número de acertos com chance de ocorrer ao acaso de no máximo alfa (cada caso
    acertado ao acaso com probabilidade p, independentes), e o poder se a taxa real de acerto fosse 0,75 ou 0,9."""
    out = []
    for k in [*range(1, 16), 20, 25, 30]:
        x = next((x for x in range(k + 1) if _cauda(k, x, p) <= alfa), None)
        chance = round(_cauda(k, x if x is not None else k, p), 4)
        out.append({"casos": k, "acertos_minimos": x, "chance_ao_acaso": chance,
                    "poder_075": round(_cauda(k, x, 0.75), 3) if x is not None else 0.0,
                    "poder_090": round(_cauda(k, x, 0.9), 3) if x is not None else 0.0})  # fmt: skip
    return out


def esperados(gabarito: Path = GABARITO) -> dict[str, Any]:
    """Casos acertáveis esperados dos exercícios de 2024 e 2025 até cada data: taxa por exercício vezes a fração dos
    casos do estudo 1 que viraram públicos até aquele atraso (todos os 36 casos com período e data)."""
    xs = []
    for r in csv.DictReader(gabarito.open(encoding="utf-8")):
        if r["data_publica"] and r["periodo_afetado_fim"]:
            xs.append(_meses(date(int(r["periodo_afetado_fim"]), 12, 31), date.fromisoformat(r["data_publica"])))
    out = {}
    for d in (HOJE, *DATAS_DE_AVALIACAO):
        alvo = date.fromisoformat(d)
        f = [sum(x <= _meses(date(ano, 12, 31), alvo) for x in xs) / len(xs) for ano in (2024, 2025)]
        out[d] = {"fracao_2024": round(f[0], 2), "fracao_2025": round(f[1], 2),
                  **{nome: round(t * sum(f), 1) for nome, t in TAXAS_DE_CASOS.items()}}  # fmt: skip
    return {"taxas_de_casos_por_exercicio": TAXAS_DE_CASOS, "por_data": out}


def persistencia() -> dict[str, float]:
    """Chance, ao acaso, de pelo menos um alerta num caso com os dois exercícios (2024 e 2025) no período afetado."""
    return {"independentes": round(1 - (1 - TAXA_DE_ALERTA) ** 2, 3),
            "com_persistencia_do_estudo_1": round(1 - (1 - TAXA_DE_ALERTA) * (1 - 0.738), 3)}  # fmt: skip


def entregas_dfp(anos: tuple[int, ...] = (2023, 2024, 2025)) -> dict[str, Any]:
    """Só metadados do índice da DFP de cada ano (sem baixar as demonstrações): companhias, primeira entrega até o corte
    (30/04 do ano seguinte) e companhias com mais de uma versão. Nada do índice é guardado."""
    from chiocca.v2 import monitor

    out = {}
    for ano in anos:
        por_cia: dict[str, list[dict[str, str]]] = collections.defaultdict(list)
        for r in monitor._linhas(monitor.indice_atual("DFP", ano)):
            if r.get("CATEG_DOC") == "DFP" and r["DT_REFER"].startswith(str(ano)):
                por_cia[r["CD_CVM"].strip().lstrip("0")].append(r)
        primeira = [min(x["DT_RECEB"] for x in rs) for rs in por_cia.values()]
        reentregas = sum(len({x["VERSAO"] for x in rs}) > 1 for rs in por_cia.values())
        out[str(ano)] = {"companhias": len(por_cia), "ate_o_corte": sum(d <= f"{ano + 1}-04-30" for d in primeira),
                         "com_mais_de_uma_versao": reentregas}  # fmt: skip
    return out


def republicacoes(anos: range = range(2010, 2023)) -> dict[str, Any]:
    """Empresa-anos com diferença destacada no comparativo da DFP seguinte (regra do produto: grupo (a) acima de 1% do
    ativo total), na data máxima de 31/12/2024, separadas pelas linhas destacadas."""
    from chiocca.v2 import comparativo
    from chiocca.v2.invariante import FontesArmazem
    from chiocca.v2.lacre import DATA_REFERENCIA_MAXIMA, ULTIMO_EXERCICIO_LIBERADO

    fontes: Any = FontesArmazem()  # a mesma interface das Fontes (como em chiocca.v2.comparativo.contagem)
    out = {}
    for ano in anos:
        if ano + 1 > ULTIMO_EXERCICIO_LIBERADO:
            raise ValueError("o comparativo seguinte passaria do lacre")
        c = {"comparadas": 0, "destacada": 0, "pl_ou_lucro": 0, "so_circulante_nao_circulante": 0}
        for p in fontes.indice_dfp(ano)[["cd_cvm", "DT_REFER"]].drop_duplicates().itertuples(index=False):
            lt = base.como_era(fontes, p.cd_cvm, ano, corte=DATA_REFERENCIA_MAXIMA, dt_refer=p.DT_REFER)
            seg = None
            if lt.status == base.OK:
                seg = comparativo.leitura_seguinte(fontes, p.cd_cvm, ano, DATA_REFERENCIA_MAXIMA)
            if seg is None or seg.status != base.OK or seg.tipo != lt.tipo:
                continue
            c["comparadas"] += 1
            dest = {d.cd_conta for d in comparativo.comparar(lt, seg) if d.destacada}
            if dest:
                c["destacada"] += 1
                c["pl_ou_lucro"] += bool(dest & {"2.03", "3.11"})
                c["so_circulante_nao_circulante"] += dest <= {"2.01", "2.02"}
        out[str(ano)] = c
        print(ano, c, flush=True)
    tot = {k: sum(v[k] for v in out.values()) for k in next(iter(out.values()))}
    return {"regra": "grupo (a) acima de 1% do ativo total (chiocca.v2.comparativo)", "por_exercicio": out,
            "total": tot}  # fmt: skip


def _phi(z: float) -> float:
    from math import erf, sqrt

    return 0.5 * (1 + erf(z / sqrt(2)))


def poder_secundario(taxa: float, n: int = 1200, rr: tuple[float, ...] = (1.5, 2.0)) -> dict[str, Any]:
    """Poder aproximado (teste de duas proporções, unilateral, alfa de 5%) para uma razão de taxas de republicação entre
    empresa-anos em alerta e fora de alerta, com metade em alerta e n empresa-anos ao todo; supõe empresa-anos
    independentes (com dois exercícios por companhia, o n efetivo é menor)."""
    from math import sqrt

    metade = n / 2
    out = {}
    for r in rr:
        p0 = 2 * taxa / (1 + r)  # taxa fora de alerta, para a média ficar igual a `taxa`
        p1 = r * p0
        pm = (p0 + p1) / 2
        z = (p1 - p0 - 1.6449 * sqrt(2 * pm * (1 - pm) / metade)) / sqrt((p0 * (1 - p0) + p1 * (1 - p1)) / metade)
        out[str(r)] = {"taxa_fora_de_alerta": round(p0, 3), "taxa_em_alerta": round(p1, 3), "poder": round(_phi(z), 2)}
    return {"empresa_anos": n, "taxa_media": round(taxa, 3), "por_razao": out}


def derivados(r: dict[str, Any]) -> dict[str, Any]:
    """Poder do desfecho secundário pelas duas definições de republicação, com a taxa de 2013 a 2022 do JSON."""
    anos = [str(a) for a in range(2013, 2023)]
    pe = r["republicacoes"]["por_exercicio"]
    comparadas = sum(pe[a]["comparadas"] for a in anos)
    taxas = {"destacada": sum(pe[a]["destacada"] for a in anos) / comparadas,
             "pl_ou_lucro": sum(pe[a]["pl_ou_lucro"] for a in anos) / comparadas}  # fmt: skip
    return {"taxas_2013_2022": {k: round(v, 3) for k, v in taxas.items()},
            "poder_secundario": {k: poder_secundario(v) for k, v in taxas.items()}}  # fmt: skip


def calcula() -> dict[str, Any]:
    return {"gerado_por": "python -m chiocca.v2.estudo2_numeros", "data": HOJE,
            "o_que_e": "números do rascunho do plano do estudo 2, sem nenhum valor de conta de exercício de 2024 em "
            "diante",
            "taxa_de_alerta": TAXA_DE_ALERTA, "alfa": ALFA, "entregas_dfp": entregas_dfp(), "atrasos": atrasos(),
            "limiares": limiares(), "persistencia": persistencia(), "esperados": esperados(),
            "republicacoes": republicacoes()}  # fmt: skip


def main(argv: list[str]) -> None:
    if argv[:1] == ["--derivados"]:  # refaz só as contas derivadas, a partir do JSON gravado (sem rede nem armazém)
        r = json.loads(DESTINO.read_text(encoding="utf-8"))
    else:
        r = calcula()
    r["derivados"] = derivados(r)
    DESTINO.write_text(json.dumps(r, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in r.items() if k not in ("limiares",)}, ensure_ascii=False, indent=1)[:4000])


if __name__ == "__main__":
    main(sys.argv[1:])
