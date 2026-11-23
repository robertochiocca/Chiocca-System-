"""Invariante do motor v2 (pré-registro do motor v2, seção 6; pedido de 23/11/2026, item 3).

Com as três mudanças desligadas (o DEPI só pela DFC, sem o Benford e com as regras de alerta do v1), o v2 reproduz o v1
nas 9.474 empresa-anos do estudo 1. Para cada exercício de 2010 a 2023, a lista do v2 (`chiocca.v2.motor_v2.lista`,
com `motor.NENHUMA`) roda sobre o armazém (`FontesArmazem`), cada empresa na data de corte do seu exercício, como o
invariante do v1 (`chiocca.v2.invariante`), e é comparada coluna por coluna com `resultados/sinais_empresa_ano.csv`
pela mesma função do invariante do v1 (`chiocca.v2.invariante.compara`: os dois lados passam pelo mesmo CSV, e a
comparação é exata). Só contagens; nenhuma empresa é citada.

É uma conferência do código do v2, fora do pacote dele: o pacote não importa este módulo.

Grava docs/motor_v2_invariante.json (versionado).
Uso: python -m chiocca.v2.motor_v2_invariante   (precisa de data/armazem e de resultados/sinais_empresa_ano.csv)
"""

from __future__ import annotations

import json
import subprocess
from datetime import datetime, timezone
from typing import Any, cast

import pandas as pd

from chiocca.base import RAIZ
from chiocca.cvm import Fontes
from chiocca.v2.armazem import PRIMEIRO_EXERCICIO, FontesArmazem
from chiocca.v2.invariante import SINAIS_ESTUDO_1, compara
from chiocca.v2.lacre import ULTIMO_EXERCICIO_LIBERADO, so_liberados
from chiocca.v2.motor_v2 import lista, motor

SAIDA = RAIZ / "docs" / "motor_v2_invariante.json"
ANOS = range(PRIMEIRO_EXERCICIO, ULTIMO_EXERCICIO_LIBERADO + 1)


def _git(*args: str) -> str:
    return subprocess.run(["git", *args], cwd=RAIZ, capture_output=True, text=True, check=True).stdout.strip()


def calcula(fontes: FontesArmazem, estudo: pd.DataFrame, anos: range = ANOS) -> dict[str, Any]:
    out: dict[str, Any] = {"exercicios": {}}
    for ano in anos:
        v2 = lista.calcular(cast(Fontes, fontes), [ano], motor.NENHUMA)  # o armazém tem a interface das fontes
        r = compara(v2, estudo[estudo.exercicio == ano])
        out["exercicios"][str(ano)] = r
        print(ano, r["empresa_anos_estudo"], r["empresa_anos_iguais"], flush=True)
    ex = out["exercicios"].values()
    out["total"] = {
        "empresa_anos_estudo": sum(r["empresa_anos_estudo"] for r in ex),
        "empresa_anos_v2": sum(r["empresa_anos_v2"] for r in ex),
        "empresa_anos_iguais": sum(r["empresa_anos_iguais"] for r in ex),
        "exercicios_com_as_mesmas_empresa_anos": sum(bool(r["mesmas_empresa_anos"]) for r in ex),
        "colunas_comparadas": sorted({r.get("colunas_comparadas", 0) for r in ex}),
        "colunas_com_diferenca": sorted({c for r in ex for c in r["colunas_com_diferenca"]}),
    }
    return out


def main() -> None:
    inicio = datetime.now(timezone.utc).isoformat(timespec="seconds")
    estudo = so_liberados(pd.read_csv(SINAIS_ESTUDO_1, dtype={"cd_cvm": str}, low_memory=False))
    out = {
        "o_que_e": (
            "invariante do motor v2 (pré-registro do motor v2, seção 6): com as três mudanças desligadas, a lista do "
            "v2 sobre o armazém, comparada coluna por coluna com resultados/sinais_empresa_ano.csv (só contagens)"
        ),
        "mudancas": {"depi_dva": motor.NENHUMA.depi_dva, "benford": motor.NENHUMA.benford,
                     "escore": motor.NENHUMA.escore},  # fmt: skip
        "commit": _git("rev-parse", "HEAD"),
        "codigo_sem_alteracao_local": _git("status", "--porcelain", "--untracked-files=no", "--", "chiocca") == "",
        **calcula(FontesArmazem(), estudo),
        "inicio_utc": inicio,
        "fim_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }
    SAIDA.write_text(json.dumps(out, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    t = out["total"]
    print(f"{t['empresa_anos_iguais']} de {t['empresa_anos_estudo']} empresa-anos iguais; gravado em {SAIDA}")


if __name__ == "__main__":
    main()
