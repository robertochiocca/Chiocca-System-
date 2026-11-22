// make demo (pedido de 21/11/2026): serve a demonstração estática no computador, com os dados de amostra já
// versionados, sem baixar nada da CVM e sem API. São os exemplos de docs/exemplos/: a Americanas, exercício 2021, em
// 30/04/2022 e em 31/12/2024, em PT e EN, com o PDF, e a página "Como o motor foi testado" (web/tests/contrato/). Nenhum
// exercício de 2024 em diante, reservados ao estudo 2. A demonstração completa, com as companhias do gabarito, está no
// GitHub Pages. Rode antes: npm run build:estatico (o make demo faz isso).
import { cpSync, existsSync, mkdtempSync } from "node:fs";
import { tmpdir } from "node:os";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { montarDados, prefixoDoBuild, servir } from "../tests/tela/servidor.mjs";

const out = join(dirname(fileURLToPath(import.meta.url)), "..", "out");
if (!existsSync(join(out, "index.html"))) {
  console.error("Falta o site exportado: rode antes npm run build:estatico (ou make demo, na raiz do repositório).");
  process.exit(1);
}
const porta = Number(process.env.PORTA ?? 3000);
const raiz = mkdtempSync(join(tmpdir(), "chiocca-demo-"));
cpSync(out, raiz, { recursive: true });
montarDados(raiz, { ficticias: false });
const { url } = await servir(raiz, prefixoDoBuild(out), porta);
console.log(`Demonstração local em ${url}/ (Ctrl+C para parar)`);
console.log(`Investigação de exemplo: ${url}/investigacao/?cd=20990&ex=2021&data=2022-04-30`);
