// Servidor estático mínimo para o teste de tela: serve o site exportado (out/) com os dados de teste da
// demonstração estática, montados a partir dos exemplos versionados (docs/exemplos/) e da resposta da API guardada
// em tests/contrato/. Não há API nem rede.
import { createServer } from "node:http";
import { cpSync, existsSync, mkdirSync, mkdtempSync, readFileSync, rmSync, statSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { dirname, extname, join } from "node:path";
import { fileURLToPath } from "node:url";

const web = join(dirname(fileURLToPath(import.meta.url)), "..", "..");
const exemplos = join(web, "..", "docs", "exemplos");
const TIPOS = { ".html": "text/html; charset=utf-8", ".js": "text/javascript", ".css": "text/css", ".json": "application/json",
  ".pdf": "application/pdf", ".svg": "image/svg+xml", ".txt": "text/plain" };

function grava(raiz, caminho, conteudo) {
  const alvo = join(raiz, "demo", caminho);
  mkdirSync(dirname(alvo), { recursive: true });
  writeFileSync(alvo, typeof conteudo === "string" ? conteudo : JSON.stringify(conteudo, null, 1));
}

/** CSV simples (RFC 4180: campos entre aspas podem ter vírgulas, quebras de linha e aspas dobradas). */
function lerCsv(texto) {
  const linhas = [];
  let linha = [], campo = "", aspas = false;
  for (let i = 0; i < texto.length; i++) {
    const c = texto[i];
    if (aspas) {
      if (c === '"' && texto[i + 1] === '"') (campo += '"'), i++;
      else if (c === '"') aspas = false;
      else campo += c;
    } else if (c === '"') aspas = true;
    else if (c === ",") linha.push(campo), (campo = "");
    else if (c === "\n") linha.push(campo), linhas.push(linha), (linha = []), (campo = "");
    else if (c !== "\r") campo += c;
  }
  if (campo || linha.length) linha.push(campo), linhas.push(linha);
  const [cab, ...resto] = linhas;
  return resto.map((l) => Object.fromEntries(cab.map((k, n) => [k, l[n] ?? ""])));
}

/** O caso da Americanas no gabarito versionado (data/gabarito_casos.csv), no formato da rota da demonstração. */
function casoDaAmericanas() {
  const g = lerCsv(readFileSync(join(web, "..", "data", "gabarito_casos.csv"), "utf-8")).find((x) => x.caso_id === "americanas");
  return {
    caso_id: g.caso_id,
    tipo_evento: g.tipo_evento.split(";").filter(Boolean),
    data_publica: g.data_publica || null,
    periodo_afetado: g.periodo_afetado_inicio ? [Number(g.periodo_afetado_inicio), Number(g.periodo_afetado_fim)] : null,
    fonte: g.fonte_principal_url || null,
  };
}

/** Monta os dados de teste: Americanas, exercício 2021, em 30/04/2022 e em 31/12/2024 (os exemplos guardados), e a
 * companhia da fixture (as respostas da API guardadas em tests/contrato/, só em PT). O índice segue o formato da rota
 * /api/v1/demonstracao, com os destaques que o Python tirou dos mesmos exemplos. */
export function montarDados(raiz) {
  rmSync(join(raiz, "demo"), { recursive: true, force: true });
  const datas = ["2022-04-30", "2024-12-31"];
  const nomes = new Set();
  let ultima = null;
  for (const data of datas) {
    for (const lang of ["pt", "en"]) {
      const base = `americanas_2021_em_${data}_${lang}`;
      const inv = JSON.parse(readFileSync(join(exemplos, `${base}.json`), "utf-8"));
      grava(raiz, `investigacoes/20990/2021/${data}/${lang}.json`, inv);
      cpSync(join(exemplos, `${base}.pdf`), join(raiz, "demo", `investigacoes/20990/2021/${data}/${lang}.pdf`));
      grava(raiz, `empresas/20990/${data}/${lang}.json`, {
        data_referencia: data, empresa: inv.empresa, exercicios: [2021], informacao_de_hoje: inv.informacao_de_hoje, aviso: inv.aviso,
      });
      nomes.add(inv.empresa.denominacao);
      if (lang === "pt") ultima = inv.empresa;
    }
  }
  const contrato = (nome) => JSON.parse(readFileSync(join(web, "tests", "contrato", `${nome}.json`), "utf-8"));
  const demonstracao = contrato("demonstracao");
  const { cd_cvm, cnpj, denominacao, origem_denominacao, codigos_negociacao, motivo_codigos_negociacao } = ultima;
  const americanas = {
    cd_cvm, cnpj, denominacao, origem_denominacao, codigos_negociacao, motivo_codigos_negociacao,
    nomes: [...nomes].sort(),
    datas: { "2022-04-30": [2021], "2024-12-31": [2021] },
    rotulos_datas: { "2022-04-30": "periodo_afetado", "2024-12-31": "depois_da_revelacao" },
    data_inicial: "2022-04-30",
    casos: [casoDaAmericanas()],
  };
  grava(raiz, "indice.json", { ...demonstracao, empresas: [americanas, ...demonstracao.empresas] });
  cpSync(join(web, "tests", "contrato", "como_testado.json"), join(raiz, "demo", "como-o-motor-foi-testado.json"));
  // a investigação da fixture (resposta da API guardada, só em PT): M-score com componentes não calculáveis
  const inv = contrato("investigacao");
  grava(raiz, `investigacoes/${inv.empresa.cd_cvm}/2020/${inv.data_referencia}/pt.json`, inv);
  grava(raiz, `empresas/${inv.empresa.cd_cvm}/${inv.data_referencia}/pt.json`, contrato("empresa"));
}

export const INV_FIXTURE = "/investigacao/?cd=100&ex=2020&data=2022-04-30";

/** Serve uma pasta (o site exportado) em http://127.0.0.1:<porta livre>, debaixo de `prefixo` (o NEXT_PUBLIC_BASE_PATH
 * do build, por exemplo "/Chiocca-System-", como no GitHub Pages). */
export async function servir(raiz, prefixo = "") {
  const servidor = createServer((req, res) => {
    const pedido = decodeURIComponent(new URL(req.url, "http://x").pathname);
    const caminho = pedido.startsWith(`${prefixo}/`) ? pedido.slice(prefixo.length) : null;
    let arquivo = caminho === null ? "" : join(raiz, caminho);
    if (arquivo && existsSync(arquivo) && statSync(arquivo).isDirectory()) arquivo = join(arquivo, "index.html");
    if (!arquivo || !existsSync(arquivo)) {
      res.writeHead(404, { "Content-Type": "text/plain" });
      return res.end("404");
    }
    res.writeHead(200, { "Content-Type": TIPOS[extname(arquivo)] ?? "application/octet-stream" });
    res.end(readFileSync(arquivo));
  });
  await new Promise((ok) => servidor.listen(0, "127.0.0.1", ok));
  const { port } = servidor.address();
  return { url: `http://127.0.0.1:${port}${prefixo}`, fechar: () => new Promise((ok) => servidor.close(ok)) };
}

/** Copia o site exportado para uma pasta temporária, monta os dados de teste e sobe o servidor. */
export async function subir() {
  const out = join(web, "out");
  if (!existsSync(join(out, "index.html"))) throw new Error("rode antes: npm run build:estatico");
  const raiz = mkdtempSync(join(tmpdir(), "chiocca-tela-"));
  cpSync(out, raiz, { recursive: true });
  montarDados(raiz);
  return { ...(await servir(raiz)), raiz };
}
