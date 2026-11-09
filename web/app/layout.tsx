// Estrutura de todas as telas: barra fixa com navegação e aviso, conteúdo e rodapé.
// Origem do script de tema antes da hidratação: DireitoAberto (github.com/robertochiocca/DireitoAberto),
// web/app/layout.tsx, commit 102e3e2d9d70e87249d8df9215737e2d98b6358d, licença MIT. Adaptado: sem fontes externas.
import type { Metadata, Viewport } from "next";
import "./globals.css";
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

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="pt-BR" suppressHydrationWarning>
      <head>
        <script dangerouslySetInnerHTML={{ __html: temaInicial }} />
      </head>
      <body>
        <ProvedorIdioma>
          <Topo />
          <main className="wrap">{children}</main>
          <footer>
            <div className="wrap">
              Chiocca System · <a href="https://github.com/robertochiocca/Chiocca-System-">github.com/robertochiocca/Chiocca-System-</a>
            </div>
          </footer>
        </ProvedorIdioma>
      </body>
    </html>
  );
}
