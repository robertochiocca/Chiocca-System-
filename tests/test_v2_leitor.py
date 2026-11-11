"""Leitor de documentos da Fase F1: texto e conferência literal, detector de nomes, partes relacionadas, risco
sacado, relatório do auditor, Formulário de Referência, acesso ao ENET (sem rede), avaliação no conjunto adversarial
de desenvolvimento, a seção da investigação e o interruptor do pré-registro."""

from __future__ import annotations

import hashlib
import io
import json
import zipfile
from datetime import date
from pathlib import Path
from typing import Any

import pytest

from chiocca import base
from chiocca.v2 import pdf_simples
from chiocca.v2.exibicao import textos_com_sinal_de_menos
from chiocca.v2.leitor import (
    avaliacao,
    enet_documentos,
    formulario,
    ler,
    nomes,
    parecer,
    partes_relacionadas,
    risco_sacado,
    secao,
    texto,
)
from chiocca.v2.modelos import LeituraDocumental

CASOS = base.RAIZ / "tests" / "leitor" / "casos" / "desenvolvimento"
MEDIDA = base.RAIZ / "docs" / "leitor_medida.json"
DESENVOLVIMENTO = base.RAIZ / "docs" / "leitor_desenvolvimento.json"


def _pdf(*paginas: list[str]) -> bytes:
    return pdf_simples.gerar_pdf([list(p) for p in paginas], [[] for _ in paginas])


# ---- texto e conferência literal ----


def test_conferencia_literal_so_normaliza_espacos() -> None:
    pagina = "A Companhia   aluga\nimóvel da controladora."
    assert texto.confere("aluga imóvel da", pagina)
    assert not texto.confere("aluga o imóvel", pagina)
    assert not texto.confere("", pagina)
    assert texto.busca("contro- ladora e garan- tias") == "controladora e garantias"


def test_pdf_sem_camada_de_texto_nao_e_lido() -> None:
    assert texto.paginas_do_pdf(_pdf([], [])).status == "nao_lido"
    assert texto.paginas_do_pdf(b"isto nao e pdf").motivo == "pdf_invalido"
    lido = texto.paginas_do_pdf(_pdf(["12. Partes relacionadas", "A Companhia aluga imóvel da controladora " * 3]))
    assert lido.status == "lido" and "Partes relacionadas" in lido.paginas[0]


# ---- detector de nomes de pessoa física (regra de 11/11/2026) ----


@pytest.mark.parametrize(
    "frase",
    [
        "Empréstimo concedido ao Sr. Almeida.",
        "A Dra. Paula prestou serviços.",
        "inscrito no CPF 123.456.789-09",
        "O acionista João Carlos Pereira concedeu aval.",
        "MARCOS FICTÍCIO TAVARES - mútuo a receber 1.500 1.200",
        "O conselheiro Ana de Fictícia Souza é sócio.",
        "aporte de J. P. Fictício, acionista",
        "A Fundação Maria Souza recebeu doações.",
    ],
)
def test_detector_marca_nome_de_pessoa(frase: str) -> None:
    assert nomes.tem_nome_de_pessoa(frase)


@pytest.mark.parametrize(
    "frase",
    [
        "A Companhia aluga imóvel da controladora Exemplo Participações S.A., em condições de mercado.",
        "O Conselho de Administração aprovou a Remuneração do Pessoal-Chave da Administração.",
        "Transações com Partes Relacionadas",
        "Em 31 de Dezembro de 2021, o saldo era de R$ 1.000 mil.",
        "Sede em São Paulo e filial no Rio de Janeiro.",
        "Lojas Americanas S.A. (i) - Aluguel Sede, Centros de distribuição e diversos",
        "Principais Assuntos de Auditoria PAA Reestruturação societária",
    ],
)
def test_detector_nao_marca_empresa_termo_ou_lugar(frase: str) -> None:
    assert not nomes.tem_nome_de_pessoa(frase)


def test_lista_de_companhias_do_cadastro_versionada() -> None:
    linhas = nomes.ARQUIVO_COMPANHIAS.read_text(encoding="utf-8").splitlines()
    assert linhas[0].startswith("# Gerado por python -m chiocca.v2.leitor.excecoes")
    assert "lojas americanas" in nomes.companhias() and len(nomes.companhias()) > 2000


# ---- partes relacionadas ----


