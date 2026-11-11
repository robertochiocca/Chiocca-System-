// Varredura da demonstração estática real, para rodar antes de publicar (npm run varrer:demo): abre no navegador,
// nas duas línguas, a página de cada companhia e cada investigação gerada, no site exportado (out/, com os dados de
// public/demo/ gerados por python -m chiocca.v2.demonstracao_estatica), e confere que a tela abre sem erro, sem
// código interno no texto, sem hífen no lugar do sinal de menos e com o PDF no lugar; na lista e na página da
// companhia, o período afetado (um ano só sem intervalo) e a etiqueta de caso anterior ao início da base (2010). Serve o site debaixo do mesmo
// prefixo do build (o do GitHub Pages, se for o caso). Não roda no CI: os dados ficam fora do git.
import { existsSync, readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { chromium } from "playwright";
import { PRIMEIRO_EXERCICIO } from "../../lib/limites.mjs";
import { codigosInternos, hifensComoSinal, textoDaTela } from "./comum.mjs";
import { servir } from "./servidor.mjs";

const out = join(dirname(fileURLToPath(import.meta.url)), "..", "..", "out");
if (!existsSync(join(out, "demo", "manifesto.json"))) {
  console.error("sem demonstração no site exportado: gere com python -m chiocca.v2.demonstracao_estatica e rode npm run build:estatico");
  process.exit(2);
}
const indice = JSON.parse(readFileSync(join(out, "demo", "indice.json"), "utf-8"));
// o prefixo do build (NEXT_PUBLIC_BASE_PATH), lido do próprio site exportado: "/Chiocca-System-" no GitHub Pages
const prefixo = /(?:src|href)="([^"]*)\/_next\//.exec(readFileSync(join(out, "index.html"), "utf-8"))?.[1] ?? "";
const { url, fechar } = await servir(out, prefixo);
const navegador = await chromium.launch();
const problemas = {};
const anota = (chave, x) => (problemas[chave] ??= []).push(x);
let investigacoes = 0;
let comAviso = 0;
// casos que terminam antes do primeiro exercício da base: a lista e a página da companhia levam a etiqueta
const anteriores = (e) => e.casos.filter((c) => c.periodo_afetado && c.periodo_afetado[1] < PRIMEIRO_EXERCICIO).length;
const intervaloDeUmAno = /\b(\d{4})–\1\b/;
// página inicial: as companhias em ordem alfabética, as dez primeiras e o botão para ver todas; busca no plural
{
  const contexto = await navegador.newContext();
  await contexto.addInitScript(() => localStorage.setItem("chiocca-idioma", "pt"));
  const p = await contexto.newPage();
  await p.goto(`${url}/`);
  await p.locator(".linha-companhia").first().waitFor();
  const n = indice.empresas.length;
  if ((await p.locator(".linha-companhia").count()) !== Math.min(10, n)) anota("página inicial", "não mostra as dez primeiras");
  const botao = p.locator("button", { hasText: `Ver as ${n} companhias` });
  if (n > 10) {
    if (!(await botao.count())) anota("página inicial", `sem o botão "Ver as ${n} companhias"`);
    else {
      await botao.click();
      if ((await p.locator(".linha-companhia").count()) !== n) anota("página inicial", "o botão não mostra todas");
    }
  }
  const nomes = await p.locator(".linha-companhia > a").allInnerTexts();
  if (nomes.join("|") !== indice.empresas.map((e) => e.nome_do_caso ?? e.denominacao).join("|")) anota("página inicial", "fora da ordem do índice");
  const etiquetas = await p.locator(".linha-companhia").evaluateAll((ls) => ls.map((l) => l.querySelectorAll(".etiqueta-info").length));
  indice.empresas.forEach((e, k) => {
    if (etiquetas[k] !== anteriores(e)) anota("página inicial", `${e.cd_cvm}: ${etiquetas[k]} etiqueta(s) de caso anterior a 2010, esperado ${anteriores(e)}`);
  });
  const lista = await p.locator("#lista-companhias").innerText();
  if (intervaloDeUmAno.test(lista)) anota("página inicial", `período de um ano como intervalo: ${intervaloDeUmAno.exec(lista)[0]}`);
  await p.locator("form[role=search] input").fill("s.a");
  await p.locator("form[role=search] button[type=submit]").click();
  const rotulo = await p.locator(".resultados .rotulo").innerText();
  if (!/^\d+ empresas encontradas/.test(rotulo)) anota("busca", `concordância: ${rotulo}`);
  await contexto.close();
}

for (const idioma of ["pt", "en"]) {
  const contexto = await navegador.newContext();
  await contexto.addInitScript((i) => localStorage.setItem("chiocca-idioma", i), idioma);
  const p = await contexto.newPage();
  p.on("pageerror", (e) => anota(`erro de página (${idioma})`, String(e)));
  for (const e of indice.empresas) {
    await p.goto(`${url}/empresa/?cd=${e.cd_cvm}`);
    await p.locator("nav.datas, .erro").first().waitFor();
    if (await p.locator(".erro").count()) anota(`empresa ${e.cd_cvm} ${idioma}`, await p.locator(".erro").innerText());
    else {
      const n = await p.locator(".cartao-caso .etiqueta-info").count();
      if (n !== anteriores(e)) anota(`empresa ${e.cd_cvm} ${idioma}`, `${n} etiqueta(s) de caso anterior a 2010, esperado ${anteriores(e)}`);
      const caso = await p.locator(".cartao-caso").innerText();
      if (intervaloDeUmAno.test(caso)) anota(`empresa ${e.cd_cvm} ${idioma}`, `período de um ano como intervalo: ${intervaloDeUmAno.exec(caso)[0]}`);
    }
    for (const [data, exercicios] of Object.entries(e.datas)) {
      for (const ex of exercicios) {
        investigacoes++;
        const chave = `${e.cd_cvm} ${ex} ${data} ${idioma}`;
        await p.goto(`${url}/investigacao/?cd=${e.cd_cvm}&ex=${ex}&data=${data}`);
        await p.locator("#mudancas, .erro").first().waitFor({ timeout: 30000 });
        if (await p.locator(".erro").count()) {
          anota(chave, `erro: ${await p.locator(".erro").innerText()}`);
          continue;
        }
        comAviso += await p.locator(".aviso-topo").count();
        const texto = await textoDaTela(p);
        for (const c of codigosInternos(texto)) anota(chave, c);
        for (const h of hifensComoSinal(texto)) anota(chave, `hífen como sinal de menos: ${h}`);
        const pdf = await p.request.get(`${url}/demo/investigacoes/${e.cd_cvm}/${ex}/${data}/${idioma}.pdf`);
        if (pdf.status() !== 200) anota(chave, `PDF: HTTP ${pdf.status()}`);
      }
    }
  }
  await contexto.close();
}
await navegador.close();
await fechar();
const resumo = {
  prefixo,
  empresas: indice.empresas.length,
  investigacoes_abertas: investigacoes,
  com_aviso_de_diferenca: comAviso,
  com_caso_anterior_a_2010: indice.empresas.filter(anteriores).map((e) => `${e.cd_cvm} ${e.nome_do_caso ?? e.denominacao}`),
};
console.log(JSON.stringify({ ...resumo, problemas }, null, 1));
process.exit(Object.keys(problemas).length ? 1 : 0);
