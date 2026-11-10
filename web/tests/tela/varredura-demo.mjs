// Varredura da demonstração estática real, para rodar antes de publicar (npm run varrer:demo): abre no navegador,
// nas duas línguas, a página de cada companhia e cada investigação gerada, no site exportado (out/, com os dados de
// public/demo/ gerados por python -m chiocca.v2.demonstracao_estatica), e confere que a tela abre sem erro, sem
// código interno no texto e com o PDF no lugar. Não roda no CI: os dados ficam fora do git.
import { existsSync, readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { chromium } from "playwright";
import { codigosInternos, textoDaTela } from "./comum.mjs";
import { servir } from "./servidor.mjs";

const out = join(dirname(fileURLToPath(import.meta.url)), "..", "..", "out");
if (!existsSync(join(out, "demo", "manifesto.json"))) {
  console.error("sem demonstração no site exportado: gere com python -m chiocca.v2.demonstracao_estatica e rode npm run build:estatico");
  process.exit(2);
}
const indice = JSON.parse(readFileSync(join(out, "demo", "indice.json"), "utf-8"));
const { url, fechar } = await servir(out);
const navegador = await chromium.launch();
const problemas = {};
const anota = (chave, x) => (problemas[chave] ??= []).push(x);
let investigacoes = 0;
let comAviso = 0;
for (const idioma of ["pt", "en"]) {
  const contexto = await navegador.newContext();
  await contexto.addInitScript((i) => localStorage.setItem("chiocca-idioma", i), idioma);
  const p = await contexto.newPage();
  p.on("pageerror", (e) => anota(`erro de página (${idioma})`, String(e)));
  for (const e of indice.empresas) {
    await p.goto(`${url}/empresa/?cd=${e.cd_cvm}`);
    await p.locator("select, .erro").first().waitFor();
    if (await p.locator(".erro").count()) anota(`empresa ${e.cd_cvm} ${idioma}`, await p.locator(".erro").innerText());
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
        for (const c of codigosInternos(await textoDaTela(p))) anota(chave, c);
        const pdf = await p.request.get(`${url}/demo/investigacoes/${e.cd_cvm}/${ex}/${data}/${idioma}.pdf`);
        if (pdf.status() !== 200) anota(chave, `PDF: HTTP ${pdf.status()}`);
      }
    }
  }
  await contexto.close();
}
await navegador.close();
await fechar();
console.log(JSON.stringify({ empresas: indice.empresas.length, investigacoes_abertas: investigacoes, com_aviso_de_diferenca: comAviso, problemas }, null, 1));
process.exit(Object.keys(problemas).length ? 1 : 0);
