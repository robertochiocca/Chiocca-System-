"""Script do estudo 2 (pré-registro do estudo 2, seção 9, item 3): a lista, o gabarito, a avaliação secundária e o
registro de SHA-256 do código. Só com dados sintéticos (empresas fictícias, `tests/fixtures_cvm.py`) ou, quando os dados
estão no ambiente, com o exercício de 2023; nada de 2024 e 2025 é lido."""

from __future__ import annotations

import ast
import hashlib
import io
import json
import math
import re
from datetime import date
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import pytest

from chiocca import base, montar_base, sinais_amostra
from chiocca.cvm import Fontes
from chiocca.v2 import lacre
from chiocca.v2.estudo2 import abertura, gabarito, lista, registro, secundaria
from tests import fixtures_cvm as fx
from tests.test_base import mundo  # noqa: F401  (fixture)

RAIZ = base.RAIZ
SINAIS_ESTUDO_1 = RAIZ / "resultados" / "sinais_empresa_ano.csv"


class FontesProibidas:
    """Qualquer leitura falha: o lacre tem de recusar antes."""

    def __getattr__(self, nome: str) -> Any:
        raise AssertionError(f"leitura de dados antes do lacre: {nome}")


def _gerar(f: Fontes, anos: list[int] | None = None) -> bytes:
    return lista.gerar(f, anos or [2020], "0" * 40, "3.13", "1" * 64)


def _corpo(conteudo: bytes) -> str:
    return "\n".join(x for x in conteudo.decode("utf-8").split("\n") if not x.startswith("#"))


# ---- lacre ----


def test_lacre_do_estudo_fechado() -> None:
    """Antes do commit de abertura, as constantes do estudo não existem (seção 9)."""
    assert not hasattr(lacre, abertura.CONSTANTE) and not hasattr(lacre, abertura.CONSTANTE_SEGUNDA)
    assert abertura.exercicios_do_estudo() == () and abertura.segunda_abertura() == ()
    assert lacre.ULTIMO_EXERCICIO_LIBERADO == 2023 and lacre.DATA_REFERENCIA_MAXIMA == date(2024, 12, 31)


def test_lista_recusa_exercicio_lacrado_antes_de_ler() -> None:
    for anos in ([2024], [2025], [2023, 2024]):
        with pytest.raises(lacre.ExercicioLacrado):
            lista.calcular(FontesProibidas(), anos)  # type: ignore[arg-type]
        with pytest.raises(lacre.ExercicioLacrado):
            lista.gerar(FontesProibidas(), anos, "0" * 40, "3.13", "1" * 64)  # type: ignore[arg-type]
    with pytest.raises(SystemExit, match="lacre do estudo 2 está fechado"):
        lista.main([])


def test_abertura_so_pela_constante(monkeypatch: pytest.MonkeyPatch) -> None:
    with pytest.raises(lacre.ExercicioLacrado):
        abertura.garantir_exercicio(2024)
    monkeypatch.setattr(lacre, abertura.CONSTANTE, (2024, 2025), raising=False)
    assert abertura.garantir_exercicio(2024) == 2024 and abertura.garantir_seguinte(2025) == 2025
    with pytest.raises(lacre.ExercicioLacrado):
        abertura.garantir_seguinte(2026)  # a DFP de 2026 só com a segunda abertura
    monkeypatch.setattr(lacre, abertura.CONSTANTE_SEGUNDA, (2026,), raising=False)
    assert abertura.garantir_seguinte(2026) == 2026
    with pytest.raises(lacre.ExercicioLacrado):
        abertura.garantir_exercicio(2026)  # só para o comparativo, não para a lista
    assert lacre.ULTIMO_EXERCICIO_LIBERADO == 2023  # o produto não muda


def test_constantes_do_estudo_e_o_script_fora_do_produto() -> None:
    """Só o script do estudo usa as constantes da abertura (e só `abertura`, por getattr); o produto não importa o
    script."""
    importa_o_estudo = re.compile(r"chiocca\.v2\.estudo2(?!\w)|from chiocca\.v2 import [^\n]*\bestudo2(?!\w)")
    for p in sorted((RAIZ / "chiocca").rglob("*.py")):
        caminho, texto = p.relative_to(RAIZ).as_posix(), p.read_text(encoding="utf-8")
        no_estudo = caminho.startswith("chiocca/v2/estudo2/")
        if not no_estudo and caminho != "chiocca/v2/lacre.py":
            assert abertura.CONSTANTE not in texto and abertura.CONSTANTE_SEGUNDA not in texto, caminho
        if not no_estudo:
            assert not importa_o_estudo.search(texto), caminho
        for no in ast.walk(ast.parse(texto)):
            assert not (isinstance(no, ast.Attribute) and no.attr.startswith("ESTUDO_2")), caminho
            if isinstance(no, ast.Call) and isinstance(no.func, ast.Name) and no.func.id == "getattr" and no.args:
                if isinstance(no.args[0], ast.Name) and no.args[0].id == "lacre":
                    assert caminho == "chiocca/v2/estudo2/abertura.py", caminho


