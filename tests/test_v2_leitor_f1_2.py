"""Fase F2b (emenda 1 do pré-registro do leitor, seção 10): a `leitor-f1-2` ao lado da `leitor-f1-1`, a regra nova do
assunto do IPE, o avaliador novo, os casos de desenvolvimento, o teste do detector (10.7, item 5) e o registro do
congelamento (docs/leitor_congelado_f1_2.json)."""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from importlib.metadata import version
from pathlib import Path
from typing import Any

import pytest

from chiocca import base
from chiocca.v2 import ipe
from chiocca.v2.leitor import avaliacao as av1
from chiocca.v2.leitor import enet_documentos, nomes, parecer, risco_sacado
from chiocca.v2.leitor import partes_relacionadas as pr1
from chiocca.v2.leitor.texto import paginas_do_pdf
from chiocca.v2.leitor.trechos import Segmento, Trecho, linha_de_tabela
from chiocca.v2.leitor_f1_2 import VERSAO, assunto, avaliacao
from chiocca.v2.leitor_f1_2 import ler as ler_f1_2
from chiocca.v2.leitor_f1_2 import partes_relacionadas as pr2

CASOS = base.RAIZ / "tests" / "leitor" / "casos"
NOVOS = CASOS / "desenvolvimento" / "f1_2"
CONGELADO = base.RAIZ / "docs" / "leitor_congelado_f1_2.json"
DESENVOLVIMENTO = base.RAIZ / "docs" / "leitor_desenvolvimento_f1_2.json"
MEDIDA = base.RAIZ / "docs" / "leitor_medida_f1_2.json"


def _json(caminho: Path) -> Any:
    return json.loads(caminho.read_text(encoding="utf-8"))


def _marcas(frase: str) -> tuple[list[str], list[str]]:
    return pr2._marcas(" ".join(frase.lower().split()))


# ---- congelamento ----


def test_leitor_f1_2_e_regra_do_assunto_congelados_nao_mudaram() -> None:
    """Emenda 1, 10.5 item 3: a `leitor-f1-2`, a regra do assunto, o avaliador novo, os módulos da f1-1 que eles usam, o
    gerador dos PDFs dos casos e as listas de palavras ficam como no commit do congelamento (o que introduz
    docs/leitor_congelado_f1_2.json). Até a medida, também as regras de hoje do assunto, medidas ao lado."""
    congelado = _json(CONGELADO)
    atuais = {str(p.relative_to(base.RAIZ)) for p in (base.RAIZ / "chiocca" / "v2" / "leitor_f1_2").glob("*.py")}
    assert atuais <= set(congelado["arquivos"]), "arquivo novo na leitor-f1-2 depois do congelamento"
    arquivos = dict(congelado["arquivos"])
    if not MEDIDA.exists():
        arquivos |= congelado["comparacao_ate_a_medida"]
    for arquivo, h in arquivos.items():
        assert (
            hashlib.sha256((base.RAIZ / arquivo).read_bytes()).hexdigest() == h
        ), f"{arquivo} mudou depois do congelamento"
    assert version("pypdf") == congelado["pypdf"]
    assert congelado["leitor"] == VERSAO == ler_f1_2.VERSAO and congelado["regra_do_assunto"] == assunto.VERSAO


