"""Armazenamento temporal (Fase C1): Parquet consultado pelo DuckDB, com todas as versões de DFP até o lacre.

Montado de `data/brutos/cvm` (já conferido por hash) e de `data/cache/enet`, sem rede, em `data/armazem/` (fora do
git). Tabelas (contratos, seção 4):
- `versoes`: o índice da DFP de cada exercício até `ULTIMO_EXERCICIO_LIBERADO`, uma linha por versão entregue, com
  a data de recebimento. Metadados de todas as versões, inclusive as entregues depois de 31/12/2024;
- `contas`: as linhas da DFP por versão disponível. Dos dados abertos vem só a última versão de cada documento
  (é o que o arquivo da CVM traz); do cache do ENET, as versões anteriores do consolidado. Contas de versão entregue
  depois de `DATA_REFERENCIA_MAXIMA` não entram (decisão de 07/11/2026: desses documentos, só metadados). Deles fica
  só a estrutura, com origem `so_metadados`: quais demonstrações existem, em consolidado ou individual, sem nenhuma
  conta nem valor. O `como_era` do motor v1 usa essa estrutura da última versão para decidir se a versão da época
  pode vir do ENET (só consolidado, emenda 8) e para nomear a DFC do ENET (método direto ou indireto); com data de
  referência até a data máxima, os valores dessa versão nunca são lidos;
- `fca`: setor de atividade de cada versão do FCA, com a data de recebimento (o setor de FCA entregue depois da data
  máxima fica vazio);
- `cadastro`: o cadastro de companhias abertas, usado pela regra congelada do setor e pela situação no cadastro;
- `escalas`: a escala original (`MIL` ou `UNIDADE`) de cada demonstração dos dados abertos, por versão. O cache do
  ENET guarda os valores já em reais; desde 09/11/2026, a busca registra a escala da página em
  `<documento>_escala.json`, que entra aqui. Documentos buscados antes disso ficam sem escala (não foram baixados de
  novo só por isso, decisão de 09/11/2026);
- `pareceres`: os textos da seção de pareceres e declarações da DFP (relatório do auditor, com o tipo: sem ressalva,
  com ressalva, adverso ou negativa de opinião), da versão dos dados abertos, com a linha do arquivo de origem;
- `auditores`: a firma de auditoria de cada versão do FCA, com o código na CVM e as datas de atuação. Não entram
  CPF nem nome de pessoa física: nem o responsável técnico nem o auditor pessoa física (identificado pelo CPF no
  campo do auditor), que fica só com `pessoa_fisica = true`, sem nome;
- `nomes`: o nome empresarial de cada versão do FCA, com a data de entrega. A investigação mostra o nome da época
  (o índice dos dados abertos traz o nome atual, que pode ser posterior à data);
- `valores_mobiliarios`: os códigos de negociação de cada versão do FCA entregue até a data máxima, com o valor
  mobiliário, o mercado e o período de negociação (Fase D, campo `codigos_negociacao` da Empresa);
- `enet/`: cópia byte a byte dos arquivos do cache do ENET que entram no armazém, para o `como_era` do motor v1
  ler do armazém sem mudança;
- `manifesto.json`: hash SHA-256 de cada arquivo de origem, contagens, lacre e data máxima.

`FontesArmazem` tem a mesma interface de `chiocca.cvm.Fontes` (`indice_dfp`, `contas_abertas`, `fca`, `cadastro`,
`cache_enet`). Com ela, `chiocca.base.como_era` e o resto do motor v1 rodam sobre o armazém sem nenhuma mudança.

Uso: python -m chiocca.v2.armazem   (monta data/armazem a partir de data/brutos/cvm e data/cache/enet)
"""

from __future__ import annotations

import hashlib
import io
import json
import shutil
import zipfile
from datetime import date
from functools import lru_cache
from pathlib import Path
from typing import Any

import duckdb
import pandas as pd

from chiocca import enet
from chiocca.base import BRUTOS, CACHE_ENET, RAIZ
from chiocca.cvm import COLUNAS_CONTAS, DEMONSTRACOES, TIPOS, Fontes, cd_texto
from chiocca.v2.lacre import DATA_REFERENCIA_MAXIMA, ULTIMO_EXERCICIO_LIBERADO, garantir_liberado

