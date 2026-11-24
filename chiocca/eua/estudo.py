"""O estudo dos EUA (pré-registro dos EUA, registrado em 24/11/2026, commit a527b9e): os motores v1 e v2 congelados no
Brasil, e a regra boba, contra o 8-K com o item 4.02 nos 12 meses depois do corte.

O script só monta as entradas de cada empresa-ano a partir do XBRL (`chiocca.eua.mapa`) e aplica as adaptações da seção
3; os sinais, os alertas e as medidas são as funções congeladas, chamadas sem mudar nenhuma linha:
- os sinais do v1: `chiocca.sinais.mscore.calcula`, `dpo.variacao`, `juro_implicito.juro` e `spread_pp`,
  `lucro_sem_caixa.accruals` (só na ficha), com a taxa média de `chiocca.cdi.medio` sobre a série DFF
  (`data/eua_dff.csv`);
- os alertas: `chiocca.v2.motor_v2.motor.calcula`, com as mudanças desligadas (o v1, que é `sinais_amostra.alertas`) e
  com o Benford e o escore ligados e o DEPI pela DVA desligado (o v2: a DVA não existe nos EUA, seção 3.1);
- a data de corte: `chiocca.corte.data_corte`;
- as medidas: `taxas`, `dr`, `bootstrap_por_companhia`, `limite_inferior`, `ranking`, `ordem_do_motor` e
  `ordem_da_regra_boba` de `chiocca/v2/estudo2/secundaria.py`, e `escore.posicoes_no_ranking` do v2.

Regras de implementação que o texto registrado não detalha (as de (i) a (vi) estão em `chiocca.eua.mapa` e no exemplo
calculado à mão, `tests/referencia/gerar_exemplo_eua.py`):
(iii)  empresa-ano: a companhia (CIK) e a data de referência (`period`) de um 10-K original com data de referência de
       2011 a 2024; o exercício é o ano da data de referência. A versão pública no corte: entre os 10-K e os 10-K/A da
       mesma companhia e da mesma data de referência com pelo menos um valor de uma tag do mapa nessa data, a última
       entregue até o corte (no mesmo dia, a de maior número de entrega). A SIC é a dessa entrega;
(v)    ordem de entrada (empates de quantidade nas faixas do Benford): pelo CIK, crescente, e pela data de referência;
(vii)  episódio na janela: a empresa-ano é positiva se um episódio se abre depois do corte e até o último dia do mesmo
       mês do ano seguinte (12 meses). Se as janelas de duas empresa-anos da mesma companhia se cruzam (troca da data de
       fim do exercício), o episódio fica com a de corte mais recente antes dele, e cada episódio cai em no máximo uma
       empresa-ano. As janelas são as das não financeiras da amostra;
(viii) os exercícios de 2009 e 2010 são calculados só para a descrição dos AAERs (seção 8), com as mesmas regras; as
       medidas e as contagens da amostra são de 2011 a 2024;
(ix)   "sem nenhum sinal calculável" (exclusão 5): não avaliada pelo v1 nem pelo v2. As medidas são nas avaliadas pelo
       v1 (seção 6); as que só o v2 avalia ficam à parte, só contadas.

O cálculo único (`main`) só começa com a autorização de Roberto, depois do PR e da release do congelamento: exige a
opção `--calculo-unico`, o registro de SHA-256 do estudo conferido (`docs/eua_codigo_congelado.json`), os arquivos da
SEC baixados de novo no dia, conferidos pelo manifesto, e não regrava um resultado que já existe. Só agregados vão para
o resultado versionado; a tabela por empresa-ano fica em `resultados/eua/`, fora do Git, e nenhuma lista de companhias
por alerta é publicada. Alerta, não acusação; nada disso é chamado de fraude.

Uso, no dia do cálculo único, com a autorização de Roberto:
  python -m chiocca.eua.estudo --calculo-unico
"""

from __future__ import annotations

import argparse
import calendar
import io
import json
import subprocess
import sys
import zipfile
from collections.abc import Callable, Iterable, Mapping
from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from chiocca import cdi, sinais_amostra
from chiocca.base import RAIZ
from chiocca.corte import data_corte
from chiocca.eua import fsds, itens, mapa, rotulos, sec
from chiocca.sinais import dpo, juro_implicito, lucro_sem_caixa, mscore
from chiocca.sinais.resultado import NaoCalculavel, Resultado, conta, divide
from chiocca.v2.estudo2 import secundaria
from chiocca.v2.estudo2.registro import sha256_registrado
from chiocca.v2.motor_v2 import benford, escore, motor
from chiocca.variaveis import ULTIMO

EXERCICIOS = range(2011, 2025)  # seção 4
EXERCICIOS_AAER = range(2009, 2015)  # seção 8
EXERCICIOS_CALCULADOS = range(EXERCICIOS_AAER.start, EXERCICIOS.stop)
FORMULARIOS = ("10-K", "10-K/A")
SEMENTE = 20270430  # decisão de Roberto de 24/11/2026
REAMOSTRAGENS = 10_000
DIAS_DO_EPISODIO = 365
ULTIMA_DATA_8K = itens.ULTIMA_DATA
V1 = motor.NENHUMA
V2 = motor.Mudancas(depi_dva=False, benford=True, escore=True)
BRACOS = ("v1", "v2", "boba")