def test_sem_o_bloco_da_abertura() -> None:
    original = (RAIZ / "chiocca/v2/lacre.py").read_text(encoding="utf-8")
    aberto = original + f"\n\n{abertura.MARCA_INICIO}\nESTUDO_2_EXERCICIOS = (2024, 2025)\n{abertura.MARCA_FIM}\n"
    assert abertura.sem_o_bloco_da_abertura(aberto) == original == abertura.sem_o_bloco_da_abertura(original)
    mudado = original.replace("ULTIMO_EXERCICIO_LIBERADO = 2023", "ULTIMO_EXERCICIO_LIBERADO = 2024")
    assert abertura.sem_o_bloco_da_abertura(mudado + aberto[len(original) :]) != original


# ---- lista ----


def test_celula_no_formato_fixo() -> None:
    assert lista.celula("mscore", -0.0000001) == "0.000000" and lista.celula("mscore", -1.5) == "-1.500000"
    assert lista.celula("mscore", 0.0) == "0.000000" and lista.celula("dpo", float("nan")) == ""
    assert lista.celula("em_alerta", True) == "1" and lista.celula("em_alerta", "False") == "0"
    assert lista.celula("em_alerta", pd.NA) == "" and lista.celula("versao", 2.0) == "2"
    assert lista.celula("dt_receb", date(2025, 3, 1)) == "2025-03-01" and lista.celula("status", "ok") == "ok"


def test_lista_igual_ao_caminho_do_estudo_1(mundo: Fontes, tmp_path: Path) -> None:  # noqa: F811
    nova = lista.calcular(mundo, [2020])
    montar_base.monta(mundo, range(2020, 2021), saida=tmp_path / "base")
    meta = pd.read_csv(tmp_path / "base" / "empresa_ano.csv", dtype={"cd_cvm": str, "num_doc": str})
    estudo, _ = sinais_amostra.alertas(sinais_amostra.calcula(meta, tmp_path / "base", range(2020, 2021)))
    chave = ["cd_cvm", "dt_refer"]
    a, b = nova.set_index(chave), estudo.set_index(chave)
    assert sorted(a.index) == sorted(b.index)
    for col in [c for c in lista.COLUNAS_ESTUDO_1 if c in estudo.columns and c not in chave]:
        for k in b.index:
            assert lista.celula(col, a.at[k, col]) == lista.celula(col, b.at[k, col]), (k, col)
    assert set(nova.amostra) >= {sinais_amostra.AMOSTRA_NF, sinais_amostra.AMOSTRA_FIN}


def test_formato_do_arquivo(mundo: Fontes) -> None:  # noqa: F811
    conteudo = _gerar(mundo)
    t = conteudo.decode("utf-8")
    assert "\r" not in t and t.endswith("\n") and not conteudo.startswith(b"\xef\xbb\xbf")
    cab = [x for x in t.split("\n") if x.startswith("#")]
    assert cab[:4] == [lista.TITULO, f"# commit: {'0' * 40}", "# python: 3.13", f"# requirements-lock.txt: {'1' * 64}"]
    entradas = dict(x.removeprefix("# entrada: ").split(" ") for x in cab if x.startswith("# entrada: "))
    for nome in ("dfp_cia_aberta_2020.zip", "fca_cia_aberta_2020.zip", "cad_cia_aberta.csv"):
        assert entradas[nome] == hashlib.sha256((mundo.pasta / nome).read_bytes()).hexdigest()
    assert entradas["enet/1001_con.csv"] == hashlib.sha256((mundo.cache_enet / "1001_con.csv").read_bytes()).hexdigest()
    assert "data/cdi_sgs4389.csv" in entradas
    corpo = pd.read_csv(io.StringIO(_corpo(conteudo)), dtype=str, keep_default_na=False)
    assert list(corpo.columns) == lista.COLUNAS
    assert corpo.cd_cvm.astype(int).tolist() == sorted(corpo.cd_cvm.astype(int))
    for col in lista.NUMEROS:
        assert all(re.fullmatch(r"-?\d+\.\d{6}", x) for x in corpo[col] if x), col
    assert date.today().isoformat() not in t  # sem data de geração


