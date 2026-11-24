"""Notas de procedimento do estudo dos EUA, antes do cálculo único (pedido de 24/11/2026, sexta rodada, item 1).

Não mudam o pré-registro nem o código congelado: registram as regras de implementação (vii) a (x), que o texto
registrado não detalha e que já estão em `chiocca/eua/estudo.py` (congelado no commit `COMMIT_DO_CONGELAMENTO`), cada
uma com o motivo, e as leituras de formato feitas nos arquivos reais da SEC, em que nenhum valor foi lido. Os números
das leituras saem de `docs/eua_leituras_de_formato.json`; o SHA-256 do código, do registro de congelamento. Um teste
confere que os documentos em PT e EN são a saída deste módulo. Fora do fecho de importação do estudo.

Uso: python -m chiocca.eua.notas
"""

from __future__ import annotations

import json
from typing import Any

from chiocca.base import RAIZ
from chiocca.formato import inteiro

DOCS = {"pt": RAIZ / "docs" / "eua-notas-de-procedimento.md", "en": RAIZ / "docs" / "en" / "us-procedure-notes.md"}
LEITURAS = RAIZ / "docs" / "eua_leituras_de_formato.json"
REGISTRO = RAIZ / "docs" / "eua_codigo_congelado.json"
COMMIT_DO_CONGELAMENTO = "dd9b662e1f2d52355722b6fe102d7e5515782115"
ARQUIVOS = ("sub.txt", "num.txt", "pre.txt")

