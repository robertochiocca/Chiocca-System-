"use client";

// Fatos relevantes e comunicados ao mercado entregues até a data (Fase F2a), dentro de "O que se sabia na data": só os
// metadados do IPE (data de entrega, assunto e link); o conteúdo dos documentos não é baixado, lido nem resumido. Sem
// poluir a página: uma linha com a contagem por categoria e as duas listas recolhidas, fatos relevantes primeiro, cada
// uma da entrega mais recente para a mais antiga (a ordem que vem da API). A tabela só é montada quando a lista é
// aberta (há companhias com milhares de comunicados). Nenhuma palavra do assunto é destacada, contada ou usada para
// alerta, nota ou ordenação. Assunto com possível nome de pessoa vem omitido da API.
import { useState } from "react";
import { data as fdata, inteiro } from "@/lib/formato";
import { useIdioma } from "@/lib/idioma";
import { fmt } from "@/lib/textos";
import type { FatosEComunicados as Fatos, ItemIPE } from "@/lib/tipos";

function Lista({ titulo, itens }: { titulo: string; itens: ItemIPE[] }) {
  const { idioma, t } = useIdioma();
  const [aberta, setAberta] = useState(false);
  if (!itens.length) return null;
  return (
    <details className="detalhes lista-ipe" onToggle={(e) => setAberta((e.currentTarget as HTMLDetailsElement).open)}>
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
              {itens.map((x) => (
                <tr key={x.id_documento}>
                  <td className="nowrap">{fdata(x.data_entrega, idioma)}</td>
                  <td lang="pt" className={x.assunto_omitido ? "trecho-omitido" : undefined}>
                    {x.assunto}
                    {(x.versao ?? 1) > 1 && <span className="discreto"> · {fmt(t.ipe_versao, { v: x.versao ?? 1 })}</span>}
                  </td>
                  <td>
                    {x.link ? (
                      <a href={x.link} rel="noopener noreferrer" target="_blank">
                        {t.ipe_ver}
                      </a>
                    ) : (
                      "—"
                    )}
                  </td>
                </tr>
              ))}
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
      <Lista titulo={fmt(t.ipe_fatos, { n: inteiro(fatos.length, idioma) })} itens={fatos} />
      <Lista titulo={fmt(t.ipe_comunicados, { n: inteiro(comunicados.length, idioma) })} itens={comunicados} />
      <p className="discreto">{fc.nota}</p>
    </div>
  );
}
