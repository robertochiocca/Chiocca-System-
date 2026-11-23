"""Código do motor v2 (pedido de 23/11/2026, item 2; pré-registro do motor v2, seções 3 a 6).

- O v2 reproduz o exemplo calculado à mão (`data/exemplo_motor_v2.json`, escrito antes do código).
- O escore, o alerta e o ranking batem com uma conta à mão; o v2 com as três mudanças desligadas é o v1.
- O código do v2 não lê `data/gabarito_casos.csv` nem importa as métricas do estudo 1 (seção 5), nem diretamente nem
  pelo que importa; o produto não importa o v2; o lacre do v2 é só o dele.
- A lista do v2 pelo caminho da lista do v1, com dados sintéticos (`tests/fixtures_cvm.py`).
"""

from __future__ import annotations

import ast
import io
import json
import math
import re
import subprocess
import sys
from datetime import date
from typing import Any

import numpy as np
import pandas as pd
import pytest

from chiocca import base, sinais_amostra
from chiocca.cvm import Fontes
from chiocca.sinais_amostra import AMOSTRA_FIN, AMOSTRA_NF, FORA_SEM_RECEITA
from chiocca.v2 import lacre
from chiocca.v2.estudo2 import lista as lista_v1
from chiocca.v2.motor_v2 import abertura, benford, dva, escore, lista, motor
from tests.test_base import mundo  # noqa: F401  (fixture)

RAIZ = base.RAIZ
EXEMPLO = json.loads((RAIZ / "data" / "exemplo_motor_v2.json").read_text(encoding="utf-8"))
TOL = EXEMPLO["tolerancia_absoluta"]
PACOTE = RAIZ / "chiocca" / "v2" / "motor_v2"
SINAIS_ESTUDO_1 = RAIZ / "resultados" / "sinais_empresa_ano.csv"
MOTIVOS = {
    "menos de 20 números": benford.POUCOS_NUMEROS,
    "faixa sem desvio-padrão (um membro só)": benford.FAIXA_SEM_DESVIO,
}


def perto(a: Any, b: float | None) -> bool:
    if b is None:
        return a is None or (isinstance(a, float) and math.isnan(a))
    return a is not None and not math.isnan(float(a)) and abs(float(a) - b) <= TOL


# ---- (a) Benford do exemplo à mão ----


def _benford_do_exemplo() -> tuple[pd.DataFrame, pd.DataFrame]:
    linhas, sinais = [], []
    for e in EXEMPLO["benford"]["entradas"]:
        dt = f"{e['exercicio']}-12-31"
        sinais.append({"exercicio": e["exercicio"], "cd_cvm": e["empresa_ano"], "dt_refer": dt, "amostra": e["grupo"]})
        for dem, ordem, valor in e["linhas"]:
            linhas.append({"cd_cvm": e["empresa_ano"], "dt_refer": dt, "demonstracao": dem, "ordem": ordem,
                           "cd_conta": "1", "ds_conta": "x", "valor": np.nan if valor is None else valor})  # fmt: skip
    return pd.DataFrame(sinais), pd.DataFrame(linhas)


def test_grupos_do_exemplo_sao_os_do_v1() -> None:
    assert {e["grupo"] for e in EXEMPLO["benford"]["entradas"]} == {AMOSTRA_NF, AMOSTRA_FIN}


def test_benford_reproduz_os_digitos_e_o_desvio() -> None:
    _, contas = _benford_do_exemplo()
    c = benford.contagens(contas).set_index("cd_cvm")
    assert np.allclose(benford.LEI, EXEMPLO["benford"]["lei"], atol=1e-15, rtol=0)
    for e in EXEMPLO["benford"]["esperado"]:
        r = c.loc[e["empresa_ano"]]
        assert [int(r[d]) for d in benford.DIGITOS] == e["contagens"], e["empresa_ano"]
        assert int(r.n_numeros_benford) == e["n_numeros"] and perto(r.desvio_benford, e["desvio"]), e["empresa_ano"]