PT = """# Notas de procedimento do estudo dos EUA, antes do cálculo único

> Escritas em 24/11/2026, depois do congelamento do código do estudo (commit `{commit}`) e antes do cálculo único, que só começa com a autorização de Roberto, depois do PR e da release do congelamento. Estas notas não mudam o [pré-registro do estudo dos EUA](pre-registro-eua.md) nem o código congelado: registram as quatro regras de implementação que o texto registrado não detalha e que já estão no código, cada uma com o motivo, e as leituras de formato feitas nos arquivos reais da SEC. Nenhum sinal americano foi calculado. Alerta, não acusação.

## 1. Onde as regras estão

- **O código congelado:** `chiocca/eua/estudo.py`, com o SHA-256 `{sha_estudo}` no [registro de congelamento](eua_codigo_congelado.json), gravado no commit `{commit}`. As regras abaixo são as do docstring desse arquivo, com o mesmo número.
- **As outras regras:** as de (i) a (vi) estão no exemplo calculado à mão (`tests/referencia/gerar_exemplo_eua.py`) e no mapa das contas (`chiocca/eua/mapa.py`); a (iii), a versão pública no corte, e a (v), a ordem de entrada, também estão no docstring de `estudo.py`. As de (vii) a (x) só existem no código do estudo.

## 2. As regras de (vii) a (x), cada uma com o motivo

### (vii) Janelas que se cruzam

- **Regra:** a empresa-ano é positiva se um episódio se abre depois do corte dela e até o último dia do mesmo mês do ano seguinte (os 12 meses da seção 5). Se as janelas de duas empresa-anos da mesma companhia se cruzam, o episódio fica com a de corte mais recente antes da abertura dele. As janelas são as das não financeiras da amostra; um episódio fora de todas elas entra só na descrição (`desfecho` e `fim_da_janela`).
- **Motivo:** a seção 5 diz que as janelas de exercícios seguidos não se sobrepõem, o que vale quando os exercícios terminam a 12 meses um do outro. Quando uma companhia muda a data de fim do exercício e entrega dois 10-K a menos de 12 meses um do outro, as janelas se cruzam. Ficar com o corte mais recente dá o episódio às demonstrações públicas mais novas na data do 8-K que o abre e mantém a regra registrada de que cada episódio cai em no máximo uma empresa-ano. O fim da janela no último dia do mês vem de o corte ser sempre o último dia de um mês (seção 3.3); para o exercício de 2024, ele cai em 30/04/2026, a data da seção 5.

### (viii) Os exercícios de 2009 e 2010, só para os AAERs

- **Regra:** os sinais e os alertas também são calculados nos exercícios de 2009 e 2010, só para a descrição dos AAERs (seção 8). Esses exercícios não entram nas medidas, nas exclusões nem nas descritivas por exercício, que são de 2011 a 2024, como na seção 4 (`EXERCICIOS_CALCULADOS` e `aaers`).
- **Motivo:** a seção 8 conta os casos de Bao et al. com anos afetados de 2009 a 2014, com a versão pública no corte, e lembra que em 2009 e 2010 só as companhias maiores entregavam em XBRL. Para saber se o v1, o v2 e a regra boba alertaram nesses anos, é preciso calcular o grupo inteiro de cada exercício, porque o decil do DPO, o da regra boba e os percentis do v2 são dentro do exercício. Como os grupos são por exercício, calcular 2009 e 2010 não muda nenhum resultado de 2011 a 2024.

### (ix) A exclusão "sem nenhum sinal calculável"

- **Regra:** a última exclusão da seção 4, "sem nenhum sinal calculável", conta as não financeiras que nem o v1 nem o v2 avaliam. As medidas são calculadas nas avaliadas pelo v1; as que só o v2 avalia (nenhum sinal do v1, mas o desvio de Benford) ficam à parte, só contadas, com a taxa do desfecho.
- **Motivo:** a seção 4 não diz de qual motor é o sinal, e o v2 tem um sinal que o v1 não tem, o desvio de Benford. A seção 6 já fixa as medidas nas avaliadas pelo v1 e o alerta do v2 calculado entre todas as que o v2 avalia, como no estudo do Brasil. Contar como excluída só a empresa-ano que nenhum dos dois avalia não tira do cálculo do v2 nenhuma que ele avalia, e o relatório mostra as duas contagens.

### (x) Os 8-K desde 2004

- **Regra:** os episódios partem de todos os 8-K e 8-K/A com o item 4.02 do histórico de entregas do EDGAR desde 2004, até 30/04/2026 (`PRIMEIRO_ANO_DO_ITEM`). As contagens da Fase 0 continuam desde 2009: o padrão de `chiocca.eua.itens.entregas` não mudou.
- **Motivo:** a seção 5 abre o episódio no primeiro 8-K da companhia com o item 4.02. Lendo só desde 2009, um 8-K de 2009 que pertence a um episódio aberto antes abriria um episódio novo e, numa sequência de 8-K a menos de 365 dias uns dos outros, poderia mudar a data de abertura dos episódios seguintes. O item 4.02 existe desde 23/08/2004, quando entraram em vigor as regras novas do 8-K.

## 3. As leituras de formato nos arquivos reais da SEC

Em {data}, durante a escrita do código e antes do congelamento, para conferir que o leitor do estudo (`chiocca.eua.estudo.le_trimestre`) aceita os arquivos como vêm da SEC. **Nenhum valor foi lido:** a coluna `value` de `num.txt` não foi carregada; nada além de nomes de arquivo, linhas de cabeçalho e contagens de linhas foi impresso; nenhum sinal, conta ou alerta foi calculado. Os números abaixo saem de [`docs/eua_leituras_de_formato.json`](eua_leituras_de_formato.json).

1. **Os nomes dos arquivos em cada zip:** nos {zips} trimestres, de {de} a {ate}, os {com} têm `sub.txt`, `num.txt` e `pre.txt`.
2. **O trimestre sem entregas ({vazio}):** a linha de cabeçalho dos três arquivos e o número de linhas de dados, como na Fase 0: {vazio_linhas}.
3. **A contagem de linhas ({trimestre}):** em cada arquivo, o número de linhas contra o número de linhas lidas pelo pandas sem tratamento de aspas (`quoting=3`, como o leitor do estudo lê `num.txt` e `pre.txt`) e com o tratamento padrão, carregando só colunas de identificação ({colunas}). As três contagens bateram em cada arquivo; as de `sub.txt` e `num.txt` são as da Fase 0.

| Arquivo | Linhas | Lidas sem aspas | Lidas com o padrão |
| --- | ---: | ---: | ---: |
{tabela}

Também foi olhado o tamanho em disco das pastas baixadas, para estimar a memória do cálculo; a escala foi medida num trimestre sintético, gerado no formato da SEC, não nos arquivos reais. O arquivo do histórico de entregas do EDGAR, com os 8-K, não foi aberto nesta etapa.

## 4. O que vem depois

O cálculo único (`python -m chiocca.eua.estudo --calculo-unico --baixar`), só com a autorização de Roberto, depois do PR e da release do congelamento (meta de 31/01/2027; reserva de 30/04/2027). Antes de ler qualquer dado, ele confere o registro de congelamento e recusa os arquivos da SEC que não foram baixados de novo no dia. Só agregados vão para o resultado versionado; nenhuma lista de companhias por alerta é publicada.
"""

