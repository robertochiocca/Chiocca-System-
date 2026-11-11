"use client";

// Cartões dos sinais da investigação (Fase E2), de cima para baixo: título e "?", o que mede e por que importa (do
// catálogo), valor grande com unidade, regra do estudo 1 com "?", selo, percentis no setor e no grupo e explicações
// alternativas. Histograma, linha do tempo, faixa de Tukey, confiança e linhas usadas ficam em "Ver detalhes". O
// M-score abre expandido, com a grade dos oito componentes. Nada aqui soma famílias nem compara com outra empresa
// pelo nome: a comparação com o setor é só agregada.
import { useEffect, useState } from "react";
import { textoDoComponente, textoDoSinal } from "@/lib/catalogo";
import { comUnidade, decimal, inteiro } from "@/lib/formato";
import type { ChaveGlossario } from "@/lib/glossario";
import { useIdioma } from "@/lib/idioma";
import type { Achado as TipoAchado, Evidencia, Idioma, Percentil } from "@/lib/tipos";
import Ajuda from "./Ajuda";
import Evidencias from "./Evidencias";
import Histograma from "./Histograma";
import LinhaDoTempo from "./LinhaDoTempo";
import { BarraPercentil, Selo, type EstadoSelo } from "./Pecas";
import TextoComLinks from "./TextoComLinks";

export type Anos = { a: number; b: number } | undefined;

/** Celular (até 760 px): os cartões ficam fechados, com "Ver detalhes". */
export function useEstreita(): boolean {
  const [estreita, setEstreita] = useState(false);
  useEffect(() => {
    const m = window.matchMedia("(max-width: 760px)");
    const atualiza = () => setEstreita(m.matches);
    atualiza();
    m.addEventListener("change", atualiza);
    return () => m.removeEventListener("change", atualiza);
  }, []);
  return estreita;
}

/** Sinal com regra do estudo 1 (M-score, DPO, juro implícito, peso não recorrente). */
export function temRegra(a: TipoAchado): boolean {
  return a.familia === "possivel_manipulacao" && !a.componente_de && a.regra !== null;
}

export function estadoDoSinal(a: TipoAchado): EstadoSelo {
  if (!temRegra(a)) return "contexto";
  if (a.alerta_v1 === true) return "alerta";
  if (a.alerta_v1 === false) return "sem_alerta";
  return "nao_calculavel";
}

function valorDe(a: TipoAchado): number | null {
  return a.valor.status === "ok" ? a.valor.valor : null;
}

function percentilTexto(p: Percentil | null | undefined, idioma: Idioma): string {
  if (!p) return "—";
  if (p.valor === null) return p.motivo ?? "—";
  return `${decimal(p.valor, idioma, 0)} (n = ${inteiro(p.n, idioma)})${p.marca ? `; ${p.marca}` : ""}`;
}

function ajudaDoTitulo(a: TipoAchado): ChaveGlossario {
  if (a.componente_de) return "componente_mscore";
  if (!temRegra(a)) return "so_contexto";
  return a.unidade === "índice" || a.unidade === "index" ? "indice" : "regra_estudo_1";
}

function Cabeca({ a, anos }: { a: TipoAchado; anos: Anos }) {
  const { idioma, t } = useIdioma();
  const cat = textoDoSinal(a.sinal, idioma);
  return (
    <>
      <h3 className="titulo-sinal">
        <span>{a.rotulo}</span> <Ajuda chave={ajudaDoTitulo(a)} anos={anos} />
      </h3>
      {cat && (
        <dl className="explica">
          <dt>{t.o_que_mede}</dt>
          <dd>{cat.o_que_mede}</dd>
          <dt>{a.familia === "possivel_manipulacao" ? t.por_que_manipulacao : t.por_que_contexto}</dt>
          <dd>{cat.por_que}</dd>
        </dl>
      )}
    </>
  );
}

