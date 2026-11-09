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
