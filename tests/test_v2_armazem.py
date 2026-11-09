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
from chiocca.v2 import armazem, buscar_enet, comparativo, invariante, na_data
from chiocca.v2.lacre import DataForaDoIntervalo, ExercicioLacrado
from chiocca.v2.linhagem import Localizador, id_evidencia
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


# ---- Fase C2: escala original, evidências, nota de estrutura posterior e busca no ENET ----


def test_escala_original(mundo_c1: tuple[Fontes, armazem.FontesArmazem]) -> None:
    _, arm = mundo_c1
    e = na_data.exercicio_na_data(arm, "100", 2020, "2021-12-31")
    assert (e.origem, e.escala_original) == ("dados_abertos", "MIL")
    e = na_data.exercicio_na_data(arm, "100", 2020, "2021-04-30")
    assert e.origem == "enet" and e.escala_original is None and na_data.SEM_ESCALA_ENET in e.notas
    assert arm.escala(2020, "100", "2020-12-31", 99, "con") is None


def test_nota_de_estrutura_de_documento_posterior(mundo_c1: tuple[Fontes, armazem.FontesArmazem]) -> None:
    _, arm = mundo_c1
    e = na_data.exercicio_na_data(arm, "100", 2020, "2021-04-30")  # v1 do ENET; a v2 é de 20/07/2021
    assert na_data.NOTA_ESTRUTURA_POSTERIOR in e.notas
    assert e.documento is not None and na_data.NOTA_ESTRUTURA_POSTERIOR in e.documento.notas
    assert (
        na_data.NOTA_ESTRUTURA_POSTERIOR.pt
        == "estrutura lida de documento posterior à data (comportamento do estudo 1, emenda 8)"
    )
    assert na_data.NOTA_ESTRUTURA_POSTERIOR not in na_data.exercicio_na_data(arm, "100", 2020, "2021-12-31").notas
    s, _ = na_data.corte_transversal(arm, 2020)
    marcadas = set(s.loc[s.estrutura_de_documento_posterior.astype(bool), "cd_cvm"])
    assert "100" in marcadas and "300" not in marcadas


def test_evidencias_do_contrato(mundo_c1: tuple[Fontes, armazem.FontesArmazem]) -> None:
    brutos, arm = mundo_c1
    loc = Localizador(brutos.pasta, arm.cache_enet)
    e = na_data.exercicio_na_data(arm, "100", 2020, "2021-12-31", localizador=loc)
    chaves = e.contas[["demonstracao", "ordem", "cd_conta"]].drop_duplicates()
    assert len(e.evidencias) == len(chaves) > 0
    ev = e.evidencias[0]
    assert ev.documento.versao == 2 and ev.documento.origem == "dados_abertos" and ev.documento.dt_receb == "2021-07-20"
    assert ev.id == id_evidencia(ev.documento, ev.demonstracao, ev.coluna, ev.cd_conta)
    assert ev.localizacao is not None and ev.localizacao["arquivo"].startswith("dfp_cia_aberta_2020.zip/")
    assert ev.localizacao["escala"] == "MIL" and ev.localizacao["linha"] >= 2
    e = na_data.exercicio_na_data(arm, "100", 2020, "2021-04-30", localizador=loc)
    ev = next(x for x in e.evidencias if x.cd_conta == "3.01" and x.coluna == "ÚLTIMO")
    assert ev.valor == 1_000_000.0 and ev.documento.origem == "enet" and ev.documento.url
    assert ev.localizacao == {"arquivo": "data/cache/enet/1001_con.csv", "linha": 2}
    sem = na_data.exercicio_na_data(arm, "100", 2020, "2021-04-30")
    assert all(x.localizacao is None for x in sem.evidencias)
    assert na_data.exercicio_na_data(arm, "500", 2020, "2021-04-30").evidencias == ()


def _baixa_falso(cache: Path, num: str, versao: int) -> pd.DataFrame:
    d = pd.DataFrame([("DRE", "ÚLTIMO", "3.01", "Receita de Venda de Bens e/ou Serviços", 70_000.0),
                      ("BPA", "ÚLTIMO", "1", "Ativo Total", 90_000.0)], columns=base.COLUNAS)  # fmt: skip
    d.to_csv(cache / f"{num}_con.csv", index=False)
    return d