def test_nota_inteira_vence_subtitulo_de_politica_e_sumario() -> None:
    paginas = [
        "Índice\n9. Partes relacionadas ......... 25\n2.15 Partes relacionadas\nAs transações com controladas são"
        " eliminadas.\n2.16 Imobilizado",
        "18. Partes relacionadas\nA Companhia presta serviços à controladora Exemplo S.A.\n"
        "19. Patrimônio líquido\nTexto.",
    ]
    nota, trechos = partes_relacionadas.ler(paginas)
    assert nota is not None and nota.titulo.startswith("18.") and (nota.pagina_inicio, nota.pagina_fim) == (2, 2)
    assert {(t.rotulo, t.pagina) for t in trechos if t.verificacao == "partes_relacionadas"} == {("controladora", 2)}


def test_nota_em_romano_so_termina_em_romano() -> None:
    paginas = ["XII. PARTES RELACIONADAS\nI - Saldos com a controlada Exemplo Ltda. a receber\nXIII. ESTOQUES\nTexto"]
    nota, trechos = partes_relacionadas.ler(paginas)
    assert nota is not None and nota.titulo.startswith("XII")
    assert ("controladas", 1) in {(t.rotulo, t.pagina) for t in trechos}


def test_controladora_como_coluna_nao_vira_parte() -> None:
    paginas = [
        "6. Partes relacionadas\nOs saldos na controladora e no consolidado:\n\nControladora Consolidado\n"
        "Controladas 4.300 3.900 - -\n7. Intangível"
    ]
    _, trechos = partes_relacionadas.ler(paginas)
    assert "controladora" not in {t.rotulo for t in trechos}


# ---- risco sacado ----


def test_risco_sacado_com_e_sem_negacao() -> None:
    afirmativa = risco_sacado.ler(["A Companhia mantém operações de risco sacado (forfait) com bancos."])
    negativa = risco_sacado.ler(["A Companhia não possui operações de risco sacado ou convênios com fornecedores."])
    depois = risco_sacado.ler(["As operações de risco sacado não são classificadas como empréstimos."])
    assert [t.negacao for t in afirmativa] == [False] and [t.negacao for t in negativa] == [True]
    assert [t.negacao for t in depois] == [False]  # negação depois do termo não é menção negativa
    assert risco_sacado.ler(["Fornecedores nacionais 45.000 38.000"]) == []


# ---- relatório do auditor ----


def test_tipo_do_parecer_pelo_titulo_e_pelo_texto() -> None:
    assert parecer.tipo("Relatório do Auditor Independente - Com Ressalva", "") == "com_ressalva"
    assert parecer.tipo("Relatório do Auditor Independente - Adverso", "") == "adversa"
    assert parecer.tipo("Relatório do Auditor Independente", "Abstenção de opinião Fomos contratados") == "abstencao"
    assert parecer.tipo(None, "Opinião Examinamos as demonstrações") == "sem_ressalva"


def test_secoes_do_parecer_e_corte_literal() -> None:
    txt = (
        "Opinião Examinamos as demonstrações. Ênfase Chamamos a atenção para a nota 1, que descreve a reorganização. "
        "Principais assuntos de auditoria "
        + "Reconhecimento de receita foi testado. " * 60
        + "Responsabilidades da administração A administração é responsável."
    )
    tipo, trechos = parecer.ler("Relatório do Auditor Independente - Sem Ressalva", txt)
    rotulos = {t.rotulo: t for t in trechos}
    assert tipo == "sem_ressalva" and set(rotulos) == {"enfase", "principais_assuntos"}
    assert rotulos["principais_assuntos"].cortado and texto.confere(rotulos["principais_assuntos"].texto, txt)


# ---- Formulário de Referência ----


def test_linha_do_formulario_omite_pessoa_fisica() -> None:
    pf = formulario.linha({"Parte_Relacionada": "Paulo Fictício Andrade", "Tipo_Pessoa": "PF"}, "pt")
    vazio = formulario.linha({"Parte_Relacionada": "Exemplo Holding S.A.", "Tipo_Pessoa": ""}, "pt")
    pj = formulario.linha(
        {
            "Parte_Relacionada": "Exemplo Holding S.A.",
            "Tipo_Pessoa": "PJ",
            "Objeto_Contrato": "Aluguel do imóvel do Sr. Paulo Andrade",
        },
        "pt",
    )
    pj_nome = formulario.linha({"Parte_Relacionada": "Ana Fictícia", "Tipo_Pessoa": "PJ"}, "pt")
    assert pf["parte_omitida"] and pf["parte"] == "parte relacionada (nome omitido)"
    assert vazio["parte_omitida"] and pj_nome["parte_omitida"]
    assert not pj["parte_omitida"] and pj["parte"] == "Exemplo Holding S.A."
    assert pj["objeto"] == "texto omitido (nome de pessoa física)"


