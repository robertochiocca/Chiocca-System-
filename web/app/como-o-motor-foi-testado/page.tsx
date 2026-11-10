"use client";

// "Como o motor foi testado": os números do estudo 1 vêm da API, que os lê do mesmo JSON do resumo
// (docs/resultados_numeros.json), os mesmos da ficha do motor; com a antecedência dos acertos.
import { useEffect, useState } from "react";
import { api, FalhaApi } from "@/lib/api";
import { data, decimal, inteiro, pct } from "@/lib/formato";
import { useIdioma } from "@/lib/idioma";
import { fmt, REPOSITORIO } from "@/lib/textos";
import type { ComoTestado } from "@/lib/tipos";

export default function PaginaComoTestado() {
  const { idioma, t } = useIdioma();
  const [c, setC] = useState<ComoTestado | null>(null);
  const [erro, setErro] = useState<string | null>(null);
  useEffect(() => {
    api
      .comoTestado()
      .then(setC)
      .catch((x) => setErro(x instanceof FalhaApi ? x.message : t.erro));
  }, [t]);
  if (erro) return <p className="erro">{erro}</p>;
  if (!c) return <p className="discreto">{t.carregando}</p>;
  const i = (v: number) => inteiro(v, idioma);
  const d = (v: number | null | undefined, casas = 1) => decimal(v ?? null, idioma, casas);
  const doc = c.documentos[idioma];
  return (
    <>
      <h1>{t.testado_titulo}</h1>
      <p className="rotulo">{t.testado_intro}</p>
      <div className="grade">
        <section className="cartao">
          <h3>{t.acertos}</h3>
          <p>
            {fmt(t.acertos_txt, {
              a: i(c.acerto.acertados),
              n: i(c.acerto.acertaveis),
              ab: i(c.acerto.acertados_boba),
              casos: i(c.acerto.casos_no_gabarito),
            })}
          </p>
        </section>
        <section className="cartao">
          <h3>{t.alarmes}</h3>
          <p>{fmt(t.alarmes_txt, { xi: d(c.alarmes_por_acerto_nf.periodo_inteiro), xt: d(c.alarmes_por_acerto_nf.teste) })}</p>
        </section>
        <section className="cartao">
          <h3>{t.taxa}</h3>
          <p>{fmt(t.taxa_txt, { t: pct(c.taxa_de_alerta.nao_financeiras, idioma), tt: pct(c.taxa_de_alerta.com_financeiras, idioma) })}</p>
        </section>
        <section className="cartao">
          <h3>{t.acaso}</h3>
          <p>
            {fmt(t.acaso_txt, {
              e2: d(c.acaso.esperado_sem_independencia, 2),
              p2: pct(c.acaso.p_sem_independencia, idioma),
              obs: i(c.acaso.observados),
              e1: d(c.acaso.esperado_anos_independentes, 2),
              p1: pct(c.acaso.p_anos_independentes, idioma),
            })}
          </p>
        </section>
      </div>
      <h2>{t.antecedencia}</h2>
      <p>
        {fmt(t.antecedencia_txt, {
          med: d(c.antecedencia.mediana_meses),
          mn: d(c.antecedencia.minimo_meses),
          mx: d(c.antecedencia.maximo_meses),
        })}
      </p>
      <div className="tabela cartao">
        <table>
          <thead>
            <tr>
              <th>{t.col_caso}</th>
              <th>{t.col_exercicio}</th>
              <th>{t.col_entrega}</th>
              <th>{t.col_publica}</th>
              <th>{t.col_meses}</th>
            </tr>
          </thead>
          <tbody>
            {c.antecedencia.casos.map((x) => (
              <tr key={x.caso_id}>
                <td>{x.empresa}</td>
                <td>{x.exercicio}</td>
                <td>{data(x.dt_receb, idioma)}</td>
                <td>{data(x.data_publica, idioma)}</td>
                <td>{d(x.meses)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <p className="discreto">{t.correcao_nao_prova}</p>
      <ul>
        <li>
          <a href={`${REPOSITORIO}${doc.ficha_do_motor}`}>{t.ficha}</a>
        </li>
        <li>
          <a href={`${REPOSITORIO}${doc.resumo}`}>{doc.resumo}</a>
        </li>
        <li>
          <a href={`${REPOSITORIO}${doc.analises}`}>{doc.analises}</a>
        </li>
      </ul>
      <p className="discreto">
        {c.motor.v1} · {c.motor.v2}
      </p>
    </>
  );
}
