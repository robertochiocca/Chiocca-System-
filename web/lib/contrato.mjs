// Conferência das respostas da API contra o contrato (docs/contratos.md, seções 2 e 6), do lado da interface.
// A mesma função roda nos testes (node --test) sobre os exemplos guardados e sobre as respostas da API geradas
// pelos testes do Python (tests/contrato/). Devolve a lista de problemas; lista vazia quer dizer contrato ok.

const AVISO = {
  pt: "Sinal estatístico baseado em demonstrações públicas. Não é acusação, não é recomendação de investimento.",
  en: "Statistical signal based on public financial statements. Not an accusation, not investment advice.",
};
export { AVISO };

const FAMILIAS = ["possivel_manipulacao", "risco_financeiro", "qualidade_financeira"];
const CHAVES_DISTRIBUICAO = new Set(["n", "quantis", "limites", "contagens", "abaixo", "acima", "motivo"]);

function tem(obj, chaves, onde, problemas) {
  if (obj === null || typeof obj !== "object") {
    problemas.push(`${onde}: não é objeto`);
    return false;
  }
  for (const c of chaves) if (!(c in obj)) problemas.push(`${onde}: falta ${c}`);
  return true;
}

function avisoOk(aviso, problemas, onde) {
  if (typeof aviso === "string") {
    if (aviso !== AVISO.pt && aviso !== AVISO.en) problemas.push(`${onde}: aviso fixo diferente`);
  } else if (!aviso || aviso.pt !== AVISO.pt || aviso.en !== AVISO.en) {
    problemas.push(`${onde}: aviso fixo diferente`);
  }
}

/** Distribuição do setor: só agregados (quantis e histograma), nunca nomes ou valores de outras empresas. */
export function validaDistribuicao(d, onde = "distribuicao") {
  const problemas = [];
  if (d === null || d === undefined) return problemas;
  for (const k of Object.keys(d)) if (!CHAVES_DISTRIBUICAO.has(k)) problemas.push(`${onde}: campo não agregado ${k}`);
  if (d.motivo === null) {
    if (!Array.isArray(d.limites) || !Array.isArray(d.contagens) || d.limites.length !== d.contagens.length + 1)
      problemas.push(`${onde}: histograma inconsistente`);
    if (typeof d.n !== "number" || d.n < 10) problemas.push(`${onde}: n abaixo do mínimo`);
  }
  return problemas;
}

export function validaInvestigacao(inv) {
  const problemas = [];
  if (!tem(inv, ["empresa", "data_referencia", "idioma", "exercicios", "achados", "mudancas", "parecer_e_auditor",
    "limites", "limitacoes", "evidencias", "informacao_de_hoje", "aviso"], "investigacao", problemas)) return problemas;
  if (!["pt", "en"].includes(inv.idioma)) problemas.push("idioma inválido");
  if (inv.aviso !== AVISO[inv.idioma]) problemas.push("aviso fixo diferente");
  if ("situacao_cadastro_atual" in inv.empresa) problemas.push("informação de hoje dentro do bloco da empresa");
  tem(inv.empresa, ["cd_cvm", "denominacao", "codigos_negociacao", "setor", "grupo"], "empresa", problemas);
  for (const e of inv.exercicios) if (e.exercicio > 2023) problemas.push("exercício acima do lacre");
  if (inv.data_referencia < "2011-04-30" || inv.data_referencia > "2024-12-31") problemas.push("data fora do intervalo");
  for (const f of Object.keys(inv.achados)) if (!FAMILIAS.includes(f)) problemas.push(`família desconhecida ${f}`);
  for (const lista of Object.values(inv.achados)) {
    for (const a of lista) {
      tem(a, ["sinal", "rotulo", "valor", "unidade", "regra", "alerta_v1", "linhagem"], `achado ${a.sinal}`, problemas);
      if (a.familia !== "possivel_manipulacao" && a.alerta_v1 !== null) problemas.push(`contexto com alerta: ${a.sinal}`);
      problemas.push(...validaDistribuicao(a.contexto?.distribuicao_setor_ano, `distribuicao ${a.sinal}`));
    }
  }
  tem(inv.informacao_de_hoje, ["titulo", "situacao_cadastro", "fonte"], "informacao_de_hoje", problemas);
  tem(inv.mudancas, ["comparativo_destacadas", "reapresentacao_pelo_comparativo"], "mudancas", problemas);
  return problemas;
}

