"use client";

// A investigação de uma empresa num exercício, como era na data (Fase E2): cabeçalho com caminho, nome na data,
// histórico de nome, datas como botões, PDF e documento na CVM; resumo no topo (as três famílias, que não se somam, e
// o caso do gabarito); índice "Nesta página"; e as seções com os cartões dos sinais. O mesmo JSON do contrato (e do
// PDF). A "Informação de hoje" fica separada, no fim, como no PDF.
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { Suspense, useEffect, useState } from "react";
import CabecalhoEmpresa from "@/components/CabecalhoEmpresa";
import LeituraDocumental from "@/components/LeituraDocumental";
import InformacaoDeHoje from "@/components/InformacaoDeHoje";
import Resumo from "@/components/Resumo";
import { CartaoMScore, CartaoSinal } from "@/components/Sinais";
import TextoComLinks from "@/components/TextoComLinks";
import { api, FalhaApi, MODO_ESTATICO } from "@/lib/api";
import { data as fdata, inteiro, milhoes } from "@/lib/formato";
import { useIdioma } from "@/lib/idioma";
import { DATA_MAXIMA, dataValida, exercicioValido, ULTIMO_EXERCICIO_LIBERADO } from "@/lib/limites.mjs";
import { fmt, type Textos } from "@/lib/textos";
import type { Achado, ComoTestado, Demonstracao, Diferenca, Investigacao } from "@/lib/tipos";

