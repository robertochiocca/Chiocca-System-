"use client";

// A investigação de uma empresa num exercício, como era na data: o mesmo JSON do contrato (e do PDF), com os
// achados por família (nunca somados), as mudanças, o que se sabia, a qualidade dos dados, parecer e auditor,
// limites e limitações. A "Informação de hoje" fica separada, no fim, como no PDF.
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { Suspense, useEffect, useState } from "react";
import Achado from "@/components/Achado";
import InformacaoDeHoje from "@/components/InformacaoDeHoje";
import TextoComLinks from "@/components/TextoComLinks";
import { api, FalhaApi } from "@/lib/api";
import { data as fdata, inteiro, milhoes } from "@/lib/formato";
import { useIdioma } from "@/lib/idioma";
import { DATA_MAXIMA, dataValida, exercicioValido } from "@/lib/limites.mjs";
import { fmt, REPOSITORIO, type Textos } from "@/lib/textos";
import type { Diferenca, Investigacao } from "@/lib/tipos";

const FAMILIAS = ["possivel_manipulacao", "risco_financeiro", "qualidade_financeira"] as const;

function Diferencas({ lista, idioma, t }: { lista: Diferenca[]; idioma: "pt" | "en"; t: Textos }) {
  return (
    <div className="tabela">
      <table>
        <tbody>
          {lista.map((x) => (
            <tr key={`${x.demonstracao}-${x.cd_conta}`}>
              <td>
                ({x.grupo}) {t.demonstracoes[x.demonstracao] ?? x.demonstracao} {x.cd_conta} {x.ds_conta}
              </td>
              <td>{milhoes(x.valor, idioma)}</td>
              <td>{milhoes(x.valor_comparativo, idioma)}</td>
              <td>{milhoes(x.diferenca, idioma)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function Pagina() {
  const { idioma, t } = useIdioma();
  const p = useSearchParams();
  const cd = p.get("cd") ?? "";
  const ex = Number(p.get("ex"));
  const data = p.get("data") ?? DATA_MAXIMA;
  const [inv, setInv] = useState<Investigacao | null>(null);
  const [erro, setErro] = useState<string | null>(null);

  useEffect(() => {
    if (!/^\d{1,6}$/.test(cd) || !exercicioValido(ex)) return setErro(t.erro);
    if (!dataValida(data)) return setErro(t.data_invalida);
    setInv(null);
    setErro(null);
    api
      .investigacao(cd, ex, data, idioma)
      .then(setInv)
      .catch((x) => setErro(x instanceof FalhaApi ? x.message : t.erro));
  }, [cd, ex, data, idioma, t]);

  if (erro) return <p className="erro">{erro}</p>;
  if (!inv) return <p className="discreto">{t.calculando}</p>;
  const e0 = inv.exercicios[0];
  const pa = inv.parecer_e_auditor;
  const mud = inv.mudancas;
  const confs = inv.qualidade_dos_dados.conferencias.filter((c) => c.resultado !== "nao_aplicavel");
  const falhas = confs.filter((c) => c.resultado === "falhou");
  return (
    <>
      <p>
        <Link href={`/empresa?cd=${inv.empresa.cd_cvm}&data=${inv.data_referencia}`}>← {inv.empresa.denominacao}</Link>
      </p>
      <h1>
        {inv.empresa.denominacao} · {t.exercicio} {e0.exercicio} · {fdata(inv.data_referencia, idioma)}
      </h1>
      {mud.comparativo_destacadas.length > 0 && (
        <p className="aviso-topo" role="note">
          {fmt(mud.comparativo_destacadas.length === 1 ? t.aviso_destacada : t.aviso_destacadas, {
            n: inteiro(mud.comparativo_destacadas.length, idioma),
            ex: e0.exercicio + 1,
            d: fdata(mud.comparativo_destacadas[0].dt_receb_seguinte, idioma),
          })}{" "}
          <a href="#mudancas">{t.ver_mudancas}</a>
        </p>
      )}
      <p className="discreto">
        {t.setor}: {inv.empresa.setor ?? "—"} · {t.grupo}: {inv.empresa.grupo ? t.grupos[inv.empresa.grupo] : "—"}
      </p>
      <p>
        <a className="botao" href={api.pdf(inv.empresa.cd_cvm, e0.exercicio, inv.data_referencia, idioma)}>
          {t.exportar_pdf}
        </a>
      </p>

      <section className="cartao">
        <h3>{t.documento_usado}</h3>
        <p>
          DFP {e0.exercicio}, {t.versao} {e0.versao_usada ?? "—"}, {t.entregue_em} {fdata(e0.dt_receb, idioma)} ·{" "}
          {t.origens[e0.origem ?? ""] ?? e0.origem} · {t.tipos[e0.tipo ?? ""] ?? e0.tipo}
        </p>
        <p className="discreto">
          {t.versoes_conhecidas}: {e0.versoes_conhecidas.map((v) => `${v.versao} (${fdata(v.dt_receb, idioma)})`).join("; ")}
        </p>
        {e0.link && (
          <p className="discreto">
            <a href={e0.link} rel="noopener noreferrer" target="_blank">
              {t.documento_cvm} ↗
            </a>
          </p>
        )}
        {e0.notas.filter(Boolean).map((n, i) => (
          <p key={i} className="discreto">
            <TextoComLinks texto={n} />
          </p>
        ))}
      </section>

      {FAMILIAS.map((f) =>
        inv.achados[f]?.length ? (
          <section key={f}>
            <h2>{t.familias[f]}</h2>
            <div className="grade">
              {inv.achados[f]!.map((a) => (
                <Achado key={a.id} a={a} evidencias={inv.evidencias} idioma={idioma} t={t} />
              ))}
            </div>
          </section>
        ) : null,
      )}

      <h2 id="mudancas">{t.mudancas}</h2>
      <section className="cartao">
        <p className="rotulo">{t.destacadas}</p>
        {mud.comparativo_destacadas.length ? <Diferencas lista={mud.comparativo_destacadas} idioma={idioma} t={t} /> : <p>{t.sem_destacadas}</p>}
        <p className="discreto">
          <TextoComLinks texto={mud.materialidade_comparativo.texto} />
        </p>
        {mud.reapresentacao_pelo_comparativo.length > 0 && (
          <details>
            <summary>{fmt(t.lista_completa, { n: inteiro(mud.reapresentacao_pelo_comparativo.length, idioma) })}</summary>
            <Diferencas lista={mud.reapresentacao_pelo_comparativo} idioma={idioma} t={t} />
          </details>
        )}
      </section>

      <h2>{t.sabia}</h2>
      <section className="cartao">
        <ul>
          {inv.o_que_se_sabia.documentos.map((d) => (
            <li key={`${d.tipo}-${d.exercicio}-${d.versao}`}>
              {d.tipo} {d.exercicio}, v{d.versao}: {fdata(d.dt_receb, idioma)}
            </li>
          ))}
        </ul>
        <p className="discreto">
          <TextoComLinks texto={inv.o_que_se_sabia.nota} />
        </p>
      </section>

      <h2>{t.qualidade_dados}</h2>
      <section className="cartao">
        <p>{fmt(t.conferencias, { n: inteiro(confs.length, idioma), f: inteiro(falhas.length, idioma) })}</p>
        <ul className="discreto">
          {falhas.map((c) => (
            <li key={c.id}>
              {c.nome} ({c.coluna}): {c.motivo}
            </li>
          ))}
        </ul>
      </section>

      {pa && (
        <>
          <h2>{t.parecer}</h2>
          <section className="cartao">
            {pa.relatorio_do_auditor.tipo && <p>{pa.relatorio_do_auditor.tipo.join(", ")}</p>}
            {pa.relatorio_do_auditor.trecho && (
              <blockquote className="discreto">
                {t.trecho}: “{pa.relatorio_do_auditor.trecho}”
              </blockquote>
            )}
            <h3 style={{ marginTop: 12 }}>{t.trocas}</h3>
            {pa.trocas_de_auditor?.length ? (
              <ul>
                {pa.trocas_de_auditor.map((x, i) => (
                  <li key={i}>
                    {x.ano_fca}: {x.de ?? "—"} → {x.para ?? "—"}
                    {x.transicao_fca ? ` (${fmt(t.transicao, { x: x.transicao_fca })})` : ""}. {x.saida?.nota}
                  </li>
                ))}
              </ul>
            ) : (
              <p>{t.sem_trocas}</p>
            )}
            {pa.rodizio?.nota && (
              <p className="discreto">
                <TextoComLinks texto={pa.rodizio.nota} />
              </p>
            )}
          </section>
        </>
      )}

      <h2>{t.limites}</h2>
      <ul className="cartao">
        {inv.limites.map((x, i) => (
          <li key={i} style={{ marginLeft: 16 }}>
            <TextoComLinks texto={x} />
          </li>
        ))}
      </ul>
      <h2>{t.limitacoes}</h2>
      <ul className="cartao">
        {inv.limitacoes.filter(Boolean).map((x, i) => (
          <li key={i} style={{ marginLeft: 16 }}>
            <TextoComLinks texto={x} />
          </li>
        ))}
      </ul>
      <p className="discreto">
        <Link href="/como-o-motor-foi-testado">{t.nav_testado}</Link> ·{" "}
        <a href={`${REPOSITORIO}${idioma === "pt" ? "docs/ficha-do-motor.md" : "docs/en/engine-card.md"}`}>{t.ficha}</a> · {inv.motor.v1};{" "}
        {inv.motor.v2}
      </p>
      <InformacaoDeHoje h={inv.informacao_de_hoje} t={t} />
    </>
  );
}

export default function PaginaInvestigacao() {
  return (
    <Suspense>
      <Pagina />
    </Suspense>
  );
}