def test_benford_reproduz_as_faixas_e_a_padronizacao() -> None:
    s, contas = _benford_do_exemplo()
    r = motor.aplica_benford(s, contas).set_index("cd_cvm")
    assert benford.MINIMO_NUMEROS == EXEMPLO["benford"]["minimo_numeros"] and benford.FAIXAS == 5
    for e in EXEMPLO["benford"]["esperado"]:
        x = r.loc[e["empresa_ano"]]
        faixa = None if pd.isna(x.faixa_benford) else int(x.faixa_benford)
        assert faixa == e["faixa"], e["empresa_ano"]
        assert perto(x.benford, e["padronizado"]), e["empresa_ano"]
        assert x.benford_motivo == (MOTIVOS[e["motivo"]] if e["motivo"] else None), e["empresa_ano"]
        if e["membros_da_faixa"]:
            membros = r[(r.exercicio == x.exercicio) & (r.amostra == x.amostra) & (r.faixa_benford == faixa)]
            assert sorted(membros.index) == sorted(e["membros_da_faixa"]), e["empresa_ano"]


def test_primeiro_digito_sem_erro_de_logaritmo() -> None:
    v = np.array([0.3, 0.03, 1000.0, 1e6, 999.9999, 0.0347, -7250.0, 1.1 * 1000, 0.3 * 1000, 2.9999999999999996])
    assert benford.primeiro_digito(v).tolist() == [3, 3, 1, 1, 9, 3, 7, 1, 3, 3]


# ---- (b) DEPI pela DVA do exemplo à mão ----


def _depi_do_exemplo(fonte: str = "dados_abertos") -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    ex, dt = EXEMPLO["depi_pela_dva"], "2020-12-31"
    contas = pd.DataFrame(
        [{"cd_cvm": "1", "dt_refer": dt, "demonstracao": d, "ordem": o, "cd_conta": c, "ds_conta": n, "valor": v}
         for d, o, c, n, v in ex["contas"]]
    )  # fmt: skip
    meta = ex["empresa_ano"]
    linha = sinais_amostra.sinais_nao_financeira(contas, dt)
    s = pd.DataFrame([{"exercicio": meta["exercicio"], "cd_cvm": "1", "dt_refer": dt, "amostra": AMOSTRA_NF,
                       "plano": "nao_financeiro", "tipo": meta["tipo"], "fonte": fonte, "versao": meta["versao"],
                       "status": "ok", **linha}])  # fmt: skip
    partes = []
    for tipo in ("con", "ind"):
        bruto = pd.DataFrame(
            [{"CD_CVM": "000001", "DT_REFER": dt, "VERSAO": str(x["versao"]), "ORDEM_EXERC": x["ordem"],
              "CD_CONTA": x["cd_conta"], "DS_CONTA": x["ds_conta"], "VL_CONTA": str(x["vl_conta"]),
              "ESCALA_MOEDA": x["escala_moeda"]} for x in ex["dva"] if x["tipo"] == tipo]
        )  # fmt: skip
        partes.append(dva.em_reais(bruto, tipo))
    return s, contas, dva.depreciacao(pd.concat(partes, ignore_index=True))


def test_v1_nao_calcula_o_depi_do_exemplo() -> None:
    s, _, _ = _depi_do_exemplo()
    e = EXEMPLO["depi_pela_dva"]["esperado"]["v1"]
    assert pd.isna(s.at[0, "DEPI"]) and pd.isna(s.at[0, "mscore"])
    for nome, valor in e["componentes"].items():
        assert perto(s.at[0, nome], valor), nome


def test_depreciacao_da_dva_reproduz_o_exemplo() -> None:
    _, _, dep = _depi_do_exemplo()
    e = EXEMPLO["depi_pela_dva"]["esperado"]["depreciacao_dva"]
    linha = dep[(dep.tipo == "con") & (dep.versao == 2)].iloc[0]
    assert (linha.conta_dva_t, linha.conta_dva_t1) == (e["conta_t"], e["conta_t-1"])
    assert perto(linha.depreciacao_dva_t, e["t"]) and perto(linha.depreciacao_dva_t1, e["t-1"])


