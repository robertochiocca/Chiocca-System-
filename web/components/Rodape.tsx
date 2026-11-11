"use client";

// Rodapé de todas as telas: link para o repositório e para a ficha do motor, na língua escolhida.
import { useIdioma } from "@/lib/idioma";
import { linkFicha } from "./Topo";

export default function Rodape() {
  const { idioma, t } = useIdioma();
  return (
    <footer>
      <div className="wrap rodape">
        <span>Chiocca System</span>
        <a href="https://github.com/robertochiocca/Chiocca-System-" rel="noopener noreferrer" target="_blank">
          {t.rodape_repositorio} ↗
        </a>
        <a href={linkFicha(idioma)} rel="noopener noreferrer" target="_blank">
          {t.nav_ficha} ↗
        </a>
      </div>
    </footer>
  );
}
