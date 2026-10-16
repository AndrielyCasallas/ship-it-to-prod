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

La aplicación puede desarrollarse en Linux, macOS o Windows con Docker Desktop.
La automatización de infraestructura de [Ansible](ansible/README.md) requiere
Linux o macOS como equipo de control; en Windows debe ejecutarse mediante WSL2
o desde una máquina Linux/macOS. El host remoto administrado por Ansible debe
ser Linux.

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

Los conceptos de entrega continua están resumidos en
[snipsheets/06-ci-cd-github-actions.md](snipsheets/06-ci-cd-github-actions.md).

## Infraestructura opcional

El directorio `terraform/` contiene la infraestructura opcional para crear un
contenedor en Proxmox y `ansible/` contiene la configuración posterior del
servidor. Este flujo no es necesario para ejecutar la aplicación localmente.

1. Revisa [terraform/README.md](terraform/README.md) para la infraestructura.
2. Revisa [ansible/README.md](ansible/README.md) para la configuración.
3. Copia `terraform.tfvars.example` a `terraform.tfvars` y completa los
   valores únicamente en tu máquina.
4. Ejecuta `terraform plan` y revisa el resultado antes de aplicar cambios.
5. Mantén los inventarios, claves, tokens, contraseñas y estados fuera de Git.

No reutilices credenciales que hayan aparecido en capturas, commits, logs o
archivos compartidos. Revócalas y genera reemplazos antes de desplegar.

La infraestructura de ejemplo no es un módulo listo para producción. Requiere
un proveedor Proxmox, conectividad SSH, un inventario local y permisos
administrativos. No expongas los puertos de observabilidad sin autenticación y
no uses los valores de ejemplo en una red real.

## Mapas conceptuales

La carpeta [snipsheets/](snipsheets/) contiene únicamente diagramas y
conceptos públicos sobre arquitectura, contenedores, persistencia, CI/CD,
infraestructura y observabilidad. No contiene guiones privados ni
instrucciones de acceso a entornos reales.
