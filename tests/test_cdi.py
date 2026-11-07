"""CDI médio do exercício a partir do snapshot (sem rede)."""

from __future__ import annotations

from pathlib import Path

import pytest

from chiocca import cdi


def test_media_dos_doze_meses(tmp_path: Path) -> None:
    arq = tmp_path / "cdi.csv"
    arq.write_text(
        "data,valor\n2019-06-28,99.0\n2019-07-01,8.0\n2020-01-02,10.0\n2020-06-30,12.0\n2020-12-31,14.0\n2021-01-04,99.0\n"
    )
    cdi.serie.cache_clear()
    assert cdi.medio("2020-12-31", arq) == pytest.approx(0.12)
    assert cdi.medio("2020-06-30", arq) == pytest.approx(0.10)  # exercício que fecha em junho: jul/2019 a jun/2020
    cdi.serie.cache_clear()


def test_snapshot_versionado_cobre_o_periodo() -> None:
    cdi.serie.cache_clear()
    s = cdi.serie()
    assert str(s.data.min()) <= "2009-01-05" and str(s.data.max()) >= "2025-12-30"
    assert cdi.medio("2023-12-31") is not None
