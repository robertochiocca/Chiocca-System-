"""Regra própria para o assunto dos fatos relevantes e comunicados do IPE (Fase F2b, emenda 1, seção 10.3 do
pré-registro do leitor). Ao lado das regras conservadoras de hoje (chiocca/v2/ipe.py), que ficam até a medida aprovar
esta regra: zero nome de pessoa (exigência) e omissão indevida de no máximo 0,20 nos casos guardados.

A regra olha cada palavra com inicial maiúscula (ou cada palavra, no assunto todo em maiúsculas) e a classifica:
- E (exceção): vocabulário do detector do leitor, lugares e companhias do cadastro (pela sequência inteira), siglas,
  meses, trimestres ("3T23"), números e um vocabulário de títulos em inglês;
- N (nome comum): um prenome ou sobrenome comum da lista escrita à mão (data/leitor/nomes_comuns.txt), mesmo que
  também seja palavra comum ou lugar ("Rosa", "Campos");
- C (palavra comum): aparece em minúsculas em assuntos de pelo menos 3 companhias (data/leitor/vocabulario_assuntos.txt,
  gerado dos dados abertos do IPE de 2010 a 2024); nome próprio de pessoa quase nunca aparece em minúsculas;
- P (desconhecida): o resto (marca, companhia fora do cadastro, lugar fora da lista ou nome de pessoa).

O assunto sai omitido quando:
1. tem pronome de tratamento, CPF ou iniciais ("J. Exemplo") — como o detector do leitor;
2. há contexto de pessoa (cargo ou evento de pessoa: diretor, presidente, conselheiro, membro, eleição, renúncia,
   posse, falecimento, desligamento, contratação de executivo e outros) e alguma palavra maiúscula, fora a primeira
   de cada parte, não é E nem cargo ou área institucional; ou, nesse contexto, a primeira palavra é N ou P;
3. sem contexto de pessoa, alguma sequência de palavras maiúsculas (com "de", "da", "do", "das", "dos", "e" e "&" no
   meio) que não é exceção inteira tem uma palavra N, ou duas ou mais palavras P;
4. no assunto todo em maiúsculas, valem as mesmas classes com as palavras em minúsculas; palavra de até 5 letras que
   não está em nenhuma lista conta como sigla.
Assunto vazio não entra (a tela mostra o aviso). Nada aqui é alerta, nota ou ordenação.
"""

from __future__ import annotations

import hashlib
import json
import re
import sys
import unicodedata
from collections import defaultdict
from functools import lru_cache
from pathlib import Path

from chiocca import base
from chiocca.v2.leitor import nomes

VERSAO = "assunto-ipe-1"
PASTA_DADOS = base.RAIZ / "data" / "leitor"
VOCABULARIO = PASTA_DADOS / "vocabulario_assuntos.txt"
MAIUSCULAS = PASTA_DADOS / "maiusculas_assuntos.txt"
NOMES_COMUNS = PASTA_DADOS / "nomes_comuns.txt"
MINIMO_COMPANHIAS = 3
MINIMO_COMPANHIAS_MAIUSCULAS = 10
# fora da lista de palavras maiúsculas comuns, mesmo aparecendo em muitas companhias: sufixos e partes de nome de
# pessoa, pronomes de tratamento e um apelido que é também marca (escrito à mão)
FORA_DAS_MAIUSCULAS = frozenset(
    "junior júnior jr filho filha neto neta sobrinho dr dra sr sra srs sras merrill lynch stanley morgan jones bastter "
    "salvador natal".split()
)

