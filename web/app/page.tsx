"use client";

// Busca: só por nome, código CVM ou CNPJ, na data de referência. O resultado vem da API em ordem alfabética e é
// mostrado na mesma ordem, sem nenhum sinal: nenhuma lista de empresas é ordenada por alerta, percentil ou escore.
import Link from "next/link";
import { useState } from "react";
import SeletorData from "@/components/SeletorData";
import { api, FalhaApi, MODO_ESTATICO } from "@/lib/api";
import { inteiro } from "@/lib/formato";
import { useIdioma } from "@/lib/idioma";
import { DATA_MAXIMA, dataValida } from "@/lib/limites.mjs";
import { fmt } from "@/lib/textos";
import type { Busca } from "@/lib/tipos";

export default function PaginaBusca() {
  const { idioma, t } = useIdioma();
  const [busca, setBusca] = useState("");
  const [data, setData] = useState(DATA_MAXIMA);
  const [r, setR] = useState<Busca | null>(null);
  const [erro, setErro] = useState<string | null>(null);
  const [carregando, setCarregando] = useState(false);

  async function buscar(e: React.FormEvent) {
    e.preventDefault();
    if (!dataValida(data)) return setErro(t.data_invalida);
    setCarregando(true);
    setErro(null);
    try {
      setR(await api.buscar(busca, data));
    } catch (x) {
      setR(null);
      setErro(x instanceof FalhaApi ? x.message : t.erro);
    } finally {
      setCarregando(false);
    }
  }

  return (
    <>
      <h1>{t.busca_titulo}</h1>
      <p className="rotulo">{t.busca_ajuda}</p>
      <form className="form cartao" onSubmit={buscar} role="search">
        <label className="campo">
          <span className="rotulo">{t.busca_campo}</span>
          <input value={busca} onChange={(e) => setBusca(e.target.value)} required minLength={1} maxLength={120} />
        </label>
        {!MODO_ESTATICO && <SeletorData valor={data} mudar={setData} t={t} />}
        <button className="botao" type="submit" disabled={carregando}>
          {t.busca_botao}
        </button>
      </form>
      {carregando && <p className="discreto">{t.carregando}</p>}
      {erro && <p className="erro">{erro}</p>}
      {r && (
        <section className="cartao">
          <p className="rotulo">{r.total ? fmt(t.resultados, { n: inteiro(r.total, idioma) }) : t.nenhum_resultado}</p>
          <ul className="lista">
            {r.resultados.map((e) => (
              <li key={e.cd_cvm}>
                <Link href={MODO_ESTATICO ? `/empresa?cd=${e.cd_cvm}` : `/empresa?cd=${e.cd_cvm}&data=${r.data_referencia}`}>{e.denominacao}</Link>
                <div className="discreto">
                  {t.codigo_cvm} {e.cd_cvm} · {t.cnpj} {e.cnpj ?? "—"}
                  {e.codigos_negociacao.length > 0 && ` · ${e.codigos_negociacao.map((c) => c.codigo).join(", ")}`}
                </div>
              </li>
            ))}
          </ul>
        </section>
      )}
    </>
  );
}
