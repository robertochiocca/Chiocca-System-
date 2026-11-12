"""Detector de nome de pessoa física nos trechos (regra de 11/11/2026; docs/pre-registro-leitor.md, seção 7).

Erra para o lado de omitir. Marca o texto quando houver:
- pronome de tratamento (Sr., Sra., Srs., Sras., Dr., Dra.) ou "Senhor"/"Senhora";
- CPF (o número no formato 000.000.000-00, ou a palavra CPF seguida de número);
- sequência de duas ou mais palavras com inicial maiúscula (podendo ter "de", "da", "do", "das", "dos", "e" ou "d'" no
  meio) que não termina em marca de empresa e não está na lista de exceções: nomes de companhias do cadastro da CVM
  (data/leitor/companhias_cadastro.txt, gerado por `python -m chiocca.v2.leitor.excecoes`), termos contábeis e
  institucionais (todas as palavras da sequência no vocabulário abaixo) e nomes de lugares.
Palavras de função com maiúscula no começo da frase ("A", "Em", "Para"...) não contam como nome.
"""

from __future__ import annotations

import re
import unicodedata
from functools import lru_cache
from pathlib import Path

ARQUIVO_COMPANHIAS = Path(__file__).resolve().parents[3] / "data" / "leitor" / "companhias_cadastro.txt"

