"""API do Chiocca System v2 (Fase D): FastAPI em `/api/v1`, espelhando o JSON do contrato (`docs/contratos.md`).

Rotas (todas GET, todas com a data de referência e o aviso fixo):
- `/saude`: lacre, intervalo de datas e o armazém;
- `/empresas?busca=`: busca só por nome, código CVM ou CNPJ, em ordem alfabética (`chiocca.v2.busca`);
- `/empresas/{cd_cvm}`: a empresa na data (nome da época, setor, grupo e códigos de negociação);
- `/empresas/{cd_cvm}/exercicios/{exercicio}`: `ExercicioNaData` com as evidências (linhas da DFP);
- `/investigacoes/{cd_cvm}/{exercicio}`: a investigação (o mesmo JSON de `chiocca.v2.investigacao.gerar`);
- `/investigacoes/{cd_cvm}/{exercicio}/pdf`: o PDF gerado só desse JSON;
- `/investigacoes/{cd_cvm}/{exercicio}/linhagem/{sinal}`: a linhagem de um número, com as evidências;
- `/como-o-motor-foi-testado`: os números do estudo 1, do mesmo JSON do resumo (`chiocca.v2.ficha_do_motor`).

Modo demonstração (Fase E, ligado por `CHIOCCA_MODO_DEMONSTRACAO=1` ou por `criar_app(modo_demonstracao=True)`):
a busca e as rotas por empresa só aceitam as companhias dos casos do gabarito (`data/gabarito_casos.csv`, todos com
condenação da CVM ou fraude admitida, pela regra do pré-registro), sem os casos em observação; as outras são
recusadas com o motivo (403). Padrão inspirado no modo demonstração do FraudShield (MIT), sem código copiado.

As mesmas validações do contrato: data de referência de 30/04/2011 a 31/12/2024 e exercício até 2023 (lacre), com
o motivo na recusa. Regra de 09/11/2026: nenhuma rota lista empresas ordenadas por alerta, percentil ou escore, e
nenhuma aceita parâmetro de ordenação; a lista de empresas só sai da busca, em ordem alfabética. A API nunca baixa
nada: versão que falta no armazém sai como `versao_pendente_enet` (a busca no ENET é um comando separado).

Uso: python -m chiocca.v2.api [porta]   (precisa de data/armazem; uvicorn em 127.0.0.1)
"""

from __future__ import annotations

import os
import sys
from collections import OrderedDict
from collections.abc import Awaitable, Callable
from datetime import date
from typing import Any

import pandas as pd
from fastapi import FastAPI, Path, Query, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, Response

from chiocca import base
from chiocca.v2 import busca, ficha_do_motor, investigacao, modelos, pdf_investigacao
from chiocca.v2.lacre import (
    DATA_REFERENCIA_MAXIMA,
    DATA_REFERENCIA_MINIMA,
    ULTIMO_EXERCICIO_LIBERADO,
    DataForaDoIntervalo,
    ExercicioLacrado,
    garantir_data_referencia,
    garantir_liberado,
)
from chiocca.v2.linhagem import MOTOR_V1, Localizador
from chiocca.v2.na_data import _meta, exercicio_na_data

PREFIXO = "/api/v1"
PRIMEIRO_EXERCICIO = 2010
LIMITE_QUERY = 2048  # caracteres da query string
LIMITE_CORPO = 16_384  # bytes de corpo (todas as rotas são GET)
CACHE_INVESTIGACOES = 16
DATA = Query(None, description="AAAA-MM-DD, de 2011-04-30 a 2024-12-31; sem ela, a data máxima")
IDIOMA = Query("pt", pattern="^(pt|en)$")
BUSCA_DESCRICAO = "nome (3 caracteres ou mais), código CVM ou CNPJ; nunca código de negociação nem sinal"


class NaoEncontrado(LookupError):
    """Empresa ou exercício sem DFP entregue até a data; a API responde 404 com o motivo."""


