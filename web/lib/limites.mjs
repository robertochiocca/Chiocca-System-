// Os mesmos limites da API e do contrato (chiocca/v2/lacre.py). Um teste confere que são iguais.
export const DATA_MINIMA = "2011-04-30";
export const DATA_MAXIMA = "2024-12-31";
export const ULTIMO_EXERCICIO_LIBERADO = 2023;
export const PRIMEIRO_EXERCICIO = 2010;

/** Data de referência dentro do intervalo do contrato. */
export function dataValida(d) {
  return typeof d === "string" && /^\d{4}-\d{2}-\d{2}$/.test(d) && d >= DATA_MINIMA && d <= DATA_MAXIMA;
}

/** Exercício liberado (o lacre: nada acima de 2023). */
export function exercicioValido(e) {
  return Number.isInteger(e) && e >= PRIMEIRO_EXERCICIO && e <= ULTIMO_EXERCICIO_LIBERADO;
}
