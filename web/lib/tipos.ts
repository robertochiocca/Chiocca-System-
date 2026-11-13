// Tipos do contrato (docs/contratos.md, seções 2 e 6), só com os campos que a interface usa.
// O modelo completo está em chiocca/v2/modelos.py (Pydantic); os testes conferem os dois lados.

export type Idioma = "pt" | "en";
export type Aviso = Record<Idioma, string>;

export interface CodigoNegociacao {
  codigo: string;
  valor_mobiliario: string | null;
  mercado: string | null;
  inicio_negociacao: string | null;
  fim_negociacao: string | null;
  fca: { ano: number; versao: number; dt_receb: string };
}

export interface EmpresaResumo {
  cd_cvm: string;
  cnpj: string | null;
  denominacao: string | null;
  origem_denominacao: "fca" | "indice_dfp";
  codigos_negociacao: CodigoNegociacao[];
  motivo_codigos_negociacao: string | null;
}

export interface NomeAnterior {
  nome: string;
  ate_ano: number;
}

export interface Empresa extends EmpresaResumo {
  setor: string | null;
  origem_setor: string | null;
  grupo: "financeira" | "nao_financeira" | null;
  nomes_anteriores?: NomeAnterior[];
}

export interface InformacaoDeHoje {
  titulo: string;
  situacao_cadastro: string | null;
  denominacao?: string | null;
  fonte: string;
}

export type RotuloData = "exercicio_anterior" | "periodo_afetado" | "depois_da_revelacao" | "data_maxima";
export type TipoCaso = "processo_cvm" | "fraude_confirmada" | "republicacao";

export interface CasoDoGabarito {
  caso_id: string;
  tipo_evento: TipoCaso[];
  data_publica: string | null;
  periodo_afetado: [number, number] | null;
  fonte: string | null;
}

export interface EmpresaDaDemonstracao extends EmpresaResumo {
  /** O nome da companhia no gabarito (o que a página inicial mostra). */
  nome_do_caso: string | null;
  nomes: string[];
  datas: Record<string, number[]>;
  rotulos_datas: Record<string, RotuloData>;
  data_inicial: string;
  casos: CasoDoGabarito[];
}

export interface Demonstracao {
  ordem: "nome_do_caso";
  empresas: EmpresaDaDemonstracao[];
  destaques: {
    cd_cvm: string;
    exercicio: number;
    na_epoca: string;
    depois: string;
    denominacao_na_epoca: string | null;
    patrimonio_liquido: { valor: number; valor_comparativo: number; exercicio_comparativo: number; dt_receb_comparativo: string };
  };
  aviso: Aviso;
}

export interface RegraDoEstudo1 {
  sinal: "mscore" | "dpo" | "juro" | "peso_nao_recorrente";
  grupo: "financeira" | "nao_financeira";
  rotulo: Record<Idioma, string>;
  regra: Record<Idioma, string>;
}

export interface Busca {
  busca: string;
  criterio: "nome" | "cd_cvm" | "cnpj";
  data_referencia: string;
  ordem: "denominacao";
  total: number;
  resultados: EmpresaResumo[];
  aviso: Aviso;
}

export interface EmpresaNaData {
  data_referencia: string;
  empresa: Empresa;
  exercicios: number[];
  informacao_de_hoje: InformacaoDeHoje;
  aviso: Aviso;
}

export interface Valor {
  valor: number | null;
  status: string;
  motivo: string | null;
  codigo: string | null;
}

export interface Percentil {
  valor: number | null;
  n: number;
  motivo: string | null;
  marca?: string;
}

export interface Distribuicao {
  n: number;
  quantis?: Record<string, number>;
  limites?: number[];
  contagens?: number[];
  abaixo?: number;
  acima?: number;
  motivo: string | null;
}

export interface Historico {
  exercicios: number[];
  serie: [number, number][];
  mediana?: number;
  q1?: number;
  q3?: number;
  faixa_tukey?: [number, number];
  posicao?: "dentro" | "acima" | "abaixo";
  motivo: string | null;
}

export interface Contexto {
  percentil_setor_ano: Percentil | null;
  percentil_grupo_ano: Percentil | null;
  distribuicao_setor_ano?: Distribuicao | null;
  historico?: Historico;
}

