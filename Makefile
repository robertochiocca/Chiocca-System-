# make demo (pedido de 21/11/2026): um comando só para ver a demonstração no computador, com os dados de amostra já
# versionados (docs/exemplos/), sem baixar nada da CVM, sem API e sem tocar nos exercícios de 2024 em diante. Precisa de
# Node.js 22 ou mais. A porta é 3000; para outra, make demo PORTA=8080. O CI confere este alvo (job demo).
PORTA ?= 3000

.PHONY: demo

# npm ci só quando o package-lock.json muda (o npm grava node_modules/.package-lock.json ao instalar)
web/node_modules/.package-lock.json: web/package-lock.json
	cd web && npm ci

demo: web/node_modules/.package-lock.json
	cd web && NEXT_TELEMETRY_DISABLED=1 NEXT_PUBLIC_BASE_PATH= npm run build:estatico
	cd web && PORTA=$(PORTA) node scripts/demonstracao-local.mjs
