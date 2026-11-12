"use client";

// Seção "Trechos dos documentos (copiados; não gera alerta)" da investigação (Fase F1): trechos copiados das notas
// explicativas e do relatório do auditor, com a página, e a tabela do Formulário de Referência. É só fato: nenhum selo,
// alerta, nota ou ordenação. Exibição (decisões de 11/11/2026, depois da medida): trecho com mais de um rótulo aparece
// uma vez, com os rótulos juntos; os omitidos da mesma página (nome de pessoa física) viram uma linha só, com a
// contagem (lib/trechos.mjs, o mesmo agrupamento do PDF); o JSON continua com um item por trecho. Na interface em
// inglês, os trechos ficam em português, marcados como "original excerpt in Portuguese". Só aparece quando a
// investigação traz a seção (o leitor só entrou depois de passar nas metas do pré-registro, docs/pre-registro-leitor.md).
import { data as fdata, decimal, inteiro } from "@/lib/formato";
import { useIdioma } from "@/lib/idioma";
import { fmt, REPOSITORIO } from "@/lib/textos";
import type { Investigacao, LeituraDocumental as Leitura, TrechoLido } from "@/lib/tipos";
import { agrupaTrechos, frase, type TrechoAgrupado } from "@/lib/trechos.mjs";

/** Montante e saldo vêm do arquivo da CVM com hífen no lugar do sinal de menos; na tela, o sinal de menos (−). */
function comMenos(v: string | null): string {
  return v === null ? "—" : v.replace(/(^|[^\w.,\-−/])-(?=\d)/g, "$1−");
}

function Trecho({ g }: { g: TrechoAgrupado }) {
  const { idioma, t } = useIdioma();
  if (g.omitido) {
    const linha = g.pagina !== null ? fmt(t.leitura_omitidos, { p: g.pagina }) : t.leitura_omitidos_sem_pagina;
    return <p className="trecho-omitido">{linha + (g.n > 1 ? fmt(t.leitura_n_trechos, { n: inteiro(g.n, idioma) }) : "")}</p>;
  }
  const onde = g.pagina !== null ? fmt(t.leitura_pagina, { p: g.pagina }) : null;
  const rotulos = g.rotulos.map((r) => t.rotulos_leitura[r] ?? r).join("; ");
  return (
    <figure className="trecho">
      {rotulos && <p className="rotulos-trecho">[{rotulos}]</p>}
      <blockquote lang="pt">“{g.texto}”</blockquote>
      <figcaption className="discreto">
        {[onde, g.negacao ? t.leitura_negativa : null, g.cortado ? t.leitura_cortado : null, idioma === "en" ? t.leitura_original : null]
          .filter(Boolean)
          .join(" · ")}
      </figcaption>
    </figure>
  );
}

function Trechos({ trechos }: { trechos: TrechoLido[] }) {
  return (
    <>
      {agrupaTrechos(trechos).map((g, k) => (
        <Trecho key={k} g={g} />
      ))}
    </>
  );
}

type Testado = NonNullable<Investigacao["como_o_leitor_foi_testado"]>;

function ComoTestado({ m }: { m: Testado }) {
  const { idioma, t } = useIdioma();
  const nomes = m.nomes_vazados === 0 ? t.leitura_sem_nomes : fmt(t.leitura_com_nomes, { n: inteiro(m.nomes_vazados, idioma) });
  return (
    <p className="discreto">
      {fmt(t.leitura_testado, {
        n: inteiro(m.casos, idioma),
        c: m.commit,
        p: decimal(m.precisao, idioma, 3),
        cob: decimal(m.cobertura, idioma, 3),
        a: inteiro(m.trechos_conferidos, idioma),
        b: inteiro(m.trechos_mostrados, idioma),
        nomes,
      })}{" "}
      (
      <a href={`${REPOSITORIO}${m.documento}`} rel="noopener noreferrer" target="_blank">
        {m.documento}
      </a>
      ).
    </p>
  );
}

