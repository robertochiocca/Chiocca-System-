"""Fatos relevantes e comunicados ao mercado (Fase F2a): só metadados do IPE até a data, nunca depois de 31/12/2024,
última versão de cada protocolo, assunto pelo detector de nomes do leitor, ordem fixa que não depende do assunto,
linhagem de cada item, a exibição no PDF (24 meses) e os números da documentação."""

from __future__ import annotations

import hashlib
import json
import random
import zipfile
import zlib
from datetime import date
from pathlib import Path

import pytest

from chiocca import base
from chiocca.v2 import ipe, pdf_investigacao
from chiocca.v2.modelos import FatosEComunicados

CABECALHO = (
    "CNPJ_Companhia;Nome_Companhia;Codigo_CVM;Data_Referencia;Categoria;Tipo;Especie;Assunto;Data_Entrega;"
    "Tipo_Apresentacao;Protocolo_Entrega;Versao;Link_Download"
)


def _linha(cd: str, categoria: str, assunto: str, entrega: str, protocolo: str, versao: int = 1,
           seq: int | None = None) -> str:  # fmt: skip
    """Uma linha do IPE como na CVM: o link traz numProtocolo, numSequencia e numVersao (o documento)."""
    n = seq if seq is not None else zlib.crc32(f"{protocolo}|{versao}".encode()) % 900_000 + 100_000
    link = f"https://www.rad.cvm.gov.br/ENET/frmDownloadDocumento.aspx?numProtocolo={n}&numSequencia={n}&numVersao={versao}"
    return (f"00.000.000/0001-00;EXEMPLO S.A.;{cd};{entrega};{categoria};Outros;;{assunto};{entrega};"
            f"AP - Apresentação;{protocolo};{versao};{link}")  # fmt: skip


