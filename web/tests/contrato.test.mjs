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
  validaDemonstracao,
  validaDistribuicao,
  validaEmpresa,
  validaErro,
  validaFatos,
  validaInvestigacao,
  validaLeitura,
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
  assert.deepEqual(validaDemonstracao(ler("contrato", "demonstracao.json")), []);
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

test('o cartão "O motor foi testado" diz "metade das empresas": a taxa de alerta do JSON tem de continuar perto de 50%', () => {
  const t = ler("contrato", "como_testado.json").taxa_de_alerta.nao_financeiras;
  assert.ok(t > 0.45 && t < 0.55, `taxa de alerta ${t}: troque "metade" no texto da página inicial`);
});

test("a demonstração lista o caso, nunca o resultado dos sinais, e sempre em ordem alfabética", () => {
  const d = ler("contrato", "demonstracao.json");
  const comSinal = { ...d, empresas: [{ ...d.empresas[0], alerta_v1: true }] };
  assert.ok(validaDemonstracao(comSinal).some((p) => p.includes("alerta_v1")));
  const comPercentil = { ...d, empresas: [{ ...d.empresas[0], casos: [{ ...d.empresas[0].casos[0], percentil: 90 }] }] };
  assert.ok(validaDemonstracao(comPercentil).some((p) => p.includes("percentil")));
  const fora = { ...d, empresas: [{ ...d.empresas[0], nome_do_caso: "Zeta" }, { ...d.empresas[0], nome_do_caso: "Alfa" }] };
  assert.ok(validaDemonstracao(fora).some((p) => p.includes("alfabética")));
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

test("seção de leitura de documentos (Fase F1): a gerada pelo Python segue o contrato; alerta, nome e omissão errada não", () => {
  for (const lang of ["pt", "en"]) {
    const l = ler("contrato", `leitura_documental_${lang}.json`);
    assert.deepEqual(validaLeitura(l), [], lang);
    const inv = { ...ler("contrato", "investigacao.json"), leitura_documental: l };
    assert.deepEqual(validaInvestigacao(inv), [], lang);
  }
  const base = () => JSON.parse(JSON.stringify(ler("contrato", "leitura_documental_pt.json")));
  const comAlerta = base();
  comAlerta.gera_alerta = true;
  assert.ok(validaLeitura(comAlerta).length > 0, "alerta");
  const semConferencia = base();
  semConferencia.partes_relacionadas.trechos[0].conferido = false;
  assert.ok(validaLeitura(semConferencia).length > 0, "conferência");
  const omissaoErrada = base();
  const omitido = omissaoErrada.partes_relacionadas.trechos.find((t) => t.omitido);
  omitido.texto = "O imóvel da sede pertence a uma pessoa";
  assert.ok(validaLeitura(omissaoErrada).length > 0, "omitido com texto");
  const pessoaFisica = base();
  pessoaFisica.formulario_de_referencia.linhas[1].parte_omitida = false;
  pessoaFisica.formulario_de_referencia.linhas[1].parte = "Nome de Pessoa";
  assert.ok(validaLeitura(pessoaFisica).length > 0, "pessoa física com nome");
  // pessoa jurídica com nome de pessoa física dentro (o nome da firma omitido): vale nas duas línguas
  for (const lang of ["pt", "en"]) {
    const firmaOmitida = JSON.parse(JSON.stringify(ler("contrato", `leitura_documental_${lang}.json`)));
    firmaOmitida.formulario_de_referencia.linhas[1].tipo_pessoa = "PJ";
    assert.deepEqual(validaLeitura(firmaOmitida), [], `firma omitida ${lang}`);
    firmaOmitida.formulario_de_referencia.linhas[1].parte = "Nome de Pessoa Comércio Ltda.";
    assert.ok(validaLeitura(firmaOmitida).length > 0, `firma omitida com nome ${lang}`);
  }
  const comPercentil = base();
  comPercentil.percentil = 50;
  assert.ok(validaLeitura(comPercentil).length > 0, "campo de sinal");
});

test("fatos relevantes e comunicados (Fase F2a): o exemplo segue o contrato; alerta, data depois, assunto, fonte e ordem não", () => {
  for (const nome of ["americanas_2021_em_2024-12-31_pt", "americanas_2021_em_2022-04-30_en"]) {
    const inv = JSON.parse(readFileSync(join(exemplos, `${nome}.json`), "utf-8"));
    const fc = inv.o_que_se_sabia.fatos_e_comunicados;
    assert.ok(fc.itens.length > 0, nome);
    assert.deepEqual(validaFatos(fc, inv.data_referencia), [], nome);
  }
  const base = () => JSON.parse(readFileSync(join(exemplos, "americanas_2021_em_2024-12-31_pt.json"), "utf-8")).o_que_se_sabia.fatos_e_comunicados;
  const D = "2024-12-31";
  const alerta = base();
  alerta.gera_alerta = true;
  assert.ok(validaFatos(alerta, D).length > 0, "alerta");
  const depois = base();
  assert.ok(validaFatos(depois, "2022-04-30").length > 0, "entregue depois da data");
  const omitido = base();
  const i = omitido.itens.findIndex((x) => x.assunto_omitido);
  omitido.itens[i].assunto = "Renúncia de um diretor";
  assert.ok(validaFatos(omitido, D).length > 0, "assunto omitido com texto");
  const semFonte = base();
  semFonte.itens[0].fonte = { arquivo: "outro.zip", ano: 2024, sha256: "x" };
  assert.ok(validaFatos(semFonte, D).length > 0, "sem fonte");
  const ordem = base();
  ordem.itens.reverse();
  assert.ok(validaFatos(ordem, D).length > 0, "fora da ordem");
  const escore = base();
  escore.itens[0].escore = 1;
  assert.ok(validaFatos(escore, D).length > 0, "campo de sinal");
  const vazio = base();
  const v = vazio.itens.findIndex((x) => x.assunto_vazio);
  vazio.itens[v].assunto = "";
  assert.ok(validaFatos(vazio, D).length > 0, "assunto vazio sem aviso");
  const semGrupo = base();
  delete semGrupo.itens[0].grupo;
  assert.ok(validaFatos(semGrupo, D).length > 0, "sem grupo");
});
