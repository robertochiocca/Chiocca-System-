// Textos do catálogo de sinais para a interface (gerados de catalogo_sinais.yaml por python -m chiocca.v2.catalogo_web,
// conferidos por teste): o que cada sinal mede e por que importa, e uma linha por componente.
import catalogo from "./catalogo.json";
import type { Idioma } from "./tipos";

export interface TextoSinal {
  nome: string;
  o_que_mede: string;
  por_que: string;
}

const SINAIS = catalogo.sinais as Record<string, Record<Idioma, TextoSinal>>;
const COMPONENTES = catalogo.componentes as Record<string, Record<Idioma, string>>;

export function textoDoSinal(sinal: string, idioma: Idioma): TextoSinal | null {
  return SINAIS[sinal]?.[idioma] ?? null;
}

export function textoDoComponente(componente: string, idioma: Idioma): string | null {
  return COMPONENTES[componente]?.[idioma] ?? null;
}
