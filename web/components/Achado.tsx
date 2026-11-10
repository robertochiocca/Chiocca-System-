// Um sinal numa família: valor com unidade, regra e alerta do estudo 1 (ou "componente do M-score"), contexto
// (percentis, distribuição agregada do setor, linha do tempo), confiança, explicações alternativas, limitações e
// a evidência clicável. Indicadores de contexto (Z'' e F) não disparam alerta.
import type { Achado as TipoAchado, Evidencia, Idioma } from "@/lib/tipos";
import { comUnidade, decimal, inteiro } from "@/lib/formato";
import type { Textos } from "@/lib/textos";
import Evidencias from "./Evidencias";
import TextoComLinks from "./TextoComLinks";
import Histograma from "./Histograma";
import LinhaDoTempo from "./LinhaDoTempo";

function percentil(p: { valor: number | null; n: number; motivo: string | null; marca?: string } | null | undefined, idioma: Idioma) {
  if (!p) return "—";
  if (p.valor === null) return p.motivo ?? "—";
  return `${decimal(p.valor, idioma, 0)} (n = ${inteiro(p.n, idioma)})${p.marca ? `; ${p.marca}` : ""}`;
}

export default function Achado({
  a,
  evidencias,
  idioma,
  t,
}: {
  a: TipoAchado;
  evidencias: Record<string, Evidencia>;
  idioma: Idioma;
  t: Textos;
}) {
  const valor = a.valor.status === "ok" ? a.valor.valor : null;
  const exibido = a.texto ?? (valor !== null ? comUnidade(valor, a.unidade, idioma) : a.valor.motivo);
  const c = a.contexto;
  return (
    <article className="cartao">
      <h3>{a.rotulo}</h3>
      <p>
        <span className="rotulo">{t.valor}: </span>
        <span className="valor">{exibido}</span>
      </p>
      {a.componente_de ? (
        <p className="discreto">{a.regra}</p>
      ) : a.familia === "possivel_manipulacao" ? (
        <>
          <p>
            <span className="rotulo">{t.alerta}: </span>
            {a.alerta_v1 === null ? (
              t.nao_dispara
            ) : a.alerta_v1 ? (
              <span className="etiqueta alerta">{t.sim}</span>
            ) : (
              <span className="etiqueta ok">{t.nao}</span>
            )}
          </p>
          {a.regra && <p className="discreto">{t.regra}: {a.regra}</p>}
        </>
      ) : (
        <p className="discreto">{t.nao_dispara}</p>
      )}
      {c && (
        <>
          <p className="rotulo">
            {t.pct_setor}: {percentil(c.percentil_setor_ano, idioma)}
            {c.percentil_grupo_ano && (
              <>
                <br />
                {t.pct_grupo}: {percentil(c.percentil_grupo_ano, idioma)}
              </>
            )}
          </p>
          <Histograma d={c.distribuicao_setor_ano} valor={valor} idioma={idioma} t={t} />
          <LinhaDoTempo h={c.historico} atual={valor} exercicio={a.exercicio} unidade={a.unidade} idioma={idioma} t={t} />
        </>
      )}
      {a.confianca && (
        <p className="rotulo">
          {t.confianca}: {t.niveis[a.confianca.nivel] ?? a.confianca.nivel}
        </p>
      )}
      {!!a.explicacoes_alternativas?.length && (
        <p className="discreto">
          {t.alternativas}: <TextoComLinks texto={a.explicacoes_alternativas.join(" ")} />
        </p>
      )}
      {!!(a.limitacoes?.length || a.marcas?.length) && (
        <ul className="discreto">
          {[...(a.limitacoes ?? []), ...(a.marcas ?? [])].filter(Boolean).map((x, i) => (
            <li key={i}>
              <TextoComLinks texto={x} />
            </li>
          ))}
        </ul>
      )}
      <Evidencias ids={a.linhagem?.entradas ?? []} todas={evidencias} idioma={idioma} t={t} />
    </article>
  );
}