CONECTORES = nomes.CONECTORES | {"&", "&amp", "&amp;"}
MESES = frozenset(
    "janeiro fevereiro março marco abril maio junho julho agosto setembro outubro novembro dezembro jan fev mar abr "
    "mai jun jul ago set out nov dez january february march april may june july august september october november "
    "december".split()
)
INGLES = frozenset(
    "material fact facts notice notices market announcement announces announcement shareholders shareholder meeting "
    "meetings general extraordinary ordinary annual results result earnings release conference call presentation "
    "investor investors day report reports board directors director capital increase dividends dividend interest on "
    "equity acquisition acquisitions sale sales agreement agreements update updates rating ratings payment payments "
    "debentures debenture issuance issue offering offer public share shares buyback program programme of the and to "
    "for in a an with from by at as new first second third fourth quarter quarterly year fiscal financial statements "
    "information operational performance guidance clarification clarifications news article press company group "
    "subsidiary subsidiaries merger incorporation spin-off spin off restructuring plan judicial recovery approval "
    "approved approves corporate governance policy policies calendar events event schedule webcast teleconference "
    "relations ir management proposal minutes summary amendment notification letter official request response reply "
    "change changes appointment resignation election cvm sec form fact-sheet factsheet production sales volume "
    "volumes traffic statistics preview previous preliminary unaudited audited structure organizational organization "
    "corporate reorganization combination business businesses transaction transactions closing completion conclusion "
    "divestment divestiture partnership joint venture ventures operations operating strategic review project projects "
    "contract contracts award awards outlook upgrade downgrade credit debt bond bonds notes senior secured unsecured "
    "tender exchange repurchase redemption prepayment settlement litigation lawsuit arbitration decision court tax "
    "taxes assessment regulatory authorization license licence auction concession tariff adjustment revision launch "
    "opening inauguration expansion investment investments capex financing funding loan facility reduction "
    "distribution interim complementary additional date record schedule postponement cancellation suspension "
    "resumption impacts impact pandemic update clarification rumor media brazil brazilian latin america american "
    "global international national holding holdings participations bank banks energy oil gas power mining steel "
    "retail stores store bonus stock stocks option options plan plans incentive long-term term short-term".split()
)
# substantivos de negócio: a sequência com um deles é nome de companhia ou de ativo ("Banco Daycoval", "Exemplo
# Energia"); e as pistas que vêm antes de um nome de companhia ("acordo com a Zanecom", "grupo Technip")
NEGOCIO = frozenset(
    "banco grupo energia energias participações participacoes capital investimentos holding brasil bank group partners "
    "asset securities seguros seguradora telecom engenharia construtora incorporadora logística transportes mineração "
    "alimentos petróleo gás saúde educação shopping shoppings malls fundo fundos fii fidc fip empreendimentos "
    "empreendimento serviços sistemas tecnologia solar eólica eólicas transmissora distribuidora geração usina usinas "
    "refinaria terminal porto portos rodovia rodovias ferrovia aeroporto hospital hospitais farmácia farmácias lojas "
    "loja rede mercado supermercados varejo indústria indústrias têxtil papel celulose química agro agrícola "
    "agronegócio imobiliária imobiliário corretora distribuidora securitizadora concessionária saneamento águas "
    "comercial comércio importadora exportadora tv rádio editora mídia".split()
)
_PISTA_DE_COMPANHIA = re.compile(
    r"(?:\b(?:empresa|empresas|companhia|companhias|banco|bancos|grupo|fundo|controlada|controladas|coligada|"
    r"coligadas|subsidiária|investida|parceira|refinaria|usina|campo|campos|projeto|produto|marca|plataforma|"
    r"aplicativo|app|loja|rede|unidade|fábrica|terminal|porto|aeroporto|rodovia|ferrovia|hospital|shopping|"
    r"empreendimento|ativo|ativos|bloco|blocos|mina|navio|sonda|fpso|operadora|cliente|fornecedor|agência|"
    r"(?:acordo|parceria|contrato|contratos|memorando|associação|fusão|combinação|negociações?|transação) com|"
    r"(?:aquisição|venda|compra|incorporação|alienação|oferta|cisão|privatização|controle|participação|ações|"
    r"desinvestimento|liquidação|recuperação judicial|falência) (?:d|n)[aoe]s?)\s+(?:d[aoe]s?\s+|a\s+|o\s+)?$)",
    re.IGNORECASE,
)
# lugares de uma palavra (os de várias palavras estão no detector): países, continentes, estados e cidades grandes
LUGARES_EXTRA = frozenset(
    "brasil argentina chile peru colômbia colombia méxico mexico canadá canada eua usa china japão japao índia india "
    "alemanha frança franca itália italia espanha portugal inglaterra escócia irlanda holanda bélgica suíça suica "
    "luxemburgo áustria noruega suécia dinamarca finlândia rússia coreia singapura austrália angola moçambique "
    "uruguai paraguai bolívia venezuela equador panamá caribe áfrica africa europa ásia asia américa americas "
    "américas oceania acre alagoas amapá amazonas bahia ceará goiás maranhão pará paraíba paraná pernambuco piauí "
    "rondônia roraima sergipe tocantins manaus belém fortaleza recife maceió aracaju teresina cuiabá goiânia brasília "
    "curitiba florianópolis campinas guarulhos sorocaba ribeirão uberlândia londrina joinville macaé itajaí "
    "paranaguá suape pecém itaqui camaçari cubatão betim contagem ipatinga niterói osasco barueri jundiaí piracicaba "
    "maringá cascavel blumenau chapecó caxias pelotas canoas juiz anápolis palmas macapá porto-alegre "
    "nordeste sudeste sul norte centro-oeste".split()
)
# cargos e áreas: não são nome, mesmo em maiúscula, também no contexto de pessoa
INSTITUCIONAL = frozenset(
    "diretor diretora diretores diretoras diretoria presidente presidentes vice vice-presidente vice-presidência "
    "presidência conselheiro conselheira conselheiros conselheiras conselho conselhos membro membros comitê comitês "
    "comite superintendente superintendência executivo executiva executivos gerente gerência administração "
    "administrativo administrativa administrador administradora administradores financeiro financeira financeiros "
    "comercial operações operacional relações investidores jurídico jurídica técnico técnica industrial auditoria "
    "auditor auditores independente independentes fiscal fiscais estatutário estatutária estatutários suplente "
    "suplentes titular titulares efetivo efetivos ceo cfo coo cto cio cro cso ri dri secretário secretária "
    "secretaria governança riscos compliance pessoas recursos humanos marketing tecnologia inovação estratégia "
    "planejamento controladoria tesouraria contabilidade sustentabilidade novo nova novos novas interino interina "
    "chief officer officers board executive vice-president president".split()
)
_CONTEXTO_PESSOA = re.compile(
    r"\b(?:diretor\w*|presidente\w*|vice-presiden\w*|conselheir\w*|superintendente\w*|executiv[oa]s?|"
    r"administrador\w*|membros?|ceo|cfo|coo|cto|cio|cro|eleiç\w*|eleit[oa]s?|elege\w*|nomea\w*|indica[çc]\w*|"
    r"indicad[oa]s?|ren[uú]nci\w*|posse|empossad\w*|falec\w*|deslig\w*|afast\w*|substitu\w*|sucess\w*|suced\w*|"
    r"contrata[çc][ãa]o de (?:novo|nova)\b|contratad[oa]s?|demiss\w*|destitu\w*|aposentad\w*|licen[çc]a|mandato|"
    r"assum\w*|deixa\w*|sa[ií]da|chief|officer|appoint\w*|resign\w*|elect\w*|step(?:s|ped)? down|passe[sd] away)\b"
)
_TRATAMENTO_EN = re.compile(r"(?<![\wÀ-ÿ])(?:Mr|Mrs|Ms|Miss|Messrs)\b\.?")
_INICIAIS = re.compile(r"(?<![\wÀ-ÿ])[A-ZÀ-Ý]\.\s?(?:[A-ZÀ-Ý]\.\s?)*[A-ZÀ-Ý][a-zà-ÿ]")
_SIGLA = re.compile(r"[A-ZÀ-Ý0-9][A-ZÀ-Ý0-9&./-]{1,7}")
_TRIMESTRE = re.compile(r"\d[tTqQ]\d{2,4}|\d{1,2}[ºª°]|\d+[tT]|[1-4](?:º|°)?\s?tri\w*|\d{4}|\d+(?:[.,/]\d+)*%?")
_TOKEN = re.compile(r"[^\s()\[\]{}\"“”«»|]+")


