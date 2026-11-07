"""Teste de referência com data/exemplo_resolvido.json (PROMPT.md: vem antes de tudo).

O código tem que reproduzir cada valor esperado dentro da tolerância do arquivo, inclusive o lado do corte
do M-score. Nenhum valor esperado é alterado para o teste passar: o hash do arquivo é conferido.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from chiocca.avaliacao import Contagem
from chiocca.sinais import dpo, juro_implicito, lucro_sem_caixa, mscore, peso_nao_recorrente

ARQUIVO = Path(__file__).resolve().parents[1] / "data" / "exemplo_resolvido.json"
SHA256_ESPERADO = "87e62bff3fcffd36b026009ab2c75e8b5f8eb4ebc413baab8d5772945e58adeb"
EX = json.loads(ARQUIVO.read_text(encoding="utf-8"))
TOL = EX["tolerancia_absoluta"]
T, T1 = EX["entradas"]["t"], EX["entradas"]["t-1"]
ESP = EX["esperado"]
# Valores de sinais da fase 2: referência futura, fora desta tarefa (PROMPT.md, "Arquivos que já existem").
FASE_2 = {"tata_versao_balanco", "rendimento_caixa", "dividendos_sem_caixa", "fscore_dechow"}


def perto(calculado: float | None, esperado: float) -> bool:
    return calculado is not None and abs(calculado - esperado) <= TOL


def test_arquivo_de_referencia_nao_mudou() -> None:
    assert hashlib.sha256(ARQUIVO.read_bytes()).hexdigest() == SHA256_ESPERADO


def test_todas_as_chaves_esperadas_estao_cobertas() -> None:
    cobertas = {"mscore_beneish", "dpo_salto", "juro_implicito", "lucro_sem_caixa", "peso_nao_recorrente_proxy"}
    assert set(ESP) == cobertas | FASE_2


@pytest.mark.parametrize("nome", list(mscore.COEFICIENTES))
def test_componentes_do_mscore(nome: str) -> None:
    m = mscore.calcula(T, T1)
    assert perto(m.componentes[nome].valor, ESP["mscore_beneish"]["componentes"][nome])


@pytest.mark.parametrize("nome", list(mscore.COEFICIENTES))
def test_contribuicoes_do_mscore(nome: str) -> None:
    m = mscore.calcula(T, T1)
    assert perto(m.contribuicao(nome), ESP["mscore_beneish"]["contribuicoes"][nome])


def test_mscore_e_lado_do_corte() -> None:
    m = mscore.calcula(T, T1)
    assert perto(m.m.valor, ESP["mscore_beneish"]["M"])
    assert m.m.valor is not None
    assert (m.m.valor > -1.78) is ESP["mscore_beneish"]["acima_de_-1.78"]
    assert (m.m.valor > -2.22) is ESP["mscore_beneish"]["acima_de_-2.22"]


def test_dpo() -> None:
    esp = ESP["dpo_salto"]
    assert perto(dpo.dpo(T1), esp["DPO_t-1_dias"])
    assert perto(dpo.dpo(T), esp["DPO_t_dias"])
    assert perto(dpo.variacao(T, T1).valor, esp["variacao_dias"])


def test_juro_implicito() -> None:
    esp = ESP["juro_implicito"]
    assert perto(juro_implicito.divida_media(T, T1), esp["divida_media"])
    j = juro_implicito.juro(T, T1).valor
    assert perto(j, esp["juro_implicito"])
    assert j is not None
    assert esp["cdi_medio_ilustrativo"] == EX["cdi_medio_t_ilustrativo"]
    assert perto(juro_implicito.spread_pp(j, EX["cdi_medio_t_ilustrativo"]), esp["spread_pp"])


def test_lucro_sem_caixa() -> None:
    r = lucro_sem_caixa.accruals(T, T1)
    assert perto(r.valor, ESP["lucro_sem_caixa"]["accruals_sobre_ativo_medio"])


def test_peso_nao_recorrente_proxy() -> None:
    r = peso_nao_recorrente.proxy_nao_financeiras(T)
    assert perto(r.valor, ESP["peso_nao_recorrente_proxy"]["outras_receitas_sobre_ebit"])


def test_contagem_da_avaliacao() -> None:
    a = EX["avaliacao_exemplo"]
    c = Contagem(a["empresas_avaliadas"], a["empresas_em_alerta"], a["casos_no_gabarito"], a["casos_acertados"])
    assert perto(c.taxa_de_alerta, a["taxa_de_alerta"])
    assert perto(c.acerto, a["acerto"])
    assert c.alertas_fora_do_gabarito == a["alertas_fora_do_gabarito"]
    assert perto(c.alarmes_por_acerto, a["alarmes_por_acerto"])


@pytest.mark.parametrize("chave", sorted(FASE_2))
def test_valores_da_fase_2_ficam_para_depois(chave: str) -> None:
    pytest.skip(f"{chave}: sinal da fase 2, fora desta tarefa (PROMPT.md)")