def test_duas_execucoes_dao_o_mesmo_arquivo(mundo: Fontes) -> None:  # noqa: F811
    primeiro = _gerar(mundo)
    assert _gerar(Fontes(mundo.pasta, mundo.cache_enet)) == primeiro


def test_lista_lida_de_volta_da_o_mesmo_corpo(mundo: Fontes) -> None:  # noqa: F811
    conteudo = _gerar(mundo)
    lida = lista.ler(conteudo)
    assert _corpo(lista.texto(lida, "0" * 40, "3.13", "1" * 64, [])) == _corpo(conteudo)
    assert lida.em_alerta.dtype == "boolean" and lida.exercicio.dtype == "Int64"


def test_pendentes_do_enet(mundo: Fontes) -> None:  # noqa: F811
    (mundo.cache_enet / "1001_con.csv").unlink()
    s = lista.calcular(Fontes(mundo.pasta, mundo.cache_enet), [2020])
    assert lista.pendentes_enet(s) == ["1001 1"]
    assert "enet/1001_con.csv" not in _gerar(Fontes(mundo.pasta, mundo.cache_enet)).decode("utf-8")


# ---- gabarito ----

INDICE_COLS = ["cd_cvm", "DT_REFER", "versao", "dt_receb"]


def _caso(**k: str) -> dict[str, str]:
    c = dict.fromkeys(gabarito.colunas(), "")
    c.update({"caso_id": "x", "cd_cvm": "100", "periodo_afetado_inicio": "2024", "periodo_afetado_fim": "2025",
              "data_publica": "2027-02-01", "acertavel_principal": "sim", "parte": "2"})  # fmt: skip
    c.update(k)
    return c


def test_parte_1_so_com_o_cabecalho() -> None:
    antes = hashlib.sha256(gabarito.PARTE_1.read_bytes()).hexdigest()
    casos = gabarito.ler_parte(gabarito.PARTE_1)
    assert casos == []
    assert gabarito.conferir_acertavel(casos, lambda ano: FontesProibidas().indice_dfp(ano)) == []  # nada é lido
    assert gabarito.descrever_parte(casos, None, 1)["texto"] == "parte 1: nenhum caso"
    assert "nenhuma divergência" in gabarito.resumo_da_conferencia(casos, [])
    assert hashlib.sha256(gabarito.PARTE_1.read_bytes()).hexdigest() == antes  # o arquivo congelado não muda


def test_parte_com_formato_errado_e_recusada(tmp_path: Path) -> None:
    errado = tmp_path / "p.csv"
    errado.write_text(",".join(gabarito.colunas()[:-1]) + "\n", encoding="utf-8")
    with pytest.raises(ValueError, match="cabeçalho"):
        gabarito.ler_parte(errado)
    curto = tmp_path / "c.csv"
    curto.write_text(",".join(gabarito.colunas()) + "\na,b\n", encoding="utf-8")
    with pytest.raises(ValueError, match="colunas"):
        gabarito.ler_parte(curto)