function ValorERegra({ a, anos }: { a: TipoAchado; anos: Anos }) {
  const { idioma, t } = useIdioma();
  const v = valorDe(a);
  const exibido = a.texto ?? (v !== null ? comUnidade(v, a.unidade, idioma) : a.valor.motivo ?? "—");
  const estado = estadoDoSinal(a);
  return (
    <>
      <p className="valor-grande">{exibido}</p>
      {temRegra(a) && a.regra && (
        <p className="regra">
          {t.regra_estudo_1}: {a.regra} <Ajuda chave={a.sinal === "mscore" ? "regra_mscore" : "regra_estudo_1"} anos={anos} />
        </p>
      )}
      <p className="linha-selo">
        <Selo estado={estado} />
        {estado === "sem_alerta" && <Ajuda chave="sem_alerta" />}
      </p>
    </>
  );
}

function Percentis({ a }: { a: TipoAchado }) {
  const { idioma, t } = useIdioma();
  const c = a.contexto;
  if (!c) return null;
  return (
    <p className="rotulo">
      {t.pct_setor}: {percentilTexto(c.percentil_setor_ano, idioma)} <Ajuda chave="percentil" />
      {c.percentil_grupo_ano && (
        <>
          <br />
          {t.pct_grupo}: {percentilTexto(c.percentil_grupo_ano, idioma)}
        </>
      )}
    </p>
  );
}

function Alternativas({ a, quadro = false }: { a: TipoAchado; quadro?: boolean }) {
  const { t } = useIdioma();
  const lista = (a.explicacoes_alternativas ?? []).filter(Boolean) as string[];
  if (!lista.length) return null;
  return (
    <div className={quadro ? "quadro" : undefined}>
      <p className="rotulo">{t.alternativas}</p>
      {lista.map((x, i) => (
        <p key={i}>
          <TextoComLinks texto={x} />
        </p>
      ))}
    </div>
  );
}

function Graficos({ a }: { a: TipoAchado }) {
  const { idioma, t } = useIdioma();
  const c = a.contexto;
  if (!c) return null;
  const v = valorDe(a);
  return (
    <div className="graficos">
      <div>
        <Histograma d={c.distribuicao_setor_ano} valor={v} idioma={idioma} t={t} /> <Ajuda chave="n" />
      </div>
      <div>
        <LinhaDoTempo h={c.historico} atual={v} exercicio={a.exercicio} unidade={a.unidade} idioma={idioma} t={t} />{" "}
        <Ajuda chave="faixa_tukey" />
      </div>
    </div>
  );
}

