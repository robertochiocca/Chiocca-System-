"use client";

// Botão "?" de ajuda: abre o verbete do glossário (lib/glossario.ts, PT e EN) logo abaixo, sem sair da página.
// É um botão de verdade (aria-expanded), fecha com Esc ou com o botão "Fechar".
import Link from "next/link";
import { useEffect, useId, useState } from "react";
import { GLOSSARIO, type ChaveGlossario } from "@/lib/glossario";
import { useIdioma } from "@/lib/idioma";
import { fmt } from "@/lib/textos";

export default function Ajuda({ chave, anos }: { chave: ChaveGlossario; anos?: { a: number; b: number } }) {
  const { idioma, t } = useIdioma();
  const [aberto, setAberto] = useState(false);
  const id = useId();
  const v = GLOSSARIO[idioma][chave];
  useEffect(() => {
    if (!aberto) return;
    const aoTeclar = (e: KeyboardEvent) => e.key === "Escape" && setAberto(false);
    document.addEventListener("keydown", aoTeclar);
    return () => document.removeEventListener("keydown", aoTeclar);
  }, [aberto]);
  return (
    <span className="ajuda">
      <button
        type="button"
        className="ajuda-btn"
        aria-expanded={aberto}
        aria-controls={id}
        aria-label={fmt(t.ajuda, { t: v.titulo })}
        onClick={() => setAberto(!aberto)}
      >
        <span aria-hidden="true">?</span>
      </button>
      {aberto && (
        <span id={id} role="note" className="ajuda-caixa">
          <strong>{v.titulo}.</strong> {fmt(v.texto, anos ?? { a: "—", b: "—" })}{" "}
          {v.testado && <Link href="/como-o-motor-foi-testado">{t.nav_testado}</Link>}
          <button type="button" className="botao leve pequeno" onClick={() => setAberto(false)}>
            {t.fechar}
          </button>
        </span>
      )}
    </span>
  );
}