def test_registro_cobre_tudo_o_que_a_f1_2_importa() -> None:
    """Todo módulo dos leitores e do IPE que a f1-2, a regra do assunto e o avaliador novo carregam (num processo
    novo), e as listas que leem, estão no registro. Ficam de fora só os módulos gerais (caminhos, cadastro da CVM e
    corte), que não decidem nada da leitura."""
    codigo = (
        "import sys, chiocca.v2.leitor_f1_2.avaliar, chiocca.v2.leitor_f1_2.assunto; "
        "print('\\n'.join(m.__file__ for n, m in sys.modules.items() if n.startswith('chiocca') and m.__file__))"
    )
    r = subprocess.run([sys.executable, "-c", codigo], cwd=base.RAIZ, capture_output=True, text=True, check=True)
    carregados = {str(Path(x).relative_to(base.RAIZ)) for x in r.stdout.split()}
    congelado = _json(CONGELADO)
    registrados = set(congelado["arquivos"]) | set(congelado["comparacao_ate_a_medida"])
    gerais = {"chiocca/__init__.py", "chiocca/base.py", "chiocca/corte.py", "chiocca/cvm.py", "chiocca/enet.py",
              "chiocca/v2/__init__.py", "chiocca/v2/lacre.py"}  # fmt: skip
    assert carregados - gerais <= registrados, sorted(carregados - gerais - registrados)
    for lista in (assunto.VOCABULARIO, assunto.MAIUSCULAS, assunto.NOMES_COMUNS, nomes.ARQUIVO_COMPANHIAS):
        assert str(lista.relative_to(base.RAIZ)) in congelado["arquivos"]
    assert "chiocca/v2/ipe.py" in congelado["comparacao_ate_a_medida"]


def test_secao_usa_a_f1_2_porque_o_criterio_de_troca_saiu_verdadeiro() -> None:
    """Decisões 2 e 3 de 10.7: os arquivos da f1-1 não mudam (o teste da f1-1 confere os hashes); a seção usa a f1-2 só
    porque, na medida única nos casos guardados novos, o critério de troca saiu verdadeiro."""
    from chiocca.v2 import investigacao, leitura_exibicao, leitura_secao
    from chiocca.v2.leitor import VERSAO as VERSAO_F1_1
    from chiocca.v2.leitor import secao as secao_f1_1

    medida = _json(MEDIDA)
    assert VERSAO == "leitor-f1-2" and VERSAO_F1_1 == "leitor-f1-1"
    assert medida["criterio_de_troca"] == {"quatro_metas_f1_2": True, "precisao_f1_2_pelo_menos_f1_1": True,
                                           "cabecalhos_f1_2_nao_mais_que_f1_1": True, "troca": True}  # fmt: skip
    assert leitura_secao.LEITOR == medida["leitor_novo"] == VERSAO and leitura_secao.LIGADO is secao_f1_1.LIGADO
    assert investigacao.leitor_secao is leitura_secao
    assert leitura_exibicao.versao() == f"leitor-f1-2 (commit {medida['commit'][:7]})"


# ---- os quatro ajustes ----


def test_ajuste_1_quem_controla_a_companhia() -> None:
    assert _marcas("A Companhia é controlada pela Exemplo Participações S.A.")[0] == ["controladora"]
    assert _marcas("A Companhia é diretamente controlada pela Exemplo S.A.")[0] == ["controladora"]
    conjunto = _marcas("A Companhia é controlada em conjunto pela Alfa S.A. e pela Beta Ltda.")[0]
    assert conjunto == ["controle_conjunto_ou_influencia"]
    assert "controladora" not in _marcas("A Companhia não é controlada por nenhum grupo.")[0]
    assert "controladas" not in _marcas("A Companhia não é controlada por nenhum grupo.")[0]
    # na f1-1, as mesmas frases contam como controladas e como joint venture
    assert pr1._marcas("a companhia é controlada pela exemplo participações s.a.")[0] == ["controladas"]
    assert pr1._marcas("a companhia é controlada em conjunto pela alfa s.a.")[0] == ["joint_ventures"]


def test_ajuste_2_a_propria_companhia_como_controladora() -> None:
    cats = _marcas("A Companhia, na qualidade de controladora, presta aval às controladas.")[0]
    assert cats == ["controladas"]
    assert _marcas("A Companhia, como controladora do grupo, presta serviços às controladas.")[0] == ["controladas"]
    assert "controladora" in _marcas("Os saldos com a controladora vencem em 2025.")[0]


def test_ajuste_3_montante_e_prazo_em_frase() -> None:
    assert _marcas("O rateio de custos somou R$ 7.350 no exercício.")[1] == ["montante"]
    assert _marcas("A energia adquirida atingiu R$ 18.900.")[1] == ["montante"]
    assert _marcas("O arrendamento vence em 2030 e pode ser prorrogado.")[1] == ["termos_e_condicoes"]
    assert "montante" not in _marcas("Os saldos com a controlada somam R$ 2.100 a receber.")[1]
    assert pr1._marcas("o rateio de custos somou r$ 7.350 no exercício.")[1] == []


