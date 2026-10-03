from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import aiosqlite

from .config import settings


def empty_to_none(value: str | None) -> str | None:
    """Convierte cadenas vacías o con espacios en ``None``."""
    return value.strip() or None if value is not None else None


def normalize_event_date(value: str) -> str:
    """Normaliza una fecha aceptando los formatos habituales de entrada.

    Raises:
        ValueError: Si el texto no representa una fecha válida.
    """
    value = value.strip()
    for pattern in (
        "%Y-%m-%d",
        "%Y/%m/%d",
        "%d/%m/%Y",
        "%d-%m-%Y",
    ):
        try:
            return datetime.strptime(value, pattern).date().isoformat()
        except ValueError:
            continue
    raise ValueError("La fecha debe tener el formato YYYY-MM-DD")


SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    telegram_id INTEGER PRIMARY KEY,
    username TEXT,
    full_name TEXT NOT NULL,
    role TEXT NOT NULL DEFAULT 'user'
        CHECK (role IN ('user', 'admin', 'superuser')),
    created_at TIMESTAMP NOT NULL
);

CREATE TABLE IF NOT EXISTS events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    event_date TEXT NOT NULL,
    created_by INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS attendees (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    telegram_id INTEGER UNIQUE NOT NULL,
    display_name TEXT NOT NULL,
    event_id INTEGER,
    registered_at TIMESTAMP NOT NULL,
    FOREIGN KEY (telegram_id) REFERENCES users (telegram_id),
    FOREIGN KEY (event_id) REFERENCES events (id)
);

CREATE TABLE IF NOT EXISTS projects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    manager TEXT NOT NULL,
    repository_url TEXT NOT NULL,
    landing_page_url TEXT,
    status TEXT NOT NULL DEFAULT 'ongoing'
        CHECK (status IN ('ongoing', 'completed', 'archived')),
    created_at TIMESTAMP NOT NULL
);

CREATE TABLE IF NOT EXISTS project_proposals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    manager TEXT NOT NULL,
    contact_phone TEXT,
    contact_email TEXT,
    description TEXT NOT NULL,
    created_at TIMESTAMP NOT NULL
);

CREATE TABLE IF NOT EXISTS speakers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    company TEXT,
    job_title TEXT,
    email TEXT,
    phone TEXT,
    created_at TIMESTAMP NOT NULL
);

