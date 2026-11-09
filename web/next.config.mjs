// Origem: DireitoAberto (github.com/robertochiocca/DireitoAberto), web/next.config.mjs,
// commit 102e3e2d9d70e87249d8df9215737e2d98b6358d, licença MIT. Adaptado para o Chiocca System:
// sem fontes externas nem PDF do usuário; o PDF da investigação vem da API (mesma origem, pelo rewrite).

/** @type {import('next').NextConfig} */
const API_URL = process.env.API_URL ?? "http://127.0.0.1:8000";

// Política de segurança de conteúdo. script-src com 'unsafe-inline': o Next injeta scripts inline de hidratação e
// há o script do tema; trocar por nonce exige renderização dinâmica.
const CSP = [
  "default-src 'self'",
  "script-src 'self' 'unsafe-inline'" + (process.env.NODE_ENV === "production" ? "" : " 'unsafe-eval'"),
  "style-src 'self' 'unsafe-inline'",
  "font-src 'self'",
  "img-src 'self' data:",
  "connect-src 'self'",
  "frame-src 'self'",
  "object-src 'none'",
  "base-uri 'self'",
  "form-action 'self'",
  "frame-ancestors 'none'",
].join("; ");

const nextConfig = {
  poweredByHeader: false,
  // A investigação calcula o corte transversal na data (dezenas de segundos na primeira vez; depois vem do cache
  // da API). O proxy padrão do Next corta em 30 s; aqui, 5 minutos.
  experimental: { proxyTimeout: 300_000 },
  async rewrites() {
    // O navegador chama /api/... no próprio Next; o Next repassa à API do Chiocca (FastAPI).
    return [{ source: "/api/:path*", destination: `${API_URL}/api/:path*` }];
  },
  async headers() {
    return [
      {
        source: "/:path*",
        headers: [
          { key: "Content-Security-Policy", value: CSP },
          { key: "X-Content-Type-Options", value: "nosniff" },
          { key: "Referrer-Policy", value: "strict-origin-when-cross-origin" },
          { key: "X-Frame-Options", value: "DENY" },
          { key: "Permissions-Policy", value: "camera=(), microphone=(), geolocation=()" },
        ],
      },
    ];
  },
};

export default nextConfig;
