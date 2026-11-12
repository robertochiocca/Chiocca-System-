// Lista do IPE na tela (lib/ipe.mjs), como no PDF: versões do mesmo documento e documentos com a mesma data, categoria
// e assunto numa linha só, com um link para cada um; no exemplo da Americanas (exercício 2021, em 31/12/2024).
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { test } from "node:test";
import { fileURLToPath } from "node:url";
import { linhasIPE, linksDaLinha, marcaDaLinha } from "../lib/ipe.mjs";

const RAIZ = join(dirname(fileURLToPath(import.meta.url)), "..", "..");
const fc = JSON.parse(readFileSync(join(RAIZ, "docs", "exemplos", "americanas_2021_em_2024-12-31_pt.json"), "utf-8")).o_que_se_sabia.fatos_e_comunicados;
const T = { ipe_e: " e ", ipe_versao: "versão {v}", ipe_versoes: "versões {v}", ipe_documentos: "{n} documentos" };

test("um item por versão no JSON; uma linha por grupo na tela, na posição do mais recente", () => {
  const fatos = fc.itens.filter((x) => x.categoria === "fato_relevante");
  const linhas = linhasIPE(fatos);
  assert.equal(linhas.flat().length, fatos.length);
  assert.ok(linhas.length < fatos.length);
  for (const l of linhas) assert.equal(new Set(l.map((x) => x.grupo)).size, 1);
  const tutela = linhas.find((l) => l[0].assunto === "Tutela de urgência cautelar");
  assert.equal(tutela.length, 2);
  assert.equal(marcaDaLinha(tutela, T), "versões 1 e 2");
  assert.deepEqual(linksDaLinha(tutela).map((x) => x.versao), [1, 2]);
});

test("marca da linha: versão sozinha, versões, documentos", () => {
  const x = (versao, id) => ({ versao, id_documento: id, data_entrega: "2023-01-13", grupo: 1 });
  assert.equal(marcaDaLinha([x(1, "a")], T), null);
  assert.equal(marcaDaLinha([x(2, "a")], T), "versão 2");
  assert.equal(marcaDaLinha([x(1, "a"), x(1, "b")], T), "2 documentos");
  // no JSON, do mais recente para o mais antigo: as versões saem em ordem de entrega
  assert.equal(marcaDaLinha([x(2, "c"), x(2, "b"), x(1, "a")], T), "3 documentos, versões 1 e 2");
});
