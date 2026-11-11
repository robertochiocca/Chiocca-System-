"use client";

// Idioma da interface (PT ou EN), guardado no navegador. O padrão é o português.
import { createContext, useContext, useEffect, useState } from "react";
import { TEXTOS, type Textos } from "./textos";
import type { Idioma } from "./tipos";

const Contexto = createContext<{ idioma: Idioma; t: Textos; trocar: () => void; definir: (i: Idioma) => void }>({
  idioma: "pt",
  t: TEXTOS.pt,
  trocar: () => {},
  definir: () => {},
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
  const definir = (novo: Idioma) => {
    setIdioma(novo);
    try {
      localStorage.setItem("chiocca-idioma", novo);
    } catch {}
  };
  const trocar = () => definir(idioma === "pt" ? "en" : "pt");
  return (
    <Contexto.Provider value={{ idioma, t: TEXTOS[idioma] as Textos, trocar, definir }}>{children}</Contexto.Provider>
  );
}

export function useIdioma() {
  return useContext(Contexto);
}
