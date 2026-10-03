import asyncio
import logging
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import AsyncIterator

from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from .bot import run_bot
from .config import settings
from .database import (
    count_completed_events,
    create_project_proposal,
    create_speaker,
    database_is_connected,
    init_db,
    list_attendees,
    list_core_team,
    list_events,
    list_projects,
    list_upcoming_events,
)


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
logging.getLogger("httpx").setLevel(logging.WARNING)


async def require_api_key(x_api_key: str | None = Header(default=None)) -> None:
    """Valida la clave API enviada en la cabecera de la petición.

    La dependencia protege todos los endpoints públicos del backend y
    diferencia entre una configuración ausente y una credencial inválida.
    """
    if not settings.api_key:
        raise HTTPException(status_code=500, detail="API_KEY no configurada")
    if x_api_key != settings.api_key:
        raise HTTPException(status_code=401, detail="API key inválida")


@asynccontextmanager
async def lifespan(application: FastAPI) -> AsyncIterator[None]:
    """Inicializa recursos al arrancar la API y los libera al cerrarla.

    Crea las tablas necesarias y, cuando existe un token, mantiene activo el
    bot de Telegram durante toda la vida de la aplicación.
    """
    await init_db()
    bot_task: asyncio.Task[None] | None = None
    if settings.bot_token:
        bot_task = asyncio.create_task(run_bot())
    else:
        logger.warning("BOT_TOKEN no configurado; se iniciará solo la API.")

    try:
        yield
    finally:
        if bot_task:
            bot_task.cancel()
            await asyncio.gather(bot_task, return_exceptions=True)


app = FastAPI(
    title="Community Telegram Backend",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in settings.cors_origins.split(",")],
    allow_credentials=False,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "X-API-Key"],
)


class ProjectProposalRequest(BaseModel):
    name: str = Field(min_length=1)
    manager: str = Field(min_length=1)
    contact_phone: str | None = None
    contact_email: str | None = None
    description: str = Field(min_length=1)


class SpeakerRequest(BaseModel):
    name: str = Field(min_length=1)
    company: str | None = None
    job_title: str | None = None
    email: str | None = None
    phone: str | None = None


@app.get("/health", dependencies=[Depends(require_api_key)])
async def health() -> dict[str, str]:
    """Comprueba que la API y la conexión con SQLite estén disponibles."""
    if not await database_is_connected():
        raise HTTPException(status_code=503, detail="Database unavailable")
    return {"status": "ok", "database": "connected"}


@app.get("/api/attendees", dependencies=[Depends(require_api_key)])
async def attendees() -> list[dict[str, str]]:
    """Devuelve la lista de asistentes registrados en la comunidad."""
    return await list_attendees()


@app.get("/api/events", dependencies=[Depends(require_api_key)])
async def events() -> list[dict[str, object]]:
    """Devuelve todos los eventos ordenados desde la capa de persistencia."""
    return await list_events()


@app.get("/api/events/completed/count", dependencies=[Depends(require_api_key)])
async def completed_event_count() -> dict[str, int | str]:
    """Cuenta los eventos cuya fecha ya ocurrió y devuelve la fecha límite."""
    today = datetime.now(timezone.utc).date().isoformat()
    return {"count": await count_completed_events(today), "until": today}


@app.get("/api/events/upcoming", dependencies=[Depends(require_api_key)])
async def upcoming_events() -> list[dict[str, object]]:
    """Devuelve los eventos posteriores a la fecha actual en UTC."""
    today = datetime.now(timezone.utc).date().isoformat()
    return await list_upcoming_events(today)


@app.get("/api/projects/ongoing", dependencies=[Depends(require_api_key)])
async def ongoing_projects() -> list[dict[str, object]]:
    """Obtiene los proyectos activos para mostrarlos en la página principal."""
    return await list_projects(page=1, page_size=1000, status="ongoing")


@app.post("/api/project-proposals", status_code=201, dependencies=[Depends(require_api_key)])
async def project_proposal(payload: ProjectProposalRequest) -> dict[str, int]:
    """Guarda una propuesta de proyecto enviada desde la comunidad."""
    proposal_id = await create_project_proposal(**payload.model_dump())
    return {"id": proposal_id}


@app.post("/api/speakers", status_code=201, dependencies=[Depends(require_api_key)])
async def speaker_registration(payload: SpeakerRequest) -> dict[str, int]:
    """Registra los datos de una persona interesada en ser speaker."""
    speaker_id = await create_speaker(**payload.model_dump())
    return {"id": speaker_id}


@app.get("/api/core-team", dependencies=[Depends(require_api_key)])
async def core_team() -> list[dict[str, object]]:
    """Devuelve los integrantes del equipo principal de la comunidad."""
    return await list_core_team()


async def serve() -> None:
    """Configura y ejecuta el servidor ASGI con los valores de Settings."""
    import uvicorn

    config = uvicorn.Config(
        app,
        host=settings.api_host,
        port=settings.api_port,
        reload=False,
    )
    server = uvicorn.Server(config)
    await server.serve()


if __name__ == "__main__":
    asyncio.run(serve())
