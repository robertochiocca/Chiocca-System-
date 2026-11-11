// Chamadas à API do Chiocca (/api/v1, repassada pelo Next à FastAPI) ou, na demonstração estática, leitura dos
// arquivos pré-gerados (public/demo/, saída da própria API para as mesmas entradas). Nos dois casos, cada resposta
// passa pela mesma conferência do contrato (lib/contrato.mjs) antes de ir para a tela.
import {
  validaBusca,
  validaComoTestado,
  validaDemonstracao,
  validaEmpresa,
  validaInvestigacao,
  validaSaude,
} from "./contrato.mjs";
import { DATA_MAXIMA } from "./limites.mjs";
import type { Busca, ComoTestado, Demonstracao, EmpresaNaData, ErroApi, Idioma, Investigacao, Saude } from "./tipos";

/** Demonstração estática: ligada no build por NEXT_PUBLIC_MODO_ESTATICO=1 (sem API rodando). */
export const MODO_ESTATICO = process.env.NEXT_PUBLIC_MODO_ESTATICO === "1";
const PREFIXO = process.env.NEXT_PUBLIC_BASE_PATH ?? "";
const BASE = "/api/v1";
const DEMO = `${PREFIXO}/demo`;

export class FalhaApi extends Error {
  constructor(
    public status: number,
    public erro: string,
    motivo: string,
  ) {
    super(motivo);
  }
}

async function pegar<T>(url: string, valida: (x: unknown) => string[]): Promise<T> {
  const r = await fetch(url, { headers: { Accept: "application/json" } });
  const corpo: unknown = await r.json().catch(() => null);
  if (!r.ok) {
    const e = (corpo ?? {}) as Partial<ErroApi>;
    throw new FalhaApi(r.status, e.erro ?? "erro", e.motivo ?? `HTTP ${r.status}`);
  }
  const problemas = valida(corpo);
  if (problemas.length) throw new FalhaApi(500, "fora_do_contrato", problemas.join("; "));
  return corpo as T;
}

const q = (p: Record<string, string | number>) => new URLSearchParams(Object.entries(p).map(([k, v]) => [k, String(v)]));

// ---- demonstração (rota /demonstracao; na demonstração estática, o indice.json, que é a mesma saída) ----

let demonstracao: Promise<Demonstracao> | null = null;
function lerDemonstracao(): Promise<Demonstracao> {
  demonstracao ??= pegar<Demonstracao>(MODO_ESTATICO ? `${DEMO}/indice.json` : `${BASE}/demonstracao`, validaDemonstracao).catch(
    (e) => {
      demonstracao = null; // tenta de novo na próxima chamada
      throw e;
    },
  );
  return demonstracao;
}

/** Sem acento, sem diferença de maiúsculas e com espaços simples (como chiocca/v2/busca.py). */
function normaliza(s: string): string {
  return s.normalize("NFKD").replace(/[̀-ͯ]/g, "").replace(/\s+/g, " ").trim().toLowerCase();
}

/** A mesma regra da API: nome (3 caracteres ou mais), código CVM (até 6 dígitos) ou CNPJ (14 dígitos). */
export function criterio(busca: string): ["nome" | "cd_cvm" | "cnpj", string] | null {
  const digitos = busca.trim().replace(/[.\-/\s]/g, "");
  if (/^\d{14}$/.test(digitos)) return ["cnpj", digitos];
  if (/^\d{1,6}$/.test(digitos)) return ["cd_cvm", digitos.replace(/^0+(?=\d)/, "")];
  const n = normaliza(busca);
  return n.length >= 3 ? ["nome", n] : null;
}

async function buscarDemo(busca: string): Promise<Busca> {
  const c = criterio(busca);
  if (!c) throw new FalhaApi(422, "busca_invalida", "busca por nome precisa de pelo menos 3 caracteres");
  const [tipo, chave] = c;
  const { empresas } = await lerDemonstracao();
  const achadas = empresas.filter((e) =>
    tipo === "cnpj"
      ? (e.cnpj ?? "").replace(/\D/g, "") === chave
      : tipo === "cd_cvm"
        ? e.cd_cvm === chave
        : e.nomes.some((n) => normaliza(n).includes(chave)),
  ); // o índice já vem em ordem alfabética; a ordem não muda
  const r: Busca = {
    busca,
    criterio: tipo,
    data_referencia: DATA_MAXIMA,
    ordem: "denominacao",
    total: achadas.length,
    resultados: achadas.map(({ cd_cvm, cnpj, denominacao, origem_denominacao, codigos_negociacao, motivo_codigos_negociacao }) => ({
      cd_cvm, cnpj, denominacao, origem_denominacao, codigos_negociacao, motivo_codigos_negociacao,
    })),
    aviso: (await import("./contrato.mjs")).AVISO,
  };
  const problemas = validaBusca(r);
  if (problemas.length) throw new FalhaApi(500, "fora_do_contrato", problemas.join("; "));
  return r;
}

async function pegarDemo<T>(caminho: string, valida: (x: unknown) => string[], t404: string): Promise<T> {
  try {
    return await pegar<T>(`${DEMO}/${caminho}`, valida);
  } catch (e) {
    if (e instanceof FalhaApi && e.status === 404) throw new FalhaApi(404, "fora_da_demonstracao", t404);
    throw e;
  }
}

const SEM_ARQUIVO = "Esta combinação não está na demonstração estática. / This combination is not in the static demo.";

export const api = {
  saude: () => pegar<Saude>(`${BASE}/saude`, validaSaude),
  buscar: (busca: string, data: string) =>
    MODO_ESTATICO ? buscarDemo(busca) : pegar<Busca>(`${BASE}/empresas?${q({ busca, data_referencia: data })}`, validaBusca),
  empresa: (cd: string, data: string, idioma: Idioma) =>
    MODO_ESTATICO
      ? pegarDemo<EmpresaNaData>(`empresas/${cd}/${data}/${idioma}.json`, validaEmpresa, SEM_ARQUIVO)
      : pegar<EmpresaNaData>(`${BASE}/empresas/${encodeURIComponent(cd)}?${q({ data_referencia: data, idioma })}`, validaEmpresa),
  investigacao: (cd: string, exercicio: number, data: string, idioma: Idioma) =>
    MODO_ESTATICO
      ? pegarDemo<Investigacao>(`investigacoes/${cd}/${exercicio}/${data}/${idioma}.json`, validaInvestigacao, SEM_ARQUIVO)
      : pegar<Investigacao>(
          `${BASE}/investigacoes/${encodeURIComponent(cd)}/${exercicio}?${q({ data_referencia: data, idioma })}`,
          validaInvestigacao,
        ),
  comoTestado: () =>
    MODO_ESTATICO
      ? pegarDemo<ComoTestado>("como-o-motor-foi-testado.json", validaComoTestado, SEM_ARQUIVO)
      : pegar<ComoTestado>(`${BASE}/como-o-motor-foi-testado`, validaComoTestado),
  pdf: (cd: string, exercicio: number, data: string, idioma: Idioma) =>
    MODO_ESTATICO
      ? `${DEMO}/investigacoes/${cd}/${exercicio}/${data}/${idioma}.pdf`
      : `${BASE}/investigacoes/${encodeURIComponent(cd)}/${exercicio}/pdf?${q({ data_referencia: data, idioma })}`,
  /** As companhias da demonstração (caso, datas e rótulos) e os destaques da página inicial. */
  demonstracao: lerDemonstracao,
};
