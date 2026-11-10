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

/** Monta os dados de teste: Americanas, exercício 2021, em 30/04/2022 e em 31/12/2024 (os exemplos guardados). */
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
      const aviso = inv.aviso;
      grava(raiz, `empresas/20990/${data}/${lang}.json`, {
        data_referencia: data, empresa: inv.empresa, exercicios: [2021], informacao_de_hoje: inv.informacao_de_hoje, aviso,
      });
      nomes.add(inv.empresa.denominacao);
      if (lang === "pt") ultima = inv.empresa;
    }
  }
  const { cd_cvm, cnpj, denominacao, origem_denominacao, codigos_negociacao, motivo_codigos_negociacao } = ultima;
  grava(raiz, "indice.json", { ordem: "denominacao", empresas: [{ cd_cvm, cnpj, denominacao, origem_denominacao,
    codigos_negociacao, motivo_codigos_negociacao, nomes: [...nomes].sort(), datas: { "2022-04-30": [2021], "2024-12-31": [2021] } }] });
  cpSync(join(web, "tests", "contrato", "como_testado.json"), join(raiz, "demo", "como-o-motor-foi-testado.json"));
}

/** Copia o site exportado para uma pasta temporária, monta os dados de teste e sobe o servidor. */
export async function subir() {
  const out = join(web, "out");
  if (!existsSync(join(out, "index.html"))) throw new Error("rode antes: npm run build:estatico");
  const raiz = mkdtempSync(join(tmpdir(), "chiocca-tela-"));
  cpSync(out, raiz, { recursive: true });
  montarDados(raiz);
  const servidor = createServer((req, res) => {
    let caminho = decodeURIComponent(new URL(req.url, "http://x").pathname);
    let arquivo = join(raiz, caminho);
    if (existsSync(arquivo) && statSync(arquivo).isDirectory()) arquivo = join(arquivo, "index.html");
    if (!existsSync(arquivo)) {
      res.writeHead(404, { "Content-Type": "text/plain" });
      return res.end("404");
    }
    res.writeHead(200, { "Content-Type": TIPOS[extname(arquivo)] ?? "application/octet-stream" });
    res.end(readFileSync(arquivo));
  });
  await new Promise((ok) => servidor.listen(0, "127.0.0.1", ok));
  const { port } = servidor.address();
  return { url: `http://127.0.0.1:${port}`, fechar: () => new Promise((ok) => servidor.close(ok)), raiz };
}
