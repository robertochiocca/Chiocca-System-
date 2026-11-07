"""Contagens da avaliação (pré-registro, seções 5 e 6), na forma do exemplo de data/exemplo_resolvido.json.

- taxa de alerta = empresas em alerta / empresas avaliadas;
- acerto = casos acertados / casos do gabarito;
- alertas fora do gabarito = empresas em alerta - casos acertados;
- alarmes por acerto = alertas fora do gabarito / casos acertados (definição do exemplo resolvido).
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Contagem:
    empresas_avaliadas: int
    empresas_em_alerta: int
    casos_no_gabarito: int
    casos_acertados: int

    @property
    def taxa_de_alerta(self) -> float | None:
        return None if self.empresas_avaliadas == 0 else self.empresas_em_alerta / self.empresas_avaliadas

    @property
    def acerto(self) -> float | None:
        return None if self.casos_no_gabarito == 0 else self.casos_acertados / self.casos_no_gabarito

    @property
    def alertas_fora_do_gabarito(self) -> int:
        return self.empresas_em_alerta - self.casos_acertados

    @property
    def alarmes_por_acerto(self) -> float | None:
        return None if self.casos_acertados == 0 else self.alertas_fora_do_gabarito / self.casos_acertados