PASTA = RAIZ / "data" / "armazem"
PRIMEIRO_EXERCICIO = 2010
COLUNAS_INDICE = ["cd_cvm", "CNPJ_CIA", "DENOM_CIA", "DT_REFER", "versao", "dt_receb", "num_doc", "ID_DOC", "LINK_DOC"]
TABELAS = ("versoes", "contas", "fca", "cadastro", "escalas", "pareceres", "auditores", "nomes", "valores_mobiliarios")
COLUNAS_AUDITORES = ["ano", "cd_cvm", "versao", "dt_receb", "auditor", "codigo_cvm_auditor", "inicio", "fim",
                     "pessoa_fisica"]  # fmt: skip
COLUNAS_VM = ["ano", "cd_cvm", "versao", "dt_receb", "valor_mobiliario", "codigo_negociacao", "mercado",
              "inicio_negociacao", "fim_negociacao"]  # fmt: skip
SO_METADADOS = "so_metadados"


def _sha256(caminho: Path) -> str:
    h = hashlib.sha256()
    with open(caminho, "rb") as f:
        for bloco in iter(lambda: f.read(1 << 20), b""):
            h.update(bloco)
    return h.hexdigest()


def _como_data(serie: pd.Series) -> pd.Series:
    """Datas como objetos `datetime.date`, como `Fontes` devolve (o `como_era` compara com `date`)."""
    return pd.to_datetime(serie).dt.date


def _escalas(zdfp: Path, ano: int) -> pd.DataFrame:
    """Escala original de cada demonstração dos dados abertos (metadado do documento)."""
    partes = []
    with zipfile.ZipFile(zdfp) as z:
        nomes = set(z.namelist())
        for dem in DEMONSTRACOES:
            for tipo in TIPOS:
                arq = f"dfp_cia_aberta_{dem}_{tipo}_{ano}.csv"
                if arq not in nomes:
                    continue
                d = pd.read_csv(io.BytesIO(z.read(arq)), sep=";", encoding="latin1", dtype=str,
                                usecols=["CD_CVM", "DT_REFER", "VERSAO", "ESCALA_MOEDA"]).drop_duplicates()  # fmt: skip
                partes.append(pd.DataFrame({"exercicio": ano, "cd_cvm": cd_texto(d.CD_CVM), "dt_refer": d.DT_REFER,
                                            "versao": d.VERSAO.astype(int), "tipo": tipo, "demonstracao": dem,
                                            "escala": d.ESCALA_MOEDA}))  # fmt: skip
    colunas = ["exercicio", "cd_cvm", "dt_refer", "versao", "tipo", "demonstracao", "escala"]
    return pd.concat(partes, ignore_index=True) if partes else pd.DataFrame(columns=colunas)


def _pareceres(zdfp: Path, ano: int, idx: pd.DataFrame, maxima: date) -> pd.DataFrame:
    """Seção de pareceres e declarações da DFP (dados abertos: só a última versão), entregue até a data máxima."""
    colunas = ["exercicio", "cd_cvm", "dt_refer", "versao", "tp_relat_aud", "tp_parecer_decl", "num_item", "texto",
               "arquivo", "linha_arquivo"]  # fmt: skip
    arq = f"dfp_cia_aberta_parecer_{ano}.csv"
    with zipfile.ZipFile(zdfp) as z:
        if arq not in z.namelist():
            return pd.DataFrame(columns=colunas)
        d = pd.read_csv(io.BytesIO(z.read(arq)), sep=";", encoding="latin1", dtype=str, keep_default_na=False)
    d["linha_arquivo"] = range(2, len(d) + 2)
    chave = idx.groupby(["CNPJ_CIA", "DT_REFER", "versao"]).agg(
        cd_cvm=("cd_cvm", "first"), dt_receb=("dt_receb", "max")
    )
    d["versao_int"] = d.VERSAO.astype(int)
    d = d.merge(chave, left_on=["CNPJ_CIA", "DT_REFER", "versao_int"], right_index=True, how="inner")
    d = d[d.dt_receb <= maxima]
    return pd.DataFrame({"exercicio": ano, "cd_cvm": d.cd_cvm, "dt_refer": d.DT_REFER, "versao": d.versao_int,
                         "tp_relat_aud": d.TP_RELAT_AUD.replace("", None), "tp_parecer_decl": d.TP_PARECER_DECL,
                         "num_item": d.NUM_ITEM_PARECER_DECL, "texto": d.TXT_PARECER_DECL,
                         "arquivo": f"{zdfp.name}/{arq}", "linha_arquivo": d.linha_arquivo})[colunas]  # fmt: skip


