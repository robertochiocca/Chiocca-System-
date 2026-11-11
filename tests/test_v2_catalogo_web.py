"""Textos do catálogo para a interface (Fase E2): web/lib/catalogo.json em dia com catalogo_sinais.yaml, PT e EN."""

from __future__ import annotations

import json

from chiocca.v2 import catalogo_web, contexto


def test_catalogo_da_interface_em_dia() -> None:
    assert catalogo_web.DESTINO.read_text(encoding="utf-8") == catalogo_web.texto()


def test_textos_nas_duas_linguas_e_componentes_completos() -> None:
    dados = json.loads(catalogo_web.texto())
    for sinal, textos in dados["sinais"].items():
        for lang in ("pt", "en"):
            assert all(textos[lang][k].strip() for k in ("nome", "o_que_mede", "por_que")), (sinal, lang)
    assert set(dados["componentes"]) == {"DSRI", "GMI", "AQI", "SGI", "DEPI", "SGAI", "LVGI", "TATA", *contexto.COEF_Z2}
    texto = json.dumps(dados, ensure_ascii=False).lower()
    assert "fraude" not in texto and "fraud" not in texto  # alerta, não acusação