class ForaDaDemonstracao(PermissionError):
    """Empresa fora do modo demonstração; a API responde 403 com o motivo."""


def empresas_da_demonstracao(raiz: Any = base.RAIZ) -> set[str]:
    """Companhias dos casos do gabarito (condenação da CVM ou fraude admitida), sem os casos em observação."""
    gab = pd.read_csv(raiz / "data" / "gabarito_casos.csv", dtype=str)
    obs = pd.read_csv(raiz / "data" / "casos_em_observacao.csv", dtype=str)
    return {_cd(c) for c in gab.cd_cvm.dropna()} - {_cd(c) for c in obs.cd_cvm.dropna()}


def modo_demonstracao_do_ambiente() -> bool:
    return os.environ.get("CHIOCCA_MODO_DEMONSTRACAO", "").strip().lower() in ("1", "true", "sim", "yes")


class Cache:
    """Investigações já geradas nesta execução (a mesma investigação serve o JSON, o PDF e a linhagem)."""

    def __init__(self, tamanho: int) -> None:
        self.tamanho, self.itens = tamanho, OrderedDict[tuple[str, int, str, str], dict[str, Any]]()

    def pega(self, chave: tuple[str, int, str, str], gera: Callable[[], dict[str, Any]]) -> dict[str, Any]:
        if chave in self.itens:
            self.itens.move_to_end(chave)
            return self.itens[chave]
        valor = gera()
        self.itens[chave] = valor
        while len(self.itens) > self.tamanho:
            self.itens.popitem(last=False)
        return valor


def _erro(status: int, erro: str, motivo: str) -> JSONResponse:
    return JSONResponse(status_code=status, content={"erro": erro, "motivo": motivo, "aviso": investigacao.AVISO})


def _data(data_referencia: str | None) -> date:
    return garantir_data_referencia(data_referencia) if data_referencia else DATA_REFERENCIA_MAXIMA


def _cd(cd_cvm: str) -> str:
    return str(cd_cvm).lstrip("0") or "0"


