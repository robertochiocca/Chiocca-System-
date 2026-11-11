"use client";

// Cabeçalho de todas as telas (Fase E2): marca, navegação, idioma "PT | EN" lado a lado (aria-pressed) e tema, com
// ícone e rótulo acessível. Só o aviso fica fixo, numa linha compacta (no celular, a versão curta com "Saiba mais",
// que leva ao texto completo no rodapé); a faixa da demonstração fica no topo da página, sem ficar fixa. No celular, o menu é um diálogo de tela cheia: Buscar, Como o motor foi testado, Ficha do motor,
// "Idioma: Português | English" e "Tema: Claro | Escuro", com o aviso no pé; fecha ao navegar, ao tocar fora dos
// itens, com Esc e com o botão de fechar.
// Origem do padrão de tema e do menu compacto: DireitoAberto (github.com/robertochiocca/DireitoAberto),
// web/components/Nav.tsx e web/app/layout.tsx, commit 102e3e2d9d70e87249d8df9215737e2d98b6358d, licença MIT.
import Link from "next/link";
import { usePathname, useSearchParams } from "next/navigation";
import { Suspense, useCallback, useEffect, useRef, useState } from "react";
import { AVISO } from "@/lib/contrato.mjs";
import { api, MODO_ESTATICO } from "@/lib/api";
import { useIdioma } from "@/lib/idioma";
import { REPOSITORIO } from "@/lib/textos";
import { useTema } from "@/lib/tema";

export function linkFicha(idioma: "pt" | "en"): string {
  return `${REPOSITORIO}${idioma === "pt" ? "docs/ficha-do-motor.md" : "docs/en/engine-card.md"}`;
}

