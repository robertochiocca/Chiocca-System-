// Regras da Fase E conferidas no código da interface (pedido de 09/11/2026).
import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync, readdirSync, statSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join, relative } from "node:path";
import { DATA_MAXIMA, DATA_MINIMA, ULTIMO_EXERCICIO_LIBERADO, dataValida, exercicioValido } from "../lib/limites.mjs";

const raiz = join(dirname(fileURLToPath(import.meta.url)), "..");
const fonte = (p) => readFileSync(join(raiz, p), "utf-8");
function arquivos(pasta) {
  return readdirSync(join(raiz, pasta)).flatMap((n) => {
    const p = join(pasta, n);
    return statSync(join(raiz, p)).isDirectory() ? arquivos(p) : /\.(tsx?|mjs)$/.test(n) ? [p] : [];
  });
}
const codigo = [...arquivos("app"), ...arquivos("components"), ...arquivos("lib")];

test("limites de data e exercício iguais aos da API (chiocca/v2/lacre.py)", () => {
  const lacre = readFileSync(join(raiz, "..", "chiocca", "v2", "lacre.py"), "utf-8");
  const iso = (nome) => {
    const m = lacre.match(new RegExp(`${nome} = date\\((\\d+), (\\d+), (\\d+)\\)`));
    return `${m[1]}-${m[2].padStart(2, "0")}-${m[3].padStart(2, "0")}`;
  };
  assert.equal(DATA_MINIMA, iso("DATA_REFERENCIA_MINIMA"));
  assert.equal(DATA_MAXIMA, iso("DATA_REFERENCIA_MAXIMA"));
  assert.equal(ULTIMO_EXERCICIO_LIBERADO, Number(lacre.match(/ULTIMO_EXERCICIO_LIBERADO = (\d+)/)[1]));
  assert.ok(dataValida("2011-04-30") && dataValida("2024-12-31") && !dataValida("2025-01-01") && !dataValida("2011-04-29"));
  assert.ok(exercicioValido(2023) && !exercicioValido(2024));
});

test("nenhuma tela ordena empresas: sem sort no código e sem rota de ranking", () => {
  for (const p of codigo) {
    const t = fonte(p);
    assert.ok(!/\.sort\(/.test(t), `${p} reordena uma lista`);
    assert.ok(!/ranking|top10|maiores_alertas/i.test(relative(raiz, p)), p);
  }
  const busca = fonte("app/page.tsx");
  assert.ok(busca.includes("r.resultados.map"), "a busca mostra os resultados na ordem da API (alfabética)");
});

test("aviso fixo em todas as telas e informação de hoje separada", () => {
  assert.ok(fonte("app/layout.tsx").includes("<Topo />"));
  assert.ok(fonte("components/Topo.tsx").includes("AVISO[idioma]"));
  for (const p of ["app/investigacao/page.tsx", "app/empresa/page.tsx"]) {
    const t = fonte(p);
    const i = t.lastIndexOf("<InformacaoDeHoje");
    assert.ok(i > 0 && t.slice(i).split("\n")[1].trim() === "</>", `${p}: informação de hoje no fim`);
  }
});

test("comparação com o setor só agregada: os gráficos não recebem nomes de outras empresas", () => {
  for (const p of ["components/Histograma.tsx", "components/LinhaDoTempo.tsx"]) {
    const t = fonte(p);
    assert.ok(!/denominacao|cd_cvm|cnpj/.test(t), p);
  }
});

test("textos em PT e EN com as mesmas chaves e sem 'fraude'", async () => {
  const t = fonte("lib/textos.ts");
  const pt = t.slice(t.indexOf("  pt: {"), t.indexOf("  en: {"));
  const en = t.slice(t.indexOf("  en: {"));
  const chaves = (s) => [...s.matchAll(/^ {4}(\w+):/gm)].map((m) => m[1]).sort();
  assert.deepEqual(chaves(pt), chaves(en));
  // A única menção é o critério do gabarito, nas palavras do pré-registro (condenação da CVM ou fraude admitida).
  const semCriterio = t.replace("condenação da CVM ou fraude admitida", "").replace("CVM conviction or admitted fraud", "");
  assert.ok(!/fraude|fraud|suspeit|suspect/i.test(semCriterio));
});
