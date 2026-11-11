"use client";

// Seção "Notas explicativas" da investigação (Fase F1): trechos copiados das notas explicativas e do relatório do
// auditor, com a página, e a tabela do Formulário de Referência. É só fato: nenhum selo, alerta, nota ou ordenação.
// Trecho com nome de pessoa física aparece como "trecho omitido; ver página N do documento". Na interface em inglês,
// os trechos ficam em português, marcados como "original excerpt in Portuguese". Só aparece quando a investigação
// traz a seção (o leitor só entra depois de passar nas metas do pré-registro, docs/pre-registro-leitor.md).
import { data as fdata } from "@/lib/formato";
import { useIdioma } from "@/lib/idioma";
import { fmt } from "@/lib/textos";
import type { LeituraDocumental as Leitura, TrechoLido } from "@/lib/tipos";

function Trecho({ x }: { x: TrechoLido }) {
  const { idioma, t } = useIdioma();
  const onde = x.pagina !== null ? fmt(t.leitura_pagina, { p: x.pagina }) : null;
  if (x.omitido) {
    return <p className="trecho-omitido">{x.aviso_omissao}</p>;
  }
  return (
    <figure className="trecho">
      <blockquote lang="pt">“{x.texto}”</blockquote>
      <figcaption className="discreto">
        {[onde, x.negacao ? t.leitura_negativa : null, x.cortado ? t.leitura_cortado : null, idioma === "en" ? t.leitura_original : null]
          .filter(Boolean)
          .join(" · ")}
      </figcaption>
    </figure>
  );
}

function PorRotulo({ trechos }: { trechos: TrechoLido[] }) {
  const { t } = useIdioma();
  const grupos = new Map<string, TrechoLido[]>();
  for (const x of trechos) grupos.set(x.rotulo ?? "", [...(grupos.get(x.rotulo ?? "") ?? []), x]);
  return (
    <>
      {[...grupos.entries()].map(([rotulo, xs]) => (
        <div key={rotulo} className="grupo-trechos">
          {rotulo && <h4>{t.rotulos_leitura[rotulo] ?? rotulo}</h4>}
          {xs.map((x, k) => (
            <Trecho key={k} x={x} />
          ))}
        </div>
      ))}
    </>
  );
}

export default function LeituraDocumental({ l }: { l: Leitura }) {
  const { idioma, t } = useIdioma();
  const pr = l.partes_relacionadas;
  const rs = l.risco_sacado;
  const rel = l.relatorio_do_auditor;
  const fre = l.formulario_de_referencia;
  const doc = l.documento;
  return (
    <div className="leitura">
      <p className="discreto">{l.nota}</p>
      {doc && doc.num_doc && (
        <p className="discreto">
          {t.leitura_documento}: DFP · {fmt(t.leitura_versao, { v: doc.versao ?? "—", d: fdata(doc.dt_receb, idioma) })}
        </p>
      )}

      <section className="cartao" aria-labelledby="titulo-leitura-partes">
        <h3 id="titulo-leitura-partes">{t.leitura_partes}</h3>
        {pr.motivo && <p className="discreto">{pr.motivo}</p>}
        {pr.nota && (
          <p>
            {t.leitura_nota}: {pr.nota.titulo} ({fmt(t.leitura_paginas, { a: pr.nota.paginas[0], b: pr.nota.paginas[1] })})
            {pr.colunas.length > 0 && <> · {fmt(t.leitura_colunas, { c: pr.colunas.join(", ") })}</>}
          </p>
        )}
        <PorRotulo trechos={pr.trechos} />
        {pr.campos_cpc05_18.length > 0 && (
          <details className="detalhes">
            <summary>{t.leitura_campos}</summary>
            <PorRotulo trechos={pr.campos_cpc05_18} />
          </details>
        )}
        {pr.condicoes_de_mercado.length > 0 && (
          <div className="grupo-trechos">
            <h4>{t.leitura_condicoes}</h4>
            {pr.condicoes_de_mercado.map((x, k) => (
              <Trecho key={k} x={x} />
            ))}
            <p className="discreto">{pr.nota_condicoes}</p>
          </div>
        )}
      </section>

      <section className="cartao" aria-labelledby="titulo-leitura-risco">
        <h3 id="titulo-leitura-risco">{t.leitura_risco}</h3>
        {rs.motivo && <p className="discreto">{rs.motivo}</p>}
        {rs.trechos.map((x, k) => (
          <Trecho key={k} x={x} />
        ))}
        {rs.nota && <p>{rs.nota}</p>}
      </section>

      <section className="cartao" aria-labelledby="titulo-leitura-relatorio">
        <h3 id="titulo-leitura-relatorio">{t.leitura_relatorio}</h3>
        {rel.motivo && <p className="discreto">{rel.motivo}</p>}
        {rel.tipo && (
          <p>
            {t.leitura_tipo}: {t.tipos_opiniao[rel.tipo] ?? rel.tipo}
          </p>
        )}
        <PorRotulo trechos={rel.trechos} />
      </section>

      <section className="cartao" aria-labelledby="titulo-leitura-formulario">
        <h3 id="titulo-leitura-formulario">{t.leitura_formulario}</h3>
        {fre.motivo && <p className="discreto">{fre.motivo}</p>}
        {fre.documento?.linhagem && (
          <p className="discreto">
            {fre.ano_formulario} · {fmt(t.leitura_versao, { v: fre.documento.versao ?? "—", d: fdata(fre.documento.dt_receb, idioma) })} ·{" "}
            {fre.documento.linhagem}
          </p>
        )}
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
                    <td>{x.montante ?? "—"}</td>
                    <td>{x.saldo ?? "—"}</td>
                    <td>{x.data_transacao ?? "—"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </div>
  );
}
