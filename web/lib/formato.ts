// Números e datas no formato de cada língua, como nos documentos do projeto (chiocca/formato.py):
// PT "1.234,5" e "31/12/2024"; EN "1,234.5" e "2024-12-31".
import type { Idioma } from "./tipos";

export function decimal(v: number | null | undefined, idioma: Idioma, casas = 3): string {
  if (v === null || v === undefined || Number.isNaN(v)) return "—";
  return new Intl.NumberFormat(idioma === "pt" ? "pt-BR" : "en-US", {
    minimumFractionDigits: casas,
    maximumFractionDigits: casas,
  })
    .format(v)
    .replace(/^-/, "−"); // sinal de menos tipográfico (−) na tela
}

/** Só o número, com as casas da unidade (dias 1, p.p. 2, índice 3): a unidade vai uma vez, no fim da frase. */
export function numero(v: number | null | undefined, unidade: string, idioma: Idioma): string {
  const casas = unidade === "dias" || unidade === "days" ? 1 : unidade === "p.p." ? 2 : 3;
  return decimal(v, idioma, casas);
}

export function inteiro(v: number | null | undefined, idioma: Idioma): string {
  return decimal(v, idioma, 0);
}

export function pct(v: number | null | undefined, idioma: Idioma, casas = 1): string {
  if (v === null || v === undefined) return "—";
  return `${decimal(v * 100, idioma, casas)}%`;
}

export function data(iso: string | null | undefined, idioma: Idioma): string {
  if (!iso) return "—";
  const [a, m, d] = iso.slice(0, 10).split("-");
  return idioma === "pt" ? `${d}/${m}/${a}` : `${a}-${m}-${d}`;
}

/** Valor com a unidade do contrato: dias (1 casa), p.p. (2 casas), índice (3 casas, unidade no fim). */
export function comUnidade(v: number | null | undefined, unidade: string, idioma: Idioma): string {
  if (v === null || v === undefined) return "—";
  if (unidade === "dias" || unidade === "days") return `${decimal(v, idioma, 1)} ${unidade}`;
  if (unidade === "p.p.") return `${decimal(v, idioma, 2)} p.p.`;
  return `${decimal(v, idioma, 3)} (${unidade})`;
}

export function milhoes(v: number | null | undefined, idioma: Idioma): string {
  return v === null || v === undefined ? "—" : decimal(v / 1e6, idioma, 1);
}

/** Valor em reais, em bilhões, com o sinal de menos antes do símbolo: PT "−R$ 12,6 bilhões", EN "−R$12.6 billion". */
export function bilhoes(v: number, idioma: Idioma): string {
  const n = decimal(Math.abs(v) / 1e9, idioma, 1);
  const s = idioma === "pt" ? `R$ ${n} bilhões` : `R$${n} billion`;
  return v < 0 ? `−${s}` : s;
}
