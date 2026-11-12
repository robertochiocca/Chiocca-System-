// Trechos da seção "Trechos dos documentos" (Fase F1) agrupados para mostrar, do mesmo jeito que o PDF
// (chiocca/v2/leitura_exibicao.py, função agrupa). Só exibição: o JSON continua com um item por trecho.
// - o mesmo texto da mesma página (e a mesma marca de menção negativa) aparece uma vez, com os rótulos juntos;
// - os omitidos da mesma página viram uma entrada só, com n = quantos itens omitidos o JSON tem nessa página (um trecho
//   omitido com dois rótulos é um item por rótulo: o texto omitido não fica no JSON).

/** @param {Array<{omitido: boolean, pagina: number|null, texto: string|null, negacao?: boolean|null, cortado?: boolean, rotulo?: string|null}>} trechos */
export function agrupaTrechos(trechos) {
  const out = [];
  const onde = new Map();
  for (const x of trechos) {
    const chave = x.omitido ? JSON.stringify(["omitido", x.pagina]) : JSON.stringify(["texto", x.texto, x.pagina, x.negacao ?? null]);
    const k = onde.get(chave);
    if (k !== undefined) {
      const g = out[k];
      g.n += 1;
      if (x.rotulo && !g.rotulos.includes(x.rotulo)) g.rotulos.push(x.rotulo);
      g.cortado = g.cortado || Boolean(x.cortado);
      continue;
    }
    onde.set(chave, out.length);
    out.push({ omitido: x.omitido, pagina: x.pagina, texto: x.texto, negacao: x.negacao ?? null, cortado: Boolean(x.cortado),
      rotulos: x.rotulo ? [x.rotulo] : [], n: 1 });
  }
  return out;
}

/** Texto de motivo como frase: inicial maiúscula e ponto no fim (como frase() no PDF). */
export function frase(x) {
  const s = (x ?? "").trim();
  if (!s) return s;
  return s[0].toUpperCase() + s.slice(1) + (/[.!?]$/.test(s) ? "" : ".");
}

/** Junta frase e ponto final sem ponto duplo quando o nome já termina em ponto ("AMERICANAS S.A."). */
export function comPonto(x) {
  return x.endsWith(".") ? x : `${x}.`;
}