function Confianca({ a, evidencias }: { a: TipoAchado; evidencias: Record<string, Evidencia> }) {
  const { idioma, t } = useIdioma();
  return (
    <>
      {a.confianca && (
        <div className="confianca">
          <p className="rotulo">
            {t.confianca}: {t.niveis[a.confianca.nivel] ?? a.confianca.nivel} <Ajuda chave="confianca" />
          </p>
          <ul className="discreto">
            {a.confianca.criterios
              .filter((c) => c.resultado !== "ok" && c.motivo)
              .map((c, i) => (
                <li key={i}>
                  <TextoComLinks texto={c.motivo} />
                </li>
              ))}
          </ul>
        </div>
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
    </>
  );
}

/** Os nove sinais do Piotroski F com os rótulos do artigo e o resultado em texto (sim, não, não calculável). */
function SinaisF({ a }: { a: TipoAchado }) {
  const { t } = useIdioma();
  const s = a.componentes?.sinais as Record<string, number | null> | undefined;
  if (!s) return null;
  return (
    <div>
      <p className="rotulo">{t.sinais_f}</p>
      <ul className="lista-sinais">
        {Object.entries(s).map(([k, v]) => (
          <li key={k}>
            <span>{t.sinais_f_rotulos[k] ?? k}</span>
            <span className={`resultado-f ${v === 1 ? "sim" : v === 0 ? "nao" : "nc"}`}>{v === 1 ? t.f_sim : v === 0 ? t.f_nao : t.f_nc}</span>
          </li>
        ))}
      </ul>
      <p className="discreto">{t.f_legenda}</p>
    </div>
  );
}

/** Os quatro componentes do Z'' com nomes legíveis (X1 capital de giro / ativo etc.). */
function ComponentesZ2({ a }: { a: TipoAchado }) {
  const { idioma, t } = useIdioma();
  const c = a.componentes as Record<string, number> | null | undefined;
  if (!c) return null;
  return (
    <div>
      <p className="rotulo">{t.componentes_z2}</p>
      <ul className="lista-sinais">
        {Object.entries(c).map(([k, v]) => (
          <li key={k}>
            <span>
              {k} {textoDoComponente(k, idioma) ?? ""}
            </span>
            <span>{decimal(v, idioma, 3)}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}

/** Cartão de um sinal (DPO, juro implícito, lucro sem caixa, peso não recorrente, Z'' e F). */
export function CartaoSinal({ a, evidencias, anos }: { a: TipoAchado; evidencias: Record<string, Evidencia>; anos: Anos }) {
  const { t } = useIdioma();
  return (
    <article className="cartao cartao-sinal" aria-label={a.rotulo ?? a.sinal}>
      <Cabeca a={a} anos={anos} />
      <ValorERegra a={a} anos={anos} />
      <Percentis a={a} />
      {a.sinal === "altman_z2" && <ComponentesZ2 a={a} />}
      {a.sinal === "piotroski_f" && <SinaisF a={a} />}
      <Alternativas a={a} />
      <details className="detalhes">
        <summary>{t.ver_detalhes}</summary>
        <Graficos a={a} />
        <Confianca a={a} evidencias={evidencias} />
      </details>
    </article>
  );
}

/** Um componente do M-score na grade: nome com a sigla, valor, o que mede, barra do percentil e a etiqueta da faixa. */
function Componente({ a }: { a: TipoAchado }) {
  const { idioma, t } = useIdioma();
  const v = valorDe(a);
  const posicao = a.contexto?.historico?.posicao;
  return (
    <li className="componente">
      <p className="componente-nome">{a.rotulo}</p>
      <p className="componente-valor">{v !== null ? decimal(v, idioma, 3) : a.valor.motivo ?? "—"}</p>
      <p className="discreto">{textoDoComponente(a.sinal, idioma)}</p>
      <BarraPercentil p={a.contexto?.percentil_setor_ano?.valor} />
      {posicao === "acima" && <span className="etiqueta-faixa">{t.acima_da_faixa}</span>}
      {posicao === "abaixo" && <span className="etiqueta-faixa">{t.abaixo_da_faixa}</span>}
    </li>
  );
}

/** O M-score, expandido: valor, regra, selo, percentis, gráficos do setor e da própria empresa, a explicação
 * alternativa num quadro, confiança e linhas usadas, e a grade dos oito componentes. No celular, os gráficos e a
 * confiança ficam em "Ver detalhes". */
export function CartaoMScore({
  a,
  componentes,
  evidencias,
  anos,
}: {
  a: TipoAchado;
  componentes: TipoAchado[];
  evidencias: Record<string, Evidencia>;
  anos: Anos;
}) {
  const { t } = useIdioma();
  const estreita = useEstreita();
  return (
    <article className="cartao cartao-sinal cartao-mscore" aria-label={a.rotulo ?? a.sinal}>
      <Cabeca a={a} anos={anos} />
      <ValorERegra a={a} anos={anos} />
      <Percentis a={a} />
      <Alternativas a={a} quadro />
      <details className="detalhes" open={!estreita}>
        <summary>{t.ver_detalhes}</summary>
        <Graficos a={a} />
        <Confianca a={a} evidencias={evidencias} />
      </details>
      {componentes.length > 0 && (
        <section className="componentes" aria-label={t.componentes_mscore}>
          <h4>
            {t.componentes_mscore}: <span className="discreto">{t.componentes_nota}</span> <Ajuda chave="componente_mscore" />
          </h4>
          <ul className="grade-componentes">
            {componentes.map((c) => (
              <Componente key={c.id} a={c} />
            ))}
          </ul>
        </section>
      )}
    </article>
  );
}
