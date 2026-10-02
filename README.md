# Community Platform: Ship It to Prod

Aplicación de comunidad con frontend Next.js, backend FastAPI, bot de Telegram y SQLite. El repositorio sirve como proyecto práctico para aprender contenedores, persistencia, CI/CD y operación local.

## Arquitectura

```text
Navegador ─────┐
               ├──> Nginx ───> Frontend Next.js
Bot Telegram ──┘              └──> Backend FastAPI ───> SQLite
                                              |
                                              └──> volumen Docker
```

## Requisitos

- Docker Engine y Docker Compose.
- Git.
- Opcional: `uv`, `pnpm` y GitHub CLI (`gh`) para desarrollo local y seguimiento de Actions.

## Inicio rápido con Docker

```bash
cp .env.example .env
docker compose build
docker compose up -d
docker compose ps
```

La aplicación queda detrás del proxy en `http://localhost`. El backend no se publica directamente al host; su healthcheck se consulta dentro de la red de Compose.

Para detener los contenedores sin borrar los datos:

```bash
docker compose down --remove-orphans
```

Para detenerlos y borrar también el volumen de SQLite, solo durante una demostración:

```bash
docker compose down -v --remove-orphans
```

## Variables de entorno

El archivo `.env.example` es una plantilla pública. El archivo `.env` real es local y está ignorado por Git.

- `BOT_TOKEN`: token del bot, solo en runtime.
- `API_KEY`: clave local para proteger la API.
- `DATABASE_URL`: ruta SQLite dentro del contenedor.
- `NEXT_PUBLIC_*`: valores incluidos en el bundle del navegador; no son secretos.
- `BACKEND_IMAGE` y `FRONTEND_IMAGE`: nombres opcionales de imágenes para usar GHCR.

No subir tokens, contraseñas ni archivos `.env` al repositorio.

## Desarrollo backend

```bash
cd backend
uv sync
uv run pytest -q
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## CI/CD

El workflow `.github/workflows/ci-cd.yml` ejecuta tests backend, build frontend y build de las imágenes Docker. En `push` a `main`, `master` o `develop`, publica las imágenes en GHCR. En Pull Requests valida sin publicar.

La documentación línea por línea está en [snipsheets/06-ci-cd-github-actions.md](snipsheets/06-ci-cd-github-actions.md).

## Material de clase

Los guiones y demostraciones están en [snipsheets/README.md](snipsheets/README.md).