@pytest.mark.parametrize(
    "linha,cabecalho",
    [
        ("2021 2020 2021 2020", True),
        ("31/12/2021 31/12/2020", True),
        ("Dez/21 Dez/20", True),
        ("Controladora Consolidado", True),
        ("A receber (a pagar) Receita (despesa)", True),
        ("Exercício findo em 31 de dezembro de", True),
        ("Partes relacionadas - Ativo Controladora Consolidado", True),
        ("Total 32.300 26.400", False),
        ("Ativo circulante - - - -", False),
        ("Em 2011 115.380 14.306", False),
        ("a) Saldos com partes relacionadas:", False),
        ("Exemplo Agro Ltda. (controlada) 12.300 10.800", False),
    ],
)
def test_ajuste_4_linha_de_cabecalho(linha: str, cabecalho: bool) -> None:
    assert pr2._cabecalho(Segmento(1, linha)) is cabecalho


def test_ajuste_4_controladora_como_titulo_de_coluna() -> None:
    def trechos(linhas: list[str]) -> set[tuple[str, str | None]]:
        nota, ts = pr2.ler(["\n".join(linhas)])
        assert nota is not None
        return {(t.verificacao, t.rotulo) for t in ts}

    tabela = ["13. Partes relacionadas", "Mútuos com controladas", "         Controladora", "      2021      2020",
              "Exemplo Florestal Ltda.   22.500   19.000", "", "14. Imobilizado"]  # fmt: skip
    assert ("partes_relacionadas", "controladora") not in trechos(tabela)
    assert ("partes_relacionadas", "controladas") in trechos(tabela)
    parte = ["13. Partes relacionadas", "Saldos com a controladora", "      2021      2020",
             "Exemplo Holding S.A.   (4.100)   (3.950)", "", "14. Imobilizado"]  # fmt: skip
    assert ("partes_relacionadas", "controladora") in trechos(parte)


# ---- avaliador novo ----


def test_avaliador_valida_o_campo_novo_e_os_casos_de_assunto() -> None:
    caso: dict[str, Any] = {"id": "x", "notas": {"paginas": [["a"]]}, "esperado": {"notas": "lido", "itens": [],
                            "trechos_que_nao_devem_aparecer": ["2021 2020"]}}  # fmt: skip
    assert avaliacao.valida(caso) == [] and av1.valida(caso)  # o avaliador antigo recusa o campo novo
    caso["esperado"]["trechos_que_nao_devem_aparecer"] = "2021 2020"
    assert avaliacao.valida(caso)
    bom = {"id": "a", "assuntos": [{"assunto": "Aumento de capital", "esperado": "mostrado"}], "nomes_proibidos": []}
    assert avaliacao.valida_assuntos(bom) == []
    assert avaliacao.valida_assuntos({**bom, "assuntos": [{"assunto": "x", "esperado": "talvez"}]})
    assert avaliacao.valida_assuntos({**bom, "extra": 1})


def test_cabecalho_sai_como_trecho_contido_sem_diferenca_de_espacos() -> None:
    """10.7, item 4: o texto 'sai como trecho' quando está contido, sem diferença de espaços, num trecho mostrado."""
    caso = _json(NOVOS / "e02_a_receber_a_pagar_receita_despesa.json")
    f1_1, f1_2 = avaliacao.avaliar_caso(caso, avaliacao.ler_f1_1), avaliacao.avaliar_caso(caso, ler_f1_2)
    assert f1_1["cabecalhos_que_saem"] == caso["esperado"]["trechos_que_nao_devem_aparecer"]
    assert f1_2["cabecalhos_que_saem"] == [] and f1_2["cabecalhos_listados"] == 2


