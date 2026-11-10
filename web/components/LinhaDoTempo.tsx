// Linha do tempo da própria empresa: os exercícios anteriores (como eram na data) e o valor atual, com a faixa de
// Tukey (1,5 × IQR) ao fundo. Nenhuma outra empresa aparece.
import type { Historico, Idioma } from "@/lib/tipos";
import { numero } from "@/lib/formato";
import { fmt, type Textos } from "@/lib/textos";

export default function LinhaDoTempo({
  h,
  atual,
  exercicio,
  unidade,
  idioma,
  t,
}: {
  h: Historico | undefined;
  atual: number | null;
  exercicio: number;
  unidade: string;
  idioma: Idioma;
  t: Textos;
}) {
  if (!h) return null;
  const pontos: [number, number][] = [...(h.serie ?? [])];
  if (atual !== null) pontos.push([exercicio, atual]);
  const resumo =
    h.faixa_tukey && h.posicao
      ? fmt(t.faixa_tukey, {
          a: numero(h.faixa_tukey[0], unidade, idioma),
          b: numero(h.faixa_tukey[1], unidade, idioma),
          u: unidade,
          p: t.posicoes[h.posicao],
        })
      : h.motivo ?? "";
  if (pontos.length < 2) return <p className="discreto">{t.historico}: {resumo}</p>;
  const L = 300,
    A = 80,
    m = 6;
  const valores = pontos.map((p) => p[1]).concat(h.faixa_tukey ?? []);
  const lo = Math.min(...valores),
    hi = Math.max(...valores);
  const anos = pontos.map((p) => p[0]);
  const x = (a: number) => m + ((a - Math.min(...anos)) / (Math.max(...anos) - Math.min(...anos) || 1)) * (L - 2 * m);
  const y = (v: number) => A - m - ((v - lo) / (hi - lo || 1)) * (A - 2 * m);
  const anteriores = pontos.slice(0, atual !== null ? -1 : undefined);
  return (
    <figure>
      <figcaption className="rotulo">{t.historico}</figcaption>
      <svg className="grafico" viewBox={`0 0 ${L} ${A + 14}`} role="img" aria-label={resumo}>
        {h.faixa_tukey && (
          <rect className="faixa" x={m} width={L - 2 * m} y={y(h.faixa_tukey[1])} height={Math.max(1, y(h.faixa_tukey[0]) - y(h.faixa_tukey[1]))} />
        )}
        <polyline className="linha" points={pontos.map((p) => `${x(p[0])},${y(p[1])}`).join(" ")} />
        {anteriores.map((p) => (
          <circle key={p[0]} className="ponto" cx={x(p[0])} cy={y(p[1])} r={3} />
        ))}
        {atual !== null && <circle className="atual" cx={x(exercicio)} cy={y(atual)} r={4} />}
        <text x={m} y={A + 12}>{Math.min(...anos)}</text>
        <text x={L - m} y={A + 12} textAnchor="end">{Math.max(...anos)}</text>
      </svg>
      <p className="discreto">{resumo}</p>
    </figure>
  );
}
