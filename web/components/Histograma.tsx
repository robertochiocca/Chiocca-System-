// Distribuição agregada do setor no ano: só contagens por faixa e quantis (sem nome nem valor de outra empresa).
// A linha marca o valor da própria empresa.
import type { Distribuicao, Idioma } from "@/lib/tipos";
import { decimal, inteiro } from "@/lib/formato";
import { fmt, type Textos } from "@/lib/textos";

export default function Histograma({
  d,
  valor,
  idioma,
  t,
}: {
  d: Distribuicao | null | undefined;
  valor: number | null;
  idioma: Idioma;
  t: Textos;
}) {
  if (!d) return null;
  if (d.motivo || !d.limites || !d.contagens) return <p className="discreto">{t.distribuicao}: {d.motivo}</p>;
  const L = 300,
    A = 80,
    m = 4;
  const max = Math.max(1, ...d.contagens);
  const lo = d.limites[0],
    hi = d.limites[d.limites.length - 1];
  const x = (v: number) => m + ((Math.min(Math.max(v, lo), hi) - lo) / (hi - lo || 1)) * (L - 2 * m);
  const larg = (L - 2 * m) / d.contagens.length;
  const descricao = fmt(t.distribuicao_desc, {
    n: inteiro(d.n, idioma),
    abaixo: inteiro(d.abaixo ?? 0, idioma),
    acima: inteiro(d.acima ?? 0, idioma),
  });
  return (
    <figure>
      <figcaption className="rotulo">{t.distribuicao}</figcaption>
      <svg className="grafico" viewBox={`0 0 ${L} ${A + 16}`} role="img" aria-label={descricao}>
        {d.contagens.map((c, i) => (
          <rect key={i} className="barra" x={m + i * larg + 1} y={A - (c / max) * A} width={larg - 2} height={(c / max) * A} />
        ))}
        <line className="eixo" x1={m} x2={L - m} y1={A} y2={A} />
        {valor !== null && <line className="marca" x1={x(valor)} x2={x(valor)} y1={0} y2={A} />}
        <text x={m} y={A + 12}>{decimal(lo, idioma, 2)}</text>
        <text x={L - m} y={A + 12} textAnchor="end">{decimal(hi, idioma, 2)}</text>
      </svg>
      <p className="discreto">{descricao}</p>
    </figure>
  );
}