TRATAMENTO = re.compile(r"(?<![\wÀ-ÿ])(Sr|Sra|Srta|Srs|Sras|Dr|Dra|Drs|Dras)\.|\bSenhor(?:a|es|as)?\b", re.UNICODE)
CPF = re.compile(r"\b\d{3}\.\d{3}\.\d{3}-\d{2}\b|\bCPF\b\s*(?:/?MF)?\s*(?:n[º°o.]*)?\s*:?\s*\d")
CONECTORES = frozenset({"de", "da", "do", "das", "dos", "e", "d'", "d’"})
# Marca de empresa no fim da sequência (ou logo depois dela), comparada sem pontuação e em minúsculas.
MARCAS = frozenset({
    "sa", "s/a", "ltda", "participacoes", "participacao", "holding", "holdings", "inc", "llc", "ltd", "limited", "corp",
    "corporation", "gmbh", "bv", "nv", "plc", "eireli", "cia", "companhia", "ag", "spa", "sarl", "fip", "fidc", "fii",
    "fundo", "fundacao", "associacao", "instituto", "cooperativa", "group", "co", "lp", "llp", "company",
})  # fmt: skip
# Palavras de função que podem vir com maiúscula no começo da frase ou de um item.
FUNCAO = frozenset("""
a o as os um uma uns umas em no na nos nas num numa de da do das dos e ou para por pela pelo pelas pelos com sem sobre
entre ao aos à às este esta estes estas esse essa esses essas isso isto aquele aquela neste nesta nesse nessa seu sua
seus suas se que quando como não sim cada todos todas todo toda outros outras outro outra também já após até durante
conforme segundo desde caso ainda mais menos assim porém contudo entretanto além há houve foi foram são é será serão
sendo nossa nosso nossas nossos tais tal qualquer quaisquer alguns algumas nenhum nenhuma referida referido referidas
referidos mesmo mesma dessa desse desta deste dessas desses destas destes nele nela neles nelas onde qual quais
""".split())  # fmt: skip
# Termos contábeis e institucionais: a sequência só de palavras daqui não é nome de pessoa.
TERMOS = frozenset("""
companhia companhias controladora controladoras controlada controladas controlador controladores coligada coligadas
consolidado consolidada consolidados consolidadas individual individuais grupo empresa empresas entidade entidades
partes parte relacionadas relacionada relacionados transações transação operações operação contratos contrato
saldos saldo ativo ativos passivo passivos patrimônio líquido resultado resultados receita receitas despesa despesas
custo custos lucro lucros prejuízo prejuízos caixa equivalentes fluxo fluxos valor valores justo contábil contábeis
demonstrações demonstração financeira financeiras financeiro financeiros nota notas explicativa explicativas
conselho conselhos administração fiscal auditoria comitê comitês diretoria diretor diretores diretora presidente
vice executivo executiva executivos assembleia assembleias geral gerais ordinária extraordinária ordinárias acionistas
acionista pessoal chave pessoal-chave remuneração remunerações benefícios benefício pós-emprego emprego curto longo
prazo prazos mútuo mútuos empréstimos empréstimo financiamentos financiamento debêntures debênture emissão emissões
série séries capital social reserva reservas legal estatutária dividendos dividendo juros sobre próprio próprios
imposto impostos renda contribuição contribuições tributos tributo diferido diferidos corrente correntes circulante
não circulantes aluguel aluguéis aluguéis mercadorias revenda venda vendas compra compras serviços serviço
prestação prestações compartilhados compartilhado plataforma digitais digital fornecedores fornecedor clientes
cliente contas receber pagar adiantamentos adiantamento provisão provisões perdas perda créditos crédito liquidação
duvidosa estimadas estimada esperadas esperada garantias garantia aval avais fiança fianças intangível imobilizado
investimentos investimento propriedades propriedade arrendamento arrendamentos direito direitos uso cessão
antecipação risco riscos sacado convênio convênios mercado mercados condições condição termos normais usuais
comutativas preços preço banco central brasil comissão mobiliários cvm cpc ifrs iasb lei leis instrução resolução
resoluções pronunciamento pronunciamentos técnico técnicos normas norma internacionais internacional relatório
relatórios auditor auditores independente independentes opinião base ênfase ênfases principais assuntos assunto
outros outras informações continuidade operacional incerteza relevante responsabilidades responsabilidade
governança órgão órgãos estatutário estatutária regimento interno política políticas código conduta ética
receita federal secretaria fazenda tesouro nacional bolsa b3 novo nível segmento mercado ações ação ordinárias
preferenciais quotas cotas fundos fundo pensão previdência privada complementar plano planos programa programas
opções opção outorga outorgas restritas restrita stock options phantom incentivo incentivos longo-prazo bônus
participação participações lucros resultados administradores administrador conselheiros conselheiro membros membro
efetivos efetivo suplentes suplente total totais subtotal saldo-final inicial final adições baixas transferências
amortização depreciação reversão constituição atualização monetária variação cambial ajuste ajustes avaliação
patrimonial equivalência período exercício exercícios trimestre semestre ano anos mês meses
sede centro centros distribuição diversos diversas estatutários estatutárias sociedade sociedades matriz filial filiais
unidade unidades negócios negócio segmentos varejo atacado indústria comércio logística tecnologia transporte transportes
energia elétrica telecomunicações saneamento seguros seguradora resseguros pagamentos meios sistemas sistema software
desenvolvimento licenciamento marcas marca royalties consultoria assessoria gestão administrativo administrativos
jurídico jurídicos contencioso trabalhistas trabalhista cíveis tributárias tributário fiscais depósitos judiciais
operacionais operacional compartilhamento rateio rateios reembolso reembolsos repasses repasse cobrança cobranças
outros-valores total-geral companhias-abertas subsidiária subsidiárias joint venture ventures coligadas investidas
investida fundador fundadores beneficiário beneficiários reais real mil milhões bilhões dólar dólares euro euros
janeiro fevereiro março abril maio junho julho agosto setembro outubro novembro dezembro
adicionado adicionados reestruturação reestruturações societária societário societárias reorganização incorporação
cisão fusão aquisição aquisições alienação combinação combinações recuperação judicial extrajudicial falência
recuperabilidade impairment teste testes estimativa estimativas julgamento julgamentos premissas premissa
reconhecimento mensuração apresentação divulgação divulgações classificação políticas práticas
paa paas cpc cpcs cvm ifrs iasb nbc ta tas dva dfp dfps itr itrs fre ipca igpm igp-m cdi selic tjlp pcld pecld
ibracon bndes irpj csll pis cofins icms iss ipi inss fgts ebitda capex uge ugc ppa sec usgaap us-gaap ofc ccr
""".split())  # fmt: skip
LUGARES = frozenset({
    "sao paulo", "rio de janeiro", "minas gerais", "belo horizonte", "porto alegre", "rio grande do sul",
    "rio grande do norte", "mato grosso", "mato grosso do sul", "santa catarina", "espirito santo", "distrito federal",
    "estados unidos", "reino unido", "america do sul", "america latina", "nova york", "nova iorque", "hong kong",
    "cayman islands", "ilhas cayman", "ilhas virgens", "costa rica", "porto rico", "nova zelandia", "africa do sul",
    "joao pessoa", "campo grande", "sao luis", "sao jose dos campos", "sao bernardo do campo", "santo andre",
})  # fmt: skip

TERMOS_CHAVE = frozenset(unicodedata.normalize("NFD", t).encode("ascii", "ignore").decode() for t in TERMOS)
_TOKEN = re.compile(r"[^\s()\[\]{}\"“”«»|]+")
_ABREVIACOES = frozenset({"s.a.", "s/a", "ltda.", "cia.", "inc.", "ltd.", "corp.", "co.", "sr.", "sra.", "dr.", "dra."})


