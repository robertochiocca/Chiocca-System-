"use client";

// A empresa na data (Fase E2): caminho, nome na data, "como era em", histórico de nome dos FCA, datas como botões com
// rótulo (na demonstração, a data inicial é a do primeiro exercício do período afetado do caso), o caso do gabarito,
// os exercícios com DFP entregue até a data e os dados da companhia. A situação e o nome de hoje ficam numa seção
// separada, no fim.
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { Suspense, useEffect, useState } from "react";
import CabecalhoEmpresa from "@/components/CabecalhoEmpresa";
import InformacaoDeHoje from "@/components/InformacaoDeHoje";
import { CartaoCaso } from "@/components/Resumo";
import { api, FalhaApi, MODO_ESTATICO } from "@/lib/api";
import { useIdioma } from "@/lib/idioma";
import { DATA_MAXIMA, dataValida } from "@/lib/limites.mjs";
import type { Demonstracao, EmpresaNaData } from "@/lib/tipos";

function Empresa() {
  const { idioma, t } = useIdioma();
  const p = useSearchParams();
  const cd = p.get("cd") ?? "";
  // undefined: ainda carregando; null: sem dados da demonstração
  const [demo, setDemo] = useState<Demonstracao | null | undefined>(undefined);
  const [r, setR] = useState<EmpresaNaData | null>(null);
  const [erro, setErro] = useState<string | null>(null);

  useEffect(() => {
    api
      .demonstracao()
      .then(setDemo)
      .catch(() => setDemo(null));
  }, []);

  const entrada = demo?.empresas.find((e) => e.cd_cvm === cd) ?? null;
  const datas = entrada ? Object.keys(entrada.datas) : []; // a rota já traz as datas em ordem cronológica
  // Na demonstração estática, espera a lista para saber a data inicial; na API completa, não espera.
  const data = p.get("data") ?? (entrada ? entrada.data_inicial : MODO_ESTATICO ? "" : DATA_MAXIMA);

  useEffect(() => {
    if (!/^\d{1,6}$/.test(cd)) return setErro(t.erro);
    if (MODO_ESTATICO && demo === undefined) return;
    if (MODO_ESTATICO && !entrada) return setErro(t.estatico_sem_arquivo);
    if (!dataValida(data)) return setErro(t.data_invalida);
    setR(null);
    setErro(null);
    api
      .empresa(cd, data, idioma)
      .then(setR)
      .catch((x) => setErro(x instanceof FalhaApi ? x.message : t.erro));
  }, [cd, data, idioma, t, demo, entrada]);

  if (erro) return <p className="erro">{erro}</p>;
  if (!r) return <p className="discreto">{t.carregando}</p>;
  const e = r.empresa;
  const exercicios = MODO_ESTATICO && entrada ? (entrada.datas[r.data_referencia] ?? []) : r.exercicios;
  return (
    <>
      <CabecalhoEmpresa
        empresa={e}
        data={r.data_referencia}
        datas={datas}
        rotulos={entrada?.rotulos_datas ?? {}}
        href={(d) => `/empresa?cd=${cd}&data=${d}`}
      />
      {MODO_ESTATICO && <p className="discreto">{t.estatico_datas}</p>}
      <section className="secao" aria-labelledby="titulo-exercicios">
        <h2 id="titulo-exercicios">{t.exercicios_na_data}</h2>
        <ul className="lista cartao">
          {exercicios
            .slice()
            .reverse()
            .map((ex) => (
              <li key={ex} className="linha-exercicio">
                <span>
                  {t.exercicio} {ex}
                </span>
                <Link className="botao" href={`/investigacao?cd=${e.cd_cvm}&ex=${ex}&data=${r.data_referencia}`}>
                  {t.investigar}
                </Link>
              </li>
            ))}
        </ul>
      </section>
      {entrada && entrada.casos.length > 0 && <CartaoCaso casos={entrada.casos} />}
      <section className="cartao" aria-label={t.companhia}>
        <p>
          {t.codigo_cvm} {e.cd_cvm} · {t.cnpj} {e.cnpj ?? "—"}
        </p>
        <p>
          {t.setor}: {e.setor ?? "—"} · {t.grupo}: {e.grupo ? t.grupos[e.grupo] : "—"}
        </p>
        <p className="discreto">{e.origem_denominacao === "fca" ? t.nome_da_epoca : t.nome_do_indice}</p>
        <p>
          {t.codigos_negociacao}:{" "}
          {e.codigos_negociacao.length
            ? e.codigos_negociacao.map((c) => `${c.codigo} (${c.valor_mobiliario ?? "—"})`).join(", ")
            : e.motivo_codigos_negociacao}
        </p>
      </section>
      <InformacaoDeHoje h={r.informacao_de_hoje} t={t} />
    </>
  );
}

export default function PaginaEmpresa() {
  return (
    <Suspense>
      <Empresa />
    </Suspense>
  );
}
