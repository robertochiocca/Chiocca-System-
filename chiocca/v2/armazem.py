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
- `enet/`: cópia byte a byte dos arquivos do cache do ENET que entram no armazém, para o `como_era` do motor v1
  ler do armazém sem mudança;
- `manifesto.json`: hash SHA-256 de cada arquivo de origem, contagens, lacre e data máxima.

`FontesArmazem` tem a mesma interface de `chiocca.cvm.Fontes` (`indice_dfp`, `contas_abertas`, `fca`, `cadastro`,
`cache_enet`). Com ela, `chiocca.base.como_era` e o resto do motor v1 rodam sobre o armazém sem nenhuma mudança.

Uso: python -m chiocca.v2.armazem   (monta data/armazem a partir de data/brutos/cvm e data/cache/enet)
"""

from __future__ import annotations

import hashlib
import json
import shutil
from datetime import date
from functools import lru_cache
from pathlib import Path
from typing import Any

import duckdb
import pandas as pd

from chiocca import enet
from chiocca.base import BRUTOS, CACHE_ENET, RAIZ
from chiocca.cvm import COLUNAS_CONTAS, Fontes, cd_texto
from chiocca.v2.lacre import DATA_REFERENCIA_MAXIMA, ULTIMO_EXERCICIO_LIBERADO, garantir_liberado

PASTA = RAIZ / "data" / "armazem"
PRIMEIRO_EXERCICIO = 2010
COLUNAS_INDICE = ["cd_cvm", "CNPJ_CIA", "DENOM_CIA", "DT_REFER", "versao", "dt_receb", "num_doc", "ID_DOC", "LINK_DOC"]
TABELAS = ("versoes", "contas", "fca", "cadastro")
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


def montar(fontes: Fontes, destino: Path = PASTA, anos: range | None = None) -> dict[str, Any]:
    """Monta o armazém a partir de uma fonte de arquivos brutos (pasta da CVM ou fixture de teste)."""
    anos = anos if anos is not None else range(PRIMEIRO_EXERCICIO, ULTIMO_EXERCICIO_LIBERADO + 1)
    for ano in anos:
        garantir_liberado(ano)
    destino.mkdir(parents=True, exist_ok=True)
    maxima = DATA_REFERENCIA_MAXIMA
    arquivos: dict[str, str] = {}
    versoes, contas, fca = [], [], []
    for ano in anos:
        zdfp = fontes.pasta / f"dfp_cia_aberta_{ano}.zip"
        if not zdfp.exists():
            continue
        arquivos[zdfp.name] = _sha256(zdfp)
        idx = fontes.indice_dfp(ano).reset_index(drop=True)
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
            fca.append(f.assign(ano=ano, linha=range(len(f))))
    tab_versoes = (
        pd.concat(versoes, ignore_index=True)
        if versoes
        else pd.DataFrame(columns=[*COLUNAS_INDICE, "exercicio", "linha"])
    )
    # ENET: só versões de exercícios liberados, entregues até a data máxima.
    (destino / "enet").mkdir(exist_ok=True)
    for velho in (destino / "enet").glob("*_con.csv"):
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