def test_conferencia_de_acertavel_pelo_indice(monkeypatch: pytest.MonkeyPatch) -> None:
    """Índices sintéticos de 2024 e 2025 (metadados fictícios), com a constante só dentro do teste."""
    monkeypatch.setattr(lacre, abertura.CONSTANTE, (2024, 2025), raising=False)
    indices = {
        2024: pd.DataFrame([["100", "2024-12-31", 1, date(2025, 3, 20)], ["200", "2024-12-31", 1, date(2025, 5, 20)],
                            ["300", "2024-12-31", 1, date(2025, 3, 1)], ["300", "2024-12-31", 2, date(2025, 4, 10)]],
                           columns=INDICE_COLS),
        2025: pd.DataFrame([["400", "2025-12-31", 1, date(2026, 3, 10)]], columns=INDICE_COLS),
    }  # fmt: skip
    casos = [
        _caso(caso_id="a"),  # versão de 2024 antes do corte e da data: acertável, sem divergência
        _caso(caso_id="b", cd_cvm="200"),  # entregue depois do corte: não acertável, diverge do "sim"
        _caso(caso_id="c", cd_cvm="300", data_publica="2025-04-01", acertavel_principal="sim"),  # v2 depois da data
        _caso(caso_id="d", cd_cvm="400", data_publica="2026-04-01", acertavel_principal="nao"),  # só 2025, regra 4.1
        _caso(caso_id="e", cd_cvm="", acertavel_principal="sim"),  # sem código CVM
    ]
    r = {c["caso_id"]: c for c in gabarito.conferir_acertavel(casos, indices.__getitem__)}
    assert (r["a"]["acertavel_pelo_indice"], r["a"]["divergente"]) == (True, False)
    assert (r["b"]["acertavel_pelo_indice"], r["b"]["divergente"]) == (False, True)
    assert (r["c"]["acertavel_pelo_indice"], r["c"]["divergente"]) == (False, True)
    assert r["d"]["exercicios_pelo_indice"] == [2025] and r["d"]["exercicios_pela_regra_4_1"] == []
    assert r["d"]["divergente"] and r["e"]["divergente"] and not r["e"]["exercicios_pelo_indice"]
    resumo = gabarito.resumo_da_conferencia(casos, list(r.values()))
    assert "4 divergências" in resumo and "- b:" in resumo


def _lista_sintetica() -> pd.DataFrame:
    linhas = [
        # cd, exercicio, amostra, avaliada, em_alerta, dt_receb, alerta_juro
        ("100", 2024, "nao_financeira", True, False, "2025-03-20", False),
        ("100", 2025, "nao_financeira", True, True, "2026-03-20", True),
        ("200", 2024, "nao_financeira", True, True, "2025-03-20", True),
        ("300", 2024, "nao_financeira", True, False, "2025-03-20", False),
        ("400", 2024, "financeira", True, False, "2025-03-20", False),
    ]
    d = pd.DataFrame(linhas, columns=["cd_cvm", "exercicio", "amostra", "avaliada", "em_alerta", "dt_receb",
                                      "alerta_juro"])  # fmt: skip
    for c in ("alerta_mscore", "alerta_dpo", "alerta_peso_nao_recorrente"):
        d[c] = pd.array([False] * len(d), dtype="boolean")
    return d.astype({"avaliada": "boolean", "em_alerta": "boolean", "alerta_juro": "boolean"})


def test_regra_4_1_e_antecedencia() -> None:
    s = _lista_sintetica()
    antes = gabarito.avaliar_caso(_caso(data_publica="2026-01-10"), s)  # antes de 30/04/2026: só a DFP de 2024
    assert antes["acertavel"] and not antes["acertado"] and [2025, "depois_da_data"] in antes["exercicios_fora"]
    so_regra = gabarito.avaliar_caso(_caso(data_publica="2026-04-29"), s)  # 2025 entregue antes, mas a regra tira
    assert [2025, "regra_4_1"] in so_regra["exercicios_fora"] and not so_regra["acertado"]
    depois = gabarito.avaliar_caso(_caso(data_publica="2027-03-20"), s)
    assert depois["acertado"] and depois["exercicios_que_contam"][1]["sinais"] == ["juro"]
    assert math.isclose(depois["antecedencia_meses"], 365 * 12 / 365.25)
    fora = gabarito.avaliar_caso(_caso(cd_cvm="999"), s)
    assert not fora["acertavel"] and fora["exercicios_fora"] == [[2024, "sem_dfp"], [2025, "sem_dfp"]]


def test_descricao_de_uma_parte_com_casos() -> None:
    s = _lista_sintetica()
    casos = [_caso(caso_id="a", cd_cvm="200", periodo_afetado_fim="2024"), _caso(caso_id="b", cd_cvm="300",
             periodo_afetado_fim="2024"), _caso(caso_id="c", cd_cvm="999")]  # fmt: skip
    d = gabarito.descrever_parte(casos, s, 2)
    assert (d["casos"], d["acertaveis"], d["acertados"]) == (3, 2, 1)
    taxa = 1 / 3  # 2024, não financeiras avaliadas: 1 em alerta de 3
    assert math.isclose(d["chance_de_ao_menos_esse_total_ao_acaso"], 1 - (1 - taxa) ** 2)
    assert gabarito.binomial_de_poisson([0.5, 0.5]) == [0.25, 0.5, 0.25]


# ---- avaliação secundária ----


