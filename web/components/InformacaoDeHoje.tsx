// "Informação de hoje (fora da data de referência)": separada da visão "como era", no fim, como no PDF.
import type { InformacaoDeHoje as Tipo } from "@/lib/tipos";
import type { Textos } from "@/lib/textos";

export default function InformacaoDeHoje({ h, t }: { h: Tipo; t: Textos }) {
  return (
    <section className="hoje" aria-label={h.titulo}>
      <h2 style={{ marginTop: 0 }}>{h.titulo}</h2>
      <p className="discreto">{t.informacao_hoje_nota}</p>
      <p>
        {t.situacao_cadastro}: {h.situacao_cadastro ?? "—"}
      </p>
      <p className="discreto">
        {t.fonte}: {h.fonte}
      </p>
    </section>
  );
}
