"use client";

// Fatos relevantes e comunicados ao mercado entregues até a data (Fase F2a), dentro de "O que se sabia na data": só os
// metadados do IPE (data de entrega, assunto e link); o conteúdo dos documentos não é baixado, lido nem resumido. Sem
// poluir a página: uma linha com a contagem de documentos por categoria e as duas listas recolhidas, fatos relevantes
// primeiro, cada uma da entrega mais recente para a mais antiga (a ordem que vem da API). Versões do mesmo documento e
// documentos com a mesma data, categoria e assunto aparecem numa linha só, com um link para cada um (lib/ipe.mjs, o
// mesmo agrupamento do PDF). A tabela só é montada quando a lista é aberta (há companhias com milhares de documentos);
// o endereço com #fatos-relevantes ou #comunicados-ao-mercado abre a lista. Nenhuma palavra do assunto é destacada,
// contada ou usada para alerta, nota ou ordenação. Assunto com possível nome de pessoa vem omitido da API, e o vazio
// nos dados abertos vem com aviso.
import { useEffect, useRef, useState } from "react";
import { data as fdata, inteiro } from "@/lib/formato";
import { linhasIPE, linksDaLinha, marcaDaLinha } from "@/lib/ipe.mjs";
import { useIdioma } from "@/lib/idioma";
import { fmt } from "@/lib/textos";
import type { FatosEComunicados as Fatos, ItemIPE } from "@/lib/tipos";

function Lista({ id, titulo, itens }: { id: string; titulo: string; itens: ItemIPE[] }) {
  const { idioma, t } = useIdioma();
  const [aberta, setAberta] = useState(false);
  const ref = useRef<HTMLDetailsElement>(null);
  useEffect(() => {
    if (ref.current && window.location.hash === `#${id}`) {
      ref.current.open = true;
      setAberta(true);
      ref.current.scrollIntoView();
    }
  }, [id]);
  if (!itens.length) return null;
  return (
    <details id={id} ref={ref} className="detalhes lista-ipe" onToggle={(e) => setAberta((e.currentTarget as HTMLDetailsElement).open)}>
      <summary>{titulo}</summary>
      {aberta && (
        <div className="tabela tabela-ipe" tabIndex={0} role="region" aria-label={titulo}>
          <table>
            <thead>
              <tr>
                <th scope="col">{t.ipe_col_data}</th>
                <th scope="col">{t.ipe_col_assunto}</th>
                <th scope="col">{t.ipe_col_documento}</th>
              </tr>
            </thead>
            <tbody>
              {linhasIPE(itens).map((grupo) => {
                const x = grupo[0];
                const marca = marcaDaLinha(grupo, t);
                const links = linksDaLinha(grupo).filter((y) => y.link);
                return (
                  <tr key={x.id_documento}>
                    <td className="nowrap">{fdata(x.data_entrega, idioma)}</td>
                    <td lang="pt" className={x.assunto_omitido || x.assunto_vazio ? "trecho-omitido" : undefined}>
                      {x.assunto}
                      {marca && <span className="discreto"> · {marca}</span>}
                    </td>
                    <td className="nowrap">
                      {links.length === 0 && "—"}
                      {links.length === 1 && (
                        <a href={links[0].link ?? undefined} rel="noopener noreferrer" target="_blank">
                          {t.ipe_ver}
                        </a>
                      )}
                      {links.length > 1 && (
                        <>
                          {t.ipe_ver}:{" "}
                          {links.map((y, k) => (
                            <span key={y.id_documento}>
                              {k > 0 && ", "}
                              <a href={y.link ?? undefined} rel="noopener noreferrer" target="_blank" aria-label={`${t.ipe_ver} ${k + 1}`}>
                                {k + 1}
                              </a>
                            </span>
                          ))}
                        </>
                      )}
                      {grupo.some((y) => y.link_pode_nao_abrir) && <div className="discreto aviso-link">{t.ipe_link_antigo}</div>}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </details>
  );
}

export default function FatosEComunicados({ fc }: { fc: Fatos }) {
  const { idioma, t } = useIdioma();
  const fatos = fc.itens.filter((x) => x.categoria === "fato_relevante");
  const comunicados = fc.itens.filter((x) => x.categoria === "comunicado_ao_mercado");
  return (
    <div className="fatos-e-comunicados">
      <h4>{t.ipe_titulo}</h4>
      {fc.itens.length ? (
        <p>
          {fmt(t.ipe_resumo, {
            f: inteiro(fc.contagem.fato_relevante ?? 0, idioma),
            c: inteiro(fc.contagem.comunicado_ao_mercado ?? 0, idioma),
          })}
        </p>
      ) : (
        <p>{fc.motivo}</p>
      )}
      <Lista id="fatos-relevantes" titulo={fmt(t.ipe_fatos, { n: inteiro(fatos.length, idioma) })} itens={fatos} />
      <Lista id="comunicados-ao-mercado" titulo={fmt(t.ipe_comunicados, { n: inteiro(comunicados.length, idioma) })} itens={comunicados} />
      <p className="discreto">{fc.nota}</p>
    </div>
  );
}
