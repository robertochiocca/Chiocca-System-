"use client";

// Barra fixa de todas as telas: navegação, idioma, tema, aviso fixo e, se ligado, o aviso do modo demonstração.
// Origem do padrão de tema e do menu compacto: DireitoAberto (github.com/robertochiocca/DireitoAberto),
// web/components/Nav.tsx e web/app/layout.tsx, commit 102e3e2d9d70e87249d8df9215737e2d98b6358d, licença MIT.
// Adaptado para o Chiocca System: sem conta nem login; idioma PT/EN; aviso fixo dentro da barra.
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useState } from "react";
import { AVISO } from "@/lib/contrato.mjs";
import { api } from "@/lib/api";
import { useIdioma } from "@/lib/idioma";

export default function Topo() {
  const { idioma, t, trocar } = useIdioma();
  const caminho = usePathname();
  const [tema, setTema] = useState("light");
  const [aberto, setAberto] = useState(false);
  const [demo, setDemo] = useState(false);

  useEffect(() => {
    setTema(document.documentElement.getAttribute("data-theme") || "light");
    api.saude().then((s) => setDemo(s.modo_demonstracao)).catch(() => setDemo(false));
  }, []);
  useEffect(() => setAberto(false), [caminho]);

  const trocarTema = () => {
    const novo = tema === "dark" ? "light" : "dark";
    setTema(novo);
    document.documentElement.setAttribute("data-theme", novo);
    try {
      localStorage.setItem("chiocca-tema", novo);
    } catch {}
  };

  return (
    <header className="topo">
      <div className="wrap topo-in">
        <Link href="/" className="logo">
          Chiocca <span>System</span>
        </Link>
        <button className="menu-btn" aria-expanded={aberto} aria-controls="nav" onClick={() => setAberto(!aberto)}>
          {t.menu}
        </button>
        <nav id="nav" className={`nav${aberto ? " aberto" : ""}`}>
          <Link href="/" className={caminho === "/" ? "on" : ""}>
            {t.nav_buscar}
          </Link>
          <Link href="/como-o-motor-foi-testado" className={caminho?.startsWith("/como") ? "on" : ""}>
            {t.nav_testado}
          </Link>
          <button className="botao-borda" onClick={() => { trocar(); setAberto(false); }} lang={idioma === "pt" ? "en" : "pt"}>
            {t.idioma}
          </button>
          <button className="botao-borda" onClick={() => { trocarTema(); setAberto(false); }} aria-label={tema === "dark" ? t.tema_claro : t.tema_escuro}>
            {tema === "dark" ? "☀" : "☾"}
          </button>
        </nav>
      </div>
      <div className="aviso" role="note">
        <div className="wrap">
          <strong>{idioma === "pt" ? "Aviso" : "Notice"}:</strong> {AVISO[idioma]}
        </div>
      </div>
      {demo && (
        <div className="demo" role="status">
          <div className="wrap">{t.demonstracao}</div>
        </div>
      )}
    </header>
  );
}
