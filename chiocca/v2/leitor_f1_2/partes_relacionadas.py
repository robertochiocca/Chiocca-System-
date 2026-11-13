"""Partes relacionadas nas notas explicativas, `leitor-f1-2` (cópia do módulo da f1-1 com os quatro ajustes da emenda
1, docs/pre-registro-leitor.md, seção 10.1; CPC 05 (R1): categorias do item 19, campos do item 18 e a frase "em
condições de mercado" do item 23, registrada como fato, sem prova).

Ajustes da f1-2, marcados no código com "f1-2":
1. "a Companhia é controlada (em conjunto) por" vira `controladora` (ou `controle_conjunto_ou_influencia`), e o trecho
   da frase não conta como menção a controladas ou a joint ventures;
2. "a Companhia, na qualidade de controladora" (a própria Companhia) não conta como `controladora`;
3. montante e prazo em frase: "somou", "atingiu", "R$ ... no exercício"; "vence em", "vigência", "prorrogável";
4. cabeçalho de tabela: a linha só de anos, datas e títulos de coluna (sem os parênteses de "(a pagar)" e
   "(despesa)", o traço separador, a numeração do item e a chamada de nota "(12)") não sai como trecho; continua
   passando as categorias e os campos para as linhas de baixo, menos "Controladora" quando é o título da coluna das
   demonstrações individuais (com "Consolidado", anos ou datas na linha, ou só anos ou datas na linha de baixo).
   Linha com valor (número com algarismo, ou dois traços de valor zerado) e subtítulo "a) ..." não são cabeçalho.

1. Acha a nota: a primeira linha de título numerada (sem decimal) com "partes relacionadas" no título; sem ela, um
   título numerado com decimal ou um título sem número só sobre partes relacionadas. A nota vai até o próximo título
   numerado (outro número) ou o fim do documento.
2. Divide a nota em segmentos (parágrafos e linhas de tabela) e marca, em cada um, as categorias do item 19, os
   campos do item 18 e a frase sobre condições de mercado, pelas palavras abaixo. Linha que é só cabeçalho de coluna
   ("Controladora  Consolidado  2021  2020") não conta.
3. Registra as colunas da nota (controladora e consolidado), quando aparecem.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from chiocca.v2.leitor.texto import busca, linhas
from chiocca.v2.leitor.trechos import Segmento, Trecho, linha_de_tabela, segmentos

_TITULO = re.compile(
    r"^(?i:nota(?:\s+explicativa)?\s*(?:n[º°o.]*\s*)?)?(\d{1,2}|[IVXLC]{1,7}(?=[\s.\-–—)]))((?:\.\d{1,2})*)"
    r"(?:\s*[.\-–—)]\s*|\s+)([A-ZÀ-Ýa-zà-ÿ].*)$"
)
_ROMANOS = {"I": 1, "V": 5, "X": 10, "L": 50, "C": 100}
_REMUNERACAO = re.compile(
    r"remunera[çc][ãa]o (?:d[aoe]s? )?(?:administra|pessoal[\s-]?chave|diretoria|diretores|conselh|" r"administradores)"
)
_SO_PARTES = re.compile(
    r"^(?:(?:saldos e |transa[çc][õo]es e saldos com |saldos e transa[çc][õo]es com |transa[çc][õo]es com |"
    r"opera[çc][õo]es com |saldos com )?partes relacionadas)$"
)
CATEGORIAS: list[tuple[str, str]] = [
    ("joint_ventures", r"joint[\s-]?ventures?|empreendimentos? controlados? em conjunto|controladas? em conjunto"),
    ("controle_conjunto_ou_influencia", r"(?:controle conjunto|influência significativa) (?:sobre|na|da) (?:a )?"
                                        r"(?:companhia|entidade|sociedade)"),
    ("controladora", r"\bcontroladora\b|\bacionistas? controlador(es)?\b|\bcontroladores?\b|\bacionista majoritário\b"),
    ("controladas", r"\bcontroladas?\b(?! em conjunto)|\bsubsidiárias?\b"),
    ("coligadas", r"\bcoligadas?\b"),
    ("pessoal_chave", r"pessoal[\s-]?chave|\badministradores\b|\bdiretoria\b|\bdiretor(?:es|a|as)?\b|conselho de administração|"
                      r"\bconselheiros\b|conselho fiscal|remuneração (global )?(da|dos) (administração|administradores)"),
    ("outras_partes", r"outras partes relacionadas|demais partes relacionadas|\bacionistas?\b(?! controlador)|"
                      r"controle comum|empresas? ligadas|partes ligadas|entidades? ligadas|\bfundação\b|fundo de pensão|"
                      r"previdência (privada|complementar)|\bfamiliares\b|membros próximos da família|\bcônjuges?\b|"
                      r"\bparentes\b"),
]  # fmt: skip
# Usos de "controladora" que são o nome da coluna (demonstrações individuais), não a parte relacionada.
_COLUNA_CONTROLADORA = re.compile(
    r"(?:\b(?:na|individual)\s+)controladora\b|controladora\s+e\s+(?:o\s+|no\s+)?consolidado|"
    r"consolidado\s+e\s+(?:a\s+|na\s+)?controladora|[-–—]\s*controladora\b|\bcontroladora\s*[-–—]|"
    r"controladora\s+consolidad[oa]"
)
# f1-2 (ajuste 1): quem controla a Companhia. "A Companhia é controlada (em conjunto) por X": a parte é a controladora
# (ou quem tem o controle conjunto); "controlada" aqui não é menção a controladas nem a joint ventures.
_CONTROLADA_POR = re.compile(
    r"\b(?:companhia|sociedade|entidade|emissora)\b[^.;]{0,60}?\b(?:é|foi|era|está|esteve|permanece|passou a ser)\s+"
    r"(?:direta(?:mente)?\s+|indireta(?:mente)?\s+|direta e indiretamente\s+)?controlad[ao]\s+(em conjunto\s+)?"
    r"(?:por|pel[oa]s?)\b"
)
# f1-2 (ajuste 2): "a Companhia, na qualidade de controladora, ..." fala da própria Companhia (item 19 a do CPC 05).
_PROPRIA_CONTROLADORA = re.compile(
    r"\b(?:companhia|sociedade|entidade|emissora)\b\s*,?\s*(?:\w+\s+){0,3}?(?:na qualidade de|como|enquanto)\s+"
    r"controladora\b"
)
CAMPOS: list[tuple[str, str]] = [
    ("montante", r"\bmontantes?\b|\breceitas?\b|\bdespesas?\b|\bcompras?\b|\bvendas?\b|\bvend(?:eu|eram|ido)\b|"
                 r"\bcompr(?:ou|aram)\b|\bpag(?:ou|aram|amentos?)\b|\bcontribu(?:iu|íram|ição|ições)\b|\bforneceu\b|"
                 r"\bpor r\$|\btotaliz\w+|\bpag[oa]s\b|\brecebid[oa]s\b|\bsomaram\b|"
                 # f1-2 (ajuste 3): montante escrito em frase
                 r"\bsomou\b|\bmontou\b|\batingi(?:u|ram)\b|"  # no passado: o valor do período ("somam" é saldo)
                 r"r\$ ?[\d.,]+ (?:mil |milhões? )?(?:no|em|durante o) (?:exercício|ano|período|semestre|trimestre)"),
    ("saldos", r"\bsaldos?\b|\ba receber\b|\ba pagar\b|\bcréditos com\b|\bdébitos com\b|\bativo\b|\bpassivo\b"),
    ("termos_e_condicoes", r"(?<!curto )(?<!longo )\bprazos?\b|\bjuros\b|\btaxas?\b|\bvencimentos?\b|\bindexad|\bcdi\b|\bipca\b|\bselic\b|"
                           r"\bcorrigid|\batualizad|termos e condições|\bencargos\b|\bremunerad[oa]s? (?:a|com|pel[oa])|"
                           r"\ba\.a\.|\bao ano\b|"
                           # f1-2 (ajuste 3): prazo escrito em frase
                           r"\bvenc(?:e|em|eu|erá|erão|ia|iam)\b|\bvigência\b|\bvigora\b|\bexpira\w*|\bprorrog\w*|"
                           r"\brenov(?:ável|áveis|ado|ada|ados|adas|ação)\b"),
    ("garantias", r"\bgarantias?\b|\bgarantid[oa]s?\b|\bavais\b|\baval\b|\bfianças?\b|\bfiador|alienação fiduciária|"
                  r"\bhipotecas?\b|\bpenhor\b|\bcaução\b|\bcolateral"),
    ("provisao_pcld", r"liquidação duvidosa|\bpcld\b|\bpecld\b|perdas? (de crédito )?esperadas?|perdas? estimadas?|"
                      r"provisão para (perdas|créditos)|devedores duvidosos"),
    ("perdas_incobraveis", r"incobráve|baixas? de créditos|perdas? efetivas|perdas? com créditos|difícil recuperação|"
                           r"baixad[oa]s? como perda"),
]  # fmt: skip
CONDICOES = re.compile(
    r"condições (?:normais |usuais |habituais |equivalentes às |semelhantes às |compatíveis com as |similares às )?"
    r"(?:de|do|praticadas no) mercado|condições comutativas|preços? de mercado|"
    r"termos? equivalentes? (?:aos|às) que prevalecem|"
    r"(?:condições|preços|termos) (?:similares|semelhantes|equivalentes|compatíveis|iguais) (?:a|às|aos) (?:praticad|"
    r"negociad|contratad)\w* com terceiros|bases? comutativas?|valores? de mercado|arm'?s[\s-]length"
)
_CABECALHO = {"controladora", "consolidado", "consolidada", "individual", "nota", "notas", "em", "r$", "mil", "milhares",
              "de", "reais", "e", "-", "–", "saldo", "saldos", "receita", "despesa", "a", "receber", "pagar", "ativo",
              "passivo", "resultado", "transações", "operações", "valores", "descrição", "com", "partes",
              "relacionadas"}  # fmt: skip


@dataclass
class Nota:
    titulo: str
    pagina_inicio: int
    pagina_fim: int
    segmentos: list[Segmento] = field(default_factory=list)
    categoria_padrao: str | None = None  # nota de remuneração da administração: tudo é pessoal-chave


def _numero(n: str) -> int:
    if n.isdigit():
        return int(n)
    total = 0
    for i, c in enumerate(n):
        v = _ROMANOS[c]
        total += -v if i + 1 < len(n) and _ROMANOS[n[i + 1]] > v else v
    return total


def _titulo(linha: str) -> tuple[int, bool, str] | None:
    """(número, tem decimal, título) se a linha for título numerado de nota; numeral romano vale negativo (-12 para
    XII), para a nota em romanos só terminar em outro título em romanos."""
    m = _TITULO.match(linha.strip())
    if not m or re.search(r"\.{4,}|…", linha) or len(linha.split()) > 14 or linha.rstrip().endswith((",", ";")):
        return None
    titulo = m.group(3)
    if (
        titulo.rstrip().endswith(".") and len(titulo.split()) > 6
    ):  # frase, não título ("15. Operações com partes relacionadas.")
        return None
    if linha_de_tabela(titulo):  # o número da nota e o travessão do título não são colunas de valor
        return None
    if not titulo[:1].isupper():
        return None
    numero = _numero(m.group(1))
    return (numero if m.group(1).isdigit() else -numero), bool(m.group(2)), titulo


SEM_NUMERO = 10_000  # título sem número


def _candidatos(paginas: list[str], qual: str) -> list[tuple[int, int, int, int, bool, str]]:
    """(prioridade, página, linha, número, decimal, título) dos títulos de nota de partes relacionadas ("partes") ou de
    remuneração da administração ("remuneracao")."""
    out = []
    for p, texto in enumerate(paginas):
        for i, linha in enumerate(linhas(texto)):
            t = _titulo(linha)
            if qual == "partes":
                if t and "partes relacionadas" in busca(t[2]):
                    out.append((1 if t[1] else 0, p, i, t[0], t[1], linha))
                elif _SO_PARTES.match(busca(linha)) and len(linha) < 80:
                    out.append((2, p, i, SEM_NUMERO, False, linha))
            elif t and not t[1] and _REMUNERACAO.search(busca(t[2])) and "partes relacionadas" not in busca(t[2]):
                out.append((0, p, i, t[0], t[1], linha))
    return out


def _nota(paginas: list[str], inicio: tuple[int, int, int, int, bool, str]) -> Nota:
    _, p0, i0, numero, decimal, titulo = inicio

    def encerra(t: tuple[int, bool, str]) -> bool:
        # nota inteira (13.) vai até o próximo título inteiro de número maior, no mesmo tipo de numeral (arábico ou
        # romano); os subtítulos (13.1) e as listas numeradas dentro da nota (1., I -) ficam dentro. Subtítulo com decimal (2.21) ou título sem número vão até o
        # próximo título numerado.
        if numero != SEM_NUMERO and not decimal:
            return not t[1] and abs(t[0]) > abs(numero) and (t[0] > 0) == (numero > 0)
        return True

    fim_p, fim_i = len(paginas) - 1, None
    for p in range(p0, len(paginas)):
        ls = linhas(paginas[p])
        for i in range(i0 + 1 if p == p0 else 0, len(ls)):
            t = _titulo(ls[i])
            if t and encerra(t):
                fim_p, fim_i = p, i
                break
        if fim_i is not None:
            break
    nota = Nota(titulo, p0 + 1, fim_p + 1)
    for p in range(p0, fim_p + 1):
        de = i0 + 1 if p == p0 else 0
        ate = fim_i if p == fim_p else None
        nota.segmentos += segmentos(paginas[p], p + 1, de, ate)
    return nota


def acha_nota(paginas: list[str]) -> Nota | None:
    candidatos = _candidatos(paginas, "partes")
    return _nota(paginas, min(candidatos, key=lambda c: (c[0], c[1], c[2]))) if candidatos else None


def notas_de_remuneracao(paginas: list[str]) -> list[Nota]:
    """Notas próprias de remuneração da administração (pessoal-chave, CPC 05 (R1)), fora da nota de partes
    relacionadas."""
    notas = [_nota(paginas, c) for c in _candidatos(paginas, "remuneracao")]
    for n in notas:
        n.categoria_padrao = "pessoal_chave"
    return notas


# f1-2 (ajuste 4): mais palavras de título de coluna e as datas e anos do cabeçalho.
_CABECALHO_F1_2 = _CABECALHO | {
    "receitas", "despesas", "ativos", "passivos", "circulante", "circulantes", "não", "custos", "custo", "exercício",
    "exercícios", "findo", "findos", "período", "períodos", "dezembro", "expressos", "natureza", "parte", "relação",
    "relacionamento", "tipo", "contraparte", "montante", "montantes", "transação", "contas", "efeito", "efeitos",
    "resultados", "valor", "o", "do", "da", "no", "na", "dos", "das", "ao", "aos", "s/a", "líquido", "líquida",
    "janeiro", "fevereiro", "março", "abril", "maio", "junho", "julho", "agosto", "setembro", "outubro", "novembro",
}  # fmt: skip
_MESES = "janeiro|fevereiro|março|abril|maio|junho|julho|agosto|setembro|outubro|novembro|dezembro"
_DIA_DO_MES = re.compile(rf"\b\d{{1,2}}º? de (?=(?:{_MESES})\b)")
_NUMERACAO = re.compile(r"\d{1,2}(?:\.\d{1,2})*")  # depois de tirar o ponto final: "6", "20.1"
_ANO_OU_DATA = re.compile(r"(?:19|20)\d\d|\d{1,2}[./]\d{1,2}[./](?:19|20)?\d\d|\w{3}/\d{2,4}|\d{4}-\d{2}-\d{2}")


_ANTES_DA_PARTE = {"a", "à", "da", "pela", "com", "sua", "nossa", "para"}  # "com a controladora": é a parte


def _so_anos_ou_datas(seg: Segmento) -> bool:
    tokens = [w.strip("().:;,*") for w in re.split(r"\s+", seg.busca)]
    tokens = [w for w in tokens if w and not re.fullmatch(r"[-–—]+", w)]
    return bool(tokens) and all(_ANO_OU_DATA.fullmatch(w) for w in tokens)


def _controladora_como_coluna(seg: Segmento, seguinte: Segmento | None) -> bool:
    """f1-2 (ajuste 4): no cabeçalho, "Controladora" é o título da coluna das demonstrações individuais (não a parte)
    quando a linha também tem "Consolidado", anos ou datas, ou quando a linha de baixo é só de anos ou datas. Com
    artigo ou preposição antes ("Saldos com a controladora", "Operações com a Controladora"), é a parte."""
    if not re.search(r"\bcontroladora\b", seg.busca):
        return False
    if any(m.group(1) in _ANTES_DA_PARTE for m in re.finditer(r"(\S+)\s+controladora\b", seg.busca)):
        return False
    anos_embaixo = seguinte is not None and _so_anos_ou_datas(seguinte)
    if not _cabecalho(seg):
        # título do bloco com o título da coluna no fim, na linha de cima dos anos ("Mútuos com controladas" e, logo
        # abaixo, "Controladora", juntados num parágrafo só)
        return bool(anos_embaixo and re.search(r"\S\s+controladora\s*$", seg.busca) and _titulo_de_bloco(seg))
    tokens = [w.strip("().:;,*") for w in seg.busca.split()]
    if re.search(r"\bconsolidad[oa]s?\b", seg.busca) or any(_ANO_OU_DATA.fullmatch(w) for w in tokens if w):
        return True
    return anos_embaixo


def _cabecalho(seg: Segmento) -> bool:
    """Linha de cabeçalho de tabela: só títulos de coluna, anos e datas (f1-2: os parênteses de "(a pagar)" e
    "(despesa)" saem antes de comparar, e a linha só de anos ou datas também é cabeçalho)."""
    if re.match(r"\s*\(?(?:[a-z]|[ivx]{1,4})\)\s", seg.busca):  # "a) Saldos com partes relacionadas:" é subtítulo
        return False
    texto = _DIA_DO_MES.sub(" ", seg.busca)  # "31 de dezembro de": data do cabeçalho
    tokens = [w for w in re.split(r"\s+", texto) if not re.fullmatch(r"\(\d{1,2}\)", w)]  # "(12)": nota
    tokens = [w.strip("().:;,*") for w in tokens]
    if sum(bool(re.fullmatch(r"[-–—]+", w)) for w in tokens) >= 2:  # "Ativo circulante - - - -": valores zerados
        return False
    tokens = [w for w in tokens if w and not re.fullmatch(r"[-–—]+", w)]  # um traço só (separador) não conta
    if tokens and _NUMERACAO.fullmatch(tokens[0]) and len(tokens) > 1:  # "20.1. Controladora": numeração do item
        tokens = tokens[1:]
    if not tokens:
        return False
    if all(_ANO_OU_DATA.fullmatch(w) for w in tokens):
        return True
    palavras = [w for w in tokens if not _ANO_OU_DATA.fullmatch(w)]
    if any(re.fullmatch(r"[\d.,%\-–]*\d[\d.,%\-–]*", w) for w in palavras):  # valor de coluna: é linha de dados
        return False
    return bool(palavras) and all(w in _CABECALHO_F1_2 for w in palavras)


def colunas(nota: Nota) -> list[str]:
    texto = " ".join(s.busca for s in nota.segmentos)
    return [c for c in ("controladora", "consolidado") if re.search(rf"\b{c}\b", texto)]


def _marcas(b: str) -> tuple[list[str], list[str]]:
    extras: list[str] = []
    resto = b
    for m in list(_CONTROLADA_POR.finditer(b)):  # f1-2 (ajuste 1); "não é controlada por" não afirma parte nenhuma
        if not re.search(r"\b(?:não|nem)\b", m.group(0)):
            extras.append("controle_conjunto_ou_influencia" if m.group(1) else "controladora")
        resto = resto.replace(m.group(0), " ")
    resto = _PROPRIA_CONTROLADORA.sub(" ", resto)  # f1-2 (ajuste 2)
    sem_coluna = _COLUNA_CONTROLADORA.sub(" ", resto)
    cats = [r for r, padrao in CATEGORIAS if re.search(padrao, sem_coluna if r == "controladora" else resto)]
    return list(dict.fromkeys(extras + cats)), [r for r, padrao in CAMPOS if re.search(padrao, b)]


def _titulo_de_bloco(seg: Segmento) -> bool:
    """Linha curta que nomeia o bloco seguinte ("Remuneração do pessoal-chave", "Saldos com partes relacionadas 2021
    2020"): as categorias e os campos dela valem para as linhas de tabela que vêm logo abaixo."""
    palavras = [w for w in seg.busca.split() if not re.fullmatch(r"[\d.,()%\-–]+", w)]
    if linha_de_tabela(seg.texto):
        return len(palavras) <= 6
    return len(palavras) <= 8 and not seg.texto.rstrip().endswith(".")


def ler(paginas: list[str]) -> tuple[Nota | None, list[Trecho]]:
    nota = acha_nota(paginas)
    extras = notas_de_remuneracao(paginas)
    if nota is None and not extras:
        return None, []
    trechos: list[Trecho] = []
    for n in ([nota] if nota else []) + extras:
        trechos += _trechos_da_nota(n)
    return nota or extras[0], trechos


def _trechos_da_nota(nota: Nota) -> list[Trecho]:
    trechos: list[Trecho] = []
    herdadas: tuple[list[str], list[str]] = ([], [])
    for i, seg in enumerate(nota.segmentos):
        cats, campos = _marcas(seg.busca)
        seguinte = nota.segmentos[i + 1] if i + 1 < len(nota.segmentos) else None
        if _controladora_como_coluna(seg, seguinte):  # f1-2 (ajuste 4)
            cats = [c for c in cats if c != "controladora"]
        tabela = linha_de_tabela(seg.texto)
        cabecalho = _cabecalho(seg)
        if _titulo_de_bloco(seg) and (cats or campos):
            herdadas = (cats, campos)
        elif tabela:
            cats = list(dict.fromkeys(cats + herdadas[0]))
            campos = list(dict.fromkeys(campos + herdadas[1]))
        elif not cabecalho:  # f1-2 (ajuste 4): o cabeçalho sem marcas é parte da tabela e não encerra o bloco
            herdadas = ([], [])  # parágrafo de texto encerra o bloco
        if cabecalho:
            continue
        if nota.categoria_padrao and nota.categoria_padrao not in cats:
            cats = [nota.categoria_padrao, *cats]
        for rotulo in cats:
            trechos.append(Trecho("partes_relacionadas", rotulo, seg.pagina, seg.texto))
        for rotulo in campos:
            trechos.append(Trecho("campo_cpc05_18", rotulo, seg.pagina, seg.texto))
        if CONDICOES.search(seg.busca):
            trechos.append(Trecho("condicoes_de_mercado", None, seg.pagina, seg.texto))
    return trechos
