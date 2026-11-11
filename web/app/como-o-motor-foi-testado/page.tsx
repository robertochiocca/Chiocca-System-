"use client";

// "Como o motor foi testado", a página de explicação (Fase E2): o que o estudo 1 testou, a tabela das quatro regras
// de alerta e seus cortes, os resultados (acertos, alarmes por acerto, teste contra o acaso e antecedência), os
// limites e os links para o pré-registro e a ficha do motor. Os números vêm da API, que os lê do mesmo JSON do
// resumo (docs/resultados_numeros.json), os mesmos da ficha do motor; nada é escrito à mão.
import { useEffect, useState } from "react";
import TextoComLinks from "@/components/TextoComLinks";
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

      <section className="secao" aria-labelledby="titulo-o-que">
        <h2 id="titulo-o-que">{t.testado_o_que}</h2>
        <p>
          {fmt(t.testado_o_que_txt, {
            a: c.dados.primeiro_exercicio,
            b: c.dados.ultimo_exercicio,
            nf: i(c.dados.empresa_anos_nao_financeiras),
            f: i(c.dados.empresa_anos_financeiras),
          })}
        </p>
      </section>

      <section className="secao" aria-labelledby="titulo-regras">
        <h2 id="titulo-regras">{t.testado_regras}</h2>
        <div className="tabela cartao" tabIndex={0} role="region" aria-label={t.testado_regras}>
          <table>
            <thead>
              <tr>
                <th scope="col">{t.testado_sinal}</th>
                <th scope="col">{t.testado_grupo}</th>
                <th scope="col">{t.testado_corte}</th>
              </tr>
            </thead>
            <tbody>
              {c.regras.map((r) => (
                <tr key={r.sinal}>
                  <td>{r.rotulo[idioma]}</td>
                  <td>{t.grupos_plural[r.grupo]}</td>
                  <td>{r.regra[idioma]}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      <section className="secao" aria-labelledby="titulo-resultados">
        <h2 id="titulo-resultados">{t.testado_resultados}</h2>
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
        <h3 className="espaco">{t.antecedencia}</h3>
        <p>
          {fmt(t.antecedencia_txt, {
            med: d(c.antecedencia.mediana_meses),
            mn: d(c.antecedencia.minimo_meses),
            mx: d(c.antecedencia.maximo_meses),
          })}
        </p>
        <div className="tabela cartao" tabIndex={0} role="region" aria-label={t.antecedencia}>
          <table>
            <thead>
              <tr>
                <th scope="col">{t.col_caso}</th>
                <th scope="col">{t.col_exercicio}</th>
                <th scope="col">{t.col_entrega}</th>
                <th scope="col">{t.col_publica}</th>
                <th scope="col">{t.col_meses}</th>
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
      </section>

      <section className="secao" aria-labelledby="titulo-limites">
        <h2 id="titulo-limites">{t.testado_limites}</h2>
        <ul className="cartao">
          {c.limites[idioma].map((x, k) => (
            <li key={k}>
              <TextoComLinks texto={x} />
            </li>
          ))}
        </ul>
      </section>

      <section className="secao" aria-labelledby="titulo-documentos">
        <h2 id="titulo-documentos">{t.testado_documentos}</h2>
        <ul>
          <li>
            <a href={`${REPOSITORIO}${doc.pre_registro}`}>{t.pre_registro}</a>
          </li>
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
      </section>
    </>
  );
}
