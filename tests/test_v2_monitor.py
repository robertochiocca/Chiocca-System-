"""Monitor da CVM (Fase F2a): índice lido de dentro do zip remoto por faixas de bytes (com CRC32), comparação com o
armazenado, fila de revisão com metadados e hash, nada depois de 31/12/2024 além de metadados e hash (sem o assunto),
e nenhum dado mudado (data/brutos fica igual)."""

from __future__ import annotations

import hashlib
import io
import json
import random
import zipfile
import zlib
from pathlib import Path

import pytest

from chiocca.v2 import monitor

CAB_DFP = "CNPJ_CIA;DT_REFER;VERSAO;DENOM_CIA;CD_CVM;CATEG_DOC;ID_DOC;DT_RECEB;LINK_DOC"
CAB_IPE = (
    "CNPJ_Companhia;Nome_Companhia;Codigo_CVM;Data_Referencia;Categoria;Tipo;Especie;Assunto;Data_Entrega;"
    "Tipo_Apresentacao;Protocolo_Entrega;Versao;Link_Download"
)


def _dfp(cd: str, refer: str, versao: int, id_doc: str, receb: str) -> str:
    return f"00.000.000/0001-00;{refer};{versao};EXEMPLO S.A.;{cd};DFP;{id_doc};{receb};https://www.rad.cvm.gov.br/x?{id_doc}"


def _ipe(assunto: str, entrega: str, protocolo: str, versao: int = 1) -> str:
    return (f"00.000.000/0001-00;EXEMPLO S.A.;777;{entrega};Fato Relevante;Outros;;{assunto};{entrega};"
            f"AP - Apresentação;{protocolo};{versao};https://www.rad.cvm.gov.br/ENET/x?{protocolo}")  # fmt: skip


def _csv(cab: str, linhas: list[str]) -> bytes:
    return ("\n".join([cab, *linhas]) + "\n").encode("latin1")


def _zip(membros: dict[str, bytes]) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        for nome, dados in membros.items():
            z.writestr(nome, dados)
    return buf.getvalue()


def test_membro_remoto_por_faixas_sem_baixar_o_resto() -> None:
    indice = _csv(CAB_DFP, [_dfp("777", "2021-12-31", 1, "100", "2022-03-01")])
    grande = random.Random(1).randbytes(2_000_000)  # as demonstrações (incompressíveis): não podem ser lidas
    arquivo = _zip({"dfp_cia_aberta_2021_BPA_con.csv": grande, "dfp_cia_aberta_2021.csv": indice})
    lidos: list[tuple[int, int]] = []

    def ler(a: int, b: int) -> bytes:
        lidos.append((a, b))
        return arquivo[a : b + 1]

    assert monitor.membro_remoto(ler, len(arquivo), "dfp_cia_aberta_2021.csv") == indice
    assert sum(b - a + 1 for a, b in lidos) < len(arquivo) // 10  # só o fim, o diretório e o próprio índice
    corrompido = bytearray(arquivo)
    info = zipfile.ZipFile(io.BytesIO(arquivo)).getinfo("dfp_cia_aberta_2021.csv")
    corrompido[info.header_offset + 30 + len(info.filename.encode()) + len(info.extra) + 5] ^= 0xFF  # dado do índice
    with pytest.raises((monitor.ZipRemotoInvalido, zlib.error)):
        monitor.membro_remoto(lambda a, b: bytes(corrompido[a : b + 1]), len(corrompido), "dfp_cia_aberta_2021.csv")


def test_comparar_novos_alterados_removidos_e_linha_de_base() -> None:
    antes = _csv(CAB_DFP, [_dfp("777", "2021-12-31", 1, "100", "2022-03-01"),
                           _dfp("888", "2021-12-31", 1, "101", "2022-03-02")])  # fmt: skip
    armazenado = {monitor.chave("DFP", r): monitor.hash_metadados(r) for r in monitor._linhas(antes)}
    agora = _csv(CAB_DFP, [_dfp("777", "2021-12-31", 1, "100", "2022-03-05"),
                           _dfp("777", "2021-12-31", 2, "102", "2025-02-01")])  # fmt: skip
    eventos = {(x["evento"], x["chave"]) for x in monitor.comparar("DFP", 2021, agora, armazenado)}
    assert eventos == {("alterado", "777|2021-12-31|1|100"), ("novo", "777|2021-12-31|2|102"),
                       ("removido_do_indice", "888|2021-12-31|1|101")}  # fmt: skip
    base = monitor.comparar("ITR", 2021, agora, None)
    h = hashlib.sha256(agora).hexdigest()
    assert base == [{"evento": "linha_de_base", "tipo": "ITR", "arquivo": "itr_cia_aberta_2021.zip",
                     "ano_arquivo": 2021, "documentos": 2, "hash_indice": h}]  # fmt: skip


