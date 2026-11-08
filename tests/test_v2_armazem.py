"""Fase C1: armazém temporal, motor v1 em qualquer data e invariante, com fixtures sintéticas (sem rede, sem dados)."""

from __future__ import annotations

import hashlib
import json
from datetime import date
from pathlib import Path

import pandas as pd
import pytest

from chiocca import base, montar_base, sinais_amostra
from chiocca.cvm import Fontes
from chiocca.v2 import armazem, invariante, na_data
from chiocca.v2.lacre import DataForaDoIntervalo, ExercicioLacrado
from tests import fixtures_cvm as fx
from tests.test_base import mundo  # noqa: F401  (fixture)

D22 = "2022-12-31"


def _acrescenta_c1(fontes: Fontes) -> None:
    """Exercício de 2022 com reapresentação entregue depois da data máxima, e um exercício lacrado (2024)."""
    indice = [
        fx.doc("150", D22, 1, "2023-03-10", 15001),  # v2 depois de 31/12/2024, com a v1 no cache do ENET
        fx.doc("150", D22, 2, "2025-02-01", 15002),
        fx.doc("160", D22, 1, "2023-03-10", 16001),  # v2 depois de 31/12/2024, sem cache: pendente
        fx.doc("160", D22, 2, "2025-02-01", 16002),
        fx.doc("170", D22, 1, "2023-03-10", 17001),  # versão única, antes do corte
    ]
    dre = fx.dre("150", D22, 2, 700, 600) + fx.dre("160", D22, 2, 70, 60) + fx.dre("170", D22, 1, 40, 30)
    bpa = fx.bpa("150", D22, 2, 900) + fx.bpa("170", D22, 1, 0)  # 170: balanço não preenchido
    fx.escreve_dfp(fontes.pasta, 2022, indice, {"DRE_con": dre, "BPA_con": bpa})
    fx.escreve_cache_enet(fontes.cache_enet, 15001, [
        ("DRE", "ÚLTIMO", "3.01", "Receita de Venda de Bens e/ou Serviços", 650_000.0),
        ("BPA", "ÚLTIMO", "1", "Ativo Total", 880_000.0),
    ])  # fmt: skip
    fx.escreve_dfp(fontes.pasta, 2024, [fx.doc("100", "2024-12-31", 1, "2025-03-10", 1201)],
                   {"DRE_con": fx.dre("100", "2024-12-31", 1, 1500, 1200)})  # fmt: skip


@pytest.fixture
def mundo_c1(mundo: Fontes, tmp_path: Path) -> tuple[Fontes, armazem.FontesArmazem]:  # noqa: F811
    _acrescenta_c1(mundo)
    armazem.montar(mundo, tmp_path / "armazem", anos=range(2020, 2024))
    return mundo, armazem.FontesArmazem(tmp_path / "armazem")


def _leitura(f: object, cd: str, ano: int, corte: date | None, dt: str) -> base.Leitura:
    return base.como_era(f, cd, ano, corte=corte, dt_refer=dt)  # type: ignore[arg-type]


def test_armazem_reproduz_os_arquivos_brutos(mundo_c1: tuple[Fontes, armazem.FontesArmazem]) -> None:
    brutos, arm = mundo_c1
    for ano in (2020, 2021, 2022):
        assert brutos.indice_dfp(ano).reset_index(drop=True).equals(arm.indice_dfp(ano))
        f_brutos, f_arm = brutos.fca(ano).reset_index(drop=True), arm.fca(ano)
        assert f_arm.empty if f_brutos.empty else f_brutos.equals(f_arm)  # vazio: os tipos das colunas podem diferir
        pares = brutos.indice_dfp(ano)[["cd_cvm", "DT_REFER"]].drop_duplicates()
        for p in pares.itertuples(index=False):
            for corte in (None, date(2021, 8, 1), date(2023, 4, 30), date(2024, 12, 31)):
                a, b = _leitura(brutos, p.cd_cvm, ano, corte, p.DT_REFER), _leitura(
                    arm, p.cd_cvm, ano, corte, p.DT_REFER
                )
                for campo in ("status", "versao", "dt_receb", "ultima_versao", "tipo", "fonte", "num_doc"):
                    assert getattr(a, campo) == getattr(b, campo), (ano, p, corte, campo)
                assert a.contas.reset_index(drop=True).equals(b.contas.reset_index(drop=True))
    assert brutos.cadastro().equals(arm.cadastro())