def _fre(pasta: Path, ano: int, versoes: list[tuple[str, str]], linhas: list[str]) -> None:
    idx = "CNPJ_CIA;DT_REFER;VERSAO;DENOM_CIA;CD_CVM;CATEG_DOC;ID_DOC;DT_RECEB;LINK_DOC\n" + "".join(
        f"00.000.000/0001-00;{ano}-01-01;{v};EXEMPLO S.A.;000100;FRE;{i};{d};x\n" for i, (v, d) in enumerate(versoes, 1)
    )
    cab = (
        "CNPJ_Companhia;Data_Referencia;Versao;ID_Documento;Nome_Companhia;Parte_Relacionada;Tipo_Pessoa;"
        "Relacao_Emissor;Objeto_Contrato;Montante_Envolvido\n"
    )
    with zipfile.ZipFile(pasta / f"fre_cia_aberta_{ano}.zip", "w") as z:
        z.writestr(f"fre_cia_aberta_{ano}.csv", idx.encode("latin1"))
        z.writestr(f"fre_cia_aberta_transacao_parte_relacionada_{ano}.csv", (cab + "".join(linhas)).encode("latin1"))


def test_formulario_so_ultima_versao_e_so_se_entregue_ate_a_data(tmp_path: Path) -> None:
    formulario._tabelas.cache_clear()
    _fre(
        tmp_path,
        2022,
        [("1", "2022-05-30"), ("2", "2022-09-10")],
        [
            "00.000.000/0001-00;2022-01-01;2;2;EXEMPLO S.A.;Exemplo Holding S.A.;PJ;Controladora;"
            '"Aluguel" da sede;1000\n',
            "00.000.000/0001-00;2022-01-01;2;2;EXEMPLO S.A.;Paulo Fictício;PF;Diretor;Mútuo;500\n",
        ],
    )
    antes = formulario.transacoes("100", 2021, date(2022, 6, 30), "pt", tmp_path)
    depois = formulario.transacoes("100", 2021, date(2024, 12, 31), "pt", tmp_path)
    assert antes["status"] == "nao_disponivel_na_data" and antes["motivo"] == "não disponível na data"
    assert depois["status"] == "disponivel" and depois["documento"]["versao"] == 2
    assert depois["documento"]["linhagem"].startswith("única versão disponível nos dados abertos")
    assert [x["parte"] for x in depois["linhas"]] == ["Exemplo Holding S.A.", "parte relacionada (nome omitido)"]
    assert depois["linhas"][0]["objeto"] == '"Aluguel" da sede'  # aspas soltas lidas como vieram
    assert formulario.transacoes("100", 2015, date(2024, 12, 31), "pt", tmp_path)["status"] == "sem_formulario"
    assert formulario.transacoes("100", 2023, date(2024, 12, 31), "pt", tmp_path)["status"] == "sem_formulario"


# ---- acesso ao ENET (sem rede) ----