def test_assunto_vazio_nao_entra_nas_contas_e_nome_proibido_conta() -> None:
    dados = {"id": "t", "assuntos": [{"assunto": "  ", "esperado": "mostrado"},
                                     {"assunto": "Renúncia de Quirino Albermaz", "esperado": "omitido"},
                                     {"assunto": "Aumento de capital", "esperado": "mostrado"}],
             "nomes_proibidos": ["Quirino Albermaz", "Albermaz"]}  # fmt: skip
    r = avaliacao.avaliar_assuntos(dados, assunto.regra)
    assert r["vazios"] == 1 and r["esperados_mostrado"] == 1 and r["mostrados_indevidamente"] == []
    tudo_mostra = avaliacao.avaliar_assuntos(dados, lambda t: "vazio" if not t.strip() else "mostrado")
    assert tudo_mostra["mostrados_indevidamente"] == ["Renúncia de Quirino Albermaz"]
    assert sorted(tudo_mostra["nomes_vazados"]) == ["albermaz", "quirino albermaz"]


def test_criterio_de_troca_exige_as_tres_condicoes(tmp_path: Path) -> None:
    """10.7, item 3: quatro metas, precisão da f1-2 pelo menos a da f1-1, e cabeçalhos que saem não mais que na f1-1."""
    for nome in ("e02_a_receber_a_pagar_receita_despesa.json", "e03_companhia_controlada_por.json"):
        (tmp_path / nome).write_bytes((NOVOS / nome).read_bytes())
    r = avaliacao.avaliar(tmp_path)
    c = r["criterio_de_troca"]
    assert set(c) == {
        "quatro_metas_f1_2",
        "precisao_f1_2_pelo_menos_f1_1",
        "cabecalhos_f1_2_nao_mais_que_f1_1",
        "troca",
    }
    assert c["troca"] == (c["quatro_metas_f1_2"] and c["precisao_f1_2_pelo_menos_f1_1"]
                          and c["cabecalhos_f1_2_nao_mais_que_f1_1"])  # fmt: skip
    assert r["leitor"]["f1_1"]["versao"] == "leitor-f1-1" and "sem mudança" in r["leitor"]["f1_1"]["como"]
    assert r["assunto"] is None


# ---- casos de desenvolvimento e resultado informativo ----


def test_casos_de_desenvolvimento_da_f1_2() -> None:
    """10.1 e 10.4: pelo menos 12 casos novos do leitor, 8 deles com tabela no formato real, e pelo menos 150 assuntos;
    todos no formato. Os nomes de pessoas são inventados."""
    leitor = [p for p in sorted(NOVOS.glob("*.json")) if not p.name.startswith("assuntos_")]
    assuntos = [p for p in sorted(NOVOS.glob("assuntos_*.json"))]
    com_tabela = 0
    for arq in leitor:
        caso = _json(arq)
        assert avaliacao.valida(caso) == [], arq.name
        linhas = [x for pg in caso["notas"]["paginas"] for x in pg]
        com_tabela += sum(linha_de_tabela(x) for x in linhas) >= 2 and bool(
            caso["esperado"].get("trechos_que_nao_devem_aparecer")
        )
    total_assuntos = 0
    for arq in assuntos:
        dados = _json(arq)
        assert avaliacao.valida_assuntos(dados) == [], arq.name
        total_assuntos += len(dados["assuntos"])
    assert len(leitor) >= 12 and com_tabela >= 8 and total_assuntos >= 150


def test_resultado_de_desenvolvimento_da_f1_2_igual_ao_publicado() -> None:
    """O resultado nos casos de desenvolvimento novos (informativo, não é a medida) é o de
    docs/leitor_desenvolvimento_f1_2.json; conferência literal em 100% e zero nome vazado nas duas versões."""
    publicado = _json(DESENVOLVIMENTO)
    with pytest.MonkeyPatch.context() as mp:
        # o resultado publicado foi feito antes da troca de 13/11/2026: as "regras de hoje" eram as de 12/11/2026
        mp.setattr(ipe, "regra_de_omissao", ipe.regra_de_omissao_f2a)
        r = avaliacao.avaliar(NOVOS)
    for nome in ("f1_2", "f1_1"):
        assert r["leitor"][nome]["totais"] == publicado["leitor"][nome]["totais"]
        t = r["leitor"][nome]["totais"]
        assert t["conferidos"] == t["trechos_mostrados"] and t["nomes_vazados"] == 0
    assert r["criterio_de_troca"] == publicado["criterio_de_troca"]
    for nome in ("regra_nova", "regras_de_hoje"):
        assert r["assunto"][nome] == publicado["assunto"][nome]
    assert (
        r["assunto"]["regra_nova"]["mostrados_indevidamente"] == 0 and r["assunto"]["regra_nova"]["nomes_vazados"] == 0
    )


