// "Informação de hoje (fora da data de referência)": separada da visão "como era", no fim, como no PDF. É o único
// lugar onde aparece o nome de hoje da companhia (Fase E2).
import type { InformacaoDeHoje as Tipo } from "@/lib/tipos";
import type { Textos } from "@/lib/textos";

export default function InformacaoDeHoje({ h, t }: { h: Tipo; t: Textos }) {
  return (
    <section id="hoje" className="hoje secao" aria-labelledby="titulo-hoje">
      <h2 id="titulo-hoje">{h.titulo}</h2>
      <p className="discreto">{t.informacao_hoje_nota}</p>
      {h.denominacao && (
        <p>
          {t.nome_hoje}: {h.denominacao}
        </p>
      )}
      <p>
        {t.situacao_cadastro}: {h.situacao_cadastro ?? "—"}
      </p>
      <p className="discreto">
        {t.fonte}: {h.fonte}
      </p>
    </section>
  );
}
