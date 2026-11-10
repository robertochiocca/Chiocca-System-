// Testes de contrato do lado da interface, sem rede: as mesmas funções que a interface usa para conferir as
// respostas da API (lib/contrato.mjs) rodam sobre os exemplos guardados (docs/exemplos/, o mesmo JSON da API) e
// sobre as respostas da API geradas pelo teste do Python (tests/contrato/, conferidas lá contra a API de agora).
import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync, readdirSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";
import {
  AVISO,
  validaBusca,
  validaComoTestado,
  validaDistribuicao,
  validaEmpresa,
  validaErro,
  validaInvestigacao,
  validaSaude,
} from "../lib/contrato.mjs";

const aqui = dirname(fileURLToPath(import.meta.url));
const ler = (...p) => JSON.parse(readFileSync(join(aqui, ...p), "utf-8"));
const exemplos = join(aqui, "..", "..", "docs", "exemplos");

test("os exemplos guardados (o JSON da API) seguem o contrato da interface", () => {
  const nomes = readdirSync(exemplos).filter((n) => n.endsWith(".json"));
  assert.equal(nomes.length, 4);
  for (const n of nomes) assert.deepEqual(validaInvestigacao(JSON.parse(readFileSync(join(exemplos, n), "utf-8"))), [], n);
});

test("as respostas da API geradas pelo Python seguem o contrato da interface", () => {
  assert.deepEqual(validaSaude(ler("contrato", "saude.json")), []);
  assert.deepEqual(validaBusca(ler("contrato", "busca.json")), []);
  assert.deepEqual(validaEmpresa(ler("contrato", "empresa.json")), []);
  assert.deepEqual(validaInvestigacao(ler("contrato", "investigacao.json")), []);
  assert.deepEqual(validaComoTestado(ler("contrato", "como_testado.json")), []);
  for (const e of ["erro_lacre", "erro_data"]) assert.deepEqual(validaErro(ler("contrato", `${e}.json`)), [], e);
  assert.equal(ler("contrato", "erro_lacre.json").erro, "exercicio_lacrado");
  assert.equal(ler("contrato", "erro_data.json").erro, "data_fora_do_intervalo");
});

test("a busca vem em ordem alfabética e sem nenhum sinal", () => {
  const b = ler("contrato", "busca.json");
  assert.equal(b.ordem, "denominacao");
  const nomes = b.resultados.map((r) => r.denominacao);
  assert.deepEqual(nomes, [...nomes].sort((a, c) => a.localeCompare(c, "pt-BR", { sensitivity: "base" })));
  const comSinal = { ...b, resultados: [{ ...b.resultados[0], alerta_v1: true }] };
  assert.ok(validaBusca(comSinal).some((p) => p.includes("alerta_v1")));
  assert.ok(validaBusca({ ...b, ordem: "alerta" }).length > 0);
});

test("o contrato recusa o que a regra recusa", () => {
  const inv = JSON.parse(readFileSync(join(exemplos, "americanas_2021_em_2024-12-31_pt.json"), "utf-8"));
  const copia = () => JSON.parse(JSON.stringify(inv));
  const a = copia();
  a.empresa.situacao_cadastro_atual = "ATIVO";
  assert.ok(validaInvestigacao(a).length > 0, "informação de hoje no bloco da empresa");
  const b = copia();
  b.exercicios[0].exercicio = 2024;
  assert.ok(validaInvestigacao(b).length > 0, "lacre");
  const c = copia();
  c.aviso = "outro";
  assert.ok(validaInvestigacao(c).length > 0, "aviso");
  assert.ok(validaDistribuicao({ n: 20, quantis: {}, limites: [0, 1], contagens: [20], motivo: null, nomes: ["X"] }).length > 0);
  assert.equal(AVISO.pt, inv.aviso);
});
