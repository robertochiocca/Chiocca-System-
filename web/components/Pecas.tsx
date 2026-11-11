"use client";

// Peças pequenas da interface (Fase E2): selo do estado de um sinal, caminho de navegação, botões de data com rótulo
// e barra de percentil. O estado sempre vai em texto, nunca só em cor; "Sem alerta" é cinza neutro, nunca verde,
// porque não ter alerta não é atestado.
import Link from "next/link";
import { data as fdata, decimal } from "@/lib/formato";
import { useIdioma } from "@/lib/idioma";
import { fmt } from "@/lib/textos";

export type EstadoSelo = "alerta" | "sem_alerta" | "contexto" | "nao_calculavel";

export function Selo({ estado }: { estado: EstadoSelo }) {
  const { t } = useIdioma();
  const texto = { alerta: t.selo_alerta, sem_alerta: t.selo_sem_alerta, contexto: t.selo_contexto, nao_calculavel: t.selo_nao_calculavel }[
    estado
  ];
  return <span className={`selo selo-${estado}`}>{texto}</span>;
}

export function Migalhas({ itens }: { itens: { rotulo: string; href?: string }[] }) {
  const { t } = useIdioma();
  return (
    <nav className="migalhas" aria-label={t.migalhas}>
      <ol>
        {itens.map((x, i) => (
          <li key={i}>
            {x.href && i < itens.length - 1 ? <Link href={x.href}>{x.rotulo}</Link> : <span aria-current="page">{x.rotulo}</span>}
          </li>
        ))}
      </ol>
    </nav>
  );
}

/** Datas como botões (links), com um rótulo curto embaixo de cada uma; a selecionada fica destacada. No celular, a
 * fila rola na horizontal. */
export function BotoesDatas({
  datas,
  rotulos,
  selecionada,
  href,
}: {
  datas: string[];
  rotulos: Record<string, string>;
  selecionada: string;
  href: (d: string) => string;
}) {
  const { idioma, t } = useIdioma();
  return (
    <nav className="datas" aria-label={t.datas_disponiveis}>
      <ul>
        {datas.map((d) => (
          <li key={d}>
            <Link href={href(d)} className="data-botao" aria-current={d === selecionada ? "true" : undefined}>
              <span className="data-valor">{fdata(d, idioma)}</span>
              {rotulos[d] && <span className="data-rotulo">{t.rotulos_datas[rotulos[d]] ?? rotulos[d]}</span>}
            </Link>
          </li>
        ))}
      </ul>
    </nav>
  );
}

/** Barra de 0 a 100 com a marca do percentil no setor (a posição, não o valor; sem nomes de outras empresas). */
export function BarraPercentil({ p }: { p: number | null | undefined }) {
  const { idioma, t } = useIdioma();
  if (p === null || p === undefined) return <p className="discreto">{t.sem_percentil}</p>;
  const rotulo = fmt(t.barra_percentil, { p: decimal(p, idioma, 0) });
  return (
    <div className="barra-percentil" role="img" aria-label={rotulo}>
      <span className="barra-percentil-marca" style={{ left: `${Math.min(100, Math.max(0, p))}%` }} />
      <span className="discreto">{rotulo}</span>
    </div>
  );
}
