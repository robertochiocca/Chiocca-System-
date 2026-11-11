// Estrutura de todas as telas: barra fixa com navegação e aviso, conteúdo e rodapé.
// Origem do script de tema antes da hidratação: DireitoAberto (github.com/robertochiocca/DireitoAberto),
// web/app/layout.tsx, commit 102e3e2d9d70e87249d8df9215737e2d98b6358d, licença MIT. Adaptado: sem fontes externas.
import type { Metadata, Viewport } from "next";
import "./globals.css";
import Rodape from "@/components/Rodape";
import Topo from "@/components/Topo";
import { ProvedorIdioma } from "@/lib/idioma";

export const metadata: Metadata = {
  title: "Chiocca System — alerta, não acusação",
  description:
    "Sinais estatísticos sobre demonstrações financeiras públicas de companhias abertas brasileiras, como eram em cada data. Não é acusação, não é recomendação de investimento.",
};

export const viewport: Viewport = { width: "device-width", initialScale: 1 };

const temaInicial = `
(function(){
  try{
    var t = localStorage.getItem("chiocca-tema") ||
      (matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light");
    document.documentElement.setAttribute("data-theme", t);
  }catch(e){}
})();`;

// Na demonstração estática não há servidor para mandar os cabeçalhos de segurança (next.config.mjs): a mesma
// política de conteúdo vai numa <meta>. frame-ancestors não vale em <meta> e fica a cargo da hospedagem.
const ESTATICO = process.env.NEXT_PUBLIC_MODO_ESTATICO === "1";
const CSP_ESTATICO = [
  "default-src 'self'",
  "script-src 'self' 'unsafe-inline'",
  "style-src 'self' 'unsafe-inline'",
  "font-src 'self'",
  "img-src 'self' data:",
  "connect-src 'self'",
  "frame-src 'self'",
  "object-src 'none'",
  "base-uri 'self'",
  "form-action 'self'",
].join("; ");

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="pt-BR" suppressHydrationWarning>
      <head>
        {ESTATICO && <meta httpEquiv="Content-Security-Policy" content={CSP_ESTATICO} />}
        {ESTATICO && <meta name="referrer" content="strict-origin-when-cross-origin" />}
        <script dangerouslySetInnerHTML={{ __html: temaInicial }} />
      </head>
      <body>
        <ProvedorIdioma>
          <Topo />
          <main id="conteudo" className="wrap">
            {children}
          </main>
          <Rodape />
        </ProvedorIdioma>
      </body>
    </html>
  );
}