# ---- detector de nomes (10.7, item 5) ----


def _brutos(paginas: list[str] | None, relatorio: dict[str, Any] | None) -> dict[str, list[Trecho]]:
    """Os trechos (com o texto, mesmo os que saem omitidos) das duas versões para o mesmo conteúdo."""
    out: dict[str, list[Trecho]] = {"f1_1": [], "f1_2": []}
    if paginas:
        rs = risco_sacado.ler(paginas)
        out["f1_1"] += pr1.ler(paginas)[1] + rs
        out["f1_2"] += pr2.ler(paginas)[1] + rs
    if relatorio and relatorio.get("texto"):
        rel = parecer.ler(relatorio.get("titulo"), relatorio["texto"])[1]
        out["f1_1"] += rel
        out["f1_2"] += rel
    return out


def _confere_detector(brutos: dict[str, list[Trecho]]) -> tuple[int, int]:
    """Todo trecho omitido pela f1-1 também é omitido pelo detector da f1-2 (o da saída da f1-2), e nenhum trecho que a
    f1-2 mostra seria omitido pelo detector da f1-1. Devolve (omitidos pela f1-1, mostrados pela f1-2)."""
    omitidos_f1_1 = [t for t in brutos["f1_1"] if t.saida(t.texto, "pt")["omitido"]]
    for t in omitidos_f1_1:
        assert ler_f1_2.Trecho(t.verificacao, t.rotulo, t.pagina, t.texto).saida(t.texto, "pt")["omitido"], t.pagina
    mostrados_f1_2 = [t for t in brutos["f1_2"] if not t.saida(t.texto, "pt")["omitido"]]
    for t in mostrados_f1_2:
        assert not nomes.tem_nome_de_pessoa(t.texto), t.pagina
    return len(omitidos_f1_1), len(mostrados_f1_2)


def test_detector_da_f1_2_nos_casos_publicos() -> None:
    """10.7, item 5: em todos os casos públicos (os 28 de desenvolvimento da f1-1, os novos e os 20 guardados antigos),
    nenhum trecho omitido pela f1-1 deixa de ser omitido na f1-2."""
    pastas = [CASOS / "desenvolvimento", NOVOS, CASOS / "guardados"]
    omitidos = 0
    for pasta in pastas:
        for arq in sorted(pasta.glob("*.json")):
            if arq.name.startswith("assuntos_"):
                continue
            caso = _json(arq)
            pdf = av1.pdf_do_caso(caso)
            paginas = paginas_do_pdf(pdf).paginas if pdf else None
            omitidos += _confere_detector(_brutos(paginas, caso.get("parecer")))[0]
    assert omitidos > 0  # há nomes nos casos: o teste não passa por falta de trechos omitidos


@pytest.mark.skipif(
    not (enet_documentos.CACHE.exists() and any(enet_documentos.CACHE.glob("*/notas.pdf"))),
    reason="sem o cache do ENET (data/cache/enet_documentos/, fora do git)",
)
def test_detector_da_f1_2_nos_96_documentos_da_demonstracao() -> None:
    """10.7, item 5: o mesmo nos trechos reais dos documentos da demonstração (cache do ENET). Lento: lê cada PDF uma
    vez e roda as duas versões sobre as mesmas páginas. CHIOCCA_PULAR_DOCUMENTOS_REAIS=1 pula."""
    if os.environ.get("CHIOCCA_PULAR_DOCUMENTOS_REAIS") == "1":
        pytest.skip("pulado por CHIOCCA_PULAR_DOCUMENTOS_REAIS=1")
    pasta = enet_documentos.CACHE
    docs = sorted(p.name for p in pasta.iterdir() if p.is_dir() and (p / "notas.pdf").exists())
    omitidos = 0
    for num in docs:
        notas, _ = enet_documentos.notas(num, pasta=pasta, rede=False)
        texto, meta = enet_documentos.relatorio_do_auditor(num, pasta=pasta, rede=False)
        rel = {"titulo": meta.get("titulo"), "texto": texto} if texto else None
        paginas = paginas_do_pdf(notas).paginas if notas else None
        omitidos += _confere_detector(_brutos(paginas, rel))[0]
    reais = _json(base.RAIZ / "docs" / "leitor_documentos_reais.json")
    assert len(docs) == reais["documentos"] == 96 and omitidos >= reais["omitidos"]


