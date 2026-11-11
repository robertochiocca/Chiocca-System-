"""Contrato entre a API e a interface (Fase E): as respostas da API sobre o armazém da fixture, sem rede, ficam em
web/tests/contrato/ e um teste do web (node --test) as confere com as mesmas funções que a interface usa
(web/lib/contrato.mjs). Aqui, o lado do Python: as respostas guardadas têm de ser iguais às da API de agora.

Para regerar depois de mudar o contrato: CHIOCCA_REGERAR_CONTRATO_WEB=1 python -m pytest tests/test_v2_contrato_web.py
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient

from chiocca.cvm import Fontes
from chiocca.v2 import api, armazem, demonstracao
from tests.test_base import mundo  # noqa: F401  (fixture)
from tests.test_v2_api import sem_rede  # noqa: F401  (fixture)
from tests.test_v2_armazem import mundo_c1  # noqa: F401  (fixture)
from tests.test_v2_demonstracao_estatica import _gabarito_da_fixture

PASTA = Path(__file__).resolve().parents[1] / "web" / "tests" / "contrato"
D = "2022-04-30"
ROTAS = {
    "saude": "/api/v1/saude",
    "busca": f"/api/v1/empresas?busca=empresa&data_referencia={D}",
    "empresa": f"/api/v1/empresas/100?data_referencia={D}",
    "investigacao": f"/api/v1/investigacoes/100/2020?data_referencia={D}&idioma=pt",
    "como_testado": "/api/v1/como-o-motor-foi-testado",
    "demonstracao": "/api/v1/demonstracao",
    "erro_lacre": f"/api/v1/investigacoes/100/2024?data_referencia={D}",
    "erro_data": "/api/v1/investigacoes/100/2020?data_referencia=2025-01-01",
}


def _sem_carimbos(x: Any) -> Any:
    if isinstance(x, dict):
        return {k: ("2026-11-09T00:00:00+00:00" if k in ("gerado_em", "calculado_em") else _sem_carimbos(v))
                for k, v in x.items()}  # fmt: skip
    if isinstance(x, list):
        return [_sem_carimbos(v) for v in x]
    return x


def test_respostas_da_api_guardadas_para_o_contrato_do_web(
    mundo_c1: tuple[Fontes, armazem.FontesArmazem], sem_rede: None, monkeypatch: pytest.MonkeyPatch  # noqa: F811
) -> None:
    _, arm = mundo_c1
    # a rota da demonstração com a companhia da fixture e um caso de exemplo no lugar do gabarito real
    monkeypatch.setattr(api, "empresas_da_demonstracao", lambda: {"100"})
    monkeypatch.setattr(demonstracao, "gabarito", _gabarito_da_fixture)
    regerar = os.environ.get("CHIOCCA_REGERAR_CONTRATO_WEB") == "1"
    with TestClient(api.criar_app(lambda: arm, modo_demonstracao=False)) as c:
        for nome, rota in ROTAS.items():
            r = c.get(rota)
            corpo = _sem_carimbos(r.json())
            if nome == "saude":
                corpo["armazem"] = {"exercicios": corpo["armazem"]["exercicios"]}  # as contagens dependem da fixture
            caminho = PASTA / f"{nome}.json"
            if regerar:
                PASTA.mkdir(parents=True, exist_ok=True)
                caminho.write_text(json.dumps(corpo, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
            assert json.loads(caminho.read_text(encoding="utf-8")) == corpo, nome
            assert r.status_code == (422 if nome.startswith("erro") else 200), nome