CREATE TABLE IF NOT EXISTS core_team (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    telegram_id INTEGER UNIQUE NOT NULL,
    name TEXT NOT NULL,
    role TEXT NOT NULL,
    instagram TEXT,
    linkedin TEXT,
    github TEXT,
    created_at TIMESTAMP NOT NULL
);
"""


@asynccontextmanager
async def get_connection() -> AsyncIterator[aiosqlite.Connection]:
    """Abre una conexión SQLite configurada y activa claves foráneas."""
    database_path = settings.database_path
    if not database_path.is_absolute():
        database_path = Path.cwd() / database_path
        # Convertir a ruta definitiva a partir de donde se ejecuta el documento
        
    database_path.parent.mkdir(parents=True, exist_ok=True)
    async with aiosqlite.connect(database_path) as connection:
        connection.row_factory = aiosqlite.Row
        await connection.execute("PRAGMA foreign_keys = ON")
        yield connection


async def init_db() -> None:
    """Crea el esquema y corrige datos heredados antes de servir peticiones."""
    async with get_connection() as connection:
        await connection.executescript(SCHEMA)
        cursor = await connection.execute("SELECT id, event_date FROM events")
        existing_events = await cursor.fetchall()
        for event in existing_events:
            try:
                normalized_date = normalize_event_date(str(event["event_date"]))
            except ValueError:
                continue
            if normalized_date != event["event_date"]:
                await connection.execute(
                    "UPDATE events SET event_date = ? WHERE id = ?",
                    (normalized_date, event["id"]),
                )
        await connection.executescript(
            """
            UPDATE projects SET landing_page_url = NULL
            WHERE landing_page_url IS NOT NULL AND TRIM(landing_page_url) = '';
            UPDATE project_proposals SET contact_phone = NULL
            WHERE contact_phone IS NOT NULL AND TRIM(contact_phone) = '';
            UPDATE project_proposals SET contact_email = NULL
            WHERE contact_email IS NOT NULL AND TRIM(contact_email) = '';
            UPDATE speakers SET company = NULL
            WHERE company IS NOT NULL AND TRIM(company) = '';
            UPDATE speakers SET job_title = NULL
            WHERE job_title IS NOT NULL AND TRIM(job_title) = '';
            UPDATE speakers SET email = NULL
            WHERE email IS NOT NULL AND TRIM(email) = '';
            UPDATE speakers SET phone = NULL
            WHERE phone IS NOT NULL AND TRIM(phone) = '';
            UPDATE core_team SET instagram = NULL
            WHERE instagram IS NOT NULL AND TRIM(instagram) = '';
            UPDATE core_team SET linkedin = NULL
            WHERE linkedin IS NOT NULL AND TRIM(linkedin) = '';
            UPDATE core_team SET github = NULL
            WHERE github IS NOT NULL AND TRIM(github) = '';
            """
        )
        await connection.commit()


async def upsert_user(
    telegram_id: int,
    username: str | None,
    full_name: str,
) -> None:
    """Crea o actualiza el perfil de un usuario de Telegram."""
    now = datetime.now(timezone.utc).isoformat()
    async with get_connection() as connection:
        await connection.execute(
            """
            INSERT INTO users (telegram_id, username, full_name, role, created_at)
            VALUES (?, ?, ?, 'user', ?)
            ON CONFLICT(telegram_id) DO UPDATE SET
                username = excluded.username,
                full_name = excluded.full_name
            """,
            (telegram_id, username, full_name, now),
        )
        await connection.commit()


async def get_user_role(telegram_id: int) -> str | None:
    """Obtiene el rol persistido de un usuario, si ya está registrado."""
    async with get_connection() as connection:
        cursor = await connection.execute(
            "SELECT role FROM users WHERE telegram_id = ?", (telegram_id,)
        )
        row = await cursor.fetchone()
    return str(row["role"]) if row else None


async def register_attendee(
    telegram_id: int,
    display_name: str,
    event_id: int | None = None,
) -> tuple[bool, aiosqlite.Row | None]:
    """Registra un asistente una sola vez y devuelve su registro resultante."""
    now = datetime.now(timezone.utc).isoformat()
    async with get_connection() as connection:
        cursor = await connection.execute(
            "SELECT * FROM attendees WHERE telegram_id = ?", (telegram_id,)
        )
        existing = await cursor.fetchone()
        if existing:
            return False, existing

        await connection.execute(
            """
            INSERT INTO attendees
                (telegram_id, display_name, event_id, registered_at)
            VALUES (?, ?, ?, ?)
            """,
            (telegram_id, display_name, event_id, now),
        )
        await connection.commit()
        cursor = await connection.execute(
            "SELECT * FROM attendees WHERE telegram_id = ?", (telegram_id,)
        )
        return True, await cursor.fetchone()


async def list_events() -> list[dict[str, Any]]:
    """Lista todos los eventos ordenados cronológicamente."""
    async with get_connection() as connection:
        cursor = await connection.execute(
            """
            SELECT id, title, description, event_date, created_by
            FROM events ORDER BY event_date ASC, id ASC
            """
        )
        rows = await cursor.fetchall()
    return [dict(row) for row in rows]


async def count_completed_events(until_date: str) -> int:
    """Cuenta eventos cuya fecha es anterior o igual a la fecha indicada."""
    async with get_connection() as connection:
        cursor = await connection.execute(
            "SELECT COUNT(*) AS total FROM events WHERE event_date <= ?",
            (until_date,),
        )
        row = await cursor.fetchone()
    return int(row["total"])


async def list_upcoming_events(from_date: str) -> list[dict[str, Any]]:
    """Lista eventos posteriores a la fecha indicada."""
    async with get_connection() as connection:
        cursor = await connection.execute(
            """
            SELECT id, title, description, event_date, created_by
            FROM events WHERE event_date > ?
            ORDER BY event_date ASC, id ASC
            """,
            (from_date,),
        )
        rows = await cursor.fetchall()
    return [dict(row) for row in rows]


async def list_projects(
    page: int = 1,
    page_size: int = 5,
    status: str | None = None,
) -> list[dict[str, Any]]:
    """Obtiene una página de proyectos, opcionalmente filtrada por estado."""
    offset = (max(page, 1) - 1) * page_size
    async with get_connection() as connection:
        query = """
            SELECT id, title, description, manager, repository_url,
                   landing_page_url, status, created_at
            FROM projects
        """
        parameters: tuple[Any, ...]
        if status:
            query += " WHERE status = ?"
            parameters = (status, page_size, offset)
        else:
            parameters = (page_size, offset)
        query += " ORDER BY id ASC LIMIT ? OFFSET ?"
        cursor = await connection.execute(query, parameters)
        rows = await cursor.fetchall()
    return [dict(row) for row in rows]


async def create_project(
    title: str,
    description: str,
    manager: str,
    repository_url: str,
    landing_page_url: str | None,
    status: str = "ongoing",
) -> int:
    """Crea un proyecto y devuelve el identificador asignado por SQLite."""
    async with get_connection() as connection:
        cursor = await connection.execute(
            """
            INSERT INTO projects
                (title, description, manager, repository_url, landing_page_url,
                 status, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (title, description, manager, repository_url, empty_to_none(landing_page_url),
             status, datetime.now(timezone.utc).isoformat()),
        )
        await connection.commit()
        return int(cursor.lastrowid)