export interface Achado {
  id: string;
  familia: "possivel_manipulacao" | "risco_financeiro" | "qualidade_financeira";
  sinal: string;
  exercicio: number;
  rotulo: string | null;
  valor: Valor;
  unidade: string;
  valor_no_produto?: Valor | null;
  regra: string | null;
  alerta_v1: boolean | null;
  componente_de?: "mscore" | null;
  contexto: Contexto | null;
  confianca?: { nivel: string; criterios: { nome: string; resultado: string; motivo: string | null }[] } | null;
  explicacao?: string | null;
  explicacoes_alternativas?: (string | null)[] | null;
  limitacoes?: (string | null)[] | null;
  texto?: string | null;
  componentes?: Record<string, unknown> | null;
  marcas?: (string | null)[] | null;
  linhagem: { entradas?: string[]; formula?: string; motor?: string; codigo?: string } | null;
}

export interface Evidencia {
  id: string;
  documento: { tipo?: string; num_doc?: string; versao?: number; dt_receb?: string; origem?: string; url?: string };
  demonstracao: string;
  coluna: string;
  cd_conta: string;
  ds_conta: string | null;
  valor: number | null;
  localizacao: { arquivo?: string; linha?: number; escala?: string } | null;
}

export interface Diferenca {
  texto: string | null;
  demonstracao: string;
  cd_conta: string;
  ds_conta: string;
  valor: number;
  valor_comparativo: number;
  diferenca: number;
  grupo: "a" | "b";
  destacada: boolean;
  versao: number | null;
  dt_receb: string | null;
  versao_seguinte: number | null;
  dt_receb_seguinte: string | null;
}

export interface Troca {
  ano_fca: number;
  de: string | null;
  para: string | null;
  transicao_fca: number | null;
  saida: { nota: string; compativel_com_rodizio: boolean } | null;
}

export interface TrechoLido {
  verificacao: "partes_relacionadas" | "campo_cpc05_18" | "condicoes_de_mercado" | "risco_sacado" | "parecer";
  rotulo: string | null;
  pagina: number | null;
  texto: string | null;
  omitido: boolean;
  aviso_omissao: string | null;
  conferido: true;
  negacao: boolean | null;
  cortado: boolean;
  idioma_original: "pt";
}

export interface LinhaDoFormulario {
  parte: string;
  parte_omitida: boolean;
  tipo_pessoa: string | null;
  relacao: string | null;
  objeto: string | null;
  garantia: string | null;
  natureza: string | null;
  duracao: string | null;
  taxa_juros: string | null;
  data_transacao: string | null;
  montante: string | null;
  saldo: string | null;
  linha_arquivo?: number | null;
}

export interface LeituraDocumental {
  natureza: "trecho_literal";
  gera_alerta: false;
  leitor: string;
  extrator: string | null;
  nota: string;
  documento?: { tipo: string; num_doc: string | null; versao: number | null; dt_receb: string | null; origem: string } | null;
  notas_explicativas: { status: string; paginas: number };
  partes_relacionadas: {
    status: "lido" | "nao_lido";
    motivo: string | null;
    nota: { titulo: string; paginas: number[] } | null;
    colunas: string[];
    trechos: TrechoLido[];
    campos_cpc05_18: TrechoLido[];
    condicoes_de_mercado: TrechoLido[];
    nota_condicoes: string;
  };
  risco_sacado: { status: "lido" | "nao_lido"; motivo?: string | null; encontrado: boolean | null; termos: string[]; trechos: TrechoLido[]; nota: string | null };
  relatorio_do_auditor: { status: "lido" | "nao_lido"; motivo?: string | null; titulo: string | null; tipo: string | null; trechos: TrechoLido[] };
  formulario_de_referencia: {
    status: "disponivel" | "nao_disponivel_na_data" | "sem_formulario" | "sem_linhas";
    motivo: string | null;
    ano_formulario?: number | null;
    documento?: { versao?: number; dt_receb?: string; linhagem?: string; arquivo?: string } | null;
    linhas: LinhaDoFormulario[];
  };
}