AMOSTRA_NF = sinais_amostra.AMOSTRA_NF
FORA_SEM_VERSAO = "fora_sem_versao_publica"
FORA_FINANCEIRA = "fora_financeira"
FORA_SPAC = "fora_spac"
FORA_SEM_RECEITA = sinais_amostra.FORA_SEM_RECEITA
SIC_SPAC = "6770"

TAXA = RAIZ / "data" / "eua_dff.csv"
REGISTRO = RAIZ / "docs" / "eua_codigo_congelado.json"
SAIDA = RAIZ / "docs" / "eua_resultado.json"
TABELA = RAIZ / "resultados" / "eua" / "empresa_anos.csv.gz"
COLUNAS_SUB = ["adsh", "cik", "sic", "form", "period", "filed"]
NUMERICAS = (*mscore.COEFICIENTES, "mscore", "dpo_t", "dpo_t1", "dpo", "taxa_media", "juro_implicito", "juro",
             "lucro_sem_caixa", "alavancagem")  # fmt: skip


# ---- as entregas: o que cada 10-K e 10-K/A traz ----


@dataclass
class Entregas:
    """As entregas (`sub`) e, de cada uma, os valores das tags do mapa, a data de t-1 e os números do Benford."""

    sub: pd.DataFrame
    valores: dict[str, dict[tuple[str, str, str], float]] = field(default_factory=dict)
    anterior: dict[str, str | None] = field(default_factory=dict)
    benford: pd.DataFrame = field(default_factory=lambda: pd.DataFrame(columns=["adsh", "demonstracao", "valor"]))


def do_exercicio(sub: pd.DataFrame, exercicios: range = EXERCICIOS_CALCULADOS) -> pd.DataFrame:
    """Os 10-K e 10-K/A com data de referência nos exercícios pedidos."""
    p = sub.period.astype(str)
    ok = sub.form.isin(FORMULARIOS) & p.str.fullmatch(r"\d{8}") & p.str[:4].isin([str(a) for a in exercicios])
    return sub.loc[ok, COLUNAS_SUB].astype(str).reset_index(drop=True)


def extrai(sub: pd.DataFrame, num: pd.DataFrame, pre: pd.DataFrame, contagem: pd.Series | None = None) -> Entregas:
    """As entregas de `sub` (já filtradas por `do_exercicio`) com os números de `num.txt` e `pre.txt`."""
    periodos = dict(zip(sub.adsh, sub.period))
    num = num[num.adsh.isin(periodos)]
    pre = pre[pre.adsh.isin(periodos)]
    contagem = mapa.contagem_de_datas(num) if contagem is None else contagem
    return Entregas(sub=sub.reset_index(drop=True), valores=mapa.valores_do_mapa(num),
                    anterior=mapa.datas_anteriores(contagem, periodos),
                    benford=mapa.numeros_do_benford(num, pre, periodos))  # fmt: skip


def junta(partes: Iterable[Entregas]) -> Entregas:
    partes = list(partes)
    if not partes:
        return Entregas(sub=pd.DataFrame(columns=COLUNAS_SUB))
    out = Entregas(sub=pd.concat([p.sub for p in partes], ignore_index=True),
                   benford=pd.concat([p.benford for p in partes], ignore_index=True))  # fmt: skip
    for p in partes:
        out.valores.update(p.valores)
        out.anterior.update(p.anterior)
    return out


def le_trimestre(zip_caminho: Path, exercicios: range = EXERCICIOS_CALCULADOS, bloco: int = 1_000_000) -> Entregas:
    """Um trimestre dos Financial Statement Data Sets: as colunas conferidas antes de qualquer conta (`fsds.exige`)."""
    with zipfile.ZipFile(zip_caminho) as z:
        sub = pd.read_csv(io.BytesIO(z.read("sub.txt")), sep="\t", dtype=str, keep_default_na=False)
        fsds.exige(sub.columns, COLUNAS_SUB, f"{zip_caminho.name}/sub.txt")
        sub = do_exercicio(sub, exercicios)
        alvo, periodos = set(sub.adsh), dict(zip(sub.adsh, sub.period))
        partes_num: list[pd.DataFrame] = []
        partes_pre: list[pd.DataFrame] = []
        contagens: list[pd.Series] = []
        for nome, colunas, partes in (("num.txt", mapa.COLUNAS_NUM, partes_num),
                                      ("pre.txt", mapa.COLUNAS_PRE, partes_pre)):  # fmt: skip
            with z.open(nome) as f:
                cabecalho = f.readline().decode("utf-8").rstrip("\r\n").split("\t")
            fsds.exige(cabecalho, colunas, f"{zip_caminho.name}/{nome}")
            for b in pd.read_csv(z.open(nome), sep="\t", dtype=str, keep_default_na=False, usecols=colunas,
                                 chunksize=bloco, quoting=3):  # fmt: skip
                b = b[b.adsh.isin(alvo)]
                if nome == "num.txt":
                    contagens.append(mapa.contagem_de_datas(b))
                    na_data = b.ddate.to_numpy() == b.adsh.map(periodos).to_numpy()
                    b = b[b.tag.isin(mapa.TAGS_DO_MAPA) | na_data]
                partes.append(b[colunas])
    num = pd.concat(partes_num, ignore_index=True) if partes_num else pd.DataFrame(columns=mapa.COLUNAS_NUM)
    pre = pd.concat(partes_pre, ignore_index=True) if partes_pre else pd.DataFrame(columns=mapa.COLUNAS_PRE)
    contagem = pd.concat(contagens).groupby(level=[0, 1]).sum() if contagens else pd.Series(dtype=int)
    return extrai(sub, num, pre, contagem)


