# STAGE 1: BASE
# Imagen base ligera con Alpine Linux + compatibilidad de librerías C (glibc/musl)
FROM node:22-alpine AS base

# Librería de compatibilidad requerida por SWC (compilador de Next.js escrito en Rust)
# Evita fallos de segmentación (SIGSEGV) y errores al cargar módulos nativos en Alpine
RUN apk add --no-cache libc6-compat


# Configuración del PATH global para pnpm gestionado vía Corepack
ENV PNPM_HOME="/pnpm"
ENV PATH="$PNPM_HOME:$PATH"


# Desactiva la recolección de telemetría de Next.js a nivel de compilación y runtime
ENV NEXT_TELEMETRY_DISABLED=1

# Habilita Corepack nativo de Node.js para usar pnpm sin instalación manual
RUN corepack enable


# STAGE 2: DEPENDENCIES (DEPS)
# Instalación congelada de dependencias con caché de capas montado en BuildKit
FROM base AS deps
WORKDIR /app

# Copia de manifiestos usando wildcards (*) para evitar fallos de build
# si el proyecto no utiliza un workspace de pnpm (pnpm-workspace.yaml)
COPY package.json pnpm-lock.yaml* pnpm-workspace.yaml* ./

# Cache Mount: Persiste el store de pnpm entre compilaciones locales/CI.
# Evita descargar paquetes repetidos si el pnpm-lock.yaml no ha cambiado.
RUN --mount=type=cache,id=pnpm,target=/pnpm/store \
    pnpm install --frozen-lockfile


# STAGE 3: BUILDER
# Compilación del bundle estático y generación del output standalone
FROM base AS builder
WORKDIR /app

# ARGs recibidos en build-time para quemar (bake) las variables NEXT_PUBLIC_* en el cliente JS.
# Valores por defecto alineados a la arquitectura de Reverse Proxy / API Key.
ARG NEXT_PUBLIC_API_URL=
ARG NEXT_PUBLIC_API_KEY=local-community-api-key-change-me
ARG NEXT_PUBLIC_WHATSAPP_URL=
ARG NEXT_PUBLIC_INSTAGRAM_URL=
ARG NEXT_PUBLIC_MEETUP_URL=
ARG NEXT_PUBLIC_TELEGRAM_URL=
ARG NEXT_PUBLIC_LINKEDIN_URL=

ENV NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL
ENV NEXT_PUBLIC_API_KEY=$NEXT_PUBLIC_API_KEY
ENV NEXT_PUBLIC_WHATSAPP_URL=$NEXT_PUBLIC_WHATSAPP_URL
ENV NEXT_PUBLIC_INSTAGRAM_URL=$NEXT_PUBLIC_INSTAGRAM_URL
ENV NEXT_PUBLIC_MEETUP_URL=$NEXT_PUBLIC_MEETUP_URL
ENV NEXT_PUBLIC_TELEGRAM_URL=$NEXT_PUBLIC_TELEGRAM_URL
ENV NEXT_PUBLIC_LINKEDIN_URL=$NEXT_PUBLIC_LINKEDIN_URL

# Traemos el node_modules ya resuelto desde la etapa 'deps'
COPY --from=deps /app/node_modules ./node_modules
COPY . .

# Genera la carpeta .next/standalone (requiere output: 'standalone' en next.config)
RUN pnpm build


# STAGE 4: RUNTIME (RUNNER)
# Entorno final de ejecución sin dependencias de compilación ni privilegios root
FROM node:22-alpine AS runner
WORKDIR /app

ENV NODE_ENV=production
ENV PORT=3000
ENV HOSTNAME=0.0.0.0
ENV NEXT_TELEMETRY_DISABLED=1

# Principio de Menor Privilegio: Crear grupo y usuario del sistema no-root
RUN addgroup --system --gid 1001 nodejs && \
    adduser --system --uid 1001 nextjs

# Copiar activos públicos asignando el ownership correcto al usuario no-root
COPY --from=builder --chown=nextjs:nodejs /app/public ./public

# Copiar el servidor embebido generado por el modo standalone de Next.js
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./

# Copiar activos estáticos dentro de la ruta requerida por el servidor standalone
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static

# Cambiar del usuario root al usuario sin privilegios
USER nextjs

EXPOSE 3000

# Iniciar el servidor Node.js ultra-liviano generado por el build standalone
CMD ["node", "server.js"]