export interface ItemIPE {
  categoria: "fato_relevante" | "comunicado_ao_mercado";
  categoria_cvm: string;
  data_entrega: string;
  assunto: string;
  assunto_omitido: boolean;
  assunto_vazio: boolean;
  link: string | null;
  link_pode_nao_abrir: boolean;
  id_documento: string;
  protocolo: string | null;
  versao: number | null;
  grupo: number;
  fonte: { arquivo: string; ano: number; sha256: string };
}

export interface FatosEComunicados {
  origem: "dados_abertos";
  conjunto: "IPE";
  desde: string;
  ate: string;
  nota: string;
  motivo: string | null;
  contagem: Record<string, number>;
  gera_alerta: false;
  itens: ItemIPE[];
}

export interface Investigacao {
  empresa: Empresa;
  data_referencia: string;
  idioma: Idioma;
  exercicios: {
    exercicio: number;
    dt_refer: string | null;
    situacao: string;
    versao_usada: number | null;
    dt_receb: string | null;
    versoes_conhecidas: { versao: number; dt_receb: string }[];
    tipo: string | null;
    origem: string | null;
    link: string | null;
    escala_original: string | null;
    notas: (string | null)[];
  }[];
  achados: Partial<Record<Achado["familia"], Achado[]>>;
  mudancas: {
    versoes_conhecidas: { versao: number; dt_receb: string; usada: boolean }[];
    comparativo_destacadas: Diferenca[];
    reapresentacao_pelo_comparativo: Diferenca[];
    tolerancia_comparativo: number;
    materialidade_comparativo: { limite: number | null; texto: string };
  };
  o_que_se_sabia: {
    documentos: { tipo: string; exercicio: number; versao: number; dt_receb: string }[];
    nota: string;
    fatos_e_comunicados?: FatosEComunicados | null;
  };
  qualidade_dos_dados: { conferencias: { id: string; nome: string | null; coluna: string | null; resultado: string; motivo: string | null }[] };
  parecer_e_auditor: {
    relatorio_do_auditor: { tipo?: string[]; trecho?: string | null; motivo?: string | null };
    auditores_no_fca?: { ano_fca: number; auditores: { auditor: string }[] }[];
    trocas_de_auditor?: Troca[];
    rodizio?: { nota: string | null; norma: string; fonte: string };
  } | null;
  leitura_documental?: LeituraDocumental | null;
  como_o_leitor_foi_testado?: {
    documento: string;
    leitor: string;
    commit: string;
    casos: number;
    precisao: number;
    cobertura: number;
    trechos_mostrados: number;
    trechos_conferidos: number;
    nomes_vazados: number;
  } | null;
  limites_da_leitura?: string[] | null;
  como_o_motor_foi_testado: { documento: string; acertados: number; acertaveis: number; taxa_de_alerta_nao_financeiras?: number };
  limites: string[];
  limitacoes: (string | null)[];
  evidencias: Record<string, Evidencia>;
  motor: { v1: string; v2: string; leitor?: string | null };
  informacao_de_hoje: InformacaoDeHoje;
  gerado_em: string | null;
  aviso: string;
}

export interface ComoTestado {
  motor: { v1: string; v2: string; leitor?: string | null };
  pre_registro: { assinatura: string; emendas: number };
  dados: Record<string, number>;
  acerto: Record<string, number>;
  alarmes_por_acerto_nf: { periodo_inteiro: number | null; teste: number | null };
  taxa_de_alerta: { nao_financeiras: number; com_financeiras: number };
  acaso: Record<string, number>;
  antecedencia: {
    casos: { caso_id: string; empresa: string; exercicio: number; dt_receb: string; data_publica: string; meses: number }[];
    mediana_meses: number;
    minimo_meses: number;
    maximo_meses: number;
  };
  documentos: Record<Idioma, Record<string, string>>;
  regras: RegraDoEstudo1[];
  limites: Record<Idioma, string[]>;
  aviso: Aviso;
}

export interface Saude {
  status: "ok";
  ultimo_exercicio_liberado: number;
  data_referencia_minima: string;
  data_referencia_maxima: string;
  modo_demonstracao: boolean;
  empresas_na_demonstracao: number | null;
  aviso: Aviso;
}

export interface ErroApi {
  erro: string;
  motivo: string;
}