def test_integridade_do_pdf() -> None:
    bom = _pdf(["texto"])
    assert enet_documentos.confere_pdf(bom) == 1
    with pytest.raises(enet_documentos.FalhaDocumento):
        enet_documentos.confere_pdf(b"<html>erro</html>")
    with pytest.raises(enet_documentos.FalhaDocumento):
        enet_documentos.confere_pdf(bom[: len(bom) // 2])  # cortado: sem %%EOF


def test_texto_do_relatorio_do_enet() -> None:
    pagina = (
        "<h2 id='TituloTabelaSemBorda'>Relatório do Auditor Independente  - Sem Ressalva</h2><br />"
        "<div style='white-space: pre-line;'>Opinião Examinamos &quot;Companhia&quot;" + " texto" * 60 + "</div>"
    )
    titulo, corpo = enet_documentos.texto_do_relatorio(pagina)
    assert titulo == "Relatório do Auditor Independente - Sem Ressalva" and '"Companhia"' in corpo


def test_tentativas_com_espera_crescente(monkeypatch: pytest.MonkeyPatch) -> None:
    esperas: list[float] = []
    monkeypatch.setattr(enet_documentos.time, "sleep", esperas.append)
    chamadas = {"n": 0}

    def instavel(_: str) -> str:
        chamadas["n"] += 1
        if chamadas["n"] < 3:
            raise enet_documentos.FalhaDocumento("download incompleto")
        return "ok"

    assert enet_documentos._com_tentativas(instavel, "1") == "ok" and esperas == [2, 4]
    with pytest.raises(enet_documentos.FalhaDocumento):
        enet_documentos._com_tentativas(lambda _: (_ for _ in ()).throw(OSError("rede")), "1")
    assert esperas[2:] == [2, 4, 8, 16]


def test_requisicao_recusa_corpo_cortado(monkeypatch: pytest.MonkeyPatch) -> None:
    class Resposta(io.BytesIO):
        headers = {"Content-Length": "100"}

        def __enter__(self) -> Resposta:
            return self

        def __exit__(self, *_: Any) -> None:
            return None

    class Abridor:
        def open(self, *_: Any, **__: Any) -> Resposta:
            return Resposta(b"so 22 bytes de conteudo")

    monkeypatch.setattr(enet_documentos, "INTERVALO", 0)
    with pytest.raises(enet_documentos.FalhaDocumento, match="incompleto"):
        enet_documentos._pede(Abridor(), "https://exemplo")  # type: ignore[arg-type]


def _cache_de_teste(pasta: Path, num_doc: str, pdf: bytes, relatorio: str) -> None:
    d = pasta / num_doc
    d.mkdir(parents=True)
    (d / "notas.pdf").write_bytes(pdf)
    (d / "notas.json").write_text(
        json.dumps(
            {
                "arquivo": "notas.pdf",
                "sha256": hashlib.sha256(pdf).hexdigest(),
                "url": "https://exemplo/notas",
                "paginas": 1,
            }
        )
    )
    (d / "relatorio.txt").write_text(relatorio, encoding="utf-8")
    (d / "relatorio.json").write_text(
        json.dumps(
            {
                "arquivo": "relatorio.txt",
                "titulo": "Relatório do Auditor " "Independente - Com Ressalva",
                "sha256": hashlib.sha256(relatorio.encode()).hexdigest(),
            }
        )
    )


def test_cache_sem_rede(tmp_path: Path) -> None:
    pdf = _pdf(["texto"])
    _cache_de_teste(tmp_path, "777", pdf, "Opinião com ressalva Texto." * 20)
    assert enet_documentos.notas("777", tmp_path, rede=False)[0] == pdf
    assert enet_documentos.notas("888", tmp_path, rede=False) == (None, {"fora_do_cache": True})
    (tmp_path / "777" / "notas.pdf").write_bytes(b"alterado")  # hash diferente: não serve o cache (iria à rede)
    with pytest.raises(Exception):
        enet_documentos._cache(
            "777", "notas", lambda _: (_ for _ in ()).throw(enet_documentos.FalhaDocumento("x")), tmp_path
        )


# ---- avaliação no conjunto adversarial de desenvolvimento ----


def test_casos_de_desenvolvimento_no_formato_do_pre_registro() -> None:
    casos = sorted(CASOS.glob("*.json"))
    assert len(casos) >= 20
    for arq in casos:
        assert avaliacao.valida(json.loads(arq.read_text(encoding="utf-8"))) == [], arq.name


def test_avaliacao_recusa_caso_fora_do_formato() -> None:
    assert avaliacao.valida({"id": "x", "esperado": {"itens": [{"verificacao": "outra"}]}, "extra": 1})
    with pytest.raises(ValueError):
        avaliacao.avaliar_caso({"id": "x", "notas": {"paginas": [["a"]]}, "esperado": {"itens": []}})


def test_resultado_de_desenvolvimento_igual_ao_publicado() -> None:
    """O resultado nos casos de desenvolvimento (informativo, não é a medida) é o de docs/leitor_desenvolvimento.json,
    e cumpre as duas exigências: conferência literal em 100% e zero nome vazado."""
    r = avaliacao.avaliar(CASOS)
    publicado = json.loads(DESENVOLVIMENTO.read_text(encoding="utf-8"))
    assert r["totais"] == publicado["totais"] and r["leitor"] == publicado["leitor"]
    assert r["totais"]["conferidos"] == r["totais"]["trechos_mostrados"] and r["totais"]["nomes_vazados"] == 0


def test_nome_vazado_reprova(monkeypatch: pytest.MonkeyPatch) -> None:
    caso = json.loads((CASOS / "d11_nome_com_tratamento.json").read_text(encoding="utf-8"))
    monkeypatch.setattr(nomes, "tem_nome_de_pessoa", lambda _: False)
    assert avaliacao.avaliar_caso(caso).nomes_vazados == ["Ernesto Fictício Barbosa"]


# ---- seção da investigação e interruptor ----


def test_secao_no_contrato_e_sem_rede(tmp_path: Path) -> None:
    caso = json.loads((CASOS / "d05_garantias_pcld.json").read_text(encoding="utf-8"))
    rel = json.loads((CASOS / "d16_parecer_com_ressalva.json").read_text(encoding="utf-8"))["parecer"]["texto"]
    pdf = avaliacao.pdf_do_caso(caso)
    assert pdf is not None
    _cache_de_teste(tmp_path, "555", pdf, rel)
    for lang in ("pt", "en"):
        s = secao.secao("555", 1, "2022-03-01", "100", 2021, date(2024, 12, 31), lang, pasta=tmp_path, brutos=tmp_path)
        m = LeituraDocumental.model_validate(s)
        assert m.gera_alerta is False and m.partes_relacionadas.nota is not None
        assert m.relatorio_do_auditor.tipo == "com_ressalva" and m.formulario_de_referencia.status == "sem_formulario"
        assert all(t.conferido for t in m.partes_relacionadas.trechos)
    fora = secao.secao("556", 1, "2022-03-01", "100", 2021, date(2024, 12, 31), "pt", pasta=tmp_path, brutos=tmp_path)
    assert fora["partes_relacionadas"]["motivo"] == "documento ainda não baixado do ENET"


def test_interruptor_so_liga_com_a_medida_aprovada() -> None:
    """Pré-registro (docs/pre-registro-leitor.md, seção 3): a seção só entra na investigação se o leitor congelado
    atingir as quatro metas nos casos guardados, registradas em docs/leitor_medida.json."""
    if secao.LIGADO:
        medida = json.loads(MEDIDA.read_text(encoding="utf-8"))
        assert medida["aprovado"] and all(medida["atingidas"].values())
    else:
        assert not MEDIDA.exists() or not json.loads(MEDIDA.read_text(encoding="utf-8"))["aprovado"]


def test_exemplos_sem_a_secao_enquanto_desligada() -> None:
    for arq in (base.RAIZ / "docs" / "exemplos").glob("*.json"):
        assert "leitura_documental" not in json.loads(arq.read_text(encoding="utf-8")), arq.name


def test_secao_fica_fora_do_sinal_de_menos() -> None:
    x = {"texto": "saldo -5", "leitura_documental": {"partes_relacionadas": {"trechos": [{"texto": "saldo -5"}]}}}
    out = textos_com_sinal_de_menos(x)
    assert (
        out["texto"] == "saldo −5"
        and out["leitura_documental"]["partes_relacionadas"]["trechos"][0]["texto"] == "saldo -5"
    )


def test_leitura_pura_sem_documentos() -> None:
    s = ler.ler(None, None, None, "pt", "sem notas", "sem relatório")
    m = LeituraDocumental.model_validate(
        s | {"formulario_de_referencia": {"status": "sem_formulario", "motivo": "x", "linhas": []}}
    )
    assert m.partes_relacionadas.status == "nao_lido" and m.risco_sacado.encontrado is None


# ---- contrato do web: a seção guardada para os testes da interface ----

CONTRATO_WEB = base.RAIZ / "web" / "tests" / "contrato"
PAGINAS_DA_FIXTURE = [
    [
        "11. Transações com partes relacionadas",
        "A controladora prestou aval em empréstimos da controlada Exemplo Energia S.A.,",
        "no montante de R$ 30.000 mil, em condições de mercado.",
        "",
        "O imóvel da sede pertence ao Sr. Ernesto Fictício Barbosa, acionista controlador.",
        "",
        "12. Fornecedores",
        "A Companhia mantém operações de risco sacado com bancos de primeira linha.",
    ]
]


def test_secao_guardada_para_o_contrato_do_web(tmp_path: Path) -> None:
    """A seção, gerada pelo leitor com documentos fictícios, fica em web/tests/contrato/ para os testes da interface
    (o mesmo esquema de tests/test_v2_contrato_web.py; para regerar: CHIOCCA_REGERAR_CONTRATO_WEB=1)."""
    import os

    formulario._tabelas.cache_clear()
    rel = json.loads((CASOS / "d16_parecer_com_ressalva.json").read_text(encoding="utf-8"))["parecer"]["texto"]
    _cache_de_teste(tmp_path, "555", _pdf(*PAGINAS_DA_FIXTURE), rel)
    _fre(
        tmp_path,
        2022,
        [("1", "2022-05-30")],
        [
            "00.000.000/0001-00;2022-01-01;1;1;EXEMPLO S.A.;Exemplo Holding S.A.;PJ;Controladora;"
            "Aluguel da sede;1000\n",
            "00.000.000/0001-00;2022-01-01;1;1;EXEMPLO S.A.;Paulo Fictício Andrade;PF;Diretor;Mútuo;500\n",
        ],
    )
    regerar = os.environ.get("CHIOCCA_REGERAR_CONTRATO_WEB") == "1"
    for lang in ("pt", "en"):
        s = secao.secao("555", 1, "2022-03-01", "100", 2021, date(2024, 12, 31), lang, pasta=tmp_path, brutos=tmp_path)
        s["formulario_de_referencia"]["documento"]["arquivo"] = "fre_cia_aberta_2022.zip"
        LeituraDocumental.model_validate(s)
        texto_saida = json.dumps(s, ensure_ascii=False)
        assert "Ernesto" not in texto_saida and "Paulo Fictício" not in texto_saida
        caminho = CONTRATO_WEB / f"leitura_documental_{lang}.json"
        if regerar:
            caminho.write_text(json.dumps(s, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
        assert json.loads(caminho.read_text(encoding="utf-8")) == s, lang
    formulario._tabelas.cache_clear()


def test_secao_no_pdf_com_trechos_literais_e_sem_nomes() -> None:
    import pypdf

    from chiocca.v2 import pdf_investigacao

    for lang in ("pt", "en"):
        inv = json.loads((base.RAIZ / "docs" / "exemplos" / f"americanas_2021_em_2024-12-31_{lang}.json").read_text())
        inv["leitura_documental"] = json.loads((CONTRATO_WEB / f"leitura_documental_{lang}.json").read_text())
        pdf = pdf_investigacao.gerar(inv)
        txt = " ".join(p.extract_text() or "" for p in pypdf.PdfReader(io.BytesIO(pdf)).pages)
        assert ("Notas explicativas" if lang == "pt" else "Explanatory notes") in txt
        assert "A controladora prestou aval" in txt and "Ernesto" not in txt and "Paulo Fictício" not in txt


def test_contratos_com_o_numero_de_casos_de_desenvolvimento() -> None:
    n = len(list(CASOS.glob("*.json")))
    assert f"{n} casos de desenvolvimento" in (base.RAIZ / "docs" / "contratos.md").read_text(encoding="utf-8")
    assert f"{n} development cases" in (base.RAIZ / "docs" / "en" / "contracts.md").read_text(encoding="utf-8")


def test_parecer_titulo_com_complemento_e_formato_antigo() -> None:
    novo = (
        "Opinião com ressalva sobre as demonstrações contábeis individuais e consolidadas Examinamos as demonstrações. "
        "Base para opinião com ressalva sobre as demonstrações contábeis individuais e consolidadas A Companhia não "
        "registrou a provisão para perdas. Responsabilidades da administração A administração é responsável."
    )
    antigo = (
        "Examinamos as demonstrações financeiras. Acreditamos que a evidência de auditoria obtida é suficiente e "
        "apropriada para fundamentar nossa opinião. A companhia não vem reconhecendo os encargos financeiros sobre "
        "empréstimos. Opinião Em nossa opinião, exceto quanto aos efeitos do parágrafo anterior, as demonstrações "
        "representam adequadamente a posição patrimonial."
    )
    tipo, trechos = parecer.ler("Relatório do Auditor Independente", novo)
    assert tipo == "com_ressalva" and [t.rotulo for t in trechos] == ["base_para_ressalva"]
    tipo, trechos = parecer.ler("Relatório do Auditor Independente - Com Ressalva", antigo)
    assert [t.rotulo for t in trechos] == ["base_para_ressalva"]
    assert trechos[0].texto.startswith("A companhia não vem reconhecendo os encargos")
    assert texto.confere(trechos[0].texto, antigo)
    # sem ressalva, o formato antigo não inventa base para ressalva
    assert parecer.ler("Relatório do Auditor Independente - Sem Ressalva", antigo)[1] == []


def test_texto_girado_usa_o_modo_simples() -> None:
    import logging

    class Pagina:
        def extract_text(self, extraction_mode: str = "plain") -> str:
            if extraction_mode == "layout":
                logging.getLogger("pypdf._text_extraction").warning(
                    "Rotated text discovered. Output will be incomplete."
                )
                return "parcial"
            return "texto completo com a tabela girada"

    assert texto._texto_da_pagina(Pagina()) == "texto completo com a tabela girada"  # type: ignore[arg-type]