def test_depi_e_mscore_do_v2_reproduzem_o_exemplo() -> None:
    s, contas, dep = _depi_do_exemplo()
    r = motor.aplica_depi_dva(s, contas, dep)
    e = EXEMPLO["depi_pela_dva"]["esperado"]["v2"]
    assert perto(r.at[0, "DEPI"], e["DEPI"]) and perto(r.at[0, "mscore"], e["M"])
    assert bool(r.at[0, "marca_depreciacao_dva"]) is e["marca_depreciacao_dva"] is True
    assert pd.isna(r.at[0, "DEPI_motivo"]) and pd.isna(r.at[0, "mscore_motivo"])
    for nome, valor in e["componentes"].items():
        assert perto(r.at[0, nome], valor), nome
    m = sum(motor.mscore.COEFICIENTES[n] * r.at[0, n] for n in motor.mscore.COEFICIENTES) + motor.mscore.INTERCEPTO
    assert perto(m, e["M"])


def test_versao_do_enet_fica_como_no_v1() -> None:
    s, contas, dep = _depi_do_exemplo(fonte="enet")
    r = motor.aplica_depi_dva(s, contas, dep)
    e = EXEMPLO["depi_pela_dva"]["esperado"]["se_a_versao_fosse_do_enet"]
    assert pd.isna(r.at[0, "DEPI"]) and pd.isna(r.at[0, "mscore"]) and e["DEPI"] is None
    assert bool(r.at[0, "marca_depreciacao_dva"]) is e["marca_depreciacao_dva"] is False


def test_depi_pela_dva_com_as_regras_do_v1() -> None:
    """Só a mudança do DEPI: o M-score do v2 passa pelo corte do v1 (-1,94 fica abaixo de -1,78)."""
    s, contas, dep = _depi_do_exemplo()
    r, _ = motor.calcula(s, contas, dep, motor.Mudancas(depi_dva=True, benford=False, escore=False))
    assert perto(r.at[0, "mscore"], EXEMPLO["depi_pela_dva"]["esperado"]["v2"]["M"])
    assert not bool(r.at[0, "alerta_mscore"])


def test_depi_do_v1_calculavel_nao_muda() -> None:
    """Com depreciação na DFC, a DVA não entra."""
    s, contas, dep = _depi_do_exemplo()
    extra = contas[contas.cd_conta == "6.01.01.02"].assign(
        cd_conta="6.01.01.03", ds_conta="Depreciação", valor=500_000.0
    )
    s2 = pd.DataFrame([{**s.iloc[0].to_dict(), **sinais_amostra.sinais_nao_financeira(pd.concat([contas, extra]),
                                                                                       "2020-12-31")}])  # fmt: skip
    assert pd.notna(s2.at[0, "DEPI"])
    r = motor.aplica_depi_dva(s2, pd.concat([contas, extra]), dep)
    assert r.at[0, "DEPI"] == s2.at[0, "DEPI"] and not bool(r.at[0, "marca_depreciacao_dva"])


def test_dva_preferencia_entre_as_contas_e_nome() -> None:
    linhas = pd.DataFrame([
        {"cd_cvm": "1", "dt_refer": "2020-12-31", "tipo": "con", "versao": 1, "ordem": "ÚLTIMO", "cd_conta": "7.04.01",
         "ds_conta": "Retenções diversas", "valor": -10.0},
        {"cd_cvm": "1", "dt_refer": "2020-12-31", "tipo": "con", "versao": 1, "ordem": "ÚLTIMO", "cd_conta": "7.07.01",
         "ds_conta": "Depreciacao  e   amortizacao", "valor": -30.0},
        {"cd_cvm": "1", "dt_refer": "2020-12-31", "tipo": "con", "versao": 1, "ordem": "ÚLTIMO", "cd_conta": "7.05.01",
         "ds_conta": "DEPRECIAÇÃO", "valor": -20.0},
        {"cd_cvm": "1", "dt_refer": "2020-12-31", "tipo": "con", "versao": 1, "ordem": "PENÚLTIMO",
         "cd_conta": "7.07.01", "ds_conta": "Depreciação", "valor": 15.0},
    ])  # fmt: skip
    d = dva.depreciacao(linhas).iloc[0]
    assert (d.conta_dva_t, d.depreciacao_dva_t) == ("7.05.01", 20.0)
    assert (d.conta_dva_t1, d.depreciacao_dva_t1) == ("7.07.01", 15.0)


