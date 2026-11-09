"use client";

// Idioma da interface (PT ou EN), guardado no navegador. O padrão é o português.
import { createContext, useContext, useEffect, useState } from "react";
import { TEXTOS, type Textos } from "./textos";
import type { Idioma } from "./tipos";

const Contexto = createContext<{ idioma: Idioma; t: Textos; trocar: () => void }>({
  idioma: "pt",
  t: TEXTOS.pt,
  trocar: () => {},
});

export function ProvedorIdioma({ children }: { children: React.ReactNode }) {
  const [idioma, setIdioma] = useState<Idioma>("pt");
  useEffect(() => {
    try {
      const salvo = localStorage.getItem("chiocca-idioma");
      if (salvo === "pt" || salvo === "en") setIdioma(salvo);
    } catch {}
  }, []);
  useEffect(() => {
    document.documentElement.lang = idioma === "pt" ? "pt-BR" : "en";
  }, [idioma]);
  const trocar = () => {
    const novo: Idioma = idioma === "pt" ? "en" : "pt";
    setIdioma(novo);
    try {
      localStorage.setItem("chiocca-idioma", novo);
    } catch {}
  };
  return <Contexto.Provider value={{ idioma, t: TEXTOS[idioma] as Textos, trocar }}>{children}</Contexto.Provider>;
}

export function useIdioma() {
  return useContext(Contexto);
}
