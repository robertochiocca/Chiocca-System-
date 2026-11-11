"use client";

// Página inicial (Fase E2): o que o Chiocca faz e o que quer dizer "como era numa data"; a nota da demonstração; a
// busca (só por nome, código CVM ou CNPJ, em ordem alfabética, sem nenhum sinal); "Comece por aqui", com três
// cartões; e as companhias da demonstração em ordem alfabética, com o caso público e nunca o resultado dos sinais.
// Os números vêm dos JSONs (rota da demonstração e "Como o motor foi testado").
import Link from "next/link";
import { useEffect, useState } from "react";
import SeletorData from "@/components/SeletorData";
import { api, FalhaApi, MODO_ESTATICO } from "@/lib/api";
import { bilhoes, data as fdata, inteiro } from "@/lib/formato";
import { useIdioma } from "@/lib/idioma";
import { DATA_MAXIMA, dataValida } from "@/lib/limites.mjs";
import { fmt, TIPOS_DE_CASO } from "@/lib/textos";
import type { Busca, ComoTestado, Demonstracao, EmpresaDaDemonstracao } from "@/lib/tipos";

const PRIMEIRAS = 10;

function LinhaDaLista({ e }: { e: EmpresaDaDemonstracao }) {
  const { idioma, t } = useIdioma();
  return (
    <li className="linha-companhia">
      <Link href={`/empresa?cd=${e.cd_cvm}`}>{e.denominacao ?? e.cd_cvm}</Link>
      <span className="casos-da-linha">
        {e.casos.map((c) => (
          <span key={c.caso_id} className="caso-da-linha">
            <span>{c.tipo_evento.map((x) => TIPOS_DE_CASO[idioma][x] ?? x).join(" · ")}</span>
            <span className="discreto">
              {t.data_publica}: {c.data_publica ? fdata(c.data_publica, idioma) : t.sem_data_publica}
            </span>
          </span>
        ))}
      </span>
    </li>
  );
}

