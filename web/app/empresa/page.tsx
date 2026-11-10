"use client";

// A empresa na data: nome da época, setor, grupo, códigos de negociação e os exercícios com DFP entregue até a data
// (só até o lacre, 2023). A situação no cadastro de hoje fica numa seção separada, no fim. Na demonstração estática,
// o seletor só oferece as datas pré-geradas e a lista só traz os exercícios gerados para a data.
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { Suspense, useEffect, useState } from "react";
import InformacaoDeHoje from "@/components/InformacaoDeHoje";
import SeletorData, { SeletorDataEstatico } from "@/components/SeletorData";
import { api, FalhaApi, MODO_ESTATICO } from "@/lib/api";
import { data as fdata } from "@/lib/formato";
import { useIdioma } from "@/lib/idioma";
import { DATA_MAXIMA, dataValida } from "@/lib/limites.mjs";
import type { EmpresaNaData } from "@/lib/tipos";

function Empresa() {
  const { idioma, t } = useIdioma();
  const p = useSearchParams();
  const router = useRouter();
  const cd = p.get("cd") ?? "";
  const [datasDemo, setDatasDemo] = useState<Record<string, number[]> | null>(null);
  const datas = datasDemo ? Object.keys(datasDemo) : []; // o índice já traz as datas em ordem cronológica
  const data = p.get("data") ?? (MODO_ESTATICO ? datas[datas.length - 1] ?? "" : DATA_MAXIMA);
  const [r, setR] = useState<EmpresaNaData | null>(null);
  const [erro, setErro] = useState<string | null>(null);

  useEffect(() => {
    if (MODO_ESTATICO) api.datasDemo(cd).then((d) => (d ? setDatasDemo(d) : setErro(t.estatico_sem_arquivo))).catch(() => setErro(t.erro));
  }, [cd, t]);

  useEffect(() => {
    if (!/^\d{1,6}$/.test(cd)) return setErro(t.erro);
    if (MODO_ESTATICO && !data) return;
    if (!dataValida(data)) return setErro(t.data_invalida);
    setR(null);
    setErro(null);
    api
      .empresa(cd, data, idioma)
      .then(setR)
      .catch((x) => setErro(x instanceof FalhaApi ? x.message : t.erro));
  }, [cd, data, idioma, t]);

  if (erro) return <p className="erro">{erro}</p>;
  if (!r) return <p className="discreto">{t.carregando}</p>;
  const e = r.empresa;
  const exercicios = MODO_ESTATICO && datasDemo ? datasDemo[r.data_referencia] ?? [] : r.exercicios;
  const irPara = (d: string) => dataValida(d) && router.push(`/empresa?cd=${cd}&data=${d}`);
  return (
    <>
      <p>
        <Link href="/">← {t.voltar}</Link>
      </p>
      <h1>{e.denominacao}</h1>
      <p className="discreto">{e.origem_denominacao === "fca" ? t.nome_da_epoca : t.nome_do_indice}</p>
      <section className="cartao">
        <p>
          {t.codigo_cvm} {e.cd_cvm} · {t.cnpj} {e.cnpj ?? "—"}
        </p>
        <p>
          {t.setor}: {e.setor ?? "—"} · {t.grupo}: {e.grupo ? t.grupos[e.grupo] : "—"}
        </p>
        <p>
          {t.codigos_negociacao}:{" "}
          {e.codigos_negociacao.length
            ? e.codigos_negociacao.map((c) => `${c.codigo} (${c.valor_mobiliario ?? "—"})`).join(", ")
            : e.motivo_codigos_negociacao}
        </p>
      </section>
      <section className="cartao form">
        {MODO_ESTATICO ? (
          <SeletorDataEstatico datas={datas} valor={r.data_referencia} mudar={irPara} t={t} idioma={idioma} />
        ) : (
          <SeletorData valor={data} mudar={irPara} t={t} />
        )}
      </section>
      <h2>{t.exercicios}</h2>
      <p className="discreto">{fdata(r.data_referencia, idioma)}</p>
      <ul className="lista cartao">
        {exercicios
          .slice()
          .reverse()
          .map((ex) => (
            <li key={ex}>
              {t.exercicio} {ex} · <Link href={`/investigacao?cd=${e.cd_cvm}&ex=${ex}&data=${r.data_referencia}`}>{t.investigar}</Link>
            </li>
          ))}
      </ul>
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
