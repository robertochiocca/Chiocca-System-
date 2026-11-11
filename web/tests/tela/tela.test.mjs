// Teste de tela (navegador de verdade, Playwright + Chromium) contra o site estático exportado (npm run build:estatico),
// com dados de teste montados dos exemplos versionados (docs/exemplos/: Americanas, exercício 2021, em 30/04/2022 e em
// 31/12/2024) e das respostas da API guardadas (tests/contrato/). Confere a experiência da Fase E2 nas duas línguas:
// cabeçalho (PT | EN, tema, só o aviso fixo), página inicial, empresa, investigação (resumo, índice, cartões, selos,
// ajuda, mudanças), "Como o motor foi testado", o menu do celular, nenhum código interno nem hífen como sinal de menos
// na tela, e a acessibilidade (axe, sem violação séria ou crítica, nos temas claro e escuro).
import assert from "node:assert/strict";
import { existsSync } from "node:fs";
import { dirname, join } from "node:path";
import { after, before, test } from "node:test";
import { fileURLToPath } from "node:url";
import AxeBuilder from "@axe-core/playwright";
import { chromium } from "playwright";
import { abrirTudo, codigosInternos, hifensComoSinal, textoDaTela } from "./comum.mjs";
import { INV_FIXTURE, subir } from "./servidor.mjs";

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
const CELULAR = { viewport: { width: 390, height: 844 }, hasTouch: true, isMobile: true };
const COMPUTADOR = { viewport: { width: 1280, height: 900 } };
const TAGS_AXE = ["wcag2a", "wcag2aa", "wcag21a", "wcag21aa", "wcag22aa"];