export default function PaginaInicial() {
  const { idioma, t } = useIdioma();
  const [busca, setBusca] = useState("");
  const [data, setData] = useState(DATA_MAXIMA);
  const [r, setR] = useState<Busca | null>(null);
  const [erro, setErro] = useState<string | null>(null);
  const [carregando, setCarregando] = useState(false);
  const [demo, setDemo] = useState<Demonstracao | null>(null);
  const [testado, setTestado] = useState<ComoTestado | null>(null);
  const [todas, setTodas] = useState(false);

  useEffect(() => {
    api.demonstracao().then(setDemo).catch(() => setDemo(null));
    api.comoTestado().then(setTestado).catch(() => setTestado(null));
  }, []);

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

  const d = demo?.destaques;
  const empresas = demo?.empresas ?? [];
  const visiveis = todas ? empresas : empresas.slice(0, PRIMEIRAS);
  return (
    <>
      <section className="abertura">
        <h1>{t.busca_titulo}</h1>
        <p>{t.home_p1}</p>
        <p>{t.home_p2}</p>
        {(MODO_ESTATICO || demo) && empresas.length > 0 && (
          <p className="nota-demo">{fmt(t.home_nota_demo, { n: inteiro(empresas.length, idioma) })}</p>
        )}
      </section>

      <section className="cartao cartao-busca" aria-labelledby="titulo-busca">
        <h2 id="titulo-busca">{t.busca_cartao}</h2>
        <form className="form" onSubmit={buscar} role="search">
          <label className="campo">
            <span className="rotulo">{t.busca_campo}</span>
            <input value={busca} onChange={(e) => setBusca(e.target.value)} required minLength={1} maxLength={120} />
          </label>
          {!MODO_ESTATICO && <SeletorData valor={data} mudar={setData} t={t} />}
          <button className="botao" type="submit" disabled={carregando}>
            {t.busca_botao}
          </button>
        </form>
        <p className="discreto">{t.busca_nota}</p>
        {carregando && <p className="discreto">{t.carregando}</p>}
        {erro && <p className="erro">{erro}</p>}
        {r && (
          <div className="resultados" aria-live="polite">
            <p className="rotulo">
              {r.total === 0 ? t.nenhum_resultado : r.total === 1 ? t.resultados_1 : fmt(t.resultados, { n: inteiro(r.total, idioma) })}
            </p>
            <ul className="lista">
              {r.resultados.map((e) => (
                <li key={e.cd_cvm}>
                  <Link href={MODO_ESTATICO ? `/empresa?cd=${e.cd_cvm}` : `/empresa?cd=${e.cd_cvm}&data=${r.data_referencia}`}>
                    {e.denominacao}
                  </Link>
                  <div className="discreto">
                    {t.codigo_cvm} {e.cd_cvm} · {t.cnpj} {e.cnpj ?? "—"}
                    {e.codigos_negociacao.length > 0 && ` · ${e.codigos_negociacao.map((c) => c.codigo).join(", ")}`}
                  </div>
                </li>
              ))}
            </ul>
          </div>
        )}
      </section>

      {d && (
        <section aria-labelledby="titulo-comece">
          <h2 id="titulo-comece">{t.comece}</h2>
          <div className="grade grade-tres">
            <article className="cartao cartao-comece">
              <h3>{t.epoca_titulo}</h3>
              <p>{fmt(t.epoca_txt, { nome: d.denominacao_na_epoca ?? d.cd_cvm, ex: d.exercicio, d: fdata(d.na_epoca, idioma) })}</p>
              <p className="discreto">{t.epoca_nota}</p>
              <Link className="botao leve" href={`/investigacao?cd=${d.cd_cvm}&ex=${d.exercicio}&data=${d.na_epoca}`}>
                {t.abrir_investigacao}
              </Link>
            </article>
            <article className="cartao cartao-comece">
              <h3>{t.depois_titulo}</h3>
              <p>
                {fmt(t.depois_txt, {
                  d: fdata(d.depois, idioma),
                  ex: d.exercicio,
                  a: bilhoes(d.patrimonio_liquido.valor, idioma),
                  b: bilhoes(d.patrimonio_liquido.valor_comparativo, idioma),
                })}
              </p>
              <Link className="botao leve" href={`/investigacao?cd=${d.cd_cvm}&ex=${d.exercicio}&data=${d.depois}`}>
                {t.abrir_investigacao}
              </Link>
            </article>
            {testado && (
              <article className="cartao cartao-comece">
                <h3>{t.testado_card_titulo}</h3>
                <p>
                  {fmt(t.testado_card_txt, { a: inteiro(testado.acerto.acertados, idioma), n: inteiro(testado.acerto.acertaveis, idioma) })}
                </p>
                <Link className="botao leve" href="/como-o-motor-foi-testado">
                  {t.ver_como_testado}
                </Link>
              </article>
            )}
          </div>
        </section>
      )}

      {empresas.length > 0 && (
        <section aria-labelledby="titulo-lista">
          <h2 id="titulo-lista">{t.lista_titulo}</h2>
          <p className="discreto">{t.lista_nota}</p>
          <ul id="lista-companhias" className="lista cartao lista-companhias">
            {visiveis.map((e) => (
              <LinhaDaLista key={e.cd_cvm} e={e} />
            ))}
          </ul>
          {empresas.length > PRIMEIRAS && (
            <button type="button" className="botao leve" aria-expanded={todas} aria-controls="lista-companhias" onClick={() => setTodas(!todas)}>
              {todas
                ? fmt(t.lista_ver_menos, { n: inteiro(PRIMEIRAS, idioma) })
                : fmt(t.lista_ver_todas, { n: inteiro(empresas.length, idioma) })}
            </button>
          )}
        </section>
      )}
    </>
  );
}