def _ipe(pasta: Path, ano: int, linhas: list[str]) -> Path:
    caminho = pasta / f"ipe_cia_aberta_{ano}.zip"
    with zipfile.ZipFile(caminho, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr(f"ipe_cia_aberta_{ano}.csv", ("\n".join([CABECALHO, *linhas]) + "\n").encode("latin1"))
    return caminho


@pytest.fixture
def brutos(tmp_path: Path) -> Path:
    _ipe(tmp_path, 2021, [
        _linha("000777", "Fato Relevante", "Aumento de capital aprovado", "2021-03-10", "P1", 1, seq=101),
        _linha("000777", "Fato Relevante", "Aumento de capital (reapresentação)", "2021-03-12", "P1R", 2, seq=102),
        _linha("777", "Fato Relevante", "Aumento de capital (reapresentação)", "2021-03-12", "P1R", 2, seq=102),
        _linha("777", "Fato Relevante", "Material fact - capital increase", "2021-03-10", "P1", 1, seq=103),
        _linha("777", "Comunicado ao Mercado", "Apresentação de resultados do trimestre", "2021-05-01", "P2"),
        _linha("777", "Comunicado ao Mercado", "Renúncia do Sr. Ernesto Fictício Barbosa", "2021-06-01", "P3"),
        _linha("777", "Assembleia", "Ata da assembleia", "2021-04-30", "P4"),
        _linha("888", "Fato Relevante", "Outra companhia", "2021-03-10", "P5"),
    ])  # fmt: skip
    _ipe(tmp_path, 2024, [
        _linha("777", "Fato Relevante", "Recuperação judicial ajuizada", "2024-06-01", "P6"),
        _linha("777", "Fato Relevante", "Entrega fora do ano por erro no arquivo", "2025-01-02", "P7"),
    ])  # fmt: skip
    ipe._ano.cache_clear()
    return tmp_path


def test_um_item_por_documento_ate_a_data_e_categorias(brutos: Path) -> None:
    r = ipe.lista("777", date(2021, 3, 11), "pt", brutos)
    # dois documentos (português e inglês) no mesmo protocolo de entrega
    assert [(x["protocolo"], x["versao"]) for x in r["itens"]] == [("P1", 1), ("P1", 1)]
    r = ipe.lista("777", date(2022, 4, 30), "pt", brutos)
    assert [(x["protocolo"], x["versao"], x["categoria"]) for x in r["itens"]] == [
        ("P1R", 2, "fato_relevante"),  # a reapresentação é outra entrega; a linha repetida conta uma vez
        ("P1", 1, "fato_relevante"),
        ("P1", 1, "fato_relevante"),
        ("P3", 1, "comunicado_ao_mercado"),
        ("P2", 1, "comunicado_ao_mercado"),
    ]
    assert len({x["id_documento"] for x in r["itens"]}) == len(r["itens"])
    assert r["contagem"] == {"fato_relevante": 3, "comunicado_ao_mercado": 2} and r["gera_alerta"] is False
    FatosEComunicados.model_validate(r)


def test_sem_protocolo_de_entrega_como_de_2010_a_2014(tmp_path: Path) -> None:
    linhas = [_linha("777", "Fato Relevante", f"Assunto número {i}", "2012-05-0" + str(i), "", 1, seq=200 + i)
              for i in range(1, 4)]  # fmt: skip
    linhas = [x.replace(";1;https", ";;https") for x in linhas]  # o arquivo de 2012 também não traz a versão
    _ipe(tmp_path, 2012, linhas)
    ipe._ano.cache_clear()
    r = ipe.lista("777", date(2012, 12, 31), "pt", tmp_path)
    assert len(r["itens"]) == 3 and all(x["protocolo"] is None and x["versao"] is None for x in r["itens"])
    FatosEComunicados.model_validate(r)


def test_nada_depois_de_31_12_2024_nem_com_data_maior(brutos: Path) -> None:
    r = ipe.lista("777", date(2025, 6, 30), "pt", brutos)  # a API não aceita essa data; aqui o limite segura
    assert max(x["data_entrega"] for x in r["itens"]) == "2024-06-01" and r["ate"] == "2024-12-31"
    assert "P7" not in {x["protocolo"] for x in r["itens"]}
    assert "P6" not in {x["protocolo"] for x in ipe.lista("777", date(2024, 5, 31), "pt", brutos)["itens"]}


def test_assunto_com_nome_de_pessoa_omitido(brutos: Path) -> None:
    for lang, texto in (("pt", "assunto omitido (possível nome de pessoa); ver o documento na CVM"),
                        ("en", "subject omitted (possible person's name); see the document at the CVM")):  # fmt: skip
        r = ipe.lista("777", date(2022, 4, 30), lang, brutos)
        p3 = next(x for x in r["itens"] if x["protocolo"] == "P3")
        assert p3["assunto_omitido"] and p3["assunto"] == texto
        assert "Ernesto" not in json.dumps(r, ensure_ascii=False)


def test_linhagem_de_cada_item(brutos: Path) -> None:
    r = ipe.lista("777", date(2024, 12, 31), "pt", brutos)
    for x in r["itens"]:
        caminho = brutos / x["fonte"]["arquivo"]
        assert x["fonte"]["ano"] == int(x["data_entrega"][:4])
        assert x["fonte"]["sha256"] == hashlib.sha256(caminho.read_bytes()).hexdigest()


def test_ordem_nao_depende_do_assunto(brutos: Path, tmp_path_factory: pytest.TempPathFactory) -> None:
    """Trocar os assuntos de lugar não muda a ordem: só categoria, data de entrega e documento ordenam."""
    original = [x["id_documento"] for x in ipe.lista("777", date(2024, 12, 31), "pt", brutos)["itens"]]
    outra = tmp_path_factory.mktemp("embaralhado")
    for ano in (2021, 2024):
        with zipfile.ZipFile(brutos / f"ipe_cia_aberta_{ano}.zip") as z:
            cab, *linhas = z.read(f"ipe_cia_aberta_{ano}.csv").decode("latin1").strip().split("\n")
        campos = [x.split(";") for x in linhas]
        assuntos = [c[7] for c in campos]
        random.Random(ano).shuffle(assuntos)
        _ipe(outra, ano, [";".join(c[:7] + [a] + c[8:]) for c, a in zip(campos, assuntos, strict=True)])
    ipe._ano.cache_clear()
    assert [x["id_documento"] for x in ipe.lista("777", date(2024, 12, 31), "pt", outra)["itens"]] == original


def test_sem_arquivo_ou_sem_documento_a_mesma_saida(brutos: Path, tmp_path_factory: pytest.TempPathFactory) -> None:
    vazio = tmp_path_factory.mktemp("vazio")
    assert ipe.lista("999", date(2022, 4, 30), "pt", brutos) == ipe.lista("999", date(2022, 4, 30), "pt", vazio)
    assert ipe.lista("999", date(2022, 4, 30), "pt", vazio)["motivo"] == ipe.TEXTOS["pt"]["sem_itens"]


def _inv_com(fc: dict, d: str, lang: str = "pt") -> dict:
    inv = json.loads((base.RAIZ / "docs" / "exemplos" / f"americanas_2021_em_2024-12-31_{lang}.json").read_text())
    inv["data_referencia"] = d
    inv["o_que_se_sabia"]["fatos_e_comunicados"] = fc
    return inv


def test_pdf_fatos_relevantes_dos_24_meses_e_o_resto_no_json(brutos: Path) -> None:
    assert pdf_investigacao.inicio_da_janela(date(2024, 12, 31)) == date(2023, 1, 1)
    assert pdf_investigacao.inicio_da_janela(date(2024, 2, 29)) == date(2022, 3, 1)
    fc = ipe.lista("777", date(2022, 4, 30), "pt", brutos)
    ls = pdf_investigacao.linhas(_inv_com(fc, "2022-04-30"))
    resumo = pdf_investigacao.FATOS["pt"]["resumo"].format(f="3", c="2")
    assert resumo.startswith("Fatos relevantes e comunicados ao mercado entregues até a data") and resumo in ls
    i = ls.index("Fatos relevantes entregues nos 24 meses antes da data (de 01/05/2020 a 30/04/2022):")
    assert ls[i + 1] == "- 12/03/2021: Aumento de capital (reapresentação) (versão 2)"
    assert ls[i + 2].startswith("- 10/03/2021: ")
    assert not any("Apresentação de resultados" in x for x in ls)  # comunicado: só a contagem no PDF
    assert pdf_investigacao.FATOS["pt"]["resto"] in ls
    fc = ipe.lista("777", date(2024, 12, 31), "en", brutos)
    ls = pdf_investigacao.linhas(_inv_com(fc, "2024-12-31", "en"))
    i = ls.index("Material facts filed in the 24 months before the date (from 2023-01-01 to 2024-12-31):")
    assert ls[i + 1] == "- 2024-06-01: Recuperação judicial ajuizada" and not ls[i + 2].startswith("- 2021")


def test_pdf_sem_fato_relevante_na_janela(brutos: Path) -> None:
    fc = ipe.lista("777", date(2023, 12, 31), "pt", brutos)
    ls = pdf_investigacao.linhas(_inv_com(fc, "2023-12-31"))
    assert "Nenhum fato relevante entregue nos 24 meses antes da data (de 01/01/2022 a 31/12/2023)." in ls


def test_assuntos_omitidos_na_documentacao() -> None:
    n = json.loads(ipe.NUMEROS.read_text(encoding="utf-8"))
    assert n["documentos"] == sum(x["documentos"] for x in n["por_categoria"].values())
    assert n["assuntos_omitidos"] == sum(x["assuntos_omitidos"] for x in n["por_categoria"].values())
    pct_pt = f"{100 * n['assuntos_omitidos'] / n['documentos']:.1f}".replace(".", ",")
    pt = (base.RAIZ / "docs" / "contratos.md").read_text(encoding="utf-8")
    en = (base.RAIZ / "docs" / "en" / "contracts.md").read_text(encoding="utf-8")
    assert f"{n['assuntos_omitidos']:,} de {n['documentos']:,}".replace(",", ".") + f" assuntos ({pct_pt}%)" in pt
    assert f"{n['assuntos_omitidos']:,} of {n['documentos']:,} subjects ({pct_pt.replace(',', '.')}%)" in en


def test_exemplos_com_a_lista_ate_a_data() -> None:
    for nome in ("americanas_2021_em_2022-04-30_pt", "americanas_2021_em_2024-12-31_en"):
        inv = json.loads((base.RAIZ / "docs" / "exemplos" / f"{nome}.json").read_text(encoding="utf-8"))
        fc = FatosEComunicados.model_validate(inv["o_que_se_sabia"]["fatos_e_comunicados"])
        assert fc.itens and all(x.data_entrega <= inv["data_referencia"] for x in fc.itens)
        assert all(x.fonte.arquivo == f"ipe_cia_aberta_{x.data_entrega[:4]}.zip" for x in fc.itens)
