"use client";

// Barra fixa de todas as telas: navegação, idioma, tema, aviso fixo e, se ligado, o aviso do modo demonstração.
// Origem do padrão de tema e do menu compacto: DireitoAberto (github.com/robertochiocca/DireitoAberto),
// web/components/Nav.tsx e web/app/layout.tsx, commit 102e3e2d9d70e87249d8df9215737e2d98b6358d, licença MIT.
// Adaptado para o Chiocca System: sem conta nem login; idioma PT/EN; aviso fixo dentro da barra; no celular, o menu
// é um painel de tela inteira com fundo sólido, que fecha ao navegar, ao tocar fora dos itens ou com Esc.
import Link from "next/link";
import { usePathname, useSearchParams } from "next/navigation";
import { Suspense, useCallback, useEffect, useRef, useState } from "react";
import { AVISO } from "@/lib/contrato.mjs";
import { api, MODO_ESTATICO } from "@/lib/api";
import { useIdioma } from "@/lib/idioma";

function Barra() {
  const { idioma, t, trocar } = useIdioma();
  const caminho = usePathname();
  const busca = useSearchParams();
  const [tema, setTema] = useState("light");
  const [aberto, setAberto] = useState(false);
  const [demo, setDemo] = useState(false);
  const botao = useRef<HTMLButtonElement>(null);

  useEffect(() => {
    setTema(document.documentElement.getAttribute("data-theme") || "light");
    if (!MODO_ESTATICO) api.saude().then((s) => setDemo(s.modo_demonstracao)).catch(() => setDemo(false));
  }, []);

  const fechar = useCallback((devolverFoco = false) => {
    setAberto(false);
    if (devolverFoco) botao.current?.focus();
  }, []);

  // Navegar (inclusive só trocando os parâmetros da página) fecha o menu.
  useEffect(() => setAberto(false), [caminho, busca]);

  // Com o menu aberto: Esc fecha e a página atrás não rola.
  useEffect(() => {
    if (!aberto) return;
    const aoTeclar = (e: KeyboardEvent) => e.key === "Escape" && fechar(true);
    document.addEventListener("keydown", aoTeclar);
    document.documentElement.classList.add("menu-aberto");
    return () => {
      document.removeEventListener("keydown", aoTeclar);
      document.documentElement.classList.remove("menu-aberto");
    };
  }, [aberto, fechar]);

  const trocarTema = () => {
    const novo = tema === "dark" ? "light" : "dark";
    setTema(novo);
    document.documentElement.setAttribute("data-theme", novo);
    try {
      localStorage.setItem("chiocca-tema", novo);
    } catch {}
  };
  // O rótulo diz o tema para o qual o botão leva: no claro, "Tema escuro"; no escuro, "Tema claro".
  const rotuloTema = tema === "dark" ? t.tema_claro : t.tema_escuro;

  return (
    <header className="topo">
      <div className="wrap topo-in">
        <Link href="/" className="logo">
          Chiocca <span>System</span>
        </Link>
        <button
          ref={botao}
          className="menu-btn"
          aria-expanded={aberto}
          aria-controls="nav"
          aria-label={aberto ? t.fechar_menu : t.menu}
          onClick={() => setAberto(!aberto)}
        >
          {aberto ? "✕" : t.menu}
        </button>
        <nav
          id="nav"
          className={`nav${aberto ? " aberto" : ""}`}
          onClick={(e) => {
            // Tocar fora dos itens (no fundo do painel) fecha o menu.
            if (e.target === e.currentTarget) fechar();
          }}
        >
          <Link href="/" className={caminho === "/" ? "on" : ""} onClick={() => fechar()}>
            {t.nav_buscar}
          </Link>
          <Link href="/como-o-motor-foi-testado" className={caminho?.startsWith("/como") ? "on" : ""} onClick={() => fechar()}>
            {t.nav_testado}
          </Link>
          <button
            className="botao-borda"
            onClick={() => {
              trocar();
              fechar();
            }}
            lang={idioma === "pt" ? "en" : "pt"}
          >
            {t.idioma}
          </button>
          <button
            className="botao-borda botao-tema"
            onClick={() => {
              trocarTema();
              fechar();
            }}
            aria-label={rotuloTema}
            title={rotuloTema}
          >
            <span aria-hidden="true">{tema === "dark" ? "☀" : "☾"}</span>
            <span className="rotulo-tema">{rotuloTema}</span>
          </button>
          <p className="aviso-menu" role="note">
            {AVISO[idioma]}
          </p>
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
      {MODO_ESTATICO && (
        <div className="demo" role="status">
          <div className="wrap">{t.estatico_busca}</div>
        </div>
      )}
    </header>
  );
}

export default function Topo() {
  return (
    <Suspense>
      <Barra />
    </Suspense>
  );
}