# ---- a amostra: a versão pública no corte e as exclusões ----


def _iso(aaaammdd: str) -> str:
    return f"{aaaammdd[:4]}-{aaaammdd[4:6]}-{aaaammdd[6:8]}"


def financeira(sic: str) -> bool:
    return sic.isdigit() and 6000 <= int(sic) <= 6999 and sic != SIC_SPAC


def versoes(e: Entregas) -> pd.DataFrame:
    """Uma linha por empresa-ano (CIK e data de referência de um 10-K original): o corte, a versão usada (ou nenhuma) e
    a situação pelas exclusões (1) a (3), na ordem (seção 4)."""
    s = e.sub
    universo = s[s.form == "10-K"].drop_duplicates(["cik", "period"])[["cik", "period"]]
    com_numeros = [f == "10-K" or mapa.tem_numero_do_mapa(e.valores.get(a, {}), p)
                   for a, f, p in zip(s.adsh, s.form, s.period)]  # fmt: skip
    candidatas = s[np.array(com_numeros, dtype=bool)]
    por_ano = {k: g for k, g in candidatas.groupby(["cik", "period"], sort=False)}
    n_entregas = s.groupby(["cik", "period"], sort=False).size().to_dict()
    linhas = []
    for cik, periodo in sorted(zip(universo.cik, universo.period), key=lambda x: (int(x[0]), x[1])):
        corte = data_corte(_iso(periodo))
        g = por_ano.get((cik, periodo))
        ate = g[g.filed <= corte.strftime("%Y%m%d")] if g is not None else None
        linha: dict[str, Any] = {"cd_cvm": str(int(cik)), "cik": cik, "periodo": periodo, "dt_refer": _iso(periodo),
                                 "exercicio": int(periodo[:4]), "data_corte": corte.isoformat(),
                                 "entregas": int(n_entregas[(cik, periodo)])}  # fmt: skip
        if ate is None or ate.empty:
            linha |= {"versao": None, "form": None, "sic": None, "amostra": FORA_SEM_VERSAO}
        else:
            usada = ate.sort_values(["filed", "adsh"]).iloc[-1]
            sic = str(usada.sic)
            linha |= {"versao": usada.adsh, "form": usada.form, "sic": sic,
                      "amostra": FORA_FINANCEIRA if financeira(sic) else FORA_SPAC if sic == SIC_SPAC
                      else None}  # fmt: skip
        linhas.append(linha)
    return pd.DataFrame(linhas)


# ---- os sinais do v1 em cada empresa-ano (as funções congeladas) ----


def _r(prefixo: str, r: Resultado) -> dict[str, Any]:
    return {prefixo: r.valor, f"{prefixo}_motivo": r.motivo}


def _dpo_de(v: Mapping[str, float | None], rotulo: str) -> float | None:
    try:
        return dpo.dpo(v, rotulo)
    except NaoCalculavel:
        return None


def alavancagem(t: Mapping[str, float | None]) -> Resultado:
    """Regra boba (seção 6): passivo total ÷ ativo total."""
    try:
        return Resultado(divide(conta(t, "passivo_total"), conta(t, "ativo_total"), "ativo total"))
    except NaoCalculavel as x:
        return Resultado(None, f"{x.motivo}:{x.detalhe}")


