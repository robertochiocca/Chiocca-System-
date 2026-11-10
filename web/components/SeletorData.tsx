"use client";

// Seletor da data de referência, limitado ao intervalo do contrato (30/04/2011 a 31/12/2024).
import { DATA_MAXIMA, DATA_MINIMA, dataValida } from "@/lib/limites.mjs";
import type { Textos } from "@/lib/textos";

export default function SeletorData({ valor, mudar, t }: { valor: string; mudar: (d: string) => void; t: Textos }) {
  return (
    <label className="campo">
      <span className="rotulo">{t.data_referencia}</span>
      <input type="date" min={DATA_MINIMA} max={DATA_MAXIMA} value={valor} onChange={(e) => mudar(e.target.value)} required />
      <span className="discreto">{dataValida(valor) ? t.data_ajuda : t.data_invalida}</span>
    </label>
  );
}

/** Na demonstração estática, o seletor só oferece as datas pré-geradas da companhia, e a tela diz isso. */
export function SeletorDataEstatico({
  datas,
  valor,
  mudar,
  t,
  idioma,
}: {
  datas: string[];
  valor: string;
  mudar: (d: string) => void;
  t: Textos;
  idioma: "pt" | "en";
}) {
  const formata = (d: string) => (idioma === "pt" ? d.split("-").reverse().join("/") : d);
  return (
    <label className="campo">
      <span className="rotulo">{t.data_referencia}</span>
      <select value={valor} onChange={(e) => mudar(e.target.value)}>
        {datas.map((d) => (
          <option key={d} value={d}>
            {formata(d)}
          </option>
        ))}
      </select>
      <span className="discreto">{t.estatico_datas}</span>
    </label>
  );
}