def _nomes(zfca: Path, ano: int, maxima: date) -> pd.DataFrame:
    """Nome empresarial de cada versão do FCA entregue até a data máxima."""
    colunas = ["ano", "cd_cvm", "versao", "dt_receb", "nome"]
    with zipfile.ZipFile(zfca) as z:
        arq = f"fca_cia_aberta_geral_{ano}.csv"
        if arq not in z.namelist():
            return pd.DataFrame(columns=colunas)
        idx = pd.read_csv(io.BytesIO(z.read(f"fca_cia_aberta_{ano}.csv")), sep=";", encoding="latin1", dtype=str)
        geral = pd.read_csv(io.BytesIO(z.read(arq)), sep=";", encoding="latin1", dtype=str)
    if "Nome_Empresarial" not in geral.columns:
        return pd.DataFrame(columns=colunas)
    idx = idx.drop_duplicates("ID_DOC")
    d = geral.drop_duplicates("ID_Documento").merge(idx[["ID_DOC", "CD_CVM", "DT_RECEB", "VERSAO"]], left_on="ID_Documento",
                                                    right_on="ID_DOC", how="inner")  # fmt: skip
    d["dt_receb"] = pd.to_datetime(d.DT_RECEB).dt.date
    d = d[d.dt_receb <= maxima]
    return pd.DataFrame({"ano": ano, "cd_cvm": cd_texto(d.CD_CVM), "versao": d.VERSAO.astype(int), "dt_receb": d.dt_receb,
                         "nome": d.Nome_Empresarial})[colunas]  # fmt: skip


def _auditores(zfca: Path, ano: int, maxima: date) -> pd.DataFrame:
    """Firma de auditoria de cada versão do FCA entregue até a data máxima (sem CPF nem pessoa física)."""
    colunas = COLUNAS_AUDITORES
    with zipfile.ZipFile(zfca) as z:
        arq = f"fca_cia_aberta_auditor_{ano}.csv"
        if arq not in z.namelist():
            return pd.DataFrame(columns=colunas)
        idx = pd.read_csv(io.BytesIO(z.read(f"fca_cia_aberta_{ano}.csv")), sep=";", encoding="latin1", dtype=str)
        au = pd.read_csv(io.BytesIO(z.read(arq)), sep=";", encoding="latin1", dtype=str)
    idx = idx.drop_duplicates("ID_DOC")
    d = au.merge(idx[["ID_DOC", "CD_CVM", "DT_RECEB"]], left_on="ID_Documento", right_on="ID_DOC", how="inner")
    d["dt_receb"] = pd.to_datetime(d.DT_RECEB).dt.date
    d = d[d.dt_receb <= maxima]
    doc = d["CPF_CNPJ_Auditor"] if "CPF_CNPJ_Auditor" in d.columns else pd.Series("", index=d.index)
    pf = doc.fillna("").astype(str).str.replace(r"\D", "", regex=True).str.len() == 11  # CPF: pessoa física
    return pd.DataFrame({"ano": ano, "cd_cvm": cd_texto(d.CD_CVM), "versao": d.Versao.astype(int), "dt_receb": d.dt_receb,
                         "auditor": d.Auditor.where(~pf, None), "codigo_cvm_auditor": d.Codigo_CVM_Auditor,
                         "inicio": d.Data_Inicio_Atuacao_Auditor, "fim": d.Data_Fim_Atuacao_Auditor,
                         "pessoa_fisica": pf})[colunas]  # fmt: skip


SIGLAS_MAPA = {s: s for s in ("KPMG", "BDO", "RCS", "EY", "S.S.", "S/S", "SS", "S.A.", "S/A", "SA", "EPP", "ME",
                               "CRC", "UHY", "BKR", "PKF", "HLB", "RSM", "GT")} | {"PWC": "PwC", "LTDA": "Ltda.",
                                                                                  "LTDA.": "Ltda."}  # fmt: skip
