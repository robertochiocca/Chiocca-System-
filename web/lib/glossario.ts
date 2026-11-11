// Glossário dos ícones de ajuda ("?"), num arquivo só, em PT e EN (Fase E2). Os anos do estudo entram por
// parâmetro ({a} e {b}), lidos do JSON de "Como o motor foi testado"; nenhum resultado é escrito à mão aqui.
import type { Idioma } from "./tipos";

export type ChaveGlossario =
  | "regra_estudo_1"
  | "regra_mscore"
  | "percentil"
  | "n"
  | "faixa_tukey"
  | "indice"
  | "confianca"
  | "componente_mscore"
  | "so_contexto"
  | "sem_alerta";

export interface Verbete {
  titulo: string;
  texto: string;
  /** Link para a página "Como o motor foi testado". */
  testado?: boolean;
}

export const GLOSSARIO: Record<Idioma, Record<ChaveGlossario, Verbete>> = {
  pt: {
    regra_estudo_1: {
      titulo: "Regra do estudo 1",
      texto:
        "Regra escrita no pré-registro, antes de olhar os dados, e testada nos exercícios de {a} a {b}. Alerta não é acusação: diz onde olhar.",
      testado: true,
    },
    regra_mscore: {
      titulo: "Regra do estudo 1",
      texto:
        "Corte fixado no pré-registro, antes de olhar os dados. Vem do artigo de Beneish (1999), estimado nos EUA, e nunca foi recalibrado para o Brasil.",
      testado: true,
    },
    percentil: {
      titulo: "Percentil",
      texto:
        "A posição da empresa entre as do mesmo setor (ou do mesmo grupo) no mesmo ano, de 0 a 100; 100 é o maior valor. Não diz se o valor é bom ou ruim.",
    },
    n: {
      titulo: "n",
      texto:
        "Quantas empresas do setor (ou do grupo) tinham o indicador calculável no ano, com o que tinha sido entregue até a data.",
    },
    faixa_tukey: {
      titulo: "Faixa de Tukey",
      texto:
        "A faixa típica da própria empresa nos exercícios anteriores, como eram na data: do primeiro quartil menos 1,5 vez a distância entre os quartis até o terceiro quartil mais 1,5 vez essa distância. Fora dela, o valor é incomum para a própria empresa.",
    },
    indice: {
      titulo: "Índice",
      texto:
        "Número sem unidade, uma razão entre contas da própria empresa. Nos componentes do M-score, 1 quer dizer igual ao ano anterior.",
    },
    confianca: {
      titulo: "Confiança nos dados",
      texto:
        "Quanto dá para confiar nas linhas que entram no número: a fonte (dados abertos ou ENET, consolidado ou individual), se todas as linhas foram achadas e se as conferências da DFP passaram. Alta, média ou baixa. Não é a chance de manipulação.",
    },
    componente_mscore: {
      titulo: "Componente do M-score",
      texto:
        "Um dos oito índices do M-score. Não tem regra própria e não dispara alerta sozinho: entra junto com os outros sete na fórmula.",
    },
    so_contexto: {
      titulo: "Só contexto",
      texto: "Indicador de contexto: não dispara alerta e não se soma às outras famílias.",
    },
    sem_alerta: {
      titulo: "Sem alerta",
      texto: "A regra do estudo 1 não disparou. Não é atestado: só quer dizer que este sinal ficou abaixo do corte.",
    },
  },
  en: {
    regra_estudo_1: {
      titulo: "Study 1 rule",
      texto:
        "A rule written in the pre-registration, before looking at the data, and tested on fiscal years {a} to {b}. An alert is not an accusation: it says where to look.",
      testado: true,
    },
    regra_mscore: {
      titulo: "Study 1 rule",
      texto:
        "A cut-off set in the pre-registration, before looking at the data. It comes from Beneish (1999), estimated in the US, and was never recalibrated for Brazil.",
      testado: true,
    },
    percentil: {
      titulo: "Percentile",
      texto:
        "The company's position among those in the same sector (or group) in the same year, from 0 to 100; 100 is the highest value. It does not say whether the value is good or bad.",
    },
    n: {
      titulo: "n",
      texto:
        "How many companies in the sector (or group) had the indicator computable in the year, with what had been filed by the date.",
    },
    faixa_tukey: {
      titulo: "Tukey range",
      texto:
        "The company's own typical range over previous fiscal years, as they were on the date: from the first quartile minus 1.5 times the interquartile distance to the third quartile plus 1.5 times that distance. Outside it, the value is unusual for the company itself.",
    },
    indice: {
      titulo: "Index",
      texto:
        "A unitless number, a ratio between the company's own accounts. In the M-score components, 1 means the same as the previous year.",
    },
    confianca: {
      titulo: "Confidence in the data",
      texto:
        "How far the lines that go into the number can be trusted: the source (open data or ENET, consolidated or individual), whether all lines were found and whether the DFP checks passed. High, medium or low. It is not the chance of manipulation.",
    },
    componente_mscore: {
      titulo: "M-score component",
      texto:
        "One of the eight M-score indices. It has no rule of its own and does not trigger alerts alone: it enters the formula together with the other seven.",
    },
    so_contexto: {
      titulo: "Context only",
      texto: "A context indicator: it does not trigger alerts and is not added to the other families.",
    },
    sem_alerta: {
      titulo: "No alert",
      texto: "The study 1 rule did not fire. It is not a clean bill: it only means this signal stayed below the cut-off.",
    },
  },
};