def sem_acento(s: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn")


def chave(s: str) -> str:
    """Forma de comparação: minúsculas, sem acento e sem pontuação, com espaços simples."""
    s = sem_acento(s).lower().replace("&", " e ")
    return re.sub(r"\s+", " ", re.sub(r"[^\w\s/]", " ", s)).strip()


def _sem_marcas(nome: str) -> str:
    """Nome de companhia sem a situação ("em recuperação judicial") e sem as marcas de empresa do fim."""
    k = re.sub(
        r"\b(em recuperacao judicial|em liquidacao extrajudicial|em liquidacao|em falencia)\b.*$", "", chave(nome)
    )
    palavras = k.replace("s/a", "sa").split()
    while palavras and (palavras[-1] in MARCAS or palavras[-1] in ("s", "a") and len(palavras) > 1):
        palavras.pop()
    return " ".join(palavras)


@lru_cache(maxsize=1)
def companhias() -> frozenset[str]:
    if not ARQUIVO_COMPANHIAS.exists():
        return frozenset()
    linhas = ARQUIVO_COMPANHIAS.read_text(encoding="utf-8").splitlines()
    return frozenset(x for x in linhas if x and not x.startswith("#"))


def _limpo(token: str) -> str:
    return token.strip(".,;:!?'\"’”").strip()


def _fim_de_frase(token: str) -> bool:
    """Pontuação que encerra a sequência: fim de frase, vírgula, ponto e vírgula, dois-pontos e travessão."""
    if token.endswith((",", ";", ":", "!", "?", "–", "—")):
        return True
    return token.lower() not in _ABREVIACOES and token.endswith(".") and not re.fullmatch(r"[A-ZÀ-Ý]\.", token)


def _palavra_de_nome(token: str) -> bool:
    t = _limpo(token)
    if not t or not t[0].isupper() or not t[0].isalpha():
        return False
    if re.fullmatch(r"[IVXLC]+", t):  # algarismo romano
        return False
    if len(t) == 1:  # inicial com ponto ("P.") faz parte de nome; sem ponto ("A", "E") é palavra de função
        return bool(re.fullmatch(r"[A-ZÀ-Ý]\.", token))
    return t.lower() not in FUNCAO


def _marca(token: str | None) -> bool:
    return token is not None and chave(token).replace(" ", "") in MARCAS


def _excecao(palavras: list[str]) -> bool:
    nucleo = [_limpo(p) for p in palavras if _limpo(p).lower() not in CONECTORES]
    if all(p.lower() in TERMOS or sem_acento(p.lower()) in TERMOS_CHAVE for p in nucleo):
        return True
    k = chave(" ".join(_limpo(p) for p in palavras))
    return k in LUGARES or k in companhias() or _sem_marcas(k) in companhias()


def sequencias(texto: str) -> list[str]:
    """As sequências de palavras com inicial maiúscula (com conectores no meio) que o detector consideraria nome."""
    tokens = _TOKEN.findall(texto)
    achadas, i = [], 0
    while i < len(tokens):
        if not _palavra_de_nome(tokens[i]):
            i += 1
            continue
        palavras, k = [tokens[i]], i + 1
        while k < len(tokens) and not _fim_de_frase(palavras[-1]):
            if _limpo(tokens[k]).lower() in CONECTORES and k + 1 < len(tokens) and _palavra_de_nome(tokens[k + 1]):
                palavras += [tokens[k], tokens[k + 1]]
                k += 2
            elif _palavra_de_nome(tokens[k]):
                palavras.append(tokens[k])
                k += 1
            else:
                break
            if _marca(palavras[-1]):  # a marca de empresa encerra a sequência ("Americanas S.A. Posteriormente")
                break
        nucleo = [p for p in palavras if _limpo(p).lower() not in CONECTORES]
        seguinte = tokens[k] if k < len(tokens) else None
        if len(nucleo) >= 2 and not _marca(nucleo[-1]) and not _marca(seguinte) and not _excecao(palavras):
            achadas.append(" ".join(_limpo(p) if j == len(palavras) - 1 else p for j, p in enumerate(palavras)))
        i = k
    return achadas


def tem_nome_de_pessoa(texto: str | None) -> bool:
    if not texto:
        return False
    return bool(TRATAMENTO.search(texto) or CPF.search(texto) or sequencias(texto))
