"use client";

// Cabeçalho da página da empresa e da investigação (Fase E2): caminho (Buscar › Companhia › Exercício), título com o
// nome na data, a linha "Exercício AAAA · como era em DD/MM/AAAA", o histórico de nome tirado dos FCA (o nome de hoje
// só aparece na "Informação de hoje"), as datas como botões com rótulo e, na investigação, "Exportar em PDF" e
// "Documento na CVM". Na API completa (fora da demonstração estática), há também o seletor de outra data.
import { useRouter } from "next/navigation";
import { data as fdata } from "@/lib/formato";
import { useIdioma } from "@/lib/idioma";
import { dataValida } from "@/lib/limites.mjs";
import { MODO_ESTATICO } from "@/lib/api";
import { fmt } from "@/lib/textos";
import type { Empresa } from "@/lib/tipos";
import { BotoesDatas, Migalhas } from "./Pecas";
import SeletorData from "./SeletorData";

export function HistoricoDeNome({ empresa }: { empresa: Empresa }) {
  const { t } = useIdioma();
  const nomes = [...(empresa.nomes_anteriores ?? [])].reverse(); // do mais recente para o mais antigo
  if (!nomes.length) return null;
  const [primeiro, ...resto] = nomes;
  return (
    <p className="historico-nome">
      {fmt(t.nome_anterior, { a: primeiro.ate_ano, n: primeiro.nome })}
      {resto.map((x) => `; ${fmt(t.nome_anterior_mais, { a: x.ate_ano, n: x.nome })}`).join("")}.
    </p>
  );
}

export default function CabecalhoEmpresa({
  empresa,
  data,
  exercicio,
  datas,
  rotulos,
  href,
  pdf,
  documento,
}: {
  empresa: Empresa;
  data: string;
  exercicio?: number;
  datas: string[];
  rotulos: Record<string, string>;
  href: (d: string) => string;
  pdf?: string;
  documento?: string | null;
}) {
  const { idioma, t } = useIdioma();
  const router = useRouter();
  const nome = empresa.denominacao ?? empresa.cd_cvm;
  const itens = [{ rotulo: t.nav_buscar, href: "/" }, { rotulo: nome, href: `/empresa?cd=${empresa.cd_cvm}&data=${data}` }];
  if (exercicio !== undefined) itens.push({ rotulo: `${t.exercicio} ${exercicio}`, href: "" });
  return (
    <header className="cabecalho-empresa">
      <Migalhas itens={itens} />
      <h1>{nome}</h1>
      <p className="linha-data">
        {exercicio !== undefined
          ? fmt(t.exercicio_linha, { ex: exercicio, d: fdata(data, idioma) })
          : fmt(t.como_era_em, { d: fdata(data, idioma) })}
      </p>
      <HistoricoDeNome empresa={empresa} />
      <div className="datas-e-acoes">
        {datas.length > 0 && <BotoesDatas datas={datas} rotulos={rotulos} selecionada={data} href={href} />}
        {(pdf || documento) && (
          <div className="acoes">
            {pdf && (
              <a className="botao" href={pdf}>
                {t.exportar_pdf}
              </a>
            )}
            {documento && (
              <a className="botao leve" href={documento} rel="noopener noreferrer" target="_blank">
                {t.documento_cvm} ↗
              </a>
            )}
          </div>
        )}
      </div>
      {!MODO_ESTATICO && (
        <details className="outra-data">
          <summary>{t.outra_data}</summary>
          <SeletorData valor={data} mudar={(d) => dataValida(d) && router.push(href(d))} t={t} />
        </details>
      )}
    </header>
  );
}