# ---- escore, alerta e ranking (conta à mão) ----


def _sinais_para_o_escore() -> pd.DataFrame:
    nan = np.nan
    linhas = [  # cd, amostra, mscore, dpo, juro, peso, benford
        ("1", AMOSTRA_NF, -1.0, 10.0, nan, nan, nan),
        ("2", AMOSTRA_NF, -2.0, nan, nan, nan, 0.5),
        ("3", AMOSTRA_NF, nan, 30.0, nan, nan, nan),
        ("4", AMOSTRA_NF, -1.0, 20.0, nan, nan, nan),
        ("5", AMOSTRA_NF, -3.0, nan, nan, nan, 1.5),
        ("6", AMOSTRA_NF, nan, nan, nan, nan, nan),
        ("7", AMOSTRA_FIN, nan, nan, nan, 0.3, nan),
        ("8", FORA_SEM_RECEITA, nan, nan, nan, nan, nan),
    ]
    return pd.DataFrame(
        [{"exercicio": 2020, "cd_cvm": c, "dt_refer": "2020-12-31", "amostra": a, "mscore": m, "dpo": d, "juro": j,
          "peso_nao_recorrente": p, "benford": b} for c, a, m, d, j, p, b in linhas]
    )  # fmt: skip


def test_escore_alerta_e_ranking_a_mao() -> None:
    """Percentis do M-score entre -1, -2, -1 e -3: 0,875, 0,5, 0,875 e 0,25 (empate pela média); do DPO entre 10, 30 e
    20: 1/3, 1 e 2/3; do Benford entre 0,5 e 1,5: 0,5 e 1. Escores 0,875, 0,5, 1, 0,875, 1 e sem escore; o quantil de
    90% dos cinco avaliados é 1 (posição 3,6 entre 1 e 1): alerta para 3 e 5."""
    s, lim = escore.alerta(_sinais_para_o_escore(), escore.sinais_do_escore(com_benford=True))
    s = s.set_index("cd_cvm")
    assert np.allclose(s.loc[["1", "2", "4", "5"], "pct_mscore"], [0.875, 0.5, 0.875, 0.25])
    assert np.allclose(s.loc[["1", "3", "4"], "pct_dpo"], [1 / 3, 1.0, 2 / 3])
    assert np.allclose(s.loc[["1", "2", "3", "4", "5"], "escore"], [0.875, 0.5, 1.0, 0.875, 1.0])
    assert pd.isna(s.at["6", "escore"]) and not s.at["6", "avaliada"] and not s.at["8", "avaliada"]
    assert s.loc[["1", "2", "3", "4", "5", "6"], "n_sinais_calculaveis"].tolist() == [2, 2, 1, 2, 2, 0]
    assert s.at["2", "sinal_do_escore"] == "mscore;benford" and s.at["5", "sinal_do_escore"] == "benford"
    assert s.index[s.em_alerta].tolist() == ["3", "5", "7"]
    nf = lim[lim.grupo == AMOSTRA_NF].iloc[0]
    assert nf.limite_p90 == 1.0 and nf.n == 5
    assert pd.isna(s.at["7", "pct_mscore"]) and s.at["7", "escore"] == 1.0  # financeiras à parte
    pos = escore.posicoes_no_ranking(s.reset_index())
    assert dict(zip(s.index, pos.tolist())) == {"3": 0, "5": 1, "7": 2, "1": 3, "4": 4, "2": 5, "6": 6, "8": 7}


def test_sem_o_benford_o_escore_usa_os_sinais_do_v1() -> None:
    assert escore.sinais_do_escore(com_benford=False) == {AMOSTRA_NF: ("mscore", "dpo", "juro"),
                                                          AMOSTRA_FIN: ("peso_nao_recorrente",)}  # fmt: skip
    s, _ = escore.alerta(_sinais_para_o_escore(), escore.sinais_do_escore(com_benford=False))
    assert s.set_index("cd_cvm").at["5", "escore"] == 0.25