def test_documento_entregue_depois_da_data_maxima_so_tem_metadados(
    mundo_c1: tuple[Fontes, armazem.FontesArmazem],
) -> None:
    _, arm = mundo_c1
    meta = arm.consulta("SELECT * FROM contas WHERE origem = ?", [armazem.SO_METADADOS])
    assert set(meta.cd_cvm) == {"150", "160"}
    assert meta.valor.isna().all() and meta.cd_conta.isna().all() and meta.ds_conta.isna().all()
    assert (
        arm.consulta("SELECT count(*) AS n FROM contas WHERE origem = 'dados_abertos' AND cd_cvm IN ('150', '160')").n[
            0
        ]
        == 0
    )
    # Os metadados da versão continuam no índice.
    assert set(arm.indice_dfp(2022).versao[arm.indice_dfp(2022).cd_cvm == "150"]) == {1, 2}
    # A v1 de 150 vem do ENET; a de 160 fica pendente, como nos arquivos brutos.
    assert _leitura(arm, "150", 2022, None, D22).fonte == "enet"
    assert _leitura(arm, "160", 2022, None, D22).status == base.PENDENTE_ENET


def test_lacre_no_armazem(mundo: Fontes, tmp_path: Path) -> None:  # noqa: F811
    _acrescenta_c1(mundo)
    m = armazem.montar(mundo, tmp_path / "a")
    assert 2024 not in m["exercicios"] and max(m["exercicios"]) <= 2023
    with pytest.raises(ExercicioLacrado):
        armazem.montar(mundo, tmp_path / "b", anos=range(2023, 2025))
    with pytest.raises(ExercicioLacrado):
        armazem.FontesArmazem(tmp_path / "a").indice_dfp(2024)


def test_manifesto_com_hash_dos_arquivos(mundo_c1: tuple[Fontes, armazem.FontesArmazem]) -> None:
    brutos, arm = mundo_c1
    hashes = arm.manifesto["arquivos_sha256"]
    for nome in ("dfp_cia_aberta_2020.zip", "dfp_cia_aberta_2022.zip", "cad_cia_aberta.csv"):
        assert hashes[nome] == hashlib.sha256((brutos.pasta / nome).read_bytes()).hexdigest()
    assert "dfp_cia_aberta_2024.zip" not in hashes


def test_versoes_na_data(mundo_c1: tuple[Fontes, armazem.FontesArmazem]) -> None:
    _, arm = mundo_c1
    v = arm.versoes_na_data(2020, date(2021, 4, 30)).set_index("cd_cvm")
    assert v.loc["100", "versao_na_data"] == 1 and v.loc["100", "versoes_conhecidas"] == 1
    v = arm.versoes_na_data(2020, date(2021, 12, 31)).set_index("cd_cvm")
    assert v.loc["100", "versao_na_data"] == 2 and v.loc["100", "versoes_conhecidas"] == 2
    assert "500" not in arm.versoes_na_data(2020, date(2021, 4, 30)).cd_cvm.values


def test_exercicio_na_data(mundo_c1: tuple[Fontes, armazem.FontesArmazem]) -> None:
    _, arm = mundo_c1
    e = na_data.exercicio_na_data(arm, "100", 2020, "2021-04-30")
    assert (e.situacao, e.versao_usada, e.origem) == ("ok", 1, "enet")
    assert e.versoes_conhecidas == ((1, date(2021, 3, 15)),)  # a v2 ainda não existia
    assert e.link and e.link.endswith("1001")
    e = na_data.exercicio_na_data(arm, "100", 2020, date(2021, 12, 31))
    assert (e.versao_usada, e.origem, len(e.versoes_conhecidas)) == (2, "dados_abertos", 2)
    assert na_data.exercicio_na_data(arm, "500", 2020, "2021-04-30").situacao == "sem_versao_ate_a_data"
    with pytest.raises(DataForaDoIntervalo):
        na_data.exercicio_na_data(arm, "100", 2020, "2025-01-01")
    with pytest.raises(ExercicioLacrado):
        na_data.exercicio_na_data(arm, "100", 2024, "2024-12-31")


