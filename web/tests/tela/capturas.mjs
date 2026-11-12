// Capturas para revisão (Fase E2, npm run capturas): a página inicial, a empresa, a investigação (topo e com os
// detalhes abertos), o menu do celular e "Como o motor foi testado", no computador e no celular, em PT e EN, nos temas
// claro e escuro. Usa o site estático exportado (npm run build:estatico) com os dados de teste do teste de tela (os
// exemplos de docs/exemplos/). No CI, a pasta capturas/ vira artefato do job do web.
// Com --readme (npm run capturas -- --readme), copia também as imagens do README: o topo da investigação da Americanas
// (exercício 2021, em 31/12/2024), no computador e no celular, tema claro, em PT (seção em português) e em EN (seção em
// inglês), para docs/imagens/demonstracao-<aparelho>-<língua>.png.
import { copyFileSync, mkdirSync, rmSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { chromium } from "playwright";
import { abrirTudo } from "./comum.mjs";
import { subir } from "./servidor.mjs";

const web = join(dirname(fileURLToPath(import.meta.url)), "..", "..");
const destino = join(web, "capturas");
rmSync(destino, { recursive: true, force: true });
mkdirSync(destino, { recursive: true });

const INV = "/investigacao/?cd=20990&ex=2021&data=2024-12-31";
const PAGINAS = [
  ["inicio", "/", "form[role=search]"],
  ["empresa", "/empresa/?cd=20990", "nav.datas"],
  ["investigacao-topo", INV, "#mudancas"],
  ["investigacao-detalhes", INV, "#mudancas"],
  ["como-testado", "/como-o-motor-foi-testado/", "main h1"],
];
const APARELHOS = {
  computador: { viewport: { width: 1280, height: 900 }, deviceScaleFactor: 2 },
  celular: { viewport: { width: 390, height: 844 }, deviceScaleFactor: 2, isMobile: true, hasTouch: true },
};

const servidor = await subir();
const navegador = await chromium.launch();
let n = 0;
for (const [aparelho, opcoes] of Object.entries(APARELHOS)) {
  for (const idioma of ["pt", "en"]) {
    for (const tema of ["claro", "escuro"]) {
      const contexto = await navegador.newContext(opcoes);
      await contexto.addInitScript(
        ([i, t]) => {
          localStorage.setItem("chiocca-idioma", i);
          localStorage.setItem("chiocca-tema", t);
        },
        [idioma, tema === "claro" ? "light" : "dark"],
      );
      const p = await contexto.newPage();
      const nome = (pagina) => join(destino, `${pagina}_${aparelho}_${idioma}_${tema}.png`);
      for (const [pagina, caminho, esperar] of PAGINAS) {
        await p.goto(servidor.url + caminho);
        await p.locator(esperar).first().waitFor();
        if (pagina === "investigacao-detalhes") {
          await abrirTudo(p);
          // a página inteira, em resolução 1x: com tudo aberto, ela passa do limite de altura da captura em 2x
          const pagina1x = await (await navegador.newContext({ ...opcoes, deviceScaleFactor: 1 })).newPage();
          await pagina1x.addInitScript(
            ([i, t]) => {
              localStorage.setItem("chiocca-idioma", i);
              localStorage.setItem("chiocca-tema", t);
            },
            [idioma, tema === "claro" ? "light" : "dark"],
          );
          await pagina1x.goto(servidor.url + caminho);
          await pagina1x.locator(esperar).first().waitFor();
          await abrirTudo(pagina1x);
          await pagina1x.screenshot({ path: nome(pagina), fullPage: true });
          await pagina1x.context().close();
        } else {
          await p.screenshot({ path: nome(pagina), fullPage: pagina !== "investigacao-topo" });
        }
        n++;
      }
      if (aparelho === "celular") {
        await p.goto(servidor.url + "/");
        await p.locator("button.menu-btn").click();
        await p.locator("#menu-celular").waitFor();
        await p.screenshot({ path: nome("menu") });
        n++;
      }
      await contexto.close();
    }
  }
}
await navegador.close();
await servidor.fechar();
console.log(`${n} capturas em ${destino}`);
if (process.argv.includes("--readme")) {
  const imagens = join(web, "..", "docs", "imagens");
  for (const aparelho of Object.keys(APARELHOS)) {
    for (const idioma of ["pt", "en"]) {
      const alvo = join(imagens, `demonstracao-${aparelho}-${idioma}.png`);
      copyFileSync(join(destino, `investigacao-topo_${aparelho}_${idioma}_claro.png`), alvo);
      console.log(`README: ${alvo}`);
    }
  }
}