CONECTIVOS = {"DE", "DA", "DO", "DAS", "DOS", "E", "EM"}


def capitalizacao(nome: str) -> str:
    """Capitalização normal de um nome em maiúsculas, mantendo as siglas (KPMG, BDO, S.S.) e os conectivos em
    minúsculas. Só para exibição."""
    palavras = []
    for i, w in enumerate(nome.split()):
        chave = w.upper()
        if chave in SIGLAS_MAPA:
            palavras.append(SIGLAS_MAPA[chave])
        elif i > 0 and chave in CONECTIVOS:
            palavras.append(w.lower())
        elif "-" in w and len(w) > 1:
            palavras.append("-".join(p[:1].upper() + p[1:].lower() for p in w.split("-")))
        else:
            palavras.append(w[:1].upper() + w[1:].lower())
    return " ".join(palavras)


def _valores_mobiliarios(zfca: Path, ano: int, maxima: date) -> pd.DataFrame:
    """Códigos de negociação de cada versão do FCA entregue até a data máxima, com o período de negociação."""
    with zipfile.ZipFile(zfca) as z:
        arq = f"fca_cia_aberta_valor_mobiliario_{ano}.csv"
        if arq not in z.namelist():
            return pd.DataFrame(columns=COLUNAS_VM)
        idx = pd.read_csv(io.BytesIO(z.read(f"fca_cia_aberta_{ano}.csv")), sep=";", encoding="latin1", dtype=str)
        vm = pd.read_csv(io.BytesIO(z.read(arq)), sep=";", encoding="latin1", dtype=str)
    if "Codigo_Negociacao" not in vm.columns:
        return pd.DataFrame(columns=COLUNAS_VM)
    vm = vm[vm.Codigo_Negociacao.notna() & (vm.Codigo_Negociacao.str.strip() != "")]
    idx = idx.drop_duplicates("ID_DOC")
    d = vm.merge(
        idx[["ID_DOC", "CD_CVM", "DT_RECEB", "VERSAO"]], left_on="ID_Documento", right_on="ID_DOC", how="inner"
    )
    d["dt_receb"] = pd.to_datetime(d.DT_RECEB).dt.date
    d = d[d.dt_receb <= maxima]
    col = lambda nome: d[nome] if nome in d.columns else None  # noqa: E731
    return pd.DataFrame({"ano": ano, "cd_cvm": cd_texto(d.CD_CVM), "versao": d.VERSAO.astype(int), "dt_receb": d.dt_receb,
                         "valor_mobiliario": col("Valor_Mobiliario"), "codigo_negociacao": d.Codigo_Negociacao.str.strip(),
                         "mercado": col("Mercado"), "inicio_negociacao": col("Data_Inicio_Negociacao"),
                         "fim_negociacao": col("Data_Fim_Negociacao")})[COLUNAS_VM]  # fmt: skip


