# Origem: Carchuna (github.com/robertochiocca/carchuna), carchuna/validade.py,
# commit a3f30ac284eb01245b022b7655bb16c4b8474cc7. Adaptado para o Chiocca System.
# O que mudou: valores em float (convenção do motor v1) em vez de Decimal; motivo em PT e EN; ponte para o
# "não calculável" do motor v1; os limiares de margem do lojista não vieram.
"""Quando o número não existe ou não merece confiança, o v2 diz isso em vez de mostrar um valor.

Três estados, e nenhum deles é exceção:

``ok``
    O número pode ir para a tela.
``indefinido``
    Não existe número: é o "não calculável" do motor v1 (conta ausente, denominador zero, receita negativa no
    denominador, plano de contas). Não há valor para mostrar, e inventar um seria pior.
``implausivel``
    A conta fechou, mas uma conferência de qualidade dos dados de entrada falhou (`chiocca.v2.conferencias`).
    O número existe e vai junto, para quem quiser auditar; confiar nele é que não dá. O estado só acompanha o
    número: **nenhum sinal ou alerta do motor v1 muda por causa dele**.

Fora de ``ok`` o motivo é obrigatório, nas duas línguas: é ele que aparece na tela no lugar do número. ``None`` e
``NaN`` nunca servem de sinal de falta.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from chiocca.sinais.resultado import Resultado as ResultadoV1

STATUS_VALIDOS = ("ok", "indefinido", "implausivel")


@dataclass(frozen=True)
class Motivo:
    pt: str
    en: str

    def __post_init__(self) -> None:
        if not self.pt.strip() or not self.en.strip():
            raise ValueError("motivo precisa de texto nas duas línguas")


@dataclass(frozen=True)
class Resultado:
    """Um número com o seu estado de validade."""

    valor: float | None
    status: str
    motivo: Motivo | None = None
    codigo: str | None = None  # motivo do motor v1 (por exemplo, "conta_ausente:depreciacao"), quando houver

    def __post_init__(self) -> None:
        if self.status not in STATUS_VALIDOS:
            raise ValueError(f"status {self.status!r} inválido; use um de {STATUS_VALIDOS}")
        if self.valor is not None and (isinstance(self.valor, float) and math.isnan(self.valor)):
            raise ValueError("NaN não é valor: use o estado indefinido")
        if self.status == "ok":
            if self.valor is None:
                raise ValueError("resultado ok precisa de valor")
        elif self.motivo is None:
            raise ValueError(f"resultado {self.status!r} precisa de motivo, que aparece no lugar do número")
        if self.status == "indefinido" and self.valor is not None:
            raise ValueError("resultado indefinido não carrega valor")

    @property
    def ok(self) -> bool:
        return self.status == "ok"

    def texto(self, lang: str = "pt", formato: str = "{}") -> str:
        """O que a tela mostra: o número formatado, ou o motivo por extenso."""
        if self.ok:
            return formato.format(self.valor)
        assert self.motivo is not None
        return self.motivo.pt if lang == "pt" else self.motivo.en

    @classmethod
    def de_valor(cls, valor: float) -> Resultado:
        return cls(valor=float(valor), status="ok")

    @classmethod
    def indefinido(cls, motivo: Motivo, codigo: str | None = None) -> Resultado:
        return cls(valor=None, status="indefinido", motivo=motivo, codigo=codigo)

    @classmethod
    def implausivel(cls, valor: float, motivo: Motivo) -> Resultado:
        return cls(valor=float(valor), status="implausivel", motivo=motivo)


# Códigos de motivo que o catálogo de textos do estudo 1 (chiocca/textos_resultados.py, congelado) não traduz: o
# M-score com componente faltando, o "não calculado" genérico e a conta ausente fora da lista curta de contas do
# catálogo (que usa, então, os nomes da tabela das duas leituras, do mesmo arquivo). O código fica como veio em
# `codigo`; o texto, não.
TIPOS_SEM_ROTULO_NO_V1 = {
    "componente_nao_calculavel": ("componente não calculável", "component not computable"),
    "nao_calculado": ("não calculado", "not computed"),
}


def rotulo_do_motivo_v1(codigo: str, lang: str) -> str:
    """Texto do motivo do motor v1 na língua pedida, sem identificador interno."""
    from chiocca.textos_resultados import CONTAS, CONTAS_TABELA, TIPOS
    from chiocca.textos_resultados import motivo as rotulo

    k = 0 if lang == "pt" else 1
    tipo, _, det = codigo.partition(":")
    if tipo in TIPOS_SEM_ROTULO_NO_V1:
        texto = TIPOS_SEM_ROTULO_NO_V1[tipo][k]
        return f"{texto}: {', '.join(det.split(','))}" if det else texto
    if tipo == "conta_ausente" and det not in CONTAS:
        from chiocca.v2.linhagem import ROTULOS_VARIAVEIS

        nome = (CONTAS_TABELA.get(det) or ROTULOS_VARIAVEIS.get(det) or (det.replace("_", " "),) * 2)[k]
        return f"{TIPOS[tipo][k]}: {nome[:1].lower()}{nome[1:]}"
    return rotulo(codigo, lang)


def de_resultado_v1(r: ResultadoV1, implausibilidades: list[Motivo] | None = None) -> Resultado:
    """Traduz o resultado do motor v1, sem mudar o valor: não calculável vira indefinido, com o mesmo motivo."""
    if r.valor is None:
        codigo = r.motivo or "nao_calculado"
        return Resultado.indefinido(
            Motivo(rotulo_do_motivo_v1(codigo, "pt"), rotulo_do_motivo_v1(codigo, "en")), codigo=codigo
        )
    if implausibilidades:
        return Resultado.implausivel(
            r.valor,
            Motivo("; ".join(m.pt for m in implausibilidades), "; ".join(m.en for m in implausibilidades)),
        )
    return Resultado.de_valor(r.valor)


def variacao_percentual(anterior: float, atual: float, grandeza: Motivo) -> Resultado:
    """Variação percentual, só quando a base é estritamente positiva.

    Com base negativa o percentual mente na travessia do zero: melhorar de −100 para −50 dá −50%, que se lê como
    piora. Com base zero não existe divisão. Nos dois casos o resultado é indefinido, e a variação absoluta (sempre
    definida) responde no lugar.
    """
    if anterior == 0:
        return Resultado.indefinido(
            Motivo(
                f"sem variação percentual de {grandeza.pt}: o exercício anterior fechou em zero",
                f"no percentage change in {grandeza.en}: the previous fiscal year closed at zero",
            )
        )
    if anterior < 0:
        return Resultado.indefinido(
            Motivo(
                f"sem variação percentual de {grandeza.pt}: o exercício anterior fechou negativo, e o percentual "
                "inverteria o sentido da mudança",
                f"no percentage change in {grandeza.en}: the previous fiscal year closed negative, and the percentage "
                "would reverse the direction of the change",
            )
        )
    return Resultado.de_valor((atual - anterior) / anterior * 100)