function Barra() {
  const { idioma, t, definir } = useIdioma();
  const [tema, definirTema] = useTema();
  const caminho = usePathname();
  const busca = useSearchParams();
  const [aberto, setAberto] = useState(false);
  const [demo, setDemo] = useState(false);
  const botaoMenu = useRef<HTMLButtonElement>(null);
  const botaoFechar = useRef<HTMLButtonElement>(null);

  useEffect(() => {
    if (!MODO_ESTATICO) api.saude().then((s) => setDemo(s.modo_demonstracao)).catch(() => setDemo(false));
  }, []);

  const fechar = useCallback((devolverFoco = false) => {
    setAberto(false);
    if (devolverFoco) botaoMenu.current?.focus();
  }, []);

  // Navegar (inclusive só trocando os parâmetros da página) fecha o menu.
  useEffect(() => setAberto(false), [caminho, busca]);

  // Com o menu aberto: foco no botão de fechar, Esc fecha e a página atrás não rola.
  useEffect(() => {
    if (!aberto) return;
    botaoFechar.current?.focus();
    const aoTeclar = (e: KeyboardEvent) => e.key === "Escape" && fechar(true);
    document.addEventListener("keydown", aoTeclar);
    document.documentElement.classList.add("menu-aberto");
    return () => {
      document.removeEventListener("keydown", aoTeclar);
      document.documentElement.classList.remove("menu-aberto");
    };
  }, [aberto, fechar]);

  // O rótulo do botão diz o tema para o qual ele leva: no claro, "Tema escuro"; no escuro, "Tema claro".
  const rotuloTema = tema === "dark" ? t.tema_claro : t.tema_escuro;
  const ficha = linkFicha(idioma);

  return (
    <>
      <header className="topo">
        <div className="wrap topo-in">
          <Link href="/" className="logo">
            Chiocca <span>System</span>
          </Link>
          <nav className="nav-principal" aria-label={t.menu}>
            <Link href="/" aria-current={caminho === "/" ? "page" : undefined}>
              {t.nav_buscar}
            </Link>
            <Link href="/como-o-motor-foi-testado" aria-current={caminho?.startsWith("/como") ? "page" : undefined}>
              {t.nav_testado}
            </Link>
            <a href={ficha} rel="noopener noreferrer" target="_blank">
              {t.nav_ficha} ↗
            </a>
          </nav>
          <div className="controles">
            <div className="segmentado" role="group" aria-label={t.idioma_rotulo}>
              <button type="button" aria-pressed={idioma === "pt"} lang="pt" onClick={() => definir("pt")}>
                PT
              </button>
              <button type="button" aria-pressed={idioma === "en"} lang="en" onClick={() => definir("en")}>
                EN
              </button>
            </div>
            <button
              type="button"
              className="botao-icone"
              aria-label={rotuloTema}
              title={rotuloTema}
              onClick={() => definirTema(tema === "dark" ? "light" : "dark")}
            >
              <span aria-hidden="true">{tema === "dark" ? "☀" : "☾"}</span>
            </button>
          </div>
          <button
            ref={botaoMenu}
            type="button"
            className="menu-btn"
            aria-expanded={aberto}
            aria-controls="menu-celular"
            onClick={() => setAberto(true)}
          >
            {t.menu}
          </button>
        </div>
      </header>
      {aberto && (
        <div
          id="menu-celular"
          className="menu-celular"
          role="dialog"
          aria-modal="true"
          aria-label={t.menu}
          onClick={(e) => {
            // Tocar fora dos itens (no fundo do painel) fecha o menu.
            if (e.target === e.currentTarget) fechar();
          }}
        >
          <div className="menu-celular-topo" onClick={(e) => e.target === e.currentTarget && fechar()}>
            <span className="logo">
              Chiocca <span>System</span>
            </span>
            <button ref={botaoFechar} type="button" className="botao-icone" aria-label={t.fechar_menu} onClick={() => fechar(true)}>
              <span aria-hidden="true">✕</span>
            </button>
          </div>
          <nav className="menu-celular-itens" aria-label={t.menu}>
            <Link href="/" onClick={() => fechar()}>
              {t.nav_buscar}
            </Link>
            <Link href="/como-o-motor-foi-testado" onClick={() => fechar()}>
              {t.nav_testado}
            </Link>
            <a href={ficha} rel="noopener noreferrer" target="_blank" onClick={() => fechar()}>
              {t.nav_ficha} ↗
            </a>
          </nav>
          <div className="menu-celular-opcao">
            <span id="rotulo-idioma">{t.idioma_rotulo}</span>
            <div className="segmentado largo" role="group" aria-labelledby="rotulo-idioma">
              <button type="button" aria-pressed={idioma === "pt"} lang="pt" onClick={() => definir("pt")}>
                {t.idioma_pt}
              </button>
              <button type="button" aria-pressed={idioma === "en"} lang="en" onClick={() => definir("en")}>
                {t.idioma_en}
              </button>
            </div>
          </div>
          <div className="menu-celular-opcao">
            <span id="rotulo-tema">{t.tema_rotulo}</span>
            <div className="segmentado largo" role="group" aria-labelledby="rotulo-tema">
              <button type="button" aria-pressed={tema === "light"} onClick={() => definirTema("light")}>
                {t.tema_claro_curto}
              </button>
              <button type="button" aria-pressed={tema === "dark"} onClick={() => definirTema("dark")}>
                {t.tema_escuro_curto}
              </button>
            </div>
          </div>
          <p className="aviso-menu" role="note">
            {AVISO[idioma]}
          </p>
        </div>
      )}
      <div className="aviso" role="note">
        <div className="wrap">
          <span className="aviso-longo">
            <strong>{t.aviso_rotulo}:</strong> {AVISO[idioma]}
          </span>
          <span className="aviso-curto">
            <span className="aviso-curto-frase">{t.aviso_curto}</span> <a href="#aviso-completo">{t.saiba_mais}</a>
          </span>
        </div>
      </div>
      {(MODO_ESTATICO || demo) && (
        <div className="faixa-demo" role="status">
          <div className="wrap">{MODO_ESTATICO ? t.estatico_busca : t.demonstracao}</div>
        </div>
      )}
    </>
  );
}

export default function Topo() {
  return (
    <Suspense>
      <Barra />
    </Suspense>
  );
}