def test_metricas_de_ranking_num_exemplo_a_mao() -> None:
    rel = np.array([1, 0, 1, 0, 0, 0, 0, 0, 0, 1])
    r = secundaria.ranking(rel, 0.30)  # k = 3
    assert r["k"] == 3 and math.isclose(r["precisao"], 2 / 3) and math.isclose(r["lift"], (2 / 3) / 0.3)
    assert math.isclose(r["ndcg"], 1.5 / (1 + 1 / math.log2(3) + 0.5))
    um = secundaria.ranking(rel, 0.01)  # k = ⌈0,1⌉ = 1
    assert (um["k"], um["precisao"], um["ndcg"]) == (1, 1.0, 1.0)
    assert math.isnan(secundaria.ranking(np.zeros(5, dtype=int), 0.4)["ndcg"])  # sem relevantes: indefinido
    assert secundaria.topo(0.05, 1201) == 61


def test_ordem_do_ranking() -> None:
    rep = pd.DataFrame({"cd_cvm": ["10", "9", "20", "30", "30"], "exercicio": [2024, 2024, 2024, 2025, 2024],
                        "n_sinais": [1, 1, 2, 1, 1], "mscore": [-1.0, -1.0, float("nan"), float("nan"), float("nan")],
                        "alavancagem": [0.5, 0.9, float("nan"), 0.7, 0.7]})  # fmt: skip
    ordem = list(np.argsort(secundaria.ordem_do_motor(rep)))
    assert ordem == [2, 1, 0, 4, 3]  # 2 sinais; M-score (empate: código 9 antes de 10); sem M-score; exercício
    assert list(np.argsort(secundaria.ordem_da_regra_boba(rep))) == [1, 4, 3, 0, 2]


def test_bootstrap_por_companhia_pareado_e_reprodutivel() -> None:
    companhia = np.array(["1", "1", "2", "3", "3"])
    estat = {"n": lambda i: float(len(i)), "par": lambda i: float((i == 0).sum() - (i == 1).sum())}
    a = secundaria.bootstrap_por_companhia(companhia, estat, 300, 7)
    b = secundaria.bootstrap_por_companhia(companhia, estat, 300, 7)
    assert all(np.array_equal(a[k], b[k]) for k in a)
    assert (a["par"] == 0).all()  # as duas empresa-anos da companhia 1 sempre juntas
    assert set(a["n"]) <= {3.0, 4.0, 5.0, 6.0} and len(set(a["n"])) > 1


def _rep_sintetico() -> pd.DataFrame:
    rng = np.random.default_rng(1)
    linhas = []
    for c in range(1, 121):
        for ano in (2024, 2025):
            alerta = (c + ano) % 2 == 0
            linhas.append({"exercicio": ano, "cd_cvm": str(c), "amostra": "nao_financeira", "avaliada": True,
                           "em_alerta": alerta, "alerta_regra_boba": c % 10 == 0, "n_sinais": int(alerta),
                           "mscore": float(rng.normal()), "alavancagem": float(rng.uniform()),
                           "estreita": bool(rng.uniform() < (0.30 if alerta else 0.03)), "larga": alerta,
                           "situacao_seguinte": "ok"})  # fmt: skip
    linhas.append({"exercicio": 2024, "cd_cvm": "999", "amostra": "financeira", "avaliada": True, "em_alerta": True,
                   "alerta_regra_boba": False, "n_sinais": 1, "mscore": float("nan"), "alavancagem": 0.9,
                   "estreita": True, "larga": True, "situacao_seguinte": "ok"})  # fmt: skip
    linhas.append({"exercicio": 2025, "cd_cvm": "998", "amostra": "nao_financeira", "avaliada": False,
                   "em_alerta": True, "alerta_regra_boba": False, "n_sinais": 1, "mscore": 0.1, "alavancagem": 0.2,
                   "estreita": False, "larga": False, "situacao_seguinte": "sem_documento"})  # fmt: skip
    return pd.DataFrame(linhas)