function Diferencas({ lista, idioma, t }: { lista: Diferenca[]; idioma: "pt" | "en"; t: Textos }) {
  return (
    <div className="tabela" tabIndex={0} role="region" aria-label={t.sec_mudancas}>
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

function Secao({ id, titulo, sub, children }: { id: string; titulo: string; sub?: string; children: React.ReactNode }) {
  return (
    <section id={id} className="secao" aria-labelledby={`titulo-${id}`}>
      <h2 id={`titulo-${id}`}>{titulo}</h2>
      {sub && <p className="subtitulo">{sub}</p>}
      {children}
    </section>
  );
}

function Grade({ itens }: { itens: React.ReactNode[] }) {
  // seção com um cartão só ocupa a largura toda
  return <div className={itens.length === 1 ? "grade grade-um" : "grade"}>{itens}</div>;
}

function Pagina() {
  const { idioma, t } = useIdioma();
  const p = useSearchParams();
  const cd = p.get("cd") ?? "";
  const ex = Number(p.get("ex"));
  const data = p.get("data") ?? DATA_MAXIMA;
  const [inv, setInv] = useState<Investigacao | null>(null);
  const [erro, setErro] = useState<string | null>(null);
  const [demo, setDemo] = useState<Demonstracao | null>(null);
  const [testado, setTestado] = useState<ComoTestado | null>(null);

  useEffect(() => {
    api.demonstracao().then(setDemo).catch(() => setDemo(null));
    api.comoTestado().then(setTestado).catch(() => setTestado(null));
  }, []);

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
  const entrada = demo?.empresas.find((x) => x.cd_cvm === inv.empresa.cd_cvm) ?? null;
  const datas = entrada ? Object.keys(entrada.datas).filter((d) => entrada.datas[d].includes(e0.exercicio)) : [];
  const anos = testado ? { a: testado.dados.primeiro_exercicio, b: testado.dados.ultimo_exercicio } : undefined;
  const href = (d: string) => `/investigacao?cd=${inv.empresa.cd_cvm}&ex=${e0.exercicio}&data=${d}`;

  const manip = inv.achados.possivel_manipulacao ?? [];
  const mscore = manip.find((a) => a.sinal === "mscore");
  const componentes = manip.filter((a) => a.componente_de === "mscore");
  const outros = manip.filter((a) => a.sinal !== "mscore" && !a.componente_de);
  const cartao = (a: Achado) => <CartaoSinal key={a.id} a={a} evidencias={inv.evidencias} anos={anos} />;

  // Mudanças: a DFP do ano seguinte já existia na data? Se não, o link para a mesma investigação numa data posterior.
  const seguinte = e0.exercicio + 1;
  const existiaSeguinte = inv.o_que_se_sabia.documentos.some((d) => d.exercicio === seguinte);
  const depois = MODO_ESTATICO ? datas[datas.length - 1] : DATA_MAXIMA;

  const indice: [string, string][] = [
    ["resumo", t.resumo],
    ["manipulacao", t.sec_manipulacao],
    ["risco", t.sec_risco],
    ["qualidade", t.sec_qualidade],
    ...(pa ? ([["parecer", t.sec_parecer]] as [string, string][]) : []),
    ...(inv.leitura_documental ? ([["trechos", t.idx_trechos]] as [string, string][]) : []),
    ["mudancas", t.sec_mudancas],
    ["limites", t.sec_limites],
    ["hoje", t.sec_hoje],
  ];

  return (
    <>
      <CabecalhoEmpresa
        empresa={inv.empresa}
        data={inv.data_referencia}
        exercicio={e0.exercicio}
        datas={datas}
        rotulos={entrada?.rotulos_datas ?? {}}
        href={href}
        pdf={api.pdf(inv.empresa.cd_cvm, e0.exercicio, inv.data_referencia, idioma)}
        documento={e0.link}
      />
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
      <p className="documento-usado">
        <span className="rotulo">{t.documento_usado}:</span> DFP {e0.exercicio}, {t.versao} {e0.versao_usada ?? "—"}, {t.entregue_em}{" "}
        {fdata(e0.dt_receb, idioma)} · {t.origens[e0.origem ?? ""] ?? e0.origem} · {t.tipos[e0.tipo ?? ""] ?? e0.tipo}
      </p>

      <div className="com-indice">
        <nav className="indice" aria-label={t.nesta_pagina}>
          <p className="rotulo">{t.nesta_pagina}</p>
          <ul>
            {indice.map(([id, rotulo]) => (
              <li key={id}>
                <a href={`#${id}`}>{rotulo}</a>
              </li>
            ))}
          </ul>
        </nav>

        <div className="conteudo">
          <Resumo inv={inv} casos={entrada?.casos ?? null} testado={testado} />

          <Secao id="manipulacao" titulo={t.sec_manipulacao} sub={t.sub_manipulacao}>
            {mscore && <CartaoMScore a={mscore} componentes={componentes} evidencias={inv.evidencias} anos={anos} />}
            {outros.length > 0 && <Grade itens={outros.map(cartao)} />}
          </Secao>

          <Secao id="risco" titulo={t.sec_risco} sub={t.sub_risco}>
            <Grade itens={(inv.achados.risco_financeiro ?? []).map(cartao)} />
          </Secao>

          <Secao id="qualidade" titulo={t.sec_qualidade} sub={t.sub_qualidade}>
            <Grade itens={(inv.achados.qualidade_financeira ?? []).map(cartao)} />
          </Secao>

          {pa && (
            <Secao id="parecer" titulo={t.sec_parecer} sub={t.sub_parecer}>
              <div className="cartao">
                {pa.relatorio_do_auditor.tipo && <p>{pa.relatorio_do_auditor.tipo.join(", ")}</p>}
                {pa.relatorio_do_auditor.motivo && <p className="discreto">{pa.relatorio_do_auditor.motivo}</p>}
                {pa.relatorio_do_auditor.trecho && (
                  <blockquote className="discreto">
                    {t.trecho}: “{pa.relatorio_do_auditor.trecho}”
                  </blockquote>
                )}
                <h3 className="espaco">{t.trocas}</h3>
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
              </div>
            </Secao>
          )}

          {inv.leitura_documental && (
            <Secao id="trechos" titulo={t.sec_trechos} sub={t.sub_trechos}>
              <LeituraDocumental l={inv.leitura_documental} testado={inv.como_o_leitor_foi_testado ?? null} limites={inv.limites_da_leitura ?? []} />
            </Secao>
          )}

          <Secao id="mudancas" titulo={t.sec_mudancas} sub={t.sub_mudancas}>
            <div className="cartao">
              {seguinte > ULTIMO_EXERCICIO_LIBERADO ? (
                <p>{fmt(t.mudancas_lacre, { ex: seguinte })}</p>
              ) : !existiaSeguinte ? (
                <>
                  <p>{fmt(t.mudancas_sem_seguinte, { ex: seguinte })}</p>
                  {depois && depois !== inv.data_referencia && (
                    <p>
                      <Link href={href(depois)}>{fmt(t.ver_depois, { d: fdata(depois, idioma) })}</Link>
                    </p>
                  )}
                </>
              ) : (
                <>
                  <p className="rotulo">{t.destacadas}</p>
                  {mud.comparativo_destacadas.length ? (
                    <Diferencas lista={mud.comparativo_destacadas} idioma={idioma} t={t} />
                  ) : (
                    <p>{t.sem_destacadas}</p>
                  )}
                  <p className="discreto">
                    <TextoComLinks texto={mud.materialidade_comparativo.texto} />
                  </p>
                  {mud.reapresentacao_pelo_comparativo.length > 0 && (
                    <details>
                      <summary>{fmt(t.lista_completa, { n: inteiro(mud.reapresentacao_pelo_comparativo.length, idioma) })}</summary>
                      <Diferencas lista={mud.reapresentacao_pelo_comparativo} idioma={idioma} t={t} />
                    </details>
                  )}
                </>
              )}
              <p className="discreto">
                {t.versoes_conhecidas}: {e0.versoes_conhecidas.map((v) => `${v.versao} (${fdata(v.dt_receb, idioma)})`).join("; ")}
              </p>
              <h3 className="espaco">{t.sabia}</h3>
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
            </div>
          </Secao>

          <Secao id="limites" titulo={t.sec_limites} sub={t.sub_limites}>
            <div className="cartao">
              <ul>
                {inv.limites.map((x, i) => (
                  <li key={i}>
                    <TextoComLinks texto={x} />
                  </li>
                ))}
              </ul>
              <h3 className="espaco">{t.limitacoes}</h3>
              <ul>
                {inv.limitacoes.filter(Boolean).map((x, i) => (
                  <li key={i}>
                    <TextoComLinks texto={x} />
                  </li>
                ))}
              </ul>
              <h3 className="espaco">{t.qualidade_dados}</h3>
              <p>{fmt(t.conferencias, { n: inteiro(confs.length, idioma), f: inteiro(falhas.length, idioma) })}</p>
              <ul className="discreto">
                {falhas.map((c) => (
                  <li key={c.id}>
                    {c.nome} ({c.coluna}): {c.motivo}
                  </li>
                ))}
              </ul>
              <p className="discreto">
                {e0.notas.filter(Boolean).map((n, i) => (
                  <span key={i}>
                    <TextoComLinks texto={n} />{" "}
                  </span>
                ))}
              </p>
              <p className="discreto">
                {[inv.motor.v1, inv.motor.v2, inv.motor.leitor].filter(Boolean).join("; ")}
              </p>
            </div>
          </Secao>

          <InformacaoDeHoje h={inv.informacao_de_hoje} t={t} />
        </div>
      </div>
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
