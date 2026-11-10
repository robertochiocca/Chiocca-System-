// Texto livre do JSON com os caminhos de arquivo do repositório (ex.: docs/resultados.md) virando link para o
// arquivo no GitHub. O resto do texto fica como veio.
import { REPOSITORIO } from "@/lib/textos";

const CAMINHO = /((?:docs|data|chiocca|tests|web|scripts|resultados)\/[\w\-./]*[\w\-])/g;

export default function TextoComLinks({ texto }: { texto: string | null | undefined }) {
  if (!texto) return null;
  const partes = texto.split(CAMINHO);
  return (
    <>
      {partes.map((p, i) =>
        i % 2 === 1 ? (
          <a key={i} href={`${REPOSITORIO}${p}`} rel="noopener noreferrer" target="_blank">
            {p}
          </a>
        ) : (
          p
        ),
      )}
    </>
  );
}
