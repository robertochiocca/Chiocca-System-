import type { ItemIPE } from "./tipos";
export function linhasIPE(itens: ItemIPE[]): ItemIPE[][];
export function linksDaLinha(itens: ItemIPE[]): ItemIPE[];
export function marcaDaLinha(itens: ItemIPE[], t: { ipe_e: string; ipe_versao: string; ipe_versoes: string; ipe_documentos: string }): string | null;