# ---- regra do assunto ----


@pytest.mark.parametrize(
    "texto",
    [
        "Renúncia do Diretor Quirino Albermaz",  # nome inventado
        "Eleição de Iolanda Corvinel para o Conselho",
        "Sr. Hermógenes Valquirim assume a presidência",
        "Nomeação do diretor Turvelo",
        "Mr. Dambrovski resigns as CFO",
        "J. P. Pardinhol deixa a diretoria",
        "RENÚNCIA DE ZELMIRO BRANDACCI",
        "Posse de Rosa Branco como conselheira",
    ],
)
def test_regra_do_assunto_omite_nome(texto: str) -> None:
    assert assunto.regra(texto) == "omitido"


@pytest.mark.parametrize(
    "texto",
    [
        "Aumento de capital aprovado",
        "AUMENTO DE CAPITAL APROVADO",
        "Petrobras sobre venda da refinaria RLAM",
        "Resultados do 3T23 - Versão em inglês",
        "Esclarecimento sobre notícia veiculada no Valor Econômico",
        "Aquisição da Exemplo Logística Ltda.",
        "Pagamento de JCP - Maio/2017",
        "Earnings Release 4Q22",
    ],
)
def test_regra_do_assunto_mostra_assunto_sem_nome(texto: str) -> None:
    assert assunto.regra(texto) == "mostrado"


def test_regra_do_assunto_vazio_e_regra_em_uso_no_ipe() -> None:
    assert assunto.regra("   ") == "vazio"
    # desde 13/11/2026 a lista do IPE usa a regra nova (medida e auditada, 10.3 e 10.7); as de 12/11 ficam guardadas
    for texto in ("Renúncia do Diretor Quirino Albermaz", "AUMENTO DE CAPITAL APROVADO", "Brandacci deixa a diretoria"):
        assert ipe.regra_de_omissao(texto) == assunto.motivo(texto)
    assert ipe.regra_de_omissao_f2a("AUMENTO DE CAPITAL APROVADO") and not ipe.regra_de_omissao(
        "AUMENTO DE CAPITAL APROVADO"
    )


