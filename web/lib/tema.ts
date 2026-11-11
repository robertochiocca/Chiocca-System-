"use client";

// Tema claro ou escuro: o atributo data-theme do <html>, guardado no navegador (o script do layout aplica antes da
// hidratação, para não piscar). Usado pelo botão do cabeçalho e pelo seletor do menu do celular.
import { useCallback, useEffect, useState } from "react";

export type Tema = "light" | "dark";

export function useTema(): [Tema, (t: Tema) => void] {
  const [tema, setTema] = useState<Tema>("light");
  useEffect(() => {
    setTema(document.documentElement.getAttribute("data-theme") === "dark" ? "dark" : "light");
  }, []);
  const definir = useCallback((novo: Tema) => {
    setTema(novo);
    document.documentElement.setAttribute("data-theme", novo);
    try {
      localStorage.setItem("chiocca-tema", novo);
    } catch {}
  }, []);
  return [tema, definir];
}
