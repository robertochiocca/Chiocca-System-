// Teste de tela (navegador de verdade, Playwright + Chromium) contra o site estático exportado (npm run build:estatico),
// com dados de teste montados dos exemplos versionados (docs/exemplos/: Americanas, exercício 2021, em 30/04/2022 e
// em 31/12/2024). Confere, nas duas línguas: nenhum código interno na tela; o aviso de diferença destacada no topo
// da investigação; a faixa de Tukey com a unidade uma vez só; caminhos do repositório como links; o menu do celular
// (fundo sólido, cobre o conteúdo, fecha ao navegar, ao tocar fora e com Esc; botão de tema com rótulo acessível); e
// o seletor de datas da demonstração estática, que só oferece as datas pré-geradas e diz isso na tela.
import assert from "node:assert/strict";
import { existsSync } from "node:fs";
import { dirname, join } from "node:path";
import { after, before, test } from "node:test";
import { fileURLToPath } from "node:url";
import { chromium } from "playwright";
import { subir } from "./servidor.mjs";

let servidor;
let navegador;

before(async () => {
  servidor = await subir();
  navegador = await chromium.launch();
});

after(async () => {
  await navegador?.close();
  await servidor?.fechar();
});

const INV_2024 = "/investigacao/?cd=20990&ex=2021&data=2024-12-31";
const INV_2022 = "/investigacao/?cd=20990&ex=2021&data=2022-04-30";
const EMPRESA = "/empresa/?cd=20990";
const TESTADO = "/como-o-motor-foi-testado/";
const REPOSITORIO = "https://github.com/robertochiocca/Chiocca-System-/blob/main/";
const RAIZ = join(dirname(fileURLToPath(import.meta.url)), "..", "..", "..");

async function pagina(idioma, opcoes = {}) {
  const contexto = await navegador.newContext(opcoes);
  await contexto.addInitScript((i) => localStorage.setItem("chiocca-idioma", i), idioma);
  const p = await contexto.newPage();
  const erros = [];
  p.on("pageerror", (e) => erros.push(String(e)));
  // a política de conteúdo da <meta> (site estático) não pode bloquear nada do próprio site
  p.on("console", (m) => m.type() === "error" && /Content Security Policy/i.test(m.text()) && erros.push(m.text()));
  return { p, contexto, erros };
}

async function abrir(p, caminho, esperar) {
  await p.goto(servidor.url + caminho);
  await p.locator(esperar).first().waitFor();
}

/** Abre tudo o que a tela esconde atrás de um clique: os <details> e os botões de evidências. */
async function abrirTudo(p) {
  await p.evaluate(() => {
    document.querySelectorAll("details").forEach((d) => (d.open = true));
    document.querySelectorAll("main button[aria-expanded='false']").forEach((b) => b.click());
  });
  await p.waitForFunction(() => !document.querySelector("main button[aria-expanded='false']"));
}

/** Texto da tela fora de links e de trechos em fonte de código (.mono), com tudo aberto. */
async function textoDaTela(p) {
  await abrirTudo(p);
  return p.evaluate(() => {
    const copia = document.body.cloneNode(true);
    copia.querySelectorAll("a, .mono, script, style, template, svg").forEach((n) => n.remove());
    copia.querySelectorAll("*").forEach((n) => n.append(" ")); // separa o texto de elementos vizinhos
    return copia.textContent.replace(/\s+/g, " ");
  });
}

// Código interno: identificador com sublinhado (dados_abertos, lucro_sem_caixa, nao_aplicavel, DFC_MI...). Ficam de
// fora o nome de arquivo de fonte pública (cad_cia_aberta.csv) e a notação do próprio artigo: EQ_OFFER é o nome que
// Piotroski (2000, p. 9) dá ao sinal, mostrado ao lado de ROA, CFO e ΔLEVER, como no artigo.
const CODIGO = /[A-Za-z][A-Za-z0-9]*(?:_[A-Za-z0-9]+)+(?:\.[a-z]{2,7}\b)?/g;
const NOTACAO_DOS_ARTIGOS = new Set(["EQ_OFFER"]);
function codigosInternos(texto) {
  const achados = [...texto.matchAll(CODIGO)]
    .map((m) => m[0])
    .filter((c) => !/\.[a-z]{2,7}$/.test(c) && !NOTACAO_DOS_ARTIGOS.has(c));
  // o defeito relatado: "dados_abertos · con" no lugar dos rótulos
  for (const m of texto.matchAll(/·\s*(con|ind)\b/g)) achados.push(m[0]);
  return [...new Set(achados)];
}

