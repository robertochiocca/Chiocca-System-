"""Fatos relevantes e comunicados ao mercado (Fase F2a): só metadados do IPE até a data, nunca depois de 31/12/2024,
um item por documento entregue, o assunto pela regra própria do assunto (em uso desde 13/11/2026, medida e auditada
na F2b; as regras de 12/11/2026 ficam só para reproduzir as comparações), o assunto vazio com aviso, as versões e os
repetidos numa linha só, o aviso dos links antigos, ordem fixa que não depende do assunto, linhagem de cada item, a
exibição no PDF (24 meses) e os números da documentação."""

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
           seq: int | None = None, link: str | None = None) -> str:  # fmt: skip
    """Uma linha do IPE como na CVM: o link traz numProtocolo, numSequencia e numVersao (o documento)."""
    n = seq if seq is not None else zlib.crc32(f"{protocolo}|{versao}".encode()) % 900_000 + 100_000
    link = (
        link
        or f"https://www.rad.cvm.gov.br/ENET/frmDownloadDocumento.aspx?numProtocolo={n}&numSequencia={n}&numVersao={versao}"
    )
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
    assert "3 documentos de fato relevante e 2 documentos de comunicado ao mercado" in resumo
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


def test_assuntos_omitidos_e_vazios_na_documentacao() -> None:
    n = json.loads(ipe.NUMEROS.read_text(encoding="utf-8"))
    motivos = [f"omitidos_{m}" for m in ipe.MOTIVOS]
    for k in ("documentos", "assuntos_vazios", "assuntos_omitidos", *motivos, "assuntos_mostrados"):
        assert n[k] == sum(x[k] for x in n["por_categoria"].values()), k
    assert n["documentos"] == n["assuntos_vazios"] + n["assuntos_omitidos"] + n["assuntos_mostrados"]
    assert n["assuntos_omitidos"] == sum(n[k] for k in motivos) and n["regra"] == "assunto-ipe-1"
    f2a = n["regras_f2a"]
    assert f2a["documentos"] == f2a["assuntos_vazios"] + f2a["assuntos_omitidos"] + f2a["assuntos_mostrados"]
    assert f2a["assuntos_vazios"] == n["assuntos_vazios"]
    pt = (base.RAIZ / "docs" / "contratos.md").read_text(encoding="utf-8")
    en = (base.RAIZ / "docs" / "en" / "contracts.md").read_text(encoding="utf-8")

    def br(x: int) -> str:
        return f"{x:,}".replace(",", ".")

    for x in (n, f2a):
        pct = f"{100 * x['assuntos_omitidos'] / x['documentos']:.1f}"
        assert f"{br(x['assuntos_omitidos'])} de {br(x['documentos'])} assuntos ({pct.replace('.', ',')}%)" in pt
        assert f"{x['assuntos_omitidos']:,} of {x['documentos']:,} subjects ({pct}%)" in en
    for k in ("assuntos_vazios", "assuntos_mostrados", *motivos):
        assert br(n[k]) in pt and f"{n[k]:,}" in en, k


def test_regra_do_assunto_em_uso() -> None:
    """Nomes inventados. Desde 13/11/2026, a lista usa a regra própria do assunto (assunto-ipe-1), aprovada na medida
    da emenda 1 do pré-registro do leitor e na auditoria de 400 assuntos reais (docs/assunto_auditoria.json); as
    regras de 12/11/2026 (detector, maiúsculas e palavra maiúscula no meio) ficam em regra_de_omissao_f2a."""
    from chiocca.v2.leitor_f1_2 import assunto

    exemplos = ("RENÚNCIA DO DIRETOR FULANO DE TAL", "BARBOSA", "Renúncia do diretor Barbosa", "Renúncia: BARBOSA",
                "Eleição do Sr. X", "Brandacci deixa a diretoria", "Aumento de capital aprovado",
                "AUMENTO DE CAPITAL APROVADO", "Petrobras sobre venda da refinaria RLAM")  # fmt: skip
    for texto in exemplos:
        assert ipe.regra_de_omissao(texto) == assunto.motivo(texto)
    for texto in exemplos[:6]:  # com nome inventado: omitidos (a primeira palavra também conta, ao contrário de 12/11)
        mostrado, omitido, vazio = ipe.assunto(texto, "pt")
        assert omitido and not vazio and "Fulano" not in mostrado and "Barbosa" not in mostrado.title()
        assert "Brandacci" not in mostrado
    for texto in exemplos[6:]:  # sem nome: aparecem, inclusive todo em maiúsculas e com nome de companhia
        assert ipe.assunto(texto, "pt") == (texto, False, False)
    assert ipe.regra_de_omissao_f2a("Brandacci deixa a diretoria") is None  # a brecha da primeira palavra em 12/11
    assert ipe.regra_de_omissao_f2a("AUMENTO DE CAPITAL APROVADO") is not None
    assert ipe.assunto("  ", "pt") == ("sem assunto nos dados abertos; ver o documento na CVM", False, True)
    assert ipe.assunto("", "en") == ("no subject in the open data; see the document at the CVM", False, True)
    auditoria = json.loads((base.RAIZ / "docs" / "assunto_auditoria.json").read_text(encoding="utf-8"))
    assert auditoria["leitura"]["lidos"] == 400 and auditoria["leitura"]["com_nome_de_pessoa_fisica"] == 0


