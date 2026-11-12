// Lista do IPE na tela (Fase F2a), como no PDF (chiocca/v2/pdf_investigacao.py, linhas_ipe): os itens do mesmo grupo
// (versões do mesmo documento e documentos com a mesma data, categoria e assunto original, agrupados pelo Python na
// geração) viram uma linha só, na posição do primeiro (o mais recente), com o assunto dele e um link por documento.
// O JSON continua com um item por versão de cada documento.

/** Os grupos na ordem da lista: cada um, os itens dele na ordem do JSON. */
export function linhasIPE(itens) {
  const ordem = [];
  const por = new Map();
  for (const x of itens) {
    if (!por.has(x.grupo)) {
      por.set(x.grupo, []);
      ordem.push(x.grupo);
    }
    por.get(x.grupo).push(x);
  }
  return ordem.map((g) => por.get(g));
}

/** Os links de uma linha em ordem de entrega ("ver na CVM: 1, 2"): a ordem do JSON (da mais recente para a mais
 * antiga) ao contrário; a tela não reordena listas. */
export function linksDaLinha(itens) {
  return [...itens].reverse();
}

function versoes(itens) {
  const vs = [];
  for (const x of linksDaLinha(itens)) if (x.versao != null && !vs.includes(x.versao)) vs.push(x.versao);
  return vs;
}

/** A marca da linha: "versão 2"; "versões 1 e 2"; ou "3 documentos" (com as versões, se houver mais de uma). */
export function marcaDaLinha(itens, t) {
  const vs = versoes(itens);
  const lista = vs.length <= 1 ? String(vs[0] ?? "") : `${vs.slice(0, -1).join(", ")}${t.ipe_e}${vs[vs.length - 1]}`;
  if (itens.length === 1) return (itens[0].versao ?? 1) > 1 ? t.ipe_versao.replace("{v}", String(itens[0].versao)) : null;
  if (vs.length === itens.length) return t.ipe_versoes.replace("{v}", lista);
  const docs = t.ipe_documentos.replace("{n}", String(itens.length));
  return vs.length > 1 ? `${docs}, ${t.ipe_versoes.replace("{v}", lista)}` : docs;
}