def test_busca_no_enet_e_comando_separado(mundo_c1: tuple[Fontes, armazem.FontesArmazem], tmp_path: Path) -> None:
    brutos, arm = mundo_c1
    lista = buscar_enet.pendentes(arm, "2023-04-30", [2022])
    assert list(lista.num_doc) == ["16001"] and list(lista.versao) == [1]
    r = buscar_enet.buscar(lista, cache=brutos.cache_enet, baixar=_baixa_falso)
    assert list(r.resultado) == ["baixado"]
    assert list(buscar_enet.buscar(lista, cache=brutos.cache_enet, baixar=_baixa_falso).resultado) == ["ja_no_cache"]
    armazem.montar(brutos, tmp_path / "armazem2", anos=range(2020, 2024))
    novo = armazem.FontesArmazem(tmp_path / "armazem2")
    e = na_data.exercicio_na_data(novo, "160", 2022, "2023-04-30")
    assert (e.situacao, e.origem, e.versao_usada) == ("ok", "enet", 1)
    assert buscar_enet.pendentes(novo, "2023-04-30", [2022]).empty
    tardia = lista.assign(dt_receb=date(2025, 2, 1))
    with pytest.raises(ValueError):
        buscar_enet.buscar(tardia, cache=brutos.cache_enet, baixar=_baixa_falso)
    with pytest.raises(ExercicioLacrado):
        buscar_enet.pendentes(novo, "2023-04-30", [2024])


def test_consulta_nunca_busca_no_enet() -> None:
    """Só o comando separado chama a rede do ENET: nenhum módulo de consulta importa as funções de download."""
    for modulo in ("armazem", "na_data", "invariante"):
        texto = (Path(armazem.__file__).parent / f"{modulo}.py").read_text(encoding="utf-8")
        assert "baixa_para_cache" not in texto and "baixa_consolidado" not in texto and "rede=True" not in texto


@pytest.mark.parametrize("lang,caminho", [("pt", "docs/contratos.md"), ("en", "docs/en/contracts.md")])
def test_contratos_contam_os_documentos_so_com_estrutura(lang: str, caminho: str) -> None:
    n = json.loads(invariante.NUMEROS.read_text(encoding="utf-8"))
    texto = (Path(armazem.__file__).parents[2] / caminho).read_text(encoding="utf-8")
    assert invariante.frase_so_metadados(n, lang) in texto
    nota = na_data.NOTA_ESTRUTURA_POSTERIOR
    assert (nota.pt if lang == "pt" else nota.en) in texto


# ---- Reapresentação pelo comparativo do ano seguinte e escala do ENET (09/11/2026) ----


def test_diferenca_no_comparativo_do_ano_seguinte(mundo_c1: tuple[Fontes, armazem.FontesArmazem]) -> None:
    _, arm = mundo_c1
    e = na_data.exercicio_na_data(arm, "100", 2020, "2022-04-30")  # a DFP de 2021 já foi entregue (10/03/2022)
    difs = e.diferencas_comparativo
    assert [(d.demonstracao, d.cd_conta) for d in difs] == [("BPA", "1")]  # 3.01 igual; 3.11 só existe em t
    d = difs[0]
    assert (d.valor, d.valor_comparativo, d.diferenca) == (5_000_000.0, 5_500_000.0, 500_000.0)
    assert (d.versao, d.dt_receb, d.versao_seguinte, d.dt_receb_seguinte) == (2, "2021-07-20", 1, "2022-03-10")
    assert d.texto.pt == "valor diferente no comparativo do ano seguinte (reapresentação ou reclassificação)"
    assert (d.grupo, d.destacada) == ("a", True)  # ativo total; R$ 500 mil > 1% de R$ 5 milhões
    assert (
        na_data.exercicio_na_data(arm, "100", 2020, "2021-12-31").diferencas_comparativo == ()
    )  # 2021 ainda não existia
    assert comparativo.contagem(arm, date(2022, 4, 30), [2020]) == {
        "2020": {"comparadas": 1, "com_diferenca": 1, "com_destacada": 1}
    }
    assert comparativo.leitura_seguinte(arm, "100", 2023, date(2024, 12, 31)) is None  # 2024 é lacrado


def test_tolerancia_do_comparativo() -> None:
    def leitura(valor: float, ordem: str) -> base.Leitura:
        contas = pd.DataFrame([("BPA", ordem, "1", "Ativo Total", valor)], columns=base.COLUNAS)
        return base.Leitura("1", "2020-12-31", None, base.OK, versao=1, tipo="con", contas=contas)

    assert comparativo.comparar(leitura(10_000.0, "ÚLTIMO"), leitura(11_000.0, "PENÚLTIMO")) == []  # igual à tolerância
    assert len(comparativo.comparar(leitura(10_000.0, "ÚLTIMO"), leitura(11_000.5, "PENÚLTIMO"))) == 1
    outra = leitura(11_000.5, "PENÚLTIMO")
    outra.tipo = "ind"
    assert comparativo.comparar(leitura(10_000.0, "ÚLTIMO"), outra) == []  # tipos diferentes


