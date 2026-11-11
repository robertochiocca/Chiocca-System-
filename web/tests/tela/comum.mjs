// Funções do teste de tela e da varredura da demonstração: o texto que a tela mostra e os códigos internos nele.

/** Abre tudo o que a tela esconde atrás de um clique: os <details> e os botões de evidências. */
export async function abrirTudo(p) {
  await p.evaluate(() => {
    document.querySelectorAll("details").forEach((d) => (d.open = true));
    document.querySelectorAll("main button[aria-expanded='false']").forEach((b) => b.click());
  });
  await p.waitForFunction(() => !document.querySelector("main button[aria-expanded='false']"));
}

/** Texto da tela fora de links, de trechos em fonte de código (.mono) e dos trechos copiados dos documentos (Fase F1:
 * dado literal, em português, fica como veio), com tudo aberto. */
export async function textoDaTela(p) {
  await abrirTudo(p);
  return p.evaluate(() => {
    const copia = document.body.cloneNode(true);
    copia.querySelectorAll("a, .mono, script, style, template, svg, blockquote[lang='pt'], td[lang='pt']").forEach((n) => n.remove());
    copia.querySelectorAll("*").forEach((n) => n.append(" ")); // separa o texto de elementos vizinhos
    return copia.textContent.replace(/\s+/g, " ");
  });
}

// Código interno: identificador com sublinhado (dados_abertos, lucro_sem_caixa, nao_aplicavel, DFC_MI...). Fica de fora
// o nome de arquivo de fonte pública (cad_cia_aberta.csv). Sigla do artigo só vale no formato combinado em 10/11/2026:
// entre parênteses, logo depois do nome legível, como nos índices do M-score ("Sem emissão de ações (EQ_OFFER)");
// sozinha ("EQ_OFFER pela DFC"), conta como código.
const CODIGO = /[A-Za-z][A-Za-z0-9]*(?:_[A-Za-z0-9]+)+(?:\.[a-z]{2,7}\b)?/g;
const SIGLA_DEPOIS_DO_NOME = /(?<=[a-zà-ü] )\(Δ?[A-Z][A-Z0-9]*(?:_[A-Z0-9]+)*\)/g;

export function codigosInternos(texto) {
  const semSiglas = texto.replace(SIGLA_DEPOIS_DO_NOME, "");
  const achados = [...semSiglas.matchAll(CODIGO)].map((m) => m[0]).filter((c) => !/\.[a-z]{2,7}$/.test(c));
  // o defeito relatado: "dados_abertos · con" no lugar dos rótulos
  for (const m of texto.matchAll(/·\s*(con|ind)\b/g)) achados.push(m[0]);
  // valor que não virou texto
  for (const m of texto.matchAll(/\b(NaN|undefined)\b|\[object \w+\]/g)) achados.push(m[0]);
  return [...new Set(achados)];
}

// Número negativo com hífen no lugar do sinal de menos (−): hífen no começo, depois de espaço, parêntese ou sinal de
// comparação, antes de um algarismo. Datas (2024-12-31) e intervalos (2010-2023) não entram.
const HIFEN_COMO_SINAL = /(?<![\w.,\-\u2212/])-(?=\d)/g;

export function hifensComoSinal(texto) {
  return [...texto.matchAll(HIFEN_COMO_SINAL)].map((m) => texto.slice(Math.max(0, m.index - 25), m.index + 8));
}