async def update_project(project_id: int, fields: dict[str, Any]) -> bool:
    """Actualiza únicamente campos permitidos y reporta si existía el proyecto."""
    allowed = {"title", "description", "manager", "repository_url", "landing_page_url", "status"}
    updates = {key: value for key, value in fields.items() if key in allowed}
    if "landing_page_url" in updates:
        updates["landing_page_url"] = empty_to_none(updates["landing_page_url"])
    if not updates:
        return False
    assignments = ", ".join(f"{key} = ?" for key in updates)
    async with get_connection() as connection:
        cursor = await connection.execute(
            f"UPDATE projects SET {assignments} WHERE id = ?",
            (*updates.values(), project_id),
        )
        await connection.commit()
    return cursor.rowcount > 0


async def delete_project(project_id: int) -> bool:
    """Elimina un proyecto por ID e indica si se eliminó alguna fila."""
    async with get_connection() as connection:
        cursor = await connection.execute("DELETE FROM projects WHERE id = ?", (project_id,))
        await connection.commit()
    return cursor.rowcount > 0


async def create_project_proposal(
    name: str, manager: str, contact_phone: str | None,
    contact_email: str | None, description: str,
) -> int:
    """Guarda una propuesta externa y devuelve su nuevo identificador."""
    async with get_connection() as connection:
        cursor = await connection.execute(
            """
            INSERT INTO project_proposals
                (name, manager, contact_phone, contact_email, description, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (name, manager, empty_to_none(contact_phone), empty_to_none(contact_email), description,
             datetime.now(timezone.utc).isoformat()),
        )
        await connection.commit()
        return int(cursor.lastrowid)


async def list_project_proposals() -> list[dict[str, Any]]:
    """Lista las propuestas recibidas, comenzando por las más recientes."""
    async with get_connection() as connection:
        cursor = await connection.execute(
            """
            SELECT id, name, manager, contact_phone, contact_email,
                   description, created_at
            FROM project_proposals
            ORDER BY id DESC
            """
        )
        rows = await cursor.fetchall()
    return [dict(row) for row in rows]


async def create_speaker(
    name: str, company: str | None, job_title: str | None,
    email: str | None, phone: str | None,
) -> int:
    """Registra un speaker, normalizando sus datos opcionales."""
    async with get_connection() as connection:
        cursor = await connection.execute(
            """
            INSERT INTO speakers (name, company, job_title, email, phone, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (name, empty_to_none(company), empty_to_none(job_title),
             empty_to_none(email), empty_to_none(phone), datetime.now(timezone.utc).isoformat()),
        )
        await connection.commit()
        return int(cursor.lastrowid)


async def list_speakers() -> list[dict[str, Any]]:
    """Lista los speakers registrados desde el más reciente."""
    async with get_connection() as connection:
        cursor = await connection.execute(
            "SELECT id, name, company, job_title, email, phone, created_at FROM speakers ORDER BY id DESC"
        )
        rows = await cursor.fetchall()
    return [dict(row) for row in rows]


async def list_core_team() -> list[dict[str, Any]]:
    """Obtiene los integrantes del equipo ordenados por identificador."""
    async with get_connection() as connection:
        cursor = await connection.execute(
            "SELECT id, name, role, instagram, linkedin, github FROM core_team ORDER BY id ASC"
        )
        rows = await cursor.fetchall()
    return [dict(row) for row in rows]


async def create_core_member(
    telegram_id: int, name: str, role: str,
    instagram: str | None, linkedin: str | None, github: str | None,
) -> int:
    """Crea un integrante del equipo y devuelve su identificador."""
    async with get_connection() as connection:
        cursor = await connection.execute(
            """
            INSERT INTO core_team
                (telegram_id, name, role, instagram, linkedin, github, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (telegram_id, name, role, empty_to_none(instagram), empty_to_none(linkedin),
             empty_to_none(github),
             datetime.now(timezone.utc).isoformat()),
        )
        await connection.commit()
        return int(cursor.lastrowid)


async def update_core_member(member_id: int, fields: dict[str, Any]) -> bool:
    """Actualiza campos permitidos de un integrante del equipo."""
    allowed = {"telegram_id", "name", "role", "instagram", "linkedin", "github"}
    updates = {key: value for key, value in fields.items() if key in allowed}
    for social_key in ("instagram", "linkedin", "github"):
        if social_key in updates:
            updates[social_key] = empty_to_none(updates[social_key])
    if not updates:
        return False
    assignments = ", ".join(f"{key} = ?" for key in updates)
    async with get_connection() as connection:
        cursor = await connection.execute(
            f"UPDATE core_team SET {assignments} WHERE id = ?",
            (*updates.values(), member_id),
        )
        await connection.commit()
    return cursor.rowcount > 0


async def delete_core_member(member_id: int) -> bool:
    """Elimina un integrante del equipo e indica si fue encontrado."""
    async with get_connection() as connection:
        cursor = await connection.execute("DELETE FROM core_team WHERE id = ?", (member_id,))
        await connection.commit()
    return cursor.rowcount > 0


async def create_event(
    title: str,
    event_date: str,
    description: str,
    created_by: int,
) -> int:
    """Valida, normaliza y persiste un evento creado por un administrador."""
    normalized_date = normalize_event_date(event_date)
    async with get_connection() as connection:
        cursor = await connection.execute(
            """
            INSERT INTO events (title, description, event_date, created_by)
            VALUES (?, ?, ?, ?)
            """,
            (title, description, normalized_date, created_by),
        )
        await connection.commit()
        return int(cursor.lastrowid)


async def promote_to_admin(telegram_id: int) -> None:
    """Eleva a administrador el usuario de Telegram indicado."""
    async with get_connection() as connection:
        await connection.execute(
            "UPDATE users SET role = 'admin' WHERE telegram_id = ?", (telegram_id,)
        )
        await connection.commit()


async def list_attendees() -> list[dict[str, str]]:
    """Lista los asistentes más recientes primero para la web pública."""
    async with get_connection() as connection:
        cursor = await connection.execute(
            """
            SELECT display_name, registered_at
            FROM attendees ORDER BY registered_at DESC, id DESC
            """
        )
        rows = await cursor.fetchall()
    return [dict(row) for row in rows]


async def database_is_connected() -> bool:
    """Comprueba que SQLite pueda abrirse y ejecutar una consulta sencilla."""
    try:
        async with get_connection() as connection:
            await connection.execute("SELECT 1")
        return True
    except Exception:
        return False