def test_corte_transversal_igual_ao_caminho_do_estudo_1(
    mundo_c1: tuple[Fontes, armazem.FontesArmazem], tmp_path: Path
) -> None:
    brutos, arm = mundo_c1
    for ano in (2020,):  # 2022 da fixture não tem financeira, e o caminho do estudo precisa dos dois grupos
        meta = montar_base.monta(brutos, range(ano, ano + 1), saida=tmp_path / f"base{ano}")
        meta = pd.read_csv(tmp_path / f"base{ano}" / "empresa_ano.csv", dtype={"cd_cvm": str, "num_doc": str})
        estudo, _ = sinais_amostra.alertas(sinais_amostra.calcula(meta, tmp_path / f"base{ano}", range(ano, ano + 1)))
        novo, _ = na_data.corte_transversal(arm, ano)
        estudo = invariante._pelo_csv(estudo, list(estudo.columns))
        r = invariante.compara(novo, estudo)
        assert r["mesmas_empresa_anos"] and r["empresa_anos_iguais"] == r["empresa_anos_estudo"], r


def test_corte_transversal_numa_data_posterior(mundo_c1: tuple[Fontes, armazem.FontesArmazem]) -> None:
    _, arm = mundo_c1
    no_corte, _ = na_data.corte_transversal(arm, 2020)
    depois, _ = na_data.corte_transversal(arm, 2020, date(2021, 12, 31))
    a = no_corte.set_index("cd_cvm")
    b = depois.set_index("cd_cvm")
    assert str(a.loc["100", "dt_receb"]) == "2021-03-15" and str(b.loc["100", "dt_receb"]) == "2021-07-20"
    assert a.loc["500", "status"] == base.SEM_VERSAO_ATE_CORTE and b.loc["500", "status"] == base.OK
    contagem = invariante.na_data_maxima(no_corte, depois)
    assert contagem["outra_versao_na_data"] >= 1
    with pytest.raises(DataForaDoIntervalo):
        na_data.corte_transversal(arm, 2020, date(2011, 1, 1))


def test_camada_do_produto_nao_muda_o_motor(mundo_c1: tuple[Fontes, armazem.FontesArmazem]) -> None:
    _, arm = mundo_c1
    s, _ = na_data.corte_transversal(arm, 2022)
    linha = s.set_index("cd_cvm").loc["170"]
    nao = linha["produto_nao_calculaveis"].split(";")
    assert "lucro_sem_caixa" in nao and "SGI" not in nao  # SGI só usa a DRE
    contas = pd.DataFrame(
        [("BPA", "ÚLTIMO", "1", "Ativo Total", 10.0), ("BPA", "PENÚLTIMO", "1", "Ativo Total", 0.0)],
        columns=base.COLUNAS,
    )
    assert "juro" in na_data.nao_calculaveis_no_produto(contas, "nao_financeiro")
    estados = {base.OK, base.SEM_DOCUMENTO, base.SEM_VERSAO_ATE_CORTE, base.INDISPONIVEL_INDIVIDUAL,
               base.INDISPONIVEL_ENET, base.PENDENTE_ENET, base.CONTA_REPETIDA}  # fmt: skip
    assert set(na_data.SITUACAO) == estados


@pytest.mark.parametrize("lang", ["pt", "en"])
def test_documento_do_invariante_igual_a_saida_do_script(lang: str) -> None:
    n = json.loads(invariante.NUMEROS.read_text(encoding="utf-8"))
    assert invariante.DOCS[lang].read_text(encoding="utf-8") == invariante.render(n, lang)


def test_invariante_registrado_sem_diferenca() -> None:
    n = json.loads(invariante.NUMEROS.read_text(encoding="utf-8"))
    assert [int(a) for a in n["exercicios"]] == list(range(2010, 2024))
    for ano, v in n["exercicios"].items():
        assert v["mesmas_empresa_anos"] and v["empresa_anos_iguais"] == v["empresa_anos_estudo"] > 0, ano
        assert v["colunas_com_diferenca"] == {}, ano


@pytest.mark.skipif(
    not (armazem.PASTA / "manifesto.json").exists() or not invariante.SINAIS_ESTUDO_1.exists(),
    reason="precisa de data/armazem e de resultados/ (fora do git)",
)
def test_invariante_com_os_dados_de_2021() -> None:
    estudo = pd.read_csv(invariante.SINAIS_ESTUDO_1, dtype={"cd_cvm": str}, low_memory=False)
    novo, _ = na_data.corte_transversal(armazem.FontesArmazem(), 2021)
    r = invariante.compara(novo, estudo[estudo.exercicio == 2021])
    assert r["empresa_anos_iguais"] == r["empresa_anos_estudo"] > 0 and r["colunas_com_diferenca"] == {}