/** Busca: só nome, código CVM ou CNPJ, em ordem alfabética, sem nenhum sinal no resultado. */
export function validaBusca(b) {
  const problemas = [];
  if (!tem(b, ["busca", "criterio", "ordem", "total", "resultados", "data_referencia", "aviso"], "busca", problemas))
    return problemas;
  if (!["nome", "cd_cvm", "cnpj"].includes(b.criterio)) problemas.push("critério de busca não permitido");
  if (b.ordem !== "denominacao") problemas.push("ordem diferente da alfabética");
  const permitidas = new Set(["cd_cvm", "cnpj", "denominacao", "origem_denominacao", "codigos_negociacao",
    "motivo_codigos_negociacao"]);
  for (const r of b.resultados) for (const k of Object.keys(r)) if (!permitidas.has(k)) problemas.push(`campo ${k} no resultado`);
  avisoOk(b.aviso, problemas, "busca");
  return problemas;
}

export function validaEmpresa(e) {
  const problemas = [];
  if (!tem(e, ["empresa", "exercicios", "informacao_de_hoje", "data_referencia", "aviso"], "empresa", problemas))
    return problemas;
  if ("situacao_cadastro_atual" in e.empresa) problemas.push("informação de hoje dentro do bloco da empresa");
  if (e.exercicios.some((x) => x > 2023)) problemas.push("exercício acima do lacre");
  avisoOk(e.aviso, problemas, "empresa");
  return problemas;
}

export function validaComoTestado(c) {
  const problemas = [];
  if (!tem(c, ["acerto", "alarmes_por_acerto_nf", "taxa_de_alerta", "acaso", "antecedencia", "documentos", "aviso"],
    "como_testado", problemas)) return problemas;
  tem(c.acerto, ["acertados", "acertaveis", "casos_no_gabarito"], "acerto", problemas);
  tem(c.antecedencia, ["casos", "mediana_meses", "minimo_meses", "maximo_meses"], "antecedencia", problemas);
  if (!Array.isArray(c.regras) || c.regras.length !== 4) problemas.push("como_testado: as quatro regras do estudo 1");
  avisoOk(c.aviso, problemas, "como_testado");
  return problemas;
}

/** Normaliza para a ordem alfabética (como chiocca/v2/busca.py): sem acento, minúsculas, espaços simples. */
function chaveAlfabetica(s) {
  return String(s ?? "").normalize("NFKD").replace(/[\u0300-\u036f]/g, "").replace(/\s+/g, " ").trim().toLowerCase();
}

const PROIBIDAS_NA_DEMONSTRACAO = /alerta|percentil|escore|score|achado|sinal/i;

/** Demonstração: companhias em ordem alfabética, com o caso do gabarito e as datas; nunca resultado de sinal. */
export function validaDemonstracao(d) {
  const problemas = [];
  if (!tem(d, ["ordem", "empresas", "destaques", "aviso"], "demonstracao", problemas)) return problemas;
  if (d.ordem !== "denominacao") problemas.push("demonstracao: ordem diferente da alfabética");
  const chaves = d.empresas.map((e) => `${chaveAlfabetica(e.denominacao)}\u0000${e.cd_cvm}`);
  if (chaves.some((c, i) => i > 0 && c < chaves[i - 1])) problemas.push("demonstracao: lista fora da ordem alfabética");
  const visitar = (x, onde) => {
    if (x && typeof x === "object")
      for (const [k, v] of Object.entries(x)) {
        if (PROIBIDAS_NA_DEMONSTRACAO.test(k)) problemas.push(`demonstracao: campo de sinal ${onde}.${k}`);
        visitar(v, `${onde}.${k}`);
      }
  };
  visitar(d.empresas, "empresas");
  for (const e of d.empresas) {
    tem(e, ["cd_cvm", "denominacao", "datas", "rotulos_datas", "data_inicial", "casos", "nomes"], `empresa ${e.cd_cvm}`, problemas);
    if (!(e.data_inicial in e.datas)) problemas.push(`empresa ${e.cd_cvm}: data inicial fora das datas`);
    for (const exs of Object.values(e.datas)) if (exs.some((x) => x > 2023)) problemas.push("exercício acima do lacre");
  }
  avisoOk(d.aviso, problemas, "demonstracao");
  return problemas;
}

export function validaSaude(s) {
  const problemas = [];
  tem(s, ["status", "ultimo_exercicio_liberado", "data_referencia_minima", "data_referencia_maxima",
    "modo_demonstracao", "aviso"], "saude", problemas);
  avisoOk(s?.aviso, problemas, "saude");
  return problemas;
}

export function validaErro(e) {
  const problemas = [];
  tem(e, ["erro", "motivo", "aviso"], "erro", problemas);
  return problemas;
}
