"use client";

// Evidência clicável: as linhas da DFP que entram num número, com documento, versão, conta, valor e localização.
import { useState } from "react";
import type { Evidencia, Idioma } from "@/lib/tipos";
import { data, decimal, inteiro } from "@/lib/formato";
import { fmt, type Textos } from "@/lib/textos";

export default function Evidencias({
  ids,
  todas,
  idioma,
  t,
}: {
  ids: string[];
  todas: Record<string, Evidencia>;
  idioma: Idioma;
  t: Textos;
}) {
  const [aberto, setAberto] = useState(false);
  const lista = ids.map((i) => todas[i]).filter(Boolean);
  if (!lista.length) return null;
  return (
    <div className={aberto ? "evidencias-abertas" : undefined}>
      <button className="botao leve" onClick={() => setAberto(!aberto)} aria-expanded={aberto}>
        {aberto ? t.esconder_evidencias : fmt(t.ver_evidencias, { n: inteiro(lista.length, idioma) })}
      </button>
      {aberto && (
        <div className="tabela" tabIndex={0} role="region" aria-label={fmt(t.ver_evidencias, { n: inteiro(lista.length, idioma) })}>
          <table>
            <thead>
              <tr>
                <th>{t.conta}</th>
                <th>{t.coluna}</th>
                <th>{t.valor}</th>
                <th>{t.documento_usado}</th>
                <th>{t.arquivo}</th>
              </tr>
            </thead>
            <tbody>
              {lista.map((e) => (
                <tr key={e.id}>
                  <td>
                    {t.demonstracoes[e.demonstracao] ?? e.demonstracao} {e.cd_conta} {e.ds_conta}
                  </td>
                  <td>{t.colunas[e.coluna] ?? e.coluna}</td>
                  <td>{decimal(e.valor, idioma, 0)}</td>
                  <td>
                    {e.documento.tipo} {t.versao} {e.documento.versao}, {t.entregue_em} {data(e.documento.dt_receb, idioma)}
                    {e.documento.url && (
                      <>
                        {" "}
                        <a href={e.documento.url} rel="noopener noreferrer" target="_blank">
                          ↗
                        </a>
                      </>
                    )}
                  </td>
                  <td className="mono">
                    {e.localizacao?.arquivo ?? "—"}
                    {e.localizacao?.linha ? `, ${t.linha} ${e.localizacao.linha}` : ""}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
