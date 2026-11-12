export interface TrechoAgrupado {
  omitido: boolean;
  pagina: number | null;
  texto: string | null;
  negacao: boolean | null;
  cortado: boolean;
  rotulos: string[];
  n: number;
}
export function agrupaTrechos(
  trechos: Array<{ omitido: boolean; pagina: number | null; texto: string | null; negacao?: boolean | null; cortado?: boolean; rotulo?: string | null }>,
): TrechoAgrupado[];
export function frase(x: string | null | undefined): string;
export function comPonto(x: string): string;