def montar(fontes: Fontes, destino: Path = PASTA, anos: range | None = None) -> dict[str, Any]:
    """Monta o armazém a partir de uma fonte de arquivos brutos (pasta da CVM ou fixture de teste)."""
    anos = anos if anos is not None else range(PRIMEIRO_EXERCICIO, ULTIMO_EXERCICIO_LIBERADO + 1)
    for ano in anos:
        garantir_liberado(ano)
    destino.mkdir(parents=True, exist_ok=True)
    maxima = DATA_REFERENCIA_MAXIMA
    arquivos: dict[str, str] = {}
    versoes, contas, fca, escalas, pareceres, auditores, nomes, vms = [], [], [], [], [], [], [], []
    for ano in anos:
        zdfp = fontes.pasta / f"dfp_cia_aberta_{ano}.zip"
        if not zdfp.exists():
            continue
        arquivos[zdfp.name] = _sha256(zdfp)
        escalas.append(_escalas(zdfp, ano))
        idx = fontes.indice_dfp(ano).reset_index(drop=True)
        pareceres.append(_pareceres(zdfp, ano, idx, maxima))
        versoes.append(idx[COLUNAS_INDICE].assign(exercicio=ano, linha=range(len(idx))))
        # Data de recebimento da última versão de cada documento (a dos dados abertos).
        receb = idx.groupby(["cd_cvm", "DT_REFER", "versao"]).dt_receb.max()
        linha = 0
        for (cd, dt_refer, tipo), g in fontes.contas_abertas(ano).items():
            versao = int(g.versao.iloc[0])
            if receb.get((cd, dt_refer, versao), maxima) > maxima:
                # Entregue depois da data máxima: só a estrutura (demonstrações presentes), sem conta nem valor.
                g = g[["cd_cvm", "dt_refer", "versao", "tipo", "demonstracao"]].drop_duplicates()
                g = g.assign(ordem=None, cd_conta=None, ds_conta=None, valor=float("nan"))
                origem = SO_METADADOS
            else:
                origem = "dados_abertos"
            contas.append(g[COLUNAS_CONTAS].assign(exercicio=ano, origem=origem, num_doc=None,
                                                   linha=range(linha, linha + len(g))))  # fmt: skip
            linha += len(g)
        zfca = fontes.pasta / f"fca_cia_aberta_{ano}.zip"
        if zfca.exists():
            arquivos[zfca.name] = _sha256(zfca)
            f = fontes.fca(ano).reset_index(drop=True)
            f["setor"] = f.setor.where(f.dt_receb <= maxima)
            auditores.append(_auditores(zfca, ano, maxima))
            nomes.append(_nomes(zfca, ano, maxima))
            vms.append(_valores_mobiliarios(zfca, ano, maxima))
            fca.append(f.assign(ano=ano, linha=range(len(f))))
    tab_versoes = (
        pd.concat(versoes, ignore_index=True)
        if versoes
        else pd.DataFrame(columns=[*COLUNAS_INDICE, "exercicio", "linha"])
    )
    # ENET: só versões de exercícios liberados, entregues até a data máxima.
    (destino / "enet").mkdir(exist_ok=True)
    for velho in [*(destino / "enet").glob("*_con.csv"), *(destino / "enet").glob("*_escala.json")]:
        velho.unlink()
    validos = tab_versoes[tab_versoes.dt_receb <= maxima]
    por_doc = {str(r.num_doc): r for r in validos.drop_duplicates("num_doc", keep="last").itertuples(index=False)}
    n_enet = 0
    for arq in sorted(Path(fontes.cache_enet).glob("*_con.csv")) if Path(fontes.cache_enet).exists() else []:
        num = arq.name.removesuffix("_con.csv")
        r = por_doc.get(num)
        if r is None:
            continue
        shutil.copyfile(arq, destino / "enet" / arq.name)
        arquivos[f"enet/{arq.name}"] = _sha256(arq)
        lateral = Path(fontes.cache_enet) / f"{num}_escala.json"
        if lateral.exists():  # escala da página, registrada pela busca desde 09/11/2026
            shutil.copyfile(lateral, destino / "enet" / lateral.name)
            arquivos[f"enet/{lateral.name}"] = _sha256(lateral)
            por_dem = json.loads(lateral.read_text(encoding="utf-8"))
            escalas.append(pd.DataFrame([{"exercicio": int(r.exercicio), "cd_cvm": r.cd_cvm, "dt_refer": r.DT_REFER,
                                          "versao": int(r.versao), "tipo": "con", "demonstracao": dem, "escala": esc}
                                         for dem, esc in sorted(por_dem.items())]))  # fmt: skip
        d = enet.le_cache(Path(fontes.cache_enet), num)
        if d is None or d.empty:
            continue
        contas.append(d.assign(cd_cvm=r.cd_cvm, dt_refer=r.DT_REFER, versao=int(r.versao), tipo="con",
                               exercicio=int(r.exercicio), origem="enet", num_doc=num,
                               linha=range(len(d)))[[*COLUNAS_CONTAS, "exercicio", "origem", "num_doc", "linha"]])  # fmt: skip
        n_enet += 1
    cad = fontes.cadastro()
    arquivos["cad_cia_aberta.csv"] = _sha256(fontes.pasta / "cad_cia_aberta.csv")
    tabelas = {
        "versoes": tab_versoes,
        "contas": pd.concat(contas, ignore_index=True) if contas else pd.DataFrame(columns=[*COLUNAS_CONTAS, "exercicio", "origem", "num_doc", "linha"]),
        "fca": pd.concat(fca, ignore_index=True) if fca else pd.DataFrame(columns=["cd_cvm", "versao", "dt_receb", "setor", "ano", "linha"]),
        "cadastro": cad.drop(columns=["cd_cvm"]),  # derivado de CD_CVM na leitura (o DuckDB não diferencia maiúsculas)
        "escalas": pd.concat(escalas, ignore_index=True) if escalas else _escalas_vazias(),
        "pareceres": pd.concat(pareceres, ignore_index=True) if pareceres else _pareceres_vazios(),
        "auditores": pd.concat(auditores, ignore_index=True) if auditores else _auditores_vazios(),
        "nomes": pd.concat(nomes, ignore_index=True) if nomes else pd.DataFrame(columns=["ano", "cd_cvm", "versao", "dt_receb", "nome"]),
        "valores_mobiliarios": pd.concat(vms, ignore_index=True) if vms else pd.DataFrame(columns=COLUNAS_VM),
    }  # fmt: skip
    tabelas["contas"]["num_doc"] = tabelas["contas"]["num_doc"].astype("string")
    for nome, t in tabelas.items():
        t.to_parquet(destino / f"{nome}.parquet", index=False)
    manifesto = {
        "ultimo_exercicio_liberado": ULTIMO_EXERCICIO_LIBERADO,
        "data_referencia_maxima": str(DATA_REFERENCIA_MAXIMA),
        "exercicios": sorted(int(x) for x in tab_versoes.exercicio.unique()),
        "linhas": {nome: int(len(t)) for nome, t in tabelas.items()},
        "documentos_enet": n_enet,
        "arquivos_sha256": dict(sorted(arquivos.items())),
    }
    (destino / "manifesto.json").write_text(
        json.dumps(manifesto, ensure_ascii=False, indent=1) + "\n", encoding="utf-8"
    )
    return manifesto