EN = """# US study procedure notes, before the single computation

> Written on 2026-11-24, after the freeze of the study code (commit `{commit}`) and before the single computation, which starts only with Roberto's authorization, after the PR and the freeze release. These notes change neither the [US study pre-registration](us-preregistration.md) nor the frozen code: they record the four implementation rules that the registered text does not detail and that are already in the code, each with its reason, and the format reads done on the real SEC files. No US signal was computed. A flag, not an accusation.

## 1. Where the rules are

- **The frozen code:** `chiocca/eua/estudo.py`, with SHA-256 `{sha_estudo}` in the [freeze registry](../eua_codigo_congelado.json), written in commit `{commit}`. The rules below are the ones in that file's docstring, with the same number.
- **The other rules:** (i) to (vi) are in the hand-computed example (`tests/referencia/gerar_exemplo_eua.py`) and in the account map (`chiocca/eua/mapa.py`); (iii), the public version at the cut-off, and (v), the entry order, are also in the docstring of `estudo.py`. Rules (vii) to (x) exist only in the study code.

## 2. Rules (vii) to (x), each with its reason

### (vii) Overlapping windows

- **Rule:** a company-year is positive if an episode opens after its cut-off and up to the last day of the same month of the following year (the 12 months of section 5). If the windows of two company-years of the same company overlap, the episode goes to the one with the latest cut-off before the episode opens. The windows are those of the sample's non-financial companies; an episode outside all of them goes only into the description (`desfecho` and `fim_da_janela`).
- **Reason:** section 5 says the windows of consecutive fiscal years do not overlap, which holds when fiscal years end 12 months apart. When a company changes its fiscal year-end and files two 10-Ks less than 12 months apart, the windows overlap. Keeping the latest cut-off gives the episode to the newest public statements on the date of the 8-K that opens it and keeps the registered rule that each episode falls in at most one company-year. The window ending on the last day of the month follows from the cut-off always being the last day of a month (section 3.3); for fiscal year 2024 it falls on 2026-04-30, the date in section 5.

### (viii) Fiscal years 2009 and 2010, for the AAERs only

- **Rule:** signals and alerts are also computed for fiscal years 2009 and 2010, only for the AAER description (section 8). These fiscal years do not enter the measures, the exclusions or the per-year descriptives, which cover 2011 to 2024, as in section 4 (`EXERCICIOS_CALCULADOS` and `aaers`).
- **Reason:** section 8 counts the Bao et al. cases with affected years from 2009 to 2014, with the public version at the cut-off, and notes that in 2009 and 2010 only the larger companies filed in XBRL. To know whether v1, v2 and the naive rule flagged those years, the whole group of each fiscal year must be computed, because the DPO decile, the naive-rule decile and the v2 percentiles are within the fiscal year. Since the groups are per fiscal year, computing 2009 and 2010 changes no result from 2011 to 2024.

### (ix) The "no computable signal" exclusion

- **Rule:** the last exclusion of section 4, "no computable signal", counts the non-financial companies that neither v1 nor v2 evaluates. The measures are computed on those evaluated by v1; those that only v2 evaluates (no v1 signal, but the Benford deviation) are kept apart, only counted, with the outcome rate.
- **Reason:** section 4 does not say which engine the signal belongs to, and v2 has a signal v1 lacks, the Benford deviation. Section 6 already fixes the measures on the company-years evaluated by v1 and the v2 alert computed among all those v2 evaluates, as in the Brazilian study. Counting as excluded only the company-year that neither evaluates removes from the v2 computation none that it evaluates, and the report shows both counts.

### (x) The 8-Ks since 2004

- **Rule:** the episodes come from all 8-K and 8-K/A filings with Item 4.02 in the EDGAR filing history since 2004, up to 2026-04-30 (`PRIMEIRO_ANO_DO_ITEM`). The Phase 0 counts still start in 2009: the default of `chiocca.eua.itens.entregas` did not change.
- **Reason:** section 5 opens the episode at the company's first 8-K with Item 4.02. Reading only from 2009, a 2009 8-K that belongs to an episode opened earlier would open a new episode and, in a sequence of 8-Ks less than 365 days apart, could shift the opening date of the following episodes. Item 4.02 exists since 2004-08-23, when the new 8-K rules took effect.

## 3. The format reads on the real SEC files

On {data}, while the code was being written and before the freeze, to check that the study reader (`chiocca.eua.estudo.le_trimestre`) accepts the files as the SEC ships them. **No value was read:** the `value` column of `num.txt` was not loaded; nothing beyond file names, header lines and line counts was printed; no signal, account or alert was computed. The numbers below come from [`docs/eua_leituras_de_formato.json`](../eua_leituras_de_formato.json).

1. **The file names in each zip:** in the {zips} quarters, from {de} to {ate}, all {com} have `sub.txt`, `num.txt` and `pre.txt`.
2. **The quarter with no filings ({vazio}):** the header line of the three files and the number of data lines, as in Phase 0: {vazio_linhas}.
3. **The line count ({trimestre}):** in each file, the number of lines against the number of rows read by pandas without quote handling (`quoting=3`, as the study reader reads `num.txt` and `pre.txt`) and with the default handling, loading only identification columns ({colunas}). The three counts matched in each file; those of `sub.txt` and `num.txt` are the Phase 0 ones.

| File | Lines | Read without quotes | Read with the default |
| --- | ---: | ---: | ---: |
{tabela}

The disk size of the downloaded folders was also looked at, to estimate the memory of the computation; the scale was measured on a synthetic quarter, generated in the SEC format, not on the real files. The EDGAR filing-history file, with the 8-Ks, was not opened at this stage.

## 4. What comes next

The single computation (`python -m chiocca.eua.estudo --calculo-unico --baixar`), only with Roberto's authorization, after the PR and the freeze release (target 2027-01-31; fallback 2027-04-30). Before reading any data, it checks the freeze registry and refuses SEC files that were not downloaded again on the day. Only aggregates go into the versioned result; no list of companies by alert is published.
"""

