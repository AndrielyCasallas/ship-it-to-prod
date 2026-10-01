# STAGE 1: BUILDER
# Utiliza la imagen oficial de 'uv' sobre Debian Bookworm Slim para compilar
# el entorno virtual (.venv) y resolver dependencias a máxima velocidad.
FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim AS builder

WORKDIR /app

# Pre-compila el bytecode de Python (.pyc) para acelerar el arranque en frío (cold start)
ENV UV_COMPILE_BYTECODE=1

# Copia paquetes en lugar de crear symlinks hacia el almacén global de uv
ENV UV_LINK_MODE=copy

# OPTIMIZACIÓN DE LAYER CACHING CON BUILDKIT
# 1. Montamos el caché global de uv en '/root/.cache/uv' para reutilizar wheels descargadas.
# 2. Usamos 'bind mount' para pyproject.toml y uv.lock: evita copiar archivos a la capa
#    y solo invalida el caché si el lockfile o manifiesto cambian.
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --frozen --no-install-project --no-dev

# Copiamos el código fuente de la aplicación
COPY . /app

# Sincronizamos el proyecto completo para instalar el paquete principal en el .venv
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev


# STAGE 2: RUNTIME
# Imagen final minimalista basada en Python 3.12 Slim.
# Excluye herramientas de compilación, uv, git y archivos temporales de build.
FROM python:3.12-slim-bookworm AS runtime

WORKDIR /app

# SEGURIDAD Y PERMISOS DE PERSISTENCIA (NON-ROOT)
# 1. Crear grupo y usuario de sistema sin privilegios de root (UID/GID 1001).
# 2. Crear '/app/data' donde SQLite guardará la base de datos en el volumen.
# 3. Transferir ownership del directorio de trabajo al usuario sin privilegios.
RUN addgroup --system --gid 1001 appgroup && \
    adduser --system --uid 1001 --gid 1001 appuser && \
    mkdir -p /app/data && \
    chown -R appuser:appgroup /app/data /app

# Copiar exclusivamente el virtualenv compilado y la estructura de la aplicación
# aplicando ownership durante el COPY para evitar la duplicación de capas pesadas.
COPY --from=builder --chown=appuser:appgroup /app/.venv /app/.venv
COPY --from=builder --chown=appuser:appgroup /app /app

# VARIABLES DE ENTORNO EN RUNTIME
# Inyecta los ejecutables del entorno virtual (.venv/bin) al PATH del sistema
ENV PATH="/app/.venv/bin:$PATH"

# Desactiva el buffering de salida en Python (logs fluyen en tiempo real a stdout/stderr)
ENV PYTHONUNBUFFERED=1

# Evita que Python intente escribir archivos .pyc en runtime como usuario no-root
ENV PYTHONDONTWRITEBYTECODE=1

# Ruta absoluta de SQLite apuntando al directorio persistente de volumen
ENV DATABASE_URL="sqlite:////app/data/community.db"

# Cambiar de root al usuario sin privilegios
USER appuser

EXPOSE 8000

# Punto de entrada de la API con Uvicorn escuchando en todas las interfaces de red
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]