def test_mudancas_desligadas_sao_o_v1() -> None:
    s, contas, dep = _depi_do_exemplo()
    faltam = [c for c in motor.SINAIS_DAS_REGRAS if c not in s.columns]  # o v1 as cria antes dos alertas
    s = s.assign(**dict.fromkeys(faltam, np.nan))
    v1, lim1 = sinais_amostra.alertas(s)
    v2, lim2 = motor.calcula(s, contas, None, motor.NENHUMA)
    pd.testing.assert_frame_equal(v1, v2)
    pd.testing.assert_frame_equal(lim1, lim2)


@pytest.mark.skipif(not SINAIS_ESTUDO_1.exists(), reason="precisa de resultados/sinais_empresa_ano.csv")
def test_mudancas_desligadas_sobre_os_sinais_do_estudo_1() -> None:
    """Sobre os sinais gravados do estudo 1 (sem os alertas), o v2 desligado devolve os alertas do estudo 1."""
    estudo = pd.read_csv(SINAIS_ESTUDO_1, dtype={"cd_cvm": str}, low_memory=False)
    alertas = ["alerta_mscore", "alerta_dpo", "alerta_juro", "alerta_peso_nao_recorrente", "alerta_regra_boba",
               "avaliada", "em_alerta"]  # fmt: skip
    vazio = pd.DataFrame(columns=["cd_cvm", "dt_refer", "demonstracao", "ordem", "cd_conta", "ds_conta", "valor"])
    v2, _ = motor.calcula(estudo.drop(columns=alertas), vazio, None, motor.NENHUMA)
    for c in alertas:
        assert (v2[c].astype("boolean").fillna(False) == estudo[c].astype("boolean").fillna(False)).all(), c
        assert (v2[c].isna() == estudo[c].isna()).all(), c


def test_tudo_ligado_tira_os_alertas_por_sinal_do_v1() -> None:
    s, contas, dep = _depi_do_exemplo()
    r, lim = motor.calcula(s, contas, dep, motor.TODAS)
    assert not set(motor.ALERTAS_POR_SINAL_DO_V1) & set(r.columns) and "alerta_regra_boba" in r.columns
    assert set(lim.sinal) <= {"alavancagem", "escore"}
    assert bool(r.at[0, "avaliada"]) and bool(r.at[0, "marca_depreciacao_dva"])


# ---- separação: gabarito, métricas do estudo 1, produto e lacre ----

PROIBIDOS = (
    "chiocca.metricas", "chiocca.avaliacao", "chiocca.relatorio_resultados", "chiocca.textos_resultados",
    "chiocca.textos_resumo", "chiocca.robustez", "chiocca.descritiva", "chiocca.emenda5", "chiocca.americanas",
    "chiocca.v2.analises_pos_estudo_1", "chiocca.v2.estudo2.gabarito", "chiocca.v2.estudo2.secundaria",
)  # fmt: skip


def _modulos_do_pacote() -> list[str]:
    return sorted(f"chiocca.v2.motor_v2.{p.stem}" for p in PACOTE.glob("*.py") if p.stem != "__init__")


def test_codigo_do_v2_nao_le_o_gabarito_nem_importa_as_metricas() -> None:
    for p in sorted(PACOTE.glob("*.py")):
        arvore = ast.parse(p.read_text(encoding="utf-8"))
        importados = {a.name for n in ast.walk(arvore) if isinstance(n, ast.Import) for a in n.names}
        for n in ast.walk(arvore):
            if isinstance(n, ast.ImportFrom) and n.module:
                importados |= {n.module} | {f"{n.module}.{a.name}" for a in n.names}
        assert not {m for m in importados if m.startswith(PROIBIDOS)}, p.name
        assert "gabarito_casos" not in p.read_text(encoding="utf-8"), p.name


def test_nem_pelo_que_importa() -> None:
    """Num Python novo, importar todo o pacote do v2 não carrega nenhum módulo das métricas do estudo 1 nem do
    gabarito."""
    codigo = f"import sys\nfor m in {_modulos_do_pacote()!r}: __import__(m)\nprint('\\n'.join(sorted(sys.modules)))"
    carregados = subprocess.run([sys.executable, "-c", codigo], cwd=RAIZ, capture_output=True, text=True, check=True)
    assert not [m for m in carregados.stdout.split() if m.startswith(PROIBIDOS)]