def test_depois_de_31_12_2024_so_metadados_e_hash() -> None:
    linhas = [_ipe("Aumento de capital", "2024-12-30", "A"), _ipe("Assunto reservado ao estudo 2", "2025-01-02", "B")]
    r_antes, r_depois = monitor._linhas(_csv(CAB_IPE, linhas))
    antes = monitor.registro("IPE", 2024, r_antes, "novo")
    depois = monitor.registro("IPE", 2025, r_depois, "novo")
    assert antes["assunto"] == "Aumento de capital" and antes["depois_de_31_12_2024"] is False
    assert "assunto" not in depois and depois["depois_de_31_12_2024"] is True
    assert depois["hash_metadados"] == monitor.hash_metadados(r_depois)  # o assunto só entra no hash


def test_verificar_registra_na_fila_e_nao_muda_os_dados(tmp_path: Path) -> None:
    brutos, pasta = tmp_path / "brutos", tmp_path / "monitor"
    brutos.mkdir()
    ipe_2024 = _csv(CAB_IPE, [_ipe("Aumento de capital", "2024-03-01", "A")])
    (brutos / "ipe_cia_aberta_2024.zip").write_bytes(_zip({"ipe_cia_aberta_2024.csv": ipe_2024}))
    antes = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in brutos.iterdir()}
    atuais = {
        ("IPE", 2024): _csv(CAB_IPE, [_ipe("Aumento de capital", "2024-03-01", "A"),
                                      _ipe("Recompra", "2024-11-01", "C")]),  # fmt: skip
        ("IPE", 2025): _csv(CAB_IPE, [_ipe("Assunto reservado ao estudo 2", "2025-01-02", "B")]),
        ("ITR", 2025): _csv(CAB_DFP, [_dfp("777", "2025-03-31", 1, "300", "2025-05-10")]),
    }

    def buscar(tipo: str, ano: int) -> bytes:
        return atuais[(tipo, ano)]

    r = monitor.verificar(("IPE",), range(2024, 2026), pasta, brutos, buscar, lambda: "2026-11-12T00:00:00Z")
    r2 = monitor.verificar(("ITR",), range(2025, 2026), pasta, brutos, buscar, lambda: "2026-11-12T00:00:00Z")
    fila = [json.loads(x) for x in (pasta / "fila.jsonl").read_text(encoding="utf-8").splitlines()]
    assert r["novidades"] == 2 and r2["novidades"] == 1
    assert [(x["arquivo"], x["evento"]) for x in fila] == [("ipe_cia_aberta_2024.zip", "novo"),
                                                           ("ipe_cia_aberta_2025.zip", "linha_de_base"),
                                                           ("itr_cia_aberta_2025.zip", "linha_de_base")]  # fmt: skip
    assert all(x["situacao"] == "a_revisar" for x in fila)
    # de novo, sem mudança na CVM: nada novo na fila
    assert monitor.verificar(("IPE", "ITR"), range(2024, 2026), pasta, brutos, buscar, lambda: "x")["novidades"] == 0
    # um documento novo em 2025: só metadados e hash, sem o assunto, em nenhum arquivo do monitor
    atuais[("IPE", 2025)] = _csv(CAB_IPE, [_ipe("Assunto reservado ao estudo 2", "2025-01-02", "B"),
                                           _ipe("Outro assunto reservado", "2025-02-03", "D")])  # fmt: skip
    assert monitor.verificar(("IPE",), range(2025, 2026), pasta, brutos, buscar, lambda: "y")["novidades"] == 1
    tudo = "".join(p.read_text(encoding="utf-8") for p in pasta.rglob("*") if p.is_file())
    assert "reservado" not in tudo
    # os dados armazenados não mudam
    assert {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in brutos.iterdir()} == antes
    assert monitor.listar(pasta)["linhas"] == 4


def test_erro_de_rede_vai_para_o_resumo_sem_parar(tmp_path: Path) -> None:
    def buscar(tipo: str, ano: int) -> bytes:
        raise OSError("sem rede")

    r = monitor.verificar(("DFP",), range(2024, 2025), tmp_path, tmp_path, buscar, lambda: "z")
    assert r["erros"] == {"dfp_cia_aberta_2024.zip": "sem rede"} and r["novidades"] == 0


def test_chave_do_ipe_pelo_link_e_linha_repetida() -> None:
    """De 2010 a 2014 o protocolo de entrega vem vazio: a chave é o documento no link; linha repetida igual conta uma
    vez, e chave repetida com conteúdo diferente vira o hash da linha."""

    def linha(assunto: str, seq: int) -> str:
        link = f"https://www.rad.cvm.gov.br/ENET/x.aspx?numProtocolo={seq}&numSequencia=0&numVersao=0"
        return f"00.000.000/0001-00;EXEMPLO S.A.;777;2012-05-02;Fato Relevante;;;{assunto};2012-05-02;AP;;;{link}"

    linhas = monitor._linhas(_csv(CAB_IPE, [linha("A", 1), linha("A", 1), linha("B", 2), linha("C", 3), linha("D", 3)]))
    ks = monitor.chaves("IPE", linhas)
    assert ks[:3] == ["1-0-0", "1-0-0", "2-0-0"] and ks[3].startswith("linha-") and ks[4].startswith("linha-")
    assert [x["evento"] for x in monitor.comparar("IPE", 2012, _csv(CAB_IPE, [linha("A", 1)]), {})] == ["novo"]