export default function LeituraDocumental({ l, testado, limites }: { l: Leitura; testado: Testado | null; limites: string[] }) {
  const { idioma, t } = useIdioma();
  const pr = l.partes_relacionadas;
  const rs = l.risco_sacado;
  const rel = l.relatorio_do_auditor;
  const fre = l.formulario_de_referencia;
  const doc = l.documento;
  const fd = fre.documento;
  const textoFre = [
    t.leitura_fre[fre.status] ?? (fre.motivo ? frase(fre.motivo) : null),
    fd?.linhagem ? t.leitura_linhagem : null,
  ].filter(Boolean);
  return (
    <div className="leitura">
      <p className="discreto">{l.nota}</p>
      {testado && <ComoTestado m={testado} />}
      {doc && doc.num_doc && (
        <p className="discreto">
          {t.leitura_documento}: DFP · {fmt(t.leitura_versao, { v: doc.versao ?? "—", d: fdata(doc.dt_receb, idioma) })}
        </p>
      )}

      <section className="cartao" aria-labelledby="titulo-leitura-notas">
        <h3 id="titulo-leitura-notas">{t.leitura_notas}</h3>
        <h4>{t.leitura_partes}</h4>
        {pr.motivo && <p className="discreto">{frase(pr.motivo)}</p>}
        {pr.nota && (
          <p>
            {t.leitura_nota}: {pr.nota.titulo} ({fmt(t.leitura_paginas, { a: pr.nota.paginas[0], b: pr.nota.paginas[1] })})
            {pr.colunas.length > 0 && <> · {fmt(t.leitura_colunas, { c: pr.colunas.join(", ") })}</>}
          </p>
        )}
        <Trechos trechos={pr.trechos} />
        {pr.campos_cpc05_18.length > 0 && (
          <details className="detalhes">
            <summary>{t.leitura_campos}</summary>
            <Trechos trechos={pr.campos_cpc05_18} />
          </details>
        )}
        {pr.condicoes_de_mercado.length > 0 && (
          <div className="grupo-trechos">
            <h5>{t.leitura_condicoes}</h5>
            <Trechos trechos={pr.condicoes_de_mercado} />
            <p className="discreto">{pr.nota_condicoes}</p>
          </div>
        )}
        <h4>{t.leitura_risco}</h4>
        {rs.motivo && <p className="discreto">{frase(rs.motivo)}</p>}
        <Trechos trechos={rs.trechos} />
        {rs.nota && <p>{rs.nota}</p>}
      </section>

      <section className="cartao" aria-labelledby="titulo-leitura-relatorio">
        <h3 id="titulo-leitura-relatorio">{t.leitura_relatorio}</h3>
        {rel.motivo && <p className="discreto">{frase(rel.motivo)}</p>}
        {rel.tipo && (
          <p>
            {t.leitura_tipo}: {t.tipos_opiniao[rel.tipo] ?? rel.tipo}
          </p>
        )}
        <Trechos trechos={rel.trechos} />
      </section>

      <section className="cartao" aria-labelledby="titulo-leitura-formulario">
        <h3 id="titulo-leitura-formulario">{t.leitura_formulario}</h3>
        {fd?.versao != null && fd.dt_receb && (fre.status === "disponivel" || fre.status === "sem_linhas") && (
          <p className="discreto">{fmt(t.leitura_fre_doc, { a: fre.ano_formulario ?? "—", v: fd.versao, d: fdata(fd.dt_receb, idioma) })}</p>
        )}
        {textoFre.length > 0 && <p>{textoFre.join(" ")}</p>}
        {fre.linhas.length > 0 && (
          <div className="tabela" tabIndex={0} role="region" aria-label={t.leitura_formulario}>
            <table>
              <thead>
                <tr>
                  <th scope="col">{t.col_parte}</th>
                  <th scope="col">{t.col_relacao}</th>
                  <th scope="col">{t.col_objeto}</th>
                  <th scope="col">{t.col_montante}</th>
                  <th scope="col">{t.col_saldo}</th>
                  <th scope="col">{t.col_data}</th>
                </tr>
              </thead>
              <tbody>
                {fre.linhas.map((x, k) => (
                  <tr key={k}>
                    <td className={x.parte_omitida ? "trecho-omitido" : undefined}>{x.parte}</td>
                    <td lang="pt">{x.relacao ?? "—"}</td>
                    <td lang="pt">{x.objeto ?? "—"}</td>
                    <td>{comMenos(x.montante)}</td>
                    <td>{comMenos(x.saldo)}</td>
                    <td>{x.data_transacao ?? "—"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>

      {limites.length > 0 && (
        <div className="limites-leitura">
          <h3>{t.leitura_limites}</h3>
          <ul>
            {limites.map((x, k) => (
              <li key={k}>{x}</li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
