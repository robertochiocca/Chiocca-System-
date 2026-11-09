// Chamadas à API do Chiocca (/api/v1, repassada pelo Next à FastAPI). Cada resposta passa pela conferência do
// contrato (lib/contrato.mjs) antes de ir para a tela; resposta fora do contrato vira erro, não tela errada.
import {
  validaBusca,
  validaComoTestado,
  validaEmpresa,
  validaInvestigacao,
  validaSaude,
} from "./contrato.mjs";
import type { Busca, ComoTestado, EmpresaNaData, ErroApi, Idioma, Investigacao, Saude } from "./tipos";

const BASE = "/api/v1";

export class FalhaApi extends Error {
  constructor(
    public status: number,
    public erro: string,
    motivo: string,
  ) {
    super(motivo);
  }
}

async function pegar<T>(caminho: string, valida: (x: unknown) => string[]): Promise<T> {
  const r = await fetch(`${BASE}${caminho}`, { headers: { Accept: "application/json" } });
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

export const api = {
  saude: () => pegar<Saude>("/saude", validaSaude),
  buscar: (busca: string, data: string) => pegar<Busca>(`/empresas?${q({ busca, data_referencia: data })}`, validaBusca),
  empresa: (cd: string, data: string, idioma: Idioma) =>
    pegar<EmpresaNaData>(`/empresas/${encodeURIComponent(cd)}?${q({ data_referencia: data, idioma })}`, validaEmpresa),
  investigacao: (cd: string, exercicio: number, data: string, idioma: Idioma) =>
    pegar<Investigacao>(
      `/investigacoes/${encodeURIComponent(cd)}/${exercicio}?${q({ data_referencia: data, idioma })}`,
      validaInvestigacao,
    ),
  comoTestado: () => pegar<ComoTestado>("/como-o-motor-foi-testado", validaComoTestado),
  pdf: (cd: string, exercicio: number, data: string, idioma: Idioma) =>
    `${BASE}/investigacoes/${encodeURIComponent(cd)}/${exercicio}/pdf?${q({ data_referencia: data, idioma })}`,
};