async function pagina(idioma, opcoes = COMPUTADOR, tema = "light") {
  const contexto = await navegador.newContext(opcoes);
  await contexto.addInitScript(
    ([i, t]) => {
      localStorage.setItem("chiocca-idioma", i);
      localStorage.setItem("chiocca-tema", t);
    },
    [idioma, tema],
  );
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

const texto = async (loc) => (await loc.innerText()).replace(/\s+/g, " ").trim();
// os itens do caminho de navegação (os separadores "›" são desenhados pelo CSS)
const itensDoCaminho = async (p) => (await p.locator("nav.migalhas li").allInnerTexts()).map((x) => x.trim());

async function violacoesSerias(p, onde) {
  const r = await new AxeBuilder({ page: p }).withTags(TAGS_AXE).analyze();
  return r.violations
    .filter((v) => ["serious", "critical"].includes(v.impact))
    .map((v) => `${onde}: ${v.id} (${v.impact}) ${v.nodes.slice(0, 3).map((n) => n.target.join(" ")).join(" | ")}`);
}

for (const idioma of ["pt", "en"]) {
  const pt = idioma === "pt";

  test(`nenhum código interno nem hífen como sinal de menos na tela (${idioma})`, async () => {
    const { p, contexto, erros } = await pagina(idioma);
    const telas = [
      [INV_2024, "#mudancas"],
      [INV_2022, "#mudancas"],
      [EMPRESA, "nav.datas"],
      [TESTADO, "table"],
      ["/", ".linha-companhia"],
      ...(pt ? [[INV_FIXTURE, "#mudancas"]] : []), // a resposta guardada da fixture só existe em PT
    ];
    for (const [caminho, esperar] of telas) {
      await abrir(p, caminho, esperar);
      const t = await textoDaTela(p);
      assert.deepEqual(codigosInternos(t), [], `${caminho} (${idioma}) mostra código interno`);
      assert.deepEqual(hifensComoSinal(t), [], `${caminho} (${idioma}) usa hífen como sinal de menos`);
    }
    await abrir(p, INV_2024, "#mudancas");
    assert.match(await texto(p.locator(".documento-usado")), pt ? /dados abertos · consolidado/ : /open data · consolidated/);
    const csp = await p.locator('meta[http-equiv="Content-Security-Policy"]').getAttribute("content");
    assert.match(csp, /default-src 'self'/);
    assert.deepEqual(erros, []);
    await contexto.close();
  });

  test(`cabeçalho: PT | EN lado a lado, tema com rótulo e só o aviso fixo (${idioma})`, async () => {
    const { p, contexto } = await pagina(idioma);
    await abrir(p, INV_2024, "#mudancas");
    const grupo = p.locator(".topo .segmentado");
    const [botaoPt, botaoEn] = [grupo.getByRole("button", { name: "PT" }), grupo.getByRole("button", { name: "EN" })];
    assert.equal(await botaoPt.getAttribute("aria-pressed"), String(pt));
    assert.equal(await botaoEn.getAttribute("aria-pressed"), String(!pt));
    const tema = p.locator(".topo button.botao-icone");
    assert.equal(await tema.getAttribute("aria-label"), pt ? "Tema escuro" : "Dark theme");
    await tema.click();
    assert.equal(await p.evaluate(() => document.documentElement.dataset.theme), "dark");
    assert.equal(await tema.getAttribute("aria-label"), pt ? "Tema claro" : "Light theme");
    await (pt ? botaoEn : botaoPt).click();
    assert.equal(await p.evaluate(() => document.documentElement.lang), pt ? "en" : "pt-BR");
    // rolando a página, o cabeçalho e a faixa da demonstração saem; o aviso fica no topo
    await p.evaluate(() => window.scrollTo(0, 2500));
    await p.waitForFunction(() => window.scrollY > 1500);
    const aviso = await p.locator(".aviso").boundingBox();
    const topo = await p.locator("header.topo").boundingBox();
    const faixa = await p.locator(".faixa-demo").boundingBox();
    assert.ok(Math.abs(aviso.y) < 1, `aviso no topo: ${aviso.y}`);
    assert.ok(topo.y + topo.height <= 0 && faixa.y + faixa.height <= 0, "cabeçalho e faixa da demonstração rolam");
    // no computador, o aviso inteiro numa linha; a versão curta do celular fica escondida
    assert.equal(await p.locator(".aviso .aviso-longo").isVisible(), true);
    assert.equal(await p.locator(".aviso .aviso-curto").isVisible(), false);
    assert.ok(aviso.height < 40, `aviso em mais de uma linha no computador: ${aviso.height}`);
    // rodapé com o aviso completo (destino do "Saiba mais" do celular; já na outra língua, trocada acima), o
    // repositório e a ficha do motor
    assert.match(await texto(p.locator("footer #aviso-completo")), pt ? /Not an accusation, not investment advice\./ : /Não é acusação, não é recomendação de investimento\./);
    const rodape = await p.locator("footer a").evaluateAll((as) => as.map((a) => a.getAttribute("href")));
    assert.ok(rodape.includes("https://github.com/robertochiocca/Chiocca-System-"));
    assert.ok(rodape.some((h) => /ficha-do-motor\.md|engine-card\.md/.test(h)));
    await contexto.close();
  });

  test(`página inicial (${idioma})`, async () => {
    const { p, contexto } = await pagina(idioma);
    await abrir(p, "/", ".linha-companhia");
    await p.locator(".cartao-comece").nth(2).waitFor();
    assert.equal(await texto(p.locator("h1")), pt ? "Investigar uma companhia aberta, como era numa data" : "Investigate a listed company, as it was on a date");
    assert.match(await texto(p.locator(".abertura")), pt ? /só entra o que já tinha sido entregue naquele dia/ : /only what had already been filed/);
    assert.match(await texto(p.locator(".nota-demo")), pt ? /^Demonstração: 2 companhias com caso público, em datas fixas/ : /^Demo: 2 companies/);
    assert.match(await texto(p.locator(".cartao-busca")), pt ? /Nada é ordenado por alerta/ : /Nothing is ranked by alert/);
    const comece = (await p.locator(".cartao-comece").allInnerTexts()).map((x) => x.replace(/\s+/g, " "));
    assert.match(comece[0], pt ? /AMERICANAS S\.A\., exercício 2021, em 30\/04\/2022\./ : /AMERICANAS S\.A\., fiscal year 2021, on 2022-04-30\./);
    assert.match(
      comece[1],
      pt ? /patrimônio líquido de 2021 passa de R\$ 15,9 bilhões para −R\$ 12,6 bilhões no comparativo/ : /2021 equity goes from R\$15\.9 billion to −R\$12\.6 billion/,
    );
    assert.match(comece[2], pt ? /7 de 13 casos, com alerta em metade das empresas/ : /7 of 13 cases, with alerts on half/);
    // companhias da demonstração: ordem alfabética pelo nome do caso no gabarito, o caso público (tipo com inicial
    // maiúscula, data pública e período afetado, um ano só sem intervalo) e nada de sinal
    const linhas = (await p.locator(".linha-companhia").allInnerTexts()).map((x) => x.replace(/\s+/g, " ").trim());
    assert.equal(linhas.length, 2);
    assert.equal(
      linhas[0],
      pt ? "Americanas S.A. Fraude admitida Data pública: 11/01/2023 Período afetado: 2021" : "Americanas S.A. Admitted fraud Public date: 2023-01-11 Affected period: 2021",
    );
    assert.match(linhas[1], pt ? /^Empresa Cem S\.A\. Condenação da CVM .*Período afetado: / : /^Empresa Cem S\.A\. CVM conviction .*Affected period: /);
    assert.equal(await p.locator(".linha-companhia .etiqueta-info").count(), 0, "nenhum caso da fixture termina antes de 2010");
    assert.doesNotMatch(linhas.join(" "), /alerta|alert|percentil|percentile|escore|score/i);
    // busca: concordância no singular
    await p.locator("form[role=search] input").fill("americanas");
    await p.locator("form[role=search] button[type=submit]").click();
    await p.locator(".resultados").waitFor();
    assert.match(await texto(p.locator(".resultados .rotulo")), pt ? /^1 empresa encontrada/ : /^1 company found/);
    await p.locator(".resultados a", { hasText: /AMERICANAS/ }).click();
    await p.waitForURL(/empresa/);
    await contexto.close();
  });

  test(`empresa: caminho, nome na data, histórico de nome, datas com rótulo e o nome de hoje só no fim (${idioma})`, async () => {
    const { p, contexto } = await pagina(idioma);
    await abrir(p, EMPRESA, "nav.datas");
    assert.deepEqual(await itensDoCaminho(p), pt ? ["Buscar", "AMERICANAS S.A."] : ["Search", "AMERICANAS S.A."]);
    assert.equal(await texto(p.locator("h1")), "AMERICANAS S.A.");
    assert.equal(await texto(p.locator(".linha-data")), pt ? "como era em 30/04/2022" : "as it was on 2022-04-30"); // a data inicial
    assert.match(
      await texto(p.locator(".historico-nome")),
      pt
        ? /^Antes de 2021, a companhia se chamava B2W - COMPANHIA DIGITAL; antes de 2013, B2W - COMPANHIA GLOBAL DO VAREJO\.$/
        : /^Before 2021, the company was called B2W - COMPANHIA DIGITAL/,
    );
    // o cartão da companhia logo abaixo do título, antes das datas; o caso do gabarito antes da lista de exercícios
    const antes = (a, b) => p.evaluate(([x, y]) => !!(document.querySelector(x).compareDocumentPosition(document.querySelector(y)) & 4), [a, b]);
    assert.match(await texto(p.locator(".cartao-companhia")), pt ? /^Código CVM 20990 · CNPJ / : /^CVM code 20990 · CNPJ /);
    assert.ok(await antes("h1", ".cartao-companhia"), "cartão da companhia depois do título");
    assert.ok(await antes(".cartao-companhia", "nav.datas"), "cartão da companhia antes das datas");
    assert.ok(await antes("nav.datas", ".cartao-caso"), "caso depois das datas");
    assert.ok(await antes(".cartao-caso", "#titulo-exercicios"), "caso antes da lista de exercícios");
    assert.match(await texto(p.locator(".cartao-caso")), pt ? /Fraude admitida Data pública: 11\/01\/2023 Período afetado: 2021( |$)/ : /Admitted fraud Public date: 2023-01-11 Affected period: 2021( |$)/);
    const datas = (await p.locator("a.data-botao").allInnerTexts()).map((d) => d.replace(/\s+/g, " ").trim());
    assert.deepEqual(datas, pt ? ["30/04/2022 período afetado do caso", "31/12/2024 depois da revelação"] : ["2022-04-30 case's affected period", "2024-12-31 after it came to light"]);
    assert.equal(await p.locator('a.data-botao[aria-current="true"]').count(), 1);
    assert.match(await texto(p.locator('a.data-botao[aria-current="true"]')), pt ? /30\/04\/2022/ : /2022-04-30/);
    assert.match(await texto(p.locator("main")), pt ? /Demonstração estática: só estas datas/ : /Static demo: only these dates/);
    // o nome de hoje aparece só na "Informação de hoje"
    const hoje = "AMERICANAS S.A. - EM RECUPERAÇÃO JUDICIAL";
    assert.ok((await texto(p.locator("#hoje"))).includes(hoje));
    const semHoje = await p.evaluate(() => {
      const copia = document.querySelector("main").cloneNode(true);
      copia.querySelector("#hoje").remove();
      return copia.textContent;
    });
    assert.ok(!semHoje.includes(hoje));
    await p.locator("a.data-botao").nth(1).click();
    await p.waitForURL(/data=2024-12-31/);
    await p.locator(".linha-data", { hasText: pt ? "31/12/2024" : "2024-12-31" }).waitFor();
    await p.locator(".linha-exercicio a").first().click();
    await p.waitForURL(/investigacao/);
    await p.locator("#mudancas").waitFor();
    await contexto.close();
  });

  test(`investigação: aviso, resumo, como ler e índice (${idioma})`, async () => {
    const { p, contexto } = await pagina(idioma);
    await abrir(p, INV_2024, ".cartao-caso");
    assert.deepEqual(
      await itensDoCaminho(p),
      pt ? ["Buscar", "AMERICANAS S.A. - em Recuperação Judicial", "Exercício 2021"] : ["Search", "AMERICANAS S.A. - em Recuperação Judicial", "Fiscal year 2021"],
    );
    assert.equal(await texto(p.locator(".linha-data")), pt ? "Exercício 2021 · como era em 31/12/2024" : "Fiscal year 2021 · as it was on 2024-12-31");
    // o aviso de diferenças logo abaixo do cabeçalho, com link para a seção
    const aviso = p.locator(".aviso-topo");
    assert.match(
      await texto(aviso),
      pt
        ? /^6 contas com diferença destacada no comparativo da DFP 2022, entregue em 16\/11\/2023\. /
        : /^6 accounts with a highlighted difference in the comparative of the 2022 DFP, filed on 2023-11-16\. /,
    );
    assert.equal(await aviso.evaluate((n) => n.previousElementSibling?.tagName), "HEADER");
    assert.equal(await aviso.locator("a").getAttribute("href"), "#mudancas");
    // resumo: quatro cartões
    const manip = await texto(p.locator(".resumo-manip"));
    assert.match(manip, pt ? /Em alerta/ : /Alert/);
    assert.match(manip, pt ? /Disparou: M-score de Beneish\. Abaixo do corte: Salto do prazo de pagamento/ : /Fired: Beneish M-score\. Below the cut-off:/);
    // risco e qualidade: rótulo pequeno em caixa alta (com "só contexto" uma vez só, sem selo), o número grande numa
    // linha própria e uma linha curta embaixo
    const linhasDe = async (sel) => (await p.locator(`${sel} > *`).allInnerTexts()).map((x) => x.replace(/\s+/g, " ").trim());
    assert.deepEqual(
      await linhasDe(".resumo-risco"),
      pt
        ? ["RISCO FINANCEIRO · SÓ CONTEXTO", "Z'' = 2,05", "Percentil 46 no setor (45 empresas). Sem zona de corte."]
        : ["FINANCIAL RISK · CONTEXT ONLY", "Z'' = 2.05", "Percentile 46 in the sector (45 companies). No cut-off zone."],
    );
    assert.deepEqual(
      await linhasDe(".resumo-qualidade"),
      pt
        ? ["QUALIDADE FINANCEIRA · SÓ CONTEXTO", "F = 5/9", "8 dos 9 sinais calculáveis. Mede força financeira, não qualidade do lucro."]
        : ["FINANCIAL QUALITY · CONTEXT ONLY", "F = 5/9", "8 of the 9 signals computable. Measures financial strength, not earnings quality."],
    );
    for (const sel of [".resumo-risco", ".resumo-qualidade"]) {
      assert.equal(await p.locator(`${sel} .selo`).count(), 0, `${sel}: sem selo repetindo "só contexto"`);
      assert.equal(await p.locator(`${sel} .rotulo-cartao`).evaluate((n) => getComputedStyle(n).textTransform), "uppercase");
      const [rotulo, numero] = await p.locator(`${sel} > *`).evaluateAll((ns) => ns.slice(0, 2).map((n) => parseFloat(getComputedStyle(n).fontSize)));
      assert.ok(numero > 1.8 * rotulo, `${sel}: número grande (${numero}px) e rótulo pequeno (${rotulo}px)`);
    }
    assert.match(
      await texto(p.locator(".cartao-caso")),
      pt
        ? /Fraude admitida Data pública: 11\/01\/2023 Período afetado: 2021 O exercício 2021 está dentro do período afetado\./
        : /Admitted fraud Public date: 2023-01-11 Affected period: 2021 Fiscal year 2021 is inside the affected period\./,
    );
    const fundoCaso = await p.locator(".cartao-caso").evaluate((n) => getComputedStyle(n).backgroundColor);
    const azulClaro = await p.locator(".faixa-demo").evaluate((n) => getComputedStyle(n).backgroundColor);
    assert.equal(fundoCaso, azulClaro, "caso do gabarito em fundo azul claro");
    assert.match(await texto(p.locator(".nao-somam")), pt ? /não se somam/ : /do not add up/);
    await p.locator("details.como-ler summary").click();
    assert.match(
      await texto(p.locator("details.como-ler")),
      pt
        ? /testadas de 2010 a 2023; alertaram 49,9% das empresas-ano não financeiras e acertaram 7 de 13 casos/
        : /tested from 2010 to 2023; they flagged 49\.9% of non-financial company-years and caught 7 of 13 cases/,
    );
    // índice "Nesta página" com as âncoras; o título não fica debaixo do aviso fixo
    const ancoras = await p.locator("nav.indice a").evaluateAll((as) => as.map((a) => a.getAttribute("href")));
    assert.deepEqual(ancoras, ["#resumo", "#manipulacao", "#risco", "#qualidade", "#parecer", "#mudancas", "#limites", "#hoje"]);
    for (const a of ancoras) assert.equal(await p.locator(a).count(), 1, a);
    await p.locator('nav.indice a[href="#qualidade"]').click();
    await p.waitForFunction(() => Math.abs(document.querySelector("#qualidade").getBoundingClientRect().top) < 200);
    const titulo = await p.locator("#titulo-qualidade").boundingBox();
    const fixo = await p.locator(".aviso").boundingBox();
    assert.ok(titulo.y >= fixo.y + fixo.height, `título escondido: ${titulo.y} < ${fixo.y + fixo.height}`);
    assert.match(await texto(p.locator("#manipulacao .subtitulo")), pt ? /É a única família que dispara alerta/ : /only family that triggers alerts/);
    assert.match(await texto(p.locator("#risco .subtitulo")), pt ? /não manipulação/ : /not manipulation/);
    await contexto.close();
  });

  test(`investigação: cartões, selos, M-score expandido, F, Z'' e ajuda (${idioma})`, async () => {
    const { p, contexto } = await pagina(idioma);
    await abrir(p, INV_2024, ".cartao-mscore");
    const m = p.locator(".cartao-mscore");
    assert.match(await texto(m), pt ? /O que mede.*Por que pode indicar manipulação/ : /What it measures.*Why it may indicate manipulation/);
    assert.match(await texto(m.locator(".valor-grande")), /^−0[,.]240/);
    assert.match(await texto(m.locator(".regra")), pt ? /Regra do estudo 1: M > −1,78/ : /Study 1 rule: M > −1\.78/);
    assert.ok(await m.locator("details.detalhes").evaluate((d) => d.open), "M-score abre expandido no computador");
    assert.ok(await m.locator(".quadro").isVisible(), "explicação alternativa num quadro");
    assert.equal(await m.locator(".grade-componentes > li.componente").count(), 8);
    assert.match(await texto(m.locator(".componentes h4")), pt ? /não têm regra própria; entram juntos no M-score/ : /no rule of their own/);
    assert.match(await texto(m.locator("li.componente").first()), pt ? /^DSRI, índice de dias de recebimento .*Recebíveis em relação às vendas/ : /^DSRI.*Receivables relative to sales/);
    assert.equal(await m.locator("li.componente .barra-percentil").count(), 8);
    // selos: "Sem alerta" em cinza neutro (nunca verde) e "Só contexto"
    const sem = p.locator(".cartao-sinal .selo-sem_alerta").first();
    assert.equal(await texto(sem), pt ? "Sem alerta" : "No alert");
    const [r, g, b] = (await sem.evaluate((n) => getComputedStyle(n).backgroundColor)).match(/\d+/g).map(Number);
    assert.ok(Math.max(r, g, b) - Math.min(r, g, b) < 16, `"sem alerta" não é cinza: ${r},${g},${b}`);
    assert.ok((await p.locator(".cartao-sinal .selo-contexto").count()) >= 3);
    // os outros cartões ficam fechados, com "Ver detalhes"
    const dpo = p.locator("#manipulacao .grade .cartao-sinal").first();
    assert.equal(await dpo.locator("details.detalhes").evaluate((d) => d.open), false);
    // F: os nove sinais com rótulos e resultado em texto
    const f = await texto(p.locator("#qualidade .cartao-sinal"));
    const sinaisF = pt
      ? ["Lucro sobre o ativo (ROA) sim", "Caixa operacional sobre o ativo (CFO) não", "Sem emissão de ações (EQ_OFFER) não calculável"]
      : ["Return on assets (ROA) yes", "Operating cash flow on assets (CFO) no", "No equity issuance (EQ_OFFER) not computable"];
    for (const x of sinaisF) assert.ok(f.includes(x), `F: falta ${x}`);
    assert.match(f, pt ? /"sim" soma 1 ponto ao F/ : /"yes" adds 1 point to F/);
    // Z'': componentes com nomes legíveis
    assert.match(await texto(p.locator("#risco .cartao-sinal")), pt ? /X1 capital de giro \/ ativo/ : /X1 working capital \/ assets/);
    // ajuda: o "?" da regra do M-score abre o verbete do glossário e fecha com Esc
    const ajuda = m.locator(".regra .ajuda-btn");
    assert.equal(await ajuda.getAttribute("aria-label"), pt ? "Ajuda sobre Regra do estudo 1" : "Help on Study 1 rule");
    await ajuda.click();
    assert.match(
      await texto(m.locator(".regra .ajuda-caixa")),
      pt ? /Vem do artigo de Beneish \(1999\), estimado nos EUA, e nunca foi recalibrado para o Brasil/ : /Beneish \(1999\), estimated in the US, and was never recalibrated for Brazil/,
    );
    await p.keyboard.press("Escape");
    assert.equal(await m.locator(".regra .ajuda-caixa").count(), 0);
    await contexto.close();
  });

  for (const tema of ["light", "dark"]) {
    test(`âmbar só no selo "Em alerta"; a etiqueta da faixa em azul claro (${idioma}, ${tema})`, async () => {
      const { p, contexto } = await pagina(idioma, COMPUTADOR, tema);
      await abrir(p, INV_2024, ".cartao-mscore");
      await abrirTudo(p);
      const alerta = p.locator(".selo-alerta").first();
      const ambar = await alerta.evaluate((n) => [getComputedStyle(n).backgroundColor, getComputedStyle(n).color]);
      const contextoCor = await p.locator(".selo-contexto").first().evaluate((n) => [getComputedStyle(n).backgroundColor, getComputedStyle(n).color]);
      // "Acima da faixa da própria empresa": azul claro, como "Só contexto"
      const faixa = p.locator(".etiqueta-faixa");
      assert.ok((await faixa.count()) > 0, "a investigação de teste tem a etiqueta da faixa");
      assert.deepEqual(await faixa.first().evaluate((n) => [getComputedStyle(n).backgroundColor, getComputedStyle(n).color]), contextoCor);
      // nenhum elemento fora do selo de alerta tem o fundo, a letra ou a borda em âmbar, em nenhuma tela
      for (const [caminho, esperar] of [[INV_2024, ".cartao-mscore"], ["/", ".linha-companhia"], [EMPRESA, "nav.datas"]]) {
        if (caminho !== INV_2024) {
          await abrir(p, caminho, esperar);
          await abrirTudo(p);
        }
        const fora = await p.evaluate(([fundo, letra]) => {
          const out = [];
          for (const n of document.querySelectorAll("body *")) {
            const c = getComputedStyle(n);
            const usa = c.backgroundColor === fundo || c.color === letra || c.borderTopColor === letra || c.borderTopColor === fundo;
            if (usa && !n.closest(".selo-alerta")) out.push(`${n.tagName.toLowerCase()}.${[...n.classList].join(".")}`);
          }
          return out;
        }, ambar);
        assert.deepEqual(fora, [], `${caminho}: âmbar fora do selo de alerta`);
      }
      await contexto.close();
    });
  }

  test(`investigação na época: sem DFP seguinte, o link para o que se soube depois (${idioma})`, async () => {
    const { p, contexto } = await pagina(idioma);
    await abrir(p, INV_2022, "#mudancas");
    assert.equal(await p.locator(".aviso-topo").count(), 0);
    assert.match(await texto(p.locator("#mudancas")), pt ? /a DFP de 2022 ainda não tinha sido entregue/ : /the 2022 DFP had not been filed yet/);
    await p.locator("#mudancas a", { hasText: pt ? "Ver a mesma investigação em 31/12/2024" : "See the same investigation on 2024-12-31" }).click();
    await p.waitForURL(/data=2024-12-31/);
    await p.locator(".aviso-topo").waitFor();
    await contexto.close();
  });

  test(`faixa de Tukey com a unidade uma vez só (${idioma})`, async () => {
    const { p, contexto } = await pagina(idioma);
    await abrir(p, INV_2024, "#mudancas");
    const t = await textoDaTela(p);
    const faixa = pt
      ? /faixa de Tukey \(1,5 × IQR\): de (\S+) a (\S+) \(([^)]+)\); valor/g
      : /Tukey range \(1\.5 × IQR\): from (\S+) to (\S+) \(([^)]+)\); value/g;
    const achadas = [...t.matchAll(faixa)];
    assert.ok(achadas.length > 0, "nenhuma faixa de Tukey na tela");
    const numero = pt ? /^−?\d{1,3}(\.\d{3})*(,\d+)?$/ : /^−?\d{1,3}(,\d{3})*(\.\d+)?$/;
    for (const [frase, a, b, unidade] of achadas) {
      assert.match(a, numero, frase);
      assert.match(b, numero, frase);
      assert.ok(unidade.length > 0 && frase.split(unidade).length === 2, `unidade repetida: ${frase}`);
    }
    await contexto.close();
  });

  test(`caminhos do repositório viram links para arquivos que existem (${idioma})`, async () => {
    const { p, contexto } = await pagina(idioma);
    await abrir(p, INV_2024, "#mudancas");
    await abrirTudo(p);
    const caminho = pt ? "docs/resultados.md" : "docs/en/results.md";
    const link = p.locator("a", { hasText: new RegExp(`^${caminho.replace(/[./]/g, "\\$&")}$`) }).first();
    assert.equal(await link.getAttribute("href"), REPOSITORIO + caminho);
    const alvos = await p.locator(`a[href^="${REPOSITORIO}"]`).evaluateAll((as) => as.map((a) => a.getAttribute("href")));
    assert.ok(alvos.length > 0);
    for (const alvo of alvos) assert.ok(existsSync(join(RAIZ, alvo.slice(REPOSITORIO.length))), `link quebrado: ${alvo}`);
    await contexto.close();
  });

  test(`"Como o motor foi testado" explica o estudo (${idioma})`, async () => {
    const { p, contexto } = await pagina(idioma);
    await abrir(p, TESTADO, "table");
    const regras = await p.locator("table").first().locator("tbody tr").allInnerTexts();
    assert.equal(regras.length, 4);
    assert.match(regras[0].replace(/\s+/g, " "), pt ? /M-score de Beneish.*não financeiras.*M > −1,78/ : /Beneish M-score.*non-financial.*M > −1\.78/);
    const main = await texto(p.locator("main"));
    assert.match(main, pt ? /Exercícios de 2010 a 2023/ : /Fiscal years 2010 to 2023/);
    assert.match(main, pt ? /7 de 13 casos acertáveis/ : /7 of 13/);
    assert.ok(await p.locator('main a[href$="docs/pre-registro.md"]').count());
    assert.ok(await p.locator('main a[href$="ficha-do-motor.md"], main a[href$="engine-card.md"]').count());
    await contexto.close();
  });

  test(`menu do celular e o layout no celular (${idioma})`, async () => {
    const { p, contexto } = await pagina(idioma, CELULAR);
    await abrir(p, INV_2024, ".cartao-mscore");
    assert.equal(await p.locator("nav.nav-principal").isVisible(), false);
    const botao = p.locator("button.menu-btn");
    await botao.click();
    const menu = p.locator("#menu-celular");
    assert.equal(await menu.getAttribute("role"), "dialog");
    assert.match(await menu.evaluate((n) => getComputedStyle(n).backgroundColor), /^rgb\(/, "fundo sólido");
    const caixa = await menu.boundingBox();
    assert.ok(caixa.x <= 0 && caixa.y <= 0 && caixa.width >= 390 && caixa.height >= 844, JSON.stringify(caixa));
    const itens = (await menu.locator(".menu-celular-itens a").allInnerTexts()).map((x) => x.replace(" ↗", "").trim());
    assert.deepEqual(itens, pt ? ["Buscar", "Como o motor foi testado", "Ficha do motor"] : ["Search", "How the engine was tested", "Engine card"]);
    assert.match(await texto(menu.locator(".aviso-menu")), pt ? /Não é acusação/ : /Not an accusation/);
    // idioma e tema como seletores lado a lado, com aria-pressed
    const portugues = menu.getByRole("button", { name: "Português" });
    const english = menu.getByRole("button", { name: "English" });
    assert.equal(await portugues.getAttribute("aria-pressed"), String(pt));
    await (pt ? english : portugues).click();
    assert.equal(await (pt ? english : portugues).getAttribute("aria-pressed"), "true");
    await (pt ? portugues : english).click(); // volta à língua do teste
    const escuro = menu.getByRole("button", { name: pt ? "Escuro" : "Dark", exact: true });
    await escuro.click();
    assert.equal(await escuro.getAttribute("aria-pressed"), "true");
    assert.equal(await p.evaluate(() => document.documentElement.dataset.theme), "dark");
    await menu.getByRole("button", { name: pt ? "Claro" : "Light", exact: true }).click();
    // tocar fora dos itens fecha; Esc fecha; navegar fecha
    await p.mouse.click(195, 620);
    assert.equal(await menu.count(), 0);
    await botao.click();
    await p.keyboard.press("Escape");
    assert.equal(await p.locator("#menu-celular").count(), 0);
    await botao.click();
    await p.locator("#menu-celular .menu-celular-itens a").nth(1).click();
    await p.waitForURL(/como-o-motor-foi-testado/);
    assert.equal(await p.locator("#menu-celular").count(), 0);
    assert.equal(await p.evaluate(() => document.documentElement.classList.contains("menu-aberto")), false);
    // datas em fila com rolagem, resumo com manipulação na largura toda, cartões fechados e índice em fila
    await abrir(p, INV_2024, ".cartao-mscore");
    assert.equal(await p.locator("nav.datas").evaluate((n) => getComputedStyle(n).overflowX), "auto");
    const manip = await p.locator(".resumo-manip").boundingBox();
    const risco = await p.locator(".resumo-risco").boundingBox();
    const qualidade = await p.locator(".resumo-qualidade").boundingBox();
    const caso = await p.locator(".cartao-caso").boundingBox();
    assert.ok(manip.width > 300 && Math.abs(risco.y - qualidade.y) < 2 && risco.x < qualidade.x, "risco e qualidade lado a lado");
    assert.ok(caso.y > risco.y && caso.width > 300, "o caso embaixo, na largura toda");
    assert.equal(await p.locator(".cartao-mscore details.detalhes").evaluate((d) => d.open), false);
    assert.equal(await p.locator("nav.indice ul").evaluate((n) => getComputedStyle(n).flexDirection), "row");
    // aviso no celular: a linha curta fixa, numa linha só, com "Saiba mais" levando ao texto completo no rodapé
    assert.equal(await p.locator(".aviso .aviso-longo").isVisible(), false);
    assert.equal(
      await texto(p.locator(".aviso .aviso-curto")),
      pt ? "Sinal estatístico. Não é acusação nem recomendação. Saiba mais" : "Statistical signal. Not an accusation or advice. Learn more",
    );
    const fixo = await p.locator(".aviso").boundingBox();
    assert.ok(fixo.height < 32, `aviso do celular em mais de uma linha: ${fixo.height}`);
    // nenhum título fica debaixo do aviso fixo: cada âncora do índice
    const ancoras = await p.locator("nav.indice a").evaluateAll((as) => as.map((a) => a.getAttribute("href")));
    assert.ok(ancoras.length >= 8);
    for (const a of ancoras) {
      await p.locator(`nav.indice a[href="${a}"]`).click();
      await p.waitForFunction((x) => Math.abs(document.querySelector(x).getBoundingClientRect().top) < 300, a);
      await p.waitForTimeout(150);
      const titulo = await p.locator(`${a} h2`).first().boundingBox();
      const aviso = await p.locator(".aviso").boundingBox();
      assert.ok(titulo.y >= aviso.y + aviso.height, `${a}: título escondido (${titulo.y} < ${aviso.y + aviso.height})`);
      await p.evaluate(() => window.scrollTo(0, 0));
    }
    await p.locator(".aviso .aviso-curto a").click();
    await p.waitForURL(/#aviso-completo$/);
    const completo = await p.locator("#aviso-completo").boundingBox();
    const aviso = await p.locator(".aviso").boundingBox();
    assert.ok(completo.y >= aviso.y + aviso.height && completo.y < 844, "o texto completo aparece, sem ficar debaixo do aviso");
    assert.match(await texto(p.locator("#aviso-completo")), pt ? /Não é acusação, não é recomendação de investimento\./ : /Not an accusation, not investment advice\./);
    await contexto.close();
  });

  for (const tema of ["light", "dark"]) {
    test(`acessibilidade: axe sem violação séria ou crítica (${idioma}, ${tema})`, async () => {
      const telas = [
        ["/", ".linha-companhia", COMPUTADOR],
        [EMPRESA, "nav.datas", COMPUTADOR],
        [INV_2024, ".cartao-mscore", COMPUTADOR],
        [INV_2022, ".cartao-mscore", COMPUTADOR],
        [TESTADO, "table", COMPUTADOR],
        [INV_2024, ".cartao-mscore", CELULAR],
      ];
      const problemas = [];
      for (const [caminho, esperar, aparelho] of telas) {
        const { p, contexto } = await pagina(idioma, aparelho, tema);
        const onde = `${caminho} ${aparelho === CELULAR ? "celular" : "computador"}`;
        await abrir(p, caminho, esperar);
        problemas.push(...(await violacoesSerias(p, `${onde} fechado`)));
        await abrirTudo(p);
        problemas.push(...(await violacoesSerias(p, `${onde} aberto`)));
        if (aparelho === CELULAR) {
          await p.evaluate(() => window.scrollTo(0, 0));
          await p.locator("button.menu-btn").click();
          await p.locator("#menu-celular").waitFor();
          problemas.push(...(await violacoesSerias(p, "menu do celular")));
        }
        await contexto.close();
      }
      assert.deepEqual(problemas, []);
    });
  }
}