def criar_app(
    fontes_fabrica: Callable[[], Any] | None = None,
    localizador: Localizador | None = None,
    modo_demonstracao: bool | None = None,
) -> FastAPI:
    """`fontes_fabrica` devolve as fontes (o armazém); nos testes, o armazém montado da fixture, sem rede."""
    estado: dict[str, Any] = {}
    demonstracao = modo_demonstracao_do_ambiente() if modo_demonstracao is None else modo_demonstracao
    permitidas = empresas_da_demonstracao() if demonstracao else set()

    def _permitida(cd_cvm: str) -> None:
        if demonstracao and cd_cvm not in permitidas:
            raise ForaDaDemonstracao(
                f"modo demonstração: só as companhias dos casos públicos do gabarito; a {cd_cvm} não é uma delas"
            )

    def fontes() -> Any:
        if "fontes" not in estado:
            if fontes_fabrica is not None:
                estado["fontes"] = fontes_fabrica()
            else:
                from chiocca.v2.armazem import FontesArmazem

                estado["fontes"] = FontesArmazem()
        return estado["fontes"]

    cache = Cache(CACHE_INVESTIGACOES)
    app = FastAPI(title="Chiocca System v2", version="1", docs_url=f"{PREFIXO}/docs",
                  openapi_url=f"{PREFIXO}/openapi.json", redoc_url=None)  # fmt: skip
    app.state.fontes = fontes  # a demonstração estática usa as mesmas fontes para montar o plano e o índice

    @app.middleware("http")
    async def limite_de_tamanho(request: Request, seguinte: Callable[[Request], Awaitable[Response]]) -> Response:
        if len(request.url.query) > LIMITE_QUERY:
            return _erro(414, "requisicao_grande", f"query string acima de {LIMITE_QUERY} caracteres")
        tamanho = request.headers.get("content-length")
        if tamanho is not None and (not tamanho.isdigit() or int(tamanho) > LIMITE_CORPO):
            return _erro(413, "requisicao_grande", f"corpo acima de {LIMITE_CORPO} bytes")
        return await seguinte(request)

    @app.exception_handler(DataForaDoIntervalo)
    async def _data_fora(_: Request, e: DataForaDoIntervalo) -> JSONResponse:
        return _erro(422, "data_fora_do_intervalo", str(e))

    @app.exception_handler(ExercicioLacrado)
    async def _lacrado(_: Request, e: ExercicioLacrado) -> JSONResponse:
        return _erro(422, "exercicio_lacrado", str(e))

    @app.exception_handler(busca.BuscaInvalida)
    async def _busca(_: Request, e: busca.BuscaInvalida) -> JSONResponse:
        return _erro(422, "busca_invalida", str(e))

    @app.exception_handler(RequestValidationError)
    async def _validacao(_: Request, e: RequestValidationError) -> JSONResponse:
        detalhe = "; ".join(f"{'.'.join(str(x) for x in err['loc'])}: {err['msg']}" for err in e.errors())
        return _erro(422, "parametro_invalido", detalhe)

    @app.exception_handler(NaoEncontrado)
    async def _nao_encontrado(_: Request, e: NaoEncontrado) -> JSONResponse:
        return _erro(404, "nao_encontrado", str(e.args[0]))

    @app.exception_handler(ForaDaDemonstracao)
    async def _fora_da_demonstracao(_: Request, e: ForaDaDemonstracao) -> JSONResponse:
        return _erro(403, "fora_do_modo_demonstracao", str(e.args[0]))

    def _existe(cd_cvm: str, exercicio: int, d: date) -> None:
        if exercicio not in busca.exercicios_na_data(fontes(), cd_cvm, d):
            raise NaoEncontrado(f"empresa {cd_cvm} sem DFP do exercício {exercicio} entregue até {d.isoformat()}")

    def _investigacao(cd_cvm: str, exercicio: int, d: date, idioma: str) -> dict[str, Any]:
        garantir_liberado(exercicio)
        _permitida(cd_cvm)
        _existe(cd_cvm, exercicio, d)
        inv = cache.pega((cd_cvm, exercicio, d.isoformat(), idioma),
                         lambda: investigacao.gerar(fontes(), cd_cvm, exercicio, d, idioma, localizador))  # fmt: skip
        return modelos.Investigacao.model_validate(inv).model_dump(mode="json", exclude_unset=True)

    @app.get(f"{PREFIXO}/saude", response_model=modelos.Saude)
    def saude() -> dict[str, Any]:
        f = fontes()
        manifesto = getattr(f, "manifesto", {})
        return {"status": "ok", "api": "v1", "ultimo_exercicio_liberado": ULTIMO_EXERCICIO_LIBERADO,
                "data_referencia_minima": DATA_REFERENCIA_MINIMA.isoformat(),
                "data_referencia_maxima": DATA_REFERENCIA_MAXIMA.isoformat(),
                "armazem": {"exercicios": manifesto.get("exercicios", []), "linhas": manifesto.get("linhas", {})},
                "modo_demonstracao": demonstracao,
                "empresas_na_demonstracao": len(permitidas) if demonstracao else None,
                "motor": {"v1": MOTOR_V1, "v2": investigacao.MOTOR_V2}, "aviso": investigacao.AVISO}  # fmt: skip

    @app.get(f"{PREFIXO}/empresas", response_model=modelos.BuscaEmpresas)
    def buscar_empresas(
        busca_: str = Query(..., alias="busca", min_length=1, max_length=120, description=BUSCA_DESCRICAO),
        data_referencia: str | None = DATA,
        limite: int = Query(busca.LIMITE_PADRAO, ge=1, le=busca.LIMITE_MAXIMO),
    ) -> dict[str, Any]:
        r = busca.buscar(fontes(), busca_, _data(data_referencia), busca.LIMITE_MAXIMO if demonstracao else limite)
        if demonstracao:  # só as companhias da demonstração, na mesma ordem alfabética
            dentro = [x for x in r["resultados"] if x["cd_cvm"] in permitidas]
            r = r | {"resultados": dentro[:limite], "total": len(dentro)}
        return modelos.BuscaEmpresas.model_validate(r | {"aviso": investigacao.AVISO}).model_dump(mode="json")

    @app.get(f"{PREFIXO}/empresas/{{cd_cvm}}", response_model=modelos.EmpresaNaData)
    def empresa(
        cd_cvm: str = Path(..., pattern=r"^\d{1,6}$"), data_referencia: str | None = DATA, idioma: str = IDIOMA
    ) -> dict[str, Any]:
        d, cd = _data(data_referencia), _cd(cd_cvm)
        _permitida(cd)
        f = fontes()
        anos = busca.exercicios_na_data(f, cd, d)
        if not anos:
            raise NaoEncontrado(f"empresa {cd} sem DFP de exercício liberado entregue até {d.isoformat()}")
        meta, _ = _meta(f, anos[-1], d, so={cd})
        mt = meta.sort_values("dt_refer").iloc[-1]
        setor = mt.setor if isinstance(mt.setor, str) else None
        e = investigacao._empresa(f, cd, d, mt, setor, mt.grupo, idioma)
        out = {"data_referencia": d.isoformat(), "empresa": e, "exercicios": anos,
               "informacao_de_hoje": investigacao.informacao_de_hoje(mt.situacao_cadastro, idioma),
               "aviso": investigacao.AVISO}  # fmt: skip
        return modelos.EmpresaNaData.model_validate(out).model_dump(mode="json")

    @app.get(f"{PREFIXO}/empresas/{{cd_cvm}}/exercicios/{{exercicio}}", response_model=modelos.ExercicioComEvidencias)
    def exercicio(
        cd_cvm: str = Path(..., pattern=r"^\d{1,6}$"),
        exercicio: int = Path(..., ge=PRIMEIRO_EXERCICIO),
        data_referencia: str | None = DATA,
        idioma: str = IDIOMA,
    ) -> dict[str, Any]:
        garantir_liberado(exercicio)
        d, cd = _data(data_referencia), _cd(cd_cvm)
        _permitida(cd)
        _existe(cd, exercicio, d)
        e = exercicio_na_data(fontes(), cd, exercicio, d, localizador=localizador)
        ex = {"exercicio": exercicio, "dt_refer": e.dt_refer, "situacao": e.situacao, "versao_usada": e.versao_usada,
              "dt_receb": None if e.dt_receb is None else str(e.dt_receb),
              "versoes_conhecidas": [{"versao": v, "dt_receb": str(x)} for v, x in e.versoes_conhecidas],
              "tipo": e.tipo, "origem": e.origem, "num_doc": e.num_doc, "link": e.link,
              "escala_original": e.escala_original, "notas": [investigacao._m(n, idioma) for n in e.notas],
              "amostra_estudo_1": None}  # fmt: skip
        evs = [investigacao._ev(x) for x in e.evidencias] if e.documento is not None else []
        out = {"data_referencia": d.isoformat(), "cd_cvm": cd, "exercicio": ex, "evidencias": evs,
               "aviso": investigacao.AVISO}  # fmt: skip
        return modelos.ExercicioComEvidencias.model_validate(out).model_dump(mode="json")

    @app.get(f"{PREFIXO}/investigacoes/{{cd_cvm}}/{{exercicio}}", response_model=modelos.Investigacao)
    def investigar(
        cd_cvm: str = Path(..., pattern=r"^\d{1,6}$"),
        exercicio: int = Path(..., ge=PRIMEIRO_EXERCICIO),
        data_referencia: str | None = DATA,
        idioma: str = IDIOMA,
    ) -> JSONResponse:
        garantir_liberado(exercicio)
        return JSONResponse(_investigacao(_cd(cd_cvm), exercicio, _data(data_referencia), idioma))

    @app.get(f"{PREFIXO}/investigacoes/{{cd_cvm}}/{{exercicio}}/pdf", response_class=Response)
    def pdf(
        cd_cvm: str = Path(..., pattern=r"^\d{1,6}$"),
        exercicio: int = Path(..., ge=PRIMEIRO_EXERCICIO),
        data_referencia: str | None = DATA,
        idioma: str = IDIOMA,
    ) -> Response:
        garantir_liberado(exercicio)
        d, cd = _data(data_referencia), _cd(cd_cvm)
        corpo = pdf_investigacao.gerar(_investigacao(cd, exercicio, d, idioma))
        nome = f"chiocca_{cd}_{exercicio}_em_{d.isoformat()}_{idioma}.pdf"
        cabecalho = {"Content-Disposition": f'inline; filename="{nome}"'}
        return Response(corpo, media_type="application/pdf", headers=cabecalho)

    @app.get(f"{PREFIXO}/investigacoes/{{cd_cvm}}/{{exercicio}}/linhagem/{{sinal}}", response_model=modelos.Linhagem)
    def linhagem(
        cd_cvm: str = Path(..., pattern=r"^\d{1,6}$"),
        exercicio: int = Path(..., ge=PRIMEIRO_EXERCICIO),
        sinal: str = Path(..., pattern=r"^[A-Za-z0-9_]{1,40}$"),
        data_referencia: str | None = DATA,
        idioma: str = IDIOMA,
    ) -> dict[str, Any]:
        garantir_liberado(exercicio)
        d, cd = _data(data_referencia), _cd(cd_cvm)
        inv = _investigacao(cd, exercicio, d, idioma)
        achados = [a for lista in inv["achados"].values() for a in lista if a["sinal"] == sinal]
        if not achados:
            raise NaoEncontrado(f"sinal {sinal} não calculado para a empresa {cd} no exercício {exercicio}")
        a = achados[0]
        ids = [str(x) for x in (a.get("linhagem") or {}).get("entradas", [])]
        out = {"data_referencia": d.isoformat(), "cd_cvm": cd, "exercicio": exercicio, "idioma": idioma, "achado": a,
               "evidencias": {k: inv["evidencias"][k] for k in ids if k in inv["evidencias"]},
               "aviso": inv["aviso"]}  # fmt: skip
        return modelos.Linhagem.model_validate(out).model_dump(mode="json", exclude_unset=True)

    @app.get(f"{PREFIXO}/como-o-motor-foi-testado", response_model=modelos.ComoOMotorFoiTestadoApi)
    def como_o_motor_foi_testado() -> dict[str, Any]:
        """Os números do estudo 1, do mesmo JSON do resumo (os mesmos da ficha do motor e do README)."""
        out = ficha_do_motor.numeros() | {
            "documentos": {"pt": {"resumo": "docs/resumo.md", "ficha_do_motor": "docs/ficha-do-motor.md",
                                  "analises": "docs/analises-pos-estudo-1.md"},
                           "en": {"resumo": "docs/summary.md", "ficha_do_motor": "docs/en/engine-card.md",
                                  "analises": "docs/en/post-study-1-analyses.md"}},
            "aviso": investigacao.AVISO,
        }  # fmt: skip
        return modelos.ComoOMotorFoiTestadoApi.model_validate(out).model_dump(mode="json")

    return app


def main(argv: list[str]) -> None:
    import uvicorn

    from chiocca.v2.armazem import FontesArmazem

    fa = FontesArmazem()
    loc = Localizador(base.BRUTOS, fa.cache_enet, base.RAIZ / "data" / "manifesto_brutos.csv")
    uvicorn.run(criar_app(lambda: fa, loc), host="127.0.0.1", port=int(argv[0]) if argv else 8000)


if __name__ == "__main__":
    main(sys.argv[1:])