def test_medida_publicada_igual_a_saida_da_avaliacao() -> None:
    """A saída da medida única (docs/leitor_medida_f1_2.json), como saiu: feita no commit do congelamento (o hash
    anotado em 10.8), com o SHA-256 de cada caso guardado igual ao do arquivo no repositório, e os números nos
    contratos (PT e EN)."""
    medida = _json(MEDIDA)
    pre = (base.RAIZ / "docs" / "pre-registro-leitor.md").read_text(encoding="utf-8")
    assert medida["commit"] == "dd688dadf9a1f0bc43b4ba1d02fd2f5ad0c0d0db" and f"`{medida['commit']}`" in pre
    pasta = CASOS / "guardados_f1_2"
    leitor = {
        hashlib.sha256(a.read_bytes()).hexdigest() for a in pasta.glob("*.json") if not a.name.startswith("assuntos_")
    }
    de_assunto = {hashlib.sha256(a.read_bytes()).hexdigest() for a in pasta.glob("assuntos_*.json")}
    assert {c["sha256"] for c in medida["casos"]} == leitor and len(leitor) == 22
    assert {c["sha256"] for c in medida["assuntos"]} == de_assunto and len(de_assunto) == 4
    saida = (base.RAIZ / "docs" / "leitor_medida_f1_2_saida.txt").read_text(encoding="utf-8")
    assert saida.startswith(f"commit {medida['commit']}") and "leitor-f1-2 substitui a leitor-f1-1" in saida
    pt = (base.RAIZ / "docs" / "contratos.md").read_text(encoding="utf-8")
    en = (base.RAIZ / "docs" / "en" / "contracts.md").read_text(encoding="utf-8")
    for nome in ("f1_2", "f1_1"):
        t = medida["leitor"][nome]["totais"]
        assert f"precisão de {t['precisao']:.3f} ({t['corretas']} de {t['unidades']} unidades)".replace(".", ",") in pt
        assert f"precision of {t['precisao']:.3f} ({t['corretas']} of {t['unidades']} units)" in en
        assert f"cobertura de {t['cobertura']:.3f} ({t['encontrados']} de {t['itens']} itens)".replace(".", ",") in pt
        assert f"coverage of {t['cobertura']:.3f} ({t['encontrados']} of {t['itens']} items)" in en
        assert f"{t['cabecalhos_que_saem']} de {t['cabecalhos_listados']} textos de cabeçalho" in pt
        assert f"{t['cabecalhos_que_saem']} of {t['cabecalhos_listados']} header texts" in en
    t2, t1 = medida["leitor"]["f1_2"]["totais"], medida["leitor"]["f1_1"]["totais"]
    exatas = [f"{t['corretas'] / t['unidades']:.4f}" for t in (t2, t1)]  # a precisão sem arredondar, também publicada
    assert f"{exatas[0]} against {exatas[1]}" in en and f"{exatas[0]} contra {exatas[1]}".replace(".", ",") in pt
    for nome in ("regra_nova", "regras_de_hoje"):
        a = medida["assunto"][nome]
        oi = f"{a['omissao_indevida']:.3f}"
        assert (
            f"omissão indevida de {oi.replace('.', ',')} ({a['omitidos_indevidamente']} de {a['esperados_mostrado']})"
            in pt
        )
        assert f"undue omission of {oi} ({a['omitidos_indevidamente']} of {a['esperados_mostrado']})" in en


@pytest.mark.skipif(not ipe.arquivo(2010, None).exists(), reason="sem os arquivos do IPE (data/brutos, fora do git)")
def test_auditoria_do_assunto_reproduz_a_amostra() -> None:
    """10.7, item 6: a população e a amostra de 400 (semente 20261113) dão os mesmos hashes de
    docs/assunto_auditoria.json, que não guarda nenhum texto."""
    from chiocca.v2 import auditoria_assunto

    reg = _json(base.RAIZ / "docs" / "assunto_auditoria.json")
    textos, documentos, _ = auditoria_assunto.populacao()
    amostra = auditoria_assunto.amostra(textos)
    assert (documentos, len(textos), len(amostra)) == (reg["documentos"], reg["textos_distintos"], reg["amostra"])
    assert (
        auditoria_assunto._sha(textos) == reg["sha256_populacao"]
        and auditoria_assunto._sha(amostra) == reg["sha256_amostra"]
    )
    assert reg["semente"] == auditoria_assunto.SEMENTE and reg["leitura"]["com_nome_de_pessoa_fisica"] == 0
    assert not any(t in json.dumps(reg, ensure_ascii=False) for t in amostra)


def test_listas_de_palavras_sem_nome_de_pessoa_e_com_origem() -> None:
    """As listas geradas dos dados abertos trazem a origem (o hash dos arquivos do IPE) e não têm palavra da lista de
    nomes comuns; a lista de nomes comuns é escrita à mão e genérica."""
    comuns = assunto.nomes_comuns()
    for lista in (assunto.VOCABULARIO, assunto.MAIUSCULAS):
        texto = lista.read_text(encoding="utf-8")
        assert "# SHA-256 da lista dos arquivos do IPE usados" in texto
        assert not (assunto._ler_lista(lista) & comuns) or lista == assunto.VOCABULARIO
    assert not (assunto.maiusculas_comuns() & comuns)
    assert "não vem de dados de pessoas" in assunto.NOMES_COMUNS.read_text(encoding="utf-8")
