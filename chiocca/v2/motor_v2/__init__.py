"""Motor v2 (pré-registro do motor v2, registrado em 22/11/2026, commit 313c52d).

O motor v1 com três mudanças, cada uma com uma chave (`motor.Mudancas`): o DEPI pela DVA (`dva`), o desvio de Benford
padronizado (`benford`) e o alerta pelo escore (`escore`). Tudo o mais vem do v1, por importação, sem mudar nenhum
arquivo do registro do v1 (`docs/estudo_2_codigo_congelado.json`). Com as três chaves desligadas, o v2 é o v1.

O produto (interface, API e demonstração) continua com o v1 e não importa este pacote. O código do v2 não lê o gabarito
do estudo 1 nem importa as métricas dele (pré-registro do motor v2, seção 5; `tests/test_v2_motor_v2.py`).
"""