for (const idioma of ["pt", "en"]) {
  test(`nenhum código interno na tela (${idioma})`, async () => {
    const { p, contexto, erros } = await pagina(idioma);
    const telas = [
      [INV_2024, "#mudancas"],
      [INV_2022, "#mudancas"],
      [EMPRESA, "select"],
      [TESTADO, "main h1"],
      ["/", "form[role=search]"],
    ];
    for (const [caminho, esperar] of telas) {
      await abrir(p, caminho, esperar);
      const codigos = codigosInternos(await textoDaTela(p));
      assert.deepEqual(codigos, [], `${caminho} (${idioma}) mostra código interno: ${codigos.join(", ")}`);
    }
    await abrir(p, INV_2024, "#mudancas");
    const doc = await p.locator("section.cartao", { has: p.locator("h3", { hasText: idioma === "pt" ? "Documento usado" : "Document used" }) }).innerText();
    assert.match(doc, idioma === "pt" ? /dados abertos · consolidado/ : /open data · consolidated/);
    const csp = await p.locator('meta[http-equiv="Content-Security-Policy"]').getAttribute("content");
    assert.match(csp, /default-src 'self'/);
    assert.deepEqual(erros, []);
    await contexto.close();
  });

  test(`aviso de diferença destacada no topo da investigação (${idioma})`, async () => {
    const { p, contexto } = await pagina(idioma);
    await abrir(p, INV_2024, "#mudancas");
    const aviso = p.locator(".aviso-topo");
    const texto = (await aviso.innerText()).replace(/\s+/g, " ");
    assert.match(
      texto,
      idioma === "pt"
        ? /^6 contas com diferença destacada no comparativo da DFP 2022, entregue em 16\/11\/2023\. /
        : /^6 accounts with a highlighted difference in the comparative of the 2022 DFP, filed on 2023-11-16\. /,
    );
    // logo abaixo do título, com link para a seção
    const anterior = await aviso.evaluate((n) => n.previousElementSibling?.tagName);
    assert.equal(anterior, "H1");
    assert.equal(await aviso.locator("a").getAttribute("href"), "#mudancas");
    assert.equal(await p.locator("#mudancas").count(), 1);
    // sem diferença destacada (em 30/04/2022 a DFP 2022 ainda não existia), sem aviso
    await abrir(p, INV_2022, "#mudancas");
    assert.equal(await p.locator(".aviso-topo").count(), 0);
    await contexto.close();
  });

  test(`faixa de Tukey com a unidade uma vez só (${idioma})`, async () => {
    const { p, contexto } = await pagina(idioma);
    await abrir(p, INV_2024, "#mudancas");
    const texto = await textoDaTela(p);
    const faixa = idioma === "pt"
      ? /faixa de Tukey \(1,5 × IQR\): de (\S+) a (\S+) \(([^)]+)\); valor/g
      : /Tukey range \(1\.5 × IQR\): from (\S+) to (\S+) \(([^)]+)\); value/g;
    const achadas = [...texto.matchAll(faixa)];
    assert.ok(achadas.length > 0, "nenhuma faixa de Tukey na tela");
    const numero = idioma === "pt" ? /^−?\d{1,3}(\.\d{3})*(,\d+)?$/ : /^−?\d{1,3}(,\d{3})*(\.\d+)?$/;
    for (const [frase, a, b, unidade] of achadas) {
      assert.match(a, numero, frase);
      assert.match(b, numero, frase);
      assert.ok(unidade.length > 0 && frase.split(unidade).length === 2, `unidade repetida: ${frase}`);
    }
    await contexto.close();
  });

  test(`caminhos do repositório viram links para o GitHub (${idioma})`, async () => {
    const { p, contexto } = await pagina(idioma);
    await abrir(p, INV_2024, "#mudancas");
    await abrirTudo(p);
    const caminho = idioma === "pt" ? "docs/resultados.md" : "docs/en/results.md";
    const link = p.locator("a", { hasText: new RegExp(`^${caminho.replace(/[./]/g, "\\$&")}$`) }).first();
    assert.equal(await link.getAttribute("href"), REPOSITORIO + caminho);
    // todo link para o repositório aponta para um arquivo que existe
    const alvos = await p.locator(`a[href^="${REPOSITORIO}"]`).evaluateAll((as) => as.map((a) => a.getAttribute("href")));
    assert.ok(alvos.length > 0);
    for (const alvo of alvos) assert.ok(existsSync(join(RAIZ, alvo.slice(REPOSITORIO.length))), `link quebrado: ${alvo}`);
    await contexto.close();
  });

  test(`menu do celular (${idioma})`, async () => {
    const { p, contexto } = await pagina(idioma, { viewport: { width: 390, height: 844 }, hasTouch: true, isMobile: true });
    await abrir(p, INV_2024, "#mudancas");
    const nav = p.locator("nav#nav");
    const botaoMenu = p.locator("button.menu-btn");
    assert.equal(await nav.isVisible(), false);
    await botaoMenu.click();
    assert.equal(await nav.isVisible(), true);
    // fundo sólido, da barra até o fim da tela, na largura toda, por cima de todo o conteúdo
    const fundo = await nav.evaluate((n) => getComputedStyle(n).backgroundColor);
    assert.match(fundo, /^rgb\(/, `fundo do menu não é sólido: ${fundo}`);
    const caixa = await nav.boundingBox();
    assert.ok(caixa.x <= 0 && caixa.width >= 390 && caixa.y + caixa.height >= 844, JSON.stringify(caixa));
    const cobre = await p.evaluate(() =>
      [[20, 300], [195, 500], [370, 800], [195, 840]].every(([x, y]) => document.getElementById("nav").contains(document.elementFromPoint(x, y))),
    );
    assert.ok(cobre, "o conteúdo aparece por cima ou através do menu");
    // botão de tema com rótulo acessível, que diz o tema para o qual leva
    const escuro = idioma === "pt" ? "Tema escuro" : "Dark theme";
    const claro = idioma === "pt" ? "Tema claro" : "Light theme";
    await p.getByRole("button", { name: escuro, exact: true }).waitFor();
    assert.ok(await p.getByText(escuro, { exact: true }).isVisible());
    // tocar fora dos itens (no fundo do painel) fecha
    await p.mouse.click(6, 700);
    assert.equal(await nav.isVisible(), false);
    assert.equal(await p.evaluate(() => document.documentElement.classList.contains("menu-aberto")), false);
    // Esc fecha
    await botaoMenu.click();
    await p.keyboard.press("Escape");
    assert.equal(await nav.isVisible(), false);
    // trocar o tema fecha o menu; o rótulo passa a ser o do outro tema
    await botaoMenu.click();
    await p.getByRole("button", { name: escuro, exact: true }).click();
    assert.equal(await nav.isVisible(), false);
    await botaoMenu.click();
    await p.getByRole("button", { name: claro, exact: true }).waitFor();
    // navegar fecha
    await nav.getByRole("link", { name: idioma === "pt" ? "Como o motor foi testado" : "How the engine was tested" }).click();
    await p.waitForURL(/como-o-motor-foi-testado/);
    await p.locator("main h1").first().waitFor();
    assert.equal(await nav.isVisible(), false);
    assert.equal(await p.evaluate(() => document.documentElement.classList.contains("menu-aberto")), false);
    await contexto.close();
  });

  test(`seletor de datas da demonstração estática (${idioma})`, async () => {
    const { p, contexto } = await pagina(idioma);
    await abrir(p, EMPRESA, "select");
    const opcoes = await p.locator("select option").allInnerTexts();
    assert.deepEqual(opcoes, idioma === "pt" ? ["30/04/2022", "31/12/2024"] : ["2022-04-30", "2024-12-31"]);
    assert.equal(await p.locator("select").inputValue(), "2024-12-31"); // a data mais recente
    const explica = idioma === "pt" ? /Demonstração estática: só estas datas/ : /Static demo: only these dates/;
    assert.ok(await p.getByText(explica).isVisible());
    await p.locator("select").selectOption("2022-04-30");
    await p.waitForURL(/data=2022-04-30/);
    await p.locator("a", { hasText: idioma === "pt" ? "Investigar" : "Investigate" }).first().click();
    await p.waitForURL(/investigacao/);
    await p.locator("#mudancas").waitFor();
    // a busca: no modo estático não há seletor de data; acha pelo nome e pelo código CVM
    await abrir(p, "/", "form[role=search]");
    assert.equal(await p.locator("form[role=search] input[type=date]").count(), 0);
    await p.locator("form[role=search] input").fill("americanas");
    await p.locator("form[role=search] button[type=submit]").click();
    await p.locator("a", { hasText: /AMERICANAS/ }).first().waitFor();
    await p.locator("form[role=search] input").fill("20990");
    await p.locator("form[role=search] button[type=submit]").click();
    await p.locator("a", { hasText: /AMERICANAS/ }).first().waitFor();
    await contexto.close();
  });
}
