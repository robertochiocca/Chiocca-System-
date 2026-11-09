"""Contratos da API em Pydantic (Fase D), do mesmo modelo do JSON da Fase C (`docs/contratos.md`, seção 2).

Os modelos validam o JSON que `chiocca.v2.investigacao.gerar` já produz: a API não recalcula nada, só confere o
contrato e devolve os mesmos números do motor. Campos desconhecidos são recusados (`extra="forbid"`), e as mesmas
validações do contrato valem aqui: data de referência de 30/04/2011 a 31/12/2024 e exercício até o lacre (2023).
"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, field_validator, model_validator

from chiocca.v2.investigacao import AVISO
from chiocca.v2.lacre import garantir_data_referencia, garantir_liberado

Idioma = Literal["pt", "en"]
Familia = Literal["possivel_manipulacao", "risco_financeiro", "qualidade_financeira"]


class Modelo(BaseModel):
    model_config = ConfigDict(extra="forbid")


class ComData(Modelo):
    data_referencia: str

    @field_validator("data_referencia")
    @classmethod
    def _data(cls, v: str) -> str:
        return garantir_data_referencia(v).isoformat()


class FcaOrigem(Modelo):
    ano: int
    versao: int
    dt_receb: str


class CodigoNegociacao(Modelo):
    codigo: str
    valor_mobiliario: str | None
    mercado: str | None
    inicio_negociacao: str | None
    fim_negociacao: str | None
    fca: FcaOrigem


class EmpresaResumo(Modelo):
    cd_cvm: str
    cnpj: str | None
    denominacao: str | None
    origem_denominacao: Literal["fca", "indice_dfp"]
    codigos_negociacao: list[CodigoNegociacao]
    motivo_codigos_negociacao: str | None


class Empresa(EmpresaResumo):
    setor: str | None
    origem_setor: str | None
    grupo: Literal["financeira", "nao_financeira"] | None
    situacao_cadastro_atual: str | None


class VersaoConhecida(Modelo):
    versao: int
    dt_receb: str


class ExercicioNaData(Modelo):
    exercicio: int
    dt_refer: str | None
    situacao: str
    versao_usada: int | None
    dt_receb: str | None
    versoes_conhecidas: list[VersaoConhecida]
    tipo: str | None
    origem: str | None
    num_doc: str | None
    link: str | None
    escala_original: Literal["MIL", "UNIDADE"] | None
    notas: list[str | None]
    amostra_estudo_1: str | None

    @field_validator("exercicio")
    @classmethod
    def _lacre(cls, v: int) -> int:
        return garantir_liberado(v)


class Valor(Modelo):
    valor: float | None
    status: str
    motivo: str | None
    codigo: str | None


class Achado(Modelo):
    """Um sinal numa família. Os do motor v1 trazem regra, alerta, confiança e linhagem; os de contexto (Z'' e F)
    trazem texto, componentes e marcas, e `alerta_v1` é sempre nulo: não geram alerta."""

    id: str
    familia: Familia
    sinal: str
    exercicio: int
    rotulo: str | None
    valor: Valor
    valor_no_produto: Valor | None = None
    regra: str | None
    alerta_v1: bool | None
    contexto: dict[str, Any] | None
    confianca: dict[str, Any] | None = None
    explicacao: str | None = None
    explicacoes_alternativas: list[str | None] | None = None
    limitacoes: list[str | None] | None = None
    texto: str | None = None
    componentes: dict[str, Any] | None = None
    marcas: list[str | None] | None = None
    linhagem: dict[str, Any] | None
    natureza: dict[str, str]

    @model_validator(mode="after")
    def _contexto_sem_alerta(self) -> Achado:
        if self.familia != "possivel_manipulacao" and self.alerta_v1 is not None:
            raise ValueError("indicador de contexto não gera alerta")
        return self


class DiferencaComparativo(Modelo):
    texto: str | None
    demonstracao: str
    cd_conta: str
    ds_conta: str
    valor: float
    valor_comparativo: float
    diferenca: float
    grupo: Literal["a", "b"]
    destacada: bool
    versao: int | None
    dt_receb: str | None
    versao_seguinte: int | None
    dt_receb_seguinte: str | None


class LinhaChave(Modelo):
    demonstracao: str
    cd_conta: str


class Materialidade(Modelo):
    linhas_chave: list[LinhaChave]
    limite_relativo: float
    ativo_total: float | None
    limite: float | None
    texto: str


class VersaoNaData(VersaoConhecida):
    usada: bool


class Mudancas(Modelo):
    versoes_conhecidas: list[VersaoNaData]
    comparativo_destacadas: list[DiferencaComparativo]
    reapresentacao_pelo_comparativo: list[DiferencaComparativo]
    tolerancia_comparativo: float
    materialidade_comparativo: Materialidade

    @model_validator(mode="after")
    def _destacadas(self) -> Mudancas:
        if any(not (x.destacada and x.grupo == "a") for x in self.comparativo_destacadas):
            raise ValueError("só diferenças do grupo (a) acima do limite são destacadas")
        return self


class DocumentoConhecido(Modelo):
    tipo: str
    exercicio: int
    versao: int
    dt_receb: str
    num_doc: str | None


class OQueSeSabia(Modelo):
    documentos: list[DocumentoConhecido]
    nota: str


class Conferencia(Modelo):
    id: str
    tipo: str
    nome: str | None
    coluna: str | None
    resultado: str
    motivo: str | None


class QualidadeDosDados(Modelo):
    conferencias: list[Conferencia]


class AuditorNoFca(Modelo):
    auditor: str
    codigo_cvm: str
    inicio: str | None
    fim: str | None


class FcaAuditores(Modelo):
    ano_fca: int
    dt_receb: str
    auditores: list[AuditorNoFca]


class Saida(Modelo):
    auditor: str
    codigo_cvm: str
    primeiro_exercicio: int | None
    ultimo_exercicio: int | None
    exercicios_consecutivos: int | None
    compativel_com_rodizio: bool
    artigo: str | None
    norma: str | None
    nota: str


class Troca(Modelo):
    ano_fca: int
    de: list[str]
    para: list[str]
    saidas: list[Saida]


class Rodizio(Modelo):
    nota: str | None
    norma: str
    fonte: str
    conferida_em: str


class ParecerEAuditor(Modelo):
    natureza: Literal["trecho_literal"]
    gera_alerta: Literal[False]
    relatorio_do_auditor: dict[str, Any]
    auditores_no_fca: list[FcaAuditores] | None = None
    trocas_de_auditor: list[Troca] | None = None
    rodizio: Rodizio | None = None


class ComoOMotorFoiTestado(Modelo):
    documento: str
    acertados: int
    acertaveis: int
    alarmes_por_acerto_periodo_inteiro: float
    taxa_de_alerta_nao_financeiras: float


class Evidencia(Modelo):
    id: str
    documento: dict[str, Any]
    demonstracao: str
    coluna: str
    cd_conta: str
    ds_conta: str | None
    valor: float | None
    localizacao: dict[str, Any] | None


class Motor(Modelo):
    v1: str
    v2: str


class Investigacao(ComData):
    empresa: Empresa
    idioma: Idioma
    exercicios: list[ExercicioNaData]
    achados: dict[Familia, list[Achado]]
    mudancas: Mudancas
    o_que_se_sabia: OQueSeSabia
    qualidade_dos_dados: QualidadeDosDados
    parecer_e_auditor: ParecerEAuditor | None
    como_o_motor_foi_testado: ComoOMotorFoiTestado
    limites: list[str]
    limitacoes: list[str | None]
    evidencias: dict[str, Evidencia]
    motor: Motor
    gerado_em: str
    aviso: str

    @model_validator(mode="after")
    def _aviso(self) -> Investigacao:
        if self.aviso != AVISO[self.idioma]:
            raise ValueError("aviso fixo diferente do contrato")
        return self


class Saude(Modelo):
    status: Literal["ok"]
    api: str
    ultimo_exercicio_liberado: int
    data_referencia_minima: str
    data_referencia_maxima: str
    armazem: dict[str, Any]
    motor: Motor
    aviso: dict[Idioma, str]


class BuscaEmpresas(ComData):
    busca: str
    criterio: Literal["nome", "cd_cvm", "cnpj"]
    ordem: Literal["denominacao"]
    total: int
    resultados: list[EmpresaResumo]
    aviso: dict[Idioma, str]


class EmpresaNaData(ComData):
    empresa: Empresa
    exercicios: list[int]
    aviso: dict[Idioma, str]


class ExercicioComEvidencias(ComData):
    cd_cvm: str
    exercicio: ExercicioNaData
    evidencias: list[Evidencia]
    aviso: dict[Idioma, str]


class Linhagem(ComData):
    cd_cvm: str
    exercicio: int
    idioma: Idioma
    achado: Achado
    evidencias: dict[str, Evidencia]
    aviso: str


class Erro(Modelo):
    erro: str
    motivo: str
    aviso: dict[Idioma, str]
