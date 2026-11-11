"use client";

// Rodapé de todas as telas: o aviso completo (o destino do "Saiba mais" do aviso curto do celular) e os links para o
// repositório e para a ficha do motor, na língua escolhida.
import { AVISO } from "@/lib/contrato.mjs";
import { useIdioma } from "@/lib/idioma";
import { linkFicha } from "./Topo";

export default function Rodape() {
  const { idioma, t } = useIdioma();
  return (
    <footer>
      <p id="aviso-completo" className="wrap aviso-rodape" role="note">
        <strong>{t.aviso_rotulo}:</strong> {AVISO[idioma]}
      </p>
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