def _proto(seq: int, versao: int) -> str:
    return f"000777IPE13012023{versao:02d}0449{seq:04d}-11"


def test_versoes_e_repetidos_numa_linha_e_links_antigos(tmp_path: Path) -> None:
    antigo = "https://www.rad.cvm.gov.br/ENET/frmDownloadDocumento.aspx?numProtocolo=321741&numSequencia=0&numVersao=0"
    _ipe(tmp_path, 2023, [
        _linha("777", "Fato Relevante", "Tutela de urgência cautelar", "2023-01-13", _proto(3912, 1), 1, seq=11),
        _linha("777", "Fato Relevante", "Tutela de urgência cautelar", "2023-01-13", _proto(3912, 2), 2, seq=12),
        _linha("777", "Fato Relevante", "Esclarecimentos sobre notícia", "2023-01-12", "P8", 1, seq=13),
        _linha("777", "Fato Relevante", "Esclarecimentos sobre notícia", "2023-01-12", "P9", 1, seq=14),
        _linha("777", "Fato Relevante", "", "2023-01-20", _proto(4000, 1), 1, seq=15),
        _linha("777", "Fato Relevante", "", "2023-01-20", _proto(4000, 2), 2, seq=16),
        _linha("777", "Fato Relevante", "Outro assunto", "2023-01-11", "P10", 1, seq=17, link=antigo),
    ])  # fmt: skip
    ipe._ano.cache_clear()
    fc = ipe.lista("777", date(2023, 12, 31), "pt", tmp_path)
    FatosEComunicados.model_validate(fc)
    assert len(fc["itens"]) == 7 and fc["contagem"]["fato_relevante"] == 7  # o JSON: um item por versão
    grupos: dict[int, list[str]] = {}
    for x in fc["itens"]:
        grupos.setdefault(x["grupo"], []).append(x["id_documento"])
    assert sorted(len(v) for v in grupos.values()) == [1, 2, 2, 2]
    vazios = [x for x in fc["itens"] if x["assunto_vazio"]]
    assert len(vazios) == 2 and len({x["grupo"] for x in vazios}) == 1  # vazios juntos só pelo protocolo
    assert [x["link_pode_nao_abrir"] for x in fc["itens"] if x["protocolo"] == "P10"] == [True]
    assert not any(x["link_pode_nao_abrir"] for x in fc["itens"] if x["protocolo"] != "P10")
    ls = pdf_investigacao.linhas(_inv_com(fc, "2023-12-31"))
    assert "- 20/01/2023: sem assunto nos dados abertos; ver o documento na CVM (versões 1 e 2)" in ls
    assert "- 13/01/2023: Tutela de urgência cautelar (versões 1 e 2)" in ls
    assert "- 12/01/2023: Esclarecimentos sobre notícia (2 documentos)" in ls
    assert sum(1 for x in ls if "Tutela de urgência cautelar" in x) == 1


def test_exemplos_com_a_lista_ate_a_data() -> None:
    for nome in ("americanas_2021_em_2022-04-30_pt", "americanas_2021_em_2024-12-31_en"):
        inv = json.loads((base.RAIZ / "docs" / "exemplos" / f"{nome}.json").read_text(encoding="utf-8"))
        fc = FatosEComunicados.model_validate(inv["o_que_se_sabia"]["fatos_e_comunicados"])
        assert fc.itens and all(x.data_entrega <= inv["data_referencia"] for x in fc.itens)
        assert all(x.fonte.arquivo == f"ipe_cia_aberta_{x.data_entrega[:4]}.zip" for x in fc.itens)
