"use client";

// Resumo no topo da investigação (Fase E2), antes de qualquer detalhe: possível manipulação (selo e uma frase com o
// que disparou e o que ficou abaixo do corte), risco financeiro e qualidade financeira (só contexto) e o caso do
// gabarito, quando houver. Logo abaixo, a frase de que as famílias não se somam e o bloco "Como ler esta página".
// Os números vêm do JSON da investigação e do de "Como o motor foi testado"; nada é escrito à mão.
import Link from "next/link";
import { data as fdata, decimal, inteiro, pct } from "@/lib/formato";
import { useIdioma } from "@/lib/idioma";
import { fmt, TIPOS_DE_CASO } from "@/lib/textos";
import type { Achado, CasoDoGabarito, ComoTestado, Investigacao } from "@/lib/tipos";
import { Selo, type EstadoSelo } from "./Pecas";
import { estadoDoSinal, temRegra } from "./Sinais";

function lista(xs: (string | null)[]): string {
  return xs.filter(Boolean).join("; ");
}

export function CartaoCaso({ casos, exercicio }: { casos: CasoDoGabarito[]; exercicio?: number }) {
  const { idioma, t } = useIdioma();
  return (
    <section className="cartao cartao-caso" aria-label={t.caso_titulo}>
      <h3>{t.caso_titulo}</h3>
      {casos.map((c) => {
        const dentro = c.periodo_afetado && exercicio !== undefined && exercicio >= c.periodo_afetado[0] && exercicio <= c.periodo_afetado[1];
        return (
          <div key={c.caso_id} className="caso">
            <p>
              <strong>{c.tipo_evento.map((x) => TIPOS_DE_CASO[idioma][x] ?? x).join(" · ")}</strong>
            </p>
            <p>
              {t.data_publica}: {c.data_publica ? fdata(c.data_publica, idioma) : t.sem_data_publica}
            </p>
            <p>{c.periodo_afetado ? fmt(t.caso_periodo, { a: c.periodo_afetado[0], b: c.periodo_afetado[1] }) : t.caso_sem_periodo}</p>
            {c.periodo_afetado && exercicio !== undefined && (
              <p>{fmt(dentro ? t.caso_dentro : t.caso_fora, { ex: exercicio })}</p>
            )}
            {c.fonte && (
              <p>
                <a href={c.fonte} rel="noopener noreferrer" target="_blank">
                  {t.caso_fonte}
                </a>
              </p>
            )}
          </div>
        );
      })}
    </section>
  );
}

export default function Resumo({ inv, casos, testado }: { inv: Investigacao; casos: CasoDoGabarito[] | null; testado: ComoTestado | null }) {
  const { idioma, t } = useIdioma();
  const manip = inv.achados.possivel_manipulacao ?? [];
  const regras = manip.filter(temRegra);
  const nome = (a: Achado) => a.rotulo ?? a.sinal;
  const disparou = regras.filter((a) => a.alerta_v1 === true);
  const abaixo = regras.filter((a) => a.alerta_v1 === false);
  const semValor = regras.filter((a) => a.alerta_v1 === null);
  const estadoManip: EstadoSelo = disparou.length ? "alerta" : abaixo.length ? "sem_alerta" : "nao_calculavel";
  const z = inv.achados.risco_financeiro?.[0];
  const f = inv.achados.qualidade_financeira?.[0];
  const mt = inv.como_o_motor_foi_testado;
  const ex = inv.exercicios[0]?.exercicio;
  const pZ = z?.contexto?.percentil_setor_ano;
  return (
    <section id="resumo" className="secao" aria-labelledby="titulo-resumo">
      <h2 id="titulo-resumo">{t.resumo}</h2>
      <div className="grade-resumo">
        <section className="cartao resumo-manip">
          <h3>{t.sec_manipulacao}</h3>
          <p>
            <Selo estado={estadoManip} />
          </p>
          <p>
            {disparou.length ? fmt(t.resumo_disparou, { s: lista(disparou.map(nome)) }) : t.resumo_nenhum}{" "}
            {abaixo.length > 0 && fmt(t.resumo_abaixo, { s: lista(abaixo.map(nome)) })}{" "}
            {semValor.length > 0 && fmt(t.resumo_nc, { s: lista(semValor.map(nome)) })}
          </p>
          <p>
            <a href="#manipulacao">{t.sec_manipulacao} ↓</a>
          </p>
        </section>
        {z && (
          <section className="cartao resumo-risco">
            <h3>{t.familias.risco_financeiro}</h3>
            <p>
              <Selo estado={estadoDoSinal(z)} />
            </p>
            <p>
              {fmt(t.resumo_risco, {
                z: z.valor.status === "ok" ? decimal(z.valor.valor, idioma, 2) : z.valor.motivo ?? "—",
                p: pZ?.valor !== null && pZ?.valor !== undefined ? decimal(pZ.valor, idioma, 0) : "—",
              })}
            </p>
          </section>
        )}
        {f && (
          <section className="cartao resumo-qualidade">
            <h3>{t.familias.qualidade_financeira}</h3>
            <p>
              <Selo estado={estadoDoSinal(f)} />
            </p>
            <p>{fmt(t.resumo_qualidade, { f: f.texto ?? f.valor.motivo ?? "—" })}</p>
          </section>
        )}
        {casos && casos.length > 0 && <CartaoCaso casos={casos} exercicio={ex} />}
      </div>
      <p className="nao-somam">{t.nao_somam}</p>
      <details className="como-ler">
        <summary>{t.como_ler}</summary>
        <ul>
          <li>{t.como_ler_familias}</li>
          <li>
            {fmt(t.como_ler_alerta, {
              a: testado?.dados.primeiro_exercicio ?? "—",
              b: testado?.dados.ultimo_exercicio ?? "—",
              t: mt.taxa_de_alerta_nao_financeiras !== undefined ? pct(mt.taxa_de_alerta_nao_financeiras, idioma) : "—",
              x: inteiro(mt.acertados, idioma),
              n: inteiro(mt.acertaveis, idioma),
            })}{" "}
            <Link href="/como-o-motor-foi-testado">{t.nav_testado}</Link>
          </li>
          <li>{t.como_ler_percentil}</li>
          <li>{t.como_ler_confianca}</li>
        </ul>
      </details>
    </section>
  );
}