def _pareceres_vazios() -> pd.DataFrame:
    return pd.DataFrame(columns=["exercicio", "cd_cvm", "dt_refer", "versao", "tp_relat_aud", "tp_parecer_decl",
                                 "num_item", "texto", "arquivo", "linha_arquivo"])  # fmt: skip


def _auditores_vazios() -> pd.DataFrame:
    return pd.DataFrame(columns=COLUNAS_AUDITORES)


def _escalas_vazias() -> pd.DataFrame:
    return pd.DataFrame(columns=["exercicio", "cd_cvm", "dt_refer", "versao", "tipo", "demonstracao", "escala"])


class Armazem:
    """Consultas SQL (DuckDB) sobre as tabelas Parquet do armazém."""

    def __init__(self, pasta: Path = PASTA) -> None:
        self.pasta = Path(pasta)
        if not (self.pasta / "manifesto.json").exists():
            raise FileNotFoundError(f"armazém não montado em {self.pasta} (python -m chiocca.v2.armazem)")
        self.manifesto = json.loads((self.pasta / "manifesto.json").read_text(encoding="utf-8"))
        self.con = duckdb.connect()
        for nome in TABELAS:
            caminho = str(self.pasta / f"{nome}.parquet").replace("'", "''")
            self.con.execute(f"CREATE VIEW {nome} AS SELECT * FROM read_parquet('{caminho}')")

    def consulta(self, sql: str, parametros: list[Any] | None = None) -> pd.DataFrame:
        return self.con.execute(sql, parametros or []).df()

    def versoes_na_data(self, exercicio: int, data_referencia: date) -> pd.DataFrame:
        """Para cada documento do exercício, a versão mais recente entregue até a data e quantas eram conhecidas."""
        garantir_liberado(exercicio)
        return self.consulta(
            """
            SELECT cd_cvm, DT_REFER AS dt_refer, max(versao) AS versao_na_data, count(DISTINCT versao) AS versoes_conhecidas
            FROM versoes WHERE exercicio = ? AND CAST(dt_receb AS DATE) <= ?
            GROUP BY cd_cvm, DT_REFER ORDER BY cd_cvm, DT_REFER
            """,
            [exercicio, data_referencia],
        )

    def parecer(self, exercicio: int, cd_cvm: str, dt_refer: str, versao: int) -> pd.DataFrame:
        """Seção de pareceres e declarações da DFP, se a versão for a dos dados abertos (só a última é publicada)."""
        return self.consulta(
            "SELECT * FROM pareceres WHERE exercicio = ? AND cd_cvm = ? AND dt_refer = ? AND versao = ? ORDER BY linha_arquivo",
            [exercicio, cd_cvm, dt_refer, versao],
        )

    def nomes_anteriores(self, cd_cvm: str, ate: date) -> list[dict[str, Any]]:
        """Nomes que a companhia teve antes do nome na data, pelos FCA entregues até a data: a última versão de cada
        ano de referência, em ordem de ano; `ate_ano` é o ano do primeiro FCA com o nome seguinte. Do mais antigo para
        o mais recente, como vieram no FCA (sem mudar maiúsculas)."""
        d = self.consulta(
            """
            SELECT ano, nome FROM (
                SELECT ano, nome, row_number() OVER (PARTITION BY ano ORDER BY versao DESC) AS r
                FROM nomes WHERE cd_cvm = ? AND CAST(dt_receb AS DATE) <= ? AND nome IS NOT NULL)
            WHERE r = 1 ORDER BY ano
            """,
            [cd_cvm, ate],
        )
        corridas: list[tuple[str, int]] = []
        for x in d.itertuples(index=False):
            nome = " ".join(str(x.nome).split())
            if not corridas or corridas[-1][0].casefold() != nome.casefold():
                corridas.append((nome, int(x.ano)))
        return [{"nome": n, "ate_ano": corridas[i + 1][1]} for i, (n, _) in enumerate(corridas[:-1])]

    def nome_na_data(self, cd_cvm: str, ate: date) -> str | None:
        """Nome empresarial na última versão do FCA entregue até a data."""
        d = self.consulta(
            "SELECT nome FROM nomes WHERE cd_cvm = ? AND CAST(dt_receb AS DATE) <= ? ORDER BY dt_receb DESC, versao DESC LIMIT 1",
            [cd_cvm, ate],
        )
        return None if d.empty else str(d.nome.iloc[0])

    def codigos_negociacao(self, cd_cvm: str, ate: date) -> list[dict[str, Any]]:
        """Códigos de negociação na última versão do FCA entregue até a data, com o período de negociação."""
        d = self.consulta(
            """
            WITH ultima AS (SELECT ano, versao FROM valores_mobiliarios WHERE cd_cvm = ? AND CAST(dt_receb AS DATE) <= ?
                            ORDER BY CAST(dt_receb AS DATE) DESC, ano DESC, versao DESC LIMIT 1)
            SELECT v.* FROM valores_mobiliarios v JOIN ultima u ON v.ano = u.ano AND v.versao = u.versao
            WHERE v.cd_cvm = ? ORDER BY v.codigo_negociacao, v.mercado
            """,
            [cd_cvm, ate, cd_cvm],
        )
        # campo vazio no FCA pode voltar do DuckDB como NaN (float): vira nulo, como os demais campos sem valor
        return [{"codigo": str(x.codigo_negociacao), "valor_mobiliario": _texto(x.valor_mobiliario),
                 "mercado": _texto(x.mercado), "inicio_negociacao": _texto(x.inicio_negociacao),
                 "fim_negociacao": _texto(x.fim_negociacao),
                 "fca": {"ano": int(x.ano), "versao": int(x.versao), "dt_receb": str(x.dt_receb)[:10]}}
                for x in d.drop_duplicates(["codigo_negociacao", "mercado"]).itertuples(index=False)]  # fmt: skip

    def nomes_canonicos_auditores(self, ate: date) -> dict[str, str]:
        """Um nome de exibição por código de firma na CVM, a partir dos FCA entregues até a data (todas as companhias):
        a grafia mais frequente entre as que já vêm em capitalização normal (com minúsculas); no empate, a mais recente.
        Se só houver grafias em maiúsculas, a mais frequente passa por `capitalizacao`, que mantém as siglas. É só
        exibição: a comparação entre firmas é pelo código. Pessoa física não tem nome guardado e não entra."""
        d = self.consulta(
            """
            SELECT codigo_cvm_auditor AS codigo, trim(auditor) AS nome, count(*) AS n,
                   max(CAST(dt_receb AS DATE)) AS u, trim(auditor) <> upper(trim(auditor)) AS normal
            FROM auditores WHERE CAST(dt_receb AS DATE) <= ? AND codigo_cvm_auditor IS NOT NULL AND auditor IS NOT NULL
            GROUP BY 1, 2 ORDER BY codigo, normal DESC, n DESC, u DESC, nome
            """,
            [ate],
        )
        d = d.drop_duplicates("codigo")  # já ordenado: capitalização normal, a mais frequente, a mais recente
        return {
            str(c): (str(n) if bool(normal) else capitalizacao(str(n)))
            for c, n, normal in zip(d.codigo, d.nome, d.normal)
        }

    def auditores(self, cd_cvm: str, ate: date) -> pd.DataFrame:
        """Firmas de auditoria nas versões do FCA entregues até a data, por ano e versão."""
        return self.consulta(
            "SELECT * FROM auditores WHERE cd_cvm = ? AND CAST(dt_receb AS DATE) <= ? ORDER BY ano, versao, auditor",
            [cd_cvm, ate],
        )

    def escala(self, exercicio: int, cd_cvm: str, dt_refer: str, versao: int, tipo: str) -> str | None:
        """Escala original da versão nos dados abertos; com escalas diferentes entre demonstrações, todas, com "+"."""
        d = self.consulta(
            "SELECT DISTINCT escala FROM escalas WHERE exercicio = ? AND cd_cvm = ? AND dt_refer = ? AND versao = ? AND tipo = ?",
            [exercicio, cd_cvm, dt_refer, versao, tipo],
        )
        valores = sorted(str(x) for x in d.escala.dropna())
        return "+".join(valores) if valores else None