def test_calculo_do_v2_nao_abre_o_gabarito(monkeypatch: pytest.MonkeyPatch) -> None:
    abertos: list[str] = []
    original = pd.read_csv

    def espia(caminho: Any, *a: Any, **k: Any) -> Any:
        abertos.append(str(caminho))
        return original(caminho, *a, **k)

    monkeypatch.setattr(pd, "read_csv", espia)
    s, contas, dep = _depi_do_exemplo()
    motor.calcula(s, contas, dep, motor.TODAS)
    sb, cb = _benford_do_exemplo()
    motor.aplica_benford(sb, cb)
    assert not [x for x in abertos if "gabarito" in x]


def test_produto_nao_importa_o_v2() -> None:
    """Só o pacote do v2 e as conferências dele, fora do pacote (`chiocca/v2/motor_v2_*.py`), importam o v2; o pacote
    não importa as conferências."""
    importa = re.compile(r"chiocca\.v2\.motor_v2(?![\w])|from chiocca\.v2 import [^\n]*\bmotor_v2(?![\w])")
    for p in sorted((RAIZ / "chiocca").rglob("*.py")):
        caminho, texto = p.relative_to(RAIZ).as_posix(), p.read_text(encoding="utf-8")
        if not caminho.startswith("chiocca/v2/motor_v2"):
            assert not importa.search(texto), caminho
        if caminho.startswith("chiocca/v2/motor_v2/"):
            assert "motor_v2_" not in texto, caminho


def test_lacre_do_v2_e_so_dele(monkeypatch: pytest.MonkeyPatch) -> None:
    """A constante da lista do v1 não abre nada para o v2; só a constante própria, no commit da sessão do lacre."""
    assert not hasattr(lacre, abertura.CONSTANTE) and abertura.exercicios_do_v2() == ()
    assert hasattr(lacre, "ESTUDO_2_EXERCICIOS")  # a do v1 existe e não vale para o v2
    for ano in (2024, 2025):
        with pytest.raises(lacre.ExercicioLacrado):
            abertura.garantir_exercicio(ano)
    assert abertura.garantir_exercicio(2023) == 2023
    monkeypatch.setattr(lacre, abertura.CONSTANTE, (2024, 2025), raising=False)
    assert abertura.garantir_exercicio(2025) == 2025
    with pytest.raises(lacre.ExercicioLacrado):
        abertura.garantir_exercicio(2026)
    for p in sorted((RAIZ / "chiocca").rglob("*.py")):
        caminho, texto = p.relative_to(RAIZ).as_posix(), p.read_text(encoding="utf-8")
        if caminho.startswith("chiocca/v2/motor_v2/"):
            assert "ESTUDO_2_EXERCICIOS" not in texto, caminho
        elif caminho != "chiocca/v2/lacre.py":
            assert abertura.CONSTANTE not in texto, caminho


class FontesProibidas:
    def __getattr__(self, nome: str) -> Any:
        raise AssertionError(f"leitura de dados antes do lacre: {nome}")


def test_lista_e_dva_recusam_exercicio_lacrado_antes_de_ler() -> None:
    for ano in (2024, 2025):
        with pytest.raises(lacre.ExercicioLacrado):
            lista.calcular(FontesProibidas(), [ano])  # type: ignore[arg-type]
        with pytest.raises(lacre.ExercicioLacrado):
            dva.le(RAIZ / "nao-existe", ano)


def test_registro_do_v1_nao_tem_arquivo_do_v2() -> None:
    gravado = json.loads((RAIZ / "docs" / "estudo_2_codigo_congelado.json").read_text(encoding="utf-8"))
    for conjunto in gravado["conjuntos"].values():
        assert not [c for c in conjunto if "motor_v2" in c]


# ---- a lista do v2, com dados sintéticos ----


def _gerar(f: Fontes) -> bytes:
    return lista.gerar(f, [2020], "0" * 40, "3.13", "1" * 64)


def _corpo(conteudo: bytes) -> str:
    return "\n".join(x for x in conteudo.decode("utf-8").split("\n") if not x.startswith("#"))