def sinais(t: Mapping[str, float | None], t1: Mapping[str, float | None], dt_refer: str,
           taxa: Path = TAXA) -> dict[str, Any]:  # fmt: skip
    """Os sinais do v1 de uma não financeira, pelas funções congeladas, com a taxa média do ano no lugar do CDI."""
    linha: dict[str, Any] = {}
    m = mscore.calcula(t, t1)
    for nome, r in m.componentes.items():
        linha.update(_r(nome, r))
    linha.update(_r("mscore", m.m))
    linha["dpo_t"], linha["dpo_t1"] = _dpo_de(t, "t"), _dpo_de(t1, "t-1")
    linha.update(_r("dpo", dpo.variacao(t, t1)))
    j = juro_implicito.juro(t, t1)
    media = cdi.medio(dt_refer, caminho=taxa)
    linha["taxa_media"], linha["juro_implicito"] = media, j.valor
    if j.valor is None:
        linha.update(_r("juro", Resultado(None, j.motivo)))
    elif media is None:
        linha.update(_r("juro", Resultado(None, "taxa_ausente")))
    else:
        linha.update(_r("juro", Resultado(juro_implicito.spread_pp(j.valor, media))))
    linha.update(_r("lucro_sem_caixa", lucro_sem_caixa.accruals(t, t1)))
    linha.update(_r("alavancagem", alavancagem(t)))
    return linha


@dataclass
class EmpresaAnos:
    """A tabela das empresa-anos (`s`, a entrada dos motores) e as contas do Benford (`contas`), mais o detalhe do mapa
    de cada uma (`detalhe`: contas de t e t-1, origem e marcas), que não vai para nenhum arquivo versionado."""

    s: pd.DataFrame
    contas: pd.DataFrame
    detalhe: dict[tuple[str, str], dict[str, Any]]


def empresa_anos(e: Entregas, taxa: Path = TAXA) -> EmpresaAnos:
    """Sinais de cada empresa-ano, na ordem de entrada (CIK e data de referência), com a exclusão (4)."""
    v = versoes(e)
    linhas, detalhe, benford = [], {}, []
    numeros = {a: g for a, g in e.benford.groupby("adsh", sort=False)}
    for r in v.to_dict("records"):
        if not pd.isna(r["versao"]):
            valores = e.valores.get(r["versao"], {})
            anterior = e.anterior.get(r["versao"])
            t, origem, marcas = mapa.contas(valores, r["periodo"])
            t1, _, marcas1 = mapa.contas(valores, anterior)
            detalhe[(r["cd_cvm"], r["dt_refer"])] = {"data_anterior": anterior, "contas_t": t, "contas_t1": t1,
                                                     "origem_t": origem,
                                                     "marcas": sorted(set(marcas + marcas1))}  # fmt: skip
            r["data_anterior"] = anterior
            r["marca_juros_largo"] = mapa.MARCA_JUROS in marcas + marcas1
            r["marca_fornecedores_largo"] = mapa.MARCA_FORNECEDORES in marcas + marcas1
            if pd.isna(r["amostra"]):
                r["amostra"] = FORA_SEM_RECEITA if not t["receita_liquida"] else AMOSTRA_NF
            if r["amostra"] == AMOSTRA_NF:
                r |= sinais(t, t1, r["dt_refer"], taxa)
                b = numeros.get(r["versao"], e.benford.iloc[:0])
                benford.append(pd.DataFrame({"cd_cvm": r["cd_cvm"], "dt_refer": r["dt_refer"],
                                             "demonstracao": b.demonstracao.to_numpy(), "ordem": ULTIMO,
                                             "valor": b.valor.to_numpy()}))  # fmt: skip
        linhas.append(r)
    s = pd.DataFrame(linhas)
    for col in NUMERICAS:
        s[col] = s[col].astype(float) if col in s.columns else np.nan
    contas = (pd.concat(benford, ignore_index=True) if benford
              else pd.DataFrame(columns=["cd_cvm", "dt_refer", "demonstracao", "ordem", "valor"]))  # fmt: skip
    return EmpresaAnos(s=s.reset_index(drop=True), contas=contas, detalhe=detalhe)


# ---- os alertas do v1 e do v2 (o motor congelado) ----


