// Funções do teste de tela e da varredura da demonstração: o texto que a tela mostra e os códigos internos nele.

/** Abre tudo o que a tela esconde atrás de um clique: os <details> e os botões de evidências. */
export async function abrirTudo(p) {
  await p.evaluate(() => {
    document.querySelectorAll("details").forEach((d) => (d.open = true));
    document.querySelectorAll("main button[aria-expanded='false']").forEach((b) => b.click());
  });
  await p.waitForFunction(() => !document.querySelector("main button[aria-expanded='false']"));
}

/** Texto da tela fora de links e de trechos em fonte de código (.mono), com tudo aberto. */
export async function textoDaTela(p) {
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

export function codigosInternos(texto) {
  const achados = [...texto.matchAll(CODIGO)]
    .map((m) => m[0])
    .filter((c) => !/\.[a-z]{2,7}$/.test(c) && !NOTACAO_DOS_ARTIGOS.has(c));
  // o defeito relatado: "dados_abertos · con" no lugar dos rótulos
  for (const m of texto.matchAll(/·\s*(con|ind)\b/g)) achados.push(m[0]);
  // valor que não virou texto
  for (const m of texto.matchAll(/\b(NaN|undefined)\b|\[object \w+\]/g)) achados.push(m[0]);
  return [...new Set(achados)];
}