def test_avaliacao_secundaria_sintetica() -> None:
    r = secundaria.avaliar(_rep_sintetico(), reamostragens=300)
    assert r["empresa_anos"] == 240 and r["companhias"] == 120 and r["semente"] == secundaria.SEMENTE
    m = r["motor"]
    assert m["em_alerta"]["empresa_anos"] == 120 and m["dr"] > 0 and m["dr_limite_inferior_95"] > 0
    assert r["resultado"] == "associação positiva"
    assert r["motor_menos_regra_boba"]["resultado"] == "o motor separa melhor que a regra boba"
    assert set(r["ranking"]) == {"1%", "5%", "10%"} and r["ranking"]["10%"]["k"] == 24
    assert r["descritivos"]["financeiras"]["em_alerta"]["empresa_anos"] == 1
    assert r["descritivos"]["nao_avaliadas_por_situacao"] == {"sem_documento": 1}
    json.dumps(r, allow_nan=False)  # só números finitos ou vazios
    assert secundaria.avaliar(_rep_sintetico(), reamostragens=300) == r  # mesma semente, mesmo resultado


def _mundo_secundario(tmp_path: Path) -> Fontes:
    """DFP fictícias de 2020 e 2021: o comparativo de 2020 na DFP de 2021 muda o PL (11), a receita (12), um valor
    abaixo do destaque (13); a 14 não tem DFP de 2021."""
    brutos = tmp_path / "brutos"
    brutos.mkdir()
    d20, d21 = "2020-12-31", "2021-12-31"
    idx20 = [fx.doc(c, d20, 1, "2021-03-10", int(c) * 100 + 1) for c in ("11", "12", "13", "14")]
    idx21 = [fx.doc(c, d21, 1, "2022-03-10", int(c) * 100 + 2) for c in ("11", "12", "13")]
    l20, l21 = [], []
    for c, pl_seguinte, rec_seguinte in (("11", 380, 500), ("12", 400, 470), ("13", 395, 500), ("14", 400, 500)):
        l20 += [fx.linha(c, d20, 1, "ÚLTIMO", "1", "Ativo Total", 1000), fx.linha(c, d20, 1, "ÚLTIMO", "2.03",
                "Patrimônio Líquido Consolidado", 400), fx.linha(c, d20, 1, "ÚLTIMO", "3.01",
                "Receita de Venda de Bens e/ou Serviços", 500)]  # fmt: skip
        l21 += [fx.linha(c, d21, 1, "PENÚLTIMO", "2.03", "Patrimônio Líquido Consolidado", pl_seguinte),
                fx.linha(c, d21, 1, "PENÚLTIMO", "3.01", "Receita de Venda de Bens e/ou Serviços", rec_seguinte),
                fx.linha(c, d21, 1, "PENÚLTIMO", "1", "Ativo Total", 1000)]  # fmt: skip
    fx.escreve_dfp(brutos, 2020, idx20, {"BPA_con": [x for x in l20 if x["CD_CONTA"] == "1"],
                                         "BPP_con": [x for x in l20 if x["CD_CONTA"] == "2.03"],
                                         "DRE_con": [x for x in l20 if x["CD_CONTA"] == "3.01"]})  # fmt: skip
    l21 = [x for x in l21 if x["CD_CVM"] != "000014"]
    fx.escreve_dfp(brutos, 2021, idx21, {"BPA_con": [x for x in l21 if x["CD_CONTA"] == "1"],
                                         "BPP_con": [x for x in l21 if x["CD_CONTA"] == "2.03"],
                                         "DRE_con": [x for x in l21 if x["CD_CONTA"] == "3.01"]})  # fmt: skip
    return Fontes(brutos, tmp_path / "cache")


def _linhas_da_lista(cds: list[str], versao: int = 1) -> pd.DataFrame:
    return pd.DataFrame({
        "exercicio": pd.array([2020] * len(cds), dtype="Int64"), "cd_cvm": cds, "dt_refer": "2020-12-31",
        "amostra": "nao_financeira", "avaliada": pd.array([True] * len(cds), dtype="boolean"),
        "em_alerta": pd.array([True] * len(cds), dtype="boolean"),
        "alerta_regra_boba": pd.array([None] * len(cds), dtype="boolean"),
        "n_sinais": pd.array([1] * len(cds), dtype="Int64"), "mscore": 0.0, "alavancagem": 0.5,
        "versao": pd.array([versao] * len(cds), dtype="Int64"), "num_doc": [str(int(c) * 100 + 1) for c in cds],
    })  # fmt: skip


