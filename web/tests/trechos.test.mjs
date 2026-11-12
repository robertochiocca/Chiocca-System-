// Agrupamento dos trechos para mostrar (lib/trechos.mjs), o mesmo do PDF (chiocca/v2/leitura_exibicao.py, conferido
// em tests/test_v2_leitura_exibicao.py com os mesmos números): no exemplo da Americanas (exercício 2021, em
// 31/12/2024), o trecho com dois rótulos aparece uma vez, com os rótulos juntos, e os omitidos da página 40 viram uma
// entrada por bloco, com a contagem. O JSON continua com um item por trecho.
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { test } from "node:test";
import { fileURLToPath } from "node:url";
import { agrupaTrechos, comPonto, frase } from "../lib/trechos.mjs";

const RAIZ = join(dirname(fileURLToPath(import.meta.url)), "..", "..");
const inv = JSON.parse(readFileSync(join(RAIZ, "docs", "exemplos", "americanas_2021_em_2024-12-31_pt.json"), "utf-8"));
const pr = inv.leitura_documental.partes_relacionadas;

test("rótulos juntos no mesmo trecho e omitidos da mesma página numa entrada só", () => {
  const campos = agrupaTrechos(pr.campos_cpc05_18);
  const cabecalho = campos.find((g) => g.texto === "2021 2020 2021 2020");
  assert.deepEqual(cabecalho.rotulos, ["montante", "saldos"]);
  assert.equal(campos.filter((g) => g.texto === "2021 2020 2021 2020").length, 1);
  const omitidos = campos.filter((g) => g.omitido);
  assert.deepEqual(omitidos.map((g) => [g.pagina, g.n]), [[40, pr.campos_cpc05_18.filter((x) => x.omitido).length]]);
  const categorias = agrupaTrechos(pr.trechos);
  assert.deepEqual(categorias.filter((g) => g.omitido).map((g) => [g.pagina, g.n]), [[40, pr.trechos.filter((x) => x.omitido).length]]);
  // nada some: cada item do JSON está numa entrada
  assert.equal(campos.reduce((s, g) => s + (g.omitido ? g.n : g.rotulos.length), 0), pr.campos_cpc05_18.length);
});

test("no relatório do auditor, sem página, os omitidos também viram uma linha só", () => {
  const xs = [
    { omitido: true, pagina: null, texto: null, rotulo: "enfase" },
    { omitido: false, pagina: null, texto: "Ênfase X", rotulo: "enfase" },
    { omitido: true, pagina: null, texto: null, rotulo: "outros_assuntos" },
  ];
  assert.deepEqual(agrupaTrechos(xs).map((g) => [g.omitido, g.n]), [[true, 2], [false, 1]]);
});

test("frase com maiúscula e ponto, sem ponto duplo", () => {
  assert.equal(frase("documento ainda não baixado do ENET"), "Documento ainda não baixado do ENET.");
  assert.equal(frase("Já é frase."), "Já é frase.");
  assert.equal(comPonto("Antes de 2023, a companhia se chamava AMERICANAS S.A."), "Antes de 2023, a companhia se chamava AMERICANAS S.A.");
  assert.equal(comPonto("Antes de 2021, a companhia se chamava B2W - COMPANHIA DIGITAL"), "Antes de 2021, a companhia se chamava B2W - COMPANHIA DIGITAL.");
});