def _sem_acento(s: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn")


def _ler_lista(caminho: Path) -> frozenset[str]:
    if not caminho.exists():
        return frozenset()
    return frozenset(
        x.strip() for x in caminho.read_text(encoding="utf-8").splitlines() if x.strip() and not x.startswith("#")
    )


@lru_cache(maxsize=1)
def vocabulario() -> frozenset[str]:
    return _ler_lista(VOCABULARIO)


@lru_cache(maxsize=1)
def maiusculas_comuns() -> frozenset[str]:
    return _ler_lista(MAIUSCULAS)


@lru_cache(maxsize=1)
def nomes_comuns() -> frozenset[str]:
    lista = _ler_lista(NOMES_COMUNS)
    return lista | frozenset(_sem_acento(x) for x in lista)


def _limpo(token: str) -> str:
    return token.strip(".,;:!?'\"’”–—-/")


def _maiuscula(token: str) -> bool:
    t = _limpo(token)
    return bool(t) and t[0].isalpha() and t[0].isupper()


def classe(token: str, todo_maiusculo: bool = False) -> str:
    """E (exceção), N (nome comum), C (palavra comum) ou P (desconhecida) de uma palavra."""
    t = _limpo(token)
    k = t.lower()
    if not any(c.isalpha() for c in t) or _TRIMESTRE.fullmatch(t) or len(t) == 1:
        return "E"  # número, trimestre ou letra sozinha ("Categoria A"); a inicial com ponto é outra regra
    if re.search(r"[/]", t) or (t.count("-") >= 1 and not re.fullmatch(r"[A-Za-zÀ-ÿ]+-[a-zà-ÿ]+", t)):
        partes = [x for x in re.split(r"[/-]", t) if x]
        if partes and len(partes) > 1:
            classes = [classe(x, todo_maiusculo) for x in partes]
            if all(c in ("E", "C") for c in classes):
                return "E"  # código ou data com barra ou hífen: "PIS/COFINS", "Maio/2017", "GEA-1"
            return "N" if "N" in classes else "P"
    if k in nomes_comuns() or _sem_acento(k) in nomes_comuns():
        return "N"
    if (k in nomes.TERMOS or _sem_acento(k) in nomes.TERMOS_CHAVE or k in INGLES or k in MESES or k in INSTITUCIONAL
            or k in LUGARES_EXTRA):  # fmt: skip
        return "E"
    if not todo_maiusculo and _SIGLA.fullmatch(t) and t.upper() == t:
        return "E"
    if todo_maiusculo and len(t) <= 5 and k not in vocabulario():
        return "E"  # no assunto todo em maiúsculas, palavra curta fora das listas conta como sigla
    if k in vocabulario() or _sem_acento(k) in vocabulario():
        return "C"
    if k in maiusculas_comuns():
        return "E"  # maiúscula em assuntos de muitas companhias: marca, instituição, lugar ou palavra em inglês
    return "P"


def _todo_maiusculo(texto: str) -> bool:
    letras = [c for c in texto if c.lower() != c.upper()]
    return bool(letras) and all(c.isupper() for c in letras)


def _corridas(tokens: list[str], todo_maiusculo: bool) -> list[tuple[int, list[str]]]:
    """Sequências de palavras maiúsculas (com conectores no meio), com a posição da primeira."""
    out, i = [], 0
    while i < len(tokens):
        if not _maiuscula(tokens[i]):
            i += 1
            continue
        palavras, k = [tokens[i]], i + 1
        while k < len(tokens) and not nomes._fim_de_frase(palavras[-1]):
            baixo = _limpo(tokens[k]).lower() or tokens[k].lower()
            if baixo in CONECTORES and k + 1 < len(tokens) and _maiuscula(tokens[k + 1]):
                palavras += [tokens[k], tokens[k + 1]]
                k += 2
            elif _maiuscula(tokens[k]):
                palavras.append(tokens[k])
                k += 1
            else:
                break
            if nomes._marca(palavras[-1]):
                break
        out.append((i, palavras))
        i = k
    return out


def _excecao_inteira(palavras: list[str], seguinte: str | None) -> bool:
    nucleo = [w for w in palavras if (_limpo(w).lower() or w.lower()) not in CONECTORES]
    if not nucleo:
        return True
    if nomes._marca(nucleo[-1]) or nomes._marca(seguinte):
        return True  # nome de companhia
    k = " ".join(_limpo(w) for w in palavras if _limpo(w))
    return nomes._excecao([k]) or nomes._excecao(palavras)


def motivo(texto: str) -> str | None:
    """Por que o assunto sai omitido (None se pode aparecer)."""
    t = texto.strip()
    if not t:
        return None
    if nomes.TRATAMENTO.search(t) or nomes.CPF.search(t) or _TRATAMENTO_EN.search(t):
        return "tratamento_ou_cpf"
    if _INICIAIS.search(t):
        return "iniciais"
    maiusculo = _todo_maiusculo(t)
    contexto = bool(_CONTEXTO_PESSOA.search(t.lower()))
    for parte in t.split("||"):
        tokens = _TOKEN.findall(parte)
        if maiusculo:
            classes = [classe(w, True) for w in tokens if any(c.isalpha() for c in w)]
            if "N" in classes or classes.count("P") >= 2 or (contexto and "P" in classes):
                return "maiusculas"
            continue
        for inicio, palavras in _corridas(tokens, maiusculo):
            fim = inicio + len(palavras)
            seguinte = tokens[fim] if fim < len(tokens) else None
            nucleo = [w for w in palavras if (_limpo(w).lower() or w.lower()) not in CONECTORES]
            classes = [classe(w) for w in nucleo]
            if contexto:
                if "N" in classes or "P" in classes:
                    if not _excecao_inteira(palavras, seguinte) or "N" in classes:
                        return "contexto_de_pessoa"
                pares = list(zip(nucleo, classes, strict=True))
                if inicio == 0 and pares and pares[0][1] == "C":
                    pares = pares[1:]  # a primeira palavra do assunto vem maiúscula por começar a frase
                if any(c == "C" for _, c in pares):
                    return "contexto_de_pessoa"
                continue
            if _excecao_inteira(palavras, seguinte):
                continue
            if "N" in classes:
                return "nome_possivel"
            if "P" not in classes:
                continue
            negocio = any((_limpo(w).lower()) in NEGOCIO for w in nucleo)
            if negocio:
                continue  # nome de companhia ou de ativo
            antes = " ".join(tokens[max(0, inicio - 4) : inicio]) + " "
            if classes.count("P") >= 2:
                return "nome_possivel"
            if inicio == 0 or _PISTA_DE_COMPANHIA.search(antes):
                continue  # a própria companhia no começo do assunto, ou companhia com pista antes
            return "nome_possivel"
    return None


def regra(texto: str) -> str:
    """ "vazio", "omitido" ou "mostrado"."""
    if not texto.strip():
        return "vazio"
    return "omitido" if motivo(texto) else "mostrado"


# ---- o vocabulário, gerado dos dados abertos do IPE (python -m chiocca.v2.leitor_f1_2.assunto vocabulario) ----


def gerar_vocabulario(brutos: Path | None = None) -> tuple[list[str], str]:
    from chiocca.v2 import ipe

    token = re.compile(r"[A-Za-zÀ-ÿ][A-Za-zÀ-ÿ'’-]*")
    por_palavra: dict[str, set[str]] = defaultdict(set)
    hashes = []
    for ano, p, tab in ipe._tabelas(brutos):
        hashes.append(f"{p.name}:{ipe._fonte(ano, p)['sha256']}")
        for cd, a in zip(tab["cd_cvm"], tab["Assunto"], strict=True):
            for w in token.findall(a):
                if w.islower() and len(w) > 1:
                    por_palavra[w].add(cd)
    palavras = sorted(w for w, cds in por_palavra.items() if len(cds) >= MINIMO_COMPANHIAS)
    return palavras, hashlib.sha256("\n".join(hashes).encode("utf-8")).hexdigest()


def gerar_maiusculas(brutos: Path | None = None) -> tuple[list[str], str]:
    """Palavras com inicial maiúscula em assuntos de pelo menos 10 companhias, fora do vocabulário em minúsculas, da
    lista de nomes comuns e da lista escrita à mão FORA_DAS_MAIUSCULAS."""
    from chiocca.v2 import ipe

    token = re.compile(r"[A-Za-zÀ-ÿ][A-Za-zÀ-ÿ'’-]*")
    por_palavra: dict[str, set[str]] = defaultdict(set)
    hashes = []
    for ano, p, tab in ipe._tabelas(brutos):
        hashes.append(f"{p.name}:{ipe._fonte(ano, p)['sha256']}")
        for cd, a in zip(tab["cd_cvm"], tab["Assunto"], strict=True):
            for w in token.findall(a):
                if w[0].isupper() and len(w) > 1:
                    por_palavra[w.lower()].add(cd)
    fora = vocabulario() | nomes_comuns() | FORA_DAS_MAIUSCULAS
    palavras = sorted(w for w, cds in por_palavra.items() if len(cds) >= MINIMO_COMPANHIAS_MAIUSCULAS and w not in fora)
    return palavras, hashlib.sha256("\n".join(hashes).encode("utf-8")).hexdigest()


def main(argv: list[str]) -> None:
    if argv[:1] == ["maiusculas"]:
        palavras, h = gerar_maiusculas()
        cab = [
            "# Palavras com inicial maiúscula nos assuntos dos fatos relevantes e comunicados ao mercado dos dados abertos",
            f"# do IPE de 2010 a 2024, em assuntos de pelo menos {MINIMO_COMPANHIAS_MAIUSCULAS} companhias, fora do vocabulário em",
            "# minúsculas, da lista de nomes comuns e de FORA_DAS_MAIUSCULAS (regra do assunto da leitor-f1-2, Fase F2b).",
            "# Gerado por python -m chiocca.v2.leitor_f1_2.assunto maiusculas.",
            f"# SHA-256 da lista dos arquivos do IPE usados (nome:sha256 de cada um): {h}",
        ]
        MAIUSCULAS.write_text("\n".join(cab + palavras) + "\n", encoding="utf-8")
        print(json.dumps({"palavras": len(palavras), "hash_dos_arquivos": h}))
        return
    if argv[:1] == ["vocabulario"]:
        palavras, h = gerar_vocabulario()
        cab = [
            "# Palavras que aparecem em minúsculas nos assuntos dos fatos relevantes e comunicados ao mercado dos dados",
            f"# abertos do IPE de 2010 a 2024, em assuntos de pelo menos {MINIMO_COMPANHIAS} companhias (regra do assunto",
            "# da leitor-f1-2, Fase F2b). Gerado por python -m chiocca.v2.leitor_f1_2.assunto vocabulario.",
            f"# SHA-256 da lista dos arquivos do IPE usados (nome:sha256 de cada um): {h}",
        ]
        VOCABULARIO.write_text("\n".join(cab + palavras) + "\n", encoding="utf-8")
        print(json.dumps({"palavras": len(palavras), "hash_dos_arquivos": h}))
        return
    for texto in argv:
        print(regra(texto), motivo(texto), texto)


if __name__ == "__main__":
    main(sys.argv[1:])