def test_republicacao_estreita_e_larga_pelo_comparativo(tmp_path: Path) -> None:
    rep = secundaria.republicacoes(_mundo_secundario(tmp_path), _linhas_da_lista(["11", "12", "13", "14"]))
    r = rep.set_index("cd_cvm")
    assert (bool(r.at["11", "estreita"]), bool(r.at["11", "larga"])) == (True, True)  # PL: 2% do ativo
    assert (bool(r.at["12", "estreita"]), bool(r.at["12", "larga"])) == (False, True)  # só a receita
    assert (bool(r.at["13", "estreita"]), bool(r.at["13", "larga"])) == (False, False)  # abaixo de 1% do ativo
    assert not r.at["14", "avaliada"] and r.at["14", "situacao_seguinte"] == base.SEM_DOCUMENTO
    assert not r.alerta_regra_boba.any()  # sem alavancagem calculável: fora de alerta, como no estudo 1


def test_secundaria_para_se_a_versao_nao_e_a_da_lista(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="não é a da lista"):
        secundaria.republicacoes(_mundo_secundario(tmp_path), _linhas_da_lista(["11"], versao=2))


def test_secundaria_recusa_a_dfp_seguinte_lacrada() -> None:
    s = _linhas_da_lista(["11"]).assign(exercicio=pd.array([2023], dtype="Int64"))
    with pytest.raises(lacre.ExercicioLacrado):
        secundaria.republicacoes(FontesProibidas(), s)  # type: ignore[arg-type]
    with pytest.raises(SystemExit, match="2027-05-31"):
        secundaria.main(["--sha256", "0" * 64])


# ---- registro de SHA-256 do código ----


def test_codigo_do_estudo_congelado_nao_mudou() -> None:
    gravado = json.loads(registro.REGISTRO.read_text(encoding="utf-8"))
    atual = registro.calcular()
    assert gravado["python"] == "3.13"
    assert gravado["requirements_lock_sha256"] == atual["requirements_lock_sha256"]
    assert gravado["entradas_versionadas"] == atual["entradas_versionadas"]
    for nome in registro.CONJUNTOS:
        assert set(gravado["conjuntos"][nome]) == set(atual["conjuntos"][nome]), f"arquivos de {nome} mudaram"
        mudaram = [c for c, h in gravado["conjuntos"][nome].items() if atual["conjuntos"][nome][c] != h]
        assert not mudaram, f"mudou depois do congelamento: {mudaram}"


def test_lista_so_com_o_motor_v1_e_o_lacre() -> None:
    gravado = json.loads(registro.REGISTRO.read_text(encoding="utf-8"))["conjuntos"]
    v2_lista = {c for c in gravado["lista"] if c.startswith("chiocca/v2/") and "/estudo2/" not in c}
    assert v2_lista == {"chiocca/v2/__init__.py", "chiocca/v2/lacre.py"}
    extras = set(gravado["secundaria"]) - set(gravado["lista"])
    assert extras == {"chiocca/v2/comparativo.py", "chiocca/v2/conferencias.py", "chiocca/v2/validade.py"}
    assert {"chiocca/base.py", "chiocca/sinais_amostra.py", "chiocca/sinais/mscore.py"} <= set(gravado["lista"])


# ---- com os dados do ambiente (exercício de 2023; pulado no CI) ----

DADOS_2023 = (base.BRUTOS / "dfp_cia_aberta_2023.zip").exists() and SINAIS_ESTUDO_1.exists()


@pytest.mark.skipif(not DADOS_2023, reason="precisa de data/brutos/cvm e de resultados/sinais_empresa_ano.csv")
def test_lista_de_2023_igual_ao_estudo_1() -> None:
    """O script do estudo, sobre os arquivos brutos e o cache do ENET, reproduz o estudo 1 no exercício de 2023."""
    nova = lista.calcular(Fontes(base.BRUTOS, base.CACHE_ENET), [2023])
    estudo = pd.read_csv(SINAIS_ESTUDO_1, dtype={"cd_cvm": str}, low_memory=False)
    estudo = estudo[estudo.exercicio == 2023]
    assert list(estudo.columns) == lista.COLUNAS_ESTUDO_1
    chave = ["cd_cvm", "dt_refer"]
    a, b = nova.set_index(chave), estudo.set_index(chave)
    assert len(a) == len(b) == 733 and sorted(a.index) == sorted(b.index)
    diferentes = {
        col: sum(lista.celula(col, a.at[k, col]) != lista.celula(col, b.at[k, col]) for k in b.index)
        for col in lista.COLUNAS_ESTUDO_1
        if col not in chave
    }
    assert not {c: n for c, n in diferentes.items() if n}, diferentes
