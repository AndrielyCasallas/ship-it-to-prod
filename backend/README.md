# Community Telegram Backend

Backend modular con FastAPI, SQLite asíncrono y `python-telegram-bot`.

## Arranque

```bash
uv sync
cp .env.example .env
# Completa BOT_TOKEN, SUPERUSER_TELEGRAM_ID y API_KEY
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000
```

La API queda disponible en `http://localhost:8000/docs`.

Todas las peticiones HTTP requieren el header:

```http
X-API-Key: el-mismo-valor-de-API_KEY
```

El frontend usa ese mismo valor mediante `NEXT_PUBLIC_API_KEY`.

## API HTTP

- `GET /api/events/completed/count`: devuelve `{ "count": 0, "until": "YYYY-MM-DD" }`.
- `GET /api/events/upcoming`: eventos posteriores a la fecha UTC actual.
- `GET /api/projects/ongoing`: proyectos con estado `ongoing`.
- `POST /api/project-proposals`: recibe `name`, `manager`, `description`, y opcionalmente `contact_phone` y `contact_email`.
- `POST /api/speakers`: recibe `name`, y opcionalmente `company`, `job_title`, `email` y `phone`.
- `GET /api/core-team`: devuelve nombre, cargo y `instagram`, `linkedin`, `github`.
- `GET /api/attendees`: devuelve los asistentes registrados.

Ejemplo de alta de propuesta:

```json
{
	"name": "Plataforma de mentorías",
	"manager": "Ana Pérez",
	"contact_email": "ana@example.com",
	"contact_phone": "+51999999999",
	"description": "Comunidad para conectar mentores y estudiantes."
}
```

## Crear eventos desde Telegram

El superusuario configurado en `SUPERUSER_TELEGRAM_ID` puede usar:

```text
/crear_evento Título del evento | 2026-10-15 | Descripción del evento
```

Todas las fechas de eventos deben usar exclusivamente el formato `YYYY-MM-DD`.

También pueden hacerlo los usuarios con rol `admin`. Para promover un usuario:

```text
/hacer_admin 123456789
```

Comandos administrativos adicionales:

```text
/speakers
/proyectos 1
/propuestas
/crear_proyecto Título | Descripción | Encargado | Repo URL | Landing URL
/editar_proyecto ID | Título | Descripción | Encargado | Repo URL | Landing URL | ongoing
/eliminar_proyecto ID
/core_team
/agregar_core Telegram ID | Nombre | Cargo | Instagram | LinkedIn | GitHub
/editar_core ID | Telegram ID | Nombre | Cargo | Instagram | LinkedIn | GitHub
/eliminar_core ID
```

`/proyectos` muestra cinco proyectos por página. Para avanzar, usa `/proyectos 2`, `/proyectos 3`, etc. Todos los proyectos y miembros del core team tienen un ID numérico estable.

Las redes sociales del core team son opcionales. Por ejemplo, también es válido:

```text
/agregar_core 12312312 | Santiago Arrigui | Lider | https://www.instagram.com/santiarrigui/ | https://www.linkedin.com/in/santiago-arrigui-2666a5395/
```

El campo GitHub quedará guardado como `null`.