def test_lista_desligada_igual_a_lista_do_v1(mundo: Fontes) -> None:  # noqa: F811
    v1 = lista_v1.calcular(mundo, [2020]).set_index(["cd_cvm", "dt_refer"])
    v2 = lista.calcular(mundo, [2020], motor.NENHUMA).set_index(["cd_cvm", "dt_refer"])
    assert list(v1.index) == list(v2.index)
    for col in [c for c in lista_v1.COLUNAS_ESTUDO_1 if c in v1.columns and c not in ("cd_cvm", "dt_refer")]:
        for k in v1.index:
            assert lista_v1.celula(col, v1.at[k, col]) == lista_v1.celula(col, v2.at[k, col]), (k, col)


def test_lista_do_v2_formato_e_reprodutivel(mundo: Fontes) -> None:  # noqa: F811
    conteudo = _gerar(mundo)
    t = conteudo.decode("utf-8")
    assert "\r" not in t and t.endswith("\n") and date.today().isoformat() not in t
    cab = [x for x in t.split("\n") if x.startswith("#")]
    assert cab[:4] == [lista.TITULO, f"# commit: {'0' * 40}", "# python: 3.13", f"# requirements-lock.txt: {'1' * 64}"]
    corpo = pd.read_csv(io.StringIO(_corpo(conteudo)), dtype=str, keep_default_na=False)
    assert list(corpo.columns) == lista.COLUNAS
    assert not set(motor.ALERTAS_POR_SINAL_DO_V1) & set(corpo.columns)
    assert all(re.fullmatch(r"\d\.\d{12}", x) for x in corpo.escore if x)
    assert (corpo.avaliada[corpo.escore != ""] == "1").all() and (corpo.avaliada[corpo.escore == ""] != "1").all()
    assert _gerar(Fontes(mundo.pasta, mundo.cache_enet)) == conteudo
    lida = lista.ler(conteudo)
    assert _corpo(lista.texto(lida, "0" * 40, "3.13", "1" * 64, [])) == _corpo(conteudo)


def test_celula_do_v2() -> None:
    assert lista.celula("escore", 0.9) == "0.900000000000" and lista.celula("benford", -0.0000001) == "0.000000"
    assert lista.celula("marca_depreciacao_dva", True) == "1" and lista.celula("n_sinais_calculaveis", 2.0) == "2"
    assert lista.celula("mscore", -1.5) == "-1.500000" and lista.celula("pct_dpo", float("nan")) == ""


# ---- invariante (item 3, com o armazém, fora do CI; aqui, o registro do resultado) ----


def test_invariante_registrado() -> None:
    """Com as três mudanças desligadas, a lista do v2 sobre o armazém é igual ao estudo 1 nas 9.474 empresa-anos de 2010
    a 2023, em todas as colunas comparadas pelo invariante do v1 (`docs/motor_v2_invariante.json`)."""
    d = json.loads((RAIZ / "docs" / "motor_v2_invariante.json").read_text(encoding="utf-8"))
    v1 = json.loads((RAIZ / "docs" / "invariante_numeros.json").read_text(encoding="utf-8"))["exercicios"]
    assert d["mudancas"] == {"depi_dva": False, "benford": False, "escore": False}
    assert d["codigo_sem_alteracao_local"] is True and re.fullmatch(r"[0-9a-f]{40}", d["commit"])
    t = d["total"]
    assert t["empresa_anos_estudo"] == t["empresa_anos_v2"] == t["empresa_anos_iguais"] == 9474
    assert t["empresa_anos_iguais"] == sum(r["empresa_anos_iguais"] for r in v1.values())
    assert t["colunas_com_diferenca"] == [] and t["exercicios_com_as_mesmas_empresa_anos"] == 14
    assert set(d["exercicios"]) == {str(a) for a in range(2010, 2024)}
    for ano, r in d["exercicios"].items():
        assert r["empresa_anos_iguais"] == r["empresa_anos_estudo"] == v1[ano]["empresa_anos_iguais"], ano
        assert r["colunas_comparadas"] == v1[ano]["colunas_comparadas"] and not r["colunas_com_diferenca"], ano