T = {"pt": PT, "en": EN}
TRIMESTRE = {"pt": "T", "en": "Q"}


def _trimestre(t: str, lang: str) -> str:
    return t.replace("q", TRIMESTRE[lang])


def valores(leituras: dict[str, Any], registro: dict[str, Any], lang: str) -> dict[str, str]:
    i = lambda v: inteiro(int(v), lang)  # noqa: E731
    z, v, c = leituras["nomes_nos_zips"], leituras["trimestre_sem_entregas"], leituras["contagem_de_linhas"]
    data = leituras["data"]
    linhas = [
        f"| `{a}` | {i(x['linhas'])} | {i(x['lidas_sem_aspas'])} | {i(x['lidas_com_o_padrao'])} |"
        for a, x in ((a, c["arquivos"][a]) for a in ARQUIVOS)
    ]
    juntar = "; "
    return {
        "commit": COMMIT_DO_CONGELAMENTO,
        "sha_estudo": registro["codigo"]["chiocca/eua/estudo.py"],
        "data": f"{data[8:10]}/{data[5:7]}/{data[:4]}" if lang == "pt" else data,
        "zips": i(z["zips"]), "de": _trimestre(z["de"], lang), "ate": _trimestre(z["ate"], lang),
        "com": i(z["com_sub_num_pre"]), "vazio": _trimestre(v["trimestre"], lang),
        "vazio_linhas": juntar.join(f"`{a}` {i(v['linhas_de_dados'][a])}" for a in ARQUIVOS),
        "trimestre": _trimestre(c["trimestre"], lang),
        "colunas": juntar.join(f"`{a}`: " + ", ".join(f"`{x}`" for x in c["colunas_carregadas"][a]) for a in ARQUIVOS),
        "tabela": "\n".join(linhas),
    }  # fmt: skip


def render(leituras: dict[str, Any], registro: dict[str, Any], lang: str) -> str:
    return T[lang].format(**valores(leituras, registro, lang))


def ler() -> tuple[dict[str, Any], dict[str, Any]]:
    return json.loads(LEITURAS.read_text(encoding="utf-8")), json.loads(REGISTRO.read_text(encoding="utf-8"))


def main() -> None:
    leituras, registro = ler()
    for lang, caminho in DOCS.items():
        caminho.write_text(render(leituras, registro, lang), encoding="utf-8")
    print("gravado:", ", ".join(str(c.relative_to(RAIZ)) for c in DOCS.values()))


if __name__ == "__main__":
    main()