def test_materialidade_do_comparativo() -> None:
    """Grupo (a): totais e linhas-chave; grupo (b): demais linhas. Destacada: grupo (a) acima de 1% do ativo total."""

    def leitura(ordem: str, linhas: list[tuple[str, str, float]]) -> base.Leitura:
        contas = pd.DataFrame([(dem, ordem, cod, f"conta {cod}", v) for dem, cod, v in linhas], columns=base.COLUNAS)
        return base.Leitura("1", "2020-12-31", None, base.OK, versao=1, tipo="con", contas=contas)

    t = leitura(
        "ÚLTIMO",
        [
            ("BPA", "1", 1e6),
            ("BPP", "2.01", 1e5),
            ("BPP", "2.02", 1e5),
            ("BPA", "1.01.01", 1e5),
            ("DFC_MI", "6.01", 5e4),
            ("DRE", "3.11", 1e4),
        ],
    )
    s = leitura("PENÚLTIMO", [("BPA", "1", 1e6), ("BPP", "2.01", 1.05e5), ("BPP", "2.02", 1.2e5),
                              ("BPA", "1.01.01", 2e5), ("DFC_MD", "6.01", 7e4), ("DRE", "3.11", 1.05e4)])  # fmt: skip
    difs = {(d.demonstracao[:3], d.cd_conta): (d.grupo, d.destacada) for d in comparativo.comparar(t, s)}
    assert difs == {
        ("BPP", "2.01"): ("a", False),  # 0,5% do ativo total: na lista, sem destaque
        ("BPP", "2.02"): ("a", True),  # 2%
        ("BPA", "1.01.01"): ("b", False),  # reclassificação: nunca destacada, mesmo grande
        ("DFC", "6.01"): ("a", True),  # a DFC pelo prefixo (o método pode mudar)
    }  # 3.11: R$ 500, dentro da tolerância
    assert comparativo.limite_destaque(t.contas) == 10_000.0
    sem_at = leitura("ÚLTIMO", [("BPA", "1", 0.0), ("BPP", "2.02", 100_000.0)])
    assert not any(d.destacada for d in comparativo.comparar(sem_at, s))  # sem ativo total positivo, nada é destacado
    assert [k for k in comparativo.CHAVES] == ["ativo_total", "passivo_circulante", "passivo_nao_circulante",
                                               "patrimonio_liquido", "receita_liquida", "lucro_liquido",
                                               "caixa_operacional_apresentado"]  # fmt: skip
    assert comparativo.LINHAS_CHAVE == (("BPA", "1"), ("BPP", "2.01"), ("BPP", "2.02"), ("BPP", "2.03"),
                                        ("DRE", "3.01"), ("DRE", "3.11"), ("DFC", "6.01"))  # fmt: skip


def test_escala_da_pagina_do_enet() -> None:
    assert buscar_enet.escala_da_pagina("<b>Valores (Reais Mil)</b>") == "MIL"
    assert buscar_enet.escala_da_pagina("<b>Valores (Reais)</b>") == "UNIDADE"
    assert buscar_enet.escala_da_pagina("<b>sem escala</b>") is None


def test_busca_registra_a_escala_do_enet(
    mundo_c1: tuple[Fontes, armazem.FontesArmazem], tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from chiocca import enet

    brutos, arm = mundo_c1
    pagina = ("<p>Valores (Reais Mil)</p><table><tr><td>Conta</td></tr>"
              "<tr><td>1</td><td>Ativo Total</td><td>90</td><td>80</td></tr></table>")  # fmt: skip
    monkeypatch.setattr(enet, "baixa_consolidado", lambda num, versao: enet.parse_tabela(pagina, "BPA"))
    lista = buscar_enet.pendentes(arm, "2023-04-30", [2022])
    assert list(buscar_enet.buscar(lista, cache=brutos.cache_enet).resultado) == ["baixado"]
    assert json.loads((brutos.cache_enet / "16001_escala.json").read_text()) == {"BPA": "MIL"}
    assert enet.parse_tabela.__name__ == "parse_tabela"  # a rota do estudo 1 volta como era
    armazem.montar(brutos, tmp_path / "armazem3", anos=range(2020, 2024))
    novo = armazem.FontesArmazem(tmp_path / "armazem3")
    e = na_data.exercicio_na_data(novo, "160", 2022, "2023-04-30")
    assert (e.origem, e.escala_original) == ("enet", "MIL") and na_data.SEM_ESCALA_ENET not in e.notas
    assert e.contas[e.contas.cd_conta == "1"].valor.iloc[0] == 90_000.0