def motores(ea: EmpresaAnos) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Os alertas do v1 e do v2 em cada empresa-ano, lado a lado, e os limites de cada exercício. A avaliação e o alerta
    do v2 levam o sufixo `_v2` (`avaliada_v2`, `em_alerta_v2`); as colunas que só o v2 tem (Benford, percentis e
    escore) vêm sem sufixo; a contagem de cada primeiro dígito sai de `benford.contagens`, a mesma função que o motor
    usa; `n_sinais` é o número de sinais do v1 disparados (a ordem do motor do estudo 2)."""
    s = ea.s
    v1, lim1 = motor.calcula(s, ea.contas, None, V1)
    v2, lim2 = motor.calcula(s, ea.contas, None, V2)
    out = v1.copy()
    out["n_sinais"] = out[["alerta_mscore", "alerta_dpo", "alerta_juro"]].fillna(False).astype(int).sum(axis=1)
    novas = ["n_numeros_benford", "desvio_benford", "faixa_benford", "benford", "benford_motivo",
             *(f"pct_{x}" for x in escore.TODOS_OS_SINAIS), "escore", "n_sinais_calculaveis",
             "sinal_do_escore"]  # fmt: skip
    for col in novas:
        out[col] = v2[col].to_numpy()
    digitos = benford.contagens(ea.contas).set_index(motor.CHAVE)[benford.DIGITOS]
    pares = pd.MultiIndex.from_arrays([out.cd_cvm, out.dt_refer])
    for col in benford.DIGITOS:
        out[col] = digitos[col].reindex(pares).to_numpy()
    out["avaliada_v2"], out["em_alerta_v2"] = v2.avaliada.to_numpy(bool), v2.em_alerta.to_numpy(bool)
    limites = pd.concat([lim1.assign(motor="v1"), lim2.assign(motor="v2")], ignore_index=True)
    return out, limites


# ---- o desfecho: episódios de 8-K com o item 4.02 ----


def episodios(datas: Mapping[str, Iterable[str]], ultima: str = ULTIMA_DATA_8K) -> pd.DataFrame:
    """Os episódios de cada companhia (seção 5): o primeiro 8-K com o item 4.02 abre um; os 8-K e 8-K/A com o item nos
    365 dias seguintes pertencem a ele; depois disso, um novo abre outro. Só as entregas até `ultima` (AAAA-MM-DD)."""
    linhas: list[tuple[str, date, int]] = []
    for cik, ds in datas.items():
        aberto: date | None = None
        for d in sorted({date.fromisoformat(x[:10]) for x in ds if x[:10] <= ultima}):
            if aberto is None or (d - aberto).days > DIAS_DO_EPISODIO:
                aberto = d
                linhas.append((str(int(cik)), d, 0))
            linhas[-1] = (linhas[-1][0], linhas[-1][1], linhas[-1][2] + 1)
    return pd.DataFrame(linhas, columns=["cd_cvm", "abertura", "dias_com_8k"])


def fim_da_janela(corte: date) -> date:
    """O último dia do mesmo mês do ano seguinte: 12 meses depois do corte (que é sempre o último dia de um mês)."""
    return date(corte.year + 1, corte.month, calendar.monthrange(corte.year + 1, corte.month)[1])


def desfecho(s: pd.DataFrame, ep: pd.DataFrame) -> tuple[pd.Series, pd.DataFrame]:
    """A empresa-ano positiva (regra (vii)) e cada episódio com a empresa-ano em que caiu (ou nenhuma)."""
    janelas: dict[str, list[tuple[date, date, int]]] = {}
    for i, cd, c in zip(s.index, s.cd_cvm, s.data_corte):
        corte = date.fromisoformat(c)
        janelas.setdefault(str(cd), []).append((corte, fim_da_janela(corte), i))
    positiva = pd.Series(False, index=s.index)
    caiu: list[Any] = []
    for cd, aberto in zip(ep.cd_cvm, ep.abertura):
        dentro = [(c, i) for c, f, i in janelas.get(str(cd), []) if c < aberto <= f]
        if dentro:
            i = max(dentro)[1]
            positiva.at[i] = True
            caiu.append(i)
        else:
            caiu.append(None)
    return positiva, ep.assign(empresa_ano=caiu)


def datas_dos_8k(linhas: Iterable[dict[str, Any]]) -> dict[str, list[str]]:
    """As datas dos 8-K e 8-K/A com o item 4.02 de cada companhia (`itens.entregas`)."""
    out: dict[str, list[str]] = {}
    for x in linhas:
        if x["form"] in ("8-K", "8-K/A") and itens.tem_item(x["itens"]):
            out.setdefault(str(int(x["cik"])), []).append(x["data"])
    return out


# ---- as medidas (seção 6), pelas funções congeladas do estudo 2 ----


def _dr_nas_linhas(alerta: np.ndarray, y: np.ndarray) -> Callable[[np.ndarray], float]:
    return lambda i: secundaria.dr(alerta[i], y[i])


def _rr_nas_linhas(alerta: np.ndarray, y: np.ndarray) -> Callable[[np.ndarray], float]:
    return lambda i: float(secundaria.taxas(alerta[i], y[i])["rr"])


def _resultado(limite: float | None, sim: str, nao: str) -> str:
    return sim if limite is not None and limite > 0 else nao


def medidas(nf: pd.DataFrame, reamostragens: int = REAMOSTRAGENS, semente: int = SEMENTE) -> dict[str, Any]:
    """A DR e a razão de taxas do v1, do v2 e da regra boba, as diferenças pareadas (cada motor contra a regra boba e o
    v2 contra o v1) e as métricas de ranking, nas empresa-anos de `nf` (as não financeiras avaliadas pelo v1), com um
    bootstrap por companhia só, pareado entre os três."""
    nf = nf.reset_index(drop=True)
    if nf.empty:
        return {"empresa_anos": 0, "companhias": 0}
    y = nf.positiva.to_numpy(bool)
    alerta = {"v1": nf.em_alerta.to_numpy(bool), "v2": nf.em_alerta_v2.to_numpy(bool),
              "boba": nf.alerta_regra_boba.astype("boolean").fillna(False).to_numpy(bool)}  # fmt: skip
    posicao = {"v1": secundaria.ordem_do_motor(nf), "v2": escore.posicoes_no_ranking(nf),
               "boba": secundaria.ordem_da_regra_boba(nf)}  # fmt: skip
    estat: dict[str, Callable[[np.ndarray], float]] = {}
    for braco in BRACOS:
        estat[f"dr_{braco}"] = _dr_nas_linhas(alerta[braco], y)
        estat[f"rr_{braco}"] = _rr_nas_linhas(alerta[braco], y)
        for p in secundaria.TOPOS:
            for m in ("precisao", "lift", "ndcg"):
                estat[f"{m}_{p}_{braco}"] = secundaria._estatistica_de_ranking(posicao[braco], y, p, m)
    pontual = {nome: f(np.arange(len(nf))) for nome, f in estat.items()}
    b = secundaria.bootstrap_por_companhia(nf.cd_cvm.to_numpy(str), estat, reamostragens, semente)
    lim = secundaria.limite_inferior
    out: dict[str, Any] = {"empresa_anos": len(nf), "companhias": int(nf.cd_cvm.nunique()),
                           "reamostragens": reamostragens, "semente": semente,
                           "reamostragens_sem_dr": {x: int(np.isnan(b[f"dr_{x}"]).sum()) for x in BRACOS}}  # fmt: skip
    for braco in BRACOS:
        l_dr = lim(b[f"dr_{braco}"])
        out[braco] = secundaria.taxas(alerta[braco], y) | {
            "dr_limite_inferior_95": l_dr, "rr_limite_inferior_95": lim(b[f"rr_{braco}"]),
            "resultado": _resultado(l_dr, "associação positiva", "sem evidência de associação")}  # fmt: skip
    for a, c, sim in (("v1", "boba", "o v1 separa melhor que a regra boba"),
                      ("v2", "boba", "o v2 separa melhor que a regra boba"),
                      ("v2", "v1", "o v2 separa melhor que o v1")):  # fmt: skip
        l_dif = lim(b[f"dr_{a}"] - b[f"dr_{c}"])
        out[f"{a}_menos_{'regra_boba' if c == 'boba' else c}"] = {
            "diferenca_dr": pontual[f"dr_{a}"] - pontual[f"dr_{c}"], "limite_inferior_95": l_dif,
            "resultado": _resultado(l_dif, sim, "sem vencedor declarado")}  # fmt: skip
    rank: dict[str, Any] = {}
    for p in secundaria.TOPOS:
        chave = f"{round(p * 100)}%"
        rank[chave] = {"k": secundaria.topo(p, len(nf))}
        for m in ("precisao", "lift", "ndcg"):
            rank[chave][m] = {x: {"valor": pontual[f"{m}_{p}_{x}"], "limite_inferior_95": lim(b[f"{m}_{p}_{x}"])}
                              for x in BRACOS}  # fmt: skip
    out["ranking"] = rank
    return secundaria._num(out)


def por_exercicio(s: pd.DataFrame) -> dict[str, Any]:
    """Descritivas de cada exercício (só agregados): as exclusões, as avaliadas, a taxa de alerta de cada motor e a da
    regra boba, a taxa do desfecho e as taxas de cada braço."""
    out: dict[str, Any] = {}
    for ano, g in s.groupby("exercicio", sort=True):
        nf = g[g.amostra == AMOSTRA_NF]
        a1, a2 = nf.avaliada.astype(bool), nf.avaliada_v2.astype(bool)
        av1, av2 = nf[a1], nf[a2]
        y = av1.positiva.to_numpy(bool)
        out[str(int(ano))] = {
            "empresa_anos": len(g), **{k: int((g.amostra == k).sum()) for k in
                                       (FORA_SEM_VERSAO, FORA_FINANCEIRA, FORA_SPAC, FORA_SEM_RECEITA)},
            "nao_financeiras": len(nf), "sem_nenhum_sinal": int((~a1 & ~a2).sum()), "avaliadas_v1": len(av1),
            "avaliadas_v2": len(av2), "so_o_v2_avalia": int((~a1 & a2).sum()),
            "taxa_de_alerta_v1": float(av1.em_alerta.mean()) if len(av1) else None,
            "taxa_de_alerta_v2": float(av2.em_alerta_v2.mean()) if len(av2) else None,
            "taxa_do_desfecho": float(y.mean()) if len(av1) else None,
            "v1": secundaria.taxas(av1.em_alerta.to_numpy(bool), y),
            "v2": secundaria.taxas(av1.em_alerta_v2.to_numpy(bool), y),
            "boba": secundaria.taxas(av1.alerta_regra_boba.astype("boolean").fillna(False).to_numpy(bool), y),
        }  # fmt: skip
    return secundaria._num(out)


# ---- os AAERs de 2009 a 2014 (seção 8): só contagens ----


def aaers(s: pd.DataFrame, firmas: pd.DataFrame, ligacoes: pd.DataFrame,
          anos: range = EXERCICIOS_AAER) -> dict[str, Any]:  # fmt: skip
    """Para os casos de Bao et al. com empresa-anos afetadas de 2009 a 2014 (ano pela convenção da Compustat, ligadas ao
    CIK pela tabela do era-py), quantos têm uma empresa-ano calculada, quantos uma não financeira avaliada pelo v1, e
    quantos o v1, o v2 e a regra boba alertaram em pelo menos um exercício afetado. Só contagens, sem lista."""
    linhas = [(p, g, a) for p, g, ini, fim in zip(firmas.p_aaer, firmas.gvkey, firmas.min_year, firmas.max_year)
              for a in range(max(int(ini), anos.start), min(int(fim), anos.stop - 1) + 1)]  # fmt: skip
    t = pd.DataFrame(linhas, columns=["p_aaer", "gvkey", "ano"])
    t["ciks"] = rotulos.ciks_ligados(t, ligacoes) if len(t) else pd.Series(dtype=object)
    calc = s.assign(ano=fsds.ano_compustat(s.periodo.astype(str)).astype(int))
    por_chave: dict[tuple[str, int], list[int]] = {}
    for i, cd, a in zip(calc.index, calc.cd_cvm, calc.ano):
        por_chave.setdefault((str(cd), int(a)), []).append(i)
    casos: dict[str, dict[str, bool]] = {}
    for p, cs, a in zip(t.p_aaer, t.ciks, t.ano):
        idx = [i for c in cs for i in por_chave.get((str(int(c)), int(a)), [])]
        caso = casos.setdefault(str(p), {"calculado": False, "avaliado_v1": False, "v1": False, "v2": False,
                                         "boba": False})  # fmt: skip
        for i in idx:
            r = calc.loc[i]
            caso["calculado"] = True
            if r.amostra == AMOSTRA_NF and bool(r.avaliada):
                caso["avaliado_v1"] = True
                caso["v1"] |= bool(r.em_alerta)
                caso["v2"] |= bool(r.em_alerta_v2)
                caso["boba"] |= bool(pd.notna(r.alerta_regra_boba) and r.alerta_regra_boba)
    c = (
        pd.DataFrame(casos.values())
        if casos
        else pd.DataFrame(columns=["calculado", "avaliado_v1", "v1", "v2", "boba"])
    )
    return {"casos_com_anos_afetados": len(c), "casos_com_empresa_ano_calculada": int(c.calculado.sum()),
            "casos_com_nao_financeira_avaliada_pelo_v1": int(c.avaliado_v1.sum()),
            "casos_em_alerta_v1": int(c.v1.sum()), "casos_em_alerta_v2": int(c.v2.sum()),
            "casos_em_alerta_regra_boba": int(c.boba.sum())}  # fmt: skip


# ---- o estudo inteiro ----


def calcula(e: Entregas, datas_8k: Mapping[str, Iterable[str]], firmas: pd.DataFrame, ligacoes: pd.DataFrame,
            taxa: Path = TAXA, reamostragens: int = REAMOSTRAGENS, semente: int = SEMENTE,
            ) -> tuple[dict[str, Any], pd.DataFrame]:  # fmt: skip
    """O resultado agregado (o que vai para `docs/eua_resultado.json`) e a tabela por empresa-ano (fora do Git)."""
    ea = empresa_anos(e, taxa)
    s, limites = motores(ea)
    amostra = s[s.exercicio.isin(list(EXERCICIOS))]
    nf_amostra = amostra[amostra.amostra == AMOSTRA_NF]
    ep = episodios(datas_8k)
    positiva, ep = desfecho(nf_amostra, ep)
    s["positiva"] = False
    s.loc[positiva.index, "positiva"] = positiva.to_numpy(bool)
    amostra = s[s.exercicio.isin(list(EXERCICIOS))]
    nf = amostra[(amostra.amostra == AMOSTRA_NF) & amostra.avaliada.astype(bool)]
    so_v2 = amostra[(amostra.amostra == AMOSTRA_NF) & ~amostra.avaliada.astype(bool) & amostra.avaliada_v2.astype(bool)]
    sem_sinal = (amostra.amostra == AMOSTRA_NF) & ~amostra.avaliada.astype(bool) & ~amostra.avaliada_v2.astype(bool)
    ep_ano = ep.abertura.map(lambda d: d.year)
    resultado = {
        "exercicios": [EXERCICIOS.start, EXERCICIOS.stop - 1],
        "exclusoes": {"empresa_anos": len(amostra),
                      **{f"({k}) {nome}": int((amostra.amostra == nome).sum()) for k, nome in
                         ((1, FORA_SEM_VERSAO), (2, FORA_FINANCEIRA), (3, FORA_SPAC), (4, FORA_SEM_RECEITA))},
                      "(5) sem_nenhum_sinal": int(sem_sinal.sum()), "nao_financeiras_avaliadas_v1": len(nf),
                      "so_o_v2_avalia": len(so_v2)},  # fmt: skip
        "episodios": {"total_ate_" + ULTIMA_DATA_8K: len(ep),
                      "por_ano_de_abertura": {str(a): int(n) for a, n in ep_ano.value_counts().sort_index().items()},
                      "em_empresa_ano_da_amostra": int(ep.empresa_ano.notna().sum()),
                      "fora_de_qualquer_empresa_ano_da_amostra": int(ep.empresa_ano.isna().sum())},  # fmt: skip
        "medidas": medidas(nf, reamostragens, semente),
        "so_o_v2_avalia": secundaria._num(secundaria.taxas(so_v2.em_alerta_v2.to_numpy(bool),
                                                           so_v2.positiva.to_numpy(bool))),
        "por_exercicio": por_exercicio(amostra),
        "aaers_2009_2014": aaers(s, firmas, ligacoes),
        "limites": [{k: (None if isinstance(v, float) and np.isnan(v) else v) for k, v in r.items()}
                    for r in limites.to_dict("records")],
    }  # fmt: skip
    return resultado, s


# ---- o cálculo único ----


def confere_congelamento(registro: Path | None = None) -> None:
    """O registro de SHA-256 do estudo tem de existir e bater com cada arquivo registrado (o lacre do v2 sem o bloco do
    estudo, `sha256_registrado`, como nos registros do v1 e do v2), e o Python tem de ser o do registro."""
    registro = REGISTRO if registro is None else registro
    if not registro.exists():
        raise SystemExit("o código do estudo ainda não foi congelado (seção 10): sem docs/eua_codigo_congelado.json")
    r = json.loads(registro.read_text(encoding="utf-8"))
    if r["python"] != f"{sys.version_info[0]}.{sys.version_info[1]}":
        raise SystemExit(f"o estudo usa o Python {r['python']} (registro de congelamento)")
    arquivos = {**r["exemplo_calculado_a_mao"], **r["entradas_versionadas"], **r["codigo"]}
    diferentes = [c for c, h in arquivos.items() if sha256_registrado(c) != h]
    if diferentes:
        raise SystemExit(f"arquivos diferentes do registro de congelamento: {diferentes}")


def confere_baixados_hoje(arquivos: Iterable[Path], hoje: date) -> list[dict[str, str]]:
    """Cada arquivo da SEC baixado de novo no dia do cálculo, com o SHA-256 do manifesto (seção 10)."""
    manifesto = {x["arquivo"]: x for x in sec.le_manifesto()}
    linhas = []
    for p in arquivos:
        x = manifesto.get(p.relative_to(sec.DADOS).as_posix())
        if x is None or x["sha256"] != sec.sha256(p) or not x["baixado_em_utc"].startswith(hoje.isoformat()):
            raise SystemExit(f"{p.name}: não foi baixado de novo hoje com o SHA-256 do manifesto")
        linhas.append(x)
    return linhas


def _git(*args: str) -> str:
    return subprocess.run(["git", *args], cwd=RAIZ, capture_output=True, text=True, check=True).stdout.strip()


def main(argv: list[str] | None = None) -> int:
    a = argparse.ArgumentParser(description="O cálculo único do estudo dos EUA (seção 10).")
    a.add_argument("--calculo-unico", action="store_true", help="com a autorização de Roberto, depois do congelamento")
    a.add_argument("--saida", type=Path, default=SAIDA)
    args = a.parse_args(argv)
    if not args.calculo_unico:
        raise SystemExit("o cálculo único só começa com a autorização de Roberto, depois do congelamento (seção 10)")
    if args.saida.exists():
        raise SystemExit(f"{args.saida} já existe: o cálculo é único")
    confere_congelamento()
    inicio = datetime.now(timezone.utc)
    zips = [fsds.PASTA / f"{t}.zip" for t in fsds.TRIMESTRES]
    baixados = confere_baixados_hoje([*zips, itens.ARQUIVO], inicio.date())
    roda = next((x for x in sec.le_manifesto() if x["arquivo"] == rotulos.RODA.relative_to(sec.DADOS).as_posix()), None)
    if roda is None or roda["sha256"] != sec.sha256(rotulos.RODA):
        raise SystemExit("o arquivo do era-py não tem o SHA-256 do manifesto")
    baixados.append(roda)
    e = junta(le_trimestre(z) for z in zips)
    datas = datas_dos_8k(itens.entregas(formularios=("8-K", "8-K/A")))
    firmas, ligacoes = rotulos.tabelas()
    resultado, s = calcula(e, datas, firmas, ligacoes)
    TABELA.parent.mkdir(parents=True, exist_ok=True)
    s.to_csv(TABELA, index=False)
    resultado["execucao"] = {
        "commit": _git("rev-parse", "HEAD"),
        "codigo_sem_alteracao_local": _git("status", "--porcelain", "--untracked-files=no", "--", "chiocca") == "",
        "python": f"{sys.version_info[0]}.{sys.version_info[1]}",
        "inicio_utc": inicio.isoformat(timespec="seconds"),
        "fim_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "arquivos": {x["arquivo"]: x["sha256"] for x in baixados} | {"data/eua_dff.csv": sec.sha256(TAXA)},
    }
    args.saida.write_text(json.dumps(resultado, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"gravado em {args.saida}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