def _texto(v: Any) -> str | None:
    """Texto do campo, ou None se o campo estiver vazio (None ou NaN)."""
    return None if v is None or (isinstance(v, float) and pd.isna(v)) else str(v)


class FontesArmazem(Armazem):
    """A interface de `chiocca.cvm.Fontes`, lida do armazém: o motor v1 roda sobre ela sem mudança."""

    def __init__(self, pasta: Path = PASTA) -> None:
        super().__init__(pasta)
        self.cache_enet = self.pasta / "enet"
        self.indice_dfp = lru_cache(maxsize=None)(self._indice_dfp)  # type: ignore[method-assign]
        self.contas_abertas = lru_cache(maxsize=2)(self._contas_abertas)  # type: ignore[method-assign]
        self.fca = lru_cache(maxsize=None)(self._fca)  # type: ignore[method-assign]
        self.cadastro = lru_cache(maxsize=1)(self._cadastro)  # type: ignore[method-assign]

    def _indice_dfp(self, ano: int) -> pd.DataFrame:
        garantir_liberado(ano)
        cols = ", ".join(COLUNAS_INDICE)
        d = self.consulta(f"SELECT {cols} FROM versoes WHERE exercicio = ? ORDER BY linha", [ano])
        d["versao"] = d.versao.astype(int)
        d["dt_receb"] = _como_data(d.dt_receb)
        return d

    def _contas_abertas(self, ano: int) -> dict[tuple[str, str, str], pd.DataFrame]:
        garantir_liberado(ano)
        cols = ", ".join(COLUNAS_CONTAS)
        d = self.consulta(
            f"SELECT {cols} FROM contas WHERE exercicio = ? AND origem IN ('dados_abertos', '{SO_METADADOS}') ORDER BY linha",
            [ano],
        )
        if d.empty:
            return {}
        d["versao"] = d.versao.astype(int)
        return {k: g.reset_index(drop=True) for k, g in d.groupby(["cd_cvm", "dt_refer", "tipo"], sort=False)}

    def _fca(self, ano: int) -> pd.DataFrame:
        d = self.consulta("SELECT cd_cvm, versao, dt_receb, setor FROM fca WHERE ano = ? ORDER BY linha", [ano])
        d["versao"] = d.versao.astype(int)
        d["dt_receb"] = _como_data(d.dt_receb)
        return d

    def _cadastro(self) -> pd.DataFrame:
        d = self.consulta("SELECT * FROM cadastro")
        d["cd_cvm"] = cd_texto(d.CD_CVM)
        return d


def main() -> None:
    m = montar(Fontes(BRUTOS, CACHE_ENET))
    print(json.dumps({k: v for k, v in m.items() if k != "arquivos_sha256"}, